from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.config.database import get_db
from app.constants.constants import VERIFY_EMAIL_PATH

router = APIRouter(tags=["registration"])

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