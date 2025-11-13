from fastapi import Depends, HTTPException, status
from app.middleware.jwt_middleware import get_current_user
from app.models.user import User, UserRole
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Ensure user is active and verified"""
    if not current_user.email_verified:
        logger.warning(f"Access denied for unverified user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email to access this resource"
        )
    return current_user

async def require_admin(current_user: User = Depends(get_current_active_user)):
    """Require admin privileges"""
    logger.info(f"Admin check for user: {current_user.email}, role: {current_user.role.value}")
    
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Admin access denied for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    logger.info(f"Admin access granted for: {current_user.email}")
    return current_user

async def require_user(current_user: User = Depends(get_current_active_user)):
    """Require basic user privileges (any authenticated user)"""
    return current_user

async def get_optional_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    Optional user dependency - returns user if authenticated, None if not
    Perfect for public endpoints with optional enhanced features
    """
    return current_user