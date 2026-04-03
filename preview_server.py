"""
OraclAI Website Preview Server
Manages website preview instances with custom URLs
"""

import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import json

# Store for generated websites
WEBSITE_STORE = {}
WEBSITE_STORE_LOCK = threading.Lock()

class PreviewServer:
    """
    Manages website previews with unique URLs
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.previews: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def create_preview(self, website_code: str, project_id: str = None) -> Dict:
        """
        Create a new website preview
        Returns preview URL and metadata
        """
        # Generate unique preview ID
        preview_id = project_id or f"preview_{uuid.uuid4().hex[:12]}"
        
        # Store website code
        with self.lock:
            self.previews[preview_id] = {
                'id': preview_id,
                'code': website_code,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
                'view_count': 0,
                'is_active': True
            }
        
        # Generate custom URL
        preview_url = f"{self.base_url}/preview/{preview_id}"
        
        return {
            'preview_id': preview_id,
            'preview_url': preview_url,
            'custom_url': preview_url,
            'created_at': datetime.now().isoformat(),
            'expires_in': '7 days',
            'status': 'active'
        }
    
    def get_preview(self, preview_id: str) -> Optional[Dict]:
        """Get preview by ID"""
        with self.lock:
            preview = self.previews.get(preview_id)
            if preview and preview['is_active']:
                # Increment view count
                preview['view_count'] += 1
                return preview
            return None
    
    def get_preview_html(self, preview_id: str) -> Optional[str]:
        """Get website HTML for preview"""
        preview = self.get_preview(preview_id)
        if preview:
            return preview['code']
        return None
    
    def list_previews(self) -> List[Dict]:
        """List all active previews"""
        with self.lock:
            return [
                {
                    'id': p['id'],
                    'created_at': p['created_at'],
                    'view_count': p['view_count'],
                    'preview_url': f"{self.base_url}/preview/{p['id']}"
                }
                for p in self.previews.values()
                if p['is_active']
            ]
    
    def delete_preview(self, preview_id: str) -> bool:
        """Delete a preview"""
        with self.lock:
            if preview_id in self.previews:
                self.previews[preview_id]['is_active'] = False
                return True
            return False


# Singleton
preview_server = PreviewServer()
