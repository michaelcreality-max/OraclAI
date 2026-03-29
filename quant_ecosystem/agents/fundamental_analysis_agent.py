"""
Fundamental Analysis Agent
Deep dive into company fundamentals - decides stance independently
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class FundamentalStance:
    """Fundamental analysis stance"""
    direction: str  # bullish, bearish, neutral
    conviction: float
    fair_value: float
    valuation_status: str  # undervalued, fair, overvalued
    quality_score: float  # 0-1 business quality
    key_metrics: Dict[str, Any]
    growth_outlook: str  # positive, stable, negative
    concerns: List[str]
    catalysts: List[str]


class FundamentalAnalysisAgent:
    """
    Fundamental Analysis Agent that independently evaluates company quality and valuation.
    NOT pre-assigned - analyzes and decides stance based on fundamentals.
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "fundamental_analysis_agent"
        self.max_analysis_time = 60
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any],
                financial_context: Dict[str, Any]) -> FundamentalStance:
        """Deep fundamental analysis with independent stance determination"""
        log.info(f"FundamentalAgent: Analyzing {symbol}")
        start_time = time.time()
        
        try:
            fundamentals = initial_data.get("fundamentals", {})
            price_data = initial_data.get("price_data", {})
            
            # Request detailed data
            detailed = self.data_collection(
                agent_id=self.agent_id,
                request_type="detailed_fundamentals",
                symbol=symbol,
                parameters={},
                urgency="high"
            )
            
            metrics = {}
            concerns = []
            catalysts = []
            
            # 1. Valuation Analysis
            valuation_score, val_status, fair_value = self._analyze_valuation(
                fundamentals, detailed, price_data
            )
            metrics["valuation_score"] = valuation_score
            
            # 2. Profitability Quality
            profit_score, profit_metrics = self._analyze_profitability(detailed)
            metrics["profitability"] = profit_score
            
            # 3. Growth Analysis
            growth_score, growth_outlook, growth_metrics = self._analyze_growth(
                fundamentals, detailed
            )
            metrics["growth"] = growth_score
            
            # 4. Financial Health
            health_score, health_metrics, health_concerns = self._analyze_financial_health(
                detailed, fundamentals
            )
            metrics["financial_health"] = health_score
            concerns.extend(health_concerns)
            
            # 5. Competitive Position
            quality_score, comp_metrics = self._analyze_competitive_position(fundamentals)
            metrics["quality"] = quality_score
            
            # Calculate overall stance
            total_score = (valuation_score + profit_score + growth_score + 
                          health_score + quality_score) / 5
            
            # Determine direction
            if total_score > 0.2 and growth_outlook in ["positive", "stable"]:
                direction = "bullish"
            elif total_score < -0.2 or growth_outlook == "negative":
                direction = "bearish"
            else:
                direction = "neutral"
            
            # Determine conviction
            conviction = min(0.95, abs(total_score) + 0.3)
            
            # Identify catalysts
            if growth_outlook == "positive":
                catalysts.append("Earnings growth trajectory positive")
            if val_status == "undervalued":
                catalysts.append("Valuation gap provides upside potential")
            if quality_score > 0.7:
                catalysts.append("Strong competitive moat supports premium")
            
            analysis_time = time.time() - start_time
            log.info(f"FundamentalAgent: {direction} stance, fair value ${fair_value:.2f}")
            
            return FundamentalStance(
                direction=direction,
                conviction=conviction,
                fair_value=fair_value,
                valuation_status=val_status,
                quality_score=quality_score,
                key_metrics=metrics,
                growth_outlook=growth_outlook,
                concerns=concerns[:5],
                catalysts=catalysts[:5]
            )
            
        except Exception as e:
            log.error(f"FundamentalAgent: Analysis error: {e}")
            return FundamentalStance(
                direction="neutral",
                conviction=0.5,
                fair_value=0,
                valuation_status="unknown",
                quality_score=0.5,
                key_metrics={},
                growth_outlook="unknown",
                concerns=["Analysis error"],
                catalysts=[]
            )
    
    def _analyze_valuation(self, fundamentals: Dict, detailed: Dict, 
                          price_data: Dict) -> tuple:
        """Analyze valuation metrics"""
        score = 0
        
        pe = fundamentals.get("pe_ratio")
        forward_pe = fundamentals.get("forward_pe")
        ps = fundamentals.get("price_to_sales")
        pb = fundamentals.get("price_to_book")
        current_price = price_data.get("current_price", 0)
        
        # P/E analysis
        pe_score = 0
        if pe:
            if pe < 15:
                pe_score = 0.3
                status = "undervalued"
            elif pe < 25:
                pe_score = 0.1
                status = "fair"
            elif pe < 35:
                pe_score = -0.1
                status = "elevated"
            else:
                pe_score = -0.3
                status = "overvalued"
        else:
            status = "unknown"
        
        score += pe_score
        
        # Growth-adjusted valuation
        peg = fundamentals.get("peg_ratio")
        if peg:
            if peg < 1.0:
                score += 0.2
            elif peg > 2.0:
                score -= 0.2
        
        # Estimate fair value
        if pe and current_price > 0:
            # Simple fair value estimate based on sector-appropriate multiple
            sector_pe = 20  # Assumed sector average
            fair_value = current_price * (sector_pe / pe)
        else:
            fair_value = current_price
        
        return score, status, fair_value
    
    def _analyze_profitability(self, detailed: Dict) -> tuple:
        """Analyze profitability metrics"""
        score = 0
        metrics = {}
        
        income = detailed.get("income_statement", {})
        
        # Operating margin
        revenue = income.get("revenue", 0)
        op_income = income.get("operating_income", 0)
        if revenue > 0 and op_income > 0:
            op_margin = op_income / revenue
            metrics["operating_margin"] = op_margin
            
            if op_margin > 0.20:
                score += 0.25
            elif op_margin > 0.10:
                score += 0.10
            elif op_margin < 0.05:
                score -= 0.15
        
        return score, metrics
    
    def _analyze_growth(self, fundamentals: Dict, detailed: Dict) -> tuple:
        """Analyze growth metrics"""
        score = 0
        metrics = {}
        
        rev_growth = fundamentals.get("revenue_growth")
        earnings_growth = fundamentals.get("earnings_growth")
        
        if rev_growth is not None:
            metrics["revenue_growth"] = rev_growth
            if rev_growth > 0.20:
                score += 0.25
                outlook = "positive"
            elif rev_growth > 0.10:
                score += 0.15
                outlook = "positive"
            elif rev_growth > 0:
                score += 0.05
                outlook = "stable"
            else:
                score -= 0.20
                outlook = "negative"
        else:
            outlook = "unknown"
        
        if earnings_growth is not None:
            metrics["earnings_growth"] = earnings_growth
            if earnings_growth > 0.25:
                score += 0.25
            elif earnings_growth < 0:
                score -= 0.20
        
        return score, outlook, metrics
    
    def _analyze_financial_health(self, detailed: Dict, fundamentals: Dict) -> tuple:
        """Analyze balance sheet strength"""
        score = 0
        metrics = {}
        concerns = []
        
        balance = detailed.get("balance_sheet", {})
        
        # Cash vs Debt
        cash = balance.get("total_cash", 0)
        debt = balance.get("total_debt", 0)
        
        if cash > 0 and debt > 0:
            cash_debt_ratio = cash / debt
            metrics["cash_debt_ratio"] = cash_debt_ratio
            
            if cash_debt_ratio > 1.0:
                score += 0.20
            elif cash_debt_ratio > 0.5:
                score += 0.10
            else:
                score -= 0.10
                concerns.append("Low cash relative to debt")
        
        # Current ratio
        current_ratio = fundamentals.get("current_ratio")
        if current_ratio:
            metrics["current_ratio"] = current_ratio
            if current_ratio > 2.0:
                score += 0.10
            elif current_ratio < 1.0:
                score -= 0.15
                concerns.append("Liquidity concerns (current ratio < 1)")
        
        return score, metrics, concerns
    
    def _analyze_competitive_position(self, fundamentals: Dict) -> tuple:
        """Analyze competitive quality"""
        score = 0.5  # Neutral starting point
        metrics = {}
        
        # ROE as quality indicator
        roe = fundamentals.get("return_on_equity")
        if roe:
            metrics["roe"] = roe
            if roe > 0.20:
                score += 0.25
            elif roe > 0.15:
                score += 0.15
            elif roe < 0.08:
                score -= 0.15
        
        # Profit margins as moat indicator
        margins = fundamentals.get("profit_margins")
        if margins:
            metrics["profit_margins"] = margins
            if margins > 0.20:
                score += 0.15
        
        return min(1.0, score), metrics
    
    def argue(self, stance: FundamentalStance, opponent_points: List[str] = None) -> Dict[str, Any]:
        """Generate argument based on fundamental stance"""
        points = []
        
        # Valuation summary
        points.append(f"Valuation: {stance.valuation_status.upper()} (fair value: ${stance.fair_value:.2f})")
        
        # Quality assessment
        if stance.quality_score > 0.7:
            points.append(f"High-quality business (score: {stance.quality_score:.2f})")
        elif stance.quality_score < 0.4:
            points.append(f"Business quality concerns (score: {stance.quality_score:.2f})")
        
        # Growth outlook
        points.append(f"Growth outlook: {stance.growth_outlook.upper()}")
        
        # Key metrics summary
        for metric, value in stance.key_metrics.items():
            if isinstance(value, (int, float)):
                points.append(f"{metric.replace('_', ' ').title()}: {value:.2f}")
        
        # Catalysts and concerns
        if stance.catalysts:
            points.append(f"Catalysts: {', '.join(stance.catalysts[:3])}")
        if stance.concerns:
            points.append(f"Concerns: {', '.join(stance.concerns[:3])}")
        
        # Direction-specific commentary
        if stance.direction == "bullish":
            points.append(f"Fundamentals support {stance.conviction*100:.0f}% bullish conviction")
        elif stance.direction == "bearish":
            points.append(f"Fundamental deterioration warrants {stance.conviction*100:.0f}% bearish stance")
        else:
            points.append("Fundamentals mixed - fair value approximately at current price")
        
        return {
            "agent": self.agent_id,
            "stance": stance.direction,
            "conviction": stance.conviction,
            "fair_value": stance.fair_value,
            "valuation_status": stance.valuation_status,
            "quality_score": stance.quality_score,
            "growth_outlook": stance.growth_outlook,
            "points": points,
            "concerns": stance.concerns,
            "catalysts": stance.catalysts,
            "timestamp": datetime.now().isoformat()
        }
