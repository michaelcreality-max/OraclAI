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
    Optional LLM hypotheses. Uses OPENAI_API_KEY + OPENAI_MODEL or HTTP
    Ollama-style endpoint via LLM_HTTP_URL (POST JSON).
    If unavailable, emits template-based unconventional ideas.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def _templates(self, symbols_context: str) -> List[Dict[str, Any]]:
        weird = [
            "Rank stocks by (momentum * inverse volatility) on rolling fear spikes from VIX proxy.",
            "Use ratio of 5d return to 20d realized vol as a 'risk-adjusted thrust' signal.",
            "Cross-asset: fade relative strength vs SPY when beta_proxy > 1.2 and RSI overbought.",
            "Sentiment placeholder spike: combine sentiment_social with vol_z only on high volume days.",
            "Unconventional: sign(ret_1) * sign(rel_strength) * (1 - hl_range) as a contrarian chop filter.",
        ]
        pick = self._rng.sample(weird, k=min(3, len(weird)))
        out = []
        for p in pick:
            out.append(
                {
                    "description": p + f" Context: {symbols_context}.",
                    "feature_hints": ["ret_5", "vol_20", "rsi_14", "rel_strength", "vol_z"],
                    "unconventional": True,
                }
            )
        return out

    def _openai(self, prompt: str) -> Optional[str]:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            return None
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
            }
        ).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode())
        return raw["choices"][0]["message"]["content"]

    def _http_llm(self, prompt: str) -> Optional[str]:
        url = os.environ.get("LLM_HTTP_URL", "").strip()
        if not url:
            return None
        body = json.dumps({"prompt": prompt}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read().decode(errors="replace")

    def generate_raw_ideas(self, context: str) -> List[Dict[str, Any]]:
        prompt = (
            "You are a creative quant researcher. Propose 3 unconventional alpha ideas "
            "using technical, sentiment placeholders, and cross-asset features. "
            "Return JSON array of objects with keys: description, feature_hints (list of strings), "
            "unconventional (bool). Be creative, not conservative.\n\n"
            f"Context: {context}"
        )
        text = None
        try:
            text = self._openai(prompt)
        except Exception:
            text = None
        if text is None:
            try:
                text = self._http_llm(prompt)
            except Exception:
                text = None
        if text:
            try:
                start = text.find("[")
                end = text.rfind("]") + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except Exception:
                pass
        return self._templates(context)

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
