"""
Sentiment Agent - Market sentiment and behavioral analysis focus
Phase 3 Implementation
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, AgentProfile, SignalType,
    RiskAssessment
)

log = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """
    Sentiment Agent Profile:
    - Risk tolerance: Medium-High
    - Time horizon: Short-Medium (2-8 weeks)
    - Preference: Sentiment-driven moves, behavioral patterns
    
    Decision Logic:
    - Analyzes sentiment indicators in signal reasoning
    - Looks for fear/greed extremes
    - Contrarian at extremes (buy fear, sell greed)
    - Momentum following in trending sentiment
    """
    
    def __init__(self, agent_id: str = "sentiment_001"):
        super().__init__(agent_id, AgentType.SENTIMENT)
    
    def _create_profile(self) -> AgentProfile:
        return AgentProfile(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            risk_tolerance="medium_high",
            time_horizon="short_medium",
            performance_score=0.58,
            win_rate=0.50,
            max_drawdown=0.15,
            current_weight=0.15
        )
    
    def analyze(self, signal: TradingSignal,
                market_context: Optional[Dict] = None) -> AgentPosition:
        """
        Sentiment analysis: Behavioral patterns and extremes
        """
        symbol = signal.symbol
        base_stance = self._signal_to_stance(signal.signal)
        
        # Extract sentiment from signal reasoning
        sentiment = self._extract_sentiment(signal)
        
        # Look for extreme sentiment (contrarian opportunities)
        is_extreme_fear = sentiment['fear_score'] > 0.8
        is_extreme_greed = sentiment['greed_score'] > 0.8
        
        supporting_factors = []
        opposing_factors = []
        
        # Contrarian logic at extremes
        if is_extreme_fear and base_stance in [PositionStance.BUY, PositionStance.HOLD]:
            # Extreme fear + positive signal = strong buy
            position_size = 0.05 if signal.confidence > 0.6 else 0.03
            
            supporting_factors.extend([
                f"Extreme fear detected: {sentiment['fear_score']:.1%}",
                "Contrarian BUY opportunity",
                f"Signal confidence: {signal.confidence:.1%}"
            ])
            
            return AgentPosition(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                symbol=symbol,
                stance=PositionStance.BUY,
                confidence=min(signal.confidence + 0.1, 0.95),
                position_size_pct=position_size,
                stop_loss=-0.04,
                take_profit=0.12,
                time_horizon="medium",
                reasoning=f"Contrarian BUY: Extreme fear ({sentiment['fear_score']:.1%}) with positive signal",
                supporting_factors=supporting_factors,
                opposing_factors=opposing_factors,
                timestamp=datetime.now()
            )
        
        elif is_extreme_greed and base_stance in [PositionStance.SELL, PositionStance.HOLD]:
            # Extreme greed + negative signal = strong sell
            position_size = 0.05 if signal.confidence > 0.6 else 0.03
            
            supporting_factors.extend([
                f"Extreme greed detected: {sentiment['greed_score']:.1%}",
                "Contrarian SELL opportunity",
                f"Signal confidence: {signal.confidence:.1%}"
            ])
            
            return AgentPosition(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                symbol=symbol,
                stance=PositionStance.SELL,
                confidence=min(signal.confidence + 0.1, 0.95),
                position_size_pct=position_size,
                stop_loss=0.04,
                take_profit=0.10,
                time_horizon="short",
                reasoning=f"Contrarian SELL: Extreme greed ({sentiment['greed_score']:.1%})",
                supporting_factors=supporting_factors,
                opposing_factors=opposing_factors,
                timestamp=datetime.now()
            )
        
        # Momentum following for moderate sentiment
        if base_stance == PositionStance.BUY and signal.confidence > 0.60:
            position_size = 0.03 + (sentiment['momentum_score'] * 0.02)
            position_size = min(position_size, 0.06)
            
            supporting_factors.extend([
                f"Positive sentiment momentum: {sentiment['momentum_score']:.1%}",
                f"Signal confidence: {signal.confidence:.1%}"
            ])
            
            return AgentPosition(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                symbol=symbol,
                stance=PositionStance.BUY,
                confidence=signal.confidence,
                position_size_pct=position_size,
                stop_loss=-0.03,
                time_horizon="short_medium",
                reasoning=f"Sentiment momentum BUY: {sentiment['momentum_score']:.1%} momentum",
                supporting_factors=supporting_factors,
                opposing_factors=opposing_factors,
                timestamp=datetime.now()
            )
        
        # Default: sentiment not extreme enough
        opposing_factors.append(f"Fear: {sentiment['fear_score']:.1%}, Greed: {sentiment['greed_score']:.1%}")
        opposing_factors.append("Sentiment not at actionable extreme")
        
        return AgentPosition(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            symbol=symbol,
            stance=PositionStance.HOLD,
            confidence=0.5,
            position_size_pct=0.0,
            reasoning="No extreme sentiment detected for contrarian action",
            supporting_factors=[],
            opposing_factors=opposing_factors,
            timestamp=datetime.now()
        )
    
    def _extract_sentiment(self, signal: TradingSignal) -> Dict:
        """
        Extract sentiment indicators from signal reasoning
        """
        # Initialize scores
        fear_score = 0.0
        greed_score = 0.0
        momentum_score = 0.0
        
        # Analyze primary factors
        reasoning_text = ' '.join(signal.reasoning.primary_factors).lower()
        evidence_text = ' '.join(signal.reasoning.supporting_evidence).lower()
        full_text = reasoning_text + ' ' + evidence_text
        
        # Fear indicators
        fear_words = ['fear', 'panic', 'crash', 'sell-off', 'concern', 'worry', 'decline', 'drop']
        fear_score = sum(0.2 for word in fear_words if word in full_text)
        fear_score = min(fear_score, 1.0)
        
        # Greed indicators
        greed_words = ['greed', 'fomo', 'euphoria', 'bubble', 'mania', 'surge', 'rally']
        greed_score = sum(0.2 for word in greed_words if word in full_text)
        greed_score = min(greed_score, 1.0)
        
        # Momentum indicators
        momentum_words = ['momentum', 'breakout', 'trend', 'strength', 'volume', 'accumulation']
        momentum_score = sum(0.15 for word in momentum_words if word in full_text)
        
        # Adjust based on signal direction
        if signal.signal == SignalType.SELL:
            fear_score = min(fear_score + 0.3, 1.0)
            greed_score = max(greed_score - 0.2, 0.0)
        elif signal.signal == SignalType.BUY:
            greed_score = min(greed_score + 0.2, 1.0)
            fear_score = max(fear_score - 0.1, 0.0)
        
        return {
            'fear_score': fear_score,
            'greed_score': greed_score,
            'momentum_score': min(momentum_score, 1.0),
            'sentiment_direction': 'bullish' if greed_score > fear_score else 'bearish'
        }
    
    def _signal_to_stance(self, signal_type: SignalType) -> PositionStance:
        """Convert signal type to position stance"""
        mapping = {
            SignalType.BUY: PositionStance.BUY,
            SignalType.SELL: PositionStance.SELL,
            SignalType.HOLD: PositionStance.HOLD
        }
        return mapping.get(signal_type, PositionStance.HOLD)
