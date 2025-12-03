from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NewsSource(str, Enum):
    NEWSAPI = "NEWSAPI"
    MARKETAUX = "MARKETAUX"
    ALPHA_VANTAGE = "ALPHA_VANTAGE"


class NewsArticleCommentBase(BaseModel):
    content: str

class NewsArticleCommentCreate(NewsArticleCommentBase):
    article_id: int

class NewsArticleCommentResponse(NewsArticleCommentBase):
    id: int
    author: str
    posted_date_time: datetime
    user_id: int
    
    class Config:
        from_attributes = True

class NewsArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[NewsSource] = None
    author: Optional[str] = None
    url: Optional[str] = None
    url_to_image: Optional[str] = None
    published_at: Optional[datetime] = None
    symbol: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    topics: Optional[str] = None

class NewsArticleCreate(NewsArticleBase):
    pass

class NewsArticleResponse(NewsArticleBase):
    id: int
    like_count: int
    comment_count: int
    liked: bool = False  # Whether current user liked this article
    comments: List[NewsArticleCommentResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NewsPaginatedResponse(BaseModel):
    items: List[NewsArticleResponse]
    total: int
    page: int
    size: int
    pages: int

class LikeResponse(BaseModel):
    article_id: int
    liked: bool
    like_count: int