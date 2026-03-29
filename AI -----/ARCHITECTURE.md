# AI Multi-Agent Intelligence Platform
## System Architecture Design Document

---

## EXECUTIVE SUMMARY

A production-grade multi-agent intelligence platform combining financial analysis, machine learning, multi-agent reasoning, debate/consensus mechanisms, and adaptive learning for investment decision-making.

---

## 1. SYSTEM OVERVIEW

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE ORCHESTRATOR                          │
│                      (Central Coordination & Flow Control)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│  Data Layer  │          │   ML Layer   │          │  Agent Layer │
│              │          │              │          │              │
│ • Ingestion  │◄────────►│ • Features   │◄────────►│ • Reasoning  │
│ • Caching    │          │ • Models     │          │ • Debate     │
│ • Quality    │          │ • Signals    │          │ • Consensus  │
└──────────────┘          └──────────────┘          └──────────────┘
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION & ADAPTATION LAYER                         │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ Backtesting  │───►│   Risk Mgmt  │───►│   Trading    │───►│ Adaptive │  │
│  │   Engine     │    │    Service   │    │   Engine     │    │ Learning │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. SERVICE ARCHITECTURE

### 2.1 Service Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  DataService    │  │ FeatureService  │  │   MLService     │  │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │  │
│  │ IN:  symbols    │  │ IN:  raw_data   │  │ IN:  features   │  │
│  │ OUT: market_data│  │ OUT: features   │  │ OUT: predictions│  │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │  │
│  │ • Multi-source  │  │ • Technicals    │  │ • Linear models │  │
│  │ • Local cache   │  │ • Momentum      │  │ • Tree models   │  │
│  │ • Quality check │  │ • Volatility    │  │ • Ensembling    │  │
│  │ • Consistency   │  │ • Cross-asset   │  │ • Probabilistic │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  SignalService  │  │  AgentService   │  │  DebateService  │  │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │  │
│  │ IN:  predictions│  │ IN:  signals    │  │ IN:  positions  │  │
│  │ OUT: signals    │  │ OUT: positions  │  │ OUT: critiques  │  │
│  │ ─────────────── │  │ ─────────────── │  │ ─────────────── │  │
│  │ • BUY/SELL/HOLD │  │ • Conservative  │  │ • Multi-round   │  │
│  │ • Confidence    │  │ • Aggressive    │  │ • Critique      │  │
│  │ • Reasoning     │  │ • Quantitative  │  │ • Belief updt   │  │
│  │ • Probability   │  │ • Sentiment     │  │ • Convergence   │  │
│  └─────────────────┘  │ • Risk Manager  │  └─────────────────┘  │
│                       └─────────────────┘                       │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │  JudgeService   │  │   RiskService   │                       │
│  │ ─────────────── │  │ ─────────────── │                       │
│  │ IN:  debates    │  │ IN:  positions  │                       │
│  │ OUT: verdict    │  │ OUT: approvals  │                       │
│  │ ─────────────── │  │ ─────────────── │                       │
│  │ • Best reason   │  │ • Position size │                       │
│  │ • Agreement lvl │  │ • Stop-loss     │                       │
│  │ • Consensus     │  │ • Exposure      │                       │
│  │ • Meta-judge    │  │ • Correlation   │                       │
│  └─────────────────┘  └─────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. DETAILED SERVICE SPECIFICATIONS

### 3.1 DataService

**Purpose**: Centralized market data acquisition, caching, and quality management

**Interface**:
```python
class DataService:
    def fetch_ohlcv(self, symbols: List[str], timeframe: str) -> Dict[str, OHLCVData]
    def fetch_fundamentals(self, symbols: List[str]) -> Dict[str, FundamentalData]
    def get_cache_status(self) -> CacheStatus
    def refresh_cache(self, symbols: List[str]) -> None
```

**Internal Components**:
- `DataSourceManager`: Multiple provider adapters (Yahoo, Alpha Vantage, etc.)
- `CacheManager`: Local SQLite cache with TTL
- `QualityEngine`: Data validation, gap detection, outlier removal
- `ConsistencyChecker`: Cross-source validation

**Key Data Structures**:
```python
@dataclass
class OHLCVData:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float]
    quality_score: float  # 0-1

@dataclass
class FundamentalData:
    symbol: str
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    market_cap: Optional[float]
    revenue: Optional[float]
    earnings: Optional[float]
    debt_to_equity: Optional[float]
    roe: Optional[float]
    last_updated: datetime
```

---

### 3.2 FeatureService

**Purpose**: Transform raw market data into ML-ready features

**Interface**:
```python
class FeatureService:
    def compute_features(self, ohlcv: OHLCVData) -> FeatureVector
    def compute_batch(self, data: List[OHLCVData]) -> FeatureMatrix
    def get_feature_importance(self) -> Dict[str, float]
    def add_custom_feature(self, feature: CustomFeature) -> None
```

**Feature Categories**:

#### Trend Indicators
- SMA (10, 20, 50, 200)
- EMA (12, 26)
- MACD (12, 26, 9)
- ADX (14)
- Parabolic SAR

#### Momentum Indicators
- RSI (14)
- Stochastic (14, 3)
- Williams %R (14)
- CCI (20)
- Rate of Change (10)

#### Volatility Measures
- Bollinger Bands (20, 2)
- ATR (14)
- Keltner Channels
- Historical Volatility (20, 60)
- Parkinson Volatility

#### Cross-Asset Features
- Sector correlation
- Market beta
- Correlation to SPY/QQQ
- Relative strength vs sector

**Key Data Structures**:
```python
@dataclass
class FeatureVector:
    symbol: str
    timestamp: datetime
    trend_features: Dict[str, float]
    momentum_features: Dict[str, float]
    volatility_features: Dict[str, float]
    cross_asset_features: Dict[str, float]
    raw_values: Dict[str, float]  # Original prices/volumes

class FeatureMatrix:
    symbols: List[str]
    timestamps: List[datetime]
    features: np.ndarray  # Shape: (n_samples, n_features)
    feature_names: List[str]
```

---

### 3.3 MLService

**Purpose**: Generate predictions using ensemble of ML models

**Interface**:
```python
class MLService:
    def train_models(self, features: FeatureMatrix, labels: np.ndarray) -> TrainingResult
    def predict(self, features: FeatureVector) -> ModelPrediction
    def predict_batch(self, features: FeatureMatrix) -> List[ModelPrediction]
    def get_model_performance(self) -> Dict[str, ModelMetrics]
    def update_weights(self, performance: Dict[str, float]) -> None
```

**Model Ensemble**:

#### Linear Models
- Ridge Regression (L2 regularized)
- Elastic Net (L1 + L2)
- Logistic Regression (for direction)

#### Tree-Based Models (Lightweight)
- Random Forest (100 trees, max_depth=10)
- Gradient Boosting (XGBoost/LightGBM)
- Decision Tree (baseline)

#### Ensemble Strategy
```
Prediction = Σ(weight_i × prediction_i) / Σ(weights)

Weight Update Rule:
weight_i(t+1) = weight_i(t) × (1 + α × performance_i)
normalized to sum = 1
```

**Key Data Structures**:
```python
@dataclass
class ModelPrediction:
    symbol: str
    direction_probability: Dict[str, float]  # {'up': 0.6, 'down': 0.3, 'flat': 0.1}
    expected_return: float  # Percentage
    confidence: float  # 0-1
    model_contributions: Dict[str, float]  # {'ridge': 0.3, 'rf': 0.4, 'gb': 0.3}
    timestamp: datetime

@dataclass
class ModelMetrics:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    sharpe_ratio: float
    max_drawdown: float
    last_updated: datetime
```

---

### 3.4 SignalService

**Purpose**: Generate actionable trading signals from ML predictions

**Interface**:
```python
class SignalService:
    def generate_signal(self, prediction: ModelPrediction, 
                       context: MarketContext) -> TradingSignal
    def generate_batch(self, predictions: List[ModelPrediction]) -> List[TradingSignal]
    def get_signal_history(self, symbol: str, days: int) -> List[TradingSignal]
```

**Signal Logic**:

```
Signal Generation Rules:

IF confidence > 0.7 AND expected_return > threshold:
    IF direction_prob['up'] > 0.6:
        SIGNAL = BUY
    ELIF direction_prob['down'] > 0.6:
        SIGNAL = SELL
    ELSE:
        SIGNAL = HOLD
ELSE:
    SIGNAL = HOLD

Confidence Adjustment:
confidence = base_confidence × market_regime_factor × quality_factor
```

**Key Data Structures**:
```python
@dataclass
class TradingSignal:
    symbol: str
    signal: SignalType  # BUY, SELL, HOLD
    confidence: float  # 0-1
    expected_return: float
    time_horizon: str  # 'short', 'medium', 'long'
    reasoning: SignalReasoning
    timestamp: datetime
    expiry: datetime  # Signal valid until...

@dataclass
class SignalReasoning:
    primary_factors: List[str]  # ['momentum_breakout', 'trend_alignment']
    supporting_evidence: List[str]
    contrarian_indicators: List[str]
    risk_factors: List[str]
    model_agreement: float  # % of models agreeing
```

---

### 3.5 AgentService

**Purpose**: Host and manage specialized AI agents with different perspectives

**Interface**:
```python
class AgentService:
    def register_agent(self, agent: TradingAgent) -> None
    def dispatch_analysis(self, signal: TradingSignal) -> List[AgentPosition]
    def get_agent_profiles(self) -> List[AgentProfile]
    def update_agent_weights(self, performance: Dict[str, float]) -> None
```

**Agent Types**:

#### 1. Conservative Agent
```
Profile:
- Risk tolerance: Low
- Time horizon: Long-term (6-12 months)
- Preference: Quality, dividend, low volatility

Decision Logic:
- Only takes signals with confidence > 0.8
- Prefers stocks with PE < 25, positive FCF
- Avoids high beta stocks (>1.5)
- Position sizing: Conservative (2-3% per trade)
```

#### 2. Aggressive Agent
```
Profile:
- Risk tolerance: High
- Time horizon: Short-term (1-4 weeks)
- Preference: Momentum, growth, volatility

Decision Logic:
- Takes signals with confidence > 0.55
- Looks for breakout patterns, volume spikes
- Comfortable with high beta, momentum stocks
- Position sizing: Aggressive (5-8% per trade)
- Uses leverage in favorable conditions
```

#### 3. Quantitative Agent
```
Profile:
- Risk tolerance: Medium
- Time horizon: Medium-term (1-3 months)
- Preference: Statistical edge, mean reversion

Decision Logic:
- Evaluates statistical significance of signals
- Uses z-scores, probability distributions
- Considers market regime (bull/bear/sideways)
- Position sizing based on Kelly criterion
- Implements pairs trading logic
```

#### 4. Sentiment Agent
```
Profile:
- Risk tolerance: Medium
- Time horizon: Short to medium
- Preference: News-driven, social sentiment

Decision Logic:
- Analyzes news sentiment scores
- Monitors social media trends
- Contrarian when sentiment extreme
- Position sizing based on sentiment volatility
- Quick exits on sentiment reversal
```

#### 5. Risk Manager Agent
```
Profile:
- Role: Gatekeeper, not profit-seeker
- Risk tolerance: Ultra-low
- Time horizon: All horizons

Decision Logic:
- Evaluates portfolio-level risk
- Checks correlation, concentration
- Validates stop-loss levels
- Monitors drawdown limits
- Can veto any trade that violates risk rules
```

**Key Data Structures**:
```python
@dataclass
class AgentPosition:
    agent_id: str
    agent_type: AgentType
    symbol: str
    stance: PositionStance  # BUY, SELL, HOLD, ABSTAIN
    confidence: float
    position_size_pct: float  # % of portfolio
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    time_horizon: str
    reasoning: str
    supporting_factors: List[str]
    opposing_factors: List[str]
    timestamp: datetime

@dataclass
class AgentProfile:
    agent_id: str
    agent_type: AgentType
    risk_tolerance: str
    time_horizon: str
    performance_score: float
    win_rate: float
    avg_return: float
    max_drawdown: float
    active_positions: int
```

---

### 3.6 DebateService

**Purpose**: Facilitate structured multi-agent debate to reach consensus

**Interface**:
```python
class DebateService:
    def initiate_debate(self, positions: List[AgentPosition]) -> DebateSession
    def run_round(self, session_id: str) -> DebateRound
    def get_consensus(self, session_id: str) -> ConsensusResult
    def get_debate_history(self, session_id: str) -> List[DebateRound]
```

**Debate Structure**:

```
Round 1: Initial Positions
- Each agent presents stance and reasoning
- Duration: 1-2 minutes per agent

Round 2: Critique & Challenge
- Agents question each other's positions
- Identify weaknesses in arguments
- Duration: 2-3 minutes

Round 3: Defense & Rebuttal
- Agents defend their positions
- Address counter-arguments
- Update confidence based on critiques
- Duration: 2-3 minutes

Round 4: Belief Update
- Agents revise positions based on debate
- Can change stance, adjust confidence
- Duration: 1 minute

Termination Conditions:
- Max 4 rounds
- Early stop if consensus > 80%
- Stop if no position changes in round
```

**Key Data Structures**:
```python
@dataclass
class DebateSession:
    session_id: str
    symbol: str
    created_at: datetime
    positions: List[AgentPosition]
    rounds: List[DebateRound]
    status: DebateStatus
    final_consensus: Optional[ConsensusResult]

@dataclass
class DebateRound:
    round_number: int
    agent_arguments: List[AgentArgument]
    critiques: List[AgentCritique]
    updated_positions: List[AgentPosition]
    agreement_delta: float  # Change in agreement level

@dataclass
class AgentArgument:
    agent_id: str
    stance: PositionStance
    thesis: str  # Main argument
    evidence: List[str]
    confidence: float

@dataclass
class AgentCritique:
    from_agent: str
    to_agent: str
    critique_type: str  # 'logic', 'evidence', 'assumption'
    critique_text: str
    severity: str  # 'minor', 'moderate', 'major'

@dataclass
class ConsensusResult:
    consensus_achieved: bool
    consensus_level: float  # 0-1
    dominant_stance: PositionStance
    confidence: float
    supporting_agents: List[str]
    opposing_agents: List[str]
    neutral_agents: List[str]
    key_reasons: List[str]
    dissenting_views: List[str]
```

---

### 3.7 JudgeService

**Purpose**: Evaluate debate outcome and select best reasoning

**Interface**:
```python
class JudgeService:
    def evaluate_debate(self, session: DebateSession) -> JudicialVerdict
    def select_best_reasoning(self, arguments: List[AgentArgument]) -> BestArgument
    def compute_agreement_level(self, positions: List[AgentPosition]) -> AgreementMetrics
    def get_judge_history(self) -> List[JudicialVerdict]
```

**Judging Criteria**:

```
Evaluation Dimensions:

1. Logic & Coherence (25%)
   - Is the reasoning internally consistent?
   - Are conclusions supported by premises?

2. Evidence Quality (25%)
   - Quality of supporting data
   - Statistical significance
   - Recency and relevance

3. Risk Awareness (20%)
   - Acknowledgment of downside scenarios
   - Mitigation strategies
   - Position sizing rationale

4. Predictive Track Record (20%)
   - Agent's historical performance
   - Calibration of confidence levels
   - Win rate in similar conditions

5. Persuasiveness (10%)
   - Ability to address critiques
   - Clarity of communication
   - Response to challenges

Scoring:
Total Score = Σ(weight_i × score_i)
Best Argument = argmax(score)
```

**Key Data Structures**:
```python
@dataclass
class JudicialVerdict:
    verdict_id: str
    session_id: str
    symbol: str
    final_stance: PositionStance
    confidence: float
    agreement_level: float  # 0-1
    unanimous: bool
    majority_size: int
    total_agents: int
    
    selected_reasoning: BestArgument
    dissenting_opinions: List[str]
    
    recommended_action: str
    position_size_pct: float
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    
    timestamp: datetime
    judge_duration_ms: float

@dataclass
class BestArgument:
    agent_id: str
    agent_type: AgentType
    thesis: str
    evidence_quality: float
    logic_score: float
    risk_score: float
    track_score: float
    persuasion_score: float
    total_score: float

@dataclass
class AgreementMetrics:
    overall_agreement: float  # 0-1
    buy_agreement: float  # % of agents buying
    sell_agreement: float  # % of agents selling
    hold_agreement: float  # % of agents holding
    polarization_index: float  # How divided agents are
    convergence_trend: str  # 'improving', 'stable', 'deteriorating'
```

---

### 3.8 RiskService

**Purpose**: Portfolio-level risk management and trade validation

**Interface**:
```python
class RiskService:
    def validate_trade(self, trade: ProposedTrade, portfolio: Portfolio) -> RiskAssessment
    def calculate_portfolio_risk(self, portfolio: Portfolio) -> PortfolioRiskMetrics
    def get_position_limits(self, symbol: str) -> PositionLimits
    def check_correlation_risk(self, positions: List[Position]) -> CorrelationRisk
    def update_risk_params(self, params: RiskParameters) -> None
```

**Risk Rules**:

```
Position-Level Limits:
- Max single position: 10% of portfolio
- Max single trade: 5% of portfolio
- Max sector exposure: 30% of portfolio

Portfolio-Level Limits:
- Max drawdown: 15% from peak
- Daily loss limit: 2% of NAV
- Beta to market: 0.5 - 1.5 range
- Correlation limit: No two positions > 0.8 correlation

Stop-Loss Rules:
- Hard stop: -5% from entry
- Trailing stop: -8% from peak
- Time stop: Close if no move in 30 days

VaR Calculation:
Daily VaR (95%) = Portfolio Value × σ × 1.645
Maximum VaR: 2% of portfolio per day
```

**Key Data Structures**:
```python
@dataclass
class RiskAssessment:
    trade_id: str
    approved: bool
    rejection_reason: Optional[str]
    
    pre_trade_exposure: float
    post_trade_exposure: float
    concentration_risk: str  # 'low', 'medium', 'high'
    correlation_risk: str
    var_impact: float
    
    stop_loss_recommended: float
    max_position_recommended: float
    time_limit_recommended: int  # days

@dataclass
class PortfolioRiskMetrics:
    portfolio_value: float
    cash_percentage: float
    invested_percentage: float
    
    number_of_positions: int
    largest_position_pct: float
    sector_concentration: Dict[str, float]
    
    portfolio_beta: float
    portfolio_volatility: float
    value_at_risk_95: float
    expected_shortfall: float
    
    max_drawdown_current: float
    max_drawdown_historical: float
    
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

@dataclass
class PositionLimits:
    symbol: str
    max_position_value: float
    max_position_pct: float
    max_daily_volume_pct: float  # % of avg volume
    min_liquidity_score: float
    allowed: bool
    reason_if_denied: Optional[str]
```

---

## 4. DATA PIPELINE ARCHITECTURE

### 4.1 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA PIPELINE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ Fetch    │───►│ Validate │───►│ Transform│───►│  Cache   │             │
│   │          │    │          │    │          │    │          │             │
│   │ Multi-src│    │ Quality  │    │ Normalize│    │  Store   │             │
│   │ Priority │    │ Checks   │    │ Format   │    │  Local   │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│        │                                                           │        │
│        │         ┌──────────────────────────────────────┐           │        │
│        └────────►│        CONSISTENCY ENGINE          │◄──────────┘        │
│                  │                                     │                        │
│                  │ • Cross-source validation           │                        │
│                  │ • Timestamp alignment               │                        │
│                  │ • Missing data imputation         │                        │
│                  │ • Outlier reconciliation          │                        │
│                  └──────────────────────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Multi-Asset Support

```python
class AssetUniverse:
    """Manage multiple asset classes"""
    
    SUPPORTED_ASSETS = {
        'equities': {
            'us_stocks': ['S&P 500', 'NASDAQ 100', 'Russell 2000'],
            'international': [' Developed Markets', 'Emerging Markets'],
        },
        'etfs': {
            'equity_etfs': ['SPY', 'QQQ', 'IWM'],
            'sector_etfs': ['XLF', 'XLK', 'XLE'],
            'bond_etfs': ['TLT', 'IEF', 'LQD'],
            'commodity_etfs': ['GLD', 'USO'],
        },
        'fx': {
            'major_pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
        },
        'crypto': {
            'major': ['BTC', 'ETH', 'SOL'],
        }
    }

class CrossAssetAnalyzer:
    """Analyze relationships between assets"""
    
    def compute_correlation_matrix(self, assets: List[str]) -> pd.DataFrame
    def find_cointegrated_pairs(self, assets: List[str]) -> List[Tuple[str, str]]
    def detect_lead_lag_relationships(self, assets: List[str]) -> Dict[str, List[str]]
    def compute_market_regime(self, assets: List[str]) -> MarketRegime
```

---

## 5. MACHINE LEARNING ARCHITECTURE

### 5.1 Model Ensemble Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ML ENSEMBLE ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   INPUT: Feature Vector (50+ features)                                        │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                     FEATURE SELECTION                             │     │
│   │  • Remove highly correlated features (|r| > 0.95)               │     │
│   │  • PCA for dimensionality reduction (retain 95% variance)       │     │
│   │  • Select top 30 features by importance                         │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │    Ridge     │  │ Random Forest│  │  LightGBM    │  │   Neural     │   │
│   │ Regression   │  │  (100 trees) │  │  (500 iter)  │  │   Net (MLP)  │   │
│   │              │  │              │  │              │  │              │   │
│   │ Weight: 20%  │  │ Weight: 30% │  │ Weight: 35% │  │ Weight: 15%  │   │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│          │                 │                 │                 │          │
│          └─────────────────┴─────────────────┴─────────────────┘          │
│                                    │                                       │
│                                    ▼                                       │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │                    ENSEMBLE COMBINATION                          │   │
│   │                                                                    │   │
│   │  Method: Weighted Average with Dynamic Weights                    │   │
│   │                                                                    │   │
│   │  prediction = Σ(w_i × pred_i) / Σ(w_i)                           │   │
│   │                                                                    │   │
│   │  Weight Update: w_i ∝ exp(β × recent_accuracy_i)               │   │
│   │                                                                    │   │
│   │  Calibration: Isotonic Regression on probabilities              │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│   ┌───────────────────────────────────────────────────────────────────┐   │
│   │                      OUTPUT                                       │   │
│   │  • Direction probability (up/down/flat)                           │   │
│   │  • Expected return (%)                                          │   │
│   │  • Confidence interval (95%)                                    │   │
│   │  • Model agreement score                                          │   │
│   └───────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Adaptive Weight Update

```python
class AdaptiveEnsemble:
    """Dynamic model weight adjustment"""
    
    def update_weights(self, recent_performance: Dict[str, float]):
        """
        Update model weights based on recent performance
        
        Algorithm:
        1. Calculate accuracy over last N predictions (N=30)
        2. Compute exponential moving average of accuracy
        3. Apply softmax to get new weights
        4. Blend with previous weights (momentum=0.7)
        """
        
        # Temperature parameter for softmax
        beta = 2.0
        
        # Calculate unnormalized weights
        raw_weights = {
            model: np.exp(beta * perf)
            for model, perf in recent_performance.items()
        }
        
        # Normalize
        total = sum(raw_weights.values())
        new_weights = {model: w/total for model, w in raw_weights.items()}
        
        # Blend with old weights (momentum)
        momentum = 0.7
        for model in self.weights:
            self.weights[model] = (
                momentum * self.weights[model] + 
                (1 - momentum) * new_weights[model]
            )
        
        # Renormalize
        total = sum(self.weights.values())
        self.weights = {m: w/total for m, w in self.weights.items()}
```

---

## 6. DEBATE ENGINE ARCHITECTURE

### 6.1 Multi-Round Debate Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DEBATE ENGINE FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   START: All agents receive same signal                                     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    ROUND 1: INITIAL POSITIONS                    │     │
│   │                                                                   │     │
│   │  Conservative  │  Aggressive  │  Quantitative  │  Sentiment   │     │
│   │  ─────────────  │  ─────────── │  ───────────── │  ──────────  │     │
│   │  BUY (conf: 70) │  BUY (85)    │  HOLD (60)     │  BUY (65)    │     │
│   │  Reasoning...   │  Reasoning...│  Reasoning... │  Reasoning...│     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    ROUND 2: CRITIQUE & CHALLENGE                 │     │
│   │                                                                   │     │
│   │  Conservative ──► Aggressive: "Why such high confidence?"       │     │
│   │  Quantitative ──► Conservative: "Your entry timing seems late"  │     │
│   │  Sentiment ────► Quantitative: "Missing sentiment component"    │     │
│   │  Risk Manager ──► All: "Portfolio risk if all buy?"             │     │
│   │                                                                   │     │
│   │  [Each agent must respond to critiques]                         │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    ROUND 3: DEFENSE & REBUTTAL                   │     │
│   │                                                                   │     │
│   │  Aggressive: "High confidence due to breakout pattern + volume"   │     │
│   │  Conservative: "Late but safer entry, better R/R"                   │     │
│   │  Quantitative: "Statistical edge is marginal, hence hold"       │     │
│   │  Sentiment: "Social momentum accelerating, supporting buy"        │     │
│   │                                                                   │     │
│   │  [Confidence scores adjusted based on defense quality]          │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    ROUND 4: BELIEF UPDATE                        │     │
│   │                                                                   │     │
│   │  Conservative: Keeping BUY (70) - convinced by momentum          │     │
│   │  Aggressive: Keeping BUY (90) - even more confident              │     │
│   │  Quantitative: Changed to BUY (55) - momentum changed stats     │     │
│   │  Sentiment: Keeping BUY (70) - sentiment improving               │     │
│   │  Risk Manager: Conditional BUY - with 3% position limit          │     │
│   │                                                                   │     │
│   │  Consensus: BUY (4/5 agents, avg conf: 71%)                      │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                        JUDGE EVALUATION                          │     │
│   │                                                                   │     │
│   │  • Select best reasoning: Aggressive (strongest evidence)        │     │
│   │  • Agreement level: 80% (high consensus)                       │     │
│   │  • Recommended action: BUY with 4% position size               │     │
│   │  • Stop loss: -5%, Take profit: +15%                            │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                        RISK VALIDATION                           │     │
│   │                                                                   │     │
│   │  • Check: Within position limits? ✓                              │     │
│   │  • Check: Portfolio exposure OK? ✓                               │     │
│   │  • Check: Stop loss acceptable? ✓                                │     │
│   │  • Check: Correlation risk low? ✓                                │     │
│   │                                                                   │     │
│   │  APPROVED → Execute Order                                        │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. BACKTESTING ARCHITECTURE

### 7.1 Simulation Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BACKTESTING FRAMEWORK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   INPUT: Historical Data + Signal History                                   │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    MARKET SIMULATOR                                │     │
│   │                                                                   │     │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │     │
│   │  │   Price      │  │   Volume     │  │   Volatility │            │     │
│   │  │   Engine     │  │   Model      │  │   Regime     │            │     │
│   │  │              │  │              │  │              │            │     │
│   │  │ • OHLC data  │  │ • Impact on  │  │ • GARCH      │            │     │
│   │  │ • Gaps/jumps │  │   slippage   │  │   models     │            │     │
│   │  │ • Limit hit  │  │ • Liquidity  │  │ • Regime     │            │     │
│   │  │              │  │   constraints│  │   switch     │            │     │
│   │  └──────────────┘  └──────────────┘  └──────────────┘            │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    EXECUTION SIMULATOR                           │     │
│   │                                                                   │     │
│   │  SLIPPAGE MODEL:                                                  │     │
│   │  ─────────────────                                                │     │
│   │  slippage = base_slippage × volatility_factor × size_factor      │     │
│   │                                                                   │     │
│   │  • Base: 5 bps (0.05%)                                           │     │
│   │  • Vol factor: 1x (normal), 1.5x (elevated), 3x (extreme)       │     │
│   │  • Size factor: 1x (<1% vol), 1.2x (1-5%), 1.5x (5-10%), 2x (>10%)│     │
│   │                                                                   │     │
│   │  DELAY MODEL:                                                     │     │
│   │  ────────────                                                     │     │
│   │  • Market orders: 1-2 seconds                                     │     │
│   │  • Limit orders: 0-30 seconds (or unfilled)                     │     │
│   │  • Stop orders: Instant when triggered                          │     │
│   │                                                                   │     │
│   │  PARTIAL FILLS:                                                   │     │
│   │  • Orders > 10% of daily volume: 70-95% fill rate                │     │
│   │  • Orders > 20% of daily volume: 50-80% fill rate                │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    PORTFOLIO TRACKER                               │     │
│   │                                                                   │     │
│   │  Tracks: Cash, Positions, PnL, Drawdown, Exposure               │     │
│   │                                                                   │     │
│   │  Metrics calculated daily:                                      │     │
│   │  • Return, Volatility, Sharpe, Sortino, MaxDD                    │     │
│   │  • Win rate, Profit factor, Average win/loss                    │     │
│   │  • Beta, Alpha, Information ratio                              │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                       OUTPUT METRICS                             │     │
│   │                                                                   │     │
│   │  Performance Summary:                                             │     │
│   │  • Total Return, CAGR, Volatility, Sharpe, Max Drawdown          │     │
│   │  • Win Rate, Profit Factor, Calmar Ratio                        │     │
│   │                                                                   │     │
│   │  Trade Statistics:                                                │     │
│   │  • # Trades, Avg duration, Avg slippage, Avg commission         │     │
│   │  • Best trade, Worst trade, Avg trade PnL                       │     │
│   │                                                                   │     │
│   │  Risk Metrics:                                                    │     │
│   │  • VaR, Expected Shortfall, Beta, Correlation matrix             │     │
│   │  • Position sizing efficiency, Stop loss effectiveness         │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Realistic Trading Conditions

```python
class RealisticExecution:
    """Simulates real-world trading frictions"""
    
    # Commission structure (per share)
    COMMISSION_PER_SHARE = 0.005  # $0.005
    MIN_COMMISSION = 1.00  # $1 minimum
    MAX_COMMISSION_PCT = 0.01  # 1% of trade value
    
    # Slippage parameters
    BASE_SLIPPAGE_BPS = 5  # 5 basis points
    
    def calculate_slippage(self, 
                          order_size: float,
                          avg_daily_volume: float,
                          volatility: float,
                          order_type: OrderType) -> float:
        """
        Realistic slippage calculation
        """
        # Base slippage
        slippage = self.BASE_SLIPPAGE_BPS / 10000
        
        # Volatility adjustment
        if volatility > 0.50:  # >50% annualized
            slippage *= 3.0
        elif volatility > 0.30:
            slippage *= 1.5
        
        # Size adjustment
        if avg_daily_volume > 0:
            volume_pct = order_size / avg_daily_volume
            if volume_pct > 0.20:
                slippage *= 2.0
            elif volume_pct > 0.10:
                slippage *= 1.5
            elif volume_pct > 0.05:
                slippage *= 1.2
        
        # Order type adjustment
        if order_type == OrderType.LIMIT:
            slippage *= 0.5  # Better execution with limits
        
        return slippage
    
    def simulate_fill(self, 
                     order: Order,
                     market_data: MarketData) -> FillResult:
        """
        Simulate order fill with realistic conditions
        """
        # Calculate fill price with slippage
        slippage = self.calculate_slippage(
            order.quantity,
            market_data.avg_volume_30d,
            market_data.volatility_20d,
            order.order_type
        )
        
        # Apply slippage (always against the trader)
        if order.side == Side.BUY:
            fill_price = market_data.current_price * (1 + slippage)
        else:
            fill_price = market_data.current_price * (1 - slippage)
        
        # Calculate commission
        commission = max(
            self.MIN_COMMISSION,
            min(
                order.quantity * self.COMMISSION_PER_SHARE,
                fill_price * order.quantity * self.MAX_COMMISSION_PCT
            )
        )
        
        # Simulate partial fills for large orders
        fill_ratio = self._calculate_fill_ratio(
            order.quantity,
            market_data.avg_volume_30d,
            order.order_type
        )
        
        filled_quantity = order.quantity * fill_ratio
        
        # Simulate execution delay
        delay_seconds = self._calculate_delay(order.order_type)
        fill_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        return FillResult(
            order_id=order.id,
            fill_price=fill_price,
            filled_quantity=filled_quantity,
            commission=commission,
            slippage=slippage,
            fill_time=fill_time,
            is_partial=(fill_ratio < 1.0)
        )
```

---

## 8. ADAPTIVE LEARNING ARCHITECTURE

### 8.1 Performance Tracking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ADAPTIVE LEARNING SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    PERFORMANCE TRACKER                           │     │
│   │                                                                   │     │
│   │  Tracks at multiple levels:                                       │     │
│   │                                                                   │     │
│   │  1. SIGNAL LEVEL                                                   │     │
│   │     • Predicted direction vs actual                               │     │
│   │     • Confidence calibration (is confident → accurate?)         │     │
│   │     • Return prediction accuracy                                  │     │
│   │                                                                   │     │
│   │  2. AGENT LEVEL                                                    │     │
│   │     • Win rate per agent                                          │     │
│   │     • Average return per agent                                    │     │
│   │     • Maximum drawdown per agent                                  │     │
│   │     • Belief accuracy (does their thesis hold?)                 │     │
│   │                                                                   │     │
│   │  3. DEBATE LEVEL                                                   │     │
│   │     • Consensus accuracy (when agree, are they right?)           │     │
│   │     • Dissent accuracy (when disagree, who was right?)          │     │
│   │     • Judge selection quality                                     │     │
│   │                                                                   │     │
│   │  4. MODEL LEVEL                                                    │     │
│   │     • ML model accuracy over time                                 │     │
│   │     • Feature importance stability                                │     │
│   │     • Prediction calibration                                      │     │
│   │                                                                   │     │
│   │  5. SYSTEM LEVEL                                                   │     │
│   │     • Overall portfolio return                                    │     │
│   │     • Risk-adjusted returns                                       │     │
│   │     • Trade efficiency                                            │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    WEIGHT ADJUSTMENT ENGINE                        │     │
│   │                                                                   │     │
│   │  Update Rules:                                                    │     │
│   │                                                                   │     │
│   │  1. ML Model Weights:                                            │     │
│   │     weight_i(t+1) = weight_i(t) × exp(α × accuracy_i)           │     │
│   │     where α = 2.0 (learning rate)                                  │     │
│   │     Then normalize to sum = 1                                   │     │
│   │                                                                   │     │
│   │  2. Agent Weights:                                                │     │
│   │     weight_i(t+1) = weight_i(t) × (1 + β × sharpe_i)            │     │
│   │     where β = 0.5                                                │     │
│   │     Momentum factor: 0.7 (blend old and new)                    │     │
│   │                                                                   │     │
│   │  3. Feature Weights:                                              │     │
│   │     Update based on feature importance stability                 │     │
│   │     Drop features with importance < 1% for 30 days             │     │
│   │     Add new features based on correlation analysis               │     │
│   │                                                                   │     │
│   │  4. Signal Thresholds:                                            │     │
│   │     If too many false positives: increase confidence threshold  │     │
│   │     If missing opportunities: decrease confidence threshold    │     │
│   │     Adaptive range: 0.55 - 0.80                                   │     │
│   │                                                                   │     │
│   │  Update Frequency:                                               │     │
│   │  • Daily: Performance tracking                                    │     │
│   │  • Weekly: Weight adjustments                                     │     │
│   │  • Monthly: Model retraining                                      │     │
│   │  • Quarterly: Architecture review                                │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                    META-LEARNING LAYER                           │     │
│   │                                                                   │     │
│   │  Detect when to:                                                  │     │
│   │                                                                   │     │
│   │  • Retrain models (performance degradation > 10%)                 │     │
│   │  • Add new agents (current agents missing opportunities)         │     │
│   │  • Change debate format (consensus too low or too high)          │     │
│   │  • Adjust risk parameters (drawdown approaching limit)          │     │
│   │                                                                   │     │
│   │  Market Regime Detection:                                         │     │
│   │  • Bull market: Favor momentum agents                            │     │
│   │  • Bear market: Favor conservative agents                        │     │
│   │  • Volatile: Reduce position sizes                              │     │
│   │  • Low vol: Increase position sizes                             │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Meta-Learning Rules

```python
class MetaLearningEngine:
    """High-level system adaptation"""
    
    ADAPTATION_RULES = {
        # ML Performance
        'ml_accuracy_drop': {
            'condition': 'accuracy_30d < accuracy_90d * 0.9',
            'action': 'trigger_model_retraining',
            'priority': 'high'
        },
        
        # Agent Performance
        'agent_underperformance': {
            'condition': 'agent_sharpe < 0.5 for 60 days',
            'action': 'reduce_agent_weight_by_50%',
            'priority': 'medium'
        },
        
        # Debate Quality
        'low_consensus_accuracy': {
            'condition': 'consensus_accuracy < 0.55 for 30 days',
            'action': 'increase_debate_rounds_or_add_agents',
            'priority': 'high'
        },
        
        # Market Regime
        'high_volatility_regime': {
            'condition': 'vix > 30 for 5 consecutive days',
            'action': [
                'reduce_position_sizes_by_30%',
                'tighten_stop_losses',
                'favor_conservative_agents'
            ],
            'priority': 'urgent'
        },
        
        # Risk Management
        'approaching_drawdown_limit': {
            'condition': 'current_drawdown > 0.7 * max_allowed',
            'action': [
                'halt_new_trades',
                'reduce_existing_positions',
                'emergency_review'
            ],
            'priority': 'urgent'
        },
        
        # Signal Quality
        'overconfidence': {
            'condition': 'calibration_error > 0.1',
            'action': 'adjust_confidence_thresholds',
            'priority': 'medium'
        }
    }
    
    def evaluate_and_adapt(self):
        """
        Run all adaptation rules and apply necessary changes
        """
        for rule_name, rule in self.ADAPTATION_RULES.items():
            if self.evaluate_condition(rule['condition']):
                self.execute_action(rule['action'], rule['priority'])
```

---

## 9. KEY DATA STRUCTURES SUMMARY

### 9.1 Core Data Types

```python
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
    source: str
    quality_score: float

@dataclass
class FeatureVector:
    """ML-ready features"""
    symbol: str
    timestamp: datetime
    features: Dict[str, float]  # 50+ features
    feature_names: List[str]

@dataclass
class ModelPrediction:
    """ML ensemble output"""
    symbol: str
    direction_prob: Dict[str, float]  # {'up': 0.6, 'down': 0.3, 'flat': 0.1}
    expected_return: float
    confidence: float
    model_weights: Dict[str, float]
    timestamp: datetime

# ==================== SIGNALS ====================

@dataclass
class TradingSignal:
    """Actionable trading signal"""
    symbol: str
    signal: SignalType  # BUY, SELL, HOLD
    confidence: float
    expected_return: float
    time_horizon: str
    reasoning: SignalReasoning
    timestamp: datetime

# ==================== AGENT SYSTEM ====================

@dataclass
class AgentPosition:
    """Individual agent's stance"""
    agent_id: str
    agent_type: AgentType
    symbol: str
    stance: PositionStance
    confidence: float
    position_size_pct: float
    reasoning: str
    supporting_factors: List[str]
    opposing_factors: List[str]

@dataclass
class DebateSession:
    """Multi-round debate state"""
    session_id: str
    symbol: str
    rounds: List[DebateRound]
    final_consensus: ConsensusResult
    status: DebateStatus

@dataclass
class ConsensusResult:
    """Debate outcome"""
    consensus_achieved: bool
    consensus_level: float
    dominant_stance: PositionStance
    supporting_agents: List[str]
    opposing_agents: List[str]

# ==================== JUDGE SYSTEM ====================

@dataclass
class JudicialVerdict:
    """Final decision"""
    verdict_id: str
    symbol: str
    final_stance: PositionStance
    confidence: float
    agreement_level: float
    recommended_action: str
    position_size_pct: float
    stop_loss_pct: Optional[float]

# ==================== RISK & EXECUTION ====================

@dataclass
class RiskAssessment:
    """Risk evaluation result"""
    approved: bool
    rejection_reason: Optional[str]
    max_position_pct: float
    stop_loss_recommended: float
    var_impact: float

@dataclass
class Trade:
    """Executed trade record"""
    trade_id: str
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    exit_price: float
    realized_pnl: float
    total_costs: float  # commission + slippage
    exit_reason: str

@dataclass
class PortfolioState:
    """Complete portfolio snapshot"""
    cash: float
    positions: Dict[str, Position]
    total_value: float
    daily_pnl: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float

# ==================== PERFORMANCE ====================

@dataclass
class PerformanceMetrics:
    """System performance summary"""
    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    model_metrics: Dict[str, ModelMetrics]
    agent_metrics: Dict[str, AgentMetrics]
    debate_metrics: DebateMetrics
```

---

## 10. IMPLEMENTATION PLAN

### Phase 1: Foundation (Week 1-2)
1. Set up project structure
2. Implement DataService with caching
3. Build FeatureService with core indicators
4. Create basic test suite

### Phase 2: ML Layer (Week 3-4)
1. Implement MLService with ensemble
2. Build SignalService
3. Add model training pipeline
4. Create backtesting framework basics

### Phase 3: Agent System (Week 5-6)
1. Implement 5 agent types
2. Build AgentService
3. Create DebateService with multi-round logic
4. Implement JudgeService

### Phase 4: Execution & Risk (Week 7)
1. Build RiskService
2. Implement realistic execution simulator
3. Add backtesting with slippage/commissions
4. Create performance tracking

### Phase 5: Integration & Adaptation (Week 8)
1. Build orchestration layer
2. Implement adaptive learning
3. Add meta-learning rules
4. Performance optimization

### Phase 6: Testing & Deployment (Week 9-10)
1. Comprehensive testing
2. Paper trading simulation
3. API development
4. Documentation

---

## 11. DIRECTORY STRUCTURE

```
AI -----/
│
├── core/
│   ├── __init__.py
│   ├── data_structures.py      # All dataclasses
│   ├── enums.py                # Enums and constants
│   └── exceptions.py           # Custom exceptions
│
├── services/
│   ├── __init__.py
│   ├── data_service.py         # DataService
│   ├── feature_service.py      # FeatureService
│   ├── ml_service.py           # MLService
│   ├── signal_service.py       # SignalService
│   ├── agent_service.py        # AgentService
│   ├── debate_service.py       # DebateService
│   ├── judge_service.py        # JudgeService
│   └── risk_service.py         # RiskService
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Abstract base class
│   ├── conservative_agent.py
│   ├── aggressive_agent.py
│   ├── quantitative_agent.py
│   ├── sentiment_agent.py
│   └── risk_manager_agent.py
│
├── ml/
│   ├── __init__.py
│   ├── models/
│   │   ├── linear_models.py
│   │   ├── tree_models.py
│   │   └── ensemble.py
│   ├── features/
│   │   ├── technical.py
│   │   ├── momentum.py
│   │   └── volatility.py
│   └── training/
│       ├── trainer.py
│       └── cross_validation.py
│
├── debate/
│   ├── __init__.py
│   ├── debate_engine.py
│   ├── critique_engine.py
│   └── consensus_calculator.py
│
├── backtest/
│   ├── __init__.py
│   ├── simulator.py
│   ├── execution_model.py
│   └── performance_analyzer.py
│
├── adaptation/
│   ├── __init__.py
│   ├── performance_tracker.py
│   ├── weight_adjuster.py
│   └── meta_learning.py
│
├── utils/
│   ├── __init__.py
│   ├── cache.py
│   ├── logging.py
│   └── validators.py
│
├── tests/
│   ├── test_data_service.py
│   ├── test_ml_service.py
│   ├── test_agents.py
│   ├── test_debate.py
│   └── test_integration.py
│
├── config/
│   ├── default.yaml
│   └── agents.yaml
│
├── main.py                     # Entry point
├── orchestrator.py             # System orchestration
└── requirements.txt
```

---

## SUMMARY

This architecture provides:

✅ **8 Modular Services** - Clear interfaces, independently testable
✅ **Multi-Source Data Pipeline** - Cached, validated, consistent
✅ **Advanced Feature Engineering** - Technical, momentum, volatility, cross-asset
✅ **ML Ensemble** - Linear + tree-based with adaptive weighting
✅ **Probabilistic Signals** - BUY/SELL/HOLD with confidence
✅ **5 Agent Types** - Conservative, Aggressive, Quantitative, Sentiment, Risk Manager
✅ **Multi-Round Debate** - Critique, defense, belief updating
✅ **Judge System** - Best reasoning selection, consensus scoring
✅ **Realistic Backtesting** - Slippage, commissions, partial fills
✅ **Adaptive Learning** - Weight adjustment, meta-learning rules

Ready for implementation phase.
