"""
Bot Executor Worker - Continuous Execution Script
Save as: app/scripts/run_bot_worker.py

This worker runs continuously as long as the container is running
"""
import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.bot.bot_executor import bot_executor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_worker.log')
    ]
)

logger = logging.getLogger(__name__)


class BotWorker:
    """Main bot worker process"""
    
    def __init__(self):
        self.is_running = False
        self.executor = bot_executor
    
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.is_running = False
        self.executor.stop()
    
    async def run(self):
        """Run the bot worker continuously"""
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        self.is_running = True
        
        logger.info("=" * 80)
        logger.info("🤖 BOT TRADING EXECUTOR STARTED")
        logger.info("=" * 80)
        logger.info("Service: Algorithmic Trading Bot Executor")
        logger.info("Mode: Continuous Execution")
        logger.info("Check Interval: 60 seconds")
        logger.info("=" * 80)
        
        try:
            # Run executor forever (checks every 60 seconds)
            await self.executor.run_forever(interval_seconds=60)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error in bot worker: {str(e)}", exc_info=True)
            raise
        finally:
            logger.info("Bot worker shutting down...")
            self.executor.stop()
            logger.info("✅ Bot worker stopped gracefully")


async def main():
    """Main entry point"""
    worker = BotWorker()
    
    try:
        await worker.run()
    except Exception as e:
        logger.error(f"Worker crashed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the worker
    asyncio.run(main())