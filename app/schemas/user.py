from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from app.constants.constants import PASSWORD_MIN_LENGTH


# -----------------------------
# ENUMS
# -----------------------------

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"

class RiskLevel(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


# -----------------------------
# BASE USER (shared fields)
# -----------------------------

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None  
    website: Optional[str] = None
    
    # Personal info
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    id_document: Optional[str] = None
    signature: Optional[str] = None


# -----------------------------
# USER CREATE
# -----------------------------

class UserCreate(UserBase):
    password: str

    # Notification settings
    email_notifications: bool = True
    push_notifications: bool = True
    trade_alerts: bool = True
    price_alerts: bool = True
    news_alerts: bool = True
    social_updates: bool = True
    weekly_report: bool = True

    # Trading preferences
    default_order_type: OrderType = OrderType.MARKET
    confirm_orders: bool = True
    auto_stop_loss: bool = False
    stop_loss_percent: float = 5.0
    auto_take_profit: bool = False
    take_profit_percent: float = 10.0
    risk_level: RiskLevel = RiskLevel.MODERATE

    # -----------------------------
    # VALIDATORS
    # -----------------------------

    @validator('password')
    def validate_password(cls, v):
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
            )
        return v

    @validator('date_of_birth', pre=True)
    def validate_dob(cls, v):
        if not v:
            return v

        try:
            if isinstance(v, str):
                v = v.strip()
                # Try dd/mm/yyyy
                try:
                    dob = datetime.strptime(v, "%d/%m/%Y").date()
                except:
                    # Try yyyy-mm-dd
                    try:
                        dob = datetime.strptime(v, "%Y-%m-%d").date()
                    except:
                        # Try dd-mm-yyyy
                        dob = datetime.strptime(v, "%d-%m-%Y").date()
            else:
                dob = v

            if dob > datetime.now().date():
                raise ValueError("Date of birth cannot be in the future")

            age = datetime.now().year - dob.year
            if age < 18:
                raise ValueError("User must be at least 18 years old")

            return dob

        except Exception as e:
            raise ValueError(f"Invalid date format. Expected dd/mm/yyyy. Error: {e}")

    # @validator('phone', pre=True)
    # def validate_phone(cls, v):
    #     if v:
    #         digits = ''.join(filter(str.isdigit, v))
    #         if len(digits) < 10:
    #             raise ValueError("Phone number must have at least 10 digits")
    #     return v

    @validator('stop_loss_percent')
    def validate_stop_loss(cls, v):
        if not 1 <= v <= 20:
            raise ValueError("Stop loss must be 1–20%")
        return v

    @validator('take_profit_percent')
    def validate_take_profit(cls, v):
        if not 5 <= v <= 50:
            raise ValueError("Take profit must be 5–50%")
        return v


# -----------------------------
# USER UPDATE
# -----------------------------

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None

    # Personal info
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    id_document: Optional[str] = None
    signature: Optional[str] = None

    # Notifications
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    trade_alerts: Optional[bool] = None
    price_alerts: Optional[bool] = None
    news_alerts: Optional[bool] = None
    social_updates: Optional[bool] = None
    weekly_report: Optional[bool] = None

    # Trading
    default_order_type: Optional[OrderType] = None
    confirm_orders: Optional[bool] = None
    auto_stop_loss: Optional[bool] = None
    stop_loss_percent: Optional[float] = None
    auto_take_profit: Optional[bool] = None
    take_profit_percent: Optional[float] = None
    risk_level: Optional[RiskLevel] = None

    @validator('date_of_birth', pre=True)
    def validate_dob_update(cls, v):
        if not v:
            return v

        try:
            v = v.strip()
            try:
                return datetime.strptime(v, "%d/%m/%Y").date()
            except:
                try:
                    return datetime.strptime(v, "%Y-%m-%d").date()
                except:
                    return datetime.strptime(v, "%d-%m-%Y").date()
        except Exception:
            raise ValueError("Invalid date format for date_of_birth")

    @validator('phone', pre=True)
    def validate_phone_update(cls, v):
        if v:
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 10:
                raise ValueError("Phone number must have at least 10 digits")
        return v


# -----------------------------
# USER RESPONSE
# -----------------------------

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

    # Notifications
    email_notifications: bool
    push_notifications: bool
    trade_alerts: bool
    price_alerts: bool
    news_alerts: bool
    social_updates: bool
    weekly_report: bool

    # Trading
    default_order_type: OrderType
    confirm_orders: bool
    auto_stop_loss: bool
    stop_loss_percent: float
    auto_take_profit: bool
    take_profit_percent: float
    risk_level: RiskLevel

    class Config:
        from_attributes = True


# -----------------------------
# SETTINGS & PUBLIC PROFILE
# -----------------------------

class UserSettingsInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    address: Optional[str]
    website: Optional[str]

    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    id_document: Optional[str] = None
    signature: Optional[str] = None

    email_notifications: bool
    push_notifications: bool
    trade_alerts: bool
    price_alerts: bool
    news_alerts: bool
    social_updates: bool
    weekly_report: bool

    default_order_type: OrderType
    confirm_orders: bool
    auto_stop_loss: bool
    stop_loss_percent: float
    auto_take_profit: bool
    take_profit_percent: float
    risk_level: RiskLevel

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


class PublicUserProfile(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    country: Optional[str]
    level: int
    join_date: datetime

    class Config:
        from_attributes = True
