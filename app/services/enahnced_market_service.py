"""
Enhanced Market Data Service for Watchlist
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.quote import QuoteResponse
from app.services.market_data_service import MarketDataService
from app.constants.market_constants import AssetClass, DataProvider
import logging
from asyncio import gather

logger = logging.getLogger(__name__)


class EnhancedMarketDataService:
    """Enhanced market data service with multi-provider support"""
    
    def __init__(self, market_data_service: MarketDataService):
        self.market_data_service = market_data_service
        # Cache for provider health status with TTL
        self.provider_health_cache = {}
        self.health_cache_ttl = 300  # 5 minutes in seconds
    
    async def get_enhanced_quotes(self, symbol: str, asset_type: str) -> List[QuoteResponse]:
        """Get quotes from all available providers for a symbol with robust error handling"""
        try:
            logger.info(f"Fetching enhanced quotes for {symbol} ({asset_type})")
            
            # Normalize symbol format for the asset type
            normalized_symbol = self._normalize_symbol(symbol, asset_type)
            logger.debug(f"Normalized {symbol} -> {normalized_symbol} for {asset_type}")
            
            # Determine which providers support this asset type
            supported_providers = self._get_providers_for_asset_type(asset_type)
            logger.debug(f"Supported providers for {asset_type}: {[p.value for p in supported_providers]}")
            
            # Filter out unhealthy providers
            healthy_providers = []
            for provider in supported_providers:
                is_healthy = await self._is_provider_healthy_cached(provider)
                if is_healthy:
                    healthy_providers.append(provider)
                else:
                    logger.warning(f"Provider {provider.value} is unhealthy, skipping")
            
            if not healthy_providers:
                logger.error(f"No healthy providers available for {symbol} ({asset_type})")
                return []
            
            logger.info(f"Using {len(healthy_providers)} healthy providers: {[p.value for p in healthy_providers]}")
            
            # Prepare tasks for healthy providers
            tasks = []
            provider_tasks_map = {}  # Map provider to task index
            
            for provider in healthy_providers:
                try:
                    # Map symbol to provider-specific format
                    provider_symbol = self._map_symbol_to_provider_format(normalized_symbol, asset_type, provider)
                    
                    if asset_type == AssetClass.STOCK:
                        task = self.market_data_service.get_stock_quote(provider_symbol, provider)
                    elif asset_type == AssetClass.CRYPTO:
                        task = self.market_data_service.get_crypto_quote(provider_symbol, provider)
                    elif asset_type == AssetClass.FOREX:
                        # Parse forex pair
                        if '/' in provider_symbol:
                            base, quote = provider_symbol.split('/')
                            task = self.market_data_service.get_forex_quote(base, quote, provider)
                        else:
                            logger.warning(f"Invalid forex symbol format for {provider_symbol} on {provider.value}")
                            continue
                    elif asset_type == AssetClass.INDEX:
                        task = self.market_data_service.get_index_quote(provider_symbol, provider)
                    else:
                        task = self.market_data_service.get_quote(provider_symbol, provider)
                    
                    tasks.append(task)
                    provider_tasks_map[len(tasks) - 1] = provider.value
                    
                except Exception as e:
                    logger.warning(f"Failed to prepare task for {provider.value}: {str(e)[:100]}")
                    continue
            
            if not tasks:
                logger.error(f"No valid tasks created for {symbol}")
                return []
            
            # Execute all tasks concurrently with timeout
            quotes = []
            failed_providers = []
            
            try:
                import asyncio
                results = await asyncio.gather(*tasks, return_exceptions=True, timeout=30.0)
                
                # Process results
                for i, result in enumerate(results):
                    provider_name = provider_tasks_map.get(i, "unknown")
                    
                    if isinstance(result, QuoteResponse):
                        # Success
                        quotes.append(result)
                        logger.info(f"✓ {provider_name} returned quote for {symbol}")
                        
                    elif isinstance(result, Exception):
                        # Failure
                        failed_providers.append(provider_name)
                        error_msg = str(result)
                        if hasattr(result, 'status_code'):
                            error_msg += f" (Status: {result.status_code})"
                        logger.warning(f"✗ {provider_name} failed: {error_msg[:150]}")
                        
                        # Check for specific errors
                        if "404" in error_msg or "not found" in error_msg.lower():
                            logger.debug(f"Symbol {symbol} may not exist on {provider_name}")
                        elif "429" in error_msg or "rate limit" in error_msg.lower():
                            logger.warning(f"Rate limit hit on {provider_name}")
                            # Mark provider as temporarily unhealthy
                            await self._mark_provider_unhealthy(provider_name)
                        elif "invalid symbol" in error_msg.lower():
                            logger.debug(f"Invalid symbol format for {provider_name}")
                    else:
                        # Unexpected result type
                        logger.error(f"Unexpected result type from {provider_name}: {type(result)}")
                        failed_providers.append(provider_name)
                        
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching quotes for {symbol} from {len(tasks)} providers")
                # Mark all providers in this batch as potentially slow
                for provider_name in provider_tasks_map.values():
                    await self._mark_provider_slow(provider_name)
            
            # Log summary
            if quotes:
                logger.info(f"Successfully retrieved {len(quotes)} quotes for {symbol} ({asset_type})")
            else:
                logger.error(f"All providers failed for {symbol} ({asset_type}): {failed_providers}")
                
                # Provide helpful suggestions
                suggestions = []
                if asset_type == AssetClass.CRYPTO:
                    suggestions.append("Try BTC/USDT instead of BTCUSDT")
                    suggestions.append("Ensure crypto symbol uses correct format (e.g., BTC-USD, BTC_USDT)")
                elif asset_type == AssetClass.FOREX:
                    suggestions.append("Use format like EUR/USD not EURUSD")
                elif asset_type == AssetClass.COMMODITY:
                    suggestions.append("Use symbols like XAU/USD, XAG/USD, CL, NG")
                
                if suggestions:
                    logger.info(f"Suggestions for {asset_type}: {', '.join(suggestions)}")
            
            return quotes
            
        except Exception as e:
            logger.error(f"Critical error in get_enhanced_quotes for {symbol}: {str(e)}", exc_info=True)
            return []
    
    def _normalize_symbol(self, symbol: str, asset_type: str) -> str:
        """Normalize symbol to standard format based on asset type"""
        if not symbol or not isinstance(symbol, str):
            return symbol
            
        symbol = symbol.strip().upper()
        
        if asset_type == AssetClass.CRYPTO:
            # Handle common crypto formats
            if 'USDT' in symbol and '/' not in symbol:
                # Convert BTCUSDT -> BTC/USDT
                base = symbol.replace('USDT', '')
                if base and base != symbol:
                    return f"{base}/USDT"
            elif '-' in symbol and '/' not in symbol:
                # Convert BTC-USD -> BTC/USD
                return symbol.replace('-', '/')
            elif '_' in symbol and '/' not in symbol:
                # Convert BTC_USDT -> BTC/USDT
                return symbol.replace('_', '/')
            
        elif asset_type == AssetClass.FOREX:
            # Handle forex formats
            if len(symbol) == 6 and '/' not in symbol:
                # Convert EURUSD -> EUR/USD
                return f"{symbol[:3]}/{symbol[3:]}"
                
        elif asset_type == AssetClass.COMMODITY:
            # Handle commodity formats
            commodities = {
                'GOLD': 'XAU/USD',
                'SILVER': 'XAG/USD',
                'OIL': 'CL',
                'CRUDEOIL': 'CL',
                'NATURALGAS': 'NG',
                'COPPER': 'HG'
            }
            if symbol in commodities:
                return commodities[symbol]
        
        return symbol
    
    def _map_symbol_to_provider_format(self, symbol: str, asset_type: str, provider: DataProvider) -> str:
        """Map normalized symbol to provider-specific format"""
        if asset_type == AssetClass.CRYPTO:
            if provider == DataProvider.BINANCE:
                # Binance uses format like BTCUSDT (no separator)
                return symbol.replace('/', '')
            elif provider == DataProvider.COINGECKO:
                # CoinGecko uses format like bitcoin
                if symbol == 'BTC/USDT':
                    return 'bitcoin'
                elif symbol == 'ETH/USDT':
                    return 'ethereum'
                # Return lowercase version for other cryptos
                base = symbol.split('/')[0] if '/' in symbol else symbol
                return base.lower()
            elif provider == DataProvider.TWELVE_DATA:
                # Twelve Data uses format like BTC/USD
                if '/USDT' in symbol:
                    return symbol.replace('USDT', 'USD')
                return symbol
            elif provider == DataProvider.ALPHA_VANTAGE:
                # Alpha Vantage uses format like BTC
                return symbol.split('/')[0] if '/' in symbol else symbol
        
        elif asset_type == AssetClass.FOREX:
            if provider in [DataProvider.ALPHA_VANTAGE, DataProvider.TWELVE_DATA]:
                # These providers typically use EUR/USD format
                return symbol
            elif provider == DataProvider.FINNHUB:
                # Finnhub uses format like OANDA:EUR_USD
                return f"OANDA:{symbol.replace('/', '_')}"
        
        elif asset_type == AssetClass.COMMODITY:
            if provider == DataProvider.TWELVE_DATA:
                # Twelve Data uses format like XAU/USD
                return symbol
            elif provider == DataProvider.ALPHA_VANTAGE:
                # Alpha Vantage uses special symbols
                if symbol == 'XAU/USD':
                    return 'XAU'
                elif symbol == 'XAG/USD':
                    return 'XAG'
        
        # Default: return symbol as-is
        return symbol
    
    async def _is_provider_healthy_cached(self, provider: DataProvider) -> bool:
        """Check provider health with caching"""
        from time import time
        
        cache_key = provider.value
        current_time = time()
        
        # Check cache first
        if cache_key in self.provider_health_cache:
            health_data = self.provider_health_cache[cache_key]
            if current_time - health_data['timestamp'] < self.health_cache_ttl:
                return health_data['healthy']
        
        # Perform health check
        try:
            is_healthy = await self.market_data_service.is_provider_healthy(provider)
            
            # Cache the result
            self.provider_health_cache[cache_key] = {
                'healthy': is_healthy,
                'timestamp': current_time
            }
            
            if not is_healthy:
                logger.warning(f"Provider {provider.value} failed health check")
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Error checking health for {provider.value}: {e}")
            # Cache negative result for shorter time on error
            self.provider_health_cache[cache_key] = {
                'healthy': False,
                'timestamp': current_time
            }
            return False
    
    async def _mark_provider_unhealthy(self, provider_name: str):
        """Mark a provider as unhealthy temporarily"""
        from time import time
        
        # Find provider enum from name
        provider = None
        for p in DataProvider:
            if p.value == provider_name:
                provider = p
                break
        
        if provider:
            self.provider_health_cache[provider.value] = {
                'healthy': False,
                'timestamp': time()
            }
            logger.warning(f"Marked {provider_name} as unhealthy for {self.health_cache_ttl} seconds")
    
    async def _mark_provider_slow(self, provider_name: str):
        """Mark a provider as slow (but not completely unhealthy)"""
        # Could implement different logic here
        # For now, just log it
        logger.debug(f"Marked {provider_name} as slow to respond")

    # The rest of your methods remain the same...
    async def get_batch_enhanced_quotes(self, symbols: List[tuple]) -> Dict[str, List[QuoteResponse]]:
        """Get enhanced quotes for multiple symbols"""
        results = {}
        
        for symbol, asset_type in symbols:
            quotes = await self.get_enhanced_quotes(symbol, asset_type)
            results[symbol] = quotes
        
        return results
    
    async def search_symbols(self, query: str, asset_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search symbols across all providers"""
        try:
            # Get all available providers
            providers = [DataProvider.POLYGON, DataProvider.ALPHA_VANTAGE, DataProvider.TWELVE_DATA]
            
            if asset_type == AssetClass.CRYPTO:
                providers.extend([DataProvider.BINANCE, DataProvider.COINGECKO])
            
            # Search from each provider
            all_results = []
            for provider in providers:
                try:
                    results = await self.market_data_service.search_symbol(query, provider)
                    for result in results:
                        result['provider'] = provider.value
                        all_results.append(result)
                except Exception as e:
                    logger.debug(f"Search failed for provider {provider}: {e}")
            
            # Remove duplicates and limit results
            seen_symbols = set()
            unique_results = []
            
            for result in all_results:
                symbol_key = f"{result.get('symbol')}_{result.get('asset_type', 'stock')}"
                if symbol_key not in seen_symbols:
                    seen_symbols.add(symbol_key)
                    unique_results.append(result)
                
                if len(unique_results) >= limit:
                    break
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            return []
    
    def _get_providers_for_asset_type(self, asset_type: str) -> List[DataProvider]:
        """Get available providers for an asset type"""
        provider_map = {
            AssetClass.STOCK: [
                DataProvider.POLYGON,
                DataProvider.ALPHA_VANTAGE,
                DataProvider.TWELVE_DATA,
                DataProvider.FINNHUB
            ],
            AssetClass.CRYPTO: [
                DataProvider.BINANCE,
                DataProvider.COINGECKO,
                DataProvider.TWELVE_DATA,
                DataProvider.ALPHA_VANTAGE
            ],
            AssetClass.FOREX: [
                DataProvider.TWELVE_DATA,
                DataProvider.ALPHA_VANTAGE,
                DataProvider.FINNHUB
            ],
            AssetClass.INDEX: [
                DataProvider.TWELVE_DATA,
                DataProvider.ALPHA_VANTAGE
            ],
            AssetClass.COMMODITY: [
                DataProvider.TWELVE_DATA,
                DataProvider.ALPHA_VANTAGE
            ]
        }
        
        return provider_map.get(asset_type, [DataProvider.ALPHA_VANTAGE])
    
    async def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all market data providers"""
        providers = [
            DataProvider.POLYGON,
            DataProvider.ALPHA_VANTAGE,
            DataProvider.BINANCE,
            DataProvider.COINGECKO,
            DataProvider.FINNHUB,
            DataProvider.TWELVE_DATA
        ]
        
        status = {}
        for provider in providers:
            try:
                is_healthy = await self.market_data_service.is_provider_healthy(provider)
                status[provider.value] = is_healthy
            except Exception as e:
                logger.error(f"Error checking provider {provider}: {e}")
                status[provider.value] = False
        
        return status


# Singleton instance
enhanced_market_service = EnhancedMarketDataService(MarketDataService())