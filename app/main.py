from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging 
import asyncio

# Database & Settings
from app.config.database import Base, engine, SessionLocal
from app.config import settings

# Services
from app.services.market_data.cache_service import CacheService
from app.services.websocket.market_stream import market_stream_service
from app.services.news_services import NewsService  
from app.services.order_processor import start_order_processor, stop_order_processor

# Models
from app.models import user as user_model, portfolio, token, stock

# Routers
from app.routers import (
    user,
    auth,
    registration,
    portfolio,
    api_key,
    admin,
    news,
    market_data,
    orders,
    candles,
    websocket,
    orders,
    watchlist,
    websocket
)



# Initialize cache & logger
cache_service = CacheService()
logger = logging.getLogger(__name__)


# -------------------------------
# Application Lifecycle
# -------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for background tasks
    Starts on app startup, stops on shutdown
    """
    # Import background services
    from app.services.order_processor import start_order_processor, stop_order_processor
    from app.services.market_data_refresher import start_market_refresher, stop_market_refresher
    
    # Start background tasks
    logger.info("Starting background services...")
    
    # Create tasks
    order_processor_task = asyncio.create_task(start_order_processor())
    market_refresher_task = asyncio.create_task(start_market_refresher())
    
    logger.info("✅ Background services started")
    
    yield
    
    # Shutdown
    logger.info("Stopping background services...")
    await stop_order_processor()
    await stop_market_refresher()
    
    # Cancel tasks
    order_processor_task.cancel()
    market_refresher_task.cancel()
    
    logger.info("✅ Background services stopped")

# -------------------------------
# FastAPI App
# -------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-time stock trading simulator with gamified order processing and live market data.",
    lifespan=lifespan
)


# -------------------------------
# Middleware
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Routers
# -------------------------------
app.include_router(auth.router)
app.include_router(registration.router)
app.include_router(user.router)
app.include_router(portfolio.router)
app.include_router(api_key.router)
app.include_router(admin.router)
app.include_router(news.router)
app.include_router(market_data.router)
app.include_router(candles.router)
app.include_router(watchlist.router)
app.include_router(websocket.router)
app.include_router(orders.router)


# -------------------------------
# Scheduler (News Refresh)
# -------------------------------
@app.on_event("startup")
async def startup_event():
    """Start periodic background tasks like the news refresh scheduler."""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    asyncio.create_task(start_binance_streams())

    async def scheduled_news_refresh():
        db = SessionLocal()
        try:
            news_service = NewsService(db)
            await news_service.refresh_news_articles()
            logger.info("✅ News refreshed successfully")
        except Exception as e:
            logger.error(f"❌ Scheduled news refresh failed: {e}")
        finally:
            db.close()

    scheduler.add_job(
        scheduled_news_refresh,
        "interval",
        minutes=30,
        id="news_refresh",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("News scheduler started — refreshing every 30 minutes.")


# -------------------------------
# Routes
# -------------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Trading Simulator FastAPI Backend"}


@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring."""
    return {
        "status": "healthy",
        "services": {
            "cache": "connected",
            "market_stream": "running",
            "order_processor": "running",
            "news_scheduler": "active",
        },
    }
