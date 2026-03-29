"""
AdaptiveLearningService - Performance tracking and dynamic weight adjustment
Phase 6 Implementation
"""

import logging
import json
from typing import Dict, List, Optional
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from core.data_structures import (
    AgentType, ModelMetrics, AgentPosition, JudicialVerdict
)

log = logging.getLogger(__name__)


class AdaptiveLearningService:
    """
    Adaptive Learning Service: Tracks performance and adjusts weights over time
    - Tracks agent performance
    - Adjusts model ensemble weights
    - Updates agent importance based on historical accuracy
    - Learns from past predictions vs actual outcomes
    """
    
    def __init__(self, storage_path: str = ".adaptive_learning"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Performance tracking
        self.agent_performance: Dict[str, List[Dict]] = {
            agent_type.value: [] for agent_type in AgentType
        }
        self.model_performance: Dict[str, List[Dict]] = {}
        self.prediction_history: List[Dict] = []
        
        # Current weights
        self.agent_weights: Dict[str, float] = {
            AgentType.CONSERVATIVE.value: 0.15,
            AgentType.AGGRESSIVE.value: 0.20,
            AgentType.QUANTITATIVE.value: 0.20,
            AgentType.SENTIMENT.value: 0.15,
            AgentType.RISK_MANAGER.value: 0.30
        }
        
        self.model_weights: Dict[str, float] = {
            'ridge': 0.25,
            'elastic': 0.25,
            'random_forest': 0.25,
            'gradient_boost': 0.25
        }
        
        self._load_history()
        log.info("AdaptiveLearningService initialized")
    
    def record_prediction(self, symbol: str, timestamp: datetime,
                         verdict: JudicialVerdict, actual_return: Optional[float] = None):
        """
        Record a prediction for later evaluation
        
        Args:
            symbol: Stock symbol
            timestamp: When prediction was made
            verdict: The judicial verdict (prediction)
            actual_return: Actual return if known (None for pending)
        """
        record = {
            'symbol': symbol,
            'timestamp': timestamp.isoformat(),
            'predicted_stance': verdict.winning_stance.value,
            'confidence': verdict.conviction_level,
            'agreement': verdict.agreement_level,
            'position_size': verdict.order_decision.position_size_pct if verdict.order_decision else 0,
            'actual_return': actual_return,
            'evaluated': actual_return is not None
        }
        
        self.prediction_history.append(record)
        
        # Auto-save periodically
        if len(self.prediction_history) % 10 == 0:
            self._save_history()
    
    def evaluate_prediction(self, symbol: str, timestamp: datetime, 
                           actual_return: float, holding_days: int = 5):
        """
        Evaluate a past prediction against actual outcome
        
        Args:
            symbol: Stock symbol
            timestamp: When prediction was made
            actual_return: Actual realized return
            holding_days: How long position was held
        """
        # Find matching prediction
        for pred in self.prediction_history:
            if (pred['symbol'] == symbol and 
                pred['timestamp'] == timestamp.isoformat() and
                not pred['evaluated']):
                
                pred['actual_return'] = actual_return
                pred['holding_days'] = holding_days
                pred['evaluated'] = True
                pred['evaluated_at'] = datetime.now().isoformat()
                
                # Determine if prediction was correct
                predicted_bullish = pred['predicted_stance'] in ['buy', 'long']
                predicted_bearish = pred['predicted_stance'] in ['sell', 'short']
                
                actually_bullish = actual_return > 0.01  # >1% gain
                actually_bearish = actual_return < -0.01  # >1% loss
                
                correct = ((predicted_bullish and actually_bullish) or
                          (predicted_bearish and actually_bearish) or
                          (pred['predicted_stance'] == 'hold' and 
                           not actually_bullish and not actually_bearish))
                
                pred['correct'] = correct
                pred['prediction_quality'] = self._calculate_quality_score(
                    pred['confidence'], actual_return, correct
                )
                
                log.info(f"Evaluated {symbol}: predicted={pred['predicted_stance']}, "
                        f"actual={actual_return:.2%}, correct={correct}")
                
                self._save_history()
                return True
        
        return False
    
    def _calculate_quality_score(self, confidence: float, 
                                  actual_return: float, correct: bool) -> float:
        """Calculate quality score for a prediction"""
        base_score = 1.0 if correct else 0.0
        
        # Confidence calibration bonus/penalty
        confidence_error = abs(confidence - (1.0 if correct else 0.0))
        calibration_penalty = confidence_error * 0.5
        
        # Return magnitude bonus
        return_bonus = min(abs(actual_return) * 2, 0.5)
        
        return max(0, base_score - calibration_penalty + return_bonus)
    
    def record_agent_performance(self, agent_type: AgentType, symbol: str,
                                  predicted_return: float, actual_return: float,
                                  timestamp: datetime = None):
        """Record individual agent performance"""
        if timestamp is None:
            timestamp = datetime.now()
        
        error = abs(predicted_return - actual_return)
        directional_correct = (predicted_return > 0) == (actual_return > 0)
        
        record = {
            'timestamp': timestamp.isoformat(),
            'symbol': symbol,
            'predicted': predicted_return,
            'actual': actual_return,
            'error': error,
            'directional_correct': directional_correct
        }
        
        self.agent_performance[agent_type.value].append(record)
        
        # Keep only last 100 records per agent
        if len(self.agent_performance[agent_type.value]) > 100:
            self.agent_performance[agent_type.value] = \
                self.agent_performance[agent_type.value][-100:]
    
    def update_weights(self, lookback_days: int = 30):
        """
        Update agent and model weights based on recent performance
        
        Args:
            lookback_days: How many days of history to consider
        """
        cutoff = datetime.now() - timedelta(days=lookback_days)
        
        # Calculate agent performance scores
        new_weights = {}
        
        for agent_type in AgentType:
            records = [
                r for r in self.agent_performance[agent_type.value]
                if datetime.fromisoformat(r['timestamp']) > cutoff
            ]
            
            if records:
                # Score based on directional accuracy and error
                directional_accuracy = sum(1 for r in records if r['directional_correct']) / len(records)
                avg_error = sum(r['error'] for r in records) / len(records)
                
                # Higher accuracy, lower error = higher weight
                score = directional_accuracy * (1 - min(avg_error, 1.0))
                new_weights[agent_type.value] = max(0.05, min(0.50, score))
            else:
                # Default weight if no recent data
                new_weights[agent_type.value] = self.agent_weights.get(agent_type.value, 0.20)
        
        # Normalize to sum to 1
        total = sum(new_weights.values())
        self.agent_weights = {k: v/total for k, v in new_weights.items()}
        
        log.info(f"Updated agent weights: {self.agent_weights}")
        
        # Save updated weights
        self._save_history()
    
    def get_agent_performance_summary(self, agent_type: AgentType,
                                     days: int = 30) -> Dict:
        """Get performance summary for an agent"""
        cutoff = datetime.now() - timedelta(days=days)
        
        records = [
            r for r in self.agent_performance[agent_type.value]
            if datetime.fromisoformat(r['timestamp']) > cutoff
        ]
        
        if not records:
            return {
                'agent_type': agent_type.value,
                'n_predictions': 0,
                'directional_accuracy': 0.0,
                'avg_error': 0.0,
                'weight': self.agent_weights.get(agent_type.value, 0.20)
            }
        
        directional_accuracy = sum(1 for r in records if r['directional_correct']) / len(records)
        avg_error = sum(r['error'] for r in records) / len(records)
        
        return {
            'agent_type': agent_type.value,
            'n_predictions': len(records),
            'directional_accuracy': directional_accuracy,
            'avg_error': avg_error,
            'weight': self.agent_weights.get(agent_type.value, 0.20),
            'recent_trend': 'improving' if len(records) > 10 and 
                           directional_accuracy > 0.55 else 'stable'
        }
    
    def get_system_performance(self, days: int = 30) -> Dict:
        """Get overall system performance metrics"""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_predictions = [
            p for p in self.prediction_history
            if p.get('evaluated') and 
            datetime.fromisoformat(p['timestamp']) > cutoff
        ]
        
        if not recent_predictions:
            return {
                'total_predictions': 0,
                'evaluated_predictions': 0,
                'accuracy': 0.0,
                'avg_return': 0.0
            }
        
        correct = sum(1 for p in recent_predictions if p.get('correct', False))
        total_return = sum(p.get('actual_return', 0) for p in recent_predictions)
        
        return {
            'total_predictions': len(self.prediction_history),
            'evaluated_predictions': len(recent_predictions),
            'accuracy': correct / len(recent_predictions) if recent_predictions else 0,
            'avg_return': total_return / len(recent_predictions),
            'current_agent_weights': self.agent_weights.copy(),
            'current_model_weights': self.model_weights.copy()
        }
    
    def _load_history(self):
        """Load historical data from storage"""
        history_file = self.storage_path / "learning_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    
                self.agent_performance = data.get('agent_performance', self.agent_performance)
                self.model_performance = data.get('model_performance', self.model_performance)
                self.prediction_history = data.get('prediction_history', [])
                self.agent_weights = data.get('agent_weights', self.agent_weights)
                self.model_weights = data.get('model_weights', self.model_weights)
                
                log.info(f"Loaded {len(self.prediction_history)} historical predictions")
            except Exception as e:
                log.warning(f"Could not load history: {e}")
    
    def _save_history(self):
        """Save current state to storage"""
        history_file = self.storage_path / "learning_history.json"
        
        data = {
            'agent_performance': self.agent_performance,
            'model_performance': self.model_performance,
            'prediction_history': self.prediction_history[-500:],  # Keep last 500
            'agent_weights': self.agent_weights,
            'model_weights': self.model_weights,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"Could not save history: {e}")
    
    def generate_learning_report(self) -> str:
        """Generate human-readable learning report"""
        system_perf = self.get_system_performance()
        
        lines = []
        lines.append("=" * 60)
        lines.append("ADAPTIVE LEARNING REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append("SYSTEM PERFORMANCE (Last 30 days)")
        lines.append(f"  Total Predictions: {system_perf['total_predictions']}")
        lines.append(f"  Evaluated: {system_perf['evaluated_predictions']}")
        lines.append(f"  Directional Accuracy: {system_perf['accuracy']:.1%}")
        lines.append(f"  Average Return: {system_perf['avg_return']:.2%}")
        lines.append("")
        
        lines.append("CURRENT AGENT WEIGHTS")
        for agent_type, weight in self.agent_weights.items():
            lines.append(f"  {agent_type}: {weight:.1%}")
        lines.append("")
        
        lines.append("AGENT PERFORMANCE")
        for agent_type in AgentType:
            summary = self.get_agent_performance_summary(agent_type)
            lines.append(f"  {agent_type.value}:")
            lines.append(f"    Accuracy: {summary['directional_accuracy']:.1%}")
            lines.append(f"    Avg Error: {summary['avg_error']:.2%}")
            lines.append(f"    Trend: {summary['recent_trend']}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# Global instance
adaptive_learning_service = AdaptiveLearningService()
