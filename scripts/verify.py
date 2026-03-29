#!/usr/bin/env python3
"""Project verification: imports + Flask smoke tests (no network by default)."""

from __future__ import annotations

import argparse
import os
import sys


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _prep_env(root: str) -> None:
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    # Skip background yfinance polling so checks stay fast and deterministic.
    os.environ.setdefault("DISABLE_MARKET_POLLER", "1")


def run_checks(include_network: bool) -> int:
    root = _project_root()
    _prep_env(root)

    print("[verify] project root:", root)
    print("[verify] importing prediction_engine + server …")
    import prediction_engine  # noqa: F401
    import werkzeug
    from server import app

    if not hasattr(werkzeug, "__version__"):
        werkzeug.__version__ = "3"

    client = app.test_client()

    def req(method: str, path: str, **kwargs):
        fn = getattr(client, method.lower())
        return fn(path, **kwargs)

    checks = []

    r = req("GET", "/health")
    checks.append(("GET /health == 200", r.status_code == 200))

    r = req("GET", "/api/v1/status")
    checks.append(("GET /api/v1/status == 200 (no API key)", r.status_code == 200))

    r = req(
        "POST",
        "/api/v1/predict",
        data="not-json",
        content_type="text/plain",
    )
    checks.append(("POST /api/v1/predict non-JSON == 400", r.status_code == 400))

    r = req("POST", "/api/v1/predict", json={})
    checks.append(("POST /api/v1/predict missing symbol == 400", r.status_code == 400))

    r = req("POST", "/api/v1/portfolio", data="x", content_type="text/plain")
    checks.append(("POST /api/v1/portfolio non-JSON == 400", r.status_code == 400))

    r = req("POST", "/api/v1/portfolio", json={})
    checks.append(("POST /api/v1/portfolio missing holdings == 400", r.status_code == 400))

    r = req("GET", "/api/v1/intelligence/local")
    ok_local = r.status_code == 200
    if ok_local:
        payload = r.get_json(silent=True) or {}
        local_intel = payload.get("local_intelligence", {}) if payload.get("success") else {}
        ok_local = (
            bool(payload.get("success"))
            and isinstance(local_intel, dict)
            and isinstance(local_intel.get("stocks"), dict)
            and bool(local_intel.get("overview"))
        )
    checks.append(("GET /api/v1/intelligence/local == 200 + payload", ok_local))

    r = req(
        "POST",
        "/api/v1/intelligence/local/market",
        json={"symbols": ["AAPL", "NVDA"], "days": 180, "include_history": False, "seed": 7},
    )
    ok_local_market = r.status_code == 200
    if ok_local_market:
        payload = r.get_json(silent=True) or {}
        market = payload.get("local_market", {}) if payload.get("success") else {}
        ok_local_market = (
            bool(payload.get("success"))
            and market.get("mode") == "offline_only"
            and sorted((market.get("stocks") or {}).keys()) == ["AAPL", "NVDA"]
        )
    checks.append(("POST /api/v1/intelligence/local/market == 200 + 2 symbols", ok_local_market))

    if include_network:
        print("[verify] network: POST /api/v1/predict {\"symbol\":\"AAPL\"} …")
        r = req("POST", "/api/v1/predict", json={"symbol": "AAPL", "days": 90})
        ok_pred = r.status_code == 200
        if r.status_code == 200:
            data = r.get_json(silent=True) or {}
            ok_pred = bool(data.get("success")) and "prediction" in (data or {})
        checks.append(("POST /api/v1/predict AAPL == 200 + prediction", ok_pred))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"[verify] {'PASS' if ok else 'FAIL'} — {name}")

    if failed:
        print("[verify] FAILED:", len(failed), "check(s)")
        return 1
    print("[verify] all checks passed")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Run project verification checks.")
    p.add_argument(
        "--network",
        action="store_true",
        help="Also call yfinance via POST /api/v1/predict (needs internet).",
    )
    args = p.parse_args()
    try:
        return run_checks(include_network=args.network)
    except Exception as e:
        print("[verify] ERROR:", e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
