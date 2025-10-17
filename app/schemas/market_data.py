from pydantic import BaseModel
from typing import List, Optional
from app.schemas.quote import QuoteResponse
from app.schemas.candle import CandleResponse

class MarketDataResponse(BaseModel):
    quotes: List[QuoteResponse]
    total: int
    cached: bool = False

class HistoricalDataResponse(BaseModel):
    symbol: str
    candles: List[CandleResponse]
    total: int
    
class MarketStatusResponse(BaseModel):
    market: str
    status: str
    next_open: Optional[str] = None
    next_close: Optional[str] = None