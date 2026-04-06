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
def _generate_real_prediction(eco: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate real prediction from ecosystem data using ensemble methods.
    Calculates direction, confidence, and risk metrics from actual model performance.
    """
    reps = eco.get("reality_reports") or []
    survivors = eco.get("state", {}).get("survivors", [])
    cycle = eco.get("cycle", 0)
    
    if not reps:
        return {
            "direction": "neutral",
            "confidence": 0.45,
            "sharpe_proxy": 0.0,
            "signal_strength": 0.0,
            "models_considered": 0,
            "models_agreeing": 0,
            "method": "default_no_data"
        }
    
    # Filter to passed models only
    passed_models = [r for r in reps if r.get("passed", False)]
    
    if not passed_models:
        # No models passed - return neutral with low confidence
        avg_sharpe = sum(r.get("sharpe", 0) for r in reps) / len(reps)
        return {
            "direction": "neutral",
            "confidence": 0.35,
            "sharpe_proxy": avg_sharpe,
            "signal_strength": 0.0,
            "models_considered": len(reps),
            "models_agreeing": 0,
            "method": "ensemble_no_passing_models",
            "reason": "All models failed validation"
        }
    
    # Calculate ensemble statistics
    sharpes = [r.get("sharpe", 0.0) for r in passed_models]
    pnls = [r.get("net_pnl_after_costs", 0.0) for r in passed_models]
    drawdowns = [r.get("max_drawdown", 0.0) for r in passed_models]
    
    # Weight by Sharpe ratio (higher Sharpe = more weight)
    total_sharpe = sum(max(0, s) for s in sharpes) or 1.0
    weights = [max(0, s) / total_sharpe for s in sharpes]
    
    # Weighted average metrics
    weighted_sharpe = sum(s * w for s, w in zip(sharpes, weights))
    weighted_pnl = sum(p * w for p, w in zip(pnls, weights))
    avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else 0
    
    # Determine direction based on weighted PnL and Sharpe
    if weighted_sharpe > 0.5 and weighted_pnl > 0:
        direction = "bullish"
        signal_strength = min(1.0, weighted_sharpe * 0.5 + abs(weighted_pnl) * 0.001)
    elif weighted_sharpe < -0.2 or weighted_pnl < -0.05:
        direction = "bearish"
        signal_strength = min(1.0, abs(weighted_sharpe) * 0.5 + abs(weighted_pnl) * 0.001)
    else:
        direction = "neutral"
        signal_strength = abs(weighted_sharpe) * 0.3
    
    # Calculate confidence based on model agreement
    bullish_count = sum(1 for r in passed_models if r.get("sharpe", 0) > 0.3)
    bearish_count = sum(1 for r in passed_models if r.get("sharpe", 0) < -0.1)
    total_passed = len(passed_models)
    
    if direction == "bullish":
        agreement_ratio = bullish_count / total_passed if total_passed > 0 else 0
    elif direction == "bearish":
        agreement_ratio = bearish_count / total_passed if total_passed > 0 else 0
    else:
        neutral_count = total_passed - bullish_count - bearish_count
        agreement_ratio = neutral_count / total_passed if total_passed > 0 else 0
    
    # Confidence calculation considers both signal strength and model agreement
    base_confidence = 0.4 + (signal_strength * 0.4) + (agreement_ratio * 0.2)
    confidence = min(0.95, max(0.3, base_confidence))
    
    # Select best model for reference
    best_model = max(passed_models, key=lambda r: r.get("sharpe", -999))
    
    return {
        "direction": direction,
        "confidence": round(confidence, 4),
        "sharpe_proxy": round(weighted_sharpe, 4),
        "signal_strength": round(signal_strength, 4),
        "weighted_pnl": round(weighted_pnl, 4),
        "avg_drawdown": round(avg_drawdown, 4),
        "models_considered": len(reps),
        "models_passed": len(passed_models),
        "models_agreeing": int(agreement_ratio * total_passed),
        "agreement_ratio": round(agreement_ratio, 4),
        "cycle": cycle,
        "method": "weighted_ensemble",
        "best_model": {
            "model_id": best_model.get("model_id"),
            "sharpe": best_model.get("sharpe"),
            "hypothesis_id": best_model.get("hypothesis_id")
        }
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

    pred_summary = _generate_real_prediction(eco)
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
