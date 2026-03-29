"""
Self-evolving strategies: feature mutation, invented indicators, genetic crossover,
and kill-switch for underperforming models (population-based evolution).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from .schemas import RealityReport


@dataclass
class StrategyDNA:
    """Genetic encoding for a strategy (features + optional nonlinear tags)."""

    id: str
    feature_names: List[str]
    recipe_tags: List[str] = field(default_factory=list)
    generation: int = 0
    fitness_hint: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


def _stable_id(parts: List[str]) -> str:
    return "dna_" + hashlib.sha256("|".join(parts).encode()).hexdigest()[:10]


def mutate_feature_set(
    base_columns: List[str],
    current: List[str],
    *,
    mutation_rate: float = 0.25,
    seed: Optional[int] = None,
) -> List[str]:
    rng = random.Random(seed)
    pool = list(base_columns)
    out = list(current)
    for i in range(len(out)):
        if rng.random() < mutation_rate:
            out[i] = rng.choice(pool)
    if rng.random() < 0.3 and len(out) < min(12, len(pool)):
        out.append(rng.choice(pool))
    if rng.random() < 0.2 and len(out) > 2:
        out.pop(rng.randrange(len(out)))
    return list(dict.fromkeys(out))


def crossover_strategies(a: StrategyDNA, b: StrategyDNA, seed: Optional[int] = None) -> StrategyDNA:
    rng = random.Random(seed)
    pool = list(dict.fromkeys(a.feature_names + b.feature_names))
    if len(pool) < 2:
        merged = pool
    else:
        cut = rng.randint(1, len(pool) - 1)
        merged = pool[:cut] + [c for c in pool[cut:] if c not in pool[:cut]]
    k = min(len(merged), max(2, rng.randint(3, min(10, len(merged)))))
    merged = merged[:k]
    return StrategyDNA(
        id=_stable_id([a.id, b.id, str(rng.random())]),
        feature_names=merged,
        recipe_tags=list(dict.fromkeys(a.recipe_tags + b.recipe_tags)),
        generation=max(a.generation, b.generation) + 1,
    )


def apply_invented_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Non-standard indicators (beyond classic RSI): nonlinear combos the system can evolve against.
    Names are stable for genetic search / Arena feature lists.
    """
    out = df.copy()
    if "ret_1" in out.columns and "vol_20" in out.columns:
        out["inv_thrust"] = np.tanh(out["ret_1"] * 50.0) * (1.0 / (1.0 + out["vol_20"] * 80.0))
    if "rsi_14" in out.columns and "mom_10" in out.columns:
        out["inv_chop_filter"] = (out["rsi_14"] / 100.0 - 0.5) * out["mom_10"]
    if "vol_z" in out.columns and "hl_range" in out.columns:
        out["inv_liquidity_stress"] = out["vol_z"] * out["hl_range"]
    if "rel_strength" in out.columns and "beta_proxy" in out.columns:
        r1 = out["ret_1"] if "ret_1" in out.columns else 0.0
        out["inv_macro_residual"] = out["rel_strength"] - out["beta_proxy"] * r1
    return out.replace([np.inf, -np.inf], np.nan).dropna()


class KillSwitchRegistry:
    """Automatically retire model/strategy ids that breach risk or quality bounds."""

    def __init__(
        self,
        *,
        min_sharpe: float = 0.0,
        max_drawdown: float = -0.45,
        max_gap: float = 0.08,
    ):
        self.min_sharpe = min_sharpe
        self.max_drawdown = max_drawdown
        self.max_gap = max_gap
        self.killed_ids: Set[str] = set()
        self.kill_reasons: Dict[str, str] = {}

    def evaluate(self, model_id: str, report: RealityReport) -> bool:
        """Return True if killed."""
        reasons: List[str] = []
        if not report.passed:
            reasons.append(report.kill_reason or "failed reality gate")
        if report.sharpe < self.min_sharpe:
            reasons.append("sharpe_floor")
        if report.max_drawdown < self.max_drawdown:
            reasons.append("drawdown")
        if report.train_val_gap > self.max_gap:
            reasons.append("overfit_gap")
        if reasons:
            self.killed_ids.add(model_id)
            self.kill_reasons[model_id] = "; ".join(reasons)
            return True
        return False


class StrategyPopulation:
    """Maintains a population of StrategyDNA with tournament replacement."""

    def __init__(self, max_size: int = 64):
        self.max_size = max_size
        self.items: Dict[str, StrategyDNA] = {}

    def upsert(self, dna: StrategyDNA) -> None:
        self.items[dna.id] = dna
        if len(self.items) > self.max_size:
            worst = sorted(self.items.values(), key=lambda x: x.fitness_hint)[: len(self.items) - self.max_size]
            for w in worst:
                self.items.pop(w.id, None)

    def evolve_step(
        self,
        base_columns: List[str],
        top: List[StrategyDNA],
        rng: random.Random,
    ) -> List[StrategyDNA]:
        children: List[StrategyDNA] = []
        if len(top) >= 2:
            for _ in range(2):
                a, b = rng.sample(top, 2)
                c = crossover_strategies(a, b, seed=rng.randint(0, 2**31 - 1))
                c.feature_names = mutate_feature_set(base_columns, c.feature_names, seed=rng.randint(0, 2**31 - 1))
                c.id = _stable_id([c.id, str(rng.random())])
                children.append(c)
        return children
