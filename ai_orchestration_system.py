"""
OraclAI Agent Orchestration System
Intelligent routing between debate, collaboration, and hybrid modes
Trains itself to select optimal interaction patterns
"""

import sqlite3
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import numpy as np


@dataclass
class TaskProfile:
    """Profile of a task to determine optimal interaction mode"""
    query: str
    domain: str
    complexity: float  # 0-1
    ambiguity: float   # 0-1 (how controversial/subjective)
    creativity_needed: float  # 0-1
    factual_density: float  # 0-1
    urgency: float  # 0-1
    stakes: str  # 'low', 'medium', 'high', 'critical'
    user_emotion: str  # 'neutral', 'frustrated', 'curious', 'urgent'


@dataclass
class InteractionDecision:
    """Decision on how agents should interact"""
    mode: str  # 'debate', 'collaborate', 'hybrid', 'solo'
    confidence: float  # 0-1
    reasoning: str
    agent_assignments: Dict[str, str]  # agent -> role
    rounds: int
    dynamic_switch: bool  # Allow switching mid-task
    subtasks: List[Dict]  # How to break down the work


class TaskAnalyzer:
    """
    Analyzes tasks to determine characteristics that inform interaction mode
    """
    
    def __init__(self):
        self.debate_indicators = {
            'high_ambiguity': [
                'should', 'best', 'better', 'worse', 'opinion', 'think', 'believe',
                'recommend', 'choose', 'select', 'compare', 'vs', 'versus'
            ],
            'controversial': [
                'controversial', 'debatable', 'disputed', 'argument', 'criticism',
                'flawed', 'problematic', 'concern', 'risk', 'dangerous'
            ],
            'multi_valid': [
                'alternatives', 'options', 'approaches', 'strategies', 'methods',
                'different ways', 'various', 'multiple'
            ],
            'subjective': [
                'beautiful', 'ugly', 'good', 'bad', 'best', 'worst', 'prefer',
                'like', 'dislike', 'favorite', 'opinion'
            ]
        }
        
        self.collaboration_indicators = {
            'complex_build': [
                'build', 'create', 'design', 'implement', 'develop', 'architect',
                'system', 'structure', 'framework', 'platform'
            ],
            'multi_component': [
                'and', 'also', 'additionally', 'furthermore', 'plus', 'with',
                'integrate', 'combine', 'connect', 'link'
            ],
            'creative': [
                'creative', 'innovative', 'novel', 'unique', 'original', 'invent',
                'imagine', 'brainstorm', 'ideate'
            ],
            'synthesis': [
                'synthesize', 'combine', 'merge', 'blend', 'integrate', 'unify',
                'comprehensive', 'holistic', 'complete solution'
            ]
        }
        
        self.solo_indicators = {
            'simple': [
                'what is', 'define', 'explain', 'how to', 'simple', 'basic',
                'quick', 'brief', 'short answer'
            ],
            'factual': [
                'fact', 'data', 'statistic', 'when', 'where', 'who', 'what year',
                'how many', 'calculate', 'formula'
            ]
        }
    
    def analyze(self, query: str, domain: str = 'general') -> TaskProfile:
        """Analyze task to create profile"""
        query_lower = query.lower()
        words = query_lower.split()
        
        # Calculate complexity
        complexity = self._calculate_complexity(query, words)
        
        # Calculate ambiguity (indicates debate potential)
        ambiguity = self._calculate_ambiguity(query_lower)
        
        # Calculate creativity needed
        creativity = self._calculate_creativity(query_lower)
        
        # Calculate factual density
        factual = self._calculate_factual_density(query_lower, words)
        
        # Determine urgency
        urgency = self._calculate_urgency(query_lower)
        
        # Determine stakes
        stakes = self._determine_stakes(query_lower)
        
        return TaskProfile(
            query=query,
            domain=domain,
            complexity=complexity,
            ambiguity=ambiguity,
            creativity_needed=creativity,
            factual_density=factual,
            urgency=urgency,
            stakes=stakes,
            user_emotion='neutral'  # Would be detected separately
        )
    
    def _calculate_complexity(self, query: str, words: List[str]) -> float:
        """Calculate task complexity 0-1"""
        factors = [
            len(words) > 20,  # Long query
            len(set(words)) / len(words) > 0.7,  # High vocabulary diversity
            '?' in query,  # Multiple questions
            any(w in query.lower() for w in ['and', 'but', 'however', 'although']),
            any(w in query.lower() for w in ['optimize', 'algorithm', 'architecture'])
        ]
        return sum(factors) / len(factors)
    
    def _calculate_ambiguity(self, query: str) -> float:
        """Calculate how ambiguous/subjective the task is"""
        debate_score = 0
        for category, indicators in self.debate_indicators.items():
            for indicator in indicators:
                if indicator in query:
                    debate_score += 1
        return min(1.0, debate_score / 5)  # Normalize
    
    def _calculate_creativity(self, query: str) -> float:
        """Calculate creativity requirement"""
        creative_score = 0
        for indicator in self.collaboration_indicators['creative']:
            if indicator in query:
                creative_score += 1
        return min(1.0, creative_score / 3)
    
    def _calculate_factual_density(self, query: str, words: List[str]) -> float:
        """Calculate factual density"""
        factual_count = sum(1 for w in self.solo_indicators['factual'] if w in query)
        return min(1.0, factual_count / 3)
    
    def _calculate_urgency(self, query: str) -> float:
        """Calculate urgency from keywords"""
        urgent_words = ['urgent', 'asap', 'immediately', 'quick', 'fast', 'now', 'emergency']
        return min(1.0, sum(1 for w in urgent_words if w in query) / 2)
    
    def _determine_stakes(self, query: str) -> str:
        """Determine stakes level"""
        critical = ['critical', 'life', 'death', 'safety', 'emergency', 'urgent']
        high = ['important', 'significant', 'major', 'serious', 'consequential']
        
        if any(w in query for w in critical):
            return 'critical'
        elif any(w in query for w in high):
            return 'high'
        elif len(query.split()) < 10:
            return 'low'
        else:
            return 'medium'


class InteractionModeSelector:
    """
    Trained system that decides interaction mode based on task profile
    Learns from feedback which modes work best
    """
    
    def __init__(self, db_path: str = "orchestration_training.db"):
        self.db_path = db_path
        self.task_analyzer = TaskAnalyzer()
        self.decision_history: List[Dict] = []
        self.mode_performance: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )  # task_type -> mode -> scores
        self._init_database()
    
    def _init_database(self):
        """Initialize training database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orchestration_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_query TEXT,
                task_profile TEXT,
                selected_mode TEXT,
                confidence REAL,
                reasoning TEXT,
                outcome_score REAL,
                user_satisfaction REAL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mode_performance (
                task_signature TEXT PRIMARY KEY,
                mode TEXT,
                avg_score REAL,
                usage_count INTEGER,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def decide_interaction_mode(self, query: str, domain: str, 
                               available_agents: List[str]) -> InteractionDecision:
        """
        Decide whether agents should debate, collaborate, or work solo
        This is the core decision-making system that gets trained
        """
        # Analyze task
        profile = self.task_analyzer.analyze(query, domain)
        
        # Get historical performance for similar tasks
        task_signature = self._create_task_signature(profile)
        historical = self._get_historical_performance(task_signature)
        
        # Decision logic with learned weights
        mode_scores = self._score_modes(profile, historical)
        
        # Select best mode
        best_mode = max(mode_scores.items(), key=lambda x: x[1])
        selected_mode = best_mode[0]
        confidence = best_mode[1]
        
        # Build reasoning
        reasoning = self._build_reasoning(profile, selected_mode, mode_scores)
        
        # Assign agents to roles
        assignments = self._assign_agents(selected_mode, available_agents, profile)
        
        # Determine rounds and structure
        rounds = self._determine_rounds(selected_mode, profile)
        
        # Create subtasks
        subtasks = self._create_subtasks(selected_mode, profile, query)
        
        decision = InteractionDecision(
            mode=selected_mode,
            confidence=confidence,
            reasoning=reasoning,
            agent_assignments=assignments,
            rounds=rounds,
            dynamic_switch=profile.complexity > 0.7,
            subtasks=subtasks
        )
        
        # Record decision for training
        self._record_decision(query, profile, decision)
        
        return decision
    
    def _create_task_signature(self, profile: TaskProfile) -> str:
        """Create signature for task similarity matching"""
        # Bucket characteristics
        complexity_bucket = 'high' if profile.complexity > 0.7 else 'med' if profile.complexity > 0.4 else 'low'
        ambiguity_bucket = 'high' if profile.ambiguity > 0.7 else 'med' if profile.ambiguity > 0.4 else 'low'
        
        return f"{profile.domain}_{complexity_bucket}_{ambiguity_bucket}_{profile.stakes}"
    
    def _get_historical_performance(self, task_signature: str) -> Dict:
        """Get historical performance data for similar tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT mode, AVG(outcome_score), COUNT(*) 
            FROM orchestration_decisions 
            WHERE task_profile LIKE ? AND outcome_score IS NOT NULL
            GROUP BY mode
        ''', (f"%{task_signature}%",))
        
        results = {}
        for row in cursor.fetchall():
            results[row[0]] = {'avg_score': row[1], 'count': row[2]}
        
        conn.close()
        return results
    
    def _score_modes(self, profile: TaskProfile, historical: Dict) -> Dict[str, float]:
        """
        Score each interaction mode for this task
        Combines rule-based heuristics with learned preferences
        """
        scores = {
            'debate': 0.5,
            'collaborate': 0.5,
            'hybrid': 0.5,
            'solo': 0.5
        }
        
        # Rule-based adjustments
        if profile.ambiguity > 0.7:
            scores['debate'] += 0.3  # High ambiguity benefits from debate
            scores['hybrid'] += 0.2
        
        if profile.creativity_needed > 0.7:
            scores['collaborate'] += 0.3  # Creative tasks benefit from collaboration
            scores['hybrid'] += 0.2
        
        if profile.complexity > 0.8:
            scores['collaborate'] += 0.2  # Complex tasks need collaboration
            scores['hybrid'] += 0.2
        
        if profile.factual_density > 0.8 and profile.ambiguity < 0.3:
            scores['solo'] += 0.4  # Factual questions don't need debate
        
        if profile.urgency > 0.8:
            scores['solo'] += 0.3  # Urgent = faster solo response
            scores['collaborate'] -= 0.1  # Collaboration takes longer
        
        if profile.stakes in ['high', 'critical']:
            scores['debate'] += 0.2  # High stakes = thorough debate
            scores['hybrid'] += 0.2
        
        # Apply learned preferences from historical
        for mode, data in historical.items():
            if mode in scores and data['count'] >= 5:  # Need minimum samples
                learned_bonus = (data['avg_score'] - 3) / 10  # Normalize around 3/5
                scores[mode] += learned_bonus
        
        return scores
    
    def _build_reasoning(self, profile: TaskProfile, selected_mode: str, 
                        all_scores: Dict) -> str:
        """Build human-readable reasoning for decision"""
        reasons = []
        
        if profile.ambiguity > 0.7:
            reasons.append(f"high ambiguity ({profile.ambiguity:.2f}) suggests multiple valid perspectives")
        
        if profile.creativity_needed > 0.7:
            reasons.append(f"creative component ({profile.creativity_needed:.2f}) benefits from collaborative ideation")
        
        if profile.complexity > 0.8:
            reasons.append(f"high complexity ({profile.complexity:.2f}) requires multi-agent collaboration")
        
        if profile.factual_density > 0.8:
            reasons.append(f"factual nature ({profile.factual_density:.2f}) suitable for direct answer")
        
        if selected_mode == 'debate':
            reasons.append("selected debate mode to explore multiple viewpoints rigorously")
        elif selected_mode == 'collaborate':
            reasons.append("selected collaborative mode to synthesize comprehensive solution")
        elif selected_mode == 'hybrid':
            reasons.append("selected hybrid mode for initial debate then collaborative synthesis")
        else:
            reasons.append("selected solo mode for efficient direct response")
        
        return "; ".join(reasons)
    
    def _assign_agents(self, mode: str, agents: List[str], 
                      profile: TaskProfile) -> Dict[str, str]:
        """Assign agents to roles based on mode"""
        assignments = {}
        
        if mode == 'debate':
            # Assign pro/con roles
            if len(agents) >= 2:
                assignments[agents[0]] = 'advocate'
                assignments[agents[1]] = 'skeptic'
                for i, agent in enumerate(agents[2:], 2):
                    assignments[agent] = 'analyst' if i % 2 == 0 else 'moderator'
        
        elif mode == 'collaborate':
            # Assign collaborative roles
            roles = ['architect', 'implementer', 'reviewer', 'optimizer']
            for i, agent in enumerate(agents):
                assignments[agent] = roles[i % len(roles)]
        
        elif mode == 'hybrid':
            # Debate then collaborate
            mid = len(agents) // 2
            for i, agent in enumerate(agents):
                if i < mid:
                    assignments[agent] = f'debater_{i+1}'
                else:
                    assignments[agent] = f'synthesizer_{i-mid+1}'
        
        else:  # solo
            assignments[agents[0]] = 'primary' if agents else 'none'
        
        return assignments
    
    def _determine_rounds(self, mode: str, profile: TaskProfile) -> int:
        """Determine number of interaction rounds"""
        if mode == 'solo':
            return 1
        elif mode == 'debate':
            base = 3
            if profile.stakes == 'critical':
                base += 2
            return base
        elif mode == 'collaborate':
            return 2 if profile.complexity > 0.6 else 1
        else:  # hybrid
            return 4  # 2 debate rounds + 2 synthesis rounds
    
    def _create_subtasks(self, mode: str, profile: TaskProfile, 
                        query: str) -> List[Dict]:
        """Break down task into subtasks based on mode"""
        subtasks = []
        
        if mode == 'debate':
            subtasks = [
                {'phase': 'opening', 'action': 'present_initial_positions', 'agents': 'all'},
                {'phase': 'clash', 'action': 'critique_opposing_views', 'agents': 'all'},
                {'phase': 'rebuttal', 'action': 'defend_and_refine', 'agents': 'all'},
                {'phase': 'conclusion', 'action': 'summarize_debate', 'agents': 'moderator'}
            ]
        
        elif mode == 'collaborate':
            subtasks = [
                {'phase': 'ideation', 'action': 'generate_components', 'agents': 'all'},
                {'phase': 'integration', 'action': 'combine_into_solution', 'agents': 'architect'},
                {'phase': 'refinement', 'action': 'optimize_and_polish', 'agents': 'all'}
            ]
        
        elif mode == 'hybrid':
            subtasks = [
                {'phase': 'exploration', 'action': 'debate_alternatives', 'agents': 'first_half'},
                {'phase': 'convergence', 'action': 'identify_common_ground', 'agents': 'all'},
                {'phase': 'synthesis', 'action': 'build_unified_solution', 'agents': 'second_half'},
                {'phase': 'validation', 'action': 'verify_completeness', 'agents': 'all'}
            ]
        
        else:  # solo
            subtasks = [
                {'phase': 'analysis', 'action': 'comprehensive_analysis', 'agents': 'primary'},
                {'phase': 'response', 'action': 'generate_answer', 'agents': 'primary'}
            ]
        
        return subtasks
    
    def _record_decision(self, query: str, profile: TaskProfile, 
                        decision: InteractionDecision):
        """Record decision for training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orchestration_decisions
            (task_query, task_profile, selected_mode, confidence, reasoning, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            query,
            json.dumps({
                'domain': profile.domain,
                'complexity': profile.complexity,
                'ambiguity': profile.ambiguity,
                'creativity': profile.creativity_needed,
                'stakes': profile.stakes
            }),
            decision.mode,
            decision.confidence,
            decision.reasoning,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def record_outcome(self, query: str, selected_mode: str, 
                      outcome_score: float, user_satisfaction: float):
        """
        Record actual outcome to train the system
        This is how the system learns which modes work best
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update the decision with outcome
        cursor.execute('''
            UPDATE orchestration_decisions
            SET outcome_score = ?, user_satisfaction = ?
            WHERE task_query = ? AND selected_mode = ?
            ORDER BY id DESC LIMIT 1
        ''', (outcome_score, user_satisfaction, query, selected_mode))
        
        conn.commit()
        conn.close()
        
        # Update in-memory stats
        profile = self.task_analyzer.analyze(query)
        signature = self._create_task_signature(profile)
        self.mode_performance[signature][selected_mode].append(outcome_score)
    
    def get_training_stats(self) -> Dict:
        """Get orchestration training statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total decisions
        cursor.execute("SELECT COUNT(*) FROM orchestration_decisions")
        total = cursor.fetchone()[0]
        
        # Decisions with outcomes (trained)
        cursor.execute("SELECT COUNT(*) FROM orchestration_decisions WHERE outcome_score IS NOT NULL")
        trained = cursor.fetchone()[0]
        
        # Mode distribution
        cursor.execute('''
            SELECT selected_mode, COUNT(*), AVG(outcome_score)
            FROM orchestration_decisions
            WHERE outcome_score IS NOT NULL
            GROUP BY selected_mode
        ''')
        
        mode_stats = {}
        for row in cursor.fetchall():
            mode_stats[row[0]] = {
                'count': row[1],
                'avg_outcome': round(row[2], 3) if row[2] else None
            }
        
        conn.close()
        
        return {
            'total_decisions': total,
            'trained_decisions': trained,
            'training_rate': round(trained / total, 3) if total > 0 else 0,
            'mode_performance': mode_stats,
            'is_learning': trained > 10
        }
    
    def recommend_mode_for_task_type(self, task_signature: str) -> Optional[str]:
        """Recommend best mode based on learned data"""
        if task_signature in self.mode_performance:
            # Find mode with best average score
            best_mode = max(
                self.mode_performance[task_signature].items(),
                key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
            )[0]
            return best_mode
        return None


class CollaborativeWorkSession:
    """
    Manages collaborative (non-debate) work sessions
    Agents build together rather than argue
    """
    
    def __init__(self, session_id: str, agents: List[str], query: str):
        self.session_id = session_id
        self.agents = agents
        self.query = query
        self.contributions: Dict[str, List[Dict]] = {agent: [] for agent in agents}
        self.synthesis = None
        self.round = 0
        self.max_rounds = 3
    
    def run_collaboration_round(self) -> Dict:
        """Run one round of collaborative work"""
        self.round += 1
        
        round_results = {
            'round': self.round,
            'contributions': {},
            'synthesis': None
        }
        
        # Each agent contributes based on their role
        for agent in self.agents:
            contribution = self._generate_contribution(agent, self.round)
            self.contributions[agent].append(contribution)
            round_results['contributions'][agent] = contribution
        
        # Synthesis phase (last round or complex task)
        if self.round == self.max_rounds or self.round > 1:
            round_results['synthesis'] = self._synthesize_contributions()
        
        return round_results
    
    def _generate_contribution(self, agent: str, round_num: int) -> Dict:
        """Generate agent contribution for this round"""
        # In practice, this would call the actual agent
        contribution_types = [
            'component_design', 'implementation_idea', 'optimization_suggestion',
            'edge_case_identification', 'alternative_approach', 'integration_plan'
        ]
        
        return {
            'agent': agent,
            'round': round_num,
            'type': random.choice(contribution_types),
            'content': f"Contribution from {agent} in round {round_num}",
            'confidence': random.uniform(0.7, 0.95)
        }
    
    def _synthesize_contributions(self) -> Dict:
        """Synthesize all contributions into unified output"""
        all_contributions = []
        for agent, contribs in self.contributions.items():
            all_contributions.extend(contribs)
        
        # Sort by confidence
        all_contributions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'synthesis_id': f"syn_{self.session_id}",
            'contributions_used': len(all_contributions),
            'top_contributions': all_contributions[:5],
            'unified_output': "Synthesized output from collaborative work",
            'confidence': sum(c['confidence'] for c in all_contributions) / len(all_contributions) if all_contributions else 0
        }
    
    def get_session_summary(self) -> Dict:
        """Get summary of collaborative session"""
        return {
            'session_id': self.session_id,
            'rounds_completed': self.round,
            'agents_involved': self.agents,
            'total_contributions': sum(len(c) for c in self.contributions.values()),
            'final_synthesis': self.synthesis
        }


class HybridDebateCollaboration:
    """
    Hybrid mode: Debate first to explore, then collaborate to synthesize
    """
    
    def __init__(self, session_id: str, debate_agents: List[str], 
                 synthesis_agents: List[str], query: str):
        self.session_id = session_id
        self.debate_agents = debate_agents
        self.synthesis_agents = synthesis_agents
        self.query = query
        self.debate_phase = 'pending'
        self.debate_positions = []
        self.common_ground = []
        self.final_synthesis = None
    
    def run_debate_phase(self, rounds: int = 2) -> Dict:
        """Run debate phase to explore alternatives"""
        self.debate_phase = 'debating'
        
        # Simulate debate rounds
        for round_num in range(1, rounds + 1):
            for agent in self.debate_agents:
                position = self._generate_position(agent, round_num)
                self.debate_positions.append(position)
        
        # Extract common ground from debate
        self.common_ground = self._identify_common_ground()
        
        return {
            'phase': 'debate_complete',
            'positions_explored': len(self.debate_positions),
            'common_ground_identified': len(self.common_ground),
            'ready_for_synthesis': True
        }
    
    def _generate_position(self, agent: str, round_num: int) -> Dict:
        """Generate debate position"""
        stances = ['pro', 'con', 'neutral', 'alternative']
        return {
            'agent': agent,
            'round': round_num,
            'stance': random.choice(stances),
            'arguments': [f"Argument {i} from {agent}" for i in range(3)],
            'confidence': random.uniform(0.6, 0.9)
        }
    
    def _identify_common_ground(self) -> List[str]:
        """Identify areas of agreement from debate"""
        # In practice, analyze positions for overlaps
        return ["Shared understanding point 1", "Common principle 2", "Agreed fact 3"]
    
    def run_synthesis_phase(self) -> Dict:
        """Run collaborative synthesis phase"""
        self.debate_phase = 'synthesizing'
        
        contributions = []
        for agent in self.synthesis_agents:
            contribution = {
                'agent': agent,
                'phase': 'synthesis',
                'incorporates': self.common_ground[:2],
                'adds_new': f"Novel contribution from {agent}",
                'confidence': random.uniform(0.75, 0.95)
            }
            contributions.append(contribution)
        
        self.final_synthesis = {
            'based_on_common_ground': self.common_ground,
            'synthesis_agents': self.synthesis_agents,
            'contributions': contributions,
            'unified_solution': "Final synthesized solution",
            'addresses_debate_concerns': True
        }
        
        self.debate_phase = 'complete'
        
        return {
            'phase': 'synthesis_complete',
            'synthesis': self.final_synthesis,
            'agents_involved': len(self.synthesis_agents),
            'debate_informed': True
        }
    
    def get_hybrid_summary(self) -> Dict:
        """Get complete hybrid session summary"""
        return {
            'session_id': self.session_id,
            'phases': ['debate', 'synthesis'],
            'debate_agents': len(self.debate_agents),
            'synthesis_agents': len(self.synthesis_agents),
            'positions_explored': len(self.debate_positions),
            'common_ground': len(self.common_ground),
            'final_output': self.final_synthesis
        }


# Global orchestration system
orchestrator = InteractionModeSelector()


def get_orchestration_dashboard() -> Dict:
    """Get orchestration system dashboard"""
    return {
        "system_status": "active",
        "training_stats": orchestrator.get_training_stats(),
        "available_modes": ['debate', 'collaborate', 'hybrid', 'solo'],
        "decision_factors": [
            "Task complexity",
            "Ambiguity/controversy level",
            "Creativity requirements",
            "Factual density",
            "Urgency",
            "Stakes/criticality"
        ],
        "capabilities": [
            "Intelligent mode selection",
            "Agent role assignment",
            "Dynamic mode switching",
            "Performance-based learning",
            "Task profile analysis",
            "Collaborative work sessions",
            "Hybrid debate-collaboration"
        ]
    }
