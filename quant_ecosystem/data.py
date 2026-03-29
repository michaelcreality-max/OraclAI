"""Market data loading for research/backtests (yfinance)."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf


def load_ohlcv(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
    *,
    reference_symbol: Optional[str] = "SPY",
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Load OHLCV for `symbol` and optional reference (e.g. SPY for cross-asset).
    Returns (df, ref_close) where df has columns open, high, low, close, volume.
    """
    sym = symbol.strip().upper()
    t = yf.Ticker(sym)
    df = t.history(period=period, interval=interval, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"No data for {sym!r}")

    df = df.rename(columns=str.lower)
    need = {"open", "high", "low", "close", "volume"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for {sym}: {missing}")

    ref = None
    if reference_symbol:
        r = yf.Ticker(reference_symbol.strip().upper())
        rdf = r.history(period=period, interval=interval, auto_adjust=True)
        if rdf is not None and not rdf.empty:
            rdf = rdf.rename(columns=str.lower)
            ref = rdf["close"].reindex(df.index).ffill()

    return df[list(need)], ref
