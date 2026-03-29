"""
Quantitative/Statistical Analysis Agent
Applies statistical models and quantitative factors - independent stance
"""

from __future__ import annotations

import logging
import time
import numpy as np
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime
from scipy import stats

log = logging.getLogger(__name__)


@dataclass
class QuantitativeStance:
    """Quantitative analysis stance"""
    direction: str  # bullish, bearish, neutral
    conviction: float
    model_consensus: str  # bullish, bearish, neutral
    statistical_edge: float  # measured edge
    mean_reversion_signal: str  # overbought, oversold, neutral
    momentum_signal: str  # positive, negative, neutral
    volatility_regime: str  # low, normal, high
    factor_scores: Dict[str, float]
    model_predictions: Dict[str, float]
    confidence_interval: tuple  # (lower, upper)
    key_metrics: List[str]


class QuantitativeAnalysisAgent:
    """
    Quantitative Analysis Agent that applies statistical models and factor analysis.
    Independently determines stance based on quantitative signals and model outputs.
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "quantitative_analysis_agent"
        self.max_analysis_time = 60
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any],
                financial_context: Dict[str, Any]) -> QuantitativeStance:
        """Apply quantitative analysis and determine independent stance"""
        log.info(f"QuantAgent: Analyzing {symbol} with statistical models")
        start_time = time.time()
        
        try:
            historical = initial_data.get("historical", {})
            price_data = initial_data.get("price_data", {})
            fundamentals = initial_data.get("fundamentals", {})
            
            # Request historical price data for calculations
            hist_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="historical_prices",
                symbol=symbol,
                parameters={"period": "2y"},
                urgency="normal"
            )
            
            factor_scores = {}
            model_predictions = {}
            metrics = []
            
            # 1. Mean Reversion Analysis
            mr_score, mr_signal = self._analyze_mean_reversion(price_data, historical)
            factor_scores["mean_reversion"] = mr_score
            
            # 2. Momentum Analysis
            mom_score, mom_signal = self._analyze_momentum(historical, hist_data)
            factor_scores["momentum"] = mom_score
            
            # 3. Volatility Analysis
            vol_score, vol_regime = self._analyze_volatility(historical, financial_context)
            factor_scores["volatility"] = vol_score
            
            # 4. Statistical Arbitrage Signals
            arb_score = self._analyze_statistical_arbitrage(initial_data, hist_data)
            factor_scores["stat_arb"] = arb_score
            
            # 5. Factor Model Scores
            value_score = self._calculate_value_factor(fundamentals)
            quality_score = self._calculate_quality_factor(fundamentals)
            growth_score = self._calculate_growth_factor(fundamentals)
            
            factor_scores["value"] = value_score
            factor_scores["quality"] = quality_score
            factor_scores["growth"] = growth_score
            
            # 6. Multi-Factor Model
            # Combine factors with weights
            factor_weights = {
                "value": 0.20,
                "quality": 0.20,
                "growth": 0.15,
                "momentum": 0.20,
                "mean_reversion": 0.15,
                "volatility": 0.10
            }
            
            multi_factor_score = sum(
                factor_scores.get(f, 0) * w for f, w in factor_weights.items()
            )
            
            model_predictions["multi_factor"] = multi_factor_score
            
            # Calculate confidence interval
            current_price = price_data.get("current_price", 0)
            volatility = historical.get("volatility", 0.20)
            
            if current_price > 0:
                std_dev = current_price * volatility / np.sqrt(252)  # Daily vol
                confidence_interval = (
                    current_price - 1.96 * std_dev,
                    current_price + 1.96 * std_dev
                )
            else:
                confidence_interval = (0, 0)
            
            # Determine model consensus
            if multi_factor_score > 0.3:
                model_consensus = "bullish"
            elif multi_factor_score < -0.3:
                model_consensus = "bearish"
            else:
                model_consensus = "neutral"
            
            # Calculate statistical edge
            statistical_edge = abs(multi_factor_score)
            
            # Determine final stance
            # Weight momentum and mean reversion
            if mom_score > 0.3 and mr_score > 0.2:
                direction = "bullish"
            elif mom_score < -0.3 and mr_score < -0.2:
                direction = "bearish"
            elif multi_factor_score > 0.25:
                direction = "bullish"
            elif multi_factor_score < -0.25:
                direction = "bearish"
            else:
                direction = "neutral"
            
            conviction = min(0.95, statistical_edge + 0.2)
            
            # Build metrics
            metrics.append(f"Multi-factor score: {multi_factor_score:.3f}")
            metrics.append(f"Value factor: {value_score:.3f}")
            metrics.append(f"Quality factor: {quality_score:.3f}")
            metrics.append(f"Momentum factor: {mom_score:.3f}")
            metrics.append(f"Mean reversion: {mr_signal}")
            
            analysis_time = time.time() - start_time
            log.info(f"QuantAgent: {direction} stance (edge: {statistical_edge:.3f})")
            
            return QuantitativeStance(
                direction=direction,
                conviction=conviction,
                model_consensus=model_consensus,
                statistical_edge=statistical_edge,
                mean_reversion_signal=mr_signal,
                momentum_signal="positive" if mom_score > 0.2 else "negative" if mom_score < -0.2 else "neutral",
                volatility_regime=vol_regime,
                factor_scores=factor_scores,
                model_predictions=model_predictions,
                confidence_interval=confidence_interval,
                key_metrics=metrics
            )
            
        except Exception as e:
            log.error(f"QuantAgent: Analysis error: {e}")
            return QuantitativeStance(
                direction="neutral",
                conviction=0.4,
                model_consensus="neutral",
                statistical_edge=0,
                mean_reversion_signal="neutral",
                momentum_signal="neutral",
                volatility_regime="normal",
                factor_scores={},
                model_predictions={},
                confidence_interval=(0, 0),
                key_metrics=["Analysis error - limited quantitative assessment"]
            )
    
    def _analyze_mean_reversion(self, price_data: Dict, historical: Dict) -> tuple:
        """Analyze mean reversion potential"""
        current = price_data.get("current_price", 0)
        high_52w = price_data.get("fifty_two_week_high", 0)
        low_52w = price_data.get("fifty_two_week_low", 0)
        
        if current > 0 and high_52w > 0 and low_52w > 0:
            range_position = (current - low_52w) / (high_52w - low_52w)
            
            if range_position > 0.9:
                score = -0.4  # Overbought - mean reversion down
                signal = "overbought"
            elif range_position < 0.1:
                score = 0.4  # Oversold - mean reversion up
                signal = "oversold"
            elif range_position > 0.7:
                score = -0.2
                signal = "elevated"
            elif range_position < 0.3:
                score = 0.2
                signal = "depressed"
            else:
                score = 0.0
                signal = "neutral"
        else:
            score = 0.0
            signal = "neutral"
        
        return score, signal
    
    def _analyze_momentum(self, historical: Dict, hist_data: Dict) -> tuple:
        """Analyze price momentum"""
        trend = historical.get("trend_6m", "sideways")
        volatility = historical.get("volatility", 0.20)
        
        if trend == "up":
            score = 0.3
            signal = "positive"
        elif trend == "down":
            score = -0.3
            signal = "negative"
        else:
            score = 0.0
            signal = "neutral"
        
        # Adjust for volatility
        if volatility > 0.35:
            # High volatility momentum is less reliable
            score *= 0.7
        
        return score, signal
    
    def _analyze_volatility(self, historical: Dict, financial_context: Dict) -> tuple:
        """Analyze volatility regime"""
        volatility = historical.get("volatility", 0.20)
        vix = financial_context.get("vix_level", 20)
        
        if volatility > 0.40 or vix > 30:
            regime = "high"
            score = -0.2  # High vol reduces predictability
        elif volatility < 0.15 and vix < 18:
            regime = "low"
            score = 0.1  # Low vol can mean complacency
        else:
            regime = "normal"
            score = 0.0
        
        return score, regime
    
    def _analyze_statistical_arbitrage(self, initial_data: Dict, hist_data: Dict) -> float:
        """Look for statistical arbitrage signals"""
        # Would analyze correlations, cointegration, etc.
        # For now, return neutral
        return 0.0
    
    def _calculate_value_factor(self, fundamentals: Dict) -> float:
        """Calculate value factor score"""
        scores = []
        
        pe = fundamentals.get("pe_ratio")
        if pe and pe > 0:
            if pe < 12:
                scores.append(0.4)
            elif pe < 18:
                scores.append(0.2)
            elif pe > 30:
                scores.append(-0.3)
        
        pb = fundamentals.get("price_to_book")
        if pb and pb > 0:
            if pb < 2:
                scores.append(0.3)
            elif pb > 5:
                scores.append(-0.2)
        
        ps = fundamentals.get("price_to_sales")
        if ps and ps > 0:
            if ps < 2:
                scores.append(0.3)
            elif ps > 10:
                scores.append(-0.3)
        
        return np.mean(scores) if scores else 0.0
    
    def _calculate_quality_factor(self, fundamentals: Dict) -> float:
        """Calculate quality factor score"""
        scores = []
        
        roe = fundamentals.get("return_on_equity")
        if roe:
            if roe > 0.20:
                scores.append(0.4)
            elif roe > 0.15:
                scores.append(0.2)
            elif roe < 0.08:
                scores.append(-0.2)
        
        roa = fundamentals.get("return_on_assets")
        if roa:
            if roa > 0.10:
                scores.append(0.3)
            elif roa < 0.04:
                scores.append(-0.2)
        
        margins = fundamentals.get("profit_margins")
        if margins:
            if margins > 0.20:
                scores.append(0.3)
            elif margins < 0.05:
                scores.append(-0.2)
        
        return np.mean(scores) if scores else 0.0
    
    def _calculate_growth_factor(self, fundamentals: Dict) -> float:
        """Calculate growth factor score"""
        scores = []
        
        rev_growth = fundamentals.get("revenue_growth")
        if rev_growth is not None:
            if rev_growth > 0.20:
                scores.append(0.4)
            elif rev_growth > 0.10:
                scores.append(0.2)
            elif rev_growth < 0:
                scores.append(-0.3)
        
        earnings_growth = fundamentals.get("earnings_growth")
        if earnings_growth is not None:
            if earnings_growth > 0.25:
                scores.append(0.4)
            elif earnings_growth < 0:
                scores.append(-0.3)
        
        return np.mean(scores) if scores else 0.0
    
    def argue(self, stance: QuantitativeStance, opponent_points: List[str] = None) -> Dict[str, Any]:
        """Generate argument based on quantitative stance"""
        points = []
        
        # Model consensus
        points.append(f"Multi-factor model: {stance.model_consensus.upper()} (score: {stance.model_predictions.get('multi_factor', 0):.3f})")
        
        # Factor breakdown
        for factor, score in stance.factor_scores.items():
            points.append(f"{factor.replace('_', ' ').title()}: {score:.3f}")
        
        # Signals
        points.append(f"Mean reversion signal: {stance.mean_reversion_signal.upper()}")
        points.append(f"Momentum signal: {stance.momentum_signal.upper()}")
        points.append(f"Volatility regime: {stance.volatility_regime.upper()}")
        
        # Statistical edge
        points.append(f"Statistical edge: {stance.statistical_edge:.2%}")
        
        # Confidence interval
        lower, upper = stance.confidence_interval
        if lower > 0 and upper > 0:
            points.append(f"95% confidence interval: ${lower:.2f} - ${upper:.2f}")
        
        # Directional stance
        if stance.direction == "bullish":
            points.append(f"Quantitative models support {stance.conviction*100:.0f}% bullish view")
            if stance.mean_reversion_signal == "oversold":
                points.append("Mean reversion suggests bounce potential")
            if stance.momentum_signal == "positive":
                points.append("Momentum confirms upward trajectory")
        elif stance.direction == "bearish":
            points.append(f"Quantitative warning signals warrant {stance.conviction*100:.0f}% bearish caution")
            if stance.mean_reversion_signal == "overbought":
                points.append("Mean reversion suggests correction risk")
            if stance.momentum_signal == "negative":
                points.append("Momentum confirms downward pressure")
        else:
            points.append("Quantitative factors neutral - no statistical edge detected")
        
        return {
            "agent": self.agent_id,
            "stance": stance.direction,
            "conviction": stance.conviction,
            "statistical_edge": stance.statistical_edge,
            "model_consensus": stance.model_consensus,
            "factor_scores": stance.factor_scores,
            "mean_reversion": stance.mean_reversion_signal,
            "momentum": stance.momentum_signal,
            "volatility_regime": stance.volatility_regime,
            "points": points,
            "timestamp": datetime.now().isoformat()
        }
