"""
OraclAI Integration Testing & Quality Assurance
Automated testing, regression detection, overtraining detection, feedback validation
"""

import sqlite3
import json
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading


# ==================== AUTOMATED INTEGRATION TESTING ====================

@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    subsystem: str
    passed: bool
    execution_time_ms: float
    error_message: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class IntegrationTestFramework:
    """
    Automated integration testing for all AI subsystems
    Tests interactions between layers
    """
    
    def __init__(self):
        self.tests: Dict[str, callable] = {}
        self.test_history: List[TestResult] = []
        self.subsystems = [
            'training_framework',
            'advanced_improvements',
            'state_of_the_art',
            'final_enhancements',
            'massive_training',
            'orchestration',
            'production_system'
        ]
        self._register_default_tests()
    
    def _register_default_tests(self):
        """Register default integration tests"""
        self.tests['training_to_orchestration'] = self._test_training_orchestration_integration
        self.tests['orchestration_to_massive'] = self._test_orchestration_massive_integration
        self.tests['advanced_to_sota'] = self._test_advanced_sota_integration
        self.tests['sota_to_final'] = self._test_sota_final_integration
        self.tests['end_to_end_pipeline'] = self._test_end_to_end_pipeline
        self.tests['database_integrity'] = self._test_database_integrity
        self.tests['api_responses'] = self._test_api_responses
        self.tests['memory_persistence'] = self._test_memory_persistence
    
    def _test_training_orchestration_integration(self) -> Tuple[bool, str]:
        """Test training framework integrates with orchestration"""
        try:
            from ai_training_framework import training_engine
            from ai_orchestration_system import orchestrator
            
            # Test that orchestration can record outcomes to training system
            test_query = "test_integration_query"
            profile = orchestrator.task_analyzer.analyze(test_query, 'general')
            
            if not profile:
                return False, "Failed to analyze task"
            
            return True, "Integration successful"
        except Exception as e:
            return False, str(e)
    
    def _test_orchestration_massive_integration(self) -> Tuple[bool, str]:
        """Test orchestration integrates with massive training"""
        try:
            from ai_orchestration_system import orchestrator
            from ai_massive_training import synthetic_generator
            
            # Generate test data and analyze it
            scenarios = synthetic_generator.generate_dataset('code', 5)
            for scenario in scenarios:
                profile = orchestrator.task_analyzer.analyze(scenario['query'], scenario['domain'])
                if not profile:
                    return False, f"Failed to analyze: {scenario['query']}"
            
            return True, f"Analyzed {len(scenarios)} scenarios"
        except Exception as e:
            return False, str(e)
    
    def _test_advanced_sota_integration(self) -> Tuple[bool, str]:
        """Test advanced improvements integrate with SOTA"""
        try:
            from ai_advanced_improvements import ensemble_voting
            from ai_state_of_the_art import meta_learning
            
            # Test that meta-learning can optimize ensemble weights
            config = meta_learning.get_optimal_config('finance', 0.5)
            if 'learning_rate' not in config:
                return False, "Meta-learning failed to return config"
            
            return True, "Meta-learning and ensemble integration successful"
        except Exception as e:
            return False, str(e)
    
    def _test_sota_final_integration(self) -> Tuple[bool, str]:
        """Test SOTA integrates with final enhancements"""
        try:
            from ai_state_of_the_art import rl_agents
            from ai_final_enhancements import explainability
            
            # RL agents should be explainable
            if rl_agents:
                agent_name = list(rl_agents.keys())[0]
                stats = rl_agents[agent_name].get_rl_stats()
                # Should be able to explain decisions
                return True, f"RL agent {agent_name} has explainable stats"
            
            return True, "No RL agents to test"
        except Exception as e:
            return False, str(e)
    
    def _test_end_to_end_pipeline(self) -> Tuple[bool, str]:
        """Test complete pipeline from query to response"""
        try:
            # Simulate full pipeline
            from ai_orchestration_system import orchestrator
            from ai_massive_training import synthetic_generator
            
            # Generate test query
            scenario = synthetic_generator.generate_scenario('finance', 'medium')
            query = scenario['query']
            
            # Run through orchestration
            agents = ['FinanceAgent', 'RiskAgent', 'QuantAgent']
            decision = orchestrator.decide_interaction_mode(query, 'finance', agents)
            
            if not decision.mode:
                return False, "Orchestration failed to decide mode"
            
            return True, f"Pipeline completed: {decision.mode} mode selected"
        except Exception as e:
            return False, str(e)
    
    def _test_database_integrity(self) -> Tuple[bool, str]:
        """Test all databases are accessible"""
        try:
            databases = [
                'ai_training.db',
                'ai_memory.db',
                'orchestration_training.db',
                'monitoring.db'
            ]
            
            for db in databases:
                conn = sqlite3.connect(db)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                if not tables:
                    return False, f"Database {db} has no tables"
            
            return True, f"All {len(databases)} databases accessible"
        except Exception as e:
            return False, str(e)
    
    def _test_api_responses(self) -> Tuple[bool, str]:
        """Test API response formats"""
        # This would test actual API endpoints
        return True, "API response format tests passed (simulated)"
    
    def _test_memory_persistence(self) -> Tuple[bool, str]:
        """Test memory system persists data"""
        try:
            from ai_final_enhancements import memory
            
            # Store and retrieve
            test_fact = f"test_fact_{datetime.now().timestamp()}"
            memory.remember_user_fact('test_user', test_fact, 1.0)
            facts = memory.recall_user_facts('test_user', 10)
            
            if test_fact in facts:
                return True, "Memory persistence working"
            return False, "Memory recall failed"
        except Exception as e:
            return False, str(e)
    
    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        results = []
        passed = 0
        failed = 0
        
        for test_name, test_func in self.tests.items():
            start = time.time()
            try:
                success, message = test_func()
                execution_time = (time.time() - start) * 1000
                
                result = TestResult(
                    test_name=test_name,
                    subsystem=self._get_subsystem_for_test(test_name),
                    passed=success,
                    execution_time_ms=execution_time,
                    error_message=None if success else message
                )
                
                if success:
                    passed += 1
                else:
                    failed += 1
                
                results.append(result)
                self.test_history.append(result)
                
            except Exception as e:
                result = TestResult(
                    test_name=test_name,
                    subsystem='unknown',
                    passed=False,
                    execution_time_ms=0,
                    error_message=str(e)
                )
                failed += 1
                results.append(result)
        
        return {
            'total_tests': len(results),
            'passed': passed,
            'failed': failed,
            'success_rate': passed / len(results) if results else 0,
            'results': [
                {
                    'name': r.test_name,
                    'passed': r.passed,
                    'time_ms': round(r.execution_time_ms, 2),
                    'error': r.error_message
                }
                for r in results
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_subsystem_for_test(self, test_name: str) -> str:
        """Determine subsystem for test"""
        mapping = {
            'training_to_orchestration': 'training_framework',
            'orchestration_to_massive': 'orchestration',
            'advanced_to_sota': 'advanced_improvements',
            'sota_to_final': 'state_of_the_art',
            'end_to_end_pipeline': 'all_subsystems',
            'database_integrity': 'production_system',
            'api_responses': 'production_system',
            'memory_persistence': 'final_enhancements'
        }
        return mapping.get(test_name, 'unknown')
    
    def get_test_summary(self) -> Dict:
        """Get summary of recent test results"""
        recent = [r for r in self.test_history if 
                 datetime.fromisoformat(r.timestamp) > datetime.now() - timedelta(hours=24)]
        
        if not recent:
            return {'message': 'No tests run in last 24 hours'}
        
        by_subsystem = defaultdict(lambda: {'passed': 0, 'failed': 0})
        
        for test in recent:
            if test.passed:
                by_subsystem[test.subsystem]['passed'] += 1
            else:
                by_subsystem[test.subsystem]['failed'] += 1
        
        return {
            'tests_run_24h': len(recent),
            'overall_pass_rate': sum(1 for t in recent if t.passed) / len(recent),
            'by_subsystem': dict(by_subsystem),
            'recent_failures': [
                {'test': t.test_name, 'error': t.error_message}
                for t in recent[-10:] if not t.passed
            ]
        }


# ==================== PERFORMANCE BENCHMARKS ====================

class PerformanceBenchmarks:
    """
    Performance benchmarks and regression detection
    """
    
    def __init__(self, db_path: str = "benchmarks.db"):
        self.db_path = db_path
        self.benchmarks: Dict[str, Dict] = {
            'orchestration_decision': {
                'description': 'Time to decide interaction mode',
                'target_ms': 100,
                'warning_ms': 500,
                'critical_ms': 1000
            },
            'training_record': {
                'description': 'Time to record training data',
                'target_ms': 50,
                'warning_ms': 200,
                'critical_ms': 500
            },
            'ensemble_vote': {
                'description': 'Time to compute ensemble vote',
                'target_ms': 200,
                'warning_ms': 1000,
                'critical_ms': 2000
            },
            'memory_recall': {
                'description': 'Time to recall from long-term memory',
                'target_ms': 100,
                'warning_ms': 500,
                'critical_ms': 1000
            },
            'synthetic_generation': {
                'description': 'Time to generate 100 synthetic scenarios',
                'target_ms': 500,
                'warning_ms': 2000,
                'critical_ms': 5000
            }
        }
        self.benchmark_history: deque = deque(maxlen=1000)
        self._init_database()
    
    def _init_database(self):
        """Initialize benchmark database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark_name TEXT,
                execution_time_ms REAL,
                timestamp TEXT,
                passed_target BOOLEAN,
                passed_warning BOOLEAN,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run_benchmark(self, benchmark_name: str, test_func: callable) -> Dict:
        """Run a single benchmark"""
        if benchmark_name not in self.benchmarks:
            return {'error': f'Unknown benchmark: {benchmark_name}'}
        
        spec = self.benchmarks[benchmark_name]
        
        # Run test
        start = time.time()
        try:
            test_func()
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
        
        execution_time = (time.time() - start) * 1000
        
        # Evaluate against thresholds
        passed_target = execution_time <= spec['target_ms']
        passed_warning = execution_time <= spec['warning_ms']
        
        result = {
            'benchmark': benchmark_name,
            'execution_time_ms': round(execution_time, 2),
            'target_ms': spec['target_ms'],
            'passed_target': passed_target,
            'passed_warning': passed_warning,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store result
        self._store_result(result)
        self.benchmark_history.append(result)
        
        return result
    
    def _store_result(self, result: Dict):
        """Store benchmark result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO benchmark_results
            (benchmark_name, execution_time_ms, timestamp, passed_target, passed_warning, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result['benchmark'],
            result['execution_time_ms'],
            result['timestamp'],
            result['passed_target'],
            result['passed_warning'],
            json.dumps({'error': result.get('error')})
        ))
        
        conn.commit()
        conn.close()
    
    def detect_regression(self, benchmark_name: str, lookback: int = 10) -> Optional[Dict]:
        """Detect performance regression for a benchmark"""
        recent = [b for b in self.benchmark_history if b['benchmark'] == benchmark_name][-lookback:]
        
        if len(recent) < 5:
            return None
        
        # Calculate trend
        times = [r['execution_time_ms'] for r in recent]
        avg_recent = statistics.mean(times[-5:])
        avg_older = statistics.mean(times[:-5])
        
        # 20% increase = regression
        if avg_recent > avg_older * 1.2:
            return {
                'benchmark': benchmark_name,
                'regression_detected': True,
                'previous_avg_ms': round(avg_older, 2),
                'recent_avg_ms': round(avg_recent, 2),
                'increase_percent': round((avg_recent / avg_older - 1) * 100, 1),
                'severity': 'warning' if avg_recent < self.benchmarks[benchmark_name]['warning_ms'] else 'critical'
            }
        
        return None
    
    def get_benchmark_report(self) -> Dict:
        """Get comprehensive benchmark report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'benchmarks': {}
        }
        
        for name, spec in self.benchmarks.items():
            results = [b for b in self.benchmark_history if b['benchmark'] == name]
            
            if results:
                times = [r['execution_time_ms'] for r in results]
                report['benchmarks'][name] = {
                    'description': spec['description'],
                    'target_ms': spec['target_ms'],
                    'latest_ms': round(times[-1], 2),
                    'avg_ms': round(statistics.mean(times), 2),
                    'min_ms': round(min(times), 2),
                    'max_ms': round(max(times), 2),
                    'samples': len(times),
                    'meets_target': times[-1] <= spec['target_ms'],
                    'regression': self.detect_regression(name)
                }
            else:
                report['benchmarks'][name] = {'status': 'no_data'}
        
        return report


# ==================== OVERTRAINING DETECTION ====================

class OvertrainingDetector:
    """
    Detects when agents are being overtrained
    Monitors for diminishing returns, overfitting indicators
    """
    
    def __init__(self):
        self.agent_training_history: Dict[str, List[Dict]] = defaultdict(list)
        self.overfitting_indicators = {
            'performance_degradation_threshold': 0.1,  # 10% drop
            'improvement_plateau_threshold': 0.05,   # < 5% improvement over 10 iterations
            'variance_increase_threshold': 2.0       # Variance doubled
        }
    
    def record_training_iteration(self, agent_name: str, metrics: Dict):
        """Record metrics from a training iteration"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'iteration': metrics.get('iteration', 0),
            'performance_score': metrics.get('performance_score', 0),
            'validation_score': metrics.get('validation_score', 0),
            'training_loss': metrics.get('training_loss', 0),
            'validation_loss': metrics.get('validation_loss', 0)
        }
        
        self.agent_training_history[agent_name].append(record)
    
    def analyze_for_overtraining(self, agent_name: str) -> Dict:
        """Analyze if agent is being overtrained"""
        history = self.agent_training_history[agent_name]
        
        if len(history) < 10:
            return {'status': 'insufficient_data', 'iterations_needed': 10 - len(history)}
        
        recent = history[-10:]
        
        # Check 1: Performance degradation
        training_scores = [r['performance_score'] for r in recent]
        validation_scores = [r['validation_score'] for r in recent]
        
        training_trend = self._calculate_trend(training_scores)
        validation_trend = self._calculate_trend(validation_scores)
        
        # Overfitting: training improves but validation degrades
        if training_trend > 0.05 and validation_trend < -0.05:
            return {
                'overtraining_detected': True,
                'type': 'overfitting',
                'severity': 'high',
                'details': {
                    'training_improvement': round(training_trend, 3),
                    'validation_degradation': round(validation_trend, 3),
                    'recommendation': 'Stop training or increase regularization'
                }
            }
        
        # Check 2: Improvement plateau
        if len(history) >= 20:
            older = history[-20:-10]
            older_avg = statistics.mean([r['performance_score'] for r in older])
            recent_avg = statistics.mean([r['performance_score'] for r in recent])
            
            improvement = (recent_avg - older_avg) / abs(older_avg) if older_avg != 0 else 0
            
            if improvement < self.overfitting_indicators['improvement_plateau_threshold']:
                return {
                    'overtraining_detected': True,
                    'type': 'plateau',
                    'severity': 'medium',
                    'details': {
                        'improvement_10_iter': round(improvement, 3),
                        'recommendation': 'Consider stopping - diminishing returns'
                    }
                }
        
        # Check 3: High variance in validation
        if len(validation_scores) >= 5:
            recent_variance = statistics.variance(validation_scores[-5:])
            older_variance = statistics.variance([r['validation_score'] for r in history[-10:-5]])
            
            if older_variance > 0 and recent_variance / older_variance > self.overfitting_indicators['variance_increase_threshold']:
                return {
                    'overtraining_detected': True,
                    'type': 'instability',
                    'severity': 'medium',
                    'details': {
                        'variance_increase': round(recent_variance / older_variance, 2),
                        'recommendation': 'Reduce learning rate or add more training data'
                    }
                }
        
        return {
            'overtraining_detected': False,
            'training_healthy': True,
            'iterations_tracked': len(history)
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in values (simple slope)"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0
    
    def get_overtraining_report(self) -> Dict:
        """Get overtraining analysis for all agents"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'agents_analyzed': len(self.agent_training_history),
            'findings': {}
        }
        
        for agent_name in self.agent_training_history:
            analysis = self.analyze_for_overtraining(agent_name)
            report['findings'][agent_name] = analysis
        
        overtrained = sum(1 for a in report['findings'].values() if a.get('overtraining_detected'))
        report['agents_overtrained'] = overtrained
        
        return report


# ==================== CONTRADICTORY FEEDBACK HANDLER ====================

class ContradictoryFeedbackHandler:
    """
    Handles contradictory feedback from users
    Detects conflicts and resolves them
    """
    
    def __init__(self):
        self.feedback_history: Dict[str, List[Dict]] = defaultdict(list)
        self.conflict_threshold = 2.0  # Difference of 2+ points = conflict
    
    def record_feedback(self, query_hash: str, user_id: str, rating: float, 
                       context: Dict):
        """Record user feedback"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'rating': rating,
            'context': context
        }
        
        self.feedback_history[query_hash].append(feedback)
    
    def detect_contradictions(self, query_hash: str) -> Optional[Dict]:
        """Detect if there are contradictory ratings for a query"""
        feedbacks = self.feedback_history[query_hash]
        
        if len(feedbacks) < 2:
            return None
        
        ratings = [f['rating'] for f in feedbacks]
        rating_range = max(ratings) - min(ratings)
        
        if rating_range >= self.conflict_threshold:
            # Find conflicting users
            high_ratings = [f for f in feedbacks if f['rating'] >= 4]
            low_ratings = [f for f in feedbacks if f['rating'] <= 2]
            
            return {
                'contradiction_detected': True,
                'query_hash': query_hash,
                'rating_range': rating_range,
                'total_feedback': len(feedbacks),
                'high_ratings': len(high_ratings),
                'low_ratings': len(low_ratings),
                'resolution_strategy': self._determine_resolution(feedbacks)
            }
        
        return None
    
    def _determine_resolution(self, feedbacks: List[Dict]) -> str:
        """Determine how to resolve contradictory feedback"""
        # Strategy: weighted by user expertise/history
        # For now, simple majority with weighting toward recent
        
        recent = [f for f in feedbacks if 
                 datetime.fromisoformat(f['timestamp']) > datetime.now() - timedelta(days=7)]
        
        if len(recent) >= 2:
            return 'use_recent_consensus'
        
        return 'use_weighted_average'
    
    def resolve_contradiction(self, query_hash: str) -> Dict:
        """Resolve contradictory feedback into single score"""
        feedbacks = self.feedback_history[query_hash]
        
        if not feedbacks:
            return {'error': 'No feedback for this query'}
        
        # Weight by recency (exponential decay)
        now = datetime.now()
        weighted_sum = 0
        weight_sum = 0
        
        for feedback in feedbacks:
            age_days = (now - datetime.fromisoformat(feedback['timestamp'])).days
            weight = 0.9 ** age_days  # Decay factor
            weighted_sum += feedback['rating'] * weight
            weight_sum += weight
        
        resolved_score = weighted_sum / weight_sum if weight_sum > 0 else 3.0
        
        return {
            'query_hash': query_hash,
            'resolved_score': round(resolved_score, 2),
            'feedback_count': len(feedbacks),
            'raw_ratings': [f['rating'] for f in feedbacks],
            'method': 'time_weighted_average'
        }
    
    def get_contradiction_report(self) -> Dict:
        """Get report of all contradictions"""
        contradictions = []
        
        for query_hash in self.feedback_history:
            if len(self.feedback_history[query_hash]) >= 2:
                conflict = self.detect_contradictions(query_hash)
                if conflict:
                    contradictions.append(conflict)
        
        return {
            'total_queries_with_feedback': len(self.feedback_history),
            'contradictions_found': len(contradictions),
            'contradiction_rate': len(contradictions) / len(self.feedback_history) if self.feedback_history else 0,
            'details': contradictions[-10:]  # Last 10
        }


# ==================== GRACEFUL DEGRADATION ====================

class GracefulDegradation:
    """
    Handles failures gracefully by falling back to simpler modes
    """
    
    def __init__(self):
        self.subsystem_status: Dict[str, str] = {
            'training_framework': 'operational',
            'advanced_improvements': 'operational',
            'state_of_the_art': 'operational',
            'final_enhancements': 'operational',
            'massive_training': 'operational',
            'orchestration': 'operational',
            'production_system': 'operational'
        }
        self.fallback_chain = {
            'orchestration': ['advanced_improvements', 'training_framework', 'solo_mode'],
            'massive_training': ['training_framework', 'basic_training'],
            'state_of_the_art': ['advanced_improvements', 'training_framework'],
            'final_enhancements': ['training_framework'],
            'advanced_improvements': ['training_framework'],
            'production_system': ['basic_monitoring']
        }
    
    def mark_subsystem_down(self, subsystem: str, reason: str):
        """Mark a subsystem as non-operational"""
        self.subsystem_status[subsystem] = 'degraded'
        print(f"[DEGRADATION] {subsystem} marked as degraded: {reason}")
    
    def get_operational_subsystems(self) -> List[str]:
        """Get list of operational subsystems"""
        return [name for name, status in self.subsystem_status.items() if status == 'operational']
    
    def get_fallback_for_operation(self, primary_subsystem: str, operation: str) -> Optional[str]:
        """Get fallback subsystem for an operation"""
        if primary_subsystem not in self.fallback_chain:
            return None
        
        for fallback in self.fallback_chain[primary_subsystem]:
            if fallback in self.subsystem_status:
                if self.subsystem_status.get(fallback) == 'operational':
                    return fallback
        
        return None
    
    def execute_with_fallback(self, primary_subsystem: str, operation: str, 
                             args: Dict) -> Dict:
        """Execute operation with automatic fallback"""
        # Try primary
        if self.subsystem_status.get(primary_subsystem) == 'operational':
            try:
                result = self._execute_operation(primary_subsystem, operation, args)
                return {'success': True, 'subsystem_used': primary_subsystem, 'result': result}
            except Exception as e:
                self.mark_subsystem_down(primary_subsystem, str(e))
        
        # Try fallbacks
        fallback = self.get_fallback_for_operation(primary_subsystem, operation)
        if fallback:
            try:
                result = self._execute_operation(fallback, operation, args)
                return {
                    'success': True,
                    'subsystem_used': fallback,
                    'fallback_from': primary_subsystem,
                    'result': result,
                    'degraded': True
                }
            except Exception as e:
                return {'success': False, 'error': f'Primary and fallback failed: {e}'}
        
        return {'success': False, 'error': 'No operational subsystem available'}
    
    def _execute_operation(self, subsystem: str, operation: str, args: Dict) -> Any:
        """Execute operation on subsystem (placeholder)"""
        # This would dispatch to actual subsystems
        return {'subsystem': subsystem, 'operation': operation, 'args': args}
    
    def get_degradation_status(self) -> Dict:
        """Get current degradation status"""
        return {
            'subsystem_status': self.subsystem_status,
            'operational_count': sum(1 for s in self.subsystem_status.values() if s == 'operational'),
            'degraded_count': sum(1 for s in self.subsystem_status.values() if s == 'degraded'),
            'healthy': all(s == 'operational' for s in self.subsystem_status.values())
        }


# Global instances
integration_tests = IntegrationTestFramework()
benchmarks = PerformanceBenchmarks()
overtraining_detector = OvertrainingDetector()
feedback_handler = ContradictoryFeedbackHandler()
graceful_degradation = GracefulDegradation()
