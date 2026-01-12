"""
Router pour la récupération des actualités
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List

from app.models.sentiment import NewsArticle
from app.services.news_sentiments import news_service

router = APIRouter()


@router.get("/", response_model=List[NewsArticle])
async def get_financial_news(
    query: str = Query(default="stock market OR finance OR trading", description="Requête de recherche"),
    language: str = Query(default="en", description="Langue des articles"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre d'articles")
):
    """
    Récupère les actualités financières
    
    Args:
        query: Requête de recherche
        language: Langue des articles
        limit: Nombre d'articles à récupérer
        
    Returns:
        Liste d'articles de presse financière
    """
    try:
        articles = await news_service.fetch_financial_news(
            query=query,
            language=language,
            page_size=limit
        )
        
        if not articles:
            raise HTTPException(status_code=404, detail="Aucune actualité trouvée")
        
        return articles
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/headlines", response_model=List[NewsArticle])
async def get_top_headlines(
    category: str = Query(default="business", description="Catégorie d'actualités"),
    country: str = Query(default="us", description="Code pays (us, fr, uk, etc.)"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre d'articles")
):
    """
    Récupère les gros titres d'actualités
    
    Args:
        category: Catégorie (business, technology, etc.)
        country: Code pays
        limit: Nombre d'articles
        
    Returns:
        Liste des gros titres
    """
    try:
        articles = await news_service.fetch_top_headlines(
            category=category,
            country=country,
            page_size=limit
        )
        
        if not articles:
            raise HTTPException(status_code=404, detail="Aucune actualité trouvée")
        
        return articles
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/symbol/{symbol}", response_model=List[NewsArticle])
async def get_news_by_symbol(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50, description="Nombre d'articles")
):
    """
    Récupère les actualités pour un symbole boursier spécifique
    
    Args:
        symbol: Symbole boursier (ex: AAPL, MSFT, BTC)
        limit: Nombre d'articles
        
    Returns:
        Liste d'articles concernant le symbole
    """
    try:
        articles = await news_service.fetch_news_by_symbol(
            symbol=symbol,
            page_size=limit
        )
        
        if not articles:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune actualité trouvée pour {symbol}"
            )
        
        return articles
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
