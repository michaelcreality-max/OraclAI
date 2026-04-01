"""
OraclAI Multi-Domain AI System
STEM Domain - Multi-Agent System
Agents: Scientist, Mathematician, Engineer, Technologist, Researcher
"""

from typing import Dict, List
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition

class ScientistAgent(BaseAgent):
    """Physics, Chemistry, Biology expert"""
    
    def __init__(self):
        super().__init__(
            name="Scientist",
            role="Natural Sciences Expert",
            expertise=['physics', 'chemistry', 'biology', 'experiments', 'scientific method']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Determine field
        field = 'general'
        if any(w in query_lower for w in ['physics', 'force', 'energy', 'motion', 'quantum', 'gravity']):
            field = 'physics'
        elif any(w in query_lower for w in ['chemistry', 'molecule', 'reaction', 'compound', 'acid', 'base']):
            field = 'chemistry'
        elif any(w in query_lower for w in ['biology', 'cell', 'organism', 'dna', 'protein', 'gene']):
            field = 'biology'
        
        key_concepts = {
            'physics': ['Newton\'s laws', 'conservation of energy', 'thermodynamics'],
            'chemistry': ['periodic table', 'chemical bonds', 'reaction rates'],
            'biology': ['evolution', 'cell theory', 'homeostasis']
        }
        
        reasoning = f"Analyzing from {field} perspective. "
        if field in key_concepts:
            reasoning += f"Key principles: {', '.join(key_concepts[field][:2])}."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.80,
            reasoning=reasoning,
            key_points=[f"Field: {field}", "Empirical evidence required"]
        )


class MathematicianAgent(BaseAgent):
    """Mathematics expert"""
    
    def __init__(self):
        super().__init__(
            name="Mathematician",
            role="Mathematics & Logic Expert",
            expertise=['calculus', 'algebra', 'statistics', 'proofs', 'theorems', 'equations']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect math type
        math_types = []
        if any(w in query_lower for w in ['calculus', 'derivative', 'integral', 'limit']):
            math_types.append('calculus')
        if any(w in query_lower for w in ['algebra', 'equation', 'variable', 'matrix']):
            math_types.append('algebra')
        if any(w in query_lower for w in ['statistics', 'probability', 'distribution', 'mean']):
            math_types.append('statistics')
        if any(w in query_lower for w in ['geometry', 'angle', 'triangle', 'circle']):
            math_types.append('geometry')
        
        if not math_types:
            math_types = ['general mathematics']
        
        # Check for equation solving
        has_equation = '=' in query and any(c.isdigit() for c in query)
        
        reasoning = f"Approaching from {', '.join(math_types)}. "
        if has_equation:
            reasoning += "Equation detected. Solution requires systematic algebraic manipulation."
        else:
            reasoning += "Conceptual analysis. Mathematical models can provide rigorous framework."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.85 if has_equation else 0.75,
            reasoning=reasoning,
            key_points=[f"Domain: {', '.join(math_types)}", "Logical deduction"]
        )


class EngineerAgent(BaseAgent):
    """Engineering and practical application expert"""
    
    def __init__(self):
        super().__init__(
            name="Engineer",
            role="Engineering & Application Expert",
            expertise=['mechanical', 'electrical', 'civil', 'design', 'systems', 'optimization']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Engineering disciplines
        disciplines = []
        if any(w in query_lower for w in ['mechanical', 'machine', 'gear', 'force']):
            disciplines.append('mechanical')
        if any(w in query_lower for w in ['electrical', 'circuit', 'voltage', 'current']):
            disciplines.append('electrical')
        if any(w in query_lower for w in ['civil', 'structure', 'bridge', 'building']):
            disciplines.append('civil')
        if any(w in query_lower for w in ['software', 'system', 'process', 'flow']):
            disciplines.append('systems')
        
        if not disciplines:
            disciplines = ['general engineering']
        
        # Engineering principles
        considerations = ['feasibility', 'cost-effectiveness', 'safety', 'efficiency']
        
        reasoning = f"Engineering perspective ({', '.join(disciplines)}). "
        reasoning += f"Key considerations: {', '.join(considerations[:2])}. "
        reasoning += "Practical implementation requires iterative design and testing."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.78,
            reasoning=reasoning,
            key_points=[f"Discipline: {', '.join(disciplines)}", "Build-test-iterate cycle"]
        )


class TechnologistAgent(BaseAgent):
    """Technology and innovation expert"""
    
    def __init__(self):
        super().__init__(
            name="Technologist",
            role="Technology & Innovation Expert",
            expertise=['emerging tech', 'AI', 'automation', 'digital transformation', 'innovation']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Tech trends
        tech_areas = []
        if any(w in query_lower for w in ['ai', 'machine learning', 'neural', 'model']):
            tech_areas.append('AI/ML')
        if any(w in query_lower for w in ['robot', 'automation', 'automate']):
            tech_areas.append('robotics/automation')
        if any(w in query_lower for w in ['data', 'database', 'analytics']):
            tech_areas.append('data tech')
        if any(w in query_lower for w in ['cloud', 'server', 'distributed']):
            tech_areas.append('cloud computing')
        
        if not tech_areas:
            tech_areas = ['general technology']
        
        reasoning = f"Technology analysis ({', '.join(tech_areas)}). "
        reasoning += "Consider: scalability, adoption barriers, future trends, ethical implications."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.75,
            reasoning=reasoning,
            key_points=[f"Tech area: {', '.join(tech_areas)}", "Innovation potential"]
        )


class ResearcherAgent(BaseAgent):
    """Scientific research and methodology expert"""
    
    def __init__(self):
        super().__init__(
            name="Researcher",
            role="Research & Methodology Expert",
            expertise=['research methods', 'peer review', 'evidence', 'hypothesis testing']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Research considerations
        methodology = []
        
        if any(w in query_lower for w in ['experiment', 'test', 'measure', 'observation']):
            methodology.append('experimental')
        if any(w in query_lower for w in ['theory', 'model', 'framework']):
            methodology.append('theoretical')
        if any(w in query_lower for w in ['data', 'statistics', 'survey']):
            methodology.append('empirical')
        
        if not methodology:
            methodology = ['literature review']
        
        reasoning = f"Research perspective ({', '.join(methodology)}). "
        reasoning += "Requires: peer-reviewed sources, reproducible results, controlled variables."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.82,
            reasoning=reasoning,
            key_points=[f"Method: {', '.join(methodology)}", "Peer review needed"]
        )


class STEM_AI(MultiAgentSystem):
    """Complete STEM Multi-Agent System"""
    
    def __init__(self):
        super().__init__(domain_name='STEM', max_rounds=3)
        
        self.register_agent(ScientistAgent())
        self.register_agent(MathematicianAgent())
        self.register_agent(EngineerAgent())
        self.register_agent(TechnologistAgent())
        self.register_agent(ResearcherAgent())
    
    def solve_problem(self, problem: str, subject: str = None) -> str:
        """Quick problem-solving entry point"""
        context = {'subject': subject} if subject else {}
        session_id = self.start_debate(problem, context)
        
        import time
        max_wait = 30
        waited = 0
        while waited < max_wait:
            status = self.get_session_status(session_id)
            if status['status'] == 'complete':
                break
            time.sleep(0.5)
            waited += 0.5
        
        result = self.get_result(session_id)
        if result:
            return result.final_answer
        return "STEM analysis in progress..."


# Singleton
stem_ai = STEM_AI()
