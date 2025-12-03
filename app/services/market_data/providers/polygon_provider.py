import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from app.services.market_data.base_provider import BaseMarketDataProvider
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse
from app.constants.market_constants import AssetClass, DataProvider
from app.constants.timeframes import Timeframe, PROVIDER_TIMEFRAME_MAP
from app.utils.api_client import AsyncAPIClient
import logging

logger = logging.getLogger(__name__)

class PolygonProvider(BaseMarketDataProvider):
    """Polygon.io API provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        super().__init__(api_key, base_url)
        self.client = AsyncAPIClient(base_url)
        self.supported_assets = [AssetClass.STOCK, AssetClass.FOREX]

    

    async def get_quote(self, symbol: str) -> QuoteResponse:
        try:
            data = await self.client.get(f"/v2/last/trade/{symbol}", params={"apiKey": self.api_key})
            trade = data["results"]
            return QuoteResponse(
                symbol=symbol,
                asset_class=self._detect_asset_class(symbol),
                open=None,
                high=None,
                low=None,
                close=float(trade["p"]),
                volume=None,
                change=None,
                change_percent=None,
                timestamp=datetime.fromtimestamp(trade["t"] / 1000),
                provider=DataProvider.POLYGON
            )
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise

    
    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Get multiple quotes in batch"""
        tasks = [self.get_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        quotes = []
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to get quote for {symbol}: {result}")
            else:
                quotes.append(result)
        
        return quotes
    
    async def is_healthy(self) -> bool:
        """Health check that works with free tier"""
        try:
            # Use a simpler endpoint that works with free tier
            await self.client.get(
                "/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-02",
                params={"apiKey": self.api_key}
            )
            return True
        except Exception as e:
            logger.warning(f"Polygon health check failed: {e}")
            return False

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

        timespan = PROVIDER_TIMEFRAME_MAP["polygon"].get(timeframe.value, "day")
        multiplier = 1

        endpoint = (
            f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/"
            f"{from_date.strftime('%Y-%m-%d')}/{to_date.strftime('%Y-%m-%d')}"
        )
        params = {"limit": limit, "sort": "asc", "apiKey": self.api_key}

        data = await self.client.get(endpoint, params=params)
        results = data.get("results", [])

        return [
            CandleResponse(
                symbol=symbol,
                timeframe=timeframe,
                open=candle["o"],
                high=candle["h"],
                low=candle["l"],
                close=candle["c"],
                volume=candle["v"],
                vwap=candle.get("vw"),
                trades=candle.get("n"),
                timestamp=datetime.fromtimestamp(candle["t"] / 1000)
            )
            for candle in results
        ]

    async def search_symbol(self, query: str) -> List[Dict]:
        """Search symbols"""
        endpoint = "/v3/reference/tickers"
        params = {"search": query, "active": True, "limit": 10, "apiKey": self.api_key}
        data = await self.client.get(endpoint, params=params)
        return data.get("results", [])

    def supports_asset_class(self, asset_class: str) -> bool:
        return asset_class in self.supported_assets

    async def is_healthy(self) -> bool:
        """Check if Polygon API is reachable"""
        try:
            await self.client.get(
                "/v2/aggs/ticker/AAPL/range/1/day/2023-01-09/2023-01-09",
                params={"apiKey": self.api_key}
            )
            return True
        except:
            return False
