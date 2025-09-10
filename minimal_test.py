#!/usr/bin/env python3
"""
Minimal test to isolate import issues
"""

print("Starting import test...")

try:
    print("1. Testing basic imports...")
    import sys
    import os
    print("   ✓ Basic imports OK")
    
    print("2. Testing chamber_app package...")
    import chamber_app
    print("   ✓ Package import OK")
    
    print("3. Testing utils imports...")
    from chamber_app.utils.config import load_config
    print("   ✓ Config import OK")
    
    print("4. Testing core chamber imports...")
    from chamber_app.core.chamber import Chamber
    print("   ✓ Chamber import OK")
    
    print("5. Testing core state imports...")  
    from chamber_app.core.chamber_state import ChamberType
    print("   ✓ Chamber state import OK")
    
    print("6. Testing application import...")
    from chamber_app.core.application import ChamberApplication
    print("   ✓ Application import OK")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
