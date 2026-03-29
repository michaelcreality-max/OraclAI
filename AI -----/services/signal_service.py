"""
SignalService - Generate trading signals from ML predictions
Phase 2 Implementation
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from core.data_structures import (
    ModelPrediction, TradingSignal, SignalReasoning, SignalType
)
from core.exceptions import MLError

log = logging.getLogger(__name__)


class SignalGenerator:
    """Generate signals from model predictions"""
    
    # Signal thresholds
    BUY_CONFIDENCE_THRESHOLD = 0.65
    SELL_CONFIDENCE_THRESHOLD = 0.65
    HOLD_CONFIDENCE_RANGE = (0.45, 0.55)
    
    # Expected return thresholds
    MIN_EXPECTED_RETURN = 0.02  # 2%
    
    def __init__(self):
        self.signal_history = []
        log.info("SignalGenerator initialized")
    
    def generate_signal(self, prediction: ModelPrediction) -> TradingSignal:
        """
        Generate trading signal from model prediction
        
        Args:
            prediction: ModelPrediction with direction probabilities
            
        Returns:
            TradingSignal with action and reasoning
        """
        symbol = prediction.symbol
        direction_prob = prediction.direction_prob
        confidence = prediction.confidence
        expected_return = prediction.expected_return
        
        # Determine primary factors
        factors = []
        
        # Check direction probabilities
        up_prob = direction_prob.get('up', 0)
        down_prob = direction_prob.get('down', 0)
        flat_prob = direction_prob.get('flat', 0)
        
        # Determine signal type
        if up_prob > self.BUY_CONFIDENCE_THRESHOLD and confidence >= 0.6:
            signal_type = SignalType.BUY
            factors.append('high_up_probability')
            if expected_return > self.MIN_EXPECTED_RETURN:
                factors.append('positive_expected_return')
        
        elif down_prob > self.SELL_CONFIDENCE_THRESHOLD and confidence >= 0.6:
            signal_type = SignalType.SELL
            factors.append('high_down_probability')
            if expected_return < -self.MIN_EXPECTED_RETURN:
                factors.append('negative_expected_return')
        
        else:
            signal_type = SignalType.HOLD
            factors.append('insufficient_confidence')
            if flat_prob > 0.4:
                factors.append('sideways_market_indicated')
        
        # Build reasoning
        reasoning = SignalReasoning(
            primary_factors=factors,
            supporting_evidence=[
                f"Model confidence: {confidence:.1%}",
                f"Expected return: {expected_return:.2%}",
                f"Up probability: {up_prob:.1%}",
                f"Down probability: {down_prob:.1%}"
            ],
            contrarian_indicators=[],
            risk_factors=[],
            model_agreement=confidence
        )
        
        # Determine time horizon based on expected return magnitude
        if abs(expected_return) > 0.05:  # > 5%
            time_horizon = "short"  # 1-2 weeks
        elif abs(expected_return) > 0.02:  # > 2%
            time_horizon = "medium"  # 1-3 months
        else:
            time_horizon = "long"  # 3+ months
        
        signal = TradingSignal(
            symbol=symbol,
            signal=signal_type,
            confidence=confidence,
            expected_return=expected_return,
            time_horizon=time_horizon,
            reasoning=reasoning,
            timestamp=datetime.now(),
            expiry=datetime.now() + timedelta(days=5)
        )
        
        self.signal_history.append({
            'timestamp': signal.timestamp,
            'symbol': symbol,
            'signal': signal_type.value,
            'confidence': confidence
        })
        
        log.info(f"Generated {signal_type.value} signal for {symbol} "
                f"(conf: {confidence:.1%}, ret: {expected_return:.2%})")
        
        return signal
    
    def generate_batch(self, predictions: List[ModelPrediction]) -> List[TradingSignal]:
        """
        Generate signals for multiple predictions
        
        Args:
            predictions: List of ModelPrediction objects
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        for pred in predictions:
            try:
                signal = self.generate_signal(pred)
                signals.append(signal)
            except Exception as e:
                log.error(f"Failed to generate signal for {pred.symbol}: {e}")
                # Return HOLD signal on error
                signals.append(TradingSignal(
                    symbol=pred.symbol,
                    signal=SignalType.HOLD,
                    confidence=0.5,
                    expected_return=0.0,
                    reasoning=SignalReasoning(primary_factors=['generation_error']),
                    timestamp=datetime.now()
                ))
        
        return signals
    
    def get_signal_history(self, symbol: Optional[str] = None, 
                          days: int = 30) -> List[Dict]:
        """
        Get historical signals
        
        Args:
            symbol: Filter by symbol (optional)
            days: Number of days to look back
            
        Returns:
            List of historical signal records
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = [
            sig for sig in self.signal_history
            if sig['timestamp'] > cutoff
            and (symbol is None or sig['symbol'] == symbol)
        ]
        
        return filtered
    
    def get_signal_statistics(self, days: int = 30) -> Dict:
        """
        Get signal generation statistics
        
        Args:
            days: Lookback period
            
        Returns:
            Statistics dictionary
        """
        history = self.get_signal_history(days=days)
        
        if not history:
            return {
                'total_signals': 0,
                'buy_count': 0,
                'sell_count': 0,
                'hold_count': 0,
                'avg_confidence': 0.0
            }
        
        buy_count = sum(1 for s in history if s['signal'] == 'buy')
        sell_count = sum(1 for s in history if s['signal'] == 'sell')
        hold_count = sum(1 for s in history if s['signal'] == 'hold')
        
        avg_confidence = sum(s['confidence'] for s in history) / len(history)
        
        return {
            'total_signals': len(history),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'hold_count': hold_count,
            'avg_confidence': avg_confidence,
            'buy_pct': buy_count / len(history) * 100,
            'sell_pct': sell_count / len(history) * 100,
            'hold_pct': hold_count / len(history) * 100
        }


class SignalService:
    """
    Service for generating and managing trading signals
    """
    
    def __init__(self):
        self.generator = SignalGenerator()
        log.info("SignalService initialized")
    
    def generate_signal(self, prediction: ModelPrediction) -> TradingSignal:
        """Generate signal from prediction"""
        return self.generator.generate_signal(prediction)
    
    def generate_batch(self, predictions: List[ModelPrediction]) -> List[TradingSignal]:
        """Generate signals for multiple predictions"""
        return self.generator.generate_batch(predictions)
    
    def get_signal_history(self, symbol: Optional[str] = None, 
                          days: int = 30) -> List[Dict]:
        """Get historical signals"""
        return self.generator.get_signal_history(symbol, days)
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Get signal statistics"""
        return self.generator.get_signal_statistics(days)


# Global instance
signal_service = SignalService()
