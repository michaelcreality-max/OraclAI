#!/usr/bin/env python3
"""
INTEGRATION TEST - Check if Superior AI actually works
"""

import sys
sys.path.insert(0, '/Users/joanna/Downloads/VSCode Folder (python)')

print("="*60)
print("SUPERIOR AI INTEGRATION TEST")
print("="*60)

# Test 1: Import
print("\n[1] Testing import...")
try:
    from multi_domain.truly_superior_ai import SuperiorAI
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Instantiation
print("\n[2] Testing instantiation...")
try:
    ai = SuperiorAI()
    print("✓ SuperiorAI instantiated")
except Exception as e:
    print(f"✗ Instantiation failed: {e}")
    sys.exit(1)

# Test 3: Basic query
print("\n[3] Testing basic query...")
try:
    result = ai.answer("What is 2+2?")
    print(f"✓ Query answered")
    print(f"  Confidence: {result['confidence']:.0%}")
    print(f"  Answer: {result['answer'][:100]}...")
except Exception as e:
    print(f"✗ Query failed: {e}")

# Test 4: Programming query
print("\n[4] Testing programming query...")
try:
    result = ai.answer("How do I fix a Python NameError?")
    print(f"✓ Programming query answered")
    print(f"  Experts consulted: {', '.join(set(result['experts_consulted']))}")
    print(f"  Confidence: {result['confidence']:.0%}")
except Exception as e:
    print(f"✗ Programming query failed: {e}")

# Test 5: Math query
print("\n[5] Testing math query...")
try:
    result = ai.answer("What's the probability of rolling two sixes?")
    print(f"✓ Math query answered")
    print(f"  Confidence: {result['confidence']:.0%}")
except Exception as e:
    print(f"✗ Math query failed: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
