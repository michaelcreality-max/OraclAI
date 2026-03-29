"""
Real-time Streaming API for AI Debate Visibility
WebSocket and Server-Sent Events support for live debate updates
"""

from __future__ import annotations

import logging
import json
import threading
import queue
import time
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from functools import wraps

log = logging.getLogger(__name__)


class DebateStreamManager:
    """
    Manages real-time streaming of AI debate updates to frontend
    Supports both WebSocket and SSE connections
    """
    
    def __init__(self):
        self.active_streams: Dict[str, 'DebateStream'] = {}
        self.lock = threading.Lock()
        
    def create_stream(self, session_id: str, stream_type: str = "sse") -> 'DebateStream':
        """Create a new debate stream"""
        with self.lock:
            stream = DebateStream(session_id, stream_type)
            self.active_streams[session_id] = stream
            log.info(f"Created {stream_type} stream for session {session_id}")
            return stream
    
    def get_stream(self, session_id: str) -> Optional['DebateStream']:
        """Get existing stream by session ID"""
        return self.active_streams.get(session_id)
    
    def remove_stream(self, session_id: str):
        """Remove a stream"""
        with self.lock:
            if session_id in self.active_streams:
                stream = self.active_streams[session_id]
                stream.close()
                del self.active_streams[session_id]
                log.info(f"Removed stream for session {session_id}")
    
    def broadcast_to_session(self, session_id: str, event_data: Dict[str, Any]):
        """Broadcast event to all connected clients for a session"""
        stream = self.get_stream(session_id)
        if stream:
            stream.broadcast(event_data)
    
    def get_active_stream_count(self) -> int:
        """Get number of active streams"""
        return len(self.active_streams)


class DebateStream:
    """
    Individual debate stream for real-time updates
    """
    
    def __init__(self, session_id: str, stream_type: str = "sse"):
        self.session_id = session_id
        self.stream_type = stream_type
        self.message_queue: queue.Queue = queue.Queue()
        self.clients: List[Callable] = []
        self.is_active = True
        self.created_at = datetime.now()
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
    def broadcast(self, event_data: Dict[str, Any]):
        """Broadcast event to all connected clients"""
        if not self.is_active:
            return
        
        # Add timestamp if not present
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now().isoformat()
        
        # Store in history
        self.event_history.append(event_data)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Put in queue for SSE/WebSocket
        self.message_queue.put(event_data)
        
        # Call registered callbacks
        for client_callback in self.clients:
            try:
                client_callback(event_data)
            except Exception as e:
                log.warning(f"Error in client callback: {e}")
    
    def register_client(self, callback: Callable):
        """Register a client callback"""
        self.clients.append(callback)
        log.debug(f"Registered client for stream {self.session_id}")
    
    def unregister_client(self, callback: Callable):
        """Unregister a client callback"""
        if callback in self.clients:
            self.clients.remove(callback)
            log.debug(f"Unregistered client for stream {self.session_id}")
    
    def get_sse_generator(self):
        """Generate SSE events"""
        def generate():
            while self.is_active:
                try:
                    # Wait for message with timeout
                    event_data = self.message_queue.get(timeout=30)
                    
                    # Format as SSE
                    sse_data = f"data: {json.dumps(event_data)}\n\n"
                    yield sse_data
                    
                except queue.Empty:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()})}\n\n"
                    continue
                except Exception as e:
                    log.error(f"SSE generation error: {e}")
                    break
        
        return generate()
    
    def get_event_history(self, since_timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get event history, optionally since a specific timestamp"""
        if since_timestamp is None:
            return self.event_history[-100:]  # Last 100 events
        
        # Filter events after timestamp
        filtered = []
        for event in self.event_history:
            if event.get("timestamp", "") > since_timestamp:
                filtered.append(event)
        return filtered
    
    def close(self):
        """Close the stream"""
        self.is_active = False
        self.clients.clear()
        log.info(f"Closed stream {self.session_id}")


# Global stream manager
stream_manager = DebateStreamManager()


def create_streaming_callback(session_id: str) -> Callable:
    """Create a callback function that streams debate updates"""
    def streaming_callback(event_data: Dict[str, Any]):
        stream_manager.broadcast_to_session(session_id, event_data)
    return streaming_callback


class LiveDebateTracker:
    """
    Tracks and displays live debate progress in real-time
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.events: List[Dict[str, Any]] = []
        self.current_round = 0
        self.agent_statuses = {
            "bull": "waiting",
            "bear": "waiting",
            "risk": "waiting",
            "judge": "waiting"
        }
        
    def update_agent_status(self, agent: str, status: str, data: Dict[str, Any] = None):
        """Update agent status and broadcast"""
        self.agent_statuses[agent] = status
        
        event = {
            "session_id": self.session_id,
            "event_type": "agent_status_update",
            "agent": agent,
            "status": status,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds()
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
    def log_agent_thought(self, agent: str, thought: str, round_num: int):
        """Log agent's thinking process"""
        event = {
            "session_id": self.session_id,
            "event_type": "agent_thought",
            "agent": agent,
            "thought": thought,
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds()
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
    def log_agent_argument(self, agent: str, argument: Dict[str, Any], round_num: int):
        """Log agent's argument"""
        self.current_round = round_num
        
        event = {
            "session_id": self.session_id,
            "event_type": "agent_argument",
            "agent": agent,
            "argument": argument,
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds()
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
        # Update agent status
        self.update_agent_status(agent, "argued", {"round": round_num})
        
    def log_judge_evaluation(self, evaluation: Dict[str, Any], round_num: int):
        """Log judge's evaluation"""
        event = {
            "session_id": self.session_id,
            "event_type": "judge_evaluation",
            "evaluation": evaluation,
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds()
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        self.update_agent_status("judge", "evaluated", {"round": round_num})
        
    def log_round_start(self, round_num: int):
        """Log round start"""
        event = {
            "session_id": self.session_id,
            "event_type": "round_start",
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds(),
            "message": f"Starting debate round {round_num}"
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
        # Reset agent statuses
        for agent in self.agent_statuses:
            self.agent_statuses[agent] = "waiting"
        
    def log_round_complete(self, round_num: int, consensus_reached: bool):
        """Log round completion"""
        event = {
            "session_id": self.session_id,
            "event_type": "round_complete",
            "round": round_num,
            "consensus_reached": consensus_reached,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds(),
            "message": f"Round {round_num} complete" + (" - Consensus reached!" if consensus_reached else "")
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
    def log_rethinking(self, reason: str):
        """Log agents rethinking"""
        event = {
            "session_id": self.session_id,
            "event_type": "rethinking",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds(),
            "message": f"Agents rethinking positions: {reason}"
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
    def log_final_verdict(self, verdict: Dict[str, Any]):
        """Log final verdict"""
        event = {
            "session_id": self.session_id,
            "event_type": "final_verdict",
            "verdict": verdict,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds(),
            "total_rounds": self.current_round,
            "message": f"Final verdict: {verdict.get('action', 'hold').upper()}"
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
    def log_timeout(self, round_num: int):
        """Log timeout event"""
        event = {
            "session_id": self.session_id,
            "event_type": "timeout",
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": self.get_elapsed_seconds(),
            "message": f"Round {round_num} timed out - agents will rethink"
        }
        
        self.events.append(event)
        stream_manager.broadcast_to_session(self.session_id, event)
        
    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get debate summary"""
        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "current_round": self.current_round,
            "elapsed_seconds": self.get_elapsed_seconds(),
            "agent_statuses": self.agent_statuses,
            "event_breakdown": self._get_event_breakdown()
        }
    
    def _get_event_breakdown(self) -> Dict[str, int]:
        """Get breakdown of event types"""
        breakdown = {}
        for event in self.events:
            event_type = event.get("event_type", "unknown")
            breakdown[event_type] = breakdown.get(event_type, 0) + 1
        return breakdown


def format_debate_for_frontend(debate_session: Any) -> Dict[str, Any]:
    """
    Format debate session data for frontend consumption
    """
    return {
        "session_id": debate_session.session_id,
        "symbol": debate_session.symbol,
        "status": debate_session.status.value,
        "total_rounds": len(debate_session.rounds),
        "current_round": debate_session.rounds[-1].round_number if debate_session.rounds else 0,
        "elapsed_time": debate_session.get_total_duration(),
        "consensus_reached": debate_session.consensus_round is not None,
        "final_verdict": debate_session.final_verdict,
        "rounds": [round.to_dict() for round in debate_session.rounds],
        "financial_context": debate_session.financial_context,
        "is_complete": debate_session.status == debate_session.status.__class__.COMPLETE
    }


# Decorator for streaming debate updates
def with_streaming_updates(func):
    """Decorator to add streaming updates to debate functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract session_id from args/kwargs
        session_id = kwargs.get('session_id') or (args[0] if args else None)
        
        if session_id and isinstance(session_id, str):
            tracker = LiveDebateTracker(session_id)
            kwargs['tracker'] = tracker
            
        return func(*args, **kwargs)
    return wrapper
