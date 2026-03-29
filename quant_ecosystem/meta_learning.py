"""
Meta-Learning Agent — adaptive controller.

Tracks decay, reallocates capital across surviving strategies, decides retrain/discard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from .schemas import EcosystemState, RealityReport


@dataclass
class MetaDecision:
    """Actions for the next ecosystem cycle."""

    retrain_ids: List[str]
    discard_ids: List[str]
    weight_updates: Dict[str, float]
    notes: str


class MetaLearningAgent:
    """
    Risk-first allocation: softmax over recent risk-adjusted scores with decay penalty.
    """

    def __init__(
        self,
        *,
        decay_halflife_days: float = 30.0,
        min_weight: float = 0.02,
        entropy_floor: float = 0.05,
    ):
        self.decay_halflife_days = decay_halflife_days
        self.min_weight = min_weight
        self.entropy_floor = entropy_floor

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        x = x - np.max(x)
        e = np.exp(np.clip(x, -20, 20))
        s = e.sum()
        if s <= 0:
            return np.ones_like(x) / len(x)
        return e / s

    def update_from_reports(
        self,
        state: EcosystemState,
        reports: List[RealityReport],
        *,
        now: Optional[datetime] = None,
    ) -> MetaDecision:
        now = now or datetime.utcnow()
        retrain: List[str] = []
        discard: List[str] = []
        scores: Dict[str, float] = {}

        for r in reports:
            sid = f"{r.hypothesis_id}::{r.model_id}"
            if not r.passed:
                discard.append(sid)
                continue
            # Score: Sharpe minus gap penalty — risk control > raw accuracy
            adj = r.sharpe - 2.0 * r.train_val_gap - max(0.0, -r.max_drawdown)
            scores[sid] = adj

            prev = state.last_strategy_scores.get(sid, adj)
            decay = abs(adj - prev) / (abs(prev) + 1e-6)
            state.last_strategy_scores[sid] = adj

            if decay > 0.5:
                retrain.append(sid)

        state.survivors = list(dict.fromkeys(r.model_id for r in reports if r.passed))
        for sid in discard:
            state.strategy_weights.pop(sid, None)

        ids = list(scores.keys())
        if not ids:
            return MetaDecision(
                retrain_ids=retrain,
                discard_ids=discard,
                weight_updates={},
                notes="No passing strategies — ecosystem starved; Alpha should explore more.",
            )

        raw = np.array([scores[i] for i in ids], dtype=float)
        # Entropy floor: blend with uniform to avoid single-strategy fragility
        p = self._softmax(raw)
        u = np.ones_like(p) / len(p)
        blended = (1 - self.entropy_floor) * p + self.entropy_floor * u

        # Apply minimum weight then renormalize
        w = np.maximum(blended, self.min_weight)
        w = w / w.sum()

        weight_updates = {ids[i]: float(w[i]) for i in range(len(ids))}
        state.strategy_weights.update(weight_updates)

        notes = (
            f"Allocated across {len(ids)} strategies; "
            f"discarded {len(discard)}, retrain queue {len(set(retrain))}."
        )
        return MetaDecision(
            retrain_ids=list(dict.fromkeys(retrain)),
            discard_ids=discard,
            weight_updates=weight_updates,
            notes=notes,
        )

    def should_full_retrain(self, state: EcosystemState, last_train: datetime) -> bool:
        """Calendar-based backstop if live metrics unavailable."""
        return datetime.utcnow() - last_train > timedelta(days=7)
