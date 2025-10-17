"""
Utility functions for timeframe conversions
"""
from datetime import datetime, timedelta
from app.constants.timeframes import Timeframe, TIMEFRAME_SECONDS, PROVIDER_TIMEFRAME_MAP
from typing import Optional


class TimeframeConverter:
    """Convert between different timeframe representations"""
    
    @staticmethod
    def to_seconds(timeframe: Timeframe) -> int:
        """Convert timeframe to seconds"""
        return TIMEFRAME_SECONDS.get(timeframe, 86400)
    
    @staticmethod
    def to_provider_format(timeframe: Timeframe, provider: str) -> str:
        """Convert timeframe to provider-specific format"""
        mapping = PROVIDER_TIMEFRAME_MAP.get(provider, {})
        return mapping.get(timeframe.value, timeframe.value)
    
    @staticmethod
    def calculate_candle_count(from_date: datetime, to_date: datetime, timeframe: Timeframe) -> int:
        """Calculate number of candles between two dates"""
        delta_seconds = (to_date - from_date).total_seconds()
        timeframe_seconds = TimeframeConverter.to_seconds(timeframe)
        return int(delta_seconds / timeframe_seconds)
    
    @staticmethod
    def calculate_from_date(to_date: datetime, candle_count: int, timeframe: Timeframe) -> datetime:
        """Calculate from_date given to_date and candle count"""
        timeframe_seconds = TimeframeConverter.to_seconds(timeframe)
        total_seconds = candle_count * timeframe_seconds
        return to_date - timedelta(seconds=total_seconds)
    
    @staticmethod
    def is_market_hours(dt: Optional[datetime] = None) -> bool:
        """Check if given time is during market hours (US stocks)"""
        if dt is None:
            dt = datetime.now()
        
        # Check if weekend
        if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check time (9:30 AM - 4:00 PM EST)
        market_open = dt.replace(hour=9, minute=30, second=0)
        market_close = dt.replace(hour=16, minute=0, second=0)
        
        return market_open <= dt <= market_close
    
    @staticmethod
    def next_market_open() -> datetime:
        """Get next market open time"""
        now = datetime.now()
        
        # If weekend, go to Monday
        if now.weekday() >= 5:
            days_ahead = 7 - now.weekday()
            next_open = now + timedelta(days=days_ahead)
            return next_open.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # If after market close, next open is tomorrow
        market_close = now.replace(hour=16, minute=0, second=0)
        if now > market_close:
            if now.weekday() == 4:  # Friday
                next_open = now + timedelta(days=3)  # Monday
            else:
                next_open = now + timedelta(days=1)
            return next_open.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # Market opens today
        return now.replace(hour=9, minute=30, second=0, microsecond=0)