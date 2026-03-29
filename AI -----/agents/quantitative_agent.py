"""
Quantitative Agent - Enhanced Reasoning
Statistical arbitrage / quant fund manager persona
"""

import logging
import numpy as np
from typing import Dict, Optional
from datetime import datetime

from agents.base_agent import BaseAgent, Belief, AssumptionType, ReasoningStep
from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, AgentProfile, SignalType
)

log = logging.getLogger(__name__)


class QuantitativeAgent(BaseAgent):
    """
    QUANTITATIVE ANALYST PERSONA:
    - Like a systematic fund PM
    - Pure statistics, no emotions
    - Seeks statistical edge, mean reversion
    - Kelly criterion for position sizing
    
    KEY BELIEFS:
    - Markets are probabilistic, not deterministic
    - Edge = win_rate * avg_win - (1-win_rate) * avg_loss
    - Position size proportional to edge/confidence
    """
    
    def __init__(self, agent_id: str = "quant_001"):
        super().__init__(agent_id, AgentType.QUANTITATIVE)
        self.base_confidence = 0.5  # Neutral start
        self.win_rate_estimate = 0.52  # Base assumption
        self.avg_win = 0.04
        self.avg_loss = 0.03
    
    def _create_profile(self) -> AgentProfile:
        return AgentProfile(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            risk_tolerance="medium",
            time_horizon="medium",
            performance_score=0.58,
            win_rate=0.52,
            max_drawdown=0.15,
            current_weight=0.20,
            min_confidence_threshold=0.55
        )
    
    def _form_specific_beliefs(self, signal: TradingSignal,
                             market_context: Optional[Dict]) -> Dict[str, Belief]:
        """Form quantitative beliefs based on statistics"""
        beliefs = {}
        
        # Belief: Statistical edge exists
        expected_return = signal.expected_return
        confidence = signal.confidence
        
        # Edge calculation
        edge = confidence * expected_return - (1 - confidence) * 0.02
        
        if edge > 0.02:  # 2%+ edge
            beliefs['statistical_edge'] = Belief(
                subject="Statistical Edge",
                confidence=0.75,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Edge calculation: {edge:.2%} (threshold: 2%)"]
            )
        elif edge > 0.01:
            beliefs['statistical_edge'] = Belief(
                subject="Statistical Edge",
                confidence=0.55,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Edge calculation: {edge:.2%} (marginal)"]
            )
        else:
            beliefs['statistical_edge'] = Belief(
                subject="Statistical Edge",
                confidence=0.3,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Edge calculation: {edge:.2%} (insufficient)"]
            )
        
        # Belief: Mean reversion vs momentum regime
        if market_context:
            regime = market_context.get('market_regime', 'unknown')
            if regime == 'mean_reverting':
                beliefs['market_regime'] = Belief(
                    subject="Market Regime",
                    confidence=0.7,
                    assumption_type=AssumptionType.MARKET_TREND,
                    evidence=["Mean-reverting regime detected - contrarian strategies favored"]
                )
            elif regime == 'trending':
                beliefs['market_regime'] = Belief(
                    subject="Market Regime",
                    confidence=0.7,
                    assumption_type=AssumptionType.MARKET_TREND,
                    evidence=["Trending regime - momentum strategies favored"]
                )
        
        # Belief: Volatility forecast
        if market_context:
            vol_forecast = market_context.get('volatility_forecast', 0.20)
            if vol_forecast < 0.15:
                beliefs['volatility_forecast'] = Belief(
                    subject="Volatility Forecast",
                    confidence=0.65,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"Low vol forecast ({vol_forecast:.1%}) - tighter stops appropriate"]
                )
            elif vol_forecast > 0.30:
                beliefs['volatility_forecast'] = Belief(
                    subject="Volatility Forecast",
                    confidence=0.7,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"High vol forecast ({vol_forecast:.1%}) - wider stops, smaller size"]
                )
        
        return beliefs
    
    def _reason_mandate_fit(self, signal: TradingSignal,
                           current_confidence: float,
                           market_context: Optional[Dict]) -> ReasoningStep:
        """Quantitative fit assessment"""
        evidence = []
        confidence_delta = 0.0
        
        # Calculate edge
        expected_return = signal.expected_return
        confidence = signal.confidence
        edge = confidence * expected_return - (1 - confidence) * 0.02
        
        evidence.append(f"Edge calculation: {edge:.2%}")
        
        if edge > 0.02:
            evidence.append("PASS: Edge exceeds 2% threshold")
            confidence_delta += 0.2
        elif edge > 0.01:
            evidence.append("MARGINAL: Edge 1-2%")
            confidence_delta += 0.05
        else:
            evidence.append("FAIL: Edge insufficient")
            confidence_delta -= 0.2
        
        # Information ratio consideration
        if signal.confidence >= 0.60:
            evidence.append(f"PASS: Confidence {signal.confidence:.1%} provides IR > 0.5")
            confidence_delta += 0.1
        
        # Statistical significance check
        if reasoning := signal.reasoning:
            factors = reasoning.primary_factors if hasattr(reasoning, 'primary_factors') else []
            if len(factors) >= 3:
                evidence.append(f"PASS: {len(factors)} factors - well diversified signal")
                confidence_delta += 0.1
            else:
                evidence.append(f"CAUTION: Only {len(factors)} factors - concentrated signal")
        
        # Market regime alignment
        if market_context:
            regime = market_context.get('market_regime', 'unknown')
            if regime in ['mean_reverting', 'trending']:
                evidence.append(f"PASS: {regime} regime - systematic strategies active")
                confidence_delta += 0.05
        
        return ReasoningStep(
            step_number=2,
            premise="Signal has quantifiable statistical edge",
            logic="Edge = P(win)*Return - P(loss)*Loss, must be > 1%",
            conclusion="Edge: " + ("POSITIVE" if confidence_delta > 0 else "NEGATIVE"),
            confidence_delta=confidence_delta,
            supporting_data=evidence
        )
    
    def _reason_risk_evaluation(self, signal: TradingSignal,
                               current_confidence: float,
                               market_context: Optional[Dict]) -> ReasoningStep:
        """Quantitative risk evaluation"""
        evidence = []
        confidence_delta = 0.0
        
        # Kelly criterion calculation
        win_rate = signal.confidence
        b = signal.expected_return / 0.02 if signal.expected_return > 0 else 1  # odds
        
        # Kelly fraction = (bp - q) / b
        q = 1 - win_rate
        kelly = (b * win_rate - q) / b if b > 0 else 0
        
        evidence.append(f"Kelly criterion: {kelly:.2%}")
        evidence.append("Using half-Kelly for safety")
        
        # Position sizing based on Kelly
        position_fraction = max(0, min(kelly * 0.5, 0.05))  # Cap at 5%
        evidence.append(f"Suggested position: {position_fraction:.2%}")
        
        # Volatility adjustment
        if market_context:
            vol = market_context.get('volatility_forecast', 0.20)
            if vol > 0.30:
                evidence.append(f"High vol ({vol:.1%}) - reduce Kelly by 50%")
                position_fraction *= 0.5
                confidence_delta -= 0.1
            elif vol < 0.15:
                evidence.append(f"Low vol ({vol:.1%}) - standard Kelly sizing")
        
        # Drawdown control
        symbol = signal.symbol
        if symbol in self.pattern_memory:
            patterns = self.pattern_memory[symbol]
            losses = [p for p in patterns if p.get('return', 0) < -0.03]
            if losses:
                avg_loss = sum(p['return'] for p in losses) / len(losses)
                evidence.append(f"Historical avg loss: {avg_loss:.2%}")
        
        return ReasoningStep(
            step_number=4,
            premise="Risk is quantified and managed via Kelly",
            logic="Half-Kelly sizing with vol adjustment",
            conclusion=f"Risk: {'QUANTIFIED' if confidence_delta >= -0.1 else 'ELEVATED'}",
            confidence_delta=confidence_delta,
            supporting_data=evidence
        )
    
    def _calculate_position_size(self, confidence: float, signal: TradingSignal,
                               reasoning: List[ReasoningStep]) -> float:
        """Kelly-based position sizing"""
        if confidence < 0.55:
            return 0.0
        
        # Kelly calculation
        win_rate = confidence
        expected_return = signal.expected_return
        loss_size = 0.02  # Assumed avg loss
        
        if expected_return <= 0:
            return 0.0
        
        b = expected_return / loss_size  # Gain/loss ratio
        kelly = (b * win_rate - (1 - win_rate)) / b if b > 0 else 0
        
        # Half-Kelly for safety
        position = max(0, kelly * 0.5)
        
        # Cap at 5%
        position = min(position, 0.05)
        
        # Apply confidence scaling
        if confidence < 0.60:
            position *= 0.5
        
        return round(position, 4)
