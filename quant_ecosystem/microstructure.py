"""
Real-time microstructure proxies: order-flow pressure and liquidity stress from quotes + intraday path.
Full L2 order book is not available via yfinance; we approximate education-grade signals.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import yfinance as yf


def _safe_fetch_intraday(symbol: str) -> Optional[pd.DataFrame]:
    try:
        t = yf.Ticker(symbol)
        intra = t.history(period="5d", interval="5m", auto_adjust=True)
        if intra is None or len(intra) < 10:
            return None
        return intra.rename(columns=str.lower)
    except Exception:
        return None


def analyze_microstructure(
    symbol: str,
    *,
    quote: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Proxies:
    - imbalance: recent up-minutes vs down-minutes
    - flow_pressure: return × volume z-score
    - liquidity_gap: high-low range vs recent average (widening = stress)
    """
    sym = str(symbol).upper().strip()
    intra = _safe_fetch_intraday(sym)
    stress = 0.0
    imbalance = 0.0
    flow_pressure = 0.0
    liquidity_gap = 0.0

    if intra is not None and len(intra) > 5:
        c = intra["close"]
        r = np.log(c / c.shift(1)).fillna(0.0)
        up = (r > 0).astype(float)
        down = (r < 0).astype(float)
        imbalance = float((up.tail(30).sum() - down.tail(30).sum()) / max(30, 1))

        vol = intra["volume"].astype(float)
        vz = (vol - vol.rolling(30).mean()) / (vol.rolling(30).std() + 1e-9)
        flow_pressure = float((r.tail(30) * vz.tail(30)).mean())

        hl = (intra["high"] - intra["low"]) / c.replace(0, np.nan)
        liquidity_gap = float(hl.tail(20).mean() - hl.tail(120).mean())

        stress = min(1.0, max(0.0, 0.4 * abs(imbalance) + 0.3 * abs(flow_pressure) + 0.3 * abs(liquidity_gap)))

    last_spread_proxy = None
    if quote and quote.get("last_price") and quote.get("previous_close"):
        try:
            lp = float(quote["last_price"])
            pc = float(quote["previous_close"])
            last_spread_proxy = abs(lp - pc) / (pc + 1e-9)
        except (TypeError, ValueError):
            pass

    return {
        "symbol": sym,
        "order_book_available": False,
        "imbalance_proxy": round(imbalance, 4),
        "flow_pressure": round(flow_pressure, 6),
        "liquidity_gap_proxy": round(liquidity_gap, 6),
        "stress_score": round(stress, 4),
        "last_spread_proxy": round(last_spread_proxy, 6) if last_spread_proxy is not None else None,
        "notes": "Proxies from delayed intraday bars; not exchange-native L2.",
    }
