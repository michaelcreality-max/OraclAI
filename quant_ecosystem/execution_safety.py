"""
Execution Safety Layer
Validates pre-execution requirements and monitors system health.
Provides auto-fallback to safe mode when system becomes unstable.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

log = logging.getLogger(__name__)


class SystemMode(Enum):
    """System operation modes"""
    TRAINING = "training"
    EXECUTION = "execution"
    SAFE = "safe"  # HOLD decisions only


@dataclass
class SafetyCheck:
    """Individual safety check result"""
    name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyStatus:
    """Complete safety status report"""
    system_safe: bool
    execution_allowed: bool
    current_mode: SystemMode
    checks: List[SafetyCheck]
    last_updated: datetime
    anomaly_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "systemSafe": self.system_safe,
            "executionAllowed": self.execution_allowed,
            "currentMode": self.current_mode.value,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "details": c.details
                }
                for c in self.checks
            ],
            "lastUpdated": self.last_updated.isoformat(),
            "anomalyScore": self.anomaly_score,
            "recommendations": self.recommendations
        }


@dataclass
class ModelValidation:
    """Model validation record"""
    model_id: str
    model_name: str
    validated_at: datetime
    validation_score: float
    is_active: bool


@dataclass
class BacktestResult:
    """Backtest completion record"""
    backtest_id: str
    strategy_name: str
    completed_at: datetime
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float


class ExecutionSafetyLayer:
    """
    Validates execution readiness and monitors system health.
    Auto-fallbacks to SAFE mode when anomalies detected.
    """
    
    # Thresholds
    MIN_WIN_RATE = 0.55  # 55% minimum win rate
    MIN_PROFIT_FACTOR = 1.2  # Minimum profit factor
    MAX_DRAWDOWN = 0.20  # 20% max drawdown
    MIN_SHARPE = 0.8  # Minimum Sharpe ratio
    
    ANOMALY_THRESHOLD = 0.7  # Score threshold for safe mode fallback
    HEALTH_CHECK_INTERVAL = 30  # seconds
    
    def __init__(self, db_path: str = "execution_safety.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._current_mode = SystemMode.TRAINING
        self._safety_status: Optional[SafetyStatus] = None
        self._health_history: List[Dict[str, Any]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        self._init_database()
        self._start_health_monitor()
    
    def _init_database(self):
        """Initialize safety database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Model validations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_validations (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    validated_at TEXT NOT NULL,
                    validation_score REAL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Backtest results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_results (
                    backtest_id TEXT PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    win_rate REAL,
                    profit_factor REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL
                )
            ''')
            
            # Safety violations log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS safety_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    description TEXT,
                    severity TEXT
                )
            ''')
            
            # System health log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT,
                    metric_value REAL,
                    anomaly_score REAL
                )
            ''')
            
            conn.commit()
            log.info("Execution safety database initialized")
    
    def record_model_validation(self, model_id: str, model_name: str, 
                                validation_score: float) -> bool:
        """Record a model validation result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO model_validations 
                (model_id, model_name, validated_at, validation_score, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (model_id, model_name, datetime.now().isoformat(), validation_score))
            conn.commit()
        
        log.info(f"Model {model_name} validated with score {validation_score:.2f}")
        return True
    
    def record_backtest(self, backtest_id: str, strategy_name: str,
                       win_rate: float, profit_factor: float,
                       max_drawdown: float, sharpe_ratio: float) -> bool:
        """Record a completed backtest"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO backtest_results
                (backtest_id, strategy_name, completed_at, win_rate, 
                 profit_factor, max_drawdown, sharpe_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (backtest_id, strategy_name, datetime.now().isoformat(),
                  win_rate, profit_factor, max_drawdown, sharpe_ratio))
            conn.commit()
        
        log.info(f"Backtest recorded for {strategy_name}: WR={win_rate:.2%}, "
                f"PF={profit_factor:.2f}, DD={max_drawdown:.2%}")
        return True
    
    def _get_recent_validations(self, days: int = 30) -> List[ModelValidation]:
        """Get recent model validations"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT model_id, model_name, validated_at, validation_score, is_active
                FROM model_validations
                WHERE validated_at > ? AND is_active = 1
                ORDER BY validated_at DESC
            ''', (cutoff,))
            
            return [
                ModelValidation(
                    model_id=row[0],
                    model_name=row[1],
                    validated_at=datetime.fromisoformat(row[2]),
                    validation_score=row[3],
                    is_active=bool(row[4])
                )
                for row in cursor.fetchall()
            ]
    
    def _get_recent_backtests(self, days: int = 30) -> List[BacktestResult]:
        """Get recent backtest results"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT backtest_id, strategy_name, completed_at, win_rate,
                       profit_factor, max_drawdown, sharpe_ratio
                FROM backtest_results
                WHERE completed_at > ?
                ORDER BY completed_at DESC
            ''', (cutoff,))
            
            return [
                BacktestResult(
                    backtest_id=row[0],
                    strategy_name=row[1],
                    completed_at=datetime.fromisoformat(row[2]),
                    win_rate=row[3],
                    profit_factor=row[4],
                    max_drawdown=row[5],
                    sharpe_ratio=row[6]
                )
                for row in cursor.fetchall()
            ]
    
    def validate_execution_readiness(self) -> SafetyStatus:
        """
        Validate all pre-execution requirements.
        Returns comprehensive safety status.
        """
        checks: List[SafetyCheck] = []
        
        # Check 1: Models validated
        validations = self._get_recent_validations(days=30)
        has_valid_models = len(validations) > 0
        avg_validation_score = (
            sum(v.validation_score for v in validations) / len(validations)
            if validations else 0
        )
        
        checks.append(SafetyCheck(
            name="Models Validated",
            passed=has_valid_models,
            message=f"{len(validations)} active models, avg score: {avg_validation_score:.2f}",
            details={"modelCount": len(validations), "avgScore": avg_validation_score}
        ))
        
        # Check 2: Backtests completed
        backtests = self._get_recent_backtests(days=30)
        has_backtests = len(backtests) > 0
        
        checks.append(SafetyCheck(
            name="Backtests Completed",
            passed=has_backtests,
            message=f"{len(backtests)} backtests completed in last 30 days",
            details={"backtestCount": len(backtests)}
        ))
        
        # Check 3: Performance thresholds
        if backtests:
            avg_win_rate = sum(b.win_rate for b in backtests) / len(backtests)
            avg_profit_factor = sum(b.profit_factor for b in backtests) / len(backtests)
            avg_drawdown = sum(b.max_drawdown for b in backtests) / len(backtests)
            avg_sharpe = sum(b.sharpe_ratio for b in backtests) / len(backtests)
            
            performance_passed = (
                avg_win_rate >= self.MIN_WIN_RATE and
                avg_profit_factor >= self.MIN_PROFIT_FACTOR and
                avg_drawdown <= self.MAX_DRAWDOWN and
                avg_sharpe >= self.MIN_SHARPE
            )
            
            details = {
                "winRate": avg_win_rate,
                "profitFactor": avg_profit_factor,
                "maxDrawdown": avg_drawdown,
                "sharpeRatio": avg_sharpe,
                "thresholds": {
                    "minWinRate": self.MIN_WIN_RATE,
                    "minProfitFactor": self.MIN_PROFIT_FACTOR,
                    "maxDrawdown": self.MAX_DRAWDOWN,
                    "minSharpe": self.MIN_SHARPE
                }
            }
        else:
            performance_passed = False
            details = {"reason": "No backtest data available"}
        
        checks.append(SafetyCheck(
            name="Performance Thresholds",
            passed=performance_passed,
            message="All performance metrics within acceptable ranges" if performance_passed 
                   else "Performance metrics below thresholds",
            details=details
        ))
        
        # Check 4: System health (anomaly detection)
        anomaly_score = self._calculate_anomaly_score()
        health_passed = anomaly_score < self.ANOMALY_THRESHOLD
        
        checks.append(SafetyCheck(
            name="System Health",
            passed=health_passed,
            message=f"Anomaly score: {anomaly_score:.2f} (threshold: {self.ANOMALY_THRESHOLD})",
            details={"anomalyScore": anomaly_score, "threshold": self.ANOMALY_THRESHOLD}
        ))
        
        # Determine overall safety
        all_passed = all(c.passed for c in checks)
        
        # Generate recommendations
        recommendations = []
        if not has_valid_models:
            recommendations.append("Validate at least one model before execution")
        if not has_backtests:
            recommendations.append("Run backtests to verify strategy performance")
        if backtests and not performance_passed:
            recommendations.append("Improve strategy performance to meet thresholds")
        if not health_passed:
            recommendations.append("Investigate system anomalies before proceeding")
        
        status = SafetyStatus(
            system_safe=health_passed,
            execution_allowed=all_passed,
            current_mode=self._current_mode,
            checks=checks,
            last_updated=datetime.now(),
            anomaly_score=anomaly_score,
            recommendations=recommendations
        )
        
        self._safety_status = status
        return status
    
    def _calculate_anomaly_score(self) -> float:
        """Calculate current anomaly score based on health history"""
        with self.lock:
            if len(self._health_history) < 5:
                return 0.0
            
            # Simple anomaly detection: variance in recent health metrics
            recent = self._health_history[-10:]
            if len(recent) < 5:
                return 0.0
            
            # Calculate variance in response times and error rates
            response_times = [h.get("response_time", 0) for h in recent if "response_time" in h]
            error_rates = [h.get("error_rate", 0) for h in recent if "error_rate" in h]
            
            score = 0.0
            
            if response_times:
                avg_rt = sum(response_times) / len(response_times)
                variance = sum((rt - avg_rt) ** 2 for rt in response_times) / len(response_times)
                # High variance = potential instability
                score += min(variance / 1000, 0.5)  # Cap at 0.5
            
            if error_rates:
                avg_er = sum(error_rates) / len(error_rates)
                score += avg_er * 2  # Error rate contributes directly
            
            return min(score, 1.0)  # Cap at 1.0
    
    def _start_health_monitor(self):
        """Start background health monitoring thread"""
        def monitor():
            while not self._stop_monitoring.wait(self.HEALTH_CHECK_INTERVAL):
                self._perform_health_check()
        
        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
        log.info("Health monitoring started")
    
    def _perform_health_check(self):
        """Perform periodic health check"""
        try:
            # Collect health metrics
            health_entry = {
                "timestamp": time.time(),
                "response_time": self._measure_response_time(),
                "memory_usage": self._get_memory_usage(),
                "active_sessions": self._get_active_sessions()
            }
            
            with self.lock:
                self._health_history.append(health_entry)
                # Keep only last 100 entries
                if len(self._health_history) > 100:
                    self._health_history = self._health_history[-100:]
            
            # Log to database
            anomaly_score = self._calculate_anomaly_score()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for metric, value in health_entry.items():
                    if isinstance(value, (int, float)) and metric != "timestamp":
                        cursor.execute('''
                            INSERT INTO health_logs (timestamp, metric_name, metric_value, anomaly_score)
                            VALUES (?, ?, ?, ?)
                        ''', (datetime.now().isoformat(), metric, value, anomaly_score))
                conn.commit()
            
            # Auto-fallback check
            if anomaly_score >= self.ANOMALY_THRESHOLD and self._current_mode == SystemMode.EXECUTION:
                log.warning(f"High anomaly score ({anomaly_score:.2f}) detected, triggering safe mode fallback")
                self.trigger_safe_mode("Anomaly threshold exceeded")
                
        except Exception as e:
            log.error(f"Health check failed: {e}")
    
    def _measure_response_time(self) -> float:
        """Measure system response time"""
        start = time.time()
        # Simple self-check - could be expanded
        time.sleep(0.001)  # Minimal operation
        return (time.time() - start) * 1000  # ms
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
    
    def _get_active_sessions(self) -> int:
        """Get number of active sessions"""
        try:
            from quant_ecosystem.multi_agent_orchestrator import orchestrator
            return len(orchestrator.active_sessions)
        except:
            return 0
    
    def get_current_mode(self) -> SystemMode:
        """Get current system mode"""
        return self._current_mode
    
    def set_mode(self, mode: SystemMode) -> Tuple[bool, str]:
        """
        Attempt to set system mode.
        Validates safety before allowing execution mode.
        """
        with self.lock:
            # Validate before switching to execution
            if mode == SystemMode.EXECUTION:
                status = self.validate_execution_readiness()
                if not status.execution_allowed:
                    return False, f"Execution not allowed: {status.recommendations[0] if status.recommendations else 'Safety checks failed'}"
            
            old_mode = self._current_mode
            self._current_mode = mode
            
            log.info(f"System mode changed: {old_mode.value} -> {mode.value}")
            return True, f"Mode switched to {mode.value}"
    
    def trigger_safe_mode(self, reason: str):
        """Trigger automatic fallback to safe mode"""
        with self.lock:
            old_mode = self._current_mode
            self._current_mode = SystemMode.SAFE
            
            # Log the violation
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO safety_violations (timestamp, violation_type, description, severity)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.now().isoformat(), "AUTO_SAFE_MODE", reason, "HIGH"))
                conn.commit()
            
            log.warning(f"AUTO-FALLBACK: System switched to SAFE MODE from {old_mode.value}. Reason: {reason}")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status for API response"""
        status = self.validate_execution_readiness()
        return {
            "systemSafe": status.system_safe,
            "executionAllowed": status.execution_allowed,
            "currentMode": status.current_mode.value,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message
                }
                for c in status.checks
            ],
            "recommendations": status.recommendations,
            "lastUpdated": status.last_updated.isoformat()
        }
    
    def stop(self):
        """Stop health monitoring"""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)


# Global instance
execution_safety = ExecutionSafetyLayer()
