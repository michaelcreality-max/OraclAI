"""
Causal-style reasoning layer: explicit event graph + simple structural 'what-if' propagation.
This is not full causal discovery from data; it encodes domain edges and runs counterfactual deltas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CausalEdge:
    cause: str
    effect: str
    strength: float  # multiplier on shock to cause
    lag_days: int = 0


@dataclass
class CausalGraph:
    """Lightweight adjacency list for narrative + numeric what-if."""

    edges: List[CausalEdge] = field(default_factory=list)

    def add(self, cause: str, effect: str, strength: float, lag_days: int = 0) -> None:
        self.edges.append(CausalEdge(cause, effect, strength, lag_days))

    def propagate(self, shocks: Dict[str, float]) -> Dict[str, float]:
        """Forward propagation: effect += strength * shock[cause]."""
        out: Dict[str, float] = {}
        for k, v in shocks.items():
            out[k] = out.get(k, 0.0) + v
        for e in self.edges:
            if e.cause in shocks:
                delta = e.strength * shocks[e.cause]
                out[e.effect] = out.get(e.effect, 0.0) + delta
        return out


def default_macro_graph() -> CausalGraph:
    g = CausalGraph()
    g.add("fed_rate_hike", "tech_stocks", -0.6)
    g.add("fed_rate_hike", "bonds", -0.4)
    g.add("inflation_up", "real_rates", 0.5)
    g.add("oil_up", "airlines", -0.7)
    g.add("oil_up", "energy_sector", 0.55)
    g.add("bonds_down", "growth_stocks", 0.35)
    g.add("usd_up", "emerging_markets", -0.45)
    return g


def what_if_scenario(
    graph: CausalGraph,
    scenario: Dict[str, float],
    *,
    baseline: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Example: scenario = {"inflation_up": 0.02}  → propagated effects on named nodes.
    """
    base = dict(baseline or {})
    propagated = graph.propagate(scenario)
    combined = {**base, **propagated}
    return {
        "scenario_shocks": scenario,
        "propagated_effects": propagated,
        "combined_state": combined,
        "notes": "Effects are relative units for ranking/routing, not price forecasts.",
    }


def event_impact_narrative(event: str, graph: Optional[CausalGraph] = None) -> Dict[str, Any]:
    """Return edges touching an event for transparency (e.g. Fed hike → tech)."""
    graph = graph or default_macro_graph()
    related = [e for e in graph.edges if e.cause == event or e.effect == event]
    return {
        "event": event,
        "edges": [
            {"cause": e.cause, "effect": e.effect, "strength": e.strength, "lag_days": e.lag_days}
            for e in related
        ],
    }
