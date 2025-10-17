from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.market_data import MarketDataResponse, MarketStatusResponse
from app.schemas.quote import QuoteRequest, QuoteResponse
from app.services.market_data_service import enhanced_market_service
from app.constants.market_constants import AssetClass
from app.config.redis_client import redis_client
import logging
from datetime import datetime, time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["Market Data"])


# ------------------------------------------------------------
# Health Check Endpoint
# ------------------------------------------------------------
@router.get("/health", response_model=dict)
async def health_check():
    """Check health of all market data providers"""
    try:
        health = await enhanced_market_service.get_active_providers()
        return {
            "status": "healthy" if health else "degraded",
            "active_providers": health
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# ------------------------------------------------------------
# Get Multiple Quotes
# ------------------------------------------------------------
def asset_class_to_lowercase(asset_class: Optional[AssetClass]) -> str:
    """Convert AssetClass enum to lowercase string expected by schema"""
    if asset_class is None:
        return "stock"
    return asset_class.value.lower()


@router.post("/quotes", response_model=MarketDataResponse)
async def get_quotes(request: QuoteRequest):
    """Get multiple quotes at once"""
    try:
        # Split comma-separated symbols and flatten the list
        all_symbols = []
        for symbol_item in request.symbols:
            if ',' in symbol_item:
                all_symbols.extend([s.strip().upper() for s in symbol_item.split(',')])
            else:
                all_symbols.append(symbol_item.strip().upper())
        
        logger.info(f"Fetching quotes for: {all_symbols}")
        
        # Create symbols with asset type
        symbols_with_asset = [
            (symbol, request.asset_class.value if request.asset_class else "STOCK")
            for symbol in all_symbols
        ]
        
        price_dict = await enhanced_market_service.get_batch_prices(symbols_with_asset)
        quotes_list = []
        for symbol, price in price_dict.items():
            if price is None or price <= 0:
                logger.warning(f"No valid price for {symbol}")
                continue
                
            quotes_list.append(
                QuoteResponse(
                    symbol=symbol,
                    close=price,
                    open=price,
                    high=price,
                    low=price,
                    volume=0.0,
                    timestamp=datetime.utcnow(),
                    asset_class=asset_class_to_lowercase(request.asset_class),
                    provider="alpha_vantage"
                )
            )
        
        return MarketDataResponse(
            quotes=quotes_list,
            total=len(quotes_list),
            cached=False
        )
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------
# Single Quote (with Redis caching)
# ------------------------------------------------------------
@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    asset_class: Optional[AssetClass] = Query(None, description="Asset class"),
):
    """
    Get a single quote for a symbol. Uses Redis cache when available.
    """
    symbol = symbol.upper()
    asset_type = asset_class.value if asset_class else "STOCK"

    # 1️⃣ Try Redis cache first (sync operation)
    try:
        cached_price = redis_client.get(f"price:{symbol}")
        if cached_price:
            logger.info(f"Cache hit for {symbol}")
            return QuoteResponse(
                symbol=symbol,
                close=float(cached_price),
                open=float(cached_price),
                high=float(cached_price),
                low=float(cached_price),
                volume=0.0,
                timestamp=datetime.utcnow(),
                asset_class=asset_class_to_lowercase(asset_class),
                provider="redis"
            )
    except Exception as e:
        logger.warning(f"Redis cache read failed for {symbol}: {e}")

    # 2️⃣ Fetch live quote
    try:
        price = await enhanced_market_service.get_price(symbol, asset_type)
        
        if price is None or price <= 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No data available for {symbol}"
            )

        # 3️⃣ Cache result (sync operation)
        try:
            redis_client.setex(f"price:{symbol}", 60, str(price))
            logger.info(f"Cached price for {symbol}: {price}")
        except Exception as e:
            logger.warning(f"Redis cache write failed for {symbol}: {e}")

        return QuoteResponse(
            symbol=symbol,
            close=price,
            open=price,
            high=price,
            low=price,
            volume=0.0,
            timestamp=datetime.utcnow(),
            asset_class=asset_class_to_lowercase(asset_class),
            provider="live"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quote fetch error for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------
# Symbol Search (if implemented)
# ------------------------------------------------------------
# @router.get("/search")
# async def search_symbols(
#     q: str = Query(..., min_length=1, description="Search query"),
#     asset_class: Optional[AssetClass] = Query(None)
# ):
#     """
#     Search for symbols (delegates to provider that supports it).
#     Example: GET /api/market/search?q=apple&asset_class=STOCK
#     """
#     try:
#         # Check if search_symbol method exists
#         if not hasattr(market_data_service, 'search_symbol'):
#             raise HTTPException(
#                 status_code=501, 
#                 detail="Symbol search not implemented"
#             )
        
#         results = await market_data_service.search_symbol(q)
#         return {"results": results, "total": len(results)}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Symbol search error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------
# Market Status (if implemented)
# ------------------------------------------------------------
@router.get("/status/{market}", response_model=MarketStatusResponse)
async def get_market_status(market: str):
    """
    Get current market status (open/closed).
    Example: GET /api/market/status/US
    """
    try:
        # Check if get_market_status method exists
        if not hasattr(enhanced_market_service, 'get_market_status'):
            raise HTTPException(
                status_code=501, 
                detail="Market status not implemented"
            )
        
        status = await enhanced_market_service.get_market_status(market)
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))