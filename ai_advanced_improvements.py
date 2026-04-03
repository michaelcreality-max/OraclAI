"""
OraclAI Advanced AI Improvements
Cross-domain learning, ensemble voting, adversarial training
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentVote:
    """Represents a weighted vote from an agent"""
    agent_name: str
    stance: str
    confidence: float
    weight: float  # Ensemble weight based on historical performance
    reasoning: str


class EnsembleVotingSystem:
    """
    Advanced ensemble voting with confidence weighting and performance tracking
    """
    
    def __init__(self):
        self.agent_weights: Dict[str, float] = defaultdict(lambda: 1.0)
        self.performance_history: Dict[str, List[Dict]] = defaultdict(list)
        self.voting_strategies = {
            'weighted_average': self._weighted_average_vote,
            'confidence_weighted': self._confidence_weighted_vote,
            'expert_cascade': self._expert_cascade_vote,
            'democratic': self._democratic_vote
        }
    
    def vote(self, agent_positions: List[Any], strategy: str = 'confidence_weighted') -> Dict:
        """
        Generate consensus using specified voting strategy
        
        Strategies:
        - weighted_average: Simple weighted average of all positions
        - confidence_weighted: Weight by confidence * historical accuracy
        - expert_cascade: Trust experts first, fall back to others
        - democratic: Equal weight, majority rules
        """
        if strategy not in self.voting_strategies:
            strategy = 'confidence_weighted'
        
        return self.voting_strategies[strategy](agent_positions)
    
    def _weighted_average_vote(self, positions: List[Any]) -> Dict:
        """Simple weighted average of agent positions"""
        if not positions:
            return {"consensus": "no_agreement", "confidence": 0.0}
        
        # Get weights for each agent
        weighted_stances = defaultdict(float)
        total_weight = 0.0
        
        for pos in positions:
            weight = self.agent_weights.get(pos.agent_name, 1.0) * pos.confidence
            weighted_stances[pos.stance] += weight
            total_weight += weight
        
        # Find winning stance
        if weighted_stances:
            winning_stance = max(weighted_stances.items(), key=lambda x: x[1])
            confidence = winning_stance[1] / total_weight if total_weight > 0 else 0.0
            
            return {
                "consensus": winning_stance[0],
                "confidence": round(confidence, 3),
                "stance_distribution": dict(weighted_stances),
                "method": "weighted_average"
            }
        
        return {"consensus": "no_agreement", "confidence": 0.0}
    
    def _confidence_weighted_vote(self, positions: List[Any]) -> Dict:
        """Weight votes by confidence calibrated with historical performance"""
        if not positions:
            return {"consensus": "no_agreement", "confidence": 0.0}
        
        calibrated_positions = []
        for pos in positions:
            # Calibrate confidence based on agent's historical accuracy
            historical_acc = self._get_historical_accuracy(pos.agent_name)
            calibrated_conf = pos.confidence * (0.5 + 0.5 * historical_acc)
            
            calibrated_positions.append({
                'agent': pos.agent_name,
                'stance': pos.stance,
                'confidence': calibrated_conf,
                'reasoning': pos.reasoning
            })
        
        # Weight by calibrated confidence
        stance_scores = defaultdict(lambda: {'score': 0.0, 'reasonings': []})
        total_confidence = sum(p['confidence'] for p in calibrated_positions)
        
        for pos in calibrated_positions:
            weight = pos['confidence'] / total_confidence if total_confidence > 0 else 0
            stance_scores[pos['stance']]['score'] += weight
            stance_scores[pos['stance']]['reasonings'].append({
                'agent': pos['agent'],
                'reasoning': pos['reasoning'],
                'weight': weight
            })
        
        # Get winning stance
        if stance_scores:
            winner = max(stance_scores.items(), key=lambda x: x[1]['score'])
            
            return {
                "consensus": winner[0],
                "confidence": round(winner[1]['score'], 3),
                "stance_distribution": {k: round(v['score'], 3) for k, v in stance_scores.items()},
                "contributing_reasonings": winner[1]['reasonings'][:3],  # Top 3 reasonings
                "method": "confidence_weighted"
            }
        
        return {"consensus": "no_agreement", "confidence": 0.0}
    
    def _expert_cascade_vote(self, positions: List[Any]) -> Dict:
        """Trust high-performing experts first, consult others if experts disagree"""
        # Sort by historical performance
        sorted_positions = sorted(
            positions,
            key=lambda p: self._get_historical_accuracy(p.agent_name),
            reverse=True
        )
        
        # Get top 3 experts
        experts = sorted_positions[:3]
        
        # Check if experts agree
        expert_stances = [p.stance for p in experts]
        if len(set(expert_stances)) == 1:
            # Experts agree
            avg_confidence = sum(p.confidence for p in experts) / len(experts)
            return {
                "consensus": expert_stances[0],
                "confidence": round(avg_confidence, 3),
                "expert_agreement": True,
                "method": "expert_cascade"
            }
        else:
            # Experts disagree, use all agents with democratic vote
            return self._democratic_vote(positions)
    
    def _democratic_vote(self, positions: List[Any]) -> Dict:
        """Equal weight voting - majority rules"""
        stance_counts = defaultdict(int)
        for pos in positions:
            stance_counts[pos.stance] += 1
        
        if stance_counts:
            winner = max(stance_counts.items(), key=lambda x: x[1])
            confidence = winner[1] / len(positions)
            
            return {
                "consensus": winner[0],
                "confidence": round(confidence, 3),
                "stance_distribution": dict(stance_counts),
                "method": "democratic"
            }
        
        return {"consensus": "no_agreement", "confidence": 0.0}
    
    def _get_historical_accuracy(self, agent_name: str) -> float:
        """Get historical accuracy for an agent"""
        history = self.performance_history.get(agent_name, [])
        if not history:
            return 0.5  # Neutral default
        
        # Calculate accuracy from recent history
        recent = history[-20:]
        correct = sum(1 for h in recent if h.get('correct', False))
        return correct / len(recent)
    
    def update_agent_performance(self, agent_name: str, prediction_correct: bool, 
                                  confidence: float, actual_outcome: str):
        """Update agent's performance history"""
        self.performance_history[agent_name].append({
            'timestamp': datetime.now().isoformat(),
            'correct': prediction_correct,
            'confidence': confidence,
            'outcome': actual_outcome
        })
        
        # Trim history to last 100 entries
        if len(self.performance_history[agent_name]) > 100:
            self.performance_history[agent_name] = self.performance_history[agent_name][-100:]
        
        # Update weight based on recent performance
        self._recalculate_weight(agent_name)
    
    def _recalculate_weight(self, agent_name: str):
        """Recalculate ensemble weight based on performance"""
        accuracy = self._get_historical_accuracy(agent_name)
        # Weight range: 0.5 to 2.0 based on accuracy
        self.agent_weights[agent_name] = 0.5 + 1.5 * accuracy


class CrossDomainKnowledgeTransfer:
    """
    Enables agents to learn from other domains
    e.g., Finance agent learns patterns from Code agent's logic
    """
    
    def __init__(self):
        self.domain_mappings: Dict[str, Dict[str, str]] = {
            'finance': {
                'risk': 'security',  # Risk management → Security patterns
                'optimization': 'algorithms',  # Portfolio optimization → Algorithm optimization
                'patterns': 'design_patterns',  # Market patterns → Code patterns
            },
            'code': {
                'complexity': 'mathematics',  # Algorithm complexity → Math analysis
                'architecture': 'system_design',  # System design → General design principles
            },
            'stem': {
                'modeling': 'finance',  # Mathematical modeling → Quantitative finance
                'data_analysis': 'finance',  # Data analysis → Financial analysis
            },
            'literature': {
                'narrative': 'user_experience',  # Storytelling → UX design
                'structure': 'architecture',  # Story structure → Code architecture
            }
        }
        self.transfer_history: List[Dict] = []
    
    def find_transfer_opportunities(self, source_domain: str, target_domain: str) -> List[Dict]:
        """Find knowledge that can be transferred between domains"""
        opportunities = []
        
        mappings = self.domain_mappings.get(source_domain, {})
        for concept, target_concept in mappings.items():
            opportunities.append({
                'source_concept': concept,
                'target_concept': target_concept,
                'transfer_type': 'analogical',
                'confidence': 0.7  # Base confidence for analogical transfer
            })
        
        return opportunities
    
    def transfer_knowledge(self, source_agent: str, target_agent: str, 
                           concept: str, knowledge: Dict) -> Dict:
        """Transfer knowledge from one agent/domain to another"""
        # Adapt knowledge to target domain
        adapted = self._adapt_knowledge(knowledge, source_agent, target_agent)
        
        # Record transfer
        self.transfer_history.append({
            'timestamp': datetime.now().isoformat(),
            'source': source_agent,
            'target': target_agent,
            'concept': concept,
            'success': adapted is not None
        })
        
        return {
            'transferred': adapted is not None,
            'adapted_knowledge': adapted,
            'source': source_agent,
            'target': target_agent
        }
    
    def _adapt_knowledge(self, knowledge: Dict, source: str, target: str) -> Optional[Dict]:
        """Adapt knowledge from source domain to target domain"""
        # This is a simplified adaptation - in practice would be more sophisticated
        adapted = knowledge.copy()
        adapted['adapted_from'] = source
        adapted['adapted_to'] = target
        adapted['adaptation_timestamp'] = datetime.now().isoformat()
        return adapted
    
    def get_transfer_statistics(self) -> Dict:
        """Get statistics on knowledge transfers"""
        total = len(self.transfer_history)
        successful = sum(1 for t in self.transfer_history if t['success'])
        
        return {
            'total_transfers': total,
            'successful_transfers': successful,
            'success_rate': round(successful / total, 3) if total > 0 else 0,
            'recent_transfers': self.transfer_history[-10:]
        }


class AdversarialTrainingSystem:
    """
    Makes agents more robust through adversarial training
    Agents critique each other's outputs to improve quality
    """
    
    def __init__(self):
        self.critique_history: List[Dict] = []
        self.robustness_scores: Dict[str, float] = defaultdict(lambda: 0.5)
    
    def generate_adversarial_critique(self, position: Any, all_positions: List[Any]) -> str:
        """Generate a challenging critique of an agent's position"""
        critiques = []
        
        # Check for weak reasoning
        if len(position.reasoning) < 50:
            critiques.append("Reasoning is too brief - lacks depth")
        
        # Check for overconfidence
        if position.confidence > 0.9:
            critiques.append("Overconfident - no uncertainty acknowledged")
        
        # Check for stance consistency with key points
        if position.stance == 'positive' and any('risk' in kp.lower() for kp in position.key_points):
            critiques.append("Stance conflicts with identified risks")
        
        # Check for missing perspectives
        other_stances = set(p.stance for p in all_positions if p.agent_name != position.agent_name)
        if len(other_stances) > 1 and position.confidence > 0.8:
            critiques.append("High confidence despite divergent expert opinions")
        
        # Check for evidence gaps
        evidence_indicators = ['because', 'due to', 'data shows', 'research indicates', 'according to']
        has_evidence = any(ind in position.reasoning.lower() for ind in evidence_indicators)
        if not has_evidence:
            critiques.append("Lacks supporting evidence or citations")
        
        return " | ".join(critiques) if critiques else "No major weaknesses identified"
    
    def conduct_adversarial_debate(self, query: str, agents: List[Any], rounds: int = 3) -> Dict:
        """Conduct multi-round adversarial debate for robustness"""
        positions_by_round = []
        
        for round_num in range(rounds):
            round_positions = []
            
            for agent in agents:
                # Get position
                position = agent.analyze(query, {})
                
                # Get adversarial critiques
                critiques = self.generate_adversarial_critique(position, round_positions)
                
                # Agent must respond to critiques
                if round_num > 0:
                    position = self._strengthen_position(agent, position, critiques)
                
                position.metadata['critiques'] = critiques
                position.metadata['round'] = round_num + 1
                
                round_positions.append(position)
            
            positions_by_round.append(round_positions)
        
        # Calculate robustness improvements
        robustness = self._calculate_robustness(positions_by_round)
        
        return {
            'final_positions': positions_by_round[-1],
            'rounds_conducted': rounds,
            'robustness_improvement': robustness['improvement'],
            'average_strengthening': robustness['avg_strengthening'],
            'critiques_addressed': robustness['critiques_addressed']
        }
    
    def _strengthen_position(self, agent: Any, position: Any, critiques: str) -> Any:
        """Strengthen position based on critiques"""
        # This would be more sophisticated in practice
        # For now, adjust confidence based on critique severity
        if len(critiques) > 50:  # Long critique = more issues
            new_confidence = max(0.5, position.confidence - 0.1)
        else:
            new_confidence = min(0.95, position.confidence + 0.05)
        
        position.confidence = round(new_confidence, 2)
        position.metadata['strengthened'] = True
        return position
    
    def _calculate_robustness(self, rounds: List[List[Any]]) -> Dict:
        """Calculate robustness improvements across rounds"""
        if len(rounds) < 2:
            return {'improvement': 0.0, 'avg_strengthening': 0.0, 'critiques_addressed': 0}
        
        first_round_conf = sum(p.confidence for p in rounds[0]) / len(rounds[0])
        last_round_conf = sum(p.confidence for p in rounds[-1]) / len(rounds[-1])
        
        strengthened = sum(
            1 for p in rounds[-1] 
            if p.metadata.get('strengthened', False)
        )
        
        return {
            'improvement': round(last_round_conf - first_round_conf, 3),
            'avg_strengthening': round(strengthened / len(rounds[-1]), 3),
            'critiques_addressed': strengthened
        }


class RealTimePerformanceMonitor:
    """
    Real-time monitoring of AI performance with alerts
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.alert_thresholds = {
            'accuracy_drop': 0.15,  # Alert if accuracy drops 15%
            'latency_spike': 5.0,   # Alert if latency increases 5x
            'error_rate': 0.1       # Alert if error rate > 10%
        }
        self.active_alerts: List[Dict] = []
    
    def record_metric(self, agent_name: str, metric_type: str, value: float, 
                      timestamp: str = None):
        """Record a performance metric"""
        self.metrics[agent_name].append({
            'type': metric_type,
            'value': value,
            'timestamp': timestamp or datetime.now().isoformat()
        })
        
        # Trim to last 1000 entries
        if len(self.metrics[agent_name]) > 1000:
            self.metrics[agent_name] = self.metrics[agent_name][-1000:]
        
        # Check for alerts
        self._check_alerts(agent_name, metric_type, value)
    
    def _check_alerts(self, agent_name: str, metric_type: str, value: float):
        """Check if metric triggers an alert"""
        history = [m for m in self.metrics[agent_name] if m['type'] == metric_type]
        
        if len(history) < 10:
            return
        
        # Calculate baseline (average of last 50)
        baseline = sum(m['value'] for m in history[-50:]) / 50
        
        if metric_type == 'accuracy':
            if baseline - value > self.alert_thresholds['accuracy_drop']:
                self._trigger_alert(agent_name, 'accuracy_drop', baseline, value)
        
        elif metric_type == 'latency':
            if value > baseline * self.alert_thresholds['latency_spike']:
                self._trigger_alert(agent_name, 'latency_spike', baseline, value)
        
        elif metric_type == 'error_rate':
            if value > self.alert_thresholds['error_rate']:
                self._trigger_alert(agent_name, 'high_error_rate', 0, value)
    
    def _trigger_alert(self, agent_name: str, alert_type: str, baseline: float, 
                       current: float):
        """Trigger a performance alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'type': alert_type,
            'baseline': baseline,
            'current': current,
            'severity': 'high' if alert_type == 'high_error_rate' else 'medium'
        }
        self.active_alerts.append(alert)
        
        # Log alert
        print(f"[ALERT] {agent_name}: {alert_type} detected! "
              f"Baseline: {baseline:.3f}, Current: {current:.3f}")
    
    def get_dashboard(self) -> Dict:
        """Get real-time performance dashboard"""
        dashboard = {
            'agents': {},
            'system_health': 'healthy',
            'active_alerts': len(self.active_alerts),
            'alerts': self.active_alerts[-10:]
        }
        
        for agent_name, metrics in self.metrics.items():
            if not metrics:
                continue
            
            recent = metrics[-50:]
            by_type = defaultdict(list)
            
            for m in recent:
                by_type[m['type']].append(m['value'])
            
            dashboard['agents'][agent_name] = {
                'metrics': {
                    metric: {
                        'current': values[-1] if values else 0,
                        'avg_50': sum(values) / len(values) if values else 0,
                        'trend': 'up' if len(values) > 10 and values[-1] > values[-10] else 'down'
                    }
                    for metric, values in by_type.items()
                }
            }
        
        # Determine system health
        if len(self.active_alerts) > 5:
            dashboard['system_health'] = 'degraded'
        if len(self.active_alerts) > 10:
            dashboard['system_health'] = 'critical'
        
        return dashboard
    
    def clear_alerts(self):
        """Clear all active alerts"""
        self.active_alerts = []


# Global instances
ensemble_voting = EnsembleVotingSystem()
cross_domain_transfer = CrossDomainKnowledgeTransfer()
adversarial_training = AdversarialTrainingSystem()
performance_monitor = RealTimePerformanceMonitor()


def get_advanced_ai_dashboard() -> Dict:
    """Get comprehensive advanced AI dashboard"""
    return {
        "ensemble_voting": {
            "strategies_available": list(ensemble_voting.voting_strategies.keys()),
            "agent_weights": dict(ensemble_voting.agent_weights)
        },
        "cross_domain_transfer": cross_domain_transfer.get_transfer_statistics(),
        "performance_monitor": performance_monitor.get_dashboard(),
        "adversarial_training": {
            "status": "active",
            "critiques_generated": len(adversarial_training.critique_history)
        },
        "overall_status": "operational",
        "improvements_active": [
            "Ensemble voting with confidence weighting",
            "Cross-domain knowledge transfer",
            "Adversarial critique generation",
            "Real-time performance monitoring",
            "Historical accuracy tracking"
        ]
    }
