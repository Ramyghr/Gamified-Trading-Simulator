"""
Margin and Risk Management Service
Handles leverage calculations, margin requirements, liquidation prices, and PnL.
Save as: app/services/margin_service.py
"""

from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from typing import Optional, Tuple, Dict
import logging
from datetime import datetime

getcontext().prec = 18
getcontext().rounding = ROUND_HALF_EVEN

logger = logging.getLogger(__name__)


class MarginService:
    """
    Service for calculating margin requirements, liquidation prices, and PnL
    for leveraged trading positions.
    """
    
    def __init__(self):
        # Margin configuration (adjustable per trading pair)
        self.initial_margin_rate = Decimal("0.10")  # 10% (for 10x max leverage)
        self.maintenance_margin_rate = Decimal("0.05")  # 5% (liquidation threshold)
        self.liquidation_fee_rate = Decimal("0.005")  # 0.5% liquidation fee
        
        # Leverage limits
        self.min_leverage = Decimal("1")
        self.max_leverage = Decimal("100")  # Adjustable per asset
        
        # Risk limits
        self.margin_call_threshold = Decimal("0.10")  # 10% above maintenance margin
    
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
    
    def validate_leverage(self, leverage: Decimal, asset_type: str = "STOCK") -> bool:
        """Validate if leverage is within allowed limits"""
        leverage = self._to_decimal(leverage)
        
        # Different max leverage for different assets
        max_allowed = {
            "STOCK": Decimal("10"),
            "CRYPTO": Decimal("100"),
            "FOREX": Decimal("50")
        }.get(asset_type, Decimal("10"))
        
        return self.min_leverage <= leverage <= max_allowed
    
    def calculate_margin_required(
        self,
        position_size: Decimal,
        entry_price: Decimal,
        leverage: Decimal
    ) -> Decimal:
        """
        Calculate initial margin required to open a position.
        
        Formula: Margin = (Position Size × Entry Price) / Leverage
        """
        position_size = self._to_decimal(position_size)
        entry_price = self._to_decimal(entry_price)
        leverage = self._to_decimal(leverage)
        
        if leverage <= 0:
            raise ValueError("Leverage must be greater than 0")
        
        position_value = position_size * entry_price
        margin_required = position_value / leverage
        
        logger.info(
            f"Margin calculation: Size={position_size}, Price={entry_price}, "
            f"Leverage={leverage}x → Margin={margin_required}"
        )
        
        return margin_required
    
    def calculate_maintenance_margin(
        self,
        position_value: Decimal
    ) -> Decimal:
        """
        Calculate maintenance margin (minimum margin to keep position open).
        
        Formula: MM = Position Value × Maintenance Margin Rate
        """
        position_value = self._to_decimal(position_value)
        maintenance_margin = position_value * self.maintenance_margin_rate
        
        return maintenance_margin
    
    def calculate_liquidation_price_long(
        self,
        entry_price: Decimal,
        leverage: Decimal,
        maintenance_margin_rate: Optional[Decimal] = None,
        initial_margin_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate liquidation price for LONG position.
        
        Formula: P_liq = Entry × (1 - (Leverage / (1 + Leverage)) × (1 - MM/IM))
        
        Simplified: P_liq = Entry × (1 - 1/Leverage + MM/(1 + Leverage))
        """
        entry_price = self._to_decimal(entry_price)
        leverage = self._to_decimal(leverage)
        mm_rate = self._to_decimal(maintenance_margin_rate or self.maintenance_margin_rate)
        im_rate = self._to_decimal(initial_margin_rate or self.initial_margin_rate)
        
        # More intuitive formula
        leverage_factor = leverage / (Decimal('1') + leverage)
        margin_factor = Decimal('1') - (mm_rate / im_rate)
        
        liquidation_price = entry_price * (Decimal('1') - (leverage_factor * margin_factor))
        
        logger.info(
            f"Long liquidation: Entry={entry_price}, Leverage={leverage}x → "
            f"Liq Price={liquidation_price}"
        )
        
        return max(liquidation_price, Decimal('0.01'))  # Ensure positive
    
    def calculate_liquidation_price_short(
        self,
        entry_price: Decimal,
        leverage: Decimal,
        maintenance_margin_rate: Optional[Decimal] = None,
        initial_margin_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate liquidation price for SHORT position.
        
        Formula: P_liq = Entry × (1 + (Leverage / (1 + Leverage)) × (1 - MM/IM))
        """
        entry_price = self._to_decimal(entry_price)
        leverage = self._to_decimal(leverage)
        mm_rate = self._to_decimal(maintenance_margin_rate or self.maintenance_margin_rate)
        im_rate = self._to_decimal(initial_margin_rate or self.initial_margin_rate)
        
        leverage_factor = leverage / (Decimal('1') + leverage)
        margin_factor = Decimal('1') - (mm_rate / im_rate)
        
        liquidation_price = entry_price * (Decimal('1') + (leverage_factor * margin_factor))
        
        logger.info(
            f"Short liquidation: Entry={entry_price}, Leverage={leverage}x → "
            f"Liq Price={liquidation_price}"
        )
        
        return liquidation_price
    
    def calculate_unrealized_pnl_long(
        self,
        quantity: Decimal,
        entry_price: Decimal,
        current_price: Decimal
    ) -> Decimal:
        """
        Calculate unrealized PnL for LONG position.
        
        Formula: UPnL = (Current Price - Entry Price) × Quantity
        """
        quantity = self._to_decimal(quantity)
        entry_price = self._to_decimal(entry_price)
        current_price = self._to_decimal(current_price)
        
        pnl = (current_price - entry_price) * quantity
        
        return pnl
    
    def calculate_unrealized_pnl_short(
        self,
        quantity: Decimal,
        entry_price: Decimal,
        current_price: Decimal
    ) -> Decimal:
        """
        Calculate unrealized PnL for SHORT position.
        
        Formula: UPnL = (Entry Price - Current Price) × Quantity
        """
        quantity = self._to_decimal(quantity)
        entry_price = self._to_decimal(entry_price)
        current_price = self._to_decimal(current_price)
        
        pnl = (entry_price - current_price) * quantity
        
        return pnl
    
    def calculate_equity(
        self,
        wallet_balance: Decimal,
        unrealized_pnl: Decimal
    ) -> Decimal:
        """
        Calculate account equity.
        
        Formula: Equity = Wallet Balance + Unrealized PnL
        """
        wallet_balance = self._to_decimal(wallet_balance)
        unrealized_pnl = self._to_decimal(unrealized_pnl)
        
        equity = wallet_balance + unrealized_pnl
        
        return equity
    
    def calculate_margin_level(
        self,
        equity: Decimal,
        margin_used: Decimal
    ) -> Decimal:
        """
        Calculate margin level percentage.
        
        Formula: Margin Level = (Equity / Margin Used) × 100
        
        Returns:
            Margin level as percentage. 
            - Above 100%: Safe
            - Below 100%: At risk
            - Below maintenance threshold: Liquidation
        """
        equity = self._to_decimal(equity)
        margin_used = self._to_decimal(margin_used)
        
        if margin_used <= 0:
            return Decimal('999999')  # Infinite margin level (no positions)
        
        margin_level = (equity / margin_used) * Decimal('100')
        
        return margin_level
    
    def calculate_available_margin(
        self,
        equity: Decimal,
        margin_used: Decimal
    ) -> Decimal:
        """
        Calculate free margin available for new positions.
        
        Formula: Available Margin = Equity - Margin Used
        """
        equity = self._to_decimal(equity)
        margin_used = self._to_decimal(margin_used)
        
        available = equity - margin_used
        
        return max(available, Decimal('0'))
    
    def calculate_max_position_size(
        self,
        available_margin: Decimal,
        entry_price: Decimal,
        leverage: Decimal
    ) -> Decimal:
        """
        Calculate maximum position size that can be opened.
        
        Formula: Max Size = (Available Margin × Leverage) / Entry Price
        """
        available_margin = self._to_decimal(available_margin)
        entry_price = self._to_decimal(entry_price)
        leverage = self._to_decimal(leverage)
        
        if entry_price <= 0:
            return Decimal('0')
        
        max_size = (available_margin * leverage) / entry_price
        
        return max_size
    
    def check_liquidation_risk(
        self,
        current_price: Decimal,
        liquidation_price: Decimal,
        side: str
    ) -> Tuple[bool, Decimal]:
        """
        Check if position should be liquidated.
        
        Returns:
            (should_liquidate, distance_from_liquidation)
        """
        current_price = self._to_decimal(current_price)
        liquidation_price = self._to_decimal(liquidation_price)
        
        if side == "LONG":
            should_liquidate = current_price <= liquidation_price
            distance = ((current_price - liquidation_price) / liquidation_price) * Decimal('100')
        else:  # SHORT
            should_liquidate = current_price >= liquidation_price
            distance = ((liquidation_price - current_price) / liquidation_price) * Decimal('100')
        
        return should_liquidate, distance
    
    def calculate_liquidation_fee(
        self,
        position_value: Decimal
    ) -> Decimal:
        """Calculate fee charged on liquidation"""
        position_value = self._to_decimal(position_value)
        fee = position_value * self.liquidation_fee_rate
        
        return fee
    
    def calculate_position_metrics(
        self,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        current_price: Decimal,
        leverage: Decimal,
        margin_used: Decimal
    ) -> Dict:
        """
        Calculate comprehensive position metrics.
        
        Returns dictionary with:
        - unrealized_pnl
        - liquidation_price
        - margin_level
        - pnl_percentage
        - roi (return on initial margin)
        """
        quantity = self._to_decimal(quantity)
        entry_price = self._to_decimal(entry_price)
        current_price = self._to_decimal(current_price)
        leverage = self._to_decimal(leverage)
        margin_used = self._to_decimal(margin_used)
        
        # Calculate PnL
        if side == "LONG":
            unrealized_pnl = self.calculate_unrealized_pnl_long(quantity, entry_price, current_price)
            liquidation_price = self.calculate_liquidation_price_long(entry_price, leverage)
        else:
            unrealized_pnl = self.calculate_unrealized_pnl_short(quantity, entry_price, current_price)
            liquidation_price = self.calculate_liquidation_price_short(entry_price, leverage)
        
        # Calculate metrics
        position_value = quantity * entry_price
        pnl_percentage = (unrealized_pnl / position_value) * Decimal('100') if position_value > 0 else Decimal('0')
        roi = (unrealized_pnl / margin_used) * Decimal('100') if margin_used > 0 else Decimal('0')
        
        # Liquidation risk
        should_liquidate, distance_from_liq = self.check_liquidation_risk(
            current_price, liquidation_price, side
        )
        
        return {
            "unrealized_pnl": float(unrealized_pnl),
            "liquidation_price": float(liquidation_price),
            "pnl_percentage": float(pnl_percentage),
            "roi": float(roi),
            "position_value": float(position_value),
            "should_liquidate": should_liquidate,
            "distance_from_liquidation": float(distance_from_liq)
        }
    
    def validate_position_open(
        self,
        available_margin: Decimal,
        required_margin: Decimal,
        leverage: Decimal,
        asset_type: str = "STOCK"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a position can be opened.
        
        Returns:
            (is_valid, error_message)
        """
        available_margin = self._to_decimal(available_margin)
        required_margin = self._to_decimal(required_margin)
        leverage = self._to_decimal(leverage)
        
        # Check leverage limits
        if not self.validate_leverage(leverage, asset_type):
            return False, f"Leverage {leverage}x exceeds maximum allowed for {asset_type}"
        
        # Check margin availability
        if available_margin < required_margin:
            return False, f"Insufficient margin. Required: {required_margin}, Available: {available_margin}"
        
        return True, None
    
    def calculate_funding_rate_payment(
        self,
        position_value: Decimal,
        funding_rate: Decimal,
        side: str
    ) -> Decimal:
        """
        Calculate funding rate payment for perpetual contracts.
        
        Args:
            position_value: Size × Current Price
            funding_rate: Current funding rate (e.g., 0.0001 = 0.01%)
            side: LONG or SHORT
        
        Returns:
            Payment amount (positive = pay, negative = receive)
        """
        position_value = self._to_decimal(position_value)
        funding_rate = self._to_decimal(funding_rate)
        
        payment = position_value * funding_rate
        
        # Longs pay when funding is positive, shorts pay when negative
        if side == "SHORT":
            payment = -payment
        
        return payment


# Global service instance
margin_service = MarginService()