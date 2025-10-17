from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Index, Numeric
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.sql import func
from app.config.database import Base
import enum

class AssetType(str, enum.Enum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    cash_balance = Column(Float, default=10000.00)  # Quest Cash
    initial_balance = Column(Float, default=10000.00)  # Starting capital
    total_value = Column(Float, default=10000.00)  # Cash + Holdings value
    locked = Column(Boolean, default=False)
    last_valuation_update = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolio")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")
    daily_snapshots = relationship("PortfolioDailySnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    reserved_cash = Column(Numeric(20, 2), nullable=False, default=0)

class Holding(Base):
    """Individual asset holdings with real-time valuation"""
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    asset_type = Column(Enum(AssetType), default=AssetType.STOCK)
    quantity = Column(Numeric, nullable=False)  
    average_buy_price = Column(Numeric, nullable=False)  # Cost basis
    average_price = synonym("average_buy_price")
    # Real-time market data (cached)
    current_price = Column(Numeric, nullable=True)  # Latest market price
    last_price_update = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    reserved_quantity = Column(Numeric(20, 8), nullable=False, default=0)    
    
    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_portfolio_symbol', 'portfolio_id', 'symbol'),
    )

class PortfolioHistory(Base):
    """Tracks every portfolio value change for detailed history"""
    __tablename__ = "portfolio_history"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    total_value = Column(Numeric, nullable=False)
    cash_balance = Column(Numeric, nullable=False)
    holdings_value = Column(Numeric, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="history")
    
    __table_args__ = (
        Index('idx_portfolio_timestamp', 'portfolio_id', 'timestamp'),
    )

class PortfolioDailySnapshot(Base):
    """Daily end-of-day snapshots for performance tracking"""
    __tablename__ = "portfolio_daily_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Portfolio metrics
    total_value = Column(Numeric, nullable=False)
    cash_balance = Column(Numeric, nullable=False)
    holdings_value = Column(Numeric, nullable=False)
    
    # Performance metrics
    daily_return = Column(Numeric, default=0.0)
    total_return = Column(Numeric, default=0.0)
    total_return_pct = Column(Numeric, default=0.0)
    
    # Risk metrics
    volatility = Column(Numeric, nullable=True)  # Rolling 30-day
    sharpe_ratio = Column(Numeric, nullable=True)
    max_drawdown = Column(Numeric, nullable=True)
    
    # Ranking
    portfolio_rank = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="daily_snapshots")
    
    __table_args__ = (
        Index('idx_portfolio_date', 'portfolio_id', 'date'),
    )

class PortfolioMetrics(Base):
    """Real-time calculated metrics (cached for performance)"""
    __tablename__ = "portfolio_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), unique=True, nullable=False)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric, default=0.0)
    
    # P&L metrics
    realized_pnl = Column(Numeric, default=0.0)
    unrealized_pnl = Column(Numeric, default=0.0)
    total_pnl = Column(Numeric, default=0.0)
    
    # Performance
    best_trade = Column(Numeric, default=0.0)
    worst_trade = Column(Numeric, default=0.0)
    avg_win = Column(Numeric, default=0.0)
    avg_loss = Column(Numeric, default=0.0)
    
    # Risk
    max_drawdown = Column(Numeric, default=0.0)
    current_drawdown = Column(Numeric, default=0.0)
    sharpe_ratio = Column(Numeric, nullable=True)
    
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio")