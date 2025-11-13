from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from sqlalchemy.ext.declarative import declarative_base

# Base declarative class
Base = declarative_base()

# Import all models so Base.metadata knows them
from app.models.candle import *
from app.models.lesson import *
from app.models.market_data import * 
from app.models.market_subscription import * 
from app.models.orders import * 
from app.models.portfolio import * 
from app.models.stock import * 
from app.models.stock_transaction import * 
from app.models.token import * 
from app.models.user import * 
from app.models.user_lesson_progress import * 
from app.models.user_xp import * 
from app.models.watchlist import * 
 
# Create engine
engine = create_engine(settings.DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
