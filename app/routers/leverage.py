"""
Leverage Trading API Router
Save as: app/routers/leverage.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.config.database import get_db
from app.models.user import User
from app.models.portfolio import Position, Portfolio, LiquidationEvent
from app.schemas.leverage import (
    OpenPositionRequest,
    ClosePositionRequest,
    PositionResponse,
    ClosePositionResponse,
    MarginInfoResponse,
    LeverageCalculatorRequest,
    LeverageCalculatorResponse,
    LiquidationEventResponse,
    PortfolioSummary,
    UpdateStopLossRequest,
    UpdateTakeProfitRequest,
    PositionMetrics,
    RiskMetrics
)
from app.services.leverage_trading_service import (
    LeverageTradingService,
    InsufficientMarginError,
    InvalidLeverageError,
    PositionNotFoundError
)
from app.services.margin_service import margin_service
from app.services.market_data_service import enhanced_market_service
from app.middleware.jwt_middleware import get_current_user
import logging
from datetime import datetime

router = APIRouter(prefix="/leverage", tags=["Leverage Trading"])
logger = logging.getLogger(__name__)


@router.post("/positions/open", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def open_position(
    request: OpenPositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Open a new leveraged position (LONG or SHORT).
    
    - **symbol**: Trading symbol (e.g., AAPL, TSLA)
    - **side**: LONG or SHORT
    - **quantity**: Position size
    - **leverage**: Leverage multiplier (1-100x depending on asset)
    - **order_type**: MARKET or LIMIT
    - **limit_price**: Required for LIMIT orders
    - **stop_loss**: Optional stop loss price
    - **take_profit**: Optional take profit price
    """
    try:
        trading_service = LeverageTradingService(db)
        
        position = await trading_service.open_leveraged_position(
            user_id=current_user.id,
            symbol=request.symbol,
            side=request.side.value,
            quantity=request.quantity,
            leverage=request.leverage,
            order_type=request.order_type,
            limit_price=request.limit_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit
        )
        
        logger.info(f"Position opened: {position.id} for user {current_user.id}")
        return position
        
    except InsufficientMarginError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidLeverageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error opening position: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open position"
        )


@router.post("/positions/close", response_model=ClosePositionResponse)
async def close_position(
    request: ClosePositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Close a leveraged position (fully or partially).
    
    - **position_id**: ID of the position to close
    - **quantity**: Amount to close (None = close entire position)
    - **exit_price**: Override exit price (for LIMIT close, None = market price)
    """
    try:
        trading_service = LeverageTradingService(db)
        
        result = await trading_service.close_leveraged_position(
            user_id=current_user.id,
            position_id=request.position_id,
            close_quantity=request.quantity,
            exit_price=request.exit_price
        )
        
        return ClosePositionResponse(
            success=True,
            message="Position closed successfully",
            **result
        )
        
    except PositionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close position"
        )


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    is_open: bool = Query(True, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all positions for the current user.
    
    - **symbol**: Filter by trading symbol (optional)
    - **is_open**: Show open or closed positions
    - **limit**: Maximum number of results
    - **offset**: Pagination offset
    """
    try:
        query = db.query(Position).filter(
            Position.user_id == current_user.id,
            Position.is_open == is_open
        )
        
        if symbol:
            query = query.filter(Position.symbol == symbol.upper())
        
        positions = query.order_by(
            Position.opened_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Update prices for open positions
        if is_open:
            trading_service = LeverageTradingService(db)
            for position in positions:
                await trading_service.update_position_prices(position)
            db.commit()
        
        return positions
        
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch positions"
        )


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific position.
    """
    try:
        trading_service = LeverageTradingService(db)
        position = trading_service.get_position_by_id(current_user.id, position_id)
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )
        
        # Update price if position is open
        if position.is_open:
            await trading_service.update_position_prices(position)
            db.commit()
        
        return position
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching position: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch position"
        )


@router.get("/positions/{position_id}/metrics", response_model=PositionMetrics)
async def get_position_metrics(
    position_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed metrics for a specific position.
    """
    try:
        trading_service = LeverageTradingService(db)
        position = trading_service.get_position_by_id(current_user.id, position_id)
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )
        
        # Update price
        await trading_service.update_position_prices(position)
        
        # Calculate metrics
        metrics = margin_service.calculate_position_metrics(
            side=position.side.value,
            quantity=Decimal(str(position.quantity)),
            entry_price=Decimal(str(position.entry_price)),
            current_price=Decimal(str(position.current_price)),
            leverage=Decimal(str(position.leverage)),
            margin_used=Decimal(str(position.margin_used))
        )
        
        # Get margin level
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == position.portfolio_id
        ).first()
        
        return PositionMetrics(
            position_id=position.id,
            symbol=position.symbol,
            side=position.side,
            current_price=Decimal(str(position.current_price)),
            entry_price=Decimal(str(position.entry_price)),
            quantity=Decimal(str(position.quantity)),
            unrealized_pnl=Decimal(str(metrics['unrealized_pnl'])),
            unrealized_pnl_pct=metrics['pnl_percentage'],
            roi=metrics['roi'],
            liquidation_price=Decimal(str(metrics['liquidation_price'])),
            distance_from_liquidation=metrics['distance_from_liquidation'],
            margin_level=float(portfolio.margin_level) if portfolio else 0.0,
            leverage=Decimal(str(position.leverage)),
            position_value=Decimal(str(metrics['position_value'])),
            margin_used=Decimal(str(position.margin_used)),
            maintenance_margin=Decimal(str(position.maintenance_margin))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching position metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch position metrics"
        )


@router.patch("/positions/{position_id}/stop-loss")
async def update_stop_loss(
    position_id: int,
    request: UpdateStopLossRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update stop loss price for a position.
    """
    try:
        trading_service = LeverageTradingService(db)
        position = trading_service.get_position_by_id(current_user.id, position_id)
        
        if not position or not position.is_open:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found or already closed"
            )
        
        # Validate stop loss
        if request.stop_loss_price:
            if position.side.value == "LONG" and request.stop_loss_price >= Decimal(str(position.entry_price)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stop loss must be below entry price for LONG positions"
                )
            if position.side.value == "SHORT" and request.stop_loss_price <= Decimal(str(position.entry_price)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stop loss must be above entry price for SHORT positions"
                )
        
        position.stop_loss_price = float(request.stop_loss_price) if request.stop_loss_price else None
        db.commit()
        
        return {"success": True, "message": "Stop loss updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stop loss: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update stop loss"
        )


@router.patch("/positions/{position_id}/take-profit")
async def update_take_profit(
    position_id: int,
    request: UpdateTakeProfitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update take profit price for a position.
    """
    try:
        trading_service = LeverageTradingService(db)
        position = trading_service.get_position_by_id(current_user.id, position_id)
        
        if not position or not position.is_open:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found or already closed"
            )
        
        # Validate take profit
        if request.take_profit_price:
            if position.side.value == "LONG" and request.take_profit_price <= Decimal(str(position.entry_price)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Take profit must be above entry price for LONG positions"
                )
            if position.side.value == "SHORT" and request.take_profit_price >= Decimal(str(position.entry_price)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Take profit must be below entry price for SHORT positions"
                )
        
        position.take_profit_price = float(request.take_profit_price) if request.take_profit_price else None
        db.commit()
        
        return {"success": True, "message": "Take profit updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating take profit: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update take profit"
        )


@router.get("/margin/info", response_model=MarginInfoResponse)
async def get_margin_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current margin information for the portfolio.
    """
    try:
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Count open positions
        open_positions_count = db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.is_open == True
        ).count()
        
        # Calculate total position value
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.is_open == True
        ).all()
        
        total_position_value = sum(
            Decimal(str(p.quantity)) * Decimal(str(p.current_price or p.entry_price))
            for p in positions
        )
        
        return MarginInfoResponse(
            cash_balance=Decimal(str(portfolio.cash_balance)),
            equity=Decimal(str(portfolio.equity)),
            margin_used=Decimal(str(portfolio.margin_used)),
            margin_available=Decimal(str(portfolio.margin_available)),
            margin_level=float(portfolio.margin_level),
            total_exposure=Decimal(str(portfolio.total_exposure)),
            unrealized_pnl=Decimal(str(portfolio.unrealized_pnl)),
            max_leverage=Decimal(str(portfolio.max_leverage)),
            open_positions_count=open_positions_count,
            total_position_value=total_position_value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching margin info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch margin info"
        )


@router.post("/calculator", response_model=LeverageCalculatorResponse)
async def calculate_leverage(
    request: LeverageCalculatorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate margin requirements and risk metrics for a potential position.
    Useful for planning trades before opening them.
    """
    try:
        # Get entry price
        if request.entry_price:
            entry_price = request.entry_price
        else:
            price = await enhanced_market_service.get_price(request.symbol, "STOCK")
            if not price or price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to fetch market price"
                )
            entry_price = Decimal(str(price))
        
        # Calculate margin required
        margin_required = margin_service.calculate_margin_required(
            request.quantity, entry_price, request.leverage
        )
        
        # Calculate position value
        position_value = request.quantity * entry_price
        
        # Calculate maintenance margin
        maintenance_margin = margin_service.calculate_maintenance_margin(position_value)
        
        # Calculate liquidation price
        if request.side == "LONG":
            liquidation_price = margin_service.calculate_liquidation_price_long(
                entry_price, request.leverage
            )
        else:
            liquidation_price = margin_service.calculate_liquidation_price_short(
                entry_price, request.leverage
            )
        
        # Calculate max loss (margin + fees)
        open_fee = position_value * Decimal("0.0005")
        close_fee = position_value * Decimal("0.0005")
        total_fees = open_fee + close_fee
        max_loss = margin_required + total_fees
        
        # Calculate break-even price (including fees)
        fee_percentage = total_fees / position_value
        if request.side == "LONG":
            break_even_price = entry_price * (Decimal('1') + fee_percentage)
        else:
            break_even_price = entry_price * (Decimal('1') - fee_percentage)
        
        # Calculate profit/loss scenarios
        def calculate_pnl(exit_price: Decimal) -> Decimal:
            if request.side == "LONG":
                pnl = (exit_price - entry_price) * request.quantity
            else:
                pnl = (entry_price - exit_price) * request.quantity
            return pnl - total_fees
        
        profit_10 = calculate_pnl(entry_price * Decimal('1.10'))
        profit_20 = calculate_pnl(entry_price * Decimal('1.20'))
        loss_10 = calculate_pnl(entry_price * Decimal('0.90'))
        loss_20 = calculate_pnl(entry_price * Decimal('0.80'))
        
        return LeverageCalculatorResponse(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            entry_price=entry_price,
            leverage=request.leverage,
            margin_required=margin_required,
            maintenance_margin=maintenance_margin,
            position_value=position_value,
            liquidation_price=liquidation_price,
            max_loss=max_loss,
            max_gain=None,  # Unlimited for LONG, capped at entry for SHORT
            estimated_open_fee=open_fee,
            estimated_close_fee=close_fee,
            total_estimated_fees=total_fees,
            break_even_price=break_even_price,
            profit_at_10_pct=profit_10,
            profit_at_20_pct=profit_20,
            loss_at_10_pct=loss_10,
            loss_at_20_pct=loss_20
        )
        
    except Exception as e:
        logger.error(f"Error calculating leverage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate leverage"
        )


@router.get("/liquidations/history", response_model=List[LiquidationEventResponse])
async def get_liquidation_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get liquidation history for the current user.
    """
    try:
        liquidations = db.query(LiquidationEvent).filter(
            LiquidationEvent.user_id == current_user.id
        ).order_by(
            LiquidationEvent.liquidated_at.desc()
        ).limit(limit).offset(offset).all()
        
        return liquidations
        
    except Exception as e:
        logger.error(f"Error fetching liquidation history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch liquidation history"
        )


@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive portfolio summary with margin metrics.
    """
    try:
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get open positions
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.is_open == True
        ).all()
        
        # Update all position prices
        trading_service = LeverageTradingService(db)
        for position in positions:
            await trading_service.update_position_prices(position)
        
        # Calculate average leverage
        if positions:
            total_weighted_leverage = sum(
                Decimal(str(p.leverage)) * Decimal(str(p.margin_used))
                for p in positions
            )
            total_margin = sum(Decimal(str(p.margin_used)) for p in positions)
            avg_leverage = float(total_weighted_leverage / total_margin) if total_margin > 0 else 0.0
        else:
            avg_leverage = 0.0
        
        # Count positions at risk (within 20% of liquidation)
        positions_at_risk = 0
        for position in positions:
            liquidation_price = Decimal(str(position.liquidation_price))
            current_price = Decimal(str(position.current_price))
            
            _, distance = margin_service.check_liquidation_risk(
                current_price, liquidation_price, position.side.value
            )
            
            if abs(distance) < Decimal('20'):
                positions_at_risk += 1
        
        # Determine liquidation risk level
        margin_level = Decimal(str(portfolio.margin_level))
        if margin_level >= Decimal('200'):
            risk_level = "LOW"
        elif margin_level >= Decimal('150'):
            risk_level = "MEDIUM"
        elif margin_level >= Decimal('110'):
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        # Calculate returns (placeholder - implement based on your history)
        total_return = Decimal(str(portfolio.equity)) - Decimal(str(portfolio.initial_balance))
        total_return_pct = (total_return / Decimal(str(portfolio.initial_balance))) * Decimal('100')
        
        return PortfolioSummary(
            cash_balance=Decimal(str(portfolio.cash_balance)),
            equity=Decimal(str(portfolio.equity)),
            total_value=Decimal(str(portfolio.total_value)),
            margin_used=Decimal(str(portfolio.margin_used)),
            margin_available=Decimal(str(portfolio.margin_available)),
            margin_level=float(portfolio.margin_level),
            unrealized_pnl=Decimal(str(portfolio.unrealized_pnl)),
            realized_pnl=Decimal('0'),  # TODO: Calculate from closed positions
            total_pnl=Decimal(str(portfolio.unrealized_pnl)),
            open_positions=len(positions),
            total_exposure=Decimal(str(portfolio.total_exposure)),
            avg_leverage=avg_leverage,
            total_return=total_return,
            total_return_pct=float(total_return_pct),
            daily_return=Decimal('0'),  # TODO: Calculate from history
            daily_return_pct=0.0,
            liquidation_risk=risk_level,
            positions_at_risk=positions_at_risk,
            last_updated=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio summary"
        )


@router.get("/risk/metrics", response_model=RiskMetrics)
async def get_risk_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed risk metrics for the portfolio.
    """
    try:
        portfolio = db.query(Portfolio).filter(
            Portfolio.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get all open positions
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.is_open == True
        ).all()
        
        # Calculate max exposure allowed (based on equity and max leverage)
        equity = Decimal(str(portfolio.equity))
        max_leverage = Decimal(str(portfolio.max_leverage))
        max_exposure_allowed = equity * max_leverage
        
        # Calculate exposure utilization
        total_exposure = Decimal(str(portfolio.total_exposure))
        exposure_utilization = float((total_exposure / max_exposure_allowed) * Decimal('100')) if max_exposure_allowed > 0 else 0.0
        
        # Calculate margin utilization
        margin_used = Decimal(str(portfolio.margin_used))
        margin_utilization = float((margin_used / equity) * Decimal('100')) if equity > 0 else 0.0
        
        # Calculate average and max leverage
        if positions:
            leverages = [Decimal(str(p.leverage)) for p in positions]
            avg_leverage = float(sum(leverages) / len(leverages))
            max_leverage_in_use = float(max(leverages))
        else:
            avg_leverage = 0.0
            max_leverage_in_use = 0.0
        
        # Calculate Value at Risk (simple estimation)
        var_1pct = total_exposure * Decimal('0.01')  # 1% market move
        var_5pct = total_exposure * Decimal('0.05')  # 5% market move
        
        # Count positions near liquidation
        positions_near_liquidation = 0
        for position in positions:
            liquidation_price = Decimal(str(position.liquidation_price))
            current_price = Decimal(str(position.current_price))
            
            _, distance = margin_service.check_liquidation_risk(
                current_price, liquidation_price, position.side.value
            )
            
            if abs(distance) < Decimal('15'):  # Within 15%
                positions_near_liquidation += 1
        
        # Calculate liquidation buffer (simplified)
        # How much equity before first liquidation occurs
        liquidation_buffer = equity - margin_used
        
        return RiskMetrics(
            total_exposure=total_exposure,
            max_exposure_allowed=max_exposure_allowed,
            exposure_utilization=exposure_utilization,
            margin_utilization=margin_utilization,
            average_leverage=avg_leverage,
            max_leverage_in_use=max_leverage_in_use,
            value_at_risk_1pct=var_1pct,
            value_at_risk_5pct=var_5pct,
            positions_near_liquidation=positions_near_liquidation,
            estimated_liquidation_buffer=max(liquidation_buffer, Decimal('0'))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch risk metrics"
        )


@router.post("/positions/{position_id}/refresh")
async def refresh_position(
    position_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force refresh position price and metrics.
    """
    try:
        trading_service = LeverageTradingService(db)
        position = trading_service.get_position_by_id(current_user.id, position_id)
        
        if not position or not position.is_open:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found or already closed"
            )
        
        await trading_service.update_position_prices(position)
        db.commit()
        
        return {
            "success": True,
            "message": "Position refreshed",
            "current_price": float(position.current_price),
            "unrealized_pnl": float(position.unrealized_pnl),
            "last_update": position.last_price_update
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing position: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh position"
        )