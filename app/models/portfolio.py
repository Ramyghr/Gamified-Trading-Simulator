"""
Updated portfolio models with margin and leverage support.
Add these columns to your existing Portfolio and Holding models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Index, Numeric
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.sql import func
from app.config.database import Base
import enum


class AssetType(str, enum.Enum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"


class PositionSide(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"  # For cash holdings


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Cash balances
    cash_balance = Column(Numeric(20, 2), default=10000.00)  # Available cash
    initial_balance = Column(Numeric(20, 2), default=10000.00)  # Starting capital
    reserved_cash = Column(Numeric(20, 2), nullable=False, default=0)  # Reserved for orders
    
    # Margin trading fields (NEW)
    margin_used = Column(Numeric(20, 2), nullable=False, default=0)  # Total margin locked
    margin_available = Column(Numeric(20, 2), nullable=False, default=0)  # Available for new positions
    
    # Equity and valuation
    equity = Column(Numeric(20, 2), nullable=False, default=10000.00)  # Cash + Unrealized PnL
    total_value = Column(Numeric(20, 2), default=10000.00)  # Total account value
    unrealized_pnl = Column(Numeric(20, 2), nullable=False, default=0)  # Sum of all position PnL
    
    # Risk metrics (NEW)
    margin_level = Column(Numeric(10, 4), nullable=False, default=0)  # (Equity / Margin Used) * 100
    total_exposure = Column(Numeric(20, 2), nullable=False, default=0)  # Sum of all position values
    
    # Settings
    locked = Column(Boolean, default=False)
    max_leverage = Column(Numeric(5, 2), nullable=False, default=10.00)  # Max allowed leverage (NEW)
    
    # Timestamps
    last_valuation_update = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")  # NEW
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")
    daily_snapshots = relationship("PortfolioDailySnapshot", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    """
    Simple holdings for spot trading (non-leveraged).
    Keep this for backward compatibility.
    """
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    asset_type = Column(Enum(AssetType), default=AssetType.STOCK)
    quantity = Column(Numeric(20, 8), nullable=False)  
    average_buy_price = Column(Numeric(20, 8), nullable=False)
    average_price = synonym("average_buy_price")
    
    # Real-time market data
    current_price = Column(Numeric(20, 8), nullable=True)
    last_price_update = Column(DateTime, nullable=True)
    
    # Reserved for pending orders
    reserved_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    __table_args__ = (
        Index('idx_portfolio_symbol', 'portfolio_id', 'symbol'),
    )


class Position(Base):
    """
    Leveraged positions with margin tracking.
    This is the NEW table for leverage trading.
    """
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Position details
    symbol = Column(String(50), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), default=AssetType.STOCK)
    side = Column(Enum(PositionSide), nullable=False)  # LONG or SHORT
    
    # Quantity and pricing
    quantity = Column(Numeric(20, 8), nullable=False)  # Position size
    entry_price = Column(Numeric(20, 8), nullable=False)  # Average entry price
    current_price = Column(Numeric(20, 8), nullable=True)  # Current market price
    
    # Leverage and margin
    leverage = Column(Numeric(10, 2), nullable=False)  # e.g., 10.00 for 10x
    margin_used = Column(Numeric(20, 2), nullable=False)  # Collateral locked
    position_value = Column(Numeric(20, 2), nullable=False)  # Quantity * Entry Price
    
    # PnL tracking
    unrealized_pnl = Column(Numeric(20, 2), nullable=False, default=0)
    realized_pnl = Column(Numeric(20, 2), nullable=False, default=0)
    
    # Risk management
    liquidation_price = Column(Numeric(20, 8), nullable=False)
    maintenance_margin = Column(Numeric(20, 2), nullable=False)  # Min margin to avoid liquidation
    initial_margin = Column(Numeric(20, 2), nullable=False)  # Margin at position open
    
    # Stop loss / Take profit (optional)
    stop_loss_price = Column(Numeric(20, 8), nullable=True)
    take_profit_price = Column(Numeric(20, 8), nullable=True)
    
    # Status
    is_open = Column(Boolean, nullable=False, default=True)
    is_liquidated = Column(Boolean, nullable=False, default=False)
    
    # Funding rate tracking (for perpetuals)
    accumulated_funding = Column(Numeric(20, 2), nullable=False, default=0)
    last_funding_time = Column(DateTime, nullable=True)
    
    # Fees
    total_fees = Column(Numeric(20, 2), nullable=False, default=0)
    
    # Timestamps
    opened_at = Column(DateTime, nullable=False, default=func.now())
    closed_at = Column(DateTime, nullable=True)
    last_price_update = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_portfolio_symbol_open', 'portfolio_id', 'symbol', 'is_open'),
        Index('idx_user_open', 'user_id', 'is_open'),
        Index('idx_liquidation_check', 'is_open', 'liquidation_price'),
    )


class PortfolioHistory(Base):
    """Enhanced to track margin metrics"""
    __tablename__ = "portfolio_history"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Standard metrics
    total_value = Column(Numeric(20, 2), nullable=False)
    cash_balance = Column(Numeric(20, 2), nullable=False)
    holdings_value = Column(Numeric(20, 2), nullable=False)
    
    # Margin metrics (NEW)
    equity = Column(Numeric(20, 2), nullable=False, default=0)
    margin_used = Column(Numeric(20, 2), nullable=False, default=0)
    unrealized_pnl = Column(Numeric(20, 2), nullable=False, default=0)
    margin_level = Column(Numeric(10, 4), nullable=False, default=0)
    
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    portfolio = relationship("Portfolio", back_populates="history")
    
    __table_args__ = (
        Index('idx_portfolio_timestamp', 'portfolio_id', 'timestamp'),
    )


class PortfolioDailySnapshot(Base):
    """Enhanced with margin metrics"""
    __tablename__ = "portfolio_daily_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Portfolio metrics
    total_value = Column(Numeric(20, 2), nullable=False)
    cash_balance = Column(Numeric(20, 2), nullable=False)
    holdings_value = Column(Numeric(20, 2), nullable=False)
    equity = Column(Numeric(20, 2), nullable=False, default=0)  # NEW
    
    # Performance metrics
    daily_return = Column(Numeric(10, 4), default=0.0)
    total_return = Column(Numeric(20, 2), default=0.0)
    total_return_pct = Column(Numeric(10, 4), default=0.0)
    
    # Margin metrics (NEW)
    margin_used = Column(Numeric(20, 2), nullable=False, default=0)
    unrealized_pnl = Column(Numeric(20, 2), nullable=False, default=0)
    realized_pnl = Column(Numeric(20, 2), nullable=False, default=0)
    total_exposure = Column(Numeric(20, 2), nullable=False, default=0)
    avg_leverage = Column(Numeric(10, 4), nullable=True)
    
    # Risk metrics
    volatility = Column(Numeric(10, 4), nullable=True)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)
    margin_level = Column(Numeric(10, 4), nullable=True)  # NEW
    
    # Ranking
    portfolio_rank = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    portfolio = relationship("Portfolio", back_populates="daily_snapshots")
    
    __table_args__ = (
        Index('idx_portfolio_date', 'portfolio_id', 'date'),
    )


class PortfolioMetrics(Base):
    """Enhanced with leverage trading metrics"""
    __tablename__ = "portfolio_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), unique=True, nullable=False)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(10, 4), default=0.0)
    
    # Leverage trading stats (NEW)
    total_leveraged_trades = Column(Integer, default=0)
    total_liquidations = Column(Integer, default=0)
    avg_leverage_used = Column(Numeric(10, 4), default=0.0)
    max_leverage_used = Column(Numeric(10, 4), default=0.0)
    
    # P&L metrics
    realized_pnl = Column(Numeric(20, 2), default=0.0)
    unrealized_pnl = Column(Numeric(20, 2), default=0.0)
    total_pnl = Column(Numeric(20, 2), default=0.0)
    liquidation_losses = Column(Numeric(20, 2), default=0.0)  # NEW
    
    # Performance
    best_trade = Column(Numeric(20, 2), default=0.0)
    worst_trade = Column(Numeric(20, 2), default=0.0)
    avg_win = Column(Numeric(20, 2), default=0.0)
    avg_loss = Column(Numeric(20, 2), default=0.0)
    
    # Risk
    max_drawdown = Column(Numeric(10, 4), default=0.0)
    current_drawdown = Column(Numeric(10, 4), default=0.0)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    portfolio = relationship("Portfolio")


class LiquidationEvent(Base):
    """
    Track liquidation events for audit and analytics.
    NEW table for margin trading.
    """
    __tablename__ = "liquidation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    
    # Liquidation details
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(PositionSide), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    liquidation_price = Column(Numeric(20, 8), nullable=False)
    actual_liquidation_price = Column(Numeric(20, 8), nullable=False)
    
    # Financial impact
    margin_used = Column(Numeric(20, 2), nullable=False)
    loss_amount = Column(Numeric(20, 2), nullable=False)
    liquidation_fee = Column(Numeric(20, 2), nullable=False, default=0)
    
    # Context
    equity_before = Column(Numeric(20, 2), nullable=False)
    equity_after = Column(Numeric(20, 2), nullable=False)
    margin_level_before = Column(Numeric(10, 4), nullable=False)
    
    # Metadata
    reason = Column(String(500), nullable=True)
    liquidated_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    portfolio = relationship("Portfolio")
    
    __table_args__ = (
        Index('idx_user_liquidated_at', 'user_id', 'liquidated_at'),
    )