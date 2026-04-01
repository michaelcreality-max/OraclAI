"""
OraclAI Multi-Domain AI System
Domain Router - Classifies and routes requests to appropriate specialized systems
"""

class DomainRouter:
    """Routes user queries to the appropriate domain system"""
    
    DOMAINS = {
        'finance': {
            'keywords': ['stock', 'trade', 'market', 'price', 'invest', 'portfolio', 'buy', 'sell', 
                        'ticker', 'chart', 'analysis', 'bull', 'bear', 'dividend', 'earnings',
                        'aapl', 'nvda', 'msft', 'tsla', 'crypto', 'bitcoin', 'forex', 'option',
                        'calls', 'puts', 'pe ratio', 'market cap', 'volume', 'volatility',
                        'vix', 'spy', 'nasdaq', 'dow', 's&p', 'etf', 'mutual fund', 'bond',
                        'interest rate', 'inflation', 'fed', 'economy', 'recession', 'gdp'],
            'system': 'FinanceAI'
        },
        'code': {
            'keywords': ['code', 'programming', 'python', 'javascript', 'function', 'class',
                        'debug', 'error', 'syntax', 'algorithm', 'data structure', 'api',
                        'database', 'sql', 'git', 'github', 'framework', 'library', 'module',
                        'import', 'variable', 'loop', 'condition', 'exception', 'bug', 'fix',
                        'refactor', 'optimize', 'compile', 'runtime', 'terminal', 'command',
                        'docker', 'kubernetes', 'deploy', 'server', 'backend', 'frontend',
                        'html', 'css', 'react', 'flask', 'django', 'node', 'react'],
            'system': 'CodeAI'
        },
        'stem': {
            'keywords': ['physics', 'chemistry', 'biology', 'math', 'calculus', 'algebra',
                        'geometry', 'statistics', 'equation', 'formula', 'theorem', 'proof',
                        'experiment', 'hypothesis', 'theory', 'lab', 'molecule', 'atom',
                        'cell', 'organism', 'dna', 'rna', 'protein', 'chemical reaction',
                        'force', 'energy', 'velocity', 'acceleration', 'gravity', 'quantum',
                        'relativity', 'thermodynamics', 'organic', 'inorganic', 'calculus',
                        'derivative', 'integral', 'matrix', 'vector', 'linear algebra'],
            'system': 'STEM_AI'
        },
        'writing': {
            'keywords': ['write', 'essay', 'article', 'blog', 'content', 'copy', 'creative',
                        'story', 'narrative', 'plot', 'character', 'dialogue', 'scene',
                        'edit', 'proofread', 'grammar', 'spelling', 'punctuation', 'style',
                        'tone', 'voice', 'structure', 'outline', 'draft', 'revise',
                        'persuasive', 'argumentative', 'descriptive', 'expository', 'poetry',
                        'script', 'screenplay', 'manuscript', 'publication', 'submission'],
            'system': 'WritingAI'
        },
        'literature': {
            'keywords': ['book', 'novel', 'author', 'poem', 'poetry', 'literature', 'literary',
                        'classic', 'fiction', 'non-fiction', 'genre', 'theme', 'symbolism',
                        'metaphor', 'simile', 'alliteration', 'rhyme', 'meter', 'stanza',
                        'character', 'protagonist', 'antagonist', 'setting', 'conflict',
                        'climax', 'resolution', 'chapter', 'verse', 'prose', 'shakespeare',
                        'dostoevsky', 'tolstoy', 'hemingway', 'faulkner', 'modernism',
                        'romanticism', 'realism', 'postmodern', 'criticism', 'review'],
            'system': 'LiteratureAI'
        },
        'general': {
            'keywords': ['what', 'how', 'why', 'when', 'where', 'who', 'explain', 'describe',
                        'tell me', 'what is', 'how to', 'help', 'advice', 'recommendation',
                        'suggestion', 'opinion', 'thoughts', 'question', 'answer', 'fact',
                        'information', 'news', 'current events', 'history', 'geography',
                        'culture', 'society', 'philosophy', 'psychology', 'politics'],
            'system': 'GeneralAI'
        }
    }
    
    def __init__(self):
        self.confidence_threshold = 0.6
    
    def classify(self, query: str) -> dict:
        """Classify a query and return the best matching domain"""
        query_lower = query.lower()
        scores = {}
        
        # Calculate scores for each domain
        for domain, config in self.DOMAINS.items():
            score = 0
            matched_keywords = []
            
            for keyword in config['keywords']:
                if keyword in query_lower:
                    # Longer keywords get higher weight
                    weight = len(keyword) / 10
                    score += weight
                    matched_keywords.append(keyword)
            
            # Normalize by keyword count
            if matched_keywords:
                scores[domain] = {
                    'score': score,
                    'confidence': min(score / 2, 1.0),  # Cap at 1.0
                    'matched_keywords': matched_keywords,
                    'system': config['system']
                }
        
        # Find best match
        if not scores:
            return {
                'domain': 'general',
                'confidence': 1.0,
                'system': 'GeneralAI',
                'matched_keywords': [],
                'all_scores': {}
            }
        
        best_domain = max(scores.items(), key=lambda x: x[1]['score'])
        
        # If confidence is too low, default to general
        if best_domain[1]['confidence'] < self.confidence_threshold:
            return {
                'domain': 'general',
                'confidence': 1.0 - best_domain[1]['confidence'],
                'system': 'GeneralAI',
                'matched_keywords': [],
                'all_scores': {k: v['confidence'] for k, v in scores.items()},
                'fallback_reason': 'Low confidence in specific domain'
            }
        
        return {
            'domain': best_domain[0],
            'confidence': best_domain[1]['confidence'],
            'system': best_domain[1]['system'],
            'matched_keywords': best_domain[1]['matched_keywords'],
            'all_scores': {k: v['confidence'] for k, v in scores.items()}
        }
    
    def route(self, query: str, context: dict = None) -> dict:
        """Route query to appropriate system and return routing info"""
        classification = self.classify(query)
        
        return {
            'query': query,
            'classification': classification,
            'context': context or {},
            'route_to': classification['system'],
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }


# Singleton instance
router = DomainRouter()
