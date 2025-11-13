"""
Enhanced Trading Service with Leverage Support
Extends your existing trading_service.py with margin trading capabilities.
Save as: app/services/leverage_trading_service.py
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Optional, Tuple, Dict
from datetime import datetime
import logging

from app.models.orders import Order, OrderType, OrderSide, OrderStatus
from app.models.portfolio import Portfolio, Position, PositionSide, LiquidationEvent
from app.schemas.order import OrderCreate
from app.services.margin_service import margin_service
from app.services.market_data_service import enhanced_market_service

getcontext().prec = 18
getcontext().rounding = ROUND_HALF_EVEN
logger = logging.getLogger(__name__)


class InsufficientMarginError(Exception):
    """Raised when user has insufficient margin"""
    pass


class InvalidLeverageError(Exception):
    """Raised when leverage is invalid"""
    pass


class PositionNotFoundError(Exception):
    """Raised when position doesn't exist"""
    pass


class LeverageTradingService:
    """
    Service for handling leveraged trading operations.
    Works alongside the existing TradingService for spot trades.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.margin_service = margin_service
        
        # Fee configuration
        self.maker_fee_percent = Decimal("0.0002")  # 0.02% maker
        self.taker_fee_percent = Decimal("0.0005")  # 0.05% taker
        self.liquidation_fee_percent = Decimal("0.005")  # 0.5% liquidation fee
    
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
    
    async def open_leveraged_position(
        self,
        user_id: int,
        symbol: str,
        side: str,  # "LONG" or "SHORT"
        quantity: Decimal,
        leverage: Decimal,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> Position:
        """
        Open a new leveraged position.
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            side: "LONG" or "SHORT"
            quantity: Position size
            leverage: Leverage multiplier (e.g., 10 for 10x)
            order_type: MARKET or LIMIT
            limit_price: Limit price if LIMIT order
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
        
        Returns:
            Created Position object
        """
        try:
            logger.info(
                f"Opening leveraged position: User={user_id}, Symbol={symbol}, "
                f"Side={side}, Qty={quantity}, Leverage={leverage}x"
            )
            
            # Convert inputs
            quantity = self._to_decimal(quantity)
            leverage = self._to_decimal(leverage)
            
            # Get portfolio with lock
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id
            ).with_for_update().first()
            
            if not portfolio:
                raise ValueError("Portfolio not found")
            
            # Validate leverage
            if not self.margin_service.validate_leverage(leverage, "STOCK"):
                raise InvalidLeverageError(
                    f"Leverage {leverage}x is invalid or exceeds maximum"
                )
            
            # Get entry price
            if order_type == OrderType.MARKET:
                entry_price = await self._get_execution_price(symbol, side)
            else:
                if not limit_price:
                    raise ValueError("Limit price required for LIMIT orders")
                entry_price = self._to_decimal(limit_price)
            
            # Calculate margin required
            margin_required = self.margin_service.calculate_margin_required(
                quantity, entry_price, leverage
            )
            
            # Calculate position value
            position_value = quantity * entry_price
            
            # Calculate fees
            fee = position_value * self.taker_fee_percent
            total_cost = margin_required + fee
            
            # Check available margin
            equity = self._calculate_portfolio_equity(portfolio)
            available_margin = self.margin_service.calculate_available_margin(
                equity, self._to_decimal(portfolio.margin_used)
            )
            
            if available_margin < total_cost:
                raise InsufficientMarginError(
                    f"Insufficient margin. Required: {total_cost}, Available: {available_margin}"
                )
            
            # Calculate liquidation price
            if side == "LONG":
                liquidation_price = self.margin_service.calculate_liquidation_price_long(
                    entry_price, leverage
                )
            else:
                liquidation_price = self.margin_service.calculate_liquidation_price_short(
                    entry_price, leverage
                )
            
            # Calculate maintenance margin
            maintenance_margin = self.margin_service.calculate_maintenance_margin(position_value)
            
            # Create position
            position = Position(
                portfolio_id=portfolio.id,
                user_id=user_id,
                symbol=symbol.upper(),
                asset_type="STOCK",
                side=PositionSide.LONG if side == "LONG" else PositionSide.SHORT,
                quantity=float(quantity),
                entry_price=float(entry_price),
                current_price=float(entry_price),
                leverage=float(leverage),
                margin_used=float(margin_required),
                position_value=float(position_value),
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                liquidation_price=float(liquidation_price),
                maintenance_margin=float(maintenance_margin),
                initial_margin=float(margin_required),
                stop_loss_price=float(stop_loss) if stop_loss else None,
                take_profit_price=float(take_profit) if take_profit else None,
                is_open=True,
                is_liquidated=False,
                total_fees=float(fee),
                opened_at=datetime.utcnow(),
                last_price_update=datetime.utcnow()
            )
            
            self.db.add(position)
            
            # Update portfolio
            portfolio.margin_used = float(
                self._to_decimal(portfolio.margin_used) + margin_required
            )
            portfolio.cash_balance = float(
                self._to_decimal(portfolio.cash_balance) - total_cost
            )
            portfolio.total_exposure = float(
                self._to_decimal(portfolio.total_exposure) + position_value
            )
            portfolio.updated_at = datetime.utcnow()
            
            self.db.flush()
            
            # Update portfolio metrics
            await self._update_portfolio_metrics(portfolio)
            
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(
                f"✅ Leveraged position opened: ID={position.id}, "
                f"Liq Price={liquidation_price}"
            )
            
            return position
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to open leveraged position: {str(e)}", exc_info=True)
            raise
    
    async def close_leveraged_position(
        self,
        user_id: int,
        position_id: int,
        close_quantity: Optional[Decimal] = None,
        exit_price: Optional[Decimal] = None
    ) -> Dict:
        """
        Close a leveraged position (fully or partially).
        
        Args:
            user_id: User ID
            position_id: Position ID to close
            close_quantity: Quantity to close (None = close all)
            exit_price: Override exit price (None = use market price)
        
        Returns:
            Dictionary with closure details
        """
        try:
            # Get position with lock
            position = self.db.query(Position).filter(
                and_(
                    Position.id == position_id,
                    Position.user_id == user_id,
                    Position.is_open == True
                )
            ).with_for_update().first()
            
            if not position:
                raise PositionNotFoundError(f"Position {position_id} not found or already closed")
            
            # Get portfolio with lock
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == position.portfolio_id
            ).with_for_update().first()
            
            # Determine close quantity
            position_quantity = self._to_decimal(position.quantity)
            if close_quantity is None:
                close_quantity = position_quantity
            else:
                close_quantity = self._to_decimal(close_quantity)
                if close_quantity > position_quantity:
                    raise ValueError("Close quantity exceeds position size")
            
            # Get exit price
            if exit_price is None:
                side_for_exit = "SHORT" if position.side == PositionSide.LONG else "LONG"
                exit_price = await self._get_execution_price(position.symbol, side_for_exit)
            else:
                exit_price = self._to_decimal(exit_price)
            
            # Calculate PnL
            entry_price = self._to_decimal(position.entry_price)
            
            if position.side == PositionSide.LONG:
                pnl = (exit_price - entry_price) * close_quantity
            else:
                pnl = (entry_price - exit_price) * close_quantity
            
            # Calculate fees
            close_value = close_quantity * exit_price
            close_fee = close_value * self.taker_fee_percent
            net_pnl = pnl - close_fee
            
            # Calculate proportion being closed
            close_ratio = close_quantity / position_quantity
            margin_to_release = self._to_decimal(position.margin_used) * close_ratio
            
            # Update position
            is_full_close = close_quantity >= position_quantity
            
            if is_full_close:
                position.is_open = False
                position.closed_at = datetime.utcnow()
                position.quantity = 0.0
            else:
                position.quantity = float(position_quantity - close_quantity)
                position.margin_used = float(
                    self._to_decimal(position.margin_used) - margin_to_release
                )
            
            position.realized_pnl = float(
                self._to_decimal(position.realized_pnl) + net_pnl
            )
            position.total_fees = float(
                self._to_decimal(position.total_fees) + close_fee
            )
            position.updated_at = datetime.utcnow()
            
            # Update portfolio
            portfolio.margin_used = float(
                self._to_decimal(portfolio.margin_used) - margin_to_release
            )
            portfolio.cash_balance = float(
                self._to_decimal(portfolio.cash_balance) + margin_to_release + net_pnl
            )
            position_value = close_quantity * entry_price
            portfolio.total_exposure = float(
                max(self._to_decimal(portfolio.total_exposure) - position_value, Decimal('0'))
            )
            portfolio.updated_at = datetime.utcnow()
            
            self.db.flush()
            
            # Update metrics
            await self._update_portfolio_metrics(portfolio)
            
            self.db.commit()
            
            logger.info(
                f"✅ Position closed: ID={position_id}, "
                f"Qty={close_quantity}, PnL={net_pnl}"
            )
            
            return {
                "position_id": position_id,
                "closed_quantity": float(close_quantity),
                "exit_price": float(exit_price),
                "pnl": float(pnl),
                "fee": float(close_fee),
                "net_pnl": float(net_pnl),
                "margin_released": float(margin_to_release),
                "is_full_close": is_full_close
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to close position: {str(e)}", exc_info=True)
            raise
    
    async def update_position_prices(self, position: Position) -> None:
        """
        Update position with current market price and recalculate metrics.
        """
        try:
            # Get current price
            current_price = await enhanced_market_service.get_price(
                position.symbol, "STOCK", force_refresh=True
            )
            
            if not current_price or current_price <= 0:
                logger.warning(f"Invalid price for {position.symbol}")
                return
            
            current_price = self._to_decimal(current_price)
            entry_price = self._to_decimal(position.entry_price)
            quantity = self._to_decimal(position.quantity)
            
            # Calculate unrealized PnL
            if position.side == PositionSide.LONG:
                unrealized_pnl = self.margin_service.calculate_unrealized_pnl_long(
                    quantity, entry_price, current_price
                )
            else:
                unrealized_pnl = self.margin_service.calculate_unrealized_pnl_short(
                    quantity, entry_price, current_price
                )
            
            # Update position
            position.current_price = float(current_price)
            position.unrealized_pnl = float(unrealized_pnl)
            position.last_price_update = datetime.utcnow()
            position.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating position prices: {str(e)}")
    
    async def liquidate_position(
        self,
        position: Position,
        liquidation_price: Decimal,
        reason: str = "Margin call"
    ) -> LiquidationEvent:
        """
        Liquidate a position that has reached its liquidation price.
        """
        try:
            logger.warning(
                f"🚨 Liquidating position: ID={position.id}, "
                f"Symbol={position.symbol}, User={position.user_id}"
            )
            
            # Get portfolio with lock
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.id == position.portfolio_id
            ).with_for_update().first()
            
            # Calculate liquidation details
            quantity = self._to_decimal(position.quantity)
            entry_price = self._to_decimal(position.entry_price)
            liq_price = self._to_decimal(liquidation_price)
            margin_used = self._to_decimal(position.margin_used)
            
            # Calculate loss
            if position.side == PositionSide.LONG:
                loss = (entry_price - liq_price) * quantity
            else:
                loss = (liq_price - entry_price) * quantity
            
            # Add liquidation fee
            position_value = quantity * liq_price
            liq_fee = position_value * self.liquidation_fee_percent
            total_loss = loss + liq_fee
            
            # Calculate equity before/after
            equity_before = self._calculate_portfolio_equity(portfolio)
            
            # Create liquidation event
            liquidation_event = LiquidationEvent(
                user_id=position.user_id,
                portfolio_id=portfolio.id,
                position_id=position.id,
                symbol=position.symbol,
                side=position.side,
                quantity=float(quantity),
                entry_price=float(entry_price),
                liquidation_price=float(position.liquidation_price),
                actual_liquidation_price=float(liq_price),
                margin_used=float(margin_used),
                loss_amount=float(total_loss),
                liquidation_fee=float(liq_fee),
                equity_before=float(equity_before),
                equity_after=0.0,  # Will update below
                margin_level_before=float(
                    self.margin_service.calculate_margin_level(equity_before, margin_used)
                ),
                reason=reason,
                liquidated_at=datetime.utcnow()
            )
            
            # Update position
            position.is_open = False
            position.is_liquidated = True
            position.closed_at = datetime.utcnow()
            position.realized_pnl = float(-total_loss)
            position.total_fees = float(
                self._to_decimal(position.total_fees) + liq_fee
            )
            
            # Update portfolio - margin is lost
            portfolio.margin_used = float(
                max(self._to_decimal(portfolio.margin_used) - margin_used, Decimal('0'))
            )
            # Don't return margin - it's lost
            portfolio.cash_balance = float(
                max(self._to_decimal(portfolio.cash_balance) - liq_fee, Decimal('0'))
            )
            portfolio.total_exposure = float(
                max(self._to_decimal(portfolio.total_exposure) - position_value, Decimal('0'))
            )
            
            equity_after = self._calculate_portfolio_equity(portfolio)
            liquidation_event.equity_after = float(equity_after)
            
            self.db.add(liquidation_event)
            self.db.flush()
            
            await self._update_portfolio_metrics(portfolio)
            
            self.db.commit()
            
            logger.warning(
                f"🚨 Position liquidated: ID={position.id}, "
                f"Loss={total_loss}, Fee={liq_fee}"
            )
            
            return liquidation_event
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to liquidate position: {str(e)}", exc_info=True)
            raise
    
    def _calculate_portfolio_equity(self, portfolio: Portfolio) -> Decimal:
        """Calculate total portfolio equity (cash + unrealized PnL)"""
        cash = self._to_decimal(portfolio.cash_balance)
        unrealized = self._to_decimal(portfolio.unrealized_pnl)
        return cash + unrealized
    
    async def _get_execution_price(self, symbol: str, side: str) -> Decimal:
        """Get execution price with slippage"""
        try:
            price = await enhanced_market_service.get_price(symbol, "STOCK", force_refresh=True)
            if not price or price <= 0:
                fallback_prices = {
                    "AAPL": 150.00,
                    "TSLA": 250.00,
                    "GOOGL": 2800.00,
                    "MSFT": 330.00
                }
                price = fallback_prices.get(symbol.upper(), 100.00)
            
            price = self._to_decimal(price)
            
            # Apply small slippage
            slippage = Decimal("0.001")  # 0.1%
            if side == "LONG":
                price = price * (Decimal('1') + slippage)
            else:
                price = price * (Decimal('1') - slippage)
            
            return price
            
        except Exception as e:
            logger.error(f"Error getting execution price: {str(e)}")
            return Decimal("100.00")
    
    async def _update_portfolio_metrics(self, portfolio: Portfolio) -> None:
        """Update portfolio-level metrics"""
        try:
            # Get all open positions
            positions = self.db.query(Position).filter(
                and_(
                    Position.portfolio_id == portfolio.id,
                    Position.is_open == True
                )
            ).all()
            
            # Calculate total unrealized PnL
            total_unrealized = Decimal('0')
            for pos in positions:
                await self.update_position_prices(pos)
                total_unrealized += self._to_decimal(pos.unrealized_pnl)
            
            # Update portfolio
            portfolio.unrealized_pnl = float(total_unrealized)
            equity = self._calculate_portfolio_equity(portfolio)
            portfolio.equity = float(equity)
            
            # Calculate margin level
            margin_used = self._to_decimal(portfolio.margin_used)
            if margin_used > 0:
                margin_level = self.margin_service.calculate_margin_level(equity, margin_used)
                portfolio.margin_level = float(margin_level)
            else:
                portfolio.margin_level = 999999.0
            
            # Calculate available margin
            available_margin = self.margin_service.calculate_available_margin(equity, margin_used)
            portfolio.margin_available = float(available_margin)
            
            portfolio.total_value = float(equity)
            portfolio.last_valuation_update = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {str(e)}")
    
    def get_open_positions(
        self,
        user_id: int,
        symbol: Optional[str] = None
    ) -> list:
        """Get all open positions for a user"""
        query = self.db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.is_open == True
            )
        )
        
        if symbol:
            query = query.filter(Position.symbol == symbol.upper())
        
        return query.order_by(Position.opened_at.desc()).all()
    
    def get_position_by_id(self, user_id: int, position_id: int) -> Optional[Position]:
        """Get specific position"""
        return self.db.query(Position).filter(
            and_(
                Position.id == position_id,
                Position.user_id == user_id
            )
        ).first()