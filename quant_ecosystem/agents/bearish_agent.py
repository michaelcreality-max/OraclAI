"""
Bearish Analysis Agent
Analyzes stock data and argues for selling/short positions
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class BearishAnalysisResult:
    """Result from bearish analysis"""
    confidence: float
    key_points: List[str]
    risk_factors: Dict[str, Any]
    requested_data: List[str]
    analysis_time: float
    timestamp: datetime


class BearishAgent:
    """
    Bearish Analysis Agent that:
    - Analyzes stock data for risks and selling opportunities
    - Requests additional risk data from Data Collection Agent
    - Argues for short/sell positions with supporting evidence
    - Identifies overvaluation and downside catalysts
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "bearish_agent"
        self.max_analysis_time = 60  # 1 minute max
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any], 
                financial_context: Dict[str, Any]) -> BearishAnalysisResult:
        """
        Perform bearish analysis with up to 1 minute time budget
        Focuses on risks, overvaluation, and negative catalysts
        """
        log.info(f"BearishAgent: Starting analysis for {symbol}")
        start_time = time.time()
        
        key_points = []
        risk_factors = {}
        requested_data_types = []
        
        try:
            # Phase 1: Analyze initial data for risks
            phase1_result = self._identify_initial_risks(initial_data)
            key_points.extend(phase1_result["points"])
            risk_factors.update(phase1_result["risks"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, risk_factors, requested_data_types, start_time)
            
            # Phase 2: Request fundamental analysis for overvaluation
            fundamentals = self._request_data("detailed_fundamentals", symbol)
            requested_data_types.append("detailed_fundamentals")
            
            if fundamentals and "error" not in fundamentals:
                phase2_result = self._check_overvaluation(fundamentals, initial_data)
                key_points.extend(phase2_result["points"])
                risk_factors.update(phase2_result["risks"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, risk_factors, requested_data_types, start_time)
            
            # Phase 3: Request short interest data
            short_data = self._request_data("short_interest", symbol)
            requested_data_types.append("short_interest")
            
            if short_data and "error" not in short_data:
                phase3_result = self._analyze_short_interest(short_data)
                key_points.extend(phase3_result["points"])
                risk_factors.update(phase3_result["risks"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, risk_factors, requested_data_types, start_time)
            
            # Phase 4: Request geopolitical/environmental risks
            geo_data = self._request_data("geopolitical_context", symbol)
            requested_data_types.append("geopolitical_context")
            
            if geo_data and "error" not in geo_data:
                phase4_result = self._assess_geopolitical_risks(geo_data, financial_context)
                key_points.extend(phase4_result["points"])
                risk_factors.update(phase4_result["risks"])
            
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, risk_factors, requested_data_types, start_time)
            
            # Phase 5: Request environmental/ESG data
            env_data = self._request_data("environmental_factors", symbol)
            requested_data_types.append("environmental_factors")
            
            if env_data and "error" not in env_data:
                phase5_result = self._assess_environmental_risks(env_data)
                key_points.extend(phase5_result["points"])
                risk_factors.update(phase5_result["risks"])
            
            # Calculate confidence based on risk severity
            confidence = self._calculate_confidence(key_points, risk_factors, financial_context)
            
            analysis_time = time.time() - start_time
            log.info(f"BearishAgent: Analysis complete in {analysis_time:.2f}s with {len(key_points)} risk factors")
            
            return BearishAnalysisResult(
                confidence=confidence,
                key_points=key_points,
                risk_factors=risk_factors,
                requested_data=requested_data_types,
                analysis_time=analysis_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            log.error(f"BearishAgent: Analysis error: {e}")
            return BearishAnalysisResult(
                confidence=0.5,
                key_points=["Analysis encountered error, identifying conservative risks"] + key_points,
                risk_factors=risk_factors,
                requested_data=requested_data_types,
                analysis_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _request_data(self, data_type: str, symbol: str) -> Dict[str, Any]:
        """Request additional data from Data Collection Agent"""
        try:
            return self.data_collection(
                agent_id=self.agent_id,
                request_type=data_type,
                symbol=symbol,
                parameters={},
                urgency="high"
            )
        except Exception as e:
            log.warning(f"BearishAgent: Failed to request {data_type}: {e}")
            return {"error": str(e)}
    
    def _identify_initial_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify initial risks from basic data"""
        points = []
        risks = {}
        
        price_data = data.get("price_data", {})
        fundamentals = data.get("fundamentals", {})
        historical = data.get("historical", {})
        
        # Price decline
        current = price_data.get("current_price", 0)
        prev_close = price_data.get("previous_close", 0)
        if current > 0 and prev_close > 0:
            change = (current - prev_close) / prev_close
            if change < -0.02:
                points.append(f"Significant daily decline: {change*100:.1f}% drop signals weakness")
                risks["daily_decline"] = change
            elif change < 0:
                points.append(f"Negative daily momentum: {change*100:.1f}% decline")
                risks["negative_momentum"] = change
        
        # 52-week range position
        high_52w = price_data.get("fifty_two_week_high", 0)
        low_52w = price_data.get("fifty_two_week_low", 0)
        if current > 0 and high_52w > 0 and low_52w > 0:
            range_position = (current - low_52w) / (high_52w - low_52w) if (high_52w - low_52w) > 0 else 0.5
            if range_position > 0.90:
                points.append(f"Trading at {range_position*100:.0f}% of 52-week range - overextended and at risk of correction")
                risks["range_position"] = range_position
                risks["correction_risk"] = "high"
            elif range_position < 0.10:
                points.append(f"Trading near 52-week lows indicates sustained weakness")
                risks["range_position"] = range_position
                risks["weakness"] = "sustained"
        
        # Volatility concerns
        volatility = historical.get("volatility", 0)
        if volatility and volatility > 0.40:  # 40% annualized volatility is high
            points.append(f"High volatility of {volatility*100:.1f}% creates significant downside risk")
            risks["high_volatility"] = volatility
        
        # Trend analysis
        trend_6m = historical.get("trend_6m", "sideways")
        if trend_6m == "down":
            points.append("6-month trend is negative, indicating sustained selling pressure")
            risks["trend_6m"] = "down"
        
        # Valuation risks
        pe = fundamentals.get("pe_ratio")
        if pe and pe > 40:
            points.append(f"Elevated P/E ratio of {pe:.1f} suggests overvaluation and multiple compression risk")
            risks["pe_ratio"] = pe
            risks["overvaluation"] = "high"
        elif pe and pe > 30:
            points.append(f"Above-average P/E of {pe:.1f} requires sustained growth to justify")
            risks["pe_ratio"] = pe
        
        # Weak growth
        revenue_growth = fundamentals.get("revenue_growth")
        if revenue_growth is not None and revenue_growth < 0:
            points.append(f"Declining revenue of {revenue_growth*100:.1f}% indicates business contraction")
            risks["revenue_decline"] = revenue_growth
        
        earnings_growth = fundamentals.get("earnings_growth")
        if earnings_growth is not None and earnings_growth < 0:
            points.append(f"Negative earnings growth of {earnings_growth*100:.1f}% signals profitability pressure")
            risks["earnings_decline"] = earnings_growth
        
        # Balance sheet concerns
        beta = fundamentals.get("beta")
        if beta and beta > 1.5:
            points.append(f"High beta of {beta:.2f} indicates amplified market downside exposure")
            risks["high_beta"] = beta
        
        return {"points": points, "risks": risks}
    
    def _check_overvaluation(self, data: Dict[str, Any], initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for overvaluation using fundamental metrics"""
        points = []
        risks = {}
        
        valuation = data.get("valuation_metrics", {})
        income = data.get("income_statement", {})
        fundamentals = initial_data.get("fundamentals", {})
        
        # P/E ratio analysis
        pe_trailing = valuation.get("pe_trailing")
        pe_forward = valuation.get("pe_forward")
        
        if pe_trailing and pe_forward:
            if pe_forward > pe_trailing:
                points.append(f"Forward P/E ({pe_forward:.1f}) exceeds trailing P/E ({pe_trailing:.1f}) - earnings expected to decline")
                risks["pe_expansion_risk"] = True
            if pe_trailing > 30:
                points.append(f"High trailing P/E of {pe_trailing:.1f}x demands perfect execution")
                risks["high_pe"] = pe_trailing
        
        # P/S ratio
        ps_ratio = valuation.get("ps_ratio")
        if ps_ratio and ps_ratio > 10:
            points.append(f"Excessive P/S ratio of {ps_ratio:.1f}x - requires exceptional growth to sustain")
            risks["high_ps_ratio"] = ps_ratio
        
        # EV/EBITDA
        ev_ebitda = valuation.get("ev_ebitda")
        if ev_ebitda and ev_ebitda > 15:
            points.append(f"High EV/EBITDA of {ev_ebitda:.1f}x suggests acquisition premium unsustainable")
            risks["high_ev_ebitda"] = ev_ebitda
        
        # Margin pressure
        revenue = income.get("revenue", 0)
        operating_income = income.get("operating_income", 0)
        if revenue > 0 and operating_income > 0:
            operating_margin = operating_income / revenue
            if operating_margin < 0.05:
                points.append(f"Thin operating margin of {operating_margin*100:.1f}% provides minimal downside buffer")
                risks["thin_margins"] = operating_margin
        
        # Sector comparison
        sector = fundamentals.get("sector", "").lower()
        if sector in ["technology"] and pe_trailing and pe_trailing > 35:
            points.append("P/E above sector average - multiple compression risk in tech selloff")
            risks["sector_multiple_risk"] = True
        
        return {"points": points, "risks": risks}
    
    def _analyze_short_interest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze short interest for bearish signals"""
        points = []
        risks = {}
        
        short_ratio = data.get("short_ratio")
        short_percent = data.get("short_percent_of_float")
        days_to_cover = data.get("days_to_cover")
        
        if short_percent and short_percent > 0.10:  # 10% short interest is significant
            points.append(f"High short interest at {short_percent*100:.1f}% of float - institutional bearishness")
            risks["high_short_interest"] = short_percent
        
        if days_to_cover and days_to_cover > 5:
            points.append(f"Days to cover of {days_to_cover:.1f} indicates potential short squeeze, but also validates bearish thesis")
            risks["high_days_to_cover"] = days_to_cover
        
        return {"points": points, "risks": risks}
    
    def _assess_geopolitical_risks(self, data: Dict[str, Any], financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess geopolitical and macro risks"""
        points = []
        risks = {}
        
        country_exposure = data.get("country_exposure", "")
        trade_sensitivity = data.get("trade_sensitivity", "")
        sanctions_risk = data.get("sanctions_risk", "low")
        
        if trade_sensitivity == "high":
            points.append("High trade sensitivity exposes company to tariff and supply chain disruptions")
            risks["trade_sensitivity"] = trade_sensitivity
        
        if sanctions_risk != "low":
            points.append(f"Elevated sanctions risk: {sanctions_risk}")
            risks["sanctions_risk"] = sanctions_risk
        
        # Adapt to financial context
        market_phase = financial_context.get("market_phase", "normal")
        if market_phase == "recession":
            points.append("Recessionary environment typically compresses multiples and reduces earnings visibility")
            risks["recession_impact"] = "earnings_compression"
        elif market_phase == "inflation":
            points.append("Inflationary pressures may squeeze margins if pricing power is limited")
            risks["inflation_risk"] = "margin_compression"
        
        systemic_risk = financial_context.get("systemic_risk", 0)
        if systemic_risk > 0.6:
            points.append(f"High systemic risk level ({systemic_risk:.2f}) suggests broad market vulnerability")
            risks["systemic_risk"] = systemic_risk
        
        return {"points": points, "risks": risks}
    
    def _assess_environmental_risks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess environmental and ESG risks"""
        points = []
        risks = {}
        
        carbon_intensity = data.get("carbon_intensity", "")
        climate_risk = data.get("climate_risk", "")
        environmental_exposure = data.get("environmental_exposure", "")
        
        if carbon_intensity == "high":
            points.append("High carbon intensity creates regulatory and transition risks")
            risks["carbon_risk"] = carbon_intensity
        
        if climate_risk == "significant":
            points.append("Significant climate risk exposure may impact operations and assets")
            risks["climate_risk"] = climate_risk
        
        if environmental_exposure == "high":
            points.append("High environmental exposure creates liability and remediation risks")
            risks["environmental_risk"] = environmental_exposure
        
        esg_score = data.get("esg_risk_score")
        if esg_score and esg_score > 30:  # High ESG risk
            points.append(f"Poor ESG risk score ({esg_score}) may limit institutional investment")
            risks["esg_risk"] = esg_score
        
        return {"points": points, "risks": risks}
    
    def _calculate_confidence(self, key_points: List[str], risk_factors: Dict[str, Any], 
                             financial_context: Dict[str, Any]) -> float:
        """Calculate confidence in bearish thesis based on risk severity"""
        base_confidence = 0.50
        
        # Critical risks add more confidence
        if "high_pe" in risk_factors:
            base_confidence += 0.08
        if "overvaluation" in risk_factors:
            base_confidence += 0.08
        if "high_short_interest" in risk_factors:
            base_confidence += 0.06
        if "high_volatility" in risk_factors:
            base_confidence += 0.05
        if "revenue_decline" in risk_factors:
            base_confidence += 0.08
        if "earnings_decline" in risk_factors:
            base_confidence += 0.08
        if "correction_risk" in risk_factors:
            base_confidence += 0.07
        if "systemic_risk" in risk_factors:
            base_confidence += 0.05
        
        # Number of risk factors
        risk_bonus = min(0.10, len(key_points) * 0.02)
        base_confidence += risk_bonus
        
        # Financial context adjustment
        market_phase = financial_context.get("market_phase", "normal")
        if market_phase in ["recession", "crisis"]:
            base_confidence += 0.05  # Bearish stance more valid in downturns
        
        return min(0.95, max(0.40, base_confidence))
    
    def _create_result(self, key_points: List[str], risk_factors: Dict, 
                      requested_data: List[str], start_time: float) -> BearishAnalysisResult:
        """Create analysis result when hitting time limit"""
        confidence = self._calculate_confidence(key_points, risk_factors, {})
        
        return BearishAnalysisResult(
            confidence=confidence,
            key_points=key_points + ["Analysis completed within time constraints"],
            risk_factors=risk_factors,
            requested_data=requested_data,
            analysis_time=time.time() - start_time,
            timestamp=datetime.now()
        )
    
    def argue(self, analysis_result: BearishAnalysisResult, opponent_points: List[str] = None) -> Dict[str, Any]:
        """
        Generate argument for selling/short position
        Can respond to bullish arguments
        """
        points = analysis_result.key_points.copy()
        
        # Address opponent arguments if provided
        if opponent_points:
            for opp_point in opponent_points:
                opp_lower = opp_point.lower()
                if "growth" in opp_lower or "expansion" in opp_lower:
                    points.append("Growth may be peaking and difficult to sustain at current levels")
                elif "margin" in opp_lower and "strong" in opp_lower:
                    points.append("Margins face pressure from competition and cost inflation")
                elif "undervalued" in opp_lower or "cheap" in opp_lower:
                    points.append("Valuation may appear attractive but ignores structural challenges")
                elif "trend" in opp_lower and "up" in opp_lower:
                    points.append("Trends can reverse quickly; mean reversion is a powerful force")
        
        # Add final risk warning
        points.append("Downside risks outweigh potential rewards at current valuation levels")
        
        return {
            "agent": self.agent_id,
            "stance": "skeptical",
            "confidence": analysis_result.confidence,
            "points": points,
            "risk_factors": analysis_result.risk_factors,
            "analysis_time": analysis_result.analysis_time,
            "requested_data_count": len(analysis_result.requested_data),
            "timestamp": analysis_result.timestamp.isoformat()
        }
