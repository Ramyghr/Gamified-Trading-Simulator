from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict  # Make sure this matches your response

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ResetPasswordLinkRequest(BaseModel):
    email: EmailStr

class JwtDto(BaseModel):
    jwt: str