"""
Simplified Watchlist Management with Enhanced Market Data
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.user import User
from app.config.database import get_db
from pydantic import BaseModel, Field
from app.middleware.jwt_middleware import get_current_user
from app.services.market_data_service import enhanced_market_service
from app.constants.market_constants import (
    POPULAR_STOCKS, POPULAR_CRYPTO, POPULAR_FOREX, 
    MAJOR_INDICES, POPULAR_COMMODITIES, AssetClass
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/watchlist", tags=["Watchlist"])


# ============================================================================
# Enhanced Pydantic Models
# ============================================================================

class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: str = Field(..., description="stock, crypto, forex, index, commodity")


class EnhancedQuoteResponse(BaseModel):
    symbol: str
    asset_type: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None
    timestamp: Optional[str] = None
    provider: Optional[str] = None
    market_status: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    asset_type: str
    added_at: str
    quotes: List[EnhancedQuoteResponse] = []
    
    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    items: List[WatchlistItemResponse] = []
    
    class Config:
        from_attributes = True


class MarketSummaryResponse(BaseModel):
    asset_class: str
    symbol_count: int
    symbols: List[str]


# ============================================================================
# Enhanced Watchlist Operations
# ============================================================================

@router.post("", response_model=WatchlistResponse, status_code=201)
async def create_watchlist(
    data: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new watchlist"""
    try:
        watchlist = Watchlist(
            user_id=current_user.id,
            name=data.name,
            description=data.description
        )
        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)
        
        return WatchlistResponse(
            id=watchlist.id,
            name=watchlist.name,
            description=watchlist.description,
            created_at=str(watchlist.created_at),
            items=[]
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[WatchlistResponse])
async def get_watchlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all user watchlists"""
    try:
        watchlists = db.query(Watchlist).filter(
            Watchlist.user_id == current_user.id
        ).all()
        
        result = []
        for wl in watchlists:
            items = [
                WatchlistItemResponse(
                    id=item.id,
                    symbol=item.symbol,
                    asset_type=item.asset_type or "stock",
                    added_at=str(item.added_at),
                    quotes=[]  # No quotes by default in list view
                )
                for item in wl.items
            ]
            
            result.append(WatchlistResponse(
                id=wl.id,
                name=wl.name,
                description=wl.description,
                created_at=str(wl.created_at),
                items=items
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error fetching watchlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: int,
    include_prices: bool = Query(True, description="Include current prices from all providers"),
    include_providers: List[str] = Query(["all"], description="Specific providers to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific watchlist with enhanced market data from all providers"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    items_with_quotes = []
    
    if include_prices and watchlist.items:
        # Get enhanced quotes for all items from all providers
        for item in watchlist.items:
            try:
                # Get quotes from all available providers for this symbol
                quotes = await enhanced_market_service.get_enhanced_quotes(
                    symbol=item.symbol,
                    asset_type=item.asset_type or "stock"
                )
                
                # Format quotes for response
                formatted_quotes = []
                for quote in quotes:
                    formatted_quotes.append(EnhancedQuoteResponse(
                        symbol=quote.symbol,
                        asset_type=item.asset_type or "stock",
                        price=quote.close,
                        change=quote.change,
                        change_percent=quote.change_percent,
                        volume=quote.volume,
                        high=quote.high,
                        low=quote.low,
                        open=quote.open,
                        previous_close=getattr(quote, 'previous_close', None),
                        timestamp=str(quote.timestamp) if quote.timestamp else None,
                        provider=quote.provider.value if quote.provider else None,
                        market_status=getattr(quote, 'market_status', None)
                    ))
                
                items_with_quotes.append(WatchlistItemResponse(
                    id=item.id,
                    symbol=item.symbol,
                    asset_type=item.asset_type or "stock",
                    added_at=str(item.added_at),
                    quotes=formatted_quotes
                ))
                
            except Exception as e:
                logger.error(f"Error getting quotes for {item.symbol}: {e}")
                # Add item without quotes if there's an error
                items_with_quotes.append(WatchlistItemResponse(
                    id=item.id,
                    symbol=item.symbol,
                    asset_type=item.asset_type or "stock",
                    added_at=str(item.added_at),
                    quotes=[]
                ))
    else:
        # Return items without quotes
        items_with_quotes = [
            WatchlistItemResponse(
                id=item.id,
                symbol=item.symbol,
                asset_type=item.asset_type or "stock",
                added_at=str(item.added_at),
                quotes=[]
            )
            for item in watchlist.items
        ]
    
    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        created_at=str(watchlist.created_at),
        items=items_with_quotes
    )


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    db.delete(watchlist)
    db.commit()
    
    return {"message": "Watchlist deleted"}


# ============================================================================
# Enhanced Watchlist Items
# ============================================================================

@router.post("/{watchlist_id}/items", status_code=201)
async def add_to_watchlist(
    watchlist_id: int,
    data: WatchlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add symbol to watchlist with asset type validation"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # Validate asset type
    valid_asset_types = ["stock", "crypto", "forex", "index", "commodity"]
    if data.asset_type not in valid_asset_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid asset type. Must be one of: {', '.join(valid_asset_types)}"
        )
    
    # Check if already exists
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.symbol == data.symbol.upper(),
        WatchlistItem.asset_type == data.asset_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")
    
    item = WatchlistItem(
        watchlist_id=watchlist_id,
        symbol=data.symbol.upper(),
        asset_type=data.asset_type
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return {
        "message": "Symbol added",
        "item": WatchlistItemResponse(
            id=item.id,
            symbol=item.symbol,
            asset_type=item.asset_type,
            added_at=str(item.added_at),
            quotes=[]
        )
    }


@router.delete("/{watchlist_id}/items/{symbol}")
async def remove_from_watchlist(
    watchlist_id: int,
    symbol: str,
    asset_type: str = Query(..., description="Asset type of the symbol to remove"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove symbol from watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    item = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.symbol == symbol.upper(),
        WatchlistItem.asset_type == asset_type
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Symbol not in watchlist")
    
    db.delete(item)
    db.commit()
    
    return {"message": "Symbol removed"}


# ============================================================================
# Enhanced Popular Symbols with All Asset Types
# ============================================================================

@router.get("/symbols/popular", response_model=Dict[str, Any])
async def get_popular_symbols(
    asset_type: Optional[str] = Query(None, description="stock, crypto, forex, index, commodity")
):
    """Get comprehensive popular symbols by category with enhanced data"""
    
    popular_symbols = {
        "stock": {
            "name": "US Stocks",
            "symbols": POPULAR_STOCKS[:50],  # Top 50 for performance
            "description": "Major US publicly traded companies"
        },
        "crypto": {
            "name": "Cryptocurrencies",
            "symbols": POPULAR_CRYPTO[:30],
            "description": "Major cryptocurrencies and tokens"
        },
        "forex": {
            "name": "Forex Pairs",
            "symbols": POPULAR_FOREX[:20],
            "description": "Major currency pairs"
        },
        "index": {
            "name": "Stock Indices",
            "symbols": MAJOR_INDICES[:15],
            "description": "Major global stock market indices"
        },
        "commodity": {
            "name": "Commodities",
            "symbols": POPULAR_COMMODITIES[:15],
            "description": "Major commodities and futures"
        }
    }
    
    if asset_type:
        asset_type_lower = asset_type.lower()
        if asset_type_lower in popular_symbols:
            return {
                "asset_type": asset_type_lower,
                "data": popular_symbols[asset_type_lower]
            }
        raise HTTPException(status_code=400, detail="Invalid asset_type")
    
    return {
        "all_categories": popular_symbols,
        "total_categories": len(popular_symbols),
        "timestamp": str(datetime.now())
    }


@router.get("/symbols/search")
async def search_symbols(
    query: str = Query(..., min_length=1, max_length=50, description="Symbol or company name to search"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    limit: int = Query(20, ge=1, le=50, description="Number of results")
):
    """Search symbols across all providers and asset types"""
    try:
        results = await enhanced_market_service.search_symbols(
            query=query,
            asset_type=asset_type,
            limit=limit
        )
        return {
            "query": query,
            "asset_type": asset_type,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail="Search service unavailable")


@router.get("/market/summary")
async def get_market_summary():
    """Get overall market summary with available symbols"""
    summary = {
        "stock": {
            "asset_class": "US Stocks",
            "symbol_count": len(POPULAR_STOCKS),
            "description": "Equities from major US exchanges"
        },
        "crypto": {
            "asset_class": "Cryptocurrencies",
            "symbol_count": len(POPULAR_CRYPTO),
            "description": "Digital currencies and tokens"
        },
        "forex": {
            "asset_class": "Forex Pairs",
            "symbol_count": len(POPULAR_FOREX),
            "description": "Currency exchange rates"
        },
        "index": {
            "asset_class": "Market Indices",
            "symbol_count": len(MAJOR_INDICES),
            "description": "Stock market indices"
        },
        "commodity": {
            "asset_class": "Commodities",
            "symbol_count": len(POPULAR_COMMODITIES),
            "description": "Physical goods and resources"
        }
    }
    
    return {
        "market_summary": summary,
        "total_asset_classes": len(summary),
        "total_symbols": sum(cat["symbol_count"] for cat in summary.values()),
        "last_updated": str(datetime.now())
    }


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/{watchlist_id}/items/batch")
async def add_multiple_to_watchlist(
    watchlist_id: int,
    items: List[WatchlistItemCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add multiple symbols to watchlist at once"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    added_items = []
    skipped_items = []
    
    for item_data in items:
        # Check if already exists
        existing = db.query(WatchlistItem).filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.symbol == item_data.symbol.upper(),
            WatchlistItem.asset_type == item_data.asset_type
        ).first()
        
        if existing:
            skipped_items.append({
                "symbol": item_data.symbol,
                "asset_type": item_data.asset_type,
                "reason": "Already exists"
            })
            continue
        
        item = WatchlistItem(
            watchlist_id=watchlist_id,
            symbol=item_data.symbol.upper(),
            asset_type=item_data.asset_type
        )
        db.add(item)
        added_items.append(item)
    
    db.commit()
    
    # Refresh to get IDs
    for item in added_items:
        db.refresh(item)
    
    return {
        "message": "Batch operation completed",
        "added": len(added_items),
        "skipped": len(skipped_items),
        "added_items": [
            {
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "id": item.id
            }
            for item in added_items
        ],
        "skipped_items": skipped_items
    }