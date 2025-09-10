#!/usr/bin/env python3
"""
Quick application startup test
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def quick_test():
    try:
        print("Testing application import...")
        from chamber_app.core.application import ChamberApplication
        print("✓ Application import successful")
        
        print("Testing config loading...")
        from chamber_app.utils.config import load_config
        config = load_config()
        print("✓ Config loading successful")
        
        print("Testing application creation...")
        app = ChamberApplication(config)
        print("✓ Application creation successful")
        print(f"✓ Application has {len(app.chambers)} chambers")
        
        # Test basic functionality
        if hasattr(app, 'database'):
            print("✓ Database manager initialized")
        if hasattr(app, 'auth_manager'):
            print("✓ Authentication manager initialized")
        if hasattr(app, 'notification_manager'):
            print("✓ Notification manager initialized")
            
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 All tests passed! The application is ready to run.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Check the errors above.")
        sys.exit(1)
