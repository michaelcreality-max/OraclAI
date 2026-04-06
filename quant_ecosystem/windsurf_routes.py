"""
Windsurf Admin Routes - API Endpoints for AI Orchestrator

Provides HTTP endpoints for:
- AI command submission
- Website building
- Code generation and analysis
- System change management
- Admin oversight
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
import logging
from typing import Dict, Any

from windsurf_admin_orchestrator import windsurf_orchestrator, ai_generate_code, ai_build_website, ai_analyze_code
from quant_ecosystem.admin_control import admin_control

log = logging.getLogger(__name__)

# Create blueprint
windsurf_routes = Blueprint('windsurf', __name__, url_prefix='/api/windsurf')


def get_auth_token() -> str:
    """Extract auth token from request"""
    # Check header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    # Check cookies
    token = request.cookies.get('admin_token')
    if token:
        return token
    
    # Check query params
    return request.args.get('token', '')


def require_admin(f):
    """Decorator to require admin authentication"""
    def decorated(*args, **kwargs):
        token = get_auth_token()
        if not token or not admin_control.validate_session(token):
            return jsonify({'success': False, 'error': 'Unauthorized - Admin access required'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


# ==================== AI COMMAND ENDPOINTS ====================

@windsurf_routes.route('/command', methods=['POST'])
@require_admin
def submit_command():
    """Submit an AI command to the orchestrator"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        command_type = data.get('command_type')
        prompt = data.get('prompt')
        context = data.get('context', {})
        priority = data.get('priority', 5)
        
        if not command_type or not prompt:
            return jsonify({'success': False, 'error': 'command_type and prompt are required'}), 400
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type=command_type,
            prompt=prompt,
            context=context,
            admin_token=token,
            priority=priority
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in submit_command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/generate-code', methods=['POST'])
@require_admin
def generate_code_endpoint():
    """Generate code using AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        prompt = data.get('prompt')
        file_path = data.get('file_path', 'generated.py')
        current_content = data.get('current_content', '')
        apply_to_system = data.get('apply_to_system', False)
        
        if not prompt:
            return jsonify({'success': False, 'error': 'prompt is required'}), 400
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type='generate_code',
            prompt=prompt,
            context={
                'file_path': file_path,
                'current_content': current_content,
                'apply_to_system': apply_to_system
            },
            admin_token=token
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in generate_code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/analyze-code', methods=['POST'])
@require_admin
def analyze_code_endpoint():
    """Analyze code using multi-agent AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        code = data.get('code', '')
        language = data.get('language', 'python')
        prompt = data.get('prompt', 'Analyze this code for issues and improvements')
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type='analyze_code',
            prompt=prompt,
            context={'code': code, 'language': language},
            admin_token=token
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in analyze_code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/refactor-code', methods=['POST'])
@require_admin
def refactor_code_endpoint():
    """Refactor code using AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        code = data.get('code', '')
        refactor_type = data.get('refactor_type', 'general')
        language = data.get('language', 'python')
        apply_to_system = data.get('apply_to_system', False)
        file_path = data.get('file_path', 'unknown')
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type='refactor_code',
            prompt=f'Refactor code: {refactor_type}',
            context={
                'code': code,
                'refactor_type': refactor_type,
                'language': language,
                'apply_to_system': apply_to_system,
                'file_path': file_path
            },
            admin_token=token
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in refactor_code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WEBSITE BUILDER ENDPOINTS ====================

@windsurf_routes.route('/build-website', methods=['POST'])
@require_admin
def build_website_endpoint():
    """Build a website using multi-agent AI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        config = data.get('config', {})
        project_path = data.get('project_path')
        
        # Ensure required fields
        config.setdefault('title', 'AI Generated Website')
        config.setdefault('description', data.get('prompt', 'A modern website'))
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type='build_website',
            prompt=config.get('description', 'Build a website'),
            context={
                'config': config,
                'project_path': project_path
            },
            admin_token=token
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in build_website: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/website-preview/<project_id>', methods=['GET'])
def website_preview(project_id: str):
    """Preview a generated website"""
    try:
        # Find the project files
        project_path = f"projects/{project_id}"
        html_path = f"{project_path}/index.html"
        
        import os
        if os.path.exists(html_path):
            with open(html_path, 'r') as f:
                html_content = f.read()
            
            # Inject preview header
            preview_header = """
            <div style="position: fixed; top: 0; left: 0; right: 0; background: #1a1a1a; 
                        color: #fff; padding: 10px; z-index: 9999; font-family: sans-serif;
                        border-bottom: 2px solid #f97316; display: flex; justify-content: space-between;">
                <span>🔮 AI Generated Preview</span>
                <span>Project: """ + project_id + """</span>
            </div>
            <div style="height: 40px;"></div>
            """
            
            html_content = html_content.replace('<body>', f'<body>{preview_header}')
            
            return Response(html_content, mimetype='text/html')
        else:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
            
    except Exception as e:
        log.error(f"Error in website_preview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SYSTEM CHANGE MANAGEMENT ====================

@windsurf_routes.route('/changes/pending', methods=['GET'])
@require_admin
def get_pending_changes():
    """Get all pending system changes"""
    try:
        token = get_auth_token()
        result = windsurf_orchestrator.get_pending_changes(token)
        return jsonify(result)
    except Exception as e:
        log.error(f"Error in get_pending_changes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/changes/approve', methods=['POST'])
@require_admin
def approve_change():
    """Approve and apply a pending change"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        change_id = data.get('change_id')
        if not change_id:
            return jsonify({'success': False, 'error': 'change_id is required'}), 400
        
        token = get_auth_token()
        result = windsurf_orchestrator.approve_change(change_id, token)
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in approve_change: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/changes/reject', methods=['POST'])
@require_admin
def reject_change():
    """Reject a pending change"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        change_id = data.get('change_id')
        reason = data.get('reason', '')
        
        if not change_id:
            return jsonify({'success': False, 'error': 'change_id is required'}), 400
        
        token = get_auth_token()
        result = windsurf_orchestrator.reject_change(change_id, token, reason)
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in reject_change: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/changes/history', methods=['GET'])
@require_admin
def get_change_history():
    """Get history of applied changes"""
    try:
        token = get_auth_token()
        result = windsurf_orchestrator.get_command_history(token)
        return jsonify(result)
    except Exception as e:
        log.error(f"Error in get_change_history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SYSTEM MODIFICATION ENDPOINTS ====================

@windsurf_routes.route('/system/modify', methods=['POST'])
@require_admin
def system_modify():
    """Submit a direct system modification"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        modification_type = data.get('modification_type')
        target = data.get('target')
        content = data.get('content')
        description = data.get('description', 'System modification')
        
        if not modification_type or not target:
            return jsonify({'success': False, 'error': 'modification_type and target are required'}), 400
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type='system_modify',
            prompt=description,
            context={
                'modification_type': modification_type,
                'target': target,
                'content': content
            },
            admin_token=token,
            priority=9  # High priority for system modifications
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in system_modify: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/system/status', methods=['GET'])
@require_admin
def system_status():
    """Get orchestrator system status"""
    try:
        status = windsurf_orchestrator.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        log.error(f"Error in system_status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== COMPLETE PROJECT ENDPOINTS ====================

@windsurf_routes.route('/complete-project', methods=['POST'])
@require_admin
def complete_project():
    """Generate a complete end-to-end project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        prompt = data.get('prompt')
        project_type = data.get('project_type', 'web_app')
        features = data.get('features', ['website'])
        
        if not prompt:
            return jsonify({'success': False, 'error': 'prompt is required'}), 400
        
        token = get_auth_token()
        result = windsurf_orchestrator.submit_command(
            command_type='complete_project',
            prompt=prompt,
            context={
                'project_type': project_type,
                'features': features
            },
            admin_token=token
        )
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in complete_project: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== UTILITY ENDPOINTS ====================

@windsurf_routes.route('/templates', methods=['GET'])
def get_templates():
    """Get available code templates"""
    try:
        from windsurf_ai_engine import CodeTemplateLibrary, CodeLanguage
        
        templates = {
            'html': CodeTemplateLibrary.list_templates(CodeLanguage.HTML),
            'python': CodeTemplateLibrary.list_templates(CodeLanguage.PYTHON),
            'css': CodeTemplateLibrary.list_templates(CodeLanguage.CSS),
            'javascript': CodeTemplateLibrary.list_templates(CodeLanguage.JAVASCRIPT)
        }
        
        return jsonify({'success': True, 'templates': templates})
        
    except Exception as e:
        log.error(f"Error in get_templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@windsurf_routes.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get available AI capabilities"""
    return jsonify({
        'success': True,
        'capabilities': {
            'code_generation': {
                'languages': ['python', 'html', 'css', 'javascript'],
                'features': ['templates', 'smart_completion', 'refactoring']
            },
            'website_building': {
                'features': ['multi_agent', 'responsive_design', 'animations', 'seo'],
                'agents': ['structure', 'styling', 'interactivity', 'content', 'optimization']
            },
            'code_analysis': {
                'agents': ['architect', 'debugger', 'optimizer', 'security', 'algorithms'],
                'features': ['complexity_analysis', 'security_audit', 'performance_review']
            },
            'system_modification': {
                'requires_approval': True,
                'features': ['file_create', 'file_modify', 'config_update']
            }
        }
    })


# Error handlers
@windsurf_routes.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@windsurf_routes.errorhandler(500)
def internal_error(e):
    log.error(f"Internal error: {e}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
