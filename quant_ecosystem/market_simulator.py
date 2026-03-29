"""
Synthetic market paths for stress training: crashes, bubbles, sideways chop, fat tails.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class Scenario(str, Enum):
    RANDOM_WALK = "random_walk"
    CRASH_2008_STYLE = "crash_2008_style"
    BUBBLE_RALLY = "bubble_rally"
    SIDEWAYS_CHOP = "sideways_chop"
    FLASH_CRASH = "flash_crash"
    FAT_TAIL = "fat_tail"


@dataclass
class SimConfig:
    n_days: int = 500
    seed: int = 42
    initial_price: float = 100.0


def _ohlcv_from_close(close: np.ndarray, volume_base: float = 1e6) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    noise = rng.uniform(0.001, 0.015, size=len(close))
    high = close * (1.0 + noise)
    low = close * (1.0 - noise)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    vol = rng.lognormal(np.log(volume_base), 0.35, size=len(close))
    idx = pd.date_range("2015-01-01", periods=len(close), freq="B")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=idx,
    )


def simulate_path(scenario: Scenario, cfg: Optional[SimConfig] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    cfg = cfg or SimConfig()
    rng = np.random.default_rng(cfg.seed)
    n = cfg.n_days
    meta: Dict[str, Any] = {"scenario": scenario.value, "n": n}

    if scenario == Scenario.RANDOM_WALK:
        r = rng.normal(0.0002, 0.012, size=n)
    elif scenario == Scenario.CRASH_2008_STYLE:
        r = rng.normal(0.0001, 0.01, size=n)
        shock_idx = int(n * 0.45)
        r[shock_idx : shock_idx + 15] -= 0.025
        meta["shock_start"] = shock_idx
    elif scenario == Scenario.BUBBLE_RALLY:
        r = rng.normal(0.0015, 0.009, size=n)
        r[int(n * 0.2) : int(n * 0.65)] += 0.0012
    elif scenario == Scenario.SIDEWAYS_CHOP:
        r = rng.normal(0.0, 0.008, size=n)
    elif scenario == Scenario.FLASH_CRASH:
        r = rng.normal(0.0002, 0.01, size=n)
        j = int(n * 0.55)
        r[j : j + 3] -= 0.08
        meta["flash_day"] = j
    else:  # FAT_TAIL
        r = rng.standard_t(df=4, size=n) * 0.012

    close = cfg.initial_price * np.exp(np.cumsum(r))
    ohlcv = _ohlcv_from_close(close.astype(float))
    return ohlcv, meta


def stress_suite(cfg: Optional[SimConfig] = None) -> Dict[str, Any]:
    """Run multiple scenarios for stress-test reporting."""
    out: Dict[str, Any] = {"scenarios": []}
    for sc in Scenario:
        ohlcv, meta = simulate_path(sc, cfg)
        rets = np.log(ohlcv["close"] / ohlcv["close"].shift(1)).dropna()
        out["scenarios"].append(
            {
                "name": sc.value,
                "meta": meta,
                "final_price": float(ohlcv["close"].iloc[-1]),
                "max_dd_approx": float((ohlcv["close"] / ohlcv["close"].cummax() - 1.0).min()),
                "vol_ann": float(rets.std() * np.sqrt(252.0)),
            }
        )
    return out
