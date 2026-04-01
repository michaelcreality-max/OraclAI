"""
OraclAI Multi-Domain AI System
Code Analysis Domain - Multi-Agent System
Agents: Architect, Debugger, Optimizer, Security, Reviewer
"""

from typing import Dict, List
from multi_domain.base_system import BaseAgent, MultiAgentSystem, AgentPosition

class ArchitectAgent(BaseAgent):
    """Focuses on code structure, patterns, and design"""
    
    def __init__(self):
        super().__init__(
            name="Architect",
            role="Code Structure & Design Expert",
            expertise=['design patterns', 'architecture', 'scalability', 'modularity', 'clean code']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        language = context.get('language', 'unknown')
        
        # Analysis logic
        concerns = []
        positives = []
        
        if 'class' in query.lower() or 'function' in query.lower():
            positives.append("Object-oriented structure detected")
        
        if len(code.split('\n')) > 50:
            concerns.append("Consider breaking into smaller modules")
        
        if 'global' in code.lower():
            concerns.append("Global variables may impact testability")
        
        if not concerns:
            stance = 'positive'
            confidence = 0.85
            reasoning = "Clean architectural approach with good separation of concerns."
        elif len(concerns) < 3:
            stance = 'constructive'
            confidence = 0.70
            reasoning = f"Good foundation with room for improvement: {'; '.join(concerns)}"
        else:
            stance = 'critical'
            confidence = 0.60
            reasoning = f"Significant architectural concerns: {'; '.join(concerns)}"
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=concerns if concerns else positives
        )


class DebuggerAgent(BaseAgent):
    """Focuses on bugs, errors, and runtime issues"""
    
    def __init__(self):
        super().__init__(
            name="Debugger",
            role="Bug Detection & Error Analysis",
            expertise=['debugging', 'error handling', 'runtime analysis', 'stack traces']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        error_msg = context.get('error', '')
        
        issues = []
        fixes = []
        
        # Common bug patterns
        if 'except' in code and 'pass' in code:
            issues.append("Bare except/pass - masks errors")
        
        if '==' in code and '=' in code:
            if code.count('==') < code.count('='):
                issues.append("Possible assignment vs comparison confusion")
        
        if 'None' in code and 'is not' not in code and '==' in code:
            issues.append("Use 'is'/'is not' for None checks")
        
        if error_msg:
            issues.append(f"Runtime error detected: {error_msg[:100]}")
        
        if 'print(' in code and 'logging' not in code:
            fixes.append("Consider using logging instead of print")
        
        if issues:
            stance = 'critical'
            confidence = 0.80 if error_msg else 0.65
            reasoning = f"Issues found: {'; '.join(issues[:3])}"
        elif fixes:
            stance = 'constructive'
            confidence = 0.75
            reasoning = f"No critical bugs. Suggestions: {'; '.join(fixes)}"
        else:
            stance = 'positive'
            confidence = 0.85
            reasoning = "No obvious bugs detected. Error handling looks adequate."
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=issues if issues else ["Clean error handling"]
        )


class OptimizerAgent(BaseAgent):
    """Focuses on performance and efficiency"""
    
    def __init__(self):
        super().__init__(
            name="Optimizer",
            role="Performance & Efficiency Expert",
            expertise=['big O', 'memory management', 'caching', 'parallelization', 'profiling']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        
        optimizations = []
        concerns = []
        
        # Performance patterns
        if 'for' in code and 'for' in code[code.find('for')+1:]:
            concerns.append("Nested loops - consider O(n²) complexity")
        
        if 'list.append' in code and 'in loop' in str(context):
            optimizations.append("Consider list comprehension for speed")
        
        if 'open(' in code and 'with' not in code:
            concerns.append("File operations should use context managers")
        
        if 'import' in code:
            imports = [line for line in code.split('\n') if 'import' in line]
            if len(imports) > 10:
                concerns.append("Many imports - consider lazy loading")
        
        if not concerns and not optimizations:
            stance = 'positive'
            confidence = 0.80
            reasoning = "Performance characteristics appear reasonable for typical use cases."
        elif optimizations and not concerns:
            stance = 'constructive'
            confidence = 0.75
            reasoning = f"Minor optimizations possible: {'; '.join(optimizations[:2])}"
        else:
            stance = 'analytical'
            confidence = 0.70
            reasoning = f"Performance concerns: {'; '.join(concerns[:3])}"
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=optimizations if optimizations else concerns
        )


class SecurityAgent(BaseAgent):
    """Focuses on security vulnerabilities"""
    
    def __init__(self):
        super().__init__(
            name="Security",
            role="Security & Vulnerability Expert",
            expertise=['vulnerability scanning', 'injection prevention', 'auth', 'encryption']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        
        risks = []
        checks = []
        
        # Security patterns
        if 'input(' in code or 'raw_input' in code:
            risks.append("User input not sanitized - injection risk")
        
        if 'password' in code.lower() or 'secret' in code.lower():
            if 'hash' not in code.lower() and 'encrypt' not in code.lower():
                risks.append("Credentials should be hashed/encrypted")
        
        if 'eval(' in code or 'exec(' in code:
            risks.append("Dangerous eval/exec usage - code injection risk")
        
        if 'http://' in code and 'https://' not in code:
            risks.append("Insecure HTTP without HTTPS fallback")
        
        if 'pickle' in code and 'loads' in code:
            risks.append("Pickle deserialization - arbitrary code execution risk")
        
        if risks:
            stance = 'critical'
            confidence = 0.85
            reasoning = f"⚠️ Security risks detected: {'; '.join(risks[:3])}"
        else:
            stance = 'positive'
            confidence = 0.80
            reasoning = "✓ No obvious security vulnerabilities detected."
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=risks if risks else ["Security checks passed"]
        )


class CodeReviewerAgent(BaseAgent):
    """General code review and best practices"""
    
    def __init__(self):
        super().__init__(
            name="Reviewer",
            role="Code Review & Best Practices",
            expertise=['code review', 'documentation', 'testing', 'style guides']
        )
    
    def analyze(self, query: str, context: Dict) -> AgentPosition:
        code = context.get('code', '')
        
        suggestions = []
        
        # Code quality
        if '"""' not in code and "'''" not in code:
            suggestions.append("Add docstrings for functions/classes")
        
        if 'TODO' in code or 'FIXME' in code:
            suggestions.append("Address TODO/FIXME comments before commit")
        
        if len(code.split('\n')) > 100:
            if 'test' not in query.lower():
                suggestions.append("Consider adding unit tests")
        
        if 'type' not in code and 'def ' in code:
            suggestions.append("Consider type hints for better maintainability")
        
        if suggestions:
            stance = 'constructive'
            confidence = 0.75
            reasoning = f"Review suggestions: {'; '.join(suggestions[:3])}"
        else:
            stance = 'positive'
            confidence = 0.85
            reasoning = "✓ Code follows best practices. Well documented and structured."
        
        return AgentPosition(
            agent_name=self.name,
            stance=stance,
            confidence=confidence,
            reasoning=reasoning,
            key_points=suggestions if suggestions else ["Code quality good"]
        )


class CodeAI(MultiAgentSystem):
    """Complete Code Analysis Multi-Agent System"""
    
    def __init__(self):
        super().__init__(domain_name='Code', max_rounds=3)
        
        # Register all code agents
        self.register_agent(ArchitectAgent())
        self.register_agent(DebuggerAgent())
        self.register_agent(OptimizerAgent())
        self.register_agent(SecurityAgent())
        self.register_agent(CodeReviewerAgent())
    
    def analyze_code(self, code: str, language: str = 'python', question: str = None) -> str:
        """Quick analysis entry point"""
        query = question or f"Analyze this {language} code"
        context = {'code': code, 'language': language}
        
        session_id = self.start_debate(query, context)
        
        # Wait for completion (with timeout)
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


# Singleton instance
code_ai = CodeAI()
