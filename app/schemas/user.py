from pydantic import BaseModel, EmailStr, validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.constants.constants import PASSWORD_MIN_LENGTH
from enum import Enum



class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None


class RiskLevel(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

    # Notification Settings
    email_notifications: bool = True
    push_notifications: bool = True
    trade_alerts: bool = True
    price_alerts: bool = True
    news_alerts: bool = True
    social_updates: bool = True
    weekly_report: bool = True

    # Trading Preferences
    default_order_type: OrderType = OrderType.MARKET
    confirm_orders: bool = True
    auto_stop_loss: bool = False
    stop_loss_percent: float = 5.0
    auto_take_profit: bool = False
    take_profit_percent: float = 10.0
    risk_level: RiskLevel = RiskLevel.MODERATE

    @validator('password')
    def password_strength(cls, v):
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters long')
        return v

    @validator('stop_loss_percent')
    def validate_stop_loss(cls, v):
        if not 1 <= v <= 20:
            raise ValueError('Stop loss percentage must be between 1 and 20')
        return v

    @validator('take_profit_percent')
    def validate_take_profit(cls, v):
        if not 5 <= v <= 50:
            raise ValueError('Take profit percentage must be between 5 and 50')
        return v

    class Config:
        extra = "allow"  # ✅ This allows any additional fields from front-end JSON

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    # Notification Settings
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    trade_alerts: Optional[bool] = None
    price_alerts: Optional[bool] = None
    news_alerts: Optional[bool] = None
    social_updates: Optional[bool] = None
    weekly_report: Optional[bool] = None
    
    # Trading Preferences
    default_order_type: Optional[OrderType] = None
    confirm_orders: Optional[bool] = None
    auto_stop_loss: Optional[bool] = None
    stop_loss_percent: Optional[float] = None
    auto_take_profit: Optional[bool] = None
    take_profit_percent: Optional[float] = None
    risk_level: Optional[RiskLevel] = None

class UserResponse(UserBase):
    id: int
    username: str
    level: int
    experience_points: int
    quest_cash: float
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    join_date: datetime
    created_at: datetime
    
    # Notification Settings
    email_notifications: bool
    push_notifications: bool
    trade_alerts: bool
    price_alerts: bool
    news_alerts: bool
    social_updates: bool
    weekly_report: bool
    
    # Trading Preferences
    default_order_type: OrderType
    confirm_orders: bool
    auto_stop_loss: bool
    stop_loss_percent: float
    auto_take_profit: bool
    take_profit_percent: float
    risk_level: RiskLevel
    
    class Config:
        from_attributes = True

class UserSettingsInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    
    # Notification Settings
    email_notifications: bool
    push_notifications: bool
    trade_alerts: bool
    price_alerts: bool
    news_alerts: bool
    social_updates: bool
    weekly_report: bool
    
    # Trading Preferences
    default_order_type: OrderType
    confirm_orders: bool
    auto_stop_loss: bool
    stop_loss_percent: float
    auto_take_profit: bool
    take_profit_percent: float
    risk_level: RiskLevel
    
    # Security
    two_factor_enabled: bool
    email_verified: bool
    phone_verified: bool
    last_password_change: datetime
    active_sessions: int

class SecuritySettings(BaseModel):
    two_factor_enabled: bool
    email_verified: bool
    phone_verified: bool
    last_password_change: datetime
    active_sessions: int

class NotificationSettings(BaseModel):
    email_notifications: bool
    push_notifications: bool
    trade_alerts: bool
    price_alerts: bool
    news_alerts: bool
    social_updates: bool
    weekly_report: bool

class TradingPreferences(BaseModel):
    default_order_type: OrderType
    confirm_orders: bool
    auto_stop_loss: bool
    stop_loss_percent: float
    auto_take_profit: bool
    take_profit_percent: float
    risk_level: RiskLevel