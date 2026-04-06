"""
Multi-Agent Orchestrator
Coordinates the 4 AI agents with 1-minute analysis timeout and real-time streaming
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from quant_ecosystem.agents.data_collection_agent import data_collection_agent
from quant_ecosystem.agents.technical_analysis_agent import TechnicalAnalysisAgent
from quant_ecosystem.agents.fundamental_analysis_agent import FundamentalAnalysisAgent
from quant_ecosystem.agents.macro_economic_agent import MacroEconomicAgent
from quant_ecosystem.agents.sentiment_analysis_agent import SentimentAnalysisAgent
from quant_ecosystem.agents.quantitative_analysis_agent import QuantitativeAnalysisAgent
from quant_ecosystem.agents.risk_assessment_agent import RiskAssessmentAgent
from quant_ecosystem.agents.judge_agent import JudgeAgent, JudicialVerdict
from quant_ecosystem.streaming_api import stream_manager, LiveDebateTracker

log = logging.getLogger(__name__)


@dataclass
class AgentDebateResult:
    """Complete result from multi-agent debate with 7+ independent agents"""
    symbol: str
    session_id: str
    data_collection: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    fundamental_analysis: Dict[str, Any]
    macro_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    quantitative_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    judge_verdict: Dict[str, Any]
    financial_context: Dict[str, Any]
    debate_duration: float
    agent_request_log: Dict[str, List[str]]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "session_id": self.session_id,
            "financial_context": self.financial_context,
            "agents": {
                "data_collection": self.data_collection,
                "technical": self.technical_analysis,
                "fundamental": self.fundamental_analysis,
                "macro": self.macro_analysis,
                "sentiment": self.sentiment_analysis,
                "quantitative": self.quantitative_analysis,
                "risk": self.risk_assessment,
                "judge": self.judge_verdict
            },
            "verdict": {
                "action": self.judge_verdict.get("action", "HOLD"),
                "confidence": self.judge_verdict.get("confidence", 0),
                "rationale": self.judge_verdict.get("rationale", ""),
                "position_size": self.judge_verdict.get("recommended_position_size", "minimal")
            },
            "debate_duration": round(self.debate_duration, 2),
            "agent_request_log": self.agent_request_log,
            "timestamp": self.timestamp.isoformat()
        }


class MultiAgentOrchestrator:
    """
    Orchestrates the complete multi-agent analysis process:
    1. Data Collection Agent gathers initial data
    2. All 3 analysis agents work in parallel (1-minute timeout each)
    3. Agents can request additional data from Data Collection Agent
    4. Judge Agent evaluates all arguments and renders verdict
    5. Real-time streaming to frontend throughout the process
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
    def start_debate(self, 
                     symbol: str,
                     financial_context: Optional[Dict[str, Any]] = None,
                     streaming_callback: Optional[Callable] = None) -> str:
        """
        Start a new multi-agent debate session
        Returns session ID for tracking
        """
        session_id = f"debate_{symbol}_{int(time.time() * 1000)}"
        
        financial_context = financial_context or {
            "market_phase": "normal",
            "vix_level": 20,
            "systemic_risk": 0.3,
            "timestamp": datetime.now().isoformat()
        }
        
        # Create stream for real-time updates
        if streaming_callback:
            stream = stream_manager.create_stream(session_id, "sse")
            stream.register_client(streaming_callback)
        
        # Create tracker for logging
        tracker = LiveDebateTracker(session_id)
        
        # Store session
        with self.lock:
            self.active_sessions[session_id] = {
                "symbol": symbol,
                "financial_context": financial_context,
                "status": "initializing",
                "tracker": tracker,
                "start_time": time.time()
            }
        
        # Start debate in background thread
        debate_thread = threading.Thread(
            target=self._run_debate_process,
            args=(session_id, symbol, financial_context, tracker, streaming_callback)
        )
        debate_thread.daemon = True
        debate_thread.start()
        
        log.info(f"Orchestrator: Started debate session {session_id} for {symbol}")
        
        return session_id
    
    def _run_debate_process(self, session_id: str, symbol: str, 
                           financial_context: Dict[str, Any],
                           tracker: LiveDebateTracker,
                           streaming_callback: Optional[Callable]):
        """Run the complete debate process"""
        start_time = time.time()
        
        try:
            # Update status
            self._update_session_status(session_id, "data_collection", tracker, streaming_callback)
            
            # Phase 1: Data Collection Agent gathers all initial data
            tracker.log_agent_thought("data_collection", f"Beginning comprehensive data gathering for {symbol}", 1)
            
            initial_data = data_collection_agent.collect_initial_data(symbol)
            
            if "error" in initial_data:
                self._handle_error(session_id, tracker, streaming_callback, 
                                 f"Data collection failed: {initial_data['error']}")
                return
            
            tracker.update_agent_status("data_collection", "completed", {
                "data_points": len(initial_data),
                "collection_time": initial_data.get("collection_time", 0)
            })
            
            self._notify(streaming_callback, {
                "event_type": "phase_complete",
                "phase": "data_collection",
                "data_summary": {
                    "price_data_available": "price_data" in initial_data,
                    "fundamentals_available": "fundamentals" in initial_data,
                    "historical_data_available": "historical" in initial_data
                }
            })
            
            # Create data collection callback for agents
            def data_request_callback(agent_id: str, request_type: str, 
                                    symbol: str, parameters: Dict, urgency: str) -> Dict:
                """Callback for agents to request additional data"""
                tracker.log_agent_thought(agent_id, f"Requesting {request_type} data", 1)
                
                response = data_collection_agent.request_data(
                    agent_id=agent_id,
                    request_type=request_type,
                    symbol=symbol,
                    parameters=parameters,
                    urgency=urgency
                )
                
                self._notify(streaming_callback, {
                    "event_type": "agent_data_request",
                    "agent": agent_id,
                    "request_type": request_type,
                    "cache_hit": response.cache_hit,
                    "processing_time": response.processing_time
                })
                
                return response.data
            
            # Phase 2: Launch all 6 analysis agents in parallel with 1-minute timeout
            self._update_session_status(session_id, "agent_analysis", tracker, streaming_callback)
            
            # Create agent instances - all independent with their own stance determination
            technical_agent = TechnicalAnalysisAgent(data_request_callback)
            fundamental_agent = FundamentalAnalysisAgent(data_request_callback)
            macro_agent = MacroEconomicAgent(data_request_callback)
            sentiment_agent = SentimentAnalysisAgent(data_request_callback)
            quantitative_agent = QuantitativeAnalysisAgent(data_request_callback)
            risk_agent = RiskAssessmentAgent(data_request_callback)
            
            # Container for results
            agent_results = {
                "technical": None,
                "fundamental": None,
                "macro": None,
                "sentiment": None,
                "quantitative": None,
                "risk": None
            }
            
            # Launch parallel threads for agent analysis
            threads = []
            
            def run_technical():
                tracker.update_agent_status("technical", "analyzing", {"start_time": time.time()})
                try:
                    result = technical_agent.analyze(symbol, initial_data, financial_context)
                    agent_results["technical"] = result
                    tracker.log_agent_argument("technical", {
                        "stance": result.direction,
                        "conviction": result.conviction,
                        "price_target": result.price_target
                    }, 1)
                except Exception as e:
                    log.error(f"Technical agent error: {e}")
                    agent_results["technical"] = None
            
            def run_fundamental():
                tracker.update_agent_status("fundamental", "analyzing", {"start_time": time.time()})
                try:
                    result = fundamental_agent.analyze(symbol, initial_data, financial_context)
                    agent_results["fundamental"] = result
                    tracker.log_agent_argument("fundamental", {
                        "stance": result.direction,
                        "conviction": result.conviction,
                        "fair_value": result.fair_value
                    }, 1)
                except Exception as e:
                    log.error(f"Fundamental agent error: {e}")
                    agent_results["fundamental"] = None
            
            def run_macro():
                tracker.update_agent_status("macro", "analyzing", {"start_time": time.time()})
                try:
                    result = macro_agent.analyze(symbol, initial_data, financial_context)
                    agent_results["macro"] = result
                    tracker.log_agent_argument("macro", {
                        "stance": result.direction,
                        "conviction": result.conviction,
                        "economic_phase": result.economic_phase
                    }, 1)
                except Exception as e:
                    log.error(f"Macro agent error: {e}")
                    agent_results["macro"] = None
            
            def run_sentiment():
                tracker.update_agent_status("sentiment", "analyzing", {"start_time": time.time()})
                try:
                    result = sentiment_agent.analyze(symbol, initial_data, financial_context)
                    agent_results["sentiment"] = result
                    tracker.log_agent_argument("sentiment", {
                        "stance": result.direction,
                        "conviction": result.conviction,
                        "sentiment_score": result.sentiment_score
                    }, 1)
                except Exception as e:
                    log.error(f"Sentiment agent error: {e}")
                    agent_results["sentiment"] = None
            
            def run_quantitative():
                tracker.update_agent_status("quantitative", "analyzing", {"start_time": time.time()})
                try:
                    result = quantitative_agent.analyze(symbol, initial_data, financial_context)
                    agent_results["quantitative"] = result
                    tracker.log_agent_argument("quantitative", {
                        "stance": result.direction,
                        "conviction": result.conviction,
                        "statistical_edge": result.statistical_edge
                    }, 1)
                except Exception as e:
                    log.error(f"Quantitative agent error: {e}")
                    agent_results["quantitative"] = None
            
            def run_risk():
                tracker.update_agent_status("risk", "analyzing", {"start_time": time.time()})
                try:
                    # Generate real bull/bear cases from technical data
                    from .data import load_ohlcv
                    from .features import build_feature_matrix
                    
                    ohlcv, ref = load_ohlcv(symbol)
                    close = ohlcv['close']
                    
                    # Calculate real technical signals for bull/bear case
                    sma_20 = close.rolling(20).mean().iloc[-1]
                    sma_50 = close.rolling(50).mean().iloc[-1]
                    current_price = close.iloc[-1]
                    
                    # RSI calculation
                    delta = close.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1]
                    
                    # Trend determination
                    trend_bullish = current_price > sma_20 > sma_50
                    trend_bearish = current_price < sma_20 < sma_50
                    
                    # Build real bull case
                    bull_case = {
                        "confidence": 0.75 if trend_bullish else 0.45,
                        "key_points": [
                            f"Price ${current_price:.2f} {'above' if current_price > sma_20 else 'below'} 20-day MA (${sma_20:.2f})",
                            f"RSI at {current_rsi:.1f} - {'neutral zone' if 30 <= current_rsi <= 70 else 'extreme'}" if not trend_bullish else f"RSI {current_rsi:.1f} supports momentum",
                            f"50-day MA trend: {'rising' if sma_50 > sma_50 * 0.98 else 'flat/declining'}"
                        ] if trend_bullish else [
                            "Technical indicators not strongly bullish",
                            f"Price needs to break above ${sma_20:.2f} for bullish confirmation"
                        ]
                    }
                    
                    # Build real bear case
                    bear_case = {
                        "confidence": 0.75 if trend_bearish else 0.45,
                        "key_points": [
                            f"Price ${current_price:.2f} {'below' if current_price < sma_20 else 'above'} 20-day MA (${sma_20:.2f})",
                            f"RSI at {current_rsi:.1f} - {'oversold bounce possible' if current_rsi < 30 else 'neutral/bearish'}" if trend_bearish else f"RSI {current_rsi:.1f} not confirming bearish momentum",
                            f"Support level: ${sma_50:.2f} (50-day MA)"
                        ] if trend_bearish else [
                            "Technical indicators not strongly bearish",
                            f"Price holding above ${sma_50:.2f} support"
                        ]
                    }
                    
                    result = risk_agent.analyze(symbol, initial_data, bull_case, 
                                              bear_case, financial_context)
                    agent_results["risk"] = result
                    tracker.log_agent_argument("risk", {
                        "risk_score": result.risk_score,
                        "risk_level": result.risk_level,
                        "bull_confidence": bull_case["confidence"],
                        "bear_confidence": bear_case["confidence"]
                    }, 1)
                except Exception as e:
                    log.error(f"Risk agent error: {e}")
                    agent_results["risk"] = None
            
            # Start all threads
            threads.append(threading.Thread(target=run_technical))
            threads.append(threading.Thread(target=run_fundamental))
            threads.append(threading.Thread(target=run_macro))
            threads.append(threading.Thread(target=run_sentiment))
            threads.append(threading.Thread(target=run_quantitative))
            threads.append(threading.Thread(target=run_risk))
            
            for t in threads:
                t.daemon = True
                t.start()
            
            # Wait for all with 1-minute timeout
            timeout = 60  # 1 minute
            start_wait = time.time()
            
            for t in threads:
                remaining = timeout - (time.time() - start_wait)
                if remaining > 0:
                    t.join(timeout=remaining)
            
            # Check if any agents timed out
            timed_out = []
            for name, result in agent_results.items():
                if result is None:
                    timed_out.append(name)
            
            if timed_out:
                tracker.log_rethinking(f"Agents {', '.join(timed_out)} timed out, rethinking with limited data")
                self._notify(streaming_callback, {
                    "event_type": "timeout",
                    "timed_out_agents": timed_out,
                    "message": "Some agents exceeded 1-minute limit, using available analysis"
                })
            
            # Generate arguments from completed analyses
            technical_arg = technical_agent.argue(agent_results["technical"]) if agent_results["technical"] else {
                "agent": "technical_analysis_agent",
                "stance": "neutral",
                "confidence": 0.5,
                "points": ["Technical analysis incomplete"],
                "timestamp": datetime.now().isoformat()
            }
            
            fundamental_arg = fundamental_agent.argue(agent_results["fundamental"]) if agent_results["fundamental"] else {
                "agent": "fundamental_analysis_agent",
                "stance": "neutral",
                "confidence": 0.5,
                "points": ["Fundamental analysis incomplete"],
                "timestamp": datetime.now().isoformat()
            }
            
            macro_arg = macro_agent.argue(agent_results["macro"]) if agent_results["macro"] else {
                "agent": "macro_economic_agent",
                "stance": "neutral",
                "confidence": 0.5,
                "points": ["Macro analysis incomplete"],
                "timestamp": datetime.now().isoformat()
            }
            
            sentiment_arg = sentiment_agent.argue(agent_results["sentiment"]) if agent_results["sentiment"] else {
                "agent": "sentiment_analysis_agent",
                "stance": "neutral",
                "confidence": 0.5,
                "points": ["Sentiment analysis incomplete"],
                "timestamp": datetime.now().isoformat()
            }
            
            quantitative_arg = quantitative_agent.argue(agent_results["quantitative"]) if agent_results["quantitative"] else {
                "agent": "quantitative_analysis_agent",
                "stance": "neutral",
                "confidence": 0.5,
                "points": ["Quantitative analysis incomplete"],
                "timestamp": datetime.now().isoformat()
            }
            
            risk_arg = risk_agent.argue(agent_results["risk"]) if agent_results["risk"] else {
                "agent": "risk_assessment_agent",
                "stance": "critique",
                "confidence": 0.5,
                "points": ["Risk assessment incomplete"],
                "risk_score": 0.5,
                "risk_level": "moderate",
                "timestamp": datetime.now().isoformat()
            }
            
            self._notify(streaming_callback, {
                "event_type": "phase_complete",
                "phase": "agent_analysis",
                "agents_completed": sum(1 for r in agent_results.values() if r is not None),
                "agents_timed_out": len(timed_out),
                "agent_stances": {
                    "technical": technical_arg["stance"],
                    "fundamental": fundamental_arg["stance"],
                    "macro": macro_arg["stance"],
                    "sentiment": sentiment_arg["stance"],
                    "quantitative": quantitative_arg["stance"],
                    "risk": risk_arg["stance"]
                }
            })
            
            # Phase 3: Judge Agent deliberates
            self._update_session_status(session_id, "judging", tracker, streaming_callback)
            tracker.update_agent_status("judge", "deliberating", {"start_time": time.time()})
            
            judge_agent = JudgeAgent()
            
            verdict = judge_agent.deliberate_multi_agent(
                symbol=symbol,
                technical_argument=technical_arg,
                fundamental_argument=fundamental_arg,
                macro_argument=macro_arg,
                sentiment_argument=sentiment_arg,
                quantitative_argument=quantitative_arg,
                risk_assessment=risk_arg,
                financial_context=financial_context
            )
            
            tracker.log_judge_evaluation({
                "action": verdict.action,
                "confidence": verdict.confidence,
                "score": verdict.score
            }, 1)
            
            # Phase 4: Finalize and return result
            self._update_session_status(session_id, "complete", tracker, streaming_callback)
            
            debate_duration = time.time() - start_time
            
            # Get data request summary
            request_summary = data_collection_agent.get_request_summary(symbol)
            
            result = AgentDebateResult(
                symbol=symbol,
                session_id=session_id,
                data_collection={
                    "initial_data_points": len(initial_data),
                    "collection_time": initial_data.get("collection_time", 0),
                    "requests_made": len(request_summary.get("unique_request_types", []))
                },
                technical_analysis=technical_arg,
                fundamental_analysis=fundamental_arg,
                macro_analysis=macro_arg,
                sentiment_analysis=sentiment_arg,
                quantitative_analysis=quantitative_arg,
                risk_assessment=risk_arg,
                judge_verdict=judge_agent.format_verdict_for_display(verdict),
                financial_context=financial_context,
                debate_duration=debate_duration,
                agent_request_log=request_summary.get("by_agent", {})
            )
            
            # Store result in session
            with self.lock:
                if session_id in self.active_sessions:
                    self.active_sessions[session_id]["result"] = result
                    self.active_sessions[session_id]["status"] = "complete"
                    self.active_sessions[session_id]["duration"] = debate_duration
            
            tracker.log_final_verdict(result.judge_verdict)
            
            self._notify(streaming_callback, {
                "event_type": "debate_complete",
                "result": result.to_dict(),
                "duration": debate_duration
            })
            
            log.info(f"Orchestrator: Debate complete for {symbol} - {verdict.action.upper()} "
                    f"({verdict.confidence:.2f} confidence) in {debate_duration:.1f}s")
            
        except Exception as e:
            log.error(f"Orchestrator: Debate process error: {e}")
            self._handle_error(session_id, tracker, streaming_callback, str(e))
    
    def _update_session_status(self, session_id: str, status: str, 
                              tracker: LiveDebateTracker,
                              streaming_callback: Optional[Callable]):
        """Update session status and notify"""
        with self.lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = status
        
        tracker.update_agent_status("system", status)
        
        self._notify(streaming_callback, {
            "event_type": "status_update",
            "status": status,
            "message": f"Debate process: {status}"
        })
    
    def _handle_error(self, session_id: str, tracker: LiveDebateTracker,
                     streaming_callback: Optional[Callable], error: str):
        """Handle errors in debate process"""
        with self.lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = "error"
                self.active_sessions[session_id]["error"] = error
        
        tracker.update_agent_status("system", "error", {"error": error})
        
        self._notify(streaming_callback, {
            "event_type": "error",
            "error": error
        })
    
    def _notify(self, callback: Optional[Callable], data: Dict[str, Any]):
        """Send notification to callback if available"""
        if callback:
            try:
                data["timestamp"] = datetime.now().isoformat()
                callback(data)
            except Exception as e:
                log.warning(f"Notification error: {e}")
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a debate session"""
        with self.lock:
            session = self.active_sessions.get(session_id)
            if session:
                return {
                    "session_id": session_id,
                    "symbol": session.get("symbol"),
                    "status": session.get("status"),
                    "duration": time.time() - session.get("start_time", time.time()),
                    "has_result": "result" in session
                }
            return None
    
    def get_session_result(self, session_id: str) -> Optional[AgentDebateResult]:
        """Get final result of a debate session"""
        with self.lock:
            session = self.active_sessions.get(session_id)
            if session:
                return session.get("result")
            return None
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of all active sessions"""
        with self.lock:
            return [
                {
                    "session_id": sid,
                    "symbol": s.get("symbol"),
                    "status": s.get("status"),
                    "elapsed": time.time() - s.get("start_time", time.time())
                }
                for sid, s in self.active_sessions.items()
            ]


# Global orchestrator instance
orchestrator = MultiAgentOrchestrator()
