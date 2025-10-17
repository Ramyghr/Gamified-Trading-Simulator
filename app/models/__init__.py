# app/models/__init__.py - KEEP THIS VERSION

# Import all models here to avoid circular imports
from app.models.user import User
from app.models.portfolio import *
from app.models.token import EmailVerificationToken, ResetPasswordToken

# Import from stock.py (the comprehensive version)
from app.models.stock import (
     NewsArticle, NewsArticleComment, 
    OrderAction, OrderType, OrderDuration, StockExchange,
    article_likes
)

# Import orders if they exist
from app.models.orders import Order, OrderType, OrderSide, OrderStatus, TimeInForce
from app.models.stock_transaction import StockTransaction, TransactionType