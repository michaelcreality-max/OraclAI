"""
Technical Analysis Agent
Analyzes charts, patterns, and technical indicators - decides stance independently
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class TechnicalStance:
    """Technical analysis stance with conviction"""
    direction: str  # bullish, bearish, neutral
    conviction: float  # 0-1
    price_target: float
    stop_loss: float
    key_signals: List[str]
    timeframe: str  # short, medium, long
    confidence_factors: Dict[str, float]


class TechnicalAnalysisAgent:
    """
    Technical Analysis Agent that independently analyzes charts and decides stance.
    NOT pre-assigned to be bullish or bearish - evaluates objectively.
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "technical_analysis_agent"
        self.max_analysis_time = 60
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any],
                financial_context: Dict[str, Any]) -> TechnicalStance:
        """Analyze technical indicators and decide independent stance"""
        log.info(f"TechnicalAgent: Analyzing {symbol}")
        start_time = time.time()
        
        try:
            price_data = initial_data.get("price_data", {})
            historical = initial_data.get("historical", {})
            
            # Request additional technical data
            hist_1y = self._request_historical_data(symbol, "1y")
            
            signals = []
            confidence_factors = {}
            
            # 1. Trend Analysis
            trend_score, trend_signals = self._analyze_trend(historical, hist_1y)
            signals.extend(trend_signals)
            confidence_factors["trend"] = abs(trend_score)
            
            # 2. Support/Resistance
            s_r_score, s_r_signals = self._analyze_support_resistance(price_data, historical)
            signals.extend(s_r_signals)
            confidence_factors["support_resistance"] = abs(s_r_score)
            
            # 3. Volume Analysis
            vol_score, vol_signals = self._analyze_volume(price_data, initial_data)
            signals.extend(vol_signals)
            confidence_factors["volume"] = abs(vol_score)
            
            # 4. Volatility Assessment
            vol_assessment = self._assess_volatility(historical, financial_context)
            confidence_factors["volatility_regime"] = vol_assessment["confidence"]
            
            # 5. Pattern Recognition
            pattern_score, pattern_signals = self._recognize_patterns(hist_1y)
            signals.extend(pattern_signals)
            confidence_factors["patterns"] = abs(pattern_score)
            
            # Calculate overall stance
            total_score = trend_score + s_r_score + vol_score + pattern_score
            avg_confidence = np.mean(list(confidence_factors.values())) if confidence_factors else 0.5
            
            # Determine direction based on total score
            if total_score > 0.3:
                direction = "bullish"
            elif total_score < -0.3:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # Calculate price targets based on ATR or volatility
            current_price = price_data.get("current_price", 0)
            volatility = historical.get("volatility", 0.20)
            
            if direction == "bullish":
                price_target = current_price * (1 + volatility * 2)
                stop_loss = current_price * (1 - volatility * 0.5)
            elif direction == "bearish":
                price_target = current_price * (1 - volatility * 2)
                stop_loss = current_price * (1 + volatility * 0.5)
            else:
                price_target = current_price * 1.02
                stop_loss = current_price * 0.98
            
            analysis_time = time.time() - start_time
            log.info(f"TechnicalAgent: {direction} stance with {avg_confidence:.2f} conviction")
            
            return TechnicalStance(
                direction=direction,
                conviction=avg_confidence,
                price_target=price_target,
                stop_loss=stop_loss,
                key_signals=signals[:8],  # Top 8 signals
                timeframe=self._determine_timeframe(historical),
                confidence_factors=confidence_factors
            )
            
        except Exception as e:
            log.error(f"TechnicalAgent: Analysis error: {e}")
            return TechnicalStance(
                direction="neutral",
                conviction=0.5,
                price_target=0,
                stop_loss=0,
                key_signals=["Analysis error - defaulting to neutral"],
                timeframe="medium",
                confidence_factors={}
            )
    
    def _request_historical_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Request historical price data"""
        try:
            response = self.data_collection(
                agent_id=self.agent_id,
                request_type="historical_prices",
                symbol=symbol,
                parameters={"period": period},
                urgency="normal"
            )
            return response
        except:
            return {}
    
    def _analyze_trend(self, historical: Dict, hist_1y: Dict) -> tuple:
        """Analyze price trend"""
        score = 0
        signals = []
        
        trend_6m = historical.get("trend_6m", "sideways")
        if trend_6m == "up":
            score += 0.25
            signals.append("6-month uptrend established")
        elif trend_6m == "down":
            score -= 0.25
            signals.append("6-month downtrend in progress")
        
        return score, signals
    
    def _analyze_support_resistance(self, price_data: Dict, historical: Dict) -> tuple:
        """Analyze support and resistance levels"""
        score = 0
        signals = []
        
        current = price_data.get("current_price", 0)
        high_52w = price_data.get("fifty_two_week_high", 0)
        low_52w = price_data.get("fifty_two_week_low", 0)
        
        if current > 0 and high_52w > 0 and low_52w > 0:
            range_position = (current - low_52w) / (high_52w - low_52w)
            
            if range_position > 0.8:
                score -= 0.2
                signals.append("Near 52-week highs - resistance likely")
            elif range_position < 0.2:
                score += 0.2
                signals.append("Near 52-week lows - potential reversal zone")
            elif 0.4 < range_position < 0.6:
                signals.append("Mid-range - balanced risk/reward")
        
        return score, signals
    
    def _analyze_volume(self, price_data: Dict, initial_data: Dict) -> tuple:
        """Analyze volume patterns"""
        score = 0
        signals = []
        
        volume = price_data.get("volume", 0)
        avg_volume = price_data.get("average_volume", 0)
        
        if volume > 0 and avg_volume > 0:
            vol_ratio = volume / avg_volume
            
            if vol_ratio > 2.0:
                score += 0.15
                signals.append(f"Heavy volume surge ({vol_ratio:.1f}x avg) - strong interest")
            elif vol_ratio > 1.5:
                score += 0.10
                signals.append(f"Above average volume ({vol_ratio:.1f}x)")
            elif vol_ratio < 0.5:
                score -= 0.10
                signals.append("Low volume - weak conviction")
        
        return score, signals
    
    def _assess_volatility(self, historical: Dict, financial_context: Dict) -> Dict:
        """Assess volatility regime"""
        volatility = historical.get("volatility", 0.20)
        vix = financial_context.get("vix_level", 20)
        
        if volatility > 0.40 or vix > 30:
            return {"regime": "high_volatility", "confidence": 0.8}
        elif volatility < 0.15 and vix < 18:
            return {"regime": "low_volatility", "confidence": 0.7}
        else:
            return {"regime": "normal_volatility", "confidence": 0.5}
    
    def _recognize_patterns(self, hist_1y: Dict) -> tuple:
        """Recognize chart patterns"""
        score = 0
        signals = []
        
        # Placeholder for pattern recognition
        # In production, this would analyze actual price data
        
        return score, signals
    
    def _determine_timeframe(self, historical: Dict) -> str:
        """Determine optimal trading timeframe"""
        volatility = historical.get("volatility", 0.20)
        
        if volatility > 0.35:
            return "short"  # High vol = shorter timeframe
        elif volatility < 0.15:
            return "long"   # Low vol = longer timeframe
        else:
            return "medium"
    
    def argue(self, stance: TechnicalStance, opponent_points: List[str] = None) -> Dict[str, Any]:
        """Generate argument based on technical stance"""
        points = stance.key_signals.copy()
        
        # Add stance-specific commentary
        if stance.direction == "bullish":
            points.append(f"Technical setup suggests {stance.conviction*100:.0f}% confidence in upside")
            points.append(f"Price target: ${stance.price_target:.2f}, Stop: ${stance.stop_loss:.2f}")
        elif stance.direction == "bearish":
            points.append(f"Technical breakdown with {stance.conviction*100:.0f}% confidence")
            points.append(f"Downside target: ${stance.price_target:.2f}, Stop: ${stance.stop_loss:.2f}")
        else:
            points.append("No clear technical edge - sideways action expected")
        
        # Address opponents
        if opponent_points:
            for opp in opponent_points:
                opp_lower = opp.lower()
                if "fundamental" in opp_lower and stance.direction != "neutral":
                    points.append("Technical setup confirms/disagrees with fundamental view")
        
        return {
            "agent": self.agent_id,
            "stance": stance.direction,  # Dynamic stance
            "conviction": stance.conviction,
            "price_target": stance.price_target,
            "stop_loss": stance.stop_loss,
            "timeframe": stance.timeframe,
            "points": points,
            "confidence_factors": stance.confidence_factors,
            "timestamp": datetime.now().isoformat()
        }
