"""
API Key Management Routes
Provides endpoints for creating, listing, and managing API keys.
"""

from flask import Blueprint, jsonify, request
from functools import wraps

from quant_ecosystem.api_key_manager import (
    api_key_manager, Role, require_admin, require_user_or_admin, get_bearer_token
)

api_key_routes = Blueprint('api_key_routes', __name__, url_prefix='/api')


@api_key_routes.route('/apikey/create', methods=['POST'])
@require_admin
def create_api_key():
    """
    Create a new API key (Admin only).
    
    Request body:
        - name: str - Name/description for the key
        - role: str - 'admin' or 'user' (default: 'user')
        - rate_limit: int - Max requests per minute (default: 60)
    
    Response:
        - key: str - The generated API key (shown only once!)
        - api_key: object - Key metadata (without the actual key)
    """
    data = request.get_json() or {}
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Name is required for the API key"}), 400
    
    # Parse role
    role_str = data.get('role', 'user').lower()
    try:
        role = Role(role_str)
    except ValueError:
        return jsonify({
            "error": f"Invalid role '{role_str}'. Must be 'admin' or 'user'"
        }), 400
    
    # Parse rate limit
    rate_limit = data.get('rate_limit', 60)
    try:
        rate_limit = int(rate_limit)
        if rate_limit < 1 or rate_limit > 10000:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            "error": "rate_limit must be an integer between 1 and 10000"
        }), 400
    
    # Generate the key
    key, api_key = api_key_manager.generate_key(name, role, rate_limit)
    
    return jsonify({
        "success": True,
        "message": "API key created successfully. Save this key - it will not be shown again!",
        "key": key,
        "api_key": api_key.to_dict(include_key=False)
    }), 201


@api_key_routes.route('/apikey/list', methods=['GET'])
@require_admin
def list_api_keys():
    """
    List all API keys (Admin only).
    
    Query params:
        - include_inactive: bool - Include revoked keys (default: false)
    
    Response:
        - keys: list - Array of API key objects (without actual key values)
    """
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    keys = api_key_manager.get_all_keys()
    
    if not include_inactive:
        keys = [k for k in keys if k.is_active]
    
    return jsonify({
        "success": True,
        "count": len(keys),
        "keys": [k.to_dict(include_key=False) for k in keys]
    })


@api_key_routes.route('/apikey/revoke/<key_id>', methods=['POST'])
@require_admin
def revoke_api_key(key_id: str):
    """
    Revoke an API key by ID (Admin only).
    Revoked keys cannot be used but remain in the database for audit.
    """
    success = api_key_manager.revoke_key(key_id)
    
    if not success:
        return jsonify({"error": "API key not found"}), 404
    
    return jsonify({
        "success": True,
        "message": "API key revoked successfully"
    })


@api_key_routes.route('/apikey/delete/<key_id>', methods=['DELETE'])
@require_admin
def delete_api_key(key_id: str):
    """
    Permanently delete an API key by ID (Admin only).
    This action cannot be undone.
    """
    success = api_key_manager.delete_key(key_id)
    
    if not success:
        return jsonify({"error": "API key not found"}), 404
    
    return jsonify({
        "success": True,
        "message": "API key deleted permanently"
    })


@api_key_routes.route('/apikey/verify', methods=['GET'])
@require_user_or_admin
def verify_api_key():
    """
    Verify the current API key and return its metadata.
    Useful for testing authentication.
    """
    from flask import g
    
    api_key = g.api_key
    
    return jsonify({
        "success": True,
        "valid": True,
        "api_key": api_key.to_dict(include_key=False)
    })


@api_key_routes.route('/apikey/setup', methods=['POST'])
def setup_initial_key():
    """
    One-time setup endpoint to create the master admin key.
    Only works if no API keys exist in the system.
    """
    master_key = api_key_manager.create_master_key()
    
    if master_key:
        return jsonify({
            "success": True,
            "message": "Master admin key created. Save this key immediately - it will not be shown again!",
            "key": master_key,
            "role": "admin",
            "usage": "Include in Authorization header: Bearer <key>"
        }), 201
    else:
        return jsonify({
            "success": False,
            "message": "API keys already exist. Use /api/apikey/create with an existing admin key to create more."
        }), 409
