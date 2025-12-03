"""
Background service for continuous market data refresh
Runs in the background to keep prices up-to-date
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Set, Dict
from decimal import Decimal
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.redis_client import redis_client
from app.models.portfolio import Portfolio, Holding
# FIX: Use the singleton instance instead of the class
from app.services.market_data_service import enhanced_market_service

logger = logging.getLogger(__name__)


class MarketDataRefresher:
    def __init__(self):
        self.is_running = False
        self.active_symbols: Set[str] = set()
        self.refresh_interval = 10  # Refresh every 10 seconds during market hours
        self.off_hours_interval = 300  # 5 minutes off-hours
        self.price_cache: Dict[str, tuple[float, datetime]] = {}
        
    async def start(self):
        """Start the market data refresher"""
        self.is_running = True
        logger.info("Market data refresher started")
        
        while self.is_running:
            try:
                # Check if market is open
                is_market_open = await self._is_market_open()
                interval = self.refresh_interval if is_market_open else self.off_hours_interval
                
                # Get active symbols from all portfolios
                await self._update_active_symbols()
                
                # Refresh prices for active symbols
                if self.active_symbols:
                    await self._refresh_prices()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in market data refresher: {str(e)}")
                await asyncio.sleep(30)
    
    async def stop(self):
        """Stop the refresher"""
        self.is_running = False
        logger.info("Market data refresher stopped")
    
    async def _is_market_open(self) -> bool:
        """Check if US market is currently open"""
        now = datetime.utcnow()
        current_time = now.time()
        
        # US market hours (9:30 AM - 4:00 PM EST = 13:30 - 20:00 UTC)
        market_open = time(13, 30)
        market_close = time(20, 0)
        
        # Check if it's a weekday
        is_weekday = now.weekday() < 5
        
        return is_weekday and market_open <= current_time <= market_close
    
    async def _update_active_symbols(self):
        """Get all symbols from active portfolios"""
        db = SessionLocal()
        try:
            holdings = db.query(Holding).all()
            self.active_symbols = {h.symbol for h in holdings if h.quantity > 0}
            logger.debug(f"Tracking {len(self.active_symbols)} active symbols")
        except Exception as e:
            logger.error(f"Error updating active symbols: {str(e)}")
        finally:
            db.close()
    
    async def _refresh_prices(self):
        """Refresh prices for all active symbols"""
        if not self.active_symbols:
            return
        
        try:
            # Batch fetch prices
            symbols_with_types = [(symbol, "STOCK") for symbol in self.active_symbols]
            
            # FIX: Use the singleton instance directly
            prices = await enhanced_market_service.get_batch_prices(symbols_with_types)
            
            # Update cache and Redis
            updated_count = 0
            for symbol, price in prices.items():
                if price and price > 0:
                    # Update local cache
                    self.price_cache[symbol] = (price, datetime.utcnow())
                    
                    # Update Redis with 60 second TTL
                    try:
                        redis_client.setex(f"price:{symbol}", 60, str(price))
                        updated_count += 1
                    except Exception as e:
                        logger.warning(f"Redis update failed for {symbol}: {e}")
            
            # Update holdings in database
            await self._update_holdings_prices(prices)
            
            logger.info(f"Refreshed {updated_count}/{len(self.active_symbols)} prices")
            
        except Exception as e:
            logger.error(f"Error refreshing prices: {str(e)}")
    
    async def _update_holdings_prices(self, prices: Dict[str, float]):
        """Update holding prices in database"""
        db = SessionLocal()
        try:
            for symbol, price in prices.items():
                if not price or price <= 0:
                    continue
                
                holdings = db.query(Holding).filter(Holding.symbol == symbol).all()
                
                for holding in holdings:
                    holding.current_price = float(price)
                    holding.last_price_update = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating holdings prices: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def get_cached_price(self, symbol: str) -> float | None:
        """Get price from cache if fresh"""
        if symbol in self.price_cache:
            price, timestamp = self.price_cache[symbol]
            # Cache valid for 30 seconds
            if (datetime.utcnow() - timestamp).seconds < 30:
                return price
        return None


# Global refresher instance
market_refresher = MarketDataRefresher()


async def start_market_refresher():
    """Start the market data refresher"""
    await market_refresher.start()


async def stop_market_refresher():
    """Stop the market data refresher"""
    await market_refresher.stop()