#!/usr/bin/env python3
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.database import SessionLocal
from app.models.user import User

def debug_database():
    db = SessionLocal()
    try:
        print("🔍 Checking database users...")
        
        # Get all users
        users = db.query(User).all()
        
        print(f"📊 Total users in database: {len(users)}")
        
        for user in users:
            print(f"👤 User: {user.email} | ID: {user.id} | Verified: {user.email_verified}")
        
        # Check for your specific email
        target_email = "ramy.gharbi@esprit.tn"
        print(f"\n🔎 Looking for specific email: {target_email}")
        
        exact_user = db.query(User).filter(User.email == target_email).first()
        if exact_user:
            print(f"✅ Exact match found: {exact_user.email}")
        else:
            print("❌ No exact match found")
            
        # Check case insensitive
        case_user = db.query(User).filter(User.email.ilike(target_email)).first()
        if case_user:
            print(f"✅ Case-insensitive match found: {case_user.email}")
        else:
            print("❌ No case-insensitive match found")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_database()