from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.middleware.role_middleware import require_admin
from app.services.user_service import UserService
from app.config.database import get_db
from app.models.user import User, UserRole
from typing import List
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
from app.services.lesson_service import LessonService
from app.services.xp_service import XPService
from app.services.xp_service import XPService
from app.models.user_xp import UserXP
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
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
