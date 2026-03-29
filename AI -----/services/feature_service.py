"""
FeatureService - Technical indicator computation and feature engineering
Phase 1 Implementation
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from core.data_structures import MarketData, FeatureVector, FeatureMatrix
from core.exceptions import FeatureError, InsufficientDataError

log = logging.getLogger(__name__)


class TechnicalIndicators:
    """Compute technical indicators from price data"""
    
    @staticmethod
    def sma(prices: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=window, min_periods=window).mean()
    
    @staticmethod
    def ema(prices: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=window, adjust=False, min_periods=window).mean()
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        Returns: MACD line, Signal line, Histogram
        """
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        
        avg_gain = gain.rolling(window=window, min_periods=window).mean()
        avg_loss = loss.rolling(window=window, min_periods=window).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        Returns: Upper band, Middle band (SMA), Lower band
        """
        middle = TechnicalIndicators.sma(prices, window)
        std = prices.rolling(window=window, min_periods=window).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        return upper, middle, lower
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=window, min_periods=window).mean()
        return atr
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   window: int = 14, smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        Returns: %K, %D
        """
        lowest_low = low.rolling(window=window, min_periods=window).min()
        highest_high = high.rolling(window=window, min_periods=window).max()
        
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = TechnicalIndicators.sma(k, smooth)
        return k, d
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(window=window, min_periods=window).max()
        lowest_low = low.rolling(window=window, min_periods=window).min()
        
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return wr
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        tp = (high + low + close) / 3
        tp_sma = TechnicalIndicators.sma(tp, window)
        tp_std = tp.rolling(window=window, min_periods=window).std()
        
        cci = (tp - tp_sma) / (0.015 * tp_std.replace(0, np.nan))
        return cci
    
    @staticmethod
    def roc(prices: pd.Series, window: int = 10) -> pd.Series:
        """Rate of Change"""
        roc = (prices - prices.shift(window)) / prices.shift(window) * 100
        return roc
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average Directional Index"""
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = low.diff().abs()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        # Calculate TR
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(window=window, min_periods=window).mean()
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm.rolling(window=window).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=window).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
        adx = dx.rolling(window=window, min_periods=window).mean()
        
        return adx
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        obv = volume.copy()
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        tp = (high + low + close) / 3
        cum_vol = volume.cumsum()
        cum_pv = (tp * volume).cumsum()
        vwap = cum_pv / cum_vol.replace(0, np.nan)
        return vwap


class VolatilityIndicators:
    """Compute volatility measures"""
    
    @staticmethod
    def historical_volatility(prices: pd.Series, window: int = 20, annualize: bool = True) -> pd.Series:
        """Historical volatility from daily returns"""
        returns = prices.pct_change()
        vol = returns.rolling(window=window, min_periods=window).std()
        
        if annualize:
            vol = vol * np.sqrt(252)
        
        return vol
    
    @staticmethod
    def parkinson_volatility(high: pd.Series, low: pd.Series, window: int = 20, annualize: bool = True) -> pd.Series:
        """Parkinson volatility (uses high-low range)"""
        hl_ratio = np.log(high / low.replace(0, np.nan))
        parkinson = np.sqrt(hl_ratio**2 / (4 * np.log(2)))
        vol = parkinson.rolling(window=window, min_periods=window).mean()
        
        if annualize:
            vol = vol * np.sqrt(252)
        
        return vol
    
    @staticmethod
    def garman_klass_volatility(open: pd.Series, high: pd.Series, 
                               low: pd.Series, close: pd.Series, 
                               window: int = 20, annualize: bool = True) -> pd.Series:
        """Garman-Klass volatility (more efficient estimator)"""
        log_hl = np.log(high / low.replace(0, np.nan))**2
        log_co = np.log(close / open.replace(0, np.nan))**2
        
        var = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
        vol = np.sqrt(var.rolling(window=window, min_periods=window).mean())
        
        if annualize:
            vol = vol * np.sqrt(252)
        
        return vol


class FeatureService:
    """
    Service for computing technical indicators and feature engineering
    """
    
    def __init__(self):
        self.tech_indicators = TechnicalIndicators()
        self.vol_indicators = VolatilityIndicators()
        
        # Define feature sets
        self.trend_features = [
            'sma_10', 'sma_20', 'sma_50',
            'ema_12', 'ema_26',
            'macd', 'macd_signal', 'macd_hist',
            'adx'
        ]
        
        self.momentum_features = [
            'rsi_14', 'stoch_k', 'stoch_d',
            'williams_r', 'cci', 'roc_10'
        ]
        
        self.volatility_features = [
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
            'atr_14', 'hist_vol_20', 'hist_vol_60'
        ]
        
        self.volume_features = [
            'volume', 'obv', 'vwap', 'volume_sma_20'
        ]
        
        self.all_feature_names = (
            self.trend_features + 
            self.momentum_features + 
            self.volatility_features +
            self.volume_features
        )
        
        log.info("FeatureService initialized")
    
    def compute_features(self, market_data: List[MarketData]) -> List[FeatureVector]:
        """
        Compute features from market data
        
        Args:
            market_data: List of MarketData objects
            
        Returns:
            List of FeatureVector objects
        """
        if len(market_data) < 50:
            raise InsufficientDataError(f"Need at least 50 data points, got {len(market_data)}")
        
        # Convert to DataFrame
        df = self._to_dataframe(market_data)
        
        # Compute all indicators
        df = self._compute_trend_features(df)
        df = self._compute_momentum_features(df)
        df = self._compute_volatility_features(df)
        df = self._compute_volume_features(df)
        
        # Create FeatureVectors
        feature_vectors = []
        for idx, row in df.iterrows():
            features = {}
            for name in self.all_feature_names:
                if name in row.index:
                    val = row[name]
                    if pd.notna(val) and np.isfinite(val):
                        features[name] = float(val)
                    else:
                        features[name] = 0.0
            
            # Get symbol and timestamp from original data
            md = market_data[df.index.get_loc(idx)]
            
            feature_vectors.append(FeatureVector(
                symbol=md.symbol,
                timestamp=md.timestamp,
                features=features,
                feature_names=self.all_feature_names.copy()
            ))
        
        return feature_vectors
    
    def compute_batch(self, market_data_dict: Dict[str, List[MarketData]]) -> FeatureMatrix:
        """
        Compute features for multiple symbols
        
        Args:
            market_data_dict: Dict of symbol -> MarketData list
            
        Returns:
            FeatureMatrix with all features
        """
        all_features = []
        all_symbols = []
        all_timestamps = []
        
        for symbol, data in market_data_dict.items():
            try:
                vectors = self.compute_features(data)
                for v in vectors:
                    all_features.append(v.values_array)
                    all_symbols.append(symbol)
                    all_timestamps.append(v.timestamp)
            except Exception as e:
                log.error(f"Failed to compute features for {symbol}: {e}")
        
        if not all_features:
            return FeatureMatrix()
        
        return FeatureMatrix(
            symbols=all_symbols,
            timestamps=all_timestamps,
            features=np.array(all_features),
            feature_names=self.all_feature_names.copy()
        )
    
    def _to_dataframe(self, market_data: List[MarketData]) -> pd.DataFrame:
        """Convert MarketData list to DataFrame"""
        records = []
        for md in market_data:
            records.append({
                'open': md.open,
                'high': md.high,
                'low': md.low,
                'close': md.close,
                'volume': md.volume,
                'adjusted_close': md.adjusted_close if md.adjusted_close else md.close
            })
        
        df = pd.DataFrame(records)
        df.index = [md.timestamp for md in market_data]
        return df
    
    def _compute_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute trend-based features"""
        prices = df['close']
        
        # Moving averages
        df['sma_10'] = TechnicalIndicators.sma(prices, 10)
        df['sma_20'] = TechnicalIndicators.sma(prices, 20)
        df['sma_50'] = TechnicalIndicators.sma(prices, 50)
        
        df['ema_12'] = TechnicalIndicators.ema(prices, 12)
        df['ema_26'] = TechnicalIndicators.ema(prices, 26)
        
        # MACD
        macd, signal, hist = TechnicalIndicators.macd(prices)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        # ADX
        df['adx'] = TechnicalIndicators.adx(df['high'], df['low'], prices)
        
        return df
    
    def _compute_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute momentum-based features"""
        prices = df['close']
        
        # RSI
        df['rsi_14'] = TechnicalIndicators.rsi(prices, 14)
        
        # Stochastic
        k, d = TechnicalIndicators.stochastic(df['high'], df['low'], prices)
        df['stoch_k'] = k
        df['stoch_d'] = d
        
        # Williams %R
        df['williams_r'] = TechnicalIndicators.williams_r(df['high'], df['low'], prices)
        
        # CCI
        df['cci'] = TechnicalIndicators.cci(df['high'], df['low'], prices)
        
        # ROC
        df['roc_10'] = TechnicalIndicators.roc(prices, 10)
        
        return df
    
    def _compute_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volatility-based features"""
        prices = df['close']
        
        # Bollinger Bands
        upper, middle, lower = TechnicalIndicators.bollinger_bands(prices)
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        df['bb_width'] = (upper - lower) / middle.replace(0, np.nan)
        
        # ATR
        df['atr_14'] = TechnicalIndicators.atr(df['high'], df['low'], prices)
        
        # Historical volatility
        df['hist_vol_20'] = VolatilityIndicators.historical_volatility(prices, 20)
        df['hist_vol_60'] = VolatilityIndicators.historical_volatility(prices, 60)
        
        return df
    
    def _compute_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volume-based features"""
        # Volume features
        df['volume_sma_20'] = TechnicalIndicators.sma(df['volume'].astype(float), 20)
        
        # OBV
        df['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])
        
        # VWAP
        df['vwap'] = TechnicalIndicators.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        return df
    
    def get_feature_importance(self, df: pd.DataFrame, target: pd.Series) -> Dict[str, float]:
        """
        Calculate feature importance using correlation with target
        
        Args:
            df: DataFrame with features
            target: Target variable (e.g., future returns)
            
        Returns:
            Dict of feature -> importance score
        """
        importance = {}
        
        for col in df.columns:
            if col in self.all_feature_names:
                try:
                    corr = df[col].corr(target)
                    if pd.notna(corr):
                        importance[col] = abs(corr)
                except:
                    importance[col] = 0.0
        
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        return importance
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        return self.all_feature_names.copy()


# Global instance
feature_service = FeatureService()
