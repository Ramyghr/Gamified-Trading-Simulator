from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum

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

class PortfolioOverview(BaseModel):
    total_value: float
    cash_balance: float
    holdings_value: float
    initial_balance: float
    
    # P&L
    total_gain: float
    total_gain_pct: float
    daily_gain: float
    daily_gain_pct: float
    
    # Asset allocation
    cash_allocation_pct: float
    holdings_allocation_pct: float
    
    last_updated: datetime

# ============= Portfolio Stats =============

class PortfolioStats(BaseModel):
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # P&L
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    
    # Performance
    total_return: float
    total_return_pct: float
    daily_return: float
    best_trade: float
    worst_trade: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Risk metrics
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: float
    current_drawdown: float
    
    last_updated: datetime

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

# ============= Portfolio Performance Chart Data =============

class PerformanceChartData(BaseModel):
    dates: List[str]
    values: List[float]
    returns: List[float]
    benchmark_values: Optional[List[float]] = None

# ============= Detailed Position =============

class DetailedPosition(BaseModel):
    symbol: str
    asset_type: AssetType
    quantity: float
    average_buy_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    allocation_pct: float
    last_price_update: Optional[datetime] = None

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
