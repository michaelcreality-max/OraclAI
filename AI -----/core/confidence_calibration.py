"""
Confidence Calibration System
Aligns confidence scores with actual accuracy through calibration
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class ConfidenceBin:
    """A bin for confidence calibration"""
    bin_start: float  # 0.0-1.0
    bin_end: float
    predictions: int = 0
    correct: int = 0
    accuracy: float = 0.0
    avg_confidence: float = 0.0
    
    def update(self, confidence: float, was_correct: bool):
        self.predictions += 1
        if was_correct:
            self.correct += 1
        self.accuracy = self.correct / self.predictions if self.predictions > 0 else 0
        # Running average
        self.avg_confidence = (self.avg_confidence * (self.predictions - 1) + confidence) / self.predictions


@dataclass
class CalibrationResult:
    """Result of calibration analysis"""
    expected_calibration_error: float  # Lower is better
    max_calibration_error: float
    reliability_diagram: Dict[str, List[float]]
    calibration_function: Dict[float, float]  # Maps raw confidence to calibrated
    is_well_calibrated: bool


class ConfidenceCalibrator:
    """
    Calibrates confidence scores to match actual probabilities.
    
    Uses isotonic regression-like binning approach to learn the mapping
    between predicted confidence and actual accuracy.
    """
    
    def __init__(self, n_bins: int = 10, storage_path: str = ".calibration"):
        self.n_bins = n_bins
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize calibration bins
        bin_size = 1.0 / n_bins
        self.bins: Dict[str, List[ConfidenceBin]] = {}
        self.calibration_history: List[Dict] = []
        
        # Calibration parameters
        self.temperature: Dict[str, float] = {}  # Temperature scaling parameter
        
        # Track predictions for calibration
        self.prediction_buffer: List[Dict] = []
        
        log.info(f"ConfidenceCalibrator initialized with {n_bins} bins")
    
    def initialize_agent_bins(self, agent_type: str):
        """Initialize calibration bins for an agent type"""
        if agent_type not in self.bins:
            bin_size = 1.0 / self.n_bins
            self.bins[agent_type] = [
                ConfidenceBin(
                    bin_start=i * bin_size,
                    bin_end=(i + 1) * bin_size
                )
                for i in range(self.n_bins)
            ]
            self.temperature[agent_type] = 1.0  # Default temperature
    
    def record_prediction(self, agent_type: str, confidence: float, 
                       predicted_outcome: str, timestamp: datetime = None):
        """Record a prediction for later calibration"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.prediction_buffer.append({
            'agent_type': agent_type,
            'confidence': confidence,
            'predicted': predicted_outcome,
            'timestamp': timestamp.isoformat(),
            'actual': None,  # To be filled
            'evaluated': False
        })
        
        # Auto-flush if buffer gets large
        if len(self.prediction_buffer) > 100:
            self._save_buffer()
    
    def evaluate_prediction(self, agent_type: str, timestamp: datetime,
                           actual_outcome: str) -> bool:
        """Evaluate a past prediction"""
        # Find matching prediction
        for pred in self.prediction_buffer:
            if (pred['agent_type'] == agent_type and 
                pred['timestamp'] == timestamp.isoformat() and
                not pred['evaluated']):
                
                pred['actual'] = actual_outcome
                pred['evaluated'] = True
                
                # Determine correctness
                was_correct = pred['predicted'] == actual_outcome
                
                # Update calibration bin
                self._update_bin(agent_type, pred['confidence'], was_correct)
                
                return True
        
        return False
    
    def _update_bin(self, agent_type: str, confidence: float, was_correct: bool):
        """Update appropriate calibration bin"""
        self.initialize_agent_bins(agent_type)
        
        # Find bin
        for bin in self.bins[agent_type]:
            if bin.bin_start <= confidence < bin.bin_end:
                bin.update(confidence, was_correct)
                break
        
        # Edge case: confidence = 1.0
        if confidence == 1.0:
            self.bins[agent_type][-1].update(confidence, was_correct)
    
    def calibrate_confidence(self, agent_type: str, raw_confidence: float) -> float:
        """
        Calibrate a raw confidence score to match actual accuracy
        
        Uses learned calibration function
        """
        self.initialize_agent_bins(agent_type)
        
        # Find appropriate bin
        for bin in self.bins[agent_type]:
            if bin.bin_start <= raw_confidence < bin.bin_end:
                if bin.predictions >= 5:  # Need sufficient data
                    return bin.accuracy
                else:
                    break
        
        # Fall back to temperature scaling if insufficient bin data
        temp = self.temperature.get(agent_type, 1.0)
        if temp != 1.0:
            # Apply temperature scaling
            from math import exp, log
            # Convert to log-odds, scale, convert back
            if raw_confidence > 0.99:
                return raw_confidence
            log_odds = log(raw_confidence / (1 - raw_confidence))
            scaled_log_odds = log_odds / temp
            calibrated = 1 / (1 + exp(-scaled_log_odds))
            return calibrated
        
        return raw_confidence
    
    def analyze_calibration(self, agent_type: str) -> CalibrationResult:
        """Analyze calibration quality for an agent type"""
        self.initialize_agent_bins(agent_type)
        
        bins = self.bins[agent_type]
        
        # Calculate Expected Calibration Error (ECE)
        total_predictions = sum(b.predictions for b in bins)
        if total_predictions == 0:
            return CalibrationResult(
                expected_calibration_error=1.0,
                max_calibration_error=1.0,
                reliability_diagram={'confidences': [], 'accuracies': []},
                calibration_function={},
                is_well_calibrated=False
            )
        
        ece = 0.0
        max_error = 0.0
        confidences = []
        accuracies = []
        calibration_func = {}
        
        for bin in bins:
            if bin.predictions > 0:
                weight = bin.predictions / total_predictions
                error = abs(bin.avg_confidence - bin.accuracy)
                ece += weight * error
                max_error = max(max_error, error)
                
                confidences.append(bin.avg_confidence)
                accuracies.append(bin.accuracy)
                calibration_func[round(bin.avg_confidence, 2)] = bin.accuracy
        
        # Well calibrated if ECE < 0.05 (5%)
        is_well_calibrated = ece < 0.05
        
        return CalibrationResult(
            expected_calibration_error=round(ece, 3),
            max_calibration_error=round(max_error, 3),
            reliability_diagram={
                'confidences': confidences,
                'accuracies': accuracies
            },
            calibration_function=calibration_func,
            is_well_calibrated=is_well_calibrated
        )
    
    def fit_temperature_scaling(self, agent_type: str):
        """
        Fit temperature scaling parameter for better calibration
        
        Temperature scaling: p_calibrated = sigmoid(logits / temperature)
        Lower temperature = sharper (more confident)
        Higher temperature = smoother (less confident)
        """
        self.initialize_agent_bins(agent_type)
        
        bins = self.bins[agent_type]
        
        # Only fit if sufficient data
        total_preds = sum(b.predictions for b in bins)
        if total_preds < 20:
            return
        
        # Simple grid search for optimal temperature
        from math import exp, log
        
        best_temp = 1.0
        best_ece = float('inf')
        
        for temp in [0.5, 0.7, 1.0, 1.3, 1.5, 2.0, 2.5]:
            ece = self._calculate_ece_with_temperature(bins, temp)
            if ece < best_ece:
                best_ece = ece
                best_temp = temp
        
        self.temperature[agent_type] = best_temp
        
        log.info(f"Fitted temperature {best_temp:.2f} for {agent_type} "
                f"(ECE improved to {best_ece:.3f})")
    
    def _calculate_ece_with_temperature(self, bins: List[ConfidenceBin], 
                                     temperature: float) -> float:
        """Calculate ECE with given temperature scaling"""
        from math import exp, log
        
        total_preds = sum(b.predictions for b in bins)
        if total_preds == 0:
            return 1.0
        
        ece = 0.0
        
        for bin in bins:
            if bin.predictions > 0:
                # Apply temperature scaling to average confidence
                conf = bin.avg_confidence
                if conf > 0.99:
                    scaled_conf = conf
                else:
                    log_odds = log(conf / (1 - conf))
                    scaled_log_odds = log_odds / temperature
                    scaled_conf = 1 / (1 + exp(-scaled_log_odds))
                
                error = abs(scaled_conf - bin.accuracy)
                weight = bin.predictions / total_preds
                ece += weight * error
        
        return ece
    
    def get_calibration_report(self, agent_type: str) -> str:
        """Generate human-readable calibration report"""
        cal = self.analyze_calibration(agent_type)
        
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"CONFIDENCE CALIBRATION REPORT: {agent_type.upper()}")
        lines.append(f"{'='*60}")
        lines.append(f"Expected Calibration Error (ECE): {cal.expected_calibration_error:.1%}")
        lines.append(f"Maximum Calibration Error: {cal.max_calibration_error:.1%}")
        lines.append(f"Well Calibrated: {'YES ✓' if cal.is_well_calibrated else 'NO ⚠'}")
        lines.append("")
        
        lines.append("RELIABILITY DIAGRAM:")
        lines.append(f"{'Confidence':<12} {'Accuracy':<12} {'Gap':<12}")
        lines.append("-" * 36)
        
        for conf, acc in zip(cal.reliability_diagram['confidences'],
                            cal.reliability_diagram['accuracies']):
            gap = abs(conf - acc)
            indicator = "✓" if gap < 0.05 else "⚠" if gap < 0.1 else "✗"
            lines.append(f"{conf:.2f}        {acc:.2f}        {gap:.2f} {indicator}")
        
        lines.append(f"{'='*60}\n")
        
        return "\n".join(lines)
    
    def get_all_calibration_summary(self) -> Dict:
        """Get summary of calibration for all agents"""
        summary = {}
        
        for agent_type in self.bins:
            cal = self.analyze_calibration(agent_type)
            summary[agent_type] = {
                'ece': cal.expected_calibration_error,
                'max_error': cal.max_calibration_error,
                'is_well_calibrated': cal.is_well_calibrated,
                'temperature': self.temperature.get(agent_type, 1.0),
                'total_predictions': sum(b.predictions for b in self.bins[agent_type])
            }
        
        return summary
    
    def _save_buffer(self):
        """Save prediction buffer to disk"""
        buffer_file = self.storage_path / "prediction_buffer.json"
        try:
            with open(buffer_file, 'w') as f:
                json.dump(self.prediction_buffer, f)
        except Exception as e:
            log.error(f"Could not save calibration buffer: {e}")
    
    def _load_calibration(self):
        """Load previous calibration data"""
        cal_file = self.storage_path / "calibration_data.json"
        if cal_file.exists():
            try:
                with open(cal_file, 'r') as f:
                    data = json.load(f)
                
                # Restore bins
                for agent_type, bins_data in data.get('bins', {}).items():
                    self.bins[agent_type] = [
                        ConfidenceBin(**b) for b in bins_data
                    ]
                
                self.temperature = data.get('temperature', {})
                log.info(f"Loaded calibration for {len(self.bins)} agents")
            except Exception as e:
                log.warning(f"Could not load calibration: {e}")
    
    def _save_calibration(self):
        """Save calibration data"""
        cal_file = self.storage_path / "calibration_data.json"
        
        data = {
            'bins': {
                agent: [{'bin_start': b.bin_start, 'bin_end': b.bin_end,
                        'predictions': b.predictions, 'correct': b.correct,
                        'accuracy': b.accuracy, 'avg_confidence': b.avg_confidence}
                       for b in bins]
                for agent, bins in self.bins.items()
            },
            'temperature': self.temperature,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(cal_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            log.error(f"Could not save calibration: {e}")


# Global instance
confidence_calibrator = ConfidenceCalibrator()
