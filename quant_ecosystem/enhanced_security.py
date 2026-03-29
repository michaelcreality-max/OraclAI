"""
Enhanced Security Module for Admin-Level Control
Provides JWT authentication, strict role checks, rate limiting, input validation, and comprehensive logging.
"""

import os
import re
import json
import hmac
import hashlib
import secrets
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, Tuple, Union
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum

from flask import request, jsonify, g, current_app
import jwt

log = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


class SecurityRole(Enum):
    """Security roles for access control"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API = "api"


class SecurityLevel(Enum):
    """Security classification levels"""
    CRITICAL = "critical"  # System-level changes
    HIGH = "high"          # Admin operations
    MEDIUM = "medium"      # User operations
    LOW = "low"            # Read-only operations


@dataclass
class JWTToken:
    """JWT Token data model"""
    token: str
    token_type: str  # 'access' or 'refresh'
    admin_id: str
    email: str
    role: SecurityRole
    issued_at: datetime
    expires_at: datetime
    jti: str  # JWT ID for revocation


@dataclass
class RateLimitEntry:
    """Rate limit tracking with enhanced security"""
    requests: List[Tuple[float, str, str]] = field(default_factory=list)  # (timestamp, ip, endpoint)
    blocked_until: Optional[float] = None
    violation_count: int = 0
    
    def is_allowed(self, limit: int, window_seconds: int = 60, 
                   burst_limit: int = 10) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed with burst protection"""
        now = time.time()
        
        # Check if currently blocked
        if self.blocked_until and now < self.blocked_until:
            remaining = int(self.blocked_until - now)
            return False, f"Rate limit exceeded. Try again in {remaining} seconds."
        
        # Clear block if expired
        if self.blocked_until and now >= self.blocked_until:
            self.blocked_until = None
        
        cutoff = now - window_seconds
        
        # Remove old requests
        self.requests = [(t, ip, ep) for t, ip, ep in self.requests if t > cutoff]
        
        # Check burst limit (requests in last 10 seconds)
        burst_cutoff = now - 10
        recent_requests = [(t, ip, ep) for t, ip, ep in self.requests if t > burst_cutoff]
        
        if len(recent_requests) >= burst_limit:
            # Block for 60 seconds on burst violation
            self.blocked_until = now + 60
            self.violation_count += 1
            return False, "Burst limit exceeded. Blocked for 60 seconds."
        
        # Check standard rate limit
        if len(self.requests) >= limit:
            return False, f"Rate limit exceeded ({limit} requests per {window_seconds}s)."
        
        return True, None
    
    def add_request(self, ip: str, endpoint: str):
        """Record a new request with context"""
        self.requests.append((time.time(), ip, endpoint))


@dataclass
class SecurityContext:
    """Security context for request handling"""
    admin_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[SecurityRole] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: str = field(default_factory=lambda: secrets.token_hex(8))
    timestamp: datetime = field(default_factory=datetime.now)
    security_level: SecurityLevel = SecurityLevel.LOW


class EnhancedSecurityManager:
    """
    Enhanced security manager with JWT authentication, strict role checks,
    rate limiting, input validation, and comprehensive logging.
    """
    
    def __init__(self, db_path: str = "enhanced_security.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._rate_limits: Dict[str, RateLimitEntry] = {}
        self._revoked_tokens: Set[str] = set()
        self._security_callbacks: List[Callable] = []
        self._init_database()
    
    def _init_database(self):
        """Initialize security database with hardened tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enhanced admin sessions table with JWT support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_sessions (
                    session_id TEXT PRIMARY KEY,
                    admin_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'admin',
                    jti TEXT UNIQUE NOT NULL,
                    issued_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_activity TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active INTEGER DEFAULT 1,
                    revoked INTEGER DEFAULT 0,
                    revoked_at TEXT,
                    revoke_reason TEXT
                )
            ''')
            
            # Security audit log with enhanced tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    admin_id TEXT,
                    email TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    method TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT,
                    security_level TEXT,
                    success INTEGER,
                    error_message TEXT,
                    duration_ms REAL
                )
            ''')
            
            # Failed login attempts tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_login_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    email TEXT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    reason TEXT,
                    count INTEGER DEFAULT 1
                )
            ''')
            
            # IP blocking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_blocks (
                    ip_address TEXT PRIMARY KEY,
                    blocked_at TEXT NOT NULL,
                    blocked_until TEXT NOT NULL,
                    reason TEXT,
                    attempt_count INTEGER DEFAULT 1
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_security_sessions_jti 
                ON security_sessions(jti)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_security_audit_admin 
                ON security_audit_log(admin_id, timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_security_audit_action 
                ON security_audit_log(action, timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_failed_login_ip 
                ON failed_login_attempts(ip_address, timestamp)
            ''')
            
            conn.commit()
            log.info("Enhanced security database initialized")
    
    # ==================== JWT AUTHENTICATION ====================
    
    def generate_jwt_tokens(self, admin_id: str, email: str, 
                          role: SecurityRole = SecurityRole.ADMIN,
                          ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Generate JWT access and refresh tokens.
        
        Returns:
            {
                'access_token': str,
                'refresh_token': str,
                'token_type': 'Bearer',
                'expires_in': int (seconds)
            }
        """
        now = datetime.utcnow()
        
        # Access token
        access_jti = secrets.token_urlsafe(16)
        access_payload = {
            'sub': admin_id,
            'email': email,
            'role': role.value,
            'type': 'access',
            'jti': access_jti,
            'iat': now,
            'exp': now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            'ip': ip_address,
            'ua': hashlib.sha256(user_agent.encode()).hexdigest()[:16] if user_agent else None
        }
        
        access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Refresh token
        refresh_jti = secrets.token_urlsafe(16)
        refresh_payload = {
            'sub': admin_id,
            'email': email,
            'role': role.value,
            'type': 'refresh',
            'jti': refresh_jti,
            'iat': now,
            'exp': now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        }
        
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Store session in database
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO security_sessions
                    (session_id, admin_id, email, role, jti, issued_at, expires_at,
                     last_activity, ip_address, user_agent, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    access_jti,
                    admin_id,
                    email,
                    role.value,
                    access_jti,
                    now.isoformat(),
                    access_payload['exp'].isoformat(),
                    now.isoformat(),
                    ip_address,
                    user_agent
                ))
                conn.commit()
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def validate_jwt_token(self, token: str, token_type: str = 'access',
                          ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token with enhanced security checks.
        
        Returns decoded payload if valid, None otherwise.
        """
        try:
            # Decode token
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check token type
            if payload.get('type') != token_type:
                log.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            # Check if token is revoked
            jti = payload.get('jti')
            if jti in self._revoked_tokens:
                log.warning(f"Attempted use of revoked token: {jti[:8]}...")
                return None
            
            # Check database for revocation
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT revoked FROM security_sessions WHERE jti = ?
                ''', (jti,))
                row = cursor.fetchone()
                if not row or row[0]:
                    log.warning(f"Token revoked or not found: {jti[:8]}...")
                    return None
                
                # Update last activity
                cursor.execute('''
                    UPDATE security_sessions 
                    SET last_activity = ?
                    WHERE jti = ?
                ''', (datetime.utcnow().isoformat(), jti))
                conn.commit()
            
            # IP binding check (if configured)
            if payload.get('ip') and ip_address and payload['ip'] != ip_address:
                log.warning(f"IP mismatch for token {jti[:8]}...: expected {payload['ip']}, got {ip_address}")
                # Don't fail immediately, but log for security review
            
            return payload
            
        except jwt.ExpiredSignatureError:
            log.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            log.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            log.error(f"JWT validation error: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Generate new access token using refresh token"""
        payload = self.validate_jwt_token(refresh_token, token_type='refresh')
        if not payload:
            return None
        
        admin_id = payload['sub']
        email = payload['email']
        role = SecurityRole(payload['role'])
        
        # Generate new tokens
        return self.generate_jwt_tokens(admin_id, email, role)
    
    def revoke_token(self, jti: str, reason: str = "Logout"):
        """Revoke a specific token by JTI"""
        with self.lock:
            self._revoked_tokens.add(jti)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE security_sessions
                    SET revoked = 1, revoked_at = ?, revoke_reason = ?
                    WHERE jti = ?
                ''', (datetime.utcnow().isoformat(), reason, jti))
                conn.commit()
    
    def revoke_all_user_tokens(self, admin_id: str, reason: str = "Security action"):
        """Revoke all tokens for a user"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all JTIs for user
                cursor.execute('''
                    SELECT jti FROM security_sessions 
                    WHERE admin_id = ? AND revoked = 0
                ''', (admin_id,))
                
                jtis = [row[0] for row in cursor.fetchall()]
                
                # Revoke in memory
                for jti in jtis:
                    self._revoked_tokens.add(jti)
                
                # Revoke in database
                cursor.execute('''
                    UPDATE security_sessions
                    SET revoked = 1, revoked_at = ?, revoke_reason = ?
                    WHERE admin_id = ? AND revoked = 0
                ''', (datetime.utcnow().isoformat(), reason, admin_id))
                conn.commit()
                
                log.info(f"Revoked {len(jtis)} tokens for admin {admin_id}")
    
    # ==================== RATE LIMITING ====================
    
    def check_rate_limit(self, identifier: str, limit: int = 60, 
                        window_seconds: int = 60, ip_address: str = None,
                        endpoint: str = None) -> Tuple[bool, Optional[str]]:
        """
        Check rate limit for an identifier (IP, user, etc.)
        
        Returns: (allowed, error_message)
        """
        with self.lock:
            if identifier not in self._rate_limits:
                self._rate_limits[identifier] = RateLimitEntry()
            
            entry = self._rate_limits[identifier]
            allowed, error = entry.is_allowed(limit, window_seconds)
            
            if allowed:
                entry.add_request(ip_address or 'unknown', endpoint or 'unknown')
            
            return allowed, error
    
    def is_ip_blocked(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """Check if IP is blocked"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT blocked_until, reason FROM ip_blocks
                WHERE ip_address = ? AND blocked_until > ?
            ''', (ip_address, datetime.utcnow().isoformat()))
            
            row = cursor.fetchone()
            if row:
                return True, f"IP blocked: {row[1]}"
            
            return False, None
    
    def block_ip(self, ip_address: str, duration_minutes: int = 60, 
                 reason: str = "Security violation"):
        """Block an IP address"""
        blocked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ip_blocks
                (ip_address, blocked_at, blocked_until, reason, attempt_count)
                VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT attempt_count + 1 FROM ip_blocks WHERE ip_address = ?), 1))
            ''', (
                ip_address,
                datetime.utcnow().isoformat(),
                blocked_until.isoformat(),
                reason,
                ip_address
            ))
            conn.commit()
        
        log.warning(f"IP {ip_address} blocked for {duration_minutes}m: {reason}")
    
    # ==================== INPUT VALIDATION & SANITIZATION ====================
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255, 
                        allow_html: bool = False) -> str:
        """Sanitize a string input"""
        if not isinstance(value, str):
            return str(value)[:max_length]
        
        # Trim whitespace
        value = value.strip()
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit length
        value = value[:max_length]
        
        # Remove HTML if not allowed
        if not allow_html:
            value = re.sub(r'<[^>]+>', '', value)
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain digit"
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Password must contain special character"
        return True, ""
    
    @staticmethod
    def validate_token_format(token: str) -> bool:
        """Validate JWT token format"""
        if not token:
            return False
        parts = token.split('.')
        return len(parts) == 3
    
    # ==================== SECURITY LOGGING ====================
    
    def log_security_event(self, context: SecurityContext, action: str,
                          resource: str = None, method: str = None,
                          success: bool = True, error_message: str = None,
                          duration_ms: float = None, details: Dict = None):
        """Log security event with full context"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO security_audit_log
                (timestamp, request_id, admin_id, email, action, resource,
                 method, ip_address, user_agent, details, security_level,
                 success, error_message, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.utcnow().isoformat(),
                context.request_id,
                context.admin_id,
                context.email,
                action,
                resource,
                method,
                context.ip_address,
                context.user_agent,
                json.dumps(details) if details else None,
                context.security_level.value,
                1 if success else 0,
                error_message,
                duration_ms
            ))
            conn.commit()
    
    def log_failed_login(self, email: str = None, ip_address: str = None,
                        user_agent: str = None, reason: str = None):
        """Log failed login attempt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if we should increment existing record
            cutoff = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            cursor.execute('''
                SELECT attempt_id, count FROM failed_login_attempts
                WHERE ip_address = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (ip_address, cutoff))
            
            row = cursor.fetchone()
            if row:
                # Increment existing
                cursor.execute('''
                    UPDATE failed_login_attempts
                    SET count = count + 1
                    WHERE attempt_id = ?
                ''', (row[0],))
                
                # Check for brute force (10+ failed attempts in 5 min)
                if row[1] + 1 >= 10:
                    self.block_ip(ip_address, 60, "Brute force detection")
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO failed_login_attempts
                    (timestamp, email, ip_address, user_agent, reason, count)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (
                    datetime.utcnow().isoformat(),
                    email,
                    ip_address,
                    user_agent,
                    reason
                ))
            
            conn.commit()
    
    def get_security_audit_log(self, admin_id: str = None, 
                              action: str = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get security audit log with filtering"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT timestamp, request_id, admin_id, email, action, resource,
                       method, ip_address, security_level, success, error_message
                FROM security_audit_log
                WHERE 1=1
            '''
            params = []
            
            if admin_id:
                query += ' AND admin_id = ?'
                params.append(admin_id)
            
            if action:
                query += ' AND action = ?'
                params.append(action)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [
                {
                    'timestamp': row[0],
                    'request_id': row[1],
                    'admin_id': row[2],
                    'email': row[3],
                    'action': row[4],
                    'resource': row[5],
                    'method': row[6],
                    'ip_address': row[7],
                    'security_level': row[8],
                    'success': bool(row[9]),
                    'error_message': row[10]
                }
                for row in cursor.fetchall()
            ]


# Global instance
security_manager = EnhancedSecurityManager()


# ==================== DECORATORS ====================

def require_jwt_auth(roles: Optional[Set[SecurityRole]] = None,
                     security_level: SecurityLevel = SecurityLevel.MEDIUM):
    """
    Decorator to require JWT authentication.
    Optionally restrict to specific roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Build security context
            context = SecurityContext(
                ip_address=_get_client_ip(),
                user_agent=_get_user_agent(),
                security_level=security_level
            )
            
            # Check IP block
            blocked, block_reason = security_manager.is_ip_blocked(context.ip_address)
            if blocked:
                security_manager.log_security_event(
                    context, "ACCESS_BLOCKED", success=False,
                    error_message=block_reason
                )
                return jsonify({
                    "error": "Access denied",
                    "message": block_reason
                }), 403
            
            # Get token from header
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                security_manager.log_security_event(
                    context, "AUTH_MISSING", success=False,
                    error_message="Missing or invalid Authorization header"
                )
                return jsonify({
                    "error": "Authentication required",
                    "message": "Include 'Authorization: Bearer <token>' header"
                }), 401
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Validate token format
            if not security_manager.validate_token_format(token):
                security_manager.log_security_event(
                    context, "AUTH_INVALID_TOKEN", success=False,
                    error_message="Invalid token format"
                )
                return jsonify({
                    "error": "Invalid token",
                    "message": "Token format is invalid"
                }), 401
            
            # Validate token
            payload = security_manager.validate_jwt_token(
                token, 
                ip_address=context.ip_address,
                user_agent=context.user_agent
            )
            
            if not payload:
                security_manager.log_security_event(
                    context, "AUTH_INVALID_TOKEN", success=False,
                    error_message="Token validation failed"
                )
                return jsonify({
                    "error": "Invalid or expired token",
                    "message": "Please log in again"
                }), 401
            
            # Update context with token info
            context.admin_id = payload['sub']
            context.email = payload['email']
            context.role = SecurityRole(payload['role'])
            
            # Check role permissions
            if roles and context.role not in roles:
                security_manager.log_security_event(
                    context, "AUTH_INSUFFICIENT_ROLE", success=False,
                    error_message=f"Required roles: {[r.value for r in roles]}"
                )
                return jsonify({
                    "error": "Insufficient permissions",
                    "message": f"This endpoint requires: {[r.value for r in roles]}"
                }), 403
            
            # Check rate limit for authenticated user
            rate_key = f"user:{context.admin_id}"
            allowed, error = security_manager.check_rate_limit(
                rate_key, limit=120, window_seconds=60,
                ip_address=context.ip_address,
                endpoint=request.endpoint
            )
            
            if not allowed:
                security_manager.log_security_event(
                    context, "RATE_LIMIT_EXCEEDED", success=False,
                    error_message=error
                )
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": error
                }), 429
            
            # Store context in Flask g
            g.security_context = context
            g.jwt_payload = payload
            
            # Log successful access
            security_manager.log_security_event(
                context, "ACCESS_GRANTED",
                resource=request.path,
                method=request.method,
                success=True
            )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin_jwt(security_level: SecurityLevel = SecurityLevel.HIGH):
    """Shortcut decorator for admin-only JWT endpoints"""
    return require_jwt_auth(roles={SecurityRole.ADMIN}, security_level=security_level)


def validate_input(schema: Dict[str, Dict[str, Any]]):
    """
    Decorator to validate and sanitize input data.
    
    Schema format:
    {
        'field_name': {
            'type': str/int/float/bool/list/dict,
            'required': True/False,
            'min': min_value (for numbers),
            'max': max_value (for numbers),
            'min_length': min_length (for strings/lists),
            'max_length': max_length (for strings/lists),
            'pattern': regex_pattern (for strings),
            'allowed_values': list of allowed values,
            'sanitize': True/False (strip HTML, etc)
        }
    }
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            errors = []
            sanitized = {}
            
            for field_name, rules in schema.items():
                value = data.get(field_name)
                
                # Check required
                if rules.get('required', False) and value is None:
                    errors.append(f"{field_name}: Required field missing")
                    continue
                
                if value is None:
                    continue
                
                # Type validation
                expected_type = rules.get('type')
                if expected_type:
                    try:
                        if expected_type == int:
                            value = int(value)
                        elif expected_type == float:
                            value = float(value)
                        elif expected_type == bool:
                            if isinstance(value, str):
                                value = value.lower() in ('true', '1', 'yes')
                            else:
                                value = bool(value)
                        elif expected_type == str:
                            value = str(value)
                        elif expected_type == list:
                            if not isinstance(value, list):
                                value = [value]
                        elif expected_type == dict:
                            if not isinstance(value, dict):
                                errors.append(f"{field_name}: Must be an object")
                                continue
                    except (ValueError, TypeError):
                        errors.append(f"{field_name}: Invalid type, expected {expected_type.__name__}")
                        continue
                
                # Range validation for numbers
                if expected_type in (int, float):
                    if 'min' in rules and value < rules['min']:
                        errors.append(f"{field_name}: Must be >= {rules['min']}")
                    if 'max' in rules and value > rules['max']:
                        errors.append(f"{field_name}: Must be <= {rules['max']}")
                
                # Length validation
                if expected_type in (str, list):
                    if 'min_length' in rules and len(value) < rules['min_length']:
                        errors.append(f"{field_name}: Length must be >= {rules['min_length']}")
                    if 'max_length' in rules and len(value) > rules['max_length']:
                        errors.append(f"{field_name}: Length must be <= {rules['max_length']}")
                
                # Pattern validation
                if expected_type == str and 'pattern' in rules:
                    if not re.match(rules['pattern'], value):
                        errors.append(f"{field_name}: Invalid format")
                
                # Allowed values
                if 'allowed_values' in rules and value not in rules['allowed_values']:
                    errors.append(f"{field_name}: Must be one of {rules['allowed_values']}")
                
                # Sanitization
                if expected_type == str and rules.get('sanitize', True):
                    value = security_manager.sanitize_string(
                        value, 
                        max_length=rules.get('max_length', 255),
                        allow_html=False
                    )
                
                sanitized[field_name] = value
            
            if errors:
                # Log validation failure
                if hasattr(g, 'security_context'):
                    security_manager.log_security_event(
                        g.security_context, "INPUT_VALIDATION_FAILED",
                        resource=request.path, method=request.method,
                        success=False, error_message="; ".join(errors),
                        details={'errors': errors}
                    )
                
                return jsonify({
                    "error": "Validation failed",
                    "errors": errors
                }), 400
            
            # Store sanitized data
            g.sanitized_input = sanitized
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit(requests_per_minute: int = 60, 
               burst_limit: int = 10,
               by_ip: bool = True,
               by_user: bool = True):
    """
    Decorator to apply rate limiting to endpoints.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = _get_client_ip()
            
            # Check IP rate limit
            if by_ip:
                allowed, error = security_manager.check_rate_limit(
                    f"ip:{ip_address}",
                    limit=requests_per_minute,
                    window_seconds=60,
                    ip_address=ip_address,
                    endpoint=request.endpoint
                )
                
                if not allowed:
                    context = SecurityContext(
                        ip_address=ip_address,
                        user_agent=_get_user_agent()
                    )
                    security_manager.log_security_event(
                        context, "RATE_LIMIT_EXCEEDED",
                        resource=request.path, method=request.method,
                        success=False, error_message=error
                    )
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "message": error
                    }), 429
            
            # Check user rate limit
            if by_user and hasattr(g, 'jwt_payload'):
                admin_id = g.jwt_payload.get('sub')
                if admin_id:
                    allowed, error = security_manager.check_rate_limit(
                        f"user:{admin_id}",
                        limit=requests_per_minute,
                        window_seconds=60,
                        ip_address=ip_address,
                        endpoint=request.endpoint
                    )
                    
                    if not allowed:
                        return jsonify({
                            "error": "Rate limit exceeded",
                            "message": error
                        }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== HELPER FUNCTIONS ====================

def _get_client_ip() -> str:
    """Get client IP address from request with proxy support"""
    # Check X-Forwarded-For header (for proxies)
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        # Take the first IP in the chain (client IP)
        return forwarded.split(',')[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to remote_addr
    return request.remote_addr or 'unknown'


def _get_user_agent() -> str:
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'unknown')


def get_current_security_context() -> Optional[SecurityContext]:
    """Get current request's security context"""
    return getattr(g, 'security_context', None)


def log_admin_action(action: str, details: Dict[str, Any] = None,
                    security_level: SecurityLevel = SecurityLevel.MEDIUM):
    """Helper to log admin action with current context"""
    context = get_current_security_context()
    if context:
        security_manager.log_security_event(
            context, action,
            resource=request.path if request else None,
            method=request.method if request else None,
            success=True,
            details=details,
            security_level=security_level
        )
