"""
OraclAI Multi-Domain AI System
Unified Orchestrator - Manages all domain systems
"""

import threading
import time
from typing import Dict, List, Optional
from datetime import datetime

# Import all domain systems
from multi_domain.domain_router import router
from multi_domain.code_system import code_ai
from multi_domain.stem_system import stem_ai
from multi_domain.writing_system import writing_ai
from multi_domain.literature_system import literature_ai
from multi_domain.general_system import general_ai

class UnifiedOrchestrator:
    """
    Central orchestrator that routes queries to appropriate domain systems
    and manages multi-agent debates across all domains
    """
    
    def __init__(self):
        self.domain_systems = {
            'finance': None,  # Will use existing trading orchestrator
            'code': code_ai,
            'stem': stem_ai,
            'writing': writing_ai,
            'literature': literature_ai,
            'general': general_ai
        }
        
        self.active_sessions: Dict[str, Dict] = {}
        self.session_lock = threading.Lock()
        self.router = router
    
    def process_query(self, query: str, context: Dict = None) -> Dict:
        """
        Main entry point - classify and route query to appropriate system
        """
        context = context or {}
        
        # Step 1: Classify the query
        classification = self.router.classify(query)
        domain = classification['domain']
        
        # Step 2: Route to appropriate system
        if domain == 'finance':
            # Use existing finance/trading system
            return self._route_to_finance(query, context, classification)
        elif domain in self.domain_systems:
            system = self.domain_systems[domain]
            return self._route_to_system(domain, system, query, context, classification)
        else:
            # Fallback to general
            return self._route_to_system('general', self.domain_systems['general'], 
                                        query, context, classification)
    
    def _route_to_finance(self, query: str, context: Dict, classification: Dict) -> Dict:
        """Route finance queries to existing trading system"""
        # Import and use the existing orchestrator
        try:
            from quant_ecosystem.orchestrator import orchestrate_trade_decision
            # For finance, we use the existing endpoint, return routing info
            return {
                'success': True,
                'domain': 'finance',
                'classification': classification,
                'route_to': '/api/v1/debate/start',
                'message': 'Finance query - use trading API endpoint',
                'estimated_time': '2-3 minutes'
            }
        except ImportError:
            return {
                'success': False,
                'domain': 'finance',
                'error': 'Finance system not available'
            }
    
    def _route_to_system(self, domain: str, system, query: str, context: Dict, 
                        classification: Dict) -> Dict:
        """Route to a multi-agent domain system"""
        
        session_id = system.start_debate(query, context)
        
        with self.session_lock:
            self.active_sessions[session_id] = {
                'domain': domain,
                'query': query,
                'classification': classification,
                'start_time': datetime.now().isoformat(),
                'status': 'running'
            }
        
        return {
            'success': True,
            'domain': domain,
            'classification': classification,
            'session_id': session_id,
            'route_to': f'/api/multi-agent/stream/{session_id}',
            'status_url': f'/api/multi-agent/status/{session_id}',
            'result_url': f'/api/multi-agent/result/{session_id}',
            'message': f'{domain.upper()} multi-agent analysis started',
            'estimated_time': '10-30 seconds'
        }
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get status of any session across all domain systems"""
        # Check each domain system
        for domain, system in self.domain_systems.items():
            if system and hasattr(system, 'active_sessions'):
                if session_id in system.active_sessions:
                    status = system.get_session_status(session_id)
                    with self.session_lock:
                        session_info = self.active_sessions.get(session_id, {})
                    return {
                        **status,
                        'domain': session_info.get('domain', domain),
                        'query': session_info.get('query', ''),
                        'start_time': session_info.get('start_time')
                    }
        
        return {'error': 'Session not found', 'status': 'unknown'}
    
    def get_result(self, session_id: str) -> Optional[Dict]:
        """Get result from any domain system"""
        for domain, system in self.domain_systems.items():
            if system and hasattr(system, 'active_sessions'):
                if session_id in system.active_sessions:
                    result = system.get_result(session_id)
                    if result:
                        return {
                            'domain': domain,
                            'consensus_reached': result.consensus_reached,
                            'confidence': result.confidence,
                            'final_answer': result.final_answer,
                            'agent_positions': [
                                {
                                    'agent': pos.agent_name,
                                    'stance': pos.stance,
                                    'confidence': pos.confidence,
                                    'reasoning': pos.reasoning
                                }
                                for pos in result.agent_positions
                            ],
                            'debate_rounds': result.debate_rounds,
                            'timestamp': result.timestamp
                        }
        return None
    
    def quick_analyze(self, query: str, domain_hint: str = None) -> str:
        """
        Quick analysis without streaming - blocks until result ready
        """
        if domain_hint and domain_hint in self.domain_systems:
            domain = domain_hint
            system = self.domain_systems[domain]
        else:
            # Auto-classify
            classification = self.router.classify(query)
            domain = classification['domain']
            
            if domain == 'finance':
                return "Finance queries require full debate API. Use /api/v1/debate/start"
            
            system = self.domain_systems.get(domain, self.domain_systems['general'])
        
        # Start debate
        session_id = system.start_debate(query, {})
        
        # Wait for completion
        max_wait = 60
        waited = 0
        while waited < max_wait:
            status = system.get_session_status(session_id)
            if status['status'] == 'complete':
                result = system.get_result(session_id)
                if result:
                    return result.final_answer
                break
            elif status['status'] == 'error':
                return f"Analysis error in {domain} domain"
            time.sleep(0.5)
            waited += 0.5
        
        return "Analysis timed out"
    
    def get_all_domains(self) -> List[Dict]:
        """Return info about all available domains"""
        return [
            {
                'id': 'finance',
                'name': 'Finance & Trading',
                'description': 'Stock analysis, market trends, trading decisions',
                'agents': ['Bullish', 'Bearish', 'Judge', 'Data'],
                'color': '#22c55e'
            },
            {
                'id': 'code',
                'name': 'Code Analysis',
                'description': 'Programming help, debugging, code review',
                'agents': ['Architect', 'Debugger', 'Optimizer', 'Security', 'Reviewer'],
                'color': '#3b82f6'
            },
            {
                'id': 'stem',
                'name': 'STEM',
                'description': 'Science, Technology, Engineering, Math',
                'agents': ['Scientist', 'Mathematician', 'Engineer', 'Technologist', 'Researcher'],
                'color': '#8b5cf6'
            },
            {
                'id': 'writing',
                'name': 'Writing',
                'description': 'Creative, technical, academic writing assistance',
                'agents': ['Creative', 'Technical', 'Editor', 'Copywriter', 'Academic'],
                'color': '#f59e0b'
            },
            {
                'id': 'literature',
                'name': 'Literature',
                'description': 'Literary analysis, book discussion, criticism',
                'agents': ['Critic', 'Historian', 'Genre Expert', 'Character Analyst', 'Symbolism'],
                'color': '#ec4899'
            },
            {
                'id': 'general',
                'name': 'General Knowledge',
                'description': 'General questions, advice, explanations',
                'agents': ['Generalist', 'Fact Checker', 'Logic', 'Creative', 'Researcher'],
                'color': '#6b7280'
            }
        ]


# Singleton instance
unified_orchestrator = UnifiedOrchestrator()
