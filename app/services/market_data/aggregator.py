from typing import List, Optional, Dict
from datetime import datetime
from app.services.market_data.base_provider import BaseMarketDataProvider
from app.services.market_data.providers.polygon_provider import PolygonProvider
from app.services.market_data.providers.alpha_vantage_provider import AlphaVantageProvider
from app.services.market_data.providers.binance_provider import BinanceProvider
from app.services.market_data.cache_service import CacheService
from app.schemas.quote import QuoteResponse, QuoteRequest
from app.schemas.candle import CandleResponse, CandleRequest
from app.constants.market_constants import AssetClass
from app.config.market_config import market_config
import logging
import asyncio

logger = logging.getLogger(__name__)

class MarketDataAggregator:
    """
    Orchestrates multiple data providers with:
    - Intelligent routing by asset class
    - Automatic fallback on failures
    - Response caching
    - Rate limiting
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseMarketDataProvider] = {}
        self.cache = CacheService()
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        if market_config.POLYGON_API_KEY:
            self.providers["polygon"] = PolygonProvider(
                market_config.POLYGON_API_KEY,
                market_config.POLYGON_BASE_URL
            )
        
        if market_config.ALPHA_VANTAGE_API_KEY:
            self.providers["alpha_vantage"] = AlphaVantageProvider(
                market_config.ALPHA_VANTAGE_API_KEY,
                market_config.ALPHA_VANTAGE_BASE_URL
            )
        
        if market_config.BINANCE_BASE_URL:
            self.providers["binance"] = BinanceProvider(
                "",  # No API key needed for public endpoints
                market_config.BINANCE_BASE_URL
            )
    
    def _get_providers_for_asset(self, asset_class: AssetClass) -> List[BaseMarketDataProvider]:
        """Get priority-ordered providers for asset class"""
        if asset_class == AssetClass.CRYPTO:
            provider_names = market_config.CRYPTO_PROVIDERS
        elif asset_class == AssetClass.FOREX:
            provider_names = market_config.FOREX_PROVIDERS
        else:
            provider_names = market_config.STOCK_PROVIDERS
        
        return [self.providers[name] for name in provider_names if name in self.providers]
    
    async def get_quote(self, symbol: str, asset_class: Optional[AssetClass] = None) -> QuoteResponse:
        """
        Get real-time quote with caching and fallback
        """
        # Check cache first
        cache_key = f"quote:{symbol}"
        cached = await self.cache.get(cache_key)
        if cached:
            return QuoteResponse(**cached)
        
        # Determine asset class if not provided
        if not asset_class:asset_class = self._detect_asset_class(symbol)
        
        providers = self._get_providers_for_asset(asset_class)
        
        # Try providers in order with fallback
        for provider in providers:
            try:
                quote = await provider.get_quote(symbol)
                # Cache successful response
                await self.cache.set(
                    cache_key,
                    quote.model_dump(),
                    ttl=market_config.QUOTE_CACHE_TTL
                )
                return quote
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for {symbol}: {e}")
                continue
        
        raise Exception(f"All providers failed for symbol {symbol}")
    
    async def get_quotes(self, request: QuoteRequest) -> List[QuoteResponse]:
        """Get multiple quotes (batch)"""
        tasks = [self.get_quote(symbol, request.asset_class) for symbol in request.symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in results if isinstance(r, QuoteResponse)]
    
    async def get_candles(self, request: CandleRequest) -> List[CandleResponse]:
        """Get historical candle data"""
        cache_key = f"candles:{request.symbol}:{request.timeframe.value}:{request.limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [CandleResponse(**c) for c in cached]
        
        asset_class = self._detect_asset_class(request.symbol)
        providers = self._get_providers_for_asset(asset_class)
        
        for provider in providers:
            try:
                candles = await provider.get_candles(
                    request.symbol,
                    request.timeframe,
                    request.limit,
                    request.from_date,
                    request.to_date
                )
                
                # Cache candles
                await self.cache.set(
                    cache_key,
                    [c.model_dump() for c in candles],
                    ttl=market_config.CANDLE_CACHE_TTL
                )
                return candles
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for candles: {e}")
                continue
        
        raise Exception(f"All providers failed for candles {request.symbol}")
    
    def _detect_asset_class(self, symbol: str) -> AssetClass:
        """Detect asset class from symbol"""
        symbol_upper = symbol.upper()
        
        # Crypto detection
        if symbol_upper in ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE"]:
            return AssetClass.CRYPTO
        if "USD" in symbol_upper and len(symbol_upper) <= 7:
            return AssetClass.CRYPTO
        
        # Forex detection (contains slash)
        if "/" in symbol:
            return AssetClass.FOREX
        
        # Default to stock
        return AssetClass.STOCK
    
    async def search_symbols(self, query: str, asset_class: Optional[AssetClass] = None) -> List[Dict]:
        """Search for symbols across providers"""
        if asset_class:
            providers = self._get_providers_for_asset(asset_class)
        else:
            providers = list(self.providers.values())
        
        results = []
        for provider in providers:
            try:
                provider_results = await provider.search_symbol(query)
                results.extend(provider_results)
            except Exception as e:
                logger.warning(f"Search failed on {provider.name}: {e}")
        
        return results[:20]  # Limit results
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        health = {}
        for name, provider in self.providers.items():
            health[name] = await provider.is_healthy()
        return health

# Singleton instance
market_data_service = MarketDataAggregator()