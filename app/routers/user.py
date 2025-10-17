from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserUpdate, UserSettingsInfo
from app.schemas.auth import LoginRequest, ResetPasswordRequest, ResetPasswordLinkRequest
from app.services.user_service import UserService
from app.middleware.jwt_middleware import get_current_user
from app.config.database import get_db
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["users"])

@router.get("/settingsInfo", response_model=UserSettingsInfo)
async def get_user_settings_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User settings requested by: {current_user.email}")
    user_service = UserService(db)
    return user_service.get_user_settings_info(current_user.email)

@router.get("/fullName")
async def get_user_full_name(
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Full name requested by: {current_user.email}")
    return {"full_name": f"{current_user.first_name} {current_user.last_name}"}

@router.patch("/update")
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"User update requested by: {current_user.email}")
    user_service = UserService(db)
    return user_service.update_user(current_user.email, user_update)

@router.post("/reset-password-request")
async def request_password_reset(request: ResetPasswordLinkRequest, db: Session = Depends(get_db)):
    logger.info(f"Password reset requested for: {request.email}")
    user_service = UserService(db)
    success = user_service.send_reset_password_link(request.email)
    if success:
        return {"message": "If the email exists, a reset password link has been sent."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email"
        )

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password with token and new password"""
    logger.info("Password reset attempt")
    user_service = UserService(db)
    success = user_service.update_password(request.token, request.new_password)
    if success:
        return {"message": "Password updated successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password"
        )

@router.delete("", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Account deletion requested by: {current_user.email}")
    user_service = UserService(db)
    user_service.delete_account(current_user.email)
    return {"message": "Account deleted successfully"}

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information (for testing auth)"""
    logger.info(f"User info requested by: {current_user.email}")
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "level": current_user.level,
        "email_verified": current_user.email_verified
    }