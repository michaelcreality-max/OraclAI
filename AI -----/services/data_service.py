"""
DataService - Multi-source data ingestion with caching
Phase 1 Implementation
"""

import logging
import sqlite3
import hashlib
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import threading
from dataclasses import asdict

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from core.data_structures import MarketData, FundamentalData, CacheStatus
from core.exceptions import DataFetchError, DataQualityError, CacheError

log = logging.getLogger(__name__)


class DataCacheManager:
    """SQLite-based cache for market data"""
    
    def __init__(self, cache_dir: str = ".ai_platform_cache", ttl_hours: int = 6):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.lock = threading.RLock()
        
        self.db_path = self.cache_dir / "market_data.db"
        self._init_db()
        
        # In-memory cache for hot data
        self._memory_cache: Dict[str, Any] = {}
        self._memory_ttl: Dict[str, datetime] = {}
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            # OHLCV data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ohlcv_data (
                    symbol TEXT,
                    timestamp TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    adjusted_close REAL,
                    source TEXT,
                    quality_score REAL,
                    PRIMARY KEY (symbol, timestamp)
                )
            """)
            
            # Fundamental data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fundamental_data (
                    symbol TEXT PRIMARY KEY,
                    pe_ratio REAL,
                    pb_ratio REAL,
                    market_cap REAL,
                    revenue REAL,
                    earnings REAL,
                    debt_to_equity REAL,
                    roe REAL,
                    dividend_yield REAL,
                    beta REAL,
                    sector TEXT,
                    industry TEXT,
                    last_updated TEXT
                )
            """)
            
            # Metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    symbol TEXT PRIMARY KEY,
                    last_fetch TEXT,
                    data_points INTEGER,
                    source TEXT
                )
            """)
            
            conn.commit()
    
    def _generate_key(self, symbol: str, data_type: str) -> str:
        """Generate cache key"""
        key_data = f"{symbol}:{data_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_ohlcv(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Get cached OHLCV data"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT timestamp, open, high, low, close, volume, adjusted_close, quality_score
                FROM ohlcv_data
                WHERE symbol = ? AND timestamp >= ?
                ORDER BY timestamp
            """
            df = pd.read_sql_query(query, conn, params=(symbol, cutoff))
            
            if not df.empty:
                # Handle timestamp parsing safely
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    df = df.dropna(subset=['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    log.info(f"Cache hit: {len(df)} rows for {symbol}")
                    return df
                except Exception as e:
                    log.warning(f"Error parsing timestamps for {symbol}: {e}")
                    return None
        
        return None
    
    def store_ohlcv(self, symbol: str, df: pd.DataFrame, source: str = "unknown"):
        """Store OHLCV data in cache"""
        if df.empty:
            return
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(df)
        
        records = []
        for timestamp, row in df.iterrows():
            # Handle timestamp conversion
            if isinstance(timestamp, (int, float)):
                # Assume it's a timestamp index position, use dataframe index
                timestamp_str = df.index[timestamp].isoformat() if hasattr(df.index[timestamp], 'isoformat') else str(df.index[timestamp])
            elif hasattr(timestamp, 'isoformat'):
                timestamp_str = timestamp.isoformat()
            elif isinstance(timestamp, pd.Timestamp):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)
            
            records.append((
                symbol,
                timestamp_str,
                float(row.get('open', 0)),
                float(row.get('high', 0)),
                float(row.get('low', 0)),
                float(row.get('close', 0)),
                int(row.get('volume', 0)),
                float(row.get('adjusted_close', row.get('close', 0))),
                source,
                quality_score
            ))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO ohlcv_data 
                   (symbol, timestamp, open, high, low, close, volume, adjusted_close, source, quality_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records
            )
            
            # Update metadata
            conn.execute(
                """INSERT OR REPLACE INTO cache_metadata 
                   (symbol, last_fetch, data_points, source)
                   VALUES (?, ?, ?, ?)""",
                (symbol, datetime.now().isoformat(), len(records), source)
            )
            conn.commit()
        
        log.info(f"Cached {len(records)} rows for {symbol} from {source}")
    
    def get_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        """Get cached fundamental data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM fundamental_data WHERE symbol = ?",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row:
                return FundamentalData(
                    symbol=row[0],
                    pe_ratio=row[1],
                    pb_ratio=row[2],
                    market_cap=row[3],
                    revenue=row[4],
                    earnings=row[5],
                    debt_to_equity=row[6],
                    roe=row[7],
                    dividend_yield=row[8],
                    beta=row[9],
                    sector=row[10],
                    industry=row[11],
                    last_updated=datetime.fromisoformat(row[12]) if row[12] else datetime.now()
                )
        return None
    
    def store_fundamentals(self, data: FundamentalData):
        """Store fundamental data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO fundamental_data
                   (symbol, pe_ratio, pb_ratio, market_cap, revenue, earnings,
                    debt_to_equity, roe, dividend_yield, beta, sector, industry, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data.symbol,
                    data.pe_ratio,
                    data.pb_ratio,
                    data.market_cap,
                    data.revenue,
                    data.earnings,
                    data.debt_to_equity,
                    data.roe,
                    data.dividend_yield,
                    data.beta,
                    data.sector,
                    data.industry,
                    data.last_updated.isoformat()
                )
            )
            conn.commit()
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score (0-1)"""
        if df.empty:
            return 0.0
        
        scores = []
        
        # Completeness
        null_pct = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        scores.append(1 - null_pct)
        
        # Price logic check
        price_cols = ['open', 'high', 'low', 'close']
        if all(c in df.columns for c in price_cols):
            valid_prices = (
                (df['high'] >= df['low']) &
                (df['close'] <= df['high']) &
                (df['close'] >= df['low']) &
                (df['open'] <= df['high']) &
                (df['open'] >= df['low'])
            )
            scores.append(valid_prices.mean())
        
        # Volume check
        if 'volume' in df.columns:
            positive_volume = (df['volume'] >= 0).mean()
            scores.append(positive_volume)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def get_cache_status(self) -> CacheStatus:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Count symbols
            cursor = conn.execute("SELECT COUNT(DISTINCT symbol) FROM ohlcv_data")
            num_symbols = cursor.fetchone()[0]
            
            # Get file size
            size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Get date range
            cursor = conn.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM ohlcv_data"
            )
            result = cursor.fetchone()
            oldest = datetime.fromisoformat(result[0]) if result[0] else None
            newest = datetime.fromisoformat(result[1]) if result[1] else None
        
        return CacheStatus(
            cache_dir=str(self.cache_dir),
            size_bytes=size_bytes,
            num_symbols=num_symbols,
            oldest_entry=oldest,
            newest_entry=newest
        )
    
    def clear_cache(self):
        """Clear all cached data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM ohlcv_data")
            conn.execute("DELETE FROM fundamental_data")
            conn.execute("DELETE FROM cache_metadata")
            conn.commit()
        
        self._memory_cache.clear()
        self._memory_ttl.clear()
        log.info("Cache cleared")


class DataQualityChecker:
    """Validate and clean market data"""
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean OHLCV data"""
        if df.empty:
            return df
        
        original_len = len(df)
        df = df.copy()
        
        # Required columns
        required = ['open', 'high', 'low', 'close']
        for col in required:
            if col not in df.columns:
                raise DataQualityError(f"Missing required column: {col}")
        
        # Remove rows with null prices
        df = df.dropna(subset=required)
        
        # Validate price logic
        valid_mask = (
            (df['high'] >= df['low']) &
            (df['close'] <= df['high']) &
            (df['close'] >= df['low']) &
            (df['open'] <= df['high']) &
            (df['open'] >= df['low'])
        )
        
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            log.warning(f"Removing {invalid_count} rows with invalid price logic")
            df = df[valid_mask]
        
        # Check for negative prices
        for col in required:
            negative_mask = df[col] < 0
            if negative_mask.any():
                log.warning(f"Removing {negative_mask.sum()} rows with negative {col}")
                df = df[~negative_mask]
        
        # Validate volume
        if 'volume' in df.columns:
            df['volume'] = df['volume'].clip(lower=0)
        
        # Remove outliers (>5 std from mean)
        for col in required:
            if len(df) > 30:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    outlier_mask = np.abs(df[col] - mean) > (5 * std)
                    if outlier_mask.sum() > 0:
                        log.warning(f"Flagging {outlier_mask.sum()} outliers in {col}")
        
        log.info(f"Quality check: {len(df)}/{original_len} rows valid")
        return df
    
    @staticmethod
    def detect_gaps(df: pd.DataFrame, max_gap_days: int = 5) -> List[datetime]:
        """Detect gaps in time series data"""
        if len(df) < 2:
            return []
        
        gaps = []
        for i in range(1, len(df)):
            prev_date = df.index[i-1]
            curr_date = df.index[i]
            gap_days = (curr_date - prev_date).days
            
            if gap_days > max_gap_days:
                gaps.append(curr_date)
        
        return gaps


class DataService:
    """
    Centralized data service with multi-source support and caching
    """
    
    def __init__(self, cache_dir: str = ".ai_platform_cache"):
        self.cache = DataCacheManager(cache_dir)
        self.quality_checker = DataQualityChecker()
        self.sources = ['cache', 'yahoo']
        
        log.info("DataService initialized")
    
    def fetch_ohlcv(self, symbol: str, period: str = "1y", 
                    use_cache: bool = True) -> List[MarketData]:
        """
        Fetch OHLCV data for a symbol
        
        Args:
            symbol: Stock ticker symbol
            period: Data period (1mo, 3mo, 6mo, 1y, 2y, 5y)
            use_cache: Whether to use cached data
        
        Returns:
            List of MarketData objects
        """
        symbol = symbol.upper()
        
        # Map period to days
        period_days = {
            '1mo': 30, '3mo': 90, '6mo': 180,
            '1y': 365, '2y': 730, '5y': 1825
        }
        days = period_days.get(period, 365)
        
        # Try cache first
        if use_cache:
            cached_df = self.cache.get_ohlcv(symbol, days)
            if cached_df is not None and not cached_df.empty:
                return self._df_to_market_data(symbol, cached_df, "cache")
        
        # Fetch from Yahoo Finance
        if YFINANCE_AVAILABLE:
            try:
                data = self._fetch_yahoo(symbol, period)
                if data:
                    # Cache the data
                    df = self._market_data_to_df(data)
                    self.cache.store_ohlcv(symbol, df, "yahoo")
                    return data
            except Exception as e:
                log.error(f"Yahoo fetch failed for {symbol}: {e}")
        
        raise DataFetchError(f"Could not fetch data for {symbol}")
    
    def _fetch_yahoo(self, symbol: str, period: str) -> List[MarketData]:
        """Fetch from Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise DataFetchError(f"No data from Yahoo for {symbol}")
        
        # Validate
        hist = self.quality_checker.validate_ohlcv(hist)
        
        # Convert to MarketData
        market_data = []
        for timestamp, row in hist.iterrows():
            market_data.append(MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                adjusted_close=float(row.get('Adj Close', row['Close'])),
                source="yahoo",
                quality_score=0.95
            ))
        
        log.info(f"Fetched {len(market_data)} rows from Yahoo for {symbol}")
        return market_data
    
    def fetch_fundamentals(self, symbol: str, use_cache: bool = True) -> FundamentalData:
        """Fetch fundamental data for a symbol"""
        symbol = symbol.upper()
        
        # Try cache first
        if use_cache:
            cached = self.cache.get_fundamentals(symbol)
            if cached:
                # Check if fresh (< 24 hours)
                age = datetime.now() - cached.last_updated
                if age < timedelta(hours=24):
                    return cached
        
        # Fetch from Yahoo
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                fundamentals = FundamentalData(
                    symbol=symbol,
                    pe_ratio=info.get('trailingPE'),
                    pb_ratio=info.get('priceToBook'),
                    market_cap=info.get('marketCap'),
                    revenue=info.get('totalRevenue'),
                    earnings=info.get('netIncomeToCommon'),
                    debt_to_equity=info.get('debtToEquity'),
                    roe=info.get('returnOnEquity'),
                    dividend_yield=info.get('dividendYield'),
                    beta=info.get('beta'),
                    sector=info.get('sector'),
                    industry=info.get('industry'),
                    last_updated=datetime.now()
                )
                
                # Cache
                self.cache.store_fundamentals(fundamentals)
                return fundamentals
                
            except Exception as e:
                log.error(f"Fundamentals fetch failed for {symbol}: {e}")
        
        raise DataFetchError(f"Could not fetch fundamentals for {symbol}")
    
    def fetch_batch(self, symbols: List[str], period: str = "1y") -> Dict[str, List[MarketData]]:
        """Fetch data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.fetch_ohlcv(symbol, period)
            except Exception as e:
                log.error(f"Failed to fetch {symbol}: {e}")
                results[symbol] = []
        
        return results
    
    def get_cache_status(self) -> CacheStatus:
        """Get cache statistics"""
        return self.cache.get_cache_status()
    
    def refresh_cache(self, symbols: List[str], period: str = "1y"):
        """Force refresh cache for symbols"""
        for symbol in symbols:
            try:
                # Fetch without cache
                data = self.fetch_ohlcv(symbol, period, use_cache=False)
                log.info(f"Refreshed cache for {symbol}")
            except Exception as e:
                log.error(f"Failed to refresh {symbol}: {e}")
    
    def _df_to_market_data(self, symbol: str, df: pd.DataFrame, source: str) -> List[MarketData]:
        """Convert DataFrame to MarketData list"""
        market_data = []
        for timestamp, row in df.iterrows():
            market_data.append(MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open=float(row.get('open', 0)),
                high=float(row.get('high', 0)),
                low=float(row.get('low', 0)),
                close=float(row.get('close', 0)),
                volume=int(row.get('volume', 0)),
                adjusted_close=float(row.get('adjusted_close', row.get('close', 0))),
                source=source,
                quality_score=float(row.get('quality_score', 0.9))
            ))
        return market_data
    
    def _market_data_to_df(self, data: List[MarketData]) -> pd.DataFrame:
        """Convert MarketData list to DataFrame"""
        records = []
        for d in data:
            records.append({
                'open': d.open,
                'high': d.high,
                'low': d.low,
                'close': d.close,
                'volume': d.volume,
                'adjusted_close': d.adjusted_close,
                'quality_score': d.quality_score
            })
        
        df = pd.DataFrame(records)
        df.index = [d.timestamp for d in data]
        return df


# Global instance
data_service = DataService()
