from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config.settings import settings
from app.schemas.auth import TokenData
from fastapi import HTTPException, status
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.config.settings import settings
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def decode_access_token(token: str = Depends(oauth2_scheme)):
    """
    Decode and verify a JWT access token.
    Returns the decoded payload if valid.
    Raises HTTP 401 if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.info(f"JWT token created successfully")
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT encoding error: {e}")
        raise

def verify_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.info(f"🔄 Starting token verification...")
        
        # DECODE THE TOKEN
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract claims
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: str = payload.get("user_id")
        
        logger.info(f"📨 Token payload - email: {email}, role: {role}, user_id: {user_id}")
        
        if email is None:
            logger.error("❌ Token missing 'sub' claim")
            raise credentials_exception
            
        logger.info(f"✅ Token validated successfully for: {email}")
        return TokenData(email=email, role=role, user_id=user_id)
        
    except JWTError as e:
        logger.error(f"❌ JWT decode error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"❌ Unexpected error during token verification: {e}")
        raise credentials_exception