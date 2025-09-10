#!/usr/bin/env python3
"""
Simple test to check if application constructor works
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_constructor():
    """Test just the application constructor"""
    try:
        print("Testing application constructor...")
        
        # Test basic config
        config = {
            'DATABASE_URL': 'sqlite:///test.db',
            'APP_VERSION': '1.0.0',
            'DEVELOPER_OVERRIDE': True
        }
        
        print("Importing ChamberApplication...")
        from chamber_app.core.application import ChamberApplication
        
        print("Creating application instance...")
        app = ChamberApplication(config)
        
        print("✓ Constructor completed successfully!")
        print(f"✓ App initialized with user: {getattr(app, 'current_user', 'Unknown')}")
        print(f"✓ Notification manager state: {type(app.notification_manager)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Constructor failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Chamber Application Constructor Test")
    print("=" * 50)
    success = test_constructor()
    print("=" * 50)
    if success:
        print("✓ Constructor test PASSED")
    else:
        print("✗ Constructor test FAILED")
