"""
Binance provider for cryptocurrency data
FREE, unlimited API calls
Real-time data with WebSocket support
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


class BinanceProvider(BaseMarketDataProvider):
    """Binance API provider (Crypto only)"""
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__("", base_url)  # No API key needed for public endpoints
        self.client = AsyncAPIClient(base_url, rate_limit=1200)  # 1200 weight/min
        self.supported_assets = [AssetClass.CRYPTO]
    
    def _format_symbol(self, symbol: str) -> str:
        """Convert symbol to Binance format (e.g., BTC -> BTCUSDT)"""
        symbol_upper = symbol.upper()
        
        # If already in pair format, return as is
        if "USDT" in symbol_upper or "BUSD" in symbol_upper:
            return symbol_upper
        
        # Common crypto symbols
        return f"{symbol_upper}USDT"
    
    def _unformat_symbol(self, binance_symbol: str) -> str:
        """Convert Binance format back to simple symbol"""
        return binance_symbol.replace("USDT", "").replace("BUSD", "")
    
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time crypto quote"""
        binance_symbol = self._format_symbol(symbol)
        
        endpoint = "/api/v3/ticker/24hr"
        params = {"symbol": binance_symbol}
        
        data = await self.client.get(endpoint, params=params)
        
        open_price = float(data.get("openPrice", 0))
        close_price = float(data.get("lastPrice", 0))
        
        return QuoteResponse(
            symbol=symbol.upper(),
            asset_class=AssetClass.CRYPTO,
            open=open_price,
            high=float(data.get("highPrice", 0)),
            low=float(data.get("lowPrice", 0)),
            close=close_price,
            volume=float(data.get("volume", 0)),
            change=float(data.get("priceChange", 0)),
            change_percent=float(data.get("priceChangePercent", 0)),
            vwap=float(data.get("weightedAvgPrice", 0)),
            trades=int(data.get("count", 0)),
            timestamp=datetime.fromtimestamp(data.get("closeTime", 0) / 1000),
            provider=DataProvider.BINANCE
        )
    
    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Get multiple crypto quotes"""
        # Binance allows batch requests
        endpoint = "/api/v3/ticker/24hr"
        
        data = await self.client.get(endpoint)  # Get all tickers
        
        # Filter to requested symbols
        symbol_map = {self._format_symbol(s): s for s in symbols}
        quotes = []
        
        for ticker in data:
            binance_symbol = ticker.get("symbol")
            if binance_symbol in symbol_map:
                original_symbol = symbol_map[binance_symbol]
                
                quotes.append(
                    QuoteResponse(
                        symbol=original_symbol.upper(),
                        asset_class=AssetClass.CRYPTO,
                        open=float(ticker.get("openPrice", 0)),
                        high=float(ticker.get("highPrice", 0)),
                        low=float(ticker.get("lowPrice", 0)),
                        close=float(ticker.get("lastPrice", 0)),
                        volume=float(ticker.get("volume", 0)),
                        change=float(ticker.get("priceChange", 0)),
                        change_percent=float(ticker.get("priceChangePercent", 0)),
                        vwap=float(ticker.get("weightedAvgPrice", 0)),
                        trades=int(ticker.get("count", 0)),
                        timestamp=datetime.fromtimestamp(ticker.get("closeTime", 0) / 1000),
                        provider=DataProvider.BINANCE
                    )
                )
        
        return quotes
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 100,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[CandleResponse]:
        """Get historical klines/candlestick data"""
        binance_symbol = self._format_symbol(symbol)
        
        # Binance intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        interval = PROVIDER_TIMEFRAME_MAP["binance"].get(timeframe.value, "1d")
        
        endpoint = "/api/v3/klines"
        params = {
            "symbol": binance_symbol,
            "interval": interval,
            "limit": min(limit, 1000)  # Binance max is 1000
        }
        
        if from_date:
            params["startTime"] = int(from_date.timestamp() * 1000)
        if to_date:
            params["endTime"] = int(to_date.timestamp() * 1000)
        
        data = await self.client.get(endpoint, params=params)
        
        candles = []
        for kline in data:
            # Binance returns: [time, open, high, low, close, volume, close_time, quote_volume, trades, ...]
            candles.append(
                CandleResponse(
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    trades=int(kline[8]),
                    timestamp=datetime.fromtimestamp(kline[0] / 1000)
                )
            )
        
        return candles
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current price (fast endpoint)"""
        binance_symbol = self._format_symbol(symbol)
        
        endpoint = "/api/v3/ticker/price"
        params = {"symbol": binance_symbol}
        
        data = await self.client.get(endpoint, params=params)
        return float(data.get("price", 0))
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book depth"""
        binance_symbol = self._format_symbol(symbol)
        
        endpoint = "/api/v3/depth"
        params = {
            "symbol": binance_symbol,
            "limit": limit
        }
        
        data = await self.client.get(endpoint, params=params)
        
        return {
            "bids": [[float(price), float(qty)] for price, qty in data.get("bids", [])],
            "asks": [[float(price), float(qty)] for price, qty in data.get("asks", [])],
            "timestamp": datetime.now()
        }
    
    async def search_symbol(self, query: str) -> List[Dict]:
        """Search for crypto symbols"""
        # Binance doesn't have a search endpoint, so we get all symbols and filter
        endpoint = "/api/v3/exchangeInfo"
        
        data = await self.client.get(endpoint)
        symbols = data.get("symbols", [])
        
        query_upper = query.upper()
        results = []
        
        for symbol_info in symbols:
            symbol = symbol_info.get("symbol", "")
            base_asset = symbol_info.get("baseAsset", "")
            
            if (query_upper in symbol or 
                query_upper in base_asset or 
                base_asset.startswith(query_upper)):
                
                results.append({
                    "symbol": self._unformat_symbol(symbol),
                    "base_asset": base_asset,
                    "quote_asset": symbol_info.get("quoteAsset"),
                    "status": symbol_info.get("status"),
                    "full_symbol": symbol
                })
            
            if len(results) >= 20:
                break
        
        return results
    
    def supports_asset_class(self, asset_class: str) -> bool:
        return asset_class == AssetClass.CRYPTO
    
    async def is_healthy(self) -> bool:
        try:
            endpoint = "/api/v3/ping"
            await self.client.get(endpoint)
            return True
        except:
            return False