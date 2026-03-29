"""
Smart Alerts System - Generates intelligent alerts for market events
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json

from .hidden_gem_detector import HiddenGemDetector
from .risk_scanner import RiskScanner
from .stock_intel_agent import StockIntelAgent
from .regime import detect_regime
from .data import load_ohlcv

log = logging.getLogger(__name__)


class SmartAlert:
    """Individual alert data structure"""
    
    def __init__(self, 
                 alert_type: str,
                 title: str,
                 message: str,
                 symbol: Optional[str] = None,
                 severity: str = "medium",
                 data: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[datetime] = None):
        self.alert_type = alert_type
        self.title = title
        self.message = message
        self.symbol = symbol
        self.severity = severity  # low, medium, high, critical
        self.data = data or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "title": self.title,
            "message": self.message,
            "symbol": self.symbol,
            "severity": self.severity,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "timestamp_human": self._format_timestamp()
        }
    
    def _format_timestamp(self) -> str:
        """Human readable timestamp"""
        now = datetime.now(timezone.utc)
        diff = now - self.timestamp
        
        if diff < timedelta(minutes=5):
            return "Just now"
        elif diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() / 60)} minutes ago"
        elif diff < timedelta(hours=24):
            return f"{int(diff.total_seconds() / 3600)} hours ago"
        else:
            return self.timestamp.strftime("%Y-%m-%d %H:%M")


class SmartAlertsSystem:
    """Generates intelligent market alerts"""
    
    def __init__(self):
        self.gem_detector = HiddenGemDetector()
        self.risk_scanner = RiskScanner()
        self.stock_intel = StockIntelAgent()
        self.alerts: List[SmartAlert] = []
    
    def generate_hidden_gem_alerts(self, symbols: List[str]) -> List[SmartAlert]:
        """Generate alerts for newly discovered hidden gems"""
        alerts = []
        
        try:
            hidden_gems = self.gem_detector.scan_market(symbols, limit=10)
            
            for gem in hidden_gems:
                score = gem.get("hidden_gem_score", 0)
                symbol = gem.get("symbol")
                
                if score > 0.7:  # High confidence hidden gem
                    alert = SmartAlert(
                        alert_type="hidden_gem",
                        title=f"💎 Hidden Gem Detected: {symbol}",
                        message=f"Strong signals with low market attention. Score: {score:.2f}",
                        symbol=symbol,
                        severity="high" if score > 0.8 else "medium",
                        data={
                            "hidden_gem_score": score,
                            "attention_score": gem.get("scores", {}).get("attention_score"),
                            "momentum_score": gem.get("scores", {}).get("momentum_score"),
                            "reasoning": gem.get("reasoning", [])
                        }
                    )
                    alerts.append(alert)
        
        except Exception as e:
            log.warning(f"Error generating hidden gem alerts: {e}")
        
        return alerts
    
    def generate_risk_alerts(self, symbols: List[str]) -> List[SmartAlert]:
        """Generate alerts for newly detected risky stocks"""
        alerts = []
        
        try:
            risky_stocks = self.risk_scanner.scan_market_risks(symbols, limit=10)
            
            for stock in risky_stocks:
                risk_score = stock.get("overall_risk_score", 0)
                symbol = stock.get("symbol")
                risk_level = stock.get("risk_level", "UNKNOWN")
                
                if risk_score > 0.8:  # Extreme risk
                    alert = SmartAlert(
                        alert_type="extreme_risk",
                        title=f"🚨 Extreme Risk Alert: {symbol}",
                        message=f"Multiple serious risk factors detected. Risk Level: {risk_level}",
                        symbol=symbol,
                        severity="critical",
                        data={
                            "risk_score": risk_score,
                            "risk_level": risk_level,
                            "warnings": stock.get("warnings", []),
                            "recommendation": stock.get("recommendation")
                        }
                    )
                    alerts.append(alert)
                elif risk_score > 0.6:  # High risk
                    alert = SmartAlert(
                        alert_type="high_risk",
                        title=f"⚠️ High Risk Detected: {symbol}",
                        message=f"Elevated risk factors present. Monitor closely.",
                        symbol=symbol,
                        severity="high",
                        data={
                            "risk_score": risk_score,
                            "risk_level": risk_level,
                            "top_warnings": stock.get("warnings", [])[:3]
                        }
                    )
                    alerts.append(alert)
        
        except Exception as e:
            log.warning(f"Error generating risk alerts: {e}")
        
        return alerts
    
    def generate_confidence_spike_alerts(self, symbols: List[str]) -> List[SmartAlert]:
        """Generate alerts for sudden model confidence spikes"""
        alerts = []
        
        try:
            for symbol in symbols:
                try:
                    # Get recent analysis
                    from quant_ecosystem.elite_intelligence import run_full_intelligence
                    
                    analysis = run_full_intelligence(
                        symbol,
                        period="3mo",
                        include_cross_market=False,
                        include_stock_intel=True,
                        max_hypotheses=2,
                        top_models=1
                    )
                    
                    if analysis.get("ok"):
                        # Extract confidence from debate or ecosystem
                        debate = analysis.get("debate", {})
                        judge_score = debate.get("judge", {}).get("score", 0)
                        
                        # Check for high confidence
                        if abs(judge_score) > 0.6:  # Strong conviction
                            action = debate.get("judge", {}).get("action", "hold")
                            
                            alert = SmartAlert(
                                alert_type="confidence_spike",
                                title=f"📈 Model Confidence Spike: {symbol}",
                                message=f"AI models show strong conviction: {action.upper()} (Score: {judge_score:.2f})",
                                symbol=symbol,
                                severity="high" if abs(judge_score) > 0.8 else "medium",
                                data={
                                    "judge_score": judge_score,
                                    "action": action,
                                    "bull_confidence": debate.get("agents", [{}])[0].get("confidence", 0),
                                    "bear_confidence": debate.get("agents", [{}])[1].get("confidence", 0)
                                }
                            )
                            alerts.append(alert)
                
                except Exception as e:
                    log.debug(f"Error analyzing {symbol} for confidence spike: {e}")
                    continue
        
        except Exception as e:
            log.warning(f"Error generating confidence spike alerts: {e}")
        
        return alerts
    
    def generate_regime_change_alerts(self, market_symbols: List[str]) -> List[SmartAlert]:
        """Generate alerts for market regime changes"""
        alerts = []
        
        try:
            # Use a market index like SPY or aggregate multiple symbols
            market_symbol = market_symbols[0] if market_symbols else "SPY"
            
            try:
                ohlcv, _ = load_ohlcv(market_symbol, period="6mo")
                if not ohlcv.empty:
                    close = ohlcv["close"]
                    volume = ohlcv["volume"]
                    
                    regime_snap = detect_regime(close, volume)
                    
                    # Check for recent regime change
                    current_regime = regime_snap.trend.value
                    confidence = regime_snap.confidence
                    
                    if confidence > 0.7:  # High confidence regime
                        if current_regime == "crash":
                            alert = SmartAlert(
                                alert_type="regime_change",
                                title="📉 Market Regime Change: CRASH DETECTED",
                                message="Market has entered crash regime. Extreme caution advised.",
                                severity="critical",
                                data={
                                    "regime": current_regime,
                                    "confidence": confidence,
                                    "volatility": regime_snap.volatility.value,
                                    "driver": regime_snap.driver.value
                                }
                            )
                        elif current_regime == "rally":
                            alert = SmartAlert(
                                alert_type="regime_change",
                                title="📈 Market Regime Change: RALLY DETECTED",
                                message="Market has entered rally regime. Opportunity window.",
                                severity="high",
                                data={
                                    "regime": current_regime,
                                    "confidence": confidence,
                                    "volatility": regime_snap.volatility.value,
                                    "driver": regime_snap.driver.value
                                }
                            )
                        else:
                            alert = SmartAlert(
                                alert_type="regime_update",
                                title=f"📊 Market Regime Update: {current_regime.upper()}",
                                message=f"Market regime: {current_regime} (Confidence: {confidence:.2f})",
                                severity="medium",
                                data={
                                    "regime": current_regime,
                                    "confidence": confidence,
                                    "volatility": regime_snap.volatility.value,
                                    "driver": regime_snap.driver.value
                                }
                            )
                        
                        alerts.append(alert)
            
            except Exception as e:
                log.warning(f"Error detecting regime for {market_symbol}: {e}")
        
        except Exception as e:
            log.warning(f"Error generating regime change alerts: {e}")
        
        return alerts
    
    def generate_volume_anomaly_alerts(self, symbols: List[str]) -> List[SmartAlert]:
        """Generate alerts for unusual volume patterns"""
        alerts = []
        
        try:
            for symbol in symbols:
                try:
                    ohlcv, _ = load_ohlcv(symbol, period="1mo")
                    if ohlcv.empty:
                        continue
                    
                    volume = ohlcv["volume"]
                    close = ohlcv["close"]
                    
                    # Calculate volume anomaly
                    recent_volume = volume.tail(5).mean()
                    historical_volume = volume.head(len(volume) - 5).mean() if len(volume) > 5 else recent_volume
                    
                    if historical_volume > 0:
                        volume_ratio = recent_volume / historical_volume
                        
                        # Check for significant volume spike
                        if volume_ratio > 3.0:  # 3x normal volume
                            # Check if price is moving significantly
                            recent_price_change = (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] if len(close) > 5 else 0
                            
                            if abs(recent_price_change) > 0.05:  # 5%+ price move
                                direction = "up" if recent_price_change > 0 else "down"
                                
                                alert = SmartAlert(
                                    alert_type="volume_anomaly",
                                    title=f"📊 Unusual Volume Activity: {symbol}",
                                    message=f"Volume spike {volume_ratio:.1f}x normal with price moving {direction}",
                                    symbol=symbol,
                                    severity="high" if volume_ratio > 5.0 else "medium",
                                    data={
                                        "volume_ratio": volume_ratio,
                                        "price_change": recent_price_change,
                                        "recent_volume": recent_volume,
                                        "direction": direction
                                    }
                                )
                                alerts.append(alert)
                
                except Exception as e:
                    log.debug(f"Error checking volume anomaly for {symbol}: {e}")
                    continue
        
        except Exception as e:
            log.warning(f"Error generating volume anomaly alerts: {e}")
        
        return alerts
    
    def generate_all_alerts(self, symbols: List[str] = None) -> List[SmartAlert]:
        """Generate all types of alerts"""
        if symbols is None:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "SPY"]
        
        all_alerts = []
        
        # Generate different types of alerts
        all_alerts.extend(self.generate_hidden_gem_alerts(symbols))
        all_alerts.extend(self.generate_risk_alerts(symbols))
        all_alerts.extend(self.generate_confidence_spike_alerts(symbols[:5]))  # Limit for performance
        all_alerts.extend(self.generate_regime_change_alerts(["SPY"]))
        all_alerts.extend(self.generate_volume_anomaly_alerts(symbols))
        
        # Sort by severity and timestamp
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        all_alerts.sort(key=lambda x: (severity_order.get(x.severity, 0), x.timestamp), reverse=True)
        
        self.alerts = all_alerts
        return all_alerts
    
    def get_alerts_by_type(self, alert_type: str) -> List[SmartAlert]:
        """Get alerts of specific type"""
        return [alert for alert in self.alerts if alert.alert_type == alert_type]
    
    def get_alerts_by_severity(self, severity: str) -> List[SmartAlert]:
        """Get alerts by severity level"""
        return [alert for alert in self.alerts if alert.severity == severity]
    
    def get_alerts_by_symbol(self, symbol: str) -> List[SmartAlert]:
        """Get alerts for specific symbol"""
        return [alert for alert in self.alerts if alert.symbol == symbol]
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all alerts to dictionary format"""
        return [alert.to_dict() for alert in self.alerts]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary statistics of alerts"""
        if not self.alerts:
            return {"total_alerts": 0, "by_type": {}, "by_severity": {}}
        
        by_type = {}
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for alert in self.alerts:
            # Count by type
            by_type[alert.alert_type] = by_type.get(alert.alert_type, 0) + 1
            
            # Count by severity
            if alert.severity in by_severity:
                by_severity[alert.severity] += 1
        
        return {
            "total_alerts": len(self.alerts),
            "by_type": by_type,
            "by_severity": by_severity,
            "latest_alert": self.alerts[0].to_dict() if self.alerts else None
        }
