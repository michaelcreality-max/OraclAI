"""
Connection Diagnostics and Improved CORS Support
Add this to production_server.py to improve frontend connectivity
"""

from flask import Flask, jsonify, request, make_response
from functools import wraps
import logging

log = logging.getLogger(__name__)

# Add this BEFORE app.run() in production_server.py:

# ============================================
# ENHANCED CORS & CONNECTION SUPPORT
# ============================================

# Handle OPTIONS preflight requests globally
@app.before_request
def handle_preflight():
    """Handle CORS preflight OPTIONS requests"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to every response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
    return response

# ============================================
# CONNECTION TEST ENDPOINTS
# ============================================

@app.route('/api/test/connection', methods=['GET', 'POST', 'OPTIONS'])
def test_connection():
    """
    Simple connection test endpoint - no auth required.
    Returns diagnostic info to help debug frontend connection issues.
    """
    # Gather request info for diagnostics
    headers_received = dict(request.headers)
    
    # Remove sensitive info from logs
    safe_headers = {k: v for k, v in headers_received.items() 
                   if k.lower() not in ['authorization', 'cookie']}
    
    log.info(f"Connection test from {request.remote_addr}")
    log.info(f"Headers: {safe_headers}")
    
    return jsonify({
        "success": True,
        "message": "Backend connection successful!",
        "timestamp": datetime.now().isoformat(),
        "your_ip": request.remote_addr,
        "method": request.method,
        "endpoint": "/api/test/connection",
        "cors_enabled": True,
        "headers_received": list(safe_headers.keys()),
        "server": {
            "host": request.host,
            "url_root": request.url_root
        }
    })


@app.route('/api/test/auth', methods=['GET', 'POST'])
def test_auth():
    """
    Test API key authentication.
    Requires valid Authorization header.
    """
    if not check_api_key():
        return jsonify({
            "success": False,
            "error": "Authentication failed",
            "message": "Check your Authorization: Bearer <api_key> header",
            "tip": "Your API key should look like: ak_xxxxx"
        }), 401
    
    from flask import g
    api_key = getattr(g, 'api_key', None)
    
    return jsonify({
        "success": True,
        "message": "Authentication successful!",
        "key_id": api_key.id if api_key else None,
        "role": api_key.role.value if api_key else None,
        "rate_limit": api_key.rate_limit if api_key else None
    })


@app.route('/api/test/cors-preflight', methods=['OPTIONS'])
def test_cors_preflight():
    """Explicit CORS preflight test endpoint"""
    response = make_response(jsonify({"success": True, "preflight": "ok"}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


# ============================================
# IMPROVED API KEY CHECK WITH BETTER ERRORS
# ============================================

def check_api_key_verbose():
    """
    Enhanced API key check with detailed error messages.
    Returns tuple: (is_valid, error_message, api_key_object)
    """
    from quant_ecosystem.api_key_manager import get_bearer_token, api_key_manager
    
    # Get the key from header
    auth_header = request.headers.get('Authorization', '')
    key = get_bearer_token()
    
    # Log for debugging (safely)
    log.debug(f"Auth header received: {auth_header[:20]}..." if auth_header else "No auth header")
    
    # Check 1: Header present?
    if not auth_header:
        return False, "No Authorization header found. Add: Authorization: Bearer YOUR_API_KEY", None
    
    # Check 2: Correct format?
    if not auth_header.startswith('Bearer '):
        return False, "Authorization header must start with 'Bearer '. Format: 'Bearer ak_xxxxx'", None
    
    # Check 3: Key present after Bearer?
    if not key or len(key) < 10:
        return False, f"API key too short or missing after 'Bearer '. Got: '{key[:20] if key else 'nothing'}...'", None
    
    # Check 4: Key format valid?
    if not key.startswith('ak_'):
        return False, f"API key should start with 'ak_'. Your key starts with: '{key[:10]}...'", None
    
    # Check 5: Validate against database
    api_key = api_key_manager.validate_key(key)
    if not api_key:
        return False, "Invalid, revoked, or expired API key. Generate a new key using generate_api_key.py", None
    
    # Check 6: Rate limit
    if not api_key_manager.check_rate_limit(api_key.id, api_key.rate_limit):
        return False, f"Rate limit exceeded ({api_key.rate_limit} requests/min). Wait a moment and retry.", None
    
    # Success!
    from flask import g
    g.api_key = api_key
    return True, None, api_key


# ============================================
# REPLACE EXISTING CHECK_API_KEY FUNCTION
# ============================================

# Comment out the old check_api_key in production_server.py and use this instead:
"""
def check_api_key():
    is_valid, error_msg, api_key = check_api_key_verbose()
    if not is_valid:
        log.warning(f"API key check failed: {error_msg}")
    return is_valid
"""

# ============================================
# FRONTEND CONNECTION CODE (Copy to your React app)
# ============================================

FRONTEND_CONNECTION_CODE = '''
// ==========================================
// RELIABLE BACKEND CONNECTION CONFIG
// ==========================================

const API_CONFIG = {
  // Primary and backup servers
  SERVERS: [
    'http://localhost:5000',
    'http://localhost:5001'
  ],
  
  // Your API key
  API_KEY: 'ak_eee359665bfda3656c19b7e0819b0637ec11aa696ae5fd220faf3bafb01ebf21',
  
  // Request settings
  TIMEOUT: 10000,  // 10 seconds
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,  // 1 second between retries
};

// ==========================================
// RELIABLE FETCH WITH RETRY & FAILOVER
// ==========================================

class BackendConnection {
  constructor() {
    this.currentServerIndex = 0;
    this.connectionStatus = 'unknown'; // 'connected', 'degraded', 'disconnected'
  }
  
  getCurrentBaseUrl() {
    return API_CONFIG.SERVERS[this.currentServerIndex];
  }
  
  async testConnection() {
    try {
      const response = await fetch(`${this.getCurrentBaseUrl()}/api/test/connection`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        signal: AbortSignal.timeout(5000)
      });
      
      if (response.ok) {
        const data = await response.json();
        this.connectionStatus = 'connected';
        return { success: true, data };
      }
    } catch (error) {
      console.warn('Connection test failed:', error.message);
    }
    return { success: false, error: 'Connection failed' };
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.getCurrentBaseUrl()}${endpoint}`;
    
    // Default headers
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${API_CONFIG.API_KEY}`,
      ...options.headers
    };
    
    // Remove Content-Type for FormData
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }
    
    const fetchOptions = {
      ...options,
      headers,
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
    };
    
    // Retry logic with failover
    for (let attempt = 0; attempt < API_CONFIG.MAX_RETRIES; attempt++) {
      try {
        console.log(`[Attempt ${attempt + 1}] ${options.method || 'GET'} ${url}`);
        
        const response = await fetch(url, fetchOptions);
        
        // Handle CORS or network errors
        if (!response) {
          throw new Error('No response received - check CORS settings');
        }
        
        // Handle HTTP errors
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          
          // Authentication error
          if (response.status === 401) {
            throw new Error(`Auth failed: ${errorData.message || 'Invalid API key'}`);
          }
          
          // Rate limit
          if (response.status === 429) {
            throw new Error('Rate limit exceeded - wait and retry');
          }
          
          throw new Error(`HTTP ${response.status}: ${errorData.message || response.statusText}`);
        }
        
        // Success!
        const data = await response.json();
        this.connectionStatus = 'connected';
        return { success: true, data, status: response.status };
        
      } catch (error) {
        console.error(`[Attempt ${attempt + 1}] Failed:`, error.message);
        
        // Try next server on connection errors
        if (error.name === 'TypeError' || error.name === 'AbortError') {
          this.currentServerIndex = (this.currentServerIndex + 1) % API_CONFIG.SERVERS.length;
          console.log(`Switching to backup server: ${this.getCurrentBaseUrl()}`);
          this.connectionStatus = 'degraded';
        }
        
        // Wait before retry (except on last attempt)
        if (attempt < API_CONFIG.MAX_RETRIES - 1) {
          await new Promise(r => setTimeout(r, API_CONFIG.RETRY_DELAY * (attempt + 1)));
        }
      }
    }
    
    this.connectionStatus = 'disconnected';
    return { 
      success: false, 
      error: `Failed after ${API_CONFIG.MAX_RETRIES} attempts on all servers`,
      connectionStatus: 'disconnected'
    };
  }
  
  // Convenience methods
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }
  
  async post(endpoint, body) {
    return this.request(endpoint, { 
      method: 'POST', 
      body: JSON.stringify(body) 
    });
  }
}

// ==========================================
// USAGE EXAMPLE
// ==========================================

const api = new BackendConnection();

// Test connection on app start
async function initializeApp() {
  const test = await api.testConnection();
  if (test.success) {
    console.log('✅ Backend connected:', test.data.message);
  } else {
    console.error('❌ Backend connection failed');
  }
  
  // Load system state
  const state = await api.get('/api/admin/system/state');
  if (state.success) {
    console.log('System state:', state.data);
  } else {
    console.error('Failed to load state:', state.error);
  }
}

// Export for use in components
export { api, API_CONFIG, initializeApp };
'''

# Print the frontend code
print("=" * 70)
print("FRONTEND CONNECTION CODE - Copy this to your React app")
print("=" * 70)
print(FRONTEND_CONNECTION_CODE)
print("=" * 70)
