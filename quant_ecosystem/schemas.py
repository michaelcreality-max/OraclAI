"""Shared dataclasses for the four-agent quantitative ecosystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MarketRegime(str, Enum):
    CRASH = "crash"
    RALLY = "rally"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


@dataclass
class AlphaHypothesis:
    """A proposed signal or feature recipe from Alpha Discovery."""

    id: str
    description: str
    feature_names: List[str]
    tags: List[str] = field(default_factory=list)
    unconventional: bool = False
    llm_rationale: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelCandidate:
    """A trained or trainable model in the arena."""

    id: str
    family: str  # e.g. xgboost, lstm, transformer, rf, mlp
    params: Dict[str, Any] = field(default_factory=dict)
    artifact: Any = None  # fitted sklearn / optional torch module
    train_score: float = 0.0
    fitness: float = 0.0
    generation: int = 0


@dataclass
class TournamentResult:
    """Outcome of model vs model comparisons."""

    winner_id: str
    loser_id: str
    metric_delta: float
    metric_name: str = "neg_mean_squared_error"


@dataclass
class BacktestConfig:
    """Strict realism knobs for Reality Check."""

    slippage_bps: float = 5.0
    commission_per_trade: float = 0.0
    latency_bars: int = 1  # shift signals forward by N bars
    position_size_fraction: float = 1.0
    annualization_factor: float = 252.0


@dataclass
class RealityReport:
    """Validation outcome: brutal skepticism in numbers."""

    hypothesis_id: str
    model_id: str
    sharpe: float
    max_drawdown: float
    turnover: float
    net_pnl_after_costs: float
    train_val_gap: float  # proxy for overfitting
    regime_scores: Dict[str, float] = field(default_factory=dict)
    passed: bool = False
    kill_reason: Optional[str] = None


@dataclass
class StrategyState:
    """Live / paper performance tracking for Meta-Learning."""

    strategy_id: str
    capital_weight: float = 0.0
    rolling_sharpe: float = 0.0
    decay_score: float = 0.0  # higher = more decay
    last_retrain: Optional[datetime] = None
    regime_history: List[str] = field(default_factory=list)


@dataclass
class EcosystemState:
    """In-memory registry the orchestrator mutates each cycle."""

    hypotheses: Dict[str, AlphaHypothesis] = field(default_factory=dict)
    models: Dict[str, ModelCandidate] = field(default_factory=dict)
    survivors: List[str] = field(default_factory=list)  # model ids that passed Reality
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    last_strategy_scores: Dict[str, float] = field(default_factory=dict)
    cycle: int = 0


@dataclass
class StockIntelSnapshot:
    """Factual market snapshot from the Stock Intel agent (observer only — no votes, no debate)."""

    symbol: str
    role: str  # always "observer"
    mandate: str
    fetched_at_utc: str
    data_sources: List[str]
    fast_metrics: Dict[str, Any]  # from yfinance fast_info + curated fields
    fundamentals: Dict[str, Any]  # whitelisted keys from ticker.info
    recent_history: Dict[str, Any]  # summary stats from recent OHLCV
    live_quote: Optional[Dict[str, Any]] = None  # optional server-side polled quote
    disclaimer: str = ""
