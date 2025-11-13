import os
from dotenv import load_dotenv
from typing import Any
import redis
from app.config.market_config import MarketDataConfig

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Trading Simulator FastAPI"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trading_simulator.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 10  # 10 days
    
    # Email
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URL: str = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

    # External APIs
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    RAPID_API_KEY: str = os.getenv("RAPID_API_KEY", "")
    
    # News APIs
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    MARKETAUX_API_KEY: str = os.getenv("MARKETAUX_API_KEY", "")

    MARKET_CONFIG: MarketDataConfig = MarketDataConfig()

    def get_market_config(self):
        from app.config.market_config import market_config
        return market_config


settings = Settings()


