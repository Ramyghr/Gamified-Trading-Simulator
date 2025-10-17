# scripts/init_db.py
from app.config.database import Base, engine

# Import all models so SQLAlchemy knows about them
from app.models.user import User
from app.models.portfolio import *
from app.models.token import EmailVerificationToken, ResetPasswordToken, BlacklistedToken
from app.models.stock import NewsArticle, NewsArticleComment
from app.models.stock_transaction import StockTransaction
from app.models.lesson import Lesson, LessonQuizQuestion
from app.models.user_xp import UserXP, XPTransaction
from app.models.watchlist import Watchlist
from app.models.orders import Order  # if you have it

# Create tables
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")
