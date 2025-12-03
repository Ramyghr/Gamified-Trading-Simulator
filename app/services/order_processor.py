"""
Background worker for processing pending orders (limit/stop/stop-limit orders).
Monitors market prices and executes orders when conditions are met.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.config.database import SessionLocal
from app.models.orders import Order, OrderType, OrderSide, OrderStatus
from app.models.portfolio import Portfolio, Holding as StockHolding
from app.services.trading_service import TradingService
from app.services.market_data_service import enhanced_market_service

logger = logging.getLogger(__name__)


class OrderProcessor:
    def __init__(self):
        self.enhanced_market_service = enhanced_market_service
        self.is_running = False
        self.check_interval = 1  # Check every second
        self.cleanup_interval = 300  # Cleanup expired orders every 5 minutes
        self.last_cleanup = datetime.utcnow()
    
    async def start(self):
        """Start the order processor"""
        self.is_running = True
        logger.info("Order processor started")
        
        while self.is_running:
            try:
                await self.process_pending_orders()
                
                # Periodic cleanup of expired orders
                if (datetime.utcnow() - self.last_cleanup).seconds >= self.cleanup_interval:
                    await self.cleanup_expired_orders()
                    self.last_cleanup = datetime.utcnow()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in order processor loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the order processor"""
        self.is_running = False
        logger.info("Order processor stopped")
    
    async def process_pending_orders(self):
        """Process all pending and partially filled orders"""
        db = SessionLocal()
        try:
            # Get all active orders
            active_orders = db.query(Order).filter(
                or_(
                    Order.status == OrderStatus.PENDING,
                    Order.status == OrderStatus.PARTIALLY_FILLED
                )
            ).all()
            
            if not active_orders:
                return
            
            # Group orders by symbol for efficient processing
            orders_by_symbol = {}
            for order in active_orders:
                if order.symbol not in orders_by_symbol:
                    orders_by_symbol[order.symbol] = []
                orders_by_symbol[order.symbol].append(order)
            
            # Process each symbol's orders
            for symbol, orders in orders_by_symbol.items():
                await self.process_symbol_orders(db, symbol, orders)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing pending orders: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def process_symbol_orders(self, db: Session, symbol: str, orders: List[Order]):
        """Process all orders for a specific symbol"""
        try:
            # Get current market price using async method
            price = await self.enhanced_market_service.get_price(symbol, "STOCK")
            if not price or price <= 0:
                logger.warning(f"No market data available for {symbol}")
                return
            
            current_price = Decimal(str(price))
            
            # Check each order
            for order in orders:
                try:
                    if self.should_execute_order(order, current_price):
                        await self.execute_order(db, order)
                except Exception as e:
                    logger.error(f"Error processing order {order.id}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error processing orders for {symbol}: {str(e)}")
    
    def should_execute_order(self, order: Order, current_price: Decimal) -> bool:
        """Determine if order conditions are met for execution"""
        
        # LIMIT orders
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                return current_price <= Decimal(str(order.price))
            else:
                return current_price >= Decimal(str(order.price))
        
        # STOP orders
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.SELL:
                return current_price <= Decimal(str(order.stop_price))
            else:
                return current_price >= Decimal(str(order.stop_price))
        
        # STOP_LIMIT orders
        elif order.order_type == OrderType.STOP_LIMIT:
            # Check if stop is triggered
            stop_triggered = False
            if order.side == OrderSide.SELL:
                stop_triggered = current_price <= Decimal(str(order.stop_price))
            else:
                stop_triggered = current_price >= Decimal(str(order.stop_price))
            
            if not stop_triggered:
                return False
            
            # Check if limit condition is met
            if order.side == OrderSide.BUY:
                return current_price <= Decimal(str(order.price))
            else:
                return current_price >= Decimal(str(order.price))
        
        # TAKE_PROFIT orders
        elif order.order_type == OrderType.TAKE_PROFIT:
            if order.side == OrderSide.SELL:
                return current_price >= Decimal(str(order.price))
            else:
                return current_price <= Decimal(str(order.price))
        
        return False
    
    async def execute_order(self, db: Session, order: Order):
        """Execute an order using the trading service"""
        try:
            logger.info(f"Executing order {order.id} for {order.symbol}")
            
            # Lock the order
            order = db.query(Order).filter(Order.id == order.id).with_for_update().first()
            
            if not order or not order.is_active:
                return
            
            # Lock portfolio
            portfolio = db.query(Portfolio).filter(
                Portfolio.user_id == order.user_id
            ).with_for_update().first()
            
            if not portfolio:
                logger.error(f"Portfolio not found for user {order.user_id}")
                return
            
            # Lock holding if SELL order
            holding = None
            if order.side == OrderSide.SELL:
                holding = db.query(StockHolding).filter(
                    and_(
                        StockHolding.portfolio_id == portfolio.id,
                        StockHolding.symbol == order.symbol
                    )
                ).with_for_update().first()
            
            # Execute using trading service
            trading_service = TradingService(db)
            await trading_service._execute_order(order, portfolio, holding)
            
            logger.info(f"Order {order.id} executed successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute order {order.id}: {str(e)}")
            # Mark order as rejected
            order.status = OrderStatus.REJECTED
            order.rejection_reason = f"Execution failed: {str(e)}"
            order.updated_at = datetime.utcnow()
    
    async def cleanup_expired_orders(self):
        """Cancel expired DAY orders and orders past their expiration"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Find expired orders
            expired_orders = db.query(Order).filter(
                and_(
                    or_(
                        Order.status == OrderStatus.PENDING,
                        Order.status == OrderStatus.PARTIALLY_FILLED
                    ),
                    Order.expires_at.isnot(None),
                    Order.expires_at <= now
                )
            ).all()
            
            if expired_orders:
                logger.info(f"Found {len(expired_orders)} expired orders to cancel")
            
            for order in expired_orders:
                try:
                    trading_service = TradingService(db)
                    trading_service.cancel_order(order.user_id, order.id)
                    
                    # Mark as expired specifically
                    order.status = OrderStatus.EXPIRED
                    
                    logger.info(f"Expired order {order.id} canceled")
                    
                except Exception as e:
                    logger.error(f"Error canceling expired order {order.id}: {str(e)}")
                    continue
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up expired orders: {str(e)}")
            db.rollback()
        finally:
            db.close()


# Global processor instance
order_processor = OrderProcessor()


async def start_order_processor():
    """Start the order processor background task"""
    await order_processor.start()


async def stop_order_processor():
    """Stop the order processor background task"""
    await order_processor.stop()


async def process_orders_once():
    """Process pending orders once (useful for testing)"""
    processor = OrderProcessor()
    await processor.process_pending_orders()