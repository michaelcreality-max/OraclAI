"""
Alpha Discovery Agent — idea generator.

Generates hypotheses via:
- Feature search (genetic algorithm over feature subsets)
- LLM-based hypotheses when API keys are present
- Deliberately unconventional recipe templates
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import urllib.request
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .schemas import AlphaHypothesis


def _stable_id(parts: Sequence[str]) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]
    return f"h_{h}"


class GeneticFeatureSearch:
    """
    Evolve binary masks over `base_columns` to maximize correlation with target
    (quick fitness proxy — full validation happens downstream).
    """

    def __init__(
        self,
        base_columns: List[str],
        population_size: int = 24,
        generations: int = 12,
        crossover_rate: float = 0.65,
        mutation_rate: float = 0.15,
        seed: Optional[int] = None,
    ):
        self.base_columns = list(base_columns)
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self._rng = random.Random(seed)

    def _random_mask(self) -> List[int]:
        return [self._rng.randint(0, 1) for _ in self.base_columns]

    def _crossover(self, a: List[int], b: List[int]) -> Tuple[List[int], List[int]]:
        if len(a) != len(b):
            raise ValueError("Length mismatch")
        if len(a) < 2:
            return a[:], b[:]
        point = self._rng.randint(1, len(a) - 1)
        c1 = a[:point] + b[point:]
        c2 = b[:point] + a[point:]
        return c1, c2

    def _mutate(self, m: List[int]) -> None:
        for i in range(len(m)):
            if self._rng.random() < self.mutation_rate:
                m[i] = 1 - m[i]

    def _fitness(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        mask: List[int],
    ) -> float:
        cols = [c for c, bit in zip(self.base_columns, mask) if bit]
        if not cols:
            return -1e9
        combo = X[cols].mean(axis=1)
        aligned = pd.concat([combo, y], axis=1).dropna()
        if len(aligned) < 30:
            return -1e9
        corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        if corr is None or np.isnan(corr):
            return -1e9
        return float(abs(corr))

    def run(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Tuple[List[str], float]:
        pop = [self._random_mask() for _ in range(self.population_size)]
        best_mask = pop[0][:]
        best_fit = self._fitness(X, y, best_mask)

        for _ in range(self.generations):
            scored = [(m, self._fitness(X, y, m)) for m in pop]
            scored.sort(key=lambda t: t[1], reverse=True)
            if scored[0][1] > best_fit:
                best_fit = scored[0][1]
                best_mask = scored[0][0][:]

            survivors = [m for m, _ in scored[: max(2, self.population_size // 4)]]
            next_gen: List[List[int]] = survivors[:]
            while len(next_gen) < self.population_size:
                p1, p2 = self._rng.choice(survivors), self._rng.choice(survivors)
                if self._rng.random() < self.crossover_rate:
                    c1, c2 = self._crossover(p1, p2)
                else:
                    c1, c2 = p1[:], p2[:]
                self._mutate(c1)
                self._mutate(c2)
                next_gen.append(c1)
                if len(next_gen) < self.population_size:
                    next_gen.append(c2)
            pop = next_gen[: self.population_size]

        selected = [c for c, bit in zip(self.base_columns, best_mask) if bit]
        if not selected:
            selected = [self.base_columns[self._rng.randrange(len(self.base_columns))]]
        return selected, best_fit


class LLMHypothesisGenerator:
    """
    Local AI hypothesis generator using templates and algorithms.
    Uses NO external APIs - completely self-contained.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load local knowledge base for hypothesis generation"""
        return {
            "momentum_factors": [
                "Rank stocks by (momentum * inverse volatility) on rolling fear spikes from VIX proxy.",
                "Use ratio of 5d return to 20d realized vol as a 'risk-adjusted thrust' signal.",
                "Combine momentum_12m with momentum_1m for intermediate-term persistence.",
            ],
            "mean_reversion_factors": [
                "Cross-asset: fade relative strength vs SPY when beta_proxy > 1.2 and RSI overbought.",
                "Unconventional: sign(ret_1) * sign(rel_strength) * (1 - hl_range) as a contrarian chop filter.",
                "Long-term reversal: stocks with worst 12m performance but recent 1m uptick.",
            ],
            "sentiment_factors": [
                "Sentiment placeholder spike: combine sentiment_social with vol_z only on high volume days.",
                "Analyst divergence: stocks with high dispersion in analyst target prices.",
                "Insider activity: buying pressure from recent insider transactions.",
            ],
            "quality_factors": [
                "Profitability stability: coefficient of variation of quarterly ROE.",
                "Balance sheet strength: (cash - debt) / market cap for liquidity screening.",
                "Earnings quality: accruals to cash flow ratio trend.",
            ],
            "technical_indicators": [
                "Support/Resistance breakouts with volume confirmation above 150% average.",
                "Bollinger Band squeeze: volatility contraction before expansion signals.",
                "MACD histogram divergence from price for early trend reversal detection.",
            ]
        }

    def _templates(self, symbols_context: str) -> List[Dict[str, Any]]:
        """Generate template-based unconventional ideas using local knowledge"""
        # Combine all factor categories
        all_factors = []
        for category, factors in self._knowledge_base.items():
            for factor in factors:
                all_factors.append({"category": category, "description": factor})

        # Randomly select 3-5 unique factors
        selected = self._rng.sample(all_factors, k=min(self._rng.randint(3, 5), len(all_factors)))

        out = []
        for item in selected:
            factor = item["description"]
            category = item["category"]

            # Generate feature hints based on category
            hints = self._generate_feature_hints(category)

            out.append(
                {
                    "description": factor + f" Context: {symbols_context}.",
                    "feature_hints": hints,
                    "unconventional": True,
                    "category": category,
                    "local_ai_generated": True
                }
            )
        return out

    def _generate_feature_hints(self, category: str) -> List[str]:
        """Generate appropriate feature hints based on factor category"""
        hint_map = {
            "momentum_factors": ["ret_5", "ret_20", "ret_60", "volatility_20", "momentum_12m"],
            "mean_reversion_factors": ["rel_strength", "rsi_14", "beta_proxy", "hl_range", "ret_1"],
            "sentiment_factors": ["sentiment_social", "vol_z", "volume_20", "analyst_dispersion"],
            "quality_factors": ["roe_cv", "cash_debt_ratio", "accruals_cfo", "earnings_quality"],
            "technical_indicators": ["volume_ratio", "bb_squeeze", "macd_hist", "price_20"]
        }
        return hint_map.get(category, ["ret_5", "vol_20", "volume"])

    def _generate_composite_idea(self, context: str) -> Dict[str, Any]:
        """Generate a composite hypothesis combining multiple factors"""
        # Select 2 random categories to combine
        categories = list(self._knowledge_base.keys())
        cat1, cat2 = self._rng.sample(categories, k=2)

        factor1 = self._rng.choice(self._knowledge_base[cat1])
        factor2 = self._rng.choice(self._knowledge_base[cat2])

        return {
            "description": f"Composite: {factor1} AND {factor2} Context: {context}.",
            "feature_hints": self._generate_feature_hints(cat1) + self._generate_feature_hints(cat2),
            "unconventional": True,
            "category": "composite",
            "local_ai_generated": True
        }

    def generate_raw_ideas(self, context: str) -> List[Dict[str, Any]]:
        """
        Generate alpha ideas using local AI - NO external API calls.
        Uses knowledge base and algorithmic generation.
        """
        # Get template-based ideas
        ideas = self._templates(context)

        # Add a composite idea
        ideas.append(self._generate_composite_idea(context))

        # Add a personalized variation based on context keywords
        if "tech" in context.lower() or "growth" in context.lower():
            ideas.append({
                "description": f"Tech-specific: High beta momentum during earnings season. Context: {context}.",
                "feature_hints": ["beta", "momentum_3m", "earnings_date", "implied_vol"],
                "unconventional": True,
                "category": "sector_specific",
                "local_ai_generated": True
            })
        elif "value" in context.lower() or "dividend" in context.lower():
            ideas.append({
                "description": f"Value play: Book-to-market with earnings stability. Context: {context}.",
                "feature_hints": ["book_to_market", "earnings_stability", "dividend_yield", "roe"],
                "unconventional": True,
                "category": "sector_specific",
                "local_ai_generated": True
            })

        return ideas

    def to_hypotheses(self, raw: List[Dict[str, Any]], available_columns: Sequence[str]) -> List[AlphaHypothesis]:
        avail = set(available_columns)
        hyps: List[AlphaHypothesis] = []
        for obj in raw:
            hints = [h for h in obj.get("feature_hints", []) if h in avail]
            if not hints:
                hints = list(avail)[:5]
            hid = _stable_id([obj.get("description", ""), ",".join(sorted(hints))])
            hyps.append(
                AlphaHypothesis(
                    id=hid,
                    description=str(obj.get("description", "LLM/template hypothesis")),
                    feature_names=hints,
                    tags=["llm" if os.environ.get("OPENAI_API_KEY") else "template"],
                    unconventional=bool(obj.get("unconventional", False)),
                    llm_rationale=obj.get("rationale"),
                )
            )
        return hyps


class AlphaDiscoveryAgent:
    """Orchestrates genetic search + LLM/templates into concrete hypotheses."""

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self.llm = LLMHypothesisGenerator(seed=seed)

    def discover(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        genetic: Optional[GeneticFeatureSearch] = None,
        n_llm: int = 3,
        context: str = "",
    ) -> List[AlphaHypothesis]:
        base_cols = list(X.columns)
        gfs = genetic or GeneticFeatureSearch(base_cols, seed=self._rng.randint(0, 2**31 - 1))
        selected, _ = gfs.run(X, y)

        genetic_hyp = AlphaHypothesis(
            id=_stable_id(["genetic", ",".join(selected)]),
            description="Genetic search over feature subsets (max abs correlation to forward return).",
            feature_names=selected,
            tags=["genetic", "feature_search"],
            unconventional=True,
        )

        raw = self.llm.generate_raw_ideas(context or "US equities daily")
        llm_hyps = self.llm.to_hypotheses(raw[:n_llm], base_cols)

        # Extra creative mashups: random unconventional combos
        mashups: List[AlphaHypothesis] = []
        for _ in range(2):
            k = self._rng.randint(3, min(7, len(base_cols)))
            cols = self._rng.sample(base_cols, k=k)
            mashups.append(
                AlphaHypothesis(
                    id=_stable_id(["mashup", ",".join(sorted(cols))]),
                    description="Random unconventional feature bundle for fast exploration.",
                    feature_names=cols,
                    tags=["mashup", "unconventional"],
                    unconventional=True,
                )
            )

        return [genetic_hyp] + llm_hyps + mashups
