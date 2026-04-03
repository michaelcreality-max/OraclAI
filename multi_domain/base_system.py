"""
OraclAI Multi-Domain AI System
Base Multi-Agent Architecture with Self-Learning
All domain systems inherit from this base
"""

import threading
import time
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentPosition:
    """Represents an agent's position on a query"""
    agent_name: str
    stance: str  # 'positive', 'negative', 'neutral', 'constructive', 'critical', 'analytical'
    confidence: float  # 0.0 to 1.0
    reasoning: str
    key_points: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)  # For tracking training data

@dataclass
class ConsensusResult:
    """Final result from multi-agent debate"""
    consensus_reached: bool
    final_answer: str
    confidence: float
    agent_positions: List[AgentPosition]
    debate_rounds: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """Base class for all domain agents with self-learning capabilities"""
    
    def __init__(self, name: str, role: str, expertise: List[str]):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.position = None
        self.learning_enabled = True
        self.performance_history = []
        self.specialization_weights = {exp: 1.0 for exp in expertise}
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        """Override in subclass to provide domain-specific analysis"""
        raise NotImplementedError
    
    def critique(self, other_position: AgentPosition, query: str) -> str:
        """Override to provide critique of other agents' positions"""
        return f"{self.name} acknowledges {other_position.agent_name}'s perspective."
    
    def learn_from_feedback(self, feedback_score: float, query: str, position: AgentPosition):
        """Learn from user feedback to improve future responses"""
        if not self.learning_enabled:
            return
        
        # Store performance data
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'query_hash': hash(query) % 10000,
            'feedback_score': feedback_score,
            'confidence': position.confidence,
            'stance': position.stance
        })
        
        # Adjust specialization weights based on feedback
        if feedback_score >= 4.0:  # Good feedback
            for key_point in position.key_points:
                area = key_point.split(':')[0] if ':' in key_point else key_point
                if area in self.specialization_weights:
                    self.specialization_weights[area] = min(2.0, self.specialization_weights[area] + 0.1)
        elif feedback_score <= 2.0:  # Poor feedback
            for key_point in position.key_points:
                area = key_point.split(':')[0] if ':' in key_point else key_point
                if area in self.specialization_weights:
                    self.specialization_weights[area] = max(0.5, self.specialization_weights[area] - 0.1)
    
    def get_specialization_score(self, area: str) -> float:
        """Get current specialization score for an area"""
        return self.specialization_weights.get(area, 1.0)
    
    def calibrate_confidence(self, predicted_confidence: float) -> float:
        """Calibrate confidence based on historical performance"""
        if len(self.performance_history) < 10:
            return predicted_confidence
        
        # Calculate accuracy vs confidence correlation
        recent = self.performance_history[-20:]
        avg_feedback = sum(p['feedback_score'] for p in recent) / len(recent)
        avg_confidence = sum(p['confidence'] for p in recent) / len(recent)
        
        # If consistently overconfident, reduce confidence
        if avg_confidence > 0.8 and avg_feedback < 3.5:
            return predicted_confidence * 0.85
        
        # If underconfident but performing well, increase confidence
        if avg_confidence < 0.6 and avg_feedback > 4.0:
            return min(0.95, predicted_confidence * 1.1)
        
        return predicted_confidence


class MultiAgentSystem:
    """Base multi-agent debate system with training integration"""
    
    def __init__(self, domain_name: str, max_rounds: int = 3, enable_training: bool = True):
        self.domain_name = domain_name
        self.max_rounds = max_rounds
        self.agents: List[BaseAgent] = []
        self.active_sessions: Dict[str, Dict] = {}
        self.session_lock = threading.Lock()
        self.enable_training = enable_training
        self._training_engine = None
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent to the system"""
        self.agents.append(agent)
    
    def start_debate(self, query: str, context: Dict = None) -> str:
        """Start a new debate session"""
        session_id = f"{self.domain_name}_{int(time.time())}_{hash(query) % 10000}"
        
        with self.session_lock:
            self.active_sessions[session_id] = {
                'query': query,
                'context': context or {},
                'status': 'running',
                'round': 0,
                'agent_positions': {},
                'consensus': None,
                'start_time': datetime.now().isoformat()
            }
        
        # Run debate in background thread
        thread = threading.Thread(
            target=self._run_debate,
            args=(session_id, query, context or {})
        )
        thread.daemon = True
        thread.start()
        
        return session_id
    
    def _run_debate(self, session_id: str, query: str, context: Dict):
        """Execute the multi-agent debate"""
        try:
            positions = []
            
            # Round 1: Initial analysis from all agents
            for agent in self.agents:
                position = agent.analyze(query, context)
                positions.append(position)
                
                with self.session_lock:
                    self.active_sessions[session_id]['agent_positions'][agent.name] = position
                    self.active_sessions[session_id]['round'] = 1
            
            # Rounds 2-N: Critique and refinement
            for round_num in range(2, self.max_rounds + 1):
                refined_positions = []
                
                for agent in self.agents:
                    # Agent critiques other positions and refines their own
                    critiques = []
                    for other_pos in positions:
                        if other_pos.agent_name != agent.name:
                            critique = agent.critique(other_pos, query)
                            critiques.append(critique)
                    
                    # Refine position based on critiques
                    refined = self._refine_position(agent, positions, critiques, query, context)
                    refined_positions.append(refined)
                    
                    with self.session_lock:
                        self.active_sessions[session_id]['agent_positions'][agent.name] = refined
                        self.active_sessions[session_id]['round'] = round_num
                
                positions = refined_positions
            
            # Generate consensus
            consensus = self._generate_consensus(positions, query)
            
            with self.session_lock:
                self.active_sessions[session_id]['consensus'] = consensus
                self.active_sessions[session_id]['status'] = 'complete'
                
        except Exception as e:
            with self.session_lock:
                self.active_sessions[session_id]['status'] = 'error'
                self.active_sessions[session_id]['error'] = str(e)
    
    def _refine_position(self, agent: BaseAgent, all_positions: List[AgentPosition], 
                         critiques: List[str], query: str, context: Dict) -> AgentPosition:
        """Refine agent position based on critiques - override in subclass"""
        # Default: return slightly modified position
        original = next(p for p in all_positions if p.agent_name == agent.name)
        
        # Increase confidence if strong consensus
        avg_confidence = sum(p.confidence for p in all_positions) / len(all_positions)
        new_confidence = (original.confidence + avg_confidence) / 2
        
        return AgentPosition(
            agent_name=agent.name,
            stance=original.stance,
            confidence=round(new_confidence, 2),
            reasoning=original.reasoning + f"\n[Refined considering {len(critiques)} critiques]",
            key_points=original.key_points
        )
    
    def _generate_consensus(self, positions: List[AgentPosition], query: str) -> ConsensusResult:
        """Generate final consensus from agent positions"""
        # Calculate overall confidence
        avg_confidence = sum(p.confidence for p in positions) / len(positions) if positions else 0
        
        # Determine if consensus reached (agents generally agree)
        stances = [p.stance for p in positions]
        unique_stances = set(stances)
        consensus_reached = len(unique_stances) <= 2  # Agree or split between two views
        
        # Build answer from positions
        answer_parts = []
        for pos in positions:
            answer_parts.append(f"**{pos.agent_name}** ({pos.stance}, {pos.confidence:.0%} confidence):\n{pos.reasoning}")
        
        final_answer = "\n\n".join(answer_parts)
        
        # Add consensus summary if reached
        if consensus_reached:
            dominant_stance = max(set(stances), key=stances.count)
            supporting = [p for p in positions if p.stance == dominant_stance]
            avg_support_conf = sum(p.confidence for p in supporting) / len(supporting)
            
            final_answer = f"**🎯 CONSENSUS: {dominant_stance.upper()}** ({avg_support_conf:.0%} confidence)\n\n" + final_answer
        else:
            final_answer = "**⚖️ DIVERGENT VIEWS** (No clear consensus)\n\n" + final_answer
        
        return ConsensusResult(
            consensus_reached=consensus_reached,
            final_answer=final_answer,
            confidence=round(avg_confidence, 2),
            agent_positions=positions,
            debate_rounds=self.max_rounds,
            metadata={'query': query, 'domain': self.domain_name}
        )
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get current debate status"""
        with self.session_lock:
            session = self.active_sessions.get(session_id, {})
            return {
                'session_id': session_id,
                'status': session.get('status', 'unknown'),
                'round': session.get('round', 0),
                'total_rounds': self.max_rounds,
                'agent_count': len(self.agents),
                'has_consensus': session.get('consensus') is not None
            }
    
    def get_result(self, session_id: str) -> ConsensusResult:
        """Get final debate result"""
        with self.session_lock:
            session = self.active_sessions.get(session_id, {})
            return session.get('consensus')
    
    def record_performance(self, session_id: str, feedback_score: float = None):
        """Record performance data for training"""
        if not self.enable_training:
            return
        
        try:
            from ai_training_framework import training_engine
            
            with self.session_lock:
                session = self.active_sessions.get(session_id, {})
                consensus = session.get('consensus')
                query = session.get('query', '')
                context = session.get('context', {})
                
                if consensus:
                    # Record each agent's performance
                    for position in consensus.agent_positions:
                        training_engine.record_query(
                            agent_name=position.agent_name,
                            query=query,
                            context=context,
                            position=position,
                            consensus_reached=consensus.consensus_reached
                        )
                        
                        # Record feedback if provided
                        if feedback_score:
                            training_engine.record_feedback(
                                session_id=session_id,
                                agent_name=position.agent_name,
                                query=query,
                                user_rating=feedback_score
                            )
                            
                            # Agent learns from feedback
                            agent = next((a for a in self.agents if a.name == position.agent_name), None)
                            if agent:
                                agent.learn_from_feedback(feedback_score, query, position)
        except Exception as e:
            print(f"[Training] Error recording performance: {e}")
    
    def get_training_stats(self) -> Dict:
        """Get training statistics for this domain"""
        try:
            from ai_training_framework import get_training_dashboard
            return get_training_dashboard()
        except Exception as e:
            return {"error": str(e)}
    
    def submit_feedback(self, session_id: str, user_rating: int, feedback_text: str = ""):
        """Submit user feedback for a completed session"""
        self.record_performance(session_id, feedback_score=user_rating)
        
        # Return updated stats
        return {
            "success": True,
            "session_id": session_id,
            "rating_recorded": user_rating,
            "message": "Thank you for your feedback! The AI will learn from this."
        }
    
    def run_advanced_consensus(self, positions: List[AgentPosition], strategy: str = 'confidence_weighted') -> Dict:
        """Run advanced ensemble voting for better consensus"""
        try:
            from ai_advanced_improvements import ensemble_voting
            return ensemble_voting.vote(positions, strategy)
        except Exception as e:
            print(f"[AdvancedConsensus] Error: {e}")
            return {"consensus": "error", "confidence": 0.0}
    
    def run_adversarial_debate(self, query: str, rounds: int = 3) -> Dict:
        """Run adversarial training debate for robustness"""
        try:
            from ai_advanced_improvements import adversarial_training
            return adversarial_training.conduct_adversarial_debate(query, self.agents, rounds)
        except Exception as e:
            print(f"[AdversarialDebate] Error: {e}")
            return {"error": str(e)}
    
    def get_realtime_metrics(self) -> Dict:
        """Get real-time performance metrics"""
        try:
            from ai_advanced_improvements import performance_monitor
            return performance_monitor.get_dashboard()
        except Exception as e:
            return {"error": str(e)}
