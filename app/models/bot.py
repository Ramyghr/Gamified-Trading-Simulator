"""
Bot Trading Models - FIXED with PositionSide enum and missing fields
Save as: app/models/bot.py
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Enum as SQLEnum, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base


class BotStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class PositionSide(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class BotStrategyType(str, enum.Enum):
    MA_CROSSOVER = "MA_CROSSOVER"
    RSI_OVERSOLD_OVERBOUGHT = "RSI_OVERSOLD_OVERBOUGHT"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    VOLUME_BREAKOUT = "VOLUME_BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    SUPPORT_RESISTANCE = "SUPPORT_RESISTANCE"
    GRID_TRADING = "GRID_TRADING"
    DCA = "DCA"  # Dollar Cost Averaging
    RAPID_TEST = "RAPID_TEST"


class TradeAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PositionSide(str, enum.Enum):  # ADD THIS ENUM
    LONG = "LONG"
    SHORT = "SHORT"


class Bot(Base):
    """Trading bot configuration"""
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Strategy configuration
    strategy_type = Column(SQLEnum(BotStrategyType), nullable=False)
    strategy_params = Column(JSON, nullable=False)  # Strategy-specific parameters
    
    # Trading configuration
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), default="STOCK")
    
    # Risk management
    max_position_size = Column(Float, default=1000.0)  # Max $ per trade
    stop_loss_pct = Column(Float, nullable=True)  # Stop loss percentage
    take_profit_pct = Column(Float, nullable=True)  # Take profit percentage
    max_daily_trades = Column(Integer, default=10)
    max_daily_loss = Column(Float, default=500.0)  # Max loss per day
    max_open_trades = Column(Integer, default=3)
    
    # Leverage settings (optional)
    use_leverage = Column(Boolean, default=False)
    leverage = Column(Float, default=1.0)
    
    # Execution settings
    interval = Column(String(20), default="5m")  # Execution interval (1m, 5m, 15m, 1h, etc.)
    
    # Status
    status = Column(SQLEnum(BotStatus), default=BotStatus.PAUSED, index=True)
    is_backtesting = Column(Boolean, default=False)
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)
    
    # Bot portfolio tracking (NEW FIELDS)
    bot_initial_capital = Column(Numeric(20, 4), nullable=True)  # Use Numeric for precise calculations
    bot_current_value = Column(Numeric(20, 4), nullable=True)
    bot_margin_level = Column(Numeric(20, 4), nullable=True)  # For leverage bots
    
    # Execution tracking
    last_execution = Column(DateTime, nullable=True)
    next_execution = Column(DateTime, nullable=True)
    last_signal = Column(SQLEnum(TradeAction), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bots")
    portfolio = relationship("Portfolio", back_populates="bots")
    trades = relationship("BotTrade", back_populates="bot", cascade="all, delete-orphan")
    backtests = relationship("BotBacktest", back_populates="bot", cascade="all, delete-orphan")
    logs = relationship("BotLog", back_populates="bot", cascade="all, delete-orphan")


class BotTrade(Base):
    """Individual bot trades - FIXED with position_side field"""
    __tablename__ = "bot_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Add position_id here (not in Bot class!)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)  # ← CORRECT PLACE!
    
    symbol = Column(String(20), nullable=False)
    action = Column(SQLEnum(TradeAction), nullable=False)
    
    # ADD POSITION_SIDE FIELD
    position_side = Column(SQLEnum(PositionSide), default=PositionSide.LONG, nullable=False)
    
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    
    trade_value = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    
    # Leverage info
    leverage_used = Column(Float, default=1.0)
    margin_used = Column(Float, default=0.0)
    
    # Stop loss / Take profit
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True)  # "STOP_LOSS", "TAKE_PROFIT", "SIGNAL", "MANUAL"
    
    # Status
    is_open = Column(Boolean, default=True)
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="trades")
    user = relationship("User")
    position = relationship("Position")  # Add this relationship too
    position_side = Column(SQLEnum(PositionSide), default=PositionSide.LONG, nullable=False)

class BotBacktest(Base):
    """Backtest results"""
    __tablename__ = "bot_backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Backtest configuration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, default=10000.0)
    
    # Results
    final_capital = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    total_return_pct = Column(Float, default=0.0)
    
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)
    
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    
    # Detailed metrics
    performance_metrics = Column(JSON)  # Detailed day-by-day performance
    trade_history = Column(JSON)  # List of all trades
    
    # Status
    status = Column(String(20), default="COMPLETED")  # RUNNING, COMPLETED, FAILED
    error_message = Column(String(500), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="backtests")
    user = relationship("User")


class BotLog(Base):
    """Bot execution logs"""
    __tablename__ = "bot_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR
    message = Column(String(1000), nullable=False)
    details = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="logs")