"""
Multi-agent debate: Bullish, Bearish, Risk critic, Judge — structured argument + verdict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AgentArgument:
    role: str
    stance: str
    points: List[str]
    confidence: float


@dataclass
class DebateVerdict:
    action: str
    score: float
    rationale: str
    risk_flags: List[str]


class DebateCouncil:
    def run(
        self,
        *,
        symbol: str,
        prediction_summary: Dict[str, Any],
        regime: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        microstructure: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        direction = str(prediction_summary.get("direction", "neutral")).lower()
        conf = float(prediction_summary.get("confidence", 0.5) or 0.5)
        trend = str(regime.get("trend", "sideways"))
        vol = str(regime.get("volatility", "normal"))

        bull_pts = [
            f"Trend regime reads {trend}; momentum aligns with stated direction {direction}.",
            f"Model confidence {conf:.2f} supports incremental long bias if risk allows.",
        ]
        bear_pts = [
            f"Volatility regime {vol} may punish directional bets.",
            "Mean reversion risk rises after extended moves; confirmation needed.",
        ]
        if trend == "bear":
            bear_pts.append("Macro trend bucket is bearish — fade aggressive longs.")
        if vol == "high_vol":
            bear_pts.append("High vol: tail risk dominates short-horizon EV.")

        risk_pts = [
            f"Drawdown proxy from metrics: {risk_metrics.get('max_drawdown_proxy', 'n/a')}",
            f"Sharpe-like gauge: {risk_metrics.get('sharpe_proxy', 'n/a')}",
        ]
        if microstructure:
            risk_pts.append(f"Microstructure stress: {microstructure.get('stress_score', 0):.2f}")

        bull_conf = min(0.95, 0.45 + conf * 0.5 + (0.1 if trend == "bull" else 0.0))
        bear_conf = min(0.95, 0.45 + (0.15 if vol == "high_vol" else 0.0) + (0.1 if trend == "bear" else 0.0))

        score = bull_conf - bear_conf
        if score > 0.25:
            action = "buy"
        elif score < -0.25:
            action = "sell"
        else:
            action = "hold"

        verdict = DebateVerdict(
            action=action,
            score=float(score),
            rationale="Judge weighs trend/vol against model confidence and risk flags.",
            risk_flags=[p for p in risk_pts if "vol" in p.lower() or "Microstructure" in p],
        )

        agents = [
            asdict(AgentArgument("bull", "constructive", bull_pts, bull_conf)),
            asdict(AgentArgument("bear", "skeptical", bear_pts, bear_conf)),
            asdict(AgentArgument("risk", "critique", risk_pts, 0.75)),
        ]
        return {
            "symbol": symbol,
            "agents": agents,
            "judge": asdict(verdict),
        }
