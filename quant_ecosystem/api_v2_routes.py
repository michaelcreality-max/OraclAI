"""
Unified API Routes for Complete Trading System
Exposes all three upgrade layers via REST API
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any
import logging

log = logging.getLogger(__name__)

# Create blueprint
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# Initialize systems (lazy load to avoid circular imports)
_data_ingestion = None
_modular_orchestrator = None
_execution_engine = None

def get_data_ingestion():
    global _data_ingestion
    if _data_ingestion is None:
        from quant_ecosystem.data_ingestion_layer import AdvancedDataIngestionLayer
        _data_ingestion = AdvancedDataIngestionLayer()
    return _data_ingestion

def get_modular_orchestrator():
    global _modular_orchestrator
    if _modular_orchestrator is None:
        from quant_ecosystem.modular_services import ModularSystemOrchestrator
        _modular_orchestrator = ModularSystemOrchestrator()
    return _modular_orchestrator

def get_execution_engine():
    global _execution_engine
    if _execution_engine is None:
        from quant_ecosystem.execution_realism import RealisticExecutionEngine
        _execution_engine = RealisticExecutionEngine(initial_capital=100000.0)
    return _execution_engine


# =============================================================================
# DATA INGESTION LAYER ENDPOINTS
# =============================================================================

@api_v2.route('/data/ingestion/status', methods=['GET'])
def data_ingestion_status():
    """Get data ingestion system status"""
    try:
        ingestion = get_data_ingestion()
        return jsonify({
            'success': True,
            'status': ingestion.get_system_status()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/data/ingestion/fetch/<symbol>', methods=['GET'])
def fetch_stock_data(symbol):
    """Fetch comprehensive data for a stock"""
    try:
        period = request.args.get('period', '1y')
        ingestion = get_data_ingestion()
        data = ingestion.get_data(symbol.upper(), period=period)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'data_points': len(data),
            'data': [d.to_dict() for d in data] if data else [],
            'quality_score': data[0].data_quality_score if data else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/data/ingestion/batch', methods=['POST'])
def fetch_batch_data():
    """Fetch data for multiple symbols"""
    try:
        symbols = request.json.get('symbols', [])
        period = request.json.get('period', '1y')
        
        ingestion = get_data_ingestion()
        results = ingestion.get_batch_data(symbols, period=period)
        
        return jsonify({
            'success': True,
            'results': {
                symbol: {
                    'data_points': len(data),
                    'quality_score': data[0].data_quality_score if data else 0
                }
                for symbol, data in results.items()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/data/quality/check/<symbol>', methods=['GET'])
def check_data_quality(symbol):
    """Check data quality for a symbol"""
    try:
        ingestion = get_data_ingestion()
        data = ingestion.get_data(symbol.upper(), period='1mo')
        
        if not data:
            return jsonify({'success': False, 'error': 'No data available'}), 404
        
        # Run quality checks
        from quant_ecosystem.data_ingestion_layer import DataQualityChecker
        import pandas as pd
        
        df = pd.DataFrame([d.to_dict() for d in data])
        checker = DataQualityChecker()
        validated_df = checker.validate_price_data(df)
        quality_score = checker.calculate_data_quality_score(df)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'quality_score': quality_score,
            'total_rows': len(df),
            'valid_rows': len(validated_df),
            'missing_values': int(df.isna().sum().sum()),
            'issues': []
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# MODULAR SERVICES ENDPOINTS
# =============================================================================

@api_v2.route('/services/health', methods=['GET'])
def services_health():
    """Get health status of all modular services"""
    try:
        orchestrator = get_modular_orchestrator()
        return jsonify({
            'success': True,
            'health': orchestrator.get_system_health()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/services/analyze/<symbol>', methods=['GET'])
def analyze_stock(symbol):
    """Run full analysis pipeline for a stock"""
    try:
        orchestrator = get_modular_orchestrator()
        result = orchestrator.analyze_stock(symbol.upper())
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/services/analyze/batch', methods=['POST'])
def analyze_batch():
    """Analyze multiple stocks"""
    try:
        symbols = request.json.get('symbols', [])
        orchestrator = get_modular_orchestrator()
        results = orchestrator.analyze_batch(symbols)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/services/logs', methods=['GET'])
def get_service_logs():
    """Get system logs"""
    try:
        service = request.args.get('service')
        limit = int(request.args.get('limit', 50))
        
        orchestrator = get_modular_orchestrator()
        logs = orchestrator.get_logs(service=service, limit=limit)
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# EXECUTION REALISM ENDPOINTS
# =============================================================================

@api_v2.route('/execution/status', methods=['GET'])
def execution_status():
    """Get execution engine status"""
    try:
        engine = get_execution_engine()
        return jsonify({
            'success': True,
            'portfolio': engine.get_portfolio_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/execution/order', methods=['POST'])
def submit_order():
    """Submit a trade order"""
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        side = data.get('side', 'buy').lower()
        quantity = float(data.get('quantity', 0))
        order_type = data.get('order_type', 'market').lower()
        
        from quant_ecosystem.execution_realism import OrderSide, OrderType
        
        side_enum = OrderSide.BUY if side == 'buy' else OrderSide.SELL
        type_enum = OrderType.MARKET
        if order_type == 'limit':
            type_enum = OrderType.LIMIT
        elif order_type == 'stop':
            type_enum = OrderType.STOP
        
        engine = get_execution_engine()
        
        # Update market data first
        engine.update_market_data(
            symbol, 
            price=data.get('current_price', 100.0),
            volume=data.get('volume', 1000000),
            volatility=data.get('volatility', 0.25)
        )
        
        order = engine.submit_order(
            symbol=symbol,
            side=side_enum,
            quantity=quantity,
            order_type=type_enum,
            limit_price=data.get('limit_price'),
            stop_price=data.get('stop_price')
        )
        
        return jsonify({
            'success': order.status.value != 'rejected',
            'order': {
                'order_id': order.order_id,
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': order.quantity,
                'status': order.status.value,
                'fill_price': order.fill_price,
                'fill_quantity': order.fill_quantity,
                'slippage': order.slippage,
                'commission': order.commission,
                'rejection_reason': order.rejection_reason
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/execution/portfolio', methods=['GET'])
def get_portfolio():
    """Get complete portfolio summary"""
    try:
        engine = get_execution_engine()
        return jsonify({
            'success': True,
            'portfolio': engine.get_portfolio_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/execution/trades', methods=['GET'])
def get_trade_history():
    """Get trade history"""
    try:
        limit = int(request.args.get('limit', 50))
        engine = get_execution_engine()
        trades = engine.performance_tracker.get_trade_history(limit=limit)
        
        return jsonify({
            'success': True,
            'trades': trades
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/execution/risk', methods=['GET'])
def get_risk_metrics():
    """Get risk metrics"""
    try:
        engine = get_execution_engine()
        return jsonify({
            'success': True,
            'risk': engine.risk_manager.get_risk_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/execution/check-stops', methods=['POST'])
def check_stop_losses():
    """Check and execute stop losses"""
    try:
        engine = get_execution_engine()
        engine.check_stop_losses()
        
        return jsonify({
            'success': True,
            'message': 'Stop losses checked',
            'portfolio': engine.get_portfolio_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# UNIFIED SYSTEM ENDPOINTS
# =============================================================================

@api_v2.route('/system/status', methods=['GET'])
def system_status():
    """Get complete system status"""
    try:
        # Check all systems
        ingestion = get_data_ingestion()
        orchestrator = get_modular_orchestrator()
        engine = get_execution_engine()
        
        return jsonify({
            'success': True,
            'system_status': 'operational',
            'data_ingestion': ingestion.get_system_status(),
            'modular_services': orchestrator.get_system_health(),
            'execution_engine': engine.get_portfolio_summary(),
            'version': '2.0.0',
            'features': [
                'advanced_data_ingestion',
                'modular_services',
                'parallel_execution',
                'execution_realism',
                'risk_management',
                'performance_tracking'
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_v2.route('/system/full-analysis/<symbol>', methods=['GET'])
def full_analysis(symbol):
    """Run complete analysis pipeline with execution simulation"""
    try:
        symbol = symbol.upper()
        
        # 1. Fetch data
        ingestion = get_data_ingestion()
        data = ingestion.get_data(symbol, period='1y')
        
        # 2. Run agent analysis
        orchestrator = get_modular_orchestrator()
        analysis = orchestrator.analyze_stock(symbol)
        
        # 3. Simulate execution if there's a consensus
        engine = get_execution_engine()
        
        consensus = analysis.get('consensus', 'hold')
        simulated_order = None
        
        if consensus in ['buy', 'sell']:
            from quant_ecosystem.execution_realism import OrderSide
            side = OrderSide.BUY if consensus == 'buy' else OrderSide.SELL
            
            # Get latest price
            latest_price = data[-1].close_price if data else 100.0
            engine.update_market_data(symbol, price=latest_price)
            
            # Simulate 100 share order
            simulated_order = engine.submit_order(
                symbol=symbol,
                side=side,
                quantity=100
            )
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data_summary': {
                'data_points': len(data),
                'quality_score': data[0].data_quality_score if data else 0,
                'latest_price': data[-1].close_price if data else None
            },
            'analysis': analysis,
            'simulated_execution': {
                'order_id': simulated_order.order_id if simulated_order else None,
                'status': simulated_order.status.value if simulated_order else 'none',
                'fill_price': simulated_order.fill_price if simulated_order else None,
                'slippage': simulated_order.slippage if simulated_order else None,
                'commission': simulated_order.commission if simulated_order else None
            } if simulated_order else None,
            'risk_status': engine.risk_manager.get_risk_summary()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# API Documentation
@api_v2.route('/docs', methods=['GET'])
def api_docs():
    """Get API documentation"""
    return jsonify({
        'version': '2.0.0',
        'description': 'Advanced Trading System API with Data Ingestion, Modular Services, and Execution Realism',
        'endpoints': {
            'data_ingestion': {
                'GET /api/v2/data/ingestion/status': 'System status',
                'GET /api/v2/data/ingestion/fetch/<symbol>': 'Fetch stock data',
                'POST /api/v2/data/ingestion/batch': 'Batch fetch data',
                'GET /api/v2/data/quality/check/<symbol>': 'Check data quality'
            },
            'modular_services': {
                'GET /api/v2/services/health': 'Services health',
                'GET /api/v2/services/analyze/<symbol>': 'Analyze stock',
                'POST /api/v2/services/analyze/batch': 'Batch analysis',
                'GET /api/v2/services/logs': 'System logs'
            },
            'execution_realism': {
                'GET /api/v2/execution/status': 'Execution status',
                'POST /api/v2/execution/order': 'Submit order',
                'GET /api/v2/execution/portfolio': 'Portfolio summary',
                'GET /api/v2/execution/trades': 'Trade history',
                'GET /api/v2/execution/risk': 'Risk metrics',
                'POST /api/v2/execution/check-stops': 'Check stop losses'
            },
            'unified': {
                'GET /api/v2/system/status': 'Complete system status',
                'GET /api/v2/system/full-analysis/<symbol>': 'Full analysis with execution'
            }
        }
    })
