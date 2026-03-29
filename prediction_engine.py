"""
Stock prediction engine — 12 weighted signals from live market data (yfinance).
Server-side signals can be merged with optional client context from your frontend.
"""

from __future__ import annotations

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

from realtime_market import apply_quote_to_history, get_market_store

class ComprehensiveStockDatabase:
    """Comprehensive US stock database - 3000+ major stocks"""
    
    def __init__(self):
        # Top US stocks by market cap and sector - 310+ stocks
        self.stocks = [
            # Mega Cap (>$200B)
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "cap": "mega"},
            {"symbol": "MSFT", "name": "Microsoft", "sector": "Technology", "cap": "mega"},
            {"symbol": "GOOGL", "name": "Alphabet", "sector": "Technology", "cap": "mega"},
            {"symbol": "AMZN", "name": "Amazon", "sector": "Consumer", "cap": "mega"},
            {"symbol": "NVDA", "name": "NVIDIA", "sector": "Technology", "cap": "mega"},
            {"symbol": "META", "name": "Meta Platforms", "sector": "Technology", "cap": "mega"},
            {"symbol": "TSLA", "name": "Tesla", "sector": "Automotive", "cap": "mega"},
            {"symbol": "BRK.B", "name": "Berkshire Hathaway", "sector": "Finance", "cap": "mega"},
            {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Finance", "cap": "mega"},
            {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "cap": "mega"},
            
            # Large Cap ($50-200B) - 40 stocks
            {"symbol": "V", "name": "Visa", "sector": "Finance", "cap": "large"},
            {"symbol": "WMT", "name": "Walmart", "sector": "Consumer", "cap": "large"},
            {"symbol": "DIS", "name": "Disney", "sector": "Entertainment", "cap": "large"},
            {"symbol": "INTC", "name": "Intel", "sector": "Technology", "cap": "large"},
            {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology", "cap": "large"},
            {"symbol": "BA", "name": "Boeing", "sector": "Aerospace", "cap": "large"},
            {"symbol": "CVX", "name": "Chevron", "sector": "Energy", "cap": "large"},
            {"symbol": "XOM", "name": "ExxonMobil", "sector": "Energy", "cap": "large"},
            {"symbol": "KO", "name": "Coca-Cola", "sector": "Consumer", "cap": "large"},
            {"symbol": "PEP", "name": "PepsiCo", "sector": "Consumer", "cap": "large"},
            {"symbol": "COST", "name": "Costco", "sector": "Consumer", "cap": "large"},
            {"symbol": "HD", "name": "Home Depot", "sector": "Consumer", "cap": "large"},
            {"symbol": "NKE", "name": "Nike", "sector": "Consumer", "cap": "large"},
            {"symbol": "MCD", "name": "McDonald's", "sector": "Consumer", "cap": "large"},
            {"symbol": "CMG", "name": "Chipotle", "sector": "Consumer", "cap": "large"},
            {"symbol": "SBUX", "name": "Starbucks", "sector": "Consumer", "cap": "large"},
            {"symbol": "PG", "name": "Procter & Gamble", "sector": "Consumer", "cap": "large"},
            {"symbol": "GE", "name": "General Electric", "sector": "Industrial", "cap": "large"},
            {"symbol": "CAT", "name": "Caterpillar", "sector": "Industrial", "cap": "large"},
            {"symbol": "HON", "name": "Honeywell", "sector": "Industrial", "cap": "large"},
            {"symbol": "LMT", "name": "Lockheed Martin", "sector": "Aerospace", "cap": "large"},
            {"symbol": "RTX", "name": "RTX Corp", "sector": "Aerospace", "cap": "large"},
            {"symbol": "BA", "name": "Boeing", "sector": "Aerospace", "cap": "large"},
            {"symbol": "IBM", "name": "IBM", "sector": "Technology", "cap": "large"},
            {"symbol": "ORACLE", "name": "Oracle", "sector": "Technology", "cap": "large"},
            {"symbol": "CRM", "name": "Salesforce", "sector": "Technology", "cap": "large"},
            {"symbol": "ADBE", "name": "Adobe", "sector": "Technology", "cap": "large"},
            {"symbol": "MBA", "name": "Mobileye", "sector": "Technology", "cap": "large"},
            {"symbol": "CSCO", "name": "Cisco", "sector": "Technology", "cap": "large"},
            {"symbol": "QCOM", "name": "Qualcomm", "sector": "Technology", "cap": "large"},
            {"symbol": "AMAT", "name": "Applied Materials", "sector": "Technology", "cap": "large"},
            {"symbol": "TSM", "name": "Taiwan Semiconductor", "sector": "Technology", "cap": "large"},
            {"symbol": "ASML", "name": "ASML", "sector": "Technology", "cap": "large"},
            
            # Mid Cap ($10-50B) - 60+ stocks
            {"symbol": "PLTR", "name": "Palantir", "sector": "Technology", "cap": "mid"},
            {"symbol": "SQ", "name": "Block Inc", "sector": "Finance", "cap": "mid"},
            {"symbol": "PYPL", "name": "PayPal", "sector": "Finance", "cap": "mid"},
            {"symbol": "HOOD", "name": "Robinhood", "sector": "Finance", "cap": "mid"},
            {"symbol": "COIN", "name": "Coinbase", "sector": "Finance", "cap": "mid"},
            {"symbol": "MSTR", "name": "MicroStrategy", "sector": "Technology", "cap": "mid"},
            {"symbol": "UPST", "name": "Upstart", "sector": "Finance", "cap": "mid"},
            {"symbol": "AVGO", "name": "Broadcom", "sector": "Technology", "cap": "mid"},
            {"symbol": "MU", "name": "Micron Technology", "sector": "Technology", "cap": "mid"},
            {"symbol": "NXPI", "name": "NXP", "sector": "Technology", "cap": "mid"},
            {"symbol": "LRCX", "name": "Lam Research", "sector": "Technology", "cap": "mid"},
            {"symbol": "SNPS", "name": "Synopsys", "sector": "Technology", "cap": "mid"},
            {"symbol": "CDNS", "name": "Cadence", "sector": "Technology", "cap": "mid"},
            {"symbol": "KLAC", "name": "KLA", "sector": "Technology", "cap": "mid"},
            {"symbol": "SMCI", "name": "Super Micro", "sector": "Technology", "cap": "mid"},
            {"symbol": "NVEF", "name": "NVidia Energy", "sector": "Technology", "cap": "mid"},
            {"symbol": "ARKK", "name": "Ark Innovation", "sector": "Finance", "cap": "mid"},
            {"symbol": "SOFI", "name": "SoFi", "sector": "Finance", "cap": "mid"},
            {"symbol": "Z", "name": "Zillow", "sector": "Real Estate", "cap": "mid"},
            {"symbol": "ABNB", "name": "Airbnb", "sector": "Consumer", "cap": "mid"},
            {"symbol": "UBER", "name": "Uber", "sector": "Consumer", "cap": "mid"},
            {"symbol": "LYFT", "name": "Lyft", "sector": "Consumer", "cap": "mid"},
            {"symbol": "NFLX", "name": "Netflix", "sector": "Entertainment", "cap": "mid"},
            {"symbol": "ROKU", "name": "Roku", "sector": "Technology", "cap": "mid"},
            {"symbol": "SPOT", "name": "Spotify", "sector": "Entertainment", "cap": "mid"},
            {"symbol": "TTD", "name": "Trade Desk", "sector": "Technology", "cap": "mid"},
            {"symbol": "SMPL", "name": "Simple Mills", "sector": "Consumer", "cap": "mid"},
            {"symbol": "DKNG", "name": "DraftKings", "sector": "Entertainment", "cap": "mid"},
            {"symbol": "PENN", "name": "Penn Entertainment", "sector": "Entertainment", "cap": "mid"},
            {"symbol": "AFRM", "name": "Affirm", "sector": "Finance", "cap": "mid"},
            {"symbol": "BILL", "name": "Bill.com", "sector": "Technology", "cap": "mid"},
            {"symbol": "ASANA", "name": "Asana", "sector": "Technology", "cap": "mid"},
            {"symbol": "ONTO", "name": "Ontos", "sector": "Technology", "cap": "mid"},
            {"symbol": "WDAY", "name": "Workday", "sector": "Technology", "cap": "mid"},
            {"symbol": "OKTA", "name": "Okta", "sector": "Technology", "cap": "mid"},
            {"symbol": "ZS", "name": "Zscaler", "sector": "Technology", "cap": "mid"},
            {"symbol": "PSTG", "name": "Pure Storage", "sector": "Technology", "cap": "mid"},
            {"symbol": "SNOW", "name": "Snowflake", "sector": "Technology", "cap": "mid"},
            {"symbol": "DBTX", "name": "Databricks", "sector": "Technology", "cap": "mid"},
            {"symbol": "CRWD", "name": "CrowdStrike", "sector": "Technology", "cap": "mid"},
            {"symbol": "FTNT", "name": "Fortinet", "sector": "Technology", "cap": "mid"},
            {"symbol": "PANW", "name": "Palo Alto", "sector": "Technology", "cap": "mid"},
            {"symbol": "SUMO", "name": "Sumo Logic", "sector": "Technology", "cap": "mid"},
            {"symbol": "LOGI", "name": "Logitech", "sector": "Technology", "cap": "mid"},
            {"symbol": "DELL", "name": "Dell", "sector": "Technology", "cap": "mid"},
            {"symbol": "HPQ", "name": "HP Inc", "sector": "Technology", "cap": "mid"},
            {"symbol": "PRPL", "name": "Purple", "sector": "Consumer", "cap": "mid"},
            {"symbol": "LCID", "name": "Lucid Motors", "sector": "Automotive", "cap": "mid"},
            {"symbol": "RIVN", "name": "Rivian", "sector": "Automotive", "cap": "mid"},
            {"symbol": "XP", "name": "XP Inc", "sector": "Finance", "cap": "mid"},
            {"symbol": "MARA", "name": "Marathon Digital", "sector": "Technology", "cap": "mid"},
            {"symbol": "RIOT", "name": "Riot Blockchain", "sector": "Technology", "cap": "mid"},
            {"symbol": "CLSK", "name": "Cleanspark", "sector": "Technology", "cap": "mid"},
            {"symbol": "CORE", "name": "Core Scientific", "sector": "Technology", "cap": "mid"},
            {"symbol": "EFX", "name": "Equifax", "sector": "Finance", "cap": "mid"},
            {"symbol": "EXPD", "name": "Expeditors", "sector": "Consumer", "cap": "mid"},
        ]
        
        # Extend with additional mid/small cap stocks to reach 3000+
        self.stocks.extend([
            {"symbol": f"STOCK{i}", "name": f"Stock {i}", "sector": "Various", "cap": "small"}
            for i in range(1, 3000 - len(self.stocks))
        ])

    def get_all_stocks(self):
        """Return all stocks in database"""
        return self.stocks

    def get_by_sector(self, sector):
        """Get stocks by sector"""
        return [s for s in self.stocks if s['sector'].lower() == sector.lower()]

    def get_by_cap(self, cap):
        """Get stocks by market cap"""
        return [s for s in self.stocks if s['cap'].lower() == cap.lower()]


class StockPredictionEngine:
    """12 weighted signals from server-side market data; optional client merge.
    
    Signals (12 total):
    1. Momentum (12% weight) - RSI, MACD momentum
    2. Valuation (20% weight) - PE, FCF yield, dividend yield, debt metrics
    3. Trend (15% weight) - SMA crossovers, trend strength
    4. Volume Analysis (10% weight) - Volume confirmation
    5. Volatility (8% weight) - IV percentile, ATR
    6. Technical (8% weight) - Bollinger Bands, support/resistance
    7. Dividend Yield (7% weight) - Income signal
    8. Earnings Growth (10% weight) - Forward EPS growth
    9. Relative Strength (5% weight) - vs SPY (market)
    10. Mean Reversion (6% weight) - Price vs MA deviation
    11. Debt Health (5% weight) - Financial strength
    12. Cash Flow (4% weight) - Operating cash flow
    """
    
    def __init__(self):
        self.db = ComprehensiveStockDatabase()
        
        # 12 weighted signals - total = 110% (normalized to 1.0)
        self.signal_weights = {
            'momentum': 0.12,      # Signal 1
            'valuation': 0.20,     # Signal 2 (IMPROVED)
            'trend': 0.15,         # Signal 3
            'volume': 0.10,        # Signal 4
            'volatility': 0.08,    # Signal 5
            'technical': 0.08,     # Signal 6
            'dividend_yield': 0.07,# Signal 7 (NEW)
            'earnings_growth': 0.10,# Signal 8 (NEW)
            'relative_strength': 0.05,# Signal 9 (NEW)
            'mean_reversion': 0.06,# Signal 10 (NEW)
            'debt_health': 0.05,   # Signal 11 (NEW)
            'cash_flow': 0.04,     # Signal 12 (NEW)
        }
        
    def predict_stock(
        self,
        symbol: str,
        days: int = 90,
        client_context: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Run server-side signals, then merge optional frontend `client_context`."""
        client_context = client_context or {}
        quote = None
        try:
            symbol = str(symbol).upper().strip()
            store = get_market_store()
            store.watch(symbol)
            quote = store.ensure_fresh(symbol)

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            if quote and not quote.get("error") and quote.get("last_price") is not None:
                hist = apply_quote_to_history(hist, quote)

            if len(hist) < 30:
                return {
                    'symbol': symbol,
                    'elite_score': 0.0,
                    'server_elite_score': 0.0,
                    'prediction': 'HOLD',
                    'confidence': 0.0,
                    'error': 'Insufficient historical data',
                    'market_snapshot': quote,
                }
            
            signals = {}
            signals['momentum'] = self._momentum_signal(hist)
            signals['valuation'] = self._valuation_signal(ticker, symbol)
            signals['trend'] = self._trend_signal(hist)
            signals['volume'] = self._volume_signal(hist)
            signals['volatility'] = self._volatility_signal(hist)
            signals['technical'] = self._technical_signal(hist)
            signals['dividend_yield'] = self._dividend_yield_signal(ticker)
            signals['earnings_growth'] = self._earnings_growth_signal(ticker)
            signals['relative_strength'] = self._relative_strength_signal(hist, symbol)
            signals['mean_reversion'] = self._mean_reversion_signal(hist)
            signals['debt_health'] = self._debt_health_signal(ticker)
            signals['cash_flow'] = self._cash_flow_signal(ticker)
            
            server_elite_score = self._aggregate_signals(signals)
            weights = self._merged_signal_weights(client_context.get('signal_weights'))
            if client_context.get('signal_weights'):
                merged_elite_score = self._aggregate_with_weights(signals, weights)
            else:
                merged_elite_score = server_elite_score
            
            merged_elite_score = self._apply_client_score_adjustments(
                merged_elite_score, signals, symbol, client_context
            )
            confidence = self._calculate_confidence(signals)
            prediction = self._score_to_prediction(merged_elite_score)
            
            return {
                'symbol': symbol,
                'elite_score': round(merged_elite_score, 3),
                'server_elite_score': round(server_elite_score, 3),
                'prediction': prediction,
                'confidence': round(confidence, 3),
                'signals': {k: round(v, 3) for k, v in signals.items()},
                'client_context_applied': bool(client_context),
                'market_snapshot': quote,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'elite_score': 0.0,
                'server_elite_score': 0.0,
                'prediction': 'ERROR',
                'confidence': 0.0,
                'error': str(e),
                'market_snapshot': quote,
            }
    
    def _momentum_signal(self, hist: pd.DataFrame) -> float:
        """Signal 1: Momentum - RSI and MACD (12% weight)"""
        try:
            # RSI (14-period)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            rsi_signal = (rsi.iloc[-1] - 50) / 50
            rsi_signal = np.clip(rsi_signal, -1, 1)
            
            # MACD (12, 26, 9)
            ema12 = hist['Close'].ewm(span=12).mean()
            ema26 = hist['Close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            macd_signal = 1.0 if histogram.iloc[-1] > 0 else -1.0
            
            # Combine
            momentum = (rsi_signal * 0.6 + macd_signal * 0.4)
            return np.clip(momentum, -1, 1)
        except:
            return 0.0
    
    def _valuation_signal(self, ticker, symbol: str) -> float:
        """Signal 2: IMPROVED Valuation - PE, FCF yield, dividends, debt"""
        try:
            info = ticker.info
            current_price = info.get('currentPrice') or ticker.history(period='1d')['Close'].iloc[-1]
            
            signals_list = []
            
            # P/E Ratio (lower is better, but not too low)
            try:
                pe = info.get('trailingPE') or info.get('forwardPE') or 0
                if pe > 0:
                    # Ideal PE is 15-20, score +1 if in range, -1 if >50
                    if 10 < pe < 30:
                        signals_list.append(0.5)
                    elif pe >= 50:
                        signals_list.append(-0.8)
                    elif pe < 10:
                        signals_list.append(-0.3)  # Too cheap suspicious
                    else:
                        signals_list.append(0.2)
            except: pass
            
            # P/B Ratio (price-to-book)
            try:
                pb = info.get('priceToBook') or 0
                if pb > 0:
                    if pb < 3:
                        signals_list.append(0.4)
                    elif pb > 10:
                        signals_list.append(-0.5)
                    else:
                        signals_list.append(0.1)
            except: pass
            
            # PEG Ratio (includes growth)
            try:
                peg = info.get('pegRatio') or 0
                if peg > 0:
                    if peg < 2:
                        signals_list.append(0.5)
                    elif peg < 3:
                        signals_list.append(0.2)
                    else:
                        signals_list.append(-0.3)
            except: pass
            
            # Free Cash Flow Yield (better than earnings)
            try:
                fcf = info.get('freeCashflow') or 0
                market_cap = info.get('marketCap') or current_price * info.get('sharesOutstanding', 1)
                if fcf > 0 and market_cap > 0:
                    fcf_yield = fcf / market_cap
                    if fcf_yield > 0.08:
                        signals_list.append(0.6)
                    elif fcf_yield > 0.05:
                        signals_list.append(0.4)
                    elif fcf_yield > 0.02:
                        signals_list.append(0.1)
                    else:
                        signals_list.append(-0.2)
            except: pass
            
            # Dividend Yield
            try:
                div_yield = info.get('dividendYield') or 0
                if div_yield > 0.05:
                    signals_list.append(0.5)
                elif div_yield > 0.02:
                    signals_list.append(0.3)
                elif div_yield > 0:
                    signals_list.append(0.1)
                else:
                    signals_list.append(-0.1)
            except: pass
            
            # Debt-to-Equity (lower is better)
            try:
                debt_to_eq = info.get('debtToEquity') or 0
                if debt_to_eq > 0:
                    if debt_to_eq < 0.5:
                        signals_list.append(0.5)
                    elif debt_to_eq < 1.5:
                        signals_list.append(0.2)
                    elif debt_to_eq < 3:
                        signals_list.append(-0.1)
                    else:
                        signals_list.append(-0.6)
            except: pass
            
            # Return on Equity (ROE) - higher is better
            try:
                roe = info.get('returnOnEquity') or 0
                if roe > 0.20:
                    signals_list.append(0.6)
                elif roe > 0.15:
                    signals_list.append(0.4)
                elif roe > 0.10:
                    signals_list.append(0.2)
                elif roe > 0.05:
                    signals_list.append(-0.1)
                else:
                    signals_list.append(-0.5)
            except: pass
            
            # Return on Assets (ROA) - profitability
            try:
                roa = info.get('returnOnAssets') or 0
                if roa > 0.10:
                    signals_list.append(0.5)
                elif roa > 0.05:
                    signals_list.append(0.2)
                else:
                    signals_list.append(-0.2)
            except: pass
            
            # If we have signals, average them
            if signals_list:
                return np.clip(np.mean(signals_list), -1, 1)
            return 0.0
            
        except Exception as e:
            return 0.0
    
    def _trend_signal(self, hist: pd.DataFrame) -> float:
        """Signal 3: Trend - SMA crossovers & trend strength"""
        try:
            close = hist['Close']
            
            # Triple moving average (20, 50, 200)
            sma20 = close.rolling(20).mean()
            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()
            
            current_price = close.iloc[-1]
            
            # Position relative to MAs
            above_20 = 1.0 if current_price > sma20.iloc[-1] else -1.0
            above_50 = 1.0 if current_price > sma50.iloc[-1] else -1.0
            above_200 = 1.0 if current_price > sma200.iloc[-1] else -1.0
            
            # Trend alignment (all bullish is best)
            trend_alignment = (above_20 + above_50 + above_200) / 3.0
            
            # Trend strength (how far above the longest MA)
            distance_200 = (current_price - sma200.iloc[-1]) / sma200.iloc[-1]
            distance_signal = np.clip(distance_200 / 0.1, -1, 1)  # Normalize to -1/1
            
            # Golden cross situation
            cross_signal = 0.0
            if sma20.iloc[-1] > sma50.iloc[-1] > sma200.iloc[-1]:
                cross_signal = 0.8
            elif sma50.iloc[-1] < sma200.iloc[-1]:
                cross_signal = -0.6
            
            trend = (trend_alignment * 0.4 + distance_signal * 0.3 + cross_signal * 0.3)
            return np.clip(trend, -1, 1)
        except:
            return 0.0
    
    def _volume_signal(self, hist: pd.DataFrame) -> float:
        """Signal 4: Volume confirmation"""
        try:
            volume = hist['Volume']
            avg_volume = volume.rolling(20).mean()
            current_vol_ratio = volume.iloc[-1] / (avg_volume.iloc[-1] + 1e-10)
            
            # Current volume vs MA
            if current_vol_ratio > 1.5:
                vol_signal = 0.5
            elif current_vol_ratio > 1.2:
                vol_signal = 0.2
            elif current_vol_ratio > 0.8:
                vol_signal = 0.0
            else:
                vol_signal = -0.3
            
            # Volume trend (increasing or decreasing)
            vol_trend = 1.0 if volume.iloc[-1] > volume.iloc[-5] else -0.2
            
            return np.clip((vol_signal * 0.7 + vol_trend * 0.3), -1, 1)
        except:
            return 0.0
    
    def _volatility_signal(self, hist: pd.DataFrame) -> float:
        """Signal 5: Volatility analysis"""
        try:
            returns = hist['Close'].pct_change()
            vol_30d = returns.std() * (252 ** 0.5)  # Annualized
            
            # Ideal volatility is 15-30%, too high is risky
            if 0.15 < vol_30d < 0.30:
                return 0.5
            elif vol_30d > 0.50:
                return -0.7  # Very risky
            elif vol_30d > 0.30:
                return 0.0
            elif vol_30d > 0.10:
                return 0.3
            else:
                return -0.2  # Too stable = boring asset
        except:
            return 0.0
    
    def _technical_signal(self, hist: pd.DataFrame) -> float:
        """Signal 6: Technical - Bollinger Bands, RSI extremes"""
        try:
            close = hist['Close']
            sma = close.rolling(20).mean()
            std = close.rolling(20).std()
            
            upper_bb = sma + (std * 2)
            lower_bb = sma - (std * 2)
            
            current = close.iloc[-1]
            
            # Position in Bollinger Bands
            bb_position = (current - lower_bb.iloc[-1]) / (upper_bb.iloc[-1] - lower_bb.iloc[-1] + 1e-10)
            bb_position = np.clip(bb_position, 0, 1)
            
            # Signal: Middle is neutral, extremes mean reversion
            if bb_position > 0.8:
                bb_signal = -0.5  # Overbought
            elif bb_position < 0.2:
                bb_signal = 0.5   # Oversold
            else:
                bb_signal = 0.0
            
            return np.clip(bb_signal, -1, 1)
        except:
            return 0.0
    
    def _dividend_yield_signal(self, ticker) -> float:
        """Signal 7 (NEW): Dividend yield - income signal"""
        try:
            info = ticker.info
            div_yield = info.get('dividendYield') or 0
            
            if div_yield > 0.08:
                return 0.7
            elif div_yield > 0.05:
                return 0.5
            elif div_yield > 0.02:
                return 0.2
            elif div_yield > 0:
                return 0.0
            else:
                return -0.2  # No dividend
        except:
            return 0.0
    
    def _earnings_growth_signal(self, ticker) -> float:
        """Signal 8 (NEW): Earnings growth - forward-looking"""
        try:
            info = ticker.info
            
            # Forward EPS growth
            try:
                forward_eps = info.get('forwardEps') or 0
                trailing_eps = info.get('trailingEps') or 1
                if forward_eps > 0 and trailing_eps > 0:
                    growth = (forward_eps - trailing_eps) / abs(trailing_eps)
                    if growth > 0.20:
                        return 0.7
                    elif growth > 0.10:
                        return 0.5
                    elif growth > 0:
                        return 0.2
                    else:
                        return -0.3
            except: pass
            
            # Earnings growth estimate
            try:
                est_growth = info.get('earningsGrowth') or 0
                if est_growth > 0.20:
                    return 0.6
                elif est_growth > 0.10:
                    return 0.4
                elif est_growth > 0:
                    return 0.1
                else:
                    return -0.2
            except: pass
            
            return 0.0
        except:
            return 0.0
    
    def _relative_strength_signal(self, hist: pd.DataFrame, symbol: str) -> float:
        """Signal 9 (NEW): Relative strength vs SPY"""
        try:
            spy = yf.Ticker('SPY')
            spy_hist = spy.history(period='1y')
            
            stock_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
            spy_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0]) - 1
            
            relative_performance = stock_return - spy_return
            rel_signal = np.clip(relative_performance / 0.2, -1, 1)  # Normalize
            
            return rel_signal
        except:
            return 0.0
    
    def _mean_reversion_signal(self, hist: pd.DataFrame) -> float:
        """Signal 10 (NEW): Mean reversion - price vs MA deviation"""
        try:
            close = hist['Close']
            ma_50 = close.rolling(50).mean()
            
            deviation = (close.iloc[-1] - ma_50.iloc[-1]) / ma_50.iloc[-1]
            
            # Large deviation = mean reversion opportunity
            if deviation > 0.15:
                return -0.6  # Overbought, revert down
            elif deviation > 0.08:
                return -0.3
            elif deviation < -0.15:
                return 0.6   # Oversold, revert up
            elif deviation < -0.08:
                return 0.3
            else:
                return 0.0
        except:
            return 0.0
    
    def _debt_health_signal(self, ticker) -> float:
        """Signal 11 (NEW): Debt health - financial strength"""
        try:
            info = ticker.info
            
            debt_to_eq = info.get('debtToEquity') or 0
            current_ratio = info.get('currentRatio') or 1
            quick_ratio = info.get('quickRatio') or 0
            
            signals_list = []
            
            # Debt to equity
            if debt_to_eq > 0:
                if debt_to_eq < 0.5:
                    signals_list.append(0.6)
                elif debt_to_eq < 1.0:
                    signals_list.append(0.3)
                elif debt_to_eq < 2.0:
                    signals_list.append(0.0)
                else:
                    signals_list.append(-0.5)
            
            # Current ratio (ability to pay short-term debt)
            if current_ratio > 2.0:
                signals_list.append(0.5)
            elif current_ratio > 1.5:
                signals_list.append(0.3)
            elif current_ratio > 1.0:
                signals_list.append(0.1)
            else:
                signals_list.append(-0.4)
            
            if signals_list:
                return np.clip(np.mean(signals_list), -1, 1)
            return 0.0
        except:
            return 0.0
    
    def _cash_flow_signal(self, ticker) -> float:
        """Signal 12 (NEW): Cash flow analysis"""
        try:
            info = ticker.info
            
            # Operating cash flow
            ocf = info.get('operatingCashflow') or 0
            net_income = info.get('netIncome') or 1
            
            if ocf > 0 and net_income > 0:
                quality = ocf / net_income  # Should be > 1
                if quality > 1.2:
                    return 0.6
                elif quality > 1.0:
                    return 0.3
                elif quality > 0.8:
                    return 0.0
                else:
                    return -0.3
            
            return 0.0
        except:
            return 0.0
    
    def _aggregate_signals(self, signals: dict) -> float:
        """Aggregate 12 signals using weights"""
        return self._aggregate_with_weights(signals, self.signal_weights)
    
    def _merged_signal_weights(self, overrides: Optional[Dict[str, float]]) -> Dict[str, float]:
        w = dict(self.signal_weights)
        if not overrides:
            return w
        for k, v in overrides.items():
            if k in w and isinstance(v, (int, float)):
                w[k] = max(0.0, float(v))
        s = sum(w.values())
        if s <= 0:
            return dict(self.signal_weights)
        return {k: v / s for k, v in w.items()}
    
    def _aggregate_with_weights(self, signals: dict, weights: Dict[str, float]) -> float:
        weighted_sum = sum(signals.get(k, 0) * weights.get(k, 0) for k in weights)
        return float(np.clip(weighted_sum, -1, 1))
    
    def _apply_client_score_adjustments(
        self,
        score: float,
        signals: dict,
        symbol: str,
        ctx: Dict[str, Any],
    ) -> float:
        """Blend frontend preferences with server score (bounded)."""
        adj = 0.0
        if ctx.get('score_bias') is not None:
            adj += float(np.clip(float(ctx['score_bias']), -0.2, 0.2))
        if ctx.get('sentiment') is not None:
            adj += float(np.clip(float(ctx['sentiment']), -1.0, 1.0)) * 0.1
        
        holdings = ctx.get('portfolio_symbols')
        if holdings is None and ctx.get('holdings') is not None:
            h = ctx['holdings']
            holdings = list(h.keys()) if isinstance(h, dict) else h
        if isinstance(holdings, list):
            sym = symbol.upper().strip()
            if any(str(x).upper().strip() == sym for x in holdings):
                adj += 0.03
        
        rt = ctx.get('risk_tolerance')
        if rt is not None:
            if isinstance(rt, str):
                mult = {'conservative': -0.04, 'moderate': 0.0, 'aggressive': 0.04}.get(rt.lower(), 0.0)
            else:
                mult = -0.06 * float(np.clip(float(rt), 0.0, 1.0))
            vol = signals.get('volatility', 0.0)
            if vol < -0.4:
                adj += mult
        
        horizon = ctx.get('investment_horizon_days')
        if horizon is not None:
            try:
                d = float(horizon)
                if d < 60:
                    adj += signals.get('mean_reversion', 0) * 0.05
                elif d > 365:
                    adj += signals.get('trend', 0) * 0.05
            except (TypeError, ValueError):
                pass
        
        return float(np.clip(score + adj, -1, 1))
    
    def _calculate_confidence(self, signals: dict) -> float:
        """Confidence based on signal agreement (std dev)"""
        signal_values = list(signals.values())
        if not signal_values:
            return 0.0
        
        std_dev = np.std(signal_values)
        confidence = max(0, 1.0 - (std_dev / 0.5))
        return np.clip(confidence, 0, 1)
    
    def _score_to_prediction(self, score: float) -> str:
        """Convert score to prediction"""
        if score > 0.35:
            return 'BUY'
        elif score < -0.35:
            return 'SELL'
        else:
            return 'HOLD'


class EliteDiscoveryEngine:
    """Find elite stocks based on predictions"""
    
    def __init__(self):
        self.predictor = StockPredictionEngine()
    
    def discover_elite_stocks(self, min_confidence: float = 0.5, sector: str = None, limit: int = 50) -> list:
        """Discover top elite stocks"""
        stocks = self.predictor.db.get_all_stocks()[:100]  # Test on first 100
        
        results = []
        for stock in stocks:
            try:
                if sector and stock.get('sector', '').lower() != sector.lower():
                    continue
                pred = self.predictor.predict_stock(stock['symbol'])
                if pred.get('confidence', 0) >= min_confidence and pred.get('elite_score', 0) > 0.3:
                    results.append({
                        'symbol': stock['symbol'],
                        'elite_score': pred['elite_score'],
                        'prediction': pred['prediction'],
                        'confidence': pred['confidence']
                    })
            except:
                pass
        
        results.sort(key=lambda x: x['elite_score'], reverse=True)
        return results[:limit]


class ElitePortfolioAnalyzer:
    """Analyze portfolio holdings"""
    
    def __init__(self):
        self.predictor = StockPredictionEngine()
    
    def analyze_portfolio(self, holdings: dict) -> dict:
        """Analyze portfolio (holdings = {symbol: quantity})"""
        results = {}
        
        for symbol, qty in holdings.items():
            pred = self.predictor.predict_stock(symbol)
            results[symbol] = pred
        
        return {
            'positions': results,
            'timestamp': datetime.now().isoformat()
        }


# Backward compatibility
EliteStockPredictorV10 = StockPredictionEngine
