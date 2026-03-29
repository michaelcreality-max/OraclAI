"""
Conservative Agent - Enhanced Reasoning
Maximum capability quantitative analyst persona
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from agents.base_agent import BaseAgent, Belief, AssumptionType, ReasoningStep
from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, AgentProfile, SignalType
)

log = logging.getLogger(__name__)


class ConservativeAgent(BaseAgent):
    """
    CONSERVATIVE ANALYST PERSONA:
    - Like a value-oriented fund manager
    - Seeks quality, stability, downside protection
    - High conviction threshold (min 80%)
    - Believes in slow, steady wealth preservation
    
    KEY BELIEFS:
    - Capital preservation > capital appreciation
    - Quality over momentum
    - Risk-adjusted returns matter most
    """
    
    def __init__(self, agent_id: str = "conservative_001"):
        super().__init__(agent_id, AgentType.CONSERVATIVE)
        self.base_confidence = 0.4  # Start skeptical
    
    def _create_profile(self) -> AgentProfile:
        return AgentProfile(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            risk_tolerance="low",
            time_horizon="long",
            performance_score=0.6,
            win_rate=0.55,
            max_drawdown=0.08,
            current_weight=0.15,
            min_confidence_threshold=0.80
        )
    
    def _form_specific_beliefs(self, signal: TradingSignal,
                             market_context: Optional[Dict]) -> Dict[str, Belief]:
        """Form conservative-specific beliefs"""
        beliefs = {}
        
        # Belief: Expected return sufficiency
        if signal.expected_return >= 0.05:  # 5%+ expected
            beliefs['return_sufficiency'] = Belief(
                subject="Expected Return Sufficiency",
                confidence=0.75,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Expected return {signal.expected_return:.2%} meets 5% minimum"]
            )
        else:
            beliefs['return_sufficiency'] = Belief(
                subject="Expected Return Sufficiency",
                confidence=0.3,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Expected return {signal.expected_return:.2%} below 5% threshold"]
            )
        
        # Belief: Market volatility regime
        if market_context:
            vix = market_context.get('vix', 20)
            if vix < 20:
                beliefs['volatility_regime'] = Belief(
                    subject="Volatility Regime",
                    confidence=0.8,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"VIX at {vix}: Low volatility, favorable for long-term positions"]
                )
            elif vix > 25:
                beliefs['volatility_regime'] = Belief(
                    subject="Volatility Regime",
                    confidence=0.9,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"VIX at {vix}: High volatility, avoid new positions"]
                )
        
        # Belief: Signal conviction quality
        if signal.confidence >= 0.90:
            beliefs['signal_quality'] = Belief(
                subject="Signal Conviction Quality",
                confidence=0.85,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Excellent signal confidence: {signal.confidence:.1%}"]
            )
        elif signal.confidence >= 0.80:
            beliefs['signal_quality'] = Belief(
                subject="Signal Conviction Quality",
                confidence=0.65,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Acceptable signal confidence: {signal.confidence:.1%}"]
            )
        else:
            beliefs['signal_quality'] = Belief(
                subject="Signal Conviction Quality",
                confidence=0.3,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Insufficient signal confidence: {signal.confidence:.1%}"]
            )
        
        return beliefs
    
    def _reason_mandate_fit(self, signal: TradingSignal,
                           current_confidence: float,
                           market_context: Optional[Dict]) -> ReasoningStep:
        """Does this fit conservative mandate?"""
        evidence = []
        confidence_delta = 0.0
        
        # Must be high confidence
        if signal.confidence < 0.80:
            evidence.append(f"FAIL: Confidence {signal.confidence:.1%} < 80% minimum")
            confidence_delta -= 0.3
        else:
            evidence.append(f"PASS: Confidence {signal.confidence:.1%} >= 80%")
            confidence_delta += 0.1
        
        # Must have reasonable expected return
        if signal.expected_return < 0.03:
            evidence.append(f"FAIL: Expected return {signal.expected_return:.2%} < 3%")
            confidence_delta -= 0.2
        elif signal.expected_return >= 0.05:
            evidence.append(f"PASS: Expected return {signal.expected_return:.2%} >= 5%")
            confidence_delta += 0.1
        
        # Check volatility regime
        if market_context:
            vix = market_context.get('vix', 20)
            if vix > 25:
                evidence.append(f"CAUTION: High VIX ({vix}) - reduce position size")
                confidence_delta -= 0.15
            elif vix < 18:
                evidence.append(f"GOOD: Low VIX ({vix}) - favorable environment")
                confidence_delta += 0.05
        
        # Check for quality factors
        reasoning = signal.reasoning
        if reasoning:
            quality_signals = ['quality', 'value', 'dividend', 'fcf', 'moat']
            momentum_signals = ['momentum', 'breakout', 'trend', 'momo']
            
            has_quality = any(f in str(reasoning).lower() for f in quality_signals)
            has_momentum = any(f in str(reasoning).lower() for f in momentum_signals)
            
            if has_quality:
                evidence.append("PASS: Quality factors present")
                confidence_delta += 0.1
            if has_momentum and not has_quality:
                evidence.append("CAUTION: Pure momentum signal, lacks quality overlay")
                confidence_delta -= 0.1
        
        return ReasoningStep(
            step_number=2,
            premise="Signal fits conservative investment mandate",
            logic="High conviction (>80%), meaningful expected return (>3%), quality factors",
            conclusion="Mandate fit: " + ("APPROVED" if confidence_delta > 0 else "QUESTIONABLE"),
            confidence_delta=confidence_delta,
            supporting_data=evidence
        )
    
    def _reason_risk_evaluation(self, signal: TradingSignal,
                               current_confidence: float,
                               market_context: Optional[Dict]) -> ReasoningStep:
        """Conservative risk evaluation"""
        evidence = []
        confidence_delta = 0.0
        
        # Stop loss requirement
        evidence.append("Conservative 5% stop-loss will be applied")
        
        # Position sizing limits
        max_position = 0.03  # 3% max
        evidence.append(f"Maximum position: {max_position:.1%} (conservative limit)")
        
        # Check drawdown potential
        if signal.expected_return < 0:
            evidence.append("Negative expected return - potential for loss")
            confidence_delta -= 0.2
        
        # Time horizon alignment
        evidence.append("Long-term horizon (6-12 months) allows riding out volatility")
        confidence_delta += 0.05
        
        # Historical memory check
        symbol = signal.symbol
        if symbol in self.pattern_memory:
            patterns = self.pattern_memory[symbol]
            losses = [p for p in patterns if p.get('return', 0) < -0.05]
            if len(losses) > 2:
                evidence.append(f"CAUTION: {len(losses)} prior >5% losses on {symbol}")
                confidence_delta -= 0.1
        
        return ReasoningStep(
            step_number=4,
            premise="Risk is acceptable for conservative profile",
            logic="Stop-loss protection, position limits, long horizon",
            conclusion=f"Risk assessment: {'ACCEPTABLE' if confidence_delta >= 0 else 'ELEVATED'}",
            confidence_delta=confidence_delta,
            supporting_data=evidence
        )
    
    def _calculate_position_size(self, confidence: float, signal: TradingSignal,
                               reasoning: List[ReasoningStep]) -> float:
        """Calculate conservative position size"""
        # Base size on confidence
        if confidence < 0.80:
            return 0.0  # No position
        
        base_size = 0.02  # 2% base
        
        # Bonus for very high confidence
        if confidence >= 0.90:
            base_size = 0.03  # Up to 3%
        
        # Reduce if any risk concerns
        risk_step = reasoning[3] if len(reasoning) > 3 else None
        if risk_step and risk_step.confidence_delta < 0:
            base_size *= 0.7
        
        # Reduce in high volatility
        if signal.confidence >= 0.80 and confidence >= 0.85:
            pass  # Full size
        else:
            base_size *= 0.8
        
        return round(base_size, 4)
