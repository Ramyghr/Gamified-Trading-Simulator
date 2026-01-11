"""
Debug script to test historical data fetching
Run this to diagnose the issue: python -m app.scripts.debug_data_fetch
"""
import asyncio
import yfinance as yf
from datetime import datetime
import pandas as pd

async def test_yahoo_direct():
    """Test Yahoo Finance directly"""
    print("\n" + "="*60)
    print("TESTING YAHOO FINANCE DIRECTLY")
    print("="*60)
    
    symbols_to_test = [
        ("GC=F", "Gold Futures"),
        ("XAUUSD=X", "Gold Forex"),
        ("SI=F", "Silver Futures"),
        ("CL=F", "Crude Oil Futures"),
        ("AAPL", "Apple Stock (control test)")
    ]
    
    for symbol, name in symbols_to_test:
        print(f"\n📊 Testing {name} ({symbol})...")
        try:
            ticker = yf.Ticker(symbol)
            
            # Test 1: Get info
            try:
                info = ticker.info
                print(f"  ✓ Ticker info available: {info.get('longName', 'N/A')}")
            except Exception as e:
                print(f"  ✗ Ticker info failed: {e}")
            
            # Test 2: Get daily data (last 30 days)
            try:
                df_daily = ticker.history(period="1mo", interval="1d")
                if not df_daily.empty:
                    print(f"  ✓ Daily data: {len(df_daily)} candles")
                    print(f"    Latest: {df_daily.index[-1]} - Close: ${df_daily['Close'].iloc[-1]:.2f}")
                else:
                    print(f"  ✗ Daily data: EMPTY")
            except Exception as e:
                print(f"  ✗ Daily data failed: {e}")
            
            # Test 3: Get hourly data (last 7 days)
            try:
                df_hourly = ticker.history(period="7d", interval="1h")
                if not df_hourly.empty:
                    print(f"  ✓ Hourly data: {len(df_hourly)} candles")
                else:
                    print(f"  ✗ Hourly data: EMPTY")
            except Exception as e:
                print(f"  ✗ Hourly data failed: {e}")
            
            # Test 4: Get specific date range
            try:
                start = datetime(2024, 12, 1)
                end = datetime(2024, 12, 10)
                df_range = ticker.history(start=start, end=end, interval="1d")
                if not df_range.empty:
                    print(f"  ✓ Date range (Dec 1-10): {len(df_range)} candles")
                    print(f"    Date range: {df_range.index[0]} to {df_range.index[-1]}")
                else:
                    print(f"  ✗ Date range (Dec 1-10): EMPTY")
            except Exception as e:
                print(f"  ✗ Date range failed: {e}")
                
        except Exception as e:
            print(f"  ✗ Complete failure: {e}")

async def test_historical_service():
    """Test our historical data service"""
    print("\n" + "="*60)
    print("TESTING HISTORICAL DATA SERVICE")
    print("="*60)
    
    try:
        from app.services.bot.historical_data_service import historical_data_service
        
        symbols = [
            ("XAUUSD", "commodity"),
            ("AAPL", "stock"),
            ("BTC-USD", "crypto")
        ]
        
        for symbol, asset_class in symbols:
            print(f"\n📈 Testing {symbol} ({asset_class})...")
            try:
                data = await historical_data_service.get_historical_data(
                    symbol=symbol,
                    start_date=datetime(2024, 12, 1),
                    end_date=datetime(2024, 12, 10),
                    interval="1d",
                    asset_class=asset_class
                )
                
                if not data.empty:
                    print(f"  ✓ SUCCESS: {len(data)} candles")
                    print(f"  Columns: {list(data.columns)}")
                    print(f"  Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
                    print(f"  Sample data:")
                    print(data.head(3).to_string(index=False))
                else:
                    print(f"  ✗ EMPTY RESULT")
                    
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")

async def test_source_status():
    """Check which data sources are enabled"""
    print("\n" + "="*60)
    print("DATA SOURCE STATUS")
    print("="*60)
    
    try:
        from app.services.bot.historical_data_service import historical_data_service
        
        status = historical_data_service.get_source_status()
        
        for source_name, info in status.items():
            enabled = "✓ ENABLED" if info["enabled"] else "✗ DISABLED"
            print(f"\n{source_name}: {enabled}")
            print(f"  Priority: {info['priority']}")
            print(f"  Asset classes: {', '.join(info['asset_classes'])}")
            print(f"  Rate limit: {info['rate_limit']}/min")
            
    except Exception as e:
        print(f"Error: {e}")

async def main():
    print("\n🔍 HISTORICAL DATA DEBUGGING TOOL")
    print("="*60)
    
    # Test 1: Yahoo Finance direct
    await test_yahoo_direct()
    
    # Test 2: Check source status
    await test_source_status()
    
    # Test 3: Test our service
    await test_historical_service()
    
    print("\n" + "="*60)
    print("DEBUGGING COMPLETE")
    print("="*60)
    
    print("\n💡 NEXT STEPS:")
    print("  1. If Yahoo works but service doesn't → Symbol conversion issue")
    print("  2. If Yahoo empty → Try different date range (more recent)")
    print("  3. If all fail → Check internet connection / firewall")
    print("  4. If AAPL works but GC=F doesn't → Yahoo may not have futures data in your region")

if __name__ == "__main__":
    asyncio.run(main())