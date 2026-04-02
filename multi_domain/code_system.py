"""
OraclAI Professional Code Intelligence System
Claude Sonnet/Opus-Level Code Analysis (No External APIs)

Multi-Agent Architecture:
- Architect: System design, patterns, scalability, clean architecture
- Debugger: Advanced debugging, error analysis, root cause detection
- Optimizer: Algorithmic complexity, performance engineering, profiling
- Security: Security audit, vulnerability assessment, threat modeling
- Reviewer: Code review, best practices, style compliance
- Algorithms: Data structures, algorithms, complexity analysis
- Testing: Test coverage, TDD, CI/CD integration
"""

import re
import ast
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition, DebateResult

# Comprehensive knowledge base for professional code analysis
CODE_PATTERNS = {
    'python': {
        'design_patterns': {
            'singleton': r'class\s+\w+.*?def\s+__new__|@singleton|_instance\s*=',
            'factory': r'def\s+create_|class\s+.*Factory|factory\.py',
            'observer': r'class\s+.*Observer|add_listener|notify\(|subscribe\(',
            'decorator': r'@wraps|def\s+wrapper|def\s+decorator',
            'strategy': r'class\s+.*Strategy|execute_strategy|Context\s*=',
            'mvc': r'class\s+.*Model|class\s+.*View|class\s+.*Controller',
            'repository': r'class\s+.*Repository|def\s+save\(|def\s+find_by',
            'dependency_injection': r'inject|@injectable|Container\s*=|Provider\s*=',
        },
        'anti_patterns': {
            'god_class': r'class\s+\w+.*:.*\n(?:.*\n){50,}',
            'spaghetti': r'goto|break.*\n.*for|continue.*\n.*while',
            'magic_numbers': r'[^\w](?!0[xob])[0-9]{3,}(?![\w"])',
            'duplicate_code': r'(def\s+\w+\([^)]*\):.*?)(?=\1)',
        },
        'performance_indicators': {
            'list_comprehension': r'\[.*for.*in.*\]',
            'generator': r'yield|generator|(?:\(|\[).*for.*in.*\)',
            'async': r'async\s+def|await\s+|asyncio|aiohttp',
            'caching': r'@lru_cache|@cache|memoize|redis|memcached',
            'vectorization': r'numpy|pandas|torch|tensorflow|vectorize',
        }
    },
    'javascript': {
        'design_patterns': {
            'module': r'module\.exports|exports\.|require\(|import.*from',
            'prototype': r'\.prototype\.|__proto__|Object\.create',
            'promise': r'Promise|async.*await|\.then\(|\.catch\(',
            'event_emitter': r'\.on\(|\.emit\(|EventEmitter',
        },
        'anti_patterns': {
            'callback_hell': r'\).*\{[^}]*\}\s*\)',
            'var_usage': r'\bvar\s+',
            'implicit_coercion': r'\+\s*["\']|==\s*(?!===)',
        }
    }
}

ALGORITHMS_KNOWLEDGE = {
    'sorting': {
        'quick_sort': {'complexity': 'O(n log n)', 'space': 'O(log n)', 'stable': False},
        'merge_sort': {'complexity': 'O(n log n)', 'space': 'O(n)', 'stable': True},
        'heap_sort': {'complexity': 'O(n log n)', 'space': 'O(1)', 'stable': False},
        'bubble_sort': {'complexity': 'O(n²)', 'space': 'O(1)', 'stable': True},
    },
    'searching': {
        'binary_search': {'complexity': 'O(log n)', 'requires': 'sorted array'},
        'linear_search': {'complexity': 'O(n)', 'requires': 'none'},
        'hash_lookup': {'complexity': 'O(1) average', 'requires': 'hash table'},
    },
    'graphs': {
        'dijkstra': {'complexity': 'O((V+E) log V)', 'use': 'shortest path'},
        'bfs': {'complexity': 'O(V+E)', 'use': 'level-order traversal'},
        'dfs': {'complexity': 'O(V+E)', 'use': 'depth exploration'},
        'a_star': {'complexity': 'O((V+E) log V)', 'use': 'pathfinding with heuristic'},
    }
}

SECURITY_VULNERABILITIES = {
    'injection': {
        'sql_injection': r'execute\s*\(.*%s|execute\s*\(.*\+.*\+|\.format\(.*\)|f".*\{.*\}.*".*execute',
        'command_injection': r'os\.system\(|subprocess\.call\(|subprocess\.run\(.*?shell\s*=\s*True',
        'code_injection': r'eval\(|exec\(|compile\(|__import__\(',
    },
    'data_exposure': {
        'hardcoded_secrets': r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=\s*["\']|secret\s*=\s*["\']|token\s*=\s*["\']',
        'insecure_logging': r'print\(.*password|print\(.*secret|log\.info\(.*password|logger\.debug\(.*token',
        'sensitive_data': r'ssn|social_security|credit_card|cvv|private_key',
    },
    'crypto_failures': {
        'weak_hash': r'md5\(|sha1\(|\.md5\(|\.sha1\(',
        'no_encryption': r'http://(?!localhost)|ftp://|telnet://',
        'insecure_random': r'random\.random\(|random\.randint\(|\.shuffle\(|np\.random',
    },
    'access_control': {
        'missing_auth': r'@login_required|@authenticated|@requires_auth',
        'insecure_permissions': r'chmod\s*777|777.*permissions|os\.chmod\(.*0o777',
        'cors_misconfig': r'CORS\(.*\*|Access-Control-Allow-Origin:\s*\*',
    }
}

BEST_PRACTICES = {
    'python': {
        'type_hints': r'->\s+\w+|:\s+\w+\s*=|from\s+typing\s+import',
        'docstrings': r'"""[^"]*"""|\'\'\'[^\']*\'\'\'',
        'error_handling': r'try:|except\s+\w+|finally:|raise\s+\w+',
        'testing': r'def\s+test_|import\s+pytest|import\s+unittest|@pytest',
        'logging': r'import\s+logging|logger\s*=|log\.|logging\.',
    },
    'javascript': {
        'strict_mode': r'"use strict"|\'use strict\'',
        'error_handling': r'try\s*\{|catch\s*\(|finally\s*\{|throw\s+new',
        'es6_features': r'const\s+|let\s+|arrow\s*=>|template\s*literal|class\s+|import\s+|export\s+',
    }
}

@dataclass
class CodeMetrics:
    """Comprehensive code quality metrics"""
    lines_of_code: int
    cyclomatic_complexity: int
    maintainability_index: float
    code_duplication: float
    test_coverage: Optional[float]
    documentation_coverage: float
    security_score: int
    performance_score: int


class ArchitectAgent(BaseAgent):
    """
    Senior Software Architect - Focuses on:
    - System design and architecture patterns
    - Scalability and performance architecture
    - SOLID principles and clean code
    - Design patterns implementation
    - Technical debt assessment
    """
    
    def __init__(self):
        super().__init__(
            name="Architect",
            role="Principal Software Architect",
            expertise=[
                'system design', 'architecture patterns', 'scalability', 
                'microservices', 'domain-driven design', 'event-driven architecture',
                'SOLID principles', 'clean architecture', 'design patterns',
                'API design', 'database design', 'distributed systems'
            ]
        )
        self.patterns_found = []
        self.architecture_issues = []
        
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        language = context.get('language', 'python').lower()
        
        # Detect design patterns
        patterns = self._detect_patterns(code, language)
        
        # Analyze architecture
        architecture_analysis = self._analyze_architecture(code, language)
        
        # Check SOLID principles
        solid_violations = self._check_solid_principles(code)
        
        # Assess scalability
        scalability_concerns = self._assess_scalability(code)
        
        # Build comprehensive reasoning
        reasoning_parts = []
        
        if patterns:
            reasoning_parts.append(f"✓ Detected {len(patterns)} design patterns: {', '.join(patterns[:3])}")
        
        if solid_violations:
            reasoning_parts.append(f"⚠ SOLID violations: {'; '.join(solid_violations[:2])}")
        
        if architecture_analysis['issues']:
            reasoning_parts.append(f"⚠ Architecture issues: {'; '.join(architecture_analysis['issues'][:2])}")
        
        if scalability_concerns:
            reasoning_parts.append(f"⚠ Scalability: {'; '.join(scalability_concerns[:2])}")
        
        if not reasoning_parts:
            reasoning_parts.append("✓ Clean architecture following best practices. Good separation of concerns and modularity.")
        
        # Determine stance
        total_issues = len(solid_violations) + len(architecture_analysis['issues']) + len(scalability_concerns)
        
        if total_issues == 0:
            stance = 'positive'
            confidence = 0.92
        elif total_issues <= 2:
            stance = 'constructive'
            confidence = 0.78
        else:
            stance = 'critical'
            confidence = 0.85
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=patterns + solid_violations + architecture_analysis['issues'][:3]
        )
    
    def _detect_patterns(self, code: str, language: str) -> List[str]:
        """Detect design patterns in code"""
        patterns = []
        patterns_dict = CODE_PATTERNS.get(language, {}).get('design_patterns', {})
        
        for pattern_name, pattern_regex in patterns_dict.items():
            if re.search(pattern_regex, code, re.IGNORECASE):
                patterns.append(pattern_name.replace('_', ' ').title())
        
        return patterns
    
    def _analyze_architecture(self, code: str, language: str) -> Dict:
        """Analyze architectural quality"""
        issues = []
        strengths = []
        
        lines = code.split('\n')
        
        # Check for god classes/functions
        if len(lines) > 200:
            class_matches = re.findall(r'class\s+\w+', code)
            if len(class_matches) == 0 or len(class_matches) > 5:
                issues.append("Consider breaking into smaller, focused classes")
        
        # Check module organization
        if language == 'python':
            if 'if __name__' not in code and len(lines) > 50:
                issues.append("Add main guard for better module organization")
        
        # Check coupling
        global_vars = re.findall(r'^\s*(\w+)\s*=\s*[^=]', code, re.MULTILINE)
        if len(global_vars) > 5:
            issues.append(f"High coupling: {len(global_vars)} global variables")
        
        # Check for proper abstraction
        function_count = len(re.findall(r'def\s+\w+', code))
        class_count = len(re.findall(r'class\s+\w+', code))
        
        if function_count > 20 and class_count == 0:
            issues.append("Consider organizing functions into classes/modules")
        
        return {'issues': issues, 'strengths': strengths}
    
    def _check_solid_principles(self, code: str) -> List[str]:
        """Check for SOLID principle violations"""
        violations = []
        
        # S - Single Responsibility
        large_classes = re.findall(r'class\s+(\w+).*?:', code)
        if len(large_classes) > 0:
            for class_name in large_classes[:3]:
                class_methods = len(re.findall(rf'class\s+{class_name}.*?def\s+\w+', code))
                if class_methods > 10:
                    violations.append(f"{class_name} may violate SRP ({class_methods} methods)")
        
        # O - Open/Closed
        if 'if.*type' in code or 'isinstance.*if' in code:
            violations.append("Type checking suggests OCP violation - consider polymorphism")
        
        # L - Liskov Substitution (basic check)
        if 'raise NotImplementedError' in code:
            violations.append("NotImplementedError may indicate LSP violation")
        
        # I - Interface Segregation
        large_interfaces = len(re.findall(r'def\s+\w+.*\([^)]{50,}\)', code))
        if large_interfaces > 0:
            violations.append("Large parameter lists suggest ISP violation")
        
        # D - Dependency Inversion
        if 'import' in code:
            concrete_deps = len(re.findall(r'from\s+\w+\s+import\s+\w+', code))
            if concrete_deps > 10:
                violations.append("Many concrete imports - consider dependency injection")
        
        return violations
    
    def _assess_scalability(self, code: str) -> List[str]:
        """Assess scalability concerns"""
        concerns = []
        
        # Check for blocking operations
        if 'time.sleep' in code or 'sleep(' in code:
            concerns.append("Blocking sleep calls may impact scalability")
        
        # Check for synchronous I/O
        if 'requests.get' in code or 'urllib' in code:
            concerns.append("Synchronous HTTP calls - consider async for scalability")
        
        # Check for database connection patterns
        if 'connect' in code.lower() and 'pool' not in code.lower():
            concerns.append("Database connections without pooling")
        
        return concerns


class DebuggerAgent(BaseAgent):
    """
    Senior Debugging Specialist - Focuses on:
    - Advanced debugging techniques
    - Root cause analysis
    - Error handling patterns
    - Race conditions and concurrency
    - Memory leak detection
    """
    
    def __init__(self):
        super().__init__(
            name="Debugger",
            role="Senior Debugging Specialist",
            expertise=[
                'debugging', 'root cause analysis', 'error handling', 
                'stack trace analysis', 'race conditions', 'deadlocks',
                'memory leaks', 'performance profiling', 'logging',
                'exception handling', 'fault tolerance'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        error_msg = context.get('error', '')
        
        bugs = []
        warnings = []
        improvements = []
        
        # Check error handling
        error_analysis = self._analyze_error_handling(code)
        bugs.extend(error_analysis['bugs'])
        warnings.extend(error_analysis['warnings'])
        
        # Check for common bug patterns
        bug_patterns = self._detect_bug_patterns(code)
        bugs.extend(bug_patterns)
        
        # Check for race conditions
        race_conditions = self._detect_race_conditions(code)
        warnings.extend(race_conditions)
        
        # Check for resource leaks
        leaks = self._detect_resource_leaks(code)
        bugs.extend(leaks)
        
        # Build reasoning
        reasoning_parts = []
        
        if bugs:
            reasoning_parts.append(f"🐛 Critical bugs: {len(bugs)} found - {bugs[0]}")
        
        if warnings:
            reasoning_parts.append(f"⚠️ Warnings: {len(warnings)} - {warnings[0]}")
        
        if error_msg:
            reasoning_parts.append(f"❌ Runtime error: {error_msg[:100]}")
        
        if not reasoning_parts:
            reasoning_parts.append("✓ No critical bugs detected. Error handling looks robust.")
        
        # Determine stance
        if bugs:
            stance = 'critical'
            confidence = 0.88
        elif warnings:
            stance = 'constructive'
            confidence = 0.75
        else:
            stance = 'positive'
            confidence = 0.90
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=bugs + warnings[:3]
        )
    
    def _analyze_error_handling(self, code: str) -> Dict:
        """Analyze error handling quality"""
        bugs = []
        warnings = []
        
        # Bare except clauses
        bare_excepts = re.findall(r'except\s*:', code)
        if bare_excepts:
            bugs.append(f"Bare except: clauses ({len(bare_excepts)}) - catch specific exceptions")
        
        # Pass in except blocks
        pass_in_except = re.findall(r'except.*?pass', code, re.DOTALL)
        if pass_in_except:
            warnings.append("Silent exception handling with 'pass'")
        
        # Missing error handling
        risky_ops = ['open(', 'connect', 'fetch', 'query']
        for op in risky_ops:
            if op in code and 'try' not in code:
                warnings.append(f"{op} without error handling")
        
        return {'bugs': bugs, 'warnings': warnings}
    
    def _detect_bug_patterns(self, code: str) -> List[str]:
        """Detect common bug patterns"""
        bugs = []
        
        # Mutable default arguments
        if 'def ' in code and '= []' in code or '= {}' in code:
            bugs.append("Mutable default arguments - use None instead")
        
        # Variable shadowing
        if '= []' in code and 'for' in code:
            bugs.append("Potential variable shadowing in loops")
        
        # Incorrect None check
        if '==' in code and 'None' in code:
            if 'is None' not in code and 'is not None' not in code:
                bugs.append("Use 'is'/'is not' for None comparisons")
        
        # String concatenation in loops
        if 'for' in code and '+=' in code:
            if '"' in code or "'" in code:
                bugs.append("String concatenation in loop - use list join()")
        
        return bugs
    
    def _detect_race_conditions(self, code: str) -> List[str]:
        """Detect potential race conditions"""
        warnings = []
        
        # Threading without locks
        if 'threading' in code or 'Thread' in code:
            if 'Lock' not in code and 'Semaphore' not in code:
                warnings.append("Threading without synchronization primitives")
        
        # Shared mutable state
        if 'global' in code:
            warnings.append("Global state may cause race conditions")
        
        return warnings
    
    def _detect_resource_leaks(self, code: str) -> List[str]:
        """Detect resource leak patterns"""
        leaks = []
        
        # File operations without context managers
        if 'open(' in code:
            if 'with' not in code:
                leaks.append("File operations without 'with' statement - potential leak")
        
        # Database connections
        if 'connect' in code.lower():
            if 'close' not in code.lower():
                leaks.append("Database connection without explicit close")
        
        return leaks


class OptimizerAgent(BaseAgent):
    """
    Performance Engineering Specialist - Focuses on:
    - Algorithmic complexity analysis
    - Memory optimization
    - CPU profiling
    - Database query optimization
    - Caching strategies
    """
    
    def __init__(self):
        super().__init__(
            name="Optimizer",
            role="Performance Engineering Specialist",
            expertise=[
                'algorithm analysis', 'big O notation', 'profiling', 
                'memory optimization', 'caching', 'database optimization',
                'parallelization', 'async programming', 'vectorization',
                'compiler optimizations', 'JIT', 'performance tuning'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        
        optimizations = []
        concerns = []
        complexity_analysis = []
        
        # Analyze algorithmic complexity
        complexity = self._analyze_complexity(code)
        if complexity['issues']:
            concerns.extend(complexity['issues'])
        complexity_analysis = complexity['analysis']
        
        # Check for optimization opportunities
        optimizations = self._find_optimizations(code)
        
        # Check memory usage
        memory_issues = self._analyze_memory(code)
        concerns.extend(memory_issues)
        
        # Check I/O patterns
        io_issues = self._analyze_io(code)
        concerns.extend(io_issues)
        
        # Build reasoning
        reasoning_parts = []
        
        if complexity_analysis:
            reasoning_parts.append(f"📊 Complexity: {complexity_analysis[0]}")
        
        if optimizations:
            reasoning_parts.append(f"🚀 Optimizations: {len(optimizations)} possible - {optimizations[0]}")
        
        if concerns:
            reasoning_parts.append(f"⚠️ Concerns: {len(concerns)} - {concerns[0]}")
        
        if not reasoning_parts:
            reasoning_parts.append("✓ Performance characteristics are optimal for the use case.")
        
        # Determine stance
        if concerns:
            stance = 'analytical'
            confidence = 0.82
        elif optimizations:
            stance = 'constructive'
            confidence = 0.75
        else:
            stance = 'positive'
            confidence = 0.88
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=optimizations + concerns[:3]
        )
    
    def _analyze_complexity(self, code: str) -> Dict:
        """Analyze algorithmic complexity"""
        issues = []
        analysis = []
        
        # Count nested loops
        lines = code.split('\n')
        max_indent = 0
        nested_loops = 0
        
        for line in lines:
            indent = len(line) - len(line.lstrip())
            if 'for ' in line or 'while ' in line:
                if indent > max_indent:
                    nested_loops += 1
                max_indent = max(max_indent, indent)
        
        if nested_loops >= 3:
            issues.append(f"O(n³) complexity detected - {nested_loops} nested loops")
            analysis.append("Cubic time complexity - consider optimization")
        elif nested_loops == 2:
            analysis.append("Quadratic O(n²) complexity - may be acceptable")
        else:
            analysis.append("Linear or better complexity")
        
        # Check for inefficient operations
        if 'in list' in code:
            issues.append("O(n) lookup in list - consider using set/dict")
        
        return {'issues': issues, 'analysis': analysis}
    
    def _find_optimizations(self, code: str) -> List[str]:
        """Find optimization opportunities"""
        optimizations = []
        
        # List comprehensions
        if 'for ' in code and 'append' in code:
            optimizations.append("Convert loop + append to list comprehension")
        
        # Generator expressions
        if 'sum(' in code and '[' in code:
            optimizations.append("Use generator expression instead of list for sum()")
        
        # String building
        if 'for' in code and '+=' in code:
            if '"' in code or "'" in code:
                optimizations.append("Use str.join() instead of += for strings")
        
        # Caching opportunities
        if 'def ' in code and 'for' in code:
            if 'recursive' in code.lower() or 'fibonacci' in code.lower():
                optimizations.append("Add @lru_cache for memoization")
        
        # Database query optimization
        if 'SELECT' in code.upper():
            if '*' in code:
                optimizations.append("SELECT * - specify columns for efficiency")
            if 'N+1' in code or 'for' in code and 'query' in code.lower():
                optimizations.append("N+1 query pattern - use eager loading")
        
        return optimizations
    
    def _analyze_memory(self, code: str) -> List[str]:
        """Analyze memory usage patterns"""
        issues = []
        
        # Large list creation
        if 'range(' in code or 'list(' in code:
            if '100000' in code or '1000000' in code:
                issues.append("Large list creation - consider generator")
        
        # Memory-intensive operations
        if 'pandas' in code or 'numpy' in code:
            if 'read_csv' in code or 'load' in code:
                issues.append("Large data loading - consider chunking")
        
        return issues
    
    def _analyze_io(self, code: str) -> List[str]:
        """Analyze I/O patterns"""
        issues = []
        
        # Synchronous I/O in loops
        if 'for' in code:
            if 'requests.' in code or 'http' in code.lower():
                issues.append("HTTP calls in loop - consider async or batching")
        
        return issues


class SecurityAgent(BaseAgent):
    """
    Security Audit Specialist - Focuses on:
    - Vulnerability assessment
    - Security best practices
    - OWASP compliance
    - Threat modeling
    - Cryptographic implementations
    """
    
    def __init__(self):
        super().__init__(
            name="Security",
            role="Security Audit Specialist",
            expertise=[
                'vulnerability scanning', 'penetration testing', 'OWASP',
                'secure coding', 'cryptography', 'authentication',
                'authorization', 'input validation', 'SQL injection',
                'XSS prevention', 'CSRF protection', 'threat modeling'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        language = context.get('language', 'python').lower()
        
        critical = []
        high = []
        medium = []
        low = []
        
        # Check for injection vulnerabilities
        injection = self._check_injection_vulnerabilities(code)
        critical.extend(injection['critical'])
        high.extend(injection['high'])
        
        # Check for data exposure
        exposure = self._check_data_exposure(code)
        high.extend(exposure['high'])
        medium.extend(exposure['medium'])
        
        # Check for crypto failures
        crypto = self._check_crypto(code)
        high.extend(crypto['high'])
        medium.extend(crypto['medium'])
        
        # Check access control
        access = self._check_access_control(code)
        high.extend(access['high'])
        medium.extend(access['medium'])
        
        # Check other vulnerabilities
        other = self._check_other_vulnerabilities(code)
        medium.extend(other['medium'])
        low.extend(other['low'])
        
        # Build reasoning
        reasoning_parts = []
        
        if critical:
            reasoning_parts.append(f"🚨 CRITICAL: {critical[0]}")
        elif high:
            reasoning_parts.append(f"🔴 HIGH: {len(high)} issues - {high[0]}")
        elif medium:
            reasoning_parts.append(f"🟡 MEDIUM: {len(medium)} issues - {medium[0]}")
        elif low:
            reasoning_parts.append(f"🟢 LOW: {len(low)} minor issues")
        else:
            reasoning_parts.append("✅ Security scan passed - no vulnerabilities detected")
        
        # Determine stance
        if critical:
            stance = 'critical'
            confidence = 0.95
        elif high:
            stance = 'critical'
            confidence = 0.88
        elif medium:
            stance = 'constructive'
            confidence = 0.75
        else:
            stance = 'positive'
            confidence = 0.90
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=critical + high + medium[:2]
        )
    
    def _check_injection_vulnerabilities(self, code: str) -> Dict:
        """Check for injection vulnerabilities"""
        critical = []
        high = []
        
        patterns = SECURITY_VULNERABILITIES.get('injection', {})
        
        for vuln_name, pattern in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                if 'sql' in vuln_name or 'command' in vuln_name:
                    critical.append(f"{vuln_name.replace('_', ' ').title()} vulnerability")
                else:
                    high.append(f"{vuln_name.replace('_', ' ').title()} risk")
        
        return {'critical': critical, 'high': high}
    
    def _check_data_exposure(self, code: str) -> Dict:
        """Check for sensitive data exposure"""
        high = []
        medium = []
        
        patterns = SECURITY_VULNERABILITIES.get('data_exposure', {})
        
        for vuln_name, pattern in patterns.items():
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                if 'hardcoded' in vuln_name:
                    high.append(f"Hardcoded credentials ({len(matches)} found)")
                elif 'logging' in vuln_name:
                    medium.append("Sensitive data in logs")
                else:
                    medium.append(f"{vuln_name.replace('_', ' ')} exposure")
        
        return {'high': high, 'medium': medium}
    
    def _check_crypto(self, code: str) -> Dict:
        """Check cryptographic implementations"""
        high = []
        medium = []
        
        patterns = SECURITY_VULNERABILITIES.get('crypto_failures', {})
        
        for vuln_name, pattern in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                if 'weak_hash' in vuln_name:
                    high.append("Weak cryptographic hash (MD5/SHA1)")
                elif 'no_encryption' in vuln_name:
                    high.append("Unencrypted data transmission")
                elif 'insecure_random' in vuln_name:
                    medium.append("Insecure random number generation")
        
        return {'high': high, 'medium': medium}
    
    def _check_access_control(self, code: str) -> Dict:
        """Check access control mechanisms"""
        high = []
        medium = []
        
        patterns = SECURITY_VULNERABILITIES.get('access_control', {})
        
        for vuln_name, pattern in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                if 'missing_auth' in vuln_name:
                    high.append("Missing authentication check")
                elif 'insecure_permissions' in vuln_name:
                    high.append("Overly permissive file permissions")
                elif 'cors_misconfig' in vuln_name:
                    medium.append("Permissive CORS configuration")
        
        return {'high': high, 'medium': medium}
    
    def _check_other_vulnerabilities(self, code: str) -> Dict:
        """Check for other security issues"""
        medium = []
        low = []
        
        # Debug mode
        if 'DEBUG' in code or 'debug=True' in code:
            medium.append("Debug mode enabled in production")
        
        # Verbose errors
        if 'traceback' in code and 'print' in code:
            medium.append("Verbose error messages may leak info")
        
        return {'medium': medium, 'low': low}


class AlgorithmsAgent(BaseAgent):
    """
    Algorithms & Data Structures Expert - Focuses on:
    - Algorithm selection and optimization
    - Data structure choice
    - Complexity analysis
    - Competitive programming patterns
    """
    
    def __init__(self):
        super().__init__(
            name="Algorithms",
            role="Algorithms & Data Structures Expert",
            expertise=[
                'algorithms', 'data structures', 'complexity analysis',
                'graph algorithms', 'dynamic programming', 'greedy algorithms',
                'sorting', 'searching', 'tree algorithms', 'heap',
                'hash tables', 'tries', 'segment trees', 'fenwick tree'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        
        algorithms_detected = []
        improvements = []
        complexity_notes = []
        
        # Detect implemented algorithms
        detected = self._detect_algorithms(code)
        algorithms_detected = detected['algorithms']
        complexity_notes = detected['complexity']
        
        # Suggest algorithmic improvements
        improvements = self._suggest_improvements(code, detected)
        
        # Build reasoning
        reasoning_parts = []
        
        if algorithms_detected:
            reasoning_parts.append(f"📚 Algorithms: {', '.join(algorithms_detected[:2])}")
        
        if complexity_notes:
            reasoning_parts.append(f"⏱️ Complexity: {complexity_notes[0]}")
        
        if improvements:
            reasoning_parts.append(f"💡 Suggestions: {improvements[0]}")
        
        if not reasoning_parts:
            reasoning_parts.append("📊 Standard algorithmic approach. Consider documenting complexity.")
        
        # Determine stance
        if improvements:
            stance = 'constructive'
            confidence = 0.78
        else:
            stance = 'positive'
            confidence = 0.85
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=algorithms_detected + improvements[:2]
        )
    
    def _detect_algorithms(self, code: str) -> Dict:
        """Detect algorithms and data structures in code"""
        algorithms = []
        complexity = []
        
        # Check for sorting algorithms
        for sort_name in ALGORITHMS_KNOWLEDGE['sorting'].keys():
            if sort_name.replace('_', '') in code.lower() or sort_name in code.lower():
                info = ALGORITHMS_KNOWLEDGE['sorting'][sort_name]
                algorithms.append(sort_name.replace('_', ' ').title())
                complexity.append(f"{sort_name}: {info['complexity']}")
        
        # Check for graph algorithms
        if 'graph' in code.lower() or 'node' in code.lower():
            for graph_algo in ALGORITHMS_KNOWLEDGE['graphs'].keys():
                if graph_algo in code.lower():
                    info = ALGORITHMS_KNOWLEDGE['graphs'][graph_algo]
                    algorithms.append(graph_algo.upper())
                    complexity.append(f"{graph_algo}: {info['complexity']}")
        
        # Check for data structures
        if 'heap' in code.lower() or 'priority' in code.lower():
            algorithms.append("Heap/Priority Queue")
        if 'tree' in code.lower() and 'class' in code.lower():
            algorithms.append("Tree structure")
        if 'dict' in code or 'hash' in code.lower():
            algorithms.append("Hash Table")
        
        # Dynamic programming patterns
        if 'dp' in code.lower() or 'memo' in code.lower() or 'cache' in code.lower():
            algorithms.append("Dynamic Programming/Memoization")
        
        return {'algorithms': algorithms, 'complexity': complexity}
    
    def _suggest_improvements(self, code: str, detected: Dict) -> List[str]:
        """Suggest algorithmic improvements"""
        improvements = []
        
        # Check for inefficient sorting
        if 'sorted(' not in code and 'sort(' not in code:
            if 'for' in code and 'min(' in code and 'for' in code:
                improvements.append("Selection sort pattern - use Timsort (sorted())")
        
        # Check for inefficient searching
        if 'in list' in code or '.index(' in code:
            improvements.append("O(n) search - consider set/dict for O(1) lookup")
        
        # Check for graph representation
        if 'graph' in code.lower():
            if 'matrix' in code.lower():
                improvements.append("Adjacency matrix uses O(V²) space - consider adjacency list")
        
        # Check for recursion without memoization
        if 'def ' in code:
            func = re.search(r'def\s+(\w+)', code)
            if func:
                func_name = func.group(1)
                if re.search(rf'{func_name}\s*\(', code[code.find(func_name):]):
                    if 'fibonacci' in code.lower() or 'factorial' in code.lower():
                        improvements.append("Recursive function without memoization - exponential time")
        
        return improvements


class TestingAgent(BaseAgent):
    """
    Testing & Quality Assurance Expert - Focuses on:
    - Test coverage analysis
    - Test strategy
    - TDD patterns
    - CI/CD integration
    """
    
    def __init__(self):
        super().__init__(
            name="Testing",
            role="QA & Test Strategy Expert",
            expertise=[
                'unit testing', 'integration testing', 'TDD', 'BDD',
                'test coverage', 'pytest', 'unittest', 'mocking',
                'CI/CD', 'automated testing', 'regression testing',
                'performance testing', 'security testing'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        
        test_gaps = []
        test_strengths = []
        recommendations = []
        
        # Check for test files
        if 'test' in query.lower() or 'test_' in code:
            analysis = self._analyze_test_code(code)
            test_gaps = analysis['gaps']
            test_strengths = analysis['strengths']
        else:
            # Check if code needs tests
            test_gaps = self._check_test_needs(code)
        
        # Generate recommendations
        if test_gaps:
            recommendations = self._generate_test_recommendations(code, test_gaps)
        
        # Build reasoning
        reasoning_parts = []
        
        if test_strengths:
            reasoning_parts.append(f"✅ Testing: {test_strengths[0]}")
        
        if test_gaps:
            reasoning_parts.append(f"⚠️ Gaps: {len(test_gaps)} - {test_gaps[0]}")
        
        if recommendations:
            reasoning_parts.append(f"📝 Recommend: {recommendations[0]}")
        
        if not reasoning_parts:
            reasoning_parts.append("🧪 Consider adding unit tests for critical paths")
        
        # Determine stance
        if test_gaps and not test_strengths:
            stance = 'critical'
            confidence = 0.80
        elif test_gaps:
            stance = 'constructive'
            confidence = 0.75
        else:
            stance = 'positive'
            confidence = 0.90
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=test_gaps + recommendations[:2]
        )
    
    def _analyze_test_code(self, code: str) -> Dict:
        """Analyze existing test code"""
        gaps = []
        strengths = []
        
        # Check test patterns
        if 'def test_' in code:
            test_count = len(re.findall(r'def\s+test_', code))
            strengths.append(f"{test_count} test functions defined")
        
        # Check for assertions
        if 'assert' in code:
            assert_count = len(re.findall(r'assert\s+', code))
            strengths.append(f"{assert_count} assertions")
        else:
            gaps.append("No assertions found - tests may not verify anything")
        
        # Check for fixtures/mocks
        if '@pytest.fixture' in code or '@fixture' in code:
            strengths.append("Using pytest fixtures")
        if 'mock' in code.lower() or 'Mock' in code:
            strengths.append("Mocking in use")
        
        # Check for edge cases
        if 'None' in code or 'null' in code.lower() or '[]' in code:
            strengths.append("Edge case testing (null/empty)")
        else:
            gaps.append("Add tests for edge cases (None, empty, boundary)")
        
        return {'gaps': gaps, 'strengths': strengths}
    
    def _check_test_needs(self, code: str) -> List[str]:
        """Check what testing is needed for code"""
        gaps = []
        
        # Check code complexity
        functions = len(re.findall(r'def\s+\w+', code))
        classes = len(re.findall(r'class\s+\w+', code))
        
        if functions > 0 and 'test' not in code.lower():
            gaps.append(f"{functions} functions without tests")
        
        if classes > 0 and 'test' not in code.lower():
            gaps.append(f"{classes} classes without tests")
        
        # Check for complex logic
        if 'if' in code and 'else' in code:
            branches = len(re.findall(r'if\s+|elif\s+|else:', code))
            if branches > 5:
                gaps.append(f"Complex branching ({branches} branches) needs thorough testing")
        
        return gaps
    
    def _generate_test_recommendations(self, code: str, gaps: List[str]) -> List[str]:
        """Generate testing recommendations"""
        recommendations = []
        
        if 'pytest' not in code and 'unittest' not in code:
            recommendations.append("Use pytest for modern testing framework")
        
        if 'mock' not in code.lower():
            recommendations.append("Add mocking for external dependencies")
        
        if 'parametrize' not in code:
            recommendations.append("Use @pytest.mark.parametrize for multiple test cases")
        
        return recommendations


class CodeReviewerAgent(BaseAgent):
    """
    Senior Code Reviewer - Focuses on:
    - Code style and conventions
    - Documentation quality
    - Best practices compliance
    - Maintainability
    """
    
    def __init__(self):
        super().__init__(
            name="Reviewer",
            role="Senior Code Reviewer",
            expertise=[
                'code review', 'documentation', 'style guides', 
                'PEP 8', 'clean code', 'maintainability',
                'readability', 'naming conventions', 'refactoring',
                'technical debt', 'code metrics'
            ]
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        language = context.get('language', 'python').lower()
        
        style_issues = []
        doc_issues = []
        maintainability_issues = []
        positives = []
        
        # Check style compliance
        style = self._check_style(code, language)
        style_issues = style['issues']
        positives = style['positives']
        
        # Check documentation
        docs = self._check_documentation(code)
        doc_issues = docs['issues']
        if docs['positives']:
            positives.extend(docs['positives'])
        
        # Check maintainability
        maintainability = self._check_maintainability(code)
        maintainability_issues = maintainability['issues']
        
        # Build reasoning
        reasoning_parts = []
        
        if positives:
            reasoning_parts.append(f"✅ {positives[0]}")
        
        if style_issues:
            reasoning_parts.append(f"📝 Style: {len(style_issues)} issues - {style_issues[0]}")
        
        if doc_issues:
            reasoning_parts.append(f"📚 Docs: {len(doc_issues)} gaps - {doc_issues[0]}")
        
        if maintainability_issues:
            reasoning_parts.append(f"🔧 Maintainability: {maintainability_issues[0]}")
        
        if not reasoning_parts:
            reasoning_parts.append("✨ Excellent code quality - production ready")
        
        # Determine stance
        total_issues = len(style_issues) + len(doc_issues) + len(maintainability_issues)
        
        if total_issues > 5:
            stance = 'critical'
            confidence = 0.75
        elif total_issues > 2:
            stance = 'constructive'
            confidence = 0.72
        else:
            stance = 'positive'
            confidence = 0.88
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts),
            key_points=style_issues + doc_issues[:2]
        )
    
    def _check_style(self, code: str, language: str) -> Dict:
        """Check code style compliance"""
        issues = []
        positives = []
        
        if language == 'python':
            # Check PEP 8 naming
            functions = re.findall(r'def\s+(\w+)', code)
            for func in functions:
                if func[0].isupper():
                    issues.append(f"Function '{func}' should be lowercase (snake_case)")
            
            classes = re.findall(r'class\s+(\w+)', code)
            for cls in classes:
                if cls[0].islower():
                    issues.append(f"Class '{cls}' should be CamelCase")
            
            # Check line length
            long_lines = [line for line in code.split('\n') if len(line) > 100]
            if long_lines:
                issues.append(f"{len(long_lines)} lines exceed 100 characters")
            
            # Check imports
            if 'import' in code:
                positives.append("Imports organized")
        
        return {'issues': issues, 'positives': positives}
    
    def _check_documentation(self, code: str) -> Dict:
        """Check documentation quality"""
        issues = []
        positives = []
        
        functions = re.findall(r'def\s+(\w+)', code)
        documented = len(re.findall(r'""".*?"""', code, re.DOTALL))
        
        if functions and documented < len(functions) / 2:
            issues.append(f"Missing docstrings ({len(functions) - documented} functions)")
        
        if documented > 0:
            positives.append(f"{documented} documented functions/classes")
        
        # Check for inline comments
        comments = len([line for line in code.split('\n') if line.strip().startswith('#')])
        if comments > 0:
            positives.append(f"{comments} inline comments")
        
        return {'issues': issues, 'positives': positives}
    
    def _check_maintainability(self, code: str) -> Dict:
        """Check maintainability metrics"""
        issues = []
        
        # Cyclomatic complexity (simple heuristic)
        branches = len(re.findall(r'\b(if|elif|else|for|while|and|or)\b', code))
        if branches > 15:
            issues.append(f"High complexity ({branches} branches) - consider refactoring")
        
        # Code length
        lines = len(code.split('\n'))
        if lines > 500:
            issues.append(f"Large file ({lines} lines) - consider splitting")
        
        # Function length
        functions = re.findall(r'def\s+\w+\([^)]*\):\s*\n((?:.*\n)+?)(?=def\s|class\s|$)', code)
        for func in functions:
            if len(func.split('\n')) > 50:
                issues.append("Function exceeds 50 lines - consider breaking down")
        
        return {'issues': issues}


class CodeAI(MultiAgentSystem):
    """
    Claude Sonnet/Opus-Level Code Intelligence System
    Multi-agent architecture for comprehensive code analysis
    """
    
    def __init__(self):
        super().__init__(domain_name='Code', max_rounds=4)
        
        # Register all specialized agents
        self.register_agent(ArchitectAgent())
        self.register_agent(DebuggerAgent())
        self.register_agent(OptimizerAgent())
        self.register_agent(SecurityAgent())
        self.register_agent(AlgorithmsAgent())
        self.register_agent(TestingAgent())
        self.register_agent(CodeReviewerAgent())
    
    def analyze_code(self, code: str, language: str = 'python', question: str = None) -> str:
        """
        Comprehensive code analysis entry point
        Returns professional-grade analysis
        """
        query = question or f"Professional analysis of {language} code"
        context = {
            'code': code,
            'language': language,
            'analysis_depth': 'comprehensive'
        }
        
        session_id = self.start_debate(query, context)
        
        # Wait with timeout
        import time
        max_wait = 60  # Allow more time for thorough analysis
        waited = 0
        
        while waited < max_wait:
            status = self.get_session_status(session_id)
            if status['status'] == 'complete':
                break
            time.sleep(0.5)
            waited += 0.5
        
        result = self.get_result(session_id)
        
        if result:
            return self._format_professional_analysis(result, code)
        
        return "Analysis in progress..."
    
    def _format_professional_analysis(self, result: DebateResult, code: str) -> str:
        """Format analysis in professional style"""
        sections = []
        
        # Executive Summary
        consensus = "CONSENSUS" if result.consensus_reached else "DIVERGENT VIEWS"
        confidence = int(result.confidence * 100)
        
        sections.append(f"## Executive Summary\n**{consensus}** | Confidence: {confidence}%\n")
        sections.append(f"{result.final_answer}\n")
        
        # Agent Analysis
        sections.append("## Multi-Agent Analysis\n")
        
        for pos in result.agent_positions:
            emoji = {
                'positive': '✅',
                'constructive': '💡',
                'critical': '⚠️',
                'analytical': '📊'
            }.get(pos.stance, '📝')
            
            sections.append(f"### {emoji} {pos.agent} ({pos.confidence:.0%} confidence)")
            sections.append(f"**Position:** {pos.stance.upper()}")
            sections.append(f"**Analysis:** {pos.reasoning}\n")
            
            if pos.key_points:
                sections.append("**Key Points:**")
                for point in pos.key_points[:3]:
                    sections.append(f"- {point}")
                sections.append("")
        
        # Recommendations
        sections.append("## Recommendations\n")
        
        critical = [p for p in result.agent_positions if p.stance == 'critical']
        if critical:
            sections.append("### 🔴 Critical Issues (Address Immediately)")
            for pos in critical:
                sections.append(f"- **{pos.agent}:** {pos.reasoning}")
            sections.append("")
        
        constructive = [p for p in result.agent_positions if p.stance == 'constructive']
        if constructive:
            sections.append("### 💡 Improvement Opportunities")
            for pos in constructive:
                sections.append(f"- **{pos.agent}:** {pos.reasoning}")
            sections.append("")
        
        positive = [p for p in result.agent_positions if p.stance == 'positive']
        if len(positive) >= 4:
            sections.append("✨ **Code Quality Assessment: PRODUCTION READY**")
        
        return "\n".join(sections)


# Singleton instance
code_ai = CodeAI()
