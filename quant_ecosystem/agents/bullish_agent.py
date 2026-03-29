"""
Bullish Analysis Agent
Analyzes stock data and argues for buying/long positions
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result from bullish analysis"""
    confidence: float
    key_points: List[str]
    supporting_evidence: Dict[str, Any]
    requested_data: List[str]
    analysis_time: float
    timestamp: datetime


class BullishAgent:
    """
    Bullish Analysis Agent that:
    - Analyzes stock data for buying opportunities
    - Requests additional data from Data Collection Agent
    - Argues for long positions with supporting evidence
    - Adapts analysis based on financial context
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "bullish_agent"
        self.max_analysis_time = 60  # 1 minute max
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any], 
                financial_context: Dict[str, Any]) -> AnalysisResult:
        """
        Perform bullish analysis with up to 1 minute time budget
        Can request additional data from Data Collection Agent
        """
        log.info(f"BullishAgent: Starting analysis for {symbol}")
        start_time = time.time()
        
        key_points = []
        supporting_evidence = {}
        requested_data_types = []
        
        try:
            # Phase 1: Analyze initial data (quick scan)
            phase1_result = self._quick_initial_analysis(initial_data)
            key_points.extend(phase1_result["points"])
            supporting_evidence.update(phase1_result["evidence"])
            
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, supporting_evidence, 
                                         requested_data_types, start_time)
            
            # Phase 2: Request additional fundamental data
            fundamentals = self._request_data("detailed_fundamentals", symbol)
            requested_data_types.append("detailed_fundamentals")
            
            if fundamentals and "error" not in fundamentals:
                phase2_result = self._analyze_fundamentals(fundamentals, financial_context)
                key_points.extend(phase2_result["points"])
                supporting_evidence.update(phase2_result["evidence"])
            
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, supporting_evidence, 
                                         requested_data_types, start_time)
            
            # Phase 3: Request analyst ratings
            analyst_data = self._request_data("analyst_ratings", symbol)
            requested_data_types.append("analyst_ratings")
            
            if analyst_data and "error" not in analyst_data:
                phase3_result = self._analyze_analyst_sentiment(analyst_data)
                key_points.extend(phase3_result["points"])
                supporting_evidence.update(phase3_result["evidence"])
            
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed >= self.max_analysis_time:
                return self._create_result(key_points, supporting_evidence, 
                                         requested_data_types, start_time)
            
            # Phase 4: Request sector analysis
            sector_data = self._request_data("sector_analysis", symbol)
            requested_data_types.append("sector_analysis")
            
            if sector_data and "error" not in sector_data:
                phase4_result = self._analyze_sector_position(sector_data, financial_context)
                key_points.extend(phase4_result["points"])
                supporting_evidence.update(phase4_result["evidence"])
            
            # Calculate confidence based on evidence strength
            confidence = self._calculate_confidence(key_points, supporting_evidence, financial_context)
            
            analysis_time = time.time() - start_time
            log.info(f"BullishAgent: Analysis complete in {analysis_time:.2f}s with {len(key_points)} points")
            
            return AnalysisResult(
                confidence=confidence,
                key_points=key_points,
                supporting_evidence=supporting_evidence,
                requested_data=requested_data_types,
                analysis_time=analysis_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            log.error(f"BullishAgent: Analysis error: {e}")
            return AnalysisResult(
                confidence=0.5,
                key_points=["Analysis encountered error, defaulting to neutral stance"] + key_points,
                supporting_evidence=supporting_evidence,
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
                urgency="high"  # Analysis is time-sensitive
            )
        except Exception as e:
            log.warning(f"BullishAgent: Failed to request {data_type}: {e}")
            return {"error": str(e)}
    
    def _quick_initial_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Quick analysis of initial data"""
        points = []
        evidence = {}
        
        price_data = data.get("price_data", {})
        fundamentals = data.get("fundamentals", {})
        historical = data.get("historical", {})
        
        # Price momentum
        current = price_data.get("current_price", 0)
        prev_close = price_data.get("previous_close", 0)
        if current > 0 and prev_close > 0:
            change = (current - prev_close) / prev_close
            if change > 0.02:
                points.append(f"Strong daily momentum: +{change*100:.1f}% gain")
                evidence["daily_momentum"] = change
            elif change > 0:
                points.append(f"Positive daily momentum: +{change*100:.1f}%")
                evidence["daily_momentum"] = change
        
        # 6-month trend
        trend = historical.get("trend_6m", "sideways")
        if trend == "up":
            points.append("6-month trend is positive, showing sustained upward momentum")
            evidence["trend_6m"] = "up"
        
        # Volume analysis
        volume = price_data.get("volume", 0)
        avg_volume = price_data.get("average_volume", 0)
        if volume > 0 and avg_volume > 0:
            vol_ratio = volume / avg_volume
            if vol_ratio > 1.5:
                points.append(f"High volume activity: {vol_ratio:.1f}x average volume indicates strong interest")
                evidence["volume_surge"] = vol_ratio
        
        # Fundamental strength
        pe = fundamentals.get("pe_ratio")
        if pe and 10 < pe < 25:
            points.append(f"Reasonable P/E ratio of {pe:.1f} suggests fair valuation")
            evidence["pe_ratio"] = pe
        elif pe and pe < 15:
            points.append(f"Attractive P/E ratio of {pe:.1f} suggests potential undervaluation")
            evidence["pe_ratio"] = pe
        
        # Growth metrics
        revenue_growth = fundamentals.get("revenue_growth")
        if revenue_growth and revenue_growth > 0.10:
            points.append(f"Strong revenue growth of {revenue_growth*100:.1f}% indicates business expansion")
            evidence["revenue_growth"] = revenue_growth
        
        earnings_growth = fundamentals.get("earnings_growth")
        if earnings_growth and earnings_growth > 0.10:
            points.append(f"Earnings growth of {earnings_growth*100:.1f}% shows profitability improvement")
            evidence["earnings_growth"] = earnings_growth
        
        return {"points": points, "evidence": evidence}
    
    def _analyze_fundamentals(self, data: Dict[str, Any], financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze detailed fundamental data"""
        points = []
        evidence = {}
        
        income = data.get("income_statement", {})
        balance = data.get("balance_sheet", {})
        cash_flow = data.get("cash_flow", {})
        valuation = data.get("valuation_metrics", {})
        
        # Profitability
        revenue = income.get("revenue", 0)
        operating_income = income.get("operating_income", 0)
        if revenue > 0 and operating_income > 0:
            operating_margin = operating_income / revenue
            if operating_margin > 0.20:
                points.append(f"Strong operating margin of {operating_margin*100:.1f}% indicates pricing power")
                evidence["operating_margin"] = operating_margin
        
        # Cash flow strength
        fcf = cash_flow.get("free_cash_flow", 0)
        if fcf > 0:
            points.append("Positive free cash flow generation supports dividend and buyback capacity")
            evidence["free_cash_flow"] = fcf
        
        # Balance sheet strength
        total_cash = balance.get("total_cash", 0)
        total_debt = balance.get("total_debt", 0)
        if total_cash > 0 and total_debt > 0:
            cash_debt_ratio = total_cash / total_debt
            if cash_debt_ratio > 0.5:
                points.append("Strong cash position relative to debt provides financial flexibility")
                evidence["cash_debt_ratio"] = cash_debt_ratio
        
        # Valuation
        ev_ebitda = valuation.get("ev_ebitda")
        if ev_ebitda and ev_ebitda < 12:
            points.append(f"Attractive EV/EBITDA of {ev_ebitda:.1f}x suggests good value")
            evidence["ev_ebitda"] = ev_ebitda
        
        return {"points": points, "evidence": evidence}
    
    def _analyze_analyst_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze analyst ratings and sentiment"""
        points = []
        evidence = {}
        
        rec_key = data.get("recommendation_key", "")
        num_analysts = data.get("number_of_analysts", 0)
        target_mean = data.get("target_mean", 0)
        current_price = data.get("current_price", 0)
        
        if rec_key in ["buy", "strong_buy"]:
            points.append(f"Analyst consensus is '{rec_key}' with {num_analysts} analysts covering")
            evidence["analyst_consensus"] = rec_key
        
        if target_mean > 0 and current_price > 0:
            upside = (target_mean - current_price) / current_price
            if upside > 0.15:
                points.append(f"Analysts see {upside*100:.1f}% upside potential to target price of ${target_mean:.2f}")
                evidence["upside_potential"] = upside
        
        return {"points": points, "evidence": evidence}
    
    def _analyze_sector_position(self, data: Dict[str, Any], financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sector and competitive position"""
        points = []
        evidence = {}
        
        sector = data.get("sector", "")
        competitive_position = data.get("competitive_position", "")
        sector_growth = data.get("sector_growth_rate", 0)
        
        if competitive_position == "strong_competitive_advantage":
            points.append("Strong competitive position with sustainable advantages")
            evidence["competitive_position"] = competitive_position
        elif competitive_position == "competitive":
            points.append("Well-positioned within competitive landscape")
            evidence["competitive_position"] = competitive_position
        
        if sector_growth > 0.10:
            points.append(f"Operating in high-growth sector ({sector_growth*100:.1f}% growth rate)")
            evidence["sector_growth"] = sector_growth
        
        # Adapt to financial context
        market_phase = financial_context.get("market_phase", "normal")
        if market_phase == "recession":
            points.append("In recessionary phase, market leaders typically gain share from weaker competitors")
            evidence["recession_strategy"] = "gain_market_share"
        elif market_phase == "expansion":
            points.append("Economic expansion creates tailwinds for growth")
            evidence["expansion_benefit"] = True
        
        return {"points": points, "evidence": evidence}
    
    def _calculate_confidence(self, key_points: List[str], evidence: Dict[str, Any], 
                             financial_context: Dict[str, Any]) -> float:
        """Calculate confidence score based on evidence strength"""
        base_confidence = 0.50
        
        # Add for each type of evidence
        if "revenue_growth" in evidence:
            base_confidence += 0.05
        if "earnings_growth" in evidence:
            base_confidence += 0.05
        if "free_cash_flow" in evidence:
            base_confidence += 0.05
        if "operating_margin" in evidence:
            base_confidence += 0.05
        if "analyst_consensus" in evidence:
            base_confidence += 0.05
        if "upside_potential" in evidence:
            base_confidence += 0.05
        if "trend_6m" in evidence and evidence["trend_6m"] == "up":
            base_confidence += 0.05
        
        # Number of supporting points
        point_bonus = min(0.10, len(key_points) * 0.02)
        base_confidence += point_bonus
        
        # Financial context adjustment
        vix = financial_context.get("vix_level", 20)
        if vix > 30:  # High volatility reduces confidence
            base_confidence *= 0.95
        
        return min(0.95, max(0.40, base_confidence))
    
    def _create_result(self, key_points: List[str], supporting_evidence: Dict, 
                      requested_data: List[str], start_time: float) -> AnalysisResult:
        """Create analysis result when hitting time limit"""
        confidence = self._calculate_confidence(key_points, supporting_evidence, {})
        
        return AnalysisResult(
            confidence=confidence,
            key_points=key_points + ["Analysis completed within time constraints"],
            supporting_evidence=supporting_evidence,
            requested_data=requested_data,
            analysis_time=time.time() - start_time,
            timestamp=datetime.now()
        )
    
    def argue(self, analysis_result: AnalysisResult, opponent_points: List[str] = None) -> Dict[str, Any]:
        """
        Generate argument for buying/long position
        Can respond to bearish arguments
        """
        points = analysis_result.key_points.copy()
        
        # Address opponent arguments if provided
        if opponent_points:
            for opp_point in opponent_points:
                if "volatility" in opp_point.lower():
                    points.append("While volatility exists, the fundamental strength provides downside protection")
                elif "overvalued" in opp_point.lower() or "expensive" in opp_point.lower():
                    points.append("Valuation is justified by growth trajectory and competitive position")
                elif "risk" in opp_point.lower():
                    points.append("Risk is manageable given strong balance sheet and cash generation")
        
        return {
            "agent": self.agent_id,
            "stance": "constructive",
            "confidence": analysis_result.confidence,
            "points": points,
            "evidence": analysis_result.supporting_evidence,
            "analysis_time": analysis_result.analysis_time,
            "requested_data_count": len(analysis_result.requested_data),
            "timestamp": analysis_result.timestamp.isoformat()
        }
