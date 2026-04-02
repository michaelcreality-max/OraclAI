"""
Live Market Data Service
Fetches real-time stock data from Yahoo Finance and other sources
"""

import yfinance as yf
import pandas as pd
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import time

log = logging.getLogger(__name__)


class LiveMarketData:
    """Real-time market data from Yahoo Finance and other sources"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = 60  # Cache for 60 seconds
        self.last_update = {}
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get live stock quote from Yahoo Finance"""
        try:
            # Check cache
            now = time.time()
            if symbol in self.cache and (now - self.last_update.get(symbol, 0)) < self.cache_time:
                return self.cache[symbol]
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price data
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = info.get('previousClose', current_price)
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0
            else:
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                prev_close = info.get('previousClose')
                change = info.get('regularMarketChange', 0)
                change_pct = info.get('regularMarketChangePercent', 0)
            
            quote = {
                'symbol': symbol.upper(),
                'name': info.get('longName') or info.get('shortName'),
                'price': round(current_price, 2) if current_price else None,
                'change': round(change, 2) if change else 0,
                'change_percent': round(change_pct, 2) if change_pct else 0,
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }
            
            # Update cache
            self.cache[symbol] = quote
            self.last_update[symbol] = now
            
            return quote
            
        except Exception as e:
            log.error(f"Error fetching quote for {symbol}: {e}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get quotes for multiple stocks"""
        quotes = []
        for symbol in symbols:
            quote = self.get_stock_quote(symbol)
            if quote:
                quotes.append(quote)
        return quotes
    
    def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices"""
        indices = {
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            '^DJI': 'Dow Jones',
            '^RUT': 'Russell 2000',
            '^VIX': 'VIX'
        }
        
        results = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    prev = info.get('previousClose', price)
                    change = price - prev
                    change_pct = (change / prev * 100) if prev else 0
                else:
                    price = info.get('regularMarketPrice', 0)
                    change = info.get('regularMarketChange', 0)
                    change_pct = info.get('regularMarketChangePercent', 0)
                
                results[name] = {
                    'symbol': symbol,
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_pct, 2),
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                log.error(f"Error fetching index {symbol}: {e}")
                
        return results
    
    def get_sp500_tickers(self) -> List[str]:
        """Get S&P 500 tickers from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            df = tables[0]
            return df['Symbol'].tolist()
        except:
            # Fallback to common S&P 500 tickers
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B", "UNH", "JNJ",
                "V", "XOM", "JPM", "WMT", "MA", "PG", "CVX", "HD", "LLY", "ABBV",
                "MRK", "BAC", "KO", "PFE", "PEP", "AVGO", "TMO", "COST", "DIS", "ABT",
                "CSCO", "ACN", "VZ", "ADBE", "CRM", "DHR", "NKE", "TXN", "WFC", "BMY",
                "QCOM", "NEE", "PM", "RTX", "INTC", "HON", "UPS", "LIN", "LOW", "AMGN"
            ]


# Global instance
live_market = LiveMarketData()
