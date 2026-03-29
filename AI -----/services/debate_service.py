"""
DebateService - Multi-agent debate and consensus mechanism
Phase 4 Implementation
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from core.data_structures import (
    DebateSession, AgentArgument, PositionStance, AgentType, TradingSignal
)
from core.exceptions import DebateError

log = logging.getLogger(__name__)


class DebateService:
    """
    Multi-round debate system where agents critique each other's positions.
    Facilitates belief updates through structured discussion.
    """
    
    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
        self.debate_history = []
        log.info(f"DebateService initialized (max_rounds={max_rounds})")
    
    def conduct_debate(self, session: DebateSession) -> DebateSession:
        """
        Conduct multi-round debate on a trading decision
        
        Args:
            session: DebateSession with initial arguments
            
        Returns:
            Updated session with debate results
        """
        log.info(f"Starting debate for {session.symbol}")
        
        for round_num in range(1, self.max_rounds + 1):
            log.info(f"Debate Round {round_num}/{self.max_rounds}")
            
            # Agents critique each other
            critiques = self._generate_critiques(session, round_num)
            session.critiques.append(critiques)
            
            # Agents update beliefs based on critiques
            updates = self._update_beliefs(session, critiques, round_num)
            session.belief_updates.append(updates)
            
            # Check for convergence
            if self._check_convergence(session, round_num):
                log.info(f"Debate converged at round {round_num}")
                break
        
        session.end_time = datetime.now()
        self.debate_history.append(session)
        
        return session
    
    def _generate_critiques(self, session: DebateSession, 
                           round_num: int) -> Dict[str, List[Dict]]:
        """
        Generate critiques from agents to each other
        
        Returns:
            Dict mapping agent_id to list of critiques
        """
        critiques = {}
        
        for agent_arg in session.arguments:
            agent_critiques = []
            
            # Critique agents with opposing views
            for other_arg in session.arguments:
                if other_arg.agent_id == agent_arg.agent_id:
                    continue
                
                # Only critique if stance differs
                if other_arg.stance != agent_arg.stance:
                    critique = self._create_critique(agent_arg, other_arg, round_num)
                    if critique:
                        agent_critiques.append(critique)
            
            critiques[agent_arg.agent_id] = agent_critiques
        
        return critiques
    
    def _create_critique(self, from_arg: AgentArgument, 
                        to_arg: AgentArgument, round_num: int) -> Dict:
        """Create a critique from one agent to another"""
        critique_points = []
        
        # Critique confidence if too high/low
        if to_arg.confidence > 0.85:
            critique_points.append(f"High confidence ({to_arg.confidence:.1%}) may indicate overconfidence")
        if to_arg.confidence < 0.55:
            critique_points.append(f"Low confidence ({to_arg.confidence:.1%}) suggests weak signal")
        
        # Critique position sizing
        if to_arg.position_size_pct > 0.07:
            critique_points.append(f"Large position size ({to_arg.position_size_pct:.1%}) increases risk")
        
        # Critique lack of opposing factors
        if not to_arg.opposing_factors:
            critique_points.append("No opposing factors listed - potential confirmation bias")
        
        # Round-specific critiques
        if round_num == 1:
            critique_points.append("Initial position - may not have considered all scenarios")
        elif round_num == 2:
            critique_points.append("Position after Round 1 - consider if critiques are valid")
        
        return {
            'from_agent': from_arg.agent_id,
            'to_agent': to_arg.agent_id,
            'stance_difference': f"{from_arg.stance.value} vs {to_arg.stance.value}",
            'points': critique_points,
            'round': round_num
        }
    
    def _update_beliefs(self, session: DebateSession,
                       critiques: Dict, round_num: int) -> Dict[str, Dict]:
        """
        Update agent beliefs based on critiques received
        
        Returns:
            Dict mapping agent_id to belief updates
        """
        updates = {}
        
        for agent_arg in session.arguments:
            agent_critiques = critiques.get(agent_arg.agent_id, [])
            
            if not agent_critiques:
                updates[agent_arg.agent_id] = {
                    'confidence_change': 0.0,
                    'stance_change': False,
                    'reason': 'No critiques received'
                }
                continue
            
            # Count critique severity
            total_critiques = sum(len(c['points']) for c in agent_critiques)
            
            # Update confidence based on critique strength
            confidence_delta = -0.05 * min(total_critiques, 3)
            new_confidence = max(0.3, min(0.95, agent_arg.confidence + confidence_delta))
            
            # Possible stance flip if confidence drops significantly and contrary evidence strong
            stance_flipped = False
            if new_confidence < 0.5 and total_critiques >= 3:
                # Check if there are strong opposing positions
                opposing_confidence = sum(
                    a.confidence for a in session.arguments
                    if a.stance != agent_arg.stance
                )
                supporting_confidence = sum(
                    a.confidence for a in session.arguments
                    if a.stance == agent_arg.stance and a.agent_id != agent_arg.agent_id
                )
                
                if opposing_confidence > supporting_confidence * 1.5:
                    stance_flipped = True
                    new_confidence = 0.55  # Reset to moderate confidence
            
            updates[agent_arg.agent_id] = {
                'confidence_change': confidence_delta,
                'new_confidence': new_confidence,
                'stance_change': stance_flipped,
                'previous_stance': agent_arg.stance.value if stance_flipped else None,
                'critiques_received': total_critiques,
                'reason': f'Updated after {len(agent_critiques)} critiques'
            }
            
            # Update the argument in place
            agent_arg.confidence = new_confidence
            if stance_flipped:
                # Flip stance
                if agent_arg.stance == PositionStance.BUY:
                    agent_arg.stance = PositionStance.SELL
                elif agent_arg.stance == PositionStance.SELL:
                    agent_arg.stance = PositionStance.BUY
        
        return updates
    
    def _check_convergence(self, session: DebateSession, round_num: int) -> bool:
        """
        Check if debate has converged to consensus
        
        Returns:
            True if debate should end early
        """
        if round_num < 2:
            return False
        
        # Check if 70%+ agents agree
        stances = [a.stance.value for a in session.arguments]
        
        from collections import Counter
        stance_counts = Counter(stances)
        
        for stance, count in stance_counts.items():
            if count >= len(session.arguments) * 0.7:
                log.info(f"Consensus reached: {stance} ({count}/{len(session.arguments)})")
                return True
        
        # Check if no significant changes in last round
        if len(session.belief_updates) >= 2:
            last_update = session.belief_updates[-1]
            prev_update = session.belief_updates[-2]
            
            significant_changes = sum(
                1 for agent_id, update in last_update.items()
                if abs(update.get('confidence_change', 0)) > 0.1
            )
            
            if significant_changes == 0:
                log.info("Debate stabilized - no significant changes")
                return True
        
        return False
    
    def get_debate_summary(self, session: DebateSession) -> Dict:
        """
        Get summary of debate results
        
        Returns:
            Summary dict with consensus info and agent positions
        """
        final_stances = [a.stance.value for a in session.arguments]
        final_confidences = [a.confidence for a in session.arguments]
        
        from collections import Counter
        stance_counts = Counter(final_stances)
        
        # Determine consensus stance
        consensus_stance = stance_counts.most_common(1)[0][0]
        consensus_count = stance_counts[most_common[0]]
        
        return {
            'symbol': session.symbol,
            'rounds_conducted': len(session.critiques),
            'consensus_stance': consensus_stance,
            'consensus_agreement': consensus_count / len(session.arguments),
            'average_confidence': sum(final_confidences) / len(final_confidences),
            'stance_distribution': dict(stance_counts),
            'risk_override': session.risk_override,
            'debate_duration_seconds': (
                (session.end_time - session.start_time).total_seconds()
                if session.end_time else None
            )
        }
    
    def get_agent_agreement_matrix(self, session: DebateSession) -> Dict:
        """
        Calculate pairwise agreement between agents
        
        Returns:
            Matrix of agreement scores
        """
        matrix = {}
        
        for arg1 in session.arguments:
            matrix[arg1.agent_id] = {}
            for arg2 in session.arguments:
                if arg1.agent_id == arg2.agent_id:
                    matrix[arg1.agent_id][arg2.agent_id] = 1.0
                else:
                    # Agreement based on stance and confidence difference
                    stance_agreement = 1.0 if arg1.stance == arg2.stance else 0.0
                    confidence_diff = abs(arg1.confidence - arg2.confidence)
                    confidence_agreement = 1.0 - confidence_diff
                    
                    matrix[arg1.agent_id][arg2.agent_id] = (
                        stance_agreement * 0.7 + confidence_agreement * 0.3
                    )
        
        return matrix
    
    def get_debate_history(self, symbol: Optional[str] = None,
                          days: int = 30) -> List[DebateSession]:
        """Get historical debates"""
        cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
        
        filtered = [
            s for s in self.debate_history
            if s.start_time > cutoff
            and (symbol is None or s.symbol == symbol)
        ]
        
        return filtered


# Global instance
debate_service = DebateService()
