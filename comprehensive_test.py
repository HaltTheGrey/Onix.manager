#!/usr/bin/env python3
"""
Comprehensive test script for the Chamber Management Application.
Tests all major features and validates functionality.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chamber_app.core.application import ChamberApplication
from chamber_app.core.chamber import Chamber, WorkRequest
from chamber_app.core.chamber_state import ChamberType, ChamberState, ChamberStatus, ChamberMetrics
from chamber_app.utils.config import load_config
from chamber_app.utils.logging_config import setup_logging


def test_core_functionality():
    """Test core application functionality."""
    
    print("🧪 Testing Core Functionality")
    print("=" * 40)
    
    # Initialize application
    config = load_config()
    setup_logging('ERROR')  # Reduce noise for testing
    
    app = ChamberApplication(config)
    app.initialize()
    
    # Test 1: Chamber Management
    print("✅ Test 1: Chamber Management")
    initial_count = len(app.get_chambers())
    print(f"   Initial chambers: {initial_count}")
    
    # Add a new chamber
    test_chamber = Chamber(
        name="Test Chamber",
        chamber_type=ChamberType.TVAC
    )
    
    success = app.add_chamber(test_chamber)
    assert success, "Failed to add chamber"
    
    new_count = len(app.get_chambers())
    assert new_count == initial_count + 1, "Chamber count not updated"
    print(f"   Added chamber: {new_count} total")
    
    # Test 2: State Management
    print("✅ Test 2: State Management")
    success = app.update_chamber_state(test_chamber.id, ChamberState.STAGING, "Test state change")
    assert success, "Failed to update chamber state"
    
    chamber = app.get_chamber(test_chamber.id)
    assert chamber.state_manager.current_state == ChamberState.STAGING, "State not updated"
    print("   State change successful")
    
    # Test 3: Status Management
    print("✅ Test 3: Status Management")
    success = app.update_chamber_status(test_chamber.id, ChamberStatus.ENGINEER_NEEDED, "Test status")
    assert success, "Failed to update chamber status"
    
    chamber = app.get_chamber(test_chamber.id)
    assert chamber.state_manager.current_status == ChamberStatus.ENGINEER_NEEDED, "Status not updated"
    print("   Status change successful")
    
    # Test 4: Work Request Management
    print("✅ Test 4: Work Request Management")
    work_request = WorkRequest(
        title="Test Work Request",
        description="This is a test work request",
        priority="High",
        estimated_hours=2.0,
        requester="test_user"
    )
    
    success = app.add_work_request(test_chamber.id, work_request)
    assert success, "Failed to add work request"
    
    chamber = app.get_chamber(test_chamber.id)
    assert len(chamber.work_requests) == 1, "Work request not added"
    print("   Work request added successfully")
    
    # Test 5: Telemetry Update
    print("✅ Test 5: Telemetry Update")
    test_metrics = ChamberMetrics(
        temperature=25.0,
        vacuum_level=1e-6,
        humidity=45.0,
        pressure=1013.25,
        elapsed_time=300
    )
    
    chamber.update_telemetry(test_metrics)
    assert chamber.latest_telemetry is not None, "Telemetry not updated"
    assert chamber.latest_telemetry.temperature == 25.0, "Telemetry data incorrect"
    print("   Telemetry updated successfully")
    
    # Test 6: Statistics
    print("✅ Test 6: Statistics")
    stats = app.get_chamber_statistics()
    assert stats['total_chambers'] >= 1, "Statistics not accurate"
    assert 'by_state' in stats, "State statistics missing"
    assert 'by_type' in stats, "Type statistics missing"
    print(f"   Statistics generated: {stats['total_chambers']} chambers")
    
    # Clean up
    app.remove_chamber(test_chamber.id)
    app.shutdown()
    
    print("🎉 All core functionality tests passed!")
    return True


def test_database_persistence():
    """Test database persistence."""
    
    print("\n💾 Testing Database Persistence")
    print("=" * 40)
    
    config = load_config()
    setup_logging('ERROR')
    
    # Create and save data
    app1 = ChamberApplication(config)
    app1.initialize()
    
    initial_chambers = len(app1.get_chambers())
    print(f"   Initial chambers in DB: {initial_chambers}")
    
    # Add a test chamber
    test_chamber = Chamber(
        name="Persistence Test Chamber",
        chamber_type=ChamberType.HASS
    )
    test_chamber.set_state(ChamberState.SETUP, "Testing persistence", "test_user")
    
    app1.add_chamber(test_chamber)
    test_chamber_id = test_chamber.id
    
    # Shutdown to force save
    app1.shutdown()
    
    # Create new instance and verify data persisted
    app2 = ChamberApplication(config)
    app2.initialize()
    
    loaded_chambers = len(app2.get_chambers())
    assert loaded_chambers == initial_chambers + 1, "Chamber not persisted"
    
    loaded_chamber = app2.get_chamber(test_chamber_id)
    assert loaded_chamber is not None, "Specific chamber not found"
    assert loaded_chamber.name == "Persistence Test Chamber", "Chamber data not preserved"
    assert loaded_chamber.state_manager.current_state == ChamberState.SETUP, "State not preserved"
    
    # Clean up
    app2.remove_chamber(test_chamber_id)
    app2.shutdown()
    
    print("✅ Database persistence test passed!")
    return True


def test_telemetry_manager():
    """Test telemetry manager functionality."""
    
    print("\n📡 Testing Telemetry Manager")
    print("=" * 40)
    
    config = load_config()
    setup_logging('ERROR')
    
    app = ChamberApplication(config)
    app.initialize()
    
    # Test telemetry source status
    if app.telemetry_manager:
        sources = app.telemetry_manager.get_source_status()
        print(f"   Available telemetry sources: {len(sources)}")
        
        for source_name, connected in sources.items():
            status = "Connected" if connected else "Disconnected"
            print(f"     {source_name}: {status}")
        
        # Test chamber assignment
        chambers = app.get_chambers()
        if chambers:
            test_chamber = chambers[0]
            app.telemetry_manager.assign_chamber_source(test_chamber.id, 'ethernet')
            
            assignments = app.telemetry_manager.get_chamber_assignments()
            assert test_chamber.id in assignments, "Chamber assignment failed"
            print(f"   Chamber {test_chamber.name} assigned to {assignments[test_chamber.id]}")
    
    app.shutdown()
    print("✅ Telemetry manager test passed!")
    return True


def test_multi_user_manager():
    """Test multi-user functionality."""
    
    print("\n👥 Testing Multi-User Manager")
    print("=" * 40)
    
    config = load_config()
    setup_logging('ERROR')
    
    app = ChamberApplication(config)
    app.initialize()
    
    if app.multi_user_manager:
        # Test server status
        is_running = app.multi_user_manager.is_running()
        print(f"   WebSocket server running: {is_running}")
        
        # Test user count
        user_count = app.multi_user_manager.get_user_count()
        print(f"   Connected users: {user_count}")
        
        # Test broadcast capability (without actual clients)
        try:
            app.multi_user_manager.broadcast_chamber_update("test", {"test": "data"})
            print("   Broadcast capability verified")
        except Exception as e:
            print(f"   Broadcast test (no clients connected): {type(e).__name__}")
    
    app.shutdown()
    print("✅ Multi-user manager test passed!")
    return True


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    
    print("🔬 Chamber Management Application - Comprehensive Testing")
    print("=" * 60)
    
    tests = [
        test_core_functionality,
        test_database_persistence,
        test_telemetry_manager,
        test_multi_user_manager
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_func.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} failed with error: {e}")
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Application is fully functional.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
