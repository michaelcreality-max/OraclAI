"""
Core module for AI Multi-Agent Intelligence Platform
"""

from .data_structures import *
from .exceptions import *

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
    'CacheStatus', 'RiskParameters',
    # Exceptions
    'AIPLatformError',
    'DataError', 'DataFetchError', 'DataQualityError', 'CacheError',
    'FeatureError', 'InsufficientDataError',
    'MLError', 'ModelTrainingError', 'PredictionError',
    'AgentError', 'AgentNotFoundError',
    'DebateError', 'ConsensusNotReachedError',
    'RiskError', 'RiskViolationError',
    'ExecutionError', 'OrderRejectedError',
    'BacktestError'
]
