from sqlalchemy import Column, Integer, String, Float, DateTime, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base
from app.constants.market_constants import AssetClass, DataProvider
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index, Enum as SQLEnum

class MarketQuote(Base):
    __tablename__ = "market_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    asset_class = Column(SQLEnum(AssetClass), nullable=False)
    
    # Price data
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(Numeric, nullable=False)
    
    # Metadata
    change = Column(Numeric)  # Absolute change
    change_percent = Column(Numeric)  # Percentage change
    vwap = Column(Numeric)  # Volume-weighted average price
    trades = Column(Integer)  # Number of trades
    
    provider = Column(SQLEnum(DataProvider), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_asset_class_timestamp', 'asset_class', 'timestamp'),
    )