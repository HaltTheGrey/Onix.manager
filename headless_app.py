#!/usr/bin/env python3
"""
Create a headless version of the application that doesn't initialize GUI
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run application in headless mode"""
    print("Starting Chamber Management Application (Headless Mode)")
    
    try:
        # Load configuration
        from chamber_app.utils.config import load_config
        config = load_config()
        print("✓ Configuration loaded")
        
        # Setup logging
        from chamber_app.utils.logging_config import setup_logging
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        print("✓ Logging configured")
        
        # Import and create application
        from chamber_app.core.application import ChamberApplication
        app = ChamberApplication(config)
        print("✓ Application created")
        
        # Initialize application (database, chambers, etc.)
        app.initialize()
        print("✓ Application initialized")
        
        # Start background services only (no GUI)
        app.is_running = True
        
        # Start task manager and performance monitoring
        from chamber_app.utils.threading_utils import start_task_manager
        from chamber_app.utils.performance_monitor import start_performance_monitoring
        start_task_manager()
        start_performance_monitoring()
        print("✓ Background services started")
        
        # Start background services
        app._start_background_services()
        print("✓ Application background services started")
        
        # Create notification manager (but don't start GUI components)
        from chamber_app.ui.notifications import NotificationManager
        app.notification_manager = NotificationManager(app)
        print("✓ Notification manager created")
        
        # Print status
        chambers = app.get_all_chambers()
        print(f"✓ Application running with {len(chambers)} chambers")
        
        print("\n=== APPLICATION RUNNING IN HEADLESS MODE ===")
        print("The application is running without GUI.")
        print("Background services are active:")
        print("- Database management")
        print("- Telemetry collection")
        print("- Multi-user networking")
        print("- Performance monitoring")
        print("- Notification system")
        print("\nPress Ctrl+C to stop the application.")
        
        # Keep running until interrupted
        import time
        while app.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down application...")
        if 'app' in locals():
            app.shutdown()
        print("Application stopped.")
        
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
