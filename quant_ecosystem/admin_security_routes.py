"""
Hardened Admin Security Routes
Implements JWT-based authentication with strict security controls for admin-level operations.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime
from typing import Dict, Any

from quant_ecosystem.admin_control import admin_control
from quant_ecosystem.enhanced_security import (
    security_manager, SecurityRole, SecurityLevel,
    require_jwt_auth, require_admin_jwt, validate_input,
    rate_limit, get_current_security_context, log_admin_action
)

admin_security_routes = Blueprint('admin_security_routes', __name__, url_prefix='/api/admin')


def _get_client_ip() -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _get_user_agent() -> str:
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'unknown')


# ==================== AUTHENTICATION ====================

@admin_security_routes.route('/auth/login', methods=['POST'])
@rate_limit(requests_per_minute=10, by_ip=True, by_user=False)
def jwt_login():
    """
    JWT-based admin login with enhanced security.
    
    Request body:
        - email: str (validated)
        - password: str (validated)
    
    Returns:
        {
            'success': bool,
            'access_token': str,
            'refresh_token': str,
            'token_type': 'Bearer',
            'expires_in': int,
            'requires_password_change': bool
        }
    """
    data = request.get_json() or {}
    
    # Input validation
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    ip_address = _get_client_ip()
    user_agent = _get_user_agent()
    
    # Validate email format
    valid_email, email_error = security_manager.validate_email(email)
    if not valid_email:
        security_manager.log_failed_login(email, ip_address, user_agent, f"Invalid email format: {email_error}")
        return jsonify({
            'success': False,
            'error': 'Invalid credentials',
            'message': 'Authentication failed'
        }), 401
    
    # Authenticate with admin_control
    result = admin_control.authenticate(
        email=email,
        password=password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not result['success']:
        # Log failed login
        security_manager.log_failed_login(email, ip_address, user_agent, result.get('message', 'Authentication failed'))
        return jsonify({
            'success': False,
            'error': 'Invalid credentials',
            'message': 'Authentication failed'
        }), 401
    
    # Generate JWT tokens
    admin_id = result.get('admin_id', email)  # Fallback if admin_id not in result
    tokens = security_manager.generate_jwt_tokens(
        admin_id=admin_id,
        email=email,
        role=SecurityRole.ADMIN,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Log successful login
    context = get_current_security_context()
    if context:
        security_manager.log_security_event(
            context, "LOGIN_SUCCESS",
            resource=request.path, method=request.method,
            success=True, details={'admin_id': admin_id}
        )
    
    return jsonify({
        'success': True,
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'token_type': tokens['token_type'],
        'expires_in': tokens['expires_in'],
        'requires_password_change': result.get('requires_password_change', False)
    })


@admin_security_routes.route('/auth/refresh', methods=['POST'])
@rate_limit(requests_per_minute=30, by_ip=True, by_user=True)
def jwt_refresh():
    """
    Refresh access token using refresh token.
    
    Request body:
        - refresh_token: str
    
    Returns:
        {
            'success': bool,
            'access_token': str,
            'refresh_token': str,
            'expires_in': int
        }
    """
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token', '')
    
    if not refresh_token:
        return jsonify({
            'success': False,
            'error': 'Refresh token required'
        }), 400
    
    # Validate and refresh
    new_tokens = security_manager.refresh_access_token(refresh_token)
    
    if not new_tokens:
        return jsonify({
            'success': False,
            'error': 'Invalid or expired refresh token'
        }), 401
    
    return jsonify({
        'success': True,
        'access_token': new_tokens['access_token'],
        'refresh_token': new_tokens['refresh_token'],
        'token_type': new_tokens['token_type'],
        'expires_in': new_tokens['expires_in']
    })


@admin_security_routes.route('/auth/logout', methods=['POST'])
@require_admin_jwt(security_level=SecurityLevel.LOW)
def jwt_logout():
    """
    Logout and revoke current token.
    """
    payload = g.jwt_payload
    jti = payload.get('jti')
    
    if jti:
        security_manager.revoke_token(jti, reason="Logout")
    
    log_admin_action("LOGOUT", security_level=SecurityLevel.LOW)
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


@admin_security_routes.route('/auth/logout-all', methods=['POST'])
@require_admin_jwt(security_level=SecurityLevel.HIGH)
def jwt_logout_all():
    """
    Logout from all devices by revoking all tokens.
    """
    payload = g.jwt_payload
    admin_id = payload['sub']
    
    security_manager.revoke_all_user_tokens(admin_id, reason="Logout from all devices")
    
    log_admin_action("LOGOUT_ALL", security_level=SecurityLevel.HIGH)
    
    return jsonify({
        'success': True,
        'message': 'Logged out from all devices'
    })


@admin_security_routes.route('/auth/verify', methods=['GET'])
@require_admin_jwt(security_level=SecurityLevel.LOW)
def jwt_verify():
    """
    Verify current JWT token and return session info.
    """
    payload = g.jwt_payload
    context = get_current_security_context()
    
    return jsonify({
        'valid': True,
        'admin_id': payload['sub'],
        'email': payload['email'],
        'role': payload['role'],
        'issued_at': payload['iat'].isoformat() if isinstance(payload['iat'], datetime) else payload['iat'],
        'expires_at': payload['exp'].isoformat() if isinstance(payload['exp'], datetime) else payload['exp'],
        'ip_address': context.ip_address if context else None
    })


# ==================== PASSWORD MANAGEMENT ====================

@admin_security_routes.route('/auth/change-password', methods=['POST'])
@require_admin_jwt(security_level=SecurityLevel.HIGH)
@validate_input({
    'old_password': {'type': str, 'required': True, 'min_length': 1},
    'new_password': {'type': str, 'required': True, 'min_length': 8}
})
def jwt_change_password():
    """
    Change admin password with validation.
    
    Request body:
        - old_password: str
        - new_password: str (min 8 chars, must include upper, lower, digit, special)
    """
    data = g.sanitized_input
    old_password = data['old_password']
    new_password = data['new_password']
    
    # Validate new password strength
    valid, error = security_manager.validate_password(new_password)
    if not valid:
        return jsonify({
            'success': False,
            'error': 'Password validation failed',
            'message': error
        }), 400
    
    # Get admin info from token
    payload = g.jwt_payload
    email = payload['email']
    
    # Change password
    result = admin_control.change_password_by_email(email, old_password, new_password)
    
    if result['success']:
        # Revoke all tokens after password change (security best practice)
        security_manager.revoke_all_user_tokens(payload['sub'], reason="Password changed")
        
        log_admin_action("PASSWORD_CHANGED", security_level=SecurityLevel.CRITICAL)
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully. Please log in again.',
            'requires_relogin': True
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Password change failed',
            'message': result.get('message', 'Unknown error')
        }), 400


# ==================== SYSTEM CONTROL ====================

@admin_security_routes.route('/system/mode', methods=['POST'])
@require_admin_jwt(security_level=SecurityLevel.CRITICAL)
@validate_input({
    'mode': {
        'type': str,
        'required': True,
        'allowed_values': ['training', 'execution', 'safe']
    },
    'reason': {'type': str, 'required': True, 'min_length': 10, 'max_length': 500}
})
def jwt_switch_mode():
    """
    Switch system mode with enhanced security logging.
    Requires detailed reason for audit trail.
    """
    data = g.sanitized_input
    mode = data['mode']
    reason = data['reason']
    
    payload = g.jwt_payload
    
    # Use existing admin_control but with enhanced logging
    result = admin_control.switch_system_mode(
        token=payload.get('jti'),  # Pass JWT for audit
        mode=mode,
        reason=reason
    )
    
    if result['success']:
        log_admin_action(
            "MODE_SWITCH",
            {'from_mode': result.get('old_mode'), 'to_mode': mode, 'reason': reason},
            SecurityLevel.CRITICAL
        )
    
    status_code = 200 if result['success'] else 403
    return jsonify(result), status_code


@admin_security_routes.route('/system/config', methods=['GET'])
@require_admin_jwt(security_level=SecurityLevel.MEDIUM)
def jwt_get_config():
    """Get system configuration"""
    config = admin_control.get_config()
    
    return jsonify({
        'success': True,
        'config': config
    })


@admin_security_routes.route('/system/config', methods=['POST'])
@require_admin_jwt(security_level=SecurityLevel.HIGH)
@validate_input({
    'updates': {'type': dict, 'required': True, 'min_length': 1}
})
def jwt_update_config():
    """
    Update system configuration with validation and logging.
    """
    data = g.sanitized_input
    updates = data['updates']
    
    payload = g.jwt_payload
    
    result = admin_control.update_config(
        token=payload.get('jti'),
        updates=updates
    )
    
    if result['success']:
        log_admin_action(
            "CONFIG_UPDATE",
            {'updated_keys': result.get('updated_keys', [])},
            SecurityLevel.HIGH
        )
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ==================== SECURITY AUDIT ====================

@admin_security_routes.route('/security/audit-log', methods=['GET'])
@require_admin_jwt(security_level=SecurityLevel.HIGH)
def jwt_get_security_audit():
    """
    Get enhanced security audit log.
    
    Query params:
        - limit: int (default: 100, max: 1000)
        - action: str (optional filter)
    """
    limit = min(request.args.get('limit', 100, type=int), 1000)
    action = request.args.get('action', None)
    
    logs = security_manager.get_security_audit_log(
        action=action,
        limit=limit
    )
    
    return jsonify({
        'success': True,
        'count': len(logs),
        'logs': logs
    })


@admin_security_routes.route('/security/sessions', methods=['GET'])
@require_admin_jwt(security_level=SecurityLevel.HIGH)
def jwt_get_active_sessions():
    """
    Get active security sessions for current admin.
    """
    payload = g.jwt_payload
    admin_id = payload['sub']
    
    # Query active sessions from database
    import sqlite3
    with sqlite3.connect(security_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, issued_at, expires_at, last_activity, 
                   ip_address, revoked
            FROM security_sessions
            WHERE admin_id = ? AND revoked = 0
            ORDER BY issued_at DESC
        ''', (admin_id,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0][:16] + '...',  # Truncated for security
                'issued_at': row[1],
                'expires_at': row[2],
                'last_activity': row[3],
                'ip_address': row[4],
                'is_current': row[0] == payload.get('jti')
            })
    
    return jsonify({
        'success': True,
        'sessions': sessions
    })


# ==================== IP BLOCKING ====================

@admin_security_routes.route('/security/block-ip', methods=['POST'])
@require_admin_jwt(security_level=SecurityLevel.CRITICAL)
@validate_input({
    'ip_address': {'type': str, 'required': True, 'pattern': r'^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F:]+)$'},
    'duration_minutes': {'type': int, 'required': True, 'min': 1, 'max': 1440},
    'reason': {'type': str, 'required': True, 'min_length': 5, 'max_length': 200}
})
def jwt_block_ip():
    """
    Block an IP address.
    Only admins can block IPs.
    """
    data = g.sanitized_input
    
    security_manager.block_ip(
        data['ip_address'],
        data['duration_minutes'],
        data['reason']
    )
    
    log_admin_action(
        "IP_BLOCKED",
        {
            'ip': data['ip_address'],
            'duration': data['duration_minutes'],
            'reason': data['reason']
        },
        SecurityLevel.CRITICAL
    )
    
    return jsonify({
        'success': True,
        'message': f"IP {data['ip_address']} blocked for {data['duration_minutes']} minutes"
    })
