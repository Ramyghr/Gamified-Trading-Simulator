from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.config.database import Base
from datetime import datetime
from app.constants.constants import EMAIL_TOKEN_EXPIRATION_MINUTES

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expiry_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="email_verification_tokens")
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expiry_datetime

class ResetPasswordToken(Base):
    __tablename__ = "reset_password_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expiry_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reset_password_tokens")
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expiry_datetime

class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, nullable=False, index=True)  # JWT token
    user_id = Column(Integer, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)  # Token expiration time
    created_at = Column(DateTime, default=func.now())
    reason = Column(String(255), nullable=True)  # Optional: reason for blacklisting

    def is_expired(self):
        return datetime.utcnow() > self.expires_at