from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.constants.timeframes import Timeframe

class CandleBase(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime

class CandleResponse(CandleBase):
    symbol: str
    timeframe: Timeframe
    vwap: Optional[float] = None
    trades: Optional[int] = None
    
    class Config:
        from_attributes = True

class CandleRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    timeframe: Timeframe = Field(default=Timeframe.ONE_DAY)
    limit: int = Field(default=100, ge=1, le=1000, description="Number of candles")
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None