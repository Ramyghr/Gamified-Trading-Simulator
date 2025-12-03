"""
Pydantic schemas for Crisis Simulation API - Enhanced Version
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class CrisisTypeEnum(str, Enum):
    """Available crisis types"""
    GREAT_DEPRESSION = "great_depression"
    BLACK_MONDAY = "black_monday"
    DOTCOM_BUBBLE = "dotcom_bubble"
    FINANCIAL_CRISIS_2008 = "financial_crisis_2008"
    COVID_CRASH = "covid_crash"


class SimulationStatusEnum(str, Enum):
    """Simulation status"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class CreateSimulationRequest(BaseModel):
    """Request to create a new simulation"""
    crisis_type: CrisisTypeEnum
    max_participants: int = Field(default=100, ge=1, le=1000)
    is_competitive: bool = Field(default=True)


class JoinSimulationRequest(BaseModel):
    """Request to join a simulation"""
    initial_cash: float = Field(default=100000.0, ge=10000, le=10000000)


class PlaceOrderRequest(BaseModel):
    """Request to place an order in simulation"""
    symbol: str = Field(..., min_length=1, max_length=20)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., gt=0)
    order_type: str = Field(..., pattern="^(MARKET|LIMIT|STOP)$")
    limit_price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SimulationPhaseInfo(BaseModel):
    """Information about a simulation phase"""
    name: str
    historical_start: datetime
    historical_end: datetime
    real_duration_minutes: float
    compression_ratio: float


class SimulationResponse(BaseModel):
    """Response with simulation details"""
    id: int
    crisis_type: str
    status: str
    real_start_time: Optional[datetime]
    real_end_time: Optional[datetime]
    historical_start_date: datetime
    historical_end_date: datetime
    current_historical_time: Optional[datetime]
    current_phase: Optional[str]
    duration_minutes: int
    max_participants: int
    is_competitive: bool
    participant_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress_percentage: Optional[float]
    
    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    """Response with participant details"""
    id: int
    user_id: int
    simulation_id: int
    joined_at: datetime
    is_active: bool
    initial_cash: float
    current_cash: float
    current_portfolio_value: Optional[float]
    current_total_value: Optional[float]
    total_return_pct: float
    max_drawdown_pct: float
    total_trades: int
    profitable_trades: int
    final_rank: Optional[int]
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Response with order details"""
    id: int
    symbol: str
    order_type: str
    side: str
    quantity: float
    limit_price: Optional[float]
    stop_price: Optional[float]
    filled_price: Optional[float]
    filled_quantity: float
    status: str
    placed_at_historical: datetime
    filled_at_historical: Optional[datetime]
    commission: float
    rejection_reason: Optional[str]
    
    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """Response with position details"""
    id: int
    symbol: str
    quantity: float
    average_cost: float
    current_price: Optional[float]
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float
    position_type: str  # NEW: "LONG" or "SHORT"
    market_value: Optional[float]  # NEW
    opened_at: datetime
    
    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    user_id: int
    total_value: float
    total_return_pct: float
    profit_loss: float  # NEW
    initial_value: float  # NEW
    max_drawdown_pct: float  # NEW
    sharpe_ratio: Optional[float]
    competition_score: float
    
    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    """Full leaderboard response"""
    simulation_id: int
    entries: List[LeaderboardEntry]
    snapshot_at_historical: datetime
    total_participants: int


class MarketDataResponse(BaseModel):
    """Current market data during simulation"""
    symbol: str
    current_price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    historical_time: datetime
    simulation_phase: Optional[str]  # NEW


class AvailableAssetsResponse(BaseModel):
    """Available assets in a crisis"""
    crisis_type: str
    assets: List[str]
    date_range_start: datetime
    date_range_end: datetime


class SimulationStateResponse(BaseModel):
    """Complete simulation state for a participant"""
    simulation: SimulationResponse
    participant: ParticipantResponse
    positions: List[PositionResponse]
    recent_orders: List[OrderResponse]
    current_rank: Optional[int]
    total_participants: int


class SimulationControlResponse(BaseModel):
    """Response for control actions"""
    success: bool
    message: str
    simulation_id: int
    new_status: Optional[str]


class SimulationHistoryResponse(BaseModel):
    """Historical simulation record"""
    id: int
    crisis_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_minutes: int
    participant_count: int
    is_competitive: bool
    historical_start_date: datetime
    historical_end_date: datetime
    
    class Config:
        from_attributes = True


class SimulationStatsResponse(BaseModel):
    """Aggregate statistics for a simulation"""
    simulation_id: int
    crisis_type: str
    status: str
    total_participants: int
    active_participants: int
    total_trades: int
    average_return_pct: float
    max_return_pct: float
    min_return_pct: float
    duration_minutes: int
    elapsed_minutes: float


class ParticipantStatsResponse(BaseModel):
    """Detailed participant statistics"""
    participant_id: int
    user_id: int
    total_return_pct: float
    initial_value: float  # NEW
    current_cash: float
    current_portfolio_value: float
    current_total_value: float
    profit_loss: float  # NEW
    max_drawdown_pct: float
    sharpe_ratio: Optional[float]
    total_trades: int
    profitable_trades: int
    total_orders: int
    filled_orders: int
    active_positions: int
    current_rank: Optional[int]
    max_leverage_used: float
    margin_calls_count: int


class CrisisTypeInfo(BaseModel):
    """Information about a crisis type"""
    type: str
    name: str
    asset_count: int
    date_range_start: str
    date_range_end: str
    duration_days: int
    available: bool
    description: Optional[str] = None


class PhaseTimelineEntry(BaseModel):
    """Entry in simulation timeline"""
    phase: str
    historical_start: str
    historical_end: str
    real_duration_minutes: float
    compression_ratio: float


class HealthResponse(BaseModel):
    """Simulator health status"""
    status: str
    active_simulations: int
    pending_simulations: int
    total_active_participants: int
    timestamp: str