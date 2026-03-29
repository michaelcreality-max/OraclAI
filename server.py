"""
Production HTTP API for stock predictions.
Merges live server-side market data with optional `client_context` from your Lovable frontend.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from prediction_engine import EliteDiscoveryEngine, ElitePortfolioAnalyzer, StockPredictionEngine
from realtime_market import get_market_store, start_market_poller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

API_VERSION = "1.0"


def _parse_origins() -> list:
    """CORS origins for browser clients (Lovable preview/live + local dev).

    Set ALLOWED_ORIGINS to a comma-separated list to override defaults entirely
    (include your Lovable preview URL or custom domain if needed).
    """
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://lovable.dev",
        "https://www.lovable.dev",
        # Lovable project previews (subdomains on lovable.app / lovable.dev)
        re.compile(r"^https://[\w.-]+\.lovable\.app$"),
        re.compile(r"^https://[\w.-]+\.lovable\.dev$"),
    ]


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, origins=_parse_origins(), supports_credentials=True)

    start_market_poller()

    predictor = StockPredictionEngine()
    discovery = EliteDiscoveryEngine()
    portfolio_analyzer = ElitePortfolioAnalyzer()

    def require_api_key() -> Optional[Tuple[Dict, int]]:
        key = os.environ.get("STOCK_API_KEY", "").strip()
        if not key:
            return None
        supplied = request.headers.get("X-API-Key", "") or request.args.get("api_key", "")
        if supplied != key:
            return {"success": False, "error": "Unauthorized"}, 401
        return None

    def ok(data: Dict[str, Any], status: int = 200):
        body = {"success": True, "api_version": API_VERSION, "timestamp": datetime.utcnow().isoformat() + "Z"}
        body.update(data)
        return jsonify(body), status

    def err(message: str, status: int = 400):
        return jsonify(
            {
                "success": False,
                "api_version": API_VERSION,
                "error": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        ), status

    def _coerce_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off", ""}:
                return False
        return default

    def _parse_local_intelligence_request() -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[str, int]]]:
        if request.method == "POST":
            if request.data and not request.is_json:
                return None, ("JSON body required", 400)
            body: Dict[str, Any] = request.get_json(silent=True) or {}
        else:
            body = request.args.to_dict(flat=True)

        raw_symbols = body.get("symbols")
        if raw_symbols is None and body.get("symbol") is not None:
            raw_symbols = [body.get("symbol")]

        symbols = None
        if isinstance(raw_symbols, str):
            symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
        elif isinstance(raw_symbols, list):
            cleaned = []
            for item in raw_symbols:
                if not isinstance(item, str):
                    return None, ("symbols must contain strings only", 400)
                symbol = item.strip().upper()
                if symbol:
                    cleaned.append(symbol)
            symbols = cleaned or None
        elif raw_symbols is not None:
            return None, ("symbols must be a list of strings or comma-separated string", 400)

        try:
            days = int(body.get("days", 252))
        except (TypeError, ValueError):
            return None, ("days must be an integer", 400)
        try:
            seed = int(body.get("seed", 42))
        except (TypeError, ValueError):
            return None, ("seed must be an integer", 400)
        try:
            max_points = int(body.get("max_points", 90))
        except (TypeError, ValueError):
            return None, ("max_points must be an integer", 400)

        return (
            {
                "symbols": symbols,
                "days": max(90, min(days, 900)),
                "seed": seed,
                "include_history": _coerce_bool(body.get("include_history"), True),
                "max_points": max(20, min(max_points, max(20, min(days, 900)))),
            },
            None,
        )

    @app.route("/health")
    def health():
        return ok({"status": "healthy", "service": "stock-prediction-api"})

    @app.route("/api/v1/quote", methods=["GET"])
    def quote():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        symbol = request.args.get("symbol")
        if not symbol:
            return err("symbol query parameter required", 400)
        q = get_market_store().ensure_fresh(symbol.strip())
        return ok({"quote": q})

    @app.route("/api/v1/intel/stock", methods=["GET"])
    def stock_intel():
        """Observer-only: detailed quote, fundamentals, and recent history (no debate / allocation)."""
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        symbol = request.args.get("symbol")
        if not symbol or not isinstance(symbol, str):
            return err("symbol query parameter required", 400)
        period = request.args.get("history_period", "3mo")
        if not isinstance(period, str):
            period = "3mo"
        try:
            from quant_ecosystem.stock_intel_agent import StockIntelAgent
        except ImportError as e:
            return err(f"Stock intel unavailable: {e}", 500)
        live = get_market_store().ensure_fresh(symbol.strip())
        agent = StockIntelAgent()
        snap = agent.gather(symbol.strip(), history_period=period, live_quote=live)
        return ok({"stock_intel": StockIntelAgent.to_dict(snap)})

    @app.route("/api/v1/status", methods=["GET"])
    def status():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        return ok(
            {
                "status": "operational",
                "engine": "StockPredictionEngine",
                "description": "Live yfinance signals merged with optional client_context",
                "market_data": get_market_store().status(),
                "intelligence_api": {
                    "analyze": "POST /api/v1/intelligence/analyze",
                    "stock_intel": "GET /api/v1/intel/stock?symbol=…",
                    "local_market": "GET|POST /api/v1/intelligence/local/market",
                    "local_intelligence": "GET|POST /api/v1/intelligence/local",
                    "transparency": "GET /api/v1/intelligence/transparency",
                    "stress": "POST /api/v1/intelligence/stress",
                },
            }
        )

    @app.route("/api/v1/predict", methods=["POST"])
    def predict():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        if not request.is_json:
            return err("JSON body required", 400)
        body = request.get_json(silent=True) or {}
        symbol = body.get("symbol")
        if not symbol or not isinstance(symbol, str):
            return err("symbol is required (string)", 400)
        client_context = body.get("client_context")
        if client_context is not None and not isinstance(client_context, dict):
            return err("client_context must be an object", 400)
        days = body.get("days", 90)
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 90
        result = predictor.predict_stock(symbol.strip(), days=days, client_context=client_context)
        return ok({"prediction": result})

    @app.route("/api/v1/discover", methods=["POST"])
    def discover():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        body = request.get_json(silent=True) or {}
        try:
            min_conf = float(body.get("min_confidence", 0.5))
        except (TypeError, ValueError):
            min_conf = 0.5
        sector = body.get("sector")
        if sector is not None and not isinstance(sector, str):
            return err("sector must be a string", 400)
        try:
            limit = int(body.get("limit", 25))
        except (TypeError, ValueError):
            limit = 25
        limit = max(1, min(limit, 100))
        rows = discovery.discover_elite_stocks(min_confidence=min_conf, sector=sector, limit=limit)
        return ok({"discover": rows})

    @app.route("/api/v1/intelligence/analyze", methods=["POST"])
    def intelligence_analyze():
        """Full elite pipeline: ecosystem + regimes + debate + causal + cross-market + patterns + transparency."""
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        if not request.is_json:
            return err("JSON body required", 400)
        body = request.get_json(silent=True) or {}
        symbol = body.get("symbol")
        if not symbol or not isinstance(symbol, str):
            return err("symbol is required (string)", 400)
        user_profile = body.get("user_profile")
        if user_profile is not None and not isinstance(user_profile, dict):
            return err("user_profile must be an object", 400)
        what_if = body.get("what_if")
        if what_if is not None and not isinstance(what_if, dict):
            return err("what_if must be an object (shock name -> magnitude)", 400)
        period = body.get("period", "2y")
        if not isinstance(period, str):
            period = "2y"
        include_cross = body.get("include_cross_market", True)
        if not isinstance(include_cross, bool):
            include_cross = bool(include_cross)
        include_stock_intel = body.get("include_stock_intel", False)
        if not isinstance(include_stock_intel, bool):
            include_stock_intel = bool(include_stock_intel)
        try:
            max_hyp = int(body.get("max_hypotheses", 4))
        except (TypeError, ValueError):
            max_hyp = 4
        try:
            top_models = int(body.get("top_models", 2))
        except (TypeError, ValueError):
            top_models = 2
        max_hyp = max(1, min(max_hyp, 12))
        top_models = max(1, min(top_models, 8))

        try:
            from quant_ecosystem.elite_intelligence import run_full_intelligence
        except ImportError as e:
            return err(f"Intelligence module unavailable: {e}", 500)

        shocks = None
        if what_if:
            shocks = {}
            for k, v in what_if.items():
                try:
                    shocks[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue

        out = run_full_intelligence(
            symbol.strip(),
            period=period,
            user_profile=user_profile,
            what_if=shocks,
            include_cross_market=include_cross,
            include_stock_intel=include_stock_intel,
            max_hypotheses=max_hyp,
            top_models=top_models,
        )
        if not out.get("ok"):
            return err(out.get("error", "intelligence failed"), 400)
        return ok({"intelligence": out})

    @app.route("/api/v1/intelligence/local/market", methods=["GET", "POST"])
    def local_market():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        params, parse_error = _parse_local_intelligence_request()
        if parse_error:
            return err(parse_error[0], parse_error[1])
        try:
            from quant_ecosystem.local_intelligence import LocalResearchEngine
        except ImportError as e:
            return err(f"Local intelligence unavailable: {e}", 500)

        engine = LocalResearchEngine(seed=int(params["seed"]))
        out = engine.generate_market(
            symbols=params["symbols"],
            days=int(params["days"]),
            include_history=bool(params["include_history"]),
            max_points=int(params["max_points"]),
        )
        return ok({"local_market": out})

    @app.route("/api/v1/intelligence/local", methods=["GET", "POST"])
    def local_intelligence():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        params, parse_error = _parse_local_intelligence_request()
        if parse_error:
            return err(parse_error[0], parse_error[1])
        try:
            from quant_ecosystem.local_intelligence import LocalResearchEngine
        except ImportError as e:
            return err(f"Local intelligence unavailable: {e}", 500)

        engine = LocalResearchEngine(seed=int(params["seed"]))
        out = engine.analyze_market(
            symbols=params["symbols"],
            days=int(params["days"]),
            include_history=bool(params["include_history"]),
            max_points=int(params["max_points"]),
        )
        return ok({"local_intelligence": out})

    @app.route("/api/v1/intelligence/transparency", methods=["GET"])
    def intelligence_transparency():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        symbol = request.args.get("symbol")
        try:
            limit = int(request.args.get("limit", "40"))
        except ValueError:
            limit = 40
        limit = max(1, min(limit, 200))
        try:
            from quant_ecosystem.transparency import get_ledger
        except ImportError as e:
            return err(f"Transparency unavailable: {e}", 500)
        ledger = get_ledger()
        sym = symbol.strip() if isinstance(symbol, str) and symbol.strip() else None
        ev = ledger.recent(symbol=sym, limit=limit)
        return ok({"transparency_events": ev})

    @app.route("/api/v1/intelligence/stress", methods=["POST"])
    def intelligence_stress():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        body = request.get_json(silent=True) or {}
        try:
            n_days = int(body.get("n_days", 400))
        except (TypeError, ValueError):
            n_days = 400
        try:
            seed = int(body.get("seed", 42))
        except (TypeError, ValueError):
            seed = 42
        from quant_ecosystem.market_simulator import SimConfig, stress_suite

        cfg = SimConfig(n_days=max(120, min(n_days, 5000)), seed=seed)
        return ok({"stress_tests": stress_suite(cfg)})

    @app.route("/api/v1/portfolio", methods=["POST"])
    def portfolio():
        auth = require_api_key()
        if auth:
            return err(auth[0]["error"], auth[1])
        if not request.is_json:
            return err("JSON body required", 400)
        body = request.get_json(silent=True) or {}
        holdings = body.get("holdings")
        if not isinstance(holdings, dict):
            return err("holdings must be an object mapping symbol -> quantity", 400)
        client_context = body.get("client_context")
        if client_context is not None and not isinstance(client_context, dict):
            return err("client_context must be an object", 400)
        out = {}
        for sym, qty in holdings.items():
            if not isinstance(sym, str):
                continue
            pred = predictor.predict_stock(sym.strip(), client_context=client_context)
            out[sym.upper().strip()] = {"quantity": qty, "prediction": pred}
        return ok(
            {
                "portfolio": out,
                "meta": {"positions": len(out)},
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    log.info("Starting server on 0.0.0.0:%s", port)
    app.run(host="0.0.0.0", port=port, threaded=True)
