from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
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
    close: float = Field(gt=0)
    open: Optional[float] = Field(None, gt=0)  # Make optional
    high: Optional[float] = Field(None, gt=0)  # Make optional  
    low: Optional[float] = Field(None, gt=0)   # Make optional
    volume: Optional[float] = Field(None, ge=0)  # Allow 0 or greater
    timestamp: datetime
    asset_class: str
    provider: str  # Should match your provider enum
    
    class Config:
        from_attributes = True

class QuoteRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=50, description="List of symbols to fetch")
    asset_class: Optional[AssetClass] = None