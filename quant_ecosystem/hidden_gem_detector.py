"""
Hidden Gem Detector - Finds undiscovered stock opportunities
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

from .data import load_ohlcv
from .features import build_feature_matrix
from .stock_intel_agent import StockIntelAgent

log = logging.getLogger(__name__)


class HiddenGemDetector:
    """Detects stocks with strong signals but low attention"""
    
    def __init__(self):
        self.stock_intel = StockIntelAgent()
    
    def _calculate_attention_score(self, symbol: str, intel_data: Dict[str, Any]) -> float:
        """Calculate how much attention a stock is getting (lower = more hidden)"""
        try:
            fundamentals = intel_data.get("fundamentals", {})
            history = intel_data.get("recent_history", {})
            
            # Volume-based attention (lower volume = less attention)
            avg_volume = fundamentals.get("averageVolume", 0)
            volume_score = 1.0 - min(avg_volume / 1_000_000, 1.0)  # Normalize to 0-1
            
            # Market cap based attention (smaller caps often less covered)
            market_cap = fundamentals.get("marketCap", 0)
            if market_cap == 0:
                cap_score = 0.5
            elif market_cap < 1_000_000_000:  # < 1B
                cap_score = 0.8
            elif market_cap < 10_000_000_000:  # < 10B
                cap_score = 0.6
            else:
                cap_score = 0.2
            
            # Analyst coverage proxy (fewer analysts = less attention)
            # Using beta and PE ratio as proxies for coverage
            beta = fundamentals.get("beta", 1.0)
            pe_ratio = fundamentals.get("trailingPE", 0)
            
            coverage_score = 0.5
            if beta == 0 or pe_ratio == 0:
                coverage_score = 0.8  # No data = likely low coverage
            else:
                coverage_score = 0.3  # Has basic metrics
            
            # Recent volatility (unusual activity might indicate discovery)
            vol_annual = history.get("vol_ann_hint", 0.2)
            volatility_score = min(vol_annual / 0.5, 1.0)  # Higher vol = more attention
            
            # Combine scores (lower = more hidden)
            attention_score = (
                volume_score * 0.3 +
                cap_score * 0.3 +
                coverage_score * 0.2 +
                (1.0 - volatility_score) * 0.2
            )
            
            return attention_score
            
        except Exception as e:
            log.warning(f"Error calculating attention score for {symbol}: {e}")
            return 0.5  # Default medium attention
    
    def _calculate_momentum_score(self, symbol: str, period: str = "6mo") -> float:
        """Calculate rising momentum score"""
        try:
            ohlcv, _ = load_ohlcv(symbol, period=period)
            if ohlcv.empty:
                return 0.0
            
            close = ohlcv["close"]
            
            # Price momentum
            price_momentum = (close.iloc[-1] / close.iloc[0] - 1) if len(close) > 1 else 0.0
            
            # Volume momentum (rising volume on up days)
            volume = ohlcv["volume"]
            volume_trend = np.polyfit(range(len(volume)), volume, 1)[0]
            volume_momentum = min(volume_trend / volume.mean(), 1.0) if volume.mean() > 0 else 0.0
            
            # Moving average convergence
            short_ma = close.rolling(20).mean()
            long_ma = close.rolling(50).mean()
            ma_convergence = (short_ma.iloc[-1] - long_ma.iloc[-1]) / long_ma.iloc[-1] if long_ma.iloc[-1] > 0 else 0.0
            
            # RSI momentum
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_momentum = (rsi.iloc[-1] - 50) / 50  # -1 to 1 scale
            
            # Combine momentum scores
            momentum_score = (
                min(price_momentum * 2, 1.0) * 0.4 +  # Price momentum weighted higher
                max(0, volume_momentum) * 0.3 +
                min(max(ma_convergence * 10, 0), 1.0) * 0.2 +
                max(0, rsi_momentum) * 0.1
            )
            
            return max(0, min(momentum_score, 1.0))
            
        except Exception as e:
            log.warning(f"Error calculating momentum for {symbol}: {e}")
            return 0.0
    
    def _calculate_sentiment_shift(self, symbol: str) -> float:
        """Proxy for sentiment shift using price action patterns"""
        try:
            ohlcv, _ = load_ohlcv(symbol, period="3mo")
            if ohlcv.empty:
                return 0.0
            
            close = ohlcv["close"]
            volume = ohlcv["volume"]
            
            # Recent breakout detection
            high_20d = close.rolling(20).max()
            current_vs_high = (close.iloc[-1] - high_20d.iloc[-2]) / high_20d.iloc[-2]
            breakout_score = max(0, current_vs_high * 20)  # Scale up significance
            
            # Volume surge on recent up days
            recent_volume = volume.tail(10).mean()
            historical_volume = volume.head(len(volume) - 10).mean() if len(volume) > 10 else recent_volume
            volume_surge = (recent_volume - historical_volume) / historical_volume if historical_volume > 0 else 0.0
            volume_score = max(0, volume_surge)
            
            # Price acceleration (second derivative)
            price_changes = close.pct_change()
            acceleration = price_changes.diff().tail(5).mean()
            acceleration_score = max(0, acceleration * 100)
            
            # Combine sentiment shift indicators
            sentiment_score = (
                min(breakout_score, 1.0) * 0.4 +
                min(volume_score, 1.0) * 0.3 +
                min(acceleration_score, 1.0) * 0.3
            )
            
            return max(0, min(sentiment_score, 1.0))
            
        except Exception as e:
            log.warning(f"Error calculating sentiment shift for {symbol}: {e}")
            return 0.0
    
    def _calculate_unusual_activity(self, symbol: str) -> float:
        """Detect unusual trading patterns"""
        try:
            ohlcv, _ = load_ohlcv(symbol, period="3mo")
            if ohlcv.empty:
                return 0.0
            
            close = ohlcv["close"]
            volume = ohlcv["volume"]
            high = ohlcv["high"]
            low = ohlcv["low"]
            
            # Intraday volatility expansion
            daily_range = (high - low) / close
            avg_range = daily_range.mean()
            recent_range = daily_range.tail(10).mean()
            range_expansion = (recent_range - avg_range) / avg_range if avg_range > 0 else 0.0
            range_score = max(0, range_expansion)
            
            # Volume pattern anomaly
            volume_std = volume.std()
            volume_mean = volume.mean()
            recent_volume_z = (volume.tail(5).mean() - volume_mean) / volume_std if volume_std > 0 else 0.0
            volume_anomaly = min(abs(recent_volume_z) / 3, 1.0)  # Normalize to 0-1
            
            # Price gap detection
            gaps = (close.open - close.shift(1)) / close.shift(1)
            recent_gaps = gaps.tail(20).abs()
            gap_activity = recent_gaps.mean() * 100  # Scale up
            gap_score = min(gap_activity, 1.0)
            
            # Combine unusual activity scores
            unusual_score = (
                min(range_score, 1.0) * 0.4 +
                volume_anomaly * 0.3 +
                gap_score * 0.3
            )
            
            return max(0, min(unusual_score, 1.0))
            
        except Exception as e:
            log.warning(f"Error calculating unusual activity for {symbol}: {e}")
            return 0.0
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Analyze a single stock for hidden gem potential"""
        try:
            # Get stock intelligence data
            intel_data = self.stock_intel.gather(symbol)
            
            # Calculate all scores
            attention_score = self._calculate_attention_score(symbol, intel_data)
            momentum_score = self._calculate_momentum_score(symbol)
            sentiment_score = self._calculate_sentiment_shift(symbol)
            unusual_score = self._calculate_unusual_activity(symbol)
            
            # Calculate hidden gem score (lower attention + higher signals = better gem)
            hidden_gem_score = (
                (1.0 - attention_score) * 0.4 +  # Low attention is good
                momentum_score * 0.3 +           # Rising momentum is good
                sentiment_score * 0.2 +           # Sentiment shift is good
                unusual_score * 0.1               # Unusual activity is interesting
            )
            
            # Determine if it's a hidden gem
            is_hidden_gem = (
                attention_score < 0.6 and          # Low attention
                momentum_score > 0.3 and           # Some momentum
                hidden_gem_score > 0.5             # Overall good score
            )
            
            # Get fundamentals for filtering
            fundamentals = intel_data.get("fundamentals", {})
            market_cap = fundamentals.get("marketCap", 0)
            
            # Filter out very large caps (less likely to be hidden gems)
            size_filter = market_cap < 50_000_000_000 or market_cap == 0  # < 50B or unknown
            
            return {
                "symbol": symbol,
                "hidden_gem_score": round(hidden_gem_score, 3),
                "is_hidden_gem": is_hidden_gem and size_filter,
                "scores": {
                    "attention_score": round(attention_score, 3),
                    "momentum_score": round(momentum_score, 3),
                    "sentiment_shift": round(sentiment_score, 3),
                    "unusual_activity": round(unusual_score, 3)
                },
                "fundamentals": {
                    "market_cap": market_cap,
                    "avg_volume": fundamentals.get("averageVolume", 0),
                    "current_price": fundamentals.get("currentPrice", 0),
                    "beta": fundamentals.get("beta", 0)
                },
                "reasoning": self._generate_reasoning(
                    attention_score, momentum_score, sentiment_score, unusual_score
                )
            }
            
        except Exception as e:
            log.error(f"Error analyzing {symbol} for hidden gems: {e}")
            return {
                "symbol": symbol,
                "hidden_gem_score": 0.0,
                "is_hidden_gem": False,
                "error": str(e)
            }
    
    def _generate_reasoning(self, attention: float, momentum: float, 
                          sentiment: float, unusual: float) -> List[str]:
        """Generate human-readable reasoning for the score"""
        reasons = []
        
        if attention < 0.4:
            reasons.append("Low market attention - undercovered by analysts")
        elif attention < 0.6:
            reasons.append("Moderate attention - not mainstream yet")
        
        if momentum > 0.6:
            reasons.append("Strong rising momentum detected")
        elif momentum > 0.3:
            reasons.append("Positive momentum building")
        
        if sentiment > 0.5:
            reasons.append("Sentiment shift indicating renewed interest")
        
        if unusual > 0.5:
            reasons.append("Unusual trading activity suggests discovery phase")
        
        if not reasons:
            reasons.append("Mixed signals - monitor for confirmation")
        
        return reasons
    
    def scan_market(self, symbols: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Scan multiple stocks for hidden gems"""
        results = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_stock(symbol)
                if analysis.get("is_hidden_gem", False):
                    results.append(analysis)
            except Exception as e:
                log.warning(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Sort by hidden gem score
        results.sort(key=lambda x: x.get("hidden_gem_score", 0), reverse=True)
        
        return results[:limit]
    
    def get_sp500_candidates(self) -> List[str]:
        """Get a list of S&P 500 stocks to scan"""
        # Common S&P 500 tickers (simplified list)
        sp500_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM",
            "JNJ", "V", "PG", "UNH", "HD", "MA", "PYPL", "DIS", "NFLX",
            "ADBE", "CRM", "BAC", "XOM", "KO", "PEP", "COST", "TMO",
            "ABT", "ACN", "CMCSA", "DHR", "VZ", "NEE", "PFE", "CVX",
            "LLY", "MDT", "ISRG", "ABNB", "QCOM", "TXN", "AMGN", "IBM",
            "GILD", "CAT", "DE", "GE", "MMM", "BA", "HON", "UPS"
        ]
        return sp500_stocks
