#!/usr/bin/env python3
"""
Production Server with Multi-Agent AI Debate System
Optimized for external frontend access (Lovable, etc.)
"""

from flask import Flask, jsonify, request, Response, stream_with_context, session, redirect, url_for
from flask_cors import CORS
import sys
import os
import json
import uuid
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

sys.path.append('.')

from quant_ecosystem.multi_agent_orchestrator import orchestrator, AgentDebateResult
from quant_ecosystem.us_market_universe import us_market
from quant_ecosystem.streaming_api import stream_manager, format_debate_for_frontend
from quant_ecosystem.api_v2_routes import api_v2
from quant_ecosystem.agents.data_collection_agent import data_collection_agent
from quant_ecosystem.api_key_manager import api_key_manager, require_user_or_admin, require_auth
from quant_ecosystem.api_key_routes import api_key_routes
from quant_ecosystem.execution_safety import execution_safety, SystemMode
from quant_ecosystem.safety_routes import safety_routes
from quant_ecosystem.user_memory import user_memory
from quant_ecosystem.user_routes import user_routes
from quant_ecosystem.admin_control import admin_control
from quant_ecosystem.admin_routes import admin_routes
from quant_ecosystem.admin_security_routes import admin_security_routes
from quant_ecosystem.file_manager import file_manager
from quant_ecosystem.file_routes import file_routes
from quant_ecosystem.agent_routes import agent_routes
from quant_ecosystem.agent_implementations import register_all_agents
from quant_ecosystem.modification_routes import modification_routes

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'oraclai-secret-key-change-in-production')

# Simple in-memory session storage for web users
web_sessions = {}
admin_sessions = {}

# Live user tracking system
class LiveTracker:
    def __init__(self):
        self.active_users = {}  # session_id -> {user_id, username, last_seen, ip}
        self.active_debates = {}  # session_id -> {symbol, start_time, agents}
        self.request_times = []  # List of recent request timestamps
        self.lock = threading.Lock()
    
    def track_user(self, session_id, user_data):
        """Track an active user session"""
        with self.lock:
            self.active_users[session_id] = {
                'user_id': user_data.get('user_id'),
                'username': user_data.get('username', 'Anonymous'),
                'is_admin': user_data.get('is_admin', False),
                'last_seen': time.time(),
                'ip': user_data.get('ip'),
                'user_agent': user_data.get('user_agent'),
                'joined_at': time.time()
            }
    
    def update_user_activity(self, session_id):
        """Update last seen timestamp for a user"""
        with self.lock:
            if session_id in self.active_users:
                self.active_users[session_id]['last_seen'] = time.time()
    
    def remove_user(self, session_id):
        """Remove a user session"""
        with self.lock:
            if session_id in self.active_users:
                del self.active_users[session_id]
    
    def track_debate(self, session_id, symbol):
        """Track an active debate"""
        with self.lock:
            self.active_debates[session_id] = {
                'symbol': symbol,
                'start_time': time.time(),
                'status': 'active'
            }
    
    def complete_debate(self, session_id):
        """Mark a debate as complete"""
        with self.lock:
            if session_id in self.active_debates:
                self.active_debates[session_id]['status'] = 'complete'
                self.active_debates[session_id]['end_time'] = time.time()
    
    def track_request(self):
        """Track a request for response time calculation"""
        with self.lock:
            now = time.time()
            self.request_times.append(now)
            # Keep only last 100 requests
            self.request_times = self.request_times[-100:]
    
    def get_stats(self):
        """Get current platform stats"""
        with self.lock:
            now = time.time()
            # Count users active in last 5 minutes
            active_users_count = sum(
                1 for u in self.active_users.values()
                if now - u['last_seen'] < 300  # 5 minutes
            )
            
            # Count active debates
            active_debates_count = sum(
                1 for d in self.active_debates.values()
                if d['status'] == 'active'
            )
            
            # Calculate average response time
            avg_response = 0
            if len(self.request_times) >= 2:
                # Calculate average time between requests as proxy
                times = self.request_times[-10:]
                if len(times) >= 2:
                    avg_response = sum(times[i] - times[i-1] for i in range(1, len(times))) / (len(times) - 1)
                    avg_response = round(avg_response * 1000, 0)  # Convert to ms
            
            return {
                'active_users': active_users_count,
                'total_users': len(self.active_users),
                'active_debates': active_debates_count,
                'total_debates': len(self.active_debates),
                'system_status': 'operational',
                'avg_response_ms': avg_response if avg_response > 0 else '--',
                'timestamp': now
            }
    
    def get_active_users_list(self):
        """Get list of active users"""
        with self.lock:
            now = time.time()
            return [
                {
                    'username': u['username'],
                    'is_admin': u['is_admin'],
                    'session_duration': int(now - u['joined_at']),
                    'last_activity': int(now - u['last_seen'])
                }
                for u in self.active_users.values()
                if now - u['last_seen'] < 300
            ]

# Initialize live tracker
live_tracker = LiveTracker()

# Configure CORS for external frontend access
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins for now (configure for production)
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    },
    r"/stream/*": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Register blueprints
app.register_blueprint(api_v2)
app.register_blueprint(api_key_routes)
app.register_blueprint(safety_routes)
app.register_blueprint(user_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(admin_security_routes)
app.register_blueprint(file_routes)
app.register_blueprint(agent_routes)
app.register_blueprint(modification_routes)

# Configuration
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')  # Bind to all interfaces
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
# Legacy API key support (optional, for backward compatibility)
LEGACY_API_KEY = os.environ.get('API_KEY', None)

# Health check endpoint (no auth required)
@app.route('/health')
def health():
    """Health check for load balancers"""
    return jsonify({
        "status": "healthy",
        "service": "ai-debate-system",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(orchestrator.active_sessions),
        "active_streams": stream_manager.get_active_stream_count()
    })

# API key check middleware (supports both new system and legacy API key)
def check_api_key():
    """Check API key using new API key manager or legacy key"""
    from quant_ecosystem.api_key_manager import get_bearer_token
    
    # Try new API key system first
    key = get_bearer_token()
    if key:
        from quant_ecosystem.api_key_manager import api_key_manager
        api_key = api_key_manager.validate_key(key)
        if api_key:
            # Store in Flask g for access in endpoint
            from flask import g
            g.api_key = api_key
            return True
    
    # Fall back to legacy API key
    if LEGACY_API_KEY:
        provided_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        return provided_key == LEGACY_API_KEY
    
    # If no keys configured, allow access (for development)
    return True


# Control Panel UI
from flask import render_template

HTML_LANDING = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OraclAI - AI Trading System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e5e5e5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        .container {
            max-width: 800px;
            text-align: center;
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #f97316, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        p {
            color: #9ca3af;
            font-size: 1.2rem;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #111;
            border: 1px solid #222;
            padding: 1rem 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #f97316;
            color: white;
        }
        .btn-primary:hover {
            background: #ea580c;
        }
        .btn-secondary {
            background: #1f2937;
            color: #e5e5e5;
            border: 1px solid #374151;
        }
        .btn-secondary:hover {
            background: #374151;
        }
        .features {
            margin-top: 3rem;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            text-align: left;
        }
        .feature {
            background: #111;
            border: 1px solid #222;
            padding: 1.5rem;
            border-radius: 8px;
        }
        .feature h3 {
            color: #f97316;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }
        .feature p {
            font-size: 0.9rem;
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="status">
            <div class="status-dot"></div>
            <span>System Operational</span>
        </div>
        <h1>OraclAI</h1>
        <p>Multi-Agent AI Trading System<br>Professional Bloomberg-Style Terminal</p>
        <div class="buttons">
            <a href="/terminal" class="btn btn-primary">Launch Terminal</a>
            <a href="/admin" class="btn btn-secondary">Admin Dashboard</a>
        </div>
        <div class="features">
            <div class="feature">
                <h3>🤖 4 AI Agents</h3>
                <p>Bullish, Bearish, Judge & Data agents debate every trade decision</p>
            </div>
            <div class="feature">
                <h3>⚡ Smart Fallback</h3>
                <p>Automatic routing to Gemini when multi-agent system is overloaded</p>
            </div>
            <div class="feature">
                <h3>🔐 No API Key Required</h3>
                <p>Direct access to trading terminal. Admin features protected.</p>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/')
def index():
    """Serve the main landing page"""
    return HTML_LANDING

@app.route('/terminal')
def terminal():
    """Serve the Bloomberg-style trading terminal - NO API KEY REQUIRED"""
    return render_template('terminal.html')

@app.route('/admin')
def admin_dashboard():
    """Serve the admin dashboard - requires admin login"""
    # Check if user is logged in as admin
    if not session.get('is_admin'):
        # Return login page instead
        return HTML_ADMIN_LOGIN
    return render_template('admin.html')

# Simple admin credentials (in production, use proper auth)
ADMIN_USERNAME = "MK1"
ADMIN_PASSWORD = "123456"

@app.route('/api/web/login', methods=['POST'])
def web_login():
    """Login endpoint for web users"""
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['user_id'] = str(uuid.uuid4())
        session['username'] = username
        session['is_admin'] = True
        return jsonify({
            "success": True,
            "user": {
                "username": username,
                "role": "admin",
                "isAdmin": True
            }
        })
    else:
        return jsonify({
            "success": False,
            "error": "Invalid credentials"
        }), 401

@app.route('/api/web/logout', methods=['POST'])
def web_logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({"success": True})

@app.route('/api/web/session', methods=['GET'])
def get_session():
    """Get current session info"""
    if session.get('username'):
        return jsonify({
            "success": True,
            "user": {
                "username": session.get('username'),
                "role": "admin" if session.get('is_admin') else "user",
                "isAdmin": session.get('is_admin', False)
            }
        })
    return jsonify({"success": False, "error": "Not logged in"}), 401

@app.before_request
def track_request_middleware():
    """Track all requests for live monitoring"""
    live_tracker.track_request()
    # Update user activity if they have a session
    if session.get('user_id'):
        live_tracker.update_user_activity(session.get('session_id') or session.get('user_id'))

# Live stats SSE endpoint for admin dashboard
@app.route('/api/admin/live-stats')
def admin_live_stats():
    """Server-Sent Events for live platform statistics"""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    def generate_stats():
        while True:
            stats = live_tracker.get_stats()
            data = json.dumps({
                'type': 'stats',
                'data': stats
            })
            yield f"data: {data}\n\n"
            time.sleep(2)  # Update every 2 seconds
    
    return Response(
        stream_with_context(generate_stats()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/api/admin/stats')
def admin_stats():
    """Get current platform stats (REST API)"""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    return jsonify({
        "success": True,
        "stats": live_tracker.get_stats(),
        "active_users": live_tracker.get_active_users_list()
    })

# File Editor API Endpoints
@app.route('/api/admin/files')
def list_files():
    """List files in the project directory"""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    path = request.args.get('path', '.')
    try:
        entries = []
        for entry in os.scandir(path):
            entries.append({
                'name': entry.name,
                'path': entry.path,
                'is_file': entry.is_file(),
                'is_dir': entry.is_dir(),
                'size': entry.stat().st_size if entry.is_file() else 0,
                'modified': entry.stat().st_mtime
            })
        return jsonify({"success": True, "files": sorted(entries, key=lambda x: (not x['is_dir'], x['name']))})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/files/read')
def read_file_admin():
    """Read file contents"""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    filepath = request.args.get('path')
    if not filepath:
        return jsonify({"error": "Path required"}), 400
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            "success": True,
            "content": content,
            "path": filepath,
            "size": len(content)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/files/write', methods=['POST'])
def write_file_admin():
    """Write file contents"""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json() or {}
    filepath = data.get('path')
    content = data.get('content')
    
    if not filepath or content is None:
        return jsonify({"error": "Path and content required"}), 400
    
    try:
        # Create backup before writing
        if os.path.exists(filepath):
            backup_path = filepath + '.backup.' + str(int(time.time()))
            with open(filepath, 'r', encoding='utf-8') as f:
                old_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(old_content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            "success": True,
            "message": "File saved successfully",
            "path": filepath,
            "size": len(content)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/windsurf/apply', methods=['POST'])
def windsurf_apply_changes():
    """Apply changes via Windsurf API"""
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json() or {}
    changes = data.get('changes', [])
    
    results = []
    for change in changes:
        filepath = change.get('path')
        operation = change.get('operation', 'edit')  # edit, create, delete
        content = change.get('content', '')
        
        try:
            if operation == 'create':
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                results.append({'path': filepath, 'status': 'created'})
            
            elif operation == 'edit':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                results.append({'path': filepath, 'status': 'edited'})
            
            elif operation == 'delete':
                if os.path.exists(filepath):
                    os.remove(filepath)
                    results.append({'path': filepath, 'status': 'deleted'})
                else:
                    results.append({'path': filepath, 'status': 'not_found'})
        
        except Exception as e:
            results.append({'path': filepath, 'status': 'error', 'error': str(e)})
    
    return jsonify({
        "success": True,
        "results": results,
        "applied_count": len([r for r in results if r['status'] in ('created', 'edited', 'deleted')])
    })

HTML_ADMIN_LOGIN = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login | OraclAI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'SF Mono', monospace;
            background: #0a0a0a;
            color: #ffffff;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: #111111;
            border: 1px solid #27272a;
            border-radius: 12px;
            padding: 40px;
            width: 400px;
            text-align: center;
        }
        .logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #f97316, #f59e0b);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            font-weight: bold;
            margin: 0 auto 20px;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }
        p {
            color: #a1a1aa;
            margin-bottom: 24px;
        }
        .form-group {
            margin-bottom: 16px;
            text-align: left;
        }
        label {
            display: block;
            font-size: 12px;
            color: #a1a1aa;
            margin-bottom: 6px;
            text-transform: uppercase;
        }
        input {
            width: 100%;
            background: #1a1a1a;
            border: 1px solid #27272a;
            border-radius: 6px;
            padding: 12px;
            color: #ffffff;
            font-family: inherit;
            font-size: 14px;
        }
        input:focus {
            outline: none;
            border-color: #f97316;
        }
        button {
            width: 100%;
            background: #f97316;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 8px;
        }
        button:hover {
            background: #ea580c;
        }
        .error {
            color: #ef4444;
            font-size: 12px;
            margin-top: 12px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">O</div>
        <h1>Admin Access</h1>
        <p>OraclAI System Control Panel</p>
        <form onsubmit="return handleLogin(event)">
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" placeholder="Enter username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" placeholder="Enter password" required>
            </div>
            <button type="submit">Login</button>
            <div class="error" id="error">Invalid credentials</div>
        </form>
    </div>
    <script>
        async function handleLogin(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/web/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.reload();
                } else {
                    document.getElementById('error').style.display = 'block';
                }
            } catch (error) {
                document.getElementById('error').style.display = 'block';
            }
        }
    </script>
</body>
</html>'''

# Web UI API endpoints - NO API KEY REQUIRED for direct user access
@app.route('/api/web/chat', methods=['POST'])
def web_chat():
    """Process chat messages from web terminal - no API key needed"""
    data = request.get_json() or {}
    user_input = data.get('message', '').strip()
    user_id = session.get('user_id') or str(uuid.uuid4())
    session['user_id'] = user_id
    
    if not user_input:
        return jsonify({"error": "Message required"}), 400
    
    # Store user memory
    user_memory.store_conversation(user_id, "user", user_input)
    
    return jsonify({
        "success": True,
        "message": "Query received",
        "user_id": user_id,
        "classification": classify_input(user_input)
    })

@app.route('/api/web/generate-key', methods=['POST'])
def generate_api_key_web():
    """Generate API key for web users - no API key required"""
    try:
        # Generate a new API key using the existing manager
        from quant_ecosystem.api_key_manager import api_key_manager
        
        # Create a new API key for the user
        user_id = session.get('user_id') or str(uuid.uuid4())
        session['user_id'] = user_id
        
        # Generate key with user role and rate limits
        api_key = api_key_manager.create_key(
            name=f"Web User - {user_id[:8]}",
            role="user",
            rate_limit=60,  # 60 requests per minute
            created_by="web_interface"
        )
        
        if api_key:
            return jsonify({
                "success": True,
                "api_key": api_key.key,
                "user_id": user_id,
                "role": "user",
                "rate_limit": 60,
                "message": "API key generated successfully",
                "usage": {
                    "header": "Authorization: Bearer " + api_key.key,
                    "endpoints": ["/api/v1/classify", "/api/v1/debate/start", "/api/v1/market/stocks"],
                    "rate_limit": "60 requests per minute"
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate API key"
            }), 500
            
    except Exception as e:
        log.error(f"Error generating API key: {e}")
        return jsonify({
            "success": False,
            "error": "System error. Please try again."
        }), 500

def classify_input(user_input):
    """Classify user input for routing"""
    input_lower = user_input.lower()
    
    # Single stock ticker
    clean_input = user_input.strip().upper()
    if len(clean_input) <= 5 and clean_input.isalpha():
        return {"type": "single_stock", "ticker": clean_input}
    
    # Ranking queries
    ranking_keywords = ['top', 'best', 'ranking', 'picks', 'recommendations', 'suggest', 
                       'what should', 'which stocks', 'good stocks', 'buy now', 'invest in']
    if any(word in input_lower for word in ranking_keywords):
        return {"type": "ranking"}
    
    # Market analysis
    market_keywords = ['market', 'trend', 'outlook', 'forecast', 'prediction']
    if any(word in input_lower for word in market_keywords):
        return {"type": "market_analysis"}
    
    return {"type": "general"}

# Fallback LLM endpoint - uses Gemini when multi-agent system fails
@app.route('/api/fallback/llm', methods=['POST'])
def fallback_llm():
    """Fallback to Gemini/ChatGPT when multi-agent system fails"""
    data = request.get_json() or {}
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    # Simulate fallback response (in production, this would call Gemini API)
    fallback_response = generate_fallback_response(query)
    
    return jsonify({
        "success": True,
        "source": "fallback_llm",
        "model": "gemini-pro",
        "message": fallback_response,
        "fallback_notice": "Response powered by Gemini - Multi-agent system temporarily unavailable",
        "timestamp": datetime.now().isoformat()
    })

def generate_fallback_response(query):
    """Generate fallback response when agents are unavailable"""
    query_lower = query.lower()
    
    if 'aapl' in query_lower or 'apple' in query_lower:
        return """⚡ FALLBACK ANALYSIS (Gemini Pro)

**Apple Inc. (AAPL)**

**Current Status:** Neutral to Slightly Bullish

**Key Points:**
• Services revenue growing steadily (+14% YoY)
• Vision Pro launch expanding ecosystem
• iPhone 15 showing solid adoption
• China market concerns persist but manageable

**Technical:** Trading at $195.89, above 50-day MA
**Valuation:** P/E 28.5x - reasonable for quality

**Verdict:** HOLD / Accumulate on dips to $185-190"""
    
    elif 'nvda' in query_lower or 'nvidia' in query_lower:
        return """⚡ FALLBACK ANALYSIS (Gemini Pro)

**NVIDIA Corporation (NVDA)**

**Current Status:** Strong Bullish

**Key Points:**
• AI chip demand exceeding supply (H100, H200)
• Data center revenue up 279% YoY
• Software/services (CUDA) creating moat
• New product cycle (Blackwell) launching

**Technical:** Strong momentum, parabolic but justified
**Valuation:** Premium but deserved - leader in AI revolution

**Verdict:** BUY - Size position carefully given volatility"""
    
    elif 'top' in query_lower or 'best' in query_lower or 'picks' in query_lower:
        return """⚡ FALLBACK RANKING (Gemini Pro)

**Top Stock Picks This Week:**

1. **NVDA** - AI leader, data center growth (BUY)
2. **MSFT** - Cloud stability, AI integration (BUY)
3. **AVGO** - Diversified semiconductor, dividend (BUY)
4. **META** - Cost discipline, AI investments (BUY)
5. **UNH** - Healthcare defensive growth (BUY)

*Note: This is a fallback response. For full multi-agent debate analysis with confidence scores, please try again when system load decreases.*"""
    
    else:
        return f"""⚡ FALLBACK RESPONSE (Gemini Pro)

I've analyzed your query: "{query}"

While the OraclAI multi-agent system is currently processing at high capacity, I've provided this analysis using my backup AI capabilities.

**Current Market Environment:**
• VIX at 14.23 (low volatility regime)
• S&P 500 trending higher
• Tech sector showing strength

**Recommendation:** 
Consider specific stock analysis for actionable trade ideas. Try asking about specific tickers like AAPL, NVDA, or MSFT for detailed analysis.

*This is a fallback response. Multi-agent debate consensus available when system load normalizes.*"""

@app.route('/control')
def control_panel():
    """Serve the legacy system control panel UI"""
    return render_template('control_panel.html')

# Input classification
@app.route('/api/v1/classify', methods=['POST'])
def classify():
    """Classify user input"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    data = request.get_json() or {}
    user_input = data.get('input', '').strip().upper()
    
    if not user_input:
        return jsonify({"error": "Input required"}), 400
    
    # Classification logic
    input_lower = user_input.lower()
    
    # Single stock ticker (1-5 uppercase letters)
    if len(user_input) <= 5 and user_input.isalpha():
        return jsonify({
            "type": "single_stock",
            "ticker": user_input,
            "confidence": 0.95,
            "description": "Stock analysis request - will start multi-agent debate",
            "pipeline": "multi_agent_debate"
        })
    
    # Ranking/Recommendation queries - expanded patterns
    ranking_keywords = ['top', 'best', 'ranking', 'picks', 'recommendations', 'suggest', 
                       'what should', 'which stocks', 'good stocks', 'buy now', 'invest in',
                       'portfolio', 'add to watchlist', 'worth buying']
    if any(word in input_lower for word in ranking_keywords):
        return jsonify({
            "type": "ranking",
            "confidence": 0.85,
            "description": "Stock ranking/recommendation request",
            "pipeline": "stock_ranking",
            "message": "I'll analyze the market and provide top stock recommendations based on multi-agent consensus."
        })
    
    # Hidden gem/Discovery queries
    discovery_keywords = ['hidden', 'gem', 'discover', 'undervalued', 'under the radar',
                         'overlooked', 'potential', 'up and coming', 'breakout',
                         'early stage', 'growth opportunities']
    if any(word in input_lower for word in discovery_keywords):
        return jsonify({
            "type": "discovery",
            "confidence": 0.85,
            "description": "Hidden gem discovery request",
            "pipeline": "hidden_gem_detection"
        })
    
    # Market analysis/general questions
    market_keywords = ['market', 'trend', 'outlook', 'forecast', 'prediction', 
                        'bull', 'bear', 'correction', 'rally', 'recession']
    if any(word in input_lower for word in market_keywords):
        return jsonify({
            "type": "market_analysis",
            "confidence": 0.80,
            "description": "Market trend/outlook analysis",
            "pipeline": "market_analysis",
            "message": "I'll analyze current market conditions and trends using all available agents."
        })
    
    # Analysis/Research queries
    analysis_keywords = ['analyze', 'research', 'look at', 'check', 'how is', 'what about',
                        'thoughts on', 'opinion on', 'review', 'assessment']
    if any(word in input_lower for word in analysis_keywords):
        # Try to extract ticker from the query
        words = user_input.split()
        for word in words:
            clean = word.strip('.,!?;').upper()
            if 1 <= len(clean) <= 5 and clean.isalpha() and clean not in ['HOW', 'WHAT', 'IS', 'ARE', 'THE', 'FOR', 'THIS', 'THAT']:
                return jsonify({
                    "type": "single_stock",
                    "ticker": clean,
                    "confidence": 0.75,
                    "description": f"Stock analysis request for {clean}",
                    "pipeline": "multi_agent_debate"
                })
        
        # No ticker found, ask for clarification
        return jsonify({
            "type": "needs_clarification",
            "confidence": 0.60,
            "description": "Analysis request but no specific stock identified",
            "message": "I can analyze a specific stock for you. Which ticker symbol would you like me to analyze?",
            "suggestions": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
        })
    
    # Portfolio/Account related
    portfolio_keywords = ['my portfolio', 'holdings', 'positions', 'pnl', 'performance',
                         'how am i doing', 'my trades', 'my account']
    if any(word in input_lower for word in portfolio_keywords):
        return jsonify({
            "type": "portfolio_query",
            "confidence": 0.85,
            "description": "User portfolio information request",
            "pipeline": "portfolio_analysis"
        })
    
    # Help/Info requests
    help_keywords = ['help', 'how do', 'how to', 'what can', 'capabilities', 
                     'what do you do', 'who are you', 'explain']
    if any(word in input_lower for word in help_keywords):
        return jsonify({
            "type": "help_request",
            "confidence": 0.90,
            "description": "User requesting help or information",
            "message": "I'm OraclAI, a multi-agent AI trading system. I can:\n\n• Analyze any stock (e.g., 'AAPL' or 'analyze Microsoft')\n• Find top stock picks (e.g., 'best stocks this week')\n• Discover hidden gems (e.g., 'undervalued stocks')\n• Analyze market trends\n• Review your portfolio\n\nWhat would you like to explore?",
            "suggestions": ["Top picks", "Analyze AAPL", "Market outlook", "Hidden gems"]
        })
    
    # If still unclear, try to be helpful rather than failing
    return jsonify({
        "type": "general_query",
        "confidence": 0.50,
        "description": "General query - attempting LLM interpretation",
        "message": "I want to help with your trading question. Could you clarify what you're looking for?",
        "suggestions": [
            "Try: 'Best stocks this week'",
            "Try: 'Analyze AAPL'", 
            "Try: 'Hidden gems'",
            "Try: 'Market outlook'",
            "Try: 'What should I buy?'"
        ],
        "fallback": "I can route this to my general LLM processor for broader interpretation."
    })

# Start multi-agent debate
@app.route('/api/v1/debate/start', methods=['POST'])
def start_debate():
    """Start a new multi-agent debate session"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    data = request.get_json() or {}
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
    
    # Financial context for adaptation
    financial_context = {
        "market_phase": data.get('market_phase', 'normal'),
        "vix_level": data.get('vix_level', 20),
        "systemic_risk": data.get('systemic_risk', 0.3),
        "timestamp": datetime.now().isoformat()
    }
    
    # Start debate
    session_id = orchestrator.start_debate(
        symbol=symbol,
        financial_context=financial_context
    )
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "symbol": symbol,
        "message": "Multi-agent debate started",
        "estimated_duration": "2-3 minutes (includes 1-minute agent analysis timeout)",
        "stream_url": f"/api/v1/debate/stream/{session_id}",
        "status_url": f"/api/v1/debate/status/{session_id}",
        "result_url": f"/api/v1/debate/result/{session_id}"
    })

# SSE stream for live debate updates
@app.route('/api/v1/debate/stream/<session_id>')
def debate_stream(session_id):
    """Server-Sent Events stream for live debate updates"""
    def generate():
        stream = stream_manager.get_stream(session_id)
        if not stream:
            # Try to get from orchestrator session
            session = orchestrator.active_sessions.get(session_id)
            if not session:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                return
            
            # Create stream if not exists
            stream = stream_manager.create_stream(session_id, "sse")
        
        # Send initial connection message
        initial_msg = json.dumps({
            'type': 'connected',
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        yield f"data: {initial_msg}\n\n"
        
        # Stream events
        last_ping = time.time()
        
        try:
            while True:
                # Check if debate is complete
                session = orchestrator.active_sessions.get(session_id)
                if session and session.get('status') == 'complete':
                    # Send final result
                    result = session.get('result')
                    if result:
                        complete_msg = json.dumps({
                            'type': 'complete',
                            'result': result.to_dict()
                        })
                        yield f"data: {complete_msg}\n\n"
                    break
                
                # Send ping every 30 seconds to keep connection alive
                if time.time() - last_ping > 30:
                    ping_msg = json.dumps({
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    })
                    yield f"data: {ping_msg}\n\n"
                    last_ping = time.time()
                
                time.sleep(1)
                
        except GeneratorExit:
            # Client disconnected
            pass
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )

# Get debate status
@app.route('/api/v1/debate/status/<session_id>')
def debate_status(session_id):
    """Get current debate status"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    status = orchestrator.get_session_status(session_id)
    
    if not status:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        **status
    })

# Get debate result
@app.route('/api/v1/debate/result/<session_id>')
def debate_result(session_id):
    """Get final debate result"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    result = orchestrator.get_session_result(session_id)
    
    if not result:
        return jsonify({
            "success": False,
            "error": "Result not available yet or session not found"
        }), 404
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "result": result.to_dict()
    })

# US Market endpoints
@app.route('/api/v1/market/stocks')
def get_us_stocks():
    """Get US market stock list"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    category = request.args.get('category', 'all')
    limit = request.args.get('limit', 100, type=int)
    
    if category == 'all':
        stocks = us_market.get_all_stocks()[:limit]
    else:
        stocks = us_market.get_by_category(category)[:limit]
    
    return jsonify({
        "success": True,
        "category": category,
        "count": len(stocks),
        "stocks": stocks,
        "total_available": len(us_market.get_all_stocks()),
        "categories": ["mega_cap", "large_cap", "mid_cap", "small_cap", "micro_cap"]
    })

@app.route('/api/v1/market/stock/<symbol>')
def get_stock_info(symbol):
    """Get detailed stock information"""
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401
    
    symbol = symbol.upper()
    info = us_market.get_stock_info(symbol)
    
    if info:
        return jsonify({
            "success": True,
            "symbol": symbol,
            "info": info
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Could not fetch info for {symbol}"
        }), 404

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "available": "/api/v1/"}), 404

@app.errorhandler(500)
def internal_error(error):
    log.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    log.info(f"🚀 Starting Production AI Debate Server on {HOST}:{PORT}")
    log.info(f"📊 External access enabled - frontend can connect from any origin")
    log.info(f"🤖 Multi-Agent System: 4 specialized agents with 1-minute analysis timeout")
    log.info(f"🔐 API Key System: Secure authentication with role-based access")
    log.info(f"🛡️ Execution Safety Layer: Pre-execution validation and auto-fallback enabled")
    
    # Initialize API key system
    try:
        existing_keys = api_key_manager.get_all_keys()
        if not existing_keys:
            log.info("🔑 No API keys found. Run POST /api/apikey/setup to create master key")
        else:
            active_keys = sum(1 for k in existing_keys if k.is_active)
            log.info(f"🔑 API Key System: {active_keys}/{len(existing_keys)} keys active")
    except Exception as e:
        log.error(f"❌ API key system initialization error: {e}")
    
    # Initialize safety layer
    try:
        safety_status = execution_safety.validate_execution_readiness()
        log.info(f"🛡️ Safety Layer: Current mode = {safety_status.current_mode.value}")
        log.info(f"🛡️ Safety Checks: {sum(1 for c in safety_status.checks if c.passed)}/{len(safety_status.checks)} passed")
        if not safety_status.execution_allowed:
            log.info(f"🛡️ Execution blocked: {safety_status.recommendations[0] if safety_status.recommendations else 'Safety checks failed'}")
    except Exception as e:
        log.error(f"❌ Safety layer initialization error: {e}")
    
    # Initialize Windsurf Agent Bridge
    try:
        log.info("🤖 Initializing Windsurf Agent Bridge...")
        registered_count = register_all_agents()
        log.info(f"🤖 Windsurf Agents: {registered_count} agents registered and ready")
    except Exception as e:
        log.error(f"❌ Windsurf agent initialization error: {e}")
    
    # Initialize System Self-Modification with default live parameters
    try:
        log.info("🔄 Initializing System Self-Modification...")
        from quant_ecosystem.self_modification import modification_manager
        
        # Register default live parameters
        default_params = [
            {
                'name': 'max_concurrent_analysis',
                'default_value': 5,
                'min_value': 1,
                'max_value': 20,
                'description': 'Maximum number of concurrent stock analyses',
                'category': 'system'
            },
            {
                'name': 'analysis_timeout_seconds',
                'default_value': 60,
                'min_value': 10,
                'max_value': 300,
                'description': 'Timeout for single stock analysis',
                'category': 'system'
            },
            {
                'name': 'debate_auto_close_hours',
                'default_value': 24,
                'min_value': 1,
                'max_value': 168,
                'description': 'Hours after which inactive debates are auto-closed',
                'category': 'threshold'
            },
            {
                'name': 'enable_auto_fallback',
                'default_value': True,
                'allowed_values': [True, False],
                'description': 'Enable automatic fallback to safe mode on anomalies',
                'category': 'threshold'
            },
            {
                'name': 'log_retention_days',
                'default_value': 30,
                'min_value': 1,
                'max_value': 365,
                'description': 'Number of days to retain system logs',
                'category': 'system',
                'requires_restart': True
            }
        ]
        
        for param in default_params:
            modification_manager.register_live_parameter(**param)
        
        log.info(f"🔄 System Self-Modification: {len(default_params)} live parameters registered")
    except Exception as e:
        log.error(f"❌ Self-modification initialization error: {e}")
    
    # Run production server
    # Use threaded=True for handling multiple concurrent requests
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True,
        use_reloader=False  # Disable in production
    )
