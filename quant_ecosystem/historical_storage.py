"""
Historical Data Storage System
Stores 20+ years of stock data persistently
"""

from __future__ import annotations

import logging
import json
import sqlite3
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import yfinance as yf
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class HistoricalPriceRecord:
    """Single historical price record"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    dividends: float = 0.0
    splits: float = 1.0


@dataclass
class StockDataHistory:
    """Complete stock data history"""
    symbol: str
    company_name: str
    sector: str
    industry: str
    first_recorded_date: str
    last_updated: str
    price_history: List[HistoricalPriceRecord]
    fundamental_history: List[Dict[str, Any]]
    splits_and_dividends: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class HistoricalDataStorage:
    """
    Persistent storage system for 20+ years of stock data.
    Uses SQLite for efficient storage and retrieval.
    """
    
    def __init__(self, db_path: str = "stock_data_historical.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    dividends REAL DEFAULT 0.0,
                    splits REAL DEFAULT 1.0,
                    PRIMARY KEY (symbol, date)
                )
            ''')
            
            # Fundamentals history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fundamentals_history (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    pe_ratio REAL,
                    pb_ratio REAL,
                    ps_ratio REAL,
                    market_cap REAL,
                    revenue_growth REAL,
                    earnings_growth REAL,
                    roe REAL,
                    profit_margins REAL,
                    debt_to_equity REAL,
                    current_ratio REAL,
                    employees INTEGER,
                    PRIMARY KEY (symbol, date)
                )
            ''')
            
            # Company info table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS company_info (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    sector TEXT,
                    industry TEXT,
                    country TEXT,
                    website TEXT,
                    business_summary TEXT,
                    first_recorded_date TEXT,
                    last_updated TEXT
                )
            ''')
            
            # Data collection log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    collection_date TEXT,
                    records_added INTEGER,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            # Metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            log.info(f"Database initialized: {self.db_path}")
    
    def fetch_and_store_historical_data(self, symbol: str, years: int = 20) -> bool:
        """Fetch and store up to 20 years of historical data"""
        log.info(f"Fetching {years} years of data for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch price history
            period = f"{years}y" if years <= 20 else "max"
            hist = ticker.history(period=period)
            
            if hist.empty:
                log.warning(f"No historical data available for {symbol}")
                return False
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Store price data
                    records_added = 0
                    for date, row in hist.iterrows():
                        date_str = date.strftime('%Y-%m-%d')
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO price_history 
                            (symbol, date, open, high, low, close, volume)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            symbol, date_str,
                            float(row['Open']), float(row['High']),
                            float(row['Low']), float(row['Close']),
                            int(row['Volume'])
                        ))
                        records_added += 1
                    
                    # Store company info
                    info = ticker.info
                    cursor.execute('''
                        INSERT OR REPLACE INTO company_info
                        (symbol, name, sector, industry, country, website, 
                         business_summary, first_recorded_date, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        info.get('longName', ''),
                        info.get('sector', ''),
                        info.get('industry', ''),
                        info.get('country', ''),
                        info.get('website', ''),
                        info.get('longBusinessSummary', '')[:500],
                        hist.index[0].strftime('%Y-%m-%d'),
                        datetime.now().isoformat()
                    ))
                    
                    # Log collection
                    cursor.execute('''
                        INSERT INTO collection_log 
                        (symbol, collection_date, records_added, status, error_message)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        datetime.now().isoformat(),
                        records_added,
                        'success',
                        None
                    ))
                    
                    conn.commit()
                    
            log.info(f"Stored {records_added} price records for {symbol}")
            return True
            
        except Exception as e:
            log.error(f"Error fetching historical data for {symbol}: {e}")
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO collection_log 
                        (symbol, collection_date, records_added, status, error_message)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        datetime.now().isoformat(),
                        0,
                        'error',
                        str(e)
                    ))
                    conn.commit()
            return False
    
    def get_price_history(self, symbol: str, 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         limit: int = 10000) -> pd.DataFrame:
        """Retrieve price history from storage"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM price_history WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
    
    def get_fundamental_at_date(self, symbol: str, date: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data at specific date (or nearest before)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM fundamentals_history 
                WHERE symbol = ? AND date <= ?
                ORDER BY date DESC LIMIT 1
            ''', (symbol, date))
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def store_fundamental_snapshot(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Store a fundamental data snapshot"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO fundamentals_history
                        (symbol, date, pe_ratio, pb_ratio, ps_ratio, market_cap,
                         revenue_growth, earnings_growth, roe, profit_margins,
                         debt_to_equity, current_ratio, employees)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol, date_str,
                        data.get('pe_ratio'),
                        data.get('price_to_book'),
                        data.get('price_to_sales'),
                        data.get('market_cap'),
                        data.get('revenue_growth'),
                        data.get('earnings_growth'),
                        data.get('return_on_equity'),
                        data.get('profit_margins'),
                        data.get('debt_to_equity'),
                        data.get('current_ratio'),
                        data.get('employees')
                    ))
                    
                    conn.commit()
                    return True
        except Exception as e:
            log.error(f"Error storing fundamentals for {symbol}: {e}")
            return False
    
    def calculate_technical_indicators(self, symbol: str, 
                                      period: str = "1y") -> Dict[str, Any]:
        """Calculate technical indicators from stored data"""
        df = self.get_price_history(symbol, limit=5000)
        
        if df.empty:
            return {}
        
        df = df.sort_values('date')
        df['close'] = pd.to_numeric(df['close'])
        
        # Calculate moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate volatility
        df['returns'] = df['close'].pct_change()
        df['volatility_20d'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        latest = df.iloc[-1]
        
        return {
            "current_price": latest['close'],
            "sma_20": latest['sma_20'],
            "sma_50": latest['sma_50'],
            "sma_200": latest['sma_200'],
            "rsi": latest['rsi'],
            "volatility_annual": latest['volatility_20d'],
            "trend_20d": "up" if latest['close'] > latest['sma_20'] else "down",
            "trend_50d": "up" if latest['close'] > latest['sma_50'] else "down",
            "trend_200d": "up" if latest['close'] > latest['sma_200'] else "down",
            "data_points": len(df)
        }
    
    def get_data_coverage(self, symbol: str) -> Dict[str, Any]:
        """Get data coverage statistics for a symbol"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Price records
            cursor.execute('''
                SELECT COUNT(*), MIN(date), MAX(date) 
                FROM price_history WHERE symbol = ?
            ''', (symbol,))
            
            price_count, first_date, last_date = cursor.fetchone()
            
            # Fundamental records
            cursor.execute('''
                SELECT COUNT(*), MIN(date), MAX(date)
                FROM fundamentals_history WHERE symbol = ?
            ''', (symbol,))
            
            fund_count, fund_first, fund_last = cursor.fetchone()
            
            return {
                "symbol": symbol,
                "price_records": price_count or 0,
                "price_date_range": f"{first_date} to {last_date}" if first_date else "No data",
                "fundamental_records": fund_count or 0,
                "fundamental_date_range": f"{fund_first} to {fund_last}" if fund_first else "No data",
                "years_of_data": self._calculate_years(first_date, last_date)
            }
    
    def _calculate_years(self, start_date: Optional[str], 
                        end_date: Optional[str]) -> float:
        """Calculate years between dates"""
        if not start_date or not end_date:
            return 0.0
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return (end - start).days / 365.25
        except:
            return 0.0
    
    def list_all_symbols(self) -> List[str]:
        """List all symbols in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT symbol FROM price_history ORDER BY symbol
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get database storage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total price records
            cursor.execute('SELECT COUNT(*) FROM price_history')
            stats['total_price_records'] = cursor.fetchone()[0]
            
            # Total fundamental records
            cursor.execute('SELECT COUNT(*) FROM fundamentals_history')
            stats['total_fundamental_records'] = cursor.fetchone()[0]
            
            # Unique symbols
            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM price_history')
            stats['unique_symbols'] = cursor.fetchone()[0]
            
            # Date range
            cursor.execute('SELECT MIN(date), MAX(date) FROM price_history')
            min_date, max_date = cursor.fetchone()
            stats['earliest_record'] = min_date
            stats['latest_record'] = max_date
            
            # Database file size
            try:
                size_bytes = os.path.getsize(self.db_path)
                stats['database_size_mb'] = round(size_bytes / (1024 * 1024), 2)
            except:
                stats['database_size_mb'] = 0
            
            return stats
    
    def bulk_fetch_major_stocks(self, symbols: List[str], max_workers: int = 4):
        """Bulk fetch data for major stocks"""
        from concurrent.futures import ThreadPoolExecutor
        
        log.info(f"Bulk fetching data for {len(symbols)} symbols")
        
        def fetch_single(symbol):
            return symbol, self.fetch_and_store_historical_data(symbol, years=20)
        
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, symbol): symbol for symbol in symbols}
            
            for future in futures:
                symbol = futures[future]
                try:
                    sym, success = future.result()
                    results[sym] = success
                except Exception as e:
                    log.error(f"Error fetching {symbol}: {e}")
                    results[symbol] = False
        
        success_count = sum(1 for v in results.values() if v)
        log.info(f"Bulk fetch complete: {success_count}/{len(symbols)} successful")
        
        return results


# Global storage instance
historical_storage = HistoricalDataStorage()


if __name__ == "__main__":
    # Test the storage system
    storage = HistoricalDataStorage()
    
    # Fetch AAPL data
    print("Testing historical data storage...")
    success = storage.fetch_and_store_historical_data("AAPL", years=5)
    print(f"Fetch result: {success}")
    
    # Get stats
    stats = storage.get_storage_stats()
    print(f"Storage stats: {json.dumps(stats, indent=2)}")
    
    # Get coverage for AAPL
    coverage = storage.get_data_coverage("AAPL")
    print(f"AAPL coverage: {json.dumps(coverage, indent=2)}")
