"""
Iterative Multi-Round Debate Engine
Real-time AI debate system with timeout, rethinking, and financial adaptation
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

log = logging.getLogger(__name__)


class DebateStatus(Enum):
    INITIALIZING = "initializing"
    ROUND_1 = "round_1"
    ROUND_2 = "round_2"
    ROUND_3 = "round_3"
    RETHINKING = "rethinking"
    CONCLUDING = "concluding"
    COMPLETE = "complete"
    TIMEOUT = "timeout"


@dataclass
class AgentArgument:
    role: str
    stance: str
    points: List[str]
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    round_number: int = 1
    adapted_from_previous: bool = False
    thinking_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "stance": self.stance,
            "points": self.points,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "round_number": self.round_number,
            "adapted_from_previous": self.adapted_from_previous,
            "thinking_time": round(self.thinking_time, 2)
        }


@dataclass
class DebateRound:
    round_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    bull_argument: Optional[AgentArgument] = None
    bear_argument: Optional[AgentArgument] = None
    risk_argument: Optional[AgentArgument] = None
    judge_evaluation: Optional[Dict[str, Any]] = None
    consensus_reached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "bull_argument": self.bull_argument.to_dict() if self.bull_argument else None,
            "bear_argument": self.bear_argument.to_dict() if self.bear_argument else None,
            "risk_argument": self.risk_argument.to_dict() if self.risk_argument else None,
            "judge_evaluation": self.judge_evaluation,
            "consensus_reached": self.consensus_reached,
            "duration_seconds": self.get_duration()
        }
    
    def get_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()


@dataclass
class DebateSession:
    session_id: str
    symbol: str
    financial_context: Dict[str, Any]
    rounds: List[DebateRound] = field(default_factory=list)
    status: DebateStatus = DebateStatus.INITIALIZING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    final_verdict: Optional[Dict[str, Any]] = None
    consensus_round: Optional[int] = None
    streaming_callback: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "symbol": self.symbol,
            "financial_context": self.financial_context,
            "status": self.status.value,
            "rounds": [r.to_dict() for r in self.rounds],
            "total_rounds": len(self.rounds),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration": self.get_total_duration(),
            "final_verdict": self.final_verdict,
            "consensus_round": self.consensus_round
        }
    
    def get_total_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def notify_update(self, event_type: str, data: Dict[str, Any]):
        """Notify streaming callback of updates"""
        if self.streaming_callback:
            try:
                self.streaming_callback({
                    "session_id": self.session_id,
                    "event_type": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                })
            except Exception as e:
                log.warning(f"Streaming callback error: {e}")


class IterativeDebateEngine:
    """
    Advanced debate system with multi-round iteration, timeout handling,
    and financial situation adaptation
    """
    
    def __init__(self, 
                 max_rounds: int = 3,
                 timeout_seconds: int = 60,
                 consensus_threshold: float = 0.7):
        self.max_rounds = max_rounds
        self.timeout_seconds = timeout_seconds
        self.consensus_threshold = consensus_threshold
        self.active_sessions: Dict[str, DebateSession] = {}
        
    def start_debate(self, 
                     symbol: str,
                     financial_context: Dict[str, Any],
                     prediction_summary: Dict[str, Any],
                     regime: Dict[str, Any],
                     risk_metrics: Dict[str, Any],
                     streaming_callback: Optional[Callable] = None) -> str:
        """Start a new debate session"""
        session_id = f"debate_{symbol}_{int(time.time())}"
        
        session = DebateSession(
            session_id=session_id,
            symbol=symbol,
            financial_context=financial_context,
            streaming_callback=streaming_callback,
            status=DebateStatus.ROUND_1
        )
        
        self.active_sessions[session_id] = session
        
        # Start debate in background thread
        debate_thread = threading.Thread(
            target=self._run_iterative_debate,
            args=(session, prediction_summary, regime, risk_metrics)
        )
        debate_thread.daemon = True
        debate_thread.start()
        
        return session_id
    
    def _run_iterative_debate(self,
                             session: DebateSession,
                             prediction_summary: Dict[str, Any],
                             regime: Dict[str, Any],
                             risk_metrics: Dict[str, Any]):
        """Run the iterative debate process"""
        try:
            for round_num in range(1, self.max_rounds + 1):
                if session.status == DebateStatus.COMPLETE:
                    break
                
                # Check if we need to rethink (after timeout in previous rounds)
                if round_num > 1 and session.rounds:
                    last_round = session.rounds[-1]
                    if last_round.get_duration() >= self.timeout_seconds:
                        session.status = DebateStatus.RETHINKING
                        session.notify_update("status_change", {
                            "status": "rethinking",
                            "message": f"Round {round_num-1} timed out. Agents rethinking positions..."
                        })
                
                # Run debate round with timeout
                round_result = self._run_debate_round(
                    session, round_num, prediction_summary, regime, risk_metrics
                )
                
                session.rounds.append(round_result)
                
                # Check for consensus
                if round_result.consensus_reached:
                    session.consensus_round = round_num
                    session.status = DebateStatus.CONCLUDING
                    session.notify_update("consensus_reached", {
                        "round": round_num,
                        "message": "Agents reached consensus!"
                    })
                    break
                
                # Check if max rounds reached without consensus
                if round_num == self.max_rounds:
                    session.status = DebateStatus.CONCLUDING
                    session.notify_update("max_rounds_reached", {
                        "message": "Maximum rounds reached without full consensus"
                    })
            
            # Generate final verdict
            final_verdict = self._generate_final_verdict(session)
            session.final_verdict = final_verdict
            session.status = DebateStatus.COMPLETE
            session.end_time = datetime.now()
            
            session.notify_update("complete", {
                "verdict": final_verdict,
                "total_rounds": len(session.rounds),
                "duration": session.get_total_duration()
            })
            
        except Exception as e:
            log.error(f"Debate error for {session.symbol}: {e}")
            session.status = DebateStatus.TIMEOUT
            session.end_time = datetime.now()
            session.notify_update("error", {"message": str(e)})
    
    def _run_debate_round(self,
                         session: DebateSession,
                         round_num: int,
                         prediction_summary: Dict[str, Any],
                         regime: Dict[str, Any],
                         risk_metrics: Dict[str, Any]) -> DebateRound:
        """Run a single debate round with timeout"""
        round_start = datetime.now()
        
        debate_round = DebateRound(
            round_number=round_num,
            start_time=round_start
        )
        
        # Update status
        status_map = {
            1: DebateStatus.ROUND_1,
            2: DebateStatus.ROUND_2,
            3: DebateStatus.ROUND_3
        }
        session.status = status_map.get(round_num, DebateStatus.ROUND_3)
        
        session.notify_update("round_start", {
            "round": round_num,
            "message": f"Starting debate round {round_num}"
        })
        
        # Get previous round arguments for adaptation
        previous_round = session.rounds[-1] if session.rounds else None
        
        # Generate Bull argument with timeout
        bull_start = time.time()
        bull_arg = self._generate_bull_argument(
            session, round_num, prediction_summary, regime, risk_metrics, previous_round
        )
        bull_arg.thinking_time = time.time() - bull_start
        debate_round.bull_argument = bull_arg
        
        session.notify_update("agent_response", {
            "agent": "bull",
            "round": round_num,
            "argument": bull_arg.to_dict()
        })
        
        # Check timeout
        if self._check_timeout(round_start):
            debate_round.end_time = datetime.now()
            return debate_round
        
        # Generate Bear argument with timeout
        bear_start = time.time()
        bear_arg = self._generate_bear_argument(
            session, round_num, prediction_summary, regime, risk_metrics, previous_round
        )
        bear_arg.thinking_time = time.time() - bear_start
        debate_round.bear_argument = bear_arg
        
        session.notify_update("agent_response", {
            "agent": "bear",
            "round": round_num,
            "argument": bear_arg.to_dict()
        })
        
        # Check timeout
        if self._check_timeout(round_start):
            debate_round.end_time = datetime.now()
            return debate_round
        
        # Generate Risk argument with timeout
        risk_start = time.time()
        risk_arg = self._generate_risk_argument(
            session, round_num, prediction_summary, regime, risk_metrics, previous_round
        )
        risk_arg.thinking_time = time.time() - risk_start
        debate_round.risk_argument = risk_arg
        
        session.notify_update("agent_response", {
            "agent": "risk",
            "round": round_num,
            "argument": risk_arg.to_dict()
        })
        
        # Check timeout
        if self._check_timeout(round_start):
            debate_round.end_time = datetime.now()
            return debate_round
        
        # Judge evaluation
        judge_eval = self._judge_evaluate_round(debate_round, session.financial_context)
        debate_round.judge_evaluation = judge_eval
        
        session.notify_update("judge_evaluation", {
            "round": round_num,
            "evaluation": judge_eval
        })
        
        # Check for consensus
        if judge_eval.get("consensus_score", 0) >= self.consensus_threshold:
            debate_round.consensus_reached = True
        
        debate_round.end_time = datetime.now()
        
        session.notify_update("round_complete", {
            "round": round_num,
            "duration": debate_round.get_duration(),
            "consensus_reached": debate_round.consensus_reached
        })
        
        return debate_round
    
    def _check_timeout(self, round_start: datetime) -> bool:
        """Check if round has timed out"""
        elapsed = (datetime.now() - round_start).total_seconds()
        return elapsed >= self.timeout_seconds
    
    def _generate_bull_argument(self,
                               session: DebateSession,
                               round_num: int,
                               prediction_summary: Dict[str, Any],
                               regime: Dict[str, Any],
                               risk_metrics: Dict[str, Any],
                               previous_round: Optional[DebateRound]) -> AgentArgument:
        """Generate bullish argument with adaptation"""
        direction = str(prediction_summary.get("direction", "neutral")).lower()
        conf = float(prediction_summary.get("confidence", 0.5) or 0.5)
        trend = str(regime.get("trend", "sideways"))
        vol = str(regime.get("volatility", "normal"))
        
        # Base points
        points = [
            f"Round {round_num}: Trend regime reads {trend}; momentum aligns with stated direction {direction}.",
            f"Model confidence {conf:.2f} supports incremental long bias if risk allows."
        ]
        
        # Adapt based on financial context
        financial_context = session.financial_context
        market_phase = financial_context.get("market_phase", "normal")
        
        if market_phase == "recession":
            points.append("In recessionary phase, value opportunities emerge as fear overshoots fundamentals.")
        elif market_phase == "expansion":
            points.append("Economic expansion phase supports growth-oriented positions.")
        elif market_phase == "inflation":
            points.append("Inflationary environment favors real assets and pricing-power companies.")
        
        # Adapt from previous round if exists
        adapted = False
        if previous_round and previous_round.bull_argument:
            prev_conf = previous_round.bull_argument.confidence
            if prev_conf < 0.5:
                points.append(f"Reassessing after low confidence ({prev_conf:.2f}) in previous round.")
                points.append("Seeking additional confirming signals for bull case.")
                adapted = True
        
        # Calculate confidence with financial context adjustment
        bull_conf = min(0.95, 0.45 + conf * 0.5 + (0.1 if trend == "bull" else 0.0))
        
        # Adjust for financial stress
        if financial_context.get("vix_level", 20) > 30:
            bull_conf *= 0.9  # Reduce confidence in high volatility
            points.append("Adjusted for elevated market volatility (VIX > 30).")
        
        return AgentArgument(
            role="bull",
            stance="constructive",
            points=points,
            confidence=round(bull_conf, 3),
            round_number=round_num,
            adapted_from_previous=adapted,
            evidence={
                "trend": trend,
                "model_confidence": conf,
                "market_phase": market_phase
            }
        )
    
    def _generate_bear_argument(self,
                               session: DebateSession,
                               round_num: int,
                               prediction_summary: Dict[str, Any],
                               regime: Dict[str, Any],
                               risk_metrics: Dict[str, Any],
                               previous_round: Optional[DebateRound]) -> AgentArgument:
        """Generate bearish argument with adaptation"""
        direction = str(prediction_summary.get("direction", "neutral")).lower()
        trend = str(regime.get("trend", "sideways"))
        vol = str(regime.get("volatility", "normal"))
        
        points = [
            f"Round {round_num}: Volatility regime {vol} may punish directional bets.",
            "Mean reversion risk rises after extended moves; confirmation needed."
        ]
        
        if trend == "bear":
            points.append("Macro trend bucket is bearish — fade aggressive longs.")
        
        if vol == "high_vol":
            points.append("High vol: tail risk dominates short-horizon EV.")
        
        # Adapt based on financial context
        financial_context = session.financial_context
        market_phase = financial_context.get("market_phase", "normal")
        
        if market_phase == "recession":
            points.append("Recessionary signals suggest defensive positioning warranted.")
        elif market_phase == "bubble":
            points.append("Bubble-phase indicators suggest elevated crash risk.")
        
        # Adapt from previous round
        adapted = False
        if previous_round and previous_round.bear_argument:
            prev_conf = previous_round.bear_argument.confidence
            if prev_conf < 0.5:
                points.append(f"Reassessing after low confidence ({prev_conf:.2f}) in previous round.")
                points.append("Strengthening risk case with additional evidence.")
                adapted = True
        
        bear_conf = min(0.95, 0.45 + (0.15 if vol == "high_vol" else 0.0) + (0.1 if trend == "bear" else 0.0))
        
        return AgentArgument(
            role="bear",
            stance="skeptical",
            points=points,
            confidence=round(bear_conf, 3),
            round_number=round_num,
            adapted_from_previous=adapted,
            evidence={
                "trend": trend,
                "volatility": vol,
                "market_phase": market_phase
            }
        )
    
    def _generate_risk_argument(self,
                                 session: DebateSession,
                                 round_num: int,
                                 prediction_summary: Dict[str, Any],
                                 regime: Dict[str, Any],
                                 risk_metrics: Dict[str, Any],
                                 previous_round: Optional[DebateRound]) -> AgentArgument:
        """Generate risk assessment argument with adaptation"""
        max_dd = risk_metrics.get("max_drawdown_proxy", 0)
        sharpe = risk_metrics.get("sharpe_proxy", 0)
        
        points = [
            f"Round {round_num}: Drawdown proxy from metrics: {max_dd}",
            f"Sharpe-like gauge: {sharpe}"
        ]
        
        # Add microstructure analysis if available
        micro = risk_metrics.get("microstructure", {})
        if micro:
            stress = micro.get("stress_score", 0)
            points.append(f"Microstructure stress: {stress:.2f}")
            
            if stress > 0.5:
                points.append("Elevated market microstructure stress detected.")
        
        # Adapt based on financial context
        financial_context = session.financial_context
        systemic_risk = financial_context.get("systemic_risk", 0)
        
        if systemic_risk > 0.7:
            points.append(f"High systemic risk detected: {systemic_risk:.2f}")
            points.append("Recommend position sizing reduction.")
        
        # Adapt from previous round
        adapted = False
        if previous_round and previous_round.risk_argument:
            prev_points = previous_round.risk_argument.points
            if len(prev_points) < 3:
                points.append("Expanding risk analysis with additional factors.")
                adapted = True
        
        risk_conf = 0.75
        
        # Adjust confidence based on market stress
        if financial_context.get("vix_level", 20) > 25:
            risk_conf = 0.85  # Higher confidence in risk assessment during stress
        
        return AgentArgument(
            role="risk",
            stance="critique",
            points=points,
            confidence=round(risk_conf, 3),
            round_number=round_num,
            adapted_from_previous=adapted,
            evidence={
                "max_drawdown": max_dd,
                "sharpe": sharpe,
                "systemic_risk": systemic_risk
            }
        )
    
    def _judge_evaluate_round(self, debate_round: DebateRound, financial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Judge evaluates the round arguments"""
        bull = debate_round.bull_argument
        bear = debate_round.bear_argument
        risk = debate_round.risk_argument
        
        if not all([bull, bear, risk]):
            return {
                "error": "Missing agent arguments",
                "consensus_score": 0
            }
        
        # Calculate weighted score
        score = bull.confidence - bear.confidence
        
        # Risk adjustment
        risk_adjustment = (1 - risk.confidence) * 0.3
        adjusted_score = score - risk_adjustment
        
        # Determine action
        if adjusted_score > 0.25:
            action = "buy"
        elif adjusted_score < -0.25:
            action = "sell"
        else:
            action = "hold"
        
        # Calculate consensus score (0-1)
        # Higher when agents agree on direction
        confidence_diff = abs(bull.confidence - bear.confidence)
        risk_alignment = 1 - abs(risk.confidence - 0.75)  # Risk should be around 0.75
        consensus_score = (confidence_diff * 0.6 + risk_alignment * 0.4)
        
        # Financial context adjustment
        if financial_context.get("market_phase") == "crisis":
            consensus_score *= 0.8  # Reduce confidence during crisis
        
        return {
            "action": action,
            "score": round(adjusted_score, 3),
            "raw_score": round(score, 3),
            "risk_adjustment": round(risk_adjustment, 3),
            "consensus_score": round(consensus_score, 3),
            "rationale": f"Judge weighs trend/vol against model confidence and risk flags in Round {debate_round.round_number}.",
            "risk_flags": [p for p in (risk.points if risk else []) if "vol" in p.lower() or "Microstructure" in p or "risk" in p.lower()],
            "agents_confidence": {
                "bull": bull.confidence,
                "bear": bear.confidence,
                "risk": risk.confidence
            }
        }
    
    def _generate_final_verdict(self, session: DebateSession) -> Dict[str, Any]:
        """Generate final verdict from all rounds"""
        if not session.rounds:
            return {
                "action": "hold",
                "score": 0,
                "rationale": "No debate rounds completed"
            }
        
        # Use the last round's evaluation or best consensus round
        if session.consensus_round:
            final_round = session.rounds[session.consensus_round - 1]
        else:
            final_round = session.rounds[-1]
        
        judge_eval = final_round.judge_evaluation or {}
        
        # Compile all arguments
        all_bull_points = []
        all_bear_points = []
        all_risk_points = []
        
        for r in session.rounds:
            if r.bull_argument:
                all_bull_points.extend(r.bull_argument.points)
            if r.bear_argument:
                all_bear_points.extend(r.bear_argument.points)
            if r.risk_argument:
                all_risk_points.extend(r.risk_argument.points)
        
        return {
            "action": judge_eval.get("action", "hold"),
            "score": judge_eval.get("score", 0),
            "consensus_score": judge_eval.get("consensus_score", 0),
            "rationale": judge_eval.get("rationale", ""),
            "risk_flags": judge_eval.get("risk_flags", []),
            "final_round": final_round.round_number,
            "total_rounds": len(session.rounds),
            "consensus_reached": session.consensus_round is not None,
            "all_arguments": {
                "bullish": all_bull_points[-3:] if all_bull_points else [],  # Last 3 points
                "bearish": all_bear_points[-3:] if all_bear_points else [],
                "risk": all_risk_points[-3:] if all_risk_points else []
            },
            "agent_confidence_evolution": {
                "bull": [r.bull_argument.confidence for r in session.rounds if r.bull_argument],
                "bear": [r.bear_argument.confidence for r in session.rounds if r.bear_argument],
                "risk": [r.risk_argument.confidence for r in session.rounds if r.risk_argument]
            }
        }
    
    def get_session(self, session_id: str) -> Optional[DebateSession]:
        """Get debate session by ID"""
        return self.active_sessions.get(session_id)
    
    def get_all_sessions(self) -> List[DebateSession]:
        """Get all active sessions"""
        return list(self.active_sessions.values())


# Global debate engine instance
debate_engine = IterativeDebateEngine()
