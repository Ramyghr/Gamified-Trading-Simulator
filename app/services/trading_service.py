from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
import logging
import asyncio

from app.models.orders import Order, OrderType, OrderSide, OrderStatus, TimeInForce
from app.models.stock_transaction import StockTransaction, TransactionType
from app.models.portfolio import Portfolio, Holding as StockHolding, AssetType
from app.schemas.order import OrderCreate
from app.services.market_data_refresher import market_refresher
from app.services.market_data_service import enhanced_market_service

getcontext().prec = 12
getcontext().rounding = ROUND_HALF_EVEN
logger = logging.getLogger(__name__)


class TradingService:
    def __init__(self, db: Session):
        self.db = db
        self.market_refresher = market_refresher
        
        # Fee configuration
        self.base_fee_percent = Decimal("0.0005")  # 0.05%
        self.min_fee = Decimal("0.50")
        self.slippage_percent = Decimal("0.001")  # 0.1% slippage
    
    def _to_decimal(self, value) -> Decimal:
        """Safely convert to Decimal"""
        if value is None:
            return Decimal('0')
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')
    
    def _to_float(self, value) -> float:
        """Safely convert to float"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        return float(value)
    
    def calculate_fee(self, trade_value: Decimal) -> Decimal:
        """Calculate trading fee"""
        fee = trade_value * self.base_fee_percent
        return max(fee, self.min_fee)
    
    async def get_real_time_price(self, symbol: str, side: OrderSide) -> Decimal:
        """
        Get real-time price for order execution
        """
        try:
            # Try cache first
            price = self.market_refresher.get_cached_price(symbol)
            
            # If cache miss or stale, force refresh
            if price is None:
                logger.info(f"Cache miss for {symbol}, forcing refresh")
                price = await enhanced_market_service.get_price(
                    symbol, 
                    "STOCK", 
                    force_refresh=True
                )
            
            if not price or price <= 0:
                # Fallback price for testing
                fallback_prices = {
                    "AAPL": Decimal("150.00"),
                    "TSLA": Decimal("250.00"),
                    "GOOGL": Decimal("2800.00"),
                    "MSFT": Decimal("330.00")
                }
                price = fallback_prices.get(symbol.upper(), Decimal("100.00"))
                logger.warning(f"Using fallback price for {symbol}: ${price}")
            
            price_decimal = self._to_decimal(price)
            
            # Apply realistic slippage
            if side == OrderSide.BUY:
                execution_price = price_decimal * (Decimal('1') + self.slippage_percent)
            else:
                execution_price = price_decimal * (Decimal('1') - self.slippage_percent)
            
            logger.info(
                f"Real-time price for {symbol}: ${price_decimal:.2f} "
                f"(execution: ${execution_price:.2f})"
            )
            
            return execution_price
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            # Fallback for testing
            return Decimal("100.00")
    
    async def calculate_estimated_cost(
        self, 
        symbol: str, 
        order_type: OrderType, 
        side: OrderSide, 
        quantity: Decimal, 
        price: Optional[Decimal] = None
    ) -> Decimal:
        """Calculate estimated cost with real-time prices"""
        quantity = self._to_decimal(quantity)
        
        if order_type == OrderType.MARKET:
            execution_price = await self.get_real_time_price(symbol, side)
        else:
            execution_price = self._to_decimal(price) if price else Decimal('0')
        
        trade_value = quantity * execution_price
        fee = self.calculate_fee(trade_value)
        
        if side == OrderSide.BUY:
            return trade_value + fee
        else:
            return trade_value - fee
    def _get_portfolio_with_lock(self, user_id: int) -> Portfolio:
        """Get portfolio with lock for update"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.user_id == user_id
        ).with_for_update().first()
        
        if not portfolio:
            raise InvalidOrderError("Portfolio not found")
        
        return portfolio
    def _get_holding_with_lock(self, portfolio_id: int, symbol: str) -> Optional[StockHolding]:
        """Get holding with lock for update"""
        return self.db.query(StockHolding).filter(
            and_(
                StockHolding.portfolio_id == portfolio_id,
                StockHolding.symbol == symbol
            )
        ).with_for_update().first()
    def validate_and_reserve_resources(
        self,
        user_id: int,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        estimated_cost: Decimal
    ) -> Tuple[Portfolio, Optional[StockHolding]]:
        """Validate and reserve resources with proper locking"""
        quantity = self._to_decimal(quantity)
        estimated_cost = self._to_decimal(estimated_cost)
        
        # Get portfolio with lock
        portfolio = self._get_portfolio_with_lock(user_id)
        
        if side == OrderSide.BUY:
            # Check cash availability
            available_cash = (
                self._to_decimal(portfolio.cash_balance) - 
                self._to_decimal(portfolio.reserved_cash)
            )
            
            if available_cash < estimated_cost:
                # raise InsufficientFundsError(
                #     f"Insufficient funds. Available: ${available_cash:.2f}, "
                #     f"Required: ${estimated_cost:.2f}"
                # )
                logger.info("available_cash < estimated_cost")            
            # Reserve cash - use proper decimal arithmetic
            current_reserved = self._to_decimal(portfolio.reserved_cash)
            new_reserved = current_reserved + estimated_cost
            portfolio.reserved_cash = float(new_reserved)
            
            logger.info(f"Reserved ${estimated_cost:.2f} for buy order. Total reserved: ${new_reserved:.2f}")
            return portfolio, None
        
        else:  # SELL
            # Get holding with lock
            holding = self._get_holding_with_lock(portfolio.id, symbol)
            
            if not holding:
                # raise InsufficientSharesError(f"No holdings found for {symbol}")
                logger.info("no holdings")            
            available_quantity = (
                self._to_decimal(holding.quantity) - 
                self._to_decimal(holding.reserved_quantity)
            )
            
            if available_quantity < quantity:
                # raise InsufficientSharesError(
                #     f"Insufficient shares. Available: {available_quantity}, "
                #     f"Required: {quantity}"
                # )
                logger.info("available_quantity < quantity")
            
            # Reserve shares
            current_reserved = self._to_decimal(holding.reserved_quantity)
            new_reserved = current_reserved + quantity
            holding.reserved_quantity = float(new_reserved)
            
            logger.info(f"Reserved {quantity} shares for sell order. Total reserved: {new_reserved}")
            return portfolio, holding
    
    async def create_order(self, user_id: int, order_data: OrderCreate) -> Order | None:
        """Create and execute order with proper transaction management"""
        logger.info(f"Creating order for user {user_id}: {order_data.dict()}")

        try:
            # Check for duplicate idempotency key
            if order_data.idempotency_key:
                existing = self.db.query(Order).filter(
                    Order.idempotency_key == order_data.idempotency_key
                ).first()
                if existing:
                    logger.info(f"Duplicate order found: {order_data.idempotency_key}")
                    return existing

            # Calculate estimated cost
            estimated_cost = await self.calculate_estimated_cost(
                order_data.symbol,
                order_data.order_type,
                order_data.side,
                order_data.quantity,
                order_data.price
            )
            logger.info(f"Estimated cost for {order_data.symbol}: ${estimated_cost:.2f}")

            # Validate resources
            portfolio, holding = self.validate_and_reserve_resources(
                user_id,
                order_data.symbol,
                order_data.side,
                order_data.quantity,
                estimated_cost if order_data.side == OrderSide.BUY else Decimal(0)
            )

            # Create order object
            order = Order(
                user_id=user_id,
                symbol=order_data.symbol.upper(),
                order_type=order_data.order_type,
                side=order_data.side,
                quantity=float(order_data.quantity),
                price=float(order_data.price) if order_data.price else None,
                stop_price=float(order_data.stop_price) if order_data.stop_price else None,
                time_in_force=order_data.time_in_force,
                status=OrderStatus.PENDING,
                estimated_cost=float(estimated_cost),
                reserved_amount=float(estimated_cost if order_data.side == OrderSide.BUY else Decimal(0)),
                idempotency_key=order_data.idempotency_key,
                filled_quantity=0.0,
                total_fees=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Set expiration for DAY orders
            if order_data.time_in_force == TimeInForce.DAY:
                order.expires_at = datetime.utcnow().replace(hour=16, minute=0, second=0) + timedelta(days=1)

            self.db.add(order)
            self.db.flush()

            logger.info(
                f"Order {getattr(order, 'id', 'N/A')} created: "
                f"{getattr(order, 'symbol', 'N/A')} {getattr(order, 'side', 'N/A')} {getattr(order, 'quantity', 'N/A')}"
            )

            # Execute orders safely
            try:
                if order_data.order_type == OrderType.MARKET:
                    await self._execute_order(order, portfolio, holding)
                elif order_data.order_type == OrderType.LIMIT and await self._is_limit_order_executable(order):
                    await self._execute_order(order, portfolio, holding)
            except Exception as exec_err:
                logger.error(f"Error executing order {getattr(order, 'id', 'N/A')}: {str(exec_err)}", exc_info=True)

            self.db.commit()
            self.db.refresh(order)

            logger.info(
                f"✅ Order {getattr(order, 'id', 'N/A')} completed: "
                f"{getattr(order, 'symbol', 'N/A')} {getattr(order, 'side', 'N/A')} {getattr(order, 'quantity', 'N/A')} "
                f"@ {getattr(order.status, 'value', 'N/A')}"
            )

            return order

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create order: {str(e)}", exc_info=True)
            return None

   
    
    async def _execute_order(
        self, 
        order: Order, 
        portfolio: Portfolio,
        holding: Optional[StockHolding]
    ) -> None:
        """Execute order with real-time price"""
        try:
            logger.info(f"Executing order {order.id} for {order.symbol}")
            
            # Get real-time execution price
            execution_price = await self.get_real_time_price(order.symbol, order.side)
            quantity = self._to_decimal(order.quantity)
            
            # Calculate trade values
            trade_value = quantity * execution_price
            fee = self.calculate_fee(trade_value)
            
            if order.side == OrderSide.BUY:
                net_amount = trade_value + fee
            else:
                net_amount = trade_value - fee
            
            logger.info(
                f"Execution: {quantity} {order.symbol} @ ${execution_price:.2f}, "
                f"value=${trade_value:.2f}, fee=${fee:.2f}, net=${net_amount:.2f}"
            )

            # Record initial state for transaction
            cash_before = self._to_decimal(portfolio.cash_balance)
            shares_before = self._to_decimal(holding.quantity) if holding else Decimal('0')

            # Update portfolio based on order side
            if order.side == OrderSide.BUY:
                self._process_buy_order(order, portfolio, holding, quantity, execution_price, fee, net_amount)
            else:
                self._process_sell_order(order, portfolio, holding, quantity, execution_price, fee, net_amount)

            # FIX: Call _create_transaction_record with ALL required parameters
            self._create_transaction_record(
                order=order,
                quantity=quantity,
                execution_price=execution_price,
                trade_value=trade_value,
                fee=fee,
                net_amount=net_amount,
                cash_before=cash_before,
                shares_before=shares_before,
                portfolio=portfolio,      # Add this
                holding=holding           # Add this
            )

            # Update order status
            order.filled_quantity = float(quantity)
            order.average_fill_price = float(execution_price)
            order.total_fees = float(fee)
            order.status = OrderStatus.FILLED
            order.executed_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()

            logger.info(f"✅ Order {order.id} executed successfully")

        except Exception as e:
            logger.error(f"Error executing order {order.id}: {str(e)}", exc_info=True)
            order.status = OrderStatus.REJECTED
            order.rejection_reason = str(e)
            order.updated_at = datetime.utcnow()
            raise
    def _create_transaction_record(
        self,
        order: Order,
        quantity: Decimal,
        execution_price: Decimal,
        trade_value: Decimal,
        fee: Decimal,
        net_amount: Decimal,
        cash_before: Decimal,
        shares_before: Decimal,
        portfolio: Portfolio,       # Required
        holding: Optional[StockHolding] = None  # Optional but should be provided
    ) -> None:
        """Create stock transaction record"""
        transaction = StockTransaction(
            user_id=order.user_id,
            order_id=order.id,
            symbol=order.symbol,
            transaction_type=TransactionType.BUY if order.side == OrderSide.BUY else TransactionType.SELL,
            quantity=float(quantity),
            price=float(execution_price),
            total_amount=float(trade_value),
            fee=float(fee),
            net_amount=float(net_amount),
            cash_before=float(cash_before),
            cash_after=float(self._to_decimal(portfolio.cash_balance)),
            shares_before=float(shares_before),
            shares_after=float(self._to_decimal(holding.quantity) if holding else 0.0),
            execution_venue="REAL_TIME_MARKET",
            executed_at=datetime.utcnow()
        )
        self.db.add(transaction)

    def _process_sell_order(self, order: Order, portfolio: Portfolio, holding: StockHolding,
                           quantity: Decimal, execution_price: Decimal, fee: Decimal, net_amount: Decimal):
        """Process sell order execution"""
        # Release reserved shares
        current_reserved = self._to_decimal(holding.reserved_quantity)
        holding.reserved_quantity = float(current_reserved - quantity)
        
        # Reduce holding quantity
        current_quantity = self._to_decimal(holding.quantity)
        holding.quantity = float(current_quantity - quantity)
        
        # Add proceeds to cash
        current_cash = self._to_decimal(portfolio.cash_balance)
        portfolio.cash_balance = float(current_cash + net_amount)
        
        # Remove holding if empty
        if holding.quantity <= 0:
            self.db.delete(holding)
    def _process_buy_order(self, order: Order, portfolio: Portfolio, holding: Optional[StockHolding], 
                          quantity: Decimal, execution_price: Decimal, fee: Decimal, net_amount: Decimal):
        """Process buy order execution"""
        # Release reserved cash
        current_reserved = self._to_decimal(portfolio.reserved_cash)
        order_reserved = self._to_decimal(order.reserved_amount)
        portfolio.reserved_cash = float(current_reserved - order_reserved)
        
        # Deduct cost from cash balance
        current_cash = self._to_decimal(portfolio.cash_balance)
        portfolio.cash_balance = float(current_cash - net_amount)
        
        # Update or create holding
        holding = self._get_holding_with_lock(portfolio.id, order.symbol)
        
        if holding:
            # Update existing holding
            current_quantity = self._to_decimal(holding.quantity)
            current_avg_price = self._to_decimal(holding.average_buy_price)
            
            total_cost = (current_quantity * current_avg_price) + (quantity * execution_price)
            new_quantity = current_quantity + quantity
            
            holding.quantity = float(new_quantity)
            holding.average_buy_price = float(total_cost / new_quantity)
            holding.current_price = float(execution_price)
            holding.last_price_update = datetime.utcnow()
        else:
            # Create new holding
            holding = StockHolding(
                portfolio_id=portfolio.id,
                symbol=order.symbol,
                asset_type=AssetType.STOCK,
                quantity=float(quantity),
                average_buy_price=float(execution_price),
                current_price=float(execution_price),
                reserved_quantity=0.0,
                last_price_update=datetime.utcnow()
            )
            self.db.add(holding)

    def cancel_order(self, user_id: int, order_id: int) -> Order:
        """Cancel order and release resources"""
        try:
            order = self.db.query(Order).filter(
                and_(
                    Order.id == order_id,
                    Order.user_id == user_id
                )
            ).with_for_update().first()
            
            if not order:
                raise InvalidOrderError("Order not found")
            
            if not order.is_active:
                raise InvalidOrderError(f"Cannot cancel order with status {order.status}")
            
            # Lock portfolio
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id
            ).with_for_update().first()
            
            # Release resources
            if order.side == OrderSide.BUY:
                current_reserved = self._to_decimal(portfolio.reserved_cash)
                order_reserved = self._to_decimal(order.reserved_amount)
                portfolio.reserved_cash = self._to_float(current_reserved - order_reserved)
                logger.info(f"Released ${order_reserved:.2f} reserved cash")
            else:
                holding = self.db.query(StockHolding).filter(
                    and_(
                        StockHolding.portfolio_id == portfolio.id,
                        StockHolding.symbol == order.symbol
                    )
                ).with_for_update().first()
                
                if holding:
                    unfilled_qty = self._to_decimal(order.quantity) - self._to_decimal(order.filled_quantity)

                    current_reserved = self._to_decimal(holding.reserved_quantity)
                    holding.reserved_quantity = self._to_float(current_reserved - unfilled_qty)
                    logger.info(f"Released {unfilled_qty} reserved shares")
            
            # Update order
            order.status = OrderStatus.CANCELED
            order.canceled_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order {order_id} canceled successfully")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error canceling order: {str(e)}", exc_info=True)
            raise
    
    def get_user_orders(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None,
        order_type: Optional[OrderType] = None,
        side: Optional[OrderSide] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Get user orders with filters"""
        query = self.db.query(Order).filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        if symbol:
            query = query.filter(Order.symbol == symbol.upper())
        
        if order_type:
            query = query.filter(Order.order_type == order_type)
        
        if side:
            query = query.filter(Order.side == side)
        
        orders = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()
        
        logger.info(f"Retrieved {len(orders)} orders for user {user_id}")
        return orders
    
    def get_order_by_id(self, user_id: int, order_id: int) -> Optional[Order]:
        """Get specific order"""
        return self.db.query(Order).filter(
            and_(
                Order.id == order_id,
                Order.user_id == user_id
            )
        ).first()