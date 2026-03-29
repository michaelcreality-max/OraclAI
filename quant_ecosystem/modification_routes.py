"""
System Self-Modification API Routes
Exposes controlled self-modification capabilities via REST API
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional
import logging

from quant_ecosystem.self_modification import (
    modification_manager, ChangeType, ChangeStatus
)
from quant_ecosystem.admin_control import admin_control

log = logging.getLogger(__name__)

# Create blueprint
modification_routes = Blueprint('modification_routes', __name__, url_prefix='/api/system')


def _get_token_from_request() -> str:
    """Extract auth token from request"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:].strip()
    
    data = request.get_json() or {}
    return data.get('token', '').strip()


def _authenticate(token: str) -> bool:
    """Validate admin token"""
    if not token:
        return False
    return admin_control.validate_session(token)


def _get_admin_info(token: str) -> tuple:
    """Get admin ID and email from token"""
    session = admin_control._get_session(token)
    if session:
        return session.admin_id, session.email
    return None, None


# ==================== LIVE PARAMETERS ====================

@modification_routes.route('/parameters', methods=['GET'])
def get_parameters():
    """
    Get all live parameters
    
    Query params:
        - category: str (optional) - Filter by category
    
    Response:
        {
            "success": bool,
            "parameters": {
                "param_name": {
                    "name": str,
                    "value": any,
                    "min_value": float | null,
                    "max_value": float | null,
                    "description": str,
                    "category": str,
                    "requires_restart": bool,
                    "last_updated": str,
                    "updated_by": str,
                    "change_count": int
                }
            }
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    category = request.args.get('category')
    
    try:
        params = modification_manager.get_all_live_parameters(category)
        
        return jsonify({
            'success': True,
            'parameters': params,
            'count': len(params)
        })
        
    except Exception as e:
        log.error(f"Failed to get parameters: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@modification_routes.route('/parameters/<name>', methods=['GET'])
def get_parameter(name: str):
    """
    Get a specific live parameter
    
    Response:
        {
            "success": bool,
            "parameter": {...} | null,
            "error": str | null
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    params = modification_manager.get_all_live_parameters()
    param = params.get(name)
    
    if not param:
        return jsonify({'success': False, 'error': f'Parameter {name} not found'}), 404
    
    return jsonify({'success': True, 'parameter': param})


@modification_routes.route('/parameters/<name>/update', methods=['POST'])
def update_parameter(name: str):
    """
    Update a live parameter
    
    Request body:
        - token: str (optional, can use header)
        - value: any - New value
        - reason: str - Why this change is being made
    
    Response:
        {
            "success": bool,
            "change_id": str | null,
            "error": str | null,
            "requires_restart": bool
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    admin_id, admin_email = _get_admin_info(token)
    
    data = request.get_json() or {}
    new_value = data.get('value')
    reason = data.get('reason', '').strip()
    
    if new_value is None:
        return jsonify({'success': False, 'error': 'value is required'}), 400
    
    if not reason:
        return jsonify({'success': False, 'error': 'reason is required'}), 400
    
    try:
        result = modification_manager.update_live_parameter(
            name=name,
            new_value=new_value,
            admin_id=admin_id,
            admin_email=admin_email,
            reason=reason
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        log.error(f"Failed to update parameter {name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@modification_routes.route('/parameters/register', methods=['POST'])
def register_parameter():
    """
    Register a new live parameter
    
    Request body:
        - name: str
        - default_value: any
        - min_value: float (optional)
        - max_value: float (optional)
        - allowed_values: list (optional)
        - description: str
        - category: str
        - requires_restart: bool
    
    Response:
        {
            "success": bool,
            "error": str | null
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    data = request.get_json() or {}
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'name is required'}), 400
    
    success = modification_manager.register_live_parameter(
        name=name,
        default_value=data.get('default_value'),
        min_value=data.get('min_value'),
        max_value=data.get('max_value'),
        allowed_values=data.get('allowed_values'),
        description=data.get('description', ''),
        category=data.get('category', 'general'),
        requires_restart=data.get('requires_restart', False)
    )
    
    if success:
        # Log to audit
        admin_id, admin_email = _get_admin_info(token)
        admin_control._log_audit(
            admin_id, "PARAMETER_REGISTERED",
            f"Registered live parameter: {name}", ""
        )
        
        return jsonify({'success': True, 'message': f'Parameter {name} registered'})
    else:
        return jsonify({'success': False, 'error': f'Parameter {name} already exists'}), 409


# ==================== CODE PATCHING ====================

@modification_routes.route('/code/propose', methods=['POST'])
def propose_code_change():
    """
    Propose a code change with validation
    
    Request body:
        - file_path: str - Relative path to file
        - new_content: str - New file content
        - reason: str - Why this change is being made
    
    Response:
        {
            "success": bool,
            "change_id": str | null,
            "validation": {
                "valid": bool,
                "errors": [str],
                "warnings": [str],
                "impact_score": float,
                "safety_checks": dict
            },
            "error": str | null
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    admin_id, admin_email = _get_admin_info(token)
    
    data = request.get_json() or {}
    file_path = data.get('file_path', '').strip()
    new_content = data.get('new_content', '')
    reason = data.get('reason', '').strip()
    
    if not file_path:
        return jsonify({'success': False, 'error': 'file_path is required'}), 400
    
    if not new_content:
        return jsonify({'success': False, 'error': 'new_content is required'}), 400
    
    if not reason:
        return jsonify({'success': False, 'error': 'reason is required'}), 400
    
    try:
        result = modification_manager.propose_code_change(
            file_path=file_path,
            new_content=new_content,
            admin_id=admin_id,
            admin_email=admin_email,
            reason=reason
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        log.error(f"Failed to propose code change: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@modification_routes.route('/code/apply', methods=['POST'])
def apply_code_change():
    """
    Apply a previously proposed code change
    
    Request body:
        - change_id: str - The change to apply
    
    Response:
        {
            "success": bool,
            "backup_path": str | null,
            "error": str | null
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    data = request.get_json() or {}
    change_id = data.get('change_id', '').strip()
    
    if not change_id:
        return jsonify({'success': False, 'error': 'change_id is required'}), 400
    
    try:
        result = modification_manager.apply_code_change(change_id)
        
        if result['success']:
            # Log to audit
            admin_id, _ = _get_admin_info(token)
            admin_control._log_audit(
                admin_id, "CODE_CHANGE_APPLIED",
                f"Applied code change: {change_id}", ""
            )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        log.error(f"Failed to apply code change: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== CHANGE HISTORY & ROLLBACK ====================

@modification_routes.route('/changes', methods=['GET'])
def get_change_history():
    """
    Get system modification history
    
    Query params:
        - limit: int (default: 100)
        - type: str (config|code_patch|parameter|threshold|weight|agent_config|rule)
        - status: str (pending|validating|applied|rolled_back|failed|reverted)
    
    Response:
        {
            "success": bool,
            "changes": [{
                "change_id": str,
                "change_type": str,
                "status": str,
                "target": str,
                "reason": str,
                "admin_email": str,
                "timestamp": str,
                "impact_score": float,
                "rollback_available": bool
            }],
            "count": int
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    limit = request.args.get('limit', 100, type=int)
    change_type_str = request.args.get('type')
    status_str = request.args.get('status')
    
    change_type = None
    if change_type_str:
        try:
            change_type = ChangeType(change_type_str)
        except ValueError:
            return jsonify({'success': False, 'error': f'Invalid type: {change_type_str}'}), 400
    
    status = None
    if status_str:
        try:
            status = ChangeStatus(status_str)
        except ValueError:
            return jsonify({'success': False, 'error': f'Invalid status: {status_str}'}), 400
    
    try:
        changes = modification_manager.get_change_history(
            limit=limit,
            change_type=change_type,
            status=status
        )
        
        return jsonify({
            'success': True,
            'changes': changes,
            'count': len(changes)
        })
        
    except Exception as e:
        log.error(f"Failed to get change history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@modification_routes.route('/changes/<change_id>', methods=['GET'])
def get_change_details(change_id: str):
    """
    Get full details of a specific change
    
    Response:
        {
            "success": bool,
            "change": {
                "change_id": str,
                "change_type": str,
                "status": str,
                "target": str,
                "old_value": any,
                "new_value": any,
                "reason": str,
                "admin_email": str,
                "timestamp": str,
                "validated": bool,
                "validation_errors": [str],
                "impact_score": float,
                "logs": [{
                    "action": str,
                    "details": str,
                    "timestamp": str
                }]
            },
            "error": str | null
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        details = modification_manager.get_change_details(change_id)
        
        if not details:
            return jsonify({'success': False, 'error': 'Change not found'}), 404
        
        return jsonify({'success': True, 'change': details})
        
    except Exception as e:
        log.error(f"Failed to get change details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@modification_routes.route('/changes/<change_id>/rollback', methods=['POST'])
def rollback_change(change_id: str):
    """
    Rollback a change to its previous state
    
    Response:
        {
            "success": bool,
            "error": str | null
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        result = modification_manager.rollback_change(change_id)
        
        if result['success']:
            # Log to audit
            admin_id, _ = _get_admin_info(token)
            admin_control._log_audit(
                admin_id, "CHANGE_ROLLED_BACK",
                f"Rolled back change: {change_id}", ""
            )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        log.error(f"Failed to rollback change: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SYSTEM STATUS ====================

@modification_routes.route('/status', methods=['GET'])
def get_modification_status():
    """
    Get overall system modification status
    
    Response:
        {
            "success": bool,
            "status": {
                "total_changes": int,
                "pending_changes": int,
                "applied_changes": int,
                "rolled_back_changes": int,
                "failed_changes": int,
                "rollback_available_count": int,
                "live_parameters_count": int
            }
        }
    """
    token = _get_token_from_request()
    
    if not _authenticate(token):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        all_changes = modification_manager.get_change_history(limit=1000)
        
        # Count by status
        pending = sum(1 for c in all_changes if c['status'] == 'pending')
        applied = sum(1 for c in all_changes if c['status'] == 'applied')
        rolled_back = sum(1 for c in all_changes if c['status'] == 'rolled_back')
        failed = sum(1 for c in all_changes if c['status'] == 'failed')
        rollback_available = sum(1 for c in all_changes if c['rollback_available'])
        
        params = modification_manager.get_all_live_parameters()
        
        return jsonify({
            'success': True,
            'status': {
                'total_changes': len(all_changes),
                'pending_changes': pending,
                'applied_changes': applied,
                'rolled_back_changes': rolled_back,
                'failed_changes': failed,
                'rollback_available_count': rollback_available,
                'live_parameters_count': len(params)
            }
        })
        
    except Exception as e:
        log.error(f"Failed to get modification status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
