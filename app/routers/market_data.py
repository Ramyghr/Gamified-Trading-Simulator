"""
Updated market data routes with proper asset type handling
Key changes: proper asset_class usage in batch requests
"""
from fastapi import APIRouter,Path, HTTPException, Query
from typing import List, Optional, Dict
from app.schemas.market_data import MarketDataResponse, MarketStatusResponse
from app.schemas.quote import QuoteRequest, QuoteResponse
from app.services.market_data_service import enhanced_market_service
from app.constants.market_constants import AssetClass
from app.config.redis_client import redis_client
import logging
from datetime import datetime, time, timedelta
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["Market Data"])


def asset_class_to_lowercase(asset_class: Optional[AssetClass]) -> str:
    """Convert AssetClass enum to lowercase string"""
    if asset_class is None:
        return "stock"
    return asset_class.value.lower()


# ============================================================================
# HEALTH CHECK
# ============================================================================
@router.get("/health", response_model=dict)
async def health_check():
    """Check health of all market data providers"""
    try:
        health = await enhanced_market_service.get_active_providers()
        
        # Count active providers
        active_count = sum(1 for p in health.values() if p.get("status") == "active")
        
        return {
            "status": "healthy" if active_count > 0 else "degraded",
            "active_providers": health,
            "total_providers": len(health),
            "active_count": active_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# ============================================================================
# BATCH QUOTES (FIXED VERSION)
# ============================================================================
@router.post("/quotes", response_model=MarketDataResponse)
async def get_quotes(request: QuoteRequest):
    """
    Get multiple quotes at once with proper asset type handling
    
    Example request:
    {
        "symbols": ["BTC", "ETH", "AAPL"],
        "asset_class": "CRYPTO"  // or "STOCK", "FOREX", etc.
    }
    """
    try:
        # Split comma-separated symbols and flatten
        all_symbols = []
        for symbol_item in request.symbols:
            if ',' in symbol_item:
                all_symbols.extend([s.strip().upper() for s in symbol_item.split(',')])
            else:
                all_symbols.append(symbol_item.strip().upper())
        
        logger.info(f"Fetching quotes for: {all_symbols} ({request.asset_class or 'STOCK'})")
        
        # KEY FIX: Use proper asset type for each symbol
        asset_type = request.asset_class.value if request.asset_class else "STOCK"
        symbols_with_asset = [(symbol, asset_type) for symbol in all_symbols]
        
        # Fetch prices with fallback
        price_dict = await enhanced_market_service.get_batch_prices(symbols_with_asset)
        
        # Build response
        quotes_list = []
        for symbol in all_symbols:
            price = price_dict.get(symbol)
            
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
                    provider="aggregated"
                )
            )
        
        logger.info(f"✓ Returned {len(quotes_list)}/{len(all_symbols)} quotes")
        
        return MarketDataResponse(
            quotes=quotes_list,
            total=len(quotes_list),
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SINGLE QUOTE WITH REDIS CACHE
# ============================================================================
@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    asset_class: Optional[AssetClass] = Query(None, description="Asset class (STOCK, CRYPTO, FOREX)"),
):
    """
    Get a single quote for a symbol with Redis caching
    
    Example: GET /api/market/quote/BTC?asset_class=CRYPTO
    """
    symbol = symbol.upper()
    asset_type = asset_class.value if asset_class else "STOCK"

    # Try Redis cache first
    try:
        cached_price = redis_client.get(f"price:{symbol}")
        if cached_price:
            logger.info(f"[CACHE HIT] {symbol}")
            return QuoteResponse(
                symbol=symbol,
                close=float(cached_price),
                open=float(cached_price),
                high=float(cached_price),
                low=float(cached_price),
                volume=0.0,
                timestamp=datetime.utcnow(),
                asset_class=asset_class_to_lowercase(asset_class),
                provider="redis_cache"
            )
    except Exception as e:
        logger.warning(f"Redis cache read failed for {symbol}: {e}")

    # Fetch live quote with provider fallback
    try:
        price = await enhanced_market_service.get_price(symbol, asset_type)
        
        if price is None or price <= 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No data available for {symbol} ({asset_type})"
            )

        # Cache result
        try:
            redis_client.setex(f"price:{symbol}", 60, str(price))
            logger.info(f"[CACHED] {symbol}: ${price:.2f}")
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


# ============================================================================
# MIXED BATCH QUOTES (NEW ENDPOINT)
# ============================================================================
@router.post("/quotes/mixed", response_model=MarketDataResponse)
async def get_mixed_quotes(symbols_data: List[dict]):
    """
    Get quotes for mixed asset types in one request
    
    Example request:
    [
        {"symbol": "BTC", "asset_class": "CRYPTO"},
        {"symbol": "AAPL", "asset_class": "STOCK"},
        {"symbol": "EUR/USD", "asset_class": "FOREX"}
    ]
    """
    try:
        if not symbols_data:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        # Parse symbols with their asset types
        symbols_with_types = []
        for item in symbols_data:
            symbol = item.get("symbol", "").strip().upper()
            asset_type = item.get("asset_class", "STOCK").upper()
            
            if symbol:
                symbols_with_types.append((symbol, asset_type))
        
        logger.info(f"Fetching {len(symbols_with_types)} mixed quotes")
        
        # Fetch with fallback
        price_dict = await enhanced_market_service.get_batch_prices(symbols_with_types)
        
        # Build response
        quotes_list = []
        for symbol, asset_type in symbols_with_types:
            price = price_dict.get(symbol)
            
            if price and price > 0:
                quotes_list.append(
                    QuoteResponse(
                        symbol=symbol,
                        close=price,
                        open=price,
                        high=price,
                        low=price,
                        volume=0.0,
                        timestamp=datetime.utcnow(),
                        asset_class=asset_type.lower(),
                        provider="aggregated"
                    )
                )
        
        logger.info(f"✓ Returned {len(quotes_list)}/{len(symbols_with_types)} quotes")
        
        return MarketDataResponse(
            quotes=quotes_list,
            total=len(quotes_list),
            cached=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching mixed quotes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROVIDER STATUS (NEW ENDPOINT)
# ============================================================================
@router.get("/providers/status")
async def get_provider_status():
    """
    Get detailed status of all market data providers
    
    Example response:
    {
        "binance": {
            "status": "active",
            "asset_classes": ["CRYPTO"],
            "priority": 1
        },
        ...
    }
    """
    try:
        providers = await enhanced_market_service.get_active_providers()
        
        # Add summary statistics
        total = len(providers)
        active = sum(1 for p in providers.values() if p.get("status") == "active")
        
        return {
            "providers": providers,
            "summary": {
                "total": total,
                "active": active,
                "inactive": total - active
            }
        }
    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRYPTO-SPECIFIC ENDPOINT
# ============================================================================
@router.get("/crypto/{symbol}")
async def get_crypto_price(symbol: str):
    """
    Get cryptocurrency price (convenience endpoint)
    
    Example: GET /api/market/crypto/BTC
    """
    try:
        symbol = symbol.upper()
        price = await enhanced_market_service.get_crypto_price(symbol)
        
        if not price or price <= 0:
            raise HTTPException(
                status_code=404,
                detail=f"Cryptocurrency {symbol} not found"
            )
        
        return {
            "symbol": symbol,
            "price": price,
            "asset_class": "crypto",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching crypto {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STOCK-SPECIFIC ENDPOINT
# ============================================================================
@router.get("/stock/{symbol}")
async def get_stock_price(symbol: str):
    """
    Get stock price (convenience endpoint)
    
    Example: GET /api/market/stock/AAPL
    """
    try:
        symbol = symbol.upper()
        price = await enhanced_market_service.get_stock_price(symbol)
        
        if not price or price <= 0:
            raise HTTPException(
                status_code=404,
                detail=f"Stock {symbol} not found"
            )
        
        return {
            "symbol": symbol,
            "price": price,
            "asset_class": "stock",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
MARKET_HOURS: Dict[str, Dict[str, time]] = {
    "US": {"open": time(14, 30), "close": time(21, 0)},   # 9:30 AM - 4:00 PM EST
    "EU": {"open": time(8, 0), "close": time(16, 30)},    # 8:00 - 16:30 CET
    "ASIA": {"open": time(0, 0), "close": time(6, 0)},    # example
    "CRYPTO": {"open": time(0, 0), "close": time(23, 59)} # 24/7
}

TUNIS_OFFSET = timedelta(hours=1)  # UTC+1

@router.get("/status/{market}", response_model=dict)
async def get_market_status(
    market: str = Path(..., description="Market identifier (US, EU, ASIA, CRYPTO, etc.)")
):
    """
    Get current market status (open/closed) in Tunisian local time

    Example: GET /api/market/status/US
    """
    market_upper = market.upper()
    
    if market_upper not in MARKET_HOURS:
        raise HTTPException(status_code=404, detail=f"Market '{market}' not found")

    now_utc = datetime.utcnow().time()
    now_tunis = (datetime.utcnow() + TUNIS_OFFSET).time()
    hours = MARKET_HOURS[market_upper]

    is_open = hours["open"] <= now_utc <= hours["close"]

    # Convert open/close times to Tunisian time
    open_tunis = (datetime.combine(datetime.today(), hours["open"]) + TUNIS_OFFSET).time()
    close_tunis = (datetime.combine(datetime.today(), hours["close"]) + TUNIS_OFFSET).time()

    return {
        "market": market_upper,
        "status": "open" if is_open else "closed",
        "open_time_tunis": open_tunis.isoformat(),
        "close_time_tunis": close_tunis.isoformat(),
        "current_time_tunis": now_tunis.isoformat()
    }
