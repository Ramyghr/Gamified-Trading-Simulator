from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from sqlalchemy.orm import Session
from app.middleware.role_middleware import require_admin
from app.services.user_service import UserService
from app.config.database import get_db
from datetime import datetime
from sqlalchemy import func, desc
from app.models.user import User, UserRole
from typing import List, Optional
from app.models.user import User
from app.middleware.jwt_middleware import get_current_user
from app.services.xp_service import XPService
from app.models.user_xp import UserXP
import logging
from app.schemas.lesson import (
    LessonCreate, LessonUpdate, LessonResponse, LessonListResponse,
    LessonWithProgress, LessonProgressResponse, LessonCompleteRequest,
    QuizCompleteRequest, SimulationCompleteRequest, LessonCompleteResponse,
    VideoProgressUpdate, XPStatusResponse, XPTransactionResponse,
    QuizQuestionCreate, QuizQuestionResponse, QuizQuestionPublic
)
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
from app.crisis_simulator.engine import SimulationEngine
from app.crisis_simulator.data_loader import HistoricalDataLoader
from app.crisis_simulator.historical_order_processor import HistoricalOrderProcessor

from app.services.lesson_service import LessonService
from app.services.xp_service import XPService
from app.services.xp_service import XPService
from app.models.user_xp import UserXP
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# ============================================================================
# ADMIN ENDPOINTS - Simulation Management
# ============================================================================

@router.post("/simulations", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    crisis_type: CrisisType = Form(..., description="Type of crisis simulation"),
    max_participants: int = Form(..., description="Maximum number of participants"),
    is_competitive: bool = Form(False, description="Whether the simulation is competitive"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Create a new crisis simulation
    
    - Creates a new simulation instance
    - Participants can join before it starts
    - Only one simulation can be active at a time
    """
    # Check if there's already an active or pending simulation
    active_sim = db.query(CrisisSimulation).filter(
        CrisisSimulation.status.in_([SimulationStatus.ACTIVE, SimulationStatus.PENDING])
    ).first()
    
    if active_sim:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Simulation {active_sim.id} is already {active_sim.status.value}. Please stop it first."
        )
    
    engine = SimulationEngine(db)
    simulation = await engine.create_simulation(
        crisis_type=crisis_type,
        created_by=current_user.id,
        max_participants=max_participants,
        is_competitive=is_competitive
    )
    
    participant_count = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation.id
    ).count()
    
    return SimulationResponse(
        **simulation.__dict__,
        participant_count=participant_count,
        progress_percentage=0.0
    )


@router.post("/simulations/{simulation_id}/start", response_model=SimulationControlResponse)
async def start_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Start a pending simulation
    
    - Begins the simulation clock
    - No more participants can join after start
    - Simulation runs for its configured duration
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
            detail=f"Cannot start simulation in {simulation.status.value} state"
        )
    
    # Check if there are participants
    participant_count = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation_id
    ).count()
    
    if participant_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start simulation with no participants"
        )
    
    engine = SimulationEngine(db)
    
    try:
        success = await engine.start_simulation(simulation_id)
        
        db.refresh(simulation)
        
        return SimulationControlResponse(
            success=success,
            message=f"Simulation {simulation_id} started successfully with {participant_count} participants",
            simulation_id=simulation_id,
            new_status=simulation.status.value
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/simulations/{simulation_id}/stop", response_model=SimulationControlResponse)
async def stop_simulation(
    simulation_id: int,
    force: bool = Query(False, description="Force stop even if simulation is not active"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Stop a running simulation immediately
    
    - Ends the simulation and finalizes results
    - Calculates final rankings and scores
    - Cannot be restarted once stopped
    - Use force=true to stop paused simulations
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    valid_statuses = [SimulationStatus.ACTIVE]
    if force:
        valid_statuses.append(SimulationStatus.PAUSED)
    
    if simulation.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop simulation in {simulation.status.value} state"
        )
    
    try:
        # Mark simulation as completed
        simulation.status = SimulationStatus.COMPLETED
        simulation.completed_at = datetime.utcnow()
        simulation.real_end_time = datetime.utcnow()
        
        # Finalize all participant states
        participants = db.query(SimulationParticipant).filter(
            SimulationParticipant.simulation_id == simulation_id,
            SimulationParticipant.is_active == True
        ).all()
        
        engine = SimulationEngine(db)
        
        # Final portfolio value calculation
        for participant in participants:
            if simulation_id in engine.active_simulations:
                order_processor = engine.active_simulations[simulation_id]["order_processor"]
                total_value = order_processor.calculate_portfolio_value(
                    participant, simulation.current_historical_time, db
                )
                
                participant.current_total_value = total_value
                participant.total_return_pct = (
                    (total_value / participant.initial_portfolio_value - 1) * 100
                )
            
            participant.is_active = False
            participant.finished_at = datetime.utcnow()
        
        # Final leaderboard update
        await engine._update_leaderboard(simulation_id)
        
        # Remove from active simulations
        if simulation_id in engine.active_simulations:
            del engine.active_simulations[simulation_id]
        
        db.commit()
        
        participant_count = len(participants)
        
        return SimulationControlResponse(
            success=True,
            message=f"Simulation {simulation_id} stopped successfully. {participant_count} participants finalized.",
            simulation_id=simulation_id,
            new_status=simulation.status.value
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping simulation: {str(e)}"
        )


@router.post("/simulations/{simulation_id}/pause", response_model=SimulationControlResponse)
async def pause_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Pause an active simulation
    
    - Temporarily halts time progression
    - Participants cannot trade while paused
    - Can be resumed later
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.status != SimulationStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause simulation in {simulation.status.value} state"
        )
    
    engine = SimulationEngine(db)
    success = await engine.pause_simulation(simulation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to pause simulation"
        )
    
    return SimulationControlResponse(
        success=True,
        message="Simulation paused successfully",
        simulation_id=simulation_id,
        new_status="paused"
    )


@router.post("/simulations/{simulation_id}/resume", response_model=SimulationControlResponse)
async def resume_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Resume a paused simulation
    
    - Continues time progression from where it was paused
    - Participants can trade again
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.status != SimulationStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume simulation in {simulation.status.value} state"
        )
    
    engine = SimulationEngine(db)
    success = await engine.resume_simulation(simulation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resume simulation"
        )
    
    return SimulationControlResponse(
        success=True,
        message="Simulation resumed successfully",
        simulation_id=simulation_id,
        new_status="active"
    )


@router.delete("/simulations/{simulation_id}", response_model=SimulationControlResponse)
async def delete_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Delete a simulation and all its data
    
    - Permanently removes simulation and all associated data
    - Can only delete pending or completed simulations
    - Active simulations must be stopped first
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    if simulation.status in [SimulationStatus.ACTIVE, SimulationStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active or paused simulation. Stop it first."
        )
    
    try:
        # Cascade delete will handle participants, orders, positions, leaderboard
        db.delete(simulation)
        db.commit()
        
        return SimulationControlResponse(
            success=True,
            message=f"Simulation {simulation_id} deleted successfully",
            simulation_id=simulation_id,
            new_status="deleted"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting simulation: {str(e)}"
        )


@router.get("/simulations/history", response_model=List[SimulationHistoryResponse])
async def get_simulation_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status"),
    crisis_type: Optional[str] = Query(None, description="Filter by crisis type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Get history of all simulations
    
    - Shows all past, current, and pending simulations
    - Includes participant counts and completion stats
    - Supports filtering and pagination
    """
    query = db.query(CrisisSimulation)
    
    if status:
        try:
            query = query.filter(CrisisSimulation.status == SimulationStatus(status))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    if crisis_type:
        try:
            query = query.filter(CrisisSimulation.crisis_type == CrisisType(crisis_type))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid crisis type: {crisis_type}"
            )
    
    simulations = query.order_by(desc(CrisisSimulation.created_at)).offset(offset).limit(limit).all()
    
    result = []
    for sim in simulations:
        participant_count = db.query(SimulationParticipant).filter(
            SimulationParticipant.simulation_id == sim.id
        ).count()
        
        result.append(SimulationHistoryResponse(
            **sim.__dict__,
            participant_count=participant_count
        ))
    
    return result


@router.get("/simulations/{simulation_id}/stats", response_model=SimulationStatsResponse)
async def get_simulation_stats(
    simulation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Get detailed statistics for a simulation
    
    - Overall performance metrics
    - Participant statistics
    - Trading activity breakdown
    """
    simulation = db.query(CrisisSimulation).filter(
        CrisisSimulation.id == simulation_id
    ).first()
    
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found"
        )
    
    # Get aggregate stats
    participants = db.query(SimulationParticipant).filter(
        SimulationParticipant.simulation_id == simulation_id
    ).all()
    
    total_participants = len(participants)
    active_participants = sum(1 for p in participants if p.is_active)
    
    total_trades = db.query(func.count(SimulationOrder.id)).join(
        SimulationParticipant
    ).filter(
        SimulationParticipant.simulation_id == simulation_id,
        SimulationOrder.status == "FILLED"
    ).scalar() or 0
    
    avg_return = db.query(func.avg(SimulationParticipant.total_return_pct)).filter(
        SimulationParticipant.simulation_id == simulation_id
    ).scalar() or 0.0
    
    max_return = db.query(func.max(SimulationParticipant.total_return_pct)).filter(
        SimulationParticipant.simulation_id == simulation_id
    ).scalar() or 0.0
    
    min_return = db.query(func.min(SimulationParticipant.total_return_pct)).filter(
        SimulationParticipant.simulation_id == simulation_id
    ).scalar() or 0.0
    
    return SimulationStatsResponse(
        simulation_id=simulation_id,
        crisis_type=simulation.crisis_type.value,
        status=simulation.status.value,
        total_participants=total_participants,
        active_participants=active_participants,
        total_trades=total_trades,
        average_return_pct=float(avg_return),
        max_return_pct=float(max_return),
        min_return_pct=float(min_return),
        duration_minutes=simulation.duration_minutes,
        elapsed_minutes=(datetime.utcnow() - simulation.real_start_time).total_seconds() / 60 if simulation.real_start_time else 0
    )

#===================Admin user management
@router.get("/users")
async def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: Get all users"""
    logger.info(f"Admin users list requested by: {current_user.email}")
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "email_verified": user.email_verified,
            "level": user.level,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]

@router.patch("/users/{user_email}/role")
async def update_user_role(
    user_email: str,
    new_role: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: Update user role"""
    logger.info(f"Role update requested by {current_user.email} for {user_email} to {new_role}")
    user_service = UserService(db)
    return user_service.update_user_role(current_user.email, user_email, new_role)

@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: Get system statistics"""
    logger.info(f"Admin stats requested by: {current_user.email}")
    
    total_users = db.query(User).count()
    verified_users = db.query(User).filter(User.email_verified == True).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    regular_users = db.query(User).filter(User.role == UserRole.USER).count()
    
    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "admin_users": admin_users,
        "regular_users": regular_users,
        "pending_verification": total_users - verified_users
    }

@router.get("/test")
async def admin_test_endpoint(
    current_user: User = Depends(require_admin)
):
    """Test endpoint for admin access"""
    logger.info(f"Admin test endpoint accessed by: {current_user.email}")
    return {
        "message": "Admin access confirmed!",
        "user": current_user.email,
        "role": current_user.role.value
    }
@router.delete("", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Account deletion requested by: {current_user.email}")
    user_service = UserService(db)
    user_service.delete_account(current_user.email)
    return {"message": "Account deleted successfully"}
#======================Admine Lessons
@router.post("/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lesson (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    lesson = LessonService.create_lesson(db, lesson_data)
    return lesson

@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a lesson (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    lesson = LessonService.update_lesson(db, lesson_id, lesson_data)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a lesson (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = LessonService.delete_lesson(db, lesson_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return None
@router.post("/recalculate-levels")
async def recalculate_all_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recalculate XP levels for all users based on their total XP.
    This fixes users who are stuck due to the old XP calculation bug.
    (Admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(UserXP).all()
    updated = []
    
    for user_xp in users:
        old_level = user_xp.level
        old_current = user_xp.current_level_xp
        old_next = user_xp.next_level_xp
        
        # Recalculate from total XP using the corrected formula
        new_level, current_level_xp, next_level_xp = XPService.calculate_level_from_xp(user_xp.total_xp)
        
        # Update if changed
        if new_level != old_level or current_level_xp != old_current or next_level_xp != old_next:
            user_xp.level = new_level
            user_xp.current_level_xp = current_level_xp
            user_xp.next_level_xp = next_level_xp
            
            updated.append({
                "user_id": user_xp.user_id,
                "old_level": old_level,
                "new_level": new_level,
                "total_xp": user_xp.total_xp,
                "old_progress": f"{old_current}/{old_next}",
                "new_progress": f"{current_level_xp}/{next_level_xp}"
            })
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Recalculated levels for {len(updated)} users",
        "updated_users": updated,
        "total_users": len(users)
    }
