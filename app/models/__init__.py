# app/models/__init__.py

# Import all models here to avoid circular imports and ensure Alembic detects them.
# The order of imports matters to avoid unresolved foreign key relationships.

# 1. Import Base from base.py
from app.models.base import Base

# 2. Import all models from individual files
from app.models.user import User, UserRole, RiskLevel, Gender
from app.models.token import EmailVerificationToken, ResetPasswordToken, BlacklistedToken
from app.models.portfolio import (
    Portfolio,
    Holding,
    Position,
    PortfolioHistory,
    PortfolioDailySnapshot,
    PortfolioMetrics,
    LiquidationEvent,
    AssetType,
    PositionSide,
)
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.user_lesson_progress import UserLessonProgress
from app.models.user_xp import UserXP, XPTransaction
from app.models.lesson import Lesson, LessonQuizQuestion
from app.models.orders import Order, OrderType, OrderSide, OrderStatus, TimeInForce
from app.models.stock import (
    NewsArticle,
    NewsArticleComment,
    article_likes,
    NewsSource,
    OrderAction,
    OrderDuration,
    StockExchange,
)
from app.models.stock_transaction import StockTransaction, TransactionType
from app.models.crisis_simulator import (
    CrisisType,
    SimulationStatus,
    CrisisSimulation,
    SimulationParticipant,
    SimulationOrder,
    SimulationPosition,
    SimulationLeaderboard,
    SimulationSnapshot,
)
from app.models.bot import (
    Bot,
    BotStatus,
    BotStrategyType,
    TradeAction,
    BotTrade,
    BotBacktest,
    BotLog,
)
from app.models.candle import Candle
from app.models.market_data import MarketQuote
from app.models.market_subscription import MarketSubscription

# 3. Define __all__ to control what `from app.models import *` imports
__all__ = [
    # Base
    "Base",
    # User & Auth
    "User",
    "UserRole",
    "RiskLevel",
    "Gender",
    "EmailVerificationToken",
    "ResetPasswordToken",
    "BlacklistedToken",
    # Portfolio & Trading
    "Portfolio",
    "Holding",
    "Position",
    "PortfolioHistory",
    "PortfolioDailySnapshot",
    "PortfolioMetrics",
    "LiquidationEvent",
    "AssetType",
    "PositionSide",
    "Watchlist",
    "WatchlistItem",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TimeInForce",
    "StockTransaction",
    "TransactionType",
    # Lessons
    "Lesson",
    "LessonQuizQuestion",
    "UserLessonProgress",
    "UserXP",
    "XPTransaction",
    # Market Data
    "Candle",
    "MarketQuote",
    "MarketSubscription",
    # News & Stocks
    "NewsArticle",
    "NewsArticleComment",
    "article_likes",
    "NewsSource",
    "OrderAction",
    "OrderDuration",
    "StockExchange",
    # Crisis Simulator
    "CrisisType",
    "SimulationStatus",
    "CrisisSimulation",
    "SimulationParticipant",
    "SimulationOrder",
    "SimulationPosition",
    "SimulationLeaderboard",
    "SimulationSnapshot",
    # Trading Bots
    "Bot",
    "BotStatus",
    "BotStrategyType",
    "TradeAction",
    "BotTrade",
    "BotBacktest",
    "BotLog",
]