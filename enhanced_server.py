#!/usr/bin/env python3
"""
Enhanced Flask server with full AI debate system
Features: Multi-round iterative debate, real-time streaming, US market coverage
"""

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import sys
import os
import json
import time
import uuid
from datetime import datetime
from threading import Thread

# Add the current directory to Python path
sys.path.append('.')

app = Flask(__name__)
CORS(app)

# Import enhanced components
from quant_ecosystem.iterative_debate_engine import debate_engine, IterativeDebateEngine
from quant_ecosystem.us_market_universe import us_market
from quant_ecosystem.streaming_api import stream_manager, create_streaming_callback, format_debate_for_frontend, LiveDebateTracker
from quant_ecosystem.debate import DebateCouncil
from quant_ecosystem.elite_intelligence import run_full_intelligence

# Store active debate sessions
active_debates = {}

@app.route('/')
def home():
    """Home page with system overview"""
    return jsonify({
        "system": "Enhanced AI Stock Prediction Agents",
        "version": "2.0",
        "status": "operational",
        "features": [
            "Multi-round iterative debate with timeout and rethinking",
            "Real-time streaming of AI agent debates",
            "US market coverage (all stocks)",
            "Financial situation adaptation",
            "Live transparency of agent thinking"
        ],
        "agents": [
            "Stock Data Collection Agent",
            "Bullish Debate Agent (with rethinking)",
            "Bearish Debate Agent (with rethinking)",
            "Risk Critic Agent (with rethinking)",
            "Judge Agent (with consensus evaluation)"
        ],
        "endpoints": {
            "health": "/health",
            "classify": "/api/v1/classify (POST)",
            "analyze": "/api/v1/intelligence/analyze (POST) - Full analysis",
            "debate_stream": "/api/v1/debate/stream (POST) - Start debate with streaming",
            "debate_sse": "/api/v1/debate/stream/<session_id> (GET) - SSE stream",
            "debate_status": "/api/v1/debate/status/<session_id> (GET)",
            "us_stocks": "/api/v1/market/stocks (GET)",
            "stock_info": "/api/v1/market/stock/<symbol> (GET)",
            "market_scan": "/api/v1/market/scan (POST)",
            "hidden_gems": "/api/v1/discover/hidden-gems (POST)",
            "risk_scan": "/api/v1/scan/risks (POST)",
            "alerts": "/api/v1/alerts/smart (POST)"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ai-agents-system",
        "version": "2.0",
        "agents_active": 5,
        "active_debates": len(active_debates),
        "active_streams": stream_manager.get_active_stream_count()
    })

@app.route('/api/v1/classify', methods=['POST'])
def classify():
    """Classify user input with enhanced routing"""
    data = request.get_json() or {}
    user_input = data.get('input', '').strip().upper()
    
    # Enhanced classification logic
    if len(user_input) <= 5 and user_input.isalpha():
        return jsonify({
            "type": "single_stock",
            "ticker": user_input,
            "confidence": 0.9,
            "pipeline": "iterative_debate_analysis",
            "description": "Will run multi-round AI debate with real-time streaming"
        })
    elif "top" in user_input.lower():
        return jsonify({
            "type": "ranking",
            "limit": 10,
            "confidence": 0.8,
            "pipeline": "stock_ranking",
            "scope": "us_market"
        })
    elif "hidden" in user_input.lower() or "gem" in user_input.lower():
        return jsonify({
            "type": "discovery",
            "confidence": 0.85,
            "pipeline": "hidden_gem_detection",
            "scope": "us_market"
        })
    elif "risk" in user_input.lower() or "danger" in user_input.lower():
        return jsonify({
            "type": "risk_scan",
            "confidence": 0.8,
            "pipeline": "risk_scanner",
            "scope": "us_market"
        })
    elif "market" in user_input.lower() or "overview" in user_input.lower():
        return jsonify({
            "type": "market_overview",
            "confidence": 0.75,
            "pipeline": "market_regime_analysis",
            "scope": "us_market"
        })
    elif "debate" in user_input.lower() or "stream" in user_input.lower():
        return jsonify({
            "type": "live_debate",
            "confidence": 0.9,
            "pipeline": "iterative_debate_stream",
            "description": "Start live multi-round AI debate with real-time updates"
        })
    else:
        return jsonify({
            "type": "unknown",
            "confidence": 0.3,
            "pipeline": "general_query",
            "suggestion": "Try: 'AAPL', 'hidden gems', 'top 10 stocks', 'risk scan', or 'market overview'"
        })

@app.route('/api/v1/debate/stream', methods=['POST'])
def start_debate_stream():
    """Start a new iterative debate with real-time streaming"""
    data = request.get_json() or {}
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"success": False, "error": "Symbol is required"}), 400
    
    # Get financial context for adaptation
    financial_context = {
        "market_phase": data.get('market_phase', 'normal'),
        "vix_level": data.get('vix_level', 20),
        "systemic_risk": data.get('systemic_risk', 0),
        "timestamp": datetime.now().isoformat()
    }
    
    # Prepare mock data for debate (in real implementation, fetch from data sources)
    prediction_summary = {
        "direction": data.get('direction', 'neutral'),
        "confidence": data.get('confidence', 0.5)
    }
    
    regime = {
        "trend": data.get('trend', 'sideways'),
        "volatility": data.get('volatility', 'normal'),
        "confidence": data.get('regime_confidence', 0.7)
    }
    
    risk_metrics = {
        "max_drawdown_proxy": data.get('max_drawdown', 0.12),
        "sharpe_proxy": data.get('sharpe', 1.0),
        "microstructure": data.get('microstructure', {"stress_score": 0.3})
    }
    
    # Create streaming session
    session_id = str(uuid.uuid4())
    stream = stream_manager.create_stream(session_id, "sse")
    
    # Create streaming callback
    streaming_callback = create_streaming_callback(session_id)
    
    # Start debate in background
    debate_thread = Thread(
        target=run_iterative_debate,
        args=(session_id, symbol, financial_context, prediction_summary, regime, risk_metrics, streaming_callback)
    )
    debate_thread.daemon = True
    debate_thread.start()
    
    active_debates[session_id] = {
        "symbol": symbol,
        "started_at": datetime.now().isoformat(),
        "financial_context": financial_context,
        "status": "running"
    }
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "symbol": symbol,
        "message": "Debate started with real-time streaming",
        "stream_url": f"/api/v1/debate/stream/{session_id}",
        "status_url": f"/api/v1/debate/status/{session_id}",
        "financial_context": financial_context,
        "estimated_duration": "2-3 minutes (max 3 rounds with 60s timeout each)"
    })

def run_iterative_debate(session_id, symbol, financial_context, prediction_summary, regime, risk_metrics, streaming_callback):
    """Run the iterative debate process"""
    try:
        # Start debate using the debate engine
        debate_session_id = debate_engine.start_debate(
            symbol=symbol,
            financial_context=financial_context,
            prediction_summary=prediction_summary,
            regime=regime,
            risk_metrics=risk_metrics,
            streaming_callback=streaming_callback
        )
        
        # Wait for debate to complete (with max timeout)
        max_wait = 240  # 4 minutes max
        waited = 0
        while waited < max_wait:
            session = debate_engine.get_session(debate_session_id)
            if session and session.status.value in ['complete', 'timeout']:
                break
            time.sleep(1)
            waited += 1
        
        # Get final results
        session = debate_engine.get_session(debate_session_id)
        if session:
            active_debates[session_id]["status"] = "complete"
            active_debates[session_id]["result"] = session.final_verdict
            active_debates[session_id]["total_rounds"] = len(session.rounds)
            active_debates[session_id]["completed_at"] = datetime.now().isoformat()
            
    except Exception as e:
        active_debates[session_id]["status"] = "error"
        active_debates[session_id]["error"] = str(e)
        streaming_callback({
            "event_type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/v1/debate/stream/<session_id>')
def debate_sse_stream(session_id):
    """Server-Sent Events endpoint for live debate updates"""
    def generate():
        stream = stream_manager.get_stream(session_id)
        if not stream:
            yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
            return
        
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Stream events
        for event_data in stream.get_sse_generator():
            yield event_data
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/v1/debate/status/<session_id>')
def debate_status(session_id):
    """Get debate status and results"""
    # Check active debates
    if session_id in active_debates:
        debate_info = active_debates[session_id].copy()
        
        # Get full session data from engine
        session = debate_engine.get_session(session_id)
        if session:
            debate_info["full_data"] = session.to_dict()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "debate_info": debate_info
        })
    
    return jsonify({
        "success": False,
        "error": "Session not found"
    }), 404

@app.route('/api/v1/intelligence/analyze', methods=['POST'])
def analyze():
    """Run the 4 AI agents debate system with full intelligence"""
    data = request.get_json() or {}
    symbol = data.get('symbol', 'SPY').upper()
    
    try:
        # Run full intelligence analysis
        result = run_full_intelligence(
            symbol,
            period=data.get('period', '6mo'),
            include_cross_market=data.get('include_cross_market', False),
            include_stock_intel=data.get('include_stock_intel', True),
            max_hypotheses=data.get('max_hypotheses', 2),
            top_models=data.get('top_models', 1)
        )
        
        if result.get("ok"):
            debate_data = result.get("debate", {})
            
            # Enhanced response with agent details
            return jsonify({
                "success": True,
                "symbol": symbol,
                "debate": debate_data,
                "regime": result.get("regime", {}),
                "patterns": result.get("patterns", {}),
                "ecosystem": result.get("ecosystem", {}),
                "agents": {
                    "count": 4,
                    "bull_confidence": debate_data.get("agents", [{}])[0].get("confidence", 0),
                    "bear_confidence": debate_data.get("agents", [{}])[1].get("confidence", 0),
                    "risk_confidence": debate_data.get("agents", [{}])[2].get("confidence", 0),
                    "judge_action": debate_data.get("judge", {}).get("action", "hold"),
                    "judge_score": debate_data.get("judge", {}).get("score", 0)
                },
                "recommendation": {
                    "action": debate_data.get("judge", {}).get("action", "hold").upper(),
                    "confidence": max(debate_data.get("agents", [{}])[0].get("confidence", 0),
                                    debate_data.get("agents", [{}])[1].get("confidence", 0))
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Analysis failed"),
                "symbol": symbol
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "symbol": symbol
        })

@app.route('/api/v1/market/stocks')
def get_market_stocks():
    """Get US market stock universe"""
    category = request.args.get('category', 'all')
    limit = request.args.get('limit', 1000, type=int)
    
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

@app.route('/api/v1/market/scan', methods=['POST'])
def scan_market():
    """Scan US market with filters"""
    data = request.get_json() or {}
    
    filter_criteria = data.get('filters', {})
    limit = data.get('limit', 100)
    
    stocks = us_market.scan_universe(filter_criteria, limit)
    
    return jsonify({
        "success": True,
        "filters": filter_criteria,
        "count": len(stocks),
        "stocks": stocks
    })

if __name__ == "__main__":
    print("🤖 Starting Enhanced AI Agents System Server...")
    print("📊 Available at: http://localhost:5000")
    print("🧪 Testing Multi-Round Debate System...")
    
    # Test the debate system
    try:
        print("✅ Iterative Debate Engine loaded")
        print("✅ US Market Universe loaded:", len(us_market.get_all_stocks()), "stocks")
        print("✅ Streaming API loaded")
        
        # Quick test of basic debate
        debate = DebateCouncil()
        result = debate.run(
            symbol="TEST",
            prediction_summary={"direction": "bullish", "confidence": 0.75},
            regime={"trend": "bull", "volatility": "normal", "confidence": 0.8},
            risk_metrics={"max_drawdown_proxy": 0.12, "sharpe_proxy": 1.45}
        )
        print(f"✅ 4-Agent Debate Test: Judge decided {result['judge']['action'].upper()}")
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
    
    print("🚀 Server ready with real-time streaming!")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
