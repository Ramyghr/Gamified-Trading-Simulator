#!/usr/bin/env python3
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_newsapi():
    """Test NewsAPI connection"""
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        print("❌ NEWS_API_KEY not found in .env")
        return
        
    try:
        async with httpx.AsyncClient() as client:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'stocks',
                'apiKey': api_key,
                'pageSize': 1
            }
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ NewsAPI: Connected successfully!")
                print(f"   Articles available: {data.get('totalResults', 0)}")
            else:
                print(f"❌ NewsAPI: Error {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ NewsAPI: Connection failed - {e}")

async def test_marketaux():
    """Test MarketAux connection"""
    api_key = os.getenv('MARKETAUX_API_KEY')
    if not api_key:
        print("❌ MARKETAUX_API_KEY not found in .env")
        return
        
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.marketaux.com/v1/news/all"
            params = {
                'api_token': api_key,
                'limit': 1
            }
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ MarketAux: Connected successfully!")
                print(f"   Articles returned: {len(data.get('data', []))}")
            else:
                print(f"❌ MarketAux: Error {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ MarketAux: Connection failed - {e}")

async def main():
    print("🔗 Testing News API Connections...")
    print("=" * 50)
    
    await test_newsapi()
    await test_marketaux()
    
    print("\n📝 Next Steps:")
    print("1. Add valid API keys to .env file")
    print("2. Run: python reset_db.py")
    print("3. Start your app: uvicorn app.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())