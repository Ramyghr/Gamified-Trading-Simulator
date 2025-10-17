from sqlalchemy.orm import Session
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.token import EmailVerificationToken, ResetPasswordToken
from app.schemas.user import UserCreate, UserUpdate
from app.utils.password_util import hash_password, verify_password
from app.services.token_service import TokenService
from app.utils.email_util import EmailUtil
from app.constants.constants import STARTING_CASH_BALANCE
from datetime import datetime
import logging
from fastapi import HTTPException, status
from fastapi import APIRouter, HTTPException, Depends
from app.config.database import get_db
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.token_service = TokenService(db)
        self.email_util = EmailUtil()

    def get_user_by_email(self, email: str) -> User:
        """Get user by email - case insensitive search"""
        try:
            logger.info(f"🔍 Database lookup for email: {email}")
            
            # Try exact match first
            user = self.db.query(User).filter(User.email == email).first()
            
            if user:
                logger.info(f"✅ User found with exact email match: {user.email}")
                return user
            
            # Try case-insensitive match if exact fails
            logger.info("🔄 Trying case-insensitive email lookup...")
            user = self.db.query(User).filter(User.email.ilike(email)).first()
            
            if user:
                logger.info(f"✅ User found with case-insensitive match: {user.email}")
                return user
            
            logger.error(f"❌ No user found for email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Database error in get_user_by_email: {str(e)}")
            return None

    def register_new_user(self, user_data: UserCreate) -> User:
        try:
            logger.info(f"Attempting to register user: {user_data.email}")
            
            # Check if user already exists
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user:
                logger.warning(f"User already exists: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash the password
            logger.info("Hashing password...")
            hashed_password = hash_password(user_data.password)
            logger.info("Password hashed successfully")
            
            # Create user
            user = User(
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                email=user_data.email,
                password_hash=hashed_password,
                display_name=user_data.display_name or f"{user_data.first_name} {user_data.last_name}",
                bio=user_data.bio,
                avatar_url=user_data.avatar_url,
                level=1,  # Starting as "Novice Trader"
                quest_cash=STARTING_CASH_BALANCE
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"User created with ID: {user.id}")
            
            # Create portfolio for user
            portfolio = Portfolio(
                user_id=user.id,
                cash_balance=STARTING_CASH_BALANCE,
                total_value=STARTING_CASH_BALANCE
            )
            self.db.add(portfolio)
            self.db.commit()
            logger.info("Portfolio created successfully")
            
            # Send verification email
            try:
                self.token_service.create_email_verification_token(user)
                logger.info("Verification email sent")
            except Exception as email_error:
                logger.error(f"Failed to send verification email: {email_error}")
                # Don't fail registration if email fails
            
            return user
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    def verify_user(self, token: str) -> bool:
        user = self.token_service.verify_email_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        user.email_verified = True
        user.verification_date = datetime.utcnow()
        self.db.commit()
        return True

    def send_reset_password_link(self, email: str) -> bool:
        user = self.get_user_by_email(email)
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True

        try:
            self.token_service.create_password_reset_token(user)
            logger.info(f"Password reset token created for user: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to create password reset token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )


    def update_password(self, token: str, new_password: str) -> bool:
        user = self.token_service.verify_password_reset_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        try:
            user.password_hash = hash_password(new_password)
            # Delete the token after successful password reset
            self.token_service.delete_password_reset_token(token)
            self.db.commit()
            logger.info(f"Password updated successfully for user: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to update password: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )   



    def get_user_settings_info(self, email: str) -> dict:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio
        }

    def update_user(self, email: str, user_update: UserUpdate) -> User:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_account(self, email: str) -> bool:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        self.db.delete(user)
        self.db.commit()
        return True

    def get_full_name(self, email: str) -> str:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return f"{user.first_name} {user.last_name}"
    def create_admin_user(self, email: str, password: str, first_name: str, last_name: str) -> User:
        """Create an admin user (for initial setup)"""
        from app.models.user import UserRole
        
        # Check if user already exists
        if self.get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            email_verified=True,  # Auto-verify admin users
            display_name=f"{first_name} {last_name}",
            level=1,
            quest_cash=10000.00
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Create portfolio for admin user
        from app.models.portfolio import Portfolio
        portfolio = Portfolio(
            user_id=user.id,
            cash_balance=10000.00,
            total_value=10000.00
        )
        self.db.add(portfolio)
        self.db.commit()
        
        return user
    

    def update_user_role(self, admin_email: str, target_email: str, new_role: str) -> User:
        """Update user role (admin only)"""
        from app.models.user import UserRole
        
        # Verify admin privileges
        admin_user = self.get_user_by_email(admin_email)
        if not admin_user or not admin_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        target_user = self.get_user_by_email(target_email)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate role
        try:
            user_role = UserRole(new_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role"
            )
        
        target_user.role = user_role
        self.db.commit()
        self.db.refresh(target_user)
        
        return target_user
