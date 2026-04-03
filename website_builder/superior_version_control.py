"""
Superior Version Control - Beyond Base44
AI-powered commit suggestions and branching
"""

import uuid
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ChangeType(Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    STYLE = "style"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"


@dataclass
class VersionCommit:
    commit_id: str
    message: str
    change_type: ChangeType
    files_changed: List[str]
    additions: int
    deletions: int
    ai_suggested: bool
    timestamp: datetime = field(default_factory=datetime.now)


class SuperiorVersionControl:
    """
    AI-powered version control with intelligent commit suggestions
    SURPASSES Base44's basic Git integration
    """
    
    def __init__(self):
        self.commits: Dict[str, VersionCommit] = {}
        self.branches: Dict[str, List[str]] = {}
        self.ai_commit_generator = AICommitGenerator()
        self.change_analyzer = ChangeAnalyzer()
    
    def analyze_changes(self, files_before: Dict[str, str], 
                       files_after: Dict[str, str]) -> Dict[str, Any]:
        """Analyze code changes with AI understanding"""
        
        # Calculate diffs
        changed_files = []
        additions = 0
        deletions = 0
        
        all_files = set(files_before.keys()) | set(files_after.keys())
        
        for filename in all_files:
            before = files_before.get(filename, '')
            after = files_after.get(filename, '')
            
            if before != after:
                changed_files.append(filename)
                # Simple line diff
                before_lines = before.split('\n')
                after_lines = after.split('\n')
                
                # Calculate additions/deletions
                if len(after_lines) > len(before_lines):
                    additions += len(after_lines) - len(before_lines)
                else:
                    deletions += len(before_lines) - len(after_lines)
        
        # AI analysis of changes
        change_analysis = self.change_analyzer.analyze(changed_files, files_after)
        
        return {
            'files_changed': changed_files,
            'additions': additions,
            'deletions': deletions,
            'change_type': change_analysis['change_type'],
            'impact_score': change_analysis['impact_score'],
            'breaking_changes': change_analysis['breaking_changes'],
            'suggested_reviewers': change_analysis['suggested_reviewers']
        }
    
    def suggest_commit(self, files_before: Dict[str, str], 
                      files_after: Dict[str, str]) -> Dict[str, Any]:
        """Generate AI commit suggestions"""
        
        # Analyze changes
        analysis = self.analyze_changes(files_before, files_after)
        
        # Generate commit message options
        suggestions = self.ai_commit_generator.generate(
            analysis['files_changed'],
            analysis['change_type'],
            analysis['additions'],
            analysis['deletions']
        )
        
        return {
            'suggested_messages': suggestions['messages'],
            'change_type': analysis['change_type'].value,
            'files_changed': analysis['files_changed'],
            'stats': {
                'additions': analysis['additions'],
                'deletions': analysis['deletions']
            },
            'breaking_changes': analysis['breaking_changes'],
            'confidence': suggestions['confidence'],
            'alternative_types': suggestions['alternative_types']
        }
    
    def create_commit(self, message: str, files: Dict[str, str],
                     change_type: ChangeType = ChangeType.FEATURE) -> VersionCommit:
        """Create a version commit"""
        commit_id = hashlib.sha256(f"{message}{datetime.now()}".encode()).hexdigest()[:12]
        
        # Calculate stats
        total_lines = sum(len(content.split('\n')) for content in files.values())
        
        commit = VersionCommit(
            commit_id=commit_id,
            message=message,
            change_type=change_type,
            files_changed=list(files.keys()),
            additions=total_lines,  # Simplified
            deletions=0,
            ai_suggested=False
        )
        
        self.commits[commit_id] = commit
        
        return commit
    
    def get_commit_history(self, branch: str = 'main', limit: int = 20) -> List[Dict]:
        """Get commit history with AI insights"""
        commits = list(self.commits.values())
        commits.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                'commit_id': c.commit_id,
                'message': c.message,
                'change_type': c.change_type.value,
                'files_changed': c.files_changed,
                'stats': f"+{c.additions}/-{c.deletions}",
                'ai_suggested': c.ai_suggested,
                'timestamp': c.timestamp.isoformat()
            }
            for c in commits[:limit]
        ]
    
    def suggest_branch_name(self, feature_description: str) -> List[str]:
        """Suggest branch names based on feature"""
        # Clean and normalize
        clean = feature_description.lower()
        clean = re.sub(r'[^\w\s]', '', clean)
        words = clean.split()[:5]
        
        suggestions = []
        
        # Type prefixes
        prefixes = ['feature', 'bugfix', 'hotfix', 'refactor', 'docs']
        
        for prefix in prefixes[:3]:
            # Short version
            short = f"{prefix}/{ '-'.join(words[:2]) }"
            suggestions.append(short[:30])
            
            # Detailed version
            detailed = f"{prefix}/{ '-'.join(words[:4]) }"
            suggestions.append(detailed[:50])
        
        return list(set(suggestions))
    
    def generate_changelog(self, since: Optional[datetime] = None) -> str:
        """Generate changelog from commits"""
        commits = list(self.commits.values())
        
        if since:
            commits = [c for c in commits if c.timestamp >= since]
        
        # Group by type
        by_type = {}
        for commit in commits:
            ct = commit.change_type.value
            if ct not in by_type:
                by_type[ct] = []
            by_type[ct].append(commit.message)
        
        # Generate markdown
        changelog = "# Changelog\n\n"
        
        for type_name in ['feature', 'bugfix', 'refactor', 'docs']:
            if type_name in by_type:
                changelog += f"## {type_name.capitalize()}s\n"
                for msg in by_type[type_name]:
                    changelog += f"- {msg}\n"
                changelog += "\n"
        
        return changelog


class AICommitGenerator:
    """AI-powered commit message generation"""
    
    def generate(self, files: List[str], change_type: ChangeType,
                additions: int, deletions: int) -> Dict[str, Any]:
        """Generate commit message suggestions"""
        
        # Analyze file patterns
        file_patterns = self._analyze_file_patterns(files)
        
        messages = []
        
        # Generate based on change type
        if change_type == ChangeType.FEATURE:
            messages.extend([
                f"Add {file_patterns['main_feature']}",
                f"Implement {file_patterns['main_feature']} functionality",
                f"Feature: {file_patterns['main_feature']}"
            ])
        elif change_type == ChangeType.BUGFIX:
            messages.extend([
                f"Fix {file_patterns['main_issue']}",
                f"Resolve issue with {file_patterns['main_issue']}",
                f"Bugfix: {file_patterns['main_issue']}"
            ])
        elif change_type == ChangeType.REFACTOR:
            messages.extend([
                f"Refactor {file_patterns['component']}",
                f"Improve {file_patterns['component']} structure",
                f"Optimize {file_patterns['component']}"
            ])
        
        # Add conventional commit format
        conventional = f"{change_type.value}: {messages[0].lower()}"
        messages.insert(0, conventional)
        
        return {
            'messages': messages[:4],
            'confidence': 0.85 if additions > 0 else 0.70,
            'alternative_types': [t.value for t in [ChangeType.REFACTOR, ChangeType.DOCS] if t != change_type][:2]
        }
    
    def _analyze_file_patterns(self, files: List[str]) -> Dict[str, str]:
        """Analyze file patterns for context"""
        # Extract component names
        components = []
        for f in files:
            parts = f.replace('/', '.').split('.')
            if len(parts) > 1:
                components.append(parts[-2])
        
        main_component = components[0] if components else 'feature'
        
        return {
            'main_feature': main_component.replace('_', ' '),
            'main_issue': f"{main_component} handling",
            'component': main_component,
            'file_types': list(set(f.split('.')[-1] for f in files if '.' in f))
        }


class ChangeAnalyzer:
    """Analyze code changes for impact and recommendations"""
    
    def analyze(self, changed_files: List[str], 
                new_files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze changes for impact"""
        
        # Determine change type
        change_type = self._detect_change_type(changed_files, new_files)
        
        # Calculate impact score
        impact_score = self._calculate_impact(changed_files, new_files)
        
        # Detect breaking changes
        breaking_changes = self._detect_breaking_changes(changed_files, new_files)
        
        # Suggest reviewers
        suggested_reviewers = self._suggest_reviewers(changed_files)
        
        return {
            'change_type': change_type,
            'impact_score': impact_score,
            'breaking_changes': breaking_changes,
            'suggested_reviewers': suggested_reviewers
        }
    
    def _detect_change_type(self, files: List[str], 
                           content: Dict[str, str]) -> ChangeType:
        """Detect type of change"""
        # Check for test files
        if any('test' in f or 'spec' in f for f in files):
            return ChangeType.TEST
        
        # Check for documentation
        if any(f.endswith('.md') or 'readme' in f.lower() for f in files):
            return ChangeType.DOCS
        
        # Check for style changes only
        if all(f.endswith(('.css', '.scss', '.less')) for f in files):
            return ChangeType.STYLE
        
        # Check content for patterns
        for f, code in content.items():
            if 'fix' in code.lower() or 'bug' in code.lower():
                return ChangeType.BUGFIX
            if 'refactor' in code.lower():
                return ChangeType.REFACTOR
        
        return ChangeType.FEATURE
    
    def _calculate_impact(self, files: List[str], 
                         content: Dict[str, str]) -> float:
        """Calculate impact score (0-1)"""
        score = 0.5
        
        # Core files have higher impact
        core_patterns = ['index', 'main', 'app', 'core', 'api']
        if any(pattern in ' '.join(files) for pattern in core_patterns):
            score += 0.2
        
        # Database changes are high impact
        if any('migration' in f or 'model' in f for f in files):
            score += 0.15
        
        # Many files = higher impact
        if len(files) > 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _detect_breaking_changes(self, files: List[str], 
                                 content: Dict[str, str]) -> List[str]:
        """Detect potential breaking changes"""
        breaking = []
        
        for f, code in content.items():
            # Check for removed exports
            if 'export' in code:
                # This would need previous state to compare
                pass
            
            # Check for database migrations
            if 'migration' in f:
                breaking.append(f"Database migration in {f}")
            
            # Check for API changes
            if 'api' in f or 'endpoint' in f.lower():
                if 'DELETE' in code or 'PATCH' in code:
                    breaking.append(f"API modification in {f}")
        
        return breaking
    
    def _suggest_reviewers(self, files: List[str]) -> List[str]:
        """Suggest code reviewers based on file history"""
        # Simplified - would use git history in production
        return ['senior-dev', 'tech-lead', 'domain-expert']


import re

# Initialize
superior_version_control = SuperiorVersionControl()
