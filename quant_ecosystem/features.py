"""Feature builders: technical, sentiment placeholders, cross-asset."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def build_feature_matrix(
    ohlcv: pd.DataFrame,
    ref_close: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """
    Build a wide matrix of base features. Columns are used by genetic search
    and model training. Sentiment_* columns are placeholders (zeros) for
    wiring in external NLP feeds later.
    """
    df = ohlcv.copy()
    c = df["close"]
    h = df["high"]
    l = df["low"]
    v = df["volume"].replace(0, np.nan)

    out = pd.DataFrame(index=df.index)
    out["ret_1"] = c.pct_change()
    out["ret_5"] = c.pct_change(5)
    out["ret_20"] = c.pct_change(20)
    out["vol_20"] = out["ret_1"].rolling(20).std()
    out["hl_range"] = (h - l) / c.replace(0, np.nan)
    out["rsi_14"] = _rsi(c, 14)
    out["mom_10"] = c / c.shift(10) - 1.0
    out["vol_z"] = (v - v.rolling(20).mean()) / (v.rolling(20).std() + 1e-9)

    if ref_close is not None:
        ref = ref_close.reindex(df.index).ffill()
        out["beta_proxy"] = out["ret_1"].rolling(20).corr(ref.pct_change())
        out["rel_strength"] = c.pct_change(20) - ref.pct_change(20)
    else:
        out["beta_proxy"] = 0.0
        out["rel_strength"] = 0.0

    # Placeholders for sentiment / alt data (replace with real series in production)
    out["sentiment_news"] = 0.0
    out["sentiment_social"] = 0.0
    out["sentiment_options"] = 0.0

    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    return out


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = avg_gain / (avg_loss + 1e-12)
    return 100.0 - (100.0 / (1.0 + rs))


def apply_feature_mask(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Subset and order columns; raises if unknown column."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Unknown feature columns: {missing}")
    return df[columns].copy()


def make_target_forward_return(
    close: pd.Series,
    horizon: int = 1,
) -> pd.Series:
    """Next-day (or h-day) log return aligned to same index (drop last NaN in training)."""
    return np.log(close.shift(-horizon) / close).rename("target")
