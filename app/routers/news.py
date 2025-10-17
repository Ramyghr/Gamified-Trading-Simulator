from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.services.news_services import NewsService
from app.schemas.news import (
    NewsArticleResponse, 
    NewsArticleCommentCreate, 
    NewsArticleCommentResponse,
    NewsPaginatedResponse,
    LikeResponse
)
from app.middleware.jwt_middleware import get_current_user
from app.middleware.role_middleware import get_optional_user
from app.config.database import get_db
from app.models.user import User

router = APIRouter(prefix="/news", tags=["news"])

@router.get("/", response_model=NewsPaginatedResponse)
async def get_news_articles(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=10, ge=1, le=50),
    sort_by: str = Query(default="published_at", regex="^(published_at|like_count|sentiment_score)$"),
    symbol: Optional[str] = Query(default=None),
    current_user: Optional[User] = Depends(get_optional_user),  # Optional auth
    db: Session = Depends(get_db)
):
    """Get paginated news articles (PUBLIC - no login required)"""
    news_service = NewsService(db)
    return news_service.get_news_articles(page, size, sort_by, symbol, current_user)

@router.post("/{article_id}/like", response_model=LikeResponse)
async def flip_like(
    article_id: int,
    current_user: User = Depends(get_current_user),  # REQUIRES login
    db: Session = Depends(get_db)
):
    """Like or unlike a news article (REQUIRES login)"""
    news_service = NewsService(db)
    return news_service.flip_like(article_id, current_user)

@router.post("/comment", response_model=NewsArticleCommentResponse)
async def add_comment(
    comment_data: NewsArticleCommentCreate,
    current_user: User = Depends(get_current_user),  # REQUIRES login
    db: Session = Depends(get_db)
):
    """Add a comment to a news article (REQUIRES login)"""
    news_service = NewsService(db)
    return news_service.add_comment(comment_data, current_user)

@router.post("/refresh")
async def refresh_news(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger news refresh (PUBLIC - but might want to protect this later)"""
    news_service = NewsService(db)
    background_tasks.add_task(news_service.refresh_news_articles)
    return {"message": "News refresh started in background"}

@router.get("/sources")
async def get_news_sources():
    """Get available news sources (PUBLIC)"""
    return {
        "sources": [
            {
                "id": "newsapi",
                "name": "NewsAPI",
                "description": "General news from various sources"
            },
            {
                "id": "marketaux", 
                "name": "MarketAux",
                "description": "Financial and market-specific news"
            }
        ]
    }

@router.get("/{article_id}")
async def get_news_article(
    article_id: int,
    current_user: Optional[User] = Depends(get_optional_user),  # Optional auth
    db: Session = Depends(get_db)
):
    """Get a specific news article by ID (PUBLIC)"""
    news_service = NewsService(db)
    try:
        # This would need to be implemented in NewsService
        return news_service.get_article_by_id(article_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))