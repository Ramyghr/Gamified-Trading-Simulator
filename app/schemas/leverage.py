"""
API Schemas for Leverage Trading
Add these to your existing app/schemas/order.py or create app/schemas/leverage.py
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OpenPositionRequest(BaseModel):
    """Request to open a leveraged position"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    side: PositionSide = Field(..., description="Position side (LONG or SHORT)")
    quantity: Decimal = Field(..., gt=0, description="Position size")
    leverage: Decimal = Field(..., gt=1, le=100, description="Leverage multiplier (e.g., 10 for 10x)")
    order_type: str = Field(default="MARKET", description="MARKET or LIMIT")
    limit_price: Optional[Decimal] = Field(None, gt=0, description="Limit price for LIMIT orders")
    stop_loss: Optional[Decimal] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[Decimal] = Field(None, gt=0, description="Take profit price")
    
    @validator('symbol')
    def symbol_uppercase(cls, v):
        return v.upper().strip()
    
    @validator('limit_price')
    def validate_limit_price(cls, v, values):
        order_type = values.get('order_type')
        if order_type == 'LIMIT' and v is None:
            raise ValueError("limit_price is required for LIMIT orders")
        return v
    
    @validator('stop_loss')
    def validate_stop_loss(cls, v, values):
        if v is not None:
            side = values.get('side')
            limit_price = values.get('limit_price')
            entry = limit_price if limit_price else None
            
            if entry and side == PositionSide.LONG and v >= entry:
                raise ValueError("Stop loss must be below entry price for LONG positions")
            if entry and side == PositionSide.SHORT and v <= entry:
                raise ValueError("Stop loss must be above entry price for SHORT positions")
        return v
    
    @validator('take_profit')
    def validate_take_profit(cls, v, values):
        if v is not None:
            side = values.get('side')
            limit_price = values.get('limit_price')
            entry = limit_price if limit_price else None
            
            if entry and side == PositionSide.LONG and v <= entry:
                raise ValueError("Take profit must be above entry price for LONG positions")
            if entry and side == PositionSide.SHORT and v >= entry:
                raise ValueError("Take profit must be below entry price for SHORT positions")
        return v


class ClosePositionRequest(BaseModel):
    """Request to close a leveraged position"""
    position_id: int = Field(..., description="Position ID to close")
    quantity: Optional[Decimal] = Field(None, gt=0, description="Quantity to close (None = close all)")
    exit_price: Optional[Decimal] = Field(None, gt=0, description="Override exit price (for LIMIT close)")


class PositionResponse(BaseModel):
    """Response with position details"""
    id: int
    portfolio_id: int
    user_id: int
    symbol: str
    asset_type: str
    side: PositionSide
    
    # Quantities and pricing
    quantity: Decimal
    entry_price: Decimal
    current_price: Optional[Decimal]
    
    # Leverage and margin
    leverage: Decimal
    margin_used: Decimal
    position_value: Decimal
    
    # PnL
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    pnl_percentage: Optional[float] = None
    roi: Optional[float] = None
    
    # Risk management
    liquidation_price: Decimal
    maintenance_margin: Decimal
    initial_margin: Decimal
    distance_from_liquidation: Optional[float] = None
    
    # Stop loss / Take profit
    stop_loss_price: Optional[Decimal]
    take_profit_price: Optional[Decimal]
    
    # Status
    is_open: bool
    is_liquidated: bool
    
    # Fees and funding
    total_fees: Decimal
    accumulated_funding: Decimal
    
    # Timestamps
    opened_at: datetime
    closed_at: Optional[datetime]
    last_price_update: Optional[datetime]
    
    class Config:
        from_attributes = True


class PositionMetrics(BaseModel):
    """Detailed position metrics"""
    position_id: int
    symbol: str
    side: PositionSide
    
    # Current state
    current_price: Decimal
    entry_price: Decimal
    quantity: Decimal
    
    # PnL metrics
    unrealized_pnl: Decimal
    unrealized_pnl_pct: float
    roi: float  # Return on initial margin
    
    # Risk metrics
    liquidation_price: Decimal
    distance_from_liquidation: float  # Percentage
    margin_level: float
    leverage: Decimal
    
    # Values
    position_value: Decimal
    margin_used: Decimal
    maintenance_margin: Decimal


class ClosePositionResponse(BaseModel):
    """Response after closing a position"""
    success: bool
    message: str
    position_id: int
    closed_quantity: Decimal
    exit_price: Decimal
    pnl: Decimal
    fee: Decimal
    net_pnl: Decimal
    margin_released: Decimal
    is_full_close: bool


class MarginInfoResponse(BaseModel):
    """Portfolio margin information"""
    cash_balance: Decimal
    equity: Decimal
    margin_used: Decimal
    margin_available: Decimal
    margin_level: float
    total_exposure: Decimal
    unrealized_pnl: Decimal
    
    # Limits
    max_leverage: Decimal
    
    # Position summary
    open_positions_count: int
    total_position_value: Decimal


class LeverageCalculatorRequest(BaseModel):
    """Request to calculate leverage requirements"""
    symbol: str
    side: PositionSide
    quantity: Decimal = Field(..., gt=0)
    leverage: Decimal = Field(..., gt=1, le=100)
    entry_price: Optional[Decimal] = Field(None, gt=0, description="Use market price if None")


class LeverageCalculatorResponse(BaseModel):
    """Response with leverage calculations"""
    symbol: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    leverage: Decimal
    
    # Margin requirements
    margin_required: Decimal
    maintenance_margin: Decimal
    position_value: Decimal
    
    # Risk metrics
    liquidation_price: Decimal
    max_loss: Decimal
    max_gain: Optional[Decimal]
    
    # Fees
    estimated_open_fee: Decimal
    estimated_close_fee: Decimal
    total_estimated_fees: Decimal
    
    # Profitability scenarios
    break_even_price: Decimal
    profit_at_10_pct: Decimal
    profit_at_20_pct: Decimal
    loss_at_10_pct: Decimal
    loss_at_20_pct: Decimal


class LiquidationEventResponse(BaseModel):
    """Response with liquidation event details"""
    id: int
    user_id: int
    position_id: int
    symbol: str
    side: PositionSide
    
    # Liquidation details
    quantity: Decimal
    entry_price: Decimal
    liquidation_price: Decimal
    actual_liquidation_price: Decimal
    
    # Financial impact
    margin_used: Decimal
    loss_amount: Decimal
    liquidation_fee: Decimal
    
    # Context
    equity_before: Decimal
    equity_after: Decimal
    margin_level_before: float
    
    reason: Optional[str]
    liquidated_at: datetime
    
    class Config:
        from_attributes = True


class PositionListQuery(BaseModel):
    """Query parameters for listing positions"""
    symbol: Optional[str] = None
    side: Optional[PositionSide] = None
    is_open: bool = True
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class PortfolioSummary(BaseModel):
    """Enhanced portfolio summary with margin metrics"""
    # Cash and equity
    cash_balance: Decimal
    equity: Decimal
    total_value: Decimal
    
    # Margin
    margin_used: Decimal
    margin_available: Decimal
    margin_level: float
    
    # PnL
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    
    # Positions
    open_positions: int
    total_exposure: Decimal
    avg_leverage: Optional[float]
    
    # Performance
    total_return: Decimal
    total_return_pct: float
    daily_return: Decimal
    daily_return_pct: float
    
    # Risk
    liquidation_risk: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    positions_at_risk: int
    
    last_updated: datetime


class UpdateStopLossRequest(BaseModel):
    """Request to update stop loss for a position"""
    position_id: int
    stop_loss_price: Optional[Decimal] = Field(None, gt=0)


class UpdateTakeProfitRequest(BaseModel):
    """Request to update take profit for a position"""
    position_id: int
    take_profit_price: Optional[Decimal] = Field(None, gt=0)


class PositionHistory(BaseModel):
    """Historical position data"""
    positions: List[PositionResponse]
    total_positions: int
    total_profit: Decimal
    total_loss: Decimal
    win_rate: float
    avg_profit: Decimal
    avg_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal


class MarginCallAlert(BaseModel):
    """Margin call alert notification"""
    alert_type: str = "MARGIN_CALL"
    position_id: int
    symbol: str
    current_margin_level: float
    distance_from_liquidation: float
    recommended_action: str
    timestamp: datetime


class RiskMetrics(BaseModel):
    """Portfolio risk metrics for leverage trading"""
    total_exposure: Decimal
    max_exposure_allowed: Decimal
    exposure_utilization: float  # Percentage
    
    margin_utilization: float  # Margin used / Equity
    average_leverage: float
    max_leverage_in_use: float
    
    value_at_risk_1pct: Decimal  # VaR if market moves 1%
    value_at_risk_5pct: Decimal  # VaR if market moves 5%
    
    positions_near_liquidation: int
    estimated_liquidation_buffer: Decimal  # How much equity before first liquidation


class FundingRateInfo(BaseModel):
    """Funding rate information for perpetual contracts"""
    symbol: str
    current_funding_rate: Decimal
    next_funding_time: datetime
    estimated_payment: Decimal  # For user's positions
    historical_avg_rate: Optional[Decimal]