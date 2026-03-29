"""
Unknown pattern detection: anomalies in feature space + hidden correlation mining.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.covariance import EmpiricalCovariance
from sklearn.ensemble import IsolationForest


def detect_anomalies(
    X: pd.DataFrame,
    *,
    contamination: float = 0.05,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Flag recent rows that look unlike historical feature distribution."""
    if len(X) < 40:
        return {"ok": False, "reason": "insufficient_rows", "anomaly_dates": []}
    xf = X.dropna()
    model = IsolationForest(contamination=contamination, random_state=random_state)
    scores = model.fit_predict(xf.values)
    last_flag = int(scores[-1] == -1)
    recent = xf.index[-1].isoformat() if hasattr(xf.index[-1], "isoformat") else str(xf.index[-1])
    return {
        "ok": True,
        "latest_bar_anomaly": bool(last_flag),
        "latest_timestamp": recent,
        "anomaly_ratio_recent_20": float(np.mean(scores[-20:] == -1)) if len(scores) >= 20 else None,
    }


def hidden_correlations(X: pd.DataFrame, *, min_abs: float = 0.35, top_k: int = 12) -> Dict[str, Any]:
    """Surface large |corr| pairs that might be non-obvious (linear view)."""
    xf = X.dropna()
    if len(xf) < 30:
        return {"ok": False, "pairs": []}
    c = xf.corr()
    pairs: List[Tuple[str, str, float]] = []
    cols = list(c.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1 :]:
            v = c.loc[a, b]
            if np.isnan(v):
                continue
            if abs(v) >= min_abs:
                pairs.append((a, b, float(v)))
    pairs.sort(key=lambda t: abs(t[2]), reverse=True)
    return {"ok": True, "pairs": [{"a": a, "b": b, "corr": round(v, 4)} for a, b, v in pairs[:top_k]]}


def precision_matrix_edges(X: pd.DataFrame, *, min_abs: float = 0.08) -> Dict[str, Any]:
    """Gaussian graphical model style: precision matrix off-diagonals (partial corr hints)."""
    xf = X.dropna()
    if len(xf) < 40:
        return {"ok": False, "edges": []}
    emp = EmpiricalCovariance().fit(xf.values)
    prec = np.linalg.pinv(emp.covariance_)
    d = np.sqrt(np.diag(prec))
    partial = -prec / np.outer(d, d)
    np.fill_diagonal(partial, 0.0)
    cols = list(xf.columns)
    edges = []
    for i, a in enumerate(cols):
        for j in range(i + 1, len(cols)):
            b = cols[j]
            v = partial[i, j]
            if abs(v) >= min_abs:
                edges.append({"a": a, "b": b, "partial_corr_hint": round(float(v), 4)})
    edges.sort(key=lambda e: abs(e["partial_corr_hint"]), reverse=True)
    return {"ok": True, "edges": edges[:20]}
