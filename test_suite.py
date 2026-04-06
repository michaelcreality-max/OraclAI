"""
Production Testing Framework
Comprehensive test suite for all system components
"""

import os
import sys
import json
import unittest
from typing import Dict, List, Any, Optional
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil


class BaseTestCase(unittest.TestCase):
    """Base test case with common utilities"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def assertValidJSON(self, data: Any):
        """Assert that data can be serialized to JSON"""
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            self.fail(f"Data is not valid JSON: {e}")
    
    def assertHasKeys(self, data: Dict, keys: List[str]):
        """Assert that dictionary has all required keys"""
        for key in keys:
            self.assertIn(key, data, f"Missing required key: {key}")


class TestWebsiteBuilder(BaseTestCase):
    """Test website builder functionality"""
    
    def setUp(self):
        super().setUp()
        from website_builder_real import RealWebsiteBuilder
        self.builder = RealWebsiteBuilder()
    
    def test_analyze_prompt_basic(self):
        """Test basic prompt analysis"""
        analysis = self.builder.analyze_prompt("Create a business website")
        self.assertHasKeys(analysis, ['template', 'purpose', 'complexity', 'features'])
        self.assertIn(analysis['template'], ['landing', 'business', 'corporate', 'saas_landing'])
    
    def test_analyze_prompt_complexity_detection(self):
        """Test complexity detection"""
        simple = self.builder.analyze_prompt("Simple portfolio")
        complex_site = self.builder.analyze_prompt("E-commerce with cart, payment, user auth")
        
        self.assertEqual(simple['complexity'], 'low')
        self.assertEqual(complex_site['complexity'], 'high')
    
    def test_generate_files(self):
        """Test file generation"""
        analysis = self.builder.analyze_prompt("Coffee shop website")
        files = self.builder.generate_files(analysis)
        
        self.assertIsInstance(files, dict)
        self.assertTrue(len(files) > 0)
        
        # Check for required files
        has_html = any(f.endswith('.html') for f in files.keys())
        has_css = any(f.endswith('.css') for f in files.keys())
        
        self.assertTrue(has_html, "Should generate HTML files")
        self.assertTrue(has_css, "Should generate CSS files")
    
    def test_generate_js_functional(self):
        """Test that generated JavaScript is functional"""
        analysis = {
            'features': ['contact_form', 'dark_mode'],
            'interactivity': ['form_validation', 'theme_toggle'],
            'complexity': 'medium'
        }
        
        js = self.builder._generate_js(analysis)
        
        # Should be valid JavaScript (basic check)
        self.assertIn('document', js)
        self.assertIn('function', js)
        self.assertIn('addEventListener', js)
    
    def test_color_palette_access(self):
        """Test color palette configuration access"""
        palette = self.builder.get_color_palette('modern')
        self.assertIsInstance(palette, dict)
        self.assertTrue(len(palette) > 0)
    
    def test_parameter_count(self):
        """Test parameter counting"""
        count = self.builder.count_total_parameters()
        self.assertIsInstance(count, int)
        self.assertGreater(count, 1000000)


class TestGitHubIntegration(BaseTestCase):
    """Test GitHub integration"""
    
    def setUp(self):
        super().setUp()
        from github_integration import GitHubIntegration
        self.github = GitHubIntegration()
    
    @patch('github_integration.requests.get')
    def test_is_authenticated(self, mock_get):
        """Test authentication check"""
        mock_get.return_value = Mock(status_code=200)
        self.github.token = "test_token"
        self.assertTrue(self.github.is_authenticated())
    
    @patch('github_integration.requests.get')
    def test_get_user(self, mock_get):
        """Test getting user info"""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"login": "testuser", "id": 123}
        )
        self.github.token = "test_token"
        
        user = self.github.get_user()
        self.assertEqual(user['login'], 'testuser')
    
    @patch('github_integration.requests.get')
    def test_list_repositories(self, mock_get):
        """Test listing repositories"""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: [{"name": "repo1"}, {"name": "repo2"}]
        )
        
        repos = self.github.list_repositories("testuser")
        self.assertEqual(len(repos), 2)
    
    @patch('github_integration.requests.post')
    def test_create_repository(self, mock_post):
        """Test repository creation"""
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {"id": 123, "name": "new-repo", "html_url": "https://github.com/user/repo"}
        )
        self.github.token = "test_token"
        
        result = self.github.create_repository("new-repo", "Test repo")
        self.assertTrue(result['success'])
        self.assertEqual(result['name'], 'new-repo')


class TestDatabase(BaseTestCase):
    """Test database operations"""
    
    def setUp(self):
        super().setUp()
        from database import DatabaseManager
        db_path = os.path.join(self.test_dir, 'test.db')
        self.db = DatabaseManager(db_path)
    
    def test_create_user(self):
        """Test user creation"""
        result = self.db.create_user(
            "user_123",
            "test@example.com",
            "testuser",
            password_hash="hashed_password"
        )
        self.assertTrue(result)
        
        # Verify user exists
        user = self.db.get_user("user_123")
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'test@example.com')
    
    def test_create_duplicate_user(self):
        """Test duplicate user handling"""
        self.db.create_user("user_123", "test@example.com", "testuser")
        result = self.db.create_user("user_456", "test@example.com", "testuser2")
        self.assertFalse(result)  # Should fail due to unique constraint
    
    def test_position_operations(self):
        """Test position CRUD"""
        position = {
            'user_id': 'user_123',
            'symbol': 'AAPL',
            'direction': 'long',
            'shares': 100,
            'avg_entry_price': 150.0,
            'current_price': 155.0,
            'market_value': 15500.0,
            'unrealized_pnl': 500.0
        }
        
        # Create
        result = self.db.create_position(position)
        self.assertTrue(result)
        
        # Read
        positions = self.db.get_positions('user_123')
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], 'AAPL')
        
        # Delete
        result = self.db.delete_position('user_123', 'AAPL', 'long')
        self.assertTrue(result)
        
        # Verify deletion
        positions = self.db.get_positions('user_123')
        self.assertEqual(len(positions), 0)
    
    def test_trade_operations(self):
        """Test trade recording"""
        trade = {
            'trade_id': 'trd_001',
            'user_id': 'user_123',
            'symbol': 'AAPL',
            'direction': 'long',
            'entry_price': 150.0,
            'shares': 100,
            'position_value': 15000.0,
            'status': 'open',
            'strategy': 'momentum'
        }
        
        result = self.db.record_trade(trade)
        self.assertTrue(result)
        
        trades = self.db.get_trades('user_123')
        self.assertEqual(len(trades), 1)
    
    def test_analysis_cache(self):
        """Test analysis caching"""
        data = {'signal': 'buy', 'confidence': 0.85}
        
        # Cache
        result = self.db.cache_analysis('AAPL', 'technical', data, ttl_hours=1)
        self.assertTrue(result)
        
        # Retrieve
        cached = self.db.get_cached_analysis('AAPL', 'technical')
        self.assertIsNotNone(cached)
        self.assertEqual(cached['signal'], 'buy')


class TestErrorHandling(BaseTestCase):
    """Test error handling system"""
    
    def test_app_error_creation(self):
        """Test custom error creation"""
        from logging_config import AppError, ValidationError
        
        error = ValidationError("Invalid input", {"field": "required"})
        self.assertEqual(error.code, "VALIDATION_ERROR")
        self.assertEqual(error.status_code, 400)
    
    def test_error_conversion(self):
        """Test error to dict conversion"""
        from logging_config import AppError
        
        error = AppError("Test error", "TEST", 500, {"detail": "info"})
        data = error.to_dict()
        
        self.assertHasKeys(data['error'], ['code', 'message', 'status_code', 'details'])


class TestFinancialAnalysis(BaseTestCase):
    """Test financial analysis components"""
    
    def test_technical_indicators_config(self):
        """Test technical indicators configuration"""
        from financial_config_params import TECHNICAL_INDICATORS
        
        self.assertIn('trend', TECHNICAL_INDICATORS)
        self.assertIn('momentum', TECHNICAL_INDICATORS)
        self.assertIn('volatility', TECHNICAL_INDICATORS)
        
        # Check RSI configuration
        rsi = TECHNICAL_INDICATORS['momentum']['rsi']
        self.assertIn('periods', rsi)
        self.assertTrue(len(rsi['periods']) > 0)
    
    def test_trading_strategies_config(self):
        """Test trading strategies configuration"""
        from financial_config_params import TRADING_STRATEGIES
        
        self.assertIn('trend_following', TRADING_STRATEGIES)
        self.assertIn('mean_reversion', TRADING_STRATEGIES)
    
    def test_risk_management_config(self):
        """Test risk management configuration"""
        from financial_config_params import RISK_MANAGEMENT
        
        self.assertIn('position_sizing', RISK_MANAGEMENT)
        self.assertIn('stop_loss', RISK_MANAGEMENT)
        
        # Check position sizing methods
        methods = RISK_MANAGEMENT['position_sizing']['methods']
        self.assertIn('kelly', methods)


class TestSystemConfig(BaseTestCase):
    """Test system configuration"""
    
    def test_ensemble_config(self):
        """Test ensemble configuration"""
        from system_config_params import ENSEMBLE_CONFIG
        
        self.assertIn('voting_ensemble', ENSEMBLE_CONFIG)
        self.assertIn('stacking_ensemble', ENSEMBLE_CONFIG)
        self.assertIn('boosting_ensemble', ENSEMBLE_CONFIG)
    
    def test_deployment_config(self):
        """Test deployment configuration"""
        from system_config_params import DEPLOYMENT_CONFIG
        
        self.assertIn('infrastructure', DEPLOYMENT_CONFIG)
        self.assertIn('containers', DEPLOYMENT_CONFIG)


class TestIntegration(BaseTestCase):
    """Integration tests"""
    
    def test_full_website_generation_flow(self):
        """Test complete website generation flow"""
        from website_builder_real import RealWebsiteBuilder
        
        builder = RealWebsiteBuilder()
        
        # Analyze
        analysis = builder.analyze_prompt("Restaurant with menu and reservation form")
        
        # Generate
        files = builder.generate_files(analysis)
        
        # Verify structure
        self.assertTrue(any('index.html' in f for f in files.keys()))
        self.assertTrue(any('.css' in f for f in files.keys()))
    
    def test_github_deployment_workflow(self):
        """Test GitHub deployment workflow"""
        from github_integration import deploy_website_to_github, GitHubIntegration
        
        # Without auth
        result = deploy_website_to_github("user", "repo", {"test.html": "<html></html>"})
        self.assertFalse(result['success'])
        self.assertIn('setup_instructions', result)


def run_all_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestWebsiteBuilder,
        TestGitHubIntegration,
        TestDatabase,
        TestErrorHandling,
        TestFinancialAnalysis,
        TestSystemConfig,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        "success": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped)
    }


if __name__ == '__main__':
    results = run_all_tests()
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    print(f"Success: {results['success']}")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Failures: {results['failures']}")
    print(f"Errors: {results['errors']}")
    print(f"Skipped: {results['skipped']}")
    
    sys.exit(0 if results['success'] else 1)
