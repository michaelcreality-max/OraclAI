"""
Regime Detection System
Identifies market regimes and adapts system behavior
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications"""
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    NEUTRAL = "neutral"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"


@dataclass
class RegimeState:
    """Current market regime state"""
    primary_regime: MarketRegime
    secondary_regime: Optional[MarketRegime]
    confidence: float
    duration_days: int
    trend_direction: str
    volatility_regime: str
    factors: Dict[str, float]


class RegimeDetector:
    """
    Detects market regimes using multiple indicators:
    - Trend strength (ADX, moving averages)
    - Volatility (VIX, realized vol)
    - Market breadth
    - Momentum
    """
    
    def __init__(self, lookback_window: int = 20):
        self.lookback_window = lookback_window
        self.regime_history: List[RegimeState] = []
        self.current_regime: Optional[RegimeState] = None
        
        # Regime thresholds
        self.thresholds = {
            'vix_high': 25,
            'vix_extreme': 35,
            'vix_low': 15,
            'adx_strong': 25,
            'adx_weak': 15,
            'trend_slope': 0.02
        }
        
        log.info("RegimeDetector initialized")
    
    def detect_regime(self, market_data: Dict) -> RegimeState:
        """
        Detect current market regime from market data
        
        Args:
            market_data: Dict with keys like 'prices', 'vix', 'volume',
                        'advancing', 'declining', 'new_highs', 'new_lows'
        """
        factors = {}
        
        # 1. Volatility Analysis
        vix = market_data.get('vix', 20)
        realized_vol = market_data.get('realized_volatility', 0.20)
        
        factors['vix'] = vix
        factors['realized_vol'] = realized_vol
        factors['vol_percentile'] = self._calculate_vol_percentile(vix)
        
        # 2. Trend Analysis
        prices = market_data.get('prices', [])
        if len(prices) >= self.lookback_window:
            trend_score, adx = self._analyze_trend(prices)
            factors['trend_score'] = trend_score
            factors['adx'] = adx
        else:
            factors['trend_score'] = 0
            factors['adx'] = 20
        
        # 3. Market Breadth
        advancing = market_data.get('advancing', 0)
        declining = market_data.get('declining', 0)
        if advancing + declining > 0:
            breadth_ratio = advancing / (advancing + declining)
        else:
            breadth_ratio = 0.5
        factors['breadth_ratio'] = breadth_ratio
        
        # 4. Momentum
        new_highs = market_data.get('new_highs', 0)
        new_lows = market_data.get('new_lows', 0)
        if new_highs + new_lows > 0:
            momentum_ratio = new_highs / (new_highs + new_lows)
        else:
            momentum_ratio = 0.5
        factors['momentum_ratio'] = momentum_ratio
        
        # Classify regime
        primary_regime = self._classify_regime(factors)
        secondary_regime = self._classify_secondary(factors, primary_regime)
        
        # Calculate regime confidence
        confidence = self._calculate_regime_confidence(factors, primary_regime)
        
        # Determine duration
        duration = self._calculate_regime_duration(primary_regime)
        
        regime = RegimeState(
            primary_regime=primary_regime,
            secondary_regime=secondary_regime,
            confidence=confidence,
            duration_days=duration,
            trend_direction='bullish' if factors['trend_score'] > 0.02 else 
                          'bearish' if factors['trend_score'] < -0.02 else 'neutral',
            volatility_regime='high' if vix > 25 else 'low' if vix < 15 else 'normal',
            factors=factors
        )
        
        self.current_regime = regime
        self.regime_history.append(regime)
        
        # Keep only last 252 days (1 year)
        if len(self.regime_history) > 252:
            self.regime_history = self.regime_history[-252:]
        
        log.info(f"Detected regime: {primary_regime.value} (conf: {confidence:.1%}, "
                f"duration: {duration}d)")
        
        return regime
    
    def _calculate_vol_percentile(self, vix: float) -> float:
        """Calculate VIX percentile relative to history"""
        # Simplified - would use historical VIX data
        if vix > 35:
            return 0.95
        elif vix > 25:
            return 0.80
        elif vix > 20:
            return 0.60
        elif vix > 15:
            return 0.40
        else:
            return 0.20
    
    def _analyze_trend(self, prices: List[float]) -> Tuple[float, float]:
        """Analyze trend strength and direction"""
        if len(prices) < self.lookback_window:
            return 0.0, 20.0
        
        recent = prices[-self.lookback_window:]
        
        # Simple linear regression for trend
        x = np.arange(len(recent))
        y = np.array(recent)
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize slope
        avg_price = np.mean(recent)
        trend_score = slope / avg_price if avg_price > 0 else 0
        
        # Simplified ADX-like measure
        adx = min(50, abs(trend_score) * 1000 + 10)
        
        return trend_score, adx
    
    def _classify_regime(self, factors: Dict) -> MarketRegime:
        """Classify primary regime from factors"""
        vix = factors['vix']
        adx = factors['adx']
        trend_score = factors['trend_score']
        breadth = factors['breadth_ratio']
        momentum = factors['momentum_ratio']
        
        # High volatility regime check first
        if vix > self.thresholds['vix_extreme']:
            return MarketRegime.HIGH_VOLATILITY
        
        # Strong trend regimes
        if adx > self.thresholds['adx_strong']:
            if trend_score > self.thresholds['trend_slope'] and breadth > 0.6:
                return MarketRegime.STRONG_BULL
            elif trend_score < -self.thresholds['trend_slope'] and breadth < 0.4:
                return MarketRegime.STRONG_BEAR
            elif abs(trend_score) > self.thresholds['trend_slope']:
                return MarketRegime.TRENDING
        
        # Mean reverting (weak trend + momentum divergence)
        if adx < self.thresholds['adx_weak'] and abs(momentum - 0.5) > 0.2:
            return MarketRegime.MEAN_REVERTING
        
        # Bull/Bear based on breadth and trend
        if trend_score > 0 and breadth > 0.55:
            return MarketRegime.BULL if vix < 20 else MarketRegime.NEUTRAL
        elif trend_score < 0 and breadth < 0.45:
            return MarketRegime.BEAR if vix < 25 else MarketRegime.NEUTRAL
        
        # Low volatility regime
        if vix < self.thresholds['vix_low'] and adx < 20:
            return MarketRegime.LOW_VOLATILITY
        
        return MarketRegime.NEUTRAL
    
    def _classify_secondary(self, factors: Dict, 
                         primary: MarketRegime) -> Optional[MarketRegime]:
        """Classify secondary regime characteristic"""
        vix = factors['vix']
        
        if primary in [MarketRegime.BULL, MarketRegime.STRONG_BULL]:
            if vix > 20:
                return MarketRegime.HIGH_VOLATILITY
        elif primary in [MarketRegime.BEAR, MarketRegime.STRONG_BEAR]:
            if vix > 30:
                return MarketRegime.HIGH_VOLATILITY
        
        return None
    
    def _calculate_regime_confidence(self, factors: Dict, 
                                    regime: MarketRegime) -> float:
        """Calculate confidence in regime classification"""
        confidences = []
        
        # VIX clarity
        vix = factors['vix']
        if vix > 35 or vix < 15:
            confidences.append(0.9)
        elif vix > 25 or vix < 18:
            confidences.append(0.75)
        else:
            confidences.append(0.6)
        
        # Trend clarity
        adx = factors['adx']
        if adx > 30:
            confidences.append(0.85)
        elif adx > 20:
            confidences.append(0.7)
        else:
            confidences.append(0.5)
        
        # Breadth clarity
        breadth = factors['breadth_ratio']
        if breadth > 0.65 or breadth < 0.35:
            confidences.append(0.8)
        else:
            confidences.append(0.6)
        
        return sum(confidences) / len(confidences)
    
    def _calculate_regime_duration(self, regime: MarketRegime) -> int:
        """Calculate how long we've been in this regime"""
        if not self.regime_history:
            return 1
        
        duration = 1
        for past in reversed(self.regime_history[:-1]):
            if past.primary_regime == regime:
                duration += 1
            else:
                break
        
        return duration
    
    def get_regime_recommendations(self, regime: RegimeState) -> Dict:
        """Get recommendations for current regime"""
        
        recommendations = {
            'favored_strategies': [],
            'avoid_strategies': [],
            'position_sizing_factor': 1.0,
            'confidence_adjustment': 0.0,
            'risk_multiplier': 1.0
        }
        
        if regime.primary_regime == MarketRegime.STRONG_BULL:
            recommendations['favored_strategies'] = ['momentum', 'trend_following', 'growth']
            recommendations['avoid_strategies'] = ['mean_reversion', 'short_selling']
            recommendations['position_sizing_factor'] = 1.2
            recommendations['confidence_adjustment'] = 0.05
            
        elif regime.primary_regime == MarketRegime.BULL:
            recommendations['favored_strategies'] = ['momentum', 'quality', 'value']
            recommendations['avoid_strategies'] = ['short_selling']
            recommendations['position_sizing_factor'] = 1.0
            
        elif regime.primary_regime == MarketRegime.BEAR:
            recommendations['favored_strategies'] = ['defensive', 'value', 'short_selling']
            recommendations['avoid_strategies'] = ['momentum', 'growth']
            recommendations['position_sizing_factor'] = 0.7
            recommendations['risk_multiplier'] = 1.3
            
        elif regime.primary_regime == MarketRegime.HIGH_VOLATILITY:
            recommendations['favored_strategies'] = ['mean_reversion', 'volatility_trading']
            recommendations['avoid_strategies'] = ['trend_following', 'momentum']
            recommendations['position_sizing_factor'] = 0.5
            recommendations['confidence_adjustment'] = -0.1
            recommendations['risk_multiplier'] = 1.5
            
        elif regime.primary_regime == MarketRegime.MEAN_REVERTING:
            recommendations['favored_strategies'] = ['mean_reversion', 'contrarian', 'stat_arb']
            recommendations['avoid_strategies'] = ['trend_following']
            recommendations['position_sizing_factor'] = 0.8
            
        elif regime.primary_regime == MarketRegime.LOW_VOLATILITY:
            recommendations['favored_strategies'] = ['quality', 'dividend', 'low_vol']
            recommendations['avoid_strategies'] = ['volatility_trading']
            recommendations['position_sizing_factor'] = 1.1
            recommendations['confidence_adjustment'] = 0.05
        
        return recommendations
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime detection"""
        if not self.current_regime:
            return {'status': 'no_regime_detected'}
        
        r = self.current_regime
        return {
            'primary_regime': r.primary_regime.value,
            'secondary_regime': r.secondary_regime.value if r.secondary_regime else None,
            'confidence': r.confidence,
            'duration_days': r.duration_days,
            'trend_direction': r.trend_direction,
            'volatility_regime': r.volatility_regime,
            'key_factors': r.factors
        }


# Global instance
regime_detector = RegimeDetector()
