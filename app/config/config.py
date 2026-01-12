import os
from dotenv import load_dotenv
from typing import Any, List
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Trading Simulator FastAPI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://localhost:4201",
        "http://127.0.0.1:4200",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@trading-postgres:5432/trading_db")
    
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
    
    # HF Token
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    RAPID_API_KEY: str = os.getenv("RAPID_API_KEY", "")
    
    # News APIs
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"
    MARKETAUX_API_KEY: str = os.getenv("MARKETAUX_API_KEY", "")
    
    # Sentiment Analysis
    SENTIMENT_MODEL: str = "ProsusAI/finbert"
    SENTIMENT_THRESHOLD_POSITIVE: float = 0.7
    SENTIMENT_THRESHOLD_NEGATIVE: float = 0.7
    
    # Cache settings
    CACHE_EXPIRATION: int = 300  # 5 minutes
    
    # Bot executor interval
    BOT_EXECUTOR_INTERVAL: int = int(os.getenv("BOT_EXECUTOR_INTERVAL", "60"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'  # CRITICAL: Ignores extra env variables

settings = Settings()