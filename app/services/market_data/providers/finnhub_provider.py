import aiohttp
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.services.market_data.base_provider import BaseMarketDataProvider
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse
from app.constants.market_constants import AssetClass, DataProvider
from app.constants.timeframes import Timeframe, TIMEFRAME_SECONDS
from app.utils.api_client import AsyncAPIClient
import logging

logger = logging.getLogger(__name__)


class FinnhubProvider(BaseMarketDataProvider):
    """Finnhub API provider"""
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.client = AsyncAPIClient(base_url, rate_limit=60)
        self.supported_assets = [AssetClass.STOCK, AssetClass.FOREX, AssetClass.CRYPTO]
    
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time quote"""
        endpoint = "/quote"
        params = {"symbol": symbol, "token": self.api_key}
        
        data = await self.client.get(endpoint, params=params)
        
        # Finnhub returns: c (current), h (high), l (low), o (open), pc (previous close)
        current_price = data.get("c", 0)
        prev_close = data.get("pc", 0)
        change = current_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close else 0
        
        return QuoteResponse(
            symbol=symbol,
            asset_class=AssetClass.STOCK,
            open=data.get("o", 0),
            high=data.get("h", 0),
            low=data.get("l", 0),
            close=current_price,
            volume=0,  # Finnhub quote doesn't include volume
            change=change,
            change_percent=change_percent,
            timestamp=datetime.fromtimestamp(data.get("t", 0)),
            provider=DataProvider.FINNHUB
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
        """Get historical candles"""
        if not to_date:
            to_date = datetime.now()
        if not from_date:
            from_date = to_date - timedelta(days=30)
        
        # Finnhub uses resolution: 1, 5, 15, 30, 60, D, W, M
        resolution_map = {
            Timeframe.ONE_MINUTE: "1",
            Timeframe.FIVE_MINUTES: "5",
            Timeframe.FIFTEEN_MINUTES: "15",
            Timeframe.THIRTY_MINUTES: "30",
            Timeframe.ONE_HOUR: "60",
            Timeframe.ONE_DAY: "D",
            Timeframe.ONE_WEEK: "W",
            Timeframe.ONE_MONTH: "M"
        }
        
        resolution = resolution_map.get(timeframe, "D")
        
        endpoint = "/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": int(from_date.timestamp()),
            "to": int(to_date.timestamp()),
            "token": self.api_key
        }
        
        data = await self.client.get(endpoint, params=params)
        
        if data.get("s") != "ok":
            return []
        
        # Finnhub returns arrays: c, h, l, o, t, v
        candles = []
        for i in range(len(data.get("t", []))):
            candles.append(
                CandleResponse(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=data["o"][i],
                    high=data["h"][i],
                    low=data["l"][i],
                    close=data["c"][i],
                    volume=data["v"][i],
                    timestamp=datetime.fromtimestamp(data["t"][i])
                )
            )
        
        return candles[:limit]
    
    async def search_symbol(self, query: str) -> List[Dict]:
        """Search for symbols"""
        endpoint = "/search"
        params = {"q": query, "token": self.api_key}
        
        data = await self.client.get(endpoint, params=params)
        results = data.get("result", [])
        
        return [
            {
                "symbol": item.get("symbol"),
                "name": item.get("description"),
                "type": item.get("type"),
                "exchange": item.get("displaySymbol")
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