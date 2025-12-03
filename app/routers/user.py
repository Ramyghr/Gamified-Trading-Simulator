from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserUpdate, UserSettingsInfo
from app.schemas.auth import (
    LoginRequest, ResetPasswordRequest, ResetPasswordLinkRequest,
    UpdateSecuritySettings, UpdateNotificationSettings, UpdateTradingPreferences,
    SecuritySettings, NotificationSettings, TradingPreferences
)
from fastapi import File, UploadFile
import shutil
from pathlib import Path
import uuid
import os
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

@router.patch("/security-settings")
async def update_security_settings(
    settings: UpdateSecuritySettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Security settings update requested by: {current_user.email}")
    user_service = UserService(db)
    user = user_service.update_security_settings(current_user.email, settings)
    return {"message": "Security settings updated successfully"}

@router.patch("/notification-settings")
async def update_notification_settings(
    settings: UpdateNotificationSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Notification settings update requested by: {current_user.email}")
    user_service = UserService(db)
    user = user_service.update_notification_settings(current_user.email, settings)
    return {"message": "Notification settings updated successfully"}

@router.patch("/trading-preferences")
async def update_trading_preferences(
    preferences: UpdateTradingPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Trading preferences update requested by: {current_user.email}")
    user_service = UserService(db)
    user = user_service.update_trading_preferences(current_user.email, preferences)
    return {"message": "Trading preferences updated successfully"}

@router.get("/security-settings", response_model=SecuritySettings)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user_info = user_service.get_user_settings_info(current_user.email)
    return SecuritySettings(
        two_factor_enabled=user_info.two_factor_enabled,
        email_verified=user_info.email_verified,
        phone_verified=user_info.phone_verified,
        last_password_change=user_info.last_password_change,
        active_sessions=user_info.active_sessions
    )

@router.get("/notification-settings", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user_info = user_service.get_user_settings_info(current_user.email)
    return NotificationSettings(
        email_notifications=user_info.email_notifications,
        push_notifications=user_info.push_notifications,
        trade_alerts=user_info.trade_alerts,
        price_alerts=user_info.price_alerts,
        news_alerts=user_info.news_alerts,
        social_updates=user_info.social_updates,
        weekly_report=user_info.weekly_report
    )

@router.get("/trading-preferences", response_model=TradingPreferences)
async def get_trading_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user_info = user_service.get_user_settings_info(current_user.email)
    return TradingPreferences(
        default_order_type=user_info.default_order_type,
        confirm_orders=user_info.confirm_orders,
        auto_stop_loss=user_info.auto_stop_loss,
        stop_loss_percent=user_info.stop_loss_percent,
        auto_take_profit=user_info.auto_take_profit,
        take_profit_percent=user_info.take_profit_percent,
        risk_level=user_info.risk_level
    )

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

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    logger.info(f"User info requested by: {current_user.email}")
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "level": current_user.level,
        "email_verified": current_user.email_verified,
        "phone_verified": current_user.phone_verified,
        "two_factor_enabled": current_user.two_factor_enabled,
        "join_date": current_user.join_date,
        "location": current_user.location,
        "website": current_user.website,
        "bio": current_user.bio
    }
@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload user avatar image"""
    logger.info(f"Avatar upload requested by: {current_user.email}")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images allowed (JPEG, PNG, GIF, WebP)"
        )
    
    # Validate file size (max 5MB)
    contents = await file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB"
        )
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/avatars")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Update user's avatar URL in database
        avatar_url = f"/uploads/avatars/{unique_filename}"
        current_user.avatar_url = avatar_url
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"✅ Avatar uploaded successfully: {avatar_url}")
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url
        }
    
    except Exception as e:
        logger.error(f"❌ Error uploading avatar: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    logger.info(f"Password change requested by: {current_user.email}")
    
    user_service = UserService(db)
    auth_service = AuthService(db)
    
    # Verify old password
    if not auth_service.verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    try:
        from datetime import datetime
        current_user.password_hash = auth_service.hash_password(new_password)
        current_user.last_password_change = datetime.now()
        db.commit()
        
        logger.info(f"✅ Password changed successfully for: {current_user.email}")
        return {"message": "Password changed successfully"}
    
    except Exception as e:
        logger.error(f"❌ Error changing password: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.get("/export-data")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user data as JSON"""
    logger.info(f"Data export requested by: {current_user.email}")
    
    user_service = UserService(db)
    user_data = user_service.get_user_settings_info(current_user.email)
    
    # Create export data
    export = {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "bio": current_user.bio,
            "location": current_user.location,
            "website": current_user.website,
            "join_date": str(current_user.join_date),
            "level": current_user.level,
            "experience_points": current_user.experience_points
        },
        "settings": {
            "security": {
                "two_factor_enabled": user_data.two_factor_enabled,
                "email_verified": user_data.email_verified,
                "phone_verified": user_data.phone_verified
            },
            "notifications": {
                "email_notifications": user_data.email_notifications,
                "push_notifications": user_data.push_notifications,
                "trade_alerts": user_data.trade_alerts,
                "price_alerts": user_data.price_alerts,
                "news_alerts": user_data.news_alerts,
                "social_updates": user_data.social_updates,
                "weekly_report": user_data.weekly_report
            },
            "trading": {
                "default_order_type": user_data.default_order_type,
                "confirm_orders": user_data.confirm_orders,
                "auto_stop_loss": user_data.auto_stop_loss,
                "stop_loss_percent": user_data.stop_loss_percent,
                "auto_take_profit": user_data.auto_take_profit,
                "take_profit_percent": user_data.take_profit_percent,
                "risk_level": user_data.risk_level
            }
        }
    }
    
    return export

@router.delete("/delete-account")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently delete user account"""
    logger.warning(f"⚠️ Account deletion requested by: {current_user.email}")
    
    try:
        user_email = current_user.email
        
        # Delete user (cascade will handle related records)
        db.delete(current_user)
        db.commit()
        
        logger.info(f"✅ Account deleted successfully: {user_email}")
        return {"message": "Account deleted successfully"}
    
    except Exception as e:
        logger.error(f"❌ Error deleting account: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )