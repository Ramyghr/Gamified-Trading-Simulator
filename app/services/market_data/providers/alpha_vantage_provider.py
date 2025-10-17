"""
Alpha Vantage provider implementation
Free tier: 25 API calls/day, 500 calls/day premium
Supports: Stocks, Forex, Crypto, Commodities
"""
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


class AlphaVantageProvider(BaseMarketDataProvider):
    """Alpha Vantage API provider"""
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.client = AsyncAPIClient(base_url, rate_limit=5)  # 5 calls/min for free tier
        self.supported_assets = [
            AssetClass.STOCK,
            AssetClass.FOREX,
            AssetClass.CRYPTO,
            AssetClass.COMMODITY
        ]
    
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time quote"""
        endpoint = "/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        data = await self.client.get(endpoint, params=params)
        
        if "Global Quote" not in data:
            raise Exception(f"Invalid response for {symbol}")
        
        quote_data = data["Global Quote"]
        
        # Alpha Vantage returns keys like "01. symbol", "05. price", etc.
        open_price = float(quote_data.get("02. open", 0))
        high_price = float(quote_data.get("03. high", 0))
        low_price = float(quote_data.get("04. low", 0))
        close_price = float(quote_data.get("05. price", 0))
        volume = float(quote_data.get("06. volume", 0))
        prev_close = float(quote_data.get("08. previous close", 0))
        
        change = close_price - prev_close
        change_percent = (change / prev_close * 100) if prev_close else 0
        
        return QuoteResponse(
            symbol=symbol,
            asset_class=AssetClass.STOCK,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            change=change,
            change_percent=change_percent,
            timestamp=datetime.now(),  # Alpha Vantage doesn't provide timestamp in quote
            provider=DataProvider.ALPHA_VANTAGE
        )
    
    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Get multiple quotes (sequential due to rate limit)"""
        import asyncio
        quotes = []
        for symbol in symbols:
            try:
                quote = await self.get_quote(symbol)
                quotes.append(quote)
                await asyncio.sleep(12)  # Rate limiting: 5 calls/min = 12 sec/call
            except Exception as e:
                logger.error(f"Failed to get quote for {symbol}: {e}")
        return quotes
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 100,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[CandleResponse]:
        """Get historical candles"""
        
        # Determine function based on timeframe
        if timeframe in [Timeframe.ONE_MINUTE, Timeframe.FIVE_MINUTES, 
                        Timeframe.FIFTEEN_MINUTES, Timeframe.THIRTY_MINUTES, 
                        Timeframe.ONE_HOUR]:
            function = "TIME_SERIES_INTRADAY"
            interval = PROVIDER_TIMEFRAME_MAP["alpha_vantage"].get(timeframe.value, "5min")
            interval_param = interval
        elif timeframe == Timeframe.ONE_DAY:
            function = "TIME_SERIES_DAILY"
            interval_param = None
        elif timeframe == Timeframe.ONE_WEEK:
            function = "TIME_SERIES_WEEKLY"
            interval_param = None
        elif timeframe == Timeframe.ONE_MONTH:
            function = "TIME_SERIES_MONTHLY"
            interval_param = None
        else:
            function = "TIME_SERIES_DAILY"
            interval_param = None
        
        endpoint = "/query"
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "full" if limit > 100 else "compact"
        }
        
        if interval_param:
            params["interval"] = interval_param
        
        data = await self.client.get(endpoint, params=params)
        
        # Find the time series key
        time_series_key = None
        for key in data.keys():
            if "Time Series" in key:
                time_series_key = key
                break
        
        if not time_series_key:
            raise Exception(f"No time series data for {symbol}")
        
        time_series = data[time_series_key]
        
        candles = []
        for timestamp_str, candle_data in list(time_series.items())[:limit]:
            try:
                timestamp = datetime.strptime(timestamp_str.split()[0], "%Y-%m-%d")
            except:
                timestamp = datetime.fromisoformat(timestamp_str)
            
            candles.append(
                CandleResponse(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=float(candle_data.get("1. open", 0)),
                    high=float(candle_data.get("2. high", 0)),
                    low=float(candle_data.get("3. low", 0)),
                    close=float(candle_data.get("4. close", 0)),
                    volume=float(candle_data.get("5. volume", 0)),
                    timestamp=timestamp
                )
            )
        
        # Sort by timestamp (oldest first)
        candles.sort(key=lambda x: x.timestamp)
        
        return candles
    
    async def get_forex_quote(self, from_currency: str, to_currency: str) -> QuoteResponse:
        """Get forex exchange rate"""
        endpoint = "/query"
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }
        
        data = await self.client.get(endpoint, params=params)
        
        if "Realtime Currency Exchange Rate" not in data:
            raise Exception(f"Invalid forex response for {from_currency}/{to_currency}")
        
        rate_data = data["Realtime Currency Exchange Rate"]
        
        exchange_rate = float(rate_data.get("5. Exchange Rate", 0))
        
        return QuoteResponse(
            symbol=f"{from_currency}/{to_currency}",
            asset_class=AssetClass.FOREX,
            open=exchange_rate,
            high=exchange_rate,
            low=exchange_rate,
            close=exchange_rate,
            volume=0,
            timestamp=datetime.now(),
            provider=DataProvider.ALPHA_VANTAGE
        )
    
    async def get_crypto_quote(self, symbol: str, market: str = "USD") -> QuoteResponse:
        """Get cryptocurrency quote"""
        endpoint = "/query"
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": symbol,
            "to_currency": market,
            "apikey": self.api_key
        }
        
        data = await self.client.get(endpoint, params=params)
        
        if "Realtime Currency Exchange Rate" not in data:
            raise Exception(f"Invalid crypto response for {symbol}")
        
        rate_data = data["Realtime Currency Exchange Rate"]
        
        price = float(rate_data.get("5. Exchange Rate", 0))
        
        return QuoteResponse(
            symbol=symbol,
            asset_class=AssetClass.CRYPTO,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=0,
            timestamp=datetime.now(),
            provider=DataProvider.ALPHA_VANTAGE
        )
    
    async def search_symbol(self, query: str) -> List[Dict]:
        """Search for symbols"""
        endpoint = "/query"
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": query,
            "apikey": self.api_key
        }
        
        data = await self.client.get(endpoint, params=params)
        
        matches = data.get("bestMatches", [])
        
        return [
            {
                "symbol": match.get("1. symbol"),
                "name": match.get("2. name"),
                "type": match.get("3. type"),
                "region": match.get("4. region"),
                "currency": match.get("8. currency"),
                "match_score": float(match.get("9. matchScore", 0))
            }
            for match in matches
        ]
    
    def supports_asset_class(self, asset_class: str) -> bool:
        return asset_class in self.supported_assets
    
    async def is_healthy(self) -> bool:
        try:
            await self.get_quote("IBM")
            return True
        except:
            return False