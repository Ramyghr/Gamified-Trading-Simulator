"""
Enhanced Market Data Service with intelligent caching and provider rotation
"""
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException
import asyncio
import os
import logging
from decimal import Decimal
from app.schemas.quote import QuoteResponse
from app.config.redis_client import redis_client
from app.services.market_data.providers.coingecko_provider import CoinGeckoProvider
from app.services.market_data.providers.finnhub_provider import FinnhubProvider
from app.services.market_data.providers.twelve_data_provider import TwelveDataProvider
from app.constants.market_constants import AssetClass, DataProvider
from asyncio import gather

logger = logging.getLogger(__name__)


class MarketDataService:
    """Enhanced service with smart caching and real-time updates"""

    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        self.twelve_key = os.getenv("TWELVE_DATA_API_KEY", "")

        # Multi-layer cache
        self.memory_cache: Dict[str, tuple[float, datetime]] = {}
        self.cache_ttl = timedelta(seconds=15)  # 15 second memory cache
        
        # Rate limiting tracking
        self.provider_calls = {}
        self.rate_limits = {
            "alpha_vantage": {"calls": 0, "limit": 5, "window": 60},  # 5 calls per minute
            "finnhub": {"calls": 0, "limit": 60, "window": 60},  # 60 calls per minute
            "twelve_data": {"calls": 0, "limit": 8, "window": 60},  # 8 calls per minute
        }
        
        # Initialize providers
        self.providers = {}
        self._initialize_providers()
        
        logger.info(f"Initialized providers: {list(self.providers.keys())}")

    def _initialize_providers(self):
        """Initialize all available providers"""
        try:
            self.providers[DataProvider.COINGECKO] = CoinGeckoProvider(
                api_key=None, 
                base_url="https://api.coingecko.com/api/v3"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize CoinGecko: {e}")
        
        if self.finnhub_key:
            try:
                self.providers[DataProvider.FINNHUB] = FinnhubProvider(
                    api_key=self.finnhub_key, 
                    base_url="https://finnhub.io/api/v1"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Finnhub: {e}")
        
        if self.twelve_key:
            try:
                self.providers[DataProvider.TWELVE_DATA] = TwelveDataProvider(
                    api_key=self.twelve_key, 
                    base_url="https://api.twelvedata.com"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize TwelveData: {e}")

    # ---------------------------------------------------------
    # Enhanced Cache Layer with Redis
    # ---------------------------------------------------------
    def _get_from_memory_cache(self, symbol: str) -> Optional[float]:
        """Check memory cache (fastest)"""
        if symbol in self.memory_cache:
            price, ts = self.memory_cache[symbol]
            if datetime.utcnow() - ts < self.cache_ttl:
                return price
        return None

    def _get_from_redis_cache(self, symbol: str) -> Optional[float]:
        """Check Redis cache (fast, shared across instances)"""
        try:
            cached = redis_client.get(f"price:{symbol}")
            if cached:
                return float(cached)
        except Exception as e:
            logger.debug(f"Redis read failed for {symbol}: {e}")
        return None

    def _save_to_cache(self, symbol: str, price: float):
        """Save to both memory and Redis"""
        # Memory cache
        self.memory_cache[symbol] = (price, datetime.utcnow())
        
        # Redis cache with 60 second TTL
        try:
            redis_client.setex(f"price:{symbol}", 60, str(price))
        except Exception as e:
            logger.warning(f"Redis cache write failed for {symbol}: {e}")

    def _can_call_provider(self, provider_name: str) -> bool:
        """Check if we can call this provider (rate limiting)"""
        if provider_name not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[provider_name]
        now = datetime.utcnow()
        
        # Clean old calls
        if provider_name in self.provider_calls:
            self.provider_calls[provider_name] = [
                call_time for call_time in self.provider_calls[provider_name]
                if (now - call_time).seconds < limit_info["window"]
            ]
        else:
            self.provider_calls[provider_name] = []
        
        # Check if under limit
        return len(self.provider_calls[provider_name]) < limit_info["limit"]

    def _record_provider_call(self, provider_name: str):
        """Record a provider API call"""
        if provider_name not in self.provider_calls:
            self.provider_calls[provider_name] = []
        self.provider_calls[provider_name].append(datetime.utcnow())

    # ---------------------------------------------------------
    # Enhanced Price Fetching with Smart Fallback
    # ---------------------------------------------------------
    async def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Optional[float]:
        """Get stock price with intelligent caching and fallback"""
        # Check cache unless force refresh
        if not force_refresh:
            cached = self._get_from_memory_cache(symbol)
            if cached:
                logger.debug(f"[MEMORY CACHE] {symbol}: {cached}")
                return cached
            
            cached = self._get_from_redis_cache(symbol)
            if cached:
                logger.debug(f"[REDIS CACHE] {symbol}: {cached}")
                self.memory_cache[symbol] = (cached, datetime.utcnow())
                return cached

        # Try providers in order of rate limit availability
        providers_to_try = []
        
        if self._can_call_provider("twelve_data"):
            providers_to_try.append(("TwelveData", self._fetch_twelve_data))
        
        if self._can_call_provider("finnhub"):
            providers_to_try.append(("Finnhub", self._fetch_finnhub))
        
        if self._can_call_provider("alpha_vantage"):
            providers_to_try.append(("AlphaVantage", self._fetch_alpha_vantage))

        # Try each provider
        for provider_name, fetch_func in providers_to_try:
            try:
                self._record_provider_call(provider_name.lower().replace(" ", "_"))
                price = await fetch_func(symbol)
                
                if price and price > 0:
                    logger.info(f"[{provider_name}] {symbol}: {price}")
                    self._save_to_cache(symbol, price)
                    return price
                    
            except Exception as e:
                logger.warning(f"[{provider_name}] Failed for {symbol}: {e}")
                continue

        logger.error(f"[ERROR] No price available for {symbol}")
        
        # Last resort: return stale cache if available
        try:
            stale = redis_client.get(f"price:{symbol}")
            if stale:
                logger.warning(f"Returning stale price for {symbol}")
                return float(stale)
        except:
            pass
        
        return None
    async def get_batch_prices(
        self, 
        symbols: List[tuple[str, str]] = None, 
        force_refresh: bool = False
    ) -> Dict[str, Optional[float]]:
        """
        Get multiple prices efficiently with intelligent batching
        """
        # Handle missing symbols parameter
        if symbols is None:
            logger.warning("get_batch_prices called without symbols, returning empty dict")
            return {}
        
        # Handle empty symbols list
        if not symbols:
            logger.debug("get_batch_prices called with empty symbols list")
            return {}
        
        results = {}
        symbols_to_fetch = []
    
        
        # Check cache first
        if not force_refresh:
            for symbol, asset_type in symbols:
                cached = self._get_from_memory_cache(symbol)
                if cached:
                    results[symbol] = cached
                else:
                    cached = self._get_from_redis_cache(symbol)
                    if cached:
                        results[symbol] = cached
                        self.memory_cache[symbol] = (cached, datetime.utcnow())
                    else:
                        symbols_to_fetch.append((symbol, asset_type))
        else:
            symbols_to_fetch = symbols
        
        # Fetch remaining symbols
        if symbols_to_fetch:
            # Batch by provider capability
            # TwelveData and Finnhub support batch requests better
            
            # Split into chunks to respect rate limits
            chunk_size = 10
            for i in range(0, len(symbols_to_fetch), chunk_size):
                chunk = symbols_to_fetch[i:i+chunk_size]
                
                # Try to fetch chunk
                tasks = [
                    self.get_stock_price(symbol, force_refresh=True)
                    for symbol, _ in chunk
                ]
                
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for (symbol, _), price in zip(chunk, chunk_results):
                    if not isinstance(price, Exception):
                        results[symbol] = price
                    else:
                        results[symbol] = None
                
                # Small delay between chunks to avoid rate limits
                if i + chunk_size < len(symbols_to_fetch):
                    await asyncio.sleep(0.5)
        
        return results
    async def get_active_providers(self) -> dict:
        """Get status of all active providers"""
        active_providers = {}
        
        for provider_name, provider in self.providers.items():
            try:
                # Test each provider with a simple symbol
                if provider_name == DataProvider.COINGECKO:
                    # CoinGecko test with Bitcoin
                    price = await provider.get_price("bitcoin")
                else:
                    # Other providers test with AAPL
                    price = await provider.get_price("AAPL")
                
                active_providers[provider_name.value] = {
                    "status": "active" if price else "inactive",
                    "test_price": price
                }
            except Exception as e:
                active_providers[provider_name.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return active_providers
    async def get_price(
        self, 
        symbol: str, 
        asset_type: str, 
        force_refresh: bool = False
    ) -> Optional[float]:
        """Universal price getter"""
        asset_type_upper = asset_type.upper()
        
        if asset_type_upper == "STOCK":
            return await self.get_stock_price(symbol, force_refresh)
        elif asset_type_upper == "CRYPTO":
            return await self.get_crypto_price(symbol, force_refresh)
        elif asset_type_upper == "FOREX":
            return await self.get_forex_price(symbol, force_refresh)
        
        logger.warning(f"Unknown asset type: {asset_type}")
        return None

    async def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Optional[float]:
        """Get cryptocurrency price"""
        # Try different symbol formats for crypto
        symbol_variants = [
            symbol,
            f"{symbol}USD",
            f"{symbol}/USD", 
            f"{symbol}-USD",
            f"{symbol}USDT",
            f"{symbol}/USDT"
        ]
        
        if not force_refresh:
            # Check cache for any variant
            for variant in symbol_variants:
                cached = self._get_from_memory_cache(variant)
                if cached:
                    return cached
                cached = self._get_from_redis_cache(variant)
                if cached:
                    self.memory_cache[variant] = (cached, datetime.utcnow())
                    return cached

        # Try each symbol variant with providers
        for symbol_variant in symbol_variants:
            # Try TwelveData first for crypto
            price = await self._fetch_twelve_data(symbol_variant)
            if price:
                self._save_to_cache(symbol, price)  # Cache with original symbol
                return price
        
        return None

    async def get_forex_price(self, symbol: str, force_refresh: bool = False) -> Optional[float]:
        """Get forex price"""
        if not force_refresh:
            cached = self._get_from_memory_cache(symbol)
            if cached:
                return cached
            cached = self._get_from_redis_cache(symbol)
            if cached:
                self.memory_cache[symbol] = (cached, datetime.utcnow())
                return cached
        
        price = await self._fetch_twelve_data(symbol)
        if price:
            self._save_to_cache(symbol, price)
            return price
        
        return None

    # ---------------------------------------------------------
    # Provider Methods (unchanged from your original)
    # ---------------------------------------------------------
    async def _fetch_alpha_vantage(self, symbol: str) -> Optional[float]:
        """Fetch from Alpha Vantage"""
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE", 
            "symbol": symbol, 
            "apikey": self.alpha_vantage_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                
                quote = data.get("Global Quote", {})
                if "05. price" in quote:
                    return float(quote["05. price"])
                
                logger.debug(f"[AlphaVantage] No price found for {symbol}")
        except Exception as e:
            logger.warning(f"[AlphaVantage] Error for {symbol}: {e}")
        
        return None

    async def _fetch_finnhub(self, symbol: str) -> Optional[float]:
        """Fetch from Finnhub"""
        if not self.finnhub_key:
            return None
        
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol, "token": self.finnhub_key}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                
                if "c" in data and data["c"] > 0:
                    return float(data["c"])
                
                logger.debug(f"[Finnhub] No valid quote for {symbol}")
        except Exception as e:
            logger.warning(f"[Finnhub] Error for {symbol}: {e}")
        
        return None

    async def _fetch_twelve_data(self, symbol: str) -> Optional[float]:
        """Fetch from Twelve Data"""
        if not self.twelve_key:
            return None
        
        url = "https://api.twelvedata.com/price"
        params = {"symbol": symbol, "apikey": self.twelve_key}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                
                if "price" in data:
                    return float(data["price"])
                
                logger.debug(f"[TwelveData] No price field for {symbol}")
        except Exception as e:
            logger.warning(f"[TwelveData] Error for {symbol}: {e}")
        
        return None

    async def get_complete_quote(self, symbol: str, asset_type: str) -> Optional[dict]:
        """Get complete OHLC data"""
        price = await self.get_price(symbol, asset_type)
        if price is None or price <= 0:
            return None
            
        return {
            'close': price,
            'open': price,
            'high': price,
            'low': price,
            'volume': 0.0,
            'provider': 'aggregated'
        }

    async def get_quote(self, symbol: str) -> dict:
        """Return dict with bid, ask, last"""
        try:
            price = await self.get_stock_price(symbol)
            if price is None:
                return {}
            return {"bid": price, "ask": price, "last": price}
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {}


# Singleton instance
enhanced_market_service = MarketDataService()