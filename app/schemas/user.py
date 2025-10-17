from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.constants.constants import PASSWORD_MIN_LENGTH

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters long')
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    level: int
    experience_points: int
    quest_cash: float
    email_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserSettingsInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]