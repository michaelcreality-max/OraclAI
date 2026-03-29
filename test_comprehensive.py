#!/usr/bin/env python3
"""
Comprehensive Multi-Agent System Test
Validates all components of the AI debate system
"""

import sys
import os
import time
import json
from datetime import datetime

sys.path.append('.')

def test_data_collection_agent():
    """Test Data Collection Agent"""
    print("\n🧪 Testing Data Collection Agent...")
    
    try:
        from quant_ecosystem.agents.data_collection_agent import data_collection_agent
        
        # Test initial data collection
        data = data_collection_agent.collect_initial_data("AAPL")
        
        assert "symbol" in data, "Missing symbol"
        assert "price_data" in data, "Missing price_data"
        assert "fundamentals" in data, "Missing fundamentals"
        
        print("✅ Initial data collection works")
        
        # Test data request
        response = data_collection_agent.request_data(
            agent_id="test_agent",
            request_type="analyst_ratings",
            symbol="AAPL",
            parameters={},
            urgency="normal"
        )
        
        assert response is not None, "Data request returned None"
        assert response.data is not None, "Response data is None"
        
        print("✅ Dynamic data requests work")
        print(f"   Data points collected: {len(data)}")
        
        return True
    except Exception as e:
        print(f"❌ Data Collection Agent error: {e}")
        return False

def test_bullish_agent():
    """Test Bullish Agent"""
    print("\n🧪 Testing Bullish Agent...")
    
    try:
        from quant_ecosystem.agents.bullish_agent import BullishAgent
        from quant_ecosystem.agents.data_collection_agent import data_collection_agent
        
        def mock_data_request(agent_id, request_type, symbol, parameters, urgency):
            return {"mock": True, "data": "test"}
        
        agent = BullishAgent(mock_data_request)
        
        # Mock initial data
        initial_data = {
            "symbol": "AAPL",
            "price_data": {
                "current_price": 150.0,
                "previous_close": 145.0,
                "fifty_two_week_high": 180.0,
                "fifty_two_week_low": 120.0
            },
            "fundamentals": {
                "pe_ratio": 25.0,
                "revenue_growth": 0.15,
                "earnings_growth": 0.20,
                "beta": 1.2
            },
            "historical": {
                "trend_6m": "up",
                "volatility": 0.25
            }
        }
        
        financial_context = {"market_phase": "normal", "vix_level": 20}
        
        result = agent.analyze("AAPL", initial_data, financial_context)
        
        assert result is not None, "Analysis returned None"
        assert result.confidence > 0, "Invalid confidence"
        assert len(result.key_points) > 0, "No key points generated"
        
        # Test argue method
        argument = agent.argue(result)
        assert argument["stance"] == "constructive", "Wrong stance"
        
        print("✅ Bullish Agent works correctly")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Key points: {len(result.key_points)}")
        
        return True
    except Exception as e:
        print(f"❌ Bullish Agent error: {e}")
        return False

def test_bearish_agent():
    """Test Bearish Agent"""
    print("\n🧪 Testing Bearish Agent...")
    
    try:
        from quant_ecosystem.agents.bearish_agent import BearishAgent
        
        def mock_data_request(agent_id, request_type, symbol, parameters, urgency):
            return {"mock": True}
        
        agent = BearishAgent(mock_data_request)
        
        initial_data = {
            "symbol": "AAPL",
            "price_data": {
                "current_price": 150.0,
                "previous_close": 155.0,
                "fifty_two_week_high": 180.0,
                "fifty_two_week_low": 140.0
            },
            "fundamentals": {
                "pe_ratio": 45.0,
                "beta": 1.5
            },
            "historical": {
                "volatility": 0.35
            }
        }
        
        financial_context = {"market_phase": "normal", "vix_level": 25}
        
        result = agent.analyze("AAPL", initial_data, financial_context)
        
        assert result is not None, "Analysis returned None"
        assert result.confidence > 0, "Invalid confidence"
        
        # Test argue
        argument = agent.argue(result)
        assert argument["stance"] == "skeptical", "Wrong stance"
        
        print("✅ Bearish Agent works correctly")
        print(f"   Confidence: {result.confidence:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Bearish Agent error: {e}")
        return False

def test_risk_agent():
    """Test Risk Assessment Agent"""
    print("\n🧪 Testing Risk Assessment Agent...")
    
    try:
        from quant_ecosystem.agents.risk_assessment_agent import RiskAssessmentAgent
        
        def mock_data_request(agent_id, request_type, symbol, parameters, urgency):
            return {"mock": True}
        
        agent = RiskAssessmentAgent(mock_data_request)
        
        initial_data = {
            "symbol": "AAPL",
            "price_data": {"volume": 1000000},
            "historical": {"volatility": 0.30}
        }
        
        bullish_analysis = {"confidence": 0.7, "key_points": ["Growth"]}
        bearish_analysis = {"confidence": 0.5, "key_points": ["Valuation"]}
        financial_context = {"market_phase": "normal", "vix_level": 25}
        
        result = agent.analyze("AAPL", initial_data, bullish_analysis, 
                              bearish_analysis, financial_context)
        
        assert result is not None, "Analysis returned None"
        assert result.risk_score >= 0, "Invalid risk score"
        assert result.risk_level in ["low", "moderate", "high", "extreme"], "Invalid risk level"
        
        # Test argue
        argument = agent.argue(result)
        assert argument["stance"] == "critique", "Wrong stance"
        
        print("✅ Risk Assessment Agent works correctly")
        print(f"   Risk Score: {result.risk_score:.2f}")
        print(f"   Risk Level: {result.risk_level}")
        
        return True
    except Exception as e:
        print(f"❌ Risk Agent error: {e}")
        return False

def test_judge_agent():
    """Test Judge Agent"""
    print("\n🧪 Testing Judge Agent...")
    
    try:
        from quant_ecosystem.agents.judge_agent import JudgeAgent
        
        judge = JudgeAgent()
        
        bullish_arg = {
            "confidence": 0.75,
            "points": ["Strong growth", "Good margins"]
        }
        
        bearish_arg = {
            "confidence": 0.45,
            "points": ["High valuation"]
        }
        
        risk_arg = {
            "confidence": 0.60,
            "risk_score": 0.35,
            "points": ["Moderate volatility"]
        }
        
        financial_context = {"market_phase": "normal", "vix_level": 20}
        
        verdict = judge.deliberate("AAPL", bullish_arg, bearish_arg, risk_arg, financial_context)
        
        assert verdict is not None, "Verdict is None"
        assert verdict.action in ["buy", "sell", "hold"], f"Invalid action: {verdict.action}"
        assert verdict.confidence >= 0, "Invalid confidence"
        assert len(verdict.rationale) > 0, "No rationale"
        
        print("✅ Judge Agent works correctly")
        print(f"   Action: {verdict.action.upper()}")
        print(f"   Confidence: {verdict.confidence:.2f}")
        print(f"   Position Size: {verdict.recommended_position_size}")
        
        return True
    except Exception as e:
        print(f"❌ Judge Agent error: {e}")
        return False

def test_orchestrator():
    """Test Multi-Agent Orchestrator"""
    print("\n🧪 Testing Multi-Agent Orchestrator...")
    
    try:
        from quant_ecosystem.multi_agent_orchestrator import orchestrator
        
        # Test orchestrator initialization
        assert orchestrator is not None, "Orchestrator not initialized"
        
        # Test session management
        session_id = orchestrator.start_debate(
            symbol="AAPL",
            financial_context={"market_phase": "normal", "vix_level": 20}
        )
        
        assert session_id is not None, "Session ID is None"
        assert isinstance(session_id, str), "Session ID not string"
        
        # Check session status
        time.sleep(1)  # Give it time to start
        status = orchestrator.get_session_status(session_id)
        assert status is not None, "Status is None"
        assert "status" in status, "Missing status field"
        
        print("✅ Multi-Agent Orchestrator works correctly")
        print(f"   Session ID: {session_id}")
        print(f"   Status: {status['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        return False

def test_us_market():
    """Test US Market Universe"""
    print("\n🧪 Testing US Market Universe...")
    
    try:
        from quant_ecosystem.us_market_universe import us_market
        
        # Test getting all stocks
        stocks = us_market.get_all_stocks()
        assert len(stocks) > 0, "No stocks loaded"
        
        # Test category filtering
        large_caps = us_market.get_by_category("large_cap")
        
        # Test stock info
        info = us_market.get_stock_info("AAPL")
        
        print("✅ US Market Universe works correctly")
        print(f"   Total stocks: {len(stocks)}")
        
        return True
    except Exception as e:
        print(f"❌ US Market error: {e}")
        return False

def test_streaming_api():
    """Test Streaming API"""
    print("\n🧪 Testing Streaming API...")
    
    try:
        from quant_ecosystem.streaming_api import stream_manager, LiveDebateTracker
        
        # Test stream manager
        test_session = "test_session_123"
        stream = stream_manager.create_stream(test_session, "sse")
        assert stream is not None, "Stream not created"
        
        # Test tracker
        tracker = LiveDebateTracker(test_session)
        tracker.log_agent_thought("bullish", "Testing thought", 1)
        
        assert len(tracker.events) > 0, "Event not logged"
        
        print("✅ Streaming API works correctly")
        
        return True
    except Exception as e:
        print(f"❌ Streaming API error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🔍 COMPREHENSIVE MULTI-AGENT SYSTEM TEST")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    
    tests = [
        ("Data Collection Agent", test_data_collection_agent),
        ("Bullish Agent", test_bullish_agent),
        ("Bearish Agent", test_bearish_agent),
        ("Risk Assessment Agent", test_risk_agent),
        ("Judge Agent", test_judge_agent),
        ("Multi-Agent Orchestrator", test_orchestrator),
        ("US Market Universe", test_us_market),
        ("Streaming API", test_streaming_api),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is operational.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
