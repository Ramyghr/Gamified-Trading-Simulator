from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.constants.market_constants import AssetClass, DataProvider

class QuoteBase(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, BTC)")
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: float = Field(..., ge=0)
class QuoteResponse(BaseModel):
    symbol: str
    asset_class: AssetClass
    open: float = Field(ge=0)  # Allow 0 instead of gt=0
    high: float = Field(ge=0)
    low: float = Field(ge=0)
    close: float = Field(ge=0)
    volume: float = Field(ge=0)
    change: float = 0
    change_percent: float = 0
    timestamp: datetime
    # provider: DataProvider
    vwap: Optional[float] = None
    trades: Optional[int] = None

    @validator('open', 'high', 'low', 'close', 'volume', pre=True)
    def validate_positive_or_zero(cls, v):
        """Allow zero values for failed API calls"""
        if v is None:
            return 0.0
        return max(float(v), 0.0)

# class QuoteResponse(BaseModel):
#     symbol: str
#     close: float = Field(gt=0)
#     open: Optional[float] = Field(None, gt=0)  # Make optional
#     high: Optional[float] = Field(None, gt=0)  # Make optional  
#     low: Optional[float] = Field(None, gt=0)   # Make optional
#     volume: Optional[float] = Field(None, ge=0)  # Allow 0 or greater
#     timestamp: datetime
#     asset_class: str
#     provider: str  # Should match your provider enum
    
#     class Config:
#         from_attributes = True

class QuoteRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=50, description="List of symbols to fetch")
    asset_class: Optional[AssetClass] = None