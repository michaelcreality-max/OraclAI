#!/usr/bin/env python3
"""
Simple Flask server for testing the AI agents system
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Add the current directory to Python path
sys.path.append('.')

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    """Home page with system overview"""
    return jsonify({
        "system": "AI Stock Prediction Agents",
        "status": "operational",
        "description": "Collection of AI agents for stock analysis",
        "agents": [
            "Stock Data Collection Agent",
            "Bullish Debate Agent", 
            "Bearish Debate Agent",
            "Risk Critic Agent",
            "Judge Agent"
        ],
        "endpoints": {
            "health": "/health",
            "classify": "/api/v1/classify (POST)",
            "analyze": "/api/v1/intelligence/analyze (POST)",
            "hidden_gems": "/api/v1/discover/hidden-gems (POST)",
            "risk_scan": "/api/v1/scan/risks (POST)",
            "alerts": "/api/v1/alerts/smart (POST)",
            "patterns": "/api/v1/discover/patterns (POST)"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ai-agents-system",
        "agents_active": 5
    })

@app.route('/api/v1/classify', methods=['POST'])
def classify():
    """Classify user input"""
    data = request.get_json() or {}
    user_input = data.get('input', '').strip().upper()
    
    # Simple classification logic
    if len(user_input) <= 5 and user_input.isalpha():
        return jsonify({
            "type": "single_stock",
            "ticker": user_input,
            "confidence": 0.9,
            "pipeline": "single_stock_analysis"
        })
    elif "top" in user_input.lower():
        return jsonify({
            "type": "ranking", 
            "limit": 10,
            "confidence": 0.8,
            "pipeline": "stock_ranking"
        })
    elif "hidden" in user_input.lower() or "gem" in user_input.lower():
        return jsonify({
            "type": "discovery",
            "confidence": 0.85,
            "pipeline": "hidden_gem_detection"
        })
    else:
        return jsonify({
            "type": "unknown",
            "confidence": 0.3,
            "pipeline": "general_query"
        })

@app.route('/api/v1/intelligence/analyze', methods=['POST'])
def analyze():
    """Run the 4 AI agents debate system"""
    try:
        from quant_ecosystem.elite_intelligence import run_full_intelligence
        
        data = request.get_json() or {}
        symbol = data.get('symbol', 'SPY')
        
        # Run the full intelligence analysis
        result = run_full_intelligence(
            symbol,
            period="6mo",
            include_cross_market=False,
            include_stock_intel=False,
            max_hypotheses=1,
            top_models=1
        )
        
        if result.get("ok"):
            return jsonify({
                "success": True,
                "symbol": symbol,
                "debate": result.get("debate", {}),
                "regime": result.get("regime", {}),
                "agents_count": 4,
                "judge_decision": result.get("debate", {}).get("judge", {}).get("action", "hold")
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Analysis failed")
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    print("🤖 Starting AI Agents System Server...")
    print("📊 Available at: http://localhost:5000")
    print("🧪 Testing 4 AI Agents Debate System...")
    
    # Test the debate system
    try:
        from quant_ecosystem.debate import DebateCouncil
        debate = DebateCouncil()
        result = debate.run(
            symbol="TEST",
            prediction_summary={"direction": "bullish", "confidence": 0.75},
            regime={"trend": "bull", "volatility": "normal", "confidence": 0.8},
            risk_metrics={"max_drawdown_proxy": 0.12, "sharpe_proxy": 1.45}
        )
        print(f"✅ Debate System Working! Judge: {result['judge']['action']}")
    except Exception as e:
        print(f"❌ Debate System Error: {e}")
    
    print("🚀 Server ready!")
    app.run(host="0.0.0.0", port=5000, debug=False)
