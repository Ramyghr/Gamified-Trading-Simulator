from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.middleware.role_middleware import require_admin
from app.services.user_service import UserService
from app.config.database import get_db
from app.models.user import User, UserRole
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

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