"""
Router pour l'analyse des tendances du marché
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime, timedelta

from app.models.sentiment import TrendAnalysis, MarketIndicator, SentimentLabel
from app.services.news_sentiments.sentiment_analyzer import sentiment_analyzer
from app.services.news_sentiments.news_service import news_service

router = APIRouter()


@router.get("/sentiment-distribution")
async def get_sentiment_distribution(
    query: str = Query(default="stock market finance", description="Requête de recherche"),
    limit: int = Query(default=50, ge=1, le=100, description="Nombre d'articles")
):
    """
    Récupère la distribution des sentiments pour une requête
    
    Args:
        query: Requête de recherche
        limit: Nombre d'articles à analyser
        
    Returns:
        Distribution des sentiments (positif, négatif, neutre)
    """
    try:
        print(f"\n📈 Sentiment Distribution Request - Query: {query}, Limit: {limit}")
        
        # Récupération des actualités
        articles = await news_service.fetch_financial_news(query=query, page_size=limit)
        print(f"✅ Fetched {len(articles)} articles")
        
        if not articles:
            print("⚠️ No articles, returning zeros")
            return {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "total": 0
            }
        
        # Analyse des sentiments
        analyses, summary = sentiment_analyzer.analyze_multiple_articles(articles)
        print(f"✅ Distribution - P: {summary.positive_count}, N: {summary.neutral_count}, Neg: {summary.negative_count}")
        
        return {
            "positive": summary.positive_count,
            "negative": summary.negative_count,
            "neutral": summary.neutral_count,
            "total": summary.total_articles
        }
        
    except Exception as e:
        print(f"❌ Error in sentiment-distribution: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/emerging", response_model=List[TrendAnalysis])
async def get_emerging_trends(
    limit: int = Query(default=5, ge=1, le=20, description="Nombre de tendances"),
    time_period: str = Query(default="24h", description="Période d'analyse")
):
    """
    Identifie les tendances émergentes basées sur l'analyse des sentiments
    
    Args:
        limit: Nombre de tendances à retourner
        time_period: Période d'analyse (ex: "24h", "7d")
        
    Returns:
        Liste des tendances émergentes avec leur momentum
    """
    try:
        print(f"\n📈 Emerging Trends Request - Limit: {limit}, Period: {time_period}")
        
        # Récupération des actualités récentes
        articles = await news_service.fetch_financial_news(page_size=50)
        print(f"✅ Fetched {len(articles)} articles")
        
        if not articles:
            print("⚠️ No articles available")
            raise HTTPException(status_code=404, detail="Aucune actualité disponible")
        
        # Analyse des sentiments
        analyses, _ = sentiment_analyzer.analyze_multiple_articles(articles)
        print(f"✅ Analyzed {len(analyses)} articles")
        
        # Regroupement par sujet/entité
        topic_sentiments = {}
        
        for analysis in analyses:
            # Utilisation des entités comme sujets
            for entity in analysis.entities:
                if entity not in topic_sentiments:
                    topic_sentiments[entity] = []
                topic_sentiments[entity].append(analysis.sentiment)
        
        print(f"✅ Found {len(topic_sentiments)} unique topics/entities")
        
        # Création des tendances
        trends = []
        for topic, sentiments in topic_sentiments.items():
            if len(sentiments) >= 1:  # Au moins 1 article pour créer une tendance
                # Calcul du momentum (positive minus negative ratio)
                positive_count = sum(1 for s in sentiments if s.label == SentimentLabel.POSITIVE)
                negative_count = sum(1 for s in sentiments if s.label == SentimentLabel.NEGATIVE)
                total = len(sentiments)
                
                momentum = (positive_count - negative_count) / total if total > 0 else 0.0
                
                trend = TrendAnalysis(
                    topic=topic,
                    sentiment_trend=sentiments[:5],  # Top 5 sentiments
                    article_count=len(sentiments),
                    time_period=time_period,
                    momentum=momentum
                )
                trends.append(trend)
        
        # Tri par momentum et nombre d'articles
        trends.sort(key=lambda x: (abs(x.momentum), x.article_count), reverse=True)
        
        print(f"✅ Created {len(trends)} trends, returning top {min(limit, len(trends))}")
        
        return trends[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in emerging trends: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/indicators", response_model=List[MarketIndicator])
async def get_market_indicators():
    """
    Génère des indicateurs de marché basés sur l'analyse des sentiments
    
    Returns:
        Liste des indicateurs de marché influencés par les sentiments
    """
    try:
        # Récupération et analyse des actualités
        articles = await news_service.fetch_financial_news(page_size=30)
        
        if not articles:
            raise HTTPException(status_code=404, detail="Aucune actualité disponible")
        
        analyses, summary = sentiment_analyzer.analyze_multiple_articles(articles)
        
        # Calcul des indicateurs
        indicators = []
        
        # 1. Indicateur de sentiment global (0-100)
        sentiment_score = (summary.positive_count - summary.negative_count) / summary.total_articles * 50 + 50
        indicators.append(MarketIndicator(
            name="Market Sentiment Index",
            value=round(sentiment_score, 2),
            sentiment_influence=summary.confidence,
            timestamp=datetime.now(),
            description="Indice global du sentiment du marché (0=très négatif, 100=très positif)"
        ))
        
        # 2. Indice de peur et d'avidité
        fear_greed = (summary.positive_count / summary.total_articles * 100) if summary.total_articles > 0 else 50
        indicators.append(MarketIndicator(
            name="Fear & Greed Index",
            value=round(fear_greed, 2),
            sentiment_influence=summary.confidence,
            timestamp=datetime.now(),
            description="Indice de peur et d'avidité basé sur les actualités"
        ))
        
        # 3. Volatilité perçue (basée sur la diversité des sentiments)
        volatility = (summary.neutral_count / summary.total_articles * 100) if summary.total_articles > 0 else 0
        indicators.append(MarketIndicator(
            name="Sentiment Volatility",
            value=round(volatility, 2),
            sentiment_influence=1 - summary.confidence,
            timestamp=datetime.now(),
            description="Volatilité perçue basée sur l'incertitude des sentiments"
        ))
        
        # 4. Momentum du marché
        momentum_value = (summary.positive_count - summary.negative_count) / summary.total_articles if summary.total_articles > 0 else 0
        indicators.append(MarketIndicator(
            name="Market Momentum",
            value=round(momentum_value, 3),
            sentiment_influence=summary.confidence,
            timestamp=datetime.now(),
            description="Momentum du marché (-1=très baissier, +1=très haussier)"
        ))
        
        return indicators
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/topic/{topic}", response_model=TrendAnalysis)
async def get_topic_trend(
    topic: str,
    limit: int = Query(default=20, ge=1, le=50, description="Nombre d'articles")
):
    """
    Analyse la tendance pour un sujet spécifique
    
    Args:
        topic: Sujet à analyser (ex: "Bitcoin", "Tesla", "AI")
        limit: Nombre d'articles à analyser
        
    Returns:
        Analyse de tendance pour le sujet
    """
    try:
        # Récupération des actualités sur le sujet
        articles = await news_service.fetch_financial_news(query=topic, page_size=limit)
        
        if not articles:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune actualité trouvée pour '{topic}'"
            )
        
        # Analyse des sentiments
        analyses, _ = sentiment_analyzer.analyze_multiple_articles(articles)
        
        # Extraction des sentiments
        sentiments = [analysis.sentiment for analysis in analyses]
        
        # Calcul du momentum
        positive_count = sum(1 for s in sentiments if s.label == SentimentLabel.POSITIVE)
        negative_count = sum(1 for s in sentiments if s.label == SentimentLabel.NEGATIVE)
        total = len(sentiments)
        
        momentum = (positive_count - negative_count) / total if total > 0 else 0.0
        
        trend = TrendAnalysis(
            topic=topic,
            sentiment_trend=sentiments,
            article_count=len(analyses),
            time_period="recent",
            momentum=momentum
        )
        
        return trend
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
