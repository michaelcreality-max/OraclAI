"""
Advanced Data Ingestion Layer
Handles multiple data sources with caching, abstraction, and quality checks
"""

from __future__ import annotations

import logging
import sqlite3
import hashlib
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import threading
import pandas as pd
import numpy as np

# Configure logging
log = logging.getLogger(__name__)


@dataclass
class UnifiedDataFormat:
    """
    Standardized data format for all market data sources.
    All data gets normalized into this structure.
    """
    symbol: str
    timestamp: datetime
    
    # Price data
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    volume: Optional[int] = None
    
    # Derived metrics
    returns: Optional[float] = None
    volatility: Optional[float] = None
    vwap: Optional[float] = None
    
    # Fundamental data
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    earnings: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # Metadata
    data_source: str = "unknown"
    data_quality_score: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'returns': self.returns,
            'volatility': self.volatility,
            'vwap': self.vwap,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
            'market_cap': self.market_cap,
            'revenue': self.revenue,
            'earnings': self.earnings,
            'dividend_yield': self.dividend_yield,
            'data_source': self.data_source,
            'data_quality_score': self.data_quality_score,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedDataFormat':
        """Create from dictionary"""
        return cls(
            symbol=data['symbol'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            open_price=data.get('open_price'),
            high_price=data.get('high_price'),
            low_price=data.get('low_price'),
            close_price=data.get('close_price'),
            volume=data.get('volume'),
            returns=data.get('returns'),
            volatility=data.get('volatility'),
            vwap=data.get('vwap'),
            pe_ratio=data.get('pe_ratio'),
            pb_ratio=data.get('pb_ratio'),
            market_cap=data.get('market_cap'),
            revenue=data.get('revenue'),
            earnings=data.get('earnings'),
            dividend_yield=data.get('dividend_yield'),
            data_source=data.get('data_source', 'unknown'),
            data_quality_score=data.get('data_quality_score', 1.0),
            last_updated=datetime.fromisoformat(data['last_updated'])
        )


class DataQualityChecker:
    """
    Validates and cleans data to ensure consistency.
    Removes missing values, checks for outliers, ensures data integrity.
    """
    
    @staticmethod
    def validate_price_data(data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean price data"""
        if data.empty:
            return data
        
        # Make a copy to avoid modifying original
        df = data.copy()
        
        # Check for required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                log.warning(f"Missing required column: {col}")
                return pd.DataFrame()
        
        # Remove rows with any missing values in price columns
        price_cols = ['open', 'high', 'low', 'close']
        df = df.dropna(subset=price_cols)
        
        # Validate price logic: high >= low, close within high/low
        invalid_mask = (
            (df['high'] < df['low']) |
            (df['close'] > df['high']) |
            (df['close'] < df['low']) |
            (df['open'] > df['high']) |
            (df['open'] < df['low'])
        )
        
        if invalid_mask.any():
            invalid_count = invalid_mask.sum()
            log.warning(f"Removing {invalid_count} rows with invalid price logic")
            df = df[~invalid_mask]
        
        # Check for negative prices
        for col in price_cols:
            negative_mask = df[col] < 0
            if negative_mask.any():
                log.warning(f"Removing {negative_mask.sum()} rows with negative {col}")
                df = df[~negative_mask]
        
        # Validate volume (should be non-negative)
        if 'volume' in df.columns:
            df['volume'] = df['volume'].clip(lower=0)
        
        # Remove outliers (>5 standard deviations from mean)
        for col in price_cols:
            if col in df.columns and len(df) > 30:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    outlier_mask = np.abs(df[col] - mean) > (5 * std)
                    if outlier_mask.any():
                        log.warning(f"Flagging {outlier_mask.sum()} outliers in {col}")
                        # Don't remove, just flag
                        df[f'{col}_is_outlier'] = outlier_mask
        
        # Ensure chronological order
        if 'timestamp' in df.columns or df.index.name == 'timestamp':
            df = df.sort_index()
        
        log.info(f"Data quality check: {len(df)} valid rows from {len(data)} total")
        return df
    
    @staticmethod
    def validate_fundamental_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate fundamental data"""
        validated = {}
        
        # Numeric fields that should be positive
        positive_fields = [
            'market_cap', 'revenue', 'earnings', 'total_assets',
            'total_debt', 'book_value', 'shares_outstanding'
        ]
        
        for key, value in data.items():
            if value is None or pd.isna(value):
                continue
            
            # Check for positive fields
            if key in positive_fields and value < 0:
                log.warning(f"Negative value for {key}: {value}, skipping")
                continue
            
            # Check for extreme outliers in ratios
            if key in ['pe_ratio', 'pb_ratio'] and value > 1000:
                log.warning(f"Suspicious {key} value: {value}, capping at 1000")
                value = 1000
            
            validated[key] = value
        
        return validated
    
    @staticmethod
    def calculate_data_quality_score(data: pd.DataFrame) -> float:
        """Calculate a quality score for the data (0-1)"""
        if data.empty:
            return 0.0
        
        scores = []
        
        # Completeness score
        completeness = 1 - (data.isna().sum().sum() / (data.shape[0] * data.shape[1]))
        scores.append(completeness * 0.4)  # 40% weight
        
        # Freshness score (if we have timestamps)
        if 'timestamp' in data.columns or isinstance(data.index, pd.DatetimeIndex):
            latest = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data['timestamp'].iloc[-1])
            age_days = (datetime.now() - latest).days
            freshness = max(0, 1 - (age_days / 30))  # Decay over 30 days
            scores.append(freshness * 0.3)  # 30% weight
        else:
            scores.append(0.3)
        
        # Consistency score (check for gaps in data)
        if len(data) > 1 and isinstance(data.index, pd.DatetimeIndex):
            # Check for gaps > 5 days
            diffs = data.index.to_series().diff().dt.days.dropna()
            if len(diffs) > 0:
                gaps = (diffs > 5).sum()
                consistency = max(0, 1 - (gaps / len(diffs)))
                scores.append(consistency * 0.3)  # 30% weight
            else:
                scores.append(0.3)
        else:
            scores.append(0.3)
        
        return sum(scores)


class DataCacheManager:
    """
    Local caching system to minimize API calls.
    Uses SQLite for persistent storage with configurable TTL.
    """
    
    def __init__(self, cache_dir: str = ".data_cache", ttl_hours: int = 6):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.lock = threading.RLock()
        
        # Initialize cache database
        self.db_path = self.cache_dir / "data_cache.db"
        self._init_cache_db()
        
        # In-memory cache for hot data
        self.memory_cache: Dict[str, Any] = {}
        self.memory_cache_ttl: Dict[str, datetime] = {}
    
    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp TEXT,
                    ttl_hours INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    symbol TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    source TEXT,
                    quality_score REAL,
                    PRIMARY KEY (symbol, date)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_date 
                ON price_data(symbol, date)
            """)
    
    def _generate_key(self, symbol: str, data_type: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        key_data = f"{symbol}:{data_type}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, symbol: str, data_type: str, params: Dict = None) -> Optional[Any]:
        """Get data from cache if available and fresh"""
        if params is None:
            params = {}
        
        cache_key = self._generate_key(symbol, data_type, params)
        
        # Check memory cache first
        with self.lock:
            if cache_key in self.memory_cache:
                if datetime.now() < self.memory_cache_ttl.get(cache_key, datetime.min):
                    log.debug(f"Memory cache hit: {cache_key}")
                    return self.memory_cache[cache_key]
        
        # Check disk cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data, timestamp, ttl_hours FROM cache WHERE key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if row:
                data, timestamp_str, ttl_hours = row
                cached_time = datetime.fromisoformat(timestamp_str)
                
                if datetime.now() - cached_time < timedelta(hours=ttl_hours):
                    log.debug(f"Disk cache hit: {cache_key}")
                    result = json.loads(data)
                    
                    # Update memory cache
                    with self.lock:
                        self.memory_cache[cache_key] = result
                        self.memory_cache_ttl[cache_key] = datetime.now() + timedelta(minutes=10)
                    
                    return result
                else:
                    # Expired
                    conn.execute("DELETE FROM cache WHERE key = ?", (cache_key,))
        
        return None
    
    def set(self, symbol: str, data_type: str, data: Any, params: Dict = None, ttl_hours: int = None):
        """Store data in cache"""
        if params is None:
            params = {}
        
        cache_key = self._generate_key(symbol, data_type, params)
        ttl = ttl_hours or self.ttl.total_seconds() / 3600
        
        # Store in memory cache
        with self.lock:
            self.memory_cache[cache_key] = data
            self.memory_cache_ttl[cache_key] = datetime.now() + timedelta(minutes=10)
        
        # Store in disk cache
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache (key, data, timestamp, ttl_hours)
                       VALUES (?, ?, ?, ?)""",
                    (cache_key, json.dumps(data), datetime.now().isoformat(), int(ttl))
                )
        except Exception as e:
            log.error(f"Failed to cache data: {e}")
    
    def get_price_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get cached price data for a symbol"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT date, open, high, low, close, volume, source, quality_score
                FROM price_data
                WHERE symbol = ? AND date >= ?
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(symbol, cutoff_date))
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                log.info(f"Retrieved {len(df)} cached price rows for {symbol}")
                return df
        
        return None
    
    def store_price_data(self, symbol: str, df: pd.DataFrame, source: str = "unknown"):
        """Store price data in cache"""
        if df.empty:
            return
        
        # Ensure index is reset for storage
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            date_col = 'index' if 'index' in df.columns else 'date'
        else:
            date_col = 'date'
        
        # Calculate quality score
        quality = DataQualityChecker.calculate_data_quality_score(df)
        
        records = []
        for _, row in df.iterrows():
            records.append((
                symbol,
                row[date_col].strftime('%Y-%m-%d') if isinstance(row[date_col], (pd.Timestamp, datetime)) else str(row[date_col]),
                float(row.get('open', 0)) if pd.notna(row.get('open')) else None,
                float(row.get('high', 0)) if pd.notna(row.get('high')) else None,
                float(row.get('low', 0)) if pd.notna(row.get('low')) else None,
                float(row.get('close', 0)) if pd.notna(row.get('close')) else None,
                int(row.get('volume', 0)) if pd.notna(row.get('volume')) else None,
                source,
                quality
            ))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO price_data 
                   (symbol, date, open, high, low, close, volume, source, quality_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records
            )
        
        log.info(f"Stored {len(records)} price rows for {symbol} from {source}")
    
    def clear_cache(self):
        """Clear all cached data"""
        with self.lock:
            self.memory_cache.clear()
            self.memory_cache_ttl.clear()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
            conn.execute("DELETE FROM price_data")
        
        log.info("Cache cleared")


class DataSourceAdapter:
    """
    Adapter for different data sources.
    Normalizes all inputs into UnifiedDataFormat.
    """
    
    def __init__(self, cache_manager: DataCacheManager):
        self.cache = cache_manager
        self.quality_checker = DataQualityChecker()
    
    def fetch_yahoo_finance(self, symbol: str, period: str = "1y") -> List[UnifiedDataFormat]:
        """Fetch and normalize data from Yahoo Finance"""
        cache_key = f"yahoo:{period}"
        
        # Check cache
        cached = self.cache.get(symbol, cache_key)
        if cached:
            return [UnifiedDataFormat.from_dict(d) for d in cached]
        
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period)
            
            if hist.empty:
                log.warning(f"No data from Yahoo Finance for {symbol}")
                return []
            
            # Validate and clean
            hist = self.quality_checker.validate_price_data(hist)
            
            if hist.empty:
                return []
            
            # Get fundamental data
            info = ticker.info
            fundamentals = {
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'market_cap': info.get('marketCap'),
                'revenue': info.get('totalRevenue'),
                'earnings': info.get('netIncomeToCommon'),
                'dividend_yield': info.get('dividendYield')
            }
            fundamentals = self.quality_checker.validate_fundamental_data(fundamentals)
            
            # Calculate quality score
            quality_score = self.quality_checker.calculate_data_quality_score(hist)
            
            # Convert to unified format
            unified_data = []
            for date, row in hist.iterrows():
                data_point = UnifiedDataFormat(
                    symbol=symbol,
                    timestamp=date,
                    open_price=row.get('open'),
                    high_price=row.get('high'),
                    low_price=row.get('low'),
                    close_price=row.get('close'),
                    volume=int(row.get('volume', 0)),
                    pe_ratio=fundamentals.get('pe_ratio'),
                    pb_ratio=fundamentals.get('pb_ratio'),
                    market_cap=fundamentals.get('market_cap'),
                    revenue=fundamentals.get('revenue'),
                    earnings=fundamentals.get('earnings'),
                    dividend_yield=fundamentals.get('dividend_yield'),
                    data_source='yahoo_finance',
                    data_quality_score=quality_score
                )
                
                # Calculate derived metrics
                if len(unified_data) > 0:
                    prev_close = unified_data[-1].close_price
                    if prev_close and data_point.close_price:
                        data_point.returns = (data_point.close_price - prev_close) / prev_close
                
                unified_data.append(data_point)
            
            # Calculate volatility (20-day rolling)
            if len(unified_data) >= 20:
                closes = [d.close_price for d in unified_data]
                returns = []
                for i in range(1, len(closes)):
                    if closes[i-1] and closes[i]:
                        returns.append((closes[i] - closes[i-1]) / closes[i-1])
                
                if len(returns) >= 20:
                    vol = np.std(returns[-20:]) * np.sqrt(252)  # Annualized
                    for d in unified_data:
                        d.volatility = vol
            
            # Calculate VWAP
            if unified_data:
                total_pv = sum(d.close_price * d.volume for d in unified_data if d.close_price and d.volume)
                total_v = sum(d.volume for d in unified_data if d.volume)
                if total_v > 0:
                    vwap = total_pv / total_v
                    for d in unified_data:
                        d.vwap = vwap
            
            # Store in cache
            self.cache.set(symbol, cache_key, [d.to_dict() for d in unified_data])
            
            # Also store in price_data table
            df = pd.DataFrame([
                {
                    'open': d.open_price,
                    'high': d.high_price,
                    'low': d.low_price,
                    'close': d.close_price,
                    'volume': d.volume
                } for d in unified_data
            ], index=[d.timestamp for d in unified_data])
            self.cache.store_price_data(symbol, df, 'yahoo_finance')
            
            log.info(f"Fetched {len(unified_data)} data points from Yahoo Finance for {symbol}")
            return unified_data
            
        except Exception as e:
            log.error(f"Yahoo Finance fetch error for {symbol}: {e}")
            return []
    
    def fetch_from_cache(self, symbol: str, days: int = 30) -> List[UnifiedDataFormat]:
        """Fetch data from local cache"""
        df = self.cache.get_price_data(symbol, days)
        
        if df is None or df.empty:
            return []
        
        unified_data = []
        for date, row in df.iterrows():
            unified_data.append(UnifiedDataFormat(
                symbol=symbol,
                timestamp=date,
                open_price=row.get('open'),
                high_price=row.get('high'),
                low_price=row.get('low'),
                close_price=row.get('close'),
                volume=int(row.get('volume', 0)),
                data_source=row.get('source', 'cache'),
                data_quality_score=row.get('quality_score', 1.0)
            ))
        
        log.info(f"Retrieved {len(unified_data)} data points from cache for {symbol}")
        return unified_data


class AdvancedDataIngestionLayer:
    """
    Main data ingestion system that orchestrates multiple sources,
    applies abstraction, caching, and quality checks.
    """
    
    def __init__(self, cache_dir: str = ".data_cache"):
        self.cache = DataCacheManager(cache_dir)
        self.adapter = DataSourceAdapter(self.cache)
        self.quality_checker = DataQualityChecker()
        
        log.info("Advanced Data Ingestion Layer initialized")
    
    def get_data(self, symbol: str, sources: List[str] = None, 
                 period: str = "1y", use_cache: bool = True) -> List[UnifiedDataFormat]:
        """
        Get unified data for a symbol from specified sources.
        Falls back through sources until data is found.
        """
        if sources is None:
            sources = ['cache', 'yahoo_finance']
        
        all_data = []
        
        for source in sources:
            try:
                if source == 'cache' and use_cache:
                    # Calculate days from period
                    days_map = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '2y': 730, '5y': 1825}
                    days = days_map.get(period, 365)
                    data = self.adapter.fetch_from_cache(symbol, days)
                    
                elif source == 'yahoo_finance':
                    data = self.adapter.fetch_yahoo_finance(symbol, period)
                else:
                    log.warning(f"Unknown data source: {source}")
                    continue
                
                if data:
                    all_data.extend(data)
                    log.info(f"Retrieved {len(data)} records from {source}")
                    
                    # If we got good data, stop trying other sources
                    if len(data) > 50:
                        break
                        
            except Exception as e:
                log.error(f"Error fetching from {source}: {e}")
                continue
        
        # Apply quality checks to combined data
        if all_data:
            # Convert to DataFrame for quality check
            df = pd.DataFrame([d.to_dict() for d in all_data])
            quality_score = self.quality_checker.calculate_data_quality_score(df)
            
            for d in all_data:
                d.data_quality_score = quality_score
            
            log.info(f"Total data points: {len(all_data)}, Quality score: {quality_score:.2f}")
        
        return all_data
    
    def get_latest_price(self, symbol: str) -> Optional[UnifiedDataFormat]:
        """Get the most recent price data for a symbol"""
        data = self.get_data(symbol, sources=['cache', 'yahoo_finance'], period='5d')
        
        if not data:
            return None
        
        # Return most recent
        return max(data, key=lambda x: x.timestamp)
    
    def get_batch_data(self, symbols: List[str], period: str = "1y") -> Dict[str, List[UnifiedDataFormat]]:
        """Get data for multiple symbols efficiently"""
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_data(symbol, period=period)
            except Exception as e:
                log.error(f"Failed to get data for {symbol}: {e}")
                results[symbol] = []
        
        return results
    
    def refresh_cache(self, symbols: List[str], period: str = "1y"):
        """Force refresh cache for specified symbols"""
        for symbol in symbols:
            try:
                # Clear cache for this symbol
                cache_key = f"yahoo:{period}"
                self.cache.set(symbol, cache_key, None, ttl_hours=0)
                
                # Re-fetch
                self.get_data(symbol, period=period, use_cache=False)
            except Exception as e:
                log.error(f"Failed to refresh {symbol}: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of the data ingestion system"""
        return {
            'cache_dir': str(self.cache.cache_dir),
            'cache_initialized': True,
            'supported_sources': ['cache', 'yahoo_finance'],
            'cache_ttl_hours': self.cache.ttl.total_seconds() / 3600,
            'timestamp': datetime.now().isoformat()
        }


# Global instance
data_ingestion_layer = AdvancedDataIngestionLayer()


if __name__ == "__main__":
    # Test the data ingestion layer
    print("Testing Advanced Data Ingestion Layer...")
    
    layer = AdvancedDataIngestionLayer()
    
    # Get data for AAPL
    data = layer.get_data("AAPL", period="1mo")
    print(f"\nRetrieved {len(data)} data points for AAPL")
    
    if data:
        latest = data[-1]
        print(f"Latest price: ${latest.close_price:.2f}")
        print(f"Volume: {latest.volume:,}")
        print(f"Quality score: {latest.data_quality_score:.2f}")
    
    # Get system status
    status = layer.get_system_status()
    print(f"\nSystem Status: {status}")
