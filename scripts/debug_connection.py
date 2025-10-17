#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.database import engine
from app.config.settings import settings

def debug_connection():
    print(f"🔗 Database URL: {settings.DATABASE_URL}")
    
    try:
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            
        # Check if we can execute a query
        with engine.connect() as conn:
            result = conn.execute("SELECT current_database();")
            db_name = result.scalar()
            print(f"📊 Connected to database: {db_name}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    debug_connection()