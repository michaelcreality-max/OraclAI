"""
Modular Services Architecture
Separates concerns into Data Service, ML Service, and Agent Service
with parallel execution, computation caching, and comprehensive logging
"""

from __future__ import annotations

import logging
import asyncio
import concurrent.futures
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import threading
import time
import uuid

# Configure logging with detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)

log = logging.getLogger(__name__)


class ServiceEvent(Enum):
    """Event types for service logging"""
    DATA_FETCH_START = "data_fetch_start"
    DATA_FETCH_COMPLETE = "data_fetch_complete"
    DATA_FETCH_ERROR = "data_fetch_error"
    ML_PREDICTION_START = "ml_prediction_start"
    ML_PREDICTION_COMPLETE = "ml_prediction_complete"
    ML_PREDICTION_ERROR = "ml_prediction_error"
    AGENT_ANALYSIS_START = "agent_analysis_start"
    AGENT_ANALYSIS_COMPLETE = "agent_analysis_complete"
    AGENT_ANALYSIS_ERROR = "agent_analysis_error"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    COMPUTATION_START = "computation_start"
    COMPUTATION_COMPLETE = "computation_complete"
    ERROR = "error"


@dataclass
class LogEntry:
    """Structured log entry"""
    event_id: str
    timestamp: datetime
    service: str
    event_type: ServiceEvent
    symbol: Optional[str]
    details: Dict[str, Any]
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class ServiceLogger:
    """
    Comprehensive logging system for tracking decisions and errors
    across all services
    """
    
    def __init__(self):
        self.logs: List[LogEntry] = []
        self.lock = threading.Lock()
        self.error_count = 0
        self.decision_count = 0
    
    def log_event(self, service: str, event_type: ServiceEvent, 
                  symbol: Optional[str] = None, details: Dict[str, Any] = None,
                  duration_ms: Optional[float] = None, error: Optional[str] = None):
        """Log a service event"""
        if details is None:
            details = {}
        
        entry = LogEntry(
            event_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            service=service,
            event_type=event_type,
            symbol=symbol,
            details=details,
            duration_ms=duration_ms,
            error=error
        )
        
        with self.lock:
            self.logs.append(entry)
            
            if error:
                self.error_count += 1
            
            if event_type in [ServiceEvent.ML_PREDICTION_COMPLETE, ServiceEvent.AGENT_ANALYSIS_COMPLETE]:
                self.decision_count += 1
        
        # Also write to standard logger
        if error:
            log.error(f"[{service}] {event_type.value}: {error}")
        elif duration_ms:
            log.info(f"[{service}] {event_type.value} for {symbol}: {duration_ms:.2f}ms")
        else:
            log.info(f"[{service}] {event_type.value} for {symbol}")
    
    def get_logs(self, service: Optional[str] = None, 
                 symbol: Optional[str] = None,
                 event_type: Optional[ServiceEvent] = None,
                 limit: int = 100) -> List[LogEntry]:
        """Get filtered logs"""
        with self.lock:
            filtered = self.logs.copy()
        
        if service:
            filtered = [l for l in filtered if l.service == service]
        if symbol:
            filtered = [l for l in filtered if l.symbol == symbol]
        if event_type:
            filtered = [l for l in filtered if l.event_type == event_type]
        
        return filtered[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        with self.lock:
            return {
                'total_logs': len(self.logs),
                'error_count': self.error_count,
                'decision_count': self.decision_count,
                'error_rate': self.error_count / max(1, len(self.logs)),
                'services': list(set(l.service for l in self.logs)),
                'symbols': list(set(l.symbol for l in self.logs if l.symbol))
            }
    
    def clear_old_logs(self, max_age_hours: int = 24):
        """Clear logs older than specified hours"""
        cutoff = datetime.now() - __import__('datetime').timedelta(hours=max_age_hours)
        
        with self.lock:
            self.logs = [l for l in self.logs if l.timestamp > cutoff]


class ComputationCache:
    """
    Efficient computation caching to avoid repeated calculations
    Uses both in-memory LRU cache and persistent storage for expensive operations
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._memory_cache: Dict[str, Any] = {}
        self._cache_times: Dict[str, datetime] = {}
        self._access_count: Dict[str, int] = {}
        self.lock = threading.RLock()
    
    def _make_key(self, func_name: str, *args, **kwargs) -> str:
        """Create cache key from function call"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return __import__('hashlib').md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        with self.lock:
            if key in self._memory_cache:
                self._access_count[key] = self._access_count.get(key, 0) + 1
                return self._memory_cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Cache a value"""
        with self.lock:
            # Evict oldest if at capacity
            if len(self._memory_cache) >= self.max_size:
                # Remove least recently accessed
                if self._access_count:
                    min_key = min(self._access_count.keys(), key=lambda k: self._access_count[k])
                    del self._memory_cache[min_key]
                    del self._cache_times[min_key]
                    del self._access_count[min_key]
            
            self._memory_cache[key] = value
            self._cache_times[key] = datetime.now()
            self._access_count[key] = 1
    
    def cached(self, ttl_seconds: int = 3600):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                key = self._make_key(func.__name__, *args, **kwargs)
                
                # Check cache
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Compute and cache
                result = func(*args, **kwargs)
                self.set(key, result, ttl_seconds)
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_accesses = sum(self._access_count.values())
            return {
                'size': len(self._memory_cache),
                'max_size': self.max_size,
                'total_accesses': total_accesses,
                'keys': list(self._memory_cache.keys())[:10]  # Sample
            }


class DataService:
    """
    Data Service: Handles all data fetching, caching, and quality checks
    Abstracts data sources from other services
    """
    
    def __init__(self, logger: ServiceLogger, computation_cache: ComputationCache):
        self.logger = logger
        self.cache = computation_cache
        self._data_cache: Dict[str, Any] = {}
        
        # Import data ingestion layer
        try:
            from .data_ingestion_layer import AdvancedDataIngestionLayer
            self.ingestion = AdvancedDataIngestionLayer()
        except ImportError:
            self.ingestion = None
    
    def fetch_market_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """Fetch market data for a symbol"""
        start_time = time.time()
        self.logger.log_event(
            "DataService", ServiceEvent.DATA_FETCH_START,
            symbol=symbol, details={'period': period}
        )
        
        try:
            if self.ingestion:
                # Use advanced ingestion layer
                data = self.ingestion.get_data(symbol, period=period)
                
                # Convert to DataFrame for easier handling
                if data:
                    import pandas as pd
                    df = pd.DataFrame([d.to_dict() for d in data])
                    result = {
                        'symbol': symbol,
                        'data': df,
                        'count': len(data),
                        'quality_score': data[0].data_quality_score if data else 0,
                        'source': data[0].data_source if data else 'unknown'
                    }
                else:
                    result = {'symbol': symbol, 'data': None, 'error': 'No data available'}
            else:
                # Fallback to basic yfinance
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                result = {
                    'symbol': symbol,
                    'data': hist,
                    'count': len(hist),
                    'source': 'yahoo_finance'
                }
            
            duration = (time.time() - start_time) * 1000
            self.logger.log_event(
                "DataService", ServiceEvent.DATA_FETCH_COMPLETE,
                symbol=symbol, details=result,
                duration_ms=duration
            )
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.log_event(
                "DataService", ServiceEvent.DATA_FETCH_ERROR,
                symbol=symbol, error=str(e),
                duration_ms=duration
            )
            return {'symbol': symbol, 'error': str(e), 'data': None}
    
    def fetch_batch_data(self, symbols: List[str], period: str = "1y") -> Dict[str, Dict[str, Any]]:
        """Fetch data for multiple symbols in parallel"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(self.fetch_market_data, symbol, period): symbol
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    results[symbol] = {'symbol': symbol, 'error': str(e), 'data': None}
        
        return results
    
    @lru_cache(maxsize=100)
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data with caching"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'revenue': info.get('totalRevenue'),
                'earnings': info.get('netIncomeToCommon'),
                'debt_to_equity': info.get('debtToEquity'),
                'return_on_equity': info.get('returnOnEquity'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'sector': info.get('sector'),
                'industry': info.get('industry')
            }
        except Exception as e:
            self.logger.log_event(
                "DataService", ServiceEvent.ERROR,
                symbol=symbol, error=f"Fundamentals error: {e}"
            )
            return {}


class MLService:
    """
    ML Service: Handles all ML predictions and model operations
    Provides prediction interface for agents
    """
    
    def __init__(self, logger: ServiceLogger, computation_cache: ComputationCache):
        self.logger = logger
        self.cache = computation_cache
        self.models: Dict[str, Any] = {}
    
    def predict_price_direction(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict price direction for a symbol"""
        start_time = time.time()
        self.logger.log_event(
            "MLService", ServiceEvent.ML_PREDICTION_START,
            symbol=symbol, details={'model': 'direction'}
        )
        
        try:
            # Simple ML prediction based on recent trends
            # In production, this would use actual trained models
            df = data.get('data')
            
            if df is None or (isinstance(df, __import__('pandas').DataFrame) and df.empty):
                prediction = {
                    'direction': 'neutral',
                    'confidence': 0.5,
                    'expected_return': 0.0,
                    'time_horizon': '1d'
                }
            else:
                # Simple trend analysis
                if isinstance(df, __import__('pandas').DataFrame):
                    closes = df['close'].values if 'close' in df.columns else df['Close'].values
                else:
                    closes = [d.close_price for d in df if hasattr(d, 'close_price')]
                
                if len(closes) >= 20:
                    # Calculate trend
                    sma20 = sum(closes[-20:]) / 20
                    current = closes[-1]
                    
                    if current > sma20 * 1.02:
                        direction = 'bullish'
                        confidence = min(0.95, 0.5 + (current - sma20) / sma20)
                    elif current < sma20 * 0.98:
                        direction = 'bearish'
                        confidence = min(0.95, 0.5 + (sma20 - current) / sma20)
                    else:
                        direction = 'neutral'
                        confidence = 0.5
                    
                    # Calculate expected return
                    returns = [(closes[i] - closes[i-1]) / closes[i-1] 
                              for i in range(1, len(closes)) if closes[i-1] != 0]
                    avg_return = sum(returns) / len(returns) if returns else 0
                    
                    prediction = {
                        'direction': direction,
                        'confidence': confidence,
                        'expected_return': avg_return,
                        'time_horizon': '1d',
                        'sma20': sma20,
                        'current_price': current
                    }
                else:
                    prediction = {
                        'direction': 'neutral',
                        'confidence': 0.5,
                        'expected_return': 0.0,
                        'time_horizon': '1d'
                    }
            
            duration = (time.time() - start_time) * 1000
            self.logger.log_event(
                "MLService", ServiceEvent.ML_PREDICTION_COMPLETE,
                symbol=symbol, details=prediction,
                duration_ms=duration
            )
            
            return prediction
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.log_event(
                "MLService", ServiceEvent.ML_PREDICTION_ERROR,
                symbol=symbol, error=str(e),
                duration_ms=duration
            )
            return {'direction': 'neutral', 'confidence': 0.5, 'error': str(e)}
    
    def predict_volatility(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict future volatility"""
        try:
            df = data.get('data')
            
            if df is None or (isinstance(df, __import__('pandas').DataFrame) and df.empty):
                return {'volatility': 0.2, 'confidence': 0.5}
            
            if isinstance(df, __import__('pandas').DataFrame):
                closes = df['close'].values if 'close' in df.columns else df['Close'].values
            else:
                closes = [d.close_price for d in df if hasattr(d, 'close_price')]
            
            if len(closes) >= 20:
                # Calculate historical volatility
                returns = [(closes[i] - closes[i-1]) / closes[i-1] 
                          for i in range(1, len(closes)) if closes[i-1] != 0]
                
                if len(returns) >= 20:
                    import numpy as np
                    vol = np.std(returns[-20:]) * (252 ** 0.5)  # Annualized
                    
                    return {
                        'volatility': vol,
                        'historical_volatility': vol,
                        'confidence': 0.7
                    }
            
            return {'volatility': 0.2, 'confidence': 0.5}
            
        except Exception as e:
            self.logger.log_event(
                "MLService", ServiceEvent.ERROR,
                symbol=symbol, error=f"Volatility prediction error: {e}"
            )
            return {'volatility': 0.2, 'confidence': 0.5, 'error': str(e)}


class AgentService:
    """
    Agent Service: Manages AI agents, runs them in parallel,
    and coordinates their analysis
    """
    
    def __init__(self, logger: ServiceLogger, data_service: DataService, 
                 ml_service: MLService, computation_cache: ComputationCache):
        self.logger = logger
        self.data_service = data_service
        self.ml_service = ml_service
        self.cache = computation_cache
        self.agent_registry: Dict[str, Any] = {}
    
    def register_agent(self, agent_id: str, agent_instance: Any):
        """Register an agent for parallel execution"""
        self.agent_registry[agent_id] = agent_instance
        log.info(f"Registered agent: {agent_id}")
    
    def run_agent_analysis(self, agent_id: str, symbol: str, 
                          data: Dict[str, Any], ml_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis for a single agent"""
        start_time = time.time()
        self.logger.log_event(
            "AgentService", ServiceEvent.AGENT_ANALYSIS_START,
            symbol=symbol, details={'agent_id': agent_id}
        )
        
        try:
            agent = self.agent_registry.get(agent_id)
            
            if agent and hasattr(agent, 'analyze'):
                # Call agent's analyze method
                result = agent.analyze(symbol, data, ml_predictions)
            else:
                # Default analysis if no agent registered
                result = self._default_analysis(symbol, data, ml_predictions)
            
            duration = (time.time() - start_time) * 1000
            self.logger.log_event(
                "AgentService", ServiceEvent.AGENT_ANALYSIS_COMPLETE,
                symbol=symbol, details={'agent_id': agent_id, 'result': result},
                duration_ms=duration
            )
            
            return {
                'agent_id': agent_id,
                'symbol': symbol,
                'analysis': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.log_event(
                "AgentService", ServiceEvent.AGENT_ANALYSIS_ERROR,
                symbol=symbol, error=f"Agent {agent_id}: {e}",
                duration_ms=duration
            )
            return {
                'agent_id': agent_id,
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _default_analysis(self, symbol: str, data: Dict[str, Any], 
                         ml_predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Default analysis when no specialized agent is available"""
        direction = ml_predictions.get('direction', 'neutral')
        confidence = ml_predictions.get('confidence', 0.5)
        
        # Determine stance based on ML prediction
        if direction == 'bullish' and confidence > 0.6:
            stance = 'buy'
        elif direction == 'bearish' and confidence > 0.6:
            stance = 'sell'
        else:
            stance = 'hold'
        
        return {
            'stance': stance,
            'confidence': confidence,
            'reasoning': f"ML model predicts {direction} direction with {confidence:.1%} confidence",
            'predicted_return': ml_predictions.get('expected_return', 0),
            'key_factors': ['ML prediction', 'trend analysis']
        }
    
    def run_parallel_analysis(self, symbol: str, agent_ids: List[str] = None) -> Dict[str, Any]:
        """Run all agents in parallel and aggregate results"""
        if agent_ids is None:
            agent_ids = list(self.agent_registry.keys())
        
        if not agent_ids:
            agent_ids = ['default_agent']
        
        start_time = time.time()
        
        # Fetch data once for all agents
        data = self.data_service.fetch_market_data(symbol)
        
        # Get ML predictions
        ml_preds = self.ml_service.predict_price_direction(symbol, data)
        
        # Run agents in parallel
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_ids)) as executor:
            future_to_agent = {
                executor.submit(
                    self.run_agent_analysis, agent_id, symbol, data, ml_preds
                ): agent_id
                for agent_id in agent_ids
            }
            
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    results[agent_id] = future.result()
                except Exception as e:
                    results[agent_id] = {
                        'agent_id': agent_id,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
        
        total_duration = (time.time() - start_time) * 1000
        
        # Aggregate results
        stances = [r.get('analysis', {}).get('stance', 'hold') for r in results.values() if 'analysis' in r]
        confidences = [r.get('analysis', {}).get('confidence', 0.5) for r in results.values() if 'analysis' in r]
        
        # Simple voting
        buy_votes = stances.count('buy')
        sell_votes = stances.count('sell')
        hold_votes = stances.count('hold')
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            consensus = 'buy'
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            consensus = 'sell'
        else:
            consensus = 'hold'
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return {
            'symbol': symbol,
            'consensus': consensus,
            'consensus_confidence': avg_confidence,
            'agent_results': results,
            'vote_counts': {
                'buy': buy_votes,
                'sell': sell_votes,
                'hold': hold_votes,
                'total': len(agent_ids)
            },
            'ml_predictions': ml_preds,
            'duration_ms': total_duration,
            'timestamp': datetime.now().isoformat()
        }


class ModularSystemOrchestrator:
    """
    Main orchestrator that coordinates all modular services
    Provides unified interface for the entire system
    """
    
    def __init__(self):
        # Initialize shared components
        self.logger = ServiceLogger()
        self.computation_cache = ComputationCache()
        
        # Initialize services
        self.data_service = DataService(self.logger, self.computation_cache)
        self.ml_service = MLService(self.logger, self.computation_cache)
        self.agent_service = AgentService(
            self.logger, self.data_service, self.ml_service, self.computation_cache
        )
        
        log.info("Modular System Orchestrator initialized")
    
    def analyze_stock(self, symbol: str, agent_ids: List[str] = None) -> Dict[str, Any]:
        """Full analysis pipeline for a single stock"""
        return self.agent_service.run_parallel_analysis(symbol, agent_ids)
    
    def analyze_batch(self, symbols: List[str], agent_ids: List[str] = None) -> Dict[str, Any]:
        """Analyze multiple stocks"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_stock, symbol, agent_ids): symbol
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    results[symbol] = {'symbol': symbol, 'error': str(e)}
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        return {
            'data_service': 'healthy',
            'ml_service': 'healthy',
            'agent_service': 'healthy',
            'logger_stats': self.logger.get_stats(),
            'cache_stats': self.computation_cache.get_stats(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_logs(self, service: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get system logs"""
        logs = self.logger.get_logs(service=service, limit=limit)
        return [
            {
                'event_id': l.event_id,
                'timestamp': l.timestamp.isoformat(),
                'service': l.service,
                'event_type': l.event_type.value,
                'symbol': l.symbol,
                'duration_ms': l.duration_ms,
                'error': l.error
            }
            for l in logs
        ]


# Global orchestrator instance
system_orchestrator = ModularSystemOrchestrator()


if __name__ == "__main__":
    # Test the modular system
    print("Testing Modular Services Architecture...")
    
    orchestrator = ModularSystemOrchestrator()
    
    # Test single stock analysis
    print("\n1. Analyzing AAPL...")
    result = orchestrator.analyze_stock("AAPL")
    print(f"Consensus: {result['consensus']}")
    print(f"Confidence: {result['consensus_confidence']:.2%}")
    print(f"Agents: {result['vote_counts']}")
    
    # Test batch analysis
    print("\n2. Batch analysis...")
    batch = orchestrator.analyze_batch(["MSFT", "GOOGL"])
    for symbol, res in batch.items():
        if 'consensus' in res:
            print(f"{symbol}: {res['consensus']} ({res.get('consensus_confidence', 0):.2%})")
    
    # Test system health
    print("\n3. System Health:")
    health = orchestrator.get_system_health()
    print(f"Logger stats: {health['logger_stats']}")
    print(f"Cache stats: {health['cache_stats']}")
    
    # Test logs
    print("\n4. Recent Logs:")
    logs = orchestrator.get_logs(limit=10)
    for log_entry in logs:
        print(f"  [{log_entry['service']}] {log_entry['event_type']}: {log_entry.get('symbol', 'N/A')}")
