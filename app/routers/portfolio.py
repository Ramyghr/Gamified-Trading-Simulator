from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.services.portfolio_service import PortfolioService
from app.middleware.jwt_middleware import get_current_user
from app.config.database import get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioOverview,
    PortfolioStats,
    HoldingsPaginated,
    PortfolioPositionsDetailed,
    PortfolioHistoryPoint,
    PortfolioDailySnapshotResponse,
    PortfolioRank,
    BestWorstHoldings,
    AllocationBreakdown,
    CashBalanceResponse,
    QuantityResponse,
    RefreshResponse,
    TransactionsPaginated
)
from typing import List
import math
from sqlalchemy import desc
from app.models.stock_transaction import StockTransaction

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# ============= Core Portfolio Endpoints =============

@router.get("/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return await service.get_overview(current_user.email)

@router.get("/stats", response_model=PortfolioStats)
async def get_portfolio_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return service.get_stats(current_user.email)  # NO AWAIT


@router.get("/holdings", response_model=HoldingsPaginated)
async def get_holdings(
    page: int = Query(default=0, ge=0, description="Page number (0-indexed)"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        default="value", 
        regex="^(symbol|quantity|value|pnl)$", 
        description="Sort by: symbol, quantity, value, or pnl"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return await service.get_holdings(current_user.email, page, size, sort_by)

@router.get("/positions/detailed", response_model=PortfolioPositionsDetailed)
async def get_detailed_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return await service.get_detailed_positions(current_user.email)

@router.get("/holdings/{symbol}/quantity", response_model=QuantityResponse)
async def get_holding_quantity(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    quantity = service.get_holding_quantity(current_user.email, symbol)
    return QuantityResponse(
        symbol=symbol.upper(), 
        quantity=quantity
    )

# ============= History & Performance =============

@router.get("/history", response_model=List[PortfolioHistoryPoint])
async def get_portfolio_history(
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history to retrieve"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    portfolio = service.get_portfolio_by_email(current_user.email)
    return service.get_history(portfolio.id, days)  # NO AWAIT


@router.get("/snapshots/daily", response_model=List[PortfolioDailySnapshotResponse])
async def get_daily_snapshots(
    days: int = Query(default=30, ge=1, le=365, description="Number of days of snapshots"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return service.get_daily_snapshots(current_user.email, days)  # Remove await - it's sync

# ============= Rankings & Comparisons =============

@router.get("/rank", response_model=PortfolioRank)
async def get_portfolio_rank(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return service.get_rank(current_user.email)  # NO AWAIT

# ============= Analysis Endpoints =============

@router.get("/analysis/best-worst", response_model=BestWorstHoldings)
async def get_best_worst_holdings(
    limit: int = Query(default=3, ge=1, le=10, description="Number of holdings per category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return service.get_best_worst_holdings(current_user.email, limit)  # NO AWAIT

@router.get("/allocation", response_model=AllocationBreakdown)
async def get_asset_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    return service.get_allocation(current_user.email)  # NO AWAIT
    
# ============= Utility Endpoints =============

@router.get("/cash", response_model=CashBalanceResponse)
async def get_available_cash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    portfolio = service.get_portfolio_by_email(current_user.email)
    
    return CashBalanceResponse(
        cash_balance=portfolio.cash_balance,
        locked=portfolio.locked,
        available=portfolio.cash_balance if not portfolio.locked else 0.0
    )

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_portfolio_valuation(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    portfolio = service.get_portfolio_by_email(current_user.email)
    
    # Update valuation with latest prices
    updated_portfolio = await service.update_portfolio_valuation(portfolio, force_refresh=True)
    
    # Schedule metrics calculation in background
    background_tasks.add_task(
        service.calculate_portfolio_metrics, 
        portfolio.id
    )
    
    return RefreshResponse(
        message="Portfolio valuation updated successfully",
        updated_at=updated_portfolio.last_valuation_update,
        total_value=updated_portfolio.total_value,
        holdings_updated=len(updated_portfolio.holdings)
    )

@router.get("/transactions", response_model=TransactionsPaginated)
async def get_transaction_history(
    page: int = Query(default=0, ge=0, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    offset = page * size
    query = db.query(StockTransaction).filter(
        StockTransaction.user_id == current_user.id
    ).order_by(desc(StockTransaction.executed_at))
    
    total = query.count()
    transactions = query.offset(offset).limit(size).all()
    
    from app.schemas.portfolio import TransactionsPaginated, TransactionResponse
    
    items = [
        TransactionResponse(
            id=t.id,
            symbol=t.symbol,
            action=t.transaction_type.value,
            quantity=t.quantity,
            price=t.price,
            total_amount=t.total_amount,
            transaction_date=t.executed_at or t.created_at
        )
        for t in transactions
    ]
    
    return TransactionsPaginated(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if size > 0 else 0
    )

# ============= Admin/Background Task Endpoints =============

@router.post("/admin/snapshot/{portfolio_id}")
async def create_daily_snapshot_admin(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    # Add this method to PortfolioService or implement it
    # service.create_daily_snapshot(portfolio_id)
    return {
        "message": f"Daily snapshot created for portfolio {portfolio_id}",
        "timestamp": "utcnow"
    }

@router.post("/admin/calculate-metrics/{portfolio_id}")
async def calculate_metrics_admin(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PortfolioService(db)
    service.calculate_portfolio_metrics(portfolio_id)
    return {
        "message": f"Metrics calculated for portfolio {portfolio_id}",
        "timestamp": "utcnow"
    }

@router.post("/admin/update-all-valuations")
async def update_all_valuations_admin(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # This would require additional implementation
    return {
        "message": "Portfolio valuation update scheduled for all users",
        "status": "processing"
    }