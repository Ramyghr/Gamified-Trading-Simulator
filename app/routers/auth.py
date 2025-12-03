from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.schemas.auth import LoginRequest, Token, JwtDto
from app.services.auth_service import AuthService , LogoutService
from app.config.database import get_db
from app.middleware.jwt_middleware import get_current_user
from app.constants.constants import VERIFY_EMAIL_PATH

from app.models.user import User
import logging
router = APIRouter(tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_new_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)
    
    # Check if user already exists
    if user_service.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = user_service.register_new_user(user_data)
    return {"message": "User registered successfully. Please check your email for verification."}

@router.get(VERIFY_EMAIL_PATH)
async def verify_user_email(token: str, db: Session = Depends(get_db)):
    user_service = UserService(db)
    try:
        user_service.verify_user(token)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value
        }
    }


@router.post("/check-jwt-expiry")
async def check_jwt_for_expiry(jwt_dto: JwtDto, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        is_valid = auth_service.validate_jwt(jwt_dto.jwt)
        return {"valid": is_valid}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by invalidating their JWT token
    """
    logout_service = LogoutService(db)
    try:
        result = await logout_service.logout_user(current_user)
        return {
            "message": "Logout successful",
            "user_id": current_user.id,
            "email": current_user.email
        }
    except Exception as e:
        logger.error(f"Logout failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/logout-all-devices")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user from all devices by incrementing token version
    """
    logout_service = LogoutService(db)
    try:
        result = await logout_service.logout_all_devices(current_user)
        return {
            "message": "Logged out from all devices",
            "user_id": current_user.id
        }
    except Exception as e:
        logger.error(f"Logout all devices failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all devices failed"
        )