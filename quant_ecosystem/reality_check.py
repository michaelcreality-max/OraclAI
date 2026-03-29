"""
Reality Check Agent — market validator.

Backtests with slippage, costs, latency; regime buckets; penalizes overfitting proxies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_squared_error

from .features import apply_feature_mask
from .model_arena import _fit_torch_lstm, _predict_torch_lstm
from .schemas import BacktestConfig, RealityReport


def _max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / (peak + 1e-12)
    return float(dd.min())


def _sharpe(returns: np.ndarray, annualization: float) -> float:
    if len(returns) < 2:
        return 0.0
    mu = returns.mean()
    sd = returns.std() + 1e-12
    return float((mu / sd) * np.sqrt(annualization))


class RealityCheckAgent:
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def _predict(
        self,
        model_family: str,
        artifact: object,
        X: np.ndarray,
    ) -> np.ndarray:
        if model_family == "lstm_torch" and isinstance(artifact, dict):
            return _predict_torch_lstm(artifact, X)
        est = artifact
        return est.predict(X)

    def validate(
        self,
        *,
        hypothesis_id: str,
        model_id: str,
        model_family: str,
        artifact: object,
        features: pd.DataFrame,
        target: pd.Series,
        close: pd.Series,
        feature_columns: List[str],
    ) -> RealityReport:
        """
        Long/flat: long when predicted next-period return > 0.
        Latency shifts the signal; slippage and commission penalize churn.
        """
        cfg = self.config
        Xf = apply_feature_mask(features, feature_columns)
        df = pd.concat(
            [Xf, target.rename("target"), close.rename("close")],
            axis=1,
        ).dropna()
        if len(df) < 80:
            return RealityReport(
                hypothesis_id=hypothesis_id,
                model_id=model_id,
                sharpe=-10.0,
                max_drawdown=-1.0,
                turnover=0.0,
                net_pnl_after_costs=-1.0,
                train_val_gap=1.0,
                passed=False,
                kill_reason="Insufficient history after alignment.",
            )

        X_mat = df[feature_columns].to_numpy(dtype=float)
        y_vec = df["target"].to_numpy(dtype=float)
        c = df["close"].to_numpy(dtype=float)

        split = int(len(df) * 0.7)
        X_train, X_val = X_mat[:split], X_mat[split:]
        y_train, y_val = y_vec[:split], y_vec[split:]

        # Train-only fits for gap + simulation so metrics match (no full-sample refit).
        art_for_pred: Optional[Dict[str, Any]] = None
        est_for_pred: Optional[object] = None

        try:
            if model_family == "lstm_torch" and isinstance(artifact, dict):
                seq_len = int(artifact.get("seq_len", 16))
                pack = _fit_torch_lstm(X_train, y_train, seq_len=seq_len)
                if pack is None:
                    gap = 1.0
                else:
                    _, art_tr = pack
                    art_for_pred = art_tr
                    pred_tr = _predict_torch_lstm(art_tr, X_train)
                    full_X = np.vstack([X_train, X_val])
                    pred_full = _predict_torch_lstm(art_tr, full_X)
                    pred_val = pred_full[-len(X_val) :]
                    mse_tr = mean_squared_error(y_train[seq_len:], pred_tr[seq_len:])
                    mse_va = mean_squared_error(y_val, pred_val)
                    gap = float(max(0.0, mse_va - mse_tr))
            else:
                est_tr = clone(artifact)
                est_tr.fit(X_train, y_train)
                est_for_pred = est_tr
                pred_train = est_tr.predict(X_train)
                pred_val = est_tr.predict(X_val)
                mse_tr = mean_squared_error(y_train, pred_train)
                mse_va = mean_squared_error(y_val, pred_val)
                gap = float(max(0.0, mse_va - mse_tr))
        except Exception:
            gap = 1.0

        try:
            if model_family == "lstm_torch" and isinstance(artifact, dict):
                if art_for_pred is not None:
                    preds = _predict_torch_lstm(art_for_pred, X_mat)
                else:
                    preds = self._predict(model_family, artifact, X_mat)
            elif est_for_pred is not None:
                preds = est_for_pred.predict(X_mat)
            else:
                preds = self._predict(model_family, artifact, X_mat)
        except Exception as exc:
            return RealityReport(
                hypothesis_id=hypothesis_id,
                model_id=model_id,
                sharpe=-10.0,
                max_drawdown=-1.0,
                turnover=0.0,
                net_pnl_after_costs=-1.0,
                train_val_gap=gap,
                passed=False,
                kill_reason=f"Prediction failed: {exc!r}",
            )

        preds_series = pd.Series(preds, index=df.index)
        signal = (preds_series.shift(cfg.latency_bars) > 0).astype(float)
        log_px = np.log(c)
        ret = pd.Series(np.diff(log_px), index=df.index[1:])
        sig = signal.shift(1).reindex(ret.index).fillna(0.0)
        strat_ret = sig * ret * cfg.position_size_fraction

        turnover = float(sig.diff().abs().sum() / max(len(sig), 1))
        cost_per_change = cfg.commission_per_trade + cfg.slippage_bps / 10000.0 * float(np.mean(np.abs(c)))
        costs = sig.diff().abs().fillna(0.0) * cost_per_change
        net = strat_ret - costs.reindex(strat_ret.index).fillna(0.0)

        sharpe = _sharpe(net.to_numpy(dtype=float), cfg.annualization_factor)
        eq = np.cumprod(1.0 + net.to_numpy(dtype=float))
        mdd = _max_drawdown(eq)
        net_pnl = float(eq[-1] - 1.0) if len(eq) else -1.0

        r = ret.rolling(20).std()
        regimes: Dict[str, float] = {}
        if len(r.dropna()) > 20:
            for label, cond in [
                ("crash", r > r.quantile(0.75)),
                ("rally", r < r.quantile(0.25)),
                ("sideways", (r >= r.quantile(0.25)) & (r <= r.quantile(0.75))),
            ]:
                mask = cond.fillna(False)
                sub = net[mask]
                regimes[label] = float(sub.mean() * cfg.annualization_factor) if len(sub) else 0.0

        kill = None
        passed = True
        if sharpe < 0.2:
            passed = False
            kill = "Sharpe below minimum after costs."
        elif mdd < -0.35:
            passed = False
            kill = "Drawdown too deep."
        elif gap > 0.05:
            passed = False
            kill = "Train/validation instability (overfitting proxy)."
        elif turnover > 25.0:
            passed = False
            kill = "Turnover too high — costs dominate."

        return RealityReport(
            hypothesis_id=hypothesis_id,
            model_id=model_id,
            sharpe=sharpe,
            max_drawdown=mdd,
            turnover=turnover,
            net_pnl_after_costs=net_pnl,
            train_val_gap=gap,
            regime_scores=regimes,
            passed=passed,
            kill_reason=kill,
        )
