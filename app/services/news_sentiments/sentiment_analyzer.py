"""
Service d'analyse des sentiments utilisant l'IA
Utilise des modèles de NLP pour analyser les sentiments des actualités financières
"""
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Tuple
import re
from datetime import datetime
import numpy as np

from app.models.sentiment import (
    SentimentScore, 
    SentimentLabel, 
    NewsArticle,
    SentimentAnalysis,
    MarketSentimentSummary,
    TradingSignal,
    RiskLevel
)
from app.config.settings import settings


class SentimentAnalyzer:
    """Analyseur de sentiments basé sur l'IA"""
    
    def __init__(self):
        """Initialisation du modèle de sentiment"""
        self.model_name = "ProsusAI/finbert"  # FinBERT spécialisé pour les textes financiers
        self._sentiment_pipeline = None
        self._tokenizer = None
        
        # Mots-clés financiers avec catégories et pondérations
        self.sentiment_keywords = {
            'positive_strong': ['surge', 'soar', 'boom', 'breakthrough', 'record', 'rally', 'bullish', 'outperform', 'growth', 'profit', 'gains'],
            'positive_moderate': ['rise', 'increase', 'improve', 'advance', 'recover', 'optimistic', 'positive', 'confident'],
            'negative_strong': ['plunge', 'crash', 'collapse', 'crisis', 'disaster', 'panic', 'bearish', 'recession', 'bankruptcy'],
            'negative_moderate': ['decline', 'drop', 'fall', 'concern', 'weak', 'uncertainty', 'risk', 'volatile'],
            'neutral': ['stable', 'unchanged', 'flat', 'steady', 'maintain']
        }
        
        # Entités financières importantes pour tracking
        self.market_entities = {
            'companies': ['Tesla', 'Apple', 'Microsoft', 'Amazon', 'Google', 'Meta', 'NVIDIA', 'Netflix'],
            'sectors': ['Technology', 'Healthcare', 'Finance', 'Energy', 'AI', 'Cloud', 'Crypto'],
            'indicators': ['S&P 500', 'Dow Jones', 'NASDAQ', 'Bitcoin', 'Oil', 'Gold'],
            'events': ['Fed', 'Earnings', 'IPO', 'Merger', 'Acquisition']
        }
    
    @property
    def sentiment_pipeline(self):
        """Lazy loading du pipeline de sentiment"""
        if self._sentiment_pipeline is None:
            try:
                # Utilisation d'un modèle pré-entraîné pour l'analyse de sentiment
                self._sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    tokenizer=self.model_name,
                    device=-1  # CPU, mettre 0 pour GPU
                )
            except Exception as e:
                print(f"Erreur lors du chargement du modèle: {e}")
                # Fallback vers un modèle plus léger
                self._sentiment_pipeline = pipeline("sentiment-analysis")
        return self._sentiment_pipeline
    
    def calculate_keyword_sentiment(self, text: str) -> Tuple[float, Dict[str, int]]:
        """
        Analyse le sentiment basé sur les mots-clés avec pondération
        
        Returns:
            Tuple (score, compteurs par catégorie)
        """
        text_lower = text.lower()
        scores = {
            'positive_strong': 0,
            'positive_moderate': 0,
            'negative_strong': 0,
            'negative_moderate': 0,
            'neutral': 0
        }
        
        for category, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                count = text_lower.count(keyword)
                scores[category] += count
        
        # Calcul du score pondéré (-1 à +1)
        weighted_score = (
            scores['positive_strong'] * 2.0 +
            scores['positive_moderate'] * 1.0 -
            scores['negative_moderate'] * 1.0 -
            scores['negative_strong'] * 2.0
        )
        
        total_keywords = sum(scores.values())
        if total_keywords > 0:
            normalized_score = weighted_score / (total_keywords * 2)  # Normaliser entre -1 et 1
        else:
            normalized_score = 0.0
        
        return normalized_score, scores
    
    def analyze_text(self, text: str) -> SentimentScore:
        """
        Analyse multi-factorielle du sentiment:
        - FinBERT AI (70%)
        - Keyword Analysis (20%)
        - Text Structure (10%)
        
        Args:
            text: Texte à analyser
            
        Returns:
            SentimentScore avec le label et le score de confiance
        """
        if not text or len(text.strip()) == 0:
            return SentimentScore(label=SentimentLabel.NEUTRAL, score=0.5)
        
        # Limitation de la taille du texte pour le modèle
        text_trimmed = text[:512]
        
        try:
            # 1. Analyse FinBERT (70%)
            result = self.sentiment_pipeline(text_trimmed)[0]
            
            # Conversion du label en notre format
            label_map = {
                'POSITIVE': SentimentLabel.POSITIVE,
                'NEGATIVE': SentimentLabel.NEGATIVE,
                'NEUTRAL': SentimentLabel.NEUTRAL
            }
            
            ai_label = label_map.get(result['label'].upper(), SentimentLabel.NEUTRAL)
            ai_score = result['score']
            
            # 2. Analyse par mots-clés (20%)
            keyword_score, keyword_counts = self.calculate_keyword_sentiment(text)
            
            # 3. Analyse structurelle (10%): ponctuation, longueur
            exclamation_count = text.count('!')
            question_count = text.count('?')
            structure_boost = min(exclamation_count * 0.05, 0.1)  # Max 10% boost
            
            # Combinaison pondérée des scores
            # Convertir ai_label en score numérique
            ai_numeric = 1.0 if ai_label == SentimentLabel.POSITIVE else (-1.0 if ai_label == SentimentLabel.NEGATIVE else 0.0)
            
            combined_score = (
                ai_numeric * 0.7 +  # 70% FinBERT
                keyword_score * 0.2 +  # 20% Keywords
                structure_boost * 0.1  # 10% Structure
            )
            
            # Détermination du label final
            if combined_score > 0.15:
                final_label = SentimentLabel.POSITIVE
                confidence = min(abs(combined_score) * ai_score, 1.0)
            elif combined_score < -0.15:
                final_label = SentimentLabel.NEGATIVE
                confidence = min(abs(combined_score) * ai_score, 1.0)
            else:
                final_label = SentimentLabel.NEUTRAL
                confidence = 1.0 - abs(combined_score)
            
            # Ajustement pour le seuil neutre
            if confidence < settings.SENTIMENT_THRESHOLD_POSITIVE and final_label == SentimentLabel.POSITIVE:
                final_label = SentimentLabel.NEUTRAL
            elif confidence < settings.SENTIMENT_THRESHOLD_NEGATIVE and final_label == SentimentLabel.NEGATIVE:
                final_label = SentimentLabel.NEUTRAL
            
            return SentimentScore(label=final_label, score=confidence)
            
        except Exception as e:
            print(f"Erreur lors de l'analyse: {e}")
            return SentimentScore(label=SentimentLabel.NEUTRAL, score=0.5)
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extrait les mots-clés financiers importants du texte avec détection d'entités
        
        Args:
            text: Texte à analyser
            top_n: Nombre de mots-clés à retourner
            
        Returns:
            Liste des mots-clés les plus pertinents
        """
        text_lower = text.lower()
        keywords = []
        
        # Extraction des entités financières importantes
        for category, entities in self.market_entities.items():
            for entity in entities:
                if entity.lower() in text_lower:
                    keywords.append(entity)
        
        # Extraction des symboles boursiers (ex: AAPL, MSFT)
        stock_symbols = re.findall(r'\b[A-Z]{2,5}\b', text)
        keywords.extend(stock_symbols[:3])
        
        # Dédupliquer et limiter
        keywords = list(dict.fromkeys(keywords))  # Garde l'ordre et supprime duplicatas
        
        return keywords[:top_n]
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extrait les entités nommées (entreprises, indices) du texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste des entités trouvées
        """
        # Liste d'entreprises et indices communs
        common_entities = [
            'Apple', 'Microsoft', 'Google', 'Amazon', 'Tesla', 'Meta',
            'S&P 500', 'NASDAQ', 'Dow Jones', 'FTSE', 'CAC 40',
            'NYSE', 'Bitcoin', 'Ethereum', 'Federal Reserve', 'ECB'
        ]
        
        entities = []
        for entity in common_entities:
            if entity.lower() in text.lower():
                entities.append(entity)
        
        return entities[:5]
    
    def analyze_article(self, article: NewsArticle) -> SentimentAnalysis:
        """
        Analyse complète d'un article de presse
        
        Args:
            article: Article à analyser
            
        Returns:
            SentimentAnalysis avec sentiment, mots-clés et entités
        """
        # Combinaison du titre et de la description pour l'analyse
        text_to_analyze = f"{article.title}. {article.description or ''}"
        
        sentiment = self.analyze_text(text_to_analyze)
        keywords = self.extract_keywords(text_to_analyze)
        entities = self.extract_entities(text_to_analyze)
        
        return SentimentAnalysis(
            article=article,
            sentiment=sentiment,
            keywords=keywords,
            entities=entities
        )
    
    def analyze_multiple_articles(
        self, 
        articles: List[NewsArticle]
    ) -> Tuple[List[SentimentAnalysis], MarketSentimentSummary]:
        """
        Analyse plusieurs articles et génère un résumé du sentiment du marché
        
        Args:
            articles: Liste d'articles à analyser
            
        Returns:
            Tuple (analyses individuelles, résumé global)
        """
        analyses = [self.analyze_article(article) for article in articles]
        
        # Calcul des statistiques
        positive_count = sum(1 for a in analyses if a.sentiment.label == SentimentLabel.POSITIVE)
        negative_count = sum(1 for a in analyses if a.sentiment.label == SentimentLabel.NEGATIVE)
        neutral_count = sum(1 for a in analyses if a.sentiment.label == SentimentLabel.NEUTRAL)
        
        # Détermination du sentiment global
        total = len(analyses)
        if total == 0:
            overall_sentiment = SentimentLabel.NEUTRAL
            confidence = 0.5
        else:
            sentiment_scores = {
                SentimentLabel.POSITIVE: positive_count / total,
                SentimentLabel.NEGATIVE: negative_count / total,
                SentimentLabel.NEUTRAL: neutral_count / total
            }
            overall_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            confidence = sentiment_scores[overall_sentiment]
        
        # Extraction des sujets tendance
        all_keywords = []
        for analysis in analyses:
            all_keywords.extend(analysis.keywords)
        
        # Comptage des mots-clés les plus fréquents
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        trending_topics = sorted(
            keyword_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        trending_topics = [topic for topic, _ in trending_topics]
        
        # Calcul des indicateurs avancés
        # 1. Momentum du sentiment (évolution)
        sentiment_momentum = (positive_count - negative_count) / total if total > 0 else 0.0
        
        # 2. Indice Fear & Greed (0-100)
        fear_greed = (positive_count / total * 100) if total > 0 else 50.0
        
        # 3. Indice de volatilité (basé sur la diversité des sentiments)
        if total > 0:
            entropy = -(
                (positive_count/total * np.log(positive_count/total + 1e-10)) +
                (negative_count/total * np.log(negative_count/total + 1e-10)) +
                (neutral_count/total * np.log(neutral_count/total + 1e-10))
            )
            volatility_index = entropy / np.log(3) * 100  # Normaliser 0-100
        else:
            volatility_index = 50.0
        
        # 4. Génération du signal de trading basé sur les indicateurs
        trading_signal, risk_level, recommendation = self._generate_trading_signal(
            sentiment_momentum, fear_greed, volatility_index, confidence
        )
        
        summary = MarketSentimentSummary(
            overall_sentiment=overall_sentiment,
            confidence=confidence,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            total_articles=total,
            timestamp=datetime.now(),
            trending_topics=trending_topics,
            sentiment_momentum=sentiment_momentum,
            market_fear_greed=fear_greed,
            volatility_index=volatility_index,
            trading_signal=trading_signal,
            risk_level=risk_level,
            recommendation=recommendation
        )
        
        return analyses, summary
    
    def _generate_trading_signal(
        self, 
        momentum: float, 
        fear_greed: float, 
        volatility: float,
        confidence: float
    ) -> Tuple[TradingSignal, RiskLevel, str]:
        """
        Génère un signal de trading basé sur les indicateurs multiples
        
        Args:
            momentum: Momentum du sentiment (-1 à +1)
            fear_greed: Indice peur/avidité (0-100)
            volatility: Indice de volatilité (0-100)
            confidence: Niveau de confiance (0-1)
            
        Returns:
            Tuple (signal, niveau de risque, recommandation)
        """
        # Détermination du niveau de risque
        if volatility > 70:
            risk_level = RiskLevel.EXTREME
        elif volatility > 50:
            risk_level = RiskLevel.HIGH
        elif volatility > 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Calcul du score composite pour le signal
        # Poids: momentum 40%, fear_greed 40%, volatility inverse 20%
        composite_score = (
            momentum * 0.4 +
            (fear_greed - 50) / 50 * 0.4 +  # Normaliser fear_greed à -1..1
            (1 - volatility / 100) * 0.2  # Volatilité faible = bon signal
        )
        
        # Ajustement selon la confiance
        composite_score *= confidence
        
        # Génération du signal
        if composite_score > 0.5:
            signal = TradingSignal.STRONG_BUY
            recommendation = f"📈 ACHAT FORT recommandé - Sentiment très positif ({momentum*100:.0f}% momentum), confiance élevée. "
            if risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                recommendation += "⚠️ Attention: Volatilité élevée, envisagez des positions progressives."
            else:
                recommendation += "✅ Conditions favorables avec risque contrôlé."
                
        elif composite_score > 0.2:
            signal = TradingSignal.BUY
            recommendation = f"📊 ACHAT suggéré - Sentiment positif modéré ({fear_greed:.0f}/100 Fear&Greed). "
            if volatility > 60:
                recommendation += "Position prudente recommandée compte tenu de la volatilité."
            else:
                recommendation += "Opportunité d'entrée intéressante."
                
        elif composite_score > -0.2:
            signal = TradingSignal.HOLD
            recommendation = f"⏸️ CONSERVER positions - Marché neutre/mixte (momentum: {momentum*100:.0f}%). "
            if volatility > 50:
                recommendation += "Attendre clarification avant nouvelles positions."
            else:
                recommendation += "Surveiller l'évolution des indicateurs."
                
        elif composite_score > -0.5:
            signal = TradingSignal.SELL
            recommendation = f"📉 VENTE suggérée - Sentiment négatif ({fear_greed:.0f}/100 Fear&Greed indique peur). "
            if momentum < -0.3:
                recommendation += "Momentum baissier confirmé, envisager réduction de positions."
            else:
                recommendation += "Prudence recommandée."
                
        else:
            signal = TradingSignal.STRONG_SELL
            recommendation = f"⛔ VENTE FORTE - Sentiment très négatif ({momentum*100:.0f}% momentum). "
            if risk_level == RiskLevel.EXTREME:
                recommendation += "🚨 ALERTE: Volatilité extrême, protégez votre capital."
            else:
                recommendation += "Sortie de positions fortement recommandée."
        
        return signal, risk_level, recommendation


# Instance singleton
sentiment_analyzer = SentimentAnalyzer()
