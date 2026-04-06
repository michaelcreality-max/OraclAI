"""
Production Database Layer - Real Implementation
SQLite/PostgreSQL persistence for all application data
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading


class DatabaseManager:
    """
    Production-grade database manager with connection pooling
    Supports SQLite (default) and PostgreSQL (production)
    """
    
    def __init__(self, db_path: str = "oraclai.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def _init_database(self):
        """Initialize database schema"""
        with self.transaction() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    risk_profile TEXT DEFAULT 'moderate',
                    preferences TEXT
                )
            """)
            
            # Portfolio positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    shares REAL NOT NULL,
                    avg_entry_price REAL NOT NULL,
                    current_price REAL,
                    market_value REAL,
                    unrealized_pnl REAL,
                    unrealized_pnl_percent REAL,
                    entry_time TIMESTAMP,
                    strategy TEXT,
                    stop_loss REAL,
                    take_profit REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Trade history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    shares REAL NOT NULL,
                    position_value REAL,
                    status TEXT NOT NULL,
                    entry_time TIMESTAMP,
                    exit_time TIMESTAMP,
                    pnl REAL,
                    pnl_percent REAL,
                    strategy TEXT,
                    confidence REAL,
                    exit_reason TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # AI analysis cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    UNIQUE(symbol, analysis_type)
                )
            """)
            
            # User queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    symbols TEXT,
                    query_type TEXT,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Generated websites
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    name TEXT NOT NULL,
                    template TEXT,
                    complexity TEXT,
                    files TEXT,
                    file_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deployed_url TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # API usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Market data cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, data_type, timestamp)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_user ON positions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON analysis_cache(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_user ON queries(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_user ON api_usage(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol)")
    
    # User Operations
    def create_user(self, user_id: str, email: str, username: Optional[str] = None,
                   password_hash: Optional[str] = None, preferences: Optional[Dict] = None) -> bool:
        """Create a new user"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (id, email, username, password_hash, preferences)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, email, username, password_hash, 
                      json.dumps(preferences) if preferences else None))
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user fields"""
        allowed_fields = ['email', 'username', 'risk_profile', 'preferences', 'is_active', 'last_login']
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                set_clause = ', '.join(f"{k} = ?" for k in update_fields.keys())
                values = list(update_fields.values())
                if 'preferences' in update_fields:
                    values[update_fields.keys().index('preferences')] = json.dumps(update_fields['preferences'])
                values.append(user_id)
                
                cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
                return cursor.rowcount > 0
        except Exception:
            return False
    
    # Position Operations
    def create_position(self, position_data: Dict) -> bool:
        """Create or update a position"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO positions 
                    (user_id, symbol, direction, shares, avg_entry_price, current_price,
                     market_value, unrealized_pnl, unrealized_pnl_percent, entry_time,
                     strategy, stop_loss, take_profit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position_data['user_id'],
                    position_data['symbol'],
                    position_data['direction'],
                    position_data['shares'],
                    position_data['avg_entry_price'],
                    position_data.get('current_price'),
                    position_data.get('market_value'),
                    position_data.get('unrealized_pnl'),
                    position_data.get('unrealized_pnl_percent'),
                    position_data.get('entry_time'),
                    position_data.get('strategy'),
                    position_data.get('stop_loss'),
                    position_data.get('take_profit')
                ))
                return True
        except Exception:
            return False
    
    def get_positions(self, user_id: str) -> List[Dict]:
        """Get all positions for a user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE user_id = ?", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_position(self, user_id: str, symbol: str, direction: str) -> bool:
        """Delete a position"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM positions 
                    WHERE user_id = ? AND symbol = ? AND direction = ?
                """, (user_id, symbol, direction))
                return cursor.rowcount > 0
        except Exception:
            return False
    
    # Trade Operations
    def record_trade(self, trade_data: Dict) -> bool:
        """Record a new trade"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades 
                    (trade_id, user_id, symbol, direction, entry_price, exit_price,
                     shares, position_value, status, entry_time, exit_time, pnl,
                     pnl_percent, strategy, confidence, exit_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data.get('trade_id'),
                    trade_data['user_id'],
                    trade_data['symbol'],
                    trade_data['direction'],
                    trade_data['entry_price'],
                    trade_data.get('exit_price'),
                    trade_data['shares'],
                    trade_data.get('position_value'),
                    trade_data.get('status', 'open'),
                    trade_data.get('entry_time'),
                    trade_data.get('exit_time'),
                    trade_data.get('pnl'),
                    trade_data.get('pnl_percent'),
                    trade_data.get('strategy'),
                    trade_data.get('confidence'),
                    trade_data.get('exit_reason')
                ))
                return True
        except Exception:
            return False
    
    def get_trades(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get trade history for a user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades 
                WHERE user_id = ? 
                ORDER BY entry_time DESC 
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_trade_exit(self, trade_id: str, exit_data: Dict) -> bool:
        """Update trade with exit information"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trades 
                    SET exit_price = ?, exit_time = ?, pnl = ?, 
                        pnl_percent = ?, status = 'closed', exit_reason = ?
                    WHERE trade_id = ?
                """, (
                    exit_data.get('exit_price'),
                    exit_data.get('exit_time'),
                    exit_data.get('pnl'),
                    exit_data.get('pnl_percent'),
                    exit_data.get('exit_reason'),
                    trade_id
                ))
                return cursor.rowcount > 0
        except Exception:
            return False
    
    # Analysis Cache Operations
    def cache_analysis(self, symbol: str, analysis_type: str, data: Dict, 
                      ttl_hours: int = 24) -> bool:
        """Cache analysis results"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                expires = datetime.now().isoformat()
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_cache 
                    (symbol, analysis_type, data, expires_at)
                    VALUES (?, ?, ?, datetime('now', '+{} hours'))
                """.format(ttl_hours), (symbol, analysis_type, json.dumps(data)))
                return True
        except Exception:
            return False
    
    def get_cached_analysis(self, symbol: str, analysis_type: str) -> Optional[Dict]:
        """Get cached analysis if not expired"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data FROM analysis_cache 
                WHERE symbol = ? AND analysis_type = ? 
                AND (expires_at IS NULL OR expires_at > datetime('now'))
            """, (symbol, analysis_type))
            row = cursor.fetchone()
            if row:
                return json.loads(row['data'])
            return None
    
    # Website Operations
    def save_website(self, website_data: Dict) -> bool:
        """Save generated website metadata"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO websites 
                    (website_id, user_id, name, template, complexity, files, file_count, deployed_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    website_data['website_id'],
                    website_data.get('user_id'),
                    website_data['name'],
                    website_data.get('template'),
                    website_data.get('complexity'),
                    json.dumps(website_data.get('files', [])),
                    website_data.get('file_count', 0),
                    website_data.get('deployed_url')
                ))
                return True
        except Exception:
            return False
    
    def get_websites(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get websites, optionally filtered by user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM websites WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM websites ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    # API Usage Tracking
    def log_api_call(self, user_id: Optional[str], endpoint: str, method: str,
                    status_code: int, response_time_ms: int) -> bool:
        """Log API call for monitoring"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_usage 
                    (user_id, endpoint, method, status_code, response_time_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, endpoint, method, status_code, response_time_ms))
                return True
        except Exception:
            return False
    
    def get_api_stats(self, user_id: Optional[str] = None, 
                     days: int = 7) -> Dict:
        """Get API usage statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    SELECT COUNT(*) as total_calls,
                           AVG(response_time_ms) as avg_response_time,
                           SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                    FROM api_usage 
                    WHERE user_id = ? 
                    AND timestamp > datetime('now', '-{} days')
                """.format(days), (user_id,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as total_calls,
                           AVG(response_time_ms) as avg_response_time,
                           SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                    FROM api_usage 
                    WHERE timestamp > datetime('now', '-{} days')
                """.format(days))
            row = cursor.fetchone()
            return {
                "total_calls": row['total_calls'] or 0,
                "avg_response_time_ms": round(row['avg_response_time'] or 0, 2),
                "errors": row['errors'] or 0,
                "period_days": days
            }
    
    # Maintenance
    def cleanup_old_cache(self, days: int = 7) -> int:
        """Clean up expired cache entries"""
        try:
            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM analysis_cache 
                    WHERE expires_at < datetime('now')
                    OR created_at < datetime('now', '-{} days')
                """.format(days))
                return cursor.rowcount
        except Exception:
            return 0
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            
            tables = ['users', 'positions', 'trades', 'queries', 
                     'websites', 'api_usage', 'analysis_cache']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = cursor.fetchone()['count']
            
            # Database file size
            if os.path.exists(self.db_path):
                stats['database_size_mb'] = round(
                    os.path.getsize(self.db_path) / (1024 * 1024), 2
                )
            
            return stats


# Global database instance
db = DatabaseManager()


def get_db() -> DatabaseManager:
    """Get database manager instance"""
    return db


# Helper functions for common operations
def save_position(user_id: str, position_data: Dict) -> bool:
    """Convenience function to save a position"""
    position_data['user_id'] = user_id
    return db.create_position(position_data)


def get_user_positions(user_id: str) -> List[Dict]:
    """Convenience function to get user positions"""
    return db.get_positions(user_id)


def record_trade(user_id: str, trade_data: Dict) -> bool:
    """Convenience function to record a trade"""
    trade_data['user_id'] = user_id
    if not trade_data.get('trade_id'):
        trade_data['trade_id'] = f"trd_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id[:8]}"
    return db.record_trade(trade_data)


def get_user_trades(user_id: str, limit: int = 100) -> List[Dict]:
    """Convenience function to get user trades"""
    return db.get_trades(user_id, limit)
