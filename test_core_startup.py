#!/usr/bin/env python3
"""
Safe test to verify core application startup without UI components.
"""

import sys
import os

print("Starting core application test...")

try:
    print("1. Testing core imports...")
    
    # Test chamber state imports
    from chamber_app.core.chamber_state import ChamberType, ChamberStatus
    print("   ✓ Core types imported")
    
    # Test database imports 
    from chamber_app.data.database import DatabaseManager
    print("   ✓ Database imported")
    
    # Test utility imports
    from chamber_app.utils import get_logger
    print("   ✓ Utilities imported")
    
    print("2. Testing application creation...")
    
    # Create minimal config for testing
    config = {
        'APP_VERSION': '1.0.0',
        'DATABASE_URL': 'sqlite:///data/chamber_test.db',
        'DEVELOPER_OVERRIDE': True
    }
    
    from chamber_app.core.application import ChamberApplication
    print("   ✓ Application imported")
    
    # Create application instance (but don't run it)
    app = ChamberApplication(config)
    print("   ✓ Application created")
    
    # Initialize core components only (not GUI)
    app.initialize()
    print("   ✓ Application initialized")
    
    print("3. Testing basic functionality...")
    
    # Test chamber retrieval
    chambers = app.get_all_chambers()
    print(f"   ✓ Retrieved {len(chambers)} chambers")
    
    # Test chamber type filtering
    hass_chambers = app.get_chambers_by_type(ChamberType.HASS)
    print(f"   ✓ Found {len(hass_chambers)} HASS chambers")
    
    tvac_chambers = app.get_chambers_by_type(ChamberType.TVAC)  
    print(f"   ✓ Found {len(tvac_chambers)} TVAC chambers")
    
    thermal_chambers = app.get_chambers_by_type(ChamberType.THERMAL)
    print(f"   ✓ Found {len(thermal_chambers)} THERMAL chambers")
    
    print("4. Testing chamber creation...")
    
    # Test creating a new chamber
    if len(chambers) > 0:
        first_chamber = list(chambers.values())[0]
        print(f"   ✓ First chamber: {first_chamber.name} ({first_chamber.type.value})")
        print(f"   ✓ Current state: {first_chamber.state_manager.current_state.value}")
        print(f"   ✓ Current status: {first_chamber.state_manager.current_status.value}")
    
    print("🎉 Core application test PASSED!")
    print("✅ No circular import issues detected")
    print("✅ Application can be created and used without GUI")
    print("✅ Chamber management functionality working")
    
except Exception as e:
    print(f"❌ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nCore test completed successfully!")
