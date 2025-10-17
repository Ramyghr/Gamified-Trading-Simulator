from typing import Dict, List
from pydantic_settings import BaseSettings

class MarketDataConfig(BaseSettings):
    # Provider Configuration
    POLYGON_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    TWELVE_DATA_API_KEY: str = ""
    
    # Provider Endpoints
    POLYGON_BASE_URL: str = "https://api.polygon.io"
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co"
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"
    TWELVE_DATA_BASE_URL: str = "https://api.twelvedata.com"
    BINANCE_BASE_URL: str = "https://api.binance.com"
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    
    # WebSocket URLs
    POLYGON_WS_URL: str = "wss://socket.polygon.io"
    FINNHUB_WS_URL: str = "wss://ws.finnhub.io"
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443"
    
    # Rate Limits (requests per minute)
    POLYGON_RATE_LIMIT: int = 5
    ALPHA_VANTAGE_RATE_LIMIT: int = 5
    FINNHUB_RATE_LIMIT: int = 60
    TWELVE_DATA_RATE_LIMIT: int = 8
    
    # Cache Configuration
    QUOTE_CACHE_TTL: int = 1  # seconds (real-time)
    CANDLE_CACHE_TTL: int = 60  # seconds (1 minute)
    HISTORICAL_CACHE_TTL: int = 3600  # seconds (1 hour)
    
    # Provider Priority (fallback order)
    STOCK_PROVIDERS: List[str] = ["polygon", "finnhub", "alpha_vantage"]
    FOREX_PROVIDERS: List[str] = ["alpha_vantage", "twelve_data"]
    CRYPTO_PROVIDERS: List[str] = ["binance", "coingecko"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'  # This ignores extra environment variables

market_config = MarketDataConfig()