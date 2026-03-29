"""
Custom Exceptions for AI Multi-Agent Intelligence Platform
"""


class AIPLatformError(Exception):
    """Base exception for AI Platform"""
    pass


# Data Errors
class DataError(AIPLatformError):
    """Base data error"""
    pass


class DataFetchError(DataError):
    """Failed to fetch data from source"""
    pass


class DataQualityError(DataError):
    """Data quality validation failed"""
    pass


class CacheError(DataError):
    """Cache operation failed"""
    pass


# Feature Errors
class FeatureError(AIPLatformError):
    """Feature engineering error"""
    pass


class InsufficientDataError(FeatureError):
    """Not enough data to compute features"""
    pass


# ML Errors
class MLError(AIPLatformError):
    """Machine learning error"""
    pass


class ModelTrainingError(MLError):
    """Model training failed"""
    pass


class PredictionError(MLError):
    """Model prediction failed"""
    pass


# Agent Errors
class AgentError(AIPLatformError):
    """Agent system error"""
    pass


class AgentNotFoundError(AgentError):
    """Requested agent not found"""
    pass


class DebateError(AIPLatformError):
    """Debate system error"""
    pass


class ConsensusNotReachedError(DebateError):
    """Could not reach consensus"""
    pass


# Risk Errors
class RiskError(AIPLatformError):
    """Risk management error"""
    pass


class RiskViolationError(RiskError):
    """Trade violates risk rules"""
    pass


# Execution Errors
class ExecutionError(AIPLatformError):
    """Trade execution error"""
    pass


class OrderRejectedError(ExecutionError):
    """Order was rejected"""
    pass


# Backtest Errors
class BacktestError(AIPLatformError):
    """Backtesting error"""
    pass


__all__ = [
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
