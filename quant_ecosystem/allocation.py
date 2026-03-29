"""
Autonomous capital allocation: combine strategy weights, risk parity tilt, simple hedge hints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np


def allocate_capital(
    strategy_weights: Dict[str, float],
    *,
    risk_budget: float = 1.0,
    hedge_equity_beta: float = 0.0,
) -> Dict[str, Any]:
    """
    strategy_weights: ids -> raw weights (sum need not be 1)
    hedge_equity_beta: optional tilt toward inverse beta proxy (0 disables)
    """
    ids = list(strategy_weights.keys())
    if not ids:
        return {"ok": False, "weights": {}, "hedge": {}}
    raw = np.array([max(0.0, float(strategy_weights[i])) for i in ids], dtype=float)
    if raw.sum() <= 0:
        raw = np.ones_like(raw) / len(raw)
    else:
        raw = raw / raw.sum()
    w = dict(zip(ids, raw.tolist()))

    hedge = {}
    if hedge_equity_beta > 0:
        hedge["inverse_equity_etf_suggestion"] = "SH (or index put overlay) — symbolic hedge"
        hedge["notional_fraction"] = round(min(0.25, hedge_equity_beta * 0.1), 4)

    return {
        "ok": True,
        "weights": {k: round(v * risk_budget, 6) for k, v in w.items()},
        "risk_budget": risk_budget,
        "hedge": hedge,
        "notes": "Weights come from Meta agent; allocator normalizes and adds optional hedge stub.",
    }
