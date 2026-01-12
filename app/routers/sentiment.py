"""
Router pour l'analyse des sentiments
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime

from app.models.sentiment import (
    SentimentRequest,
    SentimentResponse,
    SentimentScore,
    SentimentAnalysis,
    MarketSentimentSummary
)
from app.services.news_sentiments.news_service import news_service
from app.services.news_sentiments.sentiment_analyzer import sentiment_analyzer

router = APIRouter()


@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyse le sentiment d'un texte donné
    
    Args:
        request: Texte à analyser
        
    Returns:
        Résultat de l'analyse avec sentiment et mots-clés
    """
    try:
        sentiment = sentiment_analyzer.analyze_text(request.text)
        keywords = sentiment_analyzer.extract_keywords(request.text)
        
        return SentimentResponse(
            text=request.text,
            sentiment=sentiment,
            keywords=keywords,
            processed_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")


@router.get("/market-summary", response_model=MarketSentimentSummary)
async def get_market_sentiment_summary(
    query: str = Query(default="stock market OR finance OR trading", description="Requête de recherche"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre d'articles à analyser")
):
    """
    Obtient un résumé du sentiment global du marché basé sur les actualités récentes
    
    Args:
        query: Requête de recherche pour les actualités
        limit: Nombre d'articles à analyser
        
    Returns:
        Résumé du sentiment du marché avec statistiques
    """
    try:
        print(f"\n📊 Market Summary Request - Query: {query}, Limit: {limit}")
        
        # Récupération des actualités
        articles = await news_service.fetch_financial_news(query=query, page_size=limit)
        print(f"✅ Fetched {len(articles)} articles")
        
        if not articles:
            print("⚠️ No articles found")
            raise HTTPException(status_code=404, detail="Aucune actualité trouvée")
        
        # Analyse des sentiments
        _, summary = sentiment_analyzer.analyze_multiple_articles(articles)
        print(f"✅ Analysis complete - Positive: {summary.positive_count}, Neutral: {summary.neutral_count}, Negative: {summary.negative_count}")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in market-summary: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/analyze-news", response_model=List[SentimentAnalysis])
async def analyze_news_sentiment(
    query: str = Query(default="stock market OR finance", description="Requête de recherche"),
    limit: int = Query(default=10, ge=1, le=50, description="Nombre d'articles")
):
    """
    Analyse le sentiment de plusieurs articles d'actualités
    
    Args:
        query: Requête de recherche
        limit: Nombre d'articles à analyser
        
    Returns:
        Liste des analyses de sentiment pour chaque article
    """
    try:
        print(f"\n📰 Analyze News Request - Query: {query}, Limit: {limit}")
        
        # Récupération des actualités
        articles = await news_service.fetch_financial_news(query=query, page_size=limit)
        print(f"✅ Fetched {len(articles)} articles")
        
        if not articles:
            print("⚠️ No articles found")
            raise HTTPException(status_code=404, detail="Aucune actualité trouvée")
        
        # Analyse des sentiments
        analyses, _ = sentiment_analyzer.analyze_multiple_articles(articles)
        print(f"✅ Analysis complete - {len(analyses)} analyses returned")
        
        return analyses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in analyze-news: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/symbol/{symbol}", response_model=List[SentimentAnalysis])
async def analyze_symbol_sentiment(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50, description="Nombre d'articles")
):
    """
    Analyse le sentiment des actualités pour un symbole boursier spécifique
    
    Args:
        symbol: Symbole boursier (ex: AAPL, MSFT)
        limit: Nombre d'articles à analyser
        
    Returns:
        Liste des analyses de sentiment pour le symbole
    """
    try:
        # Récupération des actualités pour le symbole
        articles = await news_service.fetch_news_by_symbol(symbol=symbol, page_size=limit)
        
        if not articles:
            raise HTTPException(
                status_code=404, 
                detail=f"Aucune actualité trouvée pour {symbol}"
            )
        
        # Analyse des sentiments
        analyses, _ = sentiment_analyzer.analyze_multiple_articles(articles)
        
        return analyses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
