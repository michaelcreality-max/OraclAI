"""
OraclAI Multi-Domain AI System
Literature Domain - Multi-Agent System
Agents: LiteraryCritic, Historian, GenreExpert, CharacterAnalyst, SymbolismExpert
"""

from typing import Dict, List
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition

class LiteraryCriticAgent(BaseAgent):
    """Literary analysis and criticism expert"""
    
    def __init__(self):
        super().__init__(
            name="Literary Critic",
            role="Literary Analysis & Criticism Expert",
            expertise=['literary theory', 'critical analysis', 'themes', 'narrative structure', 'style']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect analysis type
        analysis_types = []
        if any(w in query_lower for w in ['theme', 'thematic', 'message', 'meaning']):
            analysis_types.append('thematic analysis')
        if any(w in query_lower for w in ['style', 'voice', 'tone', 'narrative', 'structure']):
            analysis_types.append('stylistic analysis')
        if any(w in query_lower for w in ['symbol', 'metaphor', 'imagery', 'allegory']):
            analysis_types.append('symbolic analysis')
        if any(w in query_lower for w in ['interpretation', 'reading', 'understand']):
            analysis_types.append('interpretive analysis')
        
        if not analysis_types:
            analysis_types = ['general literary analysis']
        
        # Critical approaches
        approaches = ['formalist', 'reader-response', 'cultural', 'psychological']
        
        reasoning = f"Literary critical perspective ({', '.join(analysis_types)}). "
        reasoning += f"Approaches: {', '.join(approaches[:2])}. "
        reasoning += "Examines how form creates meaning and cultural context shapes interpretation."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.82,
            reasoning=reasoning,
            key_points=[f"Analysis: {', '.join(analysis_types)}", "Text-context relationship"]
        )


class HistorianAgent(BaseAgent):
    """Literary history and context expert"""
    
    def __init__(self):
        super().__init__(
            name="Historian",
            role="Literary History & Context Expert",
            expertise=['literary movements', 'historical context', 'periods', 'authors', 'canon']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect periods
        periods = []
        if any(w in query_lower for w in ['classical', 'greek', 'roman', 'antiquity']):
            periods.append('Classical')
        if any(w in query_lower for w in ['medieval', 'middle ages', 'renaissance']):
            periods.append('Medieval/Renaissance')
        if any(w in query_lower for w in ['romantic', '18th', '19th', 'victorian']):
            periods.append('Romantic/Victorian')
        if any(w in query_lower for w in ['modernist', 'modernism', 'early 20th']):
            periods.append('Modernist')
        if any(w in query_lower for w in ['postmodern', 'contemporary', 'post-war']):
            periods.append('Postmodern/Contemporary')
        
        # Movements
        movements = []
        if 'realism' in query_lower:
            movements.append('Realism')
        if 'naturalism' in query_lower:
            movements.append('Naturalism')
        if 'symbolism' in query_lower:
            movements.append('Symbolism')
        if 'existential' in query_lower:
            movements.append('Existentialism')
        
        context_parts = []
        if periods:
            context_parts.append(f"Period: {', '.join(periods)}")
        if movements:
            context_parts.append(f"Movement: {', '.join(movements)}")
        
        reasoning = "Historical literary context. "
        if context_parts:
            reasoning += f"Context: {'; '.join(context_parts)}. "
        reasoning += "Considers how historical circumstances shaped literary production and reception."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.80,
            reasoning=reasoning,
            key_points=[f"Context: {', '.join(periods + movements) or 'General'}"]
        )


class GenreExpertAgent(BaseAgent):
    """Genre analysis expert"""
    
    def __init__(self):
        super().__init__(
            name="Genre Expert",
            role="Genre & Form Analysis Expert",
            expertise=['genres', 'conventions', 'poetry', 'novel', 'drama', 'short story']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect genres
        genres = []
        if any(w in query_lower for w in ['novel', 'fiction', 'prose']):
            genres.append('Novel/Fiction')
        if any(w in query_lower for w in ['poetry', 'poem', 'verse', 'stanza', 'rhyme']):
            genres.append('Poetry')
        if any(w in query_lower for w in ['drama', 'play', 'theater', 'script']):
            genres.append('Drama/Theater')
        if any(w in query_lower for w in ['short story', 'novella']):
            genres.append('Short Fiction')
        if any(w in query_lower for w in ['essay', 'non-fiction', 'memoir']):
            genres.append('Non-fiction')
        
        # Subgenres
        subgenres = []
        if 'science fiction' in query_lower or 'sci-fi' in query_lower:
            subgenres.append('Science Fiction')
        if 'fantasy' in query_lower:
            subgenres.append('Fantasy')
        if 'mystery' in query_lower or 'detective' in query_lower:
            subgenres.append('Mystery/Detective')
        if 'horror' in query_lower or 'gothic' in query_lower:
            subgenres.append('Horror/Gothic')
        if 'romance' in query_lower:
            subgenres.append('Romance')
        
        if not genres:
            genres = ['Literature']
        
        all_genres = genres + subgenres
        
        reasoning = f"Genre analysis ({', '.join(all_genres)}). "
        reasoning += "Examines genre conventions, expectations, and how the work innovates within or subverts genre norms."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.78,
            reasoning=reasoning,
            key_points=[f"Genre: {', '.join(all_genres)}", "Conventions & innovations"]
        )


class CharacterAnalystAgent(BaseAgent):
    """Character analysis expert"""
    
    def __init__(self):
        super().__init__(
            name="Character Analyst",
            role="Character Analysis & Development Expert",
            expertise=['characterization', 'protagonist', 'antagonist', 'arc', 'motivation']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        character_aspects = []
        if any(w in query_lower for w in ['protagonist', 'hero', 'main character']):
            character_aspects.append('protagonist analysis')
        if any(w in query_lower for w in ['antagonist', 'villain', 'opposition']):
            character_aspects.append('antagonist analysis')
        if any(w in query_lower for w in ['character arc', 'development', 'growth', 'change']):
            character_aspects.append('character development')
        if any(w in query_lower for w in ['motivation', 'goal', 'desire', 'conflict']):
            character_aspects.append('character motivation')
        if any(w in query_lower for w in ['relationship', 'dynamic', 'interaction']):
            character_aspects.append('character relationships')
        
        if not character_aspects:
            character_aspects = ['general character analysis']
        
        reasoning = f"Character perspective ({', '.join(character_aspects)}). "
        reasoning += "Examines how characters are constructed, their functions in narrative, psychological depth, and symbolic significance."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.80,
            reasoning=reasoning,
            key_points=[f"Focus: {', '.join(character_aspects)}", "Character function in narrative"]
        )


class SymbolismExpertAgent(BaseAgent):
    """Symbolism and figurative language expert"""
    
    def __init__(self):
        super().__init__(
            name="Symbolism Expert",
            role="Symbolism & Figurative Language Expert",
            expertise=['symbolism', 'metaphor', 'allegory', 'imagery', 'motifs', 'archetypes']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        query_lower = query.lower()
        
        # Detect symbolic elements
        elements = []
        if any(w in query_lower for w in ['symbol', 'symbolic', 'representation']):
            elements.append('symbolism')
        if any(w in query_lower for w in ['metaphor', 'simile', 'figurative']):
            elements.append('metaphor/simile')
        if any(w in query_lower for w in ['allegory', 'allegorical']):
            elements.append('allegory')
        if any(w in query_lower for w in ['imagery', 'sensory', 'description']):
            elements.append('imagery')
        if any(w in query_lower for w in ['motif', 'recurring', 'pattern']):
            elements.append('motifs')
        if any(w in query_lower for w in ['archetype', 'universal']):
            elements.append('archetypes')
        
        if not elements:
            elements = ['figurative language']
        
        reasoning = f"Symbolic analysis ({', '.join(elements)}). "
        reasoning += "Examines how concrete elements carry abstract meaning, patterns across the text, and universal resonances."
        
        return AgentPosition(
            agent_name=self.name,
            stance='analytical',
            confidence=0.78,
            reasoning=reasoning,
            key_points=[f"Elements: {', '.join(elements)}", "Abstract meaning systems"]
        )


class LiteratureAI(MultiAgentSystem):
    """Complete Literature Multi-Agent System"""
    
    def __init__(self):
        super().__init__(domain_name='Literature', max_rounds=3)
        
        self.register_agent(LiteraryCriticAgent())
        self.register_agent(HistorianAgent())
        self.register_agent(GenreExpertAgent())
        self.register_agent(CharacterAnalystAgent())
        self.register_agent(SymbolismExpertAgent())
    
    def analyze_text(self, text_reference: str, analysis_type: str = None) -> str:
        """Quick literature analysis entry point"""
        query = f"Analyze {text_reference}"
        if analysis_type:
            query += f" with focus on {analysis_type}"
        
        context = {'text': text_reference, 'analysis_type': analysis_type}
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
        return "Literary analysis in progress..."


# Singleton
literature_ai = LiteratureAI()
