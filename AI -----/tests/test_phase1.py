"""
Phase 1 Test Suite
Tests for DataService and FeatureService
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_structures import MarketData, FundamentalData, FeatureVector
from core.exceptions import DataQualityError, InsufficientDataError
from services.data_service import DataService, DataCacheManager, DataQualityChecker
from services.feature_service import FeatureService, TechnicalIndicators, VolatilityIndicators


class TestDataQualityChecker(unittest.TestCase):
    """Test data quality validation"""
    
    def setUp(self):
        self.checker = DataQualityChecker()
    
    def test_validate_ohlcv_valid_data(self):
        """Test validation with clean data"""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [98, 99, 100],
            'close': [104, 105, 106],
            'volume': [1000, 2000, 3000]
        })
        df.index = pd.date_range('2024-01-01', periods=3)
        
        result = self.checker.validate_ohlcv(df)
        self.assertEqual(len(result), 3)
    
    def test_validate_ohlcv_invalid_price_logic(self):
        """Test validation with invalid price logic"""
        df = pd.DataFrame({
            'open': [100],
            'high': [99],  # Invalid: high < low
            'low': [105],
            'close': [102],
            'volume': [1000]
        })
        df.index = pd.date_range('2024-01-01', periods=1)
        
        result = self.checker.validate_ohlcv(df)
        self.assertEqual(len(result), 0)  # Should remove invalid row
    
    def test_validate_ohlcv_negative_prices(self):
        """Test validation with negative prices"""
        df = pd.DataFrame({
            'open': [100, -50],
            'high': [105, 55],
            'low': [98, 45],
            'close': [104, 52],
            'volume': [1000, 2000]
        })
        df.index = pd.date_range('2024-01-01', periods=2)
        
        result = self.checker.validate_ohlcv(df)
        self.assertEqual(len(result), 1)
    
    def test_detect_gaps(self):
        """Test gap detection"""
        dates = pd.date_range('2024-01-01', periods=10)
        # Insert a gap
        dates = dates.delete(5)
        
        df = pd.DataFrame({'close': range(9)}, index=dates)
        gaps = self.checker.detect_gaps(df, max_gap_days=1)
        
        self.assertEqual(len(gaps), 1)


class TestDataCacheManager(unittest.TestCase):
    """Test cache functionality"""
    
    def setUp(self):
        # Use temp cache for tests
        self.cache = DataCacheManager(cache_dir=".test_cache")
    
    def tearDown(self):
        # Clean up
        self.cache.clear_cache()
        import shutil
        if Path(".test_cache").exists():
            shutil.rmtree(".test_cache")
    
    def test_store_and_retrieve_ohlcv(self):
        """Test storing and retrieving OHLCV data"""
        # Create test data with proper datetime index
        dates = pd.date_range('2024-01-01', periods=3, freq='D')
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [98.0, 99.0, 100.0],
            'close': [104.0, 105.0, 106.0],
            'volume': [1000, 2000, 3000],
            'adjusted_close': [104.0, 105.0, 106.0],
            'quality_score': [0.95, 0.95, 0.95]
        }, index=dates)
        
        # Store
        self.cache.store_ohlcv('TEST', df, 'test_source')
        
        # Retrieve
        result = self.cache.get_ohlcv('TEST', days=30)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
    
    def test_cache_status(self):
        """Test cache status reporting"""
        status = self.cache.get_cache_status()
        self.assertIsNotNone(status.cache_dir)
        self.assertIsInstance(status.size_bytes, int)
    
    def test_store_and_retrieve_fundamentals(self):
        """Test storing and retrieving fundamental data"""
        fundamentals = FundamentalData(
            symbol='TEST',
            pe_ratio=25.5,
            pb_ratio=3.2,
            market_cap=1000000000.0,
            last_updated=datetime.now()
        )
        
        self.cache.store_fundamentals(fundamentals)
        result = self.cache.get_fundamentals('TEST')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, 'TEST')
        self.assertEqual(result.pe_ratio, 25.5)


class TestTechnicalIndicators(unittest.TestCase):
    """Test technical indicator calculations"""
    
    def setUp(self):
        # Generate synthetic price data
        np.random.seed(42)
        n = 100
        trend = np.linspace(100, 150, n)
        noise = np.random.randn(n) * 2
        prices = trend + noise
        
        self.prices = pd.Series(prices)
        self.high = pd.Series(prices + np.abs(np.random.randn(n) * 3))
        self.low = pd.Series(prices - np.abs(np.random.randn(n) * 3))
        self.volume = pd.Series(np.random.randint(1000, 10000, n))
    
    def test_sma(self):
        """Test Simple Moving Average"""
        sma = TechnicalIndicators.sma(self.prices, window=20)
        self.assertEqual(len(sma), len(self.prices))
        self.assertTrue(sma.iloc[19:].notna().all())  # First 19 should be NaN
    
    def test_ema(self):
        """Test Exponential Moving Average"""
        ema = TechnicalIndicators.ema(self.prices, window=20)
        self.assertEqual(len(ema), len(self.prices))
        self.assertTrue(ema.iloc[19:].notna().all())
    
    def test_macd(self):
        """Test MACD calculation"""
        macd, signal, hist = TechnicalIndicators.macd(self.prices)
        self.assertEqual(len(macd), len(self.prices))
        self.assertEqual(len(signal), len(self.prices))
        self.assertEqual(len(hist), len(self.prices))
        
        # Histogram should be MACD - Signal
        pd.testing.assert_series_equal(hist, macd - signal, check_names=False)
    
    def test_rsi(self):
        """Test RSI calculation"""
        rsi = TechnicalIndicators.rsi(self.prices, window=14)
        self.assertEqual(len(rsi), len(self.prices))
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all() and (valid_rsi <= 100).all())
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands"""
        upper, middle, lower = TechnicalIndicators.bollinger_bands(self.prices)
        
        # Upper should be > Middle > Lower
        valid_idx = upper.notna() & middle.notna() & lower.notna()
        self.assertTrue((upper[valid_idx] >= middle[valid_idx]).all())
        self.assertTrue((middle[valid_idx] >= lower[valid_idx]).all())
    
    def test_atr(self):
        """Test Average True Range"""
        atr = TechnicalIndicators.atr(self.high, self.low, self.prices, window=14)
        self.assertEqual(len(atr), len(self.prices))
        self.assertTrue(atr.dropna().gt(0).all())  # ATR should be positive
    
    def test_stochastic(self):
        """Test Stochastic Oscillator"""
        k, d = TechnicalIndicators.stochastic(self.high, self.low, self.prices)
        
        self.assertEqual(len(k), len(self.prices))
        self.assertEqual(len(d), len(self.prices))
        
        # %K and %D should be between 0 and 100
        valid_k = k.dropna()
        self.assertTrue((valid_k >= 0).all() and (valid_k <= 100).all())
    
    def test_williams_r(self):
        """Test Williams %R"""
        wr = TechnicalIndicators.williams_r(self.high, self.low, self.prices)
        
        valid_wr = wr.dropna()
        self.assertTrue((valid_wr >= -100).all() and (valid_wr <= 0).all())
    
    def test_cci(self):
        """Test Commodity Channel Index"""
        cci = TechnicalIndicators.cci(self.high, self.low, self.prices)
        self.assertEqual(len(cci), len(self.prices))
    
    def test_roc(self):
        """Test Rate of Change"""
        roc = TechnicalIndicators.roc(self.prices, window=10)
        self.assertEqual(len(roc), len(self.prices))
    
    def test_adx(self):
        """Test ADX"""
        adx = TechnicalIndicators.adx(self.high, self.low, self.prices)
        self.assertEqual(len(adx), len(self.prices))
        
        valid_adx = adx.dropna()
        self.assertTrue((valid_adx >= 0).all() and (valid_adx <= 100).all())
    
    def test_obv(self):
        """Test On-Balance Volume"""
        obv = TechnicalIndicators.obv(self.prices, self.volume)
        self.assertEqual(len(obv), len(self.prices))
    
    def test_vwap(self):
        """Test VWAP"""
        vwap = TechnicalIndicators.vwap(self.high, self.low, self.prices, self.volume)
        self.assertEqual(len(vwap), len(self.prices))


class TestVolatilityIndicators(unittest.TestCase):
    """Test volatility indicators"""
    
    def setUp(self):
        np.random.seed(42)
        n = 100
        returns = np.random.randn(n) * 0.02  # 2% daily vol
        prices = 100 * np.exp(np.cumsum(returns))
        
        self.prices = pd.Series(prices)
        self.high = pd.Series(prices * (1 + np.abs(np.random.randn(n) * 0.01)))
        self.low = pd.Series(prices * (1 - np.abs(np.random.randn(n) * 0.01)))
    
    def test_historical_volatility(self):
        """Test historical volatility"""
        vol = VolatilityIndicators.historical_volatility(self.prices, window=20)
        self.assertEqual(len(vol), len(self.prices))
        self.assertTrue(vol.dropna().gt(0).all())
    
    def test_parkinson_volatility(self):
        """Test Parkinson volatility"""
        vol = VolatilityIndicators.parkinson_volatility(self.high, self.low, window=20)
        self.assertEqual(len(vol), len(self.prices))
        self.assertTrue(vol.dropna().gt(0).all())


class TestFeatureService(unittest.TestCase):
    """Test FeatureService"""
    
    def setUp(self):
        self.service = FeatureService()
        
        # Generate test market data
        np.random.seed(42)
        n = 100
        
        base_price = 100
        returns = np.random.randn(n) * 0.01
        prices = [base_price]
        for r in returns[1:]:
            prices.append(prices[-1] * (1 + r))
        
        self.market_data = []
        for i in range(n):
            price = prices[i]
            self.market_data.append(MarketData(
                symbol='TEST',
                timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                open=price * 0.99,
                high=price * 1.02,
                low=price * 0.98,
                close=price,
                volume=np.random.randint(1000, 10000),
                source='test'
            ))
    
    def test_compute_features(self):
        """Test feature computation"""
        features = self.service.compute_features(self.market_data)
        
        self.assertEqual(len(features), len(self.market_data))
        
        # Check first feature vector
        fv = features[50]  # Middle of series
        self.assertEqual(fv.symbol, 'TEST')
        self.assertIn('rsi_14', fv.features)
        self.assertIn('macd', fv.features)
        self.assertIn('bb_upper', fv.features)
        self.assertIn('atr_14', fv.features)
    
    def test_insufficient_data_error(self):
        """Test error on insufficient data"""
        short_data = self.market_data[:10]
        
        with self.assertRaises(InsufficientDataError):
            self.service.compute_features(short_data)
    
    def test_feature_names(self):
        """Test feature name retrieval"""
        names = self.service.get_feature_names()
        
        self.assertIn('rsi_14', names)
        self.assertIn('sma_20', names)
        self.assertIn('macd', names)
        self.assertIn('atr_14', names)


class TestDataService(unittest.TestCase):
    """Test DataService (requires network or mock)"""
    
    def setUp(self):
        self.service = DataService(cache_dir=".test_service_cache")
    
    def tearDown(self):
        self.service.cache.clear_cache()
        import shutil
        if Path(".test_service_cache").exists():
            shutil.rmtree(".test_service_cache")
    
    def test_service_initialization(self):
        """Test DataService initialization"""
        self.assertIsNotNone(self.service.cache)
        self.assertIsNotNone(self.service.quality_checker)
    
    def test_cache_status(self):
        """Test getting cache status"""
        status = self.service.get_cache_status()
        self.assertIsNotNone(status)
        self.assertIsInstance(status.num_symbols, int)


class TestIntegrationPhase1(unittest.TestCase):
    """Integration tests for Phase 1 components"""
    
    def setUp(self):
        self.data_service = DataService(cache_dir=".test_integration_cache")
        self.feature_service = FeatureService()
        
        # Generate test data
        np.random.seed(42)
        n = 100
        
        self.market_data = []
        price = 100.0
        for i in range(n):
            price = price * (1 + np.random.randn() * 0.02)
            self.market_data.append(MarketData(
                symbol='AAPL',
                timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                open=price * 0.995,
                high=price * 1.02,
                low=price * 0.98,
                close=price,
                volume=np.random.randint(1000000, 5000000),
                source='test'
            ))
    
    def tearDown(self):
        self.data_service.cache.clear_cache()
        import shutil
        if Path(".test_integration_cache").exists():
            shutil.rmtree(".test_integration_cache")
    
    def test_data_to_features_pipeline(self):
        """Test complete data -> features pipeline"""
        # Step 1: Validate data
        df = pd.DataFrame([{
            'open': md.open,
            'high': md.high,
            'low': md.low,
            'close': md.close,
            'volume': md.volume
        } for md in self.market_data])
        
        validated = self.data_service.quality_checker.validate_ohlcv(df)
        self.assertGreater(len(validated), 0)
        
        # Step 2: Cache data
        self.data_service.cache.store_ohlcv('AAPL', df, 'test')
        cached = self.data_service.cache.get_ohlcv('AAPL', days=100)
        self.assertIsNotNone(cached)
        
        # Step 3: Compute features
        features = self.feature_service.compute_features(self.market_data)
        self.assertEqual(len(features), len(self.market_data))
        
        # Step 4: Verify feature vector
        fv = features[-1]
        self.assertIsNotNone(fv.values_array)
        self.assertEqual(len(fv.values_array), len(fv.feature_names))


def run_tests():
    """Run all Phase 1 tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataQualityChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestDataCacheManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestVolatilityIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureService))
    suite.addTests(loader.loadTestsFromTestCase(TestDataService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationPhase1))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
