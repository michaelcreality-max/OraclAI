/**
 * ORACLE AI - Control Panel JavaScript
 * Real-time system management with authentication and API key management
 */

// Global state
const state = {
    apiKey: localStorage.getItem('oracle_api_key') || null,
    user: null,
    systemStatus: null,
    apiKeys: [],
    currentMode: 'training',
    lastUpdate: null,
    refreshInterval: null,
    safetyStatus: null
};

// API configuration
const API_BASE = '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    // Check if user is authenticated
    if (state.apiKey) {
        const valid = await verifyAuth();
        if (valid) {
            showDashboard();
            startRealTimeUpdates();
        } else {
            showLogin();
        }
    } else {
        showLogin();
    }
    
    // Setup mode toggle listener
    setupModeToggle();
    
    // Setup navigation
    setupNavigation();
}

// ==================== AUTHENTICATION ====================

function showLogin() {
    document.getElementById('login-modal').classList.add('active');
    document.getElementById('login-api-key').focus();
}

function hideLogin() {
    document.getElementById('login-modal').classList.remove('active');
}

async function authenticate() {
    const keyInput = document.getElementById('login-api-key');
    const key = keyInput.value.trim();
    
    if (!key) {
        showLoginError('Please enter an API key');
        return;
    }
    
    // Temporarily set key for verification
    state.apiKey = key;
    
    const valid = await verifyAuth();
    
    if (valid) {
        localStorage.setItem('oracle_api_key', key);
        hideLogin();
        showDashboard();
        startRealTimeUpdates();
        showToast('Login successful', 'success');
    } else {
        state.apiKey = null;
        showLoginError('Invalid API key');
    }
}

async function verifyAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/apikey/verify`, {
            headers: {
                'Authorization': `Bearer ${state.apiKey}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            state.user = data.api_key;
            updateUserPanel();
            return true;
        }
        return false;
    } catch (error) {
        console.error('Auth verification failed:', error);
        return false;
    }
}

function showLoginError(message) {
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function logout() {
    state.apiKey = null;
    state.user = null;
    localStorage.removeItem('oracle_api_key');
    
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
    }
    
    showLogin();
    showToast('Logged out', 'warning');
}

function updateUserPanel() {
    const panel = document.getElementById('user-panel');
    
    if (!state.user) {
        panel.innerHTML = `
            <button class="btn btn-primary" onclick="showLogin()">
                <i class="fas fa-sign-in-alt"></i> Login
            </button>
        `;
        return;
    }
    
    const isAdmin = state.user.role === 'admin';
    
    panel.innerHTML = `
        <div class="user-info">
            <span class="user-role ${state.user.role}">${state.user.role}</span>
            <span class="user-name">${state.user.name}</span>
        </div>
        <button class="btn btn-secondary" onclick="logout()">
            <i class="fas fa-sign-out-alt"></i> Logout
        </button>
    `;
    
    // Show/hide admin-only elements
    document.querySelectorAll('.admin-only').forEach(el => {
        el.classList.toggle('hidden', !isAdmin);
    });
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';
}

// ==================== DASHBOARD ====================

function showDashboard() {
    updateSystemStatus();
    loadSafetyStatus();
    loadApiKeys();
}

// ==================== REAL-TIME UPDATES ====================

function startRealTimeUpdates() {
    // Immediate update
    updateSystemStatus();
    loadSafetyStatus();
    
    // Periodic updates every 5 seconds
    state.refreshInterval = setInterval(() => {
        updateSystemStatus();
        loadSafetyStatus();
    }, 5000);
}

async function updateSystemStatus() {
    try {
        // Fetch health status
        const healthResponse = await fetch(`${API_BASE}/health`);
        const health = healthResponse.ok ? await healthResponse.json() : null;
        
        // Update status badge
        const statusBadge = document.getElementById('system-status');
        if (health && health.status === 'healthy') {
            statusBadge.className = 'status-badge online';
            statusBadge.textContent = 'Online';
        } else {
            statusBadge.className = 'status-badge offline';
            statusBadge.textContent = 'Offline';
        }
        
        // Update health indicator
        const healthStatus = document.getElementById('health-status');
        if (health && health.status === 'healthy') {
            healthStatus.innerHTML = `
                <span class="health-indicator healthy">
                    <i class="fas fa-check-circle"></i> Healthy
                </span>
            `;
        } else {
            healthStatus.innerHTML = `
                <span class="health-indicator unhealthy">
                    <i class="fas fa-times-circle"></i> Unhealthy
                </span>
            `;
        }
        
        // Update active sessions
        if (health) {
            document.getElementById('active-sessions').textContent = 
                health.active_sessions || 0;
        }
        
        // Update last update time
        state.lastUpdate = new Date();
        document.getElementById('last-update').textContent = 
            state.lastUpdate.toLocaleTimeString();
        
        // Update current mode display
        updateModeDisplay();
        
    } catch (error) {
        console.error('Failed to update system status:', error);
    }
}

// ==================== SAFETY STATUS ====================

async function loadSafetyStatus() {
    if (!state.apiKey) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/safety/status`, {
            headers: {
                'Authorization': `Bearer ${state.apiKey}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load safety status');
        }
        
        const data = await response.json();
        state.safetyStatus = data;
        state.currentMode = data.currentMode;
        renderSafetyStatus(data);
        
    } catch (error) {
        console.error('Load safety status failed:', error);
    }
}

function renderSafetyStatus(data) {
    // Update safety badge
    const badge = document.getElementById('safety-badge');
    const scoreEl = document.getElementById('safety-score');
    const execStatus = document.getElementById('execution-status');
    const checksContainer = document.getElementById('safety-checks');
    const recommendations = document.getElementById('safety-recommendations');
    const recList = document.getElementById('recommendations-list');
    const safeModeAlert = document.getElementById('safe-mode-alert');
    const safetyCard = document.querySelector('.safety-card');
    
    // Calculate passed checks
    const passedChecks = data.checks.filter(c => c.passed).length;
    const totalChecks = data.checks.length;
    
    // Update score
    scoreEl.textContent = `${passedChecks}/${totalChecks}`;
    
    // Update badge
    if (data.currentMode === 'safe') {
        badge.className = 'safety-badge safe-mode';
        badge.textContent = 'SAFE MODE';
        safetyCard.classList.add('safe');
        safetyCard.classList.remove('unsafe');
    } else if (data.executionAllowed) {
        badge.className = 'safety-badge ready';
        badge.textContent = 'Ready for Execution';
        safetyCard.classList.remove('safe', 'unsafe');
    } else {
        badge.className = 'safety-badge blocked';
        badge.textContent = 'Execution Blocked';
        safetyCard.classList.add('unsafe');
        safetyCard.classList.remove('safe');
    }
    
    // Update execution status text
    const statusText = execStatus.querySelector('.status-text');
    if (data.executionAllowed) {
        statusText.className = 'status-text allowed';
        statusText.textContent = 'Execution Allowed';
    } else {
        statusText.className = 'status-text blocked';
        statusText.textContent = 'Execution Blocked';
    }
    
    // Render checks
    checksContainer.innerHTML = data.checks.map(check => `
        <div class="safety-check ${check.passed ? 'passed' : 'failed'}">
            <div class="check-icon">
                <i class="fas ${check.passed ? 'fa-check' : 'fa-times'}"></i>
            </div>
            <div class="check-info">
                <div class="check-name">${escapeHtml(check.name)}</div>
                <div class="check-message">${escapeHtml(check.message)}</div>
            </div>
        </div>
    `).join('');
    
    // Show/hide recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        recList.innerHTML = data.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('');
        recommendations.classList.remove('hidden');
    } else {
        recommendations.classList.add('hidden');
    }
    
    // Show/hide safe mode alert
    if (data.currentMode === 'safe') {
        safeModeAlert.classList.remove('hidden');
        // Disable mode toggle
        const toggle = document.getElementById('mode-toggle');
        if (toggle) toggle.disabled = true;
    } else {
        safeModeAlert.classList.add('hidden');
        // Enable mode toggle for admins
        const toggle = document.getElementById('mode-toggle');
        if (toggle && state.user && state.user.role === 'admin') {
            toggle.disabled = false;
        }
    }
}

async function resetFromSafeMode() {
    if (!state.apiKey) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/safety/reset-safe-mode`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.apiKey}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to reset safe mode');
        }
        
        showToast('System reset to training mode', 'success');
        loadSafetyStatus();
        
    } catch (error) {
        showToast('Failed to reset: ' + error.message, 'error');
    }
}

// ==================== MODE SWITCH ====================

function setupModeToggle() {
    const toggle = document.getElementById('mode-toggle');
    
    toggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            // Switching to execution mode - show confirmation
            showExecutionConfirmModal();
            // Reset toggle until confirmed
            toggle.checked = false;
        } else {
            // Switching to training mode
            setMode('training');
        }
    });
}

function showExecutionConfirmModal() {
    document.getElementById('execution-confirm-modal').classList.add('active');
    document.getElementById('execution-confirm-input').value = '';
    document.getElementById('execution-confirm-input').focus();
    
    // Enable confirm button only when correct text entered
    document.getElementById('execution-confirm-input').addEventListener('input', (e) => {
        const btn = document.getElementById('btn-confirm-execution');
        btn.disabled = e.target.value !== 'EXECUTE';
    });
}

function confirmExecutionMode() {
    closeModal('execution-confirm-modal');
    setMode('execution');
}

async function setMode(mode) {
    try {
        // Call backend API with safety validation
        const response = await fetch(`${API_BASE}/api/mode/switch`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            // Show safety error
            showToast(data.error || 'Mode switch failed', 'error');
            
            // Reset toggle
            const toggle = document.getElementById('mode-toggle');
            toggle.checked = state.currentMode === 'execution';
            
            // Refresh safety status to show why it failed
            loadSafetyStatus();
            return;
        }
        
        // Update state
        state.currentMode = mode;
        
        // Update toggle state
        const toggle = document.getElementById('mode-toggle');
        toggle.checked = mode === 'execution';
        
        updateModeDisplay();
        loadSafetyStatus();
        
        showToast(
            mode === 'execution' 
                ? 'Execution mode enabled - Live trading active' 
                : mode === 'safe'
                ? 'Safe mode active - HOLD decisions only'
                : 'Training mode enabled - Safe environment',
            mode === 'execution' ? 'warning' : mode === 'safe' ? 'error' : 'success'
        );
        
    } catch (error) {
        showToast('Failed to change mode: ' + error.message, 'error');
        console.error('Mode change failed:', error);
        
        // Reset toggle on error
        const toggle = document.getElementById('mode-toggle');
        toggle.checked = state.currentMode === 'execution';
    }
}

function updateModeDisplay() {
    const modeDisplay = document.getElementById('current-mode');
    const mode = state.currentMode;
    
    let icon = 'fa-graduation-cap';
    let label = 'Training';
    let className = 'training';
    
    if (mode === 'execution') {
        icon = 'fa-rocket';
        label = 'Execution';
        className = 'execution';
    } else if (mode === 'safe') {
        icon = 'fa-shield-alt';
        label = 'Safe Mode';
        className = 'execution';  // Use execution styling for visibility
    }
    
    modeDisplay.innerHTML = `
        <span class="mode-indicator ${className}">
            <i class="fas ${icon}"></i>
            ${label}
        </span>
    `;
    
    // Update toggle without triggering event
    const toggle = document.getElementById('mode-toggle');
    toggle.checked = mode === 'execution';
}

// ==================== API KEY MANAGEMENT ====================

async function loadApiKeys() {
    if (!state.user || state.user.role !== 'admin') {
        return; // Only admins can view API keys
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/apikey/list?include_inactive=true`, {
            headers: {
                'Authorization': `Bearer ${state.apiKey}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load API keys');
        }
        
        const data = await response.json();
        state.apiKeys = data.keys || [];
        renderApiKeysTable();
        
    } catch (error) {
        showToast('Failed to load API keys', 'error');
        console.error('Load API keys failed:', error);
    }
}

function renderApiKeysTable() {
    const tbody = document.getElementById('api-keys-tbody');
    const emptyState = document.getElementById('api-keys-empty');
    
    if (state.apiKeys.length === 0) {
        tbody.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    tbody.innerHTML = state.apiKeys.map(key => {
        const created = new Date(key.created_at).toLocaleDateString();
        const lastUsed = key.last_used_at 
            ? new Date(key.last_used_at).toLocaleString() 
            : 'Never';
        
        return `
            <tr>
                <td>${escapeHtml(key.name)}</td>
                <td><span class="role-badge ${key.role}">${key.role}</span></td>
                <td>${created}</td>
                <td>${lastUsed}</td>
                <td>${key.request_count.toLocaleString()}</td>
                <td class="${key.is_active ? 'status-active' : 'status-revoked'}">
                    ${key.is_active ? 'Active' : 'Revoked'}
                </td>
                <td>
                    ${key.is_active ? `
                        <button class="btn-icon" onclick="showRevokeKeyModal('${key.id}', '${escapeHtml(key.name)}')" title="Revoke">
                            <i class="fas fa-ban"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function showGenerateKeyModal() {
    document.getElementById('generate-key-modal').classList.add('active');
    document.getElementById('key-name').value = '';
    document.getElementById('key-role').value = 'user';
    document.getElementById('key-rate-limit').value = '60';
    document.getElementById('key-name').focus();
}

async function generateKey() {
    const name = document.getElementById('key-name').value.trim();
    const role = document.getElementById('key-role').value;
    const rateLimit = parseInt(document.getElementById('key-rate-limit').value);
    
    if (!name) {
        showToast('Please enter a key name', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/apikey/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                role,
                rate_limit: rateLimit
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create key');
        }
        
        const data = await response.json();
        
        closeModal('generate-key-modal');
        
        // Show the new key
        document.getElementById('new-key-value').textContent = data.key;
        document.getElementById('new-key-modal').classList.add('active');
        
        showToast('API key generated successfully', 'success');
        
    } catch (error) {
        showToast(error.message, 'error');
        console.error('Generate key failed:', error);
    }
}

function copyNewKey() {
    const key = document.getElementById('new-key-value').textContent;
    navigator.clipboard.writeText(key).then(() => {
        showToast('Key copied to clipboard', 'success');
    }).catch(() => {
        showToast('Failed to copy key', 'error');
    });
}

let keyToRevoke = null;

function showRevokeKeyModal(keyId, keyName) {
    keyToRevoke = keyId;
    document.getElementById('revoke-key-name').textContent = keyName;
    document.getElementById('revoke-key-modal').classList.add('active');
}

async function confirmRevokeKey() {
    if (!keyToRevoke) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/apikey/revoke/${keyToRevoke}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.apiKey}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to revoke key');
        }
        
        closeModal('revoke-key-modal');
        showToast('API key revoked', 'warning');
        loadApiKeys();
        
    } catch (error) {
        showToast('Failed to revoke key', 'error');
        console.error('Revoke key failed:', error);
    }
    
    keyToRevoke = null;
}

// ==================== NAVIGATION ====================

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            
            // Update active state
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Scroll to section
            const sectionEl = document.getElementById(`${section}-section`);
            if (sectionEl) {
                sectionEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// ==================== MODALS ====================

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modals on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Close on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-times-circle' : 
                 type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==================== UTILITIES ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle enter key on login form
document.getElementById('login-api-key')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        authenticate();
    }
});

// Handle enter key on execution confirmation
document.getElementById('execution-confirm-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.target.value === 'EXECUTE') {
        confirmExecutionMode();
    }
});

// ==================== ADMIN AUTHENTICATION ====================

const adminState = {
    token: localStorage.getItem('oracle_admin_token') || null,
    email: null,
    requiresPasswordChange: false
};

function showAdminLogin() {
    document.getElementById('admin-login-modal').classList.add('active');
    document.getElementById('admin-password').focus();
}

function showApiKeyLogin() {
    document.getElementById('admin-login-modal').classList.remove('active');
    showLogin();
}

async function adminLogin() {
    const email = document.getElementById('admin-email').value.trim();
    const password = document.getElementById('admin-password').value;
    
    if (!email || !password) {
        showAdminLoginError('Email and password required');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            adminState.token = data.token;
            adminState.email = email;
            adminState.requiresPasswordChange = data.requires_password_change;
            localStorage.setItem('oracle_admin_token', data.token);
            
            document.getElementById('admin-login-modal').classList.remove('active');
            
            if (data.requires_password_change) {
                showPasswordChangeModal();
            } else {
                showAdminDashboard();
                showAdminNav();
                showToast('Admin login successful', 'success');
            }
        } else {
            showAdminLoginError(data.message || 'Login failed');
        }
    } catch (error) {
        showAdminLoginError('Login failed: ' + error.message);
    }
}

function showAdminLoginError(message) {
    const errorEl = document.getElementById('admin-login-error');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function showPasswordChangeModal() {
    document.getElementById('password-change-modal').classList.add('active');
}

async function changeAdminPassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (!currentPassword || !newPassword || !confirmPassword) {
        showPasswordChangeError('All fields required');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showPasswordChangeError('New passwords do not match');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                token: adminState.token,
                old_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showPasswordChangeSuccess('Password changed successfully');
            setTimeout(() => {
                document.getElementById('password-change-modal').classList.remove('active');
                showAdminDashboard();
                showAdminNav();
            }, 1500);
        } else {
            showPasswordChangeError(data.message || 'Failed to change password');
        }
    } catch (error) {
        showPasswordChangeError('Error: ' + error.message);
    }
}

function showPasswordChangeError(message) {
    const errorEl = document.getElementById('password-change-error');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

function showPasswordChangeSuccess(message) {
    const successEl = document.getElementById('password-change-success');
    successEl.textContent = message;
    successEl.classList.remove('hidden');
}

async function adminLogout() {
    if (adminState.token) {
        await fetch(`${API_BASE}/api/admin/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: adminState.token })
        });
    }
    
    adminState.token = null;
    adminState.email = null;
    localStorage.removeItem('oracle_admin_token');
    
    hideAdminNav();
    showLogin();
    showToast('Admin logged out', 'warning');
}

function showAdminNav() {
    document.getElementById('admin-nav-section').classList.remove('hidden');
}

function hideAdminNav() {
    document.getElementById('admin-nav-section').classList.add('hidden');
}

// ==================== ADMIN DASHBOARD ====================

function showAdminDashboard() {
    hideAllSections();
    document.getElementById('admin-dashboard-section').classList.remove('hidden');
    loadAdminDashboardData();
}

async function loadAdminDashboardData() {
    if (!adminState.token) return;
    
    try {
        // Load system state
        const response = await fetch(`${API_BASE}/api/admin/system/state`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.systemState) {
                document.getElementById('admin-active-debates').textContent = 
                    data.systemState.active_debates || 0;
            }
        }
    } catch (error) {
        console.error('Failed to load admin dashboard:', error);
    }
}

function showModeControl() {
    hideAllSections();
    document.getElementById('mode-control-section').classList.remove('hidden');
}

function showSystemConfig() {
    hideAllSections();
    document.getElementById('system-config-section').classList.remove('hidden');
    loadSystemConfig();
}

function hideAllSections() {
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('hidden');
    });
}

// ==================== SYSTEM CONFIG ====================

let currentConfig = {};

async function loadSystemConfig() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/config`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.config) {
                currentConfig = data.config;
                populateConfigForm(data.config);
            }
        }
    } catch (error) {
        showToast('Failed to load config', 'error');
    }
}

function populateConfigForm(config) {
    // Edge/Filter
    document.getElementById('cfg-edge-threshold').value = config.edge_threshold || 65;
    document.getElementById('cfg-max-edge-threshold').value = config.max_edge_threshold || 85;
    document.getElementById('cfg-min-confidence').value = config.min_confidence || 0.65;
    
    // Risk
    document.getElementById('cfg-max-position-risk').value = config.max_position_risk_percent || 2.0;
    document.getElementById('cfg-max-portfolio-risk').value = config.max_portfolio_risk_percent || 6.0;
    document.getElementById('cfg-max-sector-exposure').value = config.max_sector_exposure || 25.0;
    document.getElementById('cfg-max-single-position').value = config.max_single_position || 15.0;
    
    // Agents
    document.getElementById('cfg-agent-timeout').value = config.agent_timeout_seconds || 60;
    document.getElementById('cfg-debate-rounds').value = config.debate_rounds || 3;
    document.getElementById('cfg-min-agent-confidence').value = config.min_agent_confidence || 0.6;
    
    // System
    document.getElementById('cfg-log-level').value = config.log_level || 'INFO';
    document.getElementById('cfg-max-concurrent-debates').value = config.max_concurrent_debates || 10;
    document.getElementById('cfg-require-validation').checked = config.require_validation_for_execution !== false;
    document.getElementById('cfg-auto-fallback').checked = config.auto_fallback_on_anomaly !== false;
    document.getElementById('cfg-anomaly-threshold').value = config.anomaly_threshold || 0.7;
}

async function saveSystemConfig() {
    if (!adminState.token) {
        showToast('Admin authentication required', 'error');
        return;
    }
    
    const updates = {
        // Edge/Filter
        edge_threshold: parseFloat(document.getElementById('cfg-edge-threshold').value),
        max_edge_threshold: parseFloat(document.getElementById('cfg-max-edge-threshold').value),
        min_confidence: parseFloat(document.getElementById('cfg-min-confidence').value),
        
        // Risk
        max_position_risk_percent: parseFloat(document.getElementById('cfg-max-position-risk').value),
        max_portfolio_risk_percent: parseFloat(document.getElementById('cfg-max-portfolio-risk').value),
        max_sector_exposure: parseFloat(document.getElementById('cfg-max-sector-exposure').value),
        max_single_position: parseFloat(document.getElementById('cfg-max-single-position').value),
        
        // Agents
        agent_timeout_seconds: parseInt(document.getElementById('cfg-agent-timeout').value),
        debate_rounds: parseInt(document.getElementById('cfg-debate-rounds').value),
        min_agent_confidence: parseFloat(document.getElementById('cfg-min-agent-confidence').value),
        
        // System
        log_level: document.getElementById('cfg-log-level').value,
        max_concurrent_debates: parseInt(document.getElementById('cfg-max-concurrent-debates').value),
        require_validation_for_execution: document.getElementById('cfg-require-validation').checked,
        auto_fallback_on_anomaly: document.getElementById('cfg-auto-fallback').checked,
        anomaly_threshold: parseFloat(document.getElementById('cfg-anomaly-threshold').value)
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/config/update`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ updates })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Configuration saved successfully', 'success');
            document.getElementById('config-unsaved-warning').classList.add('hidden');
        } else {
            showToast(data.message || 'Failed to save config', 'error');
            if (data.errors) {
                console.error('Config errors:', data.errors);
            }
        }
    } catch (error) {
        showToast('Error saving config: ' + error.message, 'error');
    }
}

function resetConfigToDefaults() {
    if (confirm('Reset all configuration to defaults?')) {
        populateConfigForm({});
        showToast('Configuration reset to defaults (not saved yet)', 'warning');
    }
}

// Config tab switching
document.querySelectorAll('.config-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.config-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const tabId = tab.dataset.tab;
        document.querySelectorAll('.config-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`${tabId}-config`).classList.add('active');
    });
});

// Watch for config changes
document.querySelectorAll('#system-config-section input, #system-config-section select').forEach(input => {
    input.addEventListener('change', () => {
        document.getElementById('config-unsaved-warning').classList.remove('hidden');
    });
});

// ==================== SYSTEM MONITORING ====================

function showSystemMonitoring() {
    hideAllSections();
    document.getElementById('system-monitoring-section').classList.remove('hidden');
    loadSystemMetrics();
}

async function loadSystemMetrics() {
    if (!adminState.token) return;
    
    const hours = document.getElementById('metrics-time-range').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/metrics?hours=${hours}`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.metrics && data.metrics.length > 0) {
                const latest = data.metrics[0];
                document.getElementById('metric-cpu').textContent = `${latest.cpu_percent?.toFixed(1) || 0}%`;
                document.getElementById('metric-memory').textContent = `${latest.memory_percent?.toFixed(1) || 0}%`;
                document.getElementById('metric-debates').textContent = latest.active_debates || 0;
                document.getElementById('metric-response').textContent = `${latest.avg_response_time?.toFixed(0) || 0}ms`;
            }
        }
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

function loadSystemLogs() {
    // Placeholder for log loading
    showToast('System logs loaded', 'success');
}

function refreshSystemMetrics() {
    loadSystemMetrics();
    showToast('Metrics refreshed', 'success');
}

// ==================== AGENT CONTROL ====================

function showAgentControl() {
    hideAllSections();
    document.getElementById('agent-control-section').classList.remove('hidden');
    loadAgentStatus();
}

async function loadAgentStatus() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/agents`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderAgentCards(data.agents || []);
        }
    } catch (error) {
        console.error('Failed to load agent status:', error);
    }
}

function renderAgentCards(agents) {
    const container = document.getElementById('agents-grid');
    
    if (agents.length === 0) {
        container.innerHTML = '<p class="empty-state">No agent data available</p>';
        return;
    }
    
    container.innerHTML = agents.map(agent => `
        <div class="agent-card ${agent.is_enabled ? 'enabled' : 'disabled'}">
            <h4>
                <i class="fas fa-robot"></i>
                ${escapeHtml(agent.agent_name || agent.agent_id)}
            </h4>
            <span class="status ${agent.is_enabled ? 'enabled' : 'disabled'}">
                ${agent.is_enabled ? 'ENABLED' : 'DISABLED'}
            </span>
            <div class="agent-stats">
                <div>Success Rate: ${(agent.success_rate || 0).toFixed(1)}%</div>
                <div>Error Count: ${agent.error_count || 0}</div>
                <div>Avg Response: ${(agent.avg_response_time || 0).toFixed(0)}ms</div>
            </div>
            <button class="btn ${agent.is_enabled ? 'btn-danger' : 'btn-primary'}" 
                    onclick="toggleAgent('${agent.agent_id}', ${!agent.is_enabled})">
                ${agent.is_enabled ? 'Disable' : 'Enable'}
            </button>
        </div>
    `).join('');
}

async function toggleAgent(agentId, enable) {
    if (!adminState.token) return;
    
    try {
        const endpoint = enable ? 'enable' : 'disable';
        const response = await fetch(`${API_BASE}/api/admin/agents/${agentId}/${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Agent ${enable ? 'enabled' : 'disabled'}`, 'success');
            loadAgentStatus();
        } else {
            showToast(data.message || 'Failed to toggle agent', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ==================== AUDIT LOG ====================

function showAuditLog() {
    hideAllSections();
    document.getElementById('audit-log-section').classList.remove('hidden');
    loadAuditLog();
}

async function loadAuditLog() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/audit-log?limit=100`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.logs) {
                renderAuditLog(data.logs);
            }
        }
    } catch (error) {
        console.error('Failed to load audit log:', error);
    }
}

function renderAuditLog(logs) {
    const tbody = document.getElementById('audit-log-tbody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No audit entries</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${new Date(log.timestamp).toLocaleString()}</td>
            <td>${escapeHtml(log.admin_id || 'System')}</td>
            <td><span class="badge ${getActionBadgeClass(log.action)}">${escapeHtml(log.action)}</span></td>
            <td>${escapeHtml(log.details || '-')}</td>
            <td>${escapeHtml(log.ip_address || '-')}</td>
        </tr>
    `).join('');
}

function getActionBadgeClass(action) {
    if (action.includes('LOGIN')) return 'success';
    if (action.includes('FAILED')) return 'danger';
    if (action.includes('CONFIG')) return 'warning';
    if (action.includes('MODE')) return 'primary';
    return 'secondary';
}

// ==================== EMERGENCY CONTROLS ====================

async function triggerSafeMode() {
    if (!confirm('EMERGENCY: This will immediately switch to SAFE MODE. All trading will be halted. Continue?')) {
        return;
    }
    
    if (!adminState.token) {
        showToast('Admin authentication required', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/mode/switch`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: 'safe',
                reason: 'Emergency safe mode triggered from admin panel'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('EMERGENCY SAFE MODE ACTIVATED', 'error');
            loadSafetyStatus();
        } else {
            showToast('Failed to trigger safe mode: ' + data.message, 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Update navigation to support admin sections
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            
            // Update active state
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Handle admin sections
            switch(section) {
                case 'admin-dashboard':
                    showAdminDashboard();
                    break;
                case 'system-config':
                    showSystemConfig();
                    break;
                case 'system-monitoring':
                    showSystemMonitoring();
                    break;
                case 'agent-control':
                    showAgentControl();
                    break;
                case 'audit-log':
                    showAuditLog();
                    break;
                case 'overview':
                    hideAllSections();
                    document.querySelectorAll('.status-card, .safety-card').forEach(el => el.classList.remove('hidden'));
                    break;
                case 'api-keys':
                    hideAllSections();
                    document.getElementById('api-keys-section').classList.remove('hidden');
                    break;
                case 'mode-control':
                    showModeControl();
                    break;
            }
        });
    });
}

// Check for existing admin session on load
async function checkAdminSession() {
    const token = localStorage.getItem('oracle_admin_token');
    if (token) {
        try {
            const response = await fetch(`${API_BASE}/api/admin/verify`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const data = await response.json();
            
            if (data.valid) {
                adminState.token = token;
                adminState.email = data.email;
                adminState.requiresPasswordChange = data.requires_password_change;
                
                if (data.requires_password_change) {
                    showPasswordChangeModal();
                } else {
                    showAdminNav();
                }
            } else {
                localStorage.removeItem('oracle_admin_token');
            }
        } catch (error) {
            console.error('Failed to verify admin session:', error);
        }
    }
}

// Call checkAdminSession during init
checkAdminSession();

// ==================== CODE EDITOR ====================

let monacoEditor = null;
let openFiles = new Map();
let currentFile = null;
let fileTreeData = null;

function showCodeEditor() {
    hideAllSections();
    document.getElementById('code-editor-section').classList.remove('hidden');
    loadFileTree();
    initMonacoEditor();
}

function initMonacoEditor() {
    if (monacoEditor) return;
    
    require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' }});
    
    require(['vs/editor/editor.main'], function() {
        const container = document.getElementById('monaco-editor-container');
        container.innerHTML = '';
        
        monacoEditor = monaco.editor.create(container, {
            value: '',
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: true },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            roundedSelection: false,
            padding: { top: 16 }
        });
        
        monacoEditor.onDidChangeModelContent(() => {
            if (currentFile) {
                document.getElementById('btn-save-file').disabled = false;
                updateTabModified(currentFile, true);
            }
        });
        
        monacoEditor.onDidChangeCursorPosition((e) => {
            document.getElementById('editor-line-col').textContent = `Ln ${e.position.lineNumber}, Col ${e.position.column}`;
        });
    });
}

async function loadFileTree() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/files/tree`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                fileTreeData = data.tree;
                renderFileTree(fileTreeData, document.getElementById('file-tree'));
            }
        }
    } catch (error) {
        console.error('Failed to load file tree:', error);
        showToast('Failed to load file tree', 'error');
    }
}

function renderFileTree(node, container, level = 0) {
    if (!node) return;
    
    const item = document.createElement('div');
    item.className = `file-tree-item ${node.type}`;
    item.style.paddingLeft = `${8 + level * 12}px`;
    
    if (node.type === 'directory') {
        const isExpanded = level < 2;
        item.innerHTML = `
            <i class="fas fa-chevron-${isExpanded ? 'down' : 'right'} folder-toggle"></i>
            <i class="fas fa-folder${isExpanded ? '-open' : ''} folder-icon"></i>
            <span>${escapeHtml(node.name)}</span>
        `;
        
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const children = item.nextElementSibling;
            if (children && children.classList.contains('file-tree-children')) {
                const isVisible = children.style.display !== 'none';
                children.style.display = isVisible ? 'none' : 'block';
                const toggle = item.querySelector('.folder-toggle');
                const icon = item.querySelector('.folder-icon');
                toggle.className = `fas fa-chevron-${isVisible ? 'right' : 'down'} folder-toggle`;
                icon.className = `fas fa-folder${isVisible ? '' : '-open'} folder-icon`;
            }
        });
        
        container.appendChild(item);
        
        if (node.children && node.children.length > 0) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'file-tree-children';
            childrenContainer.style.display = isExpanded ? 'block' : 'none';
            
            node.children.forEach(child => {
                renderFileTree(child, childrenContainer, level + 1);
            });
            
            container.appendChild(childrenContainer);
        }
    } else {
        const ext = node.extension || '';
        const icon = getFileIcon(ext);
        
        item.innerHTML = `
            <i class="${icon} file-icon"></i>
            <span>${escapeHtml(node.name)}</span>
        `;
        
        if (!node.editable) {
            item.style.opacity = '0.5';
            item.title = 'Not editable';
        }
        
        item.addEventListener('click', () => {
            console.log('File clicked:', node.name, 'editable:', node.editable, 'path:', node.path);
            if (node.editable) {
                document.querySelectorAll('.file-tree-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                openFile(node.path);
            } else {
                console.log('File not editable:', node.name);
            }
        });
        
        container.appendChild(item);
    }
}

function getFileIcon(extension) {
    const iconMap = {
        '.py': 'fab fa-python',
        '.js': 'fab fa-js',
        '.html': 'fab fa-html5',
        '.css': 'fab fa-css3',
        '.json': 'fas fa-cog',
        '.md': 'fas fa-file-alt',
        '.txt': 'fas fa-file-alt',
        '.sql': 'fas fa-database',
        '.yml': 'fas fa-cog',
        '.yaml': 'fas fa-cog'
    };
    return iconMap[extension] || 'fas fa-file-code';
}

async function openFile(filePath) {
    if (!adminState.token) {
        console.log('No admin token, cannot open file');
        return;
    }
    
    console.log('Opening file:', filePath);
    
    if (openFiles.has(filePath)) {
        console.log('File already open, switching to tab');
        switchToTab(filePath);
        return;
    }
    
    try {
        const encodedPath = encodeURIComponent(filePath);
        const url = `${API_BASE}/api/admin/files/read?path=${encodedPath}`;
        console.log('Fetching:', url);
        
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        console.log('File data received:', data.success, data.error || 'OK');
        
        if (data.success) {
            openFiles.set(filePath, {
                content: data.content,
                modified: false,
                language: data.language
            });
            
            addEditorTab(filePath, data.language);
            switchToTab(filePath);
        } else {
            console.error('Failed to open file:', data.error);
            showToast(data.error || 'Failed to open file', 'error');
        }
    } catch (error) {
        console.error('Error opening file:', error);
        showToast('Error opening file: ' + error.message, 'error');
    }
}

function addEditorTab(filePath, language) {
    const tabsContainer = document.getElementById('editor-tabs');
    const fileName = filePath.split('/').pop();
    
    // Create unique ID for the tab based on path
    const tabId = 'tab-' + btoa(filePath).replace(/[^a-zA-Z0-9]/g, '');
    
    // Check if tab already exists
    if (document.getElementById(tabId)) {
        return;
    }
    
    const tab = document.createElement('div');
    tab.className = 'editor-tab';
    tab.id = tabId;
    tab.dataset.path = filePath;
    tab.innerHTML = `
        <span>${escapeHtml(fileName)}</span>
        <i class="fas fa-times close-btn" data-path="${escapeHtml(filePath)}"></i>
    `;
    
    // Add click handler for close button
    const closeBtn = tab.querySelector('.close-btn');
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeTab(filePath);
    });
    
    tab.addEventListener('click', (e) => {
        if (!e.target.classList.contains('close-btn')) {
            switchToTab(filePath);
        }
    });
    
    tabsContainer.appendChild(tab);
}

function switchToTab(filePath) {
    if (!openFiles.has(filePath)) return;
    
    currentFile = filePath;
    const file = openFiles.get(filePath);
    
    document.querySelectorAll('.editor-tab').forEach(t => t.classList.remove('active'));
    
    // Find tab by data-path attribute safely
    const tabs = document.querySelectorAll('.editor-tab');
    for (const tab of tabs) {
        if (tab.dataset.path === filePath) {
            tab.classList.add('active');
            break;
        }
    }
    
    if (monacoEditor) {
        monacoEditor.setValue(file.content);
        monaco.setModelLanguage(monacoEditor.getModel(), file.language || 'plaintext');
    }
    
    document.getElementById('editor-file-path').textContent = filePath;
    document.getElementById('editor-language').textContent = file.language || 'plaintext';
    document.getElementById('btn-save-file').disabled = !file.modified;
}

function closeTab(filePath) {
    const file = openFiles.get(filePath);
    if (file && file.modified) {
        if (!confirm('File has unsaved changes. Close anyway?')) {
            return;
        }
    }
    
    openFiles.delete(filePath);
    
    // Find and remove tab by data-path
    const tabs = document.querySelectorAll('.editor-tab');
    for (const tab of tabs) {
        if (tab.dataset.path === filePath) {
            tab.remove();
            break;
        }
    }
    
    if (currentFile === filePath) {
        const remaining = Array.from(openFiles.keys());
        if (remaining.length > 0) {
            switchToTab(remaining[0]);
        } else {
            currentFile = null;
            if (monacoEditor) monacoEditor.setValue('');
            document.getElementById('editor-file-path').textContent = 'No file open';
            document.getElementById('btn-save-file').disabled = true;
        }
    }
}

function updateTabModified(filePath, modified) {
    const file = openFiles.get(filePath);
    if (file) file.modified = modified;
    
    // Find tab by data-path safely
    const tabs = document.querySelectorAll('.editor-tab');
    for (const tab of tabs) {
        if (tab.dataset.path === filePath) {
            const nameSpan = tab.querySelector('span');
            const currentName = nameSpan.textContent;
            if (modified && !currentName.startsWith('●')) {
                nameSpan.textContent = '● ' + currentName;
            } else if (!modified && currentName.startsWith('●')) {
                nameSpan.textContent = currentName.substring(2);
            }
            break;
        }
    }
}

async function saveCurrentFile() {
    if (!currentFile || !monacoEditor || !adminState.token) return;
    
    const content = monacoEditor.getValue();
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/files/write`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentFile,
                content: content
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const file = openFiles.get(currentFile);
            if (file) {
                file.content = content;
                file.modified = false;
            }
            updateTabModified(currentFile, false);
            document.getElementById('btn-save-file').disabled = true;
            showToast('File saved successfully', 'success');
        } else {
            showToast(data.error || 'Failed to save file', 'error');
        }
    } catch (error) {
        showToast('Error saving file', 'error');
    }
}

async function refreshFileTree() {
    await loadFileTree();
    showToast('File tree refreshed', 'success');
}

function createNewFile() {
    const fileName = prompt('Enter file name (with extension):');
    if (!fileName) return;
    
    const currentPath = currentFile ? currentFile.substring(0, currentFile.lastIndexOf('/')) : '';
    const newPath = currentPath ? `${currentPath}/${fileName}` : fileName;
    
    saveNewFile(newPath, '');
}

function createNewFolder() {
    const folderName = prompt('Enter folder name:');
    if (!folderName) return;
    
    const currentPath = currentFile ? currentFile.substring(0, currentFile.lastIndexOf('/')) : '';
    const newPath = currentPath ? `${currentPath}/${folderName}` : folderName;
    
    createDirectory(newPath);
}

async function saveNewFile(path, content) {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/files/write`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path, content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('File created', 'success');
            refreshFileTree();
            openFile(path);
        } else {
            showToast(data.error || 'Failed to create file', 'error');
        }
    } catch (error) {
        showToast('Error creating file', 'error');
    }
}

async function createDirectory(path) {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/files/mkdir`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Directory created', 'success');
            refreshFileTree();
        } else {
            showToast(data.error || 'Failed to create directory', 'error');
        }
    } catch (error) {
        showToast('Error creating directory', 'error');
    }
}

async function reloadBackend() {
    if (!adminState.token) {
        showToast('Admin authentication required', 'error');
        return;
    }
    
    if (!confirm('Reload backend? This will clear module cache. Unsaved changes may be lost.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/files/reload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ soft_reload: true })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message || 'Backend reloaded', 'success');
        } else {
            showToast(data.error || 'Reload failed', 'error');
        }
    } catch (error) {
        showToast('Error reloading backend', 'error');
    }
}

function searchFiles() {
    const query = document.getElementById('file-search').value.toLowerCase();
    const treeItems = document.querySelectorAll('.file-tree-item');
    
    treeItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(query)) {
            item.style.display = 'flex';
            let parent = item.parentElement;
            while (parent && parent.classList.contains('file-tree-children')) {
                parent.style.display = 'block';
                parent = parent.parentElement;
            }
        } else {
            item.style.display = 'none';
        }
    });
}

// Update navigation handler to include code editor
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        const section = item.dataset.section;
        
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        
        switch(section) {
            case 'admin-dashboard':
                showAdminDashboard();
                break;
            case 'system-config':
                showSystemConfig();
                break;
            case 'system-monitoring':
                showSystemMonitoring();
                break;
            case 'agent-control':
                showAgentControl();
                break;
            case 'system-modification':
                showSystemModification();
                break;
            case 'audit-log':
                showAuditLog();
                break;
            case 'code-editor':
                showCodeEditor();
                break;
            case 'overview':
                hideAllSections();
                document.querySelectorAll('.status-card, .safety-card').forEach(el => el.classList.remove('hidden'));
                break;
            case 'api-keys':
                hideAllSections();
                document.getElementById('api-keys-section').classList.remove('hidden');
                break;
            case 'mode-control':
                showModeControl();
                break;
        }
    });
});

// ==================== WINDSURF AGENT CONTROL ====================

let currentAgentResult = null;

function showAgentControl() {
    hideAllSections();
    document.getElementById('agent-control-section').classList.remove('hidden');
    loadAgentStatus();
    loadAgentHistory();
}

async function loadAgentStatus() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/agents/status`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update stats
            const agents = data.agents || [];
            const registered = agents.filter(a => a.registered).length;
            const activeExecutions = agents.reduce((sum, a) => sum + (a.active_executions || 0), 0);
            
            document.getElementById('total-agents').textContent = agents.length;
            document.getElementById('registered-agents').textContent = registered;
            document.getElementById('active-executions').textContent = activeExecutions;
            document.getElementById('total-executions').textContent = data.total_history || 0;
            
            // Render agents grid
            renderAgentsGrid(agents);
        }
    } catch (error) {
        console.error('Failed to load agent status:', error);
        showToast('Failed to load agent status', 'error');
    }
}

function renderAgentsGrid(agents) {
    const grid = document.getElementById('agents-grid');
    grid.innerHTML = '';
    
    const agentDescriptions = {
        'windsurf_analyst': 'Performs deep market analysis and generates insights',
        'windsurf_researcher': 'Conducts comprehensive research on stocks and markets',
        'windsurf_trader': 'Makes trading decisions with high confidence threshold',
        'windsurf_risk_manager': 'Assesses portfolio and position risk levels'
    };
    
    agents.forEach(agent => {
        const card = document.createElement('div');
        card.className = `agent-card ${agent.registered ? 'registered' : 'unregistered'}`;
        
        const statusIcon = agent.registered ? 'fa-check-circle' : 'fa-times-circle';
        const statusClass = agent.registered ? 'success' : 'error';
        
        card.innerHTML = `
            <div class="agent-header">
                <i class="fas fa-robot"></i>
                <span class="agent-status ${statusClass}">
                    <i class="fas ${statusIcon}"></i>
                </span>
            </div>
            <h4>${agent.agent_id}</h4>
            <p class="agent-type">${agent.agent_type}</p>
            <p class="agent-description">${agentDescriptions[agent.agent_id] || 'Windsurf AI agent'}</p>
            <div class="agent-actions">
                <button class="btn btn-primary btn-sm" onclick="quickRunAgent('${agent.agent_id}')" ${!agent.registered ? 'disabled' : ''}>
                    <i class="fas fa-play"></i> Run
                </button>
                <button class="btn btn-secondary btn-sm" onclick="showAgentConfig('${agent.agent_id}')">
                    <i class="fas fa-cog"></i> Config
                </button>
            </div>
            <div class="agent-meta">
                <span><i class="fas fa-running"></i> ${agent.active_executions} active</span>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

async function loadAgentHistory() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/agents/history?limit=50`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderAgentHistory(data.history || []);
        }
    } catch (error) {
        console.error('Failed to load agent history:', error);
    }
}

function renderAgentHistory(history) {
    const tbody = document.getElementById('agent-history-tbody');
    tbody.innerHTML = '';
    
    history.slice().reverse().forEach(record => {
        const row = document.createElement('tr');
        const req = record.request || {};
        const resp = record.response || {};
        
        const decisionClass = (resp.decision || '').toLowerCase();
        const statusClass = (resp.state || '').toLowerCase();
        
        row.innerHTML = `
            <td>${new Date(record.start_time).toLocaleTimeString()}</td>
            <td>${req.agent_id || '-'}</td>
            <td>${req.task ? req.task.substring(0, 30) + '...' : '-'}</td>
            <td><span class="badge ${decisionClass}">${resp.decision || '-'}</span></td>
            <td>${resp.confidence ? (resp.confidence * 100).toFixed(1) + '%' : '-'}</td>
            <td><span class="status ${statusClass}">${resp.state || '-'}</span></td>
            <td>${record.duration ? record.duration.toFixed(1) + 's' : '-'}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewAgentResult('${record.record_id}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function showRunAgentModal() {
    document.getElementById('run-agent-id').value = '';
    document.getElementById('run-agent-task').value = '';
    document.getElementById('run-agent-symbol').value = '';
    document.getElementById('run-agent-context').value = '';
    showModal('run-agent-modal');
}

async function runAgent() {
    const agentId = document.getElementById('run-agent-id').value;
    const task = document.getElementById('run-agent-task').value;
    const symbol = document.getElementById('run-agent-symbol').value;
    const priority = parseInt(document.getElementById('run-agent-priority').value);
    const contextStr = document.getElementById('run-agent-context').value;
    
    if (!agentId) {
        showToast('Please select an agent', 'error');
        return;
    }
    
    if (!task) {
        showToast('Please enter a task description', 'error');
        return;
    }
    
    let context = {};
    if (contextStr) {
        try {
            context = JSON.parse(contextStr);
        } catch (e) {
            showToast('Invalid JSON in context field', 'error');
            return;
        }
    }
    
    closeModal('run-agent-modal');
    showToast('Running agent...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/agents/run`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: agentId,
                task: task,
                symbol: symbol || null,
                context: context,
                priority: priority
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAgentResult = data;
            showAgentResult(data);
            loadAgentHistory();
            loadAgentStatus();
            showToast('Agent execution completed', 'success');
        } else {
            showToast(data.error || 'Agent execution failed', 'error');
        }
    } catch (error) {
        console.error('Agent run failed:', error);
        showToast('Failed to run agent: ' + error.message, 'error');
    }
}

function quickRunAgent(agentId) {
    document.getElementById('run-agent-id').value = agentId;
    document.getElementById('run-agent-task').value = '';
    document.getElementById('run-agent-symbol').value = '';
    showModal('run-agent-modal');
}

function showAgentResult(result) {
    const decision = result.decision || 'HOLD';
    const confidence = result.confidence || 0;
    
    // Update badge
    const badge = document.getElementById('result-decision-badge');
    badge.textContent = decision.toUpperCase();
    badge.className = `result-badge ${decision.toLowerCase()}`;
    
    // Update confidence bar
    document.getElementById('result-confidence-bar').style.width = `${confidence * 100}%`;
    document.getElementById('result-confidence-value').textContent = `${(confidence * 100).toFixed(1)}%`;
    
    // Update reasoning
    document.getElementById('result-reasoning').textContent = result.reasoning || 'No reasoning provided';
    
    // Update internal state
    document.getElementById('result-internal-state').textContent = 
        JSON.stringify(result.internal_state || {}, null, 2);
    
    // Update logs
    const logsContainer = document.getElementById('result-logs');
    logsContainer.innerHTML = (result.logs || []).map(log => 
        `<div class="log-entry">${escapeHtml(log)}</div>`
    ).join('');
    
    // Update warnings
    const warningsSection = document.getElementById('result-warnings-section');
    const warningsList = document.getElementById('result-warnings');
    if (result.warnings && result.warnings.length > 0) {
        warningsSection.classList.remove('hidden');
        warningsList.innerHTML = result.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('');
    } else {
        warningsSection.classList.add('hidden');
    }
    
    // Update errors
    const errorsSection = document.getElementById('result-errors-section');
    const errorsList = document.getElementById('result-errors');
    if (result.errors && result.errors.length > 0) {
        errorsSection.classList.remove('hidden');
        errorsList.innerHTML = result.errors.map(e => `<li>${escapeHtml(e)}</li>`).join('');
    } else {
        errorsSection.classList.add('hidden');
    }
    
    showModal('agent-result-modal');
}

function viewAgentResult(recordId) {
    // Find in history
    // This would need to fetch or store history locally
    showToast('Loading execution details...', 'info');
}

function rerunAgent() {
    if (!currentAgentResult) return;
    
    document.getElementById('run-agent-id').value = currentAgentResult.agent_id;
    document.getElementById('run-agent-task').value = '';
    document.getElementById('run-agent-symbol').value = '';
    
    closeModal('agent-result-modal');
    showModal('run-agent-modal');
}

async function showAgentConfig(agentId) {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/agents/status?agent_id=${agentId}`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success && data.config) {
            const config = data.config;
            document.getElementById('config-agent-id').value = agentId;
            document.getElementById('config-max-iterations').value = config.max_iterations;
            document.getElementById('config-timeout').value = config.timeout_seconds;
            document.getElementById('config-confidence-threshold').value = config.confidence_threshold;
            document.getElementById('config-auto-approve').value = config.auto_approve_confidence;
            document.getElementById('config-loop-detection').checked = config.enable_loop_detection;
            
            showModal('agent-config-modal');
        }
    } catch (error) {
        console.error('Failed to load agent config:', error);
        showToast('Failed to load configuration', 'error');
    }
}

async function saveAgentConfig() {
    const agentId = document.getElementById('config-agent-id').value;
    
    const config = {
        max_iterations: parseInt(document.getElementById('config-max-iterations').value),
        timeout_seconds: parseFloat(document.getElementById('config-timeout').value),
        confidence_threshold: parseFloat(document.getElementById('config-confidence-threshold').value),
        auto_approve_confidence: parseFloat(document.getElementById('config-auto-approve').value),
        enable_loop_detection: document.getElementById('config-loop-detection').checked
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/agents/config/update`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: agentId,
                config: config
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeModal('agent-config-modal');
            showToast('Configuration saved', 'success');
            loadAgentStatus();
        } else {
            showToast(data.error || 'Failed to save configuration', 'error');
        }
    } catch (error) {
        console.error('Failed to save config:', error);
        showToast('Failed to save configuration', 'error');
    }
}

function refreshAgentStatus() {
    loadAgentStatus();
    loadAgentHistory();
    showToast('Agent status refreshed', 'success');
}

// ==================== END WINDSURF AGENT CONTROL ====================

// ==================== SYSTEM SELF-MODIFICATION ====================

let currentChangeId = null;
let validatedPatchData = null;

function showSystemModification() {
    hideAllSections();
    document.getElementById('system-modification-section').classList.remove('hidden');
    refreshModificationStatus();
    loadParameters();
    loadChangeHistory();
}

async function refreshModificationStatus() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/system/status`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const status = data.status;
            document.getElementById('mod-total-changes').textContent = status.total_changes || 0;
            document.getElementById('mod-applied-changes').textContent = status.applied_changes || 0;
            document.getElementById('mod-rollback-available').textContent = status.rollback_available_count || 0;
            document.getElementById('mod-live-params').textContent = status.live_parameters_count || 0;
        }
    } catch (error) {
        console.error('Failed to load modification status:', error);
    }
}

async function loadParameters() {
    if (!adminState.token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/system/parameters`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderParameters(data.parameters);
        }
    } catch (error) {
        console.error('Failed to load parameters:', error);
    }
}

function renderParameters(parameters) {
    const container = document.getElementById('parameters-list');
    container.innerHTML = '';
    
    if (Object.keys(parameters).length === 0) {
        container.innerHTML = '<p class="empty-state">No live parameters registered</p>';
        return;
    }
    
    Object.entries(parameters).forEach(([name, param]) => {
        const card = document.createElement('div');
        card.className = 'parameter-card';
        
        const rangeText = [];
        if (param.min_value !== null && param.min_value !== undefined) {
            rangeText.push(`min: ${param.min_value}`);
        }
        if (param.max_value !== null && param.max_value !== undefined) {
            rangeText.push(`max: ${param.max_value}`);
        }
        
        card.innerHTML = `
            <div class="parameter-header">
                <h4>${name}</h4>
                <span class="param-category">${param.category}</span>
            </div>
            <div class="parameter-value">
                <span class="value">${JSON.stringify(param.value)}</span>
                ${param.requires_restart ? '<span class="restart-badge"><i class="fas fa-sync"></i> Restart</span>' : ''}
            </div>
            <p class="parameter-desc">${param.description || 'No description'}</p>
            <div class="parameter-meta">
                ${rangeText.length > 0 ? `<span class="range">${rangeText.join(', ')}</span>` : ''}
                <span class="updated">Updated ${param.change_count} times</span>
            </div>
            <div class="parameter-actions">
                <button class="btn btn-primary btn-sm" onclick="editParameter('${name}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

function editParameter(name) {
    const params = document.querySelectorAll('.parameter-card');
    let paramData = null;
    
    // Find parameter data from the DOM
    params.forEach(card => {
        const h4 = card.querySelector('h4');
        if (h4 && h4.textContent === name) {
            const valueSpan = card.querySelector('.value');
            const descP = card.querySelector('.parameter-desc');
            const rangeSpan = card.querySelector('.range');
            const restartBadge = card.querySelector('.restart-badge');
            
            paramData = {
                name: name,
                value: valueSpan ? valueSpan.textContent : '',
                description: descP ? descP.textContent : '',
                range: rangeSpan ? rangeSpan.textContent : '',
                requires_restart: !!restartBadge
            };
        }
    });
    
    if (!paramData) return;
    
    document.getElementById('edit-param-name').value = name;
    document.getElementById('edit-param-display-name').value = name;
    document.getElementById('edit-param-current-value').value = paramData.value;
    document.getElementById('edit-param-new-value').value = '';
    document.getElementById('edit-param-reason').value = '';
    document.getElementById('edit-param-help').textContent = paramData.range || '';
    
    const restartWarning = document.getElementById('edit-param-restart-warning');
    restartWarning.style.display = paramData.requires_restart ? 'block' : 'none';
    
    showModal('edit-parameter-modal');
}

async function saveParameterChange() {
    const name = document.getElementById('edit-param-name').value;
    const newValueStr = document.getElementById('edit-param-new-value').value;
    const reason = document.getElementById('edit-param-reason').value.trim();
    
    if (!newValueStr) {
        showToast('Please enter a new value', 'error');
        return;
    }
    
    if (!reason) {
        showToast('Please provide a reason for the change', 'error');
        return;
    }
    
    // Try to parse as JSON, fallback to string
    let newValue;
    try {
        newValue = JSON.parse(newValueStr);
    } catch {
        newValue = newValueStr;
    }
    
    closeModal('edit-parameter-modal');
    showToast('Updating parameter...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/system/parameters/${name}/update`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                value: newValue,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Parameter updated successfully', 'success');
            if (data.requires_restart) {
                showToast('System restart required for changes to take effect', 'warning');
            }
            loadParameters();
            refreshModificationStatus();
        } else {
            showToast(data.error || 'Failed to update parameter', 'error');
        }
    } catch (error) {
        console.error('Failed to update parameter:', error);
        showToast('Failed to update parameter', 'error');
    }
}

function showRegisterParameterModal() {
    document.getElementById('reg-param-name').value = '';
    document.getElementById('reg-param-default').value = '';
    document.getElementById('reg-param-desc').value = '';
    document.getElementById('reg-param-category').value = 'general';
    document.getElementById('reg-param-min').value = '';
    document.getElementById('reg-param-max').value = '';
    document.getElementById('reg-param-restart').checked = false;
    
    showModal('register-parameter-modal');
}

async function registerNewParameter() {
    const name = document.getElementById('reg-param-name').value.trim();
    const defaultValueStr = document.getElementById('reg-param-default').value;
    const description = document.getElementById('reg-param-desc').value.trim();
    const category = document.getElementById('reg-param-category').value;
    const minValue = document.getElementById('reg-param-min').value;
    const maxValue = document.getElementById('reg-param-max').value;
    const requiresRestart = document.getElementById('reg-param-restart').checked;
    
    if (!name) {
        showToast('Parameter name is required', 'error');
        return;
    }
    
    // Parse default value
    let defaultValue;
    try {
        defaultValue = JSON.parse(defaultValueStr);
    } catch {
        defaultValue = defaultValueStr;
    }
    
    const payload = {
        name: name,
        default_value: defaultValue,
        description: description,
        category: category,
        requires_restart: requiresRestart
    };
    
    if (minValue) payload.min_value = parseFloat(minValue);
    if (maxValue) payload.max_value = parseFloat(maxValue);
    
    closeModal('register-parameter-modal');
    showToast('Registering parameter...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/system/parameters/register`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Parameter registered successfully', 'success');
            loadParameters();
        } else {
            showToast(data.error || 'Failed to register parameter', 'error');
        }
    } catch (error) {
        console.error('Failed to register parameter:', error);
        showToast('Failed to register parameter', 'error');
    }
}

async function loadChangeHistory() {
    if (!adminState.token) return;
    
    const typeFilter = document.getElementById('history-type-filter').value;
    const statusFilter = document.getElementById('history-status-filter').value;
    
    let url = `${API_BASE}/api/system/changes?limit=50`;
    if (typeFilter) url += `&type=${typeFilter}`;
    if (statusFilter) url += `&status=${statusFilter}`;
    
    try {
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderChangeHistory(data.changes);
        }
    } catch (error) {
        console.error('Failed to load change history:', error);
    }
}

function renderChangeHistory(changes) {
    const container = document.getElementById('change-history-list');
    container.innerHTML = '';
    
    if (changes.length === 0) {
        container.innerHTML = '<p class="empty-state">No changes recorded</p>';
        return;
    }
    
    changes.forEach(change => {
        const item = document.createElement('div');
        item.className = `change-item ${change.status}`;
        
        const statusIcons = {
            'applied': 'fa-check-circle',
            'rolled_back': 'fa-undo',
            'failed': 'fa-times-circle',
            'pending': 'fa-clock'
        };
        
        const impactColor = change.impact_score > 0.5 ? 'high' : change.impact_score > 0.3 ? 'medium' : 'low';
        
        item.innerHTML = `
            <div class="change-main">
                <div class="change-icon">
                    <i class="fas ${statusIcons[change.status] || 'fa-circle'}"></i>
                </div>
                <div class="change-info">
                    <h4>${change.target}</h4>
                    <span class="change-type">${change.change_type}</span>
                    <span class="change-reason">${change.reason || 'No reason provided'}</span>
                </div>
                <div class="change-meta">
                    <span class="impact-badge ${impactColor}">Impact: ${(change.impact_score * 100).toFixed(0)}%</span>
                    <span class="change-time">${new Date(change.timestamp).toLocaleString()}</span>
                    <span class="change-admin">${change.admin_email}</span>
                </div>
            </div>
            <div class="change-actions">
                <button class="btn btn-sm btn-secondary" onclick="viewChangeDetails('${change.change_id}')">
                    <i class="fas fa-eye"></i> Details
                </button>
                ${change.rollback_available && change.status === 'applied' ? `
                    <button class="btn btn-sm btn-warning" onclick="rollbackChange('${change.change_id}')">
                        <i class="fas fa-undo"></i> Rollback
                    </button>
                ` : ''}
            </div>
        `;
        
        container.appendChild(item);
    });
    
    // Also update pending patches table if on that tab
    renderPendingPatches(changes);
}

function renderPendingPatches(changes) {
    const tbody = document.getElementById('pending-patches-tbody');
    if (!tbody) return;
    
    const pending = changes.filter(c => c.status === 'pending');
    
    tbody.innerHTML = '';
    
    if (pending.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No pending changes</td></tr>';
        return;
    }
    
    pending.forEach(change => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(change.timestamp).toLocaleTimeString()}</td>
            <td>${change.target}</td>
            <td><span class="impact-badge">${(change.impact_score * 100).toFixed(0)}%</span></td>
            <td><span class="status-badge ${change.status}">${change.status}</span></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="applyPendingChange('${change.change_id}')">
                    <i class="fas fa-check"></i> Apply
                </button>
                <button class="btn btn-sm btn-secondary" onclick="viewChangeDetails('${change.change_id}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function viewChangeDetails(changeId) {
    currentChangeId = changeId;
    
    try {
        const response = await fetch(`${API_BASE}/api/system/changes/${changeId}`, {
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const change = data.change;
            
            document.getElementById('detail-change-id').textContent = change.change_id;
            document.getElementById('detail-status').textContent = change.status;
            document.getElementById('detail-status').className = `change-status ${change.status}`;
            document.getElementById('detail-type').textContent = change.change_type;
            document.getElementById('detail-target').textContent = change.target;
            document.getElementById('detail-admin').textContent = change.admin_email;
            document.getElementById('detail-timestamp').textContent = new Date(change.timestamp).toLocaleString();
            document.getElementById('detail-impact').textContent = `${(change.impact_score * 100).toFixed(1)}%`;
            document.getElementById('detail-rollback').textContent = change.rollback_available ? 'Yes' : 'No';
            
            document.getElementById('detail-old-value').textContent = JSON.stringify(change.old_value, null, 2);
            document.getElementById('detail-new-value').textContent = JSON.stringify(change.new_value, null, 2);
            document.getElementById('detail-reason').textContent = change.reason || 'No reason provided';
            
            // Show/hide rollback button
            const rollbackBtn = document.getElementById('detail-rollback-btn');
            rollbackBtn.style.display = (change.rollback_available && change.status === 'applied') ? 'inline-flex' : 'none';
            
            // Render logs
            const logsContainer = document.getElementById('detail-logs');
            if (change.logs && change.logs.length > 0) {
                logsContainer.innerHTML = change.logs.map(log => `
                    <div class="log-entry ${log.action.toLowerCase().includes('error') ? 'error' : 'info'}">
                        <span class="log-time">${new Date(log.timestamp).toLocaleTimeString()}</span>
                        <span class="log-action">${log.action}</span>
                        <span class="log-details">${log.details}</span>
                    </div>
                `).join('');
                document.getElementById('detail-logs-section').style.display = 'block';
            } else {
                document.getElementById('detail-logs-section').style.display = 'none';
            }
            
            showModal('change-details-modal');
        }
    } catch (error) {
        console.error('Failed to load change details:', error);
        showToast('Failed to load change details', 'error');
    }
}

async function rollbackChange(changeId) {
    if (!confirm('Are you sure you want to rollback this change?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/system/changes/${changeId}/rollback`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${adminState.token}` }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Change rolled back successfully', 'success');
            loadChangeHistory();
            refreshModificationStatus();
            closeModal('change-details-modal');
        } else {
            showToast(data.error || 'Failed to rollback change', 'error');
        }
    } catch (error) {
        console.error('Failed to rollback:', error);
        showToast('Failed to rollback change', 'error');
    }
}

function rollbackSelectedChange() {
    if (currentChangeId) {
        rollbackChange(currentChangeId);
    }
}

async function applyPendingChange(changeId) {
    try {
        const response = await fetch(`${API_BASE}/api/system/code/apply`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ change_id: changeId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Code change applied successfully', 'success');
            loadChangeHistory();
            refreshModificationStatus();
        } else {
            showToast(data.error || 'Failed to apply change', 'error');
        }
    } catch (error) {
        console.error('Failed to apply change:', error);
        showToast('Failed to apply change', 'error');
    }
}

async function proposeCodeChange() {
    const filePath = currentFile;
    
    if (!filePath) {
        showToast('Please open a file in the code editor first', 'error');
        return;
    }
    
    if (!monacoEditor) {
        showToast('Editor not initialized', 'error');
        return;
    }
    
    const newContent = monacoEditor.getValue();
    const reason = prompt('Enter reason for this code change:');
    
    if (!reason) {
        return;
    }
    
    showToast('Validating code change...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/system/code/propose`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath,
                new_content: newContent,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        validatedPatchData = data;
        
        if (data.validation) {
            showValidationResults(data.validation, data.change_id);
        }
        
        if (data.success) {
            showToast('Code change proposed and validated', 'success');
            loadChangeHistory();
        } else {
            showToast(data.error || 'Validation failed', 'error');
        }
    } catch (error) {
        console.error('Failed to propose change:', error);
        showToast('Failed to propose change', 'error');
    }
}

function showValidationResults(validation, changeId) {
    const statusDiv = document.getElementById('validation-status');
    const scoreBar = document.getElementById('validation-score-bar');
    const scoreValue = document.getElementById('validation-score-value');
    const safetyChecks = document.getElementById('validation-safety-checks');
    const errorsSection = document.getElementById('validation-errors-section');
    const errorsList = document.getElementById('validation-errors-list');
    const warningsSection = document.getElementById('validation-warnings-section');
    const warningsList = document.getElementById('validation-warnings-list');
    const applyBtn = document.getElementById('btn-apply-patch');
    
    // Status
    if (validation.valid) {
        statusDiv.innerHTML = '<span class="status-success"><i class="fas fa-check-circle"></i> Validation Passed</span>';
        applyBtn.style.display = 'inline-flex';
        applyBtn.dataset.changeId = changeId;
    } else {
        statusDiv.innerHTML = '<span class="status-error"><i class="fas fa-times-circle"></i> Validation Failed</span>';
        applyBtn.style.display = 'none';
    }
    
    // Score
    const score = validation.impact_score || 0;
    scoreBar.style.width = `${score * 100}%`;
    scoreValue.textContent = `${(score * 100).toFixed(1)}%`;
    
    // Safety checks
    if (validation.safety_checks) {
        safetyChecks.innerHTML = Object.entries(validation.safety_checks).map(([key, passed]) => `
            <div class="safety-check ${passed ? 'passed' : 'failed'}">
                <i class="fas ${passed ? 'fa-check' : 'fa-times'}"></i>
                <span>${key.replace(/_/g, ' ').toUpperCase()}</span>
            </div>
        `).join('');
    }
    
    // Errors
    if (validation.errors && validation.errors.length > 0) {
        errorsSection.style.display = 'block';
        errorsList.innerHTML = validation.errors.map(e => `<li>${escapeHtml(e)}</li>`).join('');
    } else {
        errorsSection.style.display = 'none';
    }
    
    // Warnings
    if (validation.warnings && validation.warnings.length > 0) {
        warningsSection.style.display = 'block';
        warningsList.innerHTML = validation.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('');
    } else {
        warningsSection.style.display = 'none';
    }
    
    showModal('code-validation-modal');
}

async function applyValidatedPatch() {
    const changeId = document.getElementById('btn-apply-patch').dataset.changeId;
    
    if (!changeId) {
        showToast('No change ID found', 'error');
        return;
    }
    
    closeModal('code-validation-modal');
    showToast('Applying code change...', 'info');
    
    await applyPendingChange(changeId);
}

async function validateCurrentFile() {
    const filePath = currentFile;
    
    if (!filePath) {
        showToast('Please open a file in the code editor first', 'error');
        return;
    }
    
    if (!monacoEditor) {
        showToast('Editor not initialized', 'error');
        return;
    }
    
    const content = monacoEditor.getValue();
    
    // Simple validation - just check syntax via API
    showToast('Validating file...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/api/system/code/propose`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminState.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath,
                new_content: content,
                reason: 'Validation check'
            })
        });
        
        const data = await response.json();
        
        if (data.validation) {
            showValidationResults(data.validation, data.change_id);
        }
    } catch (error) {
        console.error('Failed to validate:', error);
        showToast('Failed to validate file', 'error');
    }
}

// Tab switching for modification panel
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.mod-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            // Update active tab
            document.querySelectorAll('.mod-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Show corresponding panel
            document.querySelectorAll('.mod-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(`${targetTab}-panel`).classList.add('active');
        });
    });
});

// ==================== END SYSTEM SELF-MODIFICATION ====================

// ==================== ADMIN DASHBOARD ====================

// Dashboard state
let dashboardState = {
    currentFile: null,
    fileContent: null,
    logFilter: 'all',
    logs: [],
    metrics: {},
    agentStats: {},
    executions: [],
    refreshInterval: null
};

// Admin Dashboard API Base (reuse existing API_BASE or define if needed)
const ADMIN_API_BASE = API_BASE || '/api/admin';

// Initialize Admin Dashboard
function initAdminDashboard() {
    if (currentUser.role !== 'admin') {
        showToast('Admin access required', 'error');
        return;
    }
    
    refreshAdminDashboard();
    startDashboardRealtimeUpdates();
    
    // Setup keyboard shortcuts
    document.addEventListener('keydown', handleDashboardKeydown);
    
    // Setup log filter buttons
    setupLogFilters();
}

// Setup log filter event listeners
function setupLogFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            setLogFilter(btn.dataset.level);
        });
    });
}

// Keyboard shortcuts
function handleDashboardKeydown(e) {
    if (!document.getElementById('admin-dashboard-section').classList.contains('hidden')) {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            if (dashboardState.currentFile) {
                saveQuickEdit();
            }
        }
    }
}

// Refresh entire dashboard
async function refreshAdminDashboard() {
    await Promise.all([
        loadDashboardSystemStatus(),
        loadDashboardAgentStats(),
        loadDashboardMetrics(),
        loadDashboardExecutions(),
        loadDashboardFiles()
    ]);
}

// Load System Status
async function loadDashboardSystemStatus() {
    try {
        const response = await fetch(`${ADMIN_API_BASE}/system/state`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load system state');
        
        const data = await response.json();
        
        // Update mode indicator
        const modeIndicator = document.getElementById('system-mode-indicator');
        const systemState = data.systemState || {};
        const mode = systemState.mode || 'training';
        
        if (modeIndicator) {
            modeIndicator.textContent = mode;
            modeIndicator.className = `status-indicator ${mode.toLowerCase()}`;
        }
        
        // Update mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode.toLowerCase());
        });
        
        // Update threshold sliders if config available
        const config = systemState.config || {};
        if (config) {
            const edgeSlider = document.getElementById('dash-edge-threshold');
            const confSlider = document.getElementById('dash-min-confidence');
            const riskSlider = document.getElementById('dash-max-risk');
            
            if (edgeSlider && config.edge_threshold !== undefined) {
                edgeSlider.value = config.edge_threshold;
                document.getElementById('dash-edge-value').textContent = config.edge_threshold.toFixed(2);
            }
            if (confSlider && config.min_confidence !== undefined) {
                confSlider.value = config.min_confidence;
                document.getElementById('dash-confidence-value').textContent = config.min_confidence.toFixed(2);
            }
            if (riskSlider && config.max_position_risk_percent !== undefined) {
                riskSlider.value = config.max_position_risk_percent;
                document.getElementById('dash-risk-value').textContent = config.max_position_risk_percent + '%';
            }
        }
        
        // Update agent toggles
        const agents = systemState.agents || [];
        if (agents) {
            agents.forEach(agent => {
                const toggle = document.getElementById(`toggle-${agent.agent_id}`);
                if (toggle) {
                    toggle.checked = agent.is_enabled;
                }
            });
        }
        
    } catch (error) {
        console.error('Failed to load system status:', error);
    }
}

// Switch System Mode
async function switchSystemMode(mode) {
    if (mode === 'execution') {
        showExecutionConfirmModal();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mode/switch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                mode: mode,
                reason: `Switched to ${mode} mode from dashboard`
            })
        });
        
        if (response.ok) {
            showToast(`System switched to ${mode} mode`, 'success');
            loadDashboardSystemStatus();
        } else {
            const data = await response.json();
            throw new Error(data.message || 'Failed to switch mode');
        }
    } catch (error) {
        showToast('Failed to switch mode: ' + error.message, 'error');
    }
}

// Show Execution Confirm Modal
function showExecutionConfirmModal() {
    // Create modal if doesn't exist
    let modal = document.getElementById('execution-confirm-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'execution-confirm-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header warning">
                    <h3><i class="fas fa-exclamation-triangle"></i> Confirm Execution Mode</h3>
                </div>
                <div class="modal-body">
                    <p>Switching to <strong>EXECUTION MODE</strong> will enable live trading capabilities.</p>
                    <ul style="margin: 15px 0; padding-left: 20px;">
                        <li>Real trades may be executed</li>
                        <li>Actual capital will be at risk</li>
                        <li>All safeguards are still active</li>
                    </ul>
                    <div class="form-group">
                        <label>Enter reason (required for audit):</label>
                        <input type="text" id="exec-reason" class="form-input" placeholder="e.g., Market conditions favorable, strategy testing">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('execution-confirm-modal')">Cancel</button>
                    <button class="btn btn-danger" onclick="confirmExecutionMode()">Switch to Execution</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    modal.classList.add('active');
}

// Confirm Execution Mode
async function confirmExecutionMode() {
    const reason = document.getElementById('exec-reason')?.value?.trim();
    if (!reason || reason.length < 5) {
        showToast('Please enter a reason (min 5 characters)', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/mode/switch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                mode: 'execution',
                reason: reason
            })
        });
        
        if (response.ok) {
            showToast('System switched to EXECUTION mode', 'success');
            closeModal('execution-confirm-modal');
            loadDashboardSystemStatus();
        } else {
            const data = await response.json();
            throw new Error(data.message || 'Failed to switch mode');
        }
    } catch (error) {
        showToast('Failed to switch mode: ' + error.message, 'error');
    }
}

// Update threshold preview
function updateThresholdPreview(type, value) {
    const valueId = `dash-${type}-value`;
    const valueEl = document.getElementById(valueId);
    if (valueEl) {
        if (type === 'risk') {
            valueEl.textContent = value + '%';
        } else {
            valueEl.textContent = parseFloat(value).toFixed(2);
        }
    }
}

// Save dashboard thresholds
async function saveDashboardThresholds() {
    const updates = {};
    
    const edgeVal = document.getElementById('dash-edge-threshold')?.value;
    const confVal = document.getElementById('dash-min-confidence')?.value;
    const riskVal = document.getElementById('dash-max-risk')?.value;
    
    if (edgeVal !== undefined) updates.edge_threshold = parseFloat(edgeVal);
    if (confVal !== undefined) updates.min_confidence = parseFloat(confVal);
    if (riskVal !== undefined) updates.max_position_risk_percent = parseFloat(riskVal);
    
    try {
        const response = await fetch(`${ADMIN_API_BASE}/config/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ updates })
        });
        
        if (response.ok) {
            showToast('Thresholds updated successfully', 'success');
        } else {
            throw new Error('Failed to update thresholds');
        }
    } catch (error) {
        showToast('Failed to update thresholds: ' + error.message, 'error');
    }
}

// Toggle agent
async function toggleAgent(agentId, enabled) {
    try {
        const response = await fetch(`${ADMIN_API_BASE}/agent/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({ agent_id: agentId, enabled })
        });
        
        if (response.ok) {
            showToast(`Agent ${enabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            throw new Error('Failed to toggle agent');
        }
    } catch (error) {
        showToast('Failed to toggle agent: ' + error.message, 'error');
        // Revert toggle
        const toggle = document.getElementById(`toggle-${agentId}`);
        if (toggle) toggle.checked = !enabled;
    }
}

// Load Agent Stats
async function loadDashboardAgentStats() {
    try {
        const response = await fetch('/api/admin/agents', {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load agents');
        
        const data = await response.json();
        
        if (data.agents) {
            const activeAgents = data.agents.filter(a => a.is_enabled).length;
            
            document.getElementById('dash-active-agents').textContent = `${activeAgents} Active`;
            document.getElementById('dash-total-runs').textContent = data.agents.length.toString();
            // Note: avg time and success rate would need to come from agent execution history
        }
    } catch (error) {
        console.error('Failed to load agent stats:', error);
    }
}

// Load Metrics
async function loadDashboardMetrics() {
    try {
        const response = await fetch(`${ADMIN_API_BASE}/metrics?hours=1`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load metrics');
        
        const data = await response.json();
        
        if (data.metrics && data.metrics.length > 0) {
            const latest = data.metrics[data.metrics.length - 1];
            document.getElementById('dash-cpu').textContent = latest.cpu_percent?.toFixed(1) || '-';
            document.getElementById('dash-memory').textContent = latest.memory_percent?.toFixed(1) || '-';
            document.getElementById('dash-debates').textContent = latest.active_debates || '-';
            document.getElementById('dash-streams').textContent = latest.active_sessions || '-';
        }
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

// Load Recent Executions
async function loadDashboardExecutions() {
    try {
        const response = await fetch('/api/agents/history?limit=5', {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load executions');
        
        const data = await response.json();
        
        const listEl = document.getElementById('dash-execution-list');
        if (listEl && data.history) {
            listEl.innerHTML = data.history.map(exec => `
                <div class="execution-item">
                    <span class="exec-agent">${exec.agent_id?.split('_')[1] || exec.agent_id || 'Agent'}</span>
                    <span class="exec-task">${(exec.task || 'Task').substring(0, 25)}...</span>
                    <span class="exec-status ${exec.status}">
                        <i class="fas fa-${exec.status === 'completed' ? 'check' : exec.status === 'running' ? 'spinner fa-spin' : 'times'}"></i>
                    </span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load executions:', error);
    }
}

// Load Dashboard Files
async function loadDashboardFiles() {
    try {
        const response = await fetch(`${ADMIN_API_BASE}/files/list?path=.`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load files');
        
        const data = await response.json();
        
        // Update quick file list
        const quickFiles = ['production_server.py', 'requirements.txt', 'config.yaml', 'config.json'];
        const fileListEl = document.getElementById('dash-file-list');
        
        if (fileListEl && data.files) {
            const existingFiles = data.files.filter(f => quickFiles.includes(f.name));
            
            fileListEl.innerHTML = existingFiles.map(file => `
                <div class="quick-file-item ${dashboardState.currentFile === file.path ? 'active' : ''}" 
                     onclick="openQuickEdit('${file.path}')">
                    <i class="${getFileIcon(file.name)}"></i>
                    <span>${file.name}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

// Get File Icon
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'py': 'fab fa-python',
        'js': 'fab fa-js',
        'html': 'fab fa-html5',
        'css': 'fab fa-css3',
        'json': 'fas fa-code',
        'yaml': 'fas fa-cog',
        'yml': 'fas fa-cog',
        'txt': 'fas fa-file-alt',
        'md': 'fas fa-file-alt',
        'sql': 'fas fa-database'
    };
    return icons[ext] || 'fas fa-file';
}

// Open Quick Edit
async function openQuickEdit(filePath) {
    try {
        const response = await fetch(`${ADMIN_API_BASE}/files/read?path=${encodeURIComponent(filePath)}`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to read file');
        
        const data = await response.json();
        
        dashboardState.currentFile = filePath;
        dashboardState.fileContent = data.content;
        
        document.getElementById('dash-edit-filename').textContent = filePath;
        document.getElementById('dash-editor-textarea').value = data.content;
        
        // Highlight active file
        document.querySelectorAll('.quick-file-item').forEach(item => {
            item.classList.toggle('active', item.textContent.includes(filePath.split('/').pop()));
        });
        
    } catch (error) {
        showToast('Failed to open file: ' + error.message, 'error');
    }
}

// Save Quick Edit
async function saveQuickEdit() {
    if (!dashboardState.currentFile) {
        showToast('No file selected', 'error');
        return;
    }
    
    const content = document.getElementById('dash-editor-textarea').value;
    
    try {
        const response = await fetch(`${ADMIN_API_BASE}/files/write`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                path: dashboardState.currentFile,
                content: content
            })
        });
        
        if (response.ok) {
            dashboardState.fileContent = content;
            showToast('File saved successfully', 'success');
        } else {
            throw new Error('Failed to save file');
        }
    } catch (error) {
        showToast('Failed to save: ' + error.message, 'error');
    }
}

// Open Full Editor
function openFullEditor() {
    if (dashboardState.currentFile) {
        switchToSection('code-editor');
        openFileInEditor(dashboardState.currentFile);
    } else {
        switchToSection('code-editor');
    }
}

// Placeholder for full editor integration
function openFileInEditor(filePath) {
    // This would integrate with the full Monaco editor
    showToast(`Opening ${filePath} in full editor...`, 'info');
}

// Placeholder for refresh file tree
function refreshFileTree() {
    // This would refresh the full file tree in the code editor section
}

// Switch to Section
function switchToSection(sectionName) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionName);
    });
    
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('hidden');
    });
    
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.classList.remove('hidden');
    }
    
    // Refresh section-specific data
    if (sectionName === 'agent-control') {
        refreshAgentStatus();
    } else if (sectionName === 'code-editor') {
        // refreshFileTree();
    } else if (sectionName === 'admin-dashboard') {
        refreshAdminDashboard();
    }
}

// Real-time Updates
function startDashboardRealtimeUpdates() {
    // Update every 5 seconds
    dashboardState.refreshInterval = setInterval(() => {
        if (!document.getElementById('admin-dashboard-section').classList.contains('hidden')) {
            loadDashboardMetrics();
            loadDashboardExecutions();
            fetchDashboardLogs();
        }
    }, 5000);
}

// Fetch Logs
async function fetchDashboardLogs() {
    try {
        const response = await fetch(`${ADMIN_API_BASE}/logs/recent?limit=20`, {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch logs');
        
        const data = await response.json();
        
        if (data.logs) {
            dashboardState.logs = data.logs;
            updateLogsDisplay();
            
            // Check for errors
            const errors = data.logs.filter(l => l.level === 'ERROR');
            const errorAlert = document.getElementById('dash-error-alert');
            if (errorAlert) {
                errorAlert.classList.toggle('hidden', errors.length === 0);
                document.getElementById('dash-error-count').textContent = 
                    `${errors.length} error${errors.length !== 1 ? 's' : ''} in last 5 min`;
            }
        }
    } catch (error) {
        console.error('Failed to fetch logs:', error);
    }
}

// Update Logs Display
function updateLogsDisplay() {
    const logsEl = document.getElementById('dash-logs-stream');
    if (!logsEl) return;
    
    const filtered = dashboardState.logFilter === 'all' 
        ? dashboardState.logs 
        : dashboardState.logs.filter(l => l.level.toLowerCase() === dashboardState.logFilter);
    
    logsEl.innerHTML = filtered.map(log => `
        <div class="log-entry ${log.level.toLowerCase()}">
            <span class="log-time">${new Date(log.timestamp).toLocaleTimeString()}</span>
            <span class="log-level">${log.level}</span>
            <span class="log-msg">${log.message}</span>
        </div>
    `).join('');
    
    // Auto-scroll to bottom
    logsEl.scrollTop = logsEl.scrollHeight;
}

// Set Log Filter
function setLogFilter(level) {
    dashboardState.logFilter = level;
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.level === level);
    });
    updateLogsDisplay();
}

// Show Run Agent Modal
function showRunAgentModal() {
    // Create modal if doesn't exist
    let modal = document.getElementById('run-agent-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'run-agent-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-play"></i> Run Agent</h3>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Select Agent:</label>
                        <select id="run-agent-id" class="form-select">
                            <option value="analyst">Analyst</option>
                            <option value="bullish">Bullish</option>
                            <option value="bearish">Bearish</option>
                            <option value="risk">Risk Manager</option>
                            <option value="judge">Judge</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Task Description:</label>
                        <textarea id="run-agent-task" class="form-textarea" rows="3" placeholder="e.g., Analyze AAPL for swing trade opportunity"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('run-agent-modal')">Cancel</button>
                    <button class="btn btn-primary" onclick="executeAgentRun()">Run Agent</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    modal.classList.add('active');
}

// Execute Agent Run
async function executeAgentRun() {
    const agentId = document.getElementById('run-agent-id')?.value;
    const task = document.getElementById('run-agent-task')?.value?.trim();
    
    if (!task) {
        showToast('Please enter a task description', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/agents/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.token}`
            },
            body: JSON.stringify({
                agent_id: agentId,
                task: task
            })
        });
        
        if (response.ok) {
            showToast('Agent execution started', 'success');
            closeModal('run-agent-modal');
            loadDashboardExecutions();
        } else {
            throw new Error('Failed to run agent');
        }
    } catch (error) {
        showToast('Failed to run agent: ' + error.message, 'error');
    }
}

// Close Modal Helper
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (dashboardState.refreshInterval) {
        clearInterval(dashboardState.refreshInterval);
    }
});

// ==================== END ADMIN DASHBOARD ====================
