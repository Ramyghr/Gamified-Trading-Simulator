from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal
class AssetType(str, Enum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    CASH = "CASH"

# ============= Holdings =============

class HoldingBase(BaseModel):
    symbol: str
    asset_type: AssetType
    quantity: float
    average_buy_price: float

class HoldingResponse(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    asset_type: AssetType
    quantity: float
    average_buy_price: float
    current_price: Optional[float] = None
    last_price_update: Optional[datetime] = None
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    
    model_config = ConfigDict(from_attributes=True)

class HoldingsPaginated(BaseModel):
    items: List[HoldingResponse]
    total: int
    page: int
    size: int
    pages: int

# ============= Portfolio Overview =============

# class PortfolioOverview(BaseModel):
#     total_value: float
#     cash_balance: float
#     holdings_value: float
#     initial_balance: float
    
#     # P&L
#     total_gain: float
#     total_gain_pct: float
#     daily_gain: float
#     daily_gain_pct: float
    
#     # Asset allocation
#     cash_allocation_pct: float
#     holdings_allocation_pct: float
    
#     last_updated: datetime
class PortfolioOverview(BaseModel):
    """Enhanced portfolio overview including leverage metrics"""
    total_value: float
    cash_balance: float
    holdings_value: float
    initial_balance: float
    total_gain: float
    total_gain_pct: float
    daily_gain: float
    daily_gain_pct: float
    cash_allocation_pct: float
    holdings_allocation_pct: float
    last_updated: Optional[datetime]
    
    # Leverage-specific fields
    leveraged_pnl: Optional[float] = Field(default=0.0, description="Unrealized P&L from leveraged positions")
    margin_used: Optional[float] = Field(default=0.0, description="Total margin currently used")
    margin_available: Optional[float] = Field(default=0.0, description="Available margin for trading")
    margin_level: Optional[float] = Field(default=0.0, description="Margin level percentage")
    total_exposure: Optional[float] = Field(default=0.0, description="Total leveraged exposure")

# ============= Portfolio Stats =============

# class PortfolioStats(BaseModel):
#     # Trade statistics
#     total_trades: int
#     winning_trades: int
#     losing_trades: int
#     win_rate: float
    
#     # P&L
#     realized_pnl: float
#     unrealized_pnl: float
#     total_pnl: float
    
#     # Performance
#     total_return: float
#     total_return_pct: float
#     daily_return: float
#     best_trade: float
#     worst_trade: float
#     avg_win: float
#     avg_loss: float
#     profit_factor: float
    
#     # Risk metrics
#     volatility: Optional[float] = None
#     sharpe_ratio: Optional[float] = None
#     max_drawdown: float
#     current_drawdown: float
    
#     last_updated: datetime
class PortfolioStats(BaseModel):
    """Enhanced statistics including leverage trading"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    total_return: float
    total_return_pct: float
    daily_return: float
    best_trade: float
    worst_trade: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    current_drawdown: float
    last_updated: datetime
    
    # Leverage-specific stats
    leveraged_trades: Optional[int] = Field(default=0, description="Number of leveraged trades")
    liquidations: Optional[int] = Field(default=0, description="Number of liquidations")
    avg_leverage_used: Optional[float] = Field(default=0.0, description="Average leverage across positions")

# ============= Portfolio History =============

class PortfolioHistoryPoint(BaseModel):
    timestamp: datetime
    total_value: float
    cash_balance: float
    holdings_value: float
    
    model_config = ConfigDict(from_attributes=True)

class PortfolioDailySnapshotResponse(BaseModel):
    date: datetime
    total_value: float
    cash_balance: float
    holdings_value: float
    daily_return: float
    total_return: float
    total_return_pct: float
    portfolio_rank: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

# ============= Rankings =============

class PortfolioRank(BaseModel):
    rank: int
    total_users: int
    percentile: float
    total_value: float
    total_return_pct: float
    top_10_threshold: float
    top_25_threshold: float

# ============= Best/Worst Holdings =============

class TopHolding(BaseModel):
    symbol: str
    asset_type: AssetType
    quantity: float
    average_buy_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

class BestWorstHoldings(BaseModel):
    best_performing: List[TopHolding]
    worst_performing: List[TopHolding]
    largest_positions: List[TopHolding]

# ============= Asset Allocation =============

class AssetAllocation(BaseModel):
    asset_type: AssetType
    total_value: float
    percentage: float
    holdings_count: int

class AllocationBreakdown(BaseModel):
    by_asset_type: List[AssetAllocation]
    total_holdings_value: float
    cash_balance: float
    total_value: float
    leveraged_exposure: Optional[float] = Field(default=0.0, description="Total leveraged exposure")

# ============= Margin Health Response =============

class MarginHealthResponse(BaseModel):
    """Margin health check response"""
    status: str = Field(description="HEALTHY, GOOD, WARNING, DANGER, MARGIN_CALL")
    risk_level: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL, LIQUIDATION")
    margin_level: float
    equity: float
    margin_used: float
    margin_available: float
    positions_at_risk: List[dict]
    positions_at_risk_count: int
    total_exposure: float
    recommendation: str
# ============= Performance Summary =============

class PerformanceOverview(BaseModel):
    """Overview section of performance"""
    total_value: float
    total_return: float
    total_return_pct: float
    cash_balance: float


class SpotTradingPerformance(BaseModel):
    """Spot trading performance metrics"""
    holdings_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    holdings_count: int


class LeveragedTradingPerformance(BaseModel):
    """Leveraged trading performance metrics"""
    unrealized_pnl: float
    margin_used: float
    margin_available: float
    roi: float
    open_positions: int
    total_exposure: float
    margin_level: float


class RiskMetricsResponse(BaseModel):
    """Risk metrics summary"""
    leverage_utilization: float
    exposure_ratio: float
    margin_health: str


class PortfolioPerformanceSummary(BaseModel):
    """Comprehensive performance summary"""
    overview: PerformanceOverview
    spot_trading: SpotTradingPerformance
    leveraged_trading: LeveragedTradingPerformance
    risk_metrics: RiskMetricsResponse
    last_updated: Optional[datetime]

# ============= Liquidation History =============

class LiquidationHistoryItem(BaseModel):
    """Single liquidation event"""
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    liquidation_price: float
    loss_amount: float
    liquidation_fee: float
    reason: Optional[str]
    liquidated_at: datetime


class LiquidationHistory(BaseModel):
    """Liquidation history response"""
    liquidations: List[LiquidationHistoryItem]
    total_liquidations: int
    total_loss: float
    most_recent: Optional[datetime]
# ============= Leveraged Position Summary =============

class LeveragedPositionSummary(BaseModel):
    """Summary of leveraged positions for a symbol"""
    symbol: str
    long_quantity: Decimal
    short_quantity: Decimal
    net_quantity: Decimal
    long_exposure: Decimal
    short_exposure: Decimal
    net_exposure: Decimal
    total_margin_used: Decimal
    weighted_avg_leverage: float
    positions_count: int
 
 # ============= Quick Stats Widget =============

class QuickStatsWidget(BaseModel):
    """Quick stats for dashboard widgets"""
    total_value: float
    daily_change: float
    daily_change_pct: float
    open_positions: int
    margin_health: str
    alert_level: str = Field(description="NONE, INFO, WARNING, DANGER")
    alerts_count: int


# ============= Trade Execution Impact =============

class TradeImpactAnalysis(BaseModel):
    """Analysis of how a trade would impact portfolio"""
    current_margin_level: float
    projected_margin_level: float
    current_exposure: float
    projected_exposure: float
    margin_required: float
    margin_available: float
    can_execute: bool
    risk_assessment: str
    warnings: List[str]

 # ============= Portfolio Comparison =============

class PortfolioComparison(BaseModel):
    """Compare current vs previous period"""
    current_value: float
    previous_value: float
    change_amount: float
    change_pct: float
    period: str = Field(description="daily, weekly, monthly")
    
    current_positions: int
    previous_positions: int
    positions_change: int
    
    current_leverage: float
    previous_leverage: float
    leverage_change: float


# ============= Position at Risk =============

class PositionAtRisk(BaseModel):
    """Position approaching liquidation"""
    position_id: int
    symbol: str
    side: str
    current_price: float
    liquidation_price: float
    distance_pct: float
    urgency: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")


# ============= Portfolio Performance Chart Data =============

class PerformanceChartData(BaseModel):
    dates: List[str]
    values: List[float]
    returns: List[float]
    benchmark_values: Optional[List[float]] = None

# ============= Detailed Position =============

# class DetailedPosition(BaseModel):
#     symbol: str
#     asset_type: AssetType
#     quantity: float
#     average_buy_price: float
#     current_price: float
#     market_value: float
#     cost_basis: float
#     unrealized_pnl: float
#     unrealized_pnl_pct: float
#     allocation_pct: float
#     last_price_update: Optional[datetime] = None
class DetailedPosition(BaseModel):
    """Detailed position for both spot and leveraged"""
    symbol: str
    asset_type: str
    position_type: str = Field(description="SPOT, LEVERAGE_LONG, or LEVERAGE_SHORT")
    quantity: float
    average_buy_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    allocation_pct: float
    last_price_update: Optional[datetime]
    
    # Leverage-specific fields (None for spot positions)
    leverage: Optional[float] = Field(default=None, description="Leverage multiplier")
    liquidation_price: Optional[float] = Field(default=None, description="Liquidation price")
    margin_used: Optional[float] = Field(default=None, description="Margin used for this position")

class PortfolioPositionsDetailed(BaseModel):
    positions: List[DetailedPosition]
    total_market_value: float
    total_cost_basis: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float

# ============= Transaction History =============

class TransactionResponse(BaseModel):
    id: int
    symbol: str
    action: str  # BUY or SELL
    quantity: float
    price: float
    total_amount: float
    transaction_date: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TransactionsPaginated(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int
    pages: int

# ============= Cash Balance =============

class CashBalanceResponse(BaseModel):
    cash_balance: float
    locked: bool
    available: float

# ============= Quantity Response =============

class QuantityResponse(BaseModel):
    symbol: str
    quantity: float
    asset_type: Optional[AssetType] = None

# ============= Refresh Response =============

class RefreshResponse(BaseModel):
    message: str
    updated_at: datetime
    total_value: float
    holdings_updated: int
# ============= Combined Portfolio Dashboard =============

class PortfolioDashboard(BaseModel):
    """Complete portfolio dashboard with all metrics"""
    overview: PortfolioOverview
    performance: PortfolioPerformanceSummary
    positions: PortfolioPositionsDetailed
    margin_health: MarginHealthResponse
    recent_liquidations: Optional[List[LiquidationHistoryItem]]
    last_updated: datetime