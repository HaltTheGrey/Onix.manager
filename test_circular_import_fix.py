#!/usr/bin/env python3
"""
Test if the circular import issue is resolved
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import():
    """Test importing the main application"""
    try:
        print("Testing application import...")
        
        # Test config loading
        from chamber_app.utils.config import load_config
        config = load_config()
        print("✓ Config loaded")
        
        # Test application import
        from chamber_app.core.application import ChamberApplication
        print("✓ ChamberApplication imported")
        
        # Test creating application instance
        app = ChamberApplication(config)
        print("✓ Application instance created")
        
        print("\n🎉 SUCCESS: Circular import issue resolved!")
        print("The application can now be imported and instantiated without hanging.")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        if "circular import" in str(e).lower():
            print("Still has circular import issues")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    if success:
        print("\nNext steps:")
        print("1. Run: python app_launcher.py")
        print("2. Or run: python main.py")
    else:
        print("\nStill need to fix remaining import issues")
