"""
OraclAI Multi-Domain AI System
General Domain - Multi-Agent System
Agents: Generalist, FactChecker, LogicReasoner, CreativeThinker, Researcher
"""

from typing import Dict, List
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition

class GeneralistAgent(BaseAgent):
    """General knowledge and common sense expert"""
    
    def __init__(self):
        super().__init__(
            name="Generalist",
            role="General Knowledge & Common Sense Expert",
            expertise=['general knowledge', 'common sense', 'practical advice', 'everyday topics']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Determine query type
        query_types = []
        if any(w in query_lower for w in ['what is', 'define', 'meaning', 'explain']):
            query_types.append('definition/explanation')
        if any(w in query_lower for w in ['how to', 'how do', 'steps', 'process']):
            query_types.append('procedural/how-to')
        if any(w in query_lower for w in ['why', 'reason', 'cause']):
            query_types.append('causal/explanatory')
        if any(w in query_lower for w in ['compare', 'difference', 'versus', 'vs']):
            query_types.append('comparative')
        if any(w in query_lower for w in ['recommend', 'suggest', 'best', 'good']):
            query_types.append('recommendation')
        if any(w in query_lower for w in ['should', 'advice', 'help']):
            query_types.append('advisory')
        
        if not query_types:
            query_types = ['general inquiry']
        
        reasoning = f"General analysis ({', '.join(query_types)}). "
        reasoning += "Approach: accessible explanation, practical perspective, common sense reasoning."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.75,
            reasoning=reasoning,
            key_points=[f"Type: {', '.join(query_types)}", "Accessible explanation"]
        )


class FactCheckerAgent(BaseAgent):
    """Fact verification and accuracy expert"""
    
    def __init__(self):
        super().__init__(
            name="Fact Checker",
            role="Fact Verification & Accuracy Expert",
            expertise=['fact checking', 'verification', 'sources', 'accuracy', 'credibility']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Check for factual claims
        fact_indicators = ['is', 'are', 'was', 'were', 'has', 'have', 'did', 'does']
        has_factual_claim = any(f" {w} " in f" {query_lower} " for w in fact_indicators)
        
        verification_needs = []
        if any(w in query_lower for w in ['statistics', 'percent', 'number', 'data']):
            verification_needs.append('statistical claims')
        if any(w in query_lower for w in ['history', 'historical', 'date', 'year']):
            verification_needs.append('historical facts')
        if any(w in query_lower for w in ['scientific', 'research', 'study', 'proven']):
            verification_needs.append('scientific claims')
        
        if verification_needs:
            stance = 'analytical'
            confidence = 0.70
            reasoning = f"Verification needed: {', '.join(verification_needs)}. "
            reasoning += "Check: source credibility, recency, consensus among experts."
        else:
            stance = 'constructive'
            confidence = 0.80
            reasoning = "Query appears to be opinion-seeking or general. "
            reasoning += "Less fact-critical, more perspective-oriented."
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=["Source verification" if verification_needs else "Opinion/perspective", 
                       "Credibility assessment"]
        )


class LogicReasonerAgent(BaseAgent):
    """Logical reasoning and critical thinking expert"""
    
    def __init__(self):
        super().__init__(
            name="Logic Reasoner",
            role="Logical Reasoning & Critical Thinking Expert",
            expertise=['logic', 'reasoning', 'argumentation', 'fallacies', 'critical thinking']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect reasoning type
        reasoning_types = []
        if any(w in query_lower for w in ['if', 'then', 'therefore', 'because', 'since']):
            reasoning_types.append('conditional/causal')
        if any(w in query_lower for w in ['all', 'every', 'always', 'never', 'none']):
            reasoning_types.append('universal/generalization')
        if any(w in query_lower for w in ['some', 'many', 'most', 'probably', 'likely']):
            reasoning_types.append('probabilistic')
        if any(w in query_lower for w in ['either', 'or', 'option', 'choice', 'decide']):
            reasoning_types.append('decision/dilemma')
        if any(w in query_lower for w in ['assume', 'premise', 'conclusion', 'argument']):
            reasoning_types.append('formal argument')
        
        if not reasoning_types:
            reasoning_types = ['informal reasoning']
        
        # Check for potential fallacies
        fallacy_risks = []
        if 'everyone' in query_lower or 'nobody' in query_lower:
            fallacy_risks.append('hasty generalization')
        if 'always' in query_lower or 'never' in query_lower:
            fallacy_risks.append('absolutism')
        
        reasoning = f"Logical analysis ({', '.join(reasoning_types)}). "
        if fallacy_risks:
            reasoning += f"Watch for: {', '.join(fallacy_risks)}. "
        reasoning += "Structure: premises → inference → conclusion. Check validity and soundness."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.82,
            reasoning=reasoning,
            key_points=[f"Reasoning: {', '.join(reasoning_types)}", 
                       "Logical structure"]
        )


class CreativeThinkerAgent(BaseAgent):
    """Creative thinking and innovation expert"""
    
    def __init__(self):
        super().__init__(
            name="Creative Thinker",
            role="Creative Thinking & Innovation Expert",
            expertise=['creativity', 'brainstorming', 'lateral thinking', 'innovation', 'ideas']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Creative opportunity indicators
        creative_signals = []
        if any(w in query_lower for w in ['idea', 'brainstorm', 'think of', 'come up with']):
            creative_signals.append('idea generation')
        if any(w in query_lower for w in ['problem', 'solution', 'fix', 'improve']):
            creative_signals.append('problem-solving')
        if any(w in query_lower for w in ['alternative', 'different', 'other way', 'perspective']):
            creative_signals.append('alternative approaches')
        if any(w in query_lower for w in ['imagine', 'what if', 'possibility', 'future']):
            creative_signals.append('speculative thinking')
        
        if creative_signals:
            stance = 'constructive'
            confidence = 0.80
            reasoning = f"Creative opportunity ({', '.join(creative_signals)}). "
            reasoning += "Approach: divergent thinking, multiple perspectives, unconventional connections."
        else:
            stance = 'analytical'
            confidence = 0.70
            reasoning = "Limited creative signals. Focus on straightforward, practical response."
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=[f"Creative mode: {', '.join(creative_signals) or 'standard'}"]
        )


class GeneralResearcherAgent(BaseAgent):
    """Research and information gathering expert"""
    
    def __init__(self):
        super().__init__(
            name="Researcher",
            role="Research & Information Expert",
            expertise=['research', 'information gathering', 'synthesis', 'sources', 'analysis']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Research depth indicators
        depth = 'basic'
        if any(w in query_lower for w in ['deep', 'comprehensive', 'detailed', 'thorough']):
            depth = 'comprehensive'
        elif any(w in query_lower for w in ['brief', 'quick', 'simple', 'overview']):
            depth = 'overview'
        elif any(w in query_lower for w in ['compare', 'contrast', 'analyze', 'evaluate']):
            depth = 'analytical'
        
        # Topic breadth
        breadth_indicators = []
        if any(w in query_lower for w in ['overview', 'summary', 'general', 'introduction']):
            breadth_indicators.append('broad overview')
        if any(w in query_lower for w in ['specific', 'particular', 'detail', 'aspect']):
            breadth_indicators.append('focused deep-dive')
        if any(w in query_lower for w in ['examples', 'cases', 'instance']):
            breadth_indicators.append('example-rich')
        
        if not breadth_indicators:
            breadth_indicators = ['balanced']
        
        reasoning = f"Research approach ({depth} level, {', '.join(breadth_indicators)}). "
        reasoning += "Strategy: gather multiple perspectives, synthesize, present balanced view."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.78,
            reasoning=reasoning,
            key_points=[f"Depth: {depth}", f"Breadth: {', '.join(breadth_indicators)}"]
        )


class GeneralAI(MultiAgentSystem):
    """Complete General Domain Multi-Agent System"""
    
    def __init__(self):
        super().__init__(domain_name='General', max_rounds=3)
        
        self.register_agent(GeneralistAgent())
        self.register_agent(FactCheckerAgent())
        self.register_agent(LogicReasonerAgent())
        self.register_agent(CreativeThinkerAgent())
        self.register_agent(GeneralResearcherAgent())
    
    def answer_question(self, question: str, detail_level: str = 'standard') -> str:
        """Quick general question answering entry point"""
        context = {'detail_level': detail_level}
        session_id = self.start_debate(question, context)
        
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
        return "Analysis in progress..."


# Singleton
general_ai = GeneralAI()
