"""
Seed database with historical market data
Run: python scripts/seed_market_data.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data.aggregator import market_data_service
from app.models.candle import Candle
from app.constants.timeframes import Timeframe
from app.schemas.candle import CandleRequest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


async def seed_symbol(symbol: str, timeframe: Timeframe, days: int = 365):
    """Seed historical data for a symbol"""
    logger.info(f"Seeding {symbol} ({timeframe.value}) - {days} days")
    
    try:
        request = CandleRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=days,
            from_date=datetime.now() - timedelta(days=days),
            to_date=datetime.now()
        )
        
        candles = await market_data_service.get_candles(request)
        
        # Save to database
        db = SessionLocal()
        try:
            for candle_data in candles:
                candle = Candle(
                    symbol=candle_data.symbol,
                    timeframe=candle_data.timeframe,
                    open=candle_data.open,
                    high=candle_data.high,
                    low=candle_data.low,
                    close=candle_data.close,
                    volume=candle_data.volume,
                    vwap=candle_data.vwap,
                    trades=candle_data.trades,
                    timestamp=candle_data.timestamp
                )
                db.add(candle)
            
            db.commit()
            logger.info(f"  ✓ Saved {len(candles)} candles for {symbol}")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"  ✗ Failed to seed {symbol}: {e}")


async def main():
    logger.info("=== Market Data Seeding ===\n")
    
    # Popular symbols to seed
    symbols = [
        ("AAPL", Timeframe.ONE_DAY, 365),
        ("TSLA", Timeframe.ONE_DAY, 365),
        ("MSFT", Timeframe.ONE_DAY, 365),
        ("BTC", Timeframe.ONE_DAY, 365),
        ("ETH", Timeframe.ONE_DAY, 365),
    ]
    
    for symbol, timeframe, days in symbols:
        await seed_symbol(symbol, timeframe, days)
        await asyncio.sleep(1)  # Rate limiting
    
    logger.info("\n=== Seeding Complete ===")


if __name__ == "__main__":
    asyncio.run(main())