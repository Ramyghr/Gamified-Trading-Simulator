from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Create engine
engine = create_engine(settings.DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarative class
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Import all models **before creating tables**
from app.models.user import User
from app.models.portfolio import *
from app.models.token import EmailVerificationToken, ResetPasswordToken, BlacklistedToken
from app.models.stock import NewsArticle, NewsArticleComment
from app.models.stock_transaction import StockTransaction

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
