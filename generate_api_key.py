#!/usr/bin/env python3
"""
One-time API Key Generator for Admin Dashboard
Run this to create a permanent, unlimited API key for frontend connection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_ecosystem.api_key_manager import api_key_manager, Role

def generate_admin_api_key():
    """Generate unlimited admin API key for frontend."""
    
    print("="*60)
    print("OraclAI - API KEY GENERATOR")
    print("="*60)
    
    # Generate key with unlimited rate limit
    key, api_key = api_key_manager.generate_key(
        name="Frontend Dashboard - Unlimited",
        role=Role.ADMIN,
        rate_limit=100000  # Effectively unlimited
    )
    
    print("\n✅ API Key Generated Successfully!")
    print("\n" + "="*60)
    print("YOUR API KEY (COPY THIS NOW - WON'T BE SHOWN AGAIN):")
    print("="*60)
    print(f"\n{key}\n")
    print("="*60)
    print("\nKey Details:")
    print(f"  - ID: {api_key.id}")
    print(f"  - Role: {api_key.role.value}")
    print(f"  - Rate Limit: {api_key.rate_limit} requests/min")
    print(f"  - Created: {api_key.created_at}")
    print("\nUsage in Frontend:")
    print('  headers: { "Authorization": "Bearer ' + key + '" }')
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Save this key in a secure location!")
    print("="*60)
    
    # Also save to file for convenience
    key_file = os.path.join(os.path.dirname(__file__), 'frontend_api_key.txt')
    with open(key_file, 'w') as f:
        f.write(f"API Key: {key}\n")
        f.write(f"Generated: {api_key.created_at}\n")
        f.write(f"Role: {api_key.role.value}\n")
        f.write(f"Rate Limit: {api_key.rate_limit}/min\n")
    
    print(f"\nKey also saved to: {key_file}")
    
    return key

if __name__ == "__main__":
    try:
        key = generate_admin_api_key()
        
        # Test the key
        print("\n🔍 Testing key validation...")
        api_key = api_key_manager.validate_key(key)
        
        if api_key:
            print(f"✅ Key is valid! Role: {api_key.role.value}")
        else:
            print("❌ Key validation failed")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
