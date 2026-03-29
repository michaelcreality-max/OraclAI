"""
Macro/Economic Analysis Agent
Analyzes macroeconomic conditions and sector trends - independent stance
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class MacroStance:
    """Macroeconomic analysis stance"""
    direction: str  # bullish, bearish, neutral
    conviction: float
    economic_phase: str  # expansion, peak, contraction, trough
    sector_tailwind: str  # positive, neutral, negative
    interest_rate_sensitivity: str  # high, moderate, low
    inflation_impact: str  # positive, neutral, negative
    key_factors: List[str]
    headwinds: List[str]
    tailwinds: List[str]


class MacroEconomicAgent:
    """
    Macro Economic Agent that analyzes economic conditions and sector positioning.
    Independently determines if macro environment supports or hinders the stock.
    """
    
    def __init__(self, data_collection_callback: Callable):
        self.data_collection = data_collection_callback
        self.agent_id = "macro_economic_agent"
        self.max_analysis_time = 60
        
    def analyze(self, symbol: str, initial_data: Dict[str, Any],
                financial_context: Dict[str, Any]) -> MacroStance:
        """Analyze macroeconomic impact and determine independent stance"""
        log.info(f"MacroAgent: Analyzing {symbol} macro environment")
        start_time = time.time()
        
        try:
            fundamentals = initial_data.get("fundamentals", {})
            sector = fundamentals.get("sector", "Unknown")
            industry = fundamentals.get("industry", "Unknown")
            
            # Request macro data
            sector_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="sector_analysis",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            
            factors = []
            headwinds = []
            tailwinds = []
            
            # 1. Economic Phase Analysis
            market_phase = financial_context.get("market_phase", "normal")
            economic_phase = self._determine_economic_phase(financial_context)
            
            # 2. Interest Rate Sensitivity
            rate_sensitivity, rate_impact = self._analyze_rate_sensitivity(
                fundamentals, sector, financial_context
            )
            
            # 3. Inflation Impact
            inflation_impact = self._analyze_inflation_impact(sector, industry, financial_context)
            
            # 4. Sector Rotation Analysis
            sector_score, sector_trend = self._analyze_sector_position(sector_data, sector)
            
            # 5. Geopolitical/Economic Headwinds
            geo_data = self.data_collection(
                agent_id=self.agent_id,
                request_type="geopolitical_context",
                symbol=symbol,
                parameters={},
                urgency="normal"
            )
            
            geopolitical_risk = geo_data.get("trade_sensitivity", "low")
            if geopolitical_risk == "high":
                headwinds.append("High trade/geopolitical sensitivity")
            
            # Calculate overall macro score
            macro_score = 0
            
            # Economic phase impact
            phase_scores = {
                "expansion": 0.3,
                "peak": 0.0,
                "contraction": -0.3,
                "trough": 0.1,  # Early recovery
                "normal": 0.0
            }
            macro_score += phase_scores.get(economic_phase, 0)
            
            # Interest rate impact
            if rate_sensitivity == "high":
                # In rising rate environment, high sensitivity is bad
                vix = financial_context.get("vix_level", 20)
                if vix > 25:  # Proxy for stress
                    macro_score -= 0.2
                    headwinds.append("Rate-sensitive sector in tightening environment")
                else:
                    tailwinds.append("Rate sensitivity manageable in stable environment")
            
            # Sector momentum
            macro_score += sector_score * 0.3
            
            # Inflation impact
            inflation_scores = {
                "positive": 0.15,
                "neutral": 0.0,
                "negative": -0.15
            }
            macro_score += inflation_scores.get(inflation_impact, 0)
            
            # Determine stance
            if macro_score > 0.2:
                direction = "bullish"
            elif macro_score < -0.2:
                direction = "bearish"
            else:
                direction = "neutral"
            
            conviction = min(0.9, abs(macro_score) + 0.2)
            
            # Build factors list
            factors.append(f"Economic phase: {economic_phase.replace('_', ' ').title()}")
            factors.append(f"Interest rate sensitivity: {rate_sensitivity}")
            factors.append(f"Sector momentum: {sector_trend}")
            factors.append(f"Inflation impact: {inflation_impact}")
            
            if geopolitical_risk != "low":
                factors.append(f"Geopolitical risk: {geopolitical_risk}")
            
            # Add tailwinds/headwinds
            if sector_score > 0.3:
                tailwinds.append(f"{sector} sector showing positive momentum")
            elif sector_score < -0.3:
                headwinds.append(f"{sector} sector underperforming")
            
            if economic_phase == "expansion":
                tailwinds.append("Broad economic expansion supports demand")
            elif economic_phase == "contraction":
                headwinds.append("Economic contraction may reduce demand")
            
            analysis_time = time.time() - start_time
            log.info(f"MacroAgent: {direction} stance ({conviction:.2f} conviction)")
            
            return MacroStance(
                direction=direction,
                conviction=conviction,
                economic_phase=economic_phase,
                sector_tailwind="positive" if sector_score > 0.2 else "negative" if sector_score < -0.2 else "neutral",
                interest_rate_sensitivity=rate_sensitivity,
                inflation_impact=inflation_impact,
                key_factors=factors,
                headwinds=headwinds[:5],
                tailwinds=tailwinds[:5]
            )
            
        except Exception as e:
            log.error(f"MacroAgent: Analysis error: {e}")
            return MacroStance(
                direction="neutral",
                conviction=0.4,
                economic_phase="unknown",
                sector_tailwind="neutral",
                interest_rate_sensitivity="moderate",
                inflation_impact="neutral",
                key_factors=["Analysis error - limited macro assessment"],
                headwinds=[],
                tailwinds=[]
            )
    
    def _determine_economic_phase(self, financial_context: Dict) -> str:
        """Determine current economic phase"""
        market_phase = financial_context.get("market_phase", "normal")
        vix = financial_context.get("vix_level", 20)
        
        # Map market conditions to economic phases
        if market_phase == "recession":
            return "contraction"
        elif market_phase == "expansion":
            return "expansion"
        elif vix > 30:
            return "peak"  # High volatility often signals peaks
        elif vix < 15:
            return "trough"  # Low volatility can signal troughs
        else:
            return "normal"
    
    def _analyze_rate_sensitivity(self, fundamentals: Dict, sector: str, 
                                   financial_context: Dict) -> tuple:
        """Analyze interest rate sensitivity"""
        # Sectors with high rate sensitivity
        high_sensitive = ["real estate", "utilities", "financials", "technology"]
        low_sensitive = ["healthcare", "consumer defensive", "energy"]
        
        sector_lower = sector.lower()
        
        if any(s in sector_lower for s in high_sensitive):
            sensitivity = "high"
        elif any(s in sector_lower for s in low_sensitive):
            sensitivity = "low"
        else:
            sensitivity = "moderate"
        
        # Debt levels affect sensitivity
        debt_to_equity = fundamentals.get("debt_to_equity", 0)
        if debt_to_equity > 1.0:
            sensitivity = "high"  # High debt = more sensitive
        
        return sensitivity, "impact_assessed"
    
    def _analyze_inflation_impact(self, sector: str, industry: str, 
                                 financial_context: Dict) -> str:
        """Analyze inflation impact on sector"""
        sector_lower = sector.lower()
        
        # Sectors that benefit from inflation
        beneficiaries = ["energy", "materials", "financials", "real estate"]
        # Sectors hurt by inflation
        hurt = ["consumer cyclical", "technology", "utilities"]
        # Neutral sectors
        neutral = ["healthcare", "industrials", "communication services"]
        
        if any(s in sector_lower for s in beneficiaries):
            return "positive"
        elif any(s in sector_lower for s in hurt):
            return "negative"
        else:
            return "neutral"
    
    def _analyze_sector_position(self, sector_data: Dict, sector: str) -> tuple:
        """Analyze sector positioning and momentum"""
        score = 0
        
        industry_rank = sector_data.get("industry_rank", "mid_tier")
        industry_momentum = sector_data.get("industry_momentum", "stable")
        
        # Rank impact
        if industry_rank == "leader":
            score += 0.2
        elif industry_rank == "major_player":
            score += 0.1
        
        # Momentum impact
        momentum_scores = {
            "strong_momentum": 0.25,
            "positive_momentum": 0.15,
            "stable": 0.0,
            "declining": -0.15
        }
        score += momentum_scores.get(industry_momentum, 0)
        
        return score, industry_momentum
    
    def argue(self, stance: MacroStance, opponent_points: List[str] = None) -> Dict[str, Any]:
        """Generate argument based on macro stance"""
        points = []
        
        # Economic environment
        points.append(f"Economic phase: {stance.economic_phase.replace('_', ' ').title()}")
        points.append(f"Sector tailwinds: {stance.sector_tailwind.upper()}")
        
        # Rate and inflation sensitivity
        points.append(f"Rate sensitivity: {stance.interest_rate_sensitivity}")
        points.append(f"Inflation impact: {stance.inflation_impact}")
        
        # Key factors
        points.extend(stance.key_factors[:4])
        
        # Headwinds and tailwinds
        if stance.tailwinds:
            points.append(f"Macro tailwinds: {', '.join(stance.tailwinds[:2])}")
        if stance.headwinds:
            points.append(f"Macro headwinds: {', '.join(stance.headwinds[:2])}")
        
        # Direction summary
        if stance.direction == "bullish":
            points.append(f"Macro environment supports {stance.conviction*100:.0f}% bullish view")
        elif stance.direction == "bearish":
            points.append(f"Macro headwinds warrant {stance.conviction*100:.0f}% bearish caution")
        else:
            points.append("Mixed macro signals - neutral stance on macro factors")
        
        return {
            "agent": self.agent_id,
            "stance": stance.direction,
            "conviction": stance.conviction,
            "economic_phase": stance.economic_phase,
            "sector_tailwind": stance.sector_tailwind,
            "interest_rate_sensitivity": stance.interest_rate_sensitivity,
            "inflation_impact": stance.inflation_impact,
            "points": points,
            "headwinds": stance.headwinds,
            "tailwinds": stance.tailwinds,
            "timestamp": datetime.now().isoformat()
        }
