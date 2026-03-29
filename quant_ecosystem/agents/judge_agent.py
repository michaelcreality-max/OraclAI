"""
Judge Agent
Final decision maker that evaluates all agent arguments and produces verdict
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class JudicialVerdict:
    """Final verdict from judge"""
    action: str  # buy, sell, hold
    confidence: float
    score: float
    rationale: str
    consensus_level: str  # strong, moderate, weak, none
    risk_flags: List[str]
    recommended_position_size: str  # full, reduced, minimal, none
    timestamp: datetime
    judge_duration: float


class JudgeAgent:
    """
    Judge Agent that:
    - Evaluates all agent arguments impartially
    - Weights evidence based on quality and relevance
    - Considers risk factors in final decision
    - Provides transparent reasoning
    - Determines appropriate position sizing
    """
    
    def __init__(self):
        self.agent_id = "judge_agent"
        self.consensus_threshold = 0.70
        
    def deliberate(self, 
                   symbol: str,
                   bullish_argument: Dict[str, Any],
                   bearish_argument: Dict[str, Any],
                   risk_assessment: Dict[str, Any],
                   financial_context: Dict[str, Any]) -> JudicialVerdict:
        """
        Deliberate and render final verdict based on all arguments
        """
        log.info(f"JudgeAgent: Beginning deliberation for {symbol}")
        start_time = time.time()
        
        try:
            # Extract key data
            bull_conf = bullish_argument.get("confidence", 0.5)
            bear_conf = bearish_argument.get("confidence", 0.5)
            risk_conf = risk_assessment.get("confidence", 0.5)
            risk_score = risk_assessment.get("risk_score", 0.5)
            
            bull_points = bullish_argument.get("points", [])
            bear_points = bearish_argument.get("points", [])
            risk_flags = risk_assessment.get("points", [])
            
            # Phase 1: Weight the evidence
            weighted_score = self._weight_evidence(
                bull_conf, bear_conf, risk_conf, 
                bull_points, bear_points, risk_score
            )
            
            # Phase 2: Consider financial context
            context_adjustment = self._apply_context_adjustments(
                weighted_score, financial_context, risk_score
            )
            
            final_score = weighted_score + context_adjustment
            
            # Phase 3: Determine action
            action = self._determine_action(final_score, risk_score)
            
            # Phase 4: Assess consensus level
            consensus_level = self._assess_consensus(
                bull_conf, bear_conf, risk_conf, final_score
            )
            
            # Phase 5: Determine position sizing
            position_size = self._recommend_position_size(
                action, consensus_level, risk_score, financial_context
            )
            
            # Phase 6: Generate rationale
            rationale = self._generate_rationale(
                action, final_score, bull_conf, bear_conf, 
                risk_score, consensus_level, financial_context
            )
            
            judge_duration = time.time() - start_time
            
            log.info(f"JudgeAgent: Verdict rendered - {action.upper()} (confidence: {abs(final_score):.2f})")
            
            return JudicialVerdict(
                action=action,
                confidence=abs(final_score),
                score=final_score,
                rationale=rationale,
                consensus_level=consensus_level,
                risk_flags=risk_flags[:5],  # Top 5 risk flags
                recommended_position_size=position_size,
                timestamp=datetime.now(),
                judge_duration=judge_duration
            )
            
        except Exception as e:
            log.error(f"JudgeAgent: Deliberation error: {e}")
            return JudicialVerdict(
                action="hold",
                confidence=0.5,
                score=0.0,
                rationale=f"Error in deliberation: {str(e)}. Defaulting to hold.",
                consensus_level="weak",
                risk_flags=["analysis_error"],
                recommended_position_size="minimal",
                timestamp=datetime.now(),
                judge_duration=time.time() - start_time
            )
    
    def _weight_evidence(self, bull_conf: float, bear_conf: float, risk_conf: float,
                        bull_points: List[str], bear_points: List[str], 
                        risk_score: float) -> float:
        """Weight and score the evidence from all agents"""
        
        # Base score from bullish vs bearish confidence
        sentiment_score = bull_conf - bear_conf
        
        # Quality of evidence bonus
        evidence_quality = 0.0
        
        # More supporting points = higher quality (up to +0.10)
        bull_quality = min(0.10, len(bull_points) * 0.02)
        bear_quality = min(0.10, len(bear_points) * 0.02)
        
        # If bullish has more points, add to score
        if len(bull_points) > len(bear_points):
            evidence_quality += bull_quality
        else:
            evidence_quality -= bear_quality
        
        # Risk adjustment
        # Higher risk score reduces the score (more conservative)
        risk_adjustment = (0.5 - risk_score) * 0.3
        
        # Combine
        weighted_score = sentiment_score * 0.7 + evidence_quality * 0.3 + risk_adjustment
        
        return round(weighted_score, 3)
    
    def _apply_context_adjustments(self, base_score: float, 
                                  financial_context: Dict[str, Any],
                                  risk_score: float) -> float:
        """Apply adjustments based on financial context"""
        adjustments = 0.0
        
        # Market phase adjustments
        market_phase = financial_context.get("market_phase", "normal")
        if market_phase == "recession":
            # In recession, be more conservative
            if base_score > 0:  # Bullish
                adjustments -= 0.10
            else:  # Bearish
                adjustments += 0.10
        elif market_phase == "expansion":
            # In expansion, favor growth
            if base_score > 0:
                adjustments += 0.05
        elif market_phase == "crisis":
            # In crisis, strongly favor risk-off
            if base_score > 0:
                adjustments -= 0.20
            else:
                adjustments += 0.15
        
        # VIX/Volatility adjustments
        vix = financial_context.get("vix_level", 20)
        if vix > 30:  # High volatility
            # Reduce confidence in high vol environment
            adjustments -= 0.05 if base_score > 0 else -0.05
        
        # Systemic risk adjustment
        systemic_risk = financial_context.get("systemic_risk", 0)
        if systemic_risk > 0.7:
            # High systemic risk = more conservative
            if base_score > 0:
                adjustments -= 0.10
        
        return round(adjustments, 3)
    
    def _determine_action(self, final_score: float, risk_score: float) -> str:
        """Determine buy/sell/hold action"""
        # Risk-adjusted thresholds
        # Higher risk = higher threshold for buy
        buy_threshold = 0.25 + (risk_score * 0.10)  # 0.25 to 0.35
        sell_threshold = -0.25 - (risk_score * 0.05)  # -0.25 to -0.30
        
        if final_score >= buy_threshold:
            return "buy"
        elif final_score <= sell_threshold:
            return "sell"
        else:
            return "hold"
    
    def _assess_consensus(self, bull_conf: float, bear_conf: float, 
                         risk_conf: float, final_score: float) -> str:
        """Assess level of consensus among agents"""
        # Calculate variance in confidence
        confidences = [bull_conf, bear_conf, risk_conf]
        avg_conf = sum(confidences) / len(confidences)
        variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)
        
        # High variance = low consensus
        if variance < 0.02 and abs(final_score) > 0.3:
            return "strong"
        elif variance < 0.05 and abs(final_score) > 0.2:
            return "moderate"
        elif variance < 0.10:
            return "weak"
        else:
            return "none"
    
    def _recommend_position_size(self, action: str, consensus_level: str, 
                                risk_score: float, financial_context: Dict[str, Any]) -> str:
        """Recommend appropriate position size"""
        if action == "hold":
            return "none"
        
        # Base sizing
        if consensus_level == "strong":
            base_size = "full"
        elif consensus_level == "moderate":
            base_size = "reduced"
        else:
            base_size = "minimal"
        
        # Risk adjustment
        if risk_score > 0.7:
            # High risk - reduce size
            if base_size == "full":
                return "reduced"
            elif base_size == "reduced":
                return "minimal"
            else:
                return "minimal"
        
        # Market context adjustment
        market_phase = financial_context.get("market_phase", "normal")
        if market_phase == "crisis":
            # In crisis, be more conservative
            if base_size == "full":
                return "reduced"
            elif base_size == "reduced":
                return "minimal"
        
        return base_size
    
    def _generate_rationale(self, action: str, final_score: float,
                          bull_conf: float, bear_conf: float, 
                          risk_score: float, consensus_level: str,
                          financial_context: Dict[str, Any]) -> str:
        """Generate transparent rationale for the verdict"""
        
        parts = []
        
        # Decision summary
        if action == "buy":
            parts.append(f"BULLISH verdict with {abs(final_score)*100:.1f}% conviction")
        elif action == "sell":
            parts.append(f"BEARISH verdict with {abs(final_score)*100:.1f}% conviction")
        else:
            parts.append(f"NEUTRAL verdict - insufficient evidence for directional bet")
        
        # Agent confidence summary
        parts.append(f"Bullish confidence: {bull_conf*100:.1f}% | Bearish confidence: {bear_conf*100:.1f}%")
        
        # Risk consideration
        if risk_score > 0.6:
            parts.append(f"High risk score ({risk_score:.2f}) moderates position sizing")
        elif risk_score < 0.3:
            parts.append(f"Low risk profile ({risk_score:.2f}) supports conviction")
        
        # Consensus level
        if consensus_level == "strong":
            parts.append("Strong agent consensus supports this verdict")
        elif consensus_level == "none":
            parts.append("Limited consensus - verdict reflects cautious interpretation")
        
        # Financial context
        market_phase = financial_context.get("market_phase", "normal")
        if market_phase != "normal":
            parts.append(f"{market_phase.replace('_', ' ').title()} market context considered in weighting")
        
        return " | ".join(parts)
    
    def deliberate_multi_agent(self, 
                               symbol: str,
                               technical_argument: Dict[str, Any],
                               fundamental_argument: Dict[str, Any],
                               macro_argument: Dict[str, Any],
                               sentiment_argument: Dict[str, Any],
                               quantitative_argument: Dict[str, Any],
                               risk_assessment: Dict[str, Any],
                               financial_context: Dict[str, Any]) -> JudicialVerdict:
        """
        Deliberate with all 6 independent agents' arguments
        Each agent has already determined its own stance
        """
        log.info(f"JudgeAgent: Multi-agent deliberation for {symbol}")
        start_time = time.time()
        
        try:
            # Collect all agent stances and confidences
            agents = {
                "technical": technical_argument,
                "fundamental": fundamental_argument,
                "macro": macro_argument,
                "sentiment": sentiment_argument,
                "quantitative": quantitative_argument,
                "risk": risk_assessment
            }
            
            # Count stances
            stance_counts = {"bullish": 0, "bearish": 0, "neutral": 0, "critique": 0}
            total_confidence = 0
            
            for agent_name, agent_arg in agents.items():
                stance = agent_arg.get("stance", "neutral")
                confidence = agent_arg.get("confidence", 0.5)
                
                if stance in stance_counts:
                    stance_counts[stance] += 1
                
                # Weight by confidence
                if stance == "bullish":
                    total_confidence += confidence
                elif stance == "bearish":
                    total_confidence -= confidence
                # neutral and critique don't add to directional confidence
            
            # Get risk info
            risk_score = risk_assessment.get("risk_score", 0.5)
            risk_level = risk_assessment.get("risk_level", "moderate")
            
            # Calculate consensus score
            total_agents = 6
            bullish_pct = stance_counts["bullish"] / total_agents
            bearish_pct = stance_counts["bearish"] / total_agents
            
            # Determine consensus level
            if bullish_pct >= 0.67 or bearish_pct >= 0.67:
                consensus_level = "strong"
            elif bullish_pct >= 0.5 or bearish_pct >= 0.5:
                consensus_level = "moderate"
            elif max(bullish_pct, bearish_pct) >= 0.33:
                consensus_level = "weak"
            else:
                consensus_level = "none"
            
            # Weight agents by importance
            agent_weights = {
                "technical": 0.15,
                "fundamental": 0.25,
                "macro": 0.15,
                "sentiment": 0.10,
                "quantitative": 0.20,
                "risk": 0.15
            }
            
            # Calculate weighted score
            weighted_score = 0
            for agent_name, agent_arg in agents.items():
                stance = agent_arg.get("stance", "neutral")
                confidence = agent_arg.get("confidence", 0.5)
                weight = agent_weights.get(agent_name, 0.15)
                
                if stance == "bullish":
                    weighted_score += confidence * weight
                elif stance == "bearish":
                    weighted_score -= confidence * weight
                # neutral doesn't contribute
            
            # Apply context adjustments
            context_adjustment = self._apply_context_adjustments(
                weighted_score, financial_context, risk_score
            )
            
            final_score = weighted_score + context_adjustment
            
            # Determine action
            action = self._determine_action(final_score, risk_score)
            
            # Determine position size
            position_size = self._recommend_position_size(
                action, consensus_level, risk_score, financial_context
            )
            
            # Generate rationale
            parts = []
            if action == "buy":
                parts.append(f"BULLISH verdict: {stance_counts['bullish']}/{total_agents} agents bullish")
            elif action == "sell":
                parts.append(f"BEARISH verdict: {stance_counts['bearish']}/{total_agents} agents bearish")
            else:
                parts.append(f"NEUTRAL verdict: Mixed signals from {total_agents} agents")
            
            parts.append(f"Consensus level: {consensus_level.upper()}")
            parts.append(f"Risk assessment: {risk_level.upper()} ({risk_score:.2f})")
            parts.append(f"Technical: {technical_argument.get('stance', 'neutral')} | "
                        f"Fundamental: {fundamental_argument.get('stance', 'neutral')} | "
                        f"Macro: {macro_argument.get('stance', 'neutral')}")
            
            rationale = " | ".join(parts)
            
            judge_duration = time.time() - start_time
            
            log.info(f"JudgeAgent: Multi-agent verdict - {action.upper()} (confidence: {abs(final_score):.2f})")
            
            return JudicialVerdict(
                action=action,
                confidence=abs(final_score),
                score=final_score,
                rationale=rationale,
                consensus_level=consensus_level,
                risk_flags=risk_assessment.get("points", [])[:5],
                recommended_position_size=position_size,
                timestamp=datetime.now(),
                judge_duration=judge_duration
            )
            
        except Exception as e:
            log.error(f"JudgeAgent: Multi-agent deliberation error: {e}")
            return JudicialVerdict(
                action="hold",
                confidence=0.5,
                score=0.0,
                rationale=f"Deliberation error: {str(e)}. Defaulting to hold.",
                consensus_level="weak",
                risk_flags=["analysis_error"],
                recommended_position_size="minimal",
                timestamp=datetime.now(),
                judge_duration=time.time() - start_time
            )
    
    def format_verdict_for_display(self, verdict: JudicialVerdict) -> Dict[str, Any]:
        """Format verdict for frontend display"""
        return {
            "agent": self.agent_id,
            "stance": "verdict",
            "action": verdict.action.upper(),
            "confidence": round(verdict.confidence, 3),
            "score": round(verdict.score, 3),
            "rationale": verdict.rationale,
            "consensus_level": verdict.consensus_level,
            "risk_flags": verdict.risk_flags,
            "recommended_position_size": verdict.recommended_position_size,
            "deliberation_time": round(verdict.judge_duration, 2),
            "timestamp": verdict.timestamp.isoformat()
        }
