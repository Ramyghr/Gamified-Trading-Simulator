from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base
from app.constants.timeframes import Timeframe

class Candle(Base):
    __tablename__ = "candles"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(SQLEnum(Timeframe), nullable=False, index=True)
    
    # OHLCV data
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(Numeric, nullable=False)
    
    # Additional metrics
    vwap = Column(Numeric)
    trades = Column(Integer)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
    )