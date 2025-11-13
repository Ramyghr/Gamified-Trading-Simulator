"""
Enhanced Market Data Service with intelligent caching and provider rotation
Supports multi-provider fallback for stocks, crypto, forex, and commodities
"""
import httpx
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException
import asyncio
import os
import logging
from decimal import Decimal
from app.schemas.quote import QuoteResponse
from app.config.redis_client import redis_client
from app.services.market_data.providers.alpha_vantage_provider import AlphaVantageProvider
from app.services.market_data.providers.binance_provider import BinanceProvider
from app.services.market_data.providers.coingecko_provider import CoinGeckoProvider
from app.services.market_data.providers.finnhub_provider import FinnhubProvider
from app.services.market_data.providers.twelve_data_provider import TwelveDataProvider
from app.services.market_data.providers.polygon_provider import PolygonProvider
from app.constants.market_constants import AssetClass, DataProvider
from asyncio import gather

logger = logging.getLogger(__name__)


class MarketDataService:
    """Enhanced service with smart caching and provider fallback"""

    def __init__(self):
        # API Keys
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "")
        self.twelve_key = os.getenv("TWELVE_DATA_API_KEY", "")
        self.polygon_key = os.getenv("POLYGON_API_KEY", "")

        # Multi-layer cache
        self.memory_cache: Dict[str, tuple[float, datetime]] = {}
        self.cache_ttl = timedelta(seconds=15)  # 15 second memory cache
        
        # Rate limiting tracking
        self.provider_calls = {}
        self.rate_limits = {
            "alpha_vantage": {"calls": 0, "limit": 5, "window": 60},
            "finnhub": {"calls": 0, "limit": 60, "window": 60},
            "twelve_data": {"calls": 0, "limit": 8, "window": 60},
            "binance": {"calls": 0, "limit": 1200, "window": 60},
            "coingecko": {"calls": 0, "limit": 50, "window": 60},
            "polygon": {"calls": 0, "limit": 100, "window": 60},
        }
        
        # Provider instances by asset class
        self.providers_by_asset = {
            AssetClass.STOCK: [],
            AssetClass.CRYPTO: [],
            AssetClass.FOREX: [],
            AssetClass.COMMODITY: [],
            AssetClass.INDEX: []
        }
        
        # Initialize providers
        self._initialize_providers()
        
        logger.info(f"Initialized {len(self.providers_by_asset)} asset classes")
        for asset_class, providers in self.providers_by_asset.items():
            logger.info(f"  {asset_class}: {len(providers)} providers")

    def _initialize_providers(self):
        """Initialize all available providers and categorize by asset class"""
        
        # 1. BINANCE - FREE, NO API KEY, CRYPTO ONLY
        try:
            binance = BinanceProvider(
                api_key="", 
                base_url="https://api.binance.com"
            )
            self.providers_by_asset[AssetClass.CRYPTO].append({
                "name": "binance",
                "provider": binance,
                "priority": 1  # Highest priority for crypto
            })
            logger.info("✓ Binance initialized (FREE, crypto)")
        except Exception as e:
            logger.warning(f"✗ Binance failed: {e}")
        
        # 2. COINGECKO - FREE, NO API KEY, CRYPTO ONLY
        try:
            coingecko = CoinGeckoProvider(
                api_key="", 
                base_url="https://api.coingecko.com/api/v3"
            )
            self.providers_by_asset[AssetClass.CRYPTO].append({
                "name": "coingecko",
                "provider": coingecko,
                "priority": 2
            })
            logger.info("✓ CoinGecko initialized (FREE, crypto)")
        except Exception as e:
            logger.warning(f"✗ CoinGecko failed: {e}")
        
        # 3. TWELVE DATA - Stocks, Forex, Crypto, Index, Commodities
        if self.twelve_key:
            try:
                twelve = TwelveDataProvider(
                    api_key=self.twelve_key, 
                    base_url="https://api.twelvedata.com"
                )
                for asset_class in [AssetClass.STOCK, AssetClass.FOREX, 
                                   AssetClass.CRYPTO, AssetClass.COMMODITY, AssetClass.INDEX]:
                    self.providers_by_asset[asset_class].append({
                        "name": "twelve_data",
                        "provider": twelve,
                        "priority": 3
                    })
                logger.info("✓ TwelveData initialized (stocks, forex, crypto, commodities)")
            except Exception as e:
                logger.warning(f"✗ TwelveData failed: {e}")
        
        # 4. FINNHUB - Stocks, Forex, Crypto
        if self.finnhub_key:
            try:
                finnhub = FinnhubProvider(
                    api_key=self.finnhub_key, 
                    base_url="https://finnhub.io/api/v1"
                )
                for asset_class in [AssetClass.STOCK, AssetClass.FOREX, AssetClass.CRYPTO]:
                    self.providers_by_asset[asset_class].append({
                        "name": "finnhub",
                        "provider": finnhub,
                        "priority": 4
                    })
                logger.info("✓ Finnhub initialized (stocks, forex, crypto)")
            except Exception as e:
                logger.warning(f"✗ Finnhub failed: {e}")
        
        # 5. POLYGON - Stocks, Forex, Crypto
        # if self.polygon_key:
        #     try:
        #         polygon = PolygonProvider(
        #             api_key=self.polygon_key,
        #             base_url="https://api.polygon.io"
        #         )
        #         for asset_class in [AssetClass.STOCK, AssetClass.FOREX, AssetClass.CRYPTO]:
        #             self.providers_by_asset[asset_class].append({
        #                 "name": "polygon",
        #                 "provider": polygon,
        #                 "priority": 5
        #             })
        #         logger.info("✓ Polygon initialized (stocks, forex, crypto)")
        #     except Exception as e:
        #         logger.warning(f"✗ Polygon failed: {e}")
        
        # if self.polygon_key:
        #     try:
        #         polygon = PolygonProvider(
        #             api_key=self.polygon_key,
        #             base_url="https://api.polygon.io"
        #         )
        #         # ONLY stocks and forex - remove crypto
        #         for asset_class in [AssetClass.STOCK, AssetClass.FOREX]:
        #             self.providers_by_asset[asset_class].append({
        #                 "name": "polygon",
        #                 "provider": polygon,
        #                 "priority": 5
        #             })
        #         logger.info("✓ Polygon initialized (stocks, forex only - no crypto)")
        #     except Exception as e:
        #         logger.warning(f"✗ Polygon failed: {e}")
        # 6. ALPHA VANTAGE - Stocks, Forex, Crypto, Commodities
        try:
            alpha = AlphaVantageProvider(
                api_key=self.alpha_vantage_key,
                base_url="https://www.alphavantage.co"
            )
            for asset_class in [AssetClass.STOCK, AssetClass.FOREX, 
                               AssetClass.CRYPTO, AssetClass.COMMODITY]:
                self.providers_by_asset[asset_class].append({
                    "name": "alpha_vantage",
                    "provider": alpha,
                    "priority": 6  # Lowest priority (rate limited)
                })
            logger.info("✓ AlphaVantage initialized (stocks, forex, crypto, commodities)")
        except Exception as e:
            logger.warning(f"✗ AlphaVantage failed: {e}")
        
        # Sort providers by priority for each asset class
        for asset_class in self.providers_by_asset:
            self.providers_by_asset[asset_class].sort(key=lambda x: x["priority"])

    # ---------------------------------------------------------
    # Cache Layer
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
        self.memory_cache[symbol] = (price, datetime.utcnow())
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
        
        return len(self.provider_calls[provider_name]) < limit_info["limit"]

    def _record_provider_call(self, provider_name: str):
        """Record a provider API call"""
        if provider_name not in self.provider_calls:
            self.provider_calls[provider_name] = []
        self.provider_calls[provider_name].append(datetime.utcnow())

    # ---------------------------------------------------------
    # Smart Provider Selection with Fallback
    # ---------------------------------------------------------
    async def _get_price_with_fallback(
        self, 
        symbol: str, 
        asset_type: str,
        force_refresh: bool = False
    ) -> Optional[float]:
        """
        Get price with intelligent provider fallback
        Tries providers in priority order until one succeeds
        """
        # Normalize asset type
        asset_class = self._normalize_asset_type(asset_type)
        
        # Check cache first
        if not force_refresh:
            cached = self._get_from_memory_cache(symbol)
            if cached:
                logger.debug(f"[CACHE HIT] {symbol}: {cached}")
                return cached
            
            cached = self._get_from_redis_cache(symbol)
            if cached:
                logger.debug(f"[REDIS HIT] {symbol}: {cached}")
                self.memory_cache[symbol] = (cached, datetime.utcnow())
                return cached

        # Get providers for this asset class
        providers = self.providers_by_asset.get(asset_class, [])
        
        if not providers:
            logger.error(f"No providers available for {asset_class}")
            return None

        # Try each provider in priority order
        for provider_info in providers:
            provider_name = provider_info["name"]
            provider = provider_info["provider"]
            
            # Check rate limit
            if not self._can_call_provider(provider_name):
                logger.debug(f"[{provider_name}] Rate limit reached, skipping")
                continue
            
            try:
                self._record_provider_call(provider_name)
                
                # Try to get price from provider
                if hasattr(provider, 'get_price'):
                    price = await provider.get_price(symbol)
                else:
                    quote = await provider.get_quote(symbol)
                    price = quote.close if quote else None
                
                if price and price > 0:
                    logger.info(f"[{provider_name}] ✓ {symbol}: ${price:.2f}")
                    self._save_to_cache(symbol, price)
                    return price
                else:
                    logger.debug(f"[{provider_name}] No valid price for {symbol}")
                    
            except Exception as e:
                logger.warning(f"[{provider_name}] ✗ Error for {symbol}: {str(e)[:100]}")
                continue

        # All providers failed
        logger.error(f"[ALL PROVIDERS FAILED] {symbol} ({asset_type})")
        
        # Last resort: return stale cache
        try:
            stale = redis_client.get(f"price:{symbol}")
            if stale:
                logger.warning(f"Returning stale cache for {symbol}")
                return float(stale)
        except:
            pass
        
        return None

    def _normalize_asset_type(self, asset_type: str) -> AssetClass:
        """Normalize asset type string to AssetClass enum"""
        asset_type_upper = asset_type.upper()
        
        asset_map = {
            "STOCK": AssetClass.STOCK,
            "STOCKS": AssetClass.STOCK,
            "EQUITY": AssetClass.STOCK,
            "CRYPTO": AssetClass.CRYPTO,
            "CRYPTOCURRENCY": AssetClass.CRYPTO,
            "FOREX": AssetClass.FOREX,
            "FX": AssetClass.FOREX,
            "CURRENCY": AssetClass.FOREX,
            "COMMODITY": AssetClass.COMMODITY,
            "COMMODITIES": AssetClass.COMMODITY,
            "INDEX": AssetClass.INDEX,
            "INDICES": AssetClass.INDEX,
        }
        
        return asset_map.get(asset_type_upper, AssetClass.STOCK)

    # ---------------------------------------------------------
    # Public API Methods
    # ---------------------------------------------------------
    async def get_price(
        self, 
        symbol: str, 
        asset_type: str, 
        force_refresh: bool = False
    ) -> Optional[float]:
        """Universal price getter with fallback"""
        return await self._get_price_with_fallback(symbol, asset_type, force_refresh)

    async def get_stock_price(self, symbol: str, force_refresh: bool = False) -> Optional[float]:
        """Get stock price"""
        return await self._get_price_with_fallback(symbol, "STOCK", force_refresh)

    async def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Optional[float]:
        """Get crypto price"""
        return await self._get_price_with_fallback(symbol, "CRYPTO", force_refresh)

    async def get_forex_price(self, symbol: str, force_refresh: bool = False) -> Optional[float]:
        """Get forex price"""
        return await self._get_price_with_fallback(symbol, "FOREX", force_refresh)

    async def get_batch_prices(
        self, 
        symbols: List[Tuple[str, str]] = None, 
        force_refresh: bool = False
    ) -> Dict[str, Optional[float]]:
        """
        Get multiple prices efficiently with intelligent batching and fallback
        
        Args:
            symbols: List of (symbol, asset_type) tuples
            force_refresh: Skip cache if True
            
        Returns:
            Dict mapping symbol to price
        """
        if symbols is None or not symbols:
            logger.warning("get_batch_prices called without symbols")
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
            # Group by asset type for efficient provider usage
            by_asset_type = {}
            for symbol, asset_type in symbols_to_fetch:
                asset_class = self._normalize_asset_type(asset_type)
                if asset_class not in by_asset_type:
                    by_asset_type[asset_class] = []
                by_asset_type[asset_class].append(symbol)
            
            # Process each asset type group
            tasks = []
            for asset_class, symbol_list in by_asset_type.items():
                for symbol in symbol_list:
                    tasks.append(
                        self._get_price_with_fallback(
                            symbol, 
                            asset_class.value, 
                            force_refresh=True
                        )
                    )
            
            # Execute all tasks concurrently
            prices = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results back to symbols
            task_idx = 0
            for asset_class, symbol_list in by_asset_type.items():
                for symbol in symbol_list:
                    price = prices[task_idx]
                    if not isinstance(price, Exception):
                        results[symbol] = price
                    else:
                        logger.error(f"Exception for {symbol}: {price}")
                        results[symbol] = None
                    task_idx += 1
        
        return results

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

    async def get_active_providers(self) -> dict:
        """Get status of all active providers"""
        active_providers = {}
        
        for asset_class, provider_list in self.providers_by_asset.items():
            for provider_info in provider_list:
                provider_name = provider_info["name"]
                provider = provider_info["provider"]
                
                if provider_name not in active_providers:
                    try:
                        is_healthy = await provider.is_healthy()
                        active_providers[provider_name] = {
                            "status": "active" if is_healthy else "inactive",
                            "asset_classes": [asset_class.value],
                            "priority": provider_info["priority"]
                        }
                    except Exception as e:
                        active_providers[provider_name] = {
                            "status": "error",
                            "error": str(e)[:100],
                            "asset_classes": [asset_class.value]
                        }
                else:
                    # Add asset class to existing entry
                    active_providers[provider_name]["asset_classes"].append(asset_class.value)
        
        return active_providers


# Singleton instance
enhanced_market_service = MarketDataService()