"""
Risk Scanner - Identifies dangerous stocks to avoid
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .data import load_ohlcv
from .stock_intel_agent import StockIntelAgent

log = logging.getLogger(__name__)


class RiskScanner:
    """Detects dangerous stocks that investors should avoid"""
    
    def __init__(self):
        self.stock_intel = StockIntelAgent()
    
    def _calculate_volatility_risk(self, symbol: str, period: str = "3mo") -> Dict[str, float]:
        """Calculate volatility-based risk metrics"""
        try:
            ohlcv, _ = load_ohlcv(symbol, period=period)
            if ohlcv.empty:
                return {"vol_risk": 0.5, "vol_spike": False}
            
            close = ohlcv["close"]
            volume = ohlcv["volume"]
            
            # Daily volatility
            daily_returns = close.pct_change().dropna()
            daily_vol = daily_returns.std()
            
            # Annualized volatility
            ann_vol = daily_vol * np.sqrt(252)
            
            # Volatility spike detection (recent vs historical)
            recent_vol = daily_returns.tail(20).std()
            historical_vol = daily_returns.head(len(daily_returns) - 20).std() if len(daily_returns) > 20 else recent_vol
            vol_spike_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
            
            # Volume volatility
            volume_vol = volume.pct_change().std()
            
            # Risk score based on volatility
            vol_risk = min(ann_vol / 0.5, 1.0)  # 50% annual vol = max risk
            
            return {
                "vol_risk": round(vol_risk, 3),
                "ann_volatility": round(ann_vol, 3),
                "vol_spike": vol_spike_ratio > 2.0,
                "vol_spike_ratio": round(vol_spike_ratio, 2),
                "volume_volatility": round(volume_vol, 3)
            }
            
        except Exception as e:
            log.warning(f"Error calculating volatility risk for {symbol}: {e}")
            return {"vol_risk": 0.5, "vol_spike": False}
    
    def _calculate_fundamental_risk(self, intel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate fundamental quality risk"""
        try:
            fundamentals = intel_data.get("fundamentals", {})
            
            risk_factors = []
            risk_score = 0.0
            
            # No earnings (negative or zero PE)
            pe_ratio = fundamentals.get("trailingPE", 0)
            if pe_ratio is None or pe_ratio <= 0:
                risk_factors.append("No positive earnings")
                risk_score += 0.3
            
            # Extremely high PE ratio
            elif pe_ratio > 100:
                risk_factors.append("Extremely high P/E ratio")
                risk_score += 0.2
            
            # High debt (if data available)
            debt_to_equity = fundamentals.get("debtToEquity")
            if debt_to_equity is not None and debt_to_equity > 2.0:
                risk_factors.append("High debt-to-equity ratio")
                risk_score += 0.2
            
            # Low liquidity ratios
            current_ratio = fundamentals.get("currentRatio")
            if current_ratio is not None and current_ratio < 1.0:
                risk_factors.append("Low current ratio (liquidity risk)")
                risk_score += 0.15
            
            # Negative margins
            profit_margins = fundamentals.get("profitMargins")
            if profit_margins is not None and profit_margins < 0:
                risk_factors.append("Negative profit margins")
                risk_score += 0.25
            
            # No revenue or negative growth
            revenue_growth = fundamentals.get("revenueGrowth")
            if revenue_growth is not None and revenue_growth < -0.2:
                risk_factors.append("Declining revenue")
                risk_score += 0.2
            
            # High short interest (potential short squeeze)
            short_percent = fundamentals.get("shortPercentOfFloat")
            if short_percent is not None and short_percent > 0.2:
                risk_factors.append("High short interest")
                risk_score += 0.1
            
            return {
                "fundamental_risk": round(min(risk_score, 1.0), 3),
                "risk_factors": risk_factors,
                "pe_ratio": pe_ratio,
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
                "profit_margins": profit_margins,
                "revenue_growth": revenue_growth,
                "short_percent": short_percent
            }
            
        except Exception as e:
            log.warning(f"Error calculating fundamental risk: {e}")
            return {"fundamental_risk": 0.5, "risk_factors": ["Data unavailable"]}
    
    def _calculate_liquidity_trap_risk(self, symbol: str, intel_data: Dict[str, Any]) -> Dict[str, float]:
        """Detect liquidity trap risk"""
        try:
            fundamentals = intel_data.get("fundamentals", {})
            
            # Low average volume
            avg_volume = fundamentals.get("averageVolume", 0)
            volume_risk = 1.0 - min(avg_volume / 100_000, 1.0)  # < 100k daily vol = risky
            
            # Low float shares
            float_shares = fundamentals.get("floatShares", 0)
            market_cap = fundamentals.get("marketCap", 1)
            
            if float_shares > 0 and market_cap > 0:
                float_ratio = float_shares / market_cap
                float_risk = 1.0 - min(float_ratio, 1.0)  # Low float % = risky
            else:
                float_risk = 0.5
            
            # Bid-ask spread proxy (using price and volume)
            current_price = fundamentals.get("currentPrice", 1)
            if current_price > 0 and avg_volume > 0:
                # Higher price + lower volume = wider spreads likely
                spread_proxy = (current_price / avg_volume) * 1000
                spread_risk = min(spread_proxy / 10, 1.0)
            else:
                spread_risk = 0.5
            
            # Combined liquidity risk
            liquidity_risk = (
                volume_risk * 0.4 +
                float_risk * 0.3 +
                spread_risk * 0.3
            )
            
            return {
                "liquidity_risk": round(liquidity_risk, 3),
                "volume_risk": round(volume_risk, 3),
                "float_risk": round(float_risk, 3),
                "spread_risk": round(spread_risk, 3),
                "avg_volume": avg_volume,
                "float_shares": float_shares
            }
            
        except Exception as e:
            log.warning(f"Error calculating liquidity risk for {symbol}: {e}")
            return {"liquidity_risk": 0.5}
    
    def _detect_hype_vs_fundamentals(self, symbol: str, intel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect stocks with hype but weak fundamentals"""
        try:
            fundamentals = intel_data.get("fundamentals", {})
            history = intel_data.get("recent_history", {})
            
            hype_indicators = []
            fundamental_weakness = []
            hype_score = 0.0
            fundamental_score = 0.0
            
            # Hype indicators
            # High volatility without fundamentals
            vol_ann = history.get("vol_ann_hint", 0.2)
            if vol_ann > 0.6:
                hype_indicators.append("Extreme volatility")
                hype_score += 0.3
            
            # Recent price surge without earnings
            return_total = history.get("return_total", 0)
            pe_ratio = fundamentals.get("trailingPE", 0)
            if return_total > 0.5 and (pe_ratio is None or pe_ratio <= 0):
                hype_indicators.append("Price surge without earnings")
                hype_score += 0.4
            
            # High beta (speculative behavior)
            beta = fundamentals.get("beta", 1.0)
            if beta > 2.0:
                hype_indicators.append("Very high beta (speculative)")
                hype_score += 0.2
            
            # Weak fundamentals
            if pe_ratio is None or pe_ratio <= 0:
                fundamental_weakness.append("No earnings")
                fundamental_score += 0.4
            
            profit_margins = fundamentals.get("profitMargins")
            if profit_margins is not None and profit_margins < 0:
                fundamental_weakness.append("Negative margins")
                fundamental_score += 0.3
            
            revenue_growth = fundamentals.get("revenueGrowth")
            if revenue_growth is not None and revenue_growth < -0.1:
                fundamental_weakness.append("Declining revenue")
                fundamental_score += 0.3
            
            # Hype vs fundamentals mismatch
            mismatch_score = max(0, hype_score - fundamental_score)
            
            return {
                "hype_score": round(min(hype_score, 1.0), 3),
                "fundamental_score": round(min(fundamental_score, 1.0), 3),
                "mismatch_score": round(mismatch_score, 3),
                "hype_indicators": hype_indicators,
                "fundamental_weakness": fundamental_weakness,
                "is_hype_driven": mismatch_score > 0.3
            }
            
        except Exception as e:
            log.warning(f"Error detecting hype vs fundamentals for {symbol}: {e}")
            return {"mismatch_score": 0.0, "is_hype_driven": False}
    
    def _calculate_price_pattern_risk(self, symbol: str) -> Dict[str, Any]:
        """Detect dangerous price patterns"""
        try:
            ohlcv, _ = load_ohlcv(symbol, period="3mo")
            if ohlcv.empty:
                return {"pattern_risk": 0.5}
            
            close = ohlcv["close"]
            volume = ohlcv["volume"]
            
            # Pump and dump pattern detection
            # Sharp rise followed by sharp decline with high volume
            price_changes = close.pct_change()
            
            # Look for large up moves followed by large down moves
            large_up_days = (price_changes > 0.15).sum()
            large_down_days = (price_changes < -0.15).sum()
            
            # Recent crash pattern
            recent_max = close.rolling(20).max().shift(1)
            current_vs_recent_max = (close.iloc[-1] - recent_max.iloc[-1]) / recent_max.iloc[-1]
            crash_pattern = current_vs_recent_max < -0.3
            
            # Volume spike on down days (distribution)
            down_days = price_changes < 0
            volume_on_down_days = volume[down_days]
            avg_down_volume = volume_on_down_days.mean() if len(volume_on_down_days) > 0 else 0
            avg_total_volume = volume.mean()
            
            distribution_volume = avg_down_volume / avg_total_volume if avg_total_volume > 0 else 1.0
            
            pattern_risk = 0.0
            risk_patterns = []
            
            if large_up_days > 3 and large_down_days > 3:
                pattern_risk += 0.3
                risk_patterns.append("High volatility with large swings")
            
            if crash_pattern:
                pattern_risk += 0.4
                risk_patterns.append("Recent crash pattern detected")
            
            if distribution_volume > 1.5:
                pattern_risk += 0.3
                risk_patterns.append("High volume on down days (distribution)")
            
            return {
                "pattern_risk": round(min(pattern_risk, 1.0), 3),
                "risk_patterns": risk_patterns,
                "crash_pattern": crash_pattern,
                "distribution_volume": round(distribution_volume, 2),
                "large_swings": large_up_days + large_down_days
            }
            
        except Exception as e:
            log.warning(f"Error calculating price pattern risk for {symbol}: {e}")
            return {"pattern_risk": 0.5}
    
    def analyze_stock_risk(self, symbol: str) -> Dict[str, Any]:
        """Comprehensive risk analysis for a single stock"""
        try:
            # Get stock intelligence data
            intel_data = self.stock_intel.gather(symbol)
            
            # Calculate all risk components
            vol_risk = self._calculate_volatility_risk(symbol)
            fund_risk = self._calculate_fundamental_risk(intel_data)
            liq_risk = self._calculate_liquidity_trap_risk(symbol, intel_data)
            hype_risk = self._detect_hype_vs_fundamentals(symbol, intel_data)
            pattern_risk = self._calculate_price_pattern_risk(symbol)
            
            # Calculate overall risk score
            overall_risk = (
                vol_risk.get("vol_risk", 0.5) * 0.25 +
                fund_risk.get("fundamental_risk", 0.5) * 0.25 +
                liq_risk.get("liquidity_risk", 0.5) * 0.2 +
                hype_risk.get("mismatch_score", 0.0) * 0.15 +
                pattern_risk.get("pattern_risk", 0.5) * 0.15
            )
            
            # Determine if stock is dangerous
            is_dangerous = overall_risk > 0.7
            
            # Generate risk warnings
            warnings = []
            
            if vol_risk.get("vol_spike", False):
                warnings.append("🚨 Volatility spike detected")
            
            if fund_risk.get("fundamental_risk", 0) > 0.6:
                warnings.extend([f"⚠️ {factor}" for factor in fund_risk.get("risk_factors", [])])
            
            if liq_risk.get("liquidity_risk", 0) > 0.7:
                warnings.append("⚠️ Low liquidity - trading risks")
            
            if hype_risk.get("is_hype_driven", False):
                warnings.append("🚨 Hype-driven without fundamentals")
            
            if pattern_risk.get("crash_pattern", False):
                warnings.append("🚨 Recent crash pattern")
            
            # Risk level classification
            if overall_risk > 0.8:
                risk_level = "EXTREME"
            elif overall_risk > 0.6:
                risk_level = "HIGH"
            elif overall_risk > 0.4:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"
            
            return {
                "symbol": symbol,
                "overall_risk_score": round(overall_risk, 3),
                "risk_level": risk_level,
                "is_dangerous": is_dangerous,
                "risk_components": {
                    "volatility": vol_risk,
                    "fundamentals": fund_risk,
                    "liquidity": liq_risk,
                    "hype_vs_fundamentals": hype_risk,
                    "price_patterns": pattern_risk
                },
                "warnings": warnings,
                "recommendation": self._generate_risk_recommendation(overall_risk, is_dangerous, warnings),
                "fundamentals": {
                    "market_cap": intel_data.fundamentals.get("marketCap", 0),
                    "current_price": intel_data.fundamentals.get("currentPrice", 0),
                    "beta": intel_data.fundamentals.get("beta", 0),
                    "avg_volume": intel_data.fundamentals.get("averageVolume", 0)
                }
            }
            
        except Exception as e:
            log.error(f"Error analyzing risk for {symbol}: {e}")
            return {
                "symbol": symbol,
                "overall_risk_score": 0.5,
                "risk_level": "UNKNOWN",
                "is_dangerous": False,
                "error": str(e)
            }
    
    def _generate_risk_recommendation(self, risk_score: float, is_dangerous: bool, warnings: List[str]) -> str:
        """Generate risk recommendation based on analysis"""
        if is_dangerous and len(warnings) >= 3:
            return "STRONG SELL - Multiple serious risk factors detected"
        elif is_dangerous:
            return "AVOID - High risk stock with warning signs"
        elif risk_score > 0.6:
            return "CAUTION - Elevated risk, monitor closely"
        elif risk_score > 0.4:
            return "HOLD - Moderate risk, suitable for risk-tolerant investors"
        else:
            return "MONITOR - Low to moderate risk"
    
    def scan_market_risks(self, symbols: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Scan multiple stocks for dangerous patterns"""
        results = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_stock_risk(symbol)
                if analysis.get("is_dangerous", False) or analysis.get("overall_risk_score", 0) > 0.6:
                    results.append(analysis)
            except Exception as e:
                log.warning(f"Failed to analyze risk for {symbol}: {e}")
                continue
        
        # Sort by risk score (highest risk first)
        results.sort(key=lambda x: x.get("overall_risk_score", 0), reverse=True)
        
        return results[:limit]
    
    def get_market_candidates(self) -> List[str]:
        """Get list of stocks to scan for risks"""
        # Include a mix of large caps, mid caps, and some speculative stocks
        candidates = [
            # Large caps
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA",
            # Mid caps
            "PLTR", "GME", "AMC", "BB", "NOK", "SNDL",
            # Some known speculative stocks
            "MVIS", "SPCE", "RKDA", "IRBT", "TLRY",
            # Traditional stocks
            "JPM", "BAC", "WFC", "XOM", "CVX", "KO", "PEP"
        ]
        return candidates
