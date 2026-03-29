"""
Market regime awareness: trend, volatility, and proxy for news-driven vs technical-driven conditions.
Used to switch model emphasis and reweight strategies in real time.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class TrendRegime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"


class VolRegime(str, Enum):
    HIGH = "high_vol"
    LOW = "low_vol"
    NORMAL = "normal"


class DriverRegime(str, Enum):
    TECHNICAL = "technical_driven"
    NEWS = "news_driven"  # proxy: volume/vol spike without matching price trend
    MIXED = "mixed"


@dataclass
class RegimeSnapshot:
    trend: TrendRegime
    volatility: VolRegime
    driver: DriverRegime
    confidence: float
    metrics: Dict[str, float]


def detect_regime(
    close: pd.Series,
    volume: Optional[pd.Series] = None,
    *,
    lookback: int = 60,
) -> RegimeSnapshot:
    """Classify recent window using return drift, realized vol, and volume shock vs return."""
    c = close.dropna().iloc[-lookback:]
    if len(c) < 20:
        return RegimeSnapshot(
            trend=TrendRegime.SIDEWAYS,
            volatility=VolRegime.NORMAL,
            driver=DriverRegime.MIXED,
            confidence=0.2,
            metrics={},
        )
    r = np.log(c / c.shift(1)).dropna()
    mu = float(r.mean())
    vol = float(r.std() + 1e-12)
    z = mu / vol * np.sqrt(252.0)

    if z > 0.35:
        trend = TrendRegime.BULL
    elif z < -0.35:
        trend = TrendRegime.BEAR
    else:
        trend = TrendRegime.SIDEWAYS

    v_hist = r.rolling(20).std().dropna()
    if len(v_hist) < 5:
        vol_r = VolRegime.NORMAL
    else:
        vq = v_hist.iloc[-1]
        q25, q75 = v_hist.quantile(0.25), v_hist.quantile(0.75)
        if vq > q75:
            vol_r = VolRegime.HIGH
        elif vq < q25:
            vol_r = VolRegime.LOW
        else:
            vol_r = VolRegime.NORMAL

    driver = DriverRegime.MIXED
    if volume is not None:
        v = volume.reindex(c.index).ffill()
        dv = np.log(v / v.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()
        joint = pd.concat([r.loc[dv.index], dv], axis=1).dropna()
        if len(joint) > 10:
            corr = joint.iloc[:, 0].corr(joint.iloc[:, 1])
            vol_shock = float(dv.iloc[-10:].std() > dv.std() * 1.5)
            price_quiet = float(abs(r.iloc[-5:].mean()) < r.std() * 0.5)
            if vol_shock and price_quiet:
                driver = DriverRegime.NEWS
            elif corr is not None and abs(corr) > 0.25:
                driver = DriverRegime.TECHNICAL
            else:
                driver = DriverRegime.MIXED

    conf = float(min(1.0, max(0.2, len(r) / float(lookback))))
    metrics = {"trend_z": z, "realized_vol_ann": vol * np.sqrt(252.0)}
    return RegimeSnapshot(
        trend=trend,
        volatility=vol_r,
        driver=driver,
        confidence=conf,
        metrics=metrics,
    )


def regime_strategy_weights(snapshot: RegimeSnapshot) -> Dict[str, float]:
    """Suggest emphasis weights across model families for Meta / Arena routing."""
    w = {"tree": 0.25, "linear": 0.25, "neural": 0.25, "sequence": 0.25}
    if snapshot.volatility == VolRegime.HIGH:
        w["tree"] += 0.15
        w["linear"] -= 0.05
        w["neural"] -= 0.05
        w["sequence"] -= 0.05
    if snapshot.trend == TrendRegime.SIDEWAYS:
        w["linear"] += 0.1
        w["neural"] += 0.1
        w["tree"] -= 0.1
        w["sequence"] -= 0.1
    if snapshot.driver == DriverRegime.NEWS:
        w["neural"] += 0.1
        w["sequence"] += 0.1
        w["linear"] -= 0.1
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}
