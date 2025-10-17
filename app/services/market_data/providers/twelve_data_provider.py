"""
Twelve Data provider
Good for stocks, forex, crypto, indices
Free tier: 800 API calls/day
Paid: Real-time data
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.services.market_data.base_provider import BaseMarketDataProvider
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse
from app.constants.market_constants import AssetClass, DataProvider
from app.constants.timeframes import Timeframe
from app.utils.api_client import AsyncAPIClient
import logging

logger = logging.getLogger(__name__)


class TwelveDataProvider(BaseMarketDataProvider):
    """Twelve Data API provider"""
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.client = AsyncAPIClient(base_url, rate_limit=8)
        self.supported_assets = [
            AssetClass.STOCK,
            AssetClass.FOREX,
            AssetClass.CRYPTO,
            AssetClass.INDEX,
            AssetClass.COMMODITY
        ]
    
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time quote"""
        endpoint = "/quote"
        params = {"symbol": symbol, "apikey": self.api_key}
        
        data = await self.client.get(endpoint, params=params)
        
        return QuoteResponse(
            symbol=symbol,
            asset_class=AssetClass.STOCK,
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            close=float(data.get("close", 0)),
            volume=float(data.get("volume", 0)),
            change=float(data.get("change", 0)),
            change_percent=float(data.get("percent_change", 0)),
            timestamp=datetime.fromisoformat(data.get("datetime", "")),
            provider=DataProvider.TWELVE_DATA
        )
    
    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Get multiple quotes"""
        import asyncio
        tasks = [self.get_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, QuoteResponse)]
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 100,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[CandleResponse]:
        """Get time series data"""
        # Twelve Data intervals: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month
        interval_map = {
            Timeframe.ONE_MINUTE: "1min",
            Timeframe.FIVE_MINUTES: "5min",
            Timeframe.FIFTEEN_MINUTES: "15min",
            Timeframe.THIRTY_MINUTES: "30min",
            Timeframe.ONE_HOUR: "1h",
            Timeframe.FOUR_HOURS: "4h",
            Timeframe.ONE_DAY: "1day",
            Timeframe.ONE_WEEK: "1week",
            Timeframe.ONE_MONTH: "1month"
        }
        
        interval = interval_map.get(timeframe, "1day")
        
        endpoint = "/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": limit,
            "apikey": self.api_key
        }
        
        data = await self.client.get(endpoint, params=params)
        values = data.get("values", [])
        
        candles = []
        for item in values:
            candles.append(
                CandleResponse(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=float(item.get("volume", 0)),
                    timestamp=datetime.fromisoformat(item.get("datetime", ""))
                )
            )
        
        return candles
    
    async def search_symbol(self, query: str) -> List[Dict]:
        """Search for symbols"""
        endpoint = "/symbol_search"
        params = {"symbol": query, "apikey": self.api_key}
        
        data = await self.client.get(endpoint, params=params)
        results = data.get("data", [])
        
        return [
            {
                "symbol": item.get("symbol"),
                "name": item.get("instrument_name"),
                "type": item.get("instrument_type"),
                "exchange": item.get("exchange"),
                "currency": item.get("currency")
            }
            for item in results
        ]
    
    def supports_asset_class(self, asset_class: str) -> bool:
        return asset_class in self.supported_assets
    
    async def is_healthy(self) -> bool:
        try:
            await self.get_quote("AAPL")
            return True
        except:
            return False