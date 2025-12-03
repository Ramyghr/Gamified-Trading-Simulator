import asyncio
import json
import logging
from typing import List, Dict, Any
import websockets
from app.config.settings import settings
from app.services.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)

class PolygonWebSocketClient:
    def __init__(self):
        self.ws_url = "wss://socket.polygon.io/stocks"
        self.api_key = settings.MARKET_CONFIG.POLYGON_API_KEY
        self.websocket = None
        self.is_connected = False
        self.subscribed_symbols = set()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    async def connect(self):
        """Connect to Polygon WebSocket"""
        try:
            if not self.api_key:
                logger.error("POLYGON_API_KEY not configured")
                return
                
            self.websocket = await websockets.connect(f"{self.ws_url}?apiKey={self.api_key}")
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("Connected to Polygon WebSocket")
            
            # Authenticate
            auth_message = {
                "action": "auth",
                "params": self.api_key
            }
            await self.websocket.send(json.dumps(auth_message))
            
            # Resubscribe to any existing symbols
            if self.subscribed_symbols:
                await self._resubscribe()
            
        except Exception as e:
            logger.error(f"Failed to connect to Polygon WebSocket: {e}")
            self.is_connected = False
            await self._handle_reconnect()

    async def _resubscribe(self):
        """Resubscribe to all previously subscribed symbols"""
        if self.subscribed_symbols:
            subscribe_message = {
                "action": "subscribe",
                "params": ",".join(self.subscribed_symbols)
            }
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"Resubscribed to symbols: {list(self.subscribed_symbols)}")

    async def _handle_reconnect(self):
        """Handle reconnection logic"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(2 ** self.reconnect_attempts, 30)  # Exponential backoff
            logger.info(f"Reconnecting to Polygon in {wait_time} seconds (attempt {self.reconnect_attempts})")
            await asyncio.sleep(wait_time)
            await self.connect()
        else:
            logger.error("Max reconnection attempts reached. Polygon WebSocket connection failed.")

    async def subscribe(self, symbols: List[str]):
        """Subscribe to symbols"""
        if not self.is_connected or not self.websocket:
            await self.connect()
            return
            
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(symbols)
        }
        await self.websocket.send(json.dumps(subscribe_message))
        self.subscribed_symbols.update(symbols)
        logger.info(f"Subscribed to symbols: {symbols}")

    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        if self.is_connected and self.websocket:
            unsubscribe_message = {
                "action": "unsubscribe",
                "params": ",".join(symbols)
            }
            await self.websocket.send(json.dumps(unsubscribe_message))
            self.subscribed_symbols.difference_update(symbols)
            logger.info(f"Unsubscribed from symbols: {symbols}")

    async def listen(self):
        """Listen for messages from Polygon WebSocket"""
        if not self.is_connected or not self.websocket:
            await self.connect()
            if not self.is_connected:
                return
                
        try:
            async for message in self.websocket:
                await self._handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.error("Polygon WebSocket connection closed")
            self.is_connected = False
            await self._handle_reconnect()
        except Exception as e:
            logger.error(f"Error in Polygon WebSocket listener: {e}")
            self.is_connected = False
            await self._handle_reconnect()

    async def _handle_message(self, raw_message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(raw_message)
            
            # Polygon sends arrays of events
            if isinstance(data, list):
                for event in data:
                    await self._process_event(event)
            else:
                await self._process_event(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def _process_event(self, event: Dict[str, Any]):
        """Process individual events"""
        try:
            event_type = event.get("ev")
            symbol = event.get("sym", "")
            
            if event_type == "status":
                logger.info(f"Polygon status: {event.get('message', '')}")
                return
                
            # Map Polygon event types to our format
            if event_type in ["T", "Q", "A", "AM"]:  # Trades, Quotes, Aggregate
                formatted_message = {
                    "type": self._map_event_type(event_type),
                    "symbol": symbol,
                    "data": event,
                    "timestamp": event.get("t", event.get("s", 0)),
                    "source": "polygon"
                }
                
                # Broadcast to all subscribed clients
                await connection_manager.broadcast_to_subscribers(symbol, formatted_message)
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _map_event_type(self, polygon_event_type: str) -> str:
        """Map Polygon event types to our internal types"""
        event_map = {
            "T": "trade",
            "Q": "quote", 
            "A": "aggregate",
            "AM": "aggregate_minute"
        }
        return event_map.get(polygon_event_type, "unknown")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from Polygon WebSocket")

# Global instance
polygon_ws_client = PolygonWebSocketClient()