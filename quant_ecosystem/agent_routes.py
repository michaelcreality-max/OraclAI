"""
Windsurf Agent API Routes
Exposes agent control via REST API endpoints
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from quant_ecosystem.windsurf_agent_bridge import (
    agent_bridge, AgentRequest, AgentConfig
)
from quant_ecosystem.admin_control import admin_control

log = logging.getLogger(__name__)

# Create blueprint
agent_routes = Blueprint('agent_routes', __name__, url_prefix='/api/agents')


def _get_token_from_request() -> str:
    """Extract auth token from request"""
    # Check header first
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:].strip()
    
    # Check JSON body
    data = request.get_json() or {}
    return data.get('token', '').strip()


def _authenticate(token: str) -> bool:
    """Validate admin token"""
    if not token:
        return False
    return admin_control.validate_session(token)


@agent_routes.route('/run', methods=['POST'])
def run_agent():
    """
    Execute a Windsurf agent
    
    Request body:
        - token: str (or Authorization header)
        - agent_id: str (required) - Agent to run
        - task: str (required) - Task description
        - symbol: str (optional) - Stock symbol for trading tasks
        - context: dict (optional) - Additional context
        - parameters: dict (optional) - Execution parameters
        - priority: int (optional) - Priority 1-10, default 5
    
    Response:
        {
            "success": bool,
            "request_id": str,
            "agent_id": str,
            "state": str,
            "decision": str,
            "confidence": float,
            "reasoning": str,
            "internal_state": dict,
            "iterations_used": int,
            "execution_time": float,
            "logs": [str],
            "warnings": [str],
            "errors": [str],
            "timestamp": str
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired authentication token'
        }), 401
    
    data = request.get_json() or {}
    
    # Validate required fields
    agent_id = data.get('agent_id', '').strip()
    task = data.get('task', '').strip()
    
    if not agent_id:
        return jsonify({
            'success': False,
            'error': 'agent_id is required'
        }), 400
    
    if not task:
        return jsonify({
            'success': False,
            'error': 'task is required'
        }), 400
    
    # Check agent exists
    status = agent_bridge.get_agent_status(agent_id)
    if 'error' in status:
        return jsonify({
            'success': False,
            'error': status['error']
        }), 404
    
    if not status.get('registered', False):
        return jsonify({
            'success': False,
            'error': f'Agent {agent_id} is not registered. Call register endpoint first.'
        }), 400
    
    # Create request
    try:
        agent_request = agent_bridge.create_request(
            agent_id=agent_id,
            task=task,
            symbol=data.get('symbol'),
            context=data.get('context', {}),
            parameters=data.get('parameters', {}),
            priority=data.get('priority', 5)
        )
    except Exception as e:
        log.error(f"Failed to create agent request: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to create request: {str(e)}'
        }), 500
    
    # Execute agent
    try:
        response = agent_bridge.run_agent(agent_request)
        
        # Log the execution
        log.info(f"Agent {agent_id} executed: {response.state.value}, "
                f"decision={response.decision.value}, confidence={response.confidence:.2f}")
        
        # Audit log
        admin_control._log_audit(
            admin_id=admin_control._get_session(token).admin_id if admin_control._get_session(token) else 'unknown',
            action="AGENT_RUN",
            details=f"Agent: {agent_id}, Task: {task[:50]}, Result: {response.state.value}"
        )
        
        return jsonify({
            'success': True,
            **response.to_dict()
        })
        
    except Exception as e:
        log.error(f"Agent execution failed: {e}")
        return jsonify({
            'success': False,
            'error': f'Agent execution failed: {str(e)}'
        }), 500


@agent_routes.route('/config/update', methods=['POST'])
def update_config():
    """
    Update agent configuration
    
    Request body:
        - token: str (or Authorization header)
        - agent_id: str (required) - Agent to configure
        - config: dict (required) - Configuration updates
            - max_iterations: int
            - timeout_seconds: float
            - enable_loop_detection: bool
            - loop_detection_window: int
            - confidence_threshold: float
            - auto_approve_confidence: float
            - allowed_actions: List[str]
            - restricted_patterns: List[str]
    
    Response:
        {
            "success": bool,
            "message": str,
            "agent_id": str,
            "updated_config": dict
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired authentication token'
        }), 401
    
    data = request.get_json() or {}
    
    agent_id = data.get('agent_id', '').strip()
    config_updates = data.get('config', {})
    
    if not agent_id:
        return jsonify({
            'success': False,
            'error': 'agent_id is required'
        }), 400
    
    if not config_updates:
        return jsonify({
            'success': False,
            'error': 'config is required'
        }), 400
    
    # Validate config fields
    allowed_fields = {
        'max_iterations', 'timeout_seconds', 'enable_loop_detection',
        'loop_detection_window', 'confidence_threshold', 'auto_approve_confidence',
        'allowed_actions', 'restricted_patterns'
    }
    
    invalid_fields = set(config_updates.keys()) - allowed_fields
    if invalid_fields:
        return jsonify({
            'success': False,
            'error': f'Invalid config fields: {invalid_fields}. Allowed: {allowed_fields}'
        }), 400
    
    # Update config
    success = agent_bridge.update_config(agent_id, config_updates)
    
    if not success:
        return jsonify({
            'success': False,
            'error': f'Failed to update config for agent {agent_id}'
        }), 404
    
    # Get updated status
    status = agent_bridge.get_agent_status(agent_id)
    
    # Audit log
    admin_control._log_audit(
        admin_id=admin_control._get_session(token).admin_id if admin_control._get_session(token) else 'unknown',
        action="AGENT_CONFIG_UPDATE",
        details=f"Agent: {agent_id}, Updates: {config_updates}"
    )
    
    return jsonify({
        'success': True,
        'message': f'Configuration updated for agent {agent_id}',
        'agent_id': agent_id,
        'updated_config': status.get('config', {})
    })


@agent_routes.route('/status', methods=['GET'])
def get_status():
    """
    Get agent status
    
    Query params:
        - agent_id: str (optional) - Specific agent, or all if omitted
    
    Response:
        {
            "success": bool,
            "agents": [{
                "agent_id": str,
                "agent_type": str,
                "registered": bool,
                "active_executions": int
            }],
            "total_active": int,
            "total_history": int
        }
        
        Or for specific agent:
        {
            "success": bool,
            "agent_id": str,
            "configured": bool,
            "registered": bool,
            "active_executions": int,
            "config": {...},
            "recent_history": [...],
            "total_executions": int
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired authentication token'
        }), 401
    
    agent_id = request.args.get('agent_id', '').strip() or None
    
    try:
        status = agent_bridge.get_agent_status(agent_id)
        
        if 'error' in status:
            return jsonify({
                'success': False,
                'error': status['error']
            }), 404
        
        return jsonify({
            'success': True,
            **status
        })
        
    except Exception as e:
        log.error(f"Failed to get agent status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}'
        }), 500


@agent_routes.route('/history', methods=['GET'])
def get_history():
    """
    Get execution history
    
    Query params:
        - agent_id: str (optional) - Filter by agent
        - limit: int (default: 100) - Max records
    
    Response:
        {
            "success": bool,
            "history": [{
                "record_id": str,
                "request": {...},
                "response": {...},
                "start_time": str,
                "end_time": str,
                "status": str,
                "duration": float
            }],
            "count": int
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired authentication token'
        }), 401
    
    agent_id = request.args.get('agent_id', '').strip() or None
    limit = request.args.get('limit', 100, type=int)
    limit = min(limit, 1000)  # Cap at 1000
    
    try:
        history = agent_bridge.get_execution_history(agent_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        log.error(f"Failed to get execution history: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get history: {str(e)}'
        }), 500


@agent_routes.route('/stop', methods=['POST'])
def stop_execution():
    """
    Stop a running agent execution
    
    Request body:
        - token: str (or Authorization header)
        - request_id: str (required) - Execution to stop
    
    Response:
        {
            "success": bool,
            "message": str,
            "request_id": str
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired authentication token'
        }), 401
    
    data = request.get_json() or {}
    request_id = data.get('request_id', '').strip()
    
    if not request_id:
        return jsonify({
            'success': False,
            'error': 'request_id is required'
        }), 400
    
    success = agent_bridge.stop_execution(request_id)
    
    if not success:
        return jsonify({
            'success': False,
            'error': f'Execution {request_id} not found or already completed'
        }), 404
    
    # Audit log
    admin_control._log_audit(
        admin_id=admin_control._get_session(token).admin_id if admin_control._get_session(token) else 'unknown',
        action="AGENT_STOP",
        details=f"Stopped execution: {request_id}"
    )
    
    return jsonify({
        'success': True,
        'message': f'Execution {request_id} stopped',
        'request_id': request_id
    })


@agent_routes.route('/list', methods=['GET'])
def list_agents():
    """
    List all available agents
    
    Response:
        {
            "success": bool,
            "agents": [{
                "agent_id": str,
                "agent_type": str,
                "description": str,
                "config": {...}
            }]
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({
            'success': False,
            'error': 'Invalid or expired authentication token'
        }), 401
    
    # Get all agent configs
    agents = []
    for agent_id, config in agent_bridge.configs.items():
        agents.append({
            'agent_id': agent_id,
            'agent_type': config.agent_type,
            'description': _get_agent_description(config.agent_type),
            'registered': agent_id in agent_bridge.agent_registry,
            'config': config.to_dict()
        })
    
    return jsonify({
        'success': True,
        'agents': agents,
        'count': len(agents)
    })


def _get_agent_description(agent_type: str) -> str:
    """Get human-readable description for agent type"""
    descriptions = {
        'analysis': 'Performs deep market analysis and generates insights',
        'research': 'Conducts comprehensive research on stocks and markets',
        'trading': 'Makes trading decisions with high confidence threshold',
        'risk': 'Assesses portfolio and position risk levels'
    }
    return descriptions.get(agent_type, 'Windsurf AI agent')
