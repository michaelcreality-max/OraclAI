#!/usr/bin/env python3
"""
Production Server with Multi-Agent AI Debate System
Optimized for external frontend access (Lovable, etc.)
"""

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import sys
import os
import json
import uuid
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

sys.path.append('.')

from quant_ecosystem.multi_agent_orchestrator import orchestrator, AgentDebateResult
from quant_ecosystem.us_market_universe import us_market
from quant_ecosystem.streaming_api import stream_manager, format_debate_for_frontend
from quant_ecosystem.api_v2_routes import api_v2
from quant_ecosystem.agents.data_collection_agent import data_collection_agent
from quant_ecosystem.api_key_manager import api_key_manager, require_user_or_admin, require_auth
from quant_ecosystem.api_key_routes import api_key_routes
from quant_ecosystem.execution_safety import execution_safety, SystemMode
from quant_ecosystem.safety_routes import safety_routes
from quant_ecosystem.user_memory import user_memory
from quant_ecosystem.user_routes import user_routes
from quant_ecosystem.admin_control import admin_control
from quant_ecosystem.admin_routes import admin_routes
from quant_ecosystem.admin_security_routes import admin_security_routes
from quant_ecosystem.file_manager import file_manager
from quant_ecosystem.file_routes import file_routes
from quant_ecosystem.agent_routes import agent_routes
from quant_ecosystem.agent_implementations import register_all_agents
from quant_ecosystem.modification_routes import modification_routes

app = Flask(__name__)

# Configure CORS for external frontend access
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins for now (configure for production)
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    },
    r"/stream/*": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Register blueprints
app.register_blueprint(api_v2)
app.register_blueprint(api_key_routes)
app.register_blueprint(safety_routes)
app.register_blueprint(user_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(admin_security_routes)
app.register_blueprint(file_routes)
app.register_blueprint(agent_routes)
app.register_blueprint(modification_routes)

# Configuration
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')  # Bind to all interfaces
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
# Legacy API key support (optional, for backward compatibility)
LEGACY_API_KEY = os.environ.get('API_KEY', None)

# Health check endpoint (no auth required)
@app.route('/health')
def health():
    """Health check for load balancers"""
    return jsonify({
        "status": "healthy",
        "service": "ai-debate-system",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(orchestrator.active_sessions),
        "active_streams": stream_manager.get_active_stream_count()
    })

# API key check middleware (supports both new system and legacy API key)
def check_api_key():
    """Check API key using new API key manager or legacy key"""
    from quant_ecosystem.api_key_manager import get_bearer_token
    
    # Try new API key system first
    key = get_bearer_token()
    if key:
        from quant_ecosystem.api_key_manager import api_key_manager
        api_key = api_key_manager.validate_key(key)
        if api_key:
            # Store in Flask g for access in endpoint
            from flask import g
            g.api_key = api_key
            return True
    
    # Fall back to legacy API key
    if LEGACY_API_KEY:
        provided_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        return provided_key == LEGACY_API_KEY
    
    # If no keys configured, allow access (for development)
    return True

# Root endpoint with documentation
@app.route('/')
def home():
    """API documentation and status"""
    return jsonify({
        "system": "AI Stock Prediction Multi-Agent Debate System",
        "version": "2.0",
        "status": "operational",
        "features": [
            "Multi-round iterative debate with 1-minute agent timeout",
            "Real-time streaming of AI agent debates to frontend",
            "4 separate AI agents with specialized roles",
            "Data Collection Agent serving real-time info on request",
            "US market coverage (all 4,000+ stocks)",
            "Financial situation adaptation"
        ],
        "agents": [
            {
                "name": "Data Collection Agent",
                "role": "Data provider",
                "function": "Gathers all real-time stock data and serves additional info on request"
            },
            {
                "name": "Bullish Agent",
                "role": "Buy advocate",
                "function": "Analyzes for buying opportunities with up to 1 minute analysis time"
            },
            {
                "name": "Bearish Agent",
                "role": "Sell advocate",
                "function": "Analyzes risks and argues for selling with up to 1 minute analysis time"
            },
            {
                "name": "Risk Assessment Agent",
                "role": "Risk analyst",
                "function": "Evaluates multiple risk dimensions and provides mitigation strategies"
            },
            {
                "name": "Judge Agent",
                "role": "Final arbiter",
                "function": "Evaluates all arguments and renders verdict with position sizing"
            }
        ],
        "endpoints": {
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            },
            "control_panel": {
                "path": "/control",
                "method": "GET",
                "description": "System control panel UI"
            },
            "classify": {
                "path": "/api/v1/classify",
                "method": "POST",
                "description": "Classify user input"
            },
            "start_debate": {
                "path": "/api/v1/debate/start",
                "method": "POST",
                "description": "Start new multi-agent debate"
            },
            "debate_stream": {
                "path": "/api/v1/debate/stream/<session_id>",
                "method": "GET",
                "description": "SSE stream for live debate updates"
            },
            "debate_status": {
                "path": "/api/v1/debate/status/<session_id>",
                "method": "GET",
                "description": "Get debate status"
            },
            "debate_result": {
                "path": "/api/v1/debate/result/<session_id>",
                "method": "GET",
                "description": "Get final debate result"
            },
            "us_stocks": {
                "path": "/api/v1/market/stocks",
                "method": "GET",
                "description": "Get US market stock list"
            },
            "stock_info": {
                "path": "/api/v1/market/stock/<symbol>",
                "method": "GET",
                "description": "Get detailed stock info"
            },
            "api_key_setup": {
                "path": "/api/apikey/setup",
                "method": "POST",
                "description": "One-time setup to create master admin key (only works if no keys exist)"
            },
            "api_key_create": {
                "path": "/api/apikey/create",
                "method": "POST",
                "description": "Create new API key (Admin only)"
            },
            "api_key_list": {
                "path": "/api/apikey/list",
                "method": "GET",
                "description": "List all API keys (Admin only)"
            },
            "api_key_verify": {
                "path": "/api/apikey/verify",
                "method": "GET",
                "description": "Verify current API key and return metadata"
            }
        },
        "authentication": {
            "method": "Bearer Token",
            "header": "Authorization: Bearer <api_key>",
            "roles": ["admin", "user"],
            "permissions": {
                "admin": "Full access to all endpoints including key management",
                "user": "Access to debate and market endpoints only"
            },
            "rate_limiting": "60 requests per minute per key (configurable)"
        },
        "usage": {
            "example_1": "POST /api/v1/debate/start with {\"symbol\": \"AAPL\"}",
            "example_2": "GET /api/v1/debate/stream/<session_id> for live updates",
            "example_3": "GET /api/v1/debate/result/<session_id> for final verdict",
            "authentication_example": "curl -H 'Authorization: Bearer ak_xxx...' /api/v1/market/stocks"
        }
    })


# Control Panel UI
from flask import render_template

@app.route('/control')
def control_panel():
    """Serve the system control panel UI"""
    return render_template('control_panel.html')

# Input classification
@app.route('/api/v1/classify', methods=['POST'])
def classify():
    """Classify user input"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    data = request.get_json() or {}
    user_input = data.get('input', '').strip().upper()
    
    if not user_input:
        return jsonify({"error": "Input required"}), 400
    
    # Classification logic
    if len(user_input) <= 5 and user_input.isalpha():
        return jsonify({
            "type": "single_stock",
            "ticker": user_input,
            "confidence": 0.95,
            "description": "Stock analysis request - will start multi-agent debate",
            "pipeline": "multi_agent_debate"
        })
    elif any(word in user_input.lower() for word in ['top', 'best', 'ranking']):
        return jsonify({
            "type": "ranking",
            "confidence": 0.85,
            "description": "Stock ranking request",
            "pipeline": "stock_ranking"
        })
    elif any(word in user_input.lower() for word in ['hidden', 'gem', 'discover']):
        return jsonify({
            "type": "discovery",
            "confidence": 0.85,
            "description": "Hidden gem discovery request",
            "pipeline": "hidden_gem_detection"
        })
    else:
        return jsonify({
            "type": "unknown",
            "confidence": 0.3,
            "description": "Unclear request",
            "suggestions": ["Try: AAPL", "Try: analyze MSFT", "Try: hidden gems"]
        })

# Start multi-agent debate
@app.route('/api/v1/debate/start', methods=['POST'])
def start_debate():
    """Start a new multi-agent debate session"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    data = request.get_json() or {}
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
    
    # Financial context for adaptation
    financial_context = {
        "market_phase": data.get('market_phase', 'normal'),
        "vix_level": data.get('vix_level', 20),
        "systemic_risk": data.get('systemic_risk', 0.3),
        "timestamp": datetime.now().isoformat()
    }
    
    # Start debate
    session_id = orchestrator.start_debate(
        symbol=symbol,
        financial_context=financial_context
    )
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "symbol": symbol,
        "message": "Multi-agent debate started",
        "estimated_duration": "2-3 minutes (includes 1-minute agent analysis timeout)",
        "stream_url": f"/api/v1/debate/stream/{session_id}",
        "status_url": f"/api/v1/debate/status/{session_id}",
        "result_url": f"/api/v1/debate/result/{session_id}"
    })

# SSE stream for live debate updates
@app.route('/api/v1/debate/stream/<session_id>')
def debate_stream(session_id):
    """Server-Sent Events stream for live debate updates"""
    def generate():
        stream = stream_manager.get_stream(session_id)
        if not stream:
            # Try to get from orchestrator session
            session = orchestrator.active_sessions.get(session_id)
            if not session:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                return
            
            # Create stream if not exists
            stream = stream_manager.create_stream(session_id, "sse")
        
        # Send initial connection message
        initial_msg = json.dumps({
            'type': 'connected',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        yield f"data: {initial_msg}\n\n"
        
        # Stream events
        last_ping = time.time()
        
        try:
            while True:
                # Check if debate is complete
                session = orchestrator.active_sessions.get(session_id)
                if session and session.get('status') == 'complete':
                    # Send final result
                    result = session.get('result')
                    if result:
                        complete_msg = json.dumps({
                            'type': 'complete',
                            'result': result.to_dict()
                        })
                        yield f"data: {complete_msg}\n\n"
                    break
                
                # Send ping every 30 seconds to keep connection alive
                if time.time() - last_ping > 30:
                    ping_msg = json.dumps({
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    })
                    yield f"data: {ping_msg}\n\n"
                    last_ping = time.time()
                
                time.sleep(1)
                
        except GeneratorExit:
            # Client disconnected
            pass
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )

# Get debate status
@app.route('/api/v1/debate/status/<session_id>')
def debate_status(session_id):
    """Get current debate status"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    status = orchestrator.get_session_status(session_id)
    
    if not status:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        **status
    })

# Get debate result
@app.route('/api/v1/debate/result/<session_id>')
def debate_result(session_id):
    """Get final debate result"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    result = orchestrator.get_session_result(session_id)
    
    if not result:
        return jsonify({
            "success": False,
            "error": "Result not available yet or session not found"
        }), 404
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "result": result.to_dict()
    })

# US Market endpoints
@app.route('/api/v1/market/stocks')
def get_us_stocks():
    """Get US market stock list"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    category = request.args.get('category', 'all')
    limit = request.args.get('limit', 100, type=int)
    
    if category == 'all':
        stocks = us_market.get_all_stocks()[:limit]
    else:
        stocks = us_market.get_by_category(category)[:limit]
    
    return jsonify({
        "success": True,
        "category": category,
        "count": len(stocks),
        "stocks": stocks,
        "total_available": len(us_market.get_all_stocks()),
        "categories": ["mega_cap", "large_cap", "mid_cap", "small_cap", "micro_cap"]
    })

@app.route('/api/v1/market/stock/<symbol>')
def get_stock_info(symbol):
    """Get detailed stock information"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    symbol = symbol.upper()
    info = us_market.get_stock_info(symbol)
    
    if info:
        return jsonify({
            "success": True,
            "symbol": symbol,
            "info": info
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Could not fetch info for {symbol}"
        }), 404

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "available": "/api/v1/"}), 404

@app.errorhandler(500)
def internal_error(error):
    log.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    log.info(f"🚀 Starting Production AI Debate Server on {HOST}:{PORT}")
    log.info(f"📊 External access enabled - frontend can connect from any origin")
    log.info(f"🤖 Multi-Agent System: 4 specialized agents with 1-minute analysis timeout")
    log.info(f"🔐 API Key System: Secure authentication with role-based access")
    log.info(f"🛡️ Execution Safety Layer: Pre-execution validation and auto-fallback enabled")
    
    # Initialize API key system
    try:
        existing_keys = api_key_manager.get_all_keys()
        if not existing_keys:
            log.info("🔑 No API keys found. Run POST /api/apikey/setup to create master key")
        else:
            active_keys = sum(1 for k in existing_keys if k.is_active)
            log.info(f"🔑 API Key System: {active_keys}/{len(existing_keys)} keys active")
    except Exception as e:
        log.error(f"❌ API key system initialization error: {e}")
    
    # Initialize safety layer
    try:
        safety_status = execution_safety.validate_execution_readiness()
        log.info(f"🛡️ Safety Layer: Current mode = {safety_status.current_mode.value}")
        log.info(f"🛡️ Safety Checks: {sum(1 for c in safety_status.checks if c.passed)}/{len(safety_status.checks)} passed")
        if not safety_status.execution_allowed:
            log.info(f"🛡️ Execution blocked: {safety_status.recommendations[0] if safety_status.recommendations else 'Safety checks failed'}")
    except Exception as e:
        log.error(f"❌ Safety layer initialization error: {e}")
    
    # Initialize Windsurf Agent Bridge
    try:
        log.info("🤖 Initializing Windsurf Agent Bridge...")
        registered_count = register_all_agents()
        log.info(f"🤖 Windsurf Agents: {registered_count} agents registered and ready")
    except Exception as e:
        log.error(f"❌ Windsurf agent initialization error: {e}")
    
    # Initialize System Self-Modification with default live parameters
    try:
        log.info("🔄 Initializing System Self-Modification...")
        from quant_ecosystem.self_modification import modification_manager
        
        # Register default live parameters
        default_params = [
            {
                'name': 'max_concurrent_analysis',
                'default_value': 5,
                'min_value': 1,
                'max_value': 20,
                'description': 'Maximum number of concurrent stock analyses',
                'category': 'system'
            },
            {
                'name': 'analysis_timeout_seconds',
                'default_value': 60,
                'min_value': 10,
                'max_value': 300,
                'description': 'Timeout for single stock analysis',
                'category': 'system'
            },
            {
                'name': 'debate_auto_close_hours',
                'default_value': 24,
                'min_value': 1,
                'max_value': 168,
                'description': 'Hours after which inactive debates are auto-closed',
                'category': 'threshold'
            },
            {
                'name': 'enable_auto_fallback',
                'default_value': True,
                'allowed_values': [True, False],
                'description': 'Enable automatic fallback to safe mode on anomalies',
                'category': 'threshold'
            },
            {
                'name': 'log_retention_days',
                'default_value': 30,
                'min_value': 1,
                'max_value': 365,
                'description': 'Number of days to retain system logs',
                'category': 'system',
                'requires_restart': True
            }
        ]
        
        for param in default_params:
            modification_manager.register_live_parameter(**param)
        
        log.info(f"🔄 System Self-Modification: {len(default_params)} live parameters registered")
    except Exception as e:
        log.error(f"❌ Self-modification initialization error: {e}")
    
    # Test system on startup
    try:
        log.info("🧪 Running startup tests...")
        
        # Test data collection
        test_data = data_collection_agent.collect_initial_data("AAPL")
        if "error" not in test_data:
            log.info("✅ Data Collection Agent: Operational")
        
        # Test orchestrator
        log.info(f"✅ Multi-Agent Orchestrator: {len(orchestrator.active_sessions)} active sessions")
        
        # Test US market
        stock_count = len(us_market.get_all_stocks())
        log.info(f"✅ US Market Universe: {stock_count} stocks loaded")
        
        log.info("✅ All systems operational!")
        
    except Exception as e:
        log.error(f"❌ Startup test error: {e}")
    
    # Run production server
    # Use threaded=True for handling multiple concurrent requests
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True,
        use_reloader=False  # Disable in production
    )
