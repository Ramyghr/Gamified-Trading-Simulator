"""
Test WebSocket connection to market data stream
Run: python scripts/test_websocket.py
"""
import asyncio
import websockets
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_websocket():
    """Test WebSocket market data stream"""
    uri = "ws://localhost:8000/ws/market"
    
    print("🔌 Connecting to WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            print(f"📨 Received: {welcome}")
            
            # Subscribe to symbols
            subscribe_msg = {
                "action": "subscribe",
                "symbols": ["AAPL", "TSLA", "BTC"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"📤 Sent: {subscribe_msg}")
            
            # Listen for updates
            print("\n📊 Listening for market updates (Ctrl+C to stop)...\n")
            
            try:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "quote":
                        symbol = data.get("symbol")
                        price = data.get("price")
                        change_pct = data.get("change_percent", 0)
                        print(f"  {symbol:6} ${price:8.2f}  ({change_pct:+.2f}%)")
                    else:
                        print(f"  📨 {data}")
            
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping...")
                
                # Unsubscribe
                unsubscribe_msg = {
                    "action": "unsubscribe",
                    "symbols": ["AAPL", "TSLA", "BTC"]
                }
                await websocket.send(json.dumps(unsubscribe_msg))
                print("👋 Unsubscribed and disconnected")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())