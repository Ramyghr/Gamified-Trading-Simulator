"""
Base class for all market data providers
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse
from app.constants.timeframes import Timeframe


class BaseMarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.supported_assets = []
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time quote for a symbol"""
        pass
    
    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Get multiple quotes in batch"""
        pass
    
    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 100,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[CandleResponse]:
        """Get historical OHLC candles"""
        pass
    
    @abstractmethod
    async def search_symbol(self, query: str) -> List[Dict]:
        """Search for symbols"""
        pass
    
    @abstractmethod
    def supports_asset_class(self, asset_class: str) -> bool:
        """Check if provider supports an asset class"""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if provider is currently working"""
        pass