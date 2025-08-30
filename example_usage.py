#!/usr/bin/env python3
"""
Example usage of the Chamber Management Application.
This script demonstrates how to interact with chambers programmatically.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chamber_app.core.application import ChamberApplication
from chamber_app.core.chamber import Chamber, WorkRequest
from chamber_app.core.chamber_state import ChamberType, ChamberState, ChamberStatus, ChamberMetrics
from chamber_app.utils.config import load_config
from chamber_app.utils.logging_config import setup_logging


def demonstrate_chamber_operations():
    """Demonstrate basic chamber operations."""
    
    # Load configuration
    config = load_config()
    setup_logging('INFO')
    
    # Create application instance
    app = ChamberApplication(config)
    app.initialize()
    
    print("🏭 Chamber Management System - API Demo")
    print("=" * 50)
    
    # List all chambers
    chambers = app.get_chambers()
    print(f"\n📊 Total chambers: {len(chambers)}")
    
    for chamber in chambers:
        print(f"  - {chamber.name} ({chamber.type.value})")
        print(f"    State: {chamber.state_manager.current_state.value}")
        print(f"    Status: {chamber.state_manager.current_status.value if chamber.state_manager.current_status else 'None'}")
        print(f"    Connected: {'Yes' if chamber.is_connected else 'No'}")
        print()
    
    # Demonstrate state changes
    if chambers:
        demo_chamber = chambers[0]
        print(f"🔄 Demonstrating state changes on {demo_chamber.name}")
        
        # Change to staging
        print("  → Moving to staging...")
        app.update_chamber_state(demo_chamber.id, ChamberState.STAGING, "Demo: preparing for test")
        
        # Add a status
        print("  → Setting engineer needed status...")
        app.update_chamber_status(demo_chamber.id, ChamberStatus.ENGINEER_NEEDED, "Demo: needs review")
        
        # Create a work request
        print("  → Creating work request...")
        work_request = WorkRequest(
            title="Demo Work Request",
            description="This is a demonstration work request for testing",
            priority="High",
            estimated_hours=2.0,
            requester="demo_user"
        )
        app.add_work_request(demo_chamber.id, work_request)
        
        # Simulate telemetry update
        print("  → Updating telemetry...")
        demo_metrics = ChamberMetrics(
            temperature=25.5,
            vacuum_level=1e-6,
            humidity=45.0,
            pressure=1013.25,
            elapsed_time=300
        )
        demo_chamber.update_telemetry(demo_metrics)
        
        print("  ✅ Demo operations completed!")
    
    # Show statistics
    stats = app.get_chamber_statistics()
    print(f"\n📈 Chamber Statistics:")
    print(f"  Total chambers: {stats.get('total_chambers', 0)}")
    print(f"  Connected: {stats.get('connected_chambers', 0)}")
    print(f"  Active work requests: {stats.get('active_work_requests', 0)}")
    
    print(f"\n🏷️  By State:")
    for state, count in stats.get('by_state', {}).items():
        print(f"    {state}: {count}")
    
    print(f"\n🏷️  By Type:")
    for chamber_type, count in stats.get('by_type', {}).items():
        print(f"    {chamber_type}: {count}")
    
    # Show chamber history
    if chambers:
        demo_chamber = chambers[0]
        print(f"\n📋 State History for {demo_chamber.name}:")
        for transition in demo_chamber.state_manager.state_history[-5:]:  # Last 5 transitions
            print(f"    {transition.timestamp.strftime('%H:%M:%S')} - {transition.from_value} → {transition.to_value}")
            if transition.reason:
                print(f"      Reason: {transition.reason}")
    
    # Clean up
    app.shutdown()
    print(f"\n✨ Demo completed successfully!")


def create_sample_data():
    """Create sample data for testing."""
    
    config = load_config()
    setup_logging('INFO')
    
    app = ChamberApplication(config)
    app.initialize()
    
    print("🏗️  Creating sample data...")
    
    # Add a new TVAC chamber
    new_chamber = Chamber(
        name="TVAC Chamber 2",
        chamber_type=ChamberType.TVAC
    )
    
    # Set up initial state
    new_chamber.set_state(ChamberState.SETUP, "Initial setup for testing", "demo_user")
    new_chamber.set_status(ChamberStatus.SETUP_ISSUES, "Needs calibration", "demo_user")
    
    # Add work requests
    work_requests = [
        WorkRequest(
            title="Calibrate Temperature Sensors",
            description="Temperature sensors need recalibration after last maintenance",
            priority="High",
            estimated_hours=4.0,
            requester="engineer1"
        ),
        WorkRequest(
            title="Update Control Software",
            description="Update chamber control software to latest version",
            priority="Medium", 
            estimated_hours=2.0,
            requester="software_team"
        ),
        WorkRequest(
            title="Safety Inspection",
            description="Monthly safety inspection required",
            priority="Critical",
            estimated_hours=1.5,
            requester="safety_team"
        )
    ]
    
    for work_request in work_requests:
        new_chamber.add_work_request(work_request)
    
    # Add chamber to application
    app.add_chamber(new_chamber)
    
    # Create some telemetry data
    import time
    for i in range(5):
        metrics = ChamberMetrics(
            temperature=20.0 + i * 2.5,
            vacuum_level=1e-6 * (1 + i * 0.1),
            humidity=40.0 + i * 2,
            pressure=1013.25 - i * 5,
            elapsed_time=i * 60
        )
        new_chamber.update_telemetry(metrics)
        time.sleep(0.1)  # Small delay to show progression
    
    app.shutdown()
    print("✅ Sample data created successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-sample":
        create_sample_data()
    else:
        demonstrate_chamber_operations()
