"""
OraclAI Multi-Domain AI System
Writing Domain - Multi-Agent System
Agents: Creative, Technical, Editor, Copywriter, Academic
"""

from typing import Dict, List
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition

class CreativeWriterAgent(BaseAgent):
    """Creative writing and storytelling expert"""
    
    def __init__(self):
        super().__init__(
            name="Creative Writer",
            role="Creative Writing & Storytelling Expert",
            expertise=['fiction', 'story structure', 'character', 'dialogue', 'scene', 'plot']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect writing type
        writing_type = 'general creative'
        if 'story' in query_lower or 'narrative' in query_lower or 'plot' in query_lower:
            writing_type = 'story'
        elif 'character' in query_lower:
            writing_type = 'character development'
        elif 'dialogue' in query_lower:
            writing_type = 'dialogue'
        elif 'scene' in query_lower or 'setting' in query_lower:
            writing_type = 'scene'
        
        # Story elements
        elements = []
        if any(w in query_lower for w in ['beginning', 'hook', 'intro']):
            elements.append('hook')
        if any(w in query_lower for w in ['conflict', 'tension', 'problem']):
            elements.append('conflict')
        if any(w in query_lower for w in ['climax', 'resolution', 'ending']):
            elements.append('climax/resolution')
        
        reasoning = f"Creative analysis ({writing_type}). "
        if elements:
            reasoning += f"Story elements to develop: {', '.join(elements)}. "
        reasoning += "Focus: emotional resonance, pacing, showing vs telling."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.78,
            reasoning=reasoning,
            key_points=[writing_type, "Engagement & emotion"]
        )


class TechnicalWriterAgent(BaseAgent):
    """Technical documentation expert"""
    
    def __init__(self):
        super().__init__(
            name="Technical Writer",
            role="Technical Documentation Expert",
            expertise=['documentation', 'manuals', 'API docs', 'tutorials', 'procedures']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        doc_types = []
        if any(w in query_lower for w in ['api', 'endpoint', 'function', 'method']):
            doc_types.append('API documentation')
        if any(w in query_lower for w in ['how to', 'tutorial', 'guide', 'steps']):
            doc_types.append('tutorial/guide')
        if any(w in query_lower for w in ['manual', 'instruction', 'procedure']):
            doc_types.append('manual/procedure')
        if any(w in query_lower for w in ['readme', 'overview', 'intro']):
            doc_types.append('overview')
        
        if not doc_types:
            doc_types = ['technical content']
        
        # Technical writing principles
        principles = ['clarity', 'accuracy', 'completeness', 'accessibility']
        
        reasoning = f"Technical writing perspective ({', '.join(doc_types)}). "
        reasoning += f"Key principles: {', '.join(principles[:3])}. "
        reasoning += "Structure: overview → steps → examples → troubleshooting."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.82,
            reasoning=reasoning,
            key_points=[f"Type: {', '.join(doc_types)}", "User-centric clarity"]
        )


class EditorAgent(BaseAgent):
    """Editing and proofreading expert"""
    
    def __init__(self):
        super().__init__(
            name="Editor",
            role="Editing & Quality Control Expert",
            expertise=['grammar', 'style', 'clarity', 'structure', 'flow', 'consistency']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        text = context.get('text', '')
        
        issues = []
        improvements = []
        
        # Check for common issues
        if 'passive' in query_lower or text:
            issues.append("Check for passive voice")
        if 'grammar' in query_lower:
            issues.append("Grammar review needed")
        if 'flow' in query_lower or 'transition' in query_lower:
            issues.append("Smooth transitions between paragraphs")
        
        # Style suggestions
        if len(text) > 500:
            improvements.append("Consider breaking long paragraphs")
        
        if issues:
            stance = 'critical'
            confidence = 0.75
            reasoning = f"Editing concerns: {'; '.join(issues[:3])}"
        elif improvements:
            stance = 'constructive'
            confidence = 0.80
            reasoning = f"Polish suggestions: {'; '.join(improvements[:3])}"
        else:
            stance = 'positive'
            confidence = 0.85
            reasoning = "Good foundation. Minor polish can elevate impact."
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=["Grammar & style", "Clarity check"]
        )


class CopywriterAgent(BaseAgent):
    """Marketing and persuasive writing expert"""
    
    def __init__(self):
        super().__init__(
            name="Copywriter",
            role="Marketing & Persuasive Writing Expert",
            expertise=['copywriting', 'marketing', 'persuasion', 'CTA', 'headlines', 'conversion']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Copywriting type
        copy_types = []
        if any(w in query_lower for w in ['ad', 'advertisement', 'promotion']):
            copy_types.append('advertisement')
        if any(w in query_lower for w in ['email', 'newsletter', 'campaign']):
            copy_types.append('email campaign')
        if any(w in query_lower for w in ['landing page', 'website', 'home page']):
            copy_types.append('landing page')
        if any(w in query_lower for w in ['social media', 'post', 'tweet', 'linkedin']):
            copy_types.append('social media')
        if any(w in query_lower for w in ['blog', 'article', 'content']):
            copy_types.append('content marketing')
        
        if not copy_types:
            copy_types = ['general copy']
        
        # Persuasion elements
        elements = ['attention', 'interest', 'desire', 'action (AIDA)']
        
        reasoning = f"Copywriting analysis ({', '.join(copy_types)}). "
        reasoning += f"Persuasion framework: {', '.join(elements)}. "
        reasoning += "Focus: benefit-driven, emotional triggers, clear CTA."
        
        return AgentPosition(
            agent_name=self.name,
            stance='constructive',
            confidence=0.80,
            reasoning=reasoning,
            key_points=[f"Format: {', '.join(copy_types)}", "Conversion optimization"]
        )


class AcademicWriterAgent(BaseAgent):
    """Academic and research writing expert"""
    
    def __init__(self):
        super().__init__(
            name="Academic Writer",
            role="Academic & Research Writing Expert",
            expertise=['research papers', 'thesis', 'dissertation', 'citations', 'methodology']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        academic_types = []
        if any(w in query_lower for w in ['paper', 'research', 'journal']):
            academic_types.append('research paper')
        if any(w in query_lower for w in ['essay', 'argumentative', 'persuasive']):
            academic_types.append('academic essay')
        if any(w in query_lower for w in ['thesis', 'dissertation']):
            academic_types.append('thesis/dissertation')
        if any(w in query_lower for w in ['literature review', 'survey']):
            academic_types.append('literature review')
        
        if not academic_types:
            academic_types = ['academic writing']
        
        # Academic standards
        standards = ['citations', 'peer review', 'objective tone', 'evidence-based']
        
        reasoning = f"Academic perspective ({', '.join(academic_types)}). "
        reasoning += f"Standards: {', '.join(standards[:3])}. "
        reasoning += "Structure: abstract → intro → methods → results → discussion → conclusion."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.85,
            reasoning=reasoning,
            key_points=[f"Type: {', '.join(academic_types)}", "Academic rigor"]
        )


class WritingAI(MultiAgentSystem):
    """Complete Writing Multi-Agent System"""
    
    def __init__(self):
        super().__init__(domain_name='Writing', max_rounds=3)
        
        self.register_agent(CreativeWriterAgent())
        self.register_agent(TechnicalWriterAgent())
        self.register_agent(EditorAgent())
        self.register_agent(CopywriterAgent())
        self.register_agent(AcademicWriterAgent())
    
    def review_writing(self, text: str, writing_type: str = None, question: str = None) -> str:
        """Quick writing review entry point"""
        query = question or f"Review this {writing_type or ''} writing"
        context = {'text': text, 'type': writing_type}
        
        session_id = self.start_debate(query, context)
        
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
        return "Writing analysis in progress..."


# Singleton
writing_ai = WritingAI()
