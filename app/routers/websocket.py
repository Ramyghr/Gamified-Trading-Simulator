"""
WebSocket endpoints for real-time market data - REAL DATA ONLY
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
import logging
from app.config.redis_client import redis_client
from app.services.websocket.connection_manager import connection_manager
from app.services.websocket.market_stream import market_stream_service
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for REAL-TIME market data from Polygon.

    Client sends:
    {
        "action": "subscribe",
        "symbols": ["AAPL", "TSLA", "BTC"]
    }

    Server broadcasts REAL Polygon data:
    {
        "type": "trade",
        "symbol": "AAPL", 
        "data": { ... real polygon data ... },
        "timestamp": 1234567890,
        "source": "polygon"
    }
    """
    connection_id = str(uuid.uuid4())
    await connection_manager.connect(websocket, connection_id)

    try:
        # Send welcome message
        await connection_manager.send_personal_message(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "message": "Connected to REAL Polygon market data stream"
        })

        # Start market stream service if not already running
        await market_stream_service.start()

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")
            symbols = message.get("symbols", [])

            if action == "subscribe":
                await connection_manager.subscribe(connection_id, symbols)
                await market_stream_service.subscribe_symbols(symbols)
                await connection_manager.send_personal_message(connection_id, {
                    "type": "subscribed",
                    "symbols": symbols,
                    "message": f"Subscribed to REAL data for {len(symbols)} symbols"
                })

            elif action == "unsubscribe":
                await connection_manager.unsubscribe(connection_id, symbols)
                await market_stream_service.unsubscribe_symbols(symbols)
                await connection_manager.send_personal_message(connection_id, {
                    "type": "unsubscribed",
                    "symbols": symbols,
                    "message": f"Unsubscribed from {len(symbols)} symbols"
                })

            elif action == "ping":
                await connection_manager.send_personal_message(connection_id, {
                    "type": "pong"
                })

            else:
                await connection_manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })
                logger.warning(f"Unknown action received: {action}")

    except WebSocketDisconnect:
        await connection_manager.disconnect(connection_id)
        logger.info(f"Client {connection_id} disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.disconnect(connection_id)
@router.websocket("/market")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    pubsub.subscribe("market_updates")

    async for message in pubsub.listen():
        if message["type"] == "message":
            await websocket.send_text(message["data"])
@router.on_event("startup")
async def startup_event():
    """Start market stream service on application startup"""
    await market_stream_service.start()

@router.on_event("shutdown")
async def shutdown_event():
    """Stop market stream service on application shutdown"""
    await market_stream_service.stop()