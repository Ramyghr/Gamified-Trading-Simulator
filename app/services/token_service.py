from sqlalchemy.orm import Session
from app.models.token import EmailVerificationToken, ResetPasswordToken
from app.models.user import User
from app.utils.email_util import EmailUtil
from datetime import datetime, timedelta
import secrets
import string
from app.constants.constants import EMAIL_TOKEN_EXPIRATION_MINUTES

class TokenService:
    def __init__(self, db: Session):
        self.db = db
        self.email_util = EmailUtil()

    def generate_token(self, length=20):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_email_verification_token(self, user: User):
        token = self.generate_token()
        expiry = datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRATION_MINUTES)

        # Invalidate any existing tokens
        self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id
        ).delete()

        verification_token = EmailVerificationToken(
            token=token,
            user_id=user.id,
            expiry_datetime=expiry
        )
        self.db.add(verification_token)
        self.db.commit()

        # Send verification email (frontend or API link)
        self.email_util.send_verification_email(user.email, token)

    def verify_email_token(self, token: str) -> User:
        verification_token = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token
        ).first()

        if not verification_token or verification_token.is_expired:
            return None

        user = verification_token.user
        # Delete token after use
        self.db.delete(verification_token)
        self.db.commit()
        return user

    def create_password_reset_token(self, user: User):
        token = self.generate_token()
        expiry = datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRATION_MINUTES)

        # Invalidate existing tokens
        self.db.query(ResetPasswordToken).filter(
            ResetPasswordToken.user_id == user.id
        ).delete()

        reset_token = ResetPasswordToken(
            token=token,
            user_id=user.id,
            expiry_datetime=expiry
        )
        self.db.add(reset_token)
        self.db.commit()

        # ✅ Send only token
        self.email_util.send_password_reset_email(user.email, token)


    def verify_password_reset_token(self, token: str) -> User:
        reset_token = self.db.query(ResetPasswordToken).filter(
            ResetPasswordToken.token == token
        ).first()

        if not reset_token or reset_token.is_expired:
            return None

        user = reset_token.user
        # Delete token after use
        self.db.delete(reset_token)
        self.db.commit()
        return user
    def delete_password_reset_token(self, token: str):
        reset_token = self.db.query(ResetPasswordToken).filter(
            ResetPasswordToken.token == token
        ).first()
        if reset_token:
            self.db.delete(reset_token)
            self.db.commit()