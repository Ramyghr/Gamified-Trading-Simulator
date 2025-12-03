"""
Historical Order Processor - FIXED VERSION
Executes orders during simulations using historically accurate prices
"""
from datetime import datetime
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
import logging

from app.models.crisis_simulator import SimulationOrder, SimulationPosition, SimulationParticipant
from app.crisis_simulator.data_loader import HistoricalDataLoader

logger = logging.getLogger(__name__)


class HistoricalOrderProcessor:
    """
    Processes orders during crisis simulations
    Enforces period-specific rules and executes at historical prices
    """
    
    # Period-specific trading constraints
    CRISIS_CONSTRAINTS = {
        "great_depression": {
            "margin_requirement": 0.10,
            "short_selling_allowed": True,
            "commission_rate": 0.001,
            "min_tick_size": 0.125,
        },
        "black_monday": {
            "margin_requirement": 0.50,
            "short_selling_allowed": True,
            "commission_rate": 0.002,
            "circuit_breakers": True,
            "min_tick_size": 0.125,
        },
        "dotcom_bubble": {
            "margin_requirement": 0.50,
            "short_selling_allowed": True,
            "commission_rate": 0.001,
            "min_tick_size": 0.01,
        },
        "financial_crisis_2008": {
            "margin_requirement": 0.50,
            "short_selling_allowed": True,
            "short_selling_ban_start": "2008-09-19",
            "short_selling_ban_end": "2008-10-08",
            "commission_rate": 0.0005,
            "min_tick_size": 0.01,
        },
        "covid_crash": {
            "margin_requirement": 0.25,
            "short_selling_allowed": True,
            "commission_rate": 0.0,
            "min_tick_size": 0.01,
            "pattern_day_trader_rule": True,
        }
    }
    
    def __init__(self, data_loader: HistoricalDataLoader, crisis_type: str):
        """
        Initialize order processor
        
        Args:
            data_loader: Historical data loader instance
            crisis_type: Type of crisis being simulated
        """
        self.data_loader = data_loader
        self.crisis_type = crisis_type
        self.constraints = self.CRISIS_CONSTRAINTS.get(crisis_type, {})
    
    def validate_order(
        self,
        participant: SimulationParticipant,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        limit_price: Optional[float],
        historical_time: datetime,
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate order against historical constraints and participant state
        """
        # Check if asset exists in this period
        available_assets = self.data_loader.get_available_assets(self.crisis_type)
        if symbol not in available_assets:
            return False, f"Asset {symbol} not available in this crisis period"
        
        # Get current price
        current_price = self.data_loader.get_price_at_time(
            self.crisis_type, symbol, historical_time
        )
        
        if not current_price:
            return False, "Unable to get current price"
        
        # Check if this is a short sale (selling without existing position)
        if side == "SELL":
            existing_position = db.query(SimulationPosition).filter(
                SimulationPosition.participant_id == participant.id,
                SimulationPosition.symbol == symbol
            ).first()
            
            current_holding = existing_position.quantity if existing_position else 0
            
            if current_holding < quantity:
                # This is a short sale
                short_quantity = quantity - current_holding
                
                if not self.constraints.get("short_selling_allowed", True):
                    return False, "Short selling not allowed in this period"
                
                # Check for temporary bans
                ban_start = self.constraints.get("short_selling_ban_start")
                ban_end = self.constraints.get("short_selling_ban_end")
                
                if ban_start and ban_end:
                    ban_start_dt = datetime.strptime(ban_start, "%Y-%m-%d")
                    ban_end_dt = datetime.strptime(ban_end, "%Y-%m-%d")
                    
                    if ban_start_dt <= historical_time <= ban_end_dt:
                        return False, "Temporary short selling ban in effect"
        
        # Check buying power for BUY orders
        if side == "BUY":
            total_cost = current_price * quantity
            margin_required = total_cost * self.constraints.get("margin_requirement", 0.50)
            
            if participant.current_cash < margin_required:
                return False, f"Insufficient buying power. Required: ${margin_required:.2f}, Available: ${participant.current_cash:.2f}"
        
        # Validate tick size
        if limit_price:
            min_tick = self.constraints.get("min_tick_size", 0.01)
            if round(limit_price / min_tick) * min_tick != limit_price:
                return False, f"Price must be in increments of {min_tick}"
        
        return True, None
    
    def execute_market_order(
        self,
        order: SimulationOrder,
        participant: SimulationParticipant,
        historical_time: datetime,
        db: Session
    ) -> bool:
        """
        Execute a market order immediately at current price - FIXED
        """
        try:
            current_price = self.data_loader.get_price_at_time(
                self.crisis_type, order.symbol, historical_time
            )
            
            if not current_price:
                order.status = "REJECTED"
                order.rejection_reason = "Price not available"
                db.commit()
                return False
            
            # Add slippage
            slippage = 0.0005
            execution_price = current_price * (1 + slippage if order.side == "BUY" else 1 - slippage)
            
            # Calculate commission
            commission_rate = self.constraints.get("commission_rate", 0.001)
            commission = execution_price * order.quantity * commission_rate
            
            # Update order status
            order.filled_price = round(execution_price, 2)
            order.filled_quantity = order.quantity
            order.commission = round(commission, 2)
            order.status = "FILLED"
            order.filled_at_historical = historical_time
            order.filled_at_real = datetime.utcnow()
            
            # Update participant cash
            if order.side == "BUY":
                total_cost = (execution_price * order.quantity) + commission
                participant.current_cash -= total_cost
            else:  # SELL
                total_proceeds = (execution_price * order.quantity) - commission
                participant.current_cash += total_proceeds
            
            # Update position - CRITICAL FIX
            self._update_position(order, participant, execution_price, db)
            
            # Update trade statistics
            participant.total_trades += 1
            
            db.commit()
            
            logger.info(
                f"Executed MARKET {order.side} {order.quantity} {order.symbol} @ ${execution_price:.2f} "
                f"for participant {participant.user_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            db.rollback()
            order.status = "REJECTED"
            order.rejection_reason = str(e)
            db.commit()
            return False
    
    def execute_limit_order(
        self,
        order: SimulationOrder,
        participant: SimulationParticipant,
        historical_time: datetime,
        db: Session
    ) -> bool:
        """
        Check and execute limit order if price condition met - FIXED
        """
        try:
            current_price = self.data_loader.get_price_at_time(
                self.crisis_type, order.symbol, historical_time
            )
            
            if not current_price:
                return False
            
            # Check if limit condition is met
            should_execute = False
            
            if order.side == "BUY" and current_price <= order.limit_price:
                should_execute = True
                execution_price = min(order.limit_price, current_price)
            elif order.side == "SELL" and current_price >= order.limit_price:
                should_execute = True
                execution_price = max(order.limit_price, current_price)
            
            if should_execute:
                commission_rate = self.constraints.get("commission_rate", 0.001)
                commission = execution_price * order.quantity * commission_rate
                
                order.filled_price = round(execution_price, 2)
                order.filled_quantity = order.quantity
                order.commission = round(commission, 2)
                order.status = "FILLED"
                order.filled_at_historical = historical_time
                order.filled_at_real = datetime.utcnow()
                
                if order.side == "BUY":
                    total_cost = (execution_price * order.quantity) + commission
                    participant.current_cash -= total_cost
                else:
                    total_proceeds = (execution_price * order.quantity) - commission
                    participant.current_cash += total_proceeds
                
                self._update_position(order, participant, execution_price, db)
                participant.total_trades += 1
                
                db.commit()
                
                logger.info(
                    f"Executed LIMIT {order.side} {order.quantity} {order.symbol} @ ${execution_price:.2f}"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing limit order: {e}")
            return False
    
    def execute_stop_order(
        self,
        order: SimulationOrder,
        participant: SimulationParticipant,
        historical_time: datetime,
        db: Session
    ) -> bool:
        """
        Check and execute stop order if price condition met - FIXED
        """
        try:
            current_price = self.data_loader.get_price_at_time(
                self.crisis_type, order.symbol, historical_time
            )
            
            if not current_price:
                return False
            
            # Check if stop condition is met
            should_execute = False
            
            # Stop loss: triggers when price falls below stop price
            if order.side == "SELL" and current_price <= order.stop_price:
                should_execute = True
                execution_price = current_price
            # Stop buy: triggers when price rises above stop price
            elif order.side == "BUY" and current_price >= order.stop_price:
                should_execute = True
                execution_price = current_price
            
            if should_execute:
                commission_rate = self.constraints.get("commission_rate", 0.001)
                commission = execution_price * order.quantity * commission_rate
                
                order.filled_price = round(execution_price, 2)
                order.filled_quantity = order.quantity
                order.commission = round(commission, 2)
                order.status = "FILLED"
                order.filled_at_historical = historical_time
                order.filled_at_real = datetime.utcnow()
                
                if order.side == "BUY":
                    total_cost = (execution_price * order.quantity) + commission
                    participant.current_cash -= total_cost
                else:
                    total_proceeds = (execution_price * order.quantity) - commission
                    participant.current_cash += total_proceeds
                
                self._update_position(order, participant, execution_price, db)
                participant.total_trades += 1
                
                db.commit()
                
                logger.info(
                    f"Executed STOP {order.side} {order.quantity} {order.symbol} @ ${execution_price:.2f}"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing stop order: {e}")
            return False
        
    def _update_position(
        self,
        order: SimulationOrder,
        participant: SimulationParticipant,
        execution_price: float,
        db: Session
    ):
        """
        Update participant's position after order execution - COMPLETELY FIXED
        """
        position = db.query(SimulationPosition).filter(
            SimulationPosition.participant_id == participant.id,
            SimulationPosition.symbol == order.symbol
        ).first()
        
        if order.side == "BUY":
            if position:
                # Adding to existing position
                total_cost = (position.average_cost * abs(position.quantity)) + (execution_price * order.quantity)
                
                if position.quantity < 0:
                    # Covering short position
                    position.quantity += order.quantity
                    
                    if position.quantity <= 0:
                        # Still short or flat
                        if position.quantity == 0:
                            # Fully covered - delete position
                            db.delete(position)
                        else:
                            # Partially covered - keep short
                            pass
                    else:
                        # Overcovered - now long
                        position.average_cost = execution_price
                else:
                    # Adding to long position
                    position.quantity += order.quantity
                    position.average_cost = total_cost / position.quantity
            else:
                # Creating new long position
                position = SimulationPosition(
                    participant_id=participant.id,
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_cost=execution_price,
                    realized_pnl=0.0,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0
                )
                db.add(position)
        
        else:  # SELL
            if position:
                if position.quantity > 0:
                    # Selling from long position
                    sell_quantity = min(order.quantity, position.quantity)
                    realized_pnl = (execution_price - position.average_cost) * sell_quantity
                    position.realized_pnl += realized_pnl
                    position.quantity -= sell_quantity
                    
                    # Check if we sold more than we had (short sale)
                    if order.quantity > sell_quantity:
                        short_quantity = order.quantity - sell_quantity
                        position.quantity = -short_quantity
                        position.average_cost = execution_price
                    elif position.quantity == 0:
                        # Position fully closed
                        db.delete(position)
                elif position.quantity < 0:
                    # Adding to short position
                    total_proceeds = (position.average_cost * abs(position.quantity)) + (execution_price * order.quantity)
                    position.quantity -= order.quantity
                    position.average_cost = total_proceeds / abs(position.quantity)
                else:
                    # quantity is 0 - shouldn't happen but handle it
                    position.quantity = -order.quantity
                    position.average_cost = execution_price
            else:
                # Creating new short position
                position = SimulationPosition(
                    participant_id=participant.id,
                    symbol=order.symbol,
                    quantity=-order.quantity,
                    average_cost=execution_price,
                    realized_pnl=0.0,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0
                )
                db.add(position)
        
    def calculate_portfolio_value(
        self,
        participant: SimulationParticipant,
        historical_time: datetime,
        db: Session
    ) -> float:
        """
        Calculate total portfolio value at current time - FIXED
        """
        total_value = participant.current_cash
        
        positions = db.query(SimulationPosition).filter(
            SimulationPosition.participant_id == participant.id
        ).all()
        
        for position in positions:
            current_price = self.data_loader.get_price_at_time(
                self.crisis_type, position.symbol, historical_time
            )
            
            if current_price:
                # Position value calculation
                if position.quantity > 0:
                    # Long position: value = quantity * current_price
                    position_value = position.quantity * current_price
                    unrealized_pnl = (current_price - position.average_cost) * position.quantity
                else:
                    # Short position: value = initial_proceeds - current_cost
                    # When short: we received money, now we owe shares
                    position_value = position.quantity * current_price  # Negative value
                    unrealized_pnl = (position.average_cost - current_price) * abs(position.quantity)
                
                total_value += position_value
                
                # Update position metrics
                position.current_price = current_price
                position.unrealized_pnl = unrealized_pnl
                
                cost_basis = position.average_cost * abs(position.quantity)
                if cost_basis > 0:
                    position.unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100
                else:
                    position.unrealized_pnl_pct = 0.0
        
        db.commit()
        
        return total_value