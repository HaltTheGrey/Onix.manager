#!/usr/bin/env python3
"""
Simple test to verify application startup without hanging.
"""

import sys
import os
import time

print("Starting application test...")

try:
    print("1. Testing imports...")
    
    # Test core imports first
    from chamber_app.core.chamber_state import ChamberType, ChamberStatus
    print("   ✓ Core types imported")
    
    from chamber_app.utils import get_logger
    print("   ✓ Utilities imported")
    
    from chamber_app.core.application import ChamberApplication
    print("   ✓ Application imported")
    
    print("2. Testing application creation...")
    app = ChamberApplication()
    print("   ✓ Application created")
    
    print("3. Testing basic functionality...")
    
    # Test chamber retrieval without starting the full app
    chambers = app.get_all_chambers()
    print(f"   ✓ Retrieved {len(chambers)} chambers")
    
    # Test chamber type filtering
    hass_chambers = app.get_chambers_by_type(ChamberType.HASS)
    print(f"   ✓ Found {len(hass_chambers)} HASS chambers")
    
    tvac_chambers = app.get_chambers_by_type(ChamberType.TVAC)  
    print(f"   ✓ Found {len(tvac_chambers)} TVAC chambers")
    
    thermal_chambers = app.get_chambers_by_type(ChamberType.THERMAL)
    print(f"   ✓ Found {len(thermal_chambers)} THERMAL chambers")
    
    print("🎉 Application startup test PASSED!")
    print("✅ No circular import issues detected")
    print("✅ Application can be created and used")
    
except Exception as e:
    print(f"❌ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTest completed successfully!")
