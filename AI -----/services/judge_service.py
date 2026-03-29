"""
Enhanced Judge Service
Maximum reasoning capability with quality evaluation and best reasoning selection
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.data_structures import (
    DebateSession, AgentArgument, PositionStance, JudicialVerdict, OrderDecision,
    TradingSignal, OrderType, SignalType
)

log = logging.getLogger(__name__)


class ReasoningQuality(Enum):
    """Quality levels for reasoning"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    WEAK = "weak"
    POOR = "poor"


@dataclass
class ArgumentEvaluation:
    """Detailed evaluation of an argument"""
    agent_id: str
    agent_type: str
    stance: str
    
    # Quality scores (0-1)
    logical_consistency: float
    data_support: float
    historical_success: float
    risk_awareness: float
    persuasiveness: float
    
    # Overall
    overall_quality: float
    quality_label: ReasoningQuality
    
    # Specific issues found
    logical_flaws: List[str]
    missing_data: List[str]
    risk_concerns: List[str]
    
    # Recommendation
    recommended_action: str  # "accept", "question", "reject"


@dataclass
class SelectedReasoning:
    """The selected best reasoning"""
    selected_agent_id: str
    selection_criteria: List[str]
    winning_argument: str
    key_strengths: List[str]
    dissent_acknowledged: bool
    confidence_in_selection: float


class JudgeService:
    """
    Enhanced Judge Service: Evaluates reasoning quality and selects best argument
    
    Like a chief investment officer reviewing analyst recommendations:
    - Doesn't average opinions
    - Evaluates each argument on its merits
    - Selects the best reasoning regardless of popularity
    - Acknowledges but doesn't defer to dissent
    """
    
    def __init__(self):
        self.decision_history: List[JudicialVerdict] = []
        self.agent_track_record: Dict[str, List[Dict]] = {}
        
        # Evaluation weights
        self.eval_weights = {
            'logical_consistency': 0.25,
            'data_support': 0.25,
            'historical_success': 0.20,
            'risk_awareness': 0.15,
            'persuasiveness': 0.15
        }
        
        log.info("Enhanced JudgeService initialized")
    
    def render_verdict(self, debate_session: DebateSession,
                      risk_assessment: Optional[Dict] = None) -> JudicialVerdict:
        """
        Render verdict by evaluating all arguments and selecting best reasoning
        """
        log.info(f"Rendering verdict for {debate_session.symbol}")
        
        # Step 1: Evaluate all arguments
        evaluations = self._evaluate_all_arguments(debate_session)
        
        # Step 2: Select best reasoning
        selected = self._select_best_reasoning(debate_session, evaluations)
        
        # Step 3: Determine winning stance (based on best reasoning, not majority)
        winning_stance = self._determine_winning_stance(selected, debate_session)
        
        # Step 4: Calculate agreement level
        agreement_level = self._calculate_quality_weighted_agreement(
            debate_session, evaluations
        )
        
        # Step 5: Calculate conviction
        conviction = self._calculate_conviction(selected, evaluations)
        
        # Step 6: Gather dissenting views
        dissenting = self._gather_dissent(selected, debate_session, evaluations)
        
        # Step 7: Create order decision
        order_decision = self._create_order_decision(
            selected, winning_stance, conviction, risk_assessment
        )
        
        # Build verdict
        verdict = JudicialVerdict(
            symbol=debate_session.symbol,
            winning_stance=winning_stance,
            agreement_level=agreement_level,
            conviction_level=conviction,
            best_reasoning=self._format_best_reasoning(selected, evaluations),
            dissenting_views=dissenting,
            order_decision=order_decision,
            timestamp=datetime.now()
        )
        
        # Track decision
        self._track_decision(verdict, evaluations)
        
        log.info(f"Verdict: {winning_stance.value} based on {selected.selected_agent_id} "
                f"(conf: {conviction:.1%}, quality: {selected.confidence_in_selection:.1%})")
        
        return verdict
    
    def _evaluate_all_arguments(self, session: DebateSession) -> List[ArgumentEvaluation]:
        """Evaluate each argument's reasoning quality"""
        evaluations = []
        
        for arg in session.arguments:
            # Get agent track record
            history = self.agent_track_record.get(arg.agent_id, [])
            
            # 1. Logical Consistency
            logic_score = self._evaluate_logic(arg)
            logic_flaws = self._find_logical_flaws(arg)
            
            # 2. Data Support
            data_score = self._evaluate_data_support(arg)
            missing_data = self._find_missing_data(arg)
            
            # 3. Historical Success
            hist_score = self._evaluate_historical_success(arg, history)
            
            # 4. Risk Awareness
            risk_score = self._evaluate_risk_awareness(arg)
            risk_concerns = self._find_risk_concerns(arg)
            
            # 5. Persuasiveness
            persuasion_score = self._evaluate_persuasiveness(arg, session)
            
            # Overall quality
            overall = (
                logic_score * self.eval_weights['logical_consistency'] +
                data_score * self.eval_weights['data_support'] +
                hist_score * self.eval_weights['historical_success'] +
                risk_score * self.eval_weights['risk_awareness'] +
                persuasion_score * self.eval_weights['persuasiveness']
            )
            
            # Quality label
            if overall >= 0.80:
                label = ReasoningQuality.EXCELLENT
                action = "accept"
            elif overall >= 0.65:
                label = ReasoningQuality.GOOD
                action = "accept"
            elif overall >= 0.50:
                label = ReasoningQuality.ACCEPTABLE
                action = "question"
            elif overall >= 0.35:
                label = ReasoningQuality.WEAK
                action = "question"
            else:
                label = ReasoningQuality.POOR
                action = "reject"
            
            evaluations.append(ArgumentEvaluation(
                agent_id=arg.agent_id,
                agent_type=arg.agent_type.value if arg.agent_type else 'unknown',
                stance=arg.stance.value,
                logical_consistency=round(logic_score, 2),
                data_support=round(data_score, 2),
                historical_success=round(hist_score, 2),
                risk_awareness=round(risk_score, 2),
                persuasiveness=round(persuasion_score, 2),
                overall_quality=round(overall, 2),
                quality_label=label,
                logical_flaws=logic_flaws,
                missing_data=missing_data,
                risk_concerns=risk_concerns,
                recommended_action=action
            ))
        
        return sorted(evaluations, key=lambda e: e.overall_quality, reverse=True)
    
    def _evaluate_logic(self, arg: AgentArgument) -> float:
        """Evaluate logical consistency of argument"""
        score = 0.5  # Base
        
        # Check for reasoning
        if arg.reasoning and len(arg.reasoning) > 50:
            score += 0.2
        
        # Supporting factors present
        if arg.supporting_factors:
            score += min(0.2, len(arg.supporting_factors) * 0.05)
        
        # Opposing factors show balanced thinking
        if arg.opposing_factors:
            score += 0.1
        
        # Confidence appropriate for position size
        if arg.position_size_pct > 0.05 and arg.confidence < 0.7:
            score -= 0.15  # Penalty for oversized low-confidence position
        
        return max(0, min(1, score))
    
    def _find_logical_flaws(self, arg: AgentArgument) -> List[str]:
        """Identify logical flaws in argument"""
        flaws = []
        
        if arg.confidence > 0.9 and arg.position_size_pct < 0.02:
            flaws.append("High confidence but very small position size")
        
        if arg.confidence < 0.5 and arg.stance.value != 'hold':
            flaws.append("Low confidence but taking directional position")
        
        if not arg.supporting_factors:
            flaws.append("No supporting factors provided")
        
        return flaws
    
    def _evaluate_data_support(self, arg: AgentArgument) -> float:
        """Evaluate quality of data supporting the argument"""
        score = 0.4  # Base
        
        # Supporting factors as data points
        if arg.supporting_factors:
            score += min(0.3, len(arg.supporting_factors) * 0.1)
        
        # Specificity of reasoning
        if arg.reasoning:
            specificity_indicators = ['%', 'pct', 'bp', 'days', 'price', 'level']
            if any(ind in arg.reasoning.lower() for ind in specificity_indicators):
                score += 0.15
        
        return max(0, min(1, score))
    
    def _find_missing_data(self, arg: AgentArgument) -> List[str]:
        """Identify missing data that would strengthen argument"""
        missing = []
        
        if 'volatility' not in arg.reasoning.lower() and arg.agent_type.value != 'conservative':
            missing.append("Volatility assessment")
        
        if 'drawdown' not in arg.reasoning.lower() and 'stop' not in arg.reasoning.lower():
            missing.append("Risk/drawdown analysis")
        
        return missing
    
    def _evaluate_historical_success(self, arg: AgentArgument, history: List[Dict]) -> float:
        """Evaluate agent's historical success rate"""
        if not history:
            return 0.5  # Neutral if no history
        
        # Recent success rate (last 10 decisions)
        recent = history[-10:]
        success_rate = sum(1 for h in recent if h.get('correct', False)) / len(recent)
        
        # Weight recent performance more
        return 0.4 + success_rate * 0.6
    
    def _evaluate_risk_awareness(self, arg: AgentArgument) -> float:
        """Evaluate how well risk is considered"""
        score = 0.4  # Base
        
        # Opposing factors show risk awareness
        if arg.opposing_factors:
            score += min(0.3, len(arg.opposing_factors) * 0.1)
        
        # Position size appropriate for confidence
        expected_size = arg.confidence * 0.08  # Max 8%
        size_diff = abs(arg.position_size_pct - expected_size)
        score += 0.2 * max(0, 1 - size_diff * 10)
        
        return max(0, min(1, score))
    
    def _find_risk_concerns(self, arg: AgentArgument) -> List[str]:
        """Identify risk concerns"""
        concerns = []
        
        if arg.position_size_pct > 0.05 and arg.confidence < 0.75:
            concerns.append("Position size large relative to confidence")
        
        if not arg.opposing_factors:
            concerns.append("No acknowledgment of risks/opposing views")
        
        return concerns
    
    def _evaluate_persuasiveness(self, arg: AgentArgument, session) -> float:
        """Evaluate how persuasive the argument is"""
        score = arg.confidence  # Base on confidence
        
        # Risk manager gets bonus for authority
        if arg.agent_type and arg.agent_type.value == 'risk_manager':
            score += 0.1
        
        # Clear reasoning helps
        if arg.reasoning and len(arg.reasoning) > 100:
            score += 0.1
        
        return max(0, min(1, score))
    
    def _select_best_reasoning(self, session: DebateSession,
                              evaluations: List[ArgumentEvaluation]) -> SelectedReasoning:
        """Select the best argument based on quality, not popularity"""
        
        # Get highest quality evaluation
        best_eval = evaluations[0] if evaluations else None
        
        if not best_eval:
            return SelectedReasoning(
                selected_agent_id="none",
                selection_criteria=["No valid arguments"],
                winning_argument="Hold due to lack of quality arguments",
                key_strengths=[],
                dissent_acknowledged=False,
                confidence_in_selection=0.0
            )
        
        # Find the actual argument
        selected_arg = None
        for arg in session.arguments:
            if arg.agent_id == best_eval.agent_id:
                selected_arg = arg
                break
        
        criteria = [
            f"Logical consistency: {best_eval.logical_consistency:.0%}",
            f"Data support: {best_eval.data_support:.0%}",
            f"Historical success: {best_eval.historical_success:.0%}",
            f"Risk awareness: {best_eval.risk_awareness:.0%}"
        ]
        
        strengths = []
        if best_eval.logical_consistency > 0.8:
            strengths.append("Strong logical consistency")
        if best_eval.data_support > 0.7:
            strengths.append("Well-supported by data")
        if best_eval.historical_success > 0.7:
            strengths.append("Good track record")
        if best_eval.risk_awareness > 0.7:
            strengths.append("Thoughtful risk assessment")
        
        return SelectedReasoning(
            selected_agent_id=best_eval.agent_id,
            selection_criteria=criteria,
            winning_argument=selected_arg.reasoning if selected_arg else "",
            key_strengths=strengths,
            dissent_acknowledged=len(evaluations) > 1 and evaluations[1].overall_quality > 0.5,
            confidence_in_selection=best_eval.overall_quality
        )
    
    def _determine_winning_stance(self, selected: SelectedReasoning,
                                 session: DebateSession) -> PositionStance:
        """Determine stance based on best reasoning"""
        # Find the stance of the selected agent
        for arg in session.arguments:
            if arg.agent_id == selected.selected_agent_id:
                return arg.stance
        
        return PositionStance.HOLD
    
    def _calculate_quality_weighted_agreement(self, session: DebateSession,
                                            evaluations: List[ArgumentEvaluation]) -> float:
        """Calculate agreement weighted by argument quality"""
        if not evaluations:
            return 0.0
        
        # Group by stance with quality weights
        stance_weights = {}
        for eval in evaluations:
            stance = eval.stance
            stance_weights[stance] = stance_weights.get(stance, 0) + eval.overall_quality
        
        if not stance_weights:
            return 0.0
        
        # Find dominant stance
        total_weight = sum(stance_weights.values())
        dominant_weight = max(stance_weights.values())
        
        return dominant_weight / total_weight if total_weight > 0 else 0.0
    
    def _calculate_conviction(self, selected: SelectedReasoning,
                            evaluations: List[ArgumentEvaluation]) -> float:
        """Calculate conviction based on selection confidence and quality spread"""
        base_conviction = selected.confidence_in_selection
        
        # If there's a strong second place, reduce conviction
        if len(evaluations) > 1:
            second_quality = evaluations[1].overall_quality
            quality_spread = base_conviction - second_quality
            
            # Wider spread = higher conviction
            if quality_spread > 0.3:
                conviction_boost = 0.1
            elif quality_spread > 0.15:
                conviction_boost = 0.05
            else:
                conviction_boost = -0.05  # Close race = lower conviction
            
            base_conviction += conviction_boost
        
        return round(max(0.3, min(0.95, base_conviction)), 2)
    
    def _gather_dissent(self, selected: SelectedReasoning,
                       session: DebateSession,
                       evaluations: List[ArgumentEvaluation]) -> List[Dict]:
        """Gather dissenting views that had quality reasoning"""
        dissent = []
        
        selected_stance = None
        for arg in session.arguments:
            if arg.agent_id == selected.selected_agent_id:
                selected_stance = arg.stance
                break
        
        for eval in evaluations[1:]:  # Skip best
            # Only include dissent with reasonable quality
            if eval.overall_quality >= 0.4 and eval.stance != selected_stance:
                dissent.append({
                    'agent_id': eval.agent_id,
                    'agent_type': eval.agent_type,
                    'stance': eval.stance,
                    'quality_score': eval.overall_quality,
                    'key_concerns': eval.risk_concerns + eval.logical_flaws[:2]
                })
        
        return dissent
    
    def _create_order_decision(self, selected: SelectedReasoning,
                             stance: PositionStance,
                             conviction: float,
                             risk_assessment: Optional[Dict]) -> OrderDecision:
        """Create executable order from verdict"""
        
        if stance == PositionStance.BUY:
            order_type = OrderType.MARKET_BUY
        elif stance == PositionStance.SELL:
            order_type = OrderType.MARKET_SELL
        else:
            order_type = OrderType.HOLD
        
        # Position size based on conviction
        base_size = conviction * 0.06  # Max 6% at max conviction
        
        # Risk limits
        if risk_assessment:
            max_position = risk_assessment.get('max_single_position', 0.05)
            base_size = min(base_size, max_position)
            
            if risk_assessment.get('risk_level') == 'high':
                base_size *= 0.5
        
        return OrderDecision(
            symbol="",  # Will be set by caller
            order_type=order_type,
            position_size_pct=round(base_size, 4),
            conviction=conviction,
            execution_window_hours=24 if conviction > 0.7 else 48,
            constraints={'max_slippage': 0.001}
        )
    
    def _format_best_reasoning(self, selected: SelectedReasoning,
                             evaluations: List[ArgumentEvaluation]) -> Dict:
        """Format the best reasoning for output"""
        best_eval = evaluations[0] if evaluations else None
        
        return {
            'selected_from_agent': selected.selected_agent_id,
            'selection_confidence': selected.confidence_in_selection,
            'selection_criteria': selected.selection_criteria,
            'primary_argument': selected.winning_argument[:500] if selected.winning_argument else "",
            'key_strengths': selected.key_strengths,
            'quality_scores': {
                'logical_consistency': best_eval.logical_consistency if best_eval else 0,
                'data_support': best_eval.data_support if best_eval else 0,
                'risk_awareness': best_eval.risk_awareness if best_eval else 0
            }
        }
    
    def _track_decision(self, verdict: JudicialVerdict, evaluations: List[ArgumentEvaluation]):
        """Track decision for future evaluation"""
        self.decision_history.append(verdict)
        
        # Update agent track records
        for eval in evaluations:
            if eval.agent_id not in self.agent_track_record:
                self.agent_track_record[eval.agent_id] = []
    
    def update_with_outcome(self, symbol: str, timestamp: datetime,
                           predicted_stance: str, actual_return: float):
        """Update track record with actual outcome"""
        actually_bullish = actual_return > 0.01
        correct = ((predicted_stance == 'buy' and actually_bullish) or
                  (predicted_stance == 'sell' and actual_return < -0.01) or
                  (predicted_stance == 'hold' and abs(actual_return) < 0.01))
        
        # Find relevant verdict and update agent records
        for verdict in self.decision_history:
            if verdict.symbol == symbol:
                for agent_id in self.agent_track_record:
                    self.agent_track_record[agent_id].append({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'correct': correct,
                        'return': actual_return
                    })


# Global instance
judge_service = JudgeService()
