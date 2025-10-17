# app/models/__init__.py - UPDATED

# Import all models here to avoid circular imports

# User-related models
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.token import EmailVerificationToken, ResetPasswordToken

# Watchlist
from app.models.watchlist import Watchlist

# Lesson and gamification
from app.models.lesson import Lesson
from app.models.user_lesson_progress import UserLessonProgress
from app.models.user_xp import UserXP
from app.models.user_xp import XPTransaction

# Stock-related models
from app.models.stock import (
    NewsArticle,
    NewsArticleComment,
    OrderAction,
    OrderType as StockOrderType,
    OrderDuration,
    StockExchange,
    article_likes
)

# Orders
from app.models.orders import Order, OrderType, OrderSide, OrderStatus, TimeInForce

# Transactions
from app.models.stock_transaction import StockTransaction, TransactionType
