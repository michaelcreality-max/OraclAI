"""
Phase 2 Test Suite
Tests for MLService and SignalService
"""

import unittest
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_structures import (
    FeatureVector, FeatureMatrix, ModelPrediction, TradingSignal, SignalType
)
from ml.ml_service import MLService, LinearModels, TreeModels, EnsembleWeighter
from services.signal_service import SignalService, SignalGenerator


class TestEnsembleWeighter(unittest.TestCase):
    """Test ensemble weight management"""
    
    def setUp(self):
        self.models = ['model_a', 'model_b', 'model_c']
        self.weighter = EnsembleWeighter(self.models)
    
    def test_initial_weights(self):
        """Test initial weights are equal"""
        weights = self.weighter.get_weights()
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(weights['model_a'], 1/3, places=5)
        self.assertAlmostEqual(weights['model_b'], 1/3, places=5)
        self.assertAlmostEqual(weights['model_c'], 1/3, places=5)
    
    def test_weight_update(self):
        """Test weight update based on performance"""
        # Model A performs best
        performance = {
            'model_a': 0.8,
            'model_b': 0.5,
            'model_c': 0.3
        }
        
        self.weighter.update_weights(performance)
        weights = self.weighter.get_weights()
        
        # Best performer should have highest weight
        self.assertGreater(weights['model_a'], weights['model_b'])
        self.assertGreater(weights['model_b'], weights['model_c'])
        
        # Weights should still sum to 1
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)
    
    def test_weight_momentum(self):
        """Test that old weights are not completely replaced"""
        # Set initial weights
        self.weighter.weights = {'model_a': 0.5, 'model_b': 0.3, 'model_c': 0.2}
        
        # Update with new performance
        performance = {'model_a': 0.3, 'model_b': 0.8, 'model_c': 0.4}
        self.weighter.update_weights(performance)
        
        weights = self.weighter.get_weights()
        
        # Even though B performed best, A should retain some weight due to momentum
        self.assertGreater(weights['model_a'], 0.1)


class TestLinearModels(unittest.TestCase):
    """Test linear model implementations"""
    
    def setUp(self):
        self.models = LinearModels()
        # Generate synthetic data
        np.random.seed(42)
        n = 200
        X = np.random.randn(n, 10)
        y = X[:, 0] * 0.5 + X[:, 1] * 0.3 + np.random.randn(n) * 0.1
        self.X = X
        self.y = y
    
    def test_fit_and_predict(self):
        """Test fitting and prediction"""
        self.models.fit(self.X, self.y)
        
        self.assertTrue(self.models.is_fitted)
        
        predictions = self.models.predict(self.X[:10])
        self.assertIn('ridge', predictions)
        self.assertIn('elastic', predictions)
        self.assertIn('logistic_proba', predictions)
        
        self.assertEqual(len(predictions['ridge']), 10)
    
    def test_prediction_shape(self):
        """Test prediction shapes"""
        self.models.fit(self.X, self.y)
        preds = self.models.predict(self.X[:5])
        
        self.assertEqual(preds['ridge'].shape, (5,))
        self.assertEqual(preds['elastic'].shape, (5,))
        self.assertEqual(preds['logistic_proba'].shape, (5,))


class TestTreeModels(unittest.TestCase):
    """Test tree-based models"""
    
    def setUp(self):
        self.models = TreeModels()
        np.random.seed(42)
        n = 200
        X = np.random.randn(n, 10)
        y = X[:, 0] * 0.5 + X[:, 1] * 0.3 + np.random.randn(n) * 0.1
        self.X = X
        self.y = y
    
    def test_fit_and_predict(self):
        """Test fitting and prediction"""
        self.models.fit(self.X, self.y)
        
        self.assertTrue(self.models.is_fitted)
        
        predictions = self.models.predict(self.X[:10])
        self.assertIn('random_forest', predictions)
        self.assertIn('gradient_boost', predictions)
        
        self.assertEqual(len(predictions['random_forest']), 10)
    
    def test_different_predictions(self):
        """Test that RF and GB give different predictions"""
        self.models.fit(self.X, self.y)
        preds = self.models.predict(self.X[:20])
        
        # Predictions should be correlated but not identical
        rf_preds = preds['random_forest']
        gb_preds = preds['gradient_boost']
        
        correlation = np.corrcoef(rf_preds, gb_preds)[0, 1]
        self.assertGreater(correlation, 0.5)  # Should be correlated
        
        # But not identical
        self.assertFalse(np.allclose(rf_preds, gb_preds))


class TestMLService(unittest.TestCase):
    """Test MLService"""
    
    def setUp(self):
        self.service = MLService()
        
        # Generate synthetic feature data
        np.random.seed(42)
        n_samples = 200
        n_features = 20
        
        features = np.random.randn(n_samples, n_features)
        # Target: combination of first few features + noise
        returns = (
            features[:, 0] * 0.3 +
            features[:, 1] * 0.2 +
            features[:, 2] * 0.1 +
            np.random.randn(n_samples) * 0.05
        )
        
        self.feature_matrix = FeatureMatrix(
            symbols=[f'STOCK_{i}' for i in range(n_samples)],
            timestamps=[datetime.now() - timedelta(days=i) for i in range(n_samples)],
            features=features,
            feature_names=[f'feature_{i}' for i in range(n_features)]
        )
        self.returns = returns
    
    def test_train(self):
        """Test model training"""
        result = self.service.train(self.feature_matrix, self.returns)
        
        self.assertTrue(self.service.is_fitted)
        self.assertIn('cv_scores', result)
        self.assertIn('ensemble_weights', result)
        self.assertIn('n_samples', result)
        
        # Check CV scores exist for all models
        cv_scores = result['cv_scores']
        self.assertIn('ridge', cv_scores)
        self.assertIn('rf', cv_scores)
        self.assertIn('gb', cv_scores)
    
    def test_predict(self):
        """Test prediction"""
        # First train
        self.service.train(self.feature_matrix, self.returns)
        
        # Create a feature vector
        fv = FeatureVector(
            symbol='TEST',
            timestamp=datetime.now(),
            features={f'feature_{i}': 0.5 for i in range(20)},
            feature_names=[f'feature_{i}' for i in range(20)]
        )
        
        prediction = self.service.predict(fv)
        
        self.assertIsInstance(prediction, ModelPrediction)
        self.assertEqual(prediction.symbol, 'TEST')
        self.assertIn('up', prediction.direction_prob)
        self.assertIn('down', prediction.direction_prob)
        self.assertGreaterEqual(prediction.confidence, 0.0)
        self.assertLessEqual(prediction.confidence, 1.0)
    
    def test_predict_batch(self):
        """Test batch prediction"""
        self.service.train(self.feature_matrix, self.returns)
        
        predictions = self.service.predict_batch(self.feature_matrix)
        
        self.assertEqual(len(predictions), len(self.feature_matrix.symbols))
        
        for pred in predictions:
            self.assertIsInstance(pred, ModelPrediction)
            self.assertIn('up', pred.direction_prob)
    
    def test_insufficient_data_error(self):
        """Test error on insufficient data"""
        small_matrix = FeatureMatrix(
            symbols=['A', 'B'],
            timestamps=[datetime.now(), datetime.now()],
            features=np.array([[1, 2], [3, 4]]),
            feature_names=['f1', 'f2']
        )
        
        with self.assertRaises(Exception):
            self.service.train(small_matrix, np.array([0.1, 0.2]))
    
    def test_get_model_performance(self):
        """Test getting model performance metrics"""
        self.service.train(self.feature_matrix, self.returns)
        
        metrics = self.service.get_model_performance()
        
        self.assertIn('ridge', metrics)
        self.assertIn('elastic', metrics)


class TestSignalGenerator(unittest.TestCase):
    """Test signal generation"""
    
    def setUp(self):
        self.generator = SignalGenerator()
    
    def test_generate_buy_signal(self):
        """Test BUY signal generation"""
        prediction = ModelPrediction(
            symbol='AAPL',
            direction_prob={'up': 0.75, 'down': 0.20, 'flat': 0.05},
            expected_return=0.05,
            confidence=0.70,
            model_contributions={},
            timestamp=datetime.now()
        )
        
        signal = self.generator.generate_signal(prediction)
        
        self.assertEqual(signal.signal, SignalType.BUY)
        self.assertEqual(signal.symbol, 'AAPL')
        self.assertIn('high_up_probability', signal.reasoning.primary_factors)
    
    def test_generate_sell_signal(self):
        """Test SELL signal generation"""
        prediction = ModelPrediction(
            symbol='TSLA',
            direction_prob={'up': 0.15, 'down': 0.80, 'flat': 0.05},
            expected_return=-0.04,
            confidence=0.72,
            model_contributions={},
            timestamp=datetime.now()
        )
        
        signal = self.generator.generate_signal(prediction)
        
        self.assertEqual(signal.signal, SignalType.SELL)
        self.assertIn('high_down_probability', signal.reasoning.primary_factors)
    
    def test_generate_hold_signal(self):
        """Test HOLD signal generation"""
        prediction = ModelPrediction(
            symbol='MSFT',
            direction_prob={'up': 0.45, 'down': 0.45, 'flat': 0.10},
            expected_return=0.005,
            confidence=0.50,
            model_contributions={},
            timestamp=datetime.now()
        )
        
        signal = self.generator.generate_signal(prediction)
        
        self.assertEqual(signal.signal, SignalType.HOLD)
    
    def test_signal_confidence_levels(self):
        """Test that confidence is properly bounded"""
        prediction = ModelPrediction(
            symbol='TEST',
            direction_prob={'up': 0.90, 'down': 0.05, 'flat': 0.05},
            expected_return=0.08,
            confidence=0.85,
            model_contributions={},
            timestamp=datetime.now()
        )
        
        signal = self.generator.generate_signal(prediction)
        
        self.assertGreaterEqual(signal.confidence, 0.0)
        self.assertLessEqual(signal.confidence, 1.0)
    
    def test_signal_history_tracking(self):
        """Test that signals are tracked in history"""
        prediction = ModelPrediction(
            symbol='AAPL',
            direction_prob={'up': 0.70, 'down': 0.20, 'flat': 0.10},
            expected_return=0.03,
            confidence=0.65,
            model_contributions={},
            timestamp=datetime.now()
        )
        
        initial_count = len(self.generator.signal_history)
        self.generator.generate_signal(prediction)
        
        self.assertEqual(len(self.generator.signal_history), initial_count + 1)
    
    def test_get_signal_statistics(self):
        """Test signal statistics calculation"""
        # Generate several signals
        for i, signal_type in enumerate(['buy', 'buy', 'sell', 'hold', 'buy']):
            if signal_type == 'buy':
                prob = {'up': 0.75, 'down': 0.15, 'flat': 0.10}
            elif signal_type == 'sell':
                prob = {'up': 0.15, 'down': 0.75, 'flat': 0.10}
            else:
                prob = {'up': 0.45, 'down': 0.45, 'flat': 0.10}
            
            prediction = ModelPrediction(
                symbol=f'STOCK_{i}',
                direction_prob=prob,
                expected_return=0.02,
                confidence=0.65,
                model_contributions={},
                timestamp=datetime.now()
            )
            self.generator.generate_signal(prediction)
        
        stats = self.generator.get_signal_statistics(days=1)
        
        self.assertEqual(stats['total_signals'], 5)
        self.assertEqual(stats['buy_count'], 3)
        self.assertEqual(stats['sell_count'], 1)
        self.assertEqual(stats['hold_count'], 1)


class TestSignalService(unittest.TestCase):
    """Test SignalService"""
    
    def setUp(self):
        self.service = SignalService()
    
    def test_generate_batch(self):
        """Test batch signal generation"""
        predictions = [
            ModelPrediction(
                symbol='AAPL',
                direction_prob={'up': 0.75, 'down': 0.15, 'flat': 0.10},
                expected_return=0.03,
                confidence=0.65,
                model_contributions={},
                timestamp=datetime.now()
            ),
            ModelPrediction(
                symbol='TSLA',
                direction_prob={'up': 0.20, 'down': 0.70, 'flat': 0.10},
                expected_return=-0.03,
                confidence=0.65,
                model_contributions={},
                timestamp=datetime.now()
            )
        ]
        
        signals = self.service.generate_batch(predictions)
        
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0].signal, SignalType.BUY)
        self.assertEqual(signals[1].signal, SignalType.SELL)


class TestIntegrationPhase2(unittest.TestCase):
    """Integration tests for Phase 2"""
    
    def setUp(self):
        self.ml_service = MLService()
        self.signal_service = SignalService()
        
        # Generate synthetic data
        np.random.seed(42)
        n_samples = 150
        n_features = 15
        
        features = np.random.randn(n_samples, n_features)
        returns = (
            features[:, 0] * 0.25 +
            features[:, 1] * 0.15 +
            np.random.randn(n_samples) * 0.03
        )
        
        self.feature_matrix = FeatureMatrix(
            symbols=[f'STOCK_{i}' for i in range(n_samples)],
            timestamps=[datetime.now() - timedelta(days=i) for i in range(n_samples)],
            features=features,
            feature_names=[f'feature_{i}' for i in range(n_features)]
        )
        self.returns = returns
    
    def test_ml_to_signal_pipeline(self):
        """Test complete ML -> Signal pipeline"""
        # Step 1: Train models
        train_result = self.ml_service.train(self.feature_matrix, self.returns)
        self.assertIn('cv_scores', train_result)
        
        # Step 2: Generate predictions
        predictions = self.ml_service.predict_batch(self.feature_matrix[:5])
        self.assertEqual(len(predictions), 5)
        
        # Step 3: Generate signals
        signals = self.signal_service.generate_batch(predictions)
        self.assertEqual(len(signals), 5)
        
        # Step 4: Verify signals have proper structure
        for signal in signals:
            self.assertIn(signal.signal, [SignalType.BUY, SignalType.SELL, SignalType.HOLD])
            self.assertIsNotNone(signal.reasoning)


def run_tests():
    """Run all Phase 2 tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEnsembleWeighter))
    suite.addTests(loader.loadTestsFromTestCase(TestLinearModels))
    suite.addTests(loader.loadTestsFromTestCase(TestTreeModels))
    suite.addTests(loader.loadTestsFromTestCase(TestMLService))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationPhase2))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
