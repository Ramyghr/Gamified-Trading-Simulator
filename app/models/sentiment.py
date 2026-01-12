"""
Models for sentiment analysis and news articles
"""
from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# ========================
# Enums
# ========================

class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class TradingSignal(str, Enum):
    """Trading signal recommendations"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


# ========================
# Core Models
# ========================

class NewsArticle(BaseModel):
    """News article model"""
    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(None, description="Article description/summary")
    content: Optional[str] = Field(None, description="Full article content")
    source: str = Field(..., description="News source name")
    url: str = Field(..., description="Article URL")
    published_at: datetime = Field(..., description="Publication timestamp")
    author: Optional[str] = Field(None, description="Article author")
    image_url: Optional[str] = Field(None, description="Article image URL")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Tech Stocks Rally on Strong Earnings",
                "description": "Major tech companies exceed expectations",
                "content": "Technology stocks surged today...",
                "source": "Financial Times",
                "url": "https://example.com/article",
                "published_at": "2025-01-12T10:00:00Z",
                "author": "John Doe",
                "image_url": "https://example.com/image.jpg"
            }
        }


class SentimentScore(BaseModel):
    """Sentiment score with label and confidence"""
    label: SentimentLabel = Field(..., description="Sentiment classification")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "label": "positive",
                "score": 0.85
            }
        }


class SentimentAnalysis(BaseModel):
    """Complete sentiment analysis for an article"""
    article: NewsArticle = Field(..., description="The analyzed article")
    sentiment: SentimentScore = Field(..., description="Sentiment analysis result")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    entities: List[str] = Field(default_factory=list, description="Extracted entities (companies, indices)")

    class Config:
        json_schema_extra = {
            "example": {
                "article": {
                    "title": "Apple Stock Surges",
                    "description": "Apple announces record earnings",
                    "source": "Bloomberg",
                    "url": "https://example.com/apple",
                    "published_at": "2025-01-12T10:00:00Z"
                },
                "sentiment": {
                    "label": "positive",
                    "score": 0.92
                },
                "keywords": ["Apple", "earnings", "record"],
                "entities": ["Apple", "NASDAQ"]
            }
        }


class MarketSentimentSummary(BaseModel):
    """Summary of market sentiment across multiple articles"""
    overall_sentiment: SentimentLabel = Field(..., description="Overall market sentiment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in overall sentiment")
    positive_count: int = Field(..., ge=0, description="Number of positive articles")
    negative_count: int = Field(..., ge=0, description="Number of negative articles")
    neutral_count: int = Field(..., ge=0, description="Number of neutral articles")
    total_articles: int = Field(..., ge=0, description="Total articles analyzed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    trending_topics: List[str] = Field(default_factory=list, description="Top trending topics")
    sentiment_momentum: float = Field(..., ge=-1.0, le=1.0, description="Sentiment momentum (-1 to +1)")
    market_fear_greed: float = Field(..., ge=0.0, le=100.0, description="Fear & Greed index (0-100)")
    volatility_index: float = Field(..., ge=0.0, le=100.0, description="Volatility index (0-100)")
    trading_signal: TradingSignal = Field(..., description="Trading signal recommendation")
    risk_level: RiskLevel = Field(..., description="Current risk level")
    recommendation: str = Field(..., description="Detailed recommendation text")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_sentiment": "positive",
                "confidence": 0.75,
                "positive_count": 15,
                "negative_count": 3,
                "neutral_count": 2,
                "total_articles": 20,
                "timestamp": "2025-01-12T10:00:00Z",
                "trending_topics": ["AI", "Tesla", "Bitcoin"],
                "sentiment_momentum": 0.6,
                "market_fear_greed": 72.5,
                "volatility_index": 35.0,
                "trading_signal": "buy",
                "risk_level": "medium",
                "recommendation": "Market shows positive momentum with moderate risk"
            }
        }


# ========================
# Request/Response Models
# ========================

class SentimentRequest(BaseModel):
    """Request model for sentiment analysis"""
    text: str = Field(..., min_length=1, description="Text to analyze")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Apple stock surges to all-time high on strong earnings report"
            }
        }


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis"""
    text: str = Field(..., description="Original text")
    sentiment: SentimentScore = Field(..., description="Sentiment analysis result")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Apple stock surges to all-time high",
                "sentiment": {
                    "label": "positive",
                    "score": 0.89
                },
                "keywords": ["Apple", "stock", "surge"],
                "processed_at": "2025-01-12T10:00:00Z"
            }
        }


# ========================
# Trend Analysis Models
# ========================

class TrendAnalysis(BaseModel):
    """Trend analysis for a specific topic"""
    topic: str = Field(..., description="Topic or entity being analyzed")
    sentiment_trend: List[SentimentScore] = Field(..., description="Sentiment scores over time")
    article_count: int = Field(..., ge=0, description="Number of articles analyzed")
    time_period: str = Field(..., description="Time period analyzed (e.g., '24h', '7d')")
    momentum: float = Field(..., ge=-1.0, le=1.0, description="Topic momentum (-1 to +1)")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Tesla",
                "sentiment_trend": [
                    {"label": "positive", "score": 0.85},
                    {"label": "positive", "score": 0.78}
                ],
                "article_count": 15,
                "time_period": "24h",
                "momentum": 0.65
            }
        }


class MarketIndicator(BaseModel):
    """Market indicator influenced by sentiment"""
    name: str = Field(..., description="Indicator name")
    value: float = Field(..., description="Indicator value")
    sentiment_influence: float = Field(..., ge=0.0, le=1.0, description="Sentiment influence factor")
    timestamp: datetime = Field(default_factory=datetime.now, description="Indicator timestamp")
    description: str = Field(..., description="Indicator description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Market Sentiment Index",
                "value": 72.5,
                "sentiment_influence": 0.85,
                "timestamp": "2025-01-12T10:00:00Z",
                "description": "Overall market sentiment based on news analysis"
            }
        }