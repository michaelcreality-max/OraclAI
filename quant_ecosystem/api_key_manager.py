"""
API Key Management System
Provides secure API key generation, storage, validation, rate limiting, and role-based access control.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from functools import wraps

from flask import request, jsonify, g

log = logging.getLogger(__name__)


class Role(Enum):
    """User roles for permission-based access control"""
    ADMIN = "admin"
    USER = "user"


@dataclass
class APIKey:
    """API Key data model"""
    id: str
    name: str
    key_hash: str
    role: Role
    created_at: datetime
    last_used_at: Optional[datetime] = None
    request_count: int = 0
    is_active: bool = True
    rate_limit: int = 60  # requests per minute
    
    def to_dict(self, include_key: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "request_count": self.request_count,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit
        }
        if include_key:
            result["key"] = "[REDACTED]"
        return result


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry"""
    requests: List[float] = field(default_factory=list)
    
    def is_allowed(self, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        cutoff = now - window_seconds
        # Remove old requests outside the window
        self.requests = [t for t in self.requests if t > cutoff]
        return len(self.requests) < limit
    
    def add_request(self):
        """Record a new request"""
        self.requests.append(time.time())


class APIKeyManager:
    """
    Manages API keys with secure hashing, rate limiting, and role-based permissions.
    Uses SQLite for persistence.
    """
    
    def __init__(self, db_path: str = "api_keys.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._rate_limits: Dict[str, RateLimitEntry] = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # API keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    request_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    rate_limit INTEGER DEFAULT 60
                )
            ''')
            
            # Create index on key_hash for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash)
            ''')
            
            conn.commit()
            log.info("API key database initialized")
    
    def _hash_key(self, key: str) -> str:
        """
        Hash an API key using HMAC-SHA256.
        Uses a static pepper from environment for additional security.
        """
        # In production, use a proper secret key from environment
        pepper = self._get_pepper()
        return hmac.new(
            pepper.encode(),
            key.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _get_pepper(self) -> str:
        """Get pepper from environment or use default (for dev)"""
        import os
        return os.environ.get('API_KEY_PEPPER', 'dev-pepper-change-in-production')
    
    def generate_key(self, name: str, role: Role = Role.USER, rate_limit: int = 60) -> Tuple[str, APIKey]:
        """
        Generate a new API key.
        Returns the plain key (shown once) and the stored APIKey object.
        """
        # Generate cryptographically secure random key
        random_bytes = secrets.token_bytes(32)
        key = f"ak_{random_bytes.hex()}"
        
        # Hash the key for storage
        key_hash = self._hash_key(key)
        
        # Create API key record
        api_key = APIKey(
            id=secrets.token_hex(16),
            name=name,
            key_hash=key_hash,
            role=role,
            created_at=datetime.now(),
            rate_limit=rate_limit
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO api_keys (id, name, key_hash, role, created_at, last_used_at, 
                                    request_count, is_active, rate_limit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                api_key.id, api_key.name, api_key.key_hash, api_key.role.value,
                api_key.created_at.isoformat(), None, 0, 1, api_key.rate_limit
            ))
            conn.commit()
        
        log.info(f"Generated API key '{name}' with role {role.value}")
        return key, api_key
    
    def validate_key(self, key: str) -> Optional[APIKey]:
        """
        Validate an API key and return the associated APIKey object if valid.
        Also checks rate limiting and updates last_used_at.
        """
        if not key or not key.startswith('ak_'):
            return None
        
        key_hash = self._hash_key(key)
        
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, key_hash, role, created_at, last_used_at,
                           request_count, is_active, rate_limit
                    FROM api_keys WHERE key_hash = ?
                ''', (key_hash,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                api_key = APIKey(
                    id=row[0],
                    name=row[1],
                    key_hash=row[2],
                    role=Role(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    last_used_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    request_count=row[6],
                    is_active=bool(row[7]),
                    rate_limit=row[8]
                )
                
                if not api_key.is_active:
                    return None
                
                # Check rate limit
                if not self._check_rate_limit(api_key.id, api_key.rate_limit):
                    log.warning(f"Rate limit exceeded for API key {api_key.id}")
                    return None
                
                # Update usage statistics
                now = datetime.now()
                cursor.execute('''
                    UPDATE api_keys 
                    SET last_used_at = ?, request_count = request_count + 1
                    WHERE id = ?
                ''', (now.isoformat(), api_key.id))
                conn.commit()
                
                api_key.last_used_at = now
                api_key.request_count += 1
                
                return api_key
    
    def _check_rate_limit(self, key_id: str, limit: int) -> bool:
        """Check if request is within rate limit for the key"""
        with self.lock:
            if key_id not in self._rate_limits:
                self._rate_limits[key_id] = RateLimitEntry()
            
            entry = self._rate_limits[key_id]
            if entry.is_allowed(limit):
                entry.add_request()
                return True
            return False
    
    def get_all_keys(self) -> List[APIKey]:
        """Get all API keys (for admin purposes)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, key_hash, role, created_at, last_used_at,
                       request_count, is_active, rate_limit
                FROM api_keys ORDER BY created_at DESC
            ''')
            
            keys = []
            for row in cursor.fetchall():
                keys.append(APIKey(
                    id=row[0],
                    name=row[1],
                    key_hash=row[2],
                    role=Role(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    last_used_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    request_count=row[6],
                    is_active=bool(row[7]),
                    rate_limit=row[8]
                ))
            return keys
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE api_keys SET is_active = 0 WHERE id = ?', (key_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_key(self, key_id: str) -> bool:
        """Permanently delete an API key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
            conn.commit()
            # Also clean up rate limit entry
            self._rate_limits.pop(key_id, None)
            return cursor.rowcount > 0
    
    def create_master_key(self) -> Optional[str]:
        """Create initial master admin key if no keys exist"""
        keys = self.get_all_keys()
        if not keys:
            key, _ = self.generate_key("Master Admin", Role.ADMIN, rate_limit=1000)
            log.info("Created master admin key (save this!):")
            log.info(f"  {key}")
            return key
        return None


# Global instance
api_key_manager = APIKeyManager()


def get_bearer_token() -> Optional[str]:
    """Extract Bearer token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None


def require_auth(roles: Optional[Set[Role]] = None):
    """
    Decorator to require valid API key authentication.
    Optionally restrict to specific roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from Authorization header
            key = get_bearer_token()
            
            if not key:
                return jsonify({
                    "error": "Authentication required",
                    "message": "Include 'Authorization: Bearer <api_key>' header"
                }), 401
            
            # Validate key
            api_key = api_key_manager.validate_key(key)
            
            if not api_key:
                return jsonify({
                    "error": "Invalid or revoked API key",
                    "message": "The provided API key is invalid, revoked, or rate limited"
                }), 401
            
            # Check role permissions
            if roles and api_key.role not in roles:
                return jsonify({
                    "error": "Insufficient permissions",
                    "message": f"This endpoint requires one of: {[r.value for r in roles]}"
                }), 403
            
            # Store validated key in Flask g object for access in endpoint
            g.api_key = api_key
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f):
    """Shortcut decorator for admin-only endpoints"""
    return require_auth(roles={Role.ADMIN})(f)


def require_user_or_admin(f):
    """Shortcut decorator for any authenticated user"""
    return require_auth(roles={Role.USER, Role.ADMIN})(f)
