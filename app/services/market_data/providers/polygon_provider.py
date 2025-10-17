import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from app.services.market_data.base_provider import BaseMarketDataProvider
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse
from app.constants.market_constants import AssetClass, DataProvider
from app.constants.timeframes import Timeframe, PROVIDER_TIMEFRAME_MAP
from app.utils.api_client import AsyncAPIClient


class PolygonProvider(BaseMarketDataProvider):
    """Polygon.io API provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        super().__init__(api_key, base_url)
        self.client = AsyncAPIClient(base_url)
        self.supported_assets = [AssetClass.STOCK, AssetClass.FOREX, AssetClass.CRYPTO]

    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time quote"""
        endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
        data = await self.client.get(endpoint, params={"apiKey": self.api_key})

        ticker = data.get("ticker", {})
        day = ticker.get("day", {})
        prev_day = ticker.get("prevDay", {})

        return QuoteResponse(
            symbol=symbol,
            asset_class=AssetClass.STOCK,
            open=day.get("o", 0),
            high=day.get("h", 0),
            low=day.get("l", 0),
            close=day.get("c", 0),
            volume=day.get("v", 0),
            change=day.get("c", 0) - prev_day.get("c", 0),
            change_percent=((day.get("c", 0) - prev_day.get("c", 0)) / prev_day.get("c", 1)) * 100,
            vwap=day.get("vw"),
            timestamp=datetime.fromtimestamp(ticker.get("updated", 0) / 1000),
            provider=DataProvider.POLYGON
        )

    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Batch quotes"""
        tasks = [self.get_quote(symbol) for symbol in symbols]
        return await asyncio.gather(*tasks, return_exceptions=True)

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
