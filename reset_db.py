#!/usr/bin/env python3
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database FIRST
from app.config.database import engine, Base

# Then import ALL models to ensure they are registered
from app.models.user import User
from app.models.portfolio import Portfolio, Holding, PortfolioHistory
from app.models.token import EmailVerificationToken, ResetPasswordToken, BlacklistedToken
from app.models.stock import  NewsArticle, NewsArticleComment
from app.models.stock_transaction import StockTransaction
def reset_database():
    print("🗃️ Dropping all tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ Tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
    
    print("🗃️ Creating all tables in PostgreSQL...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("📊 Tables created:")
        for table in tables:
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_database()