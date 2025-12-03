"""
Bot Schemas
Save as: app/schemas/bot.py
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class BotStrategyType(str, Enum):
    MA_CROSSOVER = "MA_CROSSOVER"
    RSI_OVERSOLD_OVERBOUGHT = "RSI_OVERSOLD_OVERBOUGHT"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    VOLUME_BREAKOUT = "VOLUME_BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    SUPPORT_RESISTANCE = "SUPPORT_RESISTANCE"
    GRID_TRADING = "GRID_TRADING"
    DCA = "DCA"
    RAPID_TEST = "RAPID_TEST"  # Added from your version


class BotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ============= Bot Creation / Update =============

class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    strategy_type: BotStrategyType
    strategy_params: Dict[str, Any]
    
    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: str = Field(default="STOCK")
    
    # Risk management
    max_position_size: float = Field(default=1000.0, gt=0)
    stop_loss_pct: Optional[float] = Field(None, ge=0, le=100)
    take_profit_pct: Optional[float] = Field(None, ge=0, le=100)
    max_daily_trades: int = Field(default=10, ge=1, le=100)
    max_daily_loss: float = Field(default=500.0, gt=0)
    max_open_trades: int = Field(default=3, ge=1, le=20)  # NEW: Max concurrent trades
    
    # Leverage
    use_leverage: bool = Field(default=False)
    leverage: float = Field(default=1.0, ge=1.0, le=20.0)
    
    # Execution
    interval: str = Field(default="5m")
    
    @validator('symbol')
    def symbol_uppercase(cls, v):
        return v.upper()
    
    @validator('strategy_params')
    def validate_strategy_params(cls, v, values):
        """Validate strategy parameters based on strategy type"""
        if 'strategy_type' not in values:
            return v
        
        strategy = values['strategy_type']
        
        # Define required params for each strategy
        required_params = {
            BotStrategyType.MA_CROSSOVER: ['short_window', 'long_window'],
            BotStrategyType.RSI_OVERSOLD_OVERBOUGHT: ['period', 'oversold', 'overbought'],
            BotStrategyType.BOLLINGER_BANDS: ['period', 'std_dev'],
            BotStrategyType.MACD_CROSSOVER: ['fast_period', 'slow_period', 'signal_period'],
            BotStrategyType.VOLUME_BREAKOUT: ['volume_threshold', 'lookback_period'],
            BotStrategyType.MEAN_REVERSION: ['period', 'std_threshold'],
            BotStrategyType.MOMENTUM: ['period', 'threshold'],
            BotStrategyType.SUPPORT_RESISTANCE: ['lookback_period', 'tolerance'],
            BotStrategyType.GRID_TRADING: ['grid_levels', 'grid_spacing_pct'],
            BotStrategyType.DCA: ['buy_interval', 'buy_amount'],
            BotStrategyType.RAPID_TEST: []  # Added from your version
        }
        
        if strategy in required_params:
            for param in required_params[strategy]:
                if param not in v:
                    raise ValueError(f"Missing required parameter '{param}' for {strategy}")
        
        return v


class BotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    strategy_params: Optional[Dict[str, Any]] = None
    
    max_position_size: Optional[float] = Field(None, gt=0)
    stop_loss_pct: Optional[float] = Field(None, ge=0, le=100)
    take_profit_pct: Optional[float] = Field(None, ge=0, le=100)
    max_daily_trades: Optional[int] = Field(None, ge=1, le=100)
    max_daily_loss: Optional[float] = Field(None, gt=0)
    
    leverage: Optional[float] = Field(None, ge=1.0, le=20.0)
    interval: Optional[str] = None


# ============= Bot Responses =============

class BotResponse(BaseModel):
    id: int
    user_id: int
    portfolio_id: int
    
    name: str
    description: Optional[str]
    
    strategy_type: BotStrategyType
    strategy_params: Dict[str, Any]
    
    symbol: str
    asset_type: str
    
    max_position_size: float
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    max_daily_trades: int
    max_daily_loss: float
    
    use_leverage: bool
    leverage: float
    
    interval: str
    status: BotStatus
    
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    total_fees: float
    
    last_execution: Optional[datetime]
    next_execution: Optional[datetime]
    last_signal: Optional[TradeAction]
    
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime]
    stopped_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BotListResponse(BaseModel):
    bots: List[BotResponse]
    total: int
    active_count: int
    paused_count: int


# ============= Bot Trade =============

class BotTradeResponse(BaseModel):
    id: int
    bot_id: int
    symbol: str
    action: TradeAction
    
    # Add position_id field
    position_id: Optional[int] = None  # ← ADD THIS
    
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    
    trade_value: float
    fee: float
    pnl: float
    pnl_pct: float
    
    leverage_used: float
    margin_used: float
    
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    exit_reason: Optional[str]
    
    is_open: bool
    opened_at: datetime
    closed_at: Optional[datetime]
    
    class Config:
        orm_mode = True


# ============= Backtest =============

class BacktestRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=10000.0, gt=0)


class BacktestResponse(BaseModel):
    id: int
    bot_id: int
    
    start_date: datetime
    end_date: datetime
    initial_capital: float
    
    final_capital: float
    total_return: float
    total_return_pct: float
    
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    
    performance_metrics: Optional[Dict]
    trade_history: Optional[List]
    
    status: str
    error_message: Optional[str]
    
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True


# ============= Bot Performance =============

class BotPerformance(BaseModel):
    bot_id: int
    bot_name: str
    symbol: str
    
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    total_pnl: float
    total_pnl_pct: float
    avg_pnl_per_trade: float
    
    best_trade: float
    worst_trade: float
    
    total_fees: float
    
    status: BotStatus
    uptime_hours: float
    
    last_execution: Optional[datetime]


# ============= Bot Signal =============

class BotSignal(BaseModel):
    bot_id: int
    symbol: str
    action: TradeAction
    
    current_price: float
    signal_strength: float  # 0-1
    
    indicators: Dict[str, Any]
    reason: str
    
    timestamp: datetime


# ============= Strategy Templates =============

class StrategyTemplate(BaseModel):
    strategy_type: BotStrategyType
    name: str
    description: str
    default_params: Dict[str, Any]
    param_descriptions: Dict[str, str]
    recommended_intervals: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH


# ============= Bot Control =============

class BotControlRequest(BaseModel):
    action: str  # "START", "PAUSE", "STOP"


class BotStatusUpdate(BaseModel):
    status: BotStatus
    message: str