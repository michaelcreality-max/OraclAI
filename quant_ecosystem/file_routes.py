"""
File Manager API Routes
Secure file system access for code editor.
"""

from flask import Blueprint, jsonify, request

from quant_ecosystem.file_manager import file_manager
from quant_ecosystem.admin_control import admin_control

file_routes = Blueprint('file_routes', __name__, url_prefix='/api/admin')


def _validate_admin_token() -> tuple:
    """Validate admin token from request"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    
    if not token:
        # Also check in request body for POST requests
        data = request.get_json() or {}
        token = data.get('token', '')
    
    if not token:
        return False, jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    if not admin_control.validate_session(token):
        return False, jsonify({'success': False, 'error': 'Invalid or expired session'}), 401
    
    return True, token, None


@file_routes.route('/files/list', methods=['GET'])
def list_files():
    """
    List files in a directory.
    
    Query params:
        - path: str (relative path, default: "")
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    path = request.args.get('path', '')
    
    result = file_manager.list_directory(path)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/tree', methods=['GET'])
def get_file_tree():
    """
    Get complete project structure as tree.
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    result = file_manager.get_project_structure()
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/read', methods=['GET'])
def read_file():
    """
    Read file contents.
    
    Query params:
        - path: str (relative path, required)
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    path = request.args.get('path', '')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path parameter required'}), 400
    
    result = file_manager.read_file(path)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/write', methods=['POST'])
def write_file():
    """
    Write content to file.
    
    Request body:
        - path: str (relative path, required)
        - content: str (file content, required)
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    data = request.get_json() or {}
    
    path = data.get('path', '')
    content = data.get('content', '')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400
    
    # Log the write operation for audit
    admin_control._log_audit(
        admin_id=token_or_response,  # This is actually the token
        action="FILE_WRITE",
        details=f"File: {path}"
    )
    
    result = file_manager.write_file(path, content)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/delete', methods=['POST'])
def delete_file():
    """
    Delete a file.
    
    Request body:
        - path: str (relative path, required)
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    data = request.get_json() or {}
    path = data.get('path', '')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400
    
    # Log the delete operation for audit
    admin_control._log_audit(
        admin_id=token_or_response,
        action="FILE_DELETE",
        details=f"File: {path}"
    )
    
    result = file_manager.delete_file(path)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/mkdir', methods=['POST'])
def create_directory():
    """
    Create a new directory.
    
    Request body:
        - path: str (relative path, required)
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    data = request.get_json() or {}
    path = data.get('path', '')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400
    
    result = file_manager.create_directory(path)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/search', methods=['GET'])
def search_files():
    """
    Search for text in files.
    
    Query params:
        - query: str (search text, required)
        - pattern: str (file glob pattern, default: "*.py")
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    query = request.args.get('query', '')
    pattern = request.args.get('pattern', '*.py')
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter required'}), 400
    
    result = file_manager.search_files(query, pattern)
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@file_routes.route('/files/reload', methods=['POST'])
def reload_backend():
    """
    Trigger backend reload after code changes.
    This is a development feature - in production, manual restart is recommended.
    
    Request body:
        - soft_reload: bool (try hot reload first, default: true)
    """
    valid, token_or_response, error_code = _validate_admin_token()
    if not valid:
        return token_or_response, error_code
    
    data = request.get_json() or {}
    soft_reload = data.get('soft_reload', True)
    
    try:
        # Log the reload request
        admin_control._log_audit(
            admin_id=token_or_response,
            action="BACKEND_RELOAD",
            details=f"Soft reload: {soft_reload}"
        )
        
        if soft_reload:
            # Attempt to clear Python module cache for hot reload
            import sys
            
            modules_to_remove = []
            for name, module in list(sys.modules.items()):
                if name.startswith('quant_ecosystem'):
                    modules_to_remove.append(name)
            
            for name in modules_to_remove:
                del sys.modules[name]
            
            return jsonify({
                'success': True,
                'message': f'Modules cleared for hot reload. Removed {len(modules_to_remove)} modules.',
                'reloaded_modules': modules_to_remove[:20]  # Show first 20
            })
        else:
            # Full restart not available via API - requires external restart
            return jsonify({
                'success': True,
                'message': 'Hot reload not available. Please restart the server manually.',
                'note': 'For development, use --reload flag when starting server'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Reload failed: {str(e)}'
        }), 500
