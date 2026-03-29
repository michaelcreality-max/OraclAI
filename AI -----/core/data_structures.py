"""
Core Data Structures for AI Multi-Agent Intelligence Platform
All dataclasses for the system
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum
import numpy as np


# ==================== ENUMS ====================

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class PositionStance(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ABSTAIN = "abstain"


class AgentType(Enum):
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    QUANTITATIVE = "quantitative"
    SENTIMENT = "sentiment"
    RISK_MANAGER = "risk_manager"


class DebateStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    HOLD = "hold"
    MARKET_BUY = "market_buy"
    MARKET_SELL = "market_sell"
    LIMIT_BUY = "limit_buy"
    LIMIT_SELL = "limit_sell"


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


# ==================== INPUT DATA ====================

@dataclass
class MarketData:
    """Raw market data from any source"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    source: str = "unknown"
    quality_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'adjusted_close': self.adjusted_close,
            'source': self.source,
            'quality_score': self.quality_score
        }


@dataclass
class FundamentalData:
    """Fundamental data for a stock"""
    symbol: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    earnings: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)


# ==================== FEATURE DATA ====================

@dataclass
class FeatureVector:
    """ML-ready features for a single timestamp"""
    symbol: str
    timestamp: datetime
    features: Dict[str, float] = field(default_factory=dict)
    feature_names: List[str] = field(default_factory=list)
    
    @property
    def values_array(self) -> np.ndarray:
        """Get features as numpy array"""
        return np.array([self.features.get(name, 0.0) for name in self.feature_names])


@dataclass 
class FeatureMatrix:
    """Batch of features for multiple timestamps/symbols"""
    symbols: List[str] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    features: np.ndarray = field(default_factory=lambda: np.array([]))
    feature_names: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.features.size == 0 and self.symbols and self.feature_names:
            self.features = np.zeros((len(self.symbols), len(self.feature_names)))
    
    def __getitem__(self, idx):
        """Allow slicing to get subset of data"""
        if isinstance(idx, slice):
            return FeatureMatrix(
                symbols=self.symbols[idx],
                timestamps=self.timestamps[idx],
                features=self.features[idx],
                feature_names=self.feature_names
            )
        elif isinstance(idx, int):
            return FeatureVector(
                symbol=self.symbols[idx],
                timestamp=self.timestamps[idx],
                features=dict(zip(self.feature_names, self.features[idx])),
                feature_names=self.feature_names
            )
        else:
            raise TypeError(f"Invalid index type: {type(idx)}")


# ==================== ML PREDICTIONS ====================

@dataclass
class ModelPrediction:
    """ML ensemble output"""
    symbol: str
    direction_prob: Dict[str, float] = field(default_factory=dict)
    expected_return: float = 0.0
    confidence: float = 0.5
    model_contributions: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def predicted_direction(self) -> str:
        """Get most likely direction"""
        if not self.direction_prob:
            return "flat"
        return max(self.direction_prob.items(), key=lambda x: x[1])[0]


@dataclass
class ModelMetrics:
    """Performance metrics for a model"""
    model_name: str
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


# ==================== SIGNALS ====================

@dataclass
class SignalReasoning:
    """Reasoning behind a signal"""
    primary_factors: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    contrarian_indicators: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    model_agreement: float = 0.5


@dataclass
class TradingSignal:
    """Actionable trading signal"""
    symbol: str
    signal: SignalType = SignalType.HOLD
    confidence: float = 0.5
    expected_return: float = 0.0
    time_horizon: str = "medium"  # short, medium, long
    reasoning: SignalReasoning = field(default_factory=SignalReasoning)
    timestamp: datetime = field(default_factory=datetime.now)
    expiry: Optional[datetime] = None
    
    def __post_init__(self):
        if self.expiry is None:
            # Default expiry: 5 days
            from datetime import timedelta
            self.expiry = self.timestamp + timedelta(days=5)


# ==================== AGENT SYSTEM ====================

@dataclass
class AgentProfile:
    """Agent configuration and stats"""
    agent_id: str
    agent_type: AgentType
    risk_tolerance: str = "medium"  # low, medium, high
    time_horizon: str = "medium"  # short, medium, long
    performance_score: float = 0.5
    win_rate: float = 0.5
    avg_return: float = 0.0
    max_drawdown: float = 0.0
    active_positions: int = 0
    current_weight: float = 0.2  # For ensemble weighting


@dataclass
class AgentPosition:
    """Individual agent's stance on a stock"""
    agent_id: str
    agent_type: AgentType
    symbol: str
    stance: PositionStance = PositionStance.HOLD
    confidence: float = 0.5
    position_size_pct: float = 0.0  # % of portfolio
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_horizon: str = "medium"
    reasoning: str = ""
    supporting_factors: List[str] = field(default_factory=list)
    opposing_factors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    risk_override: bool = False


@dataclass
class AgentArgument:
    """Argument presented by agent in debate"""
    agent_id: str
    stance: PositionStance
    thesis: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class AgentCritique:
    """Critique from one agent to another"""
    from_agent: str
    to_agent: str
    critique_type: str = "logic"  # logic, evidence, assumption
    critique_text: str = ""
    severity: str = "minor"  # minor, moderate, major


# ==================== DEBATE SYSTEM ====================

@dataclass
class DebateRound:
    """Single round of debate"""
    round_number: int
    agent_arguments: List[AgentArgument] = field(default_factory=list)
    critiques: List[AgentCritique] = field(default_factory=list)
    updated_positions: List[AgentPosition] = field(default_factory=list)
    agreement_delta: float = 0.0  # Change in agreement level
    
    @property
    def duration_seconds(self) -> float:
        # Placeholder - would track actual time
        return 60.0


@dataclass
class ConsensusResult:
    """Result of debate consensus"""
    consensus_achieved: bool = False
    consensus_level: float = 0.0  # 0-1
    dominant_stance: PositionStance = PositionStance.HOLD
    confidence: float = 0.5
    supporting_agents: List[str] = field(default_factory=list)
    opposing_agents: List[str] = field(default_factory=list)
    neutral_agents: List[str] = field(default_factory=list)
    key_reasons: List[str] = field(default_factory=list)
    dissenting_views: List[str] = field(default_factory=list)


@dataclass
class DebateSession:
    """Complete debate session"""
    session_id: str
    symbol: str
    created_at: datetime = field(default_factory=datetime.now)
    positions: List[AgentPosition] = field(default_factory=list)
    rounds: List[DebateRound] = field(default_factory=list)
    status: DebateStatus = DebateStatus.PENDING
    final_consensus: Optional[ConsensusResult] = None
    
    @property
    def current_round(self) -> int:
        return len(self.rounds)
    
    @property
    def duration_seconds(self) -> float:
        # Placeholder
        return len(self.rounds) * 60.0


# ==================== JUDGE SYSTEM ====================

@dataclass
class BestArgument:
    """Best argument selected by judge"""
    agent_id: str
    agent_type: AgentType
    thesis: str
    evidence_quality: float = 0.0
    logic_score: float = 0.0
    risk_score: float = 0.0
    track_score: float = 0.0
    persuasion_score: float = 0.0
    total_score: float = 0.0


@dataclass
class AgreementMetrics:
    """Metrics about agent agreement"""
    overall_agreement: float = 0.0
    buy_agreement: float = 0.0
    sell_agreement: float = 0.0
    hold_agreement: float = 0.0
    polarization_index: float = 0.0
    convergence_trend: str = "stable"  # improving, stable, deteriorating


@dataclass
class JudicialVerdict:
    """Final verdict from judge"""
    verdict_id: str
    session_id: str
    symbol: str
    final_stance: PositionStance = PositionStance.HOLD
    confidence: float = 0.5
    agreement_level: float = 0.0
    unanimous: bool = False
    majority_size: int = 0
    total_agents: int = 0
    selected_reasoning: Optional[BestArgument] = None
    dissenting_opinions: List[str] = field(default_factory=list)
    recommended_action: str = "hold"
    position_size_pct: float = 0.0
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    judge_duration_ms: float = 0.0


# ==================== RISK & EXECUTION ====================

@dataclass
class RiskAssessment:
    """Risk evaluation result"""
    trade_id: str = ""
    approved: bool = False
    rejection_reason: Optional[str] = None
    pre_trade_exposure: float = 0.0
    post_trade_exposure: float = 0.0
    concentration_risk: str = "low"  # low, medium, high
    correlation_risk: str = "low"
    var_impact: float = 0.0
    stop_loss_recommended: float = 0.0
    max_position_recommended: float = 0.0
    time_limit_recommended: int = 30  # days


@dataclass
class PositionLimits:
    """Position limits for a symbol"""
    symbol: str
    max_position_value: float = 0.0
    max_position_pct: float = 0.1  # 10%
    max_daily_volume_pct: float = 0.05  # 5% of avg volume
    min_liquidity_score: float = 0.5
    allowed: bool = True
    reason_if_denied: Optional[str] = None


@dataclass
class Order:
    """Trade order"""
    order_id: str
    symbol: str
    side: Side
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrderDecision:
    """Order decision from judge/verdict"""
    symbol: str
    order_type: OrderType = OrderType.HOLD
    position_size_pct: float = 0.0
    conviction: float = 0.5
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    execution_window_hours: int = 24
    constraints: Dict = field(default_factory=dict)


@dataclass
class FillResult:
    """Order fill result"""
    order_id: str
    fill_price: float
    filled_quantity: float
    commission: float
    slippage: float
    fill_time: datetime
    is_partial: bool = False


@dataclass
class TradeExecution:
    """Trade execution record with slippage"""
    symbol: str
    side: str
    shares: int
    price: float
    commission: float
    slippage: float
    timestamp: datetime
    expected_price: float
    fill_quality: str = "good"


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    exit_price: float
    entry_date: datetime
    exit_date: datetime
    realized_pnl: float = 0.0
    realized_pnl_pct: float = 0.0
    total_commission: float = 0.0
    total_slippage: float = 0.0
    exit_reason: str = "manual"  # manual, stop_loss, take_profit, system


@dataclass
class Position:
    """Current position"""
    symbol: str
    quantity: float = 0.0
    average_entry_price: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    entry_date: Optional[datetime] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


# ==================== PORTFOLIO ====================

@dataclass
class BacktestResult:
    """Complete backtest results"""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    num_trades: int = 0
    avg_trade_return: float = 0.0
    trades: List[TradeExecution] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class PortfolioState:
    """Complete portfolio snapshot"""
    cash: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    total_value: float = 0.0
    daily_pnl: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    
    @property
    def invested_value(self) -> float:
        return sum(p.market_value for p in self.positions.values())
    
    @property
    def cash_percentage(self) -> float:
        if self.total_value == 0:
            return 0.0
        return self.cash / self.total_value


@dataclass
class PortfolioRiskMetrics:
    """Portfolio risk metrics"""
    portfolio_value: float = 0.0
    cash_percentage: float = 0.0
    invested_percentage: float = 0.0
    number_of_positions: int = 0
    largest_position_pct: float = 0.0
    sector_concentration: Dict[str, float] = field(default_factory=dict)
    portfolio_beta: float = 1.0
    portfolio_volatility: float = 0.2
    value_at_risk_95: float = 0.0
    expected_shortfall: float = 0.0
    max_drawdown_current: float = 0.0
    max_drawdown_historical: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0


# ==================== PERFORMANCE ====================

@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    agent_type: AgentType
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_return_per_trade: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    current_weight: float = 0.2


@dataclass
class DebateMetrics:
    """Metrics about debate performance"""
    total_debates: int = 0
    consensus_achieved: int = 0
    consensus_rate: float = 0.0
    avg_agreement_level: float = 0.0
    avg_debate_duration_seconds: float = 0.0
    consensus_accuracy: float = 0.0  # When consensus achieved, were we right?


@dataclass
class PerformanceMetrics:
    """System-wide performance summary"""
    initial_capital: float = 100000.0
    current_capital: float = 100000.0
    total_return: float = 0.0
    cagr: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    total_trades: int = 0
    avg_trade_duration_days: float = 0.0
    avg_slippage_per_trade: float = 0.0
    avg_commission_per_trade: float = 0.0
    
    model_metrics: Dict[str, ModelMetrics] = field(default_factory=dict)
    agent_metrics: Dict[str, AgentMetrics] = field(default_factory=dict)
    debate_metrics: DebateMetrics = field(default_factory=DebateMetrics)
    
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== CACHE & CONFIG ====================

@dataclass
class CacheStatus:
    """Status of data cache"""
    cache_dir: str = ".cache"
    size_bytes: int = 0
    num_symbols: int = 0
    oldest_entry: Optional[datetime] = None
    newest_entry: Optional[datetime] = None
    hit_rate: float = 0.0


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_pct: float = 0.10  # 10%
    max_single_trade_pct: float = 0.05  # 5%
    max_sector_pct: float = 0.30  # 30%
    stop_loss_pct: float = 0.05  # 5%
    trailing_stop_pct: float = 0.08  # 8%
    max_daily_loss_pct: float = 0.02  # 2%
    max_drawdown_pct: float = 0.15  # 15%
    portfolio_beta_min: float = 0.5
    portfolio_beta_max: float = 1.5


# Export all
__all__ = [
    # Enums
    'SignalType', 'PositionStance', 'AgentType', 'DebateStatus', 
    'OrderType', 'Side',
    # Data
    'MarketData', 'FundamentalData', 'FeatureVector', 'FeatureMatrix',
    'ModelPrediction', 'ModelMetrics', 'SignalReasoning', 'TradingSignal',
    # Agents
    'AgentProfile', 'AgentPosition', 'AgentArgument', 'AgentCritique',
    # Debate
    'DebateRound', 'ConsensusResult', 'DebateSession',
    # Judge
    'BestArgument', 'AgreementMetrics', 'JudicialVerdict',
    # Risk & Execution
    'RiskAssessment', 'PositionLimits', 'Order', 'FillResult', 'Trade', 'Position',
    # Portfolio
    'PortfolioState', 'PortfolioRiskMetrics',
    # Performance
    'AgentMetrics', 'DebateMetrics', 'PerformanceMetrics',
    # Config
    'CacheStatus', 'RiskParameters'
]
