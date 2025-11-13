import asyncio
import logging

logger = logging.getLogger(__name__)

class MarketStreamService:
    def __init__(self):
        self.is_running = False
        self.task = None
        self.polygon_client = None

    async def start(self):
        """Start the market data streaming service"""
        if self.is_running:
            return
            
        # Initialize Polygon client
        try:
            from app.services.market_data.polygon_websocket import polygon_ws_client
            self.polygon_client = polygon_ws_client
            
            if not self.polygon_client.api_key:
                logger.error("POLYGON_API_KEY is not configured. Real market data will not be available.")
                return
                
            logger.info("Polygon WebSocket client initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import Polygon WebSocket client: {e}")
            logger.error("Make sure app/services/market_data/polygon_websocket.py exists")
            return
        except Exception as e:
            logger.error(f"Error initializing Polygon client: {e}")
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._run())
        logger.info("Market stream service started - USING REAL POLYGON DATA")

    async def stop(self):
        """Stop the market data streaming service"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.polygon_client:
            await self.polygon_client.disconnect()
        logger.info("Market stream service stopped")

    async def _run(self):
        """Main service loop - REAL DATA ONLY"""
        while self.is_running:
            try:
                if self.polygon_client and self.polygon_client.api_key:
                    await self.polygon_client.listen()
                else:
                    logger.error("Polygon client not available or API key not configured")
                    await asyncio.sleep(5)  # Wait before retrying
                    
            except Exception as e:
                logger.error(f"Market stream service error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def subscribe_symbols(self, symbols: list):
        """Subscribe to symbols in the market data feed"""
        if self.polygon_client and self.polygon_client.api_key:
            await self.polygon_client.subscribe(symbols)
            logger.info(f"Subscribed to REAL Polygon data for: {symbols}")
        else:
            logger.error("Cannot subscribe: Polygon client not available")

    async def unsubscribe_symbols(self, symbols: list):
        """Unsubscribe from symbols in the market data feed"""
        if self.polygon_client and self.polygon_client.api_key:
            await self.polygon_client.unsubscribe(symbols)
            logger.info(f"Unsubscribed from REAL Polygon data for: {symbols}")
        else:
            logger.error("Cannot unsubscribe: Polygon client not available")

# Global instance
market_stream_service = MarketStreamService()