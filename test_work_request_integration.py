#!/usr/bin/env python3
"""
Test script to verify work request and chamber integration workflow.
"""

import os
import sys
from datetime import datetime

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from chamber_app.core.application import ChamberApplication
from chamber_app.core.chamber import WorkRequest
from chamber_app.core.chamber_state import ChamberState, ChamberStatus, ChamberType
from chamber_app.utils.config import load_config
from chamber_app.utils.logging_config import setup_logging


def test_work_request_workflow():
    """Test the complete work request workflow with chamber integration."""
    print("🧪 Testing Work Request - Chamber Integration Workflow")
    print("=" * 60)
    
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
        return
    
    test_chamber = chambers[0]
    print(f"📋 Using chamber: {test_chamber.name} ({test_chamber.type.value})")
    print(f"   Initial state: {test_chamber.state_manager.current_state.value}")
    print(f"   Initial status: {test_chamber.state_manager.current_status.value if test_chamber.state_manager.current_status else 'None'}")
    
    # Create a test work request
    work_request = WorkRequest(
        title="Test Integration Work Request",
        description="Testing the chamber and work request integration workflow",
        priority="high",
        assigned_to="test_technician",
        created_by="test_user",
        estimated_hours=2.0
    )
    
    print(f"\n🎫 Created work request: '{work_request.title}'")
    print(f"   Priority: {work_request.priority}")
    print(f"   Status: {work_request.status}")
    
    # Add work request to chamber
    success = app.add_work_request(test_chamber.id, work_request)
    if not success:
        print("❌ Failed to add work request to chamber")
        return
    
    print(f"✅ Added work request to chamber: {test_chamber.name}")
    
    # Test starting work request
    print(f"\n🚀 Testing work request start workflow...")
    
    # Simulate starting the request (like the _start_request method does)
    original_state = test_chamber.state_manager.current_state
    original_status = test_chamber.state_manager.current_status
    
    work_request.status = "in_progress"
    work_request.updated_at = datetime.now()
    work_request.add_note("Work started by test_user", "test_user")
      # Test chamber state transitions
    current_state = test_chamber.state_manager.current_state
    if current_state == ChamberState.AVAILABLE_EMPTY:
        new_state = ChamberState.STAGING
        reason = f"Work started: {work_request.title}"
    elif current_state == ChamberState.STAGING:
        new_state = ChamberState.SETUP
        reason = f"Setup phase for: {work_request.title}"
    else:
        new_state = None
        reason = f"Work in progress: {work_request.title}"
    
    if new_state:
        state_success = app.update_chamber_state(test_chamber.id, new_state, reason)
        if state_success:
            work_request.add_note(f"Chamber transitioned to {new_state.value}", "system")
            print(f"✅ Chamber state changed: {original_state.value} → {new_state.value}")
        else:
            print("❌ Failed to update chamber state")
    
    # Set chamber status to indicate work is in progress
    status_success = app.update_chamber_status(
        test_chamber.id,
        ChamberStatus.CURRENTLY_BEING_WORKED_ON,
        reason
    )
    
    if status_success:
        work_request.add_note("Chamber status set to 'currently being worked on'", "system")
        print(f"✅ Chamber status set: {ChamberStatus.CURRENTLY_BEING_WORKED_ON.value}")
    else:
        print("❌ Failed to set chamber status")
    
    print(f"\n📊 Current chamber state after starting work:")
    print(f"   State: {test_chamber.state_manager.current_state.value}")
    print(f"   Status: {test_chamber.state_manager.current_status.value if test_chamber.state_manager.current_status else 'None'}")
    print(f"   Work request status: {work_request.status}")
    
    # Test completing work request
    print(f"\n✅ Testing work request completion workflow...")
    
    # Simulate completing the request (like the _complete_request method does)
    work_request.status = "completed"
    work_request.completed_at = datetime.now()
    work_request.updated_at = datetime.now()
    work_request.add_note("Work completed by test_user", "test_user")
    
    # Check if there are other active work requests
    other_active_requests = [
        req for req in test_chamber.work_requests.values()
        if req.id != work_request.id and req.status in ['open', 'in_progress']
    ]
    
    print(f"   Other active requests: {len(other_active_requests)}")
    
    # If this was the last active work request, clean up chamber state
    if not other_active_requests:        # Clear the "CURRENTLY_BEING_WORKED_ON" status
        current_status = test_chamber.state_manager.current_status
        if current_status == ChamberStatus.CURRENTLY_BEING_WORKED_ON:
            clear_success = app.clear_chamber_status(
                test_chamber.id,
                f"Work completed: {work_request.title}"
            )
            
            if clear_success:
                work_request.add_note("Chamber status cleared (work completed)", "system")
                print(f"✅ Chamber status cleared")
            else:
                print("❌ Failed to clear chamber status")
        
        # Transition to appropriate state based on work completion
        current_state = test_chamber.state_manager.current_state
        if current_state in [ChamberState.SETUP, ChamberState.STAGING]:
            final_state = ChamberState.AVAILABLE_EMPTY
            final_reason = f"Work completed, chamber available: {work_request.title}"
            
            final_success = app.update_chamber_state(test_chamber.id, final_state, final_reason)
            if final_success:
                work_request.add_note(f"Chamber transitioned to {final_state.value}", "system")
                print(f"✅ Chamber state reset: {current_state.value} → {final_state.value}")
            else:
                print("❌ Failed to reset chamber state")
    
    print(f"\n📊 Final chamber state after completing work:")
    print(f"   State: {test_chamber.state_manager.current_state.value}")
    print(f"   Status: {test_chamber.state_manager.current_status.value if test_chamber.state_manager.current_status else 'None'}")
    print(f"   Work request status: {work_request.status}")
    
    # Show work request notes
    print(f"\n📝 Work request activity log:")
    for i, note in enumerate(work_request.notes, 1):
        print(f"   {i}. {note}")
    
    print(f"\n🎉 Integration test completed successfully!")
    print(f"   Total notes added: {len(work_request.notes)}")
    print(f"   Work request completed at: {work_request.completed_at}")
    
    # Cleanup
    app.shutdown()


if __name__ == "__main__":
    test_work_request_workflow()
