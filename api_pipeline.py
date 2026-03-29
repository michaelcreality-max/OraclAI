"""
Stock Prediction API Pipeline
Python client for the AI agents system
"""

import os
from typing import Any, Dict, List, Optional
import requests
from dataclasses import dataclass


@dataclass
class APIConfig:
    base_url: str = "http://localhost:5000"
    api_key: Optional[str] = None
    timeout: int = 30


class StockPredictionAPI:
    """Python client for the Stock Prediction API with AI agents"""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self.session = requests.Session()
        
        if self.config.api_key:
            self.session.headers.update({"X-API-Key": self.config.api_key})
    
    def _request(self, endpoint: str, method: str = "GET", 
                 data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if method != "GET" else None,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self._request("/health")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote"""
        return self._request("/api/v1/quote", params={"symbol": symbol})["quote"]
    
    def get_stock_intel(self, symbol: str, history_period: str = "3mo") -> Dict[str, Any]:
        """Get stock intelligence from data collection agent"""
        return self._request(
            "/api/v1/intel/stock", 
            params={"symbol": symbol, "history_period": history_period}
        )["stock_intel"]
    
    def predict_stock(self, symbol: str, days: int = 90, 
                     client_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Basic stock prediction"""
        data = {"symbol": symbol, "days": days}
        if client_context:
            data["client_context"] = client_context
        
        return self._request("/api/v1/predict", method="POST", data=data)["prediction"]
    
    def analyze_with_debate(self, 
                           symbol: str,
                           period: str = "2y",
                           user_profile: Optional[Dict] = None,
                           what_if: Optional[Dict[str, float]] = None,
                           include_cross_market: bool = True,
                           include_stock_intel: bool = False,
                           max_hypotheses: int = 4,
                           top_models: int = 2) -> Dict[str, Any]:
        """
        Full AI agents analysis with debate system
        Includes: Stock Data Agent + 4 Debate Agents + Full ecosystem
        """
        data = {
            "symbol": symbol,
            "period": period,
            "include_cross_market": include_cross_market,
            "include_stock_intel": include_stock_intel,
            "max_hypotheses": max_hypotheses,
            "top_models": top_models
        }
        
        if user_profile:
            data["user_profile"] = user_profile
        if what_if:
            data["what_if"] = what_if
            
        return self._request("/api/v1/intelligence/analyze", method="POST", data=data)["intelligence"]
    
    def classify_input(self, user_input: str) -> Dict[str, Any]:
        """Classify user input to determine pipeline type"""
        return self._request("/api/v1/classify", method="POST", data={"input": user_input})
    
    def discover_hidden_gems(self, 
                           limit: int = 10,
                           sector: Optional[str] = None,
                           max_attention: float = 0.6) -> List[Dict[str, Any]]:
        """Discover hidden gems (undiscovered opportunities)"""
        data = {"limit": limit, "max_attention": max_attention}
        if sector:
            data["sector"] = sector
            
        return self._request("/api/v1/discover/hidden-gems", method="POST", data=data)["hidden_gems"]
    
    def scan_risks(self, 
                   limit: int = 15,
                   min_risk_level: str = "HIGH",
                   sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan for dangerous/risky stocks"""
        data = {"limit": limit, "min_risk_level": min_risk_level}
        if sector:
            data["sector"] = sector
            
        return self._request("/api/v1/scan/risks", method="POST", data=data)["dangerous_stocks"]
    
    def generate_smart_alerts(self, 
                             symbols: Optional[List[str]] = None,
                             alert_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate smart alerts"""
        data = {}
        if symbols:
            data["symbols"] = symbols
        if alert_types:
            data["alert_types"] = alert_types
            
        return self._request("/api/v1/alerts/smart", method="POST", data=data)
    
    def discover_patterns(self, 
                         symbols: Optional[List[str]] = None,
                         pattern_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Discover unknown patterns in market data"""
        data = {}
        if symbols:
            data["symbols"] = symbols
        if pattern_types:
            data["pattern_types"] = pattern_types
            
        return self._request("/api/v1/discover/patterns", method="POST", data=data)
    
    def smart_predict(self, user_input: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Universal smart predict - classifies input and routes to appropriate pipeline"""
        options = options or {}
        
        # First classify the input
        classification = self.classify_input(user_input)
        
        if classification["type"] == "single_stock":
            return self.analyze_with_debate(classification["ticker"], **options)
        elif classification["type"] == "ranking":
            return self.discover_stocks(
                min_confidence=options.get("min_confidence", 0.5),
                sector=options.get("sector"),
                limit=classification.get("limit", 10)
            )
        elif classification["type"] == "discovery":
            return self.discover_hidden_gems(**options)
        elif classification["type"] == "risk_scan":
            return self.scan_risks(**options)
        elif classification["type"] == "market_overview":
            return self.get_market_overview()
        else:
            raise ValueError(f"Unknown request type: {classification['type']}")
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview/regime analysis"""
        # Use SPY as market proxy
        analysis = self.analyze_with_debate(
            "SPY",
            include_cross_market=True,
            include_stock_intel=True,
            max_hypotheses=2,
            top_models=1
        )
        
        return {
            "market_regime": analysis["regime"],
            "overview": {
                "trend": analysis["regime"]["trend"],
                "volatility": analysis["regime"]["volatility"],
                "confidence": analysis["regime"]["confidence"],
                "recommendation": analysis.get("debate", {}).get("judge", {}).get("action", "hold"),
                "key_insights": [
                    f"Market in {analysis['regime']['trend']} regime",
                    f"Volatility: {analysis['regime']['volatility']}",
                    f"Regime confidence: {analysis['regime']['confidence']:.1%}"
                ]
            }
        }
    
    def get_agent_summary(self, symbol: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Get comprehensive agent summary (enhanced)"""
        options = options or {}
        full_analysis = self.analyze_with_debate(symbol, **options)
        
        # Get additional risk and gem analysis
        risk_analysis = None
        gem_analysis = None
        
        try:
            risks = self.scan_risks(limit=50)
            risk_analysis = next((r for r in risks if r["symbol"] == symbol), None)
        except:
            pass
        
        try:
            gems = self.discover_hidden_gems(limit=50)
            gem_analysis = next((g for g in gems if g["symbol"] == symbol), None)
        except:
            pass
        
        return {
            "symbol": full_analysis["symbol"],
            "data_collection_agent": {
                "role": "observer",
                "mandate": "Collect and normalize factual market data",
                "key_metrics": full_analysis.get("stock_intel", {}).get("fundamentals", {}) if full_analysis.get("stock_intel") else {},
                "data_sources": full_analysis.get("stock_intel", {}).get("data_sources", []) if full_analysis.get("stock_intel") else []
            },
            "debate_agents": {
                "bullish_agent": {
                    "stance": full_analysis.get("debate", {}).get("agents", [{}])[0].get("stance", "constructive"),
                    "confidence": full_analysis.get("debate", {}).get("agents", [{}])[0].get("confidence", 0),
                    "key_points": full_analysis.get("debate", {}).get("agents", [{}])[0].get("points", [])
                },
                "bearish_agent": {
                    "stance": full_analysis.get("debate", {}).get("agents", [{}])[1].get("stance", "skeptical"),
                    "confidence": full_analysis.get("debate", {}).get("agents", [{}])[1].get("confidence", 0),
                    "key_points": full_analysis.get("debate", {}).get("agents", [{}])[1].get("points", [])
                },
                "risk_critic": {
                    "stance": full_analysis.get("debate", {}).get("agents", [{}])[2].get("stance", "critique"),
                    "confidence": full_analysis.get("debate", {}).get("agents", [{}])[2].get("confidence", 0),
                    "key_points": full_analysis.get("debate", {}).get("agents", [{}])[2].get("points", [])
                },
                "judge_verdict": {
                    "action": full_analysis.get("debate", {}).get("judge", {}).get("action", "hold"),
                    "score": full_analysis.get("debate", {}).get("judge", {}).get("score", 0),
                    "rationale": full_analysis.get("debate", {}).get("judge", {}).get("rationale", ""),
                    "risk_flags": full_analysis.get("debate", {}).get("judge", {}).get("risk_flags", [])
                }
            },
            "final_prediction": {
                "direction": full_analysis.get("ecosystem", {}).get("reality_reports", [{}])[0].get("direction", "neutral"),
                "confidence": full_analysis.get("ecosystem", {}).get("reality_reports", [{}])[0].get("confidence", 0.5),
                "action": full_analysis.get("debate", {}).get("judge", {}).get("action", "hold"),
                "score": full_analysis.get("debate", {}).get("judge", {}).get("score", 0)
            },
            "market_regime": full_analysis.get("regime"),
            "risk_analysis": risk_analysis,
            "hidden_gem_analysis": gem_analysis,
            "patterns": full_analysis.get("patterns"),
            "ecosystem_performance": full_analysis.get("ecosystem", {})
        }
    
    def get_debate_analysis(self, 
                           symbol: str,
                           options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Simplified debate analysis - just the core agent arguments and verdict
        """
        options = options or {}
        full_analysis = self.analyze_with_debate(
            symbol,
            period=options.get("period", "2y"),
            user_profile=options.get("user_profile"),
            what_if=options.get("what_if"),
            include_cross_market=False,
            include_stock_intel=False,
            max_hypotheses=options.get("max_hypotheses", 2),
            top_models=options.get("top_models", 1)
        )
        
        # Extract key debate information
        reality_reports = full_analysis.get("ecosystem", {}).get("reality_reports", [])
        first_report = reality_reports[0] if reality_reports else {}
        
        return {
            "symbol": full_analysis["symbol"],
            "debate": full_analysis["debate"],
            "prediction": {
                "direction": first_report.get("direction", "neutral"),
                "confidence": first_report.get("confidence", 0.5),
                "action": full_analysis.get("debate", {}).get("judge", {}).get("action", "hold")
            },
            "regime": full_analysis.get("regime"),
            "risk_metrics": {
                "sharpe": first_report.get("sharpe"),
                "max_drawdown": first_report.get("max_drawdown")
            } if first_report else None
        }
    
    def discover_stocks(self, 
                       min_confidence: float = 0.5,
                       sector: Optional[str] = None,
                       limit: int = 25) -> List[Dict[str, Any]]:
        """Discover elite stocks with high confidence"""
        data = {"min_confidence": min_confidence, "limit": limit}
        if sector:
            data["sector"] = sector
            
        return self._request("/api/v1/discover", method="POST", data=data)["discover"]
    
    def analyze_portfolio(self, 
                         holdings: Dict[str, float],
                         client_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze portfolio with AI agents"""
        data = {"holdings": holdings}
        if client_context:
            data["client_context"] = client_context
            
        return self._request("/api/v1/portfolio", method="POST", data=data)["portfolio"]
    
    def get_transparency(self, symbol: Optional[str] = None, limit: int = 40) -> List[Dict[str, Any]]:
        """Get decision transparency/audit trail"""
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
            
        return self._request("/api/v1/intelligence/transparency", params=params)["transparency_events"]
    
    def run_stress_tests(self, n_days: int = 400, seed: int = 42) -> Dict[str, Any]:
        """Run stress tests"""
        data = {"n_days": n_days, "seed": seed}
        return self._request("/api/v1/intelligence/stress", method="POST", data=data)["stress_tests"]
    
    def get_agent_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get a summary of all AI agents' output for a symbol
        """
        try:
            # Get stock intel (data collection agent)
            stock_intel = self.get_stock_intel(symbol)
            
            # Get debate analysis (4 agents + judge)
            debate_analysis = self.get_debate_analysis(symbol)
            
            return {
                "symbol": symbol,
                "data_collection_agent": {
                    "role": stock_intel["role"],
                    "mandate": stock_intel["mandate"],
                    "key_metrics": {
                        "price": stock_intel["fundamentals"].get("currentPrice"),
                        "pe_ratio": stock_intel["fundamentals"].get("trailingPE"),
                        "market_cap": stock_intel["fundamentals"].get("marketCap"),
                        "beta": stock_intel["fundamentals"].get("beta")
                    },
                    "data_sources": stock_intel["data_sources"]
                },
                "debate_agents": {
                    "bullish_agent": {
                        "stance": debate_analysis["debate"]["agents"][0]["stance"],
                        "confidence": debate_analysis["debate"]["agents"][0]["confidence"],
                        "key_points": debate_analysis["debate"]["agents"][0]["points"]
                    },
                    "bearish_agent": {
                        "stance": debate_analysis["debate"]["agents"][1]["stance"],
                        "confidence": debate_analysis["debate"]["agents"][1]["confidence"],
                        "key_points": debate_analysis["debate"]["agents"][1]["points"]
                    },
                    "risk_critic": {
                        "stance": debate_analysis["debate"]["agents"][2]["stance"],
                        "confidence": debate_analysis["debate"]["agents"][2]["confidence"],
                        "key_points": debate_analysis["debate"]["agents"][2]["points"]
                    },
                    "judge_verdict": {
                        "action": debate_analysis["debate"]["judge"]["action"],
                        "score": debate_analysis["debate"]["judge"]["score"],
                        "rationale": debate_analysis["debate"]["judge"]["rationale"],
                        "risk_flags": debate_analysis["debate"]["judge"]["risk_flags"]
                    }
                },
                "final_prediction": debate_analysis["prediction"],
                "market_regime": debate_analysis["regime"]
            }
        except Exception as e:
            raise Exception(f"Failed to get agent summary for {symbol}: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize API client
    api = StockPredictionAPI(APIConfig(
        base_url="http://localhost:5000",
        api_key=os.getenv("STOCK_API_KEY")
    ))
    
    # Example: Get agent summary for AAPL
    try:
        summary = api.get_agent_summary("AAPL")
        print(f"Agent Summary for AAPL:")
        print(f"Data Collection Agent: {summary['data_collection_agent']['role']}")
        print(f"Judge Verdict: {summary['debate_agents']['judge_verdict']['action']}")
        print(f"Final Prediction: {summary['final_prediction']}")
    except Exception as e:
        print(f"Error: {e}")
