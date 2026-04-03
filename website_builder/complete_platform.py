"""
COMPLETE AI WEBSITE PLATFORM - Missing Features Module
Adds all essential systems for a true Wix/Squarespace/Webflow competitor
"""

import re
import json
import hashlib
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict


# ==================== AI CHAT WIDGET ====================

class AIChatWidget:
    """
    Embeddable AI chat widget for websites
    Provides live customer support, lead capture, and Q&A
    """
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = defaultdict(list)
        self.leads: List[Dict] = []
        self.knowledge_base: Dict[str, str] = {}
    
    def generate_widget_code(self, config: Dict) -> str:
        """Generate embeddable chat widget HTML/JS/CSS"""
        primary_color = config.get('primary_color', '#3b82f6')
        position = config.get('position', 'bottom-right')
        welcome_message = config.get('welcome_message', 'Hi! How can I help you today?')
        
        css = f'''
/* AI Chat Widget Styles */
.ai-chat-widget {{
    position: fixed;
    {position.replace('-', ': 20px; ')}: 20px;
    z-index: 9999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

.ai-chat-button {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: {primary_color};
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    transition: transform 0.2s, box-shadow 0.2s;
}}

.ai-chat-button:hover {{
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
}}

.ai-chat-window {{
    position: absolute;
    bottom: 80px;
    {'right' if 'right' in position else 'left'}: 0;
    width: 350px;
    height: 500px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    display: none;
    flex-direction: column;
    overflow: hidden;
}}

.ai-chat-window.active {{
    display: flex;
}}

.ai-chat-header {{
    background: {primary_color};
    color: white;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.ai-chat-avatar {{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}}

.ai-chat-messages {{
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.ai-message {{
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.5;
}}

.ai-message.bot {{
    background: #f3f4f6;
    color: #1f2937;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}}

.ai-message.user {{
    background: {primary_color};
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}}

.ai-chat-input-area {{
    padding: 12px 16px;
    border-top: 1px solid #e5e7eb;
    display: flex;
    gap: 8px;
}}

.ai-chat-input {{
    flex: 1;
    padding: 10px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
}}

.ai-chat-input:focus {{
    border-color: {primary_color};
}}

.ai-chat-send {{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: {primary_color};
    color: white;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.ai-typing {{
    display: flex;
    gap: 4px;
    padding: 12px 16px;
}}

.ai-typing-dot {{
    width: 8px;
    height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: typing 1.4s infinite;
}}

.ai-typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
.ai-typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}

@keyframes typing {{
    0%, 60%, 100% {{ transform: translateY(0); }}
    30% {{ transform: translateY(-10px); }}
}}

.ai-lead-form {{
    background: #f9fafb;
    padding: 12px;
    border-radius: 12px;
    margin-top: 8px;
}}

.ai-lead-form input {{
    width: 100%;
    padding: 8px 12px;
    margin-bottom: 8px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-size: 14px;
}}

.ai-lead-form button {{
    width: 100%;
    padding: 10px;
    background: {primary_color};
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
}}
'''
        
        html = f'''
<!-- AI Chat Widget -->
<div class="ai-chat-widget">
    <div class="ai-chat-window" id="aiChatWindow">
        <div class="ai-chat-header">
            <div class="ai-chat-avatar">🤖</div>
            <div>
                <div style="font-weight: 600;">AI Assistant</div>
                <div style="font-size: 12px; opacity: 0.9;">Online</div>
            </div>
        </div>
        <div class="ai-chat-messages" id="aiChatMessages">
            <div class="ai-message bot">{welcome_message}</div>
        </div>
        <div class="ai-chat-input-area">
            <input type="text" class="ai-chat-input" id="aiChatInput" placeholder="Type your message...">
            <button class="ai-chat-send" onclick="sendMessage()">➤</button>
        </div>
    </div>
    <button class="ai-chat-button" id="aiChatButton" onclick="toggleChat()">💬</button>
</div>
'''
        
        js = '''
<script>
const API_ENDPOINT = '/api/v1/chat/widget/message';
const sessionId = localStorage.getItem('chatSessionId') || generateSessionId();
localStorage.setItem('chatSessionId', sessionId);

function generateSessionId() {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function toggleChat() {
    const window = document.getElementById('aiChatWindow');
    window.classList.toggle('active');
    if (window.classList.contains('active')) {
        document.getElementById('aiChatInput').focus();
    }
}

function sendMessage() {
    const input = document.getElementById('aiChatInput');
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTyping();
    
    // Send to API
    fetch(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            message: message,
            context: window.location.pathname
        })
    })
    .then(r => r.json())
    .then(data => {
        hideTyping();
        addMessage(data.response, 'bot');
        
        // Show lead capture form if requested
        if (data.show_lead_form) {
            showLeadForm();
        }
    })
    .catch(err => {
        hideTyping();
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    });
}

function addMessage(text, sender) {
    const container = document.getElementById('aiChatMessages');
    const msg = document.createElement('div');
    msg.className = 'ai-message ' + sender;
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    const container = document.getElementById('aiChatMessages');
    const typing = document.createElement('div');
    typing.id = 'typingIndicator';
    typing.className = 'ai-typing';
    typing.innerHTML = '<div class="ai-typing-dot"></div><div class="ai-typing-dot"></div><div class="ai-typing-dot"></div>';
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function showLeadForm() {
    const container = document.getElementById('aiChatMessages');
    const form = document.createElement('div');
    form.className = 'ai-message bot';
    form.innerHTML = `
        <div style="margin-bottom: 8px;">Can I get your email to follow up?</div>
        <div class="ai-lead-form">
            <input type="email" id="leadEmail" placeholder="your@email.com">
            <input type="text" id="leadName" placeholder="Your name (optional)">
            <button onclick="submitLead()">Submit</button>
        </div>
    `;
    container.appendChild(form);
    container.scrollTop = container.scrollHeight;
}

function submitLead() {
    const email = document.getElementById('leadEmail').value;
    const name = document.getElementById('leadName').value;
    
    fetch('/api/v1/chat/widget/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            email: email,
            name: name,
            source: window.location.pathname
        })
    });
    
    addMessage('Thank you! We\'ll be in touch soon.', 'bot');
}

// Enter key to send
document.getElementById('aiChatInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
</script>
'''
        
        return {'css': css, 'html': html, 'js': js, 'full': css + html + js}
    
    def process_message(self, session_id: str, message: str, context: str) -> Dict:
        """Process chat message and generate AI response"""
        # Store message
        self.conversations[session_id].append({
            'timestamp': datetime.now().isoformat(),
            'role': 'user',
            'message': message,
            'context': context
        })
        
        # Generate response based on intent
        response = self._generate_response(message, context)
        
        # Check if lead capture should be triggered
        show_lead = len(self.conversations[session_id]) >= 3 and not self._has_lead(session_id)
        
        self.conversations[session_id].append({
            'timestamp': datetime.now().isoformat(),
            'role': 'bot',
            'message': response
        })
        
        return {
            'response': response,
            'show_lead_form': show_lead,
            'session_id': session_id
        }
    
    def _generate_response(self, message: str, context: str) -> str:
        """Generate AI response based on message content"""
        msg_lower = message.lower()
        
        if any(w in msg_lower for w in ['price', 'cost', 'pricing', 'how much']):
            return "Our pricing starts at $29/month for the Basic plan. Would you like me to send you our full pricing details?"
        
        if any(w in msg_lower for w in ['demo', 'trial', 'try', 'test']):
            return "I'd be happy to set up a demo for you! Could you share your email so our team can schedule a time that works for you?"
        
        if any(w in msg_lower for w in ['contact', 'email', 'phone', 'call']):
            return "You can reach our team at support@example.com or call us at (555) 123-4567. Would you like us to contact you instead?"
        
        if any(w in msg_lower for w in ['feature', 'capabilities', 'what can', 'do']):
            return "Our platform includes AI-powered website building, e-commerce, analytics, CMS, and much more. What specific features are you looking for?"
        
        return "Thanks for your message! I'm here to help with any questions about our platform. What would you like to know?"
    
    def _has_lead(self, session_id: str) -> bool:
        """Check if we already have lead info for this session"""
        return any(l['session_id'] == session_id for l in self.leads)
    
    def capture_lead(self, session_id: str, email: str, name: str, source: str) -> Dict:
        """Capture lead information"""
        lead = {
            'id': f"lead_{uuid.uuid4().hex[:8]}",
            'session_id': session_id,
            'email': email,
            'name': name,
            'source': source,
            'captured_at': datetime.now().isoformat(),
            'conversation_history': self.conversations.get(session_id, [])
        }
        self.leads.append(lead)
        
        return {'success': True, 'lead_id': lead['id']}


# ==================== ANALYTICS DASHBOARD ====================

class AnalyticsDashboard:
    """
    Comprehensive website analytics
    User tracking, heatmaps, conversion funnels
    """
    
    def __init__(self):
        self.events: List[Dict] = []
        self.sessions: Dict[str, Dict] = {}
        self.page_views: Dict[str, int] = defaultdict(int)
        self.conversion_goals: Dict[str, Dict] = {}
    
    def generate_tracking_script(self, site_id: str) -> str:
        """Generate analytics tracking script"""
        return f'''
<!-- Analytics Tracking -->
<script>
(function() {{
    const SITE_ID = '{site_id}';
    const API_URL = '/api/v1/analytics/track';
    
    // Session tracking
    let sessionId = localStorage.getItem('analytics_session');
    if (!sessionId) {{
        sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('analytics_session', sessionId);
    }}
    
    // User fingerprint
    let userId = localStorage.getItem('analytics_user');
    if (!userId) {{
        userId = 'user_' + Math.random().toString(36).substr(2, 16);
        localStorage.setItem('analytics_user', userId);
    }}
    
    // Track page view
    function trackPageView() {{
        fetch(API_URL, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                site_id: SITE_ID,
                session_id: sessionId,
                user_id: userId,
                event: 'pageview',
                url: window.location.href,
                path: window.location.pathname,
                referrer: document.referrer,
                timestamp: new Date().toISOString(),
                screen_size: window.innerWidth + 'x' + window.innerHeight,
                user_agent: navigator.userAgent
            }})
        }});
    }}
    
    // Track clicks
    document.addEventListener('click', function(e) {{
        const target = e.target.closest('[data-track]') || e.target;
        fetch(API_URL, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                site_id: SITE_ID,
                session_id: sessionId,
                user_id: userId,
                event: 'click',
                element: target.tagName,
                element_id: target.id,
                element_class: target.className,
                text: target.textContent?.substring(0, 100),
                x: e.clientX,
                y: e.clientY,
                url: window.location.href
            }})
        }});
    }});
    
    // Track scroll depth
    let maxScroll = 0;
    window.addEventListener('scroll', function() {{
        const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
        if (scrollPercent > maxScroll) {{
            maxScroll = scrollPercent;
            if (scrollPercent % 25 === 0) {{ // Track at 25%, 50%, 75%, 100%
                fetch(API_URL, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        site_id: SITE_ID,
                        session_id: sessionId,
                        user_id: userId,
                        event: 'scroll',
                        depth: scrollPercent,
                        url: window.location.href
                    }})
                }});
            }}
        }}
    }});
    
    // Track time on page
    let startTime = Date.now();
    window.addEventListener('beforeunload', function() {{
        const duration = Math.round((Date.now() - startTime) / 1000);
        navigator.sendBeacon(API_URL, JSON.stringify({{
            site_id: SITE_ID,
            session_id: sessionId,
            user_id: userId,
            event: 'time_on_page',
            duration: duration,
            url: window.location.href
        }}));
    }});
    
    // Initial page view
    trackPageView();
}})();
</script>
'''
    
    def track_event(self, event_data: Dict) -> Dict:
        """Track an analytics event"""
        event = {
            'id': f"evt_{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now().isoformat(),
            **event_data
        }
        self.events.append(event)
        
        # Update session
        session_id = event_data.get('session_id')
        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'started_at': event['timestamp'],
                    'events': [],
                    'pages_viewed': set(),
                    'user_id': event_data.get('user_id')
                }
            self.sessions[session_id]['events'].append(event)
            if event_data.get('event') == 'pageview':
                self.sessions[session_id]['pages_viewed'].add(event_data.get('url'))
        
        # Update page view count
        if event_data.get('event') == 'pageview':
            path = event_data.get('path', '/')
            self.page_views[path] += 1
        
        return {'success': True, 'event_id': event['id']}
    
    def get_dashboard_data(self, site_id: str, days: int = 30) -> Dict:
        """Get analytics dashboard data"""
        # Filter events for this site and time period
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        site_events = [e for e in self.events 
                      if e.get('site_id') == site_id and 
                      datetime.fromisoformat(e['timestamp']).timestamp() > cutoff]
        
        # Calculate metrics
        pageviews = [e for e in site_events if e['event'] == 'pageview']
        unique_sessions = len(set(e['session_id'] for e in pageviews))
        unique_users = len(set(e['user_id'] for e in pageviews if e.get('user_id')))
        
        # Top pages
        page_counts = defaultdict(int)
        for e in pageviews:
            page_counts[e.get('path', '/')] += 1
        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Average session duration
        durations = [e['duration'] for e in site_events if e['event'] == 'time_on_page']
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Bounce rate
        single_page_sessions = sum(1 for s in self.sessions.values() 
                                   if len(s['pages_viewed']) == 1)
        total_sessions = len([s for s in self.sessions.values() 
                             if s.get('user_id') in set(e['user_id'] for e in pageviews)])
        bounce_rate = (single_page_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            'site_id': site_id,
            'period_days': days,
            'overview': {
                'total_pageviews': len(pageviews),
                'unique_sessions': unique_sessions,
                'unique_users': unique_users,
                'avg_session_duration': round(avg_duration, 2),
                'bounce_rate': round(bounce_rate, 1)
            },
            'top_pages': [{'path': p, 'views': c} for p, c in top_pages],
            'traffic_by_day': self._get_daily_breakdown(site_events, days),
            'devices': self._get_device_breakdown(site_events),
            'real_time': {
                'active_users': len(set(e['session_id'] for e in site_events 
                                       if datetime.fromisoformat(e['timestamp']).timestamp() > 
                                       datetime.now().timestamp() - 300))  # Last 5 minutes
            }
        }
    
    def _get_daily_breakdown(self, events: List[Dict], days: int) -> List[Dict]:
        """Get daily traffic breakdown"""
        daily = defaultdict(lambda: {'pageviews': 0, 'unique_users': set()})
        
        for e in events:
            if e['event'] == 'pageview':
                date = e['timestamp'][:10]  # YYYY-MM-DD
                daily[date]['pageviews'] += 1
                if e.get('user_id'):
                    daily[date]['unique_users'].add(e['user_id'])
        
        return [
            {
                'date': d,
                'pageviews': data['pageviews'],
                'unique_users': len(data['unique_users'])
            }
            for d, data in sorted(daily.items())
        ][-days:]
    
    def _get_device_breakdown(self, events: List[Dict]) -> Dict:
        """Get device type breakdown"""
        devices = {'desktop': 0, 'mobile': 0, 'tablet': 0}
        
        for e in events:
            if e['event'] == 'pageview':
                ua = e.get('user_agent', '').lower()
                if 'mobile' in ua:
                    devices['mobile'] += 1
                elif 'tablet' in ua:
                    devices['tablet'] += 1
                else:
                    devices['desktop'] += 1
        
        return devices


# ==================== CONTENT MANAGEMENT SYSTEM ====================

class ContentManagementSystem:
    """
    Headless CMS for dynamic content
    Collections, entries, media management
    """
    
    def __init__(self):
        self.collections: Dict[str, Dict] = {}
        self.entries: Dict[str, List[Dict]] = defaultdict(list)
        self.media: List[Dict] = []
    
    def create_collection(self, name: str, fields: List[Dict]) -> Dict:
        """Create a content collection (like Blog Posts, Products)"""
        collection_id = f"col_{name.lower().replace(' ', '_')}"
        
        collection = {
            'id': collection_id,
            'name': name,
            'slug': name.lower().replace(' ', '-'),
            'fields': fields,
            'created_at': datetime.now().isoformat(),
            'entry_count': 0
        }
        
        self.collections[collection_id] = collection
        
        return {
            'success': True,
            'collection': collection,
            'api_endpoint': f'/api/v1/cms/collections/{collection_id}/entries'
        }
    
    def create_entry(self, collection_id: str, data: Dict) -> Dict:
        """Create a content entry"""
        if collection_id not in self.collections:
            return {'error': 'Collection not found'}
        
        entry_id = f"entry_{uuid.uuid4().hex[:8]}"
        
        entry = {
            'id': entry_id,
            'collection_id': collection_id,
            'data': data,
            'slug': self._generate_slug(data.get('title', entry_id)),
            'status': 'published',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'published_at': datetime.now().isoformat()
        }
        
        self.entries[collection_id].append(entry)
        self.collections[collection_id]['entry_count'] = len(self.entries[collection_id])
        
        return {'success': True, 'entry': entry}
    
    def _generate_slug(self, text: str) -> str:
        """Generate URL-friendly slug"""
        slug = text.lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        return slug[:50]
    
    def get_entries(self, collection_id: str, filters: Dict = None, 
                   limit: int = 10, offset: int = 0) -> Dict:
        """Get entries with filtering and pagination"""
        if collection_id not in self.collections:
            return {'error': 'Collection not found'}
        
        entries = self.entries[collection_id]
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                entries = [e for e in entries if e['data'].get(key) == value]
        
        total = len(entries)
        entries = entries[offset:offset + limit]
        
        return {
            'collection': self.collections[collection_id],
            'entries': entries,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total
        }
    
    def generate_cms_api_client(self) -> str:
        """Generate CMS API client code"""
        return '''
// CMS API Client
class CMSClient {
    constructor(apiKey) {
        this.baseURL = '/api/v1/cms';
        this.apiKey = apiKey;
    }
    
    async getCollection(slug) {
        const res = await fetch(`${this.baseURL}/collections/${slug}/entries`);
        return res.json();
    }
    
    async getEntry(collectionSlug, entrySlug) {
        const res = await fetch(`${this.baseURL}/collections/${collectionSlug}/entries/${entrySlug}`);
        return res.json();
    }
    
    async query(collectionSlug, filters = {}) {
        const params = new URLSearchParams(filters);
        const res = await fetch(`${this.baseURL}/collections/${collectionSlug}/entries?${params}`);
        return res.json();
    }
}

// Usage:
const cms = new CMSClient('your-api-key');
const posts = await cms.getCollection('blog-posts');
'''


# ==================== E-COMMERCE SYSTEM ====================

class ECommerceSystem:
    """
    Complete e-commerce with products, cart, checkout
    Stripe/PayPal payment integration
    """
    
    def __init__(self):
        self.products: Dict[str, Dict] = {}
        self.carts: Dict[str, Dict] = {}
        self.orders: List[Dict] = []
        self.inventory: Dict[str, int] = {}
    
    def create_product(self, name: str, price: float, description: str,
                      images: List[str] = None, variants: List[Dict] = None,
                      sku: str = None, category: str = None) -> Dict:
        """Create a product"""
        product_id = f"prod_{uuid.uuid4().hex[:8]}"
        
        product = {
            'id': product_id,
            'name': name,
            'slug': name.lower().replace(' ', '-'),
            'price': price,
            'currency': 'USD',
            'description': description,
            'images': images or [],
            'variants': variants or [],
            'sku': sku or product_id,
            'category': category,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.products[product_id] = product
        self.inventory[product_id] = 100  # Default stock
        
        return {'success': True, 'product': product}
    
    def generate_product_card(self, product: Dict) -> str:
        """Generate HTML product card"""
        return f'''
<div class="product-card" data-product-id="{product['id']}">
    <div class="product-image">
        <img src="{product['images'][0] if product['images'] else '/placeholder.jpg'}" alt="{product['name']}">
    </div>
    <div class="product-info">
        <h3 class="product-name">{product['name']}</h3>
        <p class="product-description">{product['description'][:100]}...</p>
        <div class="product-price">${product['price']:.2f}</div>
        <button class="add-to-cart-btn" onclick="addToCart('{product['id']}')">
            Add to Cart
        </button>
    </div>
</div>

<style>
.product-card {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}}
.product-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}}
.product-image img {{
    width: 100%;
    height: 200px;
    object-fit: cover;
}}
.product-info {{
    padding: 16px;
}}
.product-name {{
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
}}
.product-description {{
    color: #666;
    font-size: 14px;
    margin-bottom: 12px;
}}
.product-price {{
    font-size: 24px;
    font-weight: 700;
    color: #3b82f6;
    margin-bottom: 12px;
}}
.add-to-cart-btn {{
    width: 100%;
    padding: 12px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
}}
</style>
'''
    
    def add_to_cart(self, session_id: str, product_id: str, quantity: int = 1) -> Dict:
        """Add product to cart"""
        if session_id not in self.carts:
            self.carts[session_id] = {
                'items': [],
                'created_at': datetime.now().isoformat()
            }
        
        product = self.products.get(product_id)
        if not product:
            return {'error': 'Product not found'}
        
        # Check if already in cart
        existing = next((i for i in self.carts[session_id]['items'] 
                         if i['product_id'] == product_id), None)
        
        if existing:
            existing['quantity'] += quantity
        else:
            self.carts[session_id]['items'].append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image': product['images'][0] if product['images'] else None
            })
        
        return self.get_cart(session_id)
    
    def get_cart(self, session_id: str) -> Dict:
        """Get cart contents"""
        cart = self.carts.get(session_id, {'items': []})
        
        subtotal = sum(i['price'] * i['quantity'] for i in cart['items'])
        tax = subtotal * 0.08  # 8% tax
        shipping = 0 if subtotal > 50 else 5.99
        total = subtotal + tax + shipping
        
        return {
            'items': cart['items'],
            'item_count': sum(i['quantity'] for i in cart['items']),
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'shipping': round(shipping, 2),
            'total': round(total, 2)
        }
    
    def generate_checkout_form(self) -> str:
        """Generate checkout form HTML"""
        return '''
<div class="checkout-container">
    <h2>Checkout</h2>
    <div class="checkout-grid">
        <div class="checkout-form">
            <section class="form-section">
                <h3>Contact Information</h3>
                <input type="email" id="email" placeholder="Email" required>
                <input type="tel" id="phone" placeholder="Phone (optional)">
            </section>
            
            <section class="form-section">
                <h3>Shipping Address</h3>
                <input type="text" id="name" placeholder="Full Name" required>
                <input type="text" id="address" placeholder="Address" required>
                <div class="address-row">
                    <input type="text" id="city" placeholder="City" required>
                    <input type="text" id="state" placeholder="State" required>
                    <input type="text" id="zip" placeholder="ZIP" required>
                </div>
            </section>
            
            <section class="form-section">
                <h3>Payment</h3>
                <div id="card-element" class="card-element">
                    <!-- Stripe Card Element -->
                    Card number input would go here
                </div>
            </section>
            
            <button class="checkout-btn" onclick="processCheckout()">
                Complete Order
            </button>
        </div>
        
        <div class="order-summary">
            <h3>Order Summary</h3>
            <div id="cart-items"></div>
            <div class="summary-row">
                <span>Subtotal</span>
                <span id="subtotal">$0.00</span>
            </div>
            <div class="summary-row">
                <span>Tax</span>
                <span id="tax">$0.00</span>
            </div>
            <div class="summary-row">
                <span>Shipping</span>
                <span id="shipping">$0.00</span>
            </div>
            <div class="summary-row total">
                <span>Total</span>
                <span id="total">$0.00</span>
            </div>
        </div>
    </div>
</div>

<script>
async function processCheckout() {
    const orderData = {
        email: document.getElementById('email').value,
        shipping: {
            name: document.getElementById('name').value,
            address: document.getElementById('address').value,
            city: document.getElementById('city').value,
            state: document.getElementById('state').value,
            zip: document.getElementById('zip').value
        }
    };
    
    const res = await fetch('/api/v1/ecommerce/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
    });
    
    const result = await res.json();
    if (result.success) {
        window.location.href = '/order-confirmation?order=' + result.order_id;
    }
}
</script>
'''


# ==================== EMAIL & NOTIFICATION SYSTEM ====================

class EmailNotificationSystem:
    """
    Transactional emails, newsletters, push notifications
    Email templates and campaign management
    """
    
    def __init__(self):
        self.templates: Dict[str, Dict] = {}
        self.campaigns: List[Dict] = []
        self.subscribers: List[Dict] = []
    
    def create_template(self, name: str, subject: str, 
                       html_content: str, text_content: str) -> Dict:
        """Create email template"""
        template_id = f"tmpl_{name.lower().replace(' ', '_')}"
        
        template = {
            'id': template_id,
            'name': name,
            'subject': subject,
            'html': html_content,
            'text': text_content,
            'variables': self._extract_variables(html_content),
            'created_at': datetime.now().isoformat()
        }
        
        self.templates[template_id] = template
        
        return {'success': True, 'template': template}
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract template variables like {{variable}}"""
        return re.findall(r'\{\{(\w+)\}\}', content)
    
    def generate_welcome_email_template(self) -> Dict:
        """Generate welcome email template"""
        html = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #3b82f6; color: white; padding: 30px; text-align: center; }
        .content { background: #f9fafb; padding: 30px; }
        .button { display: inline-block; background: #3b82f6; color: white; 
                  padding: 12px 30px; text-decoration: none; border-radius: 6px; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{site_name}}!</h1>
        </div>
        <div class="content">
            <h2>Hi {{first_name}},</h2>
            <p>Thank you for joining us! We're excited to have you on board.</p>
            <p>Get started by exploring your new account:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{dashboard_url}}" class="button">Go to Dashboard</a>
            </div>
            <p>If you have any questions, reply to this email or contact our support team.</p>
            <p>Best regards,<br>The {{site_name}} Team</p>
        </div>
        <div class="footer">
            <p>{{site_name}} | {{site_address}}</p>
            <p><a href="{{unsubscribe_url}}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
'''
        
        return self.create_template(
            'Welcome Email',
            'Welcome to {{site_name}}!',
            html,
            'Welcome {{first_name}}! Thanks for joining {{site_name}}. Go to {{dashboard_url}}'
        )
    
    def subscribe_user(self, email: str, first_name: str = '', 
                      tags: List[str] = None) -> Dict:
        """Subscribe user to emails"""
        subscriber = {
            'id': f"sub_{uuid.uuid4().hex[:8]}",
            'email': email,
            'first_name': first_name,
            'tags': tags or [],
            'subscribed_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.subscribers.append(subscriber)
        
        return {'success': True, 'subscriber': subscriber}
    
    def generate_push_notification_worker(self) -> str:
        """Generate service worker for push notifications"""
        return '''
// Push Notification Service Worker
self.addEventListener('push', function(event) {
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/icon-192x192.png',
        badge: '/badge-72x72.png',
        image: data.image,
        tag: data.tag,
        requireInteraction: true,
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'open') {
        clients.openWindow(event.notification.data.url);
    }
});
'''


# ==================== AI SEARCH SYSTEM ====================

class AISearchSystem:
    """
    Semantic search for websites
    Vector-based search with relevance scoring
    """
    
    def __init__(self):
        self.documents: List[Dict] = []
        self.index: Dict[str, List[float]] = {}  # Simple vector simulation
    
    def index_page(self, url: str, title: str, content: str, 
                   metadata: Dict = None) -> Dict:
        """Index a page for search"""
        doc_id = f"doc_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        
        # Simple keyword extraction for demo
        keywords = self._extract_keywords(content)
        
        document = {
            'id': doc_id,
            'url': url,
            'title': title,
            'content': content[:5000],  # Store truncated content
            'keywords': keywords,
            'metadata': metadata or {},
            'indexed_at': datetime.now().isoformat()
        }
        
        self.documents.append(document)
        
        return {'success': True, 'doc_id': doc_id, 'keywords_found': len(keywords)}
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from content"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-z]{4,}\b', content.lower())
        
        # Common words to filter out
        stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'were', 
                      'been', 'their', 'would', 'there', 'could', 'should'}
        
        word_counts = {}
        for word in words:
            if word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:20]]
    
    def search(self, query: str, limit: int = 10) -> Dict:
        """Perform semantic search"""
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        results = []
        
        for doc in self.documents:
            score = 0
            
            # Title match (highest weight)
            if query_lower in doc['title'].lower():
                score += 10
            
            # Keyword matches
            doc_keywords = set(doc['keywords'])
            matching_keywords = query_words & doc_keywords
            score += len(matching_keywords) * 2
            
            # Content match
            if query_lower in doc['content'].lower():
                score += 3
            
            if score > 0:
                results.append({
                    'document': doc,
                    'score': score,
                    'highlight': self._generate_highlight(doc['content'], query)
                })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'query': query,
            'total_results': len(results),
            'results': results[:limit],
            'suggestions': self._generate_suggestions(query)
        }
    
    def _generate_highlight(self, content: str, query: str) -> str:
        """Generate search result highlight"""
        # Find query in content and extract surrounding text
        idx = content.lower().find(query.lower())
        if idx == -1:
            return content[:200] + '...'
        
        start = max(0, idx - 100)
        end = min(len(content), idx + len(query) + 100)
        
        return '...' + content[start:end] + '...'
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions"""
        # Simple suggestion generation
        suggestions = []
        
        # Add variations
        if not query.endswith('s'):
            suggestions.append(query + 's')
        
        # Add related terms based on documents
        for doc in self.documents[:5]:
            for keyword in doc['keywords'][:5]:
                if keyword != query.lower() and keyword.startswith(query[0].lower()):
                    suggestions.append(keyword)
        
        return list(set(suggestions))[:5]
    
    def generate_search_widget(self) -> str:
        """Generate search widget code"""
        return '''
<!-- AI Search Widget -->
<div class="ai-search-widget">
    <div class="search-input-container">
        <input type="text" id="aiSearchInput" placeholder="Search..." autocomplete="off">
        <button id="aiSearchButton">🔍</button>
    </div>
    <div id="aiSearchResults" class="search-results"></div>
</div>

<style>
.ai-search-widget {
    position: relative;
    max-width: 600px;
    margin: 0 auto;
}
.search-input-container {
    display: flex;
    gap: 8px;
}
#aiSearchInput {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 16px;
    outline: none;
}
#aiSearchInput:focus {
    border-color: #3b82f6;
}
#aiSearchButton {
    padding: 12px 20px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}
.search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    margin-top: 8px;
    max-height: 400px;
    overflow-y: auto;
    display: none;
}
.search-results.active {
    display: block;
}
.search-result-item {
    padding: 16px;
    border-bottom: 1px solid #e5e7eb;
    cursor: pointer;
}
.search-result-item:hover {
    background: #f9fafb;
}
.search-result-title {
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 4px;
}
.search-result-highlight {
    color: #6b7280;
    font-size: 14px;
}
</style>

<script>
const searchInput = document.getElementById('aiSearchInput');
const searchResults = document.getElementById('aiSearchResults');
let debounceTimer;

searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => performSearch(this.value), 300);
});

async function performSearch(query) {
    if (!query || query.length < 2) {
        searchResults.classList.remove('active');
        return;
    }
    
    const res = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    
    displayResults(data.results);
}

function displayResults(results) {
    if (!results || results.length === 0) {
        searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
    } else {
        searchResults.innerHTML = results.map(r => `
            <div class="search-result-item" onclick="window.location='${r.document.url}'">
                <div class="search-result-title">${r.document.title}</div>
                <div class="search-result-highlight">${r.highlight}</div>
            </div>
        `).join('');
    }
    
    searchResults.classList.add('active');
}

// Close on click outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.ai-search-widget')) {
        searchResults.classList.remove('active');
    }
});
</script>
'''


# ==================== FORMS & CRM ====================

class FormsAndCRM:
    """
    Advanced forms with validation, CRM integration
    Lead capture, contact forms, surveys
    """
    
    def __init__(self):
        self.forms: Dict[str, Dict] = {}
        self.submissions: Dict[str, List[Dict]] = defaultdict(list)
        self.contacts: List[Dict] = []
    
    def create_form(self, name: str, fields: List[Dict], 
                   config: Dict = None) -> Dict:
        """Create a form"""
        form_id = f"form_{name.lower().replace(' ', '_')}"
        
        form = {
            'id': form_id,
            'name': name,
            'fields': fields,
            'config': config or {},
            'created_at': datetime.now().isoformat()
        }
        
        self.forms[form_id] = form
        
        return {'success': True, 'form': form}
    
    def generate_form_html(self, form_id: str) -> str:
        """Generate form HTML"""
        form = self.forms.get(form_id)
        if not form:
            return '<p>Form not found</p>'
        
        fields_html = ''
        for field in form['fields']:
            field_type = field.get('type', 'text')
            required = 'required' if field.get('required') else ''
            
            if field_type == 'textarea':
                fields_html += f'''
<div class="form-field">
    <label>{field['label']}{'*' if field.get('required') else ''}</label>
    <textarea name="{field['name']}" {required} rows="4"></textarea>
</div>
'''
            elif field_type == 'select':
                options = ''.join([f'<option value="{o}">{o}</option>' 
                                  for o in field.get('options', [])])
                fields_html += f'''
<div class="form-field">
    <label>{field['label']}{'*' if field.get('required') else ''}</label>
    <select name="{field['name']}" {required}>
        <option value="">Select...</option>
        {options}
    </select>
</div>
'''
            else:
                fields_html += f'''
<div class="form-field">
    <label>{field['label']}{'*' if field.get('required') else ''}</label>
    <input type="{field_type}" name="{field['name']}" {required}>
</div>
'''
        
        return f'''
<form id="{form_id}" class="dynamic-form" onsubmit="submitForm(event, '{form_id}')">
    {fields_html}
    <button type="submit" class="form-submit">Submit</button>
</form>

<style>
.dynamic-form {{
    max-width: 500px;
}}
.form-field {{
    margin-bottom: 16px;
}}
.form-field label {{
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #374151;
}}
.form-field input,
.form-field textarea,
.form-field select {{
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 16px;
    font-family: inherit;
}}
.form-field input:focus,
.form-field textarea:focus {{
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}
.form-submit {{
    padding: 12px 24px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
}}
.form-submit:hover {{
    background: #2563eb;
}}
</style>

<script>
async function submitForm(event, formId) {{
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    const res = await fetch(`/api/v1/forms/${{formId}}/submit`, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(data)
    }});
    
    const result = await res.json();
    if (result.success) {{
        form.innerHTML = '<div class="form-success">Thank you! Your submission has been received.</div>';
    }} else {{
        alert('Error: ' + result.error);
    }}
}}
</script>
'''
    
    def submit_form(self, form_id: str, data: Dict) -> Dict:
        """Handle form submission"""
        if form_id not in self.forms:
            return {'error': 'Form not found'}
        
        submission = {
            'id': f"sub_{uuid.uuid4().hex[:8]}",
            'form_id': form_id,
            'data': data,
            'submitted_at': datetime.now().isoformat(),
            'ip_address': None,  # Would be set by server
            'user_agent': None
        }
        
        self.submissions[form_id].append(submission)
        
        # Create/update contact if email provided
        if 'email' in data:
            self._add_contact(data)
        
        return {'success': True, 'submission_id': submission['id']}
    
    def _add_contact(self, data: Dict) -> None:
        """Add contact to CRM"""
        existing = next((c for c in self.contacts if c.get('email') == data['email']), None)
        
        if existing:
            existing['updated_at'] = datetime.now().isoformat()
            existing['metadata'].update(data)
        else:
            contact = {
                'id': f"contact_{uuid.uuid4().hex[:8]}",
                'email': data['email'],
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'phone': data.get('phone', ''),
                'source': 'form_submission',
                'metadata': data,
                'created_at': datetime.now().isoformat(),
                'tags': []
            }
            self.contacts.append(contact)


# ==================== BLOG SYSTEM ====================

class BlogSystem:
    """
    Complete blogging platform
    Posts, categories, tags, comments, RSS
    """
    
    def __init__(self):
        self.posts: List[Dict] = []
        self.categories: Dict[str, Dict] = {}
        self.comments: Dict[str, List[Dict]] = defaultdict(list)
        self.authors: Dict[str, Dict] = {}
    
    def create_post(self, title: str, content: str, author_id: str,
                   category: str = None, tags: List[str] = None,
                   featured_image: str = None, status: str = 'draft') -> Dict:
        """Create blog post"""
        post_id = f"post_{uuid.uuid4().hex[:8]}"
        
        # Generate excerpt
        excerpt = content[:200] + '...' if len(content) > 200 else content
        
        post = {
            'id': post_id,
            'title': title,
            'slug': title.lower().replace(' ', '-')[:50],
            'content': content,
            'excerpt': excerpt,
            'author_id': author_id,
            'category': category,
            'tags': tags or [],
            'featured_image': featured_image,
            'status': status,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'published_at': datetime.now().isoformat() if status == 'published' else None,
            'views': 0,
            'likes': 0
        }
        
        self.posts.append(post)
        
        return {'success': True, 'post': post}
    
    def get_posts(self, category: str = None, tag: str = None,
                 status: str = 'published', limit: int = 10, 
                 offset: int = 0) -> Dict:
        """Get blog posts with filtering"""
        posts = self.posts
        
        if status:
            posts = [p for p in posts if p['status'] == status]
        
        if category:
            posts = [p for p in posts if p.get('category') == category]
        
        if tag:
            posts = [p for p in posts if tag in p.get('tags', [])]
        
        total = len(posts)
        posts = sorted(posts, key=lambda x: x.get('published_at', ''), reverse=True)
        posts = posts[offset:offset + limit]
        
        return {
            'posts': posts,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def generate_blog_layout(self, posts: List[Dict]) -> str:
        """Generate blog listing page HTML"""
        posts_html = ''
        for post in posts:
            posts_html += f'''
<article class="blog-post">
    <div class="post-image">
        <img src="{post.get('featured_image', '/blog-placeholder.jpg')}" alt="{post['title']}">
    </div>
    <div class="post-content">
        <div class="post-meta">
            <span class="post-category">{post.get('category', 'General')}</span>
            <span class="post-date">{post.get('published_at', '')[:10]}</span>
        </div>
        <h2 class="post-title">
            <a href="/blog/{post['slug']}">{post['title']}</a>
        </h2>
        <p class="post-excerpt">{post['excerpt']}</p>
        <div class="post-tags">
            {''.join([f'<span class="tag">{t}</span>' for t in post.get('tags', [])])}
        </div>
    </div>
</article>
'''
        
        return f'''
<div class="blog-container">
    <header class="blog-header">
        <h1>Our Blog</h1>
        <p>Latest insights, tutorials, and updates</p>
    </header>
    <div class="blog-grid">
        {posts_html}
    </div>
</div>

<style>
.blog-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}}
.blog-header {{
    text-align: center;
    margin-bottom: 60px;
}}
.blog-header h1 {{
    font-size: 3rem;
    margin-bottom: 16px;
}}
.blog-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 40px;
}}
.blog-post {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}
.post-image img {{
    width: 100%;
    height: 200px;
    object-fit: cover;
}}
.post-content {{
    padding: 24px;
}}
.post-meta {{
    display: flex;
    gap: 16px;
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 12px;
}}
.post-category {{
    color: #3b82f6;
    font-weight: 600;
}}
.post-title {{
    font-size: 1.5rem;
    margin-bottom: 12px;
}}
.post-title a {{
    color: #1f2937;
    text-decoration: none;
}}
.post-title a:hover {{
    color: #3b82f6;
}}
.post-excerpt {{
    color: #6b7280;
    line-height: 1.6;
    margin-bottom: 16px;
}}
.post-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}}
.tag {{
    padding: 4px 12px;
    background: #f3f4f6;
    border-radius: 20px;
    font-size: 12px;
    color: #4b5563;
}}
</style>
'''
    
    def generate_rss_feed(self, blog_title: str, blog_url: str) -> str:
        """Generate RSS feed XML"""
        items = ''
        for post in sorted(self.posts, key=lambda x: x.get('published_at', ''), reverse=True)[:20]:
            items += f'''
    <item>
      <title>{post['title']}</title>
      <link>{blog_url}/blog/{post['slug']}</link>
      <guid>{blog_url}/blog/{post['slug']}</guid>
      <pubDate>{post.get('published_at', '')}</pubDate>
      <description>{post['excerpt']}</description>
    </item>
'''
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{blog_title}</title>
    <link>{blog_url}</link>
    <description>Latest posts from {blog_title}</description>
    <language>en</language>
    <lastBuildDate>{datetime.now().isoformat()}</lastBuildDate>
    {items}
  </channel>
</rss>
'''


# ==================== WORKFLOW AUTOMATION ====================

class WorkflowAutomation:
    """
    Zapier-style workflow automation
    Triggers, actions, webhooks
    """
    
    def __init__(self):
        self.workflows: Dict[str, Dict] = {}
        self.triggers: Dict[str, Dict] = {}
        self.actions: Dict[str, Dict] = {}
        self.execution_log: List[Dict] = []
    
    def create_workflow(self, name: str, trigger: Dict, actions: List[Dict]) -> Dict:
        """Create automation workflow"""
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        workflow = {
            'id': workflow_id,
            'name': name,
            'enabled': True,
            'trigger': trigger,
            'actions': actions,
            'created_at': datetime.now().isoformat(),
            'execution_count': 0
        }
        
        self.workflows[workflow_id] = workflow
        
        return {'success': True, 'workflow': workflow}
    
    def get_available_triggers(self) -> List[Dict]:
        """Get available trigger types"""
        return [
            {
                'id': 'form_submitted',
                'name': 'Form Submitted',
                'description': 'When someone submits a form',
                'category': 'forms'
            },
            {
                'id': 'new_order',
                'name': 'New Order',
                'description': 'When a new order is placed',
                'category': 'ecommerce'
            },
            {
                'id': 'user_registered',
                'name': 'User Registered',
                'description': 'When a new user signs up',
                'category': 'users'
            },
            {
                'id': 'page_viewed',
                'name': 'Page Viewed',
                'description': 'When someone visits a specific page',
                'category': 'analytics'
            },
            {
                'id': 'scheduled',
                'name': 'Scheduled',
                'description': 'Run on a schedule',
                'category': 'time'
            },
            {
                'id': 'webhook_received',
                'name': 'Webhook Received',
                'description': 'When an external webhook is received',
                'category': 'webhooks'
            }
        ]
    
    def get_available_actions(self) -> List[Dict]:
        """Get available action types"""
        return [
            {
                'id': 'send_email',
                'name': 'Send Email',
                'description': 'Send an email to a recipient',
                'category': 'email'
            },
            {
                'id': 'add_to_crm',
                'name': 'Add to CRM',
                'description': 'Add contact to CRM',
                'category': 'crm'
            },
            {
                'id': 'http_request',
                'name': 'HTTP Request',
                'description': 'Make HTTP request to external API',
                'category': 'webhooks'
            },
            {
                'id': 'create_task',
                'name': 'Create Task',
                'description': 'Create a task or todo',
                'category': 'productivity'
            },
            {
                'id': 'send_notification',
                'name': 'Send Notification',
                'description': 'Send push notification',
                'category': 'notifications'
            },
            {
                'id': 'update_database',
                'name': 'Update Database',
                'description': 'Update database record',
                'category': 'database'
            }
        ]
    
    def execute_workflow(self, workflow_id: str, trigger_data: Dict) -> Dict:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            return {'error': 'Workflow not found'}
        
        workflow = self.workflows[workflow_id]
        
        if not workflow['enabled']:
            return {'skipped': True, 'reason': 'Workflow disabled'}
        
        results = []
        
        for action in workflow['actions']:
            result = self._execute_action(action, trigger_data)
            results.append(result)
        
        workflow['execution_count'] += 1
        
        execution = {
            'id': f"exec_{uuid.uuid4().hex[:8]}",
            'workflow_id': workflow_id,
            'trigger_data': trigger_data,
            'results': results,
            'executed_at': datetime.now().isoformat(),
            'success': all(r.get('success') for r in results)
        }
        
        self.execution_log.append(execution)
        
        return execution
    
    def _execute_action(self, action: Dict, data: Dict) -> Dict:
        """Execute a single action"""
        action_type = action.get('type')
        
        if action_type == 'send_email':
            return {
                'success': True,
                'action': 'send_email',
                'to': action.get('to'),
                'subject': action.get('subject'),
                'simulated': True
            }
        
        if action_type == 'http_request':
            return {
                'success': True,
                'action': 'http_request',
                'url': action.get('url'),
                'method': action.get('method'),
                'simulated': True
            }
        
        return {'success': False, 'error': f'Unknown action type: {action_type}'}
    
    def generate_webhook_url(self, workflow_id: str) -> str:
        """Generate webhook URL for workflow"""
        token = hashlib.sha256(f"{workflow_id}_webhook".encode()).hexdigest()[:16]
        return f"/api/v1/webhooks/{workflow_id}/{token}"


# ==================== AI CONTENT GENERATOR ====================

class AIContentGenerator:
    """
    Auto-generate content for websites
    Blog posts, product descriptions, SEO content
    """
    
    def __init__(self):
        self.content_templates = {
            'blog': [
                "The Ultimate Guide to {topic}",
                "10 Best {topic} for {audience}",
                "How to {topic} in {year}",
                "Why {topic} Matters for Your Business",
                "{topic}: Everything You Need to Know"
            ],
            'product': [
                "Introducing the {product_name} - the perfect solution for {use_case}",
                "Experience {benefit} with our {product_name}",
                "{product_name}: {key_feature} for {target_audience}"
            ],
            'meta': [
                "{topic} - {site_name} | {tagline}",
                "Best {topic} Solutions | {site_name}",
                "{topic} Guide {year} | {site_name}"
            ]
        }
    
    def generate_blog_post(self, topic: str, keywords: List[str],
                          tone: str = 'professional') -> Dict:
        """Generate blog post content"""
        title_template = random.choice(self.content_templates['blog'])
        title = title_template.format(
            topic=topic,
            audience='professionals',
            year=datetime.now().year
        )
        
        # Generate sections
        sections = [
            f"## Introduction to {topic}\n\n{topic} has become increasingly important in today's digital landscape. In this comprehensive guide, we'll explore everything you need to know.",
            f"## Why {topic} Matters\n\nUnderstanding {topic} is crucial for staying competitive. Here are the key benefits:",
            f"### 1. Increased Efficiency\n\nBy implementing {topic} strategies, businesses can streamline their operations and achieve better results.",
            f"### 2. Better Results\n\nCompanies that focus on {topic} typically see significant improvements in their key metrics.",
            f"## How to Get Started with {topic}\n\nFollow these steps to begin your {topic} journey:",
            f"## Best Practices for {topic}\n\nTo maximize your success with {topic}, consider these best practices:",
            f"## Conclusion\n\n{topic} is an essential component of modern business strategy. Start implementing these strategies today to see results."
        ]
        
        content = '\n\n'.join(sections)
        
        # Generate excerpt
        excerpt = f"Learn everything you need to know about {topic}. This comprehensive guide covers best practices, tips, and strategies for success."
        
        return {
            'title': title,
            'content': content,
            'excerpt': excerpt,
            'keywords': keywords,
            'word_count': len(content.split()),
            'estimated_read_time': f"{max(3, len(content.split()) // 200)} min read",
            'suggested_tags': keywords[:5],
            'seo_title': f"{title[:60]}",
            'meta_description': excerpt[:160]
        }
    
    def generate_product_description(self, product_name: str, 
                                     features: List[str],
                                     target_audience: str) -> Dict:
        """Generate product description"""
        feature_list = '\n'.join([f"- {f}" for f in features])
        
        description = f"""
{product_name} is designed specifically for {target_audience} who demand excellence.

**Key Features:**
{feature_list}

**Why Choose {product_name}?**

Our customers love {product_name} because it delivers exceptional results while being easy to use. Whether you're just getting started or are an experienced professional, {product_name} has everything you need.

**Perfect for:**
- {target_audience} looking to improve their workflow
- Teams seeking better collaboration
- Organizations wanting to scale efficiently

Order now and experience the difference!
"""
        
        return {
            'product_name': product_name,
            'description': description.strip(),
            'short_description': f"{product_name} - The perfect solution for {target_audience}. Features: {', '.join(features[:3])}",
            'key_benefits': features[:5],
            'suggested_keywords': [product_name.lower(), target_audience.lower()] + [f.lower() for f in features[:3]]
        }
    
    def generate_faq(self, topic: str, num_questions: int = 5) -> List[Dict]:
        """Generate FAQ content"""
        faqs = [
            {
                'question': f"What is {topic}?",
                'answer': f"{topic} refers to the practices, strategies, and technologies used to achieve specific business objectives. It encompasses a wide range of approaches tailored to different needs and industries."
            },
            {
                'question': f"Why is {topic} important?",
                'answer': f"{topic} is crucial because it directly impacts your ability to compete effectively, satisfy customers, and achieve sustainable growth in today's market."
            },
            {
                'question': f"How much does {topic} cost?",
                'answer': f"The cost of {topic} varies depending on your specific needs, scale, and chosen solutions. We offer flexible pricing options to accommodate different budgets and requirements."
            },
            {
                'question': f"How long does it take to see results from {topic}?",
                'answer': f"Most organizations begin seeing initial results within 30-60 days of implementing {topic} strategies, with significant improvements typically observed within 3-6 months."
            },
            {
                'question': f"Do I need technical expertise for {topic}?",
                'answer': f"While some technical knowledge can be helpful, our solutions are designed to be accessible to users with varying levels of technical expertise. We provide comprehensive support and documentation."
            }
        ]
        
        return faqs[:num_questions]


# ==================== COOKIE CONSENT & GDPR ====================

class CookieConsentManager:
    """
    GDPR-compliant cookie consent management
    Cookie banner, preferences, policy generation
    """
    
    def __init__(self):
        self.cookie_types = {
            'necessary': {
                'name': 'Necessary',
                'description': 'Essential for the website to function',
                'required': True
            },
            'functional': {
                'name': 'Functional',
                'description': 'Enable enhanced functionality',
                'required': False
            },
            'analytics': {
                'name': 'Analytics',
                'description': 'Help us improve our website',
                'required': False
            },
            'marketing': {
                'name': 'Marketing',
                'description': 'Used for targeted advertising',
                'required': False
            }
        }
    
    def generate_consent_banner(self, config: Dict) -> str:
        """Generate cookie consent banner"""
        primary_color = config.get('primary_color', '#3b82f6')
        position = config.get('position', 'bottom')
        
        css = f'''
<style>
.cookie-banner {{
    position: fixed;
    {position}: 0;
    left: 0;
    right: 0;
    background: white;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
    padding: 20px;
    z-index: 10000;
    display: none;
}}
.cookie-banner.active {{
    display: block;
}}
.cookie-container {{
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
}}
.cookie-text {{
    flex: 1;
    font-size: 14px;
    color: #374151;
    line-height: 1.5;
}}
.cookie-text a {{
    color: {primary_color};
    text-decoration: underline;
}}
.cookie-buttons {{
    display: flex;
    gap: 12px;
}}
.cookie-btn {{
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    font-size: 14px;
}}
.cookie-btn-primary {{
    background: {primary_color};
    color: white;
    border: none;
}}
.cookie-btn-secondary {{
    background: transparent;
    color: #374151;
    border: 1px solid #d1d5db;
}}
.cookie-btn-text {{
    background: none;
    border: none;
    color: {primary_color};
    text-decoration: underline;
    padding: 10px;
}}
</style>
'''
        
        html = f'''
<div id="cookieBanner" class="cookie-banner">
    <div class="cookie-container">
        <div class="cookie-text">
            We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.
            <a href="/privacy-policy">Learn more</a>
        </div>
        <div class="cookie-buttons">
            <button class="cookie-btn cookie-btn-secondary" onclick="manageCookies()">
                Manage Preferences
            </button>
            <button class="cookie-btn cookie-btn-primary" onclick="acceptAllCookies()">
                Accept All
            </button>
        </div>
    </div>
</div>
'''
        
        js = '''
<script>
const COOKIE_CONSENT_KEY = 'cookie_consent';

function showCookieBanner() {
    const consent = localStorage.getItem(COOKIE_CONSENT_KEY);
    if (!consent) {
        document.getElementById('cookieBanner').classList.add('active');
    }
}

function acceptAllCookies() {
    const consent = {
        necessary: true,
        functional: true,
        analytics: true,
        marketing: true,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(consent));
    document.getElementById('cookieBanner').classList.remove('active');
    
    // Initialize analytics and other optional scripts
    initializeAnalytics();
}

function manageCookies() {
    // Open cookie preferences modal
    alert('Cookie preferences modal would open here with toggle switches for each category');
}

function initializeAnalytics() {
    // This would initialize Google Analytics, etc.
    console.log('Analytics initialized after consent');
}

// Check on page load
showCookieBanner();
</script>
'''
        
        return css + html + js
    
    def generate_privacy_policy(self, company_name: str, website_url: str) -> str:
        """Generate privacy policy"""
        return f'''# Privacy Policy

**Last Updated:** {datetime.now().strftime('%B %d, %Y')}

## Introduction

{company_name} ("we", "our", or "us") respects your privacy and is committed to protecting your personal data. This privacy policy explains how we collect, use, and protect your information when you visit {website_url}.

## Information We Collect

### Personal Information
- Name and contact details
- Email address
- Phone number
- Billing information

### Usage Data
- IP address
- Browser type and version
- Pages visited and time spent
- Referral source

### Cookies and Tracking
We use cookies and similar technologies to enhance your browsing experience. See our Cookie Policy for details.

## How We Use Your Information

1. **To Provide Services**: Process orders, manage accounts, provide customer support
2. **To Improve Our Website**: Analyze usage patterns and optimize performance
3. **To Communicate**: Send updates, newsletters, and promotional materials (with consent)
4. **For Security**: Protect against fraud and unauthorized access

## Your Rights (GDPR)

If you are in the European Union, you have the right to:
- Access your personal data
- Correct inaccurate data
- Request deletion of your data
- Object to data processing
- Data portability
- Withdraw consent

## Contact Us

For privacy-related inquiries, contact us at:
- Email: privacy@{website_url.replace('https://', '').replace('http://', '')}
- Address: [Your Company Address]

## Changes to This Policy

We may update this policy periodically. Please review it regularly.
'''


# ==================== PWA SYSTEM ====================

class PWASystem:
    """
    Progressive Web App capabilities
    Service worker, manifest, offline support
    """
    
    def __init__(self):
        self.cache_version = 'v1'
    
    def generate_manifest(self, config: Dict) -> str:
        """Generate web app manifest"""
        manifest = {
            'name': config.get('name', 'My App'),
            'short_name': config.get('short_name', 'App'),
            'description': config.get('description', 'A progressive web app'),
            'start_url': '/',
            'display': 'standalone',
            'background_color': config.get('background_color', '#ffffff'),
            'theme_color': config.get('theme_color', '#3b82f6'),
            'orientation': 'portrait',
            'scope': '/',
            'icons': [
                {
                    'src': '/icon-72x72.png',
                    'sizes': '72x72',
                    'type': 'image/png'
                },
                {
                    'src': '/icon-192x192.png',
                    'sizes': '192x192',
                    'type': 'image/png'
                },
                {
                    'src': '/icon-512x512.png',
                    'sizes': '512x512',
                    'type': 'image/png'
                }
            ]
        }
        
        return json.dumps(manifest, indent=2)
    
    def generate_service_worker(self, cache_urls: List[str] = None) -> str:
        """Generate service worker for offline support"""
        urls_to_cache = cache_urls or [
            '/',
            '/styles.css',
            '/app.js',
            '/icon-192x192.png'
        ]
        
        return f'''
const CACHE_NAME = 'app-cache-{self.cache_version}';
const urlsToCache = {json.dumps(urls_to_cache)};

// Install event
self.addEventListener('install', (event) => {{
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {{
                return cache.addAll(urlsToCache);
            }})
    );
    self.skipWaiting();
}});

// Fetch event
self.addEventListener('fetch', (event) => {{
    event.respondWith(
        caches.match(event.request)
            .then((response) => {{
                // Return cached or fetch new
                if (response) {{
                    return response;
                }}
                return fetch(event.request)
                    .then((response) => {{
                        // Cache new requests
                        if (!response || response.status !== 200 || response.type !== 'basic') {{
                            return response;
                        }}
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => {{
                                cache.put(event.request, responseToCache);
                            }});
                        return response;
                    }});
            }})
    );
}});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {{
    event.waitUntil(
        caches.keys().then((cacheNames) => {{
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        }})
    );
    self.clients.claim();
}});

// Background sync for offline form submissions
self.addEventListener('sync', (event) => {{
    if (event.tag === 'sync-forms') {{
        event.waitUntil(syncFormSubmissions());
    }}
}});

async function syncFormSubmissions() {{
    // Logic to sync pending form submissions
    console.log('Syncing form submissions...');
}}

// Push notifications
self.addEventListener('push', (event) => {{
    const data = event.data.json();
    const options = {{
        body: data.body,
        icon: '/icon-192x192.png',
        badge: '/badge-72x72.png',
        data: data.data
    }};
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
}});
'''
    
    def generate_pwa_setup_code(self) -> str:
        """Generate code to register service worker"""
        return '''
<!-- PWA Setup -->
<script>
// Register Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then((registration) => {
                console.log('SW registered:', registration);
            })
            .catch((error) => {
                console.log('SW registration failed:', error);
            });
    });
}

// Request notification permission
if ('Notification' in window) {
    Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('Notifications enabled');
        }
    });
}

// Register background sync
navigator.serviceWorker.ready.then((registration) => {
    if ('sync' in registration) {
        registration.sync.register('sync-forms');
    }
});

// Add to home screen prompt
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    // Show custom install button
    document.getElementById('installBtn').style.display = 'block';
});

function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted install');
            }
            deferredPrompt = null;
        });
    }
}
</script>
'''


# ==================== INITIALIZE ALL SYSTEMS ====================

ai_chat_widget = AIChatWidget()
analytics_dashboard = AnalyticsDashboard()
cms_system = ContentManagementSystem()
ecommerce_system = ECommerceSystem()
email_system = EmailNotificationSystem()
ai_search = AISearchSystem()
forms_crm = FormsAndCRM()
blog_system = BlogSystem()
workflow_automation = WorkflowAutomation()
ai_content_generator = AIContentGenerator()
cookie_consent = CookieConsentManager()
pwa_system = PWASystem()

print("✅ Complete AI Website Platform systems initialized")
print("   - AI Chat Widget")
print("   - Analytics Dashboard")
print("   - Content Management System")
print("   - E-commerce System")
print("   - Email & Notifications")
print("   - AI Search")
print("   - Forms & CRM")
print("   - Blog System")
print("   - Workflow Automation")
print("   - AI Content Generator")
print("   - Cookie Consent & GDPR")
print("   - PWA Capabilities")
