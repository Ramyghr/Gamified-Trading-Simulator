from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    Enum as SQLEnum, JSON, Date
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum
from datetime import datetime


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class RiskLevel(enum.Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


class Gender(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class User(Base):
    __tablename__ = "users"

    # Basic identity
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)

    # Old + new location fields
    location = Column(String(200), nullable=True)  # legacy
    address = Column(String(500), nullable=True)  # new

    # Personal information
    gender = Column(SQLEnum(Gender), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    id_document = Column(Text, nullable=True)
    signature = Column(Text, nullable=True)

    # Role & security
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    token_version = Column(Integer, default=0)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, default=func.now())
    active_sessions = Column(Integer, default=0)

    # Gamification
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    quest_cash = Column(Float, default=10000.0)

    # Notifications
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    trade_alerts = Column(Boolean, default=True)
    price_alerts = Column(Boolean, default=True)
    news_alerts = Column(Boolean, default=True)
    social_updates = Column(Boolean, default=True)
    weekly_report = Column(Boolean, default=True)

    # Trading preferences
    default_order_type = Column(SQLEnum(OrderType), default=OrderType.MARKET)
    confirm_orders = Column(Boolean, default=True)
    auto_stop_loss = Column(Boolean, default=False)
    stop_loss_percent = Column(Float, default=5.0)
    auto_take_profit = Column(Boolean, default=False)
    take_profit_percent = Column(Float, default=10.0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MODERATE)

    # Integrations
    connected_accounts = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    join_date = Column(DateTime, default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship(
        "EmailVerificationToken", back_populates="user"
    )
    reset_password_tokens = relationship(
        "ResetPasswordToken", back_populates="user"
    )
    transactions = relationship("StockTransaction", back_populates="user")
    liked_news_articles = relationship(
        "NewsArticle", secondary="article_likes", back_populates="liked_by"
    )
    chat_conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    bots = relationship("Bot", back_populates="user", cascade="all, delete-orphan")
    bot_trades = relationship("BotTrade", back_populates="user", cascade="all, delete-orphan")
    bot_backtests = relationship("BotBacktest", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("NewsArticleComment", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

    # Utility methods
    def has_liked_article(self, article):
        return article in self.liked_news_articles

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_member_since(self):
        years = datetime.now().year - self.join_date.year
        return f"{years} year{'s' if years > 1 else ''}" if years > 0 else "Less than a year"
