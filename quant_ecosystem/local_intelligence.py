"""Local-only market intelligence engine for synthetic financial research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StockProfile:
    symbol: str
    sector: str
    archetype: str
    base_price: float
    base_volume: float
    beta: float
    drift_bias: float
    volatility_bias: float


class LocalResearchEngine:
    """Generate synthetic markets locally and derive technical trade signals."""

    DEFAULT_SYMBOLS: tuple[str, ...] = ("AAPL", "MSFT", "NVDA", "JPM", "XOM", "TSLA")

    _PRESET_PROFILES: Dict[str, StockProfile] = {
        "AAPL": StockProfile("AAPL", "Technology", "quality_growth", 192.0, 62_000_000.0, 1.02, 0.00030, 0.95),
        "MSFT": StockProfile("MSFT", "Technology", "platform_compounder", 418.0, 29_000_000.0, 0.94, 0.00032, 0.82),
        "NVDA": StockProfile("NVDA", "Technology", "high_beta_growth", 865.0, 51_000_000.0, 1.42, 0.00055, 1.55),
        "JPM": StockProfile("JPM", "Financials", "macro_cyclical", 188.0, 14_000_000.0, 0.88, 0.00018, 0.88),
        "XOM": StockProfile("XOM", "Energy", "commodity_cyclical", 112.0, 19_500_000.0, 0.83, 0.00012, 1.08),
        "TSLA": StockProfile("TSLA", "Consumer Discretionary", "speculative_momentum", 236.0, 97_000_000.0, 1.76, 0.00042, 1.85),
    }

    _SECTORS: tuple[str, ...] = (
        "Technology",
        "Financials",
        "Energy",
        "Healthcare",
        "Consumer Discretionary",
        "Industrials",
    )

    _ARCHETYPES: tuple[str, ...] = (
        "quality_growth",
        "platform_compounder",
        "high_beta_growth",
        "macro_cyclical",
        "defensive_value",
        "speculative_momentum",
    )

    def __init__(self, *, seed: int = 42):
        self.seed = seed

    def generate_market(
        self,
        *,
        symbols: Optional[Sequence[str]] = None,
        days: int = 252,
        include_history: bool = True,
        max_points: int = 90,
        include_internal_frames: bool = False,
    ) -> Dict[str, Any]:
        days = max(90, min(int(days), 900))
        max_points = max(20, min(int(max_points), days))
        clean_symbols = self._normalize_symbols(symbols)
        dates = pd.date_range(
            end=pd.Timestamp.now(tz="UTC").tz_localize(None).normalize(),
            periods=days,
            freq="B",
        )

        benchmark_rng = np.random.default_rng(self.seed)
        benchmark_df, benchmark_regimes = self._simulate_benchmark(dates, benchmark_rng)
        benchmark_log_returns = np.log(benchmark_df["close"] / benchmark_df["close"].shift(1)).fillna(0.0)

        stocks: Dict[str, Any] = {}
        stock_frames: Dict[str, pd.DataFrame] = {}

        for symbol in clean_symbols:
            profile = self._profile_for_symbol(symbol)
            symbol_rng = np.random.default_rng(self._symbol_seed(symbol))
            stock_df, regimes = self._simulate_stock(
                dates=dates,
                profile=profile,
                benchmark_returns=benchmark_log_returns,
                market_regimes=benchmark_regimes,
                rng=symbol_rng,
            )
            stock_frames[symbol] = stock_df
            stocks[symbol] = {
                "profile": asdict(profile),
                "summary": self._series_summary(stock_df),
                "active_regime": regimes[-1],
                "regimes": regimes,
            }
            if include_history:
                stocks[symbol]["history"] = self._serialize_ohlcv(stock_df, max_points=max_points)

        payload: Dict[str, Any] = {
            "engine": "local_synthetic_financial_intelligence",
            "mode": "offline_only",
            "seed": self.seed,
            "days": days,
            "benchmark": {
                "symbol": "LOCAL-MKT",
                "summary": self._series_summary(benchmark_df),
                "active_regime": benchmark_regimes[-1],
                "regimes": benchmark_regimes,
            },
            "stocks": stocks,
        }
        if include_history:
            payload["benchmark"]["history"] = self._serialize_ohlcv(benchmark_df, max_points=max_points)
        if include_internal_frames:
            payload["_frames"] = stock_frames
        return payload

    def analyze_market(
        self,
        *,
        symbols: Optional[Sequence[str]] = None,
        days: int = 252,
        include_history: bool = True,
        max_points: int = 90,
    ) -> Dict[str, Any]:
        market = self.generate_market(
            symbols=symbols,
            days=days,
            include_history=include_history,
            max_points=max_points,
            include_internal_frames=True,
        )
        stock_frames = market.pop("_frames", {})
        overview_rows: List[Dict[str, Any]] = []

        for symbol, stock_payload in market["stocks"].items():
            stock_df = stock_frames[symbol]
            features = self.build_feature_frame(stock_df)
            signal = self.build_signal(symbol, stock_df, features, stock_payload)
            stock_payload["features"] = self._feature_snapshot(features)
            stock_payload["signal"] = signal
            overview_rows.append(
                {
                    "symbol": symbol,
                    "action": signal["action"],
                    "confidence": signal["confidence"],
                    "score": signal["score"],
                    "trend_strength": stock_payload["features"]["trend_strength"],
                    "realized_volatility": stock_payload["features"]["realized_volatility_20d"],
                }
            )

        market["overview"] = self._overview_summary(overview_rows)
        market["benchmark"]["market_backdrop"] = self._benchmark_backdrop(market["benchmark"])
        return market

    def build_feature_frame(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        close = ohlcv["close"].astype(float)
        returns = close.pct_change()
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()
        out = pd.DataFrame(index=ohlcv.index)
        out["sma_20"] = close.rolling(20).mean()
        out["sma_50"] = close.rolling(50).mean()
        out["ema_12"] = ema_12
        out["ema_26"] = ema_26
        out["rsi_14"] = self._rsi(close, 14)
        out["macd_line"] = macd_line
        out["macd_signal"] = macd_signal
        out["macd_hist"] = macd_line - macd_signal
        out["realized_volatility_20d"] = returns.rolling(20).std() * math.sqrt(252.0)
        out["trend_strength"] = self._trend_strength(close, window=20)
        out["close"] = close
        return out.dropna()

    def build_signal(
        self,
        symbol: str,
        ohlcv: pd.DataFrame,
        features: pd.DataFrame,
        stock_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        latest = features.iloc[-1]
        close = float(latest["close"])
        sma_20 = float(latest["sma_20"])
        sma_50 = float(latest["sma_50"])
        ema_12 = float(latest["ema_12"])
        ema_26 = float(latest["ema_26"])
        rsi_14 = float(latest["rsi_14"])
        macd_hist = float(latest["macd_hist"])
        volatility = float(latest["realized_volatility_20d"])
        trend_strength = float(latest["trend_strength"])

        score = 0.0
        confidence_penalty = 0.0
        votes: List[int] = []
        reasoning: List[str] = []
        risk_flags: List[str] = []

        if close > sma_20 > sma_50:
            score += 0.34
            votes.append(1)
            reasoning.append("Price is above the 20-day and 50-day SMA, keeping the medium-term trend constructive.")
        elif close < sma_20 < sma_50:
            score -= 0.34
            votes.append(-1)
            reasoning.append("Price is below the 20-day and 50-day SMA, which keeps the medium-term trend under pressure.")
        else:
            votes.append(0)
            reasoning.append("Moving averages are mixed, so the broader trend backdrop is not fully aligned.")

        if ema_12 > ema_26:
            score += 0.18
            votes.append(1)
            reasoning.append("The 12-day EMA is above the 26-day EMA, showing positive short-term momentum.")
        else:
            score -= 0.18
            votes.append(-1)
            reasoning.append("The 12-day EMA remains below the 26-day EMA, which points to fading short-term momentum.")

        if macd_hist > 0:
            score += 0.16
            votes.append(1)
            reasoning.append("MACD histogram is positive, which suggests upside momentum is still building.")
        else:
            score -= 0.16
            votes.append(-1)
            reasoning.append("MACD histogram is negative, so momentum remains skewed to the downside.")

        if 57.0 <= rsi_14 <= 70.0:
            score += 0.14
            votes.append(1)
            reasoning.append(f"RSI sits at {rsi_14:.1f}, a healthy momentum zone that supports continuation without extreme overheating.")
        elif 30.0 <= rsi_14 <= 43.0:
            score -= 0.14
            votes.append(-1)
            reasoning.append(f"RSI sits at {rsi_14:.1f}, which reflects weak participation and a soft momentum profile.")
        elif rsi_14 > 72.0:
            confidence_penalty += 0.08
            reasoning.append(f"RSI is elevated at {rsi_14:.1f}, so upside may be crowded and conviction is trimmed.")
            risk_flags.append("Momentum is stretched on an overbought RSI reading.")
        elif rsi_14 < 28.0:
            confidence_penalty += 0.06
            reasoning.append(f"RSI is depressed at {rsi_14:.1f}, which raises the odds of unstable, headline-driven reversals.")
            risk_flags.append("Momentum is washed out on an oversold RSI reading.")
        else:
            votes.append(0)
            reasoning.append(f"RSI is near neutral at {rsi_14:.1f}, which keeps momentum confirmation limited.")

        score += trend_strength * 0.22
        if trend_strength > 0.35:
            votes.append(1)
            reasoning.append(f"Trend strength scores {trend_strength:.2f}, indicating a persistent directional move rather than a noisy drift.")
        elif trend_strength < -0.35:
            votes.append(-1)
            reasoning.append(f"Trend strength scores {trend_strength:.2f}, which confirms a persistent downside trend.")
        else:
            votes.append(0)
            reasoning.append(f"Trend strength scores {trend_strength:.2f}, so the tape still looks range-bound.")

        if volatility > 0.42:
            confidence_penalty += 0.12
            risk_flags.append("Realized volatility is high, so signal reliability is discounted.")
        elif volatility > 0.30:
            confidence_penalty += 0.05
            risk_flags.append("Realized volatility is elevated, which trims confidence.")

        score = float(np.clip(score, -1.0, 1.0))
        action = "BUY" if score >= 0.24 else "SELL" if score <= -0.24 else "HOLD"

        non_zero_votes = [v for v in votes if v != 0]
        if non_zero_votes:
            agreement = abs(sum(non_zero_votes)) / len(non_zero_votes)
        else:
            agreement = 0.0

        confidence = 0.44 + min(abs(score), 0.75) * 0.32 + agreement * 0.24 - confidence_penalty
        if action == "HOLD":
            confidence = min(confidence, 0.67)
        confidence = float(np.clip(confidence, 0.35, 0.95))

        current_regime = stock_payload.get("active_regime", {})
        if current_regime:
            reasoning.append(
                f"Current synthetic regime is {current_regime.get('trend', 'mixed')} with {current_regime.get('volatility', 'normal')} volatility under a {current_regime.get('theme', 'stable')} backdrop."
            )

        return {
            "symbol": symbol,
            "action": action,
            "bias": "bullish" if score > 0.12 else "bearish" if score < -0.12 else "neutral",
            "score": round(score, 3),
            "confidence": round(confidence, 3),
            "reasoning": reasoning[:5],
            "risk_flags": risk_flags[:3],
        }

    def _normalize_symbols(self, symbols: Optional[Sequence[str]]) -> List[str]:
        if not symbols:
            return list(self.DEFAULT_SYMBOLS)
        cleaned: List[str] = []
        for raw in symbols:
            symbol = str(raw).strip().upper()
            if symbol and symbol not in cleaned:
                cleaned.append(symbol)
        return cleaned or list(self.DEFAULT_SYMBOLS)

    def _symbol_seed(self, symbol: str) -> int:
        digest = hashlib.sha256(f"{self.seed}:{symbol}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big")

    def _profile_for_symbol(self, symbol: str) -> StockProfile:
        preset = self._PRESET_PROFILES.get(symbol)
        if preset is not None:
            return preset

        rng = np.random.default_rng(self._symbol_seed(symbol))
        return StockProfile(
            symbol=symbol,
            sector=str(rng.choice(self._SECTORS)),
            archetype=str(rng.choice(self._ARCHETYPES)),
            base_price=float(rng.uniform(18.0, 380.0)),
            base_volume=float(rng.uniform(2_500_000.0, 45_000_000.0)),
            beta=float(rng.uniform(0.75, 1.65)),
            drift_bias=float(rng.uniform(-0.00005, 0.00045)),
            volatility_bias=float(rng.uniform(0.80, 1.65)),
        )

    def _simulate_benchmark(
        self,
        dates: pd.DatetimeIndex,
        rng: np.random.Generator,
    ) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
        weights = [0.26, 0.23, 0.18, 0.33]
        lengths = self._segment_lengths(len(dates), weights)
        templates = [
            {
                "theme": "accumulation",
                "trend": "bullish",
                "volatility": "low",
                "drift": 0.00042,
                "sigma": 0.0082,
                "volume_multiplier": 0.92,
                "catalyst": "institutions steadily absorb supply",
            },
            {
                "theme": "risk_on_expansion",
                "trend": "bullish",
                "volatility": "medium",
                "drift": 0.00076,
                "sigma": 0.0118,
                "volume_multiplier": 1.04,
                "catalyst": "breadth improves and momentum broadens",
            },
            {
                "theme": "macro_correction",
                "trend": "bearish",
                "volatility": "high",
                "drift": -0.00112,
                "sigma": 0.0215,
                "volume_multiplier": 1.36,
                "catalyst": "macro shocks force a defensive unwind",
            },
            {
                "theme": "recovery_rotation",
                "trend": "bullish",
                "volatility": "medium",
                "drift": 0.00063,
                "sigma": 0.0138,
                "volume_multiplier": 1.15,
                "catalyst": "buyers return as sellers exhaust",
            },
        ]

        closes: List[float] = []
        opens: List[float] = []
        highs: List[float] = []
        lows: List[float] = []
        volumes: List[float] = []
        regimes: List[Dict[str, Any]] = []

        previous_close = 415.0
        cursor = 0
        for template, length in zip(templates, lengths):
            start_idx = cursor
            drift = template["drift"] + rng.normal(0.0, 0.00006)
            sigma = template["sigma"] * rng.uniform(0.92, 1.08)
            for _ in range(length):
                overnight_gap = rng.normal(0.0, sigma * 0.22)
                intraday_return = drift + rng.normal(0.0, sigma)
                open_price = max(1.0, previous_close * math.exp(overnight_gap))
                close_price = max(1.0, open_price * math.exp(intraday_return))
                spread = min(0.12, abs(intraday_return) * rng.uniform(1.0, 1.8) + sigma * rng.uniform(0.8, 1.5))
                high_price = max(open_price, close_price) * (1.0 + spread)
                low_price = max(0.5, min(open_price, close_price) * (1.0 - spread))
                volume = 92_000_000.0 * template["volume_multiplier"] * (1.0 + min(abs(intraday_return) * 11.0, 2.0))
                volume *= rng.lognormal(0.0, 0.16)

                opens.append(open_price)
                highs.append(high_price)
                lows.append(low_price)
                closes.append(close_price)
                volumes.append(volume)
                previous_close = close_price
                cursor += 1

            segment_closes = pd.Series(closes[start_idx:cursor], index=dates[start_idx:cursor])
            segment_ret = float(segment_closes.iloc[-1] / segment_closes.iloc[0] - 1.0)
            segment_vol = float(segment_closes.pct_change().dropna().std() * math.sqrt(252.0)) if len(segment_closes) > 1 else 0.0
            regimes.append(
                {
                    "theme": template["theme"],
                    "trend": template["trend"],
                    "volatility": template["volatility"],
                    "catalyst": template["catalyst"],
                    "start": dates[start_idx].strftime("%Y-%m-%d"),
                    "end": dates[cursor - 1].strftime("%Y-%m-%d"),
                    "days": length,
                    "return_total": round(segment_ret, 4),
                    "realized_volatility": round(segment_vol, 4),
                }
            )

        df = pd.DataFrame(
            {
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            },
            index=dates,
        )
        return df, regimes

    def _simulate_stock(
        self,
        *,
        dates: pd.DatetimeIndex,
        profile: StockProfile,
        benchmark_returns: pd.Series,
        market_regimes: List[Dict[str, Any]],
        rng: np.random.Generator,
    ) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
        opens: List[float] = []
        highs: List[float] = []
        lows: List[float] = []
        closes: List[float] = []
        volumes: List[float] = []
        regimes: List[Dict[str, Any]] = []

        previous_close = profile.base_price
        cursor = 0
        for idx, market_regime in enumerate(market_regimes):
            length = int(market_regime["days"])
            start_idx = cursor
            drift_delta, sigma_multiplier, theme = self._stock_regime_adjustments(profile, idx, rng)
            benchmark_trend = market_regime["trend"]
            drift = profile.drift_bias + drift_delta
            if benchmark_trend == "bullish":
                drift += 0.00020
            elif benchmark_trend == "bearish":
                drift -= 0.00022

            sigma = self._volatility_base(market_regime["volatility"]) * profile.volatility_bias * sigma_multiplier
            anchor_price = previous_close

            for local_pos in range(length):
                global_idx = cursor + local_pos
                market_ret = float(benchmark_returns.iloc[global_idx])
                reversion = -0.018 * (math.log(max(previous_close, 1.0)) - math.log(max(anchor_price, 1.0)))
                overnight_gap = market_ret * 0.12 + rng.normal(0.0, sigma * 0.24)
                intraday_return = drift + profile.beta * market_ret * 0.58 + reversion + rng.normal(0.0, sigma)

                open_price = max(1.0, previous_close * math.exp(overnight_gap))
                close_price = max(1.0, open_price * math.exp(intraday_return))
                spread = min(0.18, abs(intraday_return) * rng.uniform(1.0, 1.9) + sigma * rng.uniform(0.8, 1.7))
                high_price = max(open_price, close_price) * (1.0 + spread)
                low_price = max(0.5, min(open_price, close_price) * (1.0 - spread))

                total_move = abs(close_price / max(previous_close, 1.0) - 1.0)
                volume = profile.base_volume * self._volume_multiplier(market_regime["volatility"])
                volume *= (1.0 + min(total_move * 16.0, 2.5))
                volume *= rng.lognormal(0.0, 0.24)

                opens.append(open_price)
                highs.append(high_price)
                lows.append(low_price)
                closes.append(close_price)
                volumes.append(volume)
                previous_close = close_price

            cursor += length
            segment_closes = pd.Series(closes[start_idx:cursor], index=dates[start_idx:cursor])
            segment_ret = float(segment_closes.iloc[-1] / segment_closes.iloc[0] - 1.0)
            segment_vol = float(segment_closes.pct_change().dropna().std() * math.sqrt(252.0)) if len(segment_closes) > 1 else 0.0
            regimes.append(
                {
                    "theme": theme,
                    "trend": self._trend_label(drift),
                    "volatility": self._volatility_label(sigma),
                    "catalyst": self._catalyst_text(profile, drift, sigma),
                    "start": dates[start_idx].strftime("%Y-%m-%d"),
                    "end": dates[cursor - 1].strftime("%Y-%m-%d"),
                    "days": length,
                    "return_total": round(segment_ret, 4),
                    "realized_volatility": round(segment_vol, 4),
                }
            )

        df = pd.DataFrame(
            {
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            },
            index=dates,
        )
        return df, regimes

    def _stock_regime_adjustments(
        self,
        profile: StockProfile,
        regime_index: int,
        rng: np.random.Generator,
    ) -> tuple[float, float, str]:
        style_bias = {
            "quality_growth": [0.00018, 0.00028, -0.00012, 0.00024],
            "platform_compounder": [0.00016, 0.00024, -0.00008, 0.00021],
            "high_beta_growth": [0.00024, 0.00046, -0.00034, 0.00037],
            "macro_cyclical": [0.00006, 0.00018, -0.00024, 0.00015],
            "defensive_value": [0.00010, 0.00008, -0.00004, 0.00009],
            "speculative_momentum": [0.00010, 0.00052, -0.00046, 0.00040],
        }
        sigma_bias = {
            "quality_growth": [0.92, 0.98, 1.08, 0.96],
            "platform_compounder": [0.85, 0.92, 1.00, 0.90],
            "high_beta_growth": [1.10, 1.28, 1.38, 1.16],
            "macro_cyclical": [0.95, 1.06, 1.22, 1.02],
            "defensive_value": [0.78, 0.82, 0.92, 0.80],
            "speculative_momentum": [1.16, 1.40, 1.55, 1.25],
        }
        themes = {
            "quality_growth": ["stable demand", "institutional breakout", "valuation reset", "fundamental rebound"],
            "platform_compounder": ["steady compounding", "enterprise acceleration", "multiple compression", "cash-flow recovery"],
            "high_beta_growth": ["AI accumulation", "parabolic breakout", "profit-taking cascade", "momentum rebuild"],
            "macro_cyclical": ["credit stabilization", "rate-sensitive chase", "macro stress", "balance-sheet recovery"],
            "defensive_value": ["quiet accumulation", "income rotation", "defensive resilience", "slow grind higher"],
            "speculative_momentum": ["narrative squeeze", "high-beta breakout", "violent unwind", "retail-led rebound"],
        }

        drift = style_bias.get(profile.archetype, style_bias["quality_growth"])[regime_index]
        sigma = sigma_bias.get(profile.archetype, sigma_bias["quality_growth"])[regime_index]
        theme = themes.get(profile.archetype, themes["quality_growth"])[regime_index]
        drift += rng.normal(0.0, 0.00005)
        sigma *= rng.uniform(0.96, 1.08)
        return drift, sigma, theme

    def _segment_lengths(self, days: int, weights: Sequence[float]) -> List[int]:
        lengths = [max(15, int(round(days * w))) for w in weights]
        delta = days - sum(lengths)
        index = 0
        while delta != 0:
            pos = index % len(lengths)
            if delta > 0:
                lengths[pos] += 1
                delta -= 1
            elif lengths[pos] > 15:
                lengths[pos] -= 1
                delta += 1
            index += 1
        return lengths

    def _series_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        close = df["close"].astype(float)
        returns = close.pct_change().dropna()
        drawdown = close / close.cummax() - 1.0
        return {
            "first_close": round(float(close.iloc[0]), 2),
            "last_close": round(float(close.iloc[-1]), 2),
            "return_total": round(float(close.iloc[-1] / close.iloc[0] - 1.0), 4),
            "volatility_annualized": round(float(returns.std() * math.sqrt(252.0)), 4) if not returns.empty else 0.0,
            "max_drawdown": round(float(drawdown.min()), 4),
            "average_volume": int(round(float(df["volume"].mean()))),
        }

    def _feature_snapshot(self, features: pd.DataFrame) -> Dict[str, Any]:
        latest = features.iloc[-1]
        return {
            "close": round(float(latest["close"]), 2),
            "sma_20": round(float(latest["sma_20"]), 2),
            "sma_50": round(float(latest["sma_50"]), 2),
            "ema_12": round(float(latest["ema_12"]), 2),
            "ema_26": round(float(latest["ema_26"]), 2),
            "rsi_14": round(float(latest["rsi_14"]), 2),
            "macd_line": round(float(latest["macd_line"]), 4),
            "macd_signal": round(float(latest["macd_signal"]), 4),
            "macd_hist": round(float(latest["macd_hist"]), 4),
            "realized_volatility_20d": round(float(latest["realized_volatility_20d"]), 4),
            "trend_strength": round(float(latest["trend_strength"]), 4),
        }

    def _serialize_ohlcv(self, df: pd.DataFrame, *, max_points: int) -> List[Dict[str, Any]]:
        tail = df.tail(max_points)
        rows: List[Dict[str, Any]] = []
        for ts, row in tail.iterrows():
            rows.append(
                {
                    "date": pd.Timestamp(ts).strftime("%Y-%m-%d"),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": int(round(float(row["volume"]))),
                }
            )
        return rows

    def _overview_summary(self, rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        buy = [row["symbol"] for row in rows if row["action"] == "BUY"]
        sell = [row["symbol"] for row in rows if row["action"] == "SELL"]
        hold = [row["symbol"] for row in rows if row["action"] == "HOLD"]
        strongest = max(rows, key=lambda row: row["confidence"])
        most_volatile = max(rows, key=lambda row: row["realized_volatility"])
        return {
            "buy_candidates": buy,
            "sell_candidates": sell,
            "hold_candidates": hold,
            "strongest_conviction": {
                "symbol": strongest["symbol"],
                "action": strongest["action"],
                "confidence": strongest["confidence"],
            },
            "highest_realized_volatility": {
                "symbol": most_volatile["symbol"],
                "realized_volatility_20d": most_volatile["realized_volatility"],
            },
        }

    def _benchmark_backdrop(self, benchmark_payload: Dict[str, Any]) -> Dict[str, Any]:
        active = benchmark_payload.get("active_regime", {})
        summary = benchmark_payload.get("summary", {})
        return {
            "trend": active.get("trend", "neutral"),
            "volatility": active.get("volatility", "medium"),
            "theme": active.get("theme", "balanced"),
            "return_total": summary.get("return_total", 0.0),
            "volatility_annualized": summary.get("volatility_annualized", 0.0),
        }

    def _rsi(self, close: pd.Series, window: int) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)
        avg_gain = gain.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-12)
        return 100.0 - (100.0 / (1.0 + rs))

    def _trend_strength(self, close: pd.Series, *, window: int) -> pd.Series:
        log_close = np.log(close.replace(0, np.nan))
        x = np.arange(window, dtype=float)
        x_centered = x - x.mean()
        denom = float((x_centered ** 2).sum()) + 1e-12

        def _window_strength(values: np.ndarray) -> float:
            if np.isnan(values).any():
                return np.nan
            centered = values - values.mean()
            slope = float((x_centered * centered).sum() / denom)
            fit = values.mean() + slope * x_centered
            ss_tot = float(((values - values.mean()) ** 2).sum()) + 1e-12
            r_squared = max(0.0, min(1.0, 1.0 - float(((values - fit) ** 2).sum()) / ss_tot))
            normalized = np.tanh(slope * window * 18.0)
            return float(normalized * r_squared)

        return log_close.rolling(window).apply(_window_strength, raw=True)

    def _volatility_base(self, label: str) -> float:
        if label == "low":
            return 0.0084
        if label == "high":
            return 0.0205
        return 0.0126

    def _volume_multiplier(self, volatility_label: str) -> float:
        if volatility_label == "low":
            return 0.95
        if volatility_label == "high":
            return 1.28
        return 1.08

    def _trend_label(self, drift: float) -> str:
        if drift > 0.00032:
            return "bullish"
        if drift < -0.00020:
            return "bearish"
        return "sideways"

    def _volatility_label(self, sigma: float) -> str:
        if sigma > 0.022:
            return "high"
        if sigma < 0.010:
            return "low"
        return "medium"

    def _catalyst_text(self, profile: StockProfile, drift: float, sigma: float) -> str:
        if drift > 0.00032 and sigma < 0.015:
            return f"{profile.sector} leadership stays persistent with orderly pullbacks."
        if drift > 0.00032:
            return f"{profile.archetype.replace('_', ' ')} buyers keep chasing upside momentum."
        if drift < -0.00020 and sigma > 0.018:
            return f"Macro pressure and positioning unwind create sharp downside swings in {profile.symbol}."
        if drift < -0.00020:
            return f"Softer sponsorship keeps rallies sold in {profile.symbol}."
        return f"Cross-currents keep {profile.symbol} oscillating without a clean breakout."
