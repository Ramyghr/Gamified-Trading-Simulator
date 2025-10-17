from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
from datetime import datetime
import enum

# ----------------------
# Association Table
# ----------------------
# Many-to-many relationship between users and liked articles
article_likes = Table(
    'article_likes',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('article_id', Integer, ForeignKey('news_articles.id')),
    Column('created_at', DateTime, default=func.now())
)

# ----------------------
# Enums
# ----------------------
class NewsSource(enum.Enum):
    NEWSAPI = "NEWSAPI"
    MARKETAUX = "MARKETAUX"
    ALPHA_VANTAGE = "ALPHA_VANTAGE"


class OrderAction(enum.Enum):
    BUY = "Buy"
    SELL = "Sell"

class OrderType(enum.Enum):
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"

class OrderDuration(enum.Enum):
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    DAY = "DAY"  # Day Order
    GTC = "GTC"  # Good Till Cancelled

class StockExchange(enum.Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"

# ----------------------
# Models
# ----------------------
class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core article info
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)  # AI-generated summary
    source = Column(String(255))
    source_type = Column(Enum(NewsSource), default=NewsSource.NEWSAPI)
    author = Column(String(255))
    url = Column(String(500))
    url_to_image = Column(String(500))
    published_at = Column(DateTime, default=func.now())
    
    # Stock / financial metadata
    symbol = Column(String(50))  # Related stock symbol
    sentiment = Column(String(50))  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float)  # Numerical sentiment score (-1 to 1)
    topics = Column(Text)  # Comma-separated topics/tags
    
    # Engagement metrics
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    liked_by = relationship("User", secondary=article_likes, back_populates="liked_news_articles")
    comments = relationship("NewsArticleComment", back_populates="article", cascade="all, delete-orphan")


class NewsArticleComment(Base):
    __tablename__ = "news_article_comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="comments")
    article = relationship("NewsArticle", back_populates="comments")


# class StockTransaction(Base):
#     __tablename__ = "stock_transactions"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     symbol = Column(String(50), nullable=False)
#     company_name = Column(String(255))
#     quantity = Column(Integer, nullable=False)
#     price_per_share = Column(Float, nullable=False)
#     total_amount = Column(Float, nullable=False)
#     action = Column(Enum(OrderAction), nullable=False)  # Buy or Sell
#     order_type = Column(Enum(OrderType), nullable=False)  # Market, Limit, Stop
#     duration = Column(Enum(OrderDuration), nullable=False)  # IOC, FOK, DAY, GTC
#     exchange = Column(Enum(StockExchange))
#     status = Column(String(50), default="COMPLETED")  # PENDING, COMPLETED, CANCELLED
#     transaction_date = Column(DateTime, default=func.now())
#     created_at = Column(DateTime, default=func.now())

#     # Relationships
#     user = relationship("User", back_populates="transactions")
