"""
Stock Intel Agent — observer-only data gatherer.

Pulls near–real-time quotes and detailed fundamentals/history from yfinance.
Does not participate in debate, meta-allocation, or ecosystem tournaments; it only
reports facts so other agents and humans can reason on top of the same numbers.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd
import yfinance as yf

from .schemas import StockIntelSnapshot

log = logging.getLogger(__name__)

# Curated from ticker.info — keeps payloads small and JSON-safe.
_INFO_KEYS: Sequence[str] = (
    "longName",
    "shortName",
    "symbol",
    "sector",
    "industry",
    "exchange",
    "quoteType",
    "currency",
    "marketCap",
    "enterpriseValue",
    "enterpriseToRevenue",
    "enterpriseToEbitda",
    "trailingPE",
    "forwardPE",
    "pegRatio",
    "priceToBook",
    "priceToSalesTrailing12Months",
    "dividendYield",
    "dividendRate",
    "payoutRatio",
    "beta",
    "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow",
    "fiftyDayAverage",
    "twoHundredDayAverage",
    "averageVolume",
    "averageVolume10days",
    "sharesOutstanding",
    "floatShares",
    "shortPercentOfFloat",
    "heldPercentInsiders",
    "heldPercentInstitutions",
    "currentPrice",
    "regularMarketPrice",
    "previousClose",
    "open",
    "dayHigh",
    "dayLow",
    "volume",
    "bid",
    "ask",
    "bidSize",
    "askSize",
    "earningsQuarterlyGrowth",
    "revenueGrowth",
    "earningsGrowth",
    "returnOnEquity",
    "returnOnAssets",
    "debtToEquity",
    "currentRatio",
    "quickRatio",
    "grossMargins",
    "operatingMargins",
    "profitMargins",
    "fullTimeEmployees",
    "website",
)


def _num(x: Any) -> Any:
    if x is None:
        return None
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _sanitize(obj: Any) -> Any:
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (int, float)):
        return _num(obj)
    if isinstance(obj, datetime):
        return obj.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return str(obj)


def _fast_info_dict(ticker: yf.Ticker) -> Dict[str, Any]:
    try:
        fi = ticker.fast_info
        if hasattr(fi, "items"):
            raw = dict(fi.items())
        else:
            raw = dict(fi) if isinstance(fi, dict) else {}
    except Exception as e:
        log.debug("fast_info: %s", e)
        raw = {}
    return _sanitize(raw)


def _pick_info(info: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in _INFO_KEYS:
        if k in info and info[k] is not None:
            out[k] = _sanitize(info[k])
    return out


def _history_summary(hist: pd.DataFrame) -> Dict[str, Any]:
    if hist is None or hist.empty:
        return {"error": "no_history"}
    h = hist.rename(columns=str.lower)
    if "close" not in h.columns:
        return {"error": "no_close_column"}
    c = h["close"].astype(float)
    ret = c.pct_change()
    last = float(c.iloc[-1])
    out: Dict[str, Any] = {
        "bars": int(len(h)),
        "first_date": str(h.index[0]),
        "last_date": str(h.index[-1]),
        "last_close": last,
        "high_period": float(c.max()),
        "low_period": float(c.min()),
        "return_total": float(c.iloc[-1] / c.iloc[0] - 1.0) if len(c) > 1 else 0.0,
        "vol_daily": float(ret.std()) if len(ret) > 2 else None,
        "vol_ann_hint": float(ret.std() * (252.0**0.5)) if len(ret) > 2 else None,
    }
    if len(ret) > 5:
        out["return_5d"] = _num(float(ret.iloc[-5:].sum()))
    if len(c) > 20:
        sma20 = float(c.rolling(20).mean().iloc[-1])
        out["vs_sma20_pct"] = _num((last - sma20) / sma20) if sma20 else None
    return out


class StockIntelAgent:
    """
    Gathers structured stock data only. Does not score strategies, argue, or allocate.
    """

    def gather(
        self,
        symbol: str,
        *,
        history_period: str = "3mo",
        history_interval: str = "1d",
        live_quote: Optional[Dict[str, Any]] = None,
    ) -> StockIntelSnapshot:
        sym = str(symbol).upper().strip()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ticker = yf.Ticker(sym)

        fast_metrics = _fast_info_dict(ticker)

        fundamentals: Dict[str, Any] = {}
        try:
            info = ticker.info
            if isinstance(info, dict) and info:
                fundamentals = _pick_info(info)
        except Exception as e:
            log.warning("ticker.info failed for %s: %s", sym, e)
            fundamentals = {"error": str(e)}

        recent_history: Dict[str, Any] = {}
        try:
            hist = ticker.history(period=history_period, interval=history_interval, auto_adjust=True)
            recent_history = _history_summary(hist)
        except Exception as e:
            recent_history = {"error": str(e)}

        sources = ["yfinance"]
        if live_quote:
            sources.append("server_live_cache")

        snap = StockIntelSnapshot(
            symbol=sym,
            role="observer",
            mandate="Collect and normalize factual market data; do not debate or vote on strategies.",
            fetched_at_utc=now,
            data_sources=sources,
            fast_metrics=fast_metrics,
            fundamentals=fundamentals,
            recent_history=recent_history,
            live_quote=_sanitize(live_quote) if live_quote else None,
            disclaimer=(
                "Data is delayed or aggregated per vendor rules; not investment advice. "
                "This agent does not participate in strategy debate or allocation."
            ),
        )
        return snap

    @staticmethod
    def to_dict(snapshot: StockIntelSnapshot) -> Dict[str, Any]:
        from dataclasses import asdict

        return asdict(snapshot)
