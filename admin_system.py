"""
OraclAI Admin Control System
Website Builder Release Management
Authentication: MK1/123456
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import threading
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'admin_control.db')

class AdminAuth:
    """
    Admin Authentication System
    Credentials: MK1 / 123456
    """
    
    # Admin credentials (hashed)
    ADMIN_USERNAME_HASH = hashlib.sha256("MK1".encode()).hexdigest()
    ADMIN_PASSWORD_HASH = hashlib.sha256("123456".encode()).hexdigest()
    
    def __init__(self):
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize admin database"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    session_id TEXT PRIMARY KEY,
                    username_hash TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Feature releases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_releases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_name TEXT UNIQUE,
                    is_released BOOLEAN DEFAULT 0,
                    released_at TIMESTAMP,
                    released_by TEXT
                )
            ''')
            
            # Initialize website builder as unreleased
            cursor.execute('''
                INSERT OR IGNORE INTO feature_releases (feature_name, is_released)
                VALUES ('website_builder', 0)
            ''')
            
            conn.commit()
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate admin user
        Returns session_id if successful, None if failed
        """
        # Hash credentials
        username_hash = hashlib.sha256(username.encode()).hexdigest()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Verify
        if (username_hash == self.ADMIN_USERNAME_HASH and 
            password_hash == self.ADMIN_PASSWORD_HASH):
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO admin_sessions (session_id, username_hash, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, username_hash, datetime.now(), expires_at))
                conn.commit()
            
            return session_id
        
        return None
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session is active and not expired"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT expires_at, is_active FROM admin_sessions
                WHERE session_id = ?
            ''', (session_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            expires_at, is_active = result
            if not is_active:
                return False
            
            # Check expiration
            if datetime.now() > datetime.fromisoformat(expires_at):
                # Deactivate expired session
                cursor.execute('''
                    UPDATE admin_sessions SET is_active = 0 WHERE session_id = ?
                ''', (session_id,))
                conn.commit()
                return False
            
            return True
    
    def logout(self, session_id: str):
        """Invalidate session"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE admin_sessions SET is_active = 0 WHERE session_id = ?
            ''', (session_id,))
            conn.commit()


class FeatureReleaseManager:
    """
    Manages feature releases - controls which features are public vs admin-only
    """
    
    def __init__(self):
        self.auth = AdminAuth()
    
    def is_feature_released(self, feature_name: str) -> bool:
        """Check if feature is publicly released"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT is_released FROM feature_releases
                WHERE feature_name = ?
            ''', (feature_name,))
            result = cursor.fetchone()
            
            if result:
                return bool(result[0])
            return False
    
    def release_feature(self, feature_name: str, session_id: str) -> Dict:
        """
        Release feature to public (admin only)
        """
        # Verify admin session
        if not self.auth.validate_session(session_id):
            return {'success': False, 'error': 'Invalid admin session'}
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE feature_releases
                SET is_released = 1, released_at = ?, released_by = ?
                WHERE feature_name = ?
            ''', (datetime.now(), 'MK1', feature_name))
            conn.commit()
        
        return {
            'success': True,
            'feature': feature_name,
            'released_at': datetime.now().isoformat(),
            'message': f'{feature_name} has been released to public'
        }
    
    def unreleased_feature(self, feature_name: str, session_id: str) -> Dict:
        """Hide feature from public (admin only)"""
        if not self.auth.validate_session(session_id):
            return {'success': False, 'error': 'Invalid admin session'}
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE feature_releases
                SET is_released = 0, released_at = NULL, released_by = NULL
                WHERE feature_name = ?
            ''', (feature_name,))
            conn.commit()
        
        return {
            'success': True,
            'feature': feature_name,
            'message': f'{feature_name} is now admin-only'
        }
    
    def get_all_features(self) -> List[Dict]:
        """Get all feature statuses"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT feature_name, is_released, released_at, released_by
                FROM feature_releases
            ''')
            results = cursor.fetchall()
            
            features = []
            for row in results:
                features.append({
                    'name': row[0],
                    'is_released': bool(row[1]),
                    'released_at': row[2],
                    'released_by': row[3]
                })
            
            return features


class AdminController:
    """Main admin controller combining auth and feature management"""
    
    def __init__(self):
        self.auth = AdminAuth()
        self.features = FeatureReleaseManager()
    
    def login(self, username: str, password: str) -> Dict:
        """Admin login endpoint"""
        session_id = self.auth.authenticate(username, password)
        
        if session_id:
            return {
                'success': True,
                'session_id': session_id,
                'username': username,
                'message': 'Authentication successful'
            }
        else:
            return {
                'success': False,
                'error': 'Invalid credentials'
            }
    
    def logout(self, session_id: str) -> Dict:
        """Admin logout endpoint"""
        self.auth.logout(session_id)
        return {'success': True, 'message': 'Logged out successfully'}
    
    def check_access(self, session_id: str, feature_name: str = None) -> Dict:
        """Check if user has access to feature"""
        is_admin = self.auth.validate_session(session_id)
        
        # Admin always has access
        if is_admin:
            return {'has_access': True, 'is_admin': True}
        
        # Non-admin only if feature is released
        if feature_name:
            is_released = self.features.is_feature_released(feature_name)
            return {'has_access': is_released, 'is_admin': False}
        
        return {'has_access': False, 'is_admin': False}


# Singleton
admin_controller = AdminController()
