"""
System Self-Modification Manager
Controlled system evolution with safety mechanisms
"""

from __future__ import annotations

import logging
import sqlite3
import json
import hashlib
import ast
import inspect
import sys
import os
import shutil
import threading
import uuid
from typing import Dict, Any, List, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import deque

log = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of system modifications"""
    CONFIG = "config"
    CODE_PATCH = "code_patch"
    PARAMETER = "parameter"
    THRESHOLD = "threshold"
    WEIGHT = "weight"
    AGENT_CONFIG = "agent_config"
    RULE = "rule"


class ChangeStatus(Enum):
    """Status of a change"""
    PENDING = "pending"
    VALIDATING = "validating"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class SystemChange:
    """Record of a system modification"""
    change_id: str
    change_type: ChangeType
    status: ChangeStatus
    target: str  # What was changed (file path, config key, etc.)
    old_value: Any
    new_value: Any
    reason: str
    admin_id: str
    admin_email: str
    timestamp: datetime
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    rollback_available: bool = True
    snapshot_id: Optional[str] = None
    impact_score: float = 0.0  # 0-1, higher = more risky
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'change_id': self.change_id,
            'change_type': self.change_type.value,
            'status': self.status.value,
            'target': self.target,
            'old_value': self._serialize_value(self.old_value),
            'new_value': self._serialize_value(self.new_value),
            'reason': self.reason,
            'admin_id': self.admin_id,
            'admin_email': self.admin_email,
            'timestamp': self.timestamp.isoformat(),
            'validated': self.validated,
            'validation_errors': self.validation_errors,
            'rollback_available': self.rollback_available,
            'snapshot_id': self.snapshot_id,
            'impact_score': self.impact_score,
            'dependencies': self.dependencies
        }
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize value for JSON storage"""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)


@dataclass
class CodeSnapshot:
    """Snapshot of code state before modification"""
    snapshot_id: str
    file_path: str
    original_content: str
    file_hash: str
    timestamp: datetime
    change_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'snapshot_id': self.snapshot_id,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'timestamp': self.timestamp.isoformat(),
            'change_id': self.change_id
        }


@dataclass
class LiveParameter:
    """A live-adjustable parameter"""
    name: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""
    category: str = "general"
    requires_restart: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    updated_by: str = ""
    change_count: int = 0
    
    def validate(self, new_value: Any) -> Tuple[bool, str]:
        """Validate new value for this parameter"""
        if self.allowed_values is not None:
            if new_value not in self.allowed_values:
                return False, f"Value must be one of: {self.allowed_values}"
        
        if isinstance(new_value, (int, float)):
            if self.min_value is not None and new_value < self.min_value:
                return False, f"Value must be >= {self.min_value}"
            if self.max_value is not None and new_value > self.max_value:
                return False, f"Value must be <= {self.max_value}"
        
        return True, ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'allowed_values': self.allowed_values,
            'description': self.description,
            'category': self.category,
            'requires_restart': self.requires_restart,
            'last_updated': self.last_updated.isoformat(),
            'updated_by': self.updated_by,
            'change_count': self.change_count
        }


class CodeValidator:
    """Validates code modifications before application"""
    
    # Patterns that could be dangerous
    DANGEROUS_PATTERNS = [
        'eval(', 'exec(', '__import__', 'os.system', 'subprocess',
        'open(', 'file(', 'write(', 'delete', 'remove', 'rmtree',
        'while True:', 'for():', 'recursive_call', 'infinite_loop'
    ]
    
    # Allowed modules for patching
    ALLOWED_MODULES = [
        'quant_ecosystem', 'AI -----', 'agents', 'services',
        'strategies', 'utils', 'config'
    ]
    
    # Forbidden file patterns
    FORBIDDEN_PATTERNS = [
        'test_', '_test', 'test.py', '.env', '.git', 
        '__pycache__', '.pyc', '.pyo', 'requirements',
        'production_server', 'backup', 'migration'
    ]
    
    def __init__(self):
        self._validation_cache: Dict[str, Tuple[bool, List[str]]] = {}
    
    def validate_code_change(self, file_path: str, 
                            old_content: str, 
                            new_content: str) -> Dict[str, Any]:
        """
        Comprehensive code change validation
        
        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'impact_score': float (0-1),
                'safety_checks': Dict[str, bool]
            }
        """
        errors = []
        warnings = []
        safety_checks = {}
        impact_score = 0.0
        
        # Check 1: File path validation
        path_valid, path_errors = self._validate_file_path(file_path)
        safety_checks['path_valid'] = path_valid
        if not path_valid:
            errors.extend(path_errors)
            return {'valid': False, 'errors': errors, 'warnings': warnings, 
                   'impact_score': 1.0, 'safety_checks': safety_checks}
        
        # Check 2: Syntax validation
        syntax_valid, syntax_error = self._validate_syntax(new_content)
        safety_checks['syntax_valid'] = syntax_valid
        if not syntax_valid:
            errors.append(f"Syntax error: {syntax_error}")
            impact_score += 0.5
        
        # Check 3: Dangerous pattern detection
        patterns_found = self._check_dangerous_patterns(new_content)
        safety_checks['no_dangerous_patterns'] = len(patterns_found) == 0
        if patterns_found:
            errors.extend([f"Dangerous pattern: {p}" for p in patterns_found])
            impact_score += 0.3 * len(patterns_found)
        
        # Check 4: AST structure validation
        ast_valid, ast_warnings = self._validate_ast(new_content)
        safety_checks['ast_valid'] = ast_valid
        warnings.extend(ast_warnings)
        if not ast_valid:
            impact_score += 0.2
        
        # Check 5: Change size analysis
        size_score = self._analyze_change_size(old_content, new_content)
        impact_score += size_score * 0.1
        
        # Check 6: API compatibility check
        api_valid, api_warnings = self._check_api_compatibility(old_content, new_content)
        safety_checks['api_compatible'] = api_valid
        warnings.extend(api_warnings)
        if not api_valid:
            impact_score += 0.15
        
        # Cap impact score at 1.0
        impact_score = min(1.0, impact_score)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'impact_score': impact_score,
            'safety_checks': safety_checks
        }
    
    def _validate_file_path(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate that file can be modified"""
        errors = []
        
        # Check forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in file_path:
                errors.append(f"File path contains forbidden pattern: {pattern}")
        
        # Check allowed modules
        in_allowed = any(module in file_path for module in self.ALLOWED_MODULES)
        if not in_allowed:
            errors.append(f"File not in allowed module paths")
        
        # Check file extension
        if not file_path.endswith('.py'):
            errors.append("Only Python files (.py) can be modified")
        
        return len(errors) == 0, errors
    
    def _validate_syntax(self, code: str) -> Tuple[bool, str]:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)
    
    def _check_dangerous_patterns(self, code: str) -> List[str]:
        """Check for dangerous code patterns"""
        found = []
        code_lower = code.lower()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in code_lower:
                found.append(pattern)
        
        return found
    
    def _validate_ast(self, code: str) -> Tuple[bool, List[str]]:
        """Validate AST structure"""
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            # Check for complex nested structures
            max_depth = 0
            for node in ast.walk(tree):
                depth = 0
                current = node
                while hasattr(current, 'parent'):
                    depth += 1
                    current = current.parent
                max_depth = max(max_depth, depth)
            
            if max_depth > 10:
                warnings.append(f"Deep nesting detected ({max_depth} levels) - may impact readability")
            
            # Count various node types
            import_count = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
            if import_count > 20:
                warnings.append(f"High import count ({import_count}) - consider consolidation")
            
            return True, warnings
            
        except Exception as e:
            return False, [f"AST analysis failed: {e}"]
    
    def _analyze_change_size(self, old_content: str, new_content: str) -> float:
        """Analyze the size of the change (0-1 scale)"""
        old_lines = len(old_content.split('\n'))
        new_lines = len(new_content.split('\n'))
        
        # Calculate line difference
        line_diff = abs(new_lines - old_lines)
        
        # Score based on percentage change
        if old_lines == 0:
            return 1.0 if new_lines > 0 else 0.0
        
        change_ratio = line_diff / old_lines
        return min(1.0, change_ratio)
    
    def _check_api_compatibility(self, old_content: str, 
                                  new_content: str) -> Tuple[bool, List[str]]:
        """Check if change maintains API compatibility"""
        warnings = []
        
        # Extract function/class signatures from old content
        old_signatures = self._extract_signatures(old_content)
        new_signatures = self._extract_signatures(new_content)
        
        # Check for removed functions/classes
        for name in old_signatures:
            if name not in new_signatures:
                warnings.append(f"API breaking: {name} was removed")
        
        # Check for signature changes
        for name, old_sig in old_signatures.items():
            if name in new_signatures:
                new_sig = new_signatures[name]
                if old_sig != new_sig:
                    warnings.append(f"API change: {name} signature modified")
        
        return len(warnings) == 0, warnings
    
    def _extract_signatures(self, code: str) -> Dict[str, str]:
        """Extract function/class signatures from code"""
        signatures = {}
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    signatures[node.name] = f"({', '.join(args)})"
                elif isinstance(node, ast.ClassDef):
                    signatures[node.name] = "(class)"
                    
        except:
            pass
        
        return signatures


class SelfModificationManager:
    """
    Manages controlled self-modification of the system
    with safety mechanisms, versioning, and rollback
    """
    
    def __init__(self, db_path: str = "system_modifications.db",
                 snapshot_dir: str = ".system_snapshots"):
        self.db_path = db_path
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(exist_ok=True)
        
        self._lock = threading.RLock()
        self._change_callbacks: List[Callable] = []
        self._live_parameters: Dict[str, LiveParameter] = {}
        self._validator = CodeValidator()
        
        self._init_database()
        self._load_live_parameters()
        
        log.info("SelfModificationManager initialized")
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # System changes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_changes (
                    change_id TEXT PRIMARY KEY,
                    change_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    admin_id TEXT,
                    admin_email TEXT,
                    timestamp TEXT NOT NULL,
                    validated INTEGER DEFAULT 0,
                    validation_errors TEXT,
                    rollback_available INTEGER DEFAULT 1,
                    snapshot_id TEXT,
                    impact_score REAL DEFAULT 0.0,
                    dependencies TEXT
                )
            ''')
            
            # Code snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    original_content TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    change_id TEXT NOT NULL
                )
            ''')
            
            # Live parameters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_parameters (
                    name TEXT PRIMARY KEY,
                    value TEXT,
                    min_value REAL,
                    max_value REAL,
                    allowed_values TEXT,
                    description TEXT,
                    category TEXT,
                    requires_restart INTEGER DEFAULT 0,
                    last_updated TEXT,
                    updated_by TEXT,
                    change_count INTEGER DEFAULT 0
                )
            ''')
            
            # Change log details
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS change_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    change_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL,
                    admin_id TEXT
                )
            ''')
            
            conn.commit()
            log.info("Self-modification database initialized")
    
    def _load_live_parameters(self):
        """Load live parameters from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM live_parameters')
            
            for row in cursor.fetchall():
                param = LiveParameter(
                    name=row[0],
                    value=self._deserialize_value(row[1]),
                    min_value=row[2],
                    max_value=row[3],
                    allowed_values=json.loads(row[4]) if row[4] else None,
                    description=row[5] or "",
                    category=row[6] or "general",
                    requires_restart=bool(row[7]),
                    last_updated=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    updated_by=row[9] or "",
                    change_count=row[10] or 0
                )
                self._live_parameters[param.name] = param
        
        log.info(f"Loaded {len(self._live_parameters)} live parameters")
    
    def _deserialize_value(self, value_str: str) -> Any:
        """Deserialize value from string"""
        if value_str is None:
            return None
        try:
            return json.loads(value_str)
        except:
            return value_str
    
    # ==================== LIVE PARAMETERS ====================
    
    def register_live_parameter(self, name: str, default_value: Any,
                                 min_value: Optional[float] = None,
                                 max_value: Optional[float] = None,
                                 allowed_values: Optional[List[Any]] = None,
                                 description: str = "",
                                 category: str = "general",
                                 requires_restart: bool = False) -> bool:
        """Register a new live-adjustable parameter"""
        with self._lock:
            if name in self._live_parameters:
                return False
            
            param = LiveParameter(
                name=name,
                value=default_value,
                min_value=min_value,
                max_value=max_value,
                allowed_values=allowed_values,
                description=description,
                category=category,
                requires_restart=requires_restart
            )
            
            self._live_parameters[name] = param
            self._save_live_parameter(param)
            
            log.info(f"Registered live parameter: {name}")
            return True
    
    def update_live_parameter(self, name: str, new_value: Any,
                              admin_id: str, admin_email: str,
                              reason: str) -> Dict[str, Any]:
        """
        Update a live parameter with full audit trail
        
        Returns:
            {
                'success': bool,
                'change_id': str | None,
                'error': str | None,
                'requires_restart': bool
            }
        """
        with self._lock:
            if name not in self._live_parameters:
                return {'success': False, 'error': f"Unknown parameter: {name}", 
                       'change_id': None, 'requires_restart': False}
            
            param = self._live_parameters[name]
            
            # Validate new value
            valid, error = param.validate(new_value)
            if not valid:
                return {'success': False, 'error': error, 
                       'change_id': None, 'requires_restart': False}
            
            # Create change record
            change_id = str(uuid.uuid4())
            change = SystemChange(
                change_id=change_id,
                change_type=ChangeType.PARAMETER,
                status=ChangeStatus.APPLIED,
                target=name,
                old_value=param.value,
                new_value=new_value,
                reason=reason,
                admin_id=admin_id,
                admin_email=admin_email,
                timestamp=datetime.now(),
                validated=True,
                impact_score=0.1  # Low impact for parameter changes
            )
            
            # Update parameter
            old_value = param.value
            param.value = new_value
            param.last_updated = datetime.now()
            param.updated_by = admin_email
            param.change_count += 1
            
            # Save to database
            self._save_live_parameter(param)
            self._record_change(change)
            self._log_change_detail(change_id, "PARAMETER_UPDATED",
                                   f"Changed {name} from {old_value} to {new_value}")
            
            # Trigger callbacks
            self._trigger_callbacks(change)
            
            log.info(f"Updated parameter {name}: {old_value} -> {new_value}")
            
            return {
                'success': True,
                'change_id': change_id,
                'error': None,
                'requires_restart': param.requires_restart
            }
    
    def get_live_parameter(self, name: str) -> Optional[Any]:
        """Get current value of a live parameter"""
        param = self._live_parameters.get(name)
        return param.value if param else None
    
    def get_all_live_parameters(self, category: Optional[str] = None) -> Dict[str, Dict]:
        """Get all live parameters, optionally filtered by category"""
        result = {}
        for name, param in self._live_parameters.items():
            if category is None or param.category == category:
                result[name] = param.to_dict()
        return result
    
    def _save_live_parameter(self, param: LiveParameter):
        """Save live parameter to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO live_parameters
                (name, value, min_value, max_value, allowed_values, description,
                 category, requires_restart, last_updated, updated_by, change_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                param.name,
                json.dumps(param.value),
                param.min_value,
                param.max_value,
                json.dumps(param.allowed_values) if param.allowed_values else None,
                param.description,
                param.category,
                1 if param.requires_restart else 0,
                param.last_updated.isoformat(),
                param.updated_by,
                param.change_count
            ))
            conn.commit()
    
    # ==================== CODE PATCHING ====================
    
    def propose_code_change(self, file_path: str, new_content: str,
                           admin_id: str, admin_email: str,
                           reason: str) -> Dict[str, Any]:
        """
        Propose a code change with full validation
        
        Returns:
            {
                'success': bool,
                'change_id': str | None,
                'validation': Dict,
                'error': str | None
            }
        """
        with self._lock:
            # Read current content
            full_path = self._resolve_path(file_path)
            if not full_path.exists():
                return {'success': False, 'change_id': None, 
                       'validation': None, 'error': f"File not found: {file_path}"}
            
            old_content = full_path.read_text()
            
            # Validate change
            validation = self._validator.validate_code_change(
                file_path, old_content, new_content
            )
            
            if not validation['valid']:
                return {
                    'success': False,
                    'change_id': None,
                    'validation': validation,
                    'error': f"Validation failed: {validation['errors']}"
                }
            
            # Create change record
            change_id = str(uuid.uuid4())
            change = SystemChange(
                change_id=change_id,
                change_type=ChangeType.CODE_PATCH,
                status=ChangeStatus.PENDING,
                target=file_path,
                old_value=old_content,
                new_value=new_content,
                reason=reason,
                admin_id=admin_id,
                admin_email=admin_email,
                timestamp=datetime.now(),
                validated=validation['valid'],
                validation_errors=validation.get('errors', []),
                impact_score=validation.get('impact_score', 0.5)
            )
            
            # Create snapshot
            snapshot_id = self._create_snapshot(file_path, old_content, change_id)
            change.snapshot_id = snapshot_id
            
            # Record change
            self._record_change(change)
            
            log.info(f"Proposed code change {change_id} for {file_path}")
            
            return {
                'success': True,
                'change_id': change_id,
                'validation': validation,
                'error': None
            }
    
    def apply_code_change(self, change_id: str) -> Dict[str, Any]:
        """
        Apply a previously validated code change
        
        Returns:
            {
                'success': bool,
                'error': str | None,
                'backup_path': str | None
            }
        """
        with self._lock:
            change = self._get_change(change_id)
            if not change:
                return {'success': False, 'error': "Change not found", 'backup_path': None}
            
            if change.status != ChangeStatus.PENDING:
                return {'success': False, 
                       'error': f"Change is {change.status.value}, not pending",
                       'backup_path': None}
            
            if not change.validated:
                return {'success': False, 'error': "Change not validated", 'backup_path': None}
            
            try:
                # Write new content
                full_path = self._resolve_path(change.target)
                
                # Create backup
                backup_path = self._create_backup(change.target)
                
                # Apply change
                full_path.write_text(change.new_value)
                
                # Update change status
                change.status = ChangeStatus.APPLIED
                self._update_change(change)
                
                self._log_change_detail(change_id, "CODE_PATCH_APPLIED",
                                       f"Applied patch to {change.target}")
                
                # Trigger callbacks
                self._trigger_callbacks(change)
                
                log.info(f"Applied code change {change_id} to {change.target}")
                
                return {'success': True, 'error': None, 'backup_path': backup_path}
                
            except Exception as e:
                change.status = ChangeStatus.FAILED
                self._update_change(change)
                
                log.error(f"Failed to apply code change {change_id}: {e}")
                return {'success': False, 'error': str(e), 'backup_path': None}
    
    def rollback_change(self, change_id: str) -> Dict[str, Any]:
        """
        Rollback a change to its previous state
        
        Returns:
            {
                'success': bool,
                'error': str | None
            }
        """
        with self._lock:
            change = self._get_change(change_id)
            if not change:
                return {'success': False, 'error': "Change not found"}
            
            if not change.rollback_available:
                return {'success': False, 'error': "Rollback not available for this change"}
            
            if change.change_type == ChangeType.CODE_PATCH:
                return self._rollback_code_change(change)
            elif change.change_type == ChangeType.PARAMETER:
                return self._rollback_parameter_change(change)
            else:
                return {'success': False, 'error': f"Rollback not supported for {change.change_type.value}"}
    
    def _rollback_code_change(self, change: SystemChange) -> Dict[str, Any]:
        """Rollback a code patch"""
        try:
            if change.snapshot_id:
                # Restore from snapshot
                snapshot = self._get_snapshot(change.snapshot_id)
                if snapshot:
                    full_path = self._resolve_path(change.target)
                    full_path.write_text(snapshot.original_content)
                    
                    change.status = ChangeStatus.ROLLED_BACK
                    self._update_change(change)
                    
                    self._log_change_detail(change.change_id, "CODE_PATCH_ROLLED_BACK",
                                           f"Rolled back {change.target}")
                    
                    log.info(f"Rolled back code change {change.change_id}")
                    return {'success': True, 'error': None}
            
            return {'success': False, 'error': "No snapshot available for rollback"}
            
        except Exception as e:
            log.error(f"Failed to rollback code change: {e}")
            return {'success': False, 'error': str(e)}
    
    def _rollback_parameter_change(self, change: SystemChange) -> Dict[str, Any]:
        """Rollback a parameter change"""
        try:
            if change.target in self._live_parameters:
                param = self._live_parameters[change.target]
                param.value = change.old_value
                param.last_updated = datetime.now()
                param.change_count += 1
                
                self._save_live_parameter(param)
                
                change.status = ChangeStatus.ROLLED_BACK
                self._update_change(change)
                
                self._log_change_detail(change.change_id, "PARAMETER_ROLLED_BACK",
                                       f"Rolled back {change.target} to {change.old_value}")
                
                log.info(f"Rolled back parameter change {change.change_id}")
                return {'success': True, 'error': None}
            
            return {'success': False, 'error': f"Parameter {change.target} not found"}
            
        except Exception as e:
            log.error(f"Failed to rollback parameter: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==================== CHANGE TRACKING ====================
    
    def get_change_history(self, limit: int = 100,
                        change_type: Optional[ChangeType] = None,
                        status: Optional[ChangeStatus] = None) -> List[Dict]:
        """Get change history with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM system_changes WHERE 1=1'
            params = []
            
            if change_type:
                query += ' AND change_type = ?'
                params.append(change_type.value)
            
            if status:
                query += ' AND status = ?'
                params.append(status.value)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            changes = []
            for row in cursor.fetchall():
                change = SystemChange(
                    change_id=row[0],
                    change_type=ChangeType(row[1]),
                    status=ChangeStatus(row[2]),
                    target=row[3],
                    old_value=self._deserialize_value(row[4]),
                    new_value=self._deserialize_value(row[5]),
                    reason=row[6],
                    admin_id=row[7],
                    admin_email=row[8],
                    timestamp=datetime.fromisoformat(row[9]),
                    validated=bool(row[10]),
                    validation_errors=json.loads(row[11]) if row[11] else [],
                    rollback_available=bool(row[12]),
                    snapshot_id=row[13],
                    impact_score=row[14] or 0.0,
                    dependencies=json.loads(row[15]) if row[15] else []
                )
                changes.append(change.to_dict())
            
            return changes
    
    def get_change_details(self, change_id: str) -> Optional[Dict]:
        """Get full details of a specific change including logs"""
        change = self._get_change(change_id)
        if not change:
            return None
        
        # Get log details
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT action, details, timestamp, admin_id
                FROM change_log WHERE change_id = ?
                ORDER BY timestamp DESC
            ''', (change_id,))
            
            logs = [
                {
                    'action': row[0],
                    'details': row[1],
                    'timestamp': row[2],
                    'admin_id': row[3]
                }
                for row in cursor.fetchall()
            ]
        
        result = change.to_dict()
        result['logs'] = logs
        return result
    
    # ==================== UTILITY METHODS ====================
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve relative path to absolute"""
        # Handle paths relative to project root
        if file_path.startswith('quant_ecosystem/') or file_path.startswith('AI -----/'):
            return Path(file_path)
        return Path(file_path)
    
    def _create_snapshot(self, file_path: str, content: str, 
                        change_id: str) -> str:
        """Create a snapshot of original code"""
        snapshot_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO code_snapshots
                (snapshot_id, file_path, original_content, file_hash, timestamp, change_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                file_path,
                content,
                hashlib.sha256(content.encode()).hexdigest(),
                datetime.now().isoformat(),
                change_id
            ))
            conn.commit()
        
        return snapshot_id
    
    def _get_snapshot(self, snapshot_id: str) -> Optional[CodeSnapshot]:
        """Retrieve a snapshot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM code_snapshots WHERE snapshot_id = ?', (snapshot_id,))
            
            row = cursor.fetchone()
            if row:
                return CodeSnapshot(
                    snapshot_id=row[0],
                    file_path=row[1],
                    original_content=row[2],
                    file_hash=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    change_id=row[5]
                )
        return None
    
    def _create_backup(self, file_path: str) -> str:
        """Create a file backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.replace('/', '_')}_{timestamp}.bak"
        backup_path = self.snapshot_dir / backup_name
        
        full_path = self._resolve_path(file_path)
        if full_path.exists():
            shutil.copy2(full_path, backup_path)
        
        return str(backup_path)
    
    def _record_change(self, change: SystemChange):
        """Record a change to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_changes
                (change_id, change_type, status, target, old_value, new_value,
                 reason, admin_id, admin_email, timestamp, validated,
                 validation_errors, rollback_available, snapshot_id, impact_score, dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                change.change_id,
                change.change_type.value,
                change.status.value,
                change.target,
                json.dumps(change.old_value) if change.old_value is not None else None,
                json.dumps(change.new_value) if change.new_value is not None else None,
                change.reason,
                change.admin_id,
                change.admin_email,
                change.timestamp.isoformat(),
                1 if change.validated else 0,
                json.dumps(change.validation_errors),
                1 if change.rollback_available else 0,
                change.snapshot_id,
                change.impact_score,
                json.dumps(change.dependencies)
            ))
            conn.commit()
    
    def _get_change(self, change_id: str) -> Optional[SystemChange]:
        """Get a change by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM system_changes WHERE change_id = ?', (change_id,))
            
            row = cursor.fetchone()
            if row:
                return SystemChange(
                    change_id=row[0],
                    change_type=ChangeType(row[1]),
                    status=ChangeStatus(row[2]),
                    target=row[3],
                    old_value=self._deserialize_value(row[4]),
                    new_value=self._deserialize_value(row[5]),
                    reason=row[6],
                    admin_id=row[7],
                    admin_email=row[8],
                    timestamp=datetime.fromisoformat(row[9]),
                    validated=bool(row[10]),
                    validation_errors=json.loads(row[11]) if row[11] else [],
                    rollback_available=bool(row[12]),
                    snapshot_id=row[13],
                    impact_score=row[14] or 0.0,
                    dependencies=json.loads(row[15]) if row[15] else []
                )
        return None
    
    def _update_change(self, change: SystemChange):
        """Update change status in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE system_changes
                SET status = ?, rollback_available = ?
                WHERE change_id = ?
            ''', (change.status.value, 1 if change.rollback_available else 0, change.change_id))
            conn.commit()
    
    def _log_change_detail(self, change_id: str, action: str, 
                          details: str, admin_id: str = None):
        """Log a detail about a change"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO change_log (change_id, action, details, timestamp, admin_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (change_id, action, details, datetime.now().isoformat(), admin_id))
            conn.commit()
    
    def _trigger_callbacks(self, change: SystemChange):
        """Trigger registered callbacks"""
        for callback in self._change_callbacks:
            try:
                callback(change)
            except Exception as e:
                log.error(f"Change callback error: {e}")
    
    def register_change_callback(self, callback: Callable):
        """Register a callback for change events"""
        self._change_callbacks.append(callback)
    
    def unregister_change_callback(self, callback: Callable):
        """Unregister a change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)


# Global instance
modification_manager = SelfModificationManager()
