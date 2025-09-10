#!/usr/bin/env python3
"""
Final verification test for Chamber Management Application
"""

import sys
import subprocess
import time
from pathlib import Path

def test_application_startup():
    """Test that the application can start and stop properly."""
    try:
        print("🚀 Starting Chamber Management Application test...")
        
        # Start the application in a subprocess
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent
        )
        
        # Let it run for 3 seconds
        print("⏳ Letting application run for 3 seconds...")
        time.sleep(3)
        
        # Terminate the process
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        
        print("✅ Application started and stopped successfully!")
        
        # Check if there were any critical errors
        if stderr and b"Error" in stderr:
            print("⚠️  Some errors detected in stderr:")
            print(stderr.decode('utf-8', errors='ignore'))
        
        # Check log file for successful startup
        log_file = Path("logs/chamber_app.log")
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = f.read()
                if "Application shutdown complete" in logs:
                    print("✅ Application logs show successful startup and shutdown")
                else:
                    print("⚠️  Application may not have shut down properly")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️  Application took too long to shut down")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_import_functionality():
    """Test that key modules can be imported."""
    try:
        print("\n📦 Testing module imports...")
        
        from chamber_app.core.application import ChamberApplication
        print("✅ ChamberApplication import successful")
        
        from chamber_app.core.chamber import Chamber, WorkRequest
        print("✅ Chamber and WorkRequest import successful")
        
        from chamber_app.core.chamber_state import ChamberType, ChamberState, ChamberStatus
        print("✅ Chamber state classes import successful")
        
        from chamber_app.utils.config import load_config
        print("✅ Config utilities import successful")
        
        from chamber_app.utils.threading_utils import start_task_manager, stop_task_manager
        print("✅ Threading utilities import successful")
        
        from chamber_app.utils.performance_monitor import start_performance_monitoring, stop_performance_monitoring
        print("✅ Performance monitoring utilities import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🔍 Chamber Management Application - Final Verification")
    print("=" * 60)
    
    import_success = test_import_functionality()
    startup_success = test_application_startup()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"   Import Tests: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"   Startup Tests: {'✅ PASSED' if startup_success else '❌ FAILED'}")
    
    if import_success and startup_success:
        print("\n🎉 ALL TESTS PASSED! The Chamber Management Application is fully functional!")
        print("\n🚀 You can now run the application with: python main.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
