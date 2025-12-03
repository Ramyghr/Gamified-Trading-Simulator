from sqlalchemy.orm import Session
from app.models.user import User, RiskLevel, OrderType
from app.models.portfolio import Portfolio
from app.models.token import EmailVerificationToken, ResetPasswordToken
from app.schemas.user import UserCreate, UserUpdate, UserSettingsInfo
from app.utils.password_util import hash_password, verify_password
from app.services.token_service import TokenService
from app.utils.email_util import EmailUtil
from app.constants.constants import STARTING_CASH_BALANCE
from datetime import datetime
import logging
from fastapi import HTTPException, status
from app.schemas.auth import UpdateSecuritySettings, UpdateNotificationSettings, UpdateTradingPreferences
from app.models.user import Gender
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.token_service = TokenService(db)
        self.email_util = EmailUtil()

    def get_user_by_email(self, email: str) -> User:
        try:
            return (
                self.db.query(User)
                .filter(User.email == email)
                .first()
            )
        except Exception as e:
            logger.error(f"DB error in get_user_by_email: {e}")
            self.db.rollback()    # ← IMPORTANT
            return None


    def get_user_by_username(self, username: str) -> User:
        try:
            return (
                self.db.query(User)
                .filter(User.username == username)
                .first()
            )
        except Exception as e:
            logger.error(f"DB error in get_user_by_username: {e}")
            self.db.rollback()   # ALWAYS rollback on error
            return None

    
# n self.db.query(User).filter(User.username == username).first()

    def register_new_user(self, user_data: UserCreate) -> User:
        try:
            logger.info(f"Attempting to register user: {user_data.email}")

            existing_user = self.get_user_by_email(user_data.email.lower())
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            if user_data.phone:
                existing_user_with_phone = self.get_user_by_phone(user_data.phone)
                if existing_user_with_phone:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Phone number already registered"
                    )

            if user_data.username:
                existing_username = self.get_user_by_username(user_data.username)
                if existing_username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )

            hashed_password = hash_password(user_data.password)

            # Remove address from user creation
            user = User(
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                email=user_data.email.lower(),
                username=user_data.username or user_data.email.split('@')[0],
                password_hash=hashed_password,
                display_name=user_data.display_name or f"{user_data.first_name} {user_data.last_name}",
                bio=user_data.bio,
                avatar_url=user_data.avatar_url,
                location=user_data.location,
                # REMOVED: address=user_data.address,
                website=user_data.website,
                gender=Gender(user_data.gender),  # convert string to Enum
                date_of_birth=user_data.date_of_birth,
                phone=user_data.phone,
                country=user_data.country,
                id_document=user_data.id_document,
                signature=user_data.signature,
                email_notifications=user_data.email_notifications,
                push_notifications=user_data.push_notifications,
                trade_alerts=user_data.trade_alerts,
                price_alerts=user_data.price_alerts,
                news_alerts=user_data.news_alerts,
                social_updates=user_data.social_updates,
                weekly_report=user_data.weekly_report,
                default_order_type=user_data.default_order_type,
                confirm_orders=user_data.confirm_orders,
                auto_stop_loss=user_data.auto_stop_loss,
                stop_loss_percent=user_data.stop_loss_percent,
                auto_take_profit=user_data.auto_take_profit,
                take_profit_percent=user_data.take_profit_percent,
                risk_level=user_data.risk_level,
                level=1,
                quest_cash=STARTING_CASH_BALANCE,
                join_date=datetime.utcnow()
            )

            self.db.add(user)
            self.db.flush()

            portfolio = Portfolio(
                user_id=user.id,
                cash_balance=STARTING_CASH_BALANCE,
                total_value=STARTING_CASH_BALANCE
            )
            self.db.add(portfolio)

            self.db.commit()
            self.db.refresh(user)

            try:
                self.token_service.create_email_verification_token(user)
            except Exception:
                pass

            return user

        except HTTPException:
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
    def safe_query(self, query_fn):
        try:
            return query_fn()
        except Exception as e:
            logger.error(f"DB error: {e}")
            self.db.rollback()
            return None

    def safe_rollback(self):
        try:
            self.db.rollback()
        except Exception:
            pass

    def get_user_by_phone(self, phone: str) -> User:
        try:
            logger.info(f"🔍 Database lookup for phone: {phone}")
            return self.db.query(User).filter(User.phone == phone).first()

        except Exception as e:
            logger.error(f"❌ Database error in get_user_by_phone: {str(e)}")
            self.db.rollback()   # ← REQUIRED!!!
            return None


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
            user.last_password_change = datetime.utcnow()
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

    def get_user_settings_info(self, email: str) -> UserSettingsInfo:
        user = self.get_user_by_email(email.lower())
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserSettingsInfo(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            location=user.location,
            address=user.address,
            website=user.website,
            gender=user.gender,
            date_of_birth=user.date_of_birth,
            phone=user.phone,
            country=user.country,
            id_document=user.id_document,
            signature=user.signature,
            email_notifications=user.email_notifications,
            push_notifications=user.push_notifications,
            trade_alerts=user.trade_alerts,
            price_alerts=user.price_alerts,
            news_alerts=user.news_alerts,
            social_updates=user.social_updates,
            weekly_report=user.weekly_report,
            default_order_type=user.default_order_type,
            confirm_orders=user.confirm_orders,
            auto_stop_loss=user.auto_stop_loss,
            stop_loss_percent=user.stop_loss_percent,
            auto_take_profit=user.auto_take_profit,
            take_profit_percent=user.take_profit_percent,
            risk_level=user.risk_level,
            two_factor_enabled=user.two_factor_enabled,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            last_password_change=user.last_password_change,
            active_sessions=user.active_sessions
        )

    def update_user(self, email: str, user_update: UserUpdate) -> User:
        user = self.get_user_by_email(email.lower())
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_update.dict(exclude_unset=True)

        if 'username' in update_data and update_data['username'] != user.username:
            existing_user = self.get_user_by_username(update_data['username'])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    
    def update_security_settings(self, email: str, settings: UpdateSecuritySettings) -> User:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = settings.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_notification_settings(self, email: str, settings: UpdateNotificationSettings) -> User:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = settings.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_trading_preferences(self, email: str, preferences: UpdateTradingPreferences) -> User:
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = preferences.dict(exclude_unset=True)
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
