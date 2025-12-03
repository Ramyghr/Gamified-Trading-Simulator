import asyncio
import json
import websockets
from app.config.redis_client import redis_client

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

async def subscribe_ticker(symbol: str):
    """
    Subscribe to a Binance ticker stream and push updates to Redis.
    """
    stream_name = f"{symbol.lower()}@ticker"
    url = f"{BINANCE_WS_URL}/{stream_name}"
    
    async with websockets.connect(url) as ws:
        print(f"Subscribed to {symbol} ticker stream.")
        while True:
            message = await ws.recv()
            data = json.loads(message)
            price = float(data["c"])  # current price
            redis_client.set(f"price:{symbol}", price)
            redis_client.publish("market_updates", json.dumps({"symbol": symbol, "price": price}))
