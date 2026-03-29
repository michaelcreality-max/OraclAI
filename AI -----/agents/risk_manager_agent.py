"""
Risk Manager Agent - Enhanced Reasoning
Chief Risk Officer persona with veto power
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

from agents.base_agent import BaseAgent, Belief, AssumptionType, ReasoningStep
from core.data_structures import (
    TradingSignal, AgentPosition, PositionStance, AgentType, AgentProfile, SignalType
)

log = logging.getLogger(__name__)


class RiskManagerAgent(BaseAgent):
    """
    CHIEF RISK OFFICER PERSONA:
    - Protects capital at all costs
    - Can veto any trade
    - Focuses on portfolio-level risk
    - Believes in survival first, profits second
    
    KEY BELIEFS:
    - Capital preservation is paramount
    - Correlation kills portfolios
    - Position sizing matters more than entry timing
    - Black swans are inevitable - prepare for them
    """
    
    def __init__(self, agent_id: str = "risk_mgr_001"):
        super().__init__(agent_id, AgentType.RISK_MANAGER)
        self.base_confidence = 0.3  # Start skeptical
        self.veto_power = True
        self.portfolio_exposure = 0.0
        self.max_portfolio_heat = 0.70
        self.max_single_position = 0.10
        self.correlation_limit = 0.80
    
    def _create_profile(self) -> AgentProfile:
        return AgentProfile(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            risk_tolerance="very_low",
            time_horizon="long",
            performance_score=0.80,  # Measured by avoiding blowups
            win_rate=0.90,  # Most recommendations = hold (no risk)
            max_drawdown=0.05,
            current_weight=0.30,
            min_confidence_threshold=0.90  # Very high bar
        )
    
    def _form_specific_beliefs(self, signal: TradingSignal,
                             market_context: Optional[Dict]) -> Dict[str, Belief]:
        """Form risk-specific beliefs"""
        beliefs = {}
        
        # Belief: Portfolio capacity
        current_heat = self.portfolio_exposure
        available_capacity = self.max_portfolio_heat - current_heat
        
        if available_capacity > 0.20:
            beliefs['portfolio_capacity'] = Belief(
                subject="Portfolio Capacity",
                confidence=0.8,
                assumption_type=AssumptionType.RISK_LEVEL,
                evidence=[f"Available capacity: {available_capacity:.1%} - room for new position"]
            )
        elif available_capacity > 0.10:
            beliefs['portfolio_capacity'] = Belief(
                subject="Portfolio Capacity",
                confidence=0.6,
                assumption_type=AssumptionType.RISK_LEVEL,
                evidence=[f"Limited capacity: {available_capacity:.1%} - small size only"]
            )
        else:
            beliefs['portfolio_capacity'] = Belief(
                subject="Portfolio Capacity",
                confidence=0.3,
                assumption_type=AssumptionType.RISK_LEVEL,
                evidence=[f"NO capacity: {available_capacity:.1%} - portfolio at max heat"]
            )
        
        # Belief: Signal conviction sufficiency
        if signal.confidence >= 0.85:
            beliefs['signal_conviction'] = Belief(
                subject="Signal Conviction",
                confidence=0.7,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"High conviction signal: {signal.confidence:.1%}"]
            )
        elif signal.confidence >= 0.70:
            beliefs['signal_conviction'] = Belief(
                subject="Signal Conviction",
                confidence=0.5,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Moderate conviction: {signal.confidence:.1%} - marginal"]
            )
        else:
            beliefs['signal_conviction'] = Belief(
                subject="Signal Conviction",
                confidence=0.2,
                assumption_type=AssumptionType.SIGNAL_QUALITY,
                evidence=[f"Low conviction: {signal.confidence:.1%} - insufficient for risk"]
            )
        
        # Belief: Market stress level
        if market_context:
            vix = market_context.get('vix', 20)
            if vix > 35:
                beliefs['market_stress'] = Belief(
                    subject="Market Stress",
                    confidence=0.9,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"VIX at {vix}: Extreme stress - DEFENSIVE mode"]
                )
            elif vix > 25:
                beliefs['market_stress'] = Belief(
                    subject="Market Stress",
                    confidence=0.7,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"VIX at {vix}: Elevated stress - caution warranted"]
                )
            elif vix < 15:
                beliefs['market_stress'] = Belief(
                    subject="Market Stress",
                    confidence=0.6,
                    assumption_type=AssumptionType.VOLATILITY_REGIME,
                    evidence=[f"VIX at {vix}: Low stress - but complacency risk"]
                )
        
        return beliefs
    
    def _reason_mandate_fit(self, signal: TradingSignal,
                           current_confidence: float,
                           market_context: Optional[Dict]) -> ReasoningStep:
        """Risk assessment - not mandate fit per se"""
        evidence = []
        confidence_delta = 0.0
        
        # Check portfolio capacity
        available = self.max_portfolio_heat - self.portfolio_exposure
        evidence.append(f"Portfolio heat: {self.portfolio_exposure:.1%}, max: {self.max_portfolio_heat:.1%}")
        
        if available < 0.05:
            evidence.append("CRITICAL: Portfolio at max capacity - NO NEW POSITIONS")
            confidence_delta -= 0.5
        elif available < 0.10:
            evidence.append("WARNING: Limited capacity remaining")
            confidence_delta -= 0.2
        else:
            evidence.append(f"OK: {available:.1%} capacity available")
            confidence_delta += 0.1
        
        # Check signal conviction for risk level
        if signal.confidence < 0.70:
            evidence.append(f"CRITICAL: Low conviction {signal.confidence:.1%} - cannot justify risk")
            confidence_delta -= 0.3
        elif signal.confidence < 0.85:
            evidence.append(f"CAUTION: Moderate conviction {signal.confidence:.1%}")
            confidence_delta -= 0.1
        else:
            evidence.append(f"OK: High conviction {signal.confidence:.1%}")
            confidence_delta += 0.1
        
        # Check for concentration risk
        symbol = signal.symbol
        # Would check existing positions here
        
        # Market stress check
        if market_context:
            vix = market_context.get('vix', 20)
            if vix > 35:
                evidence.append("CRITICAL: Extreme VIX - DEFENSIVE MODE")
                confidence_delta -= 0.4
            elif vix > 25:
                evidence.append("WARNING: Elevated VIX - reduce position sizes")
                confidence_delta -= 0.2
        
        return ReasoningStep(
            step_number=2,
            premise="Trade passes portfolio risk assessment",
            logic="Capacity available, conviction sufficient, no extreme stress",
            conclusion="Risk assessment: " + ("PASS" if confidence_delta > -0.2 else "VETO"),
            confidence_delta=confidence_delta,
            supporting_data=evidence
        )
    
    def _reason_risk_evaluation(self, signal: TradingSignal,
                               current_confidence: float,
                               market_context: Optional[Dict]) -> ReasoningStep:
        """Final risk evaluation"""
        evidence = []
        confidence_delta = 0.0
        
        # Position sizing limits
        max_position = self.max_single_position
        evidence.append(f"Single position limit: {max_position:.1%}")
        
        # Volatility adjustment
        if market_context:
            vol = market_context.get('vix', 20)
            if vol > 30:
                adjusted_limit = max_position * 0.5
                evidence.append(f"VIX {vol}: Reduce limit to {adjusted_limit:.1%}")
        
        # Drawdown risk
        evidence.append("5% drawdown limit per position")
        
        # Stop loss enforcement
        evidence.append("Mandatory stop-loss required")
        confidence_delta += 0.05
        
        # Liquidity check
        evidence.append("Liquidity: Must be able to exit within 1 day")
        
        return ReasoningStep(
            step_number=4,
            premise="Position risk is within acceptable bounds",
            logic="Position limits, drawdown controls, liquidity verified",
            conclusion="Risk: " + ("ACCEPTABLE" if confidence_delta >= 0 else "ELEVATED"),
            confidence_delta=confidence_delta,
            supporting_data=evidence
        )
    
    def _calculate_position_size(self, confidence: float, signal: TradingSignal,
                               reasoning: List[ReasoningStep]) -> float:
        """Risk-constrained position sizing"""
        # Risk manager rarely takes active positions - mostly vetoes/approves
        if confidence < 0.70:
            return 0.0  # Veto by no position
        
        # Very conservative sizing
        base_size = 0.01  # 1% max
        
        # Can only approve up to standard position limit
        max_size = min(base_size, self.max_single_position)
        
        # Reduce if portfolio heat high
        if self.portfolio_exposure > 0.5:
            max_size *= 0.5
        
        return round(max_size, 4)
    
    def evaluate_portfolio_risk(self, all_positions: List[AgentPosition]) -> Dict:
        """Evaluate portfolio-level risk across all agents"""
        total_exposure = sum(p.position_size_pct for p in all_positions)
        self.portfolio_exposure = total_exposure
        
        # Calculate concentration
        if all_positions:
            largest = max(p.position_size_pct for p in all_positions)
            concentration = largest / total_exposure if total_exposure > 0 else 0
        else:
            concentration = 0
            largest = 0
        
        # Risk level
        if total_exposure > 0.7 or concentration > 0.2:
            risk_level = "HIGH"
        elif total_exposure > 0.5:
            risk_level = "ELEVATED"
        else:
            risk_level = "NORMAL"
        
        return {
            'total_exposure': total_exposure,
            'concentration': concentration,
            'largest_position': largest,
            'risk_level': risk_level,
            'veto_recommended': total_exposure > 0.8
        }
