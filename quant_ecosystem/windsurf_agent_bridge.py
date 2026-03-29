"""
Windsurf Agent Bridge - Interface between backend and Windsurf AI agents
Provides controlled execution, safety mechanisms, and comprehensive logging
"""

from __future__ import annotations

import logging
import time
import threading
import uuid
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
import traceback

log = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    STOPPED = "stopped"


class AgentDecision(Enum):
    """Agent decision types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ANALYZE = "analyze"
    MODIFY = "modify"
    RESEARCH = "research"


@dataclass
class AgentConfig:
    """Configuration for Windsurf agent"""
    agent_id: str
    agent_type: str
    max_iterations: int = 10
    timeout_seconds: float = 120.0
    enable_loop_detection: bool = True
    loop_detection_window: int = 5
    allowed_actions: List[str] = field(default_factory=lambda: [
        "analyze", "research", "calculate", "fetch_data", "report"
    ])
    restricted_patterns: List[str] = field(default_factory=lambda: [
        "while True", "recursive_call", "infinite_loop"
    ])
    confidence_threshold: float = 0.6
    auto_approve_confidence: float = 0.85
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentConfig:
        return cls(**data)


@dataclass
class AgentRequest:
    """Request to run a Windsurf agent"""
    request_id: str
    agent_id: str
    task: str
    symbol: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5  # 1-10, lower is higher priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'agent_id': self.agent_id,
            'task': self.task,
            'symbol': self.symbol,
            'context': self.context,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority
        }


@dataclass
class AgentResponse:
    """Response from Windsurf agent execution"""
    request_id: str
    agent_id: str
    state: AgentState
    decision: AgentDecision
    confidence: float
    reasoning: str
    internal_state: Dict[str, Any]
    iterations_used: int
    execution_time: float
    timestamp: datetime
    logs: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'agent_id': self.agent_id,
            'state': self.state.value,
            'decision': self.decision.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'internal_state': self.internal_state,
            'iterations_used': self.iterations_used,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
            'logs': self.logs,
            'warnings': self.warnings,
            'errors': self.errors
        }


@dataclass
class AgentExecutionRecord:
    """Record of an agent execution for history/auditing"""
    record_id: str
    request: AgentRequest
    response: Optional[AgentResponse]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'request': self.request.to_dict(),
            'response': self.response.to_dict() if self.response else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time else None
        }


class LoopDetector:
    """Detects infinite loops in agent execution"""
    
    def __init__(self, window_size: int = 5, similarity_threshold: float = 0.9):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.state_history: deque = deque(maxlen=window_size)
        
    def record_state(self, state: Dict[str, Any]) -> bool:
        """
        Record state and check for loop
        Returns True if loop detected
        """
        # Create a hash of the state
        state_hash = self._hash_state(state)
        
        # Check for repetition
        if len(self.state_history) >= self.window_size:
            # Check if current state matches any in history
            for historical_hash in self.state_history:
                if self._calculate_similarity(state_hash, historical_hash) > self.similarity_threshold:
                    return True
        
        self.state_history.append(state_hash)
        return False
    
    def _hash_state(self, state: Dict[str, Any]) -> str:
        """Create deterministic hash of state"""
        # Extract key fields that indicate state
        key_fields = {
            'task': state.get('task', ''),
            'iteration': state.get('iteration', 0),
            'action': state.get('current_action', ''),
            'decision': str(state.get('decision', '')),
            'confidence': round(state.get('confidence', 0.0), 2)
        }
        return json.dumps(key_fields, sort_keys=True)
    
    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two state hashes"""
        if hash1 == hash2:
            return 1.0
        
        # Parse and compare
        try:
            dict1 = json.loads(hash1)
            dict2 = json.loads(hash2)
            
            matches = sum(1 for k in dict1 if dict1[k] == dict2.get(k))
            return matches / len(dict1)
        except:
            return 0.0
    
    def reset(self):
        """Clear history"""
        self.state_history.clear()


class AgentSandbox:
    """Sandbox for safe agent execution"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.loop_detector = LoopDetector(
            window_size=config.loop_detection_window
        ) if config.enable_loop_detection else None
        self.iteration_count = 0
        self.start_time: Optional[float] = None
        self.logs: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        
    def execute(self, request: AgentRequest, 
                agent_callable: Callable) -> AgentResponse:
        """
        Execute agent with safety controls
        """
        self.start_time = time.time()
        self.iteration_count = 0
        request_id = request.request_id
        agent_id = request.agent_id
        
        self._log(f"Starting agent execution: {agent_id} for task: {request.task}")
        
        try:
            # Check for restricted patterns in task
            if self._contains_restricted_patterns(request.task):
                return self._create_error_response(
                    request_id, agent_id,
                    "Task contains restricted patterns"
                )
            
            # Execute with timeout control
            result = self._execute_with_timeout(request, agent_callable)
            
            execution_time = time.time() - self.start_time
            self._log(f"Agent execution completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Agent execution error: {str(e)}"
            log.error(error_msg)
            log.error(traceback.format_exc())
            self.errors.append(error_msg)
            
            return self._create_error_response(
                request_id, agent_id,
                error_msg
            )
    
    def _execute_with_timeout(self, request: AgentRequest,
                             agent_callable: Callable) -> AgentResponse:
        """Execute agent with timeout protection"""
        request_id = request.request_id
        agent_id = request.agent_id
        
        # Create result container
        result_container = {'response': None, 'error': None}
        
        def execute_wrapper():
            try:
                # Call the actual agent
                raw_response = agent_callable(
                    task=request.task,
                    symbol=request.symbol,
                    context=request.context,
                    parameters=request.parameters,
                    iteration_callback=self._iteration_callback
                )
                
                # Validate and process response
                result_container['response'] = self._process_agent_response(
                    request_id, agent_id, raw_response
                )
            except Exception as e:
                result_container['error'] = str(e)
        
        # Run in thread with timeout
        thread = threading.Thread(target=execute_wrapper)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.config.timeout_seconds)
        
        if thread.is_alive():
            # Timeout occurred
            self.warnings.append(f"Agent execution timed out after {self.config.timeout_seconds}s")
            return AgentResponse(
                request_id=request_id,
                agent_id=agent_id,
                state=AgentState.TIMEOUT,
                decision=AgentDecision.HOLD,
                confidence=0.0,
                reasoning="Agent execution timed out",
                internal_state={'timeout_after': self.config.timeout_seconds},
                iterations_used=self.iteration_count,
                execution_time=self.config.timeout_seconds,
                timestamp=datetime.now(),
                logs=self.logs,
                warnings=self.warnings,
                errors=self.errors
            )
        
        if result_container['error']:
            return self._create_error_response(
                request_id, agent_id,
                result_container['error']
            )
        
        return result_container['response']
    
    def _iteration_callback(self, iteration: int, state: Dict[str, Any]) -> bool:
        """
        Called on each agent iteration
        Returns False to stop execution, True to continue
        """
        self.iteration_count = iteration
        
        # Check iteration limit
        if iteration >= self.config.max_iterations:
            self.warnings.append(f"Max iterations ({self.config.max_iterations}) reached")
            return False
        
        # Check for loops
        if self.loop_detector:
            if self.loop_detector.record_state(state):
                self.warnings.append("Loop detected - stopping execution")
                return False
        
        self._log(f"Iteration {iteration}: {state.get('current_action', 'processing')}")
        return True
    
    def _process_agent_response(self, request_id: str, agent_id: str,
                               raw_response: Dict[str, Any]) -> AgentResponse:
        """Process and validate raw agent response"""
        
        execution_time = time.time() - self.start_time if self.start_time else 0
        
        # Extract decision
        decision_str = raw_response.get('decision', 'hold').lower()
        try:
            decision = AgentDecision(decision_str)
        except ValueError:
            decision = AgentDecision.HOLD
        
        # Extract confidence
        confidence = float(raw_response.get('confidence', 0.5))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        # Check confidence threshold
        if confidence < self.config.confidence_threshold:
            self.warnings.append(
                f"Confidence {confidence:.2f} below threshold {self.config.confidence_threshold}"
            )
        
        return AgentResponse(
            request_id=request_id,
            agent_id=agent_id,
            state=AgentState.COMPLETED,
            decision=decision,
            confidence=confidence,
            reasoning=raw_response.get('reasoning', 'No reasoning provided'),
            internal_state=raw_response.get('internal_state', {}),
            iterations_used=self.iteration_count,
            execution_time=execution_time,
            timestamp=datetime.now(),
            logs=self.logs,
            warnings=self.warnings,
            errors=self.errors
        )
    
    def _contains_restricted_patterns(self, text: str) -> bool:
        """Check for restricted/dangerous patterns"""
        text_lower = text.lower()
        for pattern in self.config.restricted_patterns:
            if pattern.lower() in text_lower:
                self.errors.append(f"Restricted pattern detected: {pattern}")
                return True
        return False
    
    def _create_error_response(self, request_id: str, agent_id: str,
                              error_message: str) -> AgentResponse:
        """Create error response"""
        execution_time = time.time() - self.start_time if self.start_time else 0
        self.errors.append(error_message)
        
        return AgentResponse(
            request_id=request_id,
            agent_id=agent_id,
            state=AgentState.ERROR,
            decision=AgentDecision.HOLD,
            confidence=0.0,
            reasoning=f"Error: {error_message}",
            internal_state={'error': error_message},
            iterations_used=self.iteration_count,
            execution_time=execution_time,
            timestamp=datetime.now(),
            logs=self.logs,
            warnings=self.warnings,
            errors=self.errors
        )
    
    def _log(self, message: str):
        """Add log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        log.info(f"[Agent {self.config.agent_id}] {message}")


class WindsurfAgentBridge:
    """
    Bridge for integrating Windsurf AI agents into the backend
    Manages agent lifecycle, execution, and safety
    """
    
    def __init__(self):
        self.configs: Dict[str, AgentConfig] = {}
        self.active_executions: Dict[str, AgentExecutionRecord] = {}
        self.execution_history: deque = deque(maxlen=1000)
        self.agent_registry: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        
        # Default configurations for built-in agents
        self._initialize_default_configs()
        
        log.info("WindsurfAgentBridge initialized")
    
    def _initialize_default_configs(self):
        """Initialize default agent configurations"""
        default_agents = [
            AgentConfig(
                agent_id="windsurf_analyst",
                agent_type="analysis",
                max_iterations=15,
                timeout_seconds=180.0,
                confidence_threshold=0.65
            ),
            AgentConfig(
                agent_id="windsurf_researcher",
                agent_type="research",
                max_iterations=20,
                timeout_seconds=300.0,
                confidence_threshold=0.6
            ),
            AgentConfig(
                agent_id="windsurf_trader",
                agent_type="trading",
                max_iterations=10,
                timeout_seconds=120.0,
                confidence_threshold=0.75,
                auto_approve_confidence=0.90
            ),
            AgentConfig(
                agent_id="windsurf_risk_manager",
                agent_type="risk",
                max_iterations=12,
                timeout_seconds=150.0,
                confidence_threshold=0.70
            )
        ]
        
        for config in default_agents:
            self.configs[config.agent_id] = config
    
    def register_agent(self, agent_id: str, agent_callable: Callable) -> bool:
        """
        Register an agent implementation
        
        Args:
            agent_id: Unique identifier for the agent
            agent_callable: Function that executes agent logic
                Signature: (task, symbol, context, parameters, iteration_callback) -> dict
        
        Returns:
            True if registered successfully
        """
        with self._lock:
            if agent_id not in self.configs:
                log.error(f"Cannot register unknown agent: {agent_id}")
                return False
            
            self.agent_registry[agent_id] = agent_callable
            log.info(f"Registered agent: {agent_id}")
            return True
    
    def run_agent(self, request: AgentRequest) -> AgentResponse:
        """
        Execute an agent with full safety controls
        
        Args:
            request: Agent execution request
            
        Returns:
            AgentResponse with results
        """
        agent_id = request.agent_id
        
        # Validate agent exists
        if agent_id not in self.configs:
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent_id,
                state=AgentState.ERROR,
                decision=AgentDecision.HOLD,
                confidence=0.0,
                reasoning=f"Unknown agent: {agent_id}",
                internal_state={},
                iterations_used=0,
                execution_time=0,
                timestamp=datetime.now(),
                errors=[f"Agent {agent_id} not configured"]
            )
        
        # Check if agent is registered
        if agent_id not in self.agent_registry:
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent_id,
                state=AgentState.ERROR,
                decision=AgentDecision.HOLD,
                confidence=0.0,
                reasoning=f"Agent {agent_id} not registered",
                internal_state={},
                iterations_used=0,
                execution_time=0,
                timestamp=datetime.now(),
                errors=[f"Agent {agent_id} implementation not registered"]
            )
        
        # Get config and create sandbox
        config = self.configs[agent_id]
        sandbox = AgentSandbox(config)
        
        # Create execution record
        record = AgentExecutionRecord(
            record_id=str(uuid.uuid4()),
            request=request,
            response=None,
            start_time=datetime.now(),
            status="running"
        )
        
        with self._lock:
            self.active_executions[request.request_id] = record
        
        # Execute
        try:
            agent_callable = self.agent_registry[agent_id]
            response = sandbox.execute(request, agent_callable)
            
            # Update record
            record.response = response
            record.end_time = datetime.now()
            record.status = response.state.value
            
            # Move to history
            with self._lock:
                if request.request_id in self.active_executions:
                    del self.active_executions[request.request_id]
                self.execution_history.append(record)
            
            return response
            
        except Exception as e:
            error_msg = f"Bridge execution error: {str(e)}"
            log.error(error_msg)
            
            error_response = AgentResponse(
                request_id=request.request_id,
                agent_id=agent_id,
                state=AgentState.ERROR,
                decision=AgentDecision.HOLD,
                confidence=0.0,
                reasoning=error_msg,
                internal_state={'exception': traceback.format_exc()},
                iterations_used=0,
                execution_time=0,
                timestamp=datetime.now(),
                errors=[error_msg]
            )
            
            record.response = error_response
            record.end_time = datetime.now()
            record.status = "error"
            
            with self._lock:
                if request.request_id in self.active_executions:
                    del self.active_executions[request.request_id]
                self.execution_history.append(record)
            
            return error_response
    
    def update_config(self, agent_id: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update agent configuration
        
        Args:
            agent_id: Agent identifier
            config_updates: Dict of configuration changes
            
        Returns:
            True if updated successfully
        """
        with self._lock:
            if agent_id not in self.configs:
                log.error(f"Cannot update unknown agent config: {agent_id}")
                return False
            
            config = self.configs[agent_id]
            
            # Update allowed fields
            allowed_fields = [
                'max_iterations', 'timeout_seconds', 'enable_loop_detection',
                'loop_detection_window', 'confidence_threshold',
                'auto_approve_confidence', 'allowed_actions', 'restricted_patterns'
            ]
            
            for field_name, value in config_updates.items():
                if field_name in allowed_fields and hasattr(config, field_name):
                    setattr(config, field_name, value)
                    log.info(f"Updated {agent_id}.{field_name} = {value}")
            
            return True
    
    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of agents
        
        Args:
            agent_id: Optional specific agent, or None for all
            
        Returns:
            Status information
        """
        with self._lock:
            if agent_id:
                if agent_id not in self.configs:
                    return {'error': f'Unknown agent: {agent_id}'}
                
                config = self.configs[agent_id]
                is_registered = agent_id in self.agent_registry
                
                # Find active executions for this agent
                active_count = sum(
                    1 for r in self.active_executions.values()
                    if r.request.agent_id == agent_id
                )
                
                # Recent history for this agent
                recent_history = [
                    r.to_dict() for r in self.execution_history
                    if r.request.agent_id == agent_id
                ][-50:]  # Last 50
                
                return {
                    'agent_id': agent_id,
                    'configured': True,
                    'registered': is_registered,
                    'active_executions': active_count,
                    'config': config.to_dict(),
                    'recent_history': recent_history,
                    'total_executions': len(recent_history)
                }
            else:
                # Return status for all agents
                return {
                    'agents': [
                        {
                            'agent_id': aid,
                            'agent_type': config.agent_type,
                            'registered': aid in self.agent_registry,
                            'active_executions': sum(
                                1 for r in self.active_executions.values()
                                if r.request.agent_id == aid
                            )
                        }
                        for aid, config in self.configs.items()
                    ],
                    'total_active': len(self.active_executions),
                    'total_history': len(self.execution_history)
                }
    
    def get_execution_history(self, 
                             agent_id: Optional[str] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Args:
            agent_id: Filter by agent (optional)
            limit: Maximum records to return
            
        Returns:
            List of execution records
        """
        with self._lock:
            history = list(self.execution_history)
            
            if agent_id:
                history = [r for r in history if r.request.agent_id == agent_id]
            
            return [r.to_dict() for r in history[-limit:]]
    
    def stop_execution(self, request_id: str) -> bool:
        """
        Stop a running agent execution
        
        Args:
            request_id: Execution request ID
            
        Returns:
            True if stopped
        """
        with self._lock:
            if request_id not in self.active_executions:
                return False
            
            record = self.active_executions[request_id]
            record.status = "stopped"
            record.end_time = datetime.now()
            
            # Create stopped response
            record.response = AgentResponse(
                request_id=request_id,
                agent_id=record.request.agent_id,
                state=AgentState.STOPPED,
                decision=AgentDecision.HOLD,
                confidence=0.0,
                reasoning="Execution stopped by user",
                internal_state={},
                iterations_used=0,
                execution_time=0,
                timestamp=datetime.now()
            )
            
            del self.active_executions[request_id]
            self.execution_history.append(record)
            
            log.info(f"Stopped execution: {request_id}")
            return True
    
    def create_request(self, agent_id: str, task: str,
                      symbol: Optional[str] = None,
                      context: Optional[Dict] = None,
                      parameters: Optional[Dict] = None,
                      priority: int = 5) -> AgentRequest:
        """Helper to create a properly formatted request"""
        return AgentRequest(
            request_id=str(uuid.uuid4()),
            agent_id=agent_id,
            task=task,
            symbol=symbol,
            context=context or {},
            parameters=parameters or {},
            timestamp=datetime.now(),
            priority=priority
        )


# Global instance
agent_bridge = WindsurfAgentBridge()
