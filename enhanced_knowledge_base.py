"""
OraclAI Enhanced Knowledge Bases
Comprehensive knowledge expansion for all domain agents
"""

from typing import Dict, List, Any

# Enhanced Code Intelligence Knowledge
ENHANCED_CODE_PATTERNS = {
    'python': {
        'advanced_patterns': {
            'metaclasses': r'class.*\(metaclass\s*=|__metaclass__|type\([^)]*,\s*\([^)]*\)',
            'descriptors': r'def\s+__get__|def\s+__set__|def\s+__delete__',
            'context_managers': r'class.*:\s*def\s+__enter__|def\s+__exit__|@contextmanager',
            'coroutines': r'async\s+def|await\s+|asyncio\.(create_task|gather)|async\s+for',
            'generators': r'yield\s+|yield\s+from|\.send\(|\.throw\(',
            'type_hints': r'from\s+typing\s+import|:\s*[A-Z][a-zA-Z]*\[|->\s*[A-Z]',
        },
        'performance_patterns': {
            'memoization': r'@functools\.lru_cache|@cache|memoize|_cache\s*=\s*\{\}',
            'vectorization': r'numpy|pandas|torch\.tensor|tensorflow|@vectorize|@jit',
            'parallel': r'concurrent\.futures|multiprocessing|threading\.Pool|asyncio\.gather',
            'c_extensions': r'ctypes|cython|cffi|Cython\.Build|\.so\s+import',
            'lazy_loading': r'@property\s*\n\s*def|lazy_import|importlib\.lazy_load',
        },
        'testing_patterns': {
            'unit_tests': r'def\s+test_|class.*TestCase|unittest|pytest|@pytest',
            'fixtures': r'@pytest\.fixture|setUp|tearDown|conftest\.py',
            'mocks': r'unittest\.mock|@patch|MagicMock|Mock\(|monkeypatch',
            'coverage': r'pytest-cov|coverage\.run|codecov|#\s*pragma:\s*no cover',
            'parametrized': r'@pytest\.mark\.parametrize|@parameterized|ddt\.data',
        }
    },
    'javascript': {
        'modern_patterns': {
            'es6_plus': r'const\s+|let\s+|arrow\s*=>|template\s+literal|\.\.\.|class\s+\w+',
            'async_patterns': r'async\s+function|await\s+|Promise\.(all|race)|\.then\(',
            'modules': r'import\s+.*from|export\s+(default|const|class)|require\(',
            'functional': r'\.map\(|\.filter\(|\.reduce\(|\.flatMap\(|curry|compose',
        },
        'framework_patterns': {
            'react': r'React\.|useState|useEffect|JSX|componentDid|functional\s+component',
            'vue': r'Vue\.|v-if|v-for|computed|watch|mounted|created',
            'angular': r'@Component|@Injectable|ngOnInit|Angular|RxJS',
            'node': r'Express|Koa|Fastify|app\.(get|post|use)|middleware',
        }
    }
}

# Enhanced Algorithm Knowledge
ADVANCED_ALGORITHMS = {
    'dynamic_programming': {
        'patterns': ['memoization', 'tabulation', 'state machine', 'knapsack variants'],
        'problems': ['longest common subsequence', 'edit distance', 'matrix chain multiplication'],
        'optimization': ['space optimization', 'rolling array', 'bitmask DP', 'digit DP'],
        'complexity': {'time': 'O(n^2) to O(2^n)', 'space': 'O(n) to O(2^n)'}
    },
    'graph_algorithms': {
        'advanced_traversal': ['A* search', 'IDA*', 'bidirectional BFS', '0-1 BFS'],
        'shortest_path': ['Bellman-Ford', 'Floyd-Warshall', 'Johnson\'s algorithm'],
        'network_flow': ['Ford-Fulkerson', 'Edmonds-Karp', 'Dinic\'s algorithm', 'Min-Cost Max-Flow'],
        'matching': ['Hungarian algorithm', 'blossom algorithm', 'Hopcroft-Karp'],
    },
    'string_algorithms': {
        'pattern_matching': ['KMP', 'Rabin-Karp', 'Boyer-Moore', 'Aho-Corasick'],
        'suffix_structures': ['suffix array', 'suffix tree', 'suffix automaton'],
        'advanced': ['manacher\'s algorithm', 'Z-algorithm', 'rolling hash variants'],
    },
    'computational_geometry': {
        'convex_hull': ['Graham scan', 'Jarvis march', 'Chan\'s algorithm', 'QuickHull'],
        'intersection': ['line sweep', 'bentley-ottmann', 'plane sweep'],
        'voronoi': ['fortune\'s algorithm', 'delanuay triangulation'],
    }
}

# Enhanced Security Knowledge
ADVANCED_SECURITY = {
    'owasp_top_10_2024': {
        'A01': {'name': 'Broken Access Control', 'patterns': [r'@login_required|permission|access.*control|role.*check']},
        'A02': {'name': 'Cryptographic Failures', 'patterns': [r'md5|sha1|des|rc4|weak.*cipher|hardcoded.*key']},
        'A03': {'name': 'Injection', 'patterns': [r'execute.*%s|\.format\(.*execute|f".*\{.*\}".*query']},
        'A04': {'name': 'Insecure Design', 'patterns': [r'todo.*security|FIXME.*auth|bypass.*check']},
        'A05': {'name': 'Security Misconfiguration', 'patterns': [r'debug.*=.*True|admin.*password.*default|CORS.*\*']},
        'A06': {'name': 'Vulnerable Components', 'patterns': [r'pip.*install|requirements.*txt|package\.json']},
        'A07': {'name': 'Auth Failures', 'patterns': [r'session.*forever|jwt.*none|weak.*password.*policy']},
        'A08': {'name': 'Data Integrity Failures', 'patterns': [r'no.*signature|unsigned.*data|deserialize.*user']},
        'A09': {'name': 'Logging Failures', 'patterns': [r'no.*audit.*log|insufficient.*logging|log.*sensitive']},
        'A10': {'name': 'SSRF', 'patterns': [r'urllib.*user.*input|requests\.get\(.*user|curl.*user']},
    },
    'secure_coding': {
        'input_validation': ['whitelist validation', 'parameterized queries', 'output encoding'],
        'authentication': ['multi-factor auth', 'secure session management', 'password hashing (bcrypt/argon2)'],
        'authorization': ['principle of least privilege', 'RBAC', 'ABAC', 'attribute-based access control'],
        'cryptography': ['AES-256-GCM', 'RSA-4096', 'ECDSA P-256', 'ChaCha20-Poly1305'],
    }
}

# Enhanced Finance Knowledge
ADVANCED_FINANCE = {
    'quantitative_strategies': {
        'statistical_arbitrage': {
            'methods': ['cointegration testing', 'Kalman filtering', 'mean reversion detection'],
            'pairs_selection': ['distance method', 'cointegration method', 'copula approach'],
            'risk_management': ['position sizing', 'stop losses', 'correlation monitoring']
        },
        'factor_investing': {
            'traditional_factors': ['value (HML)', 'size (SMB)', 'momentum (MOM)', 'quality', 'low volatility'],
            'alternative_factors': ['liquidity', 'beta', 'residual momentum', 'earnings surprise'],
            'factor_timing': ['macro regime based', 'volatility adjusted', 'crowding detection']
        },
        'machine_learning_alpha': {
            'supervised': ['random forest', 'gradient boosting', 'neural networks', 'SVM'],
            'unsupervised': ['clustering regimes', 'PCA for factors', 'autoencoders'],
            'reinforcement': ['PPO for execution', 'DQN for portfolio', 'multi-agent systems'],
            'features': ['technical indicators', 'fundamental ratios', 'alternative data', 'sentiment'],
        }
    },
    'risk_management_advanced': {
        'tail_risk': ['extreme value theory', 'copula models', 'Monte Carlo with fat tails'],
        'liquidity_risk': ['Amihud illiquidity', 'bid-ask bounce', 'market impact models'],
        'correlation_risk': ['DCC-GARCH', 'realized correlation', 'correlation breakdown'],
        'stress_testing': ['historical scenarios', 'hypothetical scenarios', 'reverse stress test'],
    },
    'derivatives': {
        'pricing_models': ['Black-Scholes', 'Heston', 'local volatility', 'stochastic vol with jumps'],
        'greeks_management': ['delta hedging', 'gamma scalping', 'vega exposure', 'theta decay'],
        'exotic_options': ['barriers', 'Asians', 'lookbacks', 'compounds', 'quantos'],
        'volatility_trading': ['variance swaps', 'volatility swaps', 'VIX futures', 'volatility ETPs'],
    }
}

# Enhanced STEM Knowledge
ADVANCED_STEM = {
    'mathematics': {
        'linear_algebra': ['SVD applications', 'tensor decomposition', 'sparse matrices', 'numerical stability'],
        'calculus': ['automatic differentiation', 'symbolic computation', 'variational methods', 'optimal control'],
        'probability': ['Bayesian inference', 'MCMC methods', 'variational inference', 'Gaussian processes'],
        'optimization': ['convex optimization', 'non-convex methods', 'distributed optimization', 'metaheuristics'],
    },
    'physics': {
        'classical_mechanics': ['Lagrangian mechanics', 'Hamiltonian mechanics', 'canonical transformations'],
        'quantum_mechanics': ['path integrals', 'perturbation theory', 'scattering theory', 'quantum computing'],
        'thermodynamics': ['statistical mechanics', 'non-equilibrium', 'entropy production', 'information thermodynamics'],
        'electromagnetism': ['computational electromagnetics', 'FDTD', 'MoM', 'FEM for Maxwell'],
    },
    'chemistry': {
        'quantum_chemistry': ['DFT', 'Hartree-Fock', 'post-HF methods', 'QM/MM', 'molecular dynamics'],
        'materials': ['DFT for materials', 'band structure', 'phonons', 'defects', 'interfaces'],
        'reaction_mechanisms': ['microkinetic modeling', 'TS theory', 'kinetic Monte Carlo'],
    },
    'biology': {
        'computational_biology': ['sequence alignment', 'phylogenetics', 'protein folding', 'systems biology'],
        'genomics': ['GWAS', 'RNA-seq', 'single-cell RNA-seq', 'epigenomics', 'metagenomics'],
        'neuroscience': ['neural coding', 'connectomics', 'brain imaging', 'neural modeling'],
    }
}

# Enhanced Literature Knowledge
ADVANCED_LITERATURE = {
    'critical_theory': {
        'approaches': ['structuralism', 'post-structuralism', 'deconstruction', 'psychoanalytic criticism'],
        'lenses': ['feminist theory', 'marxist criticism', 'post-colonial theory', 'ecocriticism'],
        'methods': ['close reading', 'distant reading', 'narratology', 'intertextuality'],
    },
    'genre_analysis': {
        'literary_fiction': ['character interiority', 'thematic complexity', 'stylistic innovation'],
        'genre_fiction': ['science fiction', 'fantasy', 'mystery', 'romance', 'horror', 'thriller'],
        'poetry': ['prosody', 'free verse', 'narrative poetry', 'lyric poetry', 'dramatic monologue'],
        'drama': ['tragedy', 'comedy', 'history', 'modern drama', 'absurdist theater'],
    },
    'narrative_techniques': {
        'point_of_view': ['first person', 'third person limited', 'omniscient', 'unreliable narrator'],
        'structure': ['linear', 'non-linear', 'framed narrative', 'epistolary', 'stream of consciousness'],
        'devices': ['foreshadowing', 'irony', 'symbolism', 'motif', 'allegory', 'metaphor'],
    }
}

# Enhanced Writing Knowledge
ADVANCED_WRITING = {
    'rhetoric': {
        'ethos': ['credibility building', 'authority establishment', 'trust development'],
        'pathos': ['emotional appeal', 'storytelling', 'empathy generation'],
        'logos': ['logical argument', 'evidence presentation', 'syllogistic reasoning'],
        'kairos': ['timeliness', 'occasion awareness', 'rhetorical situation'],
    },
    'style_guides': {
        'academic': ['APA', 'MLA', 'Chicago', 'IEEE', 'Harvard'],
        'professional': ['AP Style', 'Chicago Manual', 'house styles'],
        'technical': ['Microsoft Style', 'Google Developer', 'Apple Style'],
    },
    'content_strategy': {
        'audience_analysis': ['persona development', 'user research', 'journey mapping'],
        'information_architecture': ['content hierarchy', 'taxonomy', 'metadata', 'findability'],
        'editorial': ['editorial calendar', 'workflow', 'governance', 'voice and tone'],
    }
}

# Enhanced Website Builder Knowledge
ADVANCED_WEB_DESIGN = {
    'css_architecture': {
        'methodologies': ['BEM', 'SMACSS', 'OOCSS', 'Atomic CSS', 'ITCSS', 'CUBE CSS'],
        'systems': ['Tailwind CSS', 'Bootstrap', 'Material Design', 'Chakra UI'],
        'modern_features': ['Container Queries', 'CSS Layers', 'Cascade Layers', 'Scope'],
    },
    'javascript_patterns': {
        'architectures': ['MVC', 'MVVM', 'Flux', 'Redux', 'Reactive Programming'],
        'performance': ['lazy loading', 'code splitting', 'tree shaking', 'bundle optimization'],
        'testing': ['unit testing', 'integration testing', 'e2e testing', 'visual regression'],
    },
    'accessibility': {
        'wcag': ['WCAG 2.1 Level A', 'WCAG 2.1 Level AA', 'WCAG 2.1 Level AAA'],
        'aria': ['ARIA roles', 'ARIA states', 'ARIA properties', 'live regions'],
        'testing': ['automated testing', 'screen reader testing', 'keyboard navigation'],
    },
    'performance': {
        'metrics': ['Core Web Vitals', 'LCP', 'FID', 'CLS', 'TTFB', 'FCP'],
        'optimization': ['image optimization', 'font optimization', 'critical CSS', 'resource hints'],
    }
}


def get_enhanced_knowledge(domain: str, category: str = None) -> Dict:
    """Get enhanced knowledge for a specific domain"""
    knowledge_map = {
        'code': ENHANCED_CODE_PATTERNS,
        'algorithms': ADVANCED_ALGORITHMS,
        'security': ADVANCED_SECURITY,
        'finance': ADVANCED_FINANCE,
        'stem': ADVANCED_STEM,
        'literature': ADVANCED_LITERATURE,
        'writing': ADVANCED_WRITING,
        'web': ADVANCED_WEB_DESIGN,
    }
    
    domain_knowledge = knowledge_map.get(domain.lower(), {})
    
    if category and category in domain_knowledge:
        return domain_knowledge[category]
    
    return domain_knowledge


def merge_with_existing(existing: Dict, enhanced: Dict) -> Dict:
    """Merge enhanced knowledge with existing knowledge base"""
    merged = existing.copy()
    
    for key, value in enhanced.items():
        if key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = merge_with_existing(merged[key], value)
            elif isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = list(set(merged[key] + value))
            else:
                merged[key] = value
        else:
            merged[key] = value
    
    return merged
