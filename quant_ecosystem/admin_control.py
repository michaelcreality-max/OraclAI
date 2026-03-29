"""
Admin Control System
Full admin authentication, system control, and monitoring.
"""

import hashlib
import json
import logging
import secrets
import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from functools import wraps

log = logging.getLogger(__name__)


@dataclass
class AdminSession:
    """Admin session record"""
    session_id: str
    admin_id: str
    email: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    requires_password_change: bool = False


@dataclass
class SystemConfig:
    """Live system configuration"""
    # Edge/Filter thresholds
    edge_threshold: float = 65.0
    min_confidence: float = 0.65
    max_edge_threshold: float = 85.0
    
    # Risk thresholds
    max_position_risk_percent: float = 2.0
    max_portfolio_risk_percent: float = 6.0
    max_sector_exposure: float = 25.0
    max_single_position: float = 15.0
    
    # Agent settings
    agent_timeout_seconds: int = 60
    debate_rounds: int = 3
    min_agent_confidence: float = 0.6
    
    # System settings
    auto_update_interval: int = 300
    log_level: str = "INFO"
    max_concurrent_debates: int = 10
    
    # Mode settings
    require_validation_for_execution: bool = True
    auto_fallback_on_anomaly: bool = True
    anomaly_threshold: float = 0.7
    
    updated_at: datetime = None
    updated_by: str = ""
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


class AdminControlSystem:
    """
    Complete admin control system with authentication, config management,
    system control, and monitoring.
    """
    
    # Default admin credentials (dev only)
    DEFAULT_ADMIN_EMAIL = "michael.creality@gmail.com"
    DEFAULT_ADMIN_PASSWORD = "123456"
    
    def __init__(self, db_path: str = "admin_control.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self.config_lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = {}
        self._init_database()
        self._load_config()
        self._create_default_admin()
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Combine password and salt, hash multiple times for security
        hashed = password + salt
        for _ in range(100000):  # 100k iterations
            hashed = hashlib.sha256(hashed.encode()).hexdigest()
        
        return hashed, salt
    
    def _verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        computed, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed, hashed)
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Admin accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_accounts (
                    admin_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1,
                    requires_password_change INTEGER DEFAULT 1,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TEXT
                )
            ''')
            
            # Admin sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    session_id TEXT PRIMARY KEY,
                    admin_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    requires_password_change INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # System configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    config_key TEXT PRIMARY KEY,
                    config_value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    updated_by TEXT NOT NULL
                )
            ''')
            
            # System audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    admin_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT
                )
            ''')
            
            # Agent status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_status (
                    agent_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    is_enabled INTEGER DEFAULT 1,
                    last_active TEXT,
                    error_count INTEGER DEFAULT 0,
                    avg_response_time REAL,
                    success_rate REAL DEFAULT 100.0
                )
            ''')
            
            # System metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    active_debates INTEGER,
                    active_sessions INTEGER,
                    avg_response_time REAL,
                    error_rate REAL
                )
            ''')
            
            conn.commit()
            log.info("Admin control database initialized")
    
    def _create_default_admin(self):
        """Create default admin account if none exists"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if any admin exists
                cursor.execute('SELECT COUNT(*) FROM admin_accounts')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    # Create default admin
                    admin_id = f"admin_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    password_hash, salt = self._hash_password(self.DEFAULT_ADMIN_PASSWORD)
                    
                    cursor.execute('''
                        INSERT INTO admin_accounts
                        (admin_id, email, password_hash, salt, created_at, requires_password_change)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        admin_id,
                        self.DEFAULT_ADMIN_EMAIL,
                        password_hash,
                        salt,
                        datetime.now().isoformat(),
                        1  # Force password change on first login
                    ))
                    
                    conn.commit()
                    log.warning(f"⚠️  Default admin created: {self.DEFAULT_ADMIN_EMAIL}")
                    log.warning("⚠️  IMPORTANT: Change password on first login!")
    
    def _load_config(self):
        """Load system configuration from database"""
        with self.config_lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT config_key, config_value FROM system_config')
                
                rows = cursor.fetchall()
                if not rows:
                    # Initialize with defaults
                    self._save_config(SystemConfig())
                    self._config = SystemConfig()
                else:
                    config_dict = {row[0]: row[1] for row in rows}
                    self._config = self._dict_to_config(config_dict)
    
    def _save_config(self, config: SystemConfig):
        """Save configuration to database"""
        config_dict = asdict(config)
        config_dict['updated_at'] = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for key, value in config_dict.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO system_config (config_key, config_value, updated_at, updated_by)
                    VALUES (?, ?, ?, ?)
                ''', (key, str(value), config_dict['updated_at'], config_dict.get('updated_by', '')))
            
            conn.commit()
    
    def _dict_to_config(self, data: Dict) -> SystemConfig:
        """Convert dict to SystemConfig"""
        # Parse values appropriately
        def parse_value(key, val):
            if key in ['updated_at']:
                return datetime.fromisoformat(val) if val else None
            if key in ['requires_validation_for_execution', 'auto_fallback_on_anomaly']:
                return val.lower() == 'true' if isinstance(val, str) else bool(val)
            try:
                return float(val)
            except:
                return val
        
        parsed = {k: parse_value(k, v) for k, v in data.items()}
        return SystemConfig(**parsed)
    
    def _log_audit(self, admin_id: Optional[str], action: str, details: str = "", ip_address: str = ""):
        """Log admin action to audit log"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_audit_log (timestamp, admin_id, action, details, ip_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), admin_id, action, details, ip_address))
            conn.commit()
    
    # ==================== AUTHENTICATION ====================
    
    def authenticate(self, email: str, password: str, 
                    ip_address: str = "", user_agent: str = "") -> Dict[str, Any]:
        """
        Authenticate admin and create session.
        
        Returns:
            {
                'success': bool,
                'token': str | None,
                'requires_password_change': bool,
                'message': str
            }
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get admin record
                cursor.execute('''
                    SELECT admin_id, password_hash, salt, is_active, 
                           requires_password_change, locked_until, failed_login_attempts
                    FROM admin_accounts
                    WHERE email = ?
                ''', (email,))
                
                row = cursor.fetchone()
                if not row:
                    self._log_audit(None, "LOGIN_FAILED", f"Invalid email: {email}", ip_address)
                    return {'success': False, 'token': None, 'requires_password_change': False, 'message': 'Invalid credentials'}
                
                admin_id, password_hash, salt, is_active, requires_change, locked_until, failed_attempts = row
                
                # Check if account is active
                if not is_active:
                    return {'success': False, 'token': None, 'requires_password_change': False, 'message': 'Account deactivated'}
                
                # Check if locked
                if locked_until:
                    locked_time = datetime.fromisoformat(locked_until)
                    if locked_time > datetime.now():
                        return {'success': False, 'token': None, 'requires_password_change': False, 'message': f'Account locked until {locked_until}'}
                
                # Verify password
                if not self._verify_password(password, password_hash, salt):
                    # Increment failed attempts
                    failed_attempts = (failed_attempts or 0) + 1
                    
                    if failed_attempts >= 5:
                        # Lock account for 30 minutes
                        locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                        cursor.execute('''
                            UPDATE admin_accounts
                            SET failed_login_attempts = ?, locked_until = ?
                            WHERE admin_id = ?
                        ''', (failed_attempts, locked_until, admin_id))
                        conn.commit()
                        
                        self._log_audit(admin_id, "ACCOUNT_LOCKED", f"Failed attempts: {failed_attempts}", ip_address)
                        return {'success': False, 'token': None, 'requires_password_change': False, 'message': 'Account locked for 30 minutes due to failed attempts'}
                    else:
                        cursor.execute('''
                            UPDATE admin_accounts
                            SET failed_login_attempts = ?
                            WHERE admin_id = ?
                        ''', (failed_attempts, admin_id))
                        conn.commit()
                    
                    self._log_audit(admin_id, "LOGIN_FAILED", f"Invalid password (attempt {failed_attempts})", ip_address)
                    return {'success': False, 'token': None, 'requires_password_change': False, 'message': 'Invalid credentials'}
                
                # Password correct - reset failed attempts
                cursor.execute('''
                    UPDATE admin_accounts
                    SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                    WHERE admin_id = ?
                ''', (datetime.now().isoformat(), admin_id))
                
                # Create session
                session_id = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=8)  # 8 hour sessions
                
                cursor.execute('''
                    INSERT INTO admin_sessions
                    (session_id, admin_id, email, created_at, expires_at, ip_address, user_agent, requires_password_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, admin_id, email, datetime.now().isoformat(),
                    expires_at.isoformat(), ip_address, user_agent, requires_change
                ))
                
                conn.commit()
                
                self._log_audit(admin_id, "LOGIN_SUCCESS", f"Session: {session_id[:16]}...", ip_address)
                
                return {
                    'success': True,
                    'token': session_id,
                    'requires_password_change': bool(requires_change),
                    'message': 'Authentication successful'
                }
    
    def change_password(self, token: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change admin password"""
        # Validate session
        session = self._get_session(token)
        if not session:
            return {'success': False, 'message': 'Invalid or expired session'}
        
        # Validate new password
        if len(new_password) < 8:
            return {'success': False, 'message': 'Password must be at least 8 characters'}
        
        if not any(c.isupper() for c in new_password):
            return {'success': False, 'message': 'Password must contain uppercase letter'}
        
        if not any(c.islower() for c in new_password):
            return {'success': False, 'message': 'Password must contain lowercase letter'}
        
        if not any(c.isdigit() for c in new_password):
            return {'success': False, 'message': 'Password must contain digit'}
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verify old password
                cursor.execute('SELECT password_hash, salt FROM admin_accounts WHERE admin_id = ?', (session.admin_id,))
                row = cursor.fetchone()
                if not row or not self._verify_password(old_password, row[0], row[1]):
                    return {'success': False, 'message': 'Current password is incorrect'}
                
                # Hash new password
                new_hash, new_salt = self._hash_password(new_password)
                
                # Update password
                cursor.execute('''
                    UPDATE admin_accounts
                    SET password_hash = ?, salt = ?, requires_password_change = 0
                    WHERE admin_id = ?
                ''', (new_hash, new_salt, session.admin_id))
                
                # Update session
                cursor.execute('''
                    UPDATE admin_sessions
                    SET requires_password_change = 0
                    WHERE session_id = ?
                ''', (token,))
                
                conn.commit()
                
                self._log_audit(session.admin_id, "PASSWORD_CHANGED", "Password successfully changed")
                
                return {'success': True, 'message': 'Password changed successfully'}
    
    def change_password_by_email(self, email: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change admin password by email (for JWT-based auth)"""
        # Validate new password
        if len(new_password) < 8:
            return {'success': False, 'message': 'Password must be at least 8 characters'}
        
        if not any(c.isupper() for c in new_password):
            return {'success': False, 'message': 'Password must contain uppercase letter'}
        
        if not any(c.islower() for c in new_password):
            return {'success': False, 'message': 'Password must contain lowercase letter'}
        
        if not any(c.isdigit() for c in new_password):
            return {'success': False, 'message': 'Password must contain digit'}
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get admin by email
                cursor.execute('''
                    SELECT admin_id, password_hash, salt FROM admin_accounts 
                    WHERE email = ? AND is_active = 1
                ''', (email,))
                row = cursor.fetchone()
                
                if not row:
                    return {'success': False, 'message': 'Admin not found'}
                
                admin_id, password_hash, salt = row
                
                # Verify old password
                if not self._verify_password(old_password, password_hash, salt):
                    return {'success': False, 'message': 'Current password is incorrect'}
                
                # Hash new password
                new_hash, new_salt = self._hash_password(new_password)
                
                # Update password
                cursor.execute('''
                    UPDATE admin_accounts
                    SET password_hash = ?, salt = ?, requires_password_change = 0
                    WHERE admin_id = ?
                ''', (new_hash, new_salt, admin_id))
                
                conn.commit()
                
                self._log_audit(admin_id, "PASSWORD_CHANGED", "Password successfully changed via JWT auth")
                
                return {'success': True, 'message': 'Password changed successfully'}
    
    def _get_session(self, token: str) -> Optional[AdminSession]:
        """Get valid session by token"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, admin_id, email, created_at, expires_at, 
                       ip_address, user_agent, requires_password_change
                FROM admin_sessions
                WHERE session_id = ? AND is_active = 1
            ''', (token,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            session = AdminSession(
                session_id=row[0],
                admin_id=row[1],
                email=row[2],
                created_at=datetime.fromisoformat(row[3]),
                expires_at=datetime.fromisoformat(row[4]),
                ip_address=row[5],
                user_agent=row[6],
                requires_password_change=bool(row[7])
            )
            
            # Check expiration
            if session.expires_at < datetime.now():
                cursor.execute('UPDATE admin_sessions SET is_active = 0 WHERE session_id = ?', (token,))
                conn.commit()
                return None
            
            return session
    
    def validate_session(self, token: str) -> bool:
        """Validate if session is active"""
        return self._get_session(token) is not None
    
    def logout(self, token: str) -> bool:
        """Invalidate session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE admin_sessions SET is_active = 0 WHERE session_id = ?', (token,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_session_info(self, token: str) -> Optional[Dict]:
        """Get session information"""
        session = self._get_session(token)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'admin_id': session.admin_id,
            'email': session.email,
            'created_at': session.created_at.isoformat(),
            'expires_at': session.expires_at.isoformat(),
            'requires_password_change': session.requires_password_change
        }
    
    # ==================== SYSTEM CONFIGURATION ====================
    
    def get_config(self) -> Dict[str, Any]:
        """Get current system configuration"""
        with self.config_lock:
            return asdict(self._config)
    
    def update_config(self, token: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update system configuration.
        Validates all inputs before applying.
        """
        # Validate session
        session = self._get_session(token)
        if not session:
            return {'success': False, 'message': 'Invalid or expired session'}
        
        with self.config_lock:
            config_dict = asdict(self._config)
            
            # Validate and apply updates
            validated_updates = {}
            errors = []
            
            for key, value in updates.items():
                if key not in config_dict:
                    errors.append(f"Unknown config key: {key}")
                    continue
                
                # Validate specific fields
                validation_result = self._validate_config_value(key, value)
                if validation_result['valid']:
                    validated_updates[key] = validation_result['value']
                else:
                    errors.append(f"{key}: {validation_result['error']}")
            
            if errors:
                return {'success': False, 'message': 'Validation failed', 'errors': errors}
            
            # Apply updates
            config_dict.update(validated_updates)
            config_dict['updated_by'] = session.email
            config_dict['updated_at'] = datetime.now()
            
            # Save to database
            self._config = self._dict_to_config(config_dict)
            self._save_config(self._config)
            
            # Log change
            self._log_audit(
                session.admin_id,
                "CONFIG_UPDATED",
                f"Updated: {', '.join(validated_updates.keys())}"
            )
            
            # Trigger callbacks
            for key in validated_updates:
                self._trigger_callbacks(key, validated_updates[key])
            
            return {
                'success': True,
                'message': 'Configuration updated',
                'updated_keys': list(validated_updates.keys()),
                'config': asdict(self._config)
            }
    
    def _validate_config_value(self, key: str, value: Any) -> Dict[str, Any]:
        """Validate a config value"""
        try:
            # Edge thresholds
            if key == 'edge_threshold':
                val = float(value)
                if not 0 <= val <= 100:
                    return {'valid': False, 'error': 'Must be between 0 and 100'}
                return {'valid': True, 'value': val}
            
            if key == 'min_confidence':
                val = float(value)
                if not 0 <= val <= 1:
                    return {'valid': False, 'error': 'Must be between 0 and 1'}
                return {'valid': True, 'value': val}
            
            # Risk thresholds
            if key in ['max_position_risk_percent', 'max_portfolio_risk_percent']:
                val = float(value)
                if not 0 < val <= 50:
                    return {'valid': False, 'error': 'Must be between 0 and 50'}
                return {'valid': True, 'value': val}
            
            if key in ['max_sector_exposure', 'max_single_position']:
                val = float(value)
                if not 0 < val <= 100:
                    return {'valid': False, 'error': 'Must be between 0 and 100'}
                return {'valid': True, 'value': val}
            
            # Agent settings
            if key == 'agent_timeout_seconds':
                val = int(value)
                if not 10 <= val <= 300:
                    return {'valid': False, 'error': 'Must be between 10 and 300 seconds'}
                return {'valid': True, 'value': val}
            
            if key == 'debate_rounds':
                val = int(value)
                if not 1 <= val <= 10:
                    return {'valid': False, 'error': 'Must be between 1 and 10'}
                return {'valid': True, 'value': val}
            
            # System settings
            if key == 'log_level':
                val = str(value).upper()
                if val not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                    return {'valid': False, 'error': 'Must be DEBUG, INFO, WARNING, or ERROR'}
                return {'valid': True, 'value': val}
            
            if key == 'max_concurrent_debates':
                val = int(value)
                if not 1 <= val <= 100:
                    return {'valid': False, 'error': 'Must be between 1 and 100'}
                return {'valid': True, 'value': val}
            
            # Boolean settings
            if key in ['require_validation_for_execution', 'auto_fallback_on_anomaly']:
                if isinstance(value, bool):
                    return {'valid': True, 'value': value}
                if isinstance(value, str):
                    return {'valid': True, 'value': value.lower() in ['true', '1', 'yes']}
                return {'valid': True, 'value': bool(value)}
            
            if key == 'anomaly_threshold':
                val = float(value)
                if not 0 <= val <= 1:
                    return {'valid': False, 'error': 'Must be between 0 and 1'}
                return {'valid': True, 'value': val}
            
            # Default: accept as string/number
            return {'valid': True, 'value': value}
            
        except (ValueError, TypeError) as e:
            return {'valid': False, 'error': f'Invalid value: {str(e)}'}
    
    def register_config_callback(self, key: str, callback: Callable):
        """Register callback for config changes"""
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)
    
    def _trigger_callbacks(self, key: str, value: Any):
        """Trigger callbacks for config change"""
        for callback in self._callbacks.get(key, []):
            try:
                callback(value)
            except Exception as e:
                log.error(f"Config callback error for {key}: {e}")
    
    # ==================== SYSTEM CONTROL ====================
    
    def switch_system_mode(self, token: str, mode: str, reason: str = "") -> Dict[str, Any]:
        """
        Switch system mode (training/execution/safe).
        Requires admin session.
        """
        session = self._get_session(token)
        if not session:
            return {'success': False, 'message': 'Invalid or expired session'}
        
        from quant_ecosystem.execution_safety import execution_safety, SystemMode
        
        try:
            target_mode = SystemMode(mode.lower())
        except ValueError:
            return {'success': False, 'message': f"Invalid mode: {mode}. Must be training, execution, or safe"}
        
        success, message = execution_safety.set_mode(target_mode)
        
        if success:
            self._log_audit(
                session.admin_id,
                "MODE_SWITCH",
                f"Switched to {mode}. Reason: {reason}"
            )
        
        return {'success': success, 'message': message, 'mode': mode}
    
    def set_agent_enabled(self, token: str, agent_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable an agent"""
        session = self._get_session(token)
        if not session:
            return {'success': False, 'message': 'Invalid or expired session'}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO agent_status
                (agent_id, is_enabled, last_active)
                VALUES (?, ?, ?)
            ''', (agent_id, 1 if enabled else 0, datetime.now().isoformat()))
            conn.commit()
        
        action = "ENABLED" if enabled else "DISABLED"
        self._log_audit(session.admin_id, f"AGENT_{action}", f"Agent: {agent_id}")
        
        return {'success': True, 'message': f'Agent {agent_id} {"enabled" if enabled else "disabled"}'}
    
    def get_agent_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT agent_id, agent_name, is_enabled, last_active, 
                       error_count, avg_response_time, success_rate
                FROM agent_status
            ''')
            
            return [
                {
                    'agent_id': row[0],
                    'agent_name': row[1],
                    'is_enabled': bool(row[2]),
                    'last_active': row[3],
                    'error_count': row[4],
                    'avg_response_time': row[5],
                    'success_rate': row[6]
                }
                for row in cursor.fetchall()
            ]
    
    # ==================== SYSTEM MONITORING ====================
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get complete system state"""
        from quant_ecosystem.execution_safety import execution_safety
        from quant_ecosystem.multi_agent_orchestrator import orchestrator
        from quant_ecosystem.streaming_api import stream_manager
        
        safety_status = execution_safety.get_safety_status()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'mode': safety_status['currentMode'],
            'execution_allowed': safety_status['executionAllowed'],
            'system_safe': safety_status['systemSafe'],
            'safety_checks': safety_status['checks'],
            'config': asdict(self._config),
            'active_debates': len(orchestrator.active_sessions),
            'active_streams': stream_manager.get_active_stream_count(),
            'agents': self.get_agent_status()
        }
    
    def record_system_metrics(self, metrics: Dict[str, Any]):
        """Record system metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_metrics
                (timestamp, cpu_percent, memory_percent, active_debates, 
                 active_sessions, avg_response_time, error_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                metrics.get('cpu_percent', 0),
                metrics.get('memory_percent', 0),
                metrics.get('active_debates', 0),
                metrics.get('active_sessions', 0),
                metrics.get('avg_response_time', 0),
                metrics.get('error_rate', 0)
            ))
            conn.commit()
    
    def get_system_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics history"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, cpu_percent, memory_percent, active_debates,
                       active_sessions, avg_response_time, error_rate
                FROM system_metrics
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 1000
            ''', (cutoff,))
            
            return [
                {
                    'timestamp': row[0],
                    'cpu_percent': row[1],
                    'memory_percent': row[2],
                    'active_debates': row[3],
                    'active_sessions': row[4],
                    'avg_response_time': row[5],
                    'error_rate': row[6]
                }
                for row in cursor.fetchall()
            ]
    
    def get_audit_log(self, token: str, limit: int = 100) -> Dict[str, Any]:
        """Get system audit log (admin only)"""
        session = self._get_session(token)
        if not session:
            return {'success': False, 'message': 'Invalid session'}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, admin_id, action, details, ip_address
                FROM system_audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return {
                'success': True,
                'logs': [
                    {
                        'timestamp': row[0],
                        'admin_id': row[1],
                        'action': row[2],
                        'details': row[3],
                        'ip_address': row[4]
                    }
                    for row in cursor.fetchall()
                ]
            }


# Global instance
admin_control = AdminControlSystem()
