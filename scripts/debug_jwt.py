#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jose import jwt
from app.config.settings import settings

def debug_token():
    # Your token from the error
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyYW15LmdoYXJiaUBlc3ByaXQudG4iLCJleHAiOjE3NjA5ODc3OTR9.NqQKeArClXwcE0TP9oe7Wvc8dOf77M0xFQ4bdGE65uo"
    
    print("🔍 Debugging JWT Token...")
    print(f"Token: {token}")
    print(f"Secret Key: {settings.SECRET_KEY}")
    print(f"Algorithm: {settings.ALGORITHM}")
    
    try:
        # Try to decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("✅ Token decoded successfully!")
        print(f"Payload: {payload}")
        
        # Check expiration
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            exp_date = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            print(f"Token expires: {exp_date}")
            print(f"Current time: {now}")
            print(f"Is expired: {now > exp_date}")
            
    except Exception as e:
        print(f"❌ Token decode failed: {e}")

if __name__ == "__main__":
    debug_token()