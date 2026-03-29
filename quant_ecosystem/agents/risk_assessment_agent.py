"""
Risk Assessment Agent
Specialized agent for evaluating investment risks and portfolio impact
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class RiskAssessmentResult:
    """Result from risk assessment"""
    risk_score: float  # 0-1 scale
    risk_level: str  # low, moderate, high, extreme
    risk_factors: List[Dict[str, Any]]
    mitigation_strategies: List[str]
    max_drawdown_estimate: float
    requested_data: List[str]
    analysis_time: float
    timestamp: datetime


class RiskAssessmentAgent:
    """
    Risk Assessment Agent that:
    - Evaluates multiple risk dimensions
    - Requests specialized risk data
    - Calculates portfolio impact
    - Provides risk mitigation strategies
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "risk_assessment_agent"
        self.max_analysis_time = 60  # 1 minute max
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any],
                bullish_analysis: Dict[str, Any],
                bearish_analysis: Dict[str, Any],
                financial_context: Dict[str, Any]) -> RiskAssessmentResult:
        """
        Comprehensive risk assessment with 1-minute time budget
        Analyzes market, credit, liquidity, and operational risks
        """
        log.info(f"RiskAgent: Starting risk assessment for {symbol}")
        start_time = time.time()
        
        risk_factors = []
        mitigation_strategies = []
        requested_data_types = []
        
        try:
            # Phase 1: Analyze initial volatility and market risks
            phase1_result = self._assess_market_risks(initial_data, financial_context)
            risk_factors.extend(phase1_result["risks"])
            mitigation_strategies.extend(phase1_result["mitigations"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(risk_factors, mitigation_strategies, requested_data_types, start_time)
            
            # Phase 2: Request options data for implied volatility
            options_data = self._request_data("options_data", symbol)
            requested_data_types.append("options_data")
            
            if options_data and "error" not in options_data:
                phase2_result = self._assess_options_risks(options_data)
                risk_factors.extend(phase2_result["risks"])
                mitigation_strategies.extend(phase2_result["mitigations"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(risk_factors, mitigation_strategies, requested_data_types, start_time)
            
            # Phase 3: Request institutional ownership for liquidity risk
            inst_data = self._request_data("institutional_ownership", symbol)
            requested_data_types.append("institutional_ownership")
            
            if inst_data and "error" not in inst_data:
                phase3_result = self._assess_liquidity_risks(inst_data, initial_data)
                risk_factors.extend(phase3_result["risks"])
                mitigation_strategies.extend(phase3_result["mitigations"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(risk_factors, mitigation_strategies, requested_data_types, start_time)
            
            # Phase 4: Request earnings calendar for event risk
            earnings_data = self._request_data("earnings_calendar", symbol)
            requested_data_types.append("earnings_calendar")
            
            if earnings_data and "error" not in earnings_data:
                phase4_result = self._assess_event_risks(earnings_data)
                risk_factors.extend(phase4_result["risks"])
                mitigation_strategies.extend(phase4_result["mitigations"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(risk_factors, mitigation_strategies, requested_data_types, start_time)
            
            # Phase 5: Request insider trading data
            insider_data = self._request_data("insider_trading", symbol)
            requested_data_types.append("insider_trading")
            
            if insider_data and "error" not in insider_data:
                phase5_result = self._assess_insider_risks(insider_data)
                risk_factors.extend(phase5_result["risks"])
                mitigation_strategies.extend(phase5_result["mitigations"])
            
            # Calculate final risk score and level
            risk_score = self._calculate_risk_score(risk_factors, financial_context)
            risk_level = self._get_risk_level(risk_score)
            max_dd = self._estimate_max_drawdown(risk_factors, initial_data)
            
            analysis_time = time.time() - start_time
            log.info(f"RiskAgent: Assessment complete in {analysis_time:.2f}s - Risk Level: {risk_level}")
            
            return RiskAssessmentResult(
                risk_score=risk_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                mitigation_strategies=mitigation_strategies,
                max_drawdown_estimate=max_dd,
                requested_data=requested_data_types,
                analysis_time=analysis_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            log.error(f"RiskAgent: Assessment error: {e}")
            return RiskAssessmentResult(
                risk_score=0.5,
                risk_level="moderate",
                risk_factors=[{"type": "analysis_error", "description": str(e), "severity": 0.5}],
                mitigation_strategies=["Proceed with caution due to analysis limitations"],
                max_drawdown_estimate=0.15,
                requested_data=requested_data_types,
                analysis_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _request_data(self, data_type: str, symbol: str) -> Dict[str, Any]:
        """Request risk-specific data from Data Collection Agent"""
        try:
            return self.data_collection(
                agent_id=self.agent_id,
                request_type=data_type,
                symbol=symbol,
                parameters={},
                urgency="high"
            )
        except Exception as e:
            log.warning(f"RiskAgent: Failed to request {data_type}: {e}")
            return {"error": str(e)}
    
    def _assess_market_risks(self, initial_data: Dict[str, Any], financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess market-related risks"""
        risks = []
        mitigations = []
        
        price_data = initial_data.get("price_data", {})
        fundamentals = initial_data.get("fundamentals", {})
        historical = initial_data.get("historical", {})
        
        # Volatility risk
        volatility = historical.get("volatility", 0)
        if volatility:
            if volatility > 0.50:
                risks.append({
                    "type": "volatility",
                    "description": f"Extreme volatility ({volatility*100:.1f}%) - large price swings likely",
                    "severity": 0.9,
                    "metric": volatility
                })
                mitigations.append("Use position sizing to limit exposure to 1-2% of portfolio")
            elif volatility > 0.30:
                risks.append({
                    "type": "volatility",
                    "description": f"High volatility ({volatility*100:.1f}%) - expect significant price movements",
                    "severity": 0.7,
                    "metric": volatility
                })
                mitigations.append("Consider options strategies for volatility protection")
            elif volatility > 0.20:
                risks.append({
                    "type": "volatility",
                    "description": f"Moderate volatility ({volatility*100:.1f}%)",
                    "severity": 0.4,
                    "metric": volatility
                })
        
        # Beta/market correlation risk
        beta = fundamentals.get("beta")
        if beta:
            if beta > 1.5:
                risks.append({
                    "type": "market_correlation",
                    "description": f"High beta ({beta:.2f}) - amplified market moves, {beta:.1f}x market sensitivity",
                    "severity": 0.75,
                    "metric": beta
                })
                mitigations.append("Monitor broader market trends closely - position will amplify market moves")
            elif beta < 0.5:
                risks.append({
                    "type": "low_correlation",
                    "description": f"Low beta ({beta:.2f}) - may not participate in market rallies",
                    "severity": 0.3,
                    "metric": beta
                })
        
        # Market context risks
        vix = financial_context.get("vix_level", 20)
        if vix > 30:
            risks.append({
                "type": "market_stress",
                "description": f"Elevated market stress (VIX: {vix}) - broader selloff risk",
                "severity": 0.8,
                "metric": vix
            })
            mitigations.append("Consider hedging with index options or increasing cash allocation")
        
        systemic_risk = financial_context.get("systemic_risk", 0)
        if systemic_risk > 0.7:
            risks.append({
                "type": "systemic",
                "description": f"High systemic risk ({systemic_risk:.2f}) - correlated drawdown likely",
                "severity": 0.85,
                "metric": systemic_risk
            })
            mitigations.append("Reduce overall equity exposure until systemic risk subsides")
        
        return {"risks": risks, "mitigations": mitigations}
    
    def _assess_options_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks from options market"""
        risks = []
        mitigations = []
        
        iv = data.get("implied_volatility_avg", 0)
        put_call_ratio = data.get("put_call_ratio", 1.0)
        unusual_activity = data.get("unusual_activity", False)
        
        if iv > 0.60:  # 60% implied volatility is high
            risks.append({
                "type": "options_iv",
                "description": f"High implied volatility ({iv*100:.1f}%) - options market expects big moves",
                "severity": 0.7,
                "metric": iv
            })
        
        if put_call_ratio > 1.5:
            risks.append({
                "type": "options_sentiment",
                "description": f"Elevated put/call ratio ({put_call_ratio:.2f}) - bearish options positioning",
                "severity": 0.6,
                "metric": put_call_ratio
            })
            mitigations.append("Monitor for potential capitulation or hedging activity")
        
        if unusual_activity:
            risks.append({
                "type": "options_activity",
                "description": "Unusual options activity detected - potential catalyst ahead",
                "severity": 0.65,
                "metric": 1.0
            })
            mitigations.append("Stay alert for earnings, guidance, or news catalysts")
        
        return {"risks": risks, "mitigations": mitigations}
    
    def _assess_liquidity_risks(self, inst_data: Dict[str, Any], initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess liquidity and ownership concentration risks"""
        risks = []
        mitigations = []
        
        held_pct = inst_data.get("held_percent_institutions", 0)
        held_insiders = inst_data.get("held_percent_insiders", 0)
        
        fundamentals = initial_data.get("fundamentals", {})
        avg_volume = fundamentals.get("averageVolume", 0)
        market_cap = fundamentals.get("marketCap", 0)
        
        # Institutional concentration risk
        if held_pct > 0.90:
            risks.append({
                "type": "concentration",
                "description": f"Extreme institutional concentration ({held_pct*100:.1f}%) - vulnerable to block selling",
                "severity": 0.75,
                "metric": held_pct
            })
            mitigations.append("Use limit orders - avoid market orders due to potential illiquidity")
        elif held_pct > 0.75:
            risks.append({
                "type": "concentration",
                "description": f"High institutional concentration ({held_pct*100:.1f}%)",
                "severity": 0.5,
                "metric": held_pct
            })
        
        # Volume-based liquidity
        if avg_volume > 0 and market_cap > 0:
            turnover = avg_volume / (market_cap / fundamentals.get("currentPrice", 1))
            if turnover < 0.001:  # Less than 0.1% daily turnover
                risks.append({
                    "type": "liquidity",
                    "description": f"Low trading liquidity - may face wide bid-ask spreads",
                    "severity": 0.6,
                    "metric": turnover
                })
                mitigations.append("Plan for longer exit timeframe; use patience with orders")
        
        # Insider ownership
        if held_insiders > 0.20:
            risks.append({
                "type": "insider_control",
                "description": f"High insider ownership ({held_insiders*100:.1f}%) - voting control concentrated",
                "severity": 0.4,
                "metric": held_insiders
            })
        
        return {"risks": risks, "mitigations": mitigations}
    
    def _assess_event_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess event-driven risks (earnings, etc.)"""
        risks = []
        mitigations = []
        
        next_earnings = data.get("next_earnings_date")
        eps_estimate = data.get("eps_estimate")
        
        if next_earnings:
            risks.append({
                "type": "earnings_event",
                "description": f"Upcoming earnings on {next_earnings} - potential for significant price gap",
                "severity": 0.6,
                "metric": 1.0
            })
            mitigations.append("Consider position size before earnings; reduce if uncomfortable with gap risk")
        
        return {"risks": risks, "mitigations": mitigations}
    
    def _assess_insider_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks from insider trading patterns"""
        risks = []
        mitigations = []
        
        sentiment = data.get("insider_sentiment", "neutral")
        recent_transactions = data.get("recent_transactions", [])
        
        if sentiment == "bearish":
            risks.append({
                "type": "insider_selling",
                "description": "Insider selling detected - executives reducing exposure",
                "severity": 0.7,
                "metric": 1.0
            })
            mitigations.append("Investigate SEC Form 4 filings for pattern of selling")
        
        return {"risks": risks, "mitigations": mitigations}
    
    def _calculate_risk_score(self, risk_factors: List[Dict[str, Any]], 
                            financial_context: Dict[str, Any]) -> float:
        """Calculate overall risk score 0-1"""
        if not risk_factors:
            return 0.3  # Default moderate risk
        
        # Weighted average of severity
        total_weight = 0
        weighted_sum = 0
        
        for risk in risk_factors:
            severity = risk.get("severity", 0.5)
            risk_type = risk.get("type", "")
            
            # Weight certain risk types more heavily
            weight = 1.0
            if risk_type in ["volatility", "systemic", "market_stress"]:
                weight = 1.5
            elif risk_type in ["liquidity", "concentration"]:
                weight = 1.3
            
            weighted_sum += severity * weight
            total_weight += weight
        
        base_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Adjust for financial context
        vix = financial_context.get("vix_level", 20)
        if vix > 30:
            base_score += 0.1
        
        return min(0.95, max(0.1, base_score))
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score < 0.3:
            return "low"
        elif score < 0.5:
            return "moderate"
        elif score < 0.7:
            return "high"
        else:
            return "extreme"
    
    def _estimate_max_drawdown(self, risk_factors: List[Dict[str, Any]], 
                              initial_data: Dict[str, Any]) -> float:
        """Estimate potential maximum drawdown"""
        base_dd = 0.10  # 10% base drawdown estimate
        
        # Adjust based on volatility
        historical = initial_data.get("historical", {})
        volatility = historical.get("volatility", 0.20)
        
        # Rough estimate: 2x annualized volatility for max DD
        volatility_adjusted = volatility * 2
        
        # Adjust for risk factors
        for risk in risk_factors:
            risk_type = risk.get("type", "")
            severity = risk.get("severity", 0)
            
            if risk_type == "systemic":
                base_dd += severity * 0.15
            elif risk_type == "volatility":
                base_dd += severity * 0.10
            elif risk_type == "concentration":
                base_dd += severity * 0.08
        
        # Use higher of volatility-based or risk-based estimate
        estimated_dd = max(volatility_adjusted, base_dd)
        
        return min(0.60, estimated_dd)  # Cap at 60%
    
    def _create_result(self, risk_factors: List[Dict], mitigations: List[str],
                      requested_data: List[str], start_time: float) -> RiskAssessmentResult:
        """Create result when hitting time limit"""
        risk_score = self._calculate_risk_score(risk_factors, {})
        
        return RiskAssessmentResult(
            risk_score=risk_score,
            risk_level=self._get_risk_level(risk_score),
            risk_factors=risk_factors,
            mitigation_strategies=mitigations,
            max_drawdown_estimate=self._estimate_max_drawdown(risk_factors, {}),
            requested_data=requested_data,
            analysis_time=time.time() - start_time,
            timestamp=datetime.now()
        )
    
    def argue(self, assessment_result: RiskAssessmentResult, 
             opponent_points: List[str] = None) -> Dict[str, Any]:
        """Generate risk critique argument"""
        points = []
        
        # Summarize key risks
        high_severity_risks = [r for r in assessment_result.risk_factors if r.get("severity", 0) > 0.6]
        
        for risk in high_severity_risks[:3]:  # Top 3 risks
            points.append(f"{risk['type'].replace('_', ' ').title()}: {risk['description']}")
        
        # Add risk score summary
        points.append(f"Overall risk score: {assessment_result.risk_score:.2f} ({assessment_result.risk_level.upper()})")
        points.append(f"Estimated maximum drawdown potential: {assessment_result.max_drawdown_estimate*100:.1f}%")
        
        # Add mitigation strategies
        if assessment_result.mitigation_strategies:
            points.append(f"Risk mitigation: {assessment_result.mitigation_strategies[0]}")
        
        return {
            "agent": self.agent_id,
            "stance": "critique",
            "confidence": min(0.95, 0.5 + assessment_result.risk_score * 0.5),
            "points": points,
            "risk_score": assessment_result.risk_score,
            "risk_level": assessment_result.risk_level,
            "max_drawdown_estimate": assessment_result.max_drawdown_estimate,
            "analysis_time": assessment_result.analysis_time,
            "requested_data_count": len(assessment_result.requested_data),
            "timestamp": assessment_result.timestamp.isoformat()
        }
