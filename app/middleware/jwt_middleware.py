import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.utils.jwt_util import verify_token
from app.services.user_service import UserService
from app.config.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract the JWT token from the Authorization header, verify it,
    and return the current authenticated user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token from header
        token = credentials.credentials
        logger.info("🔐 Extracting token from Authorization header")

        # Verify the token
        logger.info("🔄 Verifying JWT token...")
        token_data = verify_token(token)  # should return payload with 'email' or 'sub'
        logger.info(f"✅ Token verified for: {token_data}")

        # Get user by email or id
        user_service = UserService(db)
        user = user_service.get_user_by_email(token_data.email)

        if user is None:
            logger.error(f"❌ User not found in database: {token_data.email}")
            raise credentials_exception

        # Optionally check email verification
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email first",
            )

        logger.info(f"✅ Authenticated user: {user.email} (ID: {user.id})")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_current_user: {str(e)}", exc_info=True)
        raise credentials_exception
