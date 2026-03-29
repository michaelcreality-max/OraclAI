"""
Aggressive Agent - High risk, short-term momentum focus
Phase 3 Implementation
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, AgentProfile, SignalType
)

log = logging.getLogger(__name__)


class AggressiveAgent(BaseAgent):
    """
    Aggressive Agent Profile:
    - Risk tolerance: High
    - Time horizon: Short-term (1-4 weeks)
    - Preference: Momentum, growth, volatility
    
    Decision Logic:
    - Takes signals with confidence > 0.55
    - Looks for breakout patterns, volume spikes
    - Comfortable with high beta, momentum stocks
    - Position sizing: Aggressive (5-8% per trade)
    - Uses leverage in favorable conditions
    """
    
    def __init__(self, agent_id: str = "aggressive_001"):
        super().__init__(agent_id, AgentType.AGGRESSIVE)
    
    def _create_profile(self) -> AgentProfile:
        return AgentProfile(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            risk_tolerance="high",
            time_horizon="short",
            performance_score=0.65,
            win_rate=0.45,  # Lower win rate but higher returns
            max_drawdown=0.20,
            current_weight=0.20
        )
    
    def analyze(self, signal: TradingSignal,
                market_context: Optional[Dict] = None) -> AgentPosition:
        """
        Aggressive analysis: Takes more signals, larger positions
        """
        symbol = signal.symbol
        base_stance = self._signal_to_stance(signal.signal)
        
        # Lower confidence threshold
        if signal.confidence < 0.55:
            return AgentPosition(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                symbol=symbol,
                stance=PositionStance.HOLD,
                confidence=0.5,
                position_size_pct=0.0,
                reasoning=f"Confidence {signal.confidence:.1%} below aggressive threshold (55%)",
                supporting_factors=[],
                opposing_factors=["Insufficient momentum"],
                timestamp=datetime.now()
            )
        
        # Check for momentum indicators in reasoning
        reasoning_text = ' '.join(signal.reasoning.primary_factors).lower()
        has_momentum = any(word in reasoning_text for word in ['momentum', 'breakout', 'volume'])
        
        # Position sizing based on confidence and momentum
        if base_stance == PositionStance.BUY:
            # Base position size
            position_size = 0.05  # 5% minimum
            
            # Scale up with confidence
            if signal.confidence > 0.70:
                position_size = 0.07  # 7%
            if signal.confidence > 0.85:
                position_size = 0.08  # 8% max
            
            # Bonus for momentum confirmation
            if has_momentum:
                position_size = min(position_size + 0.01, 0.10)  # Up to 10% with momentum
            
            # Tighter stop loss for aggressive trades (willing to cut losses quickly)
            stop_loss = -0.03  # 3% stop
            
            # Take profit target
            take_profit = 0.15  # 15% target
            
            supporting_factors = [
                f"Confidence: {signal.confidence:.1%}",
                f"Expected return: {signal.expected_return:.2%}",
                f"Signal: {signal.signal.value}"
            ]
            if has_momentum:
                supporting_factors.append("Momentum confirmed")
            
            return AgentPosition(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                symbol=symbol,
                stance=PositionStance.BUY,
                confidence=signal.confidence,
                position_size_pct=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                time_horizon="short",
                reasoning=f"Aggressive BUY: {signal.confidence:.1%} confidence, {signal.expected_return:.2%} expected return",
                supporting_factors=supporting_factors,
                opposing_factors=[],
                timestamp=datetime.now()
            )
        
        elif base_stance == PositionStance.SELL:
            # Aggressive short/momentum reversal
            position_size = 0.06 if signal.confidence > 0.70 else 0.05
            
            return AgentPosition(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                symbol=symbol,
                stance=PositionStance.SELL,
                confidence=signal.confidence,
                position_size_pct=position_size,
                stop_loss=0.03,  # 3% on short
                take_profit=0.12,
                time_horizon="short",
                reasoning=f"Aggressive SELL: Capturing momentum reversal",
                supporting_factors=[
                    f"Confidence: {signal.confidence:.1%}",
                    f"Expected decline: {signal.expected_return:.2%}"
                ],
                opposing_factors=[],
                timestamp=datetime.now()
            )
        
        # HOLD
        return AgentPosition(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            symbol=symbol,
            stance=PositionStance.HOLD,
            confidence=0.5,
            position_size_pct=0.0,
            reasoning="No actionable momentum signal",
            supporting_factors=[],
            opposing_factors=["Signal lacks momentum confirmation"],
            timestamp=datetime.now()
        )
    
    def _signal_to_stance(self, signal_type: SignalType) -> PositionStance:
        """Convert signal type to position stance"""
        mapping = {
            SignalType.BUY: PositionStance.BUY,
            SignalType.SELL: PositionStance.SELL,
            SignalType.HOLD: PositionStance.HOLD
        }
        return mapping.get(signal_type, PositionStance.HOLD)
