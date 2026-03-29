"""
Sentiment Analysis Agent
Analyzes market sentiment, news, and social signals - independent stance
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class SentimentStance:
    """Sentiment analysis stance"""
    direction: str  # bullish, bearish, neutral
    conviction: float
    overall_sentiment: str  # positive, neutral, negative
    sentiment_score: float  # -1 to 1
    institutional_sentiment: str  # bullish, neutral, bearish
    retail_sentiment: str  # bullish, neutral, bearish
    analyst_consensus: str  # buy, hold, sell
    news_sentiment: str  # positive, neutral, negative
    social_sentiment: str  # positive, neutral, negative
    key_signals: List[str]
    contrarian_indicators: List[str]


class SentimentAnalysisAgent:
    """
    Sentiment Analysis Agent that evaluates market psychology and positioning.
    Independently determines if sentiment supports bullish or bearish positioning.
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "sentiment_analysis_agent"
        self.max_analysis_time = 60
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any],
                financial_context: Dict[str, Any]) -> SentimentStance:
        """Analyze market sentiment and determine independent stance"""
        log.info(f"SentimentAgent: Analyzing {symbol} sentiment")
        start_time = time.time()
        
        try:
            # Request sentiment data
            analyst_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="analyst_ratings",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            
            institutional_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="institutional_ownership",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            
            short_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="short_interest",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            
            insider_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="insider_trading",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            
            signals = []
            contrarian = []
            
            # 1. Analyst Sentiment
            analyst_sentiment, analyst_score = self._analyze_analyst_sentiment(analyst_data)
            signals.append(f"Analyst consensus: {analyst_sentiment.upper()}")
            
            # 2. Institutional Positioning
            inst_sentiment, inst_score = self._analyze_institutional_sentiment(institutional_data)
            signals.append(f"Institutional sentiment: {inst_sentiment.upper()}")
            
            # 3. Short Interest Analysis
            short_sentiment, short_score = self._analyze_short_sentiment(short_data)
            signals.append(f"Short interest sentiment: {short_sentiment.upper()}")
            
            # 4. Insider Activity
            insider_sentiment, insider_score = self._analyze_insider_sentiment(insider_data)
            signals.append(f"Insider sentiment: {insider_sentiment.upper()}")
            
            # 5. Options Sentiment (implied volatility skew)
            options_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="options_data",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            options_sentiment, options_score = self._analyze_options_sentiment(options_data)
            signals.append(f"Options sentiment: {options_sentiment.upper()}")
            
            # Calculate overall sentiment score
            sentiment_score = (
                analyst_score * 0.30 +
                inst_score * 0.25 +
                short_score * 0.20 +
                insider_score * 0.15 +
                options_score * 0.10
            )
            
            # Determine sentiment classification
            if sentiment_score > 0.3:
                overall_sentiment = "positive"
            elif sentiment_score < -0.3:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
            
            # Determine stance (sentiment can be contrarian)
            # Extreme sentiment can signal reversals
            if sentiment_score > 0.7:
                # Very bullish - potential contrarian sell signal
                direction = "bearish"
                contrarian.append("Extreme bullish sentiment - potential reversal risk")
                conviction = 0.6
            elif sentiment_score > 0.2:
                direction = "bullish"
                conviction = abs(sentiment_score)
            elif sentiment_score < -0.7:
                # Very bearish - potential contrarian buy signal
                direction = "bullish"
                contrarian.append("Extreme bearish sentiment - potential bottom forming")
                conviction = 0.6
            elif sentiment_score < -0.2:
                direction = "bearish"
                conviction = abs(sentiment_score)
            else:
                direction = "neutral"
                conviction = 0.5
            
            # Market context adjustment
            vix = financial_context.get("vix_level", 20)
            if vix > 30 and sentiment_score > 0.5:
                signals.append("High VIX with bullish sentiment - dislocation possible")
                contrarian.append("Fear and optimism coexisting")
            
            analysis_time = time.time() - start_time
            log.info(f"SentimentAgent: {direction} stance (sentiment: {overall_sentiment})")
            
            return SentimentStance(
                direction=direction,
                conviction=conviction,
                overall_sentiment=overall_sentiment,
                sentiment_score=sentiment_score,
                institutional_sentiment=inst_sentiment,
                retail_sentiment=self._estimate_retail_sentiment(short_data, options_data),
                analyst_consensus=analyst_sentiment,
                news_sentiment="neutral",  # Would need news API
                social_sentiment="neutral",  # Would need social API
                key_signals=signals,
                contrarian_indicators=contrarian
            )
            
        except Exception as e:
            log.error(f"SentimentAgent: Analysis error: {e}")
            return SentimentStance(
                direction="neutral",
                conviction=0.4,
                overall_sentiment="neutral",
                sentiment_score=0,
                institutional_sentiment="neutral",
                retail_sentiment="neutral",
                analyst_consensus="hold",
                news_sentiment="neutral",
                social_sentiment="neutral",
                key_signals=["Sentiment analysis unavailable"],
                contrarian_indicators=[]
            )
    
    def _analyze_analyst_sentiment(self, data: Dict) -> tuple:
        """Analyze analyst ratings sentiment"""
        rec_key = data.get("recommendation_key", "hold")
        num_analysts = data.get("number_of_analysts", 0)
        
        sentiment_map = {
            "strong_buy": ("buy", 0.8),
            "buy": ("buy", 0.6),
            "hold": ("hold", 0.0),
            "sell": ("sell", -0.6),
            "strong_sell": ("sell", -0.8)
        }
        
        sentiment, score = sentiment_map.get(rec_key, ("hold", 0))
        
        # Adjust for analyst coverage
        if num_analysts > 20:
            score *= 1.1  # High coverage = more reliable
        elif num_analysts < 5:
            score *= 0.7  # Low coverage = less reliable
        
        return sentiment, max(-1, min(1, score))
    
    def _analyze_institutional_sentiment(self, data: Dict) -> tuple:
        """Analyze institutional positioning"""
        held_pct = data.get("held_percent_institutions", 0)
        held_insiders = data.get("held_percent_insiders", 0)
        
        if held_pct > 0.80:
            sentiment = "bullish"
            score = 0.3
        elif held_pct > 0.50:
            sentiment = "neutral"
            score = 0.0
        else:
            sentiment = "bearish"
            score = -0.2
        
        # High insider ownership is bullish signal
        if held_insiders > 0.10:
            score += 0.1
        
        return sentiment, score
    
    def _analyze_short_sentiment(self, data: Dict) -> tuple:
        """Analyze short interest sentiment"""
        short_pct = data.get("short_percent_of_float", 0)
        days_to_cover = data.get("days_to_cover", 0)
        
        if short_pct > 0.15:  # High short interest
            # Can be bearish (negativity) or bullish (squeeze potential)
            if days_to_cover > 5:
                sentiment = "bullish"  # Short squeeze potential
                score = 0.4
            else:
                sentiment = "bearish"
                score = -0.3
        elif short_pct < 0.05:
            sentiment = "bullish"  # Low negativity
            score = 0.2
        else:
            sentiment = "neutral"
            score = 0.0
        
        return sentiment, score
    
    def _analyze_insider_sentiment(self, data: Dict) -> tuple:
        """Analyze insider trading sentiment"""
        sentiment_str = data.get("insider_sentiment", "neutral")
        
        sentiment_map = {
            "bullish": ("bullish", 0.4),
            "neutral": ("neutral", 0.0),
            "bearish": ("bearish", -0.4)
        }
        
        return sentiment_map.get(sentiment_str, ("neutral", 0))
    
    def _analyze_options_sentiment(self, data: Dict) -> tuple:
        """Analyze options market sentiment"""
        put_call_ratio = data.get("put_call_ratio", 1.0)
        unusual_activity = data.get("unusual_activity", False)
        
        if put_call_ratio > 1.5:
            sentiment = "bearish"
            score = -0.3
        elif put_call_ratio < 0.7:
            sentiment = "bullish"
            score = 0.3
        else:
            sentiment = "neutral"
            score = 0.0
        
        if unusual_activity:
            # Unusual activity can signal smart money positioning
            score *= 1.2
        
        return sentiment, score
    
    def _estimate_retail_sentiment(self, short_data: Dict, options_data: Dict) -> str:
        """Estimate retail sentiment from available data"""
        # Proxy using options activity and short interest
        put_call = options_data.get("put_call_ratio", 1.0)
        
        if put_call > 1.2:
            return "bearish"
        elif put_call < 0.8:
            return "bullish"
        else:
            return "neutral"
    
    def argue(self, stance: SentimentStance, opponent_points: List[str] = None) -> Dict[str, Any]:
        """Generate argument based on sentiment stance"""
        points = []
        
        # Overall sentiment
        points.append(f"Overall sentiment: {stance.overall_sentiment.upper()} (score: {stance.sentiment_score:.2f})")
        
        # Breakdown
        points.append(f"Analyst consensus: {stance.analyst_consensus.upper()}")
        points.append(f"Institutional sentiment: {stance.institutional_sentiment.upper()}")
        points.append(f"Retail sentiment: {stance.retail_sentiment.upper()}")
        
        # Key signals
        points.extend(stance.key_signals[:4])
        
        # Contrarian indicators
        if stance.contrarian_indicators:
            points.append("⚠️ Contrarian signals detected:")
            points.extend(stance.contrarian_indicators[:2])
        
        # Direction reasoning
        if stance.direction == "bullish":
            if stance.sentiment_score > 0.7:
                points.append(f"Extreme positive sentiment - taking contrarian bearish stance")
            else:
                points.append(f"Positive sentiment supports {stance.conviction*100:.0f}% bullish view")
        elif stance.direction == "bearish":
            if stance.sentiment_score < -0.7:
                points.append(f"Extreme negative sentiment - taking contrarian bullish stance")
            else:
                points.append(f"Negative sentiment warrants {stance.conviction*100:.0f}% bearish caution")
        else:
            points.append("Mixed sentiment signals - neutral positioning appropriate")
        
        return {
            "agent": self.agent_id,
            "stance": stance.direction,
            "conviction": stance.conviction,
            "sentiment_score": stance.sentiment_score,
            "overall_sentiment": stance.overall_sentiment,
            "analyst_consensus": stance.analyst_consensus,
            "institutional_sentiment": stance.institutional_sentiment,
            "points": points,
            "contrarian_indicators": stance.contrarian_indicators,
            "timestamp": datetime.now().isoformat()
        }
