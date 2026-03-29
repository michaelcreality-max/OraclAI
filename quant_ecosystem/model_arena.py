"""
Model Arena Agent — competition engine.

Trains many model families in parallel and runs round-robin / elimination tournaments.
Uses sklearn-heavy stack; optional XGBoost / PyTorch when installed.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .schemas import ModelCandidate, TournamentResult

try:
    import xgboost as xgb  # type: ignore
except Exception:  # pragma: no cover
    xgb = None


def _neg_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return -float(mean_squared_error(y_true, y_pred))


def _time_series_cv_score(
    X: np.ndarray,
    y: np.ndarray,
    build_estimator: Callable[[], Any],
    n_splits: int = 5,
) -> float:
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores: List[float] = []
    for train_idx, test_idx in tscv.split(X):
        est = build_estimator()
        est.fit(X[train_idx], y[train_idx])
        pred = est.predict(X[test_idx])
        scores.append(_neg_mse(y[test_idx], pred))
    return float(np.mean(scores)) if scores else -1e9


def _fit_torch_lstm(
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int = 16,
    epochs: int = 40,
    lr: float = 1e-2,
) -> Optional[Tuple[Any, Dict[str, Any]]]:
    try:
        import torch  # type: ignore
        import torch.nn as nn  # type: ignore
    except Exception:  # pragma: no cover
        return None
    if len(X) <= seq_len + 50:
        return None
    n_features = X.shape[1]

    class _TinyLSTM(nn.Module):
        def __init__(self, n_feat: int, hidden: int = 32):
            super().__init__()
            self.lstm = nn.LSTM(n_feat, hidden, batch_first=True)
            self.fc = nn.Linear(hidden, 1)

        def forward(self, x):  # type: ignore[no-untyped-def]
            out, _ = self.lstm(x)
            last = out[:, -1, :]
            return self.fc(last).squeeze(-1)

    xs: List[np.ndarray] = []
    ys: List[float] = []
    for i in range(seq_len, len(X)):
        xs.append(X[i - seq_len : i])
        ys.append(y[i])
    tx = torch.tensor(np.stack(xs), dtype=torch.float32)
    ty = torch.tensor(np.array(ys), dtype=torch.float32)
    model = _TinyLSTM(n_features)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        pred = model(tx)
        loss = loss_fn(pred, ty)
        loss.backward()
        opt.step()
    model.eval()
    artifact = {"model": model, "seq_len": seq_len, "n_features": n_features}
    return model, artifact


def _predict_torch_lstm(artifact: Dict[str, Any], X: np.ndarray) -> np.ndarray:
    try:
        import torch  # type: ignore
    except Exception:  # pragma: no cover
        return np.zeros(len(X))
    model = artifact["model"]
    seq_len = int(artifact["seq_len"])
    model.eval()
    out: List[float] = []
    with torch.no_grad():
        for i in range(len(X)):
            if i < seq_len:
                out.append(0.0)
                continue
            chunk = X[i - seq_len : i]
            t = torch.tensor(chunk[None, ...], dtype=torch.float32)
            p = model(t).cpu().numpy().reshape(-1)[0]
            out.append(float(p))
    return np.array(out)


class ModelArenaAgent:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def _candidates(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> List[Tuple[str, Callable[[], Any], Optional[str]]]:
        """Returns list of (family, builder, optional_kind)."""

        def ridge() -> Pipeline:
            return Pipeline(
                [("scaler", StandardScaler()), ("m", Ridge(alpha=1.0, random_state=42))]
            )

        def rf() -> RandomForestRegressor:
            return RandomForestRegressor(
                n_estimators=200,
                max_depth=8,
                random_state=42,
                n_jobs=-1,
            )

        def gbm() -> GradientBoostingRegressor:
            return GradientBoostingRegressor(random_state=42)

        def mlp() -> Pipeline:
            return Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "m",
                        MLPRegressor(
                            hidden_layer_sizes=(128, 64),
                            max_iter=300,
                            random_state=42,
                            early_stopping=True,
                        ),
                    ),
                ]
            )

        specs: List[Tuple[str, Callable[[], Any], Optional[str]]] = [
            ("ridge", ridge, None),
            ("random_forest", rf, None),
            ("sklearn_gbm", gbm, None),
            ("mlp", mlp, None),
        ]

        if xgb is not None:

            def xgb_est() -> Any:
                return xgb.XGBRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1,
                )

            specs.append(("xgboost", xgb_est, None))

        # Transformer-style: wide MLP on scaled features (placeholder for real attention models)
        def transformer_style() -> Pipeline:
            return Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "m",
                        MLPRegressor(
                            hidden_layer_sizes=(256, 256, 128),
                            max_iter=400,
                            random_state=43,
                            early_stopping=True,
                        ),
                    ),
                ]
            )

        specs.append(("transformer_style_mlp", transformer_style, None))

        return specs

    def train_all(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        n_splits: int = 5,
    ) -> List[ModelCandidate]:
        Xa, ya = X.align(y, join="inner", axis=0)
        Xn = Xa.to_numpy(dtype=float)
        yn = ya.to_numpy(dtype=float)
        specs = self._candidates(Xa, ya)

        results: List[ModelCandidate] = []

        def job(
            spec: Tuple[str, Callable[[], Any], Optional[str]],
        ) -> Optional[ModelCandidate]:
            family, builder, _ = spec
            score = _time_series_cv_score(Xn, yn, builder, n_splits=n_splits)
            est = builder()
            est.fit(Xn, yn)
            mid = f"{family}_{uuid.uuid4().hex[:8]}"
            return ModelCandidate(
                id=mid,
                family=family,
                params={},
                artifact=est,
                train_score=score,
                fitness=score,
            )

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futs = [ex.submit(job, s) for s in specs]
            for fut in as_completed(futs):
                r = fut.result()
                if r is not None:
                    results.append(r)

        # Optional LSTM track (sequential; separate from thread pool to avoid torch issues)
        lstm_pack = _fit_torch_lstm(Xn, yn)
        if lstm_pack is not None:
            model, art = lstm_pack
            # quick CV proxy: in-sample neg MSE on last 20% after seq warmup
            seq_len = art["seq_len"]
            preds = _predict_torch_lstm(art, Xn)
            yv = yn[seq_len:]
            pv = preds[seq_len:]
            score = _neg_mse(yv, pv)
            mid = f"lstm_{uuid.uuid4().hex[:8]}"
            results.append(
                ModelCandidate(
                    id=mid,
                    family="lstm_torch",
                    params={"seq_len": art["seq_len"]},
                    artifact=art,
                    train_score=score,
                    fitness=score,
                )
            )

        return results

    def tournament(
        self,
        models: List[ModelCandidate],
        X: pd.DataFrame,
        y: pd.Series,
        *,
        top_k: int = 5,
    ) -> Tuple[List[ModelCandidate], List[TournamentResult]]:
        """Pairwise comparison on last time-series fold proxy: full refit score."""
        Xa, ya = X.align(y, join="inner", axis=0)
        Xn = Xa.to_numpy(dtype=float)
        yn = ya.to_numpy(dtype=float)
        n = len(Xn)
        if n < 50:
            return sorted(models, key=lambda m: m.fitness, reverse=True)[:top_k], []

        split = int(n * 0.8)
        X_train, X_test = Xn[:split], Xn[split:]
        y_train, y_test = yn[:split], yn[split:]

        def predict_one(mc: ModelCandidate) -> np.ndarray:
            if mc.family == "lstm_torch":
                seq_len = int(mc.params.get("seq_len", 16))
                pack = _fit_torch_lstm(X_train, y_train, seq_len=seq_len)
                if pack is None:
                    return np.zeros(len(X_test))
                _, art = pack
                full_X = np.vstack([X_train, X_test])
                preds_full = _predict_torch_lstm(art, full_X)
                return preds_full[-len(X_test) :]
            est = mc.artifact
            est.fit(X_train, y_train)
            return est.predict(X_test)

        scored: List[Tuple[ModelCandidate, float]] = []
        for mc in models:
            try:
                pred = predict_one(mc)
                s = _neg_mse(y_test, pred)
            except Exception:
                s = -1e9
            scored.append((mc, s))

        scored.sort(key=lambda t: t[1], reverse=True)
        ordered = [m for m, _ in scored]

        tourney: List[TournamentResult] = []
        for i in range(0, len(ordered) - 1, 2):
            a, b = ordered[i], ordered[i + 1]
            sa = next(s for m, s in scored if m.id == a.id)
            sb = next(s for m, s in scored if m.id == b.id)
            if sa >= sb:
                w, l = a, b
                delta = sa - sb
            else:
                w, l = b, a
                delta = sb - sa
            tourney.append(TournamentResult(winner_id=w.id, loser_id=l.id, metric_delta=delta))

        return ordered[:top_k], tourney
