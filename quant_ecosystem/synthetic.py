"""Synthetic OHLCV for offline tests without market data."""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_synthetic_ohlcv(
    n: int = 600,
    *,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Geometric random walk close with derived OHLC; returns (ohlcv, spy_proxy_close).
    """
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0003, 0.015, size=n)
    close = 100.0 * np.exp(np.cumsum(r))
    noise = rng.uniform(0.002, 0.01, size=n)
    high = close * (1.0 + noise)
    low = close * (1.0 - noise)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    vol = rng.lognormal(15, 0.5, size=n)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    ohlcv = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": vol,
        },
        index=idx,
    )
    spy = pd.Series(400.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.008, size=n))), index=idx)
    return ohlcv, spy
