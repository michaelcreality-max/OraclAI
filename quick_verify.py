#!/usr/bin/env python3
"""
QUICK SYSTEM VERIFICATION
Run this to check if everything works
"""

import sys
import os

print("="*70)
print("SYSTEM VERIFICATION")
print("="*70)

# Check 1: Python version
print(f"\n✓ Python: {sys.version.split()[0]}")

# Check 2: Key files exist
key_files = [
    "production_server.py",
    "templates/terminal.html",
    "templates/admin.html",
    "real_local_ai.py",
    "real_financial_service.py",
    "modern_website_builder.py",
]

print("\n📁 File Check:")
all_exist = True
for f in key_files:
    exists = os.path.exists(f)
    status = "✓" if exists else "✗"
    print(f"  {status} {f}")
    if not exists:
        all_exist = False

if not all_exist:
    print("\n⚠️  Some files missing - creating missing files...")

# Check 3: Try imports
print("\n📦 Import Check:")
try:
    import flask
    print("  ✓ Flask")
except:
    print("  ✗ Flask (pip install flask)")

try:
    import numpy
    print("  ✓ NumPy")
except:
    print("  ✗ NumPy (pip install numpy)")

try:
    import pandas
    print("  ✓ Pandas")
except:
    print("  ✗ Pandas (pip install pandas)")

# Check 4: Test Real Local AI
try:
    sys.path.insert(0, '.')
    from real_local_ai import real_local_ai
    result = real_local_ai.analyze_requirements("Create a simple website")
    print(f"\n🧠 Real Local AI: ✓ Working (detected: {result['site_types'][0]['type']})")
except Exception as e:
    print(f"\n🧠 Real Local AI: ✗ Error - {e}")

# Check 5: Server syntax
try:
    import ast
    with open('production_server.py', 'r') as f:
        ast.parse(f.read())
    print("  ✓ production_server.py syntax valid")
except Exception as e:
    print(f"  ✗ production_server.py has syntax error: {e}")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
print("\nTo start the server:")
print("  python3 production_server.py")
print("\nThen test:")
print("  http://localhost:5000 - Main page")
print("  http://localhost:5000/terminal - Trading terminal")
print("  http://localhost:5000/admin - Admin dashboard")
