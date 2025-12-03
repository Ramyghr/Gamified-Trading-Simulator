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
    
    async def get_enhanced_quotes(self, symbol: str, asset_type: str) -> List[QuoteResponse]:
        """Get quotes from all available providers for a symbol"""
        try:
            # Determine which providers support this asset type
            supported_providers = self._get_providers_for_asset_type(asset_type)
            
            # Get quotes from all supported providers concurrently
            tasks = []
            for provider in supported_providers:
                try:
                    if asset_type == AssetClass.STOCK:
                        task = self.market_data_service.get_stock_quote(symbol, provider)
                    elif asset_type == AssetClass.CRYPTO:
                        task = self.market_data_service.get_crypto_quote(symbol, provider)
                    elif asset_type == AssetClass.FOREX:
                        # For forex, we need to parse the pair
                        if '/' in symbol:
                            base, quote = symbol.split('/')
                            task = self.market_data_service.get_forex_quote(base, quote, provider)
                        else:
                            continue
                    elif asset_type == AssetClass.INDEX:
                        task = self.market_data_service.get_index_quote(symbol, provider)
                    else:
                        task = self.market_data_service.get_quote(symbol, provider)
                    
                    tasks.append(task)
                except Exception as e:
                    logger.debug(f"Provider {provider} not available for {symbol}: {e}")
                    continue
            
            # Execute all tasks
            results = await gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            quotes = []
            for i, result in enumerate(results):
                if isinstance(result, QuoteResponse):
                    quotes.append(result)
                elif isinstance(result, Exception):
                    logger.debug(f"Failed to get quote from {supported_providers[i]}: {result}")
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting enhanced quotes for {symbol}: {e}")
            return []
    
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