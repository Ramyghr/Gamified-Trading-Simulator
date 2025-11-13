"""
Enhanced Portfolio Router with Complete Leverage Trading Integration
Integrates spot holdings and leveraged positions seamlessly
File: app/routers/portfolio.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from decimal import Decimal
import math
import logging

from app.services.portfolio_service import PortfolioService
from app.services.leverage_trading_service import LeverageTradingService
from app.middleware.jwt_middleware import get_current_user
from app.config.database import get_db
from app.models.user import User
from app.models.portfolio import Position, LiquidationEvent
from app.models.stock_transaction import StockTransaction

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
    TransactionsPaginated,
    MarginHealthResponse,
    PortfolioPerformanceSummary,
    LiquidationHistory,
    LiquidationHistoryItem,
    PortfolioDashboard,
    QuickStatsWidget,
    LeveragedPositionSummary
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
logger = logging.getLogger(__name__)


# ============= CORE PORTFOLIO ENDPOINTS =============

@router.get("/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive portfolio overview including:
    - Total value (cash + holdings + leveraged positions)
    - P&L metrics
    - Asset allocation
    - Margin metrics (used, available, level)
    - Total exposure from leveraged positions
    """
    try:
        service = PortfolioService(db)
        return await service.get_overview(current_user.email)
    except Exception as e:
        logger.error(f"Error fetching portfolio overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio overview"
        )


@router.get("/stats", response_model=PortfolioStats)
async def get_portfolio_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed portfolio statistics including:
    - Trade statistics (wins, losses, win rate)
    - P&L metrics (realized, unrealized, total)
    - Performance metrics (returns, best/worst trades)
    - Leverage-specific stats (leveraged trades, liquidations, avg leverage)
    """
    try:
        service = PortfolioService(db)
        return service.get_stats(current_user.email)
    except Exception as e:
        logger.error(f"Error fetching portfolio stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio statistics"
        )


@router.get("/performance/summary", response_model=PortfolioPerformanceSummary)
async def get_performance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive performance summary with breakdown:
    - Overall performance metrics
    - Spot trading performance (holdings)
    - Leveraged trading performance (margin positions)
    - Risk metrics (leverage utilization, exposure ratio)
    """
    try:
        service = PortfolioService(db)
        performance_data = await service.get_portfolio_performance_summary(current_user.email)
        
        return PortfolioPerformanceSummary(
            overview=performance_data["overview"],
            spot_trading=performance_data["spot_trading"],
            leveraged_trading=performance_data["leveraged_trading"],
            risk_metrics=performance_data["risk_metrics"],
            last_updated=performance_data["last_updated"]
        )
    except Exception as e:
        logger.error(f"Error fetching performance summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch performance summary"
        )


@router.get("/dashboard", response_model=PortfolioDashboard)
async def get_portfolio_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete portfolio dashboard with all metrics:
    - Overview, performance, positions
    - Margin health status
    - Recent liquidations
    """
    try:
        service = PortfolioService(db)
        
        # Get all components
        overview = await service.get_overview(current_user.email)
        performance = await service.get_portfolio_performance_summary(current_user.email)
        positions = await service.get_detailed_positions(current_user.email)
        margin_health = await service.check_margin_health(current_user.email)
        liquidation_history = service.get_liquidation_history(current_user.email, limit=5)
        
        return PortfolioDashboard(
            overview=overview,
            performance=PortfolioPerformanceSummary(
                overview=performance["overview"],
                spot_trading=performance["spot_trading"],
                leveraged_trading=performance["leveraged_trading"],
                risk_metrics=performance["risk_metrics"],
                last_updated=performance["last_updated"]
            ),
            positions=positions,
            margin_health=MarginHealthResponse(**margin_health),
            recent_liquidations=[LiquidationHistoryItem(**liq) for liq in liquidation_history],
            last_updated=overview.last_updated
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio dashboard"
        )


# @router.get("/quick-stats", response_model=QuickStatsWidget)
# async def get_quick_stats(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get quick stats for dashboard widgets/summary cards
#     """
#     try:
#         service = PortfolioService(db)
#         portfolio = service.get_portfolio_by_email(current_user.email)
#         await service.update_portfolio_valuation(portfolio, force_refresh=False)
        
#         # Count open positions
#         open_positions = db.query(Position).filter(
#             and_(
#                 Position.portfolio_id == portfolio.id,
#                 Position.is_open == True
#             )
#         ).count()
        
#         # Determine margin health
#         margin_level = float(portfolio.margin_level)
#         if margin_level >= 200:
#             margin_health = "HEALTHY"
#             alert_level = "NONE"
#         elif margin_level >= 150:
#             margin_health = "GOOD"
#             alert_level = "INFO"
#         elif margin_level >= 120:
#             margin_health = "WARNING"
#             alert_level = "WARNING"
#         else:
#             margin_health = "CRITICAL"
#             alert_level = "DANGER"
        
#         # Count alerts (positions at risk)
#         positions_at_risk = db.query(Position).filter(
#             and_(
#                 Position.portfolio_id == portfolio.id,
#                 Position.is_open == True
#             )
#         ).all()
        
#         alerts_count = 0
#         for pos in positions_at_risk:
#             current_price = Decimal(str(pos.current_price))
#             liquidation_price = Decimal(str(pos.liquidation_price))
            
#             if pos.side.value == "LONG":
#                 distance = ((current_price - liquidation_price) / current_price * Decimal('100'))
#             else:
#                 distance = ((liquidation_price - current_price) / current_price * Decimal('100'))
            
#             if abs(distance) < Decimal('20'):
#                 alerts_count += 1
        
#         # Calculate daily change
#         from datetime import datetime, timedelta
#         yesterday = datetime.utcnow() - timedelta(days=1)
#         previous_snapshot = db.query(PortfolioDailySnapshotResponse).filter(
#             and_(
#                 PortfolioDailySnapshotResponse.portfolio_id == portfolio.id,
#                 PortfolioDailySnapshotResponse.date >= yesterday
#             )
#         ).order_by(desc(PortfolioDailySnapshotResponse.date)).first()
        
#         if previous_snapshot:
#             daily_change = float(portfolio.total_value) - float(previous_snapshot.total_value)
#             daily_change_pct = (daily_change / float(previous_snapshot.total_value) * 100) if previous_snapshot.total_value > 0 else 0
#         else:
#             daily_change = 0.0
#             daily_change_pct = 0.0
        
#         return QuickStatsWidget(
#             total_value=float(portfolio.total_value),
#             daily_change=daily_change,
#             daily_change_pct=daily_change_pct,
#             open_positions=open_positions,
#             margin_health=margin_health,
#             alert_level=alert_level,
#             alerts_count=alerts_count
#         )
#     except Exception as e:
#         logger.error(f"Error fetching quick stats: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to fetch quick stats"
#         )


# ============= HOLDINGS & POSITIONS =============

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
    """
    Get spot holdings (not leveraged positions) with pagination
    """
    try:
        service = PortfolioService(db)
        return await service.get_holdings(current_user.email, page, size, sort_by)
    except Exception as e:
        logger.error(f"Error fetching holdings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch holdings"
        )


@router.get("/positions/detailed", response_model=PortfolioPositionsDetailed)
async def get_detailed_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all positions (spot holdings + leveraged positions) with detailed metrics
    """
    try:
        service = PortfolioService(db)
        return await service.get_detailed_positions(current_user.email)
    except Exception as e:
        logger.error(f"Error fetching detailed positions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch detailed positions"
        )


@router.get("/positions/leveraged/{symbol}", response_model=LeveragedPositionSummary)
async def get_leveraged_position_summary(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary of leveraged positions for a specific symbol
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio_by_email(current_user.email)
        
        positions = db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.symbol == symbol.upper(),
                Position.is_open == True
            )
        ).all()
        
        if not positions:
            return LeveragedPositionSummary(
                symbol=symbol.upper(),
                long_quantity=Decimal('0'),
                short_quantity=Decimal('0'),
                net_quantity=Decimal('0'),
                long_exposure=Decimal('0'),
                short_exposure=Decimal('0'),
                net_exposure=Decimal('0'),
                total_margin_used=Decimal('0'),
                weighted_avg_leverage=0.0,
                positions_count=0
            )
        
        long_qty = Decimal('0')
        short_qty = Decimal('0')
        long_exposure = Decimal('0')
        short_exposure = Decimal('0')
        total_margin = Decimal('0')
        weighted_leverage = Decimal('0')
        
        for pos in positions:
            qty = Decimal(str(pos.quantity))
            price = Decimal(str(pos.current_price or pos.entry_price))
            exposure = qty * price
            margin = Decimal(str(pos.margin_used))
            leverage = Decimal(str(pos.leverage))
            
            if pos.side.value == "LONG":
                long_qty += qty
                long_exposure += exposure
            else:
                short_qty += qty
                short_exposure += exposure
            
            total_margin += margin
            weighted_leverage += leverage * margin
        
        avg_leverage = float(weighted_leverage / total_margin) if total_margin > 0 else 0.0
        
        return LeveragedPositionSummary(
            symbol=symbol.upper(),
            long_quantity=long_qty,
            short_quantity=short_qty,
            net_quantity=long_qty - short_qty,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            net_exposure=long_exposure - short_exposure,
            total_margin_used=total_margin,
            weighted_avg_leverage=avg_leverage,
            positions_count=len(positions)
        )
    except Exception as e:
        logger.error(f"Error fetching leveraged position summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leveraged position summary"
        )


@router.get("/holdings/{symbol}/quantity", response_model=QuantityResponse)
async def get_holding_quantity(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quantity of a specific spot holding
    """
    try:
        service = PortfolioService(db)
        quantity = service.get_holding_quantity(current_user.email, symbol)
        
        # Also get leveraged position info
        leveraged_info = service.get_leveraged_position_quantity(current_user.email, symbol)
        
        return QuantityResponse(
            symbol=symbol.upper(),
            quantity=float(quantity)
        )
    except Exception as e:
        logger.error(f"Error fetching holding quantity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch holding quantity"
        )


# ============= MARGIN & RISK MANAGEMENT =============

@router.get("/margin/health", response_model=MarginHealthResponse)
async def check_margin_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check margin health and get risk warnings
    Returns positions at risk of liquidation
    """
    try:
        service = PortfolioService(db)
        health_data = await service.check_margin_health(current_user.email)
        return MarginHealthResponse(**health_data)
    except Exception as e:
        logger.error(f"Error checking margin health: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check margin health"
        )


@router.get("/liquidations/history", response_model=LiquidationHistory)
async def get_liquidation_history(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's liquidation history
    """
    try:
        service = PortfolioService(db)
        liquidations_data = service.get_liquidation_history(current_user.email, limit)
        
        liquidations = [LiquidationHistoryItem(**liq) for liq in liquidations_data]
        total_loss = sum(liq.loss_amount for liq in liquidations)
        most_recent = liquidations[0].liquidated_at if liquidations else None
        
        return LiquidationHistory(
            liquidations=liquidations,
            total_liquidations=len(liquidations),
            total_loss=total_loss,
            most_recent=most_recent
        )
    except Exception as e:
        logger.error(f"Error fetching liquidation history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch liquidation history"
        )


# ============= HISTORY & PERFORMANCE =============

@router.get("/history", response_model=List[PortfolioHistoryPoint])
async def get_portfolio_history(
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get portfolio value history over time
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio_by_email(current_user.email)
        return service.get_history(portfolio.id, days)
    except Exception as e:
        logger.error(f"Error fetching portfolio history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio history"
        )


@router.get("/snapshots/daily", response_model=List[PortfolioDailySnapshotResponse])
async def get_daily_snapshots(
    days: int = Query(default=30, ge=1, le=365, description="Number of days of snapshots"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get daily portfolio snapshots
    """
    try:
        service = PortfolioService(db)
        return service.get_daily_snapshots(current_user.email, days)
    except Exception as e:
        logger.error(f"Error fetching daily snapshots: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch daily snapshots"
        )


# ============= RANKINGS & COMPARISONS =============

@router.get("/rank", response_model=PortfolioRank)
async def get_portfolio_rank(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get portfolio ranking compared to other users
    """
    try:
        service = PortfolioService(db)
        return service.get_rank(current_user.email)
    except Exception as e:
        logger.error(f"Error fetching portfolio rank: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio rank"
        )


# ============= ANALYSIS ENDPOINTS =============

@router.get("/analysis/best-worst", response_model=BestWorstHoldings)
async def get_best_worst_holdings(
    limit: int = Query(default=3, ge=1, le=10, description="Number of holdings per category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get best and worst performing holdings (spot only)
    """
    try:
        service = PortfolioService(db)
        return service.get_best_worst_holdings(current_user.email, limit)
    except Exception as e:
        logger.error(f"Error fetching best/worst holdings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch best/worst holdings"
        )


@router.get("/allocation", response_model=AllocationBreakdown)
async def get_asset_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get asset allocation including leveraged exposure
    """
    try:
        service = PortfolioService(db)
        return service.get_allocation(current_user.email)
    except Exception as e:
        logger.error(f"Error fetching asset allocation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch asset allocation"
        )


# ============= UTILITY ENDPOINTS =============

@router.get("/cash", response_model=CashBalanceResponse)
async def get_available_cash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available cash balance (considering margin requirements)
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio_by_email(current_user.email)
        
        # Calculate truly available cash (cash - margin used)
        available = service.get_available_cash(current_user.email)
        
        return CashBalanceResponse(
            cash_balance=float(portfolio.cash_balance),
            locked=portfolio.locked,
            available=float(available)
        )
    except Exception as e:
        logger.error(f"Error fetching cash balance: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cash balance"
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_portfolio_valuation(
    background_tasks: BackgroundTasks,
    force: bool = Query(default=False, description="Force refresh all prices from market"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh portfolio valuation with latest market prices
    Updates both spot holdings and leveraged positions
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio_by_email(current_user.email)
        
        # Update valuation with latest prices
        updated_portfolio = await service.update_portfolio_valuation(
            portfolio, 
            force_refresh=force
        )
        
        # Schedule metrics calculation in background
        background_tasks.add_task(
            service.calculate_portfolio_metrics,
            portfolio.id
        )
        
        return RefreshResponse(
            message="Portfolio valuation updated successfully",
            updated_at=updated_portfolio.last_valuation_update,
            total_value=float(updated_portfolio.total_value),
            holdings_updated=len(updated_portfolio.holdings)
        )
    except Exception as e:
        logger.error(f"Error refreshing portfolio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh portfolio"
        )


@router.get("/transactions", response_model=TransactionsPaginated)
async def get_transaction_history(
    page: int = Query(default=0, ge=0, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history (spot trades only)
    For leveraged position history, use /leverage/positions endpoint
    """
    try:
        offset = page * size
        query = db.query(StockTransaction).filter(
            StockTransaction.user_id == current_user.id
        ).order_by(desc(StockTransaction.executed_at))
        
        total = query.count()
        transactions = query.offset(offset).limit(size).all()
        
        from app.schemas.portfolio import TransactionResponse
        
        items = [
            TransactionResponse(
                id=t.id,
                symbol=t.symbol,
                action=t.transaction_type.value,
                quantity=float(t.quantity),
                price=float(t.price),
                total_amount=float(t.total_amount),
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
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction history"
        )


# ============= HEALTH CHECK =============

@router.get("/health")
async def portfolio_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Quick health check for portfolio system
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio_by_email(current_user.email)
        
        # Count positions
        holdings_count = len(portfolio.holdings)
        leveraged_positions_count = db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.is_open == True
            )
        ).count()
        
        return {
            "status": "healthy",
            "portfolio_id": portfolio.id,
            "holdings_count": holdings_count,
            "leveraged_positions_count": leveraged_positions_count,
            "total_value": float(portfolio.total_value),
            "margin_level": float(portfolio.margin_level),
            "last_update": portfolio.last_valuation_update
        }
    except Exception as e:
        logger.error(f"Portfolio health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }