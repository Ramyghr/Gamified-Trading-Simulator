import json
from typing import Dict, List, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        logger.info(f"Client {connection_id} connected")

    async def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].close()
            except Exception:
                pass
            del self.active_connections[connection_id]
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
        logger.info(f"Client {connection_id} disconnected")

    async def send_personal_message(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")

    async def broadcast_to_subscribers(self, symbol: str, message: dict):
        """Broadcast message to all connections subscribed to a specific symbol"""
        disconnected_connections = []
        
        for connection_id, symbols in self.subscriptions.items():
            if symbol in symbols and connection_id in self.active_connections:
                try:
                    await self.active_connections[connection_id].send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)

    async def subscribe(self, connection_id: str, symbols: List[str]):
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].update(symbols)
        logger.info(f"Client {connection_id} subscribed to {symbols}")

    async def unsubscribe(self, connection_id: str, symbols: List[str]):
        if connection_id in self.subscriptions:
            for symbol in symbols:
                self.subscriptions[connection_id].discard(symbol)
        logger.info(f"Client {connection_id} unsubscribed from {symbols}")

    def get_subscribed_symbols(self, connection_id: str) -> Set[str]:
        return self.subscriptions.get(connection_id, set())

    def get_all_subscribed_symbols(self) -> Set[str]:
        """Get all unique symbols that clients are subscribed to"""
        all_symbols = set()
        for symbols in self.subscriptions.values():
            all_symbols.update(symbols)
        return all_symbols

# Global instance
connection_manager = ConnectionManager()