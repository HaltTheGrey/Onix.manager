#!/usr/bin/env python3
"""
Test application startup with timeout and detailed logging
"""
import sys
import threading
import time
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_startup():
    """Test application startup with detailed progress tracking"""
    try:
        print("Starting application test...")
        
        # Test imports first
        print("1. Testing imports...")
        from chamber_app.core.application import ChamberApplication
        print("✓ Application import successful")
        
        # Test instantiation
        print("2. Testing application instantiation...")
        app = ChamberApplication()
        print("✓ Application instance created")
        
        # Test startup with timeout
        print("3. Testing application startup...")
        startup_success = False
        
        def startup_thread():
            nonlocal startup_success
            try:
                app.startup()
                startup_success = True
                print("✓ Application startup completed")
            except Exception as e:
                print(f"✗ Application startup failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Start in thread with timeout
        thread = threading.Thread(target=startup_thread, daemon=True)
        thread.start()
        
        # Wait with timeout
        timeout = 15  # 15 seconds
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"✗ Application startup hanging after {timeout} seconds")
            print("This suggests an issue in the GUI initialization or background services")
            return False
        elif startup_success:
            print("✓ Application started successfully")
            
            # Test shutdown
            print("4. Testing application shutdown...")
            try:
                app.shutdown()
                print("✓ Application shutdown completed")
            except Exception as e:
                print(f"✗ Application shutdown failed: {e}")
            
            return True
        else:
            print("✗ Application startup failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Chamber Application Startup Test")
    print("=" * 50)
    success = test_startup()
    print("=" * 50)
    if success:
        print("✓ Application test PASSED")
        sys.exit(0)
    else:
        print("✗ Application test FAILED")
        sys.exit(1)
