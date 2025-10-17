from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Role-based access control
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    token_version = Column(Integer, default=0)
    
    # Gamification stats
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    quest_cash = Column(Float, default=10000.00)
    
    email_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # ✅ Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")  # <--- ADD THIS
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user")
    reset_password_tokens = relationship("ResetPasswordToken", back_populates="user")
    transactions = relationship("StockTransaction", back_populates="user")
    liked_news_articles = relationship("NewsArticle", secondary="article_likes", back_populates="liked_by")
    comments = relationship("NewsArticleComment", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    def has_liked_article(self, article):
        return article in self.liked_news_articles
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_moderator(self):
        return self.role == UserRole.MODERATOR or self.role == UserRole.ADMIN
