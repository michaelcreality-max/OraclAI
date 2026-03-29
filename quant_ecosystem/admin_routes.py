"""
Admin Control API Routes
Full admin endpoints for system control, monitoring, and configuration.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime
from typing import Dict, Any

from quant_ecosystem.admin_control import admin_control
from quant_ecosystem.api_key_manager import require_admin, Role

admin_routes = Blueprint('admin_routes', __name__, url_prefix='/api/admin')


def _get_client_ip() -> str:
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _get_user_agent() -> str:
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'unknown')


# ==================== AUTHENTICATION ====================

@admin_routes.route('/login', methods=['POST'])
def admin_login():
    """
    Admin login endpoint.
    
    Request body:
        - email: str
        - password: str
    
    Returns:
        {
            'success': bool,
            'token': str | None,
            'requires_password_change': bool,
            'message': str
        }
    """
    data = request.get_json() or {}
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400
    
    result = admin_control.authenticate(
        email=email,
        password=password,
        ip_address=_get_client_ip(),
        user_agent=_get_user_agent()
    )
    
    status_code = 200 if result['success'] else 401
    return jsonify(result), status_code


@admin_routes.route('/change-password', methods=['POST'])
def admin_change_password():
    """
    Change admin password.
    Requires valid session token.
    
    Request body:
        - token: str
        - old_password: str
        - new_password: str
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not all([token, old_password, new_password]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    
    result = admin_control.change_password(token, old_password, new_password)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@admin_routes.route('/logout', methods=['POST'])
def admin_logout():
    """
    Logout admin and invalidate session.
    
    Request body:
        - token: str
    """
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Token required'}), 400
    
    success = admin_control.logout(token)
    
    return jsonify({'success': success, 'message': 'Logged out' if success else 'Invalid token'})


@admin_routes.route('/session', methods=['GET'])
def admin_session_info():
    """
    Get current session information.
    
    Query params:
        - token: str
    """
    token = request.args.get('token', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Token required'}), 400
    
    info = admin_control.get_session_info(token)
    
    if info:
        return jsonify({'success': True, 'session': info})
    else:
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401


# ==================== SYSTEM STATE & CONFIG ====================

@admin_routes.route('/system/state', methods=['GET'])
def get_system_state():
    """
    Get complete system state including mode, safety status, agents, config.
    Requires valid admin session.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    state = admin_control.get_system_state()
    
    return jsonify({
        'success': True,
        'systemState': state
    })


@admin_routes.route('/config', methods=['GET'])
def get_config():
    """
    Get current system configuration.
    Requires valid admin session.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    config = admin_control.get_config()
    
    return jsonify({
        'success': True,
        'config': config
    })


@admin_routes.route('/config/update', methods=['POST'])
def update_config():
    """
    Update system configuration.
    Validates all inputs before applying.
    
    Request body:
        - token: str (or Authorization header)
        - updates: dict {key: value}
    
    Returns:
        {
            'success': bool,
            'message': str,
            'errors': list (if validation failed),
            'updated_keys': list,
            'config': dict
        }
    """
    data = request.get_json() or {}
    
    # Get token from body or header
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    updates = data.get('updates', {})
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    if not updates:
        return jsonify({'success': False, 'message': 'No updates provided'}), 400
    
    result = admin_control.update_config(token, updates)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== SYSTEM CONTROL ====================

@admin_routes.route('/mode/switch', methods=['POST'])
def switch_mode():
    """
    Switch system mode (training/execution/safe).
    
    Request body:
        - token: str (or Authorization header)
        - mode: str ('training', 'execution', 'safe')
        - reason: str (optional)
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    mode = data.get('mode', '').lower().strip()
    reason = data.get('reason', '')
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    if not mode:
        return jsonify({'success': False, 'message': 'Mode required (training/execution/safe)'}), 400
    
    result = admin_control.switch_system_mode(token, mode, reason)
    
    status_code = 200 if result['success'] else 403
    return jsonify(result), status_code


@admin_routes.route('/agents/<agent_id>/enable', methods=['POST'])
def enable_agent(agent_id: str):
    """
    Enable an agent.
    
    Request body:
        - token: str (or Authorization header)
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    result = admin_control.set_agent_enabled(token, agent_id, True)
    
    return jsonify(result)


@admin_routes.route('/agents/<agent_id>/disable', methods=['POST'])
def disable_agent(agent_id: str):
    """
    Disable an agent.
    
    Request body:
        - token: str (or Authorization header)
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    result = admin_control.set_agent_enabled(token, agent_id, False)
    
    return jsonify(result)


@admin_routes.route('/agents', methods=['GET'])
def get_agents():
    """
    Get status of all agents.
    Requires valid admin session.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    agents = admin_control.get_agent_status()
    
    return jsonify({
        'success': True,
        'agents': agents
    })


# ==================== SYSTEM MONITORING ====================

@admin_routes.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get system metrics history.
    
    Query params:
        - hours: int (default: 24)
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    hours = request.args.get('hours', 24, type=int)
    
    metrics = admin_control.get_system_metrics(hours)
    
    return jsonify({
        'success': True,
        'hours': hours,
        'count': len(metrics),
        'metrics': metrics
    })


@admin_routes.route('/metrics/record', methods=['POST'])
def record_metrics():
    """
    Record current system metrics.
    Used by monitoring systems.
    
    Request body:
        - token: str (or Authorization header)
        - metrics: dict
            - cpu_percent: float
            - memory_percent: float
            - active_debates: int
            - active_sessions: int
            - avg_response_time: float
            - error_rate: float
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    metrics = data.get('metrics', {})
    
    admin_control.record_system_metrics(metrics)
    
    return jsonify({'success': True, 'message': 'Metrics recorded'})


@admin_routes.route('/audit-log', methods=['GET'])
def get_audit_log():
    """
    Get system audit log.
    
    Query params:
        - limit: int (default: 100)
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    limit = request.args.get('limit', 100, type=int)
    
    result = admin_control.get_audit_log(token, limit)
    
    return jsonify(result)


# ==================== UTILITY ENDPOINTS ====================

@admin_routes.route('/verify', methods=['GET'])
def verify_admin():
    """
    Verify if admin session is valid.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not token:
        return jsonify({'valid': False, 'message': 'No token provided'}), 401
    
    valid = admin_control.validate_session(token)
    session_info = admin_control.get_session_info(token) if valid else None
    
    return jsonify({
        'valid': valid,
        'requires_password_change': session_info.get('requires_password_change', False) if session_info else False,
        'email': session_info.get('email') if session_info else None
    })


@admin_routes.route('/default-admin', methods=['GET'])
def get_default_admin_info():
    """
    Get default admin email (for development only).
    Does not expose password.
    """
    return jsonify({
        'email': admin_control.DEFAULT_ADMIN_EMAIL,
        'message': 'Use this email for initial login. Password change required on first login.'
    })


# ==================== FILE MANAGEMENT ====================

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@admin_routes.route('/files/list', methods=['GET'])
def list_files():
    """
    List files in a directory.
    
    Query params:
        - path: str (relative path, default: '.')
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    rel_path = request.args.get('path', '.')
    # Security: prevent directory traversal
    rel_path = os.path.normpath(rel_path).lstrip('/')
    full_path = os.path.join(BASE_DIR, rel_path)
    
    # Ensure path is within BASE_DIR
    if not full_path.startswith(BASE_DIR):
        return jsonify({'success': False, 'message': 'Invalid path'}), 400
    
    if not os.path.exists(full_path):
        return jsonify({'success': False, 'message': 'Path not found'}), 404
    
    files = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            files.append({
                'name': item,
                'path': os.path.join(rel_path, item),
                'is_dir': os.path.isdir(item_path),
                'size': os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                'modified': os.path.getmtime(item_path)
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': True, 'path': rel_path, 'files': files})


@admin_routes.route('/files/read', methods=['GET'])
def read_file():
    """
    Read file content.
    
    Query params:
        - path: str (required)
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    rel_path = request.args.get('path', '')
    if not rel_path:
        return jsonify({'success': False, 'message': 'Path required'}), 400
    
    # Security: prevent directory traversal
    rel_path = os.path.normpath(rel_path).lstrip('/')
    full_path = os.path.join(BASE_DIR, rel_path)
    
    if not full_path.startswith(BASE_DIR):
        return jsonify({'success': False, 'message': 'Invalid path'}), 400
    
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'success': True, 'path': rel_path, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_routes.route('/files/write', methods=['POST'])
def write_file():
    """
    Write content to file.
    
    Request body:
        - path: str
        - content: str
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    rel_path = data.get('path', '')
    content = data.get('content', '')
    
    if not rel_path:
        return jsonify({'success': False, 'message': 'Path required'}), 400
    
    # Security: prevent directory traversal
    rel_path = os.path.normpath(rel_path).lstrip('/')
    full_path = os.path.join(BASE_DIR, rel_path)
    
    if not full_path.startswith(BASE_DIR):
        return jsonify({'success': False, 'message': 'Invalid path'}), 400
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True, 'message': 'File saved', 'path': rel_path})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== AGENT TOGGLE ====================

@admin_routes.route('/agent/toggle', methods=['POST'])
def toggle_agent_endpoint():
    """
    Enable or disable an agent.
    
    Request body:
        - agent_id: str
        - enabled: bool
    """
    data = request.get_json() or {}
    
    token = data.get('token', '').strip()
    if not token:
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    agent_id = data.get('agent_id', '').strip()
    enabled = data.get('enabled', True)
    
    if not token:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    if not agent_id:
        return jsonify({'success': False, 'message': 'agent_id required'}), 400
    
    result = admin_control.set_agent_enabled(token, agent_id, enabled)
    return jsonify(result)


# ==================== LOGS ====================

@admin_routes.route('/logs/recent', methods=['GET'])
def get_recent_logs():
    """
    Get recent system logs.
    
    Query params:
        - limit: int (default: 50, max: 500)
        - level: str (optional filter: INFO, WARNING, ERROR)
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not admin_control.validate_session(token):
        return jsonify({'success': False, 'message': 'Invalid or expired session'}), 401
    
    limit = min(request.args.get('limit', 50, type=int), 500)
    level = request.args.get('level', None)
    
    # Get from audit log as system logs
    result = admin_control.get_audit_log(token, limit)
    logs = result.get('logs', [])
    
    # Convert to standard log format
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            'timestamp': log.get('timestamp', ''),
            'level': 'INFO',  # Default level
            'message': f"{log.get('action', 'UNKNOWN')}: {log.get('details', '')}"
        })
    
    return jsonify({
        'success': True,
        'count': len(formatted_logs),
        'logs': formatted_logs
    })
