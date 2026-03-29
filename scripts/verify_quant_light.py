#!/usr/bin/env python3
"""
Fast checks for quant_ecosystem (no full yfinance / arena cycle).
Run: ./scripts/verify_quant_light.py  or  python scripts/verify_quant_light.py
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

    from quant_ecosystem.alpha_discovery import GeneticFeatureSearch
    from quant_ecosystem.features import build_feature_matrix, make_target_forward_return
    from quant_ecosystem.synthetic import make_synthetic_ohlcv

    ohlcv, spy = make_synthetic_ohlcv(250)
    feats = build_feature_matrix(ohlcv, spy)
    close = ohlcv["close"].reindex(feats.index).ffill()
    y = make_target_forward_return(close, horizon=1)
    aligned = feats.join(y, how="inner").dropna()
    assert len(aligned) > 100, "expected enough rows after alignment"

    X = aligned[feats.columns]
    y_series = aligned["target"]

    # Single-column GA: must not crash (regression guard)
    one_col = X.iloc[:, :1]
    gfs = GeneticFeatureSearch(list(one_col.columns), population_size=8, generations=3, seed=0)
    cols, _ = gfs.run(one_col, y_series)
    assert len(cols) >= 1

    print("[verify_quant_light] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
