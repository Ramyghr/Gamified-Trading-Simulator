from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.utils.jwt_util import create_access_token, verify_token
from app.utils.password_util import verify_password
from app.models.user import User, UserRole
from app.config.settings import settings
from fastapi import HTTPException, status
import logging
from app.models.token import BlacklistedToken
import jwt
from fastapi import Request

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        if not verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: Invalid password for {email}")
            return None
        logger.info(f"Authentication successful for {email}")
        return user

    def create_access_token(self, data: dict) -> str:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(data, expires_delta)

    def validate_jwt(self, token: str) -> bool:
        try:
            token_data = verify_token(token)
            if token_data and hasattr(token_data, 'email'):
                user = self.db.query(User).filter(User.email == token_data.email).first()
                return user is not None
            return False
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return False

    def login(self, email: str, password: str) -> dict:
        user = self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified"
            )
        
        # Create token with proper claims
        access_token = self.create_access_token(
            data={
                "sub": user.email,  # This is REQUIRED
                "role": user.role.value,
                "user_id": str(user.id)
            }
        )
        
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
class LogoutService:
    def __init__(self, db: Session):
        self.db = db

    async def logout_user(self, user: User, token: str = None) -> bool:
        """
        Logout user by blacklisting their current token
        """
        try:
            # If token is provided, blacklist it specifically
            if token:
                await self._blacklist_token(token, user.id)
            
            # Log the logout activity
            logger.info(f"User {user.email} logged out")
            
            # You can add additional cleanup here:
            # - Clear user session data if any
            # - Update user status
            # - Log security event
            
            return True
            
        except Exception as e:
            logger.error(f"Error during logout for user {user.email}: {e}")
            raise

    async def logout_all_devices(self, user: User) -> bool:
        """
        Logout from all devices by incrementing token version
        This invalidates all previously issued tokens
        """
        try:
            # Increment user's token version
            user.token_version = getattr(user, 'token_version', 0) + 1
            self.db.commit()
            
            logger.info(f"User {user.email} logged out from all devices, token version: {user.token_version}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during logout all devices for user {user.email}: {e}")
            raise

    async def _blacklist_token(self, token: str, user_id: int) -> None:
        """
        Add token to blacklist
        """
        try:
            # Decode token to get expiration
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp_timestamp = payload.get('exp')
            
            if exp_timestamp:
                expires_at = datetime.fromtimestamp(exp_timestamp)
                
                # Check if token is already blacklisted
                existing = self.db.query(BlacklistedToken).filter(
                    BlacklistedToken.token == token
                ).first()
                
                if not existing:
                    blacklisted_token = BlacklistedToken(
                        token=token,
                        user_id=user_id,
                        expires_at=expires_at
                    )
                    self.db.add(blacklisted_token)
                    self.db.commit()
                    logger.info(f"Token blacklisted for user_id: {user_id}")
                    
        except jwt.ExpiredSignatureError:
            logger.warning("Attempt to blacklist expired token")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token during blacklisting: {e}")
            raise

    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted
        """
        blacklisted = self.db.query(BlacklistedToken).filter(
            BlacklistedToken.token == token
        ).first()
        
        return blacklisted is not None

    async def clean_expired_blacklisted_tokens(self) -> None:
        """
        Clean up expired blacklisted tokens (run as periodic task)
        """
        try:
            expired_tokens = self.db.query(BlacklistedToken).filter(
                BlacklistedToken.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {expired_tokens} expired blacklisted tokens")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning expired blacklisted tokens: {e}")