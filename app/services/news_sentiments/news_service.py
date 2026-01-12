"""
Service de récupération des actualités financières
"""
import aiohttp
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from app.models.sentiment import NewsArticle
from app.config.settings import settings


class NewsService:
    """Service de récupération des actualités financières"""
    
    def __init__(self):
        self.news_api_key = settings.NEWS_API_KEY
        self.base_url = settings.NEWS_API_BASE_URL
        
    async def fetch_financial_news(
        self,
        query: str = "stock market OR finance OR trading",
        language: str = "en",
        page_size: int = 20,
        sort_by: str = "publishedAt"
    ) -> List[NewsArticle]:
        """
        Récupère les actualités financières depuis News API
        
        Args:
            query: Requête de recherche
            language: Langue des articles
            page_size: Nombre d'articles à récupérer
            sort_by: Critère de tri
            
        Returns:
            Liste d'articles de presse
        """
        if not self.news_api_key:
            # Retour de données fictives pour la démo si pas de clé API
            return self._get_mock_news()
        
        try:
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                "language": language,
                "pageSize": page_size,
                "sortBy": sort_by,
                "apiKey": self.news_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_news_articles(data.get("articles", []))
                    else:
                        print(f"Erreur API News: {response.status}")
                        return self._get_mock_news()
                        
        except Exception as e:
            print(f"Erreur lors de la récupération des actualités: {e}")
            return self._get_mock_news()
    
    async def fetch_news_by_symbol(
        self,
        symbol: str,
        page_size: int = 10
    ) -> List[NewsArticle]:
        """
        Récupère les actualités pour un symbole boursier spécifique
        
        Args:
            symbol: Symbole boursier (ex: AAPL, MSFT)
            page_size: Nombre d'articles
            
        Returns:
            Liste d'articles concernant le symbole
        """
        query = f"{symbol} stock OR {symbol} shares"
        return await self.fetch_financial_news(query=query, page_size=page_size)
    
    async def fetch_top_headlines(
        self,
        category: str = "business",
        country: str = "us",
        page_size: int = 20
    ) -> List[NewsArticle]:
        """
        Récupère les gros titres d'actualités
        
        Args:
            category: Catégorie d'actualités
            country: Code pays
            page_size: Nombre d'articles
            
        Returns:
            Liste des gros titres
        """
        if not self.news_api_key:
            return self._get_mock_news()
        
        try:
            url = f"{self.base_url}/top-headlines"
            params = {
                "category": category,
                "country": country,
                "pageSize": page_size,
                "apiKey": self.news_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_news_articles(data.get("articles", []))
                    else:
                        return self._get_mock_news()
                        
        except Exception as e:
            print(f"Erreur: {e}")
            return self._get_mock_news()
    
    def _parse_news_articles(self, articles_data: List[dict]) -> List[NewsArticle]:
        """Parse les données brutes en objets NewsArticle"""
        news_articles = []
        
        for article_data in articles_data:
            try:
                article = NewsArticle(
                    title=article_data.get("title", ""),
                    description=article_data.get("description", ""),
                    content=article_data.get("content", ""),
                    source=article_data.get("source", {}).get("name", "Unknown"),
                    url=article_data.get("url", ""),
                    published_at=datetime.fromisoformat(
                        article_data.get("publishedAt", "").replace("Z", "+00:00")
                    ),
                    author=article_data.get("author"),
                    image_url=article_data.get("urlToImage")
                )
                news_articles.append(article)
            except Exception as e:
                print(f"Erreur parsing article: {e}")
                continue
        
        return news_articles
    
    def _get_mock_news(self) -> List[NewsArticle]:
        """Retourne des données d'actualités fictives pour la démo"""
        now = datetime.now()
        
        mock_articles = [
            NewsArticle(
                title="Tech Stocks Rally on Strong Earnings Reports",
                description="Major technology companies reported better-than-expected earnings, driving market optimism.",
                content="Technology stocks surged today as several major companies exceeded analyst expectations...",
                source="Financial Times",
                url="https://example.com/tech-rally",
                published_at=now - timedelta(hours=2),
                author="John Doe",
                image_url="https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3"
            ),
            NewsArticle(
                title="Federal Reserve Signals Potential Rate Changes",
                description="The Fed chairman hinted at upcoming monetary policy adjustments in today's speech.",
                content="In a closely watched address, the Federal Reserve chairman discussed the current economic outlook...",
                source="Bloomberg",
                url="https://example.com/fed-rates",
                published_at=now - timedelta(hours=5),
                author="Jane Smith",
                image_url="https://images.unsplash.com/photo-1526304640581-d334cdbbf45e"
            ),
            NewsArticle(
                title="Global Markets Mixed Amid Economic Uncertainty",
                description="International markets show varied performance as investors weigh economic indicators.",
                content="Global equity markets displayed mixed signals today, with European indices...",
                source="Reuters",
                url="https://example.com/global-markets",
                published_at=now - timedelta(hours=8),
                author="Market Desk",
                image_url="https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f"
            ),
            NewsArticle(
                title="Oil Prices Surge on Supply Concerns",
                description="Crude oil futures jumped following reports of production disruptions.",
                content="Energy markets reacted strongly to news of potential supply chain issues...",
                source="CNBC",
                url="https://example.com/oil-prices",
                published_at=now - timedelta(hours=12),
                author="Energy Reporter",
                image_url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23"
            ),
            NewsArticle(
                title="Cryptocurrency Market Faces Regulatory Scrutiny",
                description="New regulations proposed for digital asset trading platforms.",
                content="Regulators announced plans to introduce comprehensive oversight of cryptocurrency exchanges...",
                source="Wall Street Journal",
                url="https://example.com/crypto-regulation",
                published_at=now - timedelta(hours=15),
                author="Crypto Analyst",
                image_url="https://images.unsplash.com/photo-1621761191319-c6fb62004040"
            ),
            NewsArticle(
                title="Emerging Markets Show Strong Growth Potential",
                description="Analysts predict robust economic expansion in developing economies.",
                content="Investment strategists are increasingly bullish on emerging market opportunities...",
                source="Financial Express",
                url="https://example.com/emerging-markets",
                published_at=now - timedelta(hours=18),
                author="Market Analyst",
                image_url="https://images.unsplash.com/photo-1559526324-4b87b5e36e44"
            ),
            NewsArticle(
                title="Corporate Mergers Drive Market Activity",
                description="Major acquisition announcements boost investor sentiment.",
                content="Several high-profile merger and acquisition deals were announced this week...",
                source="Business Insider",
                url="https://example.com/mergers",
                published_at=now - timedelta(hours=24),
                author="M&A Desk",
                image_url="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40"
            ),
            NewsArticle(
                title="Banking Sector Faces Digital Transformation Pressure",
                description="Traditional banks accelerate technology adoption to compete with fintech.",
                content="The banking industry is undergoing rapid digital transformation as fintech companies...",
                source="Financial Review",
                url="https://example.com/banking-digital",
                published_at=now - timedelta(hours=30),
                author="Banking Reporter",
                image_url="https://images.unsplash.com/photo-1563013544-824ae1b704d3"
            ),
            NewsArticle(
                title="Tesla Stock Surges on Record Deliveries",
                description="Tesla announces record-breaking vehicle deliveries for the quarter.",
                content="Electric vehicle maker Tesla reported unprecedented delivery numbers, exceeding market expectations...",
                source="MarketWatch",
                url="https://example.com/tesla-deliveries",
                published_at=now - timedelta(hours=3),
                author="Auto Industry Reporter",
                image_url="https://images.unsplash.com/photo-1560958089-b8a1929cea89"
            ),
            NewsArticle(
                title="Apple Unveils AI-Powered Products",
                description="Apple introduces new lineup with advanced artificial intelligence features.",
                content="In a major product launch event, Apple showcased its latest AI-enhanced devices...",
                source="TechCrunch",
                url="https://example.com/apple-ai",
                published_at=now - timedelta(hours=6),
                author="Tech Reporter",
                image_url="https://images.unsplash.com/photo-1591337676887-a217a6970a8a"
            ),
            NewsArticle(
                title="Microsoft Cloud Revenue Beats Expectations",
                description="Microsoft's Azure cloud platform drives strong quarterly results.",
                content="Microsoft reported robust growth in its cloud computing division, surpassing analyst forecasts...",
                source="Forbes",
                url="https://example.com/microsoft-cloud",
                published_at=now - timedelta(hours=9),
                author="Cloud Computing Analyst",
                image_url="https://images.unsplash.com/photo-1633356122544-f134324a6cee"
            ),
            NewsArticle(
                title="Amazon Expands into Healthcare Market",
                description="E-commerce giant announces new healthcare services initiative.",
                content="Amazon is making a significant push into the healthcare sector with new digital health offerings...",
                source="Healthcare Today",
                url="https://example.com/amazon-healthcare",
                published_at=now - timedelta(hours=11),
                author="Healthcare Reporter",
                image_url="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d"
            ),
            NewsArticle(
                title="Google AI Breakthrough in Medical Diagnostics",
                description="Google's AI system demonstrates superior accuracy in disease detection.",
                content="Google researchers unveiled an artificial intelligence system that outperforms doctors in diagnosing...",
                source="Medical AI Journal",
                url="https://example.com/google-medical-ai",
                published_at=now - timedelta(hours=14),
                author="AI Research Team",
                image_url="https://images.unsplash.com/photo-1576091160550-2173dba999ef"
            ),
            NewsArticle(
                title="Bitcoin Hits New All-Time High",
                description="Leading cryptocurrency reaches unprecedented valuation.",
                content="Bitcoin soared to a new record high as institutional adoption continues to accelerate...",
                source="CoinDesk",
                url="https://example.com/bitcoin-ath",
                published_at=now - timedelta(hours=4),
                author="Crypto Reporter",
                image_url="https://images.unsplash.com/photo-1518546305927-5a555bb7020d"
            ),
            NewsArticle(
                title="NVIDIA AI Chips See Unprecedented Demand",
                description="GPU manufacturer reports record orders for AI processors.",
                content="NVIDIA's latest AI-focused graphics processors are experiencing massive demand from tech companies...",
                source="Semiconductor News",
                url="https://example.com/nvidia-ai-chips",
                published_at=now - timedelta(hours=7),
                author="Hardware Analyst",
                image_url="https://images.unsplash.com/photo-1591488320449-011701bb6704"
            ),
            NewsArticle(
                title="AI Startups Attract Record Venture Funding",
                description="Artificial intelligence companies raise billions in new investment.",
                content="Venture capital firms poured unprecedented amounts into AI startups this quarter...",
                source="VentureBeat",
                url="https://example.com/ai-funding",
                published_at=now - timedelta(hours=10),
                author="VC Reporter",
                image_url="https://images.unsplash.com/photo-1559526324-4b87b5e36e44"
            ),
            NewsArticle(
                title="Renewable Energy Stocks Rally on Policy Support",
                description="Green energy companies surge on new government initiatives.",
                content="Renewable energy stocks jumped following the announcement of expanded clean energy subsidies...",
                source="Green Finance",
                url="https://example.com/renewable-rally",
                published_at=now - timedelta(hours=16),
                author="Energy Markets",
                image_url="https://images.unsplash.com/photo-1509391366360-2e959784a276"
            ),
            NewsArticle(
                title="Tesla Autopilot Receives Major Software Update",
                description="Tesla rolls out enhanced self-driving capabilities to fleet.",
                content="The electric vehicle manufacturer deployed a significant software update improving autonomous driving...",
                source="Automotive News",
                url="https://example.com/tesla-autopilot",
                published_at=now - timedelta(hours=19),
                author="Auto Tech Reporter",
                image_url="https://images.unsplash.com/photo-1617704548623-340376564e68"
            ),
            NewsArticle(
                title="Apple Services Revenue Reaches New Milestone",
                description="iPhone maker's subscription services drive profit growth.",
                content="Apple's services division including App Store and Apple Music reached record revenue levels...",
                source="Apple Insider",
                url="https://example.com/apple-services",
                published_at=now - timedelta(hours=22),
                author="Apple Analyst",
                image_url="https://images.unsplash.com/photo-1517694712202-14dd9538aa97"
            ),
            NewsArticle(
                title="AI Technology Transforms Financial Trading",
                description="Machine learning algorithms revolutionize investment strategies.",
                content="Artificial intelligence is fundamentally changing how financial markets operate with algorithmic trading...",
                source="Quant Finance",
                url="https://example.com/ai-trading",
                published_at=now - timedelta(hours=25),
                author="Algorithmic Trading Desk",
                image_url="https://images.unsplash.com/photo-1551288049-bebda4e38f71"
            )
        ]
        
        return mock_articles


# Instance singleton
news_service = NewsService()
