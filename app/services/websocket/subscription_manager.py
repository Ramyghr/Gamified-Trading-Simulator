"""
Manages WebSocket subscriptions across multiple providers
Handles subscription lifecycle and optimization
"""
import asyncio
from typing import Dict, Set, List, Optional
from collections import defaultdict
from app.constants.market_constants import AssetClass
import logging

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """
    Manages symbol subscriptions across providers
    Optimizes connections and prevents duplicate subscriptions
    """
    
    def __init__(self):
        # symbol -> set of connection_ids
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # connection_id -> set of symbols
        self.connection_symbols: Dict[str, Set[str]] = defaultdict(set)
        
        # symbol -> provider
        self.symbol_providers: Dict[str, str] = {}
        
        # Provider-specific subscriptions
        self.provider_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Active WebSocket connections per provider
        self.active_connections: Dict[str, bool] = {}
        
        self.lock = asyncio.Lock()
    
    async def subscribe(self, connection_id: str, symbols: List[str]) -> Dict[str, List[str]]:
        """
        Subscribe connection to symbols
        Returns dict of provider -> symbols that need to be subscribed
        """
        async with self.lock:
            new_subscriptions = defaultdict(list)
            
            for symbol in symbols:
                # Add to connection's symbols
                self.connection_symbols[connection_id].add(symbol)
                
                # Check if this is a new symbol subscription
                is_new_symbol = len(self.subscriptions[symbol]) == 0
                
                # Add connection to symbol's subscribers
                self.subscriptions[symbol].add(connection_id)
                
                if is_new_symbol:
                    # Determine provider for this symbol
                    provider = self._determine_provider(symbol)
                    self.symbol_providers[symbol] = provider
                    self.provider_subscriptions[provider].add(symbol)
                    
                    # Add to new subscriptions
                    new_subscriptions[provider].append(symbol)
                    
                    logger.info(f"New subscription: {symbol} via {provider}")
            
            return dict(new_subscriptions)
    
    async def unsubscribe(self, connection_id: str, symbols: List[str]) -> Dict[str, List[str]]:
        """
        Unsubscribe connection from symbols
        Returns dict of provider -> symbols that can be unsubscribed
        """
        async with self.lock:
            removed_subscriptions = defaultdict(list)
            
            for symbol in symbols:
                # Remove from connection's symbols
                self.connection_symbols[connection_id].discard(symbol)
                
                # Remove connection from symbol's subscribers
                if symbol in self.subscriptions:
                    self.subscriptions[symbol].discard(connection_id)
                    
                    # If no more subscribers, remove from provider
                    if len(self.subscriptions[symbol]) == 0:
                        provider = self.symbol_providers.get(symbol)
                        if provider:
                            self.provider_subscriptions[provider].discard(symbol)
                            removed_subscriptions[provider].append(symbol)
                            
                            logger.info(f"Removed subscription: {symbol} from {provider}")
                        
                        # Clean up
                        del self.subscriptions[symbol]
                        del self.symbol_providers[symbol]
            
            return dict(removed_subscriptions)
    
    async def unsubscribe_connection(self, connection_id: str) -> Dict[str, List[str]]:
        """
        Unsubscribe all symbols for a connection
        Returns dict of provider -> symbols that can be unsubscribed
        """
        symbols = list(self.connection_symbols.get(connection_id, set()))
        
        if symbols:
            logger.info(f"Unsubscribing connection {connection_id} from {len(symbols)} symbols")
            return await self.unsubscribe(connection_id, symbols)
        
        # Clean up connection
        if connection_id in self.connection_symbols:
            del self.connection_symbols[connection_id]
        
        return {}
    
    def get_subscribers(self, symbol: str) -> Set[str]:
        """Get all connection IDs subscribed to a symbol"""
        return self.subscriptions.get(symbol, set()).copy()
    
    def get_connection_symbols(self, connection_id: str) -> Set[str]:
        """Get all symbols a connection is subscribed to"""
        return self.connection_symbols.get(connection_id, set()).copy()
    
    def get_provider_symbols(self, provider: str) -> Set[str]:
        """Get all symbols subscribed via a provider"""
        return self.provider_subscriptions.get(provider, set()).copy()
    
    def get_all_subscribed_symbols(self) -> List[str]:
        """Get list of all subscribed symbols"""
        return list(self.subscriptions.keys())
    
    def get_subscription_count(self, symbol: str) -> int:
        """Get number of subscribers for a symbol"""
        return len(self.subscriptions.get(symbol, set()))
    
    def get_total_subscriptions(self) -> int:
        """Get total number of unique symbols subscribed"""
        return len(self.subscriptions)
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return len(self.connection_symbols)
    
    def _determine_provider(self, symbol: str) -> str:
        """Determine which provider to use for a symbol"""
        symbol_upper = symbol.upper()
        
        # Crypto symbols
        crypto_symbols = ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOGE", "DOT", "MATIC", "AVAX"]
        if symbol_upper in crypto_symbols or "USDT" in symbol_upper:
            return "binance"
        
        # Forex pairs
        if "/" in symbol:
            return "polygon"  # or "alpha_vantage"
        
        # Default to polygon for stocks
        return "polygon"
    
    async def get_stats(self) -> Dict:
        """Get subscription statistics"""
        async with self.lock:
            return {
                "total_symbols": len(self.subscriptions),
                "total_connections": len(self.connection_symbols),
                "provider_stats": {
                    provider: len(symbols)
                    for provider, symbols in self.provider_subscriptions.items()
                },
                "most_subscribed": [
                    {
                        "symbol": symbol,
                        "subscribers": len(subs)
                    }
                    for symbol, subs in sorted(
                        self.subscriptions.items(),
                        key=lambda x: len(x[1]),
                        reverse=True
                    )[:10]
                ]
            }
    
    async def optimize_subscriptions(self):
        """
        Optimize subscriptions by consolidating providers
        and removing stale subscriptions
        """
        async with self.lock:
            # Remove empty subscriptions
            empty_symbols = [
                symbol for symbol, subs in self.subscriptions.items()
                if len(subs) == 0
            ]
            
            for symbol in empty_symbols:
                provider = self.symbol_providers.get(symbol)
                if provider:
                    self.provider_subscriptions[provider].discard(symbol)
                
                del self.subscriptions[symbol]
                if symbol in self.symbol_providers:
                    del self.symbol_providers[symbol]
            
            if empty_symbols:
                logger.info(f"Cleaned up {len(empty_symbols)} empty subscriptions")
    
    async def rebalance_providers(self, symbol: str, new_provider: str):
        """Move a symbol subscription to a different provider"""
        async with self.lock:
            old_provider = self.symbol_providers.get(symbol)
            
            if old_provider and old_provider != new_provider:
                # Remove from old provider
                self.provider_subscriptions[old_provider].discard(symbol)
                
                # Add to new provider
                self.symbol_providers[symbol] = new_provider
                self.provider_subscriptions[new_provider].add(symbol)
                
                logger.info(f"Rebalanced {symbol}: {old_provider} -> {new_provider}")
                
                return {
                    "unsubscribe": {old_provider: [symbol]},
                    "subscribe": {new_provider: [symbol]}
                }
        
        return None


# Singleton instance
subscription_manager = SubscriptionManager()