"""
Elite intelligence facade — wires evolution, regimes, debate, causal, microstructure,
cross-market, pattern radar, transparency, allocation, and world context into one response.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .allocation import allocate_capital
from .causal_engine import default_macro_graph, event_impact_narrative, what_if_scenario
from .cross_market import fetch_bundle
from .data import load_ohlcv
from .debate import DebateCouncil
from .evolution import KillSwitchRegistry, apply_invented_indicators, mutate_feature_set
from .features import build_feature_matrix, make_target_forward_return
from .market_simulator import stress_suite, SimConfig
from .microstructure import analyze_microstructure
from .orchestrator import QuantEcosystemOrchestrator
from .pattern_radar import detect_anomalies, hidden_correlations, precision_matrix_edges
from .personal_trader import adapt_signal, profile_from_dict
from .regime import detect_regime, regime_strategy_weights
from .schemas import RealityReport
from .transparency import get_ledger
from .world_context import world_context
def _prediction_stub_from_ecosystem(eco: Dict[str, Any]) -> Dict[str, Any]:
    reps = eco.get("reality_reports") or []
    if not reps:
        return {"direction": "neutral", "confidence": 0.45, "sharpe_proxy": 0.0}
    best = max(reps, key=lambda r: r.get("sharpe", -999))
    sharpe = float(best.get("sharpe", 0.0))
    passed = bool(best.get("passed"))
    direction = "bullish" if sharpe > 0.4 and passed else "bearish" if sharpe < 0 else "neutral"
    return {
        "direction": direction,
        "confidence": min(0.95, 0.5 + abs(sharpe) * 0.1),
        "sharpe_proxy": sharpe,
        "best_model": best.get("model_id"),
    }


def run_full_intelligence(
    symbol: str,
    *,
    period: str = "2y",
    user_profile: Optional[Dict[str, Any]] = None,
    what_if: Optional[Dict[str, float]] = None,
    include_cross_market: bool = True,
    include_stock_intel: bool = False,
    max_hypotheses: int = 4,
    top_models: int = 2,
) -> Dict[str, Any]:
    """
    Single entrypoint for backend: one symbol, optional user profile and causal shocks.

    When ``include_stock_intel`` is True, attaches factual ``stock_intel`` from the
    observer-only Stock Intel agent (does not affect debate or allocation).
    """
    sym = symbol.upper().strip()
    ledger = get_ledger()
    orch = QuantEcosystemOrchestrator(arena_workers=4)

    try:
        ohlcv, ref = load_ohlcv(sym, period=period)
    except Exception as e:
        return {"ok": False, "error": str(e), "symbol": sym}

    feats = build_feature_matrix(ohlcv, ref)
    feats = apply_invented_indicators(feats)
    close = ohlcv["close"].reindex(feats.index).ffill()
    vol = ohlcv["volume"].reindex(feats.index).ffill()
    regime_snap = detect_regime(close, vol)
    regime_dict = {
        "trend": regime_snap.trend.value,
        "volatility": regime_snap.volatility.value,
        "driver": regime_snap.driver.value,
        "confidence": regime_snap.confidence,
        "metrics": regime_snap.metrics,
        "strategy_weights_by_regime": regime_strategy_weights(regime_snap),
    }

    patterns = {
        "anomaly": detect_anomalies(feats),
        "hidden_correlations": hidden_correlations(feats),
        "partial_corr_hints": precision_matrix_edges(feats),
    }

    eco = orch.run_cycle_from_ohlcv(
        ohlcv,
        reference_close=ref,
        symbol=sym,
        max_hypotheses=max_hypotheses,
        top_models=top_models,
    )

    kill = KillSwitchRegistry()
    killed: Dict[str, str] = {}

    for rdict in eco.get("reality_reports") or []:
        rep = RealityReport(
            hypothesis_id=str(rdict.get("hypothesis_id", "")),
            model_id=str(rdict.get("model_id", "")),
            sharpe=float(rdict.get("sharpe", 0.0)),
            max_drawdown=float(rdict.get("max_drawdown", 0.0)),
            turnover=float(rdict.get("turnover", 0.0)),
            net_pnl_after_costs=float(rdict.get("net_pnl_after_costs", 0.0)),
            train_val_gap=float(rdict.get("train_val_gap", 0.0)),
            regime_scores=rdict.get("regime_scores") or {},
            passed=bool(rdict.get("passed")),
            kill_reason=rdict.get("kill_reason"),
        )
        if kill.evaluate(rep.model_id, rep):
            killed[rep.model_id] = kill.kill_reasons.get(rep.model_id, "killed")

    pred_summary = _prediction_stub_from_ecosystem(eco)
    risk_metrics = {
        "max_drawdown_proxy": min([r.get("max_drawdown", 0) for r in eco.get("reality_reports") or []] or [0]),
        "sharpe_proxy": pred_summary.get("sharpe_proxy"),
    }

    quote = None
    try:
        from realtime_market import get_market_store

        quote = get_market_store().ensure_fresh(sym)
    except Exception:
        quote = None

    micro = analyze_microstructure(sym, quote=quote)

    debate = DebateCouncil().run(
        symbol=sym,
        prediction_summary=pred_summary,
        regime=regime_dict,
        risk_metrics=risk_metrics,
        microstructure=micro,
    )

    profile = profile_from_dict(user_profile)
    adapted = adapt_signal(pred_summary, profile, debate_action=debate["judge"]["action"])

    graph = default_macro_graph()
    causal = {
        "graph_preview": [{"cause": e.cause, "effect": e.effect, "strength": e.strength} for e in graph.edges[:12]],
        "fed_hike_impact": event_impact_narrative("fed_rate_hike", graph),
    }
    if what_if:
        causal["what_if"] = what_if_scenario(graph, what_if)

    cross = fetch_bundle(period="1y") if include_cross_market else {"ok": False, "skipped": True}

    wts = eco.get("meta", {}).get("weights") or {}
    if not wts:
        wts = eco.get("state", {}).get("strategy_weights") or {}
    alloc = allocate_capital(
        wts,
        risk_budget=float(profile.risk_tolerance),
        hedge_equity_beta=0.15 if regime_snap.volatility.value == "high_vol" else 0.0,
    )

    stress = stress_suite(SimConfig(n_days=400, seed=42))

    world = world_context(sym)

    evolution = {
        "feature_mutation_example": mutate_feature_set(
            list(feats.columns),
            list(feats.columns[:5]),
            seed=42,
        ),
        "population_note": "StrategyPopulation available for multi-generation evolution runs.",
        "killed_models": killed,
        "invented_indicator_columns": [c for c in feats.columns if c.startswith("inv_")],
    }

    ledger.log(
        kind="ecosystem_cycle",
        symbol=sym,
        detail={
            "cycle": eco.get("cycle"),
            "survivors": eco.get("state", {}).get("survivors"),
            "killed": list(killed.keys()),
        },
    )
    ledger.log(
        kind="debate_verdict",
        symbol=sym,
        detail=debate["judge"],
    )

    transparency = {
        "recent_events": ledger.recent(symbol=sym, limit=20),
        "confidence_decay": "Per-model decay available when model_id history is logged via TransparencyLedger.record_model_score",
    }

    out: Dict[str, Any] = {
        "ok": True,
        "symbol": sym,
        "ecosystem": eco,
        "regime": regime_dict,
        "patterns": patterns,
        "microstructure": micro,
        "debate": debate,
        "personal": adapted,
        "causal": causal,
        "cross_market": cross,
        "allocation": alloc,
        "stress_tests": stress,
        "world_context": world,
        "evolution": evolution,
        "transparency": transparency,
    }

    if include_stock_intel:
        from .stock_intel_agent import StockIntelAgent

        intel = StockIntelAgent()
        snap = intel.gather(sym, live_quote=quote)
        out["stock_intel"] = StockIntelAgent.to_dict(snap)

    return out
