#!/usr/bin/env python3
import sys
import os
print("Starting basic test...")

try:
    # Add project to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("Path added")
    
    # Test basic imports
    print("Testing imports...")
    from chamber_app.utils import get_logger
    print("✓ utils imported")
    
    from chamber_app.data.database import DatabaseManager
    print("✓ database imported")
    
    print("All basic imports successful!")
    
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
