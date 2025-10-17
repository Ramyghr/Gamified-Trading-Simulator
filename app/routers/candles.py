from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from app.schemas.candle import CandleRequest, CandleResponse
from app.schemas.market_data import HistoricalDataResponse
from app.services.market_data.aggregator import market_data_service
from app.constants.timeframes import Timeframe
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/candles", tags=["Candles"])

@router.get("/{symbol}", response_model=HistoricalDataResponse)
async def get_candles(
    symbol: str,
    timeframe: Timeframe = Query(
        Timeframe.ONE_DAY, 
        description="Candle timeframe. Examples: 1m, 5m, 1h, 1D"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of candles"),
    from_date: Optional[datetime] = Query(None, description="Start date"),
    to_date: Optional[datetime] = Query(None, description="End date")
):
    """
    Get historical candlestick data
    
    Example: GET /api/v1/candles/AAPL?timeframe=1h&limit=24
    """
    try:
        request = CandleRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            from_date=from_date or datetime.now() - timedelta(days=30),
            to_date=to_date or datetime.now()
        )
        
        candles = await market_data_service.get_candles(request)
        
        return HistoricalDataResponse(
            symbol=symbol,
            candles=candles,
            total=len(candles)
        )
    except Exception as e:
        logger.error(f"Candle fetch error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/latest", response_model=CandleResponse)
async def get_latest_candle(
    symbol: str,
    timeframe: Timeframe = Query(
        Timeframe.ONE_DAY, 
        description="Candle timeframe. Examples: 1m, 5m, 1h, 1D"
    )
):
    """Get the most recent candle"""
    try:
        request = CandleRequest(symbol=symbol, timeframe=timeframe, limit=1)
        candles = await market_data_service.get_candles(request)
        
        if not candles:
            raise HTTPException(status_code=404, detail="No candles found")
        
        return candles[0]
    except Exception as e:
        logger.error(f"Latest candle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
