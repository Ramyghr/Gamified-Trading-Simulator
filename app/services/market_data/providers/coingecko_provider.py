"""
CoinGecko provider for cryptocurrency data
Completely FREE, no API key required
Covers 10,000+ cryptocurrencies
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


class CoinGeckoProvider(BaseMarketDataProvider):
    """CoinGecko API provider"""
    
    # Symbol to CoinGecko ID mapping
    SYMBOL_TO_ID = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "ADA": "cardano",
        "XRP": "ripple",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "AVAX": "avalanche-2"
    }
    
    def __init__(self, api_key: str, base_url: str):
        super().__init__("", base_url)  # No API key needed
        self.client = AsyncAPIClient(base_url, rate_limit=50)
        self.supported_assets = [AssetClass.CRYPTO]
    
    def _symbol_to_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        symbol_upper = symbol.upper()
        return self.SYMBOL_TO_ID.get(symbol_upper, symbol.lower())
    
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Get real-time crypto quote"""
        coin_id = self._symbol_to_id(symbol)
        
        endpoint = "/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        data = await self.client.get(endpoint, params=params)
        
        if coin_id not in data:
            raise Exception(f"Coin {symbol} not found")
        
        coin_data = data[coin_id]
        current_price = coin_data.get("usd", 0)
        change_24h = coin_data.get("usd_24h_change", 0)
        volume_24h = coin_data.get("usd_24h_vol", 0)
        
        # Calculate open price from current and 24h change
        open_price = current_price / (1 + change_24h / 100) if change_24h else current_price
        
        return QuoteResponse(
            symbol=symbol.upper(),
            asset_class=AssetClass.CRYPTO,
            open=open_price,
            high=current_price * 1.02,  # Approximate
            low=current_price * 0.98,   # Approximate
            close=current_price,
            volume=volume_24h,
            change=current_price - open_price,
            change_percent=change_24h,
            timestamp=datetime.now(),
            provider=DataProvider.COINGECKO
        )
    
    async def get_quotes(self, symbols: List[str]) -> List[QuoteResponse]:
        """Get multiple crypto quotes in batch"""
        coin_ids = [self._symbol_to_id(s) for s in symbols]
        
        endpoint = "/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        
        data = await self.client.get(endpoint, params=params)
        
        quotes = []
        for i, symbol in enumerate(symbols):
            coin_id = coin_ids[i]
            if coin_id in data:
                coin_data = data[coin_id]
                current_price = coin_data.get("usd", 0)
                change_24h = coin_data.get("usd_24h_change", 0)
                
                quotes.append(
                    QuoteResponse(
                        symbol=symbol.upper(),
                        asset_class=AssetClass.CRYPTO,
                        open=current_price / (1 + change_24h / 100),
                        high=current_price * 1.02,
                        low=current_price * 0.98,
                        close=current_price,
                        volume=coin_data.get("usd_24h_vol", 0),
                        change_percent=change_24h,
                        timestamp=datetime.now(),
                        provider=DataProvider.COINGECKO
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
        """Get historical OHLC data"""
        coin_id = self._symbol_to_id(symbol)
        
        # CoinGecko OHLC endpoint supports: 1, 7, 14, 30, 90, 180, 365 days
        if not from_date:
            from_date = datetime.now() - timedelta(days=30)
        
        days = (datetime.now() - from_date).days
        days = min(max(days, 1), 365)
        
        endpoint = f"/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        data = await self.client.get(endpoint, params=params)
        
        candles = []
        for item in data[:limit]:
            # CoinGecko returns: [timestamp, open, high, low, close]
            candles.append(
                CandleResponse(
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    open=item[1],
                    high=item[2],
                    low=item[3],
                    close=item[4],
                    volume=0,  # OHLC endpoint doesn't include volume
                    timestamp=datetime.fromtimestamp(item[0] / 1000)
                )
            )
        
        return candles
    
    async def search_symbol(self, query: str) -> List[Dict]:
        """Search for cryptocurrencies"""
        endpoint = "/search"
        params = {"query": query}
        
        data = await self.client.get(endpoint, params=params)
        coins = data.get("coins", [])
        
        return [
            {
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "id": coin.get("id"),
                "market_cap_rank": coin.get("market_cap_rank")
            }
            for coin in coins[:20]
        ]
    
    def supports_asset_class(self, asset_class: str) -> bool:
        return asset_class == AssetClass.CRYPTO
    
    async def is_healthy(self) -> bool:
        try:
            await self.get_quote("BTC")
            return True
        except:
            return False