from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.user import SecuritySettings, NotificationSettings, TradingPreferences

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ResetPasswordLinkRequest(BaseModel):
    email: EmailStr

class JwtDto(BaseModel):
    jwt: str

class AccountSettingsResponse(BaseModel):
    security: SecuritySettings
    notifications: NotificationSettings
    trading: TradingPreferences

class UpdateSecuritySettings(BaseModel):
    two_factor_enabled: Optional[bool] = None

class UpdateNotificationSettings(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    trade_alerts: Optional[bool] = None
    price_alerts: Optional[bool] = None
    news_alerts: Optional[bool] = None
    social_updates: Optional[bool] = None
    weekly_report: Optional[bool] = None

class UpdateTradingPreferences(BaseModel):
    default_order_type: Optional[str] = None
    confirm_orders: Optional[bool] = None
    auto_stop_loss: Optional[bool] = None
    stop_loss_percent: Optional[float] = None
    auto_take_profit: Optional[bool] = None
    take_profit_percent: Optional[float] = None
    risk_level: Optional[str] = None