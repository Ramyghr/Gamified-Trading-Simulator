"""
Test all market data providers
Run: python scripts/test_providers.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data.aggregator import market_data_service
from app.constants.market_constants import AssetClass
from app.constants.timeframes import Timeframe
from app.schemas.candle import CandleRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_quotes():
    """Test quote fetching"""
    logger.info("\n=== Testing Quotes ===")
    
    test_symbols = {
        AssetClass.STOCK: ["AAPL", "TSLA"],
        AssetClass.CRYPTO: ["BTC", "ETH"],
        AssetClass.FOREX: ["EUR/USD"]
    }
    
    for asset_class, symbols in test_symbols.items():
        logger.info(f"\nTesting {asset_class.value}:")
        for symbol in symbols:
            try:
                quote = await market_data_service.get_quote(symbol, asset_class)
                logger.info(f"  ✓ {symbol}: ${quote.close:.2f} ({quote.change_percent:+.2f}%)")
            except Exception as e:
                logger.error(f"  ✗ {symbol}: {e}")


async def test_candles():
    """Test candle data"""
    logger.info("\n=== Testing Candles ===")
    
    request = CandleRequest(
        symbol="AAPL",
        timeframe=Timeframe.ONE_DAY,
        limit=5
    )
    
    try:
        candles = await market_data_service.get_candles(request)
        logger.info(f"  ✓ Retrieved {len(candles)} candles for AAPL")
        for candle in candles[:3]:
            logger.info(f"    {candle.timestamp.date()}: O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}")
    except Exception as e:
        logger.error(f"  ✗ Candles failed: {e}")


async def test_search():
    """Test symbol search"""
    logger.info("\n=== Testing Search ===")
    
    try:
        results = await market_data_service.search_symbols("apple", AssetClass.STOCK)
        logger.info(f"  ✓ Found {len(results)} results for 'apple'")
        for result in results[:3]:
            logger.info(f"    - {result.get('symbol', 'N/A')}: {result.get('name', 'N/A')}")
    except Exception as e:
        logger.error(f"  ✗ Search failed: {e}")


async def test_health():
    """Test provider health"""
    logger.info("\n=== Testing Provider Health ===")
    
    health = await market_data_service.health_check()
    for provider, status in health.items():
        status_icon = "✓" if status else "✗"
        logger.info(f"  {status_icon} {provider}: {'healthy' if status else 'unhealthy'}")


async def main():
    logger.info("Starting Market Data Provider Tests\n")
    
    await test_health()
    await test_quotes()
    await test_candles()
    await test_search()
    
    logger.info("\n=== Tests Complete ===")


if __name__ == "__main__":
    asyncio.run(main())