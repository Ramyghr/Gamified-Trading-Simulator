import httpx
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import json

from app.models.stock import NewsArticle, NewsArticleComment, NewsSource, article_likes
from app.models.user import User
from app.schemas.news import NewsArticleCreate, NewsArticleCommentCreate
from app.config.settings import settings
from app.middleware.jwt_middleware import get_current_user

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self, db: Session):
        self.db = db
        
    async def fetch_newsapi_articles(self) -> List[NewsArticleCreate]:
        """Fetch articles from NewsAPI"""
        if not settings.NEWS_API_KEY:
            logger.warning("NewsAPI key not configured")
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                # Get news from last 24 hours
                from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'q': 'stocks OR trading OR investing OR finance',
                    'from': from_date,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'apiKey': settings.NEWS_API_KEY,
                    'pageSize': 50
                }
                
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                articles = []
                
                for item in data.get('articles', []):
                    # Skip articles without title or content
                    if not item.get('title') or not item.get('content'):
                        continue
                        
                    article = NewsArticleCreate(
                        title=item['title'],
                        content=item['content'],
                        author=item.get('author'),
                        source=item.get('source', {}).get('name'),
                        source_type=NewsSource.NEWSAPI,
                        url=item.get('url'),
                        url_to_image=item.get('urlToImage'),
                        published_at=datetime.fromisoformat(item['publishedAt'].replace('Z', '+00:00')) if item.get('publishedAt') else None,
                        summary=item.get('description')
                    )
                    articles.append(article)
                    
                logger.info(f"Fetched {len(articles)} articles from NewsAPI")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []

    async def fetch_marketaux_articles(self) -> List[NewsArticleCreate]:
        """Fetch articles from MarketAux (more financial-focused)"""
        if not settings.MARKETAUX_API_KEY:
            logger.warning("MarketAux API key not configured")
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                url = "https://api.marketaux.com/v1/news/all"
                params = {
                    'api_token': settings.MARKETAUX_API_KEY,
                    'language': 'en',
                    'limit': 50,
                    'entities': 'TSLA,AAPL,MSFT,GOOGL,AMZN'  # Top tech stocks
                }
                
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                articles = []
                
                for item in data.get('data', []):
                    # Extract symbols from entities
                    symbols = []
                    for entity in item.get('entities', []):
                        if entity.get('symbol'):
                            symbols.append(entity['symbol'])
                    
                    article = NewsArticleCreate(
                        title=item['title'],
                        content=item.get('description'),
                        source=item.get('source'),
                        source_type=NewsSource.MARKETAUX,
                        url=item.get('url'),
                        url_to_image=item.get('image_url'),
                        published_at=datetime.fromisoformat(item['published_at'].replace('Z', '+00:00')) if item.get('published_at') else None,
                        symbol=','.join(symbols) if symbols else None,
                        sentiment=item.get('sentiment'),
                        sentiment_score=float(item['sentiment_score']) if item.get('sentiment_score') else None,
                        topics=', '.join(item.get('topics', [])),
                        summary=item.get('snippet')
                    )
                    articles.append(article)
                    
                logger.info(f"Fetched {len(articles)} articles from MarketAux")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching from MarketAux: {e}")
            return []

    async def refresh_news_articles(self):
        """Refresh news articles from all sources"""
        logger.info("Starting news refresh from all sources...")
        
        try:
            # Fetch from both sources concurrently
            newsapi_articles, marketaux_articles = await asyncio.gather(
                self.fetch_newsapi_articles(),
                self.fetch_marketaux_articles(),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(newsapi_articles, Exception):
                logger.error(f"NewsAPI fetch failed: {newsapi_articles}")
                newsapi_articles = []
            if isinstance(marketaux_articles, Exception):
                logger.error(f"MarketAux fetch failed: {marketaux_articles}")
                marketaux_articles = []
            
            all_articles = newsapi_articles + marketaux_articles
            saved_count = 0
            
            for article_data in all_articles:
                try:
                    # Check if article already exists (by title and source)
                    existing = self.db.query(NewsArticle).filter(
                        NewsArticle.title == article_data.title,
                        NewsArticle.source_type == article_data.source_type
                    ).first()
                    
                    if not existing:
                        # Create new article
                        article = NewsArticle(**article_data.dict())
                        self.db.add(article)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving article '{article_data.title}': {e}")
                    continue
            
            self.db.commit()
            logger.info(f"News refresh completed. Saved {saved_count} new articles.")
            
            # Clean up old articles (keep only last 1000)
            self.cleanup_old_articles()
            
        except Exception as e:
            logger.error(f"Error in news refresh: {e}")
            self.db.rollback()

    def cleanup_old_articles(self):
        """Keep only the most recent 1000 articles"""
        try:
            # Get total count
            total_count = self.db.query(NewsArticle).count()
            
            if total_count > 1000:
                # Find the 1000th newest article
                thousandth_article = self.db.query(NewsArticle).order_by(
                    desc(NewsArticle.published_at)
                ).offset(999).first()
                
                if thousandth_article:
                    # Delete articles older than the 1000th
                    deleted_count = self.db.query(NewsArticle).filter(
                        NewsArticle.published_at < thousandth_article.published_at
                    ).delete()
                    
                    self.db.commit()
                    logger.info(f"Cleaned up {deleted_count} old articles")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old articles: {e}")
            self.db.rollback()

    def get_news_articles(self, page: int = 0, size: int = 10, sort_by: str = "published_at", 
                         symbol: Optional[str] = None, current_user: Optional[User] = None) -> dict:
        """Get paginated news articles with user engagement data"""
        try:
            # Build query
            query = self.db.query(NewsArticle)
            
            # Filter by symbol if provided
            if symbol:
                query = query.filter(NewsArticle.symbol.contains(symbol))
            
            # Apply sorting
            if sort_by == "published_at":
                query = query.order_by(desc(NewsArticle.published_at))
            elif sort_by == "like_count":
                query = query.order_by(desc(NewsArticle.like_count))
            elif sort_by == "sentiment_score":
                query = query.order_by(desc(NewsArticle.sentiment_score))
            else:
                query = query.order_by(desc(NewsArticle.published_at))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = page * size
            articles = query.offset(offset).limit(size).all()
            
            # Convert to response format with user engagement
            article_responses = []
            for article in articles:
                article_dict = {
                    **article.__dict__,
                    'liked': False,
                    'comments': []
                }
                
                # Check if current user liked this article
                if current_user:
                    liked = self.db.query(article_likes).filter(
                        article_likes.c.user_id == current_user.id,
                        article_likes.c.article_id == article.id
                    ).first() is not None
                    article_dict['liked'] = liked
                
                # Get comments for this article
                comments = self.db.query(NewsArticleComment).filter(
                    NewsArticleComment.article_id == article.id
                ).order_by(desc(NewsArticleComment.created_at)).all()
                
                # Convert comments to response format
                article_dict['comments'] = [
                    {
                        'id': comment.id,
                        'content': comment.content,
                        'author': f"{comment.user.first_name} {comment.user.last_name}",
                        'posted_date_time': comment.created_at,
                        'user_id': comment.user_id
                    }
                    for comment in comments
                ]
                
                article_responses.append(article_dict)
            
            return {
                'items': article_responses,
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"Error getting news articles: {e}")
            raise

    def flip_like(self, article_id: int, current_user: User) -> dict:
        """Like or unlike an article"""
        try:
            article = self.db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            if not article:
                raise ValueError(f"Article with id {article_id} not found")
            
            # Check if user already liked the article
            existing_like = self.db.query(article_likes).filter(
                article_likes.c.user_id == current_user.id,
                article_likes.c.article_id == article_id
            ).first()
            
            if existing_like:
                # Unlike
                self.db.execute(
                    article_likes.delete().where(
                        (article_likes.c.user_id == current_user.id) &
                        (article_likes.c.article_id == article_id)
                    )
                )
                article.like_count = max(0, article.like_count - 1)
                liked = False
            else:
                # Like
                self.db.execute(
                    article_likes.insert().values(
                        user_id=current_user.id,
                        article_id=article_id
                    )
                )
                article.like_count += 1
                liked = True
            
            self.db.commit()
            
            return {
                'article_id': article_id,
                'liked': liked,
                'like_count': article.like_count
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error flipping like: {e}")
            raise

    def add_comment(self, comment_data: NewsArticleCommentCreate, current_user: User) -> dict:
        """Add a comment to an article"""
        try:
            # Verify article exists
            article = self.db.query(NewsArticle).filter(NewsArticle.id == comment_data.article_id).first()
            if not article:
                raise ValueError(f"Article with id {comment_data.article_id} not found")
            
            # Create comment
            comment = NewsArticleComment(
                content=comment_data.content,
                user_id=current_user.id,
                article_id=comment_data.article_id
            )
            
            self.db.add(comment)
            
            # Update comment count
            article.comment_count += 1
            
            self.db.commit()
            self.db.refresh(comment)
            
            # Return comment response
            return {
                'id': comment.id,
                'content': comment.content,
                'author': f"{current_user.first_name} {current_user.last_name}",
                'posted_date_time': comment.created_at,
                'user_id': current_user.id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding comment: {e}")
            raise
    def get_news_articles_public(self, page: int = 0, size: int = 10, sort_by: str = "published_at", 
                            symbol: Optional[str] = None) -> dict:
        """Get paginated news articles for public access (no user required)"""
        try:
            # Build query
            query = self.db.query(NewsArticle)
            
            # Filter by symbol if provided
            if symbol:
                query = query.filter(NewsArticle.symbol.contains(symbol))
            
            # Apply sorting
            if sort_by == "published_at":
                query = query.order_by(desc(NewsArticle.published_at))
            elif sort_by == "like_count":
                query = query.order_by(desc(NewsArticle.like_count))
            elif sort_by == "sentiment_score":
                query = query.order_by(desc(NewsArticle.sentiment_score))
            else:
                query = query.order_by(desc(NewsArticle.published_at))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = page * size
            articles = query.offset(offset).limit(size).all()
            
            # Convert to response format (no user engagement data)
            article_responses = []
            for article in articles:
                article_dict = {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'summary': article.summary,
                    'source': article.source,
                    'source_type': article.source_type,
                    'author': article.author,
                    'url': article.url,
                    'url_to_image': article.url_to_image,
                    'published_at': article.published_at,
                    'symbol': article.symbol,
                    'sentiment': article.sentiment,
                    'sentiment_score': article.sentiment_score,
                    'topics': article.topics,
                    'like_count': article.like_count,
                    'comment_count': article.comment_count,
                    'liked': False,  # Always false for public access
                    'comments': [],
                    'created_at': article.created_at,
                    'updated_at': article.updated_at
                }
                
                # Get comments for this article (public can see comments)
                comments = self.db.query(NewsArticleComment).filter(
                    NewsArticleComment.article_id == article.id
                ).order_by(desc(NewsArticleComment.created_at)).all()
                
                # Convert comments to response format
                article_dict['comments'] = [
                    {
                        'id': comment.id,
                        'content': comment.content,
                        'author': f"{comment.user.first_name} {comment.user.last_name}",
                        'posted_date_time': comment.created_at,
                        'user_id': comment.user_id
                    }
                    for comment in comments
                ]
                
                article_responses.append(article_dict)
            
            return {
                'items': article_responses,
                'total': total,
                'page': page,
                'size': size,
                'pages': (total + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"Error getting public news articles: {e}")
            raise

    def get_article_by_id(self, article_id: int, current_user: Optional[User] = None) -> dict:
        """Get a specific article by ID (works for both public and authenticated users)"""
        try:
            article = self.db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            if not article:
                raise ValueError(f"Article with id {article_id} not found")
            
            # Build response
            article_dict = {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'summary': article.summary,
                'source': article.source,
                'source_type': article.source_type,
                'author': article.author,
                'url': article.url,
                'url_to_image': article.url_to_image,
                'published_at': article.published_at,
                'symbol': article.symbol,
                'sentiment': article.sentiment,
                'sentiment_score': article.sentiment_score,
                'topics': article.topics,
                'like_count': article.like_count,
                'comment_count': article.comment_count,
                'liked': False,  # Default to false
                'comments': [],
                'created_at': article.created_at,
                'updated_at': article.updated_at
            }
            
            # Check if user liked this article (if authenticated)
            if current_user:
                liked = self.db.query(article_likes).filter(
                    article_likes.c.user_id == current_user.id,
                    article_likes.c.article_id == article.id
                ).first() is not None
                article_dict['liked'] = liked
            
            # Get comments
            comments = self.db.query(NewsArticleComment).filter(
                NewsArticleComment.article_id == article.id
            ).order_by(desc(NewsArticleComment.created_at)).all()
            
            article_dict['comments'] = [
                {
                    'id': comment.id,
                    'content': comment.content,
                    'author': f"{comment.user.first_name} {comment.user.last_name}",
                    'posted_date_time': comment.created_at,
                    'user_id': comment.user_id
                }
                for comment in comments
            ]
            
            return article_dict
            
        except Exception as e:
            logger.error(f"Error getting article {article_id}: {e}")
            raise