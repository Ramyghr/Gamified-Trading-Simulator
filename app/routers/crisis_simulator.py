"""
Crisis Simulator API Router - Enhanced Version
FastAPI endpoints for managing and interacting with crisis simulations
"""
from fastapi import APIRouter,Form, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime

from app.config.database import get_db
from app.models.user import User
from app.models.crisis_simulator import (
    CrisisSimulation, SimulationParticipant, SimulationOrder,
    SimulationPosition, SimulationLeaderboard, SimulationSnapshot,
    SimulationStatus, CrisisType
)
from app.schemas.crisis_simulator import (
    CreateSimulationRequest, SimulationResponse, JoinSimulationRequest,
    ParticipantResponse, PlaceOrderRequest, OrderResponse,
    PositionResponse, LeaderboardResponse, LeaderboardEntry,
    MarketDataResponse, AvailableAssetsResponse, SimulationStateResponse,
    SimulationControlResponse, SimulationHistoryResponse, SimulationStatsResponse,
    ParticipantStatsResponse
)
from app.middleware.jwt_middleware import get_current_user
from app.middleware.role_middleware import require_admin
from app.crisis_simulator.engine import SimulationEngine
from app.crisis_simulator.data_loader import HistoricalDataLoader
from app.crisis_simulator.historical_order_processor import HistoricalOrderProcessor
import logging
router = APIRouter(prefix="/api/crisis-simulator", tags=["Crisis Simulator"])
logger = logging.getLogger(__name__)




# ============================================================================
# USER ENDPOINTS - Participation & Trading
# ============================================================================

@router.get("/simulations/active", response_model=Optional[SimulationResponse])
async def get_active_simulation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get currently active or pending simulation
    
    - Returns the simulation users can join or are participating in
    - Returns None if no simulation is available
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status.in_([SimulationStatus.ACTIVE, SimulationStatus.PENDING])
    ).first()
    
    if not simulation:
        return None
    
    participant_count = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id
    ).count()
    
    # Calculate progress if active
    progress = None
    if simulation.status == SimulationStatus.ACTIVE and simulation.real_start_time:
        elapsed = (datetime.utcnow() - simulation.real_start_time).total_seconds()
        total_duration = simulation.duration_minutes * 60
        progress = min((elapsed / total_duration) * 100, 100.0)
    
    return SimulationResponse(
        **simulation.__dict__,
        participant_count=participant_count,
        progress_percentage=progress
    )


@router.post("/simulations/{simulation_id}/join", response_model=ParticipantResponse)
async def join_simulation(
    simulation_id: int,
    request: JoinSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Join a pending simulation
    
    - Can only join before simulation starts
    - Each user gets an isolated portfolio
    - Starting cash is configurable
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.status != SimulationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join simulation that has already started"
        )
    
    # Check if already joined
    existing = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation_id,
        SimulationParticipant.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already joined this simulation"
        )
    
    # Check participant limit
    participant_count = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation_id
    ).count()
    
    if participant_count >= simulation.max_participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation is full"
        )
    
    # Create participant
    participant = SimulationParticipant(
        simulation_id=simulation_id,
        user_id=current_user.id,
        initial_cash=request.initial_cash,
        initial_portfolio_value=request.initial_cash,
        current_cash=request.initial_cash
    )
    
    db.add(participant)
    db.commit()
    db.refresh(participant)
    
    return ParticipantResponse(**participant.__dict__)


@router.delete("/simulations/{simulation_id}/leave", response_model=SimulationControlResponse)
async def leave_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Leave a pending simulation
    
    - Can only leave before simulation starts
    - Removes participant and all their data
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.status != SimulationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot leave simulation that has already started"
        )
    
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation_id,
        SimulationParticipant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in this simulation"
        )
    
    try:
        db.delete(participant)
        db.commit()
        
        return SimulationControlResponse(
            success=True,
            message="Successfully left the simulation",
            simulation_id=simulation_id,
            new_status=simulation.status.value
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error leaving simulation: {str(e)}"
        )




@router.get("/crisis-types", response_model=List[dict])
async def get_available_crisis_types(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all available crisis types with metadata
    
    - Shows all historical crises available for simulation
    - Includes date ranges and asset counts
    """
    data_loader = HistoricalDataLoader()
    crisis_info = []
    
    for crisis_type in CrisisType:
        try:
            assets = data_loader.get_available_assets(crisis_type.value)
            start_date, end_date = data_loader.get_date_range(crisis_type.value)
            
            crisis_info.append({
                "type": crisis_type.value,
                "name": crisis_type.value.replace("_", " ").title(),
                "asset_count": len(assets),
                "date_range_start": start_date.isoformat(),
                "date_range_end": end_date.isoformat(),
                "duration_days": (end_date - start_date).days,
                "available": True
            })
        except Exception as e:
            crisis_info.append({
                "type": crisis_type.value,
                "name": crisis_type.value.replace("_", " ").title(),
                "available": False,
                "error": str(e)
            })
    
    return crisis_info







# ============================================================================
# TRADING ENDPOINTS - FIXED
# ============================================================================

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    request: PlaceOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Place an order during active simulation - FIXED
    
    - Market orders execute immediately
    - Limit/Stop orders execute when conditions met
    - Properly opens/closes positions
    """
    # Find active simulation
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active simulation"
        )
    
    # Get participant
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id,
        SimulationParticipant.is_active == True
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in active simulation"
        )
    
    # Validate order
    data_loader = HistoricalDataLoader()
    order_processor = HistoricalOrderProcessor(data_loader, simulation.crisis_type.value)
    
    is_valid, rejection_reason = order_processor.validate_order(
        participant=participant,
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        limit_price=request.limit_price,
        historical_time=simulation.current_historical_time,
        db=db
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=rejection_reason
        )
    
    # Create order
    order = SimulationOrder(
        participant_id=participant.id,
        symbol=request.symbol,
        order_type=request.order_type,
        side=request.side,
        quantity=request.quantity,
        limit_price=request.limit_price,
        stop_price=request.stop_price,
        placed_at_historical=simulation.current_historical_time,
        placed_at_real=datetime.utcnow(),
        status="PENDING"
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Execute orders immediately based on type
    if request.order_type == "MARKET":
        # Market orders fill immediately
        order_processor.execute_market_order(
            order, participant, simulation.current_historical_time, db
        )
        db.refresh(order)
        db.refresh(participant)
    elif request.order_type == "LIMIT":
        # Try to execute limit order
        executed = order_processor.execute_limit_order(
            order, participant, simulation.current_historical_time, db
        )
        if executed:
            db.refresh(order)
            db.refresh(participant)
    elif request.order_type == "STOP":
        # Try to execute stop order
        executed = order_processor.execute_stop_order(
            order, participant, simulation.current_historical_time, db
        )
        if executed:
            db.refresh(order)
            db.refresh(participant)
    
    return OrderResponse(**order.__dict__)

@router.get("/dashboard/trading", response_model=dict)
async def get_trading_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get trading dashboard data
    """
    # Get active simulation
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status.in_([SimulationStatus.ACTIVE, SimulationStatus.PENDING])
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No simulation available"
        )
    
    # Get participant
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id
    ).first()
    
    # Get symbols for this crisis
    data_loader = HistoricalDataLoader()
    symbols = data_loader.get_available_assets(simulation.crisis_type.value)
    
    return {
        "simulation": simulation.__dict__,
        "participant": participant.__dict__ if participant else None,
        "available_symbols": symbols[:10],  # First 10 symbols
        "can_trade": participant is not None and simulation.status == SimulationStatus.ACTIVE
    }
@router.post("/positions/{position_id}/close", response_model=dict)
async def close_position(
    position_id: int,
    quantity: Optional[float] = None,  # Changed from Query(None)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Close an open position (full or partial) - COMPLETELY FIXED
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active simulation"
        )
    
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id,
        SimulationParticipant.is_active == True
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in active simulation"
        )
    
    position = db.query(SimulationPosition).filter(
        SimulationPosition.id == position_id,
        SimulationPosition.participant_id == participant.id
    ).first()
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Determine quantity and side for closing order
    close_qty = quantity if quantity else abs(position.quantity)
    
    if close_qty > abs(position.quantity):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot close {close_qty} shares. Position only has {abs(position.quantity)} shares"
        )
    
    if close_qty <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive"
        )
    
    # Determine order side (opposite of position)
    if position.quantity > 0:
        # Long position - close by selling
        order_side = "SELL"
    else:
        # Short position - close by buying
        order_side = "BUY"
    
    # Get current price
    data_loader = HistoricalDataLoader()
    current_price = data_loader.get_price_at_time(
        simulation.crisis_type.value,
        position.symbol,
        simulation.current_historical_time
    )
    
    if not current_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to get current price for {position.symbol}"
        )
    
    # Create closing market order
    closing_order = SimulationOrder(
        participant_id=participant.id,
        symbol=position.symbol,
        order_type="MARKET",
        side=order_side,
        quantity=close_qty,
        placed_at_historical=simulation.current_historical_time,
        placed_at_real=datetime.utcnow(),
        status="PENDING"
    )
    
    db.add(closing_order)
    db.flush()
    
    # Execute the closing order
    order_processor = HistoricalOrderProcessor(data_loader, simulation.crisis_type.value)
    
    try:
        success = order_processor.execute_market_order(
            closing_order, participant, simulation.current_historical_time, db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to execute closing order"
            )
        
        db.refresh(closing_order)
        db.refresh(participant)
        
        # Get updated position (may have been deleted if fully closed)
        updated_position = db.query(SimulationPosition).filter(
            SimulationPosition.id == position_id
        ).first()
        
        # Calculate P&L
        execution_price = closing_order.filled_price
        
        if position.quantity > 0:  # Was long
            realized_pnl = (execution_price - position.average_cost) * close_qty
        else:  # Was short
            realized_pnl = (position.average_cost - execution_price) * close_qty
        
        realized_pnl_pct = ((execution_price / position.average_cost) - 1) * 100
        if position.quantity < 0:
            realized_pnl_pct = -realized_pnl_pct
        
        gross_proceeds = execution_price * close_qty
        commission = closing_order.commission
        net_proceeds = gross_proceeds - commission
        
        # Update participant stats
        if realized_pnl > 0:
            participant.profitable_trades += 1
        
        # Recalculate portfolio value
        total_portfolio_value = order_processor.calculate_portfolio_value(
            participant, simulation.current_historical_time, db
        )
        
        participant.current_portfolio_value = total_portfolio_value - participant.current_cash
        participant.current_total_value = total_portfolio_value
        participant.total_return_pct = ((total_portfolio_value / participant.initial_portfolio_value) - 1) * 100
        
        if participant.total_return_pct < participant.max_drawdown_pct:
            participant.max_drawdown_pct = participant.total_return_pct
        
        db.commit()
        
        position_fully_closed = updated_position is None
        remaining_quantity = 0 if position_fully_closed else abs(updated_position.quantity)
        
        return {
            "success": True,
            "message": f"Successfully closed {close_qty} shares of {position.symbol}",
            "closing_details": {
                "symbol": position.symbol,
                "quantity_closed": close_qty,
                "remaining_quantity": remaining_quantity,
                "average_cost": round(position.average_cost, 2),
                "closing_price": round(execution_price, 2),
                "gross_proceeds": round(gross_proceeds, 2),
                "commission": round(commission, 2),
                "net_proceeds": round(net_proceeds, 2),
                "realized_pnl": round(realized_pnl, 2),
                "realized_pnl_pct": round(realized_pnl_pct, 2),
                "position_fully_closed": position_fully_closed
            },
            "updated_portfolio": {
                "current_cash": round(participant.current_cash, 2),
                "portfolio_value": round(participant.current_portfolio_value or 0, 2),
                "total_value": round(participant.current_total_value or 0, 2),
                "total_return_pct": round(participant.total_return_pct, 2)
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing position: {str(e)}"
        )


@router.post("/positions/close-all", response_model=dict)
async def close_all_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Close all open positions at once - FIXED
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active simulation"
        )
    
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id,
        SimulationParticipant.is_active == True
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in active simulation"
        )
    
    positions = db.query(SimulationPosition).filter(
        SimulationPosition.participant_id == participant.id
    ).all()
    
    if not positions:
        return {
            "success": True,
            "message": "No open positions to close",
            "positions_closed": 0,
            "total_realized_pnl": 0.0
        }
    
    data_loader = HistoricalDataLoader()
    order_processor = HistoricalOrderProcessor(data_loader, simulation.crisis_type.value)
    
    closed_positions = []
    total_realized_pnl = 0.0
    failed_closures = []
    
    for position in positions:
        try:
            current_price = data_loader.get_price_at_time(
                simulation.crisis_type.value,
                position.symbol,
                simulation.current_historical_time
            )
            
            if not current_price:
                failed_closures.append({
                    "symbol": position.symbol,
                    "reason": "Price not available"
                })
                continue
            
            # Determine closing side
            order_side = "SELL" if position.quantity > 0 else "BUY"
            close_qty = abs(position.quantity)
            
            closing_order = SimulationOrder(
                participant_id=participant.id,
                symbol=position.symbol,
                order_type="MARKET",
                side=order_side,
                quantity=close_qty,
                placed_at_historical=simulation.current_historical_time,
                placed_at_real=datetime.utcnow(),
                status="PENDING"
            )
            
            db.add(closing_order)
            db.flush()
            
            success = order_processor.execute_market_order(
                closing_order, participant, simulation.current_historical_time, db
            )
            
            if success:
                db.refresh(closing_order)
                
                if position.quantity > 0:
                    realized_pnl = (closing_order.filled_price - position.average_cost) * close_qty
                else:
                    realized_pnl = (position.average_cost - closing_order.filled_price) * close_qty
                
                total_realized_pnl += realized_pnl
                
                if realized_pnl > 0:
                    participant.profitable_trades += 1
                
                closed_positions.append({
                    "symbol": position.symbol,
                    "quantity": close_qty,
                    "side": "LONG" if position.quantity > 0 else "SHORT",
                    "average_cost": round(position.average_cost, 2),
                    "closing_price": round(closing_order.filled_price, 2),
                    "realized_pnl": round(realized_pnl, 2)
                })
            else:
                failed_closures.append({
                    "symbol": position.symbol,
                    "reason": "Order execution failed"
                })
                
        except Exception as e:
            failed_closures.append({
                "symbol": position.symbol,
                "reason": str(e)
            })
    
    # Recalculate portfolio
    total_portfolio_value = order_processor.calculate_portfolio_value(
        participant, simulation.current_historical_time, db
    )
    
    participant.current_portfolio_value = total_portfolio_value - participant.current_cash
    participant.current_total_value = total_portfolio_value
    participant.total_return_pct = ((total_portfolio_value / participant.initial_portfolio_value) - 1) * 100
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Closed {len(closed_positions)} positions",
        "positions_closed": len(closed_positions),
        "positions_failed": len(failed_closures),
        "total_realized_pnl": round(total_realized_pnl, 2),
        "closed_positions": closed_positions,
        "failed_closures": failed_closures,
        "updated_portfolio": {
            "current_cash": round(participant.current_cash, 2),
            "portfolio_value": round(participant.current_portfolio_value or 0, 2),
            "total_value": round(participant.current_total_value or 0, 2),
            "total_return_pct": round(participant.total_return_pct, 2)
        }
    }

"""
Crisis Simulator API Router - FIXED VERSION (Part 2)
Leaderboard with P&L, Market Data synced to simulation timeline, Stats updates
"""

@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current market data for a symbol - FIXED
    Returns data adjusted to simulation's compressed timeline
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active simulation"
        )
    
    data_loader = HistoricalDataLoader()
    
    # Get OHLCV at current simulation time (compressed timeline)
    ohlcv = data_loader.get_ohlcv_at_time(
        simulation.crisis_type.value,
        symbol,
        simulation.current_historical_time
    )
    
    if not ohlcv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data not available for {symbol} at current simulation time"
        )
    
    current_price = data_loader.get_price_at_time(
        simulation.crisis_type.value,
        symbol,
        simulation.current_historical_time
    )
    
    return MarketDataResponse(
        symbol=symbol,
        current_price=current_price,
        open=ohlcv["open"],
        high=ohlcv["high"],
        low=ohlcv["low"],
        close=ohlcv["close"],
        volume=ohlcv["volume"],
        historical_time=simulation.current_historical_time,
        simulation_phase=simulation.current_phase
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current leaderboard - FIXED with P&L amounts
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active simulation"
        )
    
    leaderboard = db.query(SimulationLeaderboard).filter(
        SimulationLeaderboard.simulation_id == simulation.id
    ).order_by(SimulationLeaderboard.current_rank.asc()).limit(limit).all()
    
    total_participants = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id
    ).count()
    
    # Enhanced leaderboard with P&L
    entries = []
    for entry in leaderboard:
        participant = db.query(SimulationParticipant).filter(
            SimulationParticipant.simulation_id == simulation.id,
            SimulationParticipant.user_id == entry.user_id
        ).first()
        
        if participant:
            # Calculate absolute P&L
            profit_loss = participant.current_total_value - participant.initial_portfolio_value
            
            entries.append(LeaderboardEntry(
                rank=entry.current_rank,
                user_id=entry.user_id,
                total_value=entry.total_value,
                total_return_pct=entry.total_return_pct,
                profit_loss=round(profit_loss, 2),  # NEW: Absolute P&L
                sharpe_ratio=entry.sharpe_ratio,
                competition_score=entry.competition_score,
                initial_value=participant.initial_portfolio_value,  # NEW
                max_drawdown_pct=participant.max_drawdown_pct  # NEW
            ))
    
    return LeaderboardResponse(
        simulation_id=simulation.id,
        entries=entries,
        snapshot_at_historical=simulation.current_historical_time,
        total_participants=total_participants
    )




@router.get("/my-stats", response_model=ParticipantStatsResponse)
async def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed participant statistics with real-time portfolio calculation
    """
    # Fetch the active simulation
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active simulation"
        )
    
    # Fetch the participant
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in simulation"
        )
    
    # -------------------------------
    # Recalculate portfolio in real-time
    # -------------------------------
    data_loader = HistoricalDataLoader()
    order_processor = HistoricalOrderProcessor(data_loader, simulation.crisis_type.value)
    
    # Calculate total positions value
    total_positions_value = order_processor.calculate_portfolio_value(
        participant, simulation.current_historical_time, db
    )
    
    # Update participant values
    participant.current_portfolio_value = max(total_positions_value, 0.0)
    participant.current_total_value = participant.current_cash + participant.current_portfolio_value
    participant.profit_loss = participant.current_total_value - participant.initial_portfolio_value
    participant.total_return_pct = ((participant.current_total_value / participant.initial_portfolio_value) - 1) * 100
    
    # Update max drawdown if needed
    if participant.total_return_pct < participant.max_drawdown_pct:
        participant.max_drawdown_pct = participant.total_return_pct
    
    db.commit()
    db.refresh(participant)
    
    # Trading stats
    total_orders = db.query(func.count(SimulationOrder.id)).filter(
        SimulationOrder.participant_id == participant.id
    ).scalar() or 0
    
    filled_orders = db.query(func.count(SimulationOrder.id)).filter(
        SimulationOrder.participant_id == participant.id,
        SimulationOrder.status == "FILLED"
    ).scalar() or 0
    
    active_positions = db.query(func.count(SimulationPosition.id)).filter(
        SimulationPosition.participant_id == participant.id
    ).scalar() or 0
    
    # Get rank from leaderboard
    leaderboard_entry = db.query(SimulationLeaderboard).filter(
        SimulationLeaderboard.simulation_id == simulation.id,
        SimulationLeaderboard.user_id == current_user.id
    ).first()
    
    # Build response
    return ParticipantStatsResponse(
        participant_id=participant.id,
        user_id=current_user.id,
        initial_value=participant.initial_portfolio_value,
        current_cash=participant.current_cash,
        current_portfolio_value=participant.current_portfolio_value,
        current_total_value=participant.current_total_value,
        profit_loss=round(participant.profit_loss, 2),
        total_return_pct=participant.total_return_pct,
        max_drawdown_pct=participant.max_drawdown_pct,
        sharpe_ratio=participant.sharpe_ratio,
        total_trades=participant.total_trades,
        profitable_trades=participant.profitable_trades,
        total_orders=total_orders,
        filled_orders=filled_orders,
        active_positions=active_positions,
        current_rank=leaderboard_entry.current_rank if leaderboard_entry else None,
        max_leverage_used=participant.max_leverage_used,
        margin_calls_count=participant.margin_calls_count
    )

@router.get("/orders", response_model=List[OrderResponse])
async def get_my_orders(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get order history - FIXED
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active simulation"
        )
    
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in simulation"
        )
    
    query = db.query(SimulationOrder).filter(
        SimulationOrder.participant_id == participant.id
    )
    
    if status_filter:
        query = query.filter(SimulationOrder.status == status_filter.upper())
    
    orders = query.order_by(SimulationOrder.placed_at_real.desc()).limit(limit).all()
    
    return [OrderResponse(**order.__dict__) for order in orders]


@router.delete("/orders/{order_id}", response_model=SimulationControlResponse)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending order - FIXED
    """
    order = db.query(SimulationOrder).join(SimulationParticipant).filter(
        SimulationOrder.id == order_id,
        SimulationParticipant.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {order.status}"
        )
    
    order.status = "CANCELLED"
    order.rejection_reason = "Cancelled by user"
    db.commit()
    
    return SimulationControlResponse(
        success=True,
        message=f"Order {order_id} cancelled successfully",
        simulation_id=order.participant.simulation_id,
        new_status="cancelled"
    )


@router.get("/crisis/{crisis_type}/symbols", response_model=dict)
async def get_crisis_symbols(
    crisis_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed symbol information for a crisis - FIXED
    """
    try:
        # Validate crisis type
        try:
            crisis_enum = CrisisType(crisis_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid crisis type. Available: {[c.value for c in CrisisType]}"
            )
        
        data_loader = HistoricalDataLoader()
        
        symbols = data_loader.get_available_assets(crisis_type)
        start_date, end_date = data_loader.get_date_range(crisis_type)
        
        df = data_loader.load_crisis_data(crisis_type)
        
        symbol_details = []
        
        for symbol in symbols:
            try:
                prices = df[symbol].dropna()
                
                if len(prices) == 0:
                    continue
                
                returns = prices.pct_change().dropna()
                daily_volatility = returns.std()
                annualized_volatility = daily_volatility * (252 ** 0.5) * 100
                
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative / running_max - 1) * 100
                max_drawdown = drawdown.min()
                
                min_price = float(prices.min())
                max_price = float(prices.max())
                start_price = float(prices.iloc[0])
                end_price = float(prices.iloc[-1])
                
                total_return = ((end_price / start_price) - 1) * 100
                
                symbol_details.append({
                    "symbol": symbol,
                    "data_points": len(prices),
                    "price_statistics": {
                        "start_price": round(start_price, 2),
                        "end_price": round(end_price, 2),
                        "min_price": round(min_price, 2),
                        "max_price": round(max_price, 2),
                        "average_price": round(float(prices.mean()), 2)
                    },
                    "performance": {
                        "total_return_pct": round(total_return, 2),
                        "annualized_volatility_pct": round(annualized_volatility, 2),
                        "max_drawdown_pct": round(max_drawdown, 2)
                    }
                })
                
            except Exception as e:
                logger.warning(f"Error processing symbol {symbol}: {e}")
                continue
        
        symbol_details.sort(key=lambda x: x["symbol"])
        
        order_processor = HistoricalOrderProcessor(data_loader, crisis_type)
        constraints = order_processor.constraints
        
        for detail in symbol_details:
            detail["trading_info"] = {
                "can_short": constraints.get("short_selling_allowed", True),
                "margin_requirement": constraints.get("margin_requirement", 0.50),
                "commission_rate": constraints.get("commission_rate", 0.001),
                "min_tick_size": constraints.get("min_tick_size", 0.01)
            }
        
        return {
            "crisis_type": crisis_type,
            "crisis_name": crisis_type.replace("_", " ").title(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "duration_days": (end_date - start_date).days
            },
            "total_symbols": len(symbol_details),
            "symbols": symbol_details,
            "trading_constraints": {
                "short_selling_allowed": constraints.get("short_selling_allowed", True),
                "margin_requirement": constraints.get("margin_requirement", 0.50),
                "commission_rate": constraints.get("commission_rate", 0.001),
                "min_tick_size": constraints.get("min_tick_size", 0.01)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting symbols for {crisis_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading symbol data: {str(e)}"
        )

@router.get("/assets/{crisis_type}", response_model=AvailableAssetsResponse)
async def get_available_assets(
    crisis_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get available assets for a specific crisis type
    
    - Shows what can be traded in each crisis
    - Includes historical date range
    """
    data_loader = HistoricalDataLoader()
    
    try:
        assets = data_loader.get_available_assets(crisis_type)
        start_date, end_date = data_loader.get_date_range(crisis_type)
        
        return AvailableAssetsResponse(
            crisis_type=crisis_type,
            assets=assets,
            date_range_start=start_date,
            date_range_end=end_date
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )







@router.get("/participants", response_model=List[ParticipantResponse])
async def get_simulation_participants(
    simulation_id: Optional[int] = Query(None, description="Simulation ID (defaults to active)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all participants in a simulation
    
    - Shows all users participating
    - Includes their current performance
    """
    if simulation_id:
        simulation = db.query(CrisisSimulation).filter(
            CrisisSimulation.id == simulation_id
        ).first()
    else:
        simulation = db.query(CrisisSimulation).filter(
            CrisisSimulation.status.in_([SimulationStatus.ACTIVE, SimulationStatus.PENDING])
        ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    participants = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id
    ).order_by(SimulationParticipant.total_return_pct.desc()).all()
    
    return [ParticipantResponse(**p.__dict__) for p in participants]

@router.get("/positions", response_model=List[PositionResponse])
async def get_my_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current open positions with enhanced position type
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.status == SimulationStatus.ACTIVE
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active simulation"
        )
    
    participant = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id,
        SimulationParticipant.user_id == current_user.id,
        SimulationParticipant.is_active == True
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not participating in active simulation"
        )
    
    positions = db.query(SimulationPosition).filter(
        SimulationPosition.participant_id == participant.id
    ).all()
    
    # Get current prices for all positions
    data_loader = HistoricalDataLoader()
    response_positions = []
    
    for position in positions:
        # Get current price
        current_price = data_loader.get_price_at_time(
            simulation.crisis_type.value,
            position.symbol,
            simulation.current_historical_time
        )
        
        # Calculate market value
        market_value = position.quantity * current_price if current_price else None
        
        # Determine position type
        position_type = "LONG" if position.quantity > 0 else "SHORT"
        
        # Calculate unrealized P&L
        if current_price:
            if position.quantity > 0:  # Long
                unrealized_pnl = (current_price - position.average_cost) * position.quantity
            else:  # Short
                unrealized_pnl = (position.average_cost - current_price) * abs(position.quantity)
        else:
            unrealized_pnl = 0.0
        
        # Create response with all fields
        position_dict = position.__dict__.copy()
        position_dict["position_type"] = position_type
        position_dict["market_value"] = market_value
        position_dict["current_price"] = current_price
        position_dict["unrealized_pnl"] = unrealized_pnl
        
        # Remove SQLAlchemy internal attribute
        position_dict.pop('_sa_instance_state', None)
        
        response_positions.append(PositionResponse(**position_dict))
    
    return response_positions
# @router.get("/crisis-types", response_model=List[dict])
# async def get_available_crisis_types(
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get list of all available crisis types with metadata
    
#     - Shows all historical crises available for simulation
#     - Includes date ranges and asset counts
#     """
#     data_loader = HistoricalDataLoader()
#     crisis_info = []
    
#     for crisis_type in CrisisType:
#         try:
#             assets = data_loader.get_available_assets(crisis_type.value)
#             start_date, end_date = data_loader.get_date_range(crisis_type.value)
            
#             crisis_info.append({
#                 "type": crisis_type.value,
#                 "name": crisis_type.value.replace("_", " ").title(),
#                 "asset_count": len(assets),
#                 "date_range_start": start_date.isoformat(),
#                 "date_range_end": end_date.isoformat(),
#                 "duration_days": (end_date - start_date).days,
#                 "available": True
#             })
#         except Exception as e:
#             crisis_info.append({
#                 "type": crisis_type.value,
#                 "name": crisis_type.value.replace("_", " ").title(),
#                 "available": False,
#                 "error": str(e)
#             })
    
#     return crisis_info


@router.get("/simulation/{simulation_id}/timeline", response_model=List[dict])
async def get_simulation_timeline(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get timeline of major events during a simulation
    
    - Shows key moments and phase changes
    - Useful for replay and analysis
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    # Build timeline from phase config
    timeline = []
    
    if simulation.phase_config:
        for phase_name, phase_data in simulation.phase_config.items():
            timeline.append({
                "phase": phase_name,
                "historical_start": phase_data.get("historical_start"),
                "historical_end": phase_data.get("historical_end"),
                "real_duration_minutes": phase_data.get("real_duration_minutes"),
                "compression_ratio": phase_data.get("compression_ratio")
            })
    
    return timeline


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@router.get("/health", response_model=dict)
async def get_simulator_health(
    db: Session = Depends(get_db)
):
    """
    Get crisis simulator health status
    
    - Shows if simulator is operational
    - Number of active simulations
    - System metrics
    """
    try:
        active_count = db.query(func.count(CrisisSimulation.id)).filter(
            CrisisSimulation.status == SimulationStatus.ACTIVE
        ).scalar() or 0
        
        pending_count = db.query(func.count(CrisisSimulation.id)).filter(
            CrisisSimulation.status == SimulationStatus.PENDING
        ).scalar() or 0
        
        total_participants = db.query(func.count(SimulationParticipant.id)).filter(
            SimulationParticipant.is_active == True
        ).scalar() or 0
        
        return {
            "status": "healthy",
            "active_simulations": active_count,
            "pending_simulations": pending_count,
            "total_active_participants": total_participants,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }