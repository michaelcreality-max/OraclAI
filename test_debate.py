#!/usr/bin/env python3
"""
Test script to verify the 4 AI agents debate system is working
"""

import sys
import os
sys.path.append('.')

from quant_ecosystem.debate import DebateCouncil
from quant_ecosystem.elite_intelligence import run_full_intelligence

def test_debate_system():
    """Test the 4 AI agents debate system"""
    print("🤖 Testing 4 AI Agents Debate System...")
    
    # Test 1: Direct debate council
    print("\n📋 Test 1: Direct Debate Council")
    debate = DebateCouncil()
    
    # Mock data for testing
    prediction_summary = {
        "direction": "bullish",
        "confidence": 0.75
    }
    
    regime = {
        "trend": "bull",
        "volatility": "normal",
        "confidence": 0.8
    }
    
    risk_metrics = {
        "max_drawdown_proxy": 0.12,
        "sharpe_proxy": 1.45
    }
    
    result = debate.run(
        symbol="TEST",
        prediction_summary=prediction_summary,
        regime=regime,
        risk_metrics=risk_metrics
    )
    
    print("✅ Debate Council Working!")
    print(f"   Judge Action: {result['judge']['action']}")
    print(f"   Judge Score: {result['judge']['score']}")
    print(f"   Number of Agents: {len(result['agents'])}")
    
    for i, agent in enumerate(result['agents']):
        print(f"   Agent {i+1} ({agent['role']}): {agent['stance']} (Conf: {agent['confidence']:.2f})")
    
    # Test 2: Full intelligence system (if possible)
    print("\n📋 Test 2: Full Intelligence System")
    try:
        # Try with a simple symbol that might work
        analysis = run_full_intelligence(
            "SPY",  # Use ETF instead of stock
            period="6mo",
            include_cross_market=False,
            include_stock_intel=False,
            max_hypotheses=1,
            top_models=1
        )
        
        if analysis.get("ok"):
            print("✅ Full Intelligence System Working!")
            if "debate" in analysis:
                debate = analysis["debate"]
                print(f"   Judge Action: {debate['judge']['action']}")
                print(f"   Judge Score: {debate['judge']['score']}")
                print(f"   Bullish Agent Confidence: {debate['agents'][0]['confidence']:.2f}")
                print(f"   Bearish Agent Confidence: {debate['agents'][1]['confidence']:.2f}")
                print(f"   Risk Critic Confidence: {debate['agents'][2]['confidence']:.2f}")
            else:
                print("   No debate data found")
        else:
            print(f"❌ Full Intelligence System Error: {analysis.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Full Intelligence System Failed: {e}")
    
    print("\n🎯 Debate System Test Complete!")

if __name__ == "__main__":
    test_debate_system()
