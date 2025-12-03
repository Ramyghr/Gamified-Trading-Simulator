#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Checking model imports...")

try:
    from app.models.user import User
    print("✅ User model imported successfully")
except Exception as e:
    print(f"❌ User model import failed: {e}")

try:
    from app.models.portfolio import Portfolio
    print("✅ Portfolio model imported successfully")
except Exception as e:
    print(f"❌ Portfolio model import failed: {e}")

try:
    from app.models.stock import StockTransaction
    print("✅ Stock model imported successfully")
except Exception as e:
    print(f"❌ Stock model import failed: {e}")

try:
    from app.models.token import EmailVerificationToken
    print("✅ Token model imported successfully")
except Exception as e:
    print(f"❌ Token model import failed: {e}")

# Check if Base has tables registered
try:
    from app.config.database import Base
    print(f"📊 Tables registered with Base: {list(Base.metadata.tables.keys())}")
except Exception as e:
    print(f"❌ Base metadata check failed: {e}")