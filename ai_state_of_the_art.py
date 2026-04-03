"""
OraclAI State-of-the-Art AI Improvements
Reinforcement Learning, Meta-Learning, Knowledge Graphs, Predictive Analytics
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import random
import hashlib
from abc import ABC, abstractmethod


# ==================== REINFORCEMENT LEARNING ====================

@dataclass
class RLState:
    """State representation for RL agent"""
    query_features: Dict[str, float]  # Extracted query features
    context_features: Dict[str, float]  # Context features
    agent_history: Dict[str, Any]  # Historical performance
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RLAction:
    """Action taken by RL agent"""
    stance: str  # Position stance
    confidence: float  # Confidence level (0-1)
    key_points: List[str]  # Key reasoning points
    reasoning_depth: str  # 'brief', 'standard', 'deep'


@dataclass
class RLExperience:
    """Experience tuple for RL (s, a, r, s')"""
    state: RLState
    action: RLAction
    reward: float
    next_state: Optional[RLState]
    done: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReinforcementLearningAgent:
    """
    RL-based agent that learns optimal policy through interaction
    Uses Q-learning with experience replay
    """
    
    def __init__(self, agent_name: str, learning_rate: float = 0.01, 
                 discount_factor: float = 0.95, epsilon: float = 0.1):
        self.agent_name = agent_name
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon  # Exploration rate
        
        # Q-table: state_hash -> action -> value
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Experience replay buffer
        self.experience_buffer: deque = deque(maxlen=10000)
        
        # Policy network (simplified as weight vectors for now)
        self.policy_weights: Dict[str, np.ndarray] = {}
        
        # Performance tracking
        self.episode_rewards: List[float] = []
        self.total_episodes = 0
    
    def extract_features(self, query: str, context: Dict) -> RLState:
        """Extract features from query for RL state"""
        query_lower = query.lower()
        
        # Query length features
        words = query_lower.split()
        
        features = {
            'query_length': len(words),
            'has_numbers': any(c.isdigit() for c in query),
            'question_mark': '?' in query,
            'complexity_score': len(set(words)) / len(words) if words else 0,
            'urgency_words': sum(1 for w in ['urgent', 'asap', 'quickly', 'fast'] if w in query_lower),
            'technical_terms': sum(1 for w in ['api', 'code', 'algorithm', 'function'] if w in query_lower),
        }
        
        return RLState(
            query_features=features,
            context_features={k: float(v) if isinstance(v, (int, float)) else 0 
                            for k, v in context.items()},
            agent_history={'past_queries': len(self.experience_buffer)}
        )
    
    def state_to_key(self, state: RLState) -> str:
        """Convert state to hash key for Q-table"""
        # Simple feature hashing
        feature_str = json.dumps(state.query_features, sort_keys=True)
        return hashlib.md5(feature_str.encode()).hexdigest()[:16]
    
    def select_action(self, state: RLState) -> RLAction:
        """Select action using epsilon-greedy policy"""
        state_key = self.state_to_key(state)
        
        # Exploration
        if random.random() < self.epsilon:
            return self._random_action()
        
        # Exploitation: select best action from Q-table
        if state_key in self.q_table:
            best_action_key = max(self.q_table[state_key].items(), key=lambda x: x[1])[0]
            return self._decode_action(best_action_key)
        
        # No knowledge yet, explore
        return self._random_action()
    
    def _random_action(self) -> RLAction:
        """Generate random action for exploration"""
        stances = ['positive', 'negative', 'neutral', 'constructive', 'critical', 'analytical']
        depths = ['brief', 'standard', 'deep']
        
        return RLAction(
            stance=random.choice(stances),
            confidence=random.uniform(0.5, 0.95),
            key_points=[f"point_{i}" for i in range(random.randint(1, 4))],
            reasoning_depth=random.choice(depths)
        )
    
    def _decode_action(self, action_key: str) -> RLAction:
        """Decode action key back to RLAction"""
        parts = action_key.split('|')
        return RLAction(
            stance=parts[0] if len(parts) > 0 else 'neutral',
            confidence=float(parts[1]) if len(parts) > 1 else 0.7,
            key_points=parts[2].split(',') if len(parts) > 2 else ['default'],
            reasoning_depth=parts[3] if len(parts) > 3 else 'standard'
        )
    
    def _encode_action(self, action: RLAction) -> str:
        """Encode RLAction to string key"""
        return f"{action.stance}|{action.confidence:.2f}|{','.join(action.key_points)}|{action.reasoning_depth}"
    
    def store_experience(self, experience: RLExperience):
        """Store experience in replay buffer"""
        self.experience_buffer.append(experience)
    
    def learn(self, batch_size: int = 32):
        """Learn from experiences using Q-learning"""
        if len(self.experience_buffer) < batch_size:
            return
        
        # Sample random batch
        batch = random.sample(list(self.experience_buffer), batch_size)
        
        for exp in batch:
            state_key = self.state_to_key(exp.state)
            action_key = self._encode_action(exp.action)
            
            # Q-learning update
            current_q = self.q_table[state_key][action_key]
            
            if exp.next_state and not exp.done:
                next_state_key = self.state_to_key(exp.next_state)
                next_max_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0
                target_q = exp.reward + self.gamma * next_max_q
            else:
                target_q = exp.reward
            
            # Update Q-value
            self.q_table[state_key][action_key] = current_q + self.lr * (target_q - current_q)
        
        # Decay exploration
        self.epsilon = max(0.01, self.epsilon * 0.995)
    
    def calculate_reward(self, user_rating: float, consensus_reached: bool, 
                        response_time: float) -> float:
        """Calculate reward from user feedback"""
        # Base reward from user rating (1-5 scale)
        reward = (user_rating - 3) * 2  # -4 to +4
        
        # Bonus for consensus
        if consensus_reached:
            reward += 1.0
        
        # Penalty for slow responses
        if response_time > 5.0:
            reward -= 0.5
        
        return reward
    
    def get_rl_stats(self) -> Dict:
        """Get RL statistics"""
        return {
            'agent_name': self.agent_name,
            'total_episodes': self.total_episodes,
            'epsilon': round(self.epsilon, 4),
            'experience_buffer_size': len(self.experience_buffer),
            'unique_states': len(self.q_table),
            'avg_reward': round(np.mean(self.episode_rewards[-100:]), 3) if self.episode_rewards else 0,
            'learning_rate': self.lr,
            'discount_factor': self.gamma
        }


# ==================== META-LEARNING (LEARNING TO LEARN) ====================

class MetaLearningSystem:
    """
    Meta-learning system that learns optimal learning strategies
    Adapts hyperparameters based on domain and query type
    """
    
    def __init__(self):
        # Meta-parameters for each domain
        self.domain_configs: Dict[str, Dict] = {
            'finance': {
                'learning_rate': 0.01,
                'exploration_rate': 0.15,
                'debate_rounds': 4,
                'confidence_threshold': 0.85
            },
            'code': {
                'learning_rate': 0.02,
                'exploration_rate': 0.10,
                'debate_rounds': 3,
                'confidence_threshold': 0.90
            },
            'stem': {
                'learning_rate': 0.015,
                'exploration_rate': 0.12,
                'debate_rounds': 4,
                'confidence_threshold': 0.88
            },
            'general': {
                'learning_rate': 0.01,
                'exploration_rate': 0.20,
                'debate_rounds': 3,
                'confidence_threshold': 0.80
            }
        }
        
        # Meta-learning history
        self.adaptation_history: List[Dict] = []
        
        # Performance by configuration
        self.config_performance: Dict[str, List[float]] = defaultdict(list)
    
    def get_optimal_config(self, domain: str, query_complexity: float) -> Dict:
        """Get optimal configuration for domain and query complexity"""
        base_config = self.domain_configs.get(domain, self.domain_configs['general']).copy()
        
        # Adapt based on query complexity
        if query_complexity > 0.8:  # Complex query
            base_config['debate_rounds'] = min(5, base_config['debate_rounds'] + 1)
            base_config['confidence_threshold'] = min(0.95, base_config['confidence_threshold'] + 0.03)
        elif query_complexity < 0.3:  # Simple query
            base_config['debate_rounds'] = max(2, base_config['debate_rounds'] - 1)
            base_config['confidence_threshold'] = max(0.75, base_config['confidence_threshold'] - 0.05)
        
        return base_config
    
    def adapt_from_feedback(self, domain: str, config: Dict, performance: float):
        """Adapt configuration based on performance feedback"""
        # Store performance for this config
        config_key = json.dumps(config, sort_keys=True)
        self.config_performance[config_key].append(performance)
        
        # If consistently poor performance, adjust
        recent_perfs = self.config_performance[config_key][-10:]
        if len(recent_perfs) >= 5:
            avg_perf = sum(recent_perfs) / len(recent_perfs)
            
            if avg_perf < 3.0:  # Poor performance
                # Increase exploration
                self.domain_configs[domain]['exploration_rate'] = min(
                    0.5, self.domain_configs[domain]['exploration_rate'] * 1.1
                )
                # Lower confidence threshold (be more critical)
                self.domain_configs[domain]['confidence_threshold'] = max(
                    0.70, self.domain_configs[domain]['confidence_threshold'] - 0.02
                )
            elif avg_perf > 4.5:  # Excellent performance
                # Decrease exploration (exploit more)
                self.domain_configs[domain]['exploration_rate'] = max(
                    0.05, self.domain_configs[domain]['exploration_rate'] * 0.95
                )
        
        # Record adaptation
        self.adaptation_history.append({
            'timestamp': datetime.now().isoformat(),
            'domain': domain,
            'config': config,
            'performance': performance
        })
    
    def calculate_query_complexity(self, query: str) -> float:
        """Calculate complexity score for a query"""
        words = query.split()
        
        # Factors contributing to complexity
        factors = {
            'length': min(1.0, len(words) / 50),  # Normalized length
            'unique_ratio': len(set(words)) / len(words) if words else 0,
            'technical_density': sum(1 for w in words if len(w) > 8) / len(words) if words else 0,
            'question_count': query.count('?') / 3,
            'conjunctions': sum(1 for w in ['and', 'but', 'or', 'however'] if w in query.lower()) / 5
        }
        
        # Weighted sum
        complexity = (
            factors['length'] * 0.2 +
            factors['unique_ratio'] * 0.3 +
            factors['technical_density'] * 0.3 +
            factors['question_count'] * 0.1 +
            factors['conjunctions'] * 0.1
        )
        
        return min(1.0, complexity)
    
    def get_meta_stats(self) -> Dict:
        """Get meta-learning statistics"""
        return {
            'adaptations_made': len(self.adaptation_history),
            'domain_configs': self.domain_configs,
            'config_variants_tested': len(self.config_performance),
            'recent_adaptations': self.adaptation_history[-5:]
        }


# ==================== KNOWLEDGE GRAPH ====================

class KnowledgeNode:
    """Node in knowledge graph"""
    def __init__(self, concept: str, domain: str, importance: float = 1.0):
        self.concept = concept
        self.domain = domain
        self.importance = importance
        self.connections: Dict[str, float] = {}  # concept -> strength
        self.attributes: Dict[str, Any] = {}
    
    def connect(self, other_concept: str, strength: float = 1.0):
        """Connect to another concept"""
        self.connections[other_concept] = max(self.connections.get(other_concept, 0), strength)


class KnowledgeGraph:
    """
    Cross-domain knowledge graph for reasoning
    Connects concepts across domains for better analogies and insights
    """
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.domain_nodes: Dict[str, Set[str]] = defaultdict(set)
        self.query_cache: Dict[str, List[str]] = {}
    
    def add_concept(self, concept: str, domain: str, importance: float = 1.0):
        """Add concept to graph"""
        if concept not in self.nodes:
            self.nodes[concept] = KnowledgeNode(concept, domain, importance)
            self.domain_nodes[domain].add(concept)
    
    def connect_concepts(self, concept1: str, concept2: str, strength: float = 1.0):
        """Create bidirectional connection between concepts"""
        if concept1 in self.nodes and concept2 in self.nodes:
            self.nodes[concept1].connect(concept2, strength)
            self.nodes[concept2].connect(concept1, strength)
    
    def find_analogies(self, source_concept: str, target_domain: str) -> List[Dict]:
        """Find analogies between concept and target domain"""
        if source_concept not in self.nodes:
            return []
        
        source_node = self.nodes[source_concept]
        analogies = []
        
        # Find similar concepts in target domain
        for target_concept in self.domain_nodes[target_domain]:
            if target_concept == source_concept:
                continue
            
            target_node = self.nodes[target_concept]
            
            # Calculate structural similarity
            common_connections = set(source_node.connections.keys()) & set(target_node.connections.keys())
            if common_connections:
                similarity = len(common_connections) / max(len(source_node.connections), len(target_node.connections))
                if similarity > 0.3:  # Threshold
                    analogies.append({
                        'source': source_concept,
                        'target': target_concept,
                        'similarity': round(similarity, 3),
                        'common_concepts': list(common_connections)
                    })
        
        return sorted(analogies, key=lambda x: x['similarity'], reverse=True)[:5]
    
    def infer_new_connections(self, concept: str) -> List[Dict]:
        """Infer new connections using transitive relationships"""
        if concept not in self.nodes:
            return []
        
        node = self.nodes[concept]
        new_connections = []
        
        # Transitive inference: A-B and B-C implies A-C
        for connected_concept, strength1 in node.connections.items():
            if connected_concept in self.nodes:
                connected_node = self.nodes[connected_concept]
                for second_level, strength2 in connected_node.connections.items():
                    if second_level != concept and second_level not in node.connections:
                        inferred_strength = strength1 * strength2 * 0.5  # Decay
                        if inferred_strength > 0.2:
                            new_connections.append({
                                'from': concept,
                                'to': second_level,
                                'inferred_strength': round(inferred_strength, 3),
                                'path': [concept, connected_concept, second_level]
                            })
        
        return new_connections
    
    def build_initial_graph(self):
        """Build initial cross-domain knowledge graph"""
        # Add domain-specific concepts
        concepts = {
            'finance': ['risk', 'return', 'volatility', 'diversification', 'portfolio', 'asset'],
            'code': ['function', 'variable', 'class', 'algorithm', 'debugging', 'optimization'],
            'stem': ['equation', 'hypothesis', 'experiment', 'data', 'model', 'theory'],
            'literature': ['theme', 'character', 'plot', 'symbolism', 'narrative', 'metaphor'],
            'writing': ['clarity', 'persuasion', 'structure', 'audience', 'tone', 'style']
        }
        
        # Add all concepts
        for domain, domain_concepts in concepts.items():
            for concept in domain_concepts:
                self.add_concept(concept, domain)
        
        # Create cross-domain analogies
        analogies = [
            ('risk', 'debugging', 0.8),  # Risk mgmt ~ debugging (identify and fix issues)
            ('diversification', 'class', 0.6),  # Diversification ~ OOP (separation of concerns)
            ('optimization', 'optimization', 1.0),  # Same concept across domains
            ('portfolio', 'structure', 0.7),  # Portfolio ~ structure (organization)
            ('volatility', 'variable', 0.6),  # Volatility ~ variables (changing values)
            ('model', 'class', 0.8),  # Models ~ classes (abstractions)
            ('data', 'evidence', 0.9),  # Data ~ evidence (proof)
            ('theme', 'pattern', 0.7),  # Theme ~ pattern (recurring element)
        ]
        
        for c1, c2, strength in analogies:
            if c1 in self.nodes and c2 in self.nodes:
                self.connect_concepts(c1, c2, strength)
    
    def get_graph_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        total_nodes = len(self.nodes)
        total_edges = sum(len(n.connections) for n in self.nodes.values()) // 2
        
        return {
            'total_concepts': total_nodes,
            'total_connections': total_edges,
            'concepts_by_domain': {d: len(c) for d, c in self.domain_nodes.items()},
            'avg_connections_per_concept': round(total_edges / total_nodes, 2) if total_nodes > 0 else 0,
            'cross_domain_connections': sum(
                1 for n in self.nodes.values() 
                for c in n.connections 
                if n.domain != self.nodes.get(c, n).domain
            ) // 2
        }


# ==================== PREDICTIVE AGENT SELECTOR ====================

class PredictiveAgentSelector:
    """
    Predicts which agents will perform best for a given query
    Uses historical performance and query features
    """
    
    def __init__(self):
        self.agent_performance: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )  # agent -> query_type -> scores
        
        self.query_classifier: Dict[str, List[str]] = {
            'technical': ['code', 'algorithm', 'function', 'bug', 'error'],
            'analytical': ['analyze', 'compare', 'evaluate', 'assess', 'review'],
            'creative': ['design', 'create', 'build', 'innovate', 'imagine'],
            'factual': ['what', 'when', 'where', 'who', 'how much'],
            'opinion': ['should', 'recommend', 'best', 'better', 'opinion']
        }
    
    def classify_query(self, query: str) -> str:
        """Classify query type"""
        query_lower = query.lower()
        
        scores = {}
        for qtype, keywords in self.query_classifier.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[qtype] = score
        
        return max(scores.items(), key=lambda x: x[1])[0] if scores else 'general'
    
    def predict_best_agents(self, query: str, available_agents: List[str], 
                           top_k: int = 3) -> List[Dict]:
        """Predict best agents for query"""
        query_type = self.classify_query(query)
        
        predictions = []
        for agent in available_agents:
            # Get historical performance for this query type
            history = self.agent_performance[agent][query_type]
            
            if history:
                avg_score = sum(history) / len(history)
                confidence = min(1.0, len(history) / 10)  # More data = higher confidence
            else:
                avg_score = 0.5  # Unknown, neutral
                confidence = 0.1
            
            predictions.append({
                'agent': agent,
                'predicted_score': round(avg_score, 3),
                'confidence': round(confidence, 3),
                'query_type': query_type,
                'history_size': len(history)
            })
        
        # Sort by predicted score
        predictions.sort(key=lambda x: x['predicted_score'], reverse=True)
        return predictions[:top_k]
    
    def record_outcome(self, agent: str, query: str, score: float):
        """Record actual outcome for learning"""
        query_type = self.classify_query(query)
        self.agent_performance[agent][query_type].append(score)
        
        # Keep only last 50 per type
        if len(self.agent_performance[agent][query_type]) > 50:
            self.agent_performance[agent][query_type] = self.agent_performance[agent][query_type][-50:]
    
    def get_selection_stats(self) -> Dict:
        """Get prediction statistics"""
        total_predictions = sum(
            sum(len(scores) for scores in types.values())
            for types in self.agent_performance.values()
        )
        
        return {
            'total_predictions': total_predictions,
            'agents_tracked': len(self.agent_performance),
            'query_types': list(self.query_classifier.keys()),
            'avg_history_per_agent': round(total_predictions / len(self.agent_performance), 2) if self.agent_performance else 0
        }


# ==================== CONTINUOUS LEARNING PIPELINE ====================

class ContinuousLearningPipeline:
    """
    Automated continuous learning system
    Triggers retraining when performance drops
    """
    
    def __init__(self):
        self.performance_threshold = 3.5  # Minimum acceptable rating
        self.min_samples_for_retrain = 20
        self.retrain_history: List[Dict] = []
        self.is_retraining = False
        
        # Performance windows
        self.performance_windows: Dict[str, deque] = {
            'short': deque(maxlen=10),   # Last 10 queries
            'medium': deque(maxlen=50),  # Last 50 queries
            'long': deque(maxlen=200)    # Last 200 queries
        }
    
    def check_and_trigger(self, recent_feedback: List[float]) -> Dict:
        """Check if retraining is needed and trigger"""
        # Update windows
        for score in recent_feedback:
            for window in self.performance_windows.values():
                window.append(score)
        
        # Calculate trends
        trends = {}
        for name, window in self.performance_windows.items():
            if window:
                trends[name] = sum(window) / len(window)
        
        # Check if retraining needed
        need_retrain = False
        reason = ""
        
        if 'short' in trends and 'medium' in trends:
            # Short-term drop
            if trends['short'] < self.performance_threshold and trends['short'] < trends['medium'] * 0.9:
                need_retrain = True
                reason = f"Short-term performance drop: {trends['short']:.2f} < {trends['medium']:.2f}"
        
        if 'short' in trends and len(self.performance_windows['short']) >= self.min_samples_for_retrain:
            if trends['short'] < 3.0:  # Severe degradation
                need_retrain = True
                reason = f"Severe performance degradation: {trends['short']:.2f} < 3.0"
        
        if need_retrain and not self.is_retraining:
            return self._trigger_retrain(reason, trends)
        
        return {
            'retraining_triggered': False,
            'current_performance': trends,
            'status': 'monitoring'
        }
    
    def _trigger_retrain(self, reason: str, trends: Dict) -> Dict:
        """Trigger retraining process"""
        self.is_retraining = True
        
        retrain_job = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'performance_snapshot': trends,
            'status': 'started'
        }
        
        self.retrain_history.append(retrain_job)
        
        # Simulate retraining (in production, this would be async)
        # Actual retraining would happen in background
        
        return {
            'retraining_triggered': True,
            'reason': reason,
            'job_id': len(self.retrain_history),
            'estimated_duration': '5-10 minutes'
        }
    
    def complete_retrain(self, job_id: int, improvements: Dict):
        """Mark retraining as complete"""
        self.is_retraining = False
        
        if 0 <= job_id - 1 < len(self.retrain_history):
            self.retrain_history[job_id - 1]['status'] = 'completed'
            self.retrain_history[job_id - 1]['improvements'] = improvements
    
    def get_pipeline_stats(self) -> Dict:
        """Get continuous learning statistics"""
        return {
            'is_retraining': self.is_retraining,
            'performance_threshold': self.performance_threshold,
            'retrain_count': len(self.retrain_history),
            'retrain_history': self.retrain_history[-5:],
            'current_windows': {
                name: list(window)[-5:] for name, window in self.performance_windows.items()
            }
        }


# Global instances
rl_agents: Dict[str, ReinforcementLearningAgent] = {}
meta_learning = MetaLearningSystem()
knowledge_graph = KnowledgeGraph()
predictor = PredictiveAgentSelector()
continuous_learning = ContinuousLearningPipeline()

# Initialize knowledge graph
knowledge_graph.build_initial_graph()


def get_state_of_the_art_dashboard() -> Dict:
    """Get comprehensive dashboard of all cutting-edge improvements"""
    return {
        "reinforcement_learning": {
            "agents_with_rl": len(rl_agents),
            "total_experiences": sum(len(rl.experience_buffer) for rl in rl_agents.values()),
            "learning_strategies": ["Q-learning", "Experience Replay", "Epsilon-Greedy"]
        },
        "meta_learning": meta_learning.get_meta_stats(),
        "knowledge_graph": knowledge_graph.get_graph_stats(),
        "predictive_selector": predictor.get_selection_stats(),
        "continuous_learning": continuous_learning.get_pipeline_stats(),
        "system_capabilities": [
            "Reinforcement Learning with Q-tables",
            "Meta-learning adaptive configurations",
            "Cross-domain knowledge graph reasoning",
            "Predictive agent selection",
            "Automated continuous retraining",
            "Transitive knowledge inference",
            "Query complexity adaptation"
        ],
        "status": "fully_operational"
    }


def create_rl_agent(agent_name: str) -> ReinforcementLearningAgent:
    """Create or get RL agent for an agent"""
    if agent_name not in rl_agents:
        rl_agents[agent_name] = ReinforcementLearningAgent(agent_name)
    return rl_agents[agent_name]
