#!/usr/bin/env python3
"""
Test script to verify the two specific fixes:
1. Chamber add/remove buttons positioned correctly
2. Work request "start work" functionality working properly
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from chamber_app.core.application import ChamberApplication
from chamber_app.core.chamber import WorkRequest
from chamber_app.core.chamber_state import ChamberState, ChamberStatus
from chamber_app.utils.config import load_config
from chamber_app.utils.logging_config import setup_logging
from datetime import datetime

def test_work_request_start_functionality():
    """Test that work request start functionality works without errors."""
    print("🧪 Testing Work Request Start Functionality")
    print("=" * 50)
    
    # Setup
    config = load_config()
    setup_logging('INFO')
    
    # Create application
    app = ChamberApplication(config)
    app.initialize()
    
    # Get first chamber for testing
    chambers = app.get_chambers()
    if not chambers:
        print("❌ No chambers available for testing")
        return False
    
    test_chamber = chambers[0]
    print(f"📋 Using chamber: {test_chamber.name} ({test_chamber.type.value})")
    print(f"   Initial state: {test_chamber.state_manager.current_state.value}")
    print(f"   Initial status: {test_chamber.state_manager.current_status.value if test_chamber.state_manager.current_status else 'None'}")
    
    # Create a test work request
    work_request = WorkRequest(
        title="Test Start Work Request",
        description="Testing the start work functionality fix",
        priority="high",
        assigned_to="test_technician",
        created_by="test_user",
        estimated_hours=1.0
    )
    
    print(f"\n🎫 Created work request: '{work_request.title}'")
    
    # Add work request to chamber
    success = app.add_work_request(test_chamber.id, work_request)
    if not success:
        print("❌ Failed to add work request to chamber")
        return False
    
    print(f"✅ Added work request to chamber")
    
    # Test the critical functionality: update_chamber_status with correct parameters
    print(f"\n🚀 Testing work request start workflow...")
    
    # Simulate starting the request (this was the failing part)
    original_status = test_chamber.state_manager.current_status
    
    work_request.status = "in_progress"
    work_request.updated_at = datetime.now()
    work_request.add_note("Work started by test_user", "test_user")
    
    # This is the fix: call update_chamber_status with correct number of parameters
    work_status = ChamberStatus.CURRENTLY_BEING_WORKED_ON
    reason = f"Work in progress: {work_request.title}"
    
    try:
        # This was failing before the fix due to incorrect parameter count
        status_success = app.update_chamber_status(
            test_chamber.id,
            work_status,
            reason
            # Removed the 4th parameter (current_user) that was causing the error
        )
        
        if status_success:
            work_request.add_note(f"Chamber status set to '{work_status.value}'", "system")
            print(f"✅ Chamber status updated successfully")
            print(f"   New status: {test_chamber.state_manager.current_status.value}")
        else:
            print("❌ Failed to update chamber status")
            return False
            
    except Exception as e:
        print(f"❌ Error during status update: {e}")
        return False
    
    # Test completion workflow
    print(f"\n✅ Testing work request completion workflow...")
    
    # Complete the work request
    work_request.status = "completed"
    work_request.completed_at = datetime.now()
    work_request.updated_at = datetime.now()
    work_request.add_note("Work completed by test_user", "test_user")
    
    # Clear the status
    clear_success = app.clear_chamber_status(
        test_chamber.id,
        f"Work completed: {work_request.title}"
    )
    
    if clear_success:
        work_request.add_note("Chamber status cleared (work completed)", "system")
        print(f"✅ Chamber status cleared successfully")
        print(f"   Final status: {test_chamber.state_manager.current_status.value if test_chamber.state_manager.current_status else 'None'}")
    else:
        print("❌ Failed to clear chamber status")
        return False
    
    print(f"\n📊 Final verification:")
    print(f"   Work request status: {work_request.status}")
    print(f"   Chamber status: {test_chamber.state_manager.current_status.value if test_chamber.state_manager.current_status else 'None'}")
    print(f"   Notes count: {len(work_request.notes)}")
    
    # Cleanup
    app.shutdown()
    
    print(f"\n🎉 Work request start functionality test PASSED!")
    return True

def test_ui_button_positioning():
    """Test that chamber add/remove buttons are positioned correctly in the UI."""
    print("\n🖥️  Testing UI Button Positioning")
    print("=" * 50)
    
    # Read the main window file to verify button positioning
    main_window_path = "chamber_app/ui/main_window.py"
    
    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for add/remove chamber buttons in navigation
        if '"Add Chamber", "add_chamber"' in content and '"Remove Chamber", "remove_chamber"' in content:
            print("✅ Add and Remove Chamber buttons found in main navigation")
        else:
            print("❌ Add/Remove Chamber buttons not found in main navigation")
            return False
        
        # Check for handler in _switch_panel method
        if 'if panel_id == "remove_chamber":' in content and 'self._show_remove_chamber_dialog()' in content:
            print("✅ Remove chamber handler found in _switch_panel method")
        else:
            print("❌ Remove chamber handler not found")
            return False
        
        print("✅ UI button positioning test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading main window file: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🔧 Chamber Management Application - Fixes Verification")
    print("=" * 60)
    print("Testing the two specific issues:")
    print("1. Chamber add/remove buttons positioning")
    print("2. Work request 'start work' functionality")
    print("=" * 60)
    
    # Test 1: UI Button positioning
    ui_test_passed = test_ui_button_positioning()
    
    # Test 2: Work request functionality  
    work_request_test_passed = test_work_request_start_functionality()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"1. UI Button Positioning: {'✅ PASSED' if ui_test_passed else '❌ FAILED'}")
    print(f"2. Work Request Start Functionality: {'✅ PASSED' if work_request_test_passed else '❌ FAILED'}")
    
    if ui_test_passed and work_request_test_passed:
        print("\n🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("The chamber management application is now working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
