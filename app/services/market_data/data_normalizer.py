"""
Normalize data from different providers to standard format
"""
from typing import Dict, Any
from datetime import datetime
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse
from app.constants.market_constants import AssetClass, DataProvider
from app.constants.timeframes import Timeframe


class DataNormalizer:
    """Normalize provider-specific data formats"""
    
    @staticmethod
    def normalize_polygon_quote(data: Dict, symbol: str) -> QuoteResponse:
        """Normalize Polygon quote data"""
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
    
    @staticmethod
    def normalize_binance_quote(data: Dict, symbol: str) -> QuoteResponse:
        """Normalize Binance quote data"""
        return QuoteResponse(
            symbol=symbol,
            asset_class=AssetClass.CRYPTO,
            open=float(data.get("openPrice", 0)),
            high=float(data.get("highPrice", 0)),
            low=float(data.get("lowPrice", 0)),
            close=float(data.get("lastPrice", 0)),
            volume=float(data.get("volume", 0)),
            change=float(data.get("priceChange", 0)),
            change_percent=float(data.get("priceChangePercent", 0)),
            trades=int(data.get("count", 0)),
            timestamp=datetime.fromtimestamp(data.get("closeTime", 0) / 1000),
            provider=DataProvider.BINANCE
        )
    
    @staticmethod
    def normalize_alpha_vantage_candle(data: Dict, symbol: str, timeframe: Timeframe) -> CandleResponse:
        """Normalize Alpha Vantage candle data"""
        return CandleResponse(
            symbol=symbol,
            timeframe=timeframe,
            open=float(data.get("1. open", 0)),
            high=float(data.get("2. high", 0)),
            low=float(data.get("3. low", 0)),
            close=float(data.get("4. close", 0)),
            volume=float(data.get("5. volume", 0)),
            timestamp=datetime.fromisoformat(data.get("timestamp", ""))
        )