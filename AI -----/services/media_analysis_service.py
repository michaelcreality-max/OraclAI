"""
Media & News Analysis Service
Sentiment analysis from news, social media, and alternative sources
"""

import logging
import re
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

log = logging.getLogger(__name__)


class SentimentType(Enum):
    """Sentiment classification"""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


@dataclass
class NewsArticle:
    """News article data"""
    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    author: Optional[str] = None
    sentiment_score: float = 0.0  # -1.0 to 1.0
    sentiment_label: str = "neutral"
    relevance_score: float = 0.0  # 0 to 1
    entities: List[str] = field(default_factory=list)


@dataclass
class SentimentAnalysis:
    """Aggregated sentiment analysis"""
    symbol: str
    overall_sentiment: str
    sentiment_score: float
    confidence: float
    article_count: int
    bullish_articles: int
    bearish_articles: int
    key_topics: List[str]
    risk_indicators: List[str]
    opportunity_indicators: List[str]
    last_updated: datetime


class MediaAnalysisService:
    """
    Media and news sentiment analysis service
    
    Features:
    - NLP-based sentiment scoring
    - Named entity recognition for stocks
    - Topic extraction
    - Risk/opportunity detection
    - Aggregate sentiment trends
    """
    
    # Sentiment lexicons
    BULLISH_WORDS = [
        'surge', 'rally', 'boom', 'breakthrough', 'record high', 'soar', 'jump',
        'beat', 'exceeds', 'outperform', 'strong', 'growth', 'profit', 'gain',
        'upgrade', 'buy', 'bullish', 'momentum', 'breakout', ' ATH', 'all-time',
        'partnership', 'expansion', 'innovation', 'success', 'launch', 'approve'
    ]
    
    BEARISH_WORDS = [
        'crash', 'plunge', 'drop', 'decline', 'fall', 'bearish', 'sell', 'downgrade',
        'miss', 'disappoint', 'weak', 'loss', 'decline', 'concern', 'worry', 'risk',
        'investigation', 'lawsuit', 'recall', 'layoff', 'cut', 'debt', 'bankruptcy',
        'selloff', 'correction', 'support', 'low', 'dump', 'short'
    ]
    
    RISK_INDICATORS = [
        'investigation', 'lawsuit', 'SEC', 'audit', 'irregularities', 'fraud',
        'recall', 'safety', 'breach', 'hack', 'data loss', 'CEO departure',
        'earnings miss', 'guidance cut', 'downgrade', 'debt', 'default'
    ]
    
    OPPORTUNITY_INDICATORS = [
        'partnership', 'contract', 'deal', 'acquisition', 'merger', 'expansion',
        'new market', 'product launch', 'FDA approval', 'patent', 'innovation',
        'earnings beat', 'guidance raise', 'upgrade', 'buyback', 'dividend'
    ]
    
    def __init__(self):
        self.article_cache: Dict[str, List[NewsArticle]] = defaultdict(list)
        self.sentiment_history: Dict[str, List[Dict]] = defaultdict(list)
        self.symbol_mentions: Dict[str, int] = defaultdict(int)
        log.info("MediaAnalysisService initialized")
    
    def analyze_sentiment(self, symbol: str, articles: Optional[List[Dict]] = None) -> SentimentAnalysis:
        """
        Analyze media sentiment for a symbol
        
        Args:
            symbol: Stock symbol
            articles: Optional list of article dicts with 'title', 'content', 'source', 'published_at'
            
        Returns:
            SentimentAnalysis with aggregated scores
        """
        # If articles provided, process them
        if articles:
            processed = self._process_articles(symbol, articles)
            self.article_cache[symbol] = processed
        
        # Get cached articles for symbol
        cached = self.article_cache.get(symbol, [])
        
        if not cached:
            return SentimentAnalysis(
                symbol=symbol,
                overall_sentiment="neutral",
                sentiment_score=0.0,
                confidence=0.0,
                article_count=0,
                bullish_articles=0,
                bearish_articles=0,
                key_topics=[],
                risk_indicators=[],
                opportunity_indicators=[],
                last_updated=datetime.now()
            )
        
        # Calculate aggregate metrics
        scores = [a.sentiment_score for a in cached]
        avg_score = sum(scores) / len(scores)
        
        # Count sentiment categories
        bullish = sum(1 for s in scores if s > 0.2)
        bearish = sum(1 for s in scores if s < -0.2)
        neutral = len(scores) - bullish - bearish
        
        # Extract key topics
        all_topics = []
        for article in cached:
            all_topics.extend(article.entities)
        key_topics = self._extract_top_topics(all_topics, n=5)
        
        # Detect risks and opportunities
        risks = self._detect_risks(cached)
        opportunities = self._detect_opportunities(cached)
        
        # Determine overall sentiment
        if avg_score > 0.5:
            overall = SentimentType.VERY_BULLISH.value
        elif avg_score > 0.2:
            overall = SentimentType.BULLISH.value
        elif avg_score < -0.5:
            overall = SentimentType.VERY_BEARISH.value
        elif avg_score < -0.2:
            overall = SentimentType.BEARISH.value
        else:
            overall = SentimentType.NEUTRAL.value
        
        # Calculate confidence based on article count and agreement
        agreement = 1.0 - (np.std(scores) if len(scores) > 1 else 0)
        confidence = min(len(cached) / 10, 1.0) * (0.5 + 0.5 * agreement)
        
        analysis = SentimentAnalysis(
            symbol=symbol,
            overall_sentiment=overall,
            sentiment_score=avg_score,
            confidence=confidence,
            article_count=len(cached),
            bullish_articles=bullish,
            bearish_articles=bearish,
            key_topics=key_topics,
            risk_indicators=risks,
            opportunity_indicators=opportunities,
            last_updated=datetime.now()
        )
        
        # Store in history
        self.sentiment_history[symbol].append({
            'timestamp': datetime.now(),
            'score': avg_score,
            'articles': len(cached)
        })
        
        return analysis
    
    def _process_articles(self, symbol: str, articles: List[Dict]) -> List[NewsArticle]:
        """Process raw articles into NewsArticle objects"""
        processed = []
        
        for article in articles:
            try:
                title = article.get('title', '')
                content = article.get('content', '')
                source = article.get('source', 'unknown')
                
                # Parse date
                pub_date = article.get('published_at')
                if isinstance(pub_date, str):
                    try:
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    except:
                        pub_date = datetime.now()
                elif not isinstance(pub_date, datetime):
                    pub_date = datetime.now()
                
                # Skip articles older than 7 days
                if (datetime.now() - pub_date).days > 7:
                    continue
                
                # Calculate sentiment
                sentiment_score = self._calculate_sentiment(title, content)
                sentiment_label = self._score_to_label(sentiment_score)
                
                # Extract entities
                entities = self._extract_entities(title + ' ' + content)
                
                # Calculate relevance to symbol
                relevance = self._calculate_relevance(symbol, title + ' ' + content)
                
                news_article = NewsArticle(
                    title=title,
                    content=content[:500],  # Truncate for storage
                    source=source,
                    published_at=pub_date,
                    url=article.get('url'),
                    author=article.get('author'),
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label,
                    relevance_score=relevance,
                    entities=entities
                )
                
                processed.append(news_article)
                
            except Exception as e:
                log.warning(f"Failed to process article: {e}")
                continue
        
        return processed
    
    def _calculate_sentiment(self, title: str, content: str) -> float:
        """Calculate sentiment score from -1.0 (bearish) to 1.0 (bullish)"""
        text = (title + ' ' + content).lower()
        
        # Count bullish and bearish words
        bullish_count = sum(1 for word in self.BULLISH_WORDS if word in text)
        bearish_count = sum(1 for word in self.BEARISH_WORDS if word in text)
        
        # Title has more weight (2x)
        title_lower = title.lower()
        bullish_count += sum(1 for word in self.BULLISH_WORDS if word in title_lower)
        bearish_count += sum(1 for word in self.BEARISH_WORDS if word in title_lower)
        
        # Calculate score
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        # Normalize to -1 to 1
        score = (bullish_count - bearish_count) / total
        
        # Boost for strong signals
        if bullish_count >= 3:
            score = min(score * 1.3, 1.0)
        if bearish_count >= 3:
            score = max(score * 1.3, -1.0)
        
        return score
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract relevant entities (topics, companies, etc.)"""
        entities = []
        
        # Look for common financial entities
        financial_terms = [
            'earnings', 'revenue', 'profit', 'guidance', 'dividend',
            'FDA', 'clinical trial', 'patent', 'lawsuit', 'merger',
            'acquisition', 'partnership', 'contract', 'expansion',
            'AI', 'machine learning', 'cloud', 'cybersecurity',
            'semiconductor', 'EV', 'electric vehicle', 'battery',
            'oil', 'gas', 'energy', 'renewable'
        ]
        
        text_lower = text.lower()
        for term in financial_terms:
            if term in text_lower:
                entities.append(term)
        
        return entities
    
    def _calculate_relevance(self, symbol: str, text: str) -> float:
        """Calculate how relevant article is to symbol"""
        text_lower = text.lower()
        symbol_lower = symbol.lower()
        
        # Direct mention
        if symbol_lower in text_lower:
            return 1.0
        
        # Company name variations could be checked here
        # For now, use entity density as proxy
        words = text_lower.split()
        if not words:
            return 0.0
        
        # Check for ticker patterns
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        tickers = re.findall(ticker_pattern, text)
        
        # Higher relevance if fewer tickers mentioned (more focused)
        if tickers:
            focus_score = 1.0 / len(tickers)
            return min(focus_score, 1.0)
        
        return 0.5
    
    def _detect_risks(self, articles: List[NewsArticle]) -> List[str]:
        """Detect risk indicators in articles"""
        risks = []
        
        all_text = ' '.join([a.title + ' ' + a.content for a in articles]).lower()
        
        for risk in self.RISK_INDICATORS:
            if risk in all_text:
                risks.append(risk)
        
        return risks[:5]  # Top 5 risks
    
    def _detect_opportunities(self, articles: List[NewsArticle]) -> List[str]:
        """Detect opportunity indicators in articles"""
        opportunities = []
        
        all_text = ' '.join([a.title + ' ' + a.content for a in articles]).lower()
        
        for opp in self.OPPORTUNITY_INDICATORS:
            if opp in all_text:
                opportunities.append(opp)
        
        return opportunities[:5]  # Top 5 opportunities
    
    def _extract_top_topics(self, topics: List[str], n: int = 5) -> List[str]:
        """Extract most common topics"""
        if not topics:
            return []
        
        topic_counts = defaultdict(int)
        for topic in topics:
            topic_counts[topic] += 1
        
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:n]]
    
    def _score_to_label(self, score: float) -> str:
        """Convert score to sentiment label"""
        if score > 0.5:
            return "very_bullish"
        elif score > 0.2:
            return "bullish"
        elif score < -0.5:
            return "very_bearish"
        elif score < -0.2:
            return "bearish"
        else:
            return "neutral"
    
    def get_sentiment_trend(self, symbol: str, days: int = 7) -> Dict:
        """Get sentiment trend over time"""
        history = self.sentiment_history.get(symbol, [])
        
        if not history:
            return {'trend': 'insufficient_data', 'change': 0}
        
        # Get recent entries
        cutoff = datetime.now() - timedelta(days=days)
        recent = [h for h in history if h['timestamp'] > cutoff]
        
        if len(recent) < 2:
            return {'trend': 'insufficient_data', 'change': 0}
        
        # Calculate trend
        scores = [h['score'] for h in recent]
        
        # Linear regression slope
        x = range(len(scores))
        slope = np.polyfit(x, scores, 1)[0] if len(scores) > 1 else 0
        
        if slope > 0.1:
            trend = 'improving'
        elif slope < -0.1:
            trend = 'deteriorating'
        else:
            trend = 'stable'
        
        # Calculate change
        if scores:
            change = scores[-1] - scores[0]
        else:
            change = 0
        
        return {
            'trend': trend,
            'change': change,
            'current_score': scores[-1] if scores else 0,
            'data_points': len(recent),
            'avg_score': sum(scores) / len(scores) if scores else 0
        }
    
    def detect_sentiment_extremes(self, symbol: str) -> Dict:
        """Detect if sentiment is at extreme levels (contrarian signals)"""
        analysis = self.analyze_sentiment(symbol)
        
        # Check for extreme fear (buy signal)
        extreme_fear = (
            analysis.sentiment_score < -0.6 and 
            analysis.confidence > 0.5 and
            analysis.bearish_articles > analysis.bullish_articles * 2
        )
        
        # Check for extreme greed (sell signal)
        extreme_greed = (
            analysis.sentiment_score > 0.6 and 
            analysis.confidence > 0.5 and
            analysis.bullish_articles > analysis.bearish_articles * 2
        )
        
        return {
            'extreme_fear': extreme_fear,
            'extreme_greed': extreme_greed,
            'fear_score': max(0, -analysis.sentiment_score) if analysis.sentiment_score < 0 else 0,
            'greed_score': analysis.sentiment_score if analysis.sentiment_score > 0 else 0,
            'contrarian_signal': 'buy' if extreme_fear else 'sell' if extreme_greed else None,
            'confidence': analysis.confidence
        }


# Global instance
media_service = MediaAnalysisService()
