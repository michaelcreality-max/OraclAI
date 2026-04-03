"""
OraclAI Production Hardening System
Real-time monitoring, auto-scaling, failover, rate limiting, resource management
"""

import sqlite3
import json
import time
import threading
import psutil
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import shutil
import gzip


# ==================== REAL-TIME MONITORING DASHBOARD ====================

@dataclass
class SystemMetrics:
    """Real-time system metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_threads: int
    api_requests_per_minute: int
    training_operations_active: int
    database_size_mb: float
    response_time_ms: float
    error_rate: float


class RealTimeMonitor:
    """
    Real-time monitoring system for AI operations
    Tracks performance, resources, and health
    """
    
    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path
        self.metrics_history: deque = deque(maxlen=10000)
        self.alert_thresholds = {
            'cpu_percent': 85.0,
            'memory_percent': 90.0,
            'disk_usage_percent': 95.0,
            'response_time_ms': 5000.0,
            'error_rate': 0.1
        }
        self.active_alerts: List[Dict] = []
        self.monitoring_active = False
        self.monitor_thread = None
        self._init_database()
    
    def _init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_usage_percent REAL,
                active_threads INTEGER,
                api_requests_per_minute INTEGER,
                training_operations_active INTEGER,
                database_size_mb REAL,
                response_time_ms REAL,
                error_rate REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                metric_value REAL,
                threshold REAL,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring in background thread"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, 
                                                  args=(interval_seconds,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                self._check_alerts(metrics)
                time.sleep(interval)
            except Exception as e:
                print(f"[Monitor] Error: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU and memory
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        # Thread count
        threads = threading.active_count()
        
        # Database sizes
        db_size = self._get_database_sizes()
        
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu,
            memory_percent=memory,
            disk_usage_percent=disk,
            active_threads=threads,
            api_requests_per_minute=self._get_api_request_rate(),
            training_operations_active=self._get_active_training_ops(),
            database_size_mb=db_size,
            response_time_ms=self._get_avg_response_time(),
            error_rate=self._get_error_rate()
        )
    
    def _get_database_sizes(self) -> float:
        """Get total database size in MB"""
        total = 0
        db_files = ['ai_training.db', 'ai_memory.db', 'orchestration_training.db', 'monitoring.db']
        for db_file in db_files:
            if os.path.exists(db_file):
                total += os.path.getsize(db_file) / (1024 * 1024)
        return total
    
    def _get_api_request_rate(self) -> int:
        """Get API requests per minute"""
        # Placeholder - would integrate with actual request tracking
        return random.randint(50, 500)
    
    def _get_active_training_ops(self) -> int:
        """Get number of active training operations"""
        # Placeholder
        return random.randint(0, 10)
    
    def _get_avg_response_time(self) -> float:
        """Get average API response time"""
        # Placeholder
        return random.uniform(100, 2000)
    
    def _get_error_rate(self) -> float:
        """Get error rate"""
        # Placeholder
        return random.uniform(0.001, 0.05)
    
    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_metrics
            (timestamp, cpu_percent, memory_percent, disk_usage_percent,
             active_threads, api_requests_per_minute, training_operations_active,
             database_size_mb, response_time_ms, error_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
            metrics.disk_usage_percent, metrics.active_threads,
            metrics.api_requests_per_minute, metrics.training_operations_active,
            metrics.database_size_mb, metrics.response_time_ms, metrics.error_rate
        ))
        
        conn.commit()
        conn.close()
        
        # Keep in memory
        self.metrics_history.append(metrics)
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Check for alert conditions"""
        alerts_triggered = []
        
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts_triggered.append({
                'type': 'high_cpu',
                'severity': 'warning' if metrics.cpu_percent < 95 else 'critical',
                'message': f'CPU usage at {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent']
            })
        
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts_triggered.append({
                'type': 'high_memory',
                'severity': 'warning' if metrics.memory_percent < 95 else 'critical',
                'message': f'Memory usage at {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': self.alert_thresholds['memory_percent']
            })
        
        if metrics.response_time_ms > self.alert_thresholds['response_time_ms']:
            alerts_triggered.append({
                'type': 'slow_response',
                'severity': 'warning',
                'message': f'Average response time {metrics.response_time_ms:.0f}ms',
                'value': metrics.response_time_ms,
                'threshold': self.alert_thresholds['response_time_ms']
            })
        
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            alerts_triggered.append({
                'type': 'high_error_rate',
                'severity': 'critical',
                'message': f'Error rate at {metrics.error_rate:.2%}',
                'value': metrics.error_rate,
                'threshold': self.alert_thresholds['error_rate']
            })
        
        for alert in alerts_triggered:
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Dict):
        """Trigger and store alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts
            (timestamp, alert_type, severity, message, metric_value, threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            alert['type'],
            alert['severity'],
            alert['message'],
            alert['value'],
            alert['threshold']
        ))
        
        conn.commit()
        conn.close()
        
        self.active_alerts.append(alert)
        print(f"[ALERT] {alert['severity'].upper()}: {alert['message']}")
    
    def get_dashboard_data(self) -> Dict:
        """Get data for monitoring dashboard"""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        latest = self.metrics_history[-1]
        
        # Calculate trends
        cpu_trend = self._calculate_trend('cpu_percent')
        memory_trend = self._calculate_trend('memory_percent')
        response_trend = self._calculate_trend('response_time_ms')
        
        return {
            'current_metrics': {
                'cpu_percent': round(latest.cpu_percent, 1),
                'memory_percent': round(latest.memory_percent, 1),
                'disk_usage_percent': round(latest.disk_usage_percent, 1),
                'api_requests_per_minute': latest.api_requests_per_minute,
                'active_training_ops': latest.training_operations_active,
                'database_size_mb': round(latest.database_size_mb, 2),
                'response_time_ms': round(latest.response_time_ms, 0),
                'error_rate': round(latest.error_rate, 4)
            },
            'trends': {
                'cpu': cpu_trend,
                'memory': memory_trend,
                'response_time': response_trend
            },
            'active_alerts': len(self.active_alerts),
            'alerts': self.active_alerts[-5:],
            'system_health': self._assess_health(latest),
            'last_updated': latest.timestamp
        }
    
    def _calculate_trend(self, metric_name: str) -> str:
        """Calculate trend direction for a metric"""
        if len(self.metrics_history) < 10:
            return 'stable'
        
        recent = [getattr(m, metric_name) for m in list(self.metrics_history)[-10:]]
        older = [getattr(m, metric_name) for m in list(self.metrics_history)[-20:-10]]
        
        if not older:
            return 'stable'
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        threshold = older_avg * 0.1
        
        if diff > threshold:
            return 'increasing'
        elif diff < -threshold:
            return 'decreasing'
        return 'stable'
    
    def _assess_health(self, metrics: SystemMetrics) -> str:
        """Assess overall system health"""
        critical_count = sum(1 for a in self.active_alerts if a['severity'] == 'critical')
        warning_count = sum(1 for a in self.active_alerts if a['severity'] == 'warning')
        
        if critical_count > 0:
            return 'critical'
        elif warning_count > 2:
            return 'degraded'
        elif warning_count > 0:
            return 'warning'
        return 'healthy'


# ==================== AUTO-SCALING SYSTEM ====================

class AutoScaler:
    """
    Automatically scales agent resources based on query load
    """
    
    def __init__(self):
        self.min_agents = 2
        self.max_agents = 20
        self.current_agents = 4
        self.scale_up_threshold = 100  # requests per minute
        self.scale_down_threshold = 20
        self.cooldown_minutes = 5
        self.last_scale_time = datetime.now() - timedelta(hours=1)
        self.scale_history: List[Dict] = []
    
    def evaluate_scaling(self, current_load: int) -> Dict:
        """Evaluate if scaling is needed"""
        now = datetime.now()
        cooldown_elapsed = (now - self.last_scale_time).total_seconds() / 60
        
        if cooldown_elapsed < self.cooldown_minutes:
            return {'action': 'none', 'reason': 'cooldown_active'}
        
        # Calculate desired agents
        agents_per_unit_load = 0.04  # 1 agent per 25 requests/min
        desired_agents = int(current_load * agents_per_unit_load)
        desired_agents = max(self.min_agents, min(self.max_agents, desired_agents))
        
        if desired_agents > self.current_agents:
            return self._scale_up(desired_agents, current_load)
        elif desired_agents < self.current_agents:
            return self._scale_down(desired_agents, current_load)
        
        return {'action': 'none', 'reason': 'optimal_capacity'}
    
    def _scale_up(self, target: int, load: int) -> Dict:
        """Scale up agent capacity"""
        old_count = self.current_agents
        self.current_agents = target
        self.last_scale_time = datetime.now()
        
        scale_record = {
            'timestamp': datetime.now().isoformat(),
            'action': 'scale_up',
            'from_count': old_count,
            'to_count': target,
            'trigger_load': load,
            'reason': f'High load ({load} req/min)'
        }
        self.scale_history.append(scale_record)
        
        return {
            'action': 'scale_up',
            'from': old_count,
            'to': target,
            'reason': f'Load at {load} req/min exceeds capacity'
        }
    
    def _scale_down(self, target: int, load: int) -> Dict:
        """Scale down agent capacity"""
        old_count = self.current_agents
        self.current_agents = target
        self.last_scale_time = datetime.now()
        
        scale_record = {
            'timestamp': datetime.now().isoformat(),
            'action': 'scale_down',
            'from_count': old_count,
            'to_count': target,
            'trigger_load': load,
            'reason': f'Low load ({load} req/min)'
        }
        self.scale_history.append(scale_record)
        
        return {
            'action': 'scale_down',
            'from': old_count,
            'to': target,
            'reason': f'Load at {load} req/min, excess capacity'
        }
    
    def get_scaling_stats(self) -> Dict:
        """Get auto-scaling statistics"""
        return {
            'current_agents': self.current_agents,
            'min_agents': self.min_agents,
            'max_agents': self.max_agents,
            'scale_history': self.scale_history[-10:],
            'total_scale_events': len(self.scale_history),
            'last_scale': self.last_scale_time.isoformat()
        }


# ==================== FAILOVER & RECOVERY ====================

class FailoverManager:
    """
    Manages failover and recovery for training data
    """
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self.databases = [
            'ai_training.db',
            'ai_memory.db',
            'orchestration_training.db',
            'monitoring.db'
        ]
        os.makedirs(backup_dir, exist_ok=True)
        self.last_backup = None
        self.backup_history: List[Dict] = []
    
    def create_backup(self, compress: bool = True) -> Dict:
        """Create backup of all databases"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
        os.makedirs(backup_path, exist_ok=True)
        
        backed_up = []
        failed = []
        
        for db_file in self.databases:
            if os.path.exists(db_file):
                try:
                    if compress:
                        # Compress with gzip
                        dest = os.path.join(backup_path, f"{db_file}.gz")
                        with open(db_file, 'rb') as f_in:
                            with gzip.open(dest, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    else:
                        # Plain copy
                        dest = os.path.join(backup_path, db_file)
                        shutil.copy2(db_file, dest)
                    backed_up.append(db_file)
                except Exception as e:
                    failed.append({'file': db_file, 'error': str(e)})
        
        backup_info = {
            'timestamp': timestamp,
            'path': backup_path,
            'backed_up': backed_up,
            'failed': failed,
            'compressed': compress
        }
        
        self.backup_history.append(backup_info)
        self.last_backup = timestamp
        
        return backup_info
    
    def restore_backup(self, timestamp: str) -> Dict:
        """Restore from backup"""
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': f'Backup {timestamp} not found'}
        
        restored = []
        failed = []
        
        for db_file in self.databases:
            compressed_path = os.path.join(backup_path, f"{db_file}.gz")
            plain_path = os.path.join(backup_path, db_file)
            
            try:
                if os.path.exists(compressed_path):
                    # Decompress
                    with gzip.open(compressed_path, 'rb') as f_in:
                        with open(db_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    restored.append(db_file)
                elif os.path.exists(plain_path):
                    shutil.copy2(plain_path, db_file)
                    restored.append(db_file)
            except Exception as e:
                failed.append({'file': db_file, 'error': str(e)})
        
        return {
            'success': len(failed) == 0,
            'restored': restored,
            'failed': failed,
            'timestamp': timestamp
        }
    
    def check_database_integrity(self) -> Dict:
        """Check integrity of all databases"""
        results = {}
        
        for db_file in self.databases:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()
                    conn.close()
                    
                    results[db_file] = {
                        'status': 'healthy' if result[0] == 'ok' else 'corrupted',
                        'integrity': result[0]
                    }
                except Exception as e:
                    results[db_file] = {'status': 'error', 'error': str(e)}
            else:
                results[db_file] = {'status': 'missing'}
        
        return results
    
    def auto_recover(self) -> Dict:
        """Automatically recover from corruption"""
        integrity = self.check_database_integrity()
        corrupted = [db for db, info in integrity.items() if info['status'] == 'corrupted']
        
        if not corrupted:
            return {'action': 'none', 'reason': 'all_databases_healthy'}
        
        # Find most recent backup
        if not self.backup_history:
            return {'action': 'failed', 'reason': 'no_backups_available'}
        
        latest_backup = self.backup_history[-1]['timestamp']
        restore_result = self.restore_backup(latest_backup)
        
        return {
            'action': 'auto_recover',
            'corrupted_databases': corrupted,
            'restored_from': latest_backup,
            'restore_result': restore_result
        }


# ==================== RATE LIMITING ====================

class RateLimiter:
    """
    Rate limiting for training APIs to prevent abuse
    """
    
    def __init__(self):
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.limits = {
            'training_api': {'requests_per_minute': 60, 'requests_per_hour': 500},
            'inference_api': {'requests_per_minute': 120, 'requests_per_hour': 2000},
            'orchestration_api': {'requests_per_minute': 30, 'requests_per_hour': 200}
        }
        self.blocked_ips: Dict[str, datetime] = {}
    
    def is_allowed(self, client_id: str, api_type: str = 'training_api') -> Tuple[bool, Dict]:
        """Check if request is allowed"""
        now = datetime.now()
        
        # Check if blocked
        if client_id in self.blocked_ips:
            block_expires = self.blocked_ips[client_id]
            if now < block_expires:
                return False, {
                    'allowed': False,
                    'reason': 'temporarily_blocked',
                    'block_expires': block_expires.isoformat()
                }
            else:
                del self.blocked_ips[client_id]
        
        # Get limits
        limits = self.limits.get(api_type, self.limits['training_api'])
        
        # Clean old requests
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_hour = now - timedelta(hours=1)
        
        minute_count = 0
        hour_count = 0
        
        for timestamp in list(self.request_counts[client_id]):
            if timestamp > cutoff_minute:
                minute_count += 1
            if timestamp > cutoff_hour:
                hour_count += 1
        
        # Check limits
        if minute_count >= limits['requests_per_minute']:
            self._block_client(client_id, 5)  # Block for 5 minutes
            return False, {
                'allowed': False,
                'reason': 'rate_limit_exceeded',
                'limit': limits['requests_per_minute'],
                'window': 'per_minute',
                'retry_after_seconds': 300
            }
        
        if hour_count >= limits['requests_per_hour']:
            self._block_client(client_id, 60)  # Block for 1 hour
            return False, {
                'allowed': False,
                'reason': 'hourly_limit_exceeded',
                'limit': limits['requests_per_hour'],
                'window': 'per_hour',
                'retry_after_seconds': 3600
            }
        
        # Record request
        self.request_counts[client_id].append(now)
        
        return True, {
            'allowed': True,
            'remaining_minute': limits['requests_per_minute'] - minute_count - 1,
            'remaining_hour': limits['requests_per_hour'] - hour_count - 1
        }
    
    def _block_client(self, client_id: str, minutes: int):
        """Temporarily block a client"""
        self.blocked_ips[client_id] = datetime.now() + timedelta(minutes=minutes)


# ==================== RESOURCE CAPS ====================

class ResourceManager:
    """
    Manages resource usage caps to prevent runaway training
    """
    
    def __init__(self):
        self.caps = {
            'max_training_iterations_per_hour': 10000,
            'max_database_size_mb': 1024,  # 1 GB
            'max_memory_usage_percent': 85,
            'max_cpu_usage_percent': 90,
            'max_concurrent_training_sessions': 5
        }
        self.usage_history: Dict[str, deque] = {
            'training_iterations': deque(maxlen=1000),
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100)
        }
        self.training_sessions_active = 0
        self.emergency_stop = False
    
    def check_resource_available(self, operation_type: str, 
                                  requested_amount: int = 1) -> Tuple[bool, Dict]:
        """Check if resources are available for operation"""
        if self.emergency_stop:
            return False, {'allowed': False, 'reason': 'emergency_stop_active'}
        
        if operation_type == 'training_iteration':
            recent_count = len([t for t in self.usage_history['training_iterations'] 
                              if t > datetime.now() - timedelta(hours=1)])
            if recent_count >= self.caps['max_training_iterations_per_hour']:
                return False, {
                    'allowed': False,
                    'reason': 'hourly_training_cap_reached',
                    'cap': self.caps['max_training_iterations_per_hour'],
                    'used': recent_count
                }
        
        elif operation_type == 'training_session':
            if self.training_sessions_active >= self.caps['max_concurrent_training_sessions']:
                return False, {
                    'allowed': False,
                    'reason': 'max_concurrent_sessions_reached',
                    'cap': self.caps['max_concurrent_training_sessions'],
                    'active': self.training_sessions_active
                }
        
        return True, {'allowed': True}
    
    def record_usage(self, operation_type: str, amount: int = 1):
        """Record resource usage"""
        now = datetime.now()
        
        if operation_type == 'training_iteration':
            for _ in range(amount):
                self.usage_history['training_iterations'].append(now)
        
        elif operation_type == 'training_session_start':
            self.training_sessions_active += 1
        
        elif operation_type == 'training_session_end':
            self.training_sessions_active = max(0, self.training_sessions_active - 1)
        
        # Check for emergency conditions
        self._check_emergency_conditions()
    
    def _check_emergency_conditions(self):
        """Check if emergency stop should be activated"""
        # Memory check
        memory = psutil.virtual_memory().percent
        if memory > self.caps['max_memory_usage_percent']:
            self.emergency_stop = True
            print(f"[EMERGENCY] High memory usage ({memory}%). Stopping operations.")
            return
        
        # CPU check
        cpu = psutil.cpu_percent(interval=1)
        if cpu > self.caps['max_cpu_usage_percent']:
            self.emergency_stop = True
            print(f"[EMERGENCY] High CPU usage ({cpu}%). Stopping operations.")
            return
        
        # Database size check
        total_size = 0
        for db_file in ['ai_training.db', 'ai_memory.db', 'orchestration_training.db']:
            if os.path.exists(db_file):
                total_size += os.path.getsize(db_file) / (1024 * 1024)
        
        if total_size > self.caps['max_database_size_mb']:
            self.emergency_stop = True
            print(f"[EMERGENCY] Database size exceeded ({total_size:.0f} MB). Stopping operations.")


# Global instances
monitor = RealTimeMonitor()
autoscaler = AutoScaler()
failover = FailoverManager()
rate_limiter = RateLimiter()
resource_manager = ResourceManager()
