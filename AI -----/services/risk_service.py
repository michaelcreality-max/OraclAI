"""
RiskService - Comprehensive risk management
Phase 5 Implementation
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.data_structures import AgentPosition, RiskAssessment, OrderDecision
from core.exceptions import RiskError

log = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PositionRisk:
    """Risk metrics for a single position"""
    symbol: str
    position_size: float
    risk_amount: float  # Dollar amount at risk
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    beta: float
    correlation_to_portfolio: float
    concentration_risk: float


@dataclass
class PortfolioRiskState:
    """Complete risk state of portfolio"""
    total_exposure: float
    net_exposure: float
    gross_exposure: float
    var_95: float
    var_99: float
    max_drawdown_current: float
    risk_level: RiskLevel
    heat_map: Dict[str, float] = field(default_factory=dict)
    limit_breaches: List[str] = field(default_factory=list)


class RiskService:
    """
    Comprehensive risk management service
    Enforces limits, monitors exposure, provides risk overlays
    """
    
    # Risk limits
    DEFAULT_LIMITS = {
        'max_position_size': 0.10,  # 10% per position
        'max_sector_exposure': 0.30,  # 30% per sector
        'max_portfolio_heat': 0.70,  # 70% total exposure
        'max_daily_loss': 0.02,  # 2% daily loss limit
        'max_drawdown': 0.15,  # 15% max drawdown
        'min_cash_buffer': 0.05,  # 5% minimum cash
        'max_correlation': 0.80,  # 80% max correlation
        'var_95_limit': 0.03,  # 3% daily VaR limit
    }
    
    def __init__(self, limits: Optional[Dict] = None):
        self.limits = limits or self.DEFAULT_LIMITS.copy()
        self.current_positions: Dict[str, AgentPosition] = {}
        self.daily_pnl: List[Dict] = []
        self.risk_events: List[Dict] = []
        
        log.info("RiskService initialized")
    
    def assess_position_risk(self, position: AgentPosition,
                            market_data: Optional[Dict] = None) -> PositionRisk:
        """
        Assess risk for a single position
        """
        # Estimate VaR from position size and volatility
        volatility = market_data.get('volatility', 0.20) if market_data else 0.20
        var_95 = position.position_size_pct * volatility * 1.65
        var_99 = position.position_size_pct * volatility * 2.33
        
        # Risk amount (assuming $100k portfolio for example)
        portfolio_value = 100000
        risk_amount = var_95 * portfolio_value
        
        return PositionRisk(
            symbol=position.symbol,
            position_size=position.position_size_pct,
            risk_amount=risk_amount,
            var_95=var_95,
            var_99=var_99,
            beta=market_data.get('beta', 1.0) if market_data else 1.0,
            correlation_to_portfolio=0.5,  # Default
            concentration_risk=position.position_size_pct / self.limits['max_position_size']
        )
    
    def calculate_portfolio_risk(self, positions: List[AgentPosition]) -> PortfolioRiskState:
        """
        Calculate comprehensive portfolio risk metrics
        """
        if not positions:
            return PortfolioRiskState(
                total_exposure=0.0,
                net_exposure=0.0,
                gross_exposure=0.0,
                var_95=0.0,
                var_99=0.0,
                max_drawdown_current=0.0,
                risk_level=RiskLevel.LOW,
                heat_map={},
                limit_breaches=[]
            )
        
        # Calculate exposures
        long_exposure = sum(p.position_size_pct for p in positions 
                           if p.stance.value == 'buy')
        short_exposure = sum(p.position_size_pct for p in positions 
                            if p.stance.value == 'sell')
        
        gross_exposure = long_exposure + short_exposure
        net_exposure = abs(long_exposure - short_exposure)
        
        # Simple VaR calculation (diversified)
        individual_vars = [
            p.position_size_pct * 0.20 * 1.65 for p in positions
        ]
        portfolio_var_95 = sum(individual_vars) * 0.7  # Diversification benefit
        
        # Check limits
        breaches = []
        if gross_exposure > self.limits['max_portfolio_heat']:
            breaches.append(f"Portfolio heat {gross_exposure:.1%} exceeds limit")
        if portfolio_var_95 > self.limits['var_95_limit']:
            breaches.append(f"VaR {portfolio_var_95:.2%} exceeds limit")
        
        # Determine risk level
        if breaches:
            risk_level = RiskLevel.CRITICAL if len(breaches) > 1 else RiskLevel.HIGH
        elif gross_exposure > self.limits['max_portfolio_heat'] * 0.8:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Heat map
        heat_map = {p.symbol: p.position_size_pct for p in positions}
        
        return PortfolioRiskState(
            total_exposure=gross_exposure,
            net_exposure=net_exposure,
            gross_exposure=gross_exposure,
            var_95=portfolio_var_95,
            var_99=portfolio_var_95 * 1.4,  # Approximate
            max_drawdown_current=self._calculate_drawdown(),
            risk_level=risk_level,
            heat_map=heat_map,
            limit_breaches=breaches
        )
    
    def check_order_risk(self, order: OrderDecision,
                        current_positions: List[AgentPosition]) -> Dict:
        """
        Check if order complies with risk limits
        
        Returns:
            Dict with approved status and any restrictions
        """
        issues = []
        restrictions = {}
        
        # Check position size
        if order.position_size_pct > self.limits['max_position_size']:
            issues.append(f"Position size {order.position_size_pct:.1%} exceeds limit")
            restrictions['max_size'] = self.limits['max_position_size']
        
        # Check portfolio heat
        current_heat = sum(p.position_size_pct for p in current_positions)
        new_heat = current_heat + order.position_size_pct
        
        if new_heat > self.limits['max_portfolio_heat']:
            issues.append(f"Portfolio heat would be {new_heat:.1%}")
            restrictions['reduced_size'] = self.limits['max_portfolio_heat'] - current_heat
        
        # Check conviction threshold for large positions
        if order.position_size_pct > 0.05 and order.conviction < 0.6:
            issues.append("Low conviction for large position")
        
        approved = len(issues) == 0
        
        if not approved:
            log.warning(f"Order for {order.symbol} has risk issues: {issues}")
        
        return {
            'approved': approved,
            'issues': issues,
            'restrictions': restrictions,
            'risk_level': 'high' if issues else 'normal'
        }
    
    def update_position(self, position: AgentPosition):
        """Update tracked position"""
        if position.position_size_pct > 0:
            self.current_positions[position.symbol] = position
        else:
            self.current_positions.pop(position.symbol, None)
    
    def record_daily_pnl(self, date: datetime, pnl_pct: float):
        """Record daily P&L for drawdown calculation"""
        self.daily_pnl.append({
            'date': date,
            'pnl_pct': pnl_pct
        })
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown from daily P&L history"""
        if not self.daily_pnl:
            return 0.0
        
        # Simplified - track peak and current
        cumulative = 1.0
        peak = 1.0
        max_dd = 0.0
        
        for day in self.daily_pnl[-252:]:  # Last year
            cumulative *= (1 + day['pnl_pct'])
            peak = max(peak, cumulative)
            dd = (peak - cumulative) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def get_risk_summary(self) -> Dict:
        """Get current risk summary"""
        positions = list(self.current_positions.values())
        portfolio_risk = self.calculate_portfolio_risk(positions)
        
        return {
            'gross_exposure': portfolio_risk.gross_exposure,
            'net_exposure': portfolio_risk.net_exposure,
            'var_95': portfolio_risk.var_95,
            'current_drawdown': portfolio_risk.max_drawdown_current,
            'risk_level': portfolio_risk.risk_level.value,
            'limit_breaches': portfolio_risk.limit_breaches,
            'n_positions': len(positions)
        }
    
    def generate_risk_report(self) -> str:
        """Generate human-readable risk report"""
        summary = self.get_risk_summary()
        
        report = []
        report.append("=" * 50)
        report.append("RISK MANAGEMENT REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 50)
        report.append("")
        report.append(f"Portfolio Heat: {summary['gross_exposure']:.1%}")
        report.append(f"Net Exposure: {summary['net_exposure']:.1%}")
        report.append(f"Daily VaR (95%): {summary['var_95']:.2%}")
        report.append(f"Current Drawdown: {summary['current_drawdown']:.1%}")
        report.append(f"Risk Level: {summary['risk_level'].upper()}")
        report.append("")
        
        if summary['limit_breaches']:
            report.append("⚠️  LIMIT BREACHES:")
            for breach in summary['limit_breaches']:
                report.append(f"   - {breach}")
        else:
            report.append("✓ All risk limits within bounds")
        
        report.append("")
        report.append(f"Active Positions: {summary['n_positions']}")
        report.append("=" * 50)
        
        return "\n".join(report)


# Global instance
risk_service = RiskService()
