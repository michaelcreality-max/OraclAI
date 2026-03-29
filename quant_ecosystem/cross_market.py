"""
Cross-market intelligence: joint pulls for equities, crypto, commodities, FX proxies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf


DEFAULT_BUNDLE = {
    "SPY": "us_equities",
    "QQQ": "growth_tech",
    "GLD": "gold",
    "USO": "oil",
    "UUP": "usd",
    "BTC-USD": "crypto_btc",
}


def fetch_bundle(
    symbols: Optional[List[str]] = None,
    *,
    period: str = "1y",
) -> Dict[str, Any]:
    syms = symbols or list(DEFAULT_BUNDLE.keys())
    frames: Dict[str, pd.Series] = {}
    for s in syms:
        try:
            t = yf.Ticker(s)
            h = t.history(period=period, interval="1d", auto_adjust=True)
            if h is not None and len(h) > 20:
                frames[s] = h["Close"].rename(s)
        except Exception:
            continue
    if not frames:
        return {"ok": False, "error": "No cross-market data", "correlations": {}}

    df = pd.concat(frames.values(), axis=1).dropna()
    corr = df.pct_change().dropna().corr()

    macro_links = []
    if "USO" in df.columns and "SPY" in df.columns:
        try:
            c_os = float(corr.loc["USO", "SPY"])
        except Exception:
            c_os = None
        macro_links.append(
            {
                "hypothesis": "oil_up_airlines_down",
                "correlation_oil_spy": c_os,
                "note": "Oil shocks often pressure broad risk when energy costs spike (simplified).",
            }
        )
    if "UUP" in df.columns and "QQQ" in df.columns:
        try:
            c_uq = float(corr.loc["UUP", "QQQ"])
        except Exception:
            c_uq = None
        macro_links.append(
            {
                "hypothesis": "usd_up_growth_multiples_compress",
                "correlation_usd_qqq": c_uq,
            }
        )

    return {
        "ok": True,
        "symbols": list(frames.keys()),
        "correlation_matrix": corr.round(4).to_dict(),
        "macro_links": macro_links,
        "window": period,
    }
