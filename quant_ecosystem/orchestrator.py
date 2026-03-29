"""
Orchestrator — wires Alpha → Arena → Reality → Meta into one self-improving loop.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

import pandas as pd

from .alpha_discovery import AlphaDiscoveryAgent
from .data import load_ohlcv
from .evolution import apply_invented_indicators
from .features import build_feature_matrix, make_target_forward_return
from .meta_learning import MetaLearningAgent, MetaDecision
from .model_arena import ModelArenaAgent
from .reality_check import RealityCheckAgent
from .schemas import BacktestConfig, EcosystemState


def _hyp_to_dict(x: Any) -> Dict[str, Any]:
    d = asdict(x)
    d["created_at"] = x.created_at.isoformat() + "Z"
    return d


class QuantEcosystemOrchestrator:
    def __init__(
        self,
        *,
        backtest: Optional[BacktestConfig] = None,
        arena_workers: int = 4,
    ):
        self.alpha = AlphaDiscoveryAgent()
        self.arena = ModelArenaAgent(max_workers=arena_workers)
        self.reality = RealityCheckAgent(config=backtest)
        self.meta = MetaLearningAgent()
        self.state = EcosystemState()

    def _execute_cycle(
        self,
        ohlcv: pd.DataFrame,
        reference_close: Optional[pd.Series],
        *,
        symbol: str,
        alpha_context: str,
        top_models: int,
        max_hypotheses: int,
    ) -> Dict[str, Any]:
        feats = build_feature_matrix(ohlcv, reference_close)
        feats = apply_invented_indicators(feats)
        close = ohlcv["close"].reindex(feats.index).ffill()
        target = make_target_forward_return(close, horizon=1)
        aligned = pd.concat([feats, target], axis=1).dropna()
        if len(aligned) < 120:
            return {
                "ok": False,
                "error": "Not enough rows after alignment (need ~120+).",
                "symbol": symbol,
                "cycle": self.state.cycle,
            }

        X = aligned[feats.columns]
        y = aligned["target"]

        hyps = self.alpha.discover(X, y, context=alpha_context)[:max_hypotheses]

        for h in hyps:
            self.state.hypotheses[h.id] = h

        reports = []
        arena_summaries: List[Dict[str, Any]] = []

        for h in hyps:
            cols = h.feature_names
            try:
                Xh = X[cols]
            except Exception:
                continue

            models = self.arena.train_all(Xh, y, n_splits=5)
            for m in models:
                self.state.models[m.id] = m

            winners, tourney = self.arena.tournament(models, Xh, y, top_k=top_models)

            for mc in winners:
                rep = self.reality.validate(
                    hypothesis_id=h.id,
                    model_id=mc.id,
                    model_family=mc.family,
                    artifact=mc.artifact,
                    features=X,
                    target=y,
                    close=close.reindex(X.index).ffill(),
                    feature_columns=cols,
                )
                reports.append(rep)

            arena_summaries.append(
                {
                    "hypothesis_id": h.id,
                    "models_trained": len(models),
                    "tournament_pairs": len(tourney),
                    "top_model_ids": [w.id for w in winners],
                }
            )

        decision: MetaDecision = self.meta.update_from_reports(self.state, reports)

        return {
            "ok": True,
            "symbol": symbol,
            "cycle": self.state.cycle,
            "hypotheses": [_hyp_to_dict(x) for x in hyps],
            "arena": arena_summaries,
            "reality_reports": [asdict(r) for r in reports],
            "meta": {
                "retrain_ids": decision.retrain_ids,
                "discard_ids": decision.discard_ids,
                "weights": decision.weight_updates,
                "notes": decision.notes,
            },
            "state": {
                "survivors": list(dict.fromkeys(self.state.survivors)),
                "strategy_weights": self.state.strategy_weights,
            },
        }

    def run_cycle(
        self,
        symbol: str,
        *,
        period: str = "2y",
        top_models: int = 3,
        max_hypotheses: int = 5,
    ) -> Dict[str, Any]:
        """
        One full ecosystem cycle on a single symbol (yfinance).
        Returns a JSON-serializable summary.
        """
        self.state.cycle += 1
        try:
            ohlcv, ref = load_ohlcv(symbol, period=period)
        except ValueError as e:
            return {
                "ok": False,
                "error": str(e),
                "symbol": symbol,
                "cycle": self.state.cycle,
            }
        return self._execute_cycle(
            ohlcv,
            ref,
            symbol=symbol.upper().strip(),
            alpha_context=f"symbol={symbol} period={period}",
            top_models=top_models,
            max_hypotheses=max_hypotheses,
        )

    def run_cycle_from_ohlcv(
        self,
        ohlcv: pd.DataFrame,
        *,
        symbol: str = "SYNTH",
        reference_close: Optional[pd.Series] = None,
        top_models: int = 3,
        max_hypotheses: int = 5,
    ) -> Dict[str, Any]:
        """
        Same as ``run_cycle`` but uses pre-loaded OHLCV (e.g. synthetic or DB)
        instead of yfinance. Columns must include open, high, low, close, volume.
        """
        self.state.cycle += 1
        return self._execute_cycle(
            ohlcv,
            reference_close,
            symbol=symbol,
            alpha_context=f"symbol={symbol} source=frames",
            top_models=top_models,
            max_hypotheses=max_hypotheses,
        )
