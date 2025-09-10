#!/usr/bin/env python3
"""
Debug main with detailed logging of MainWindow initialization
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main application entry point with detailed debug info."""
    try:
        print("=== DETAILED DEBUG MAIN START ===")
        
        print("1. Loading config...")
        from chamber_app.utils.config import load_config
        config = load_config()
        print(f"✓ Config loaded: {list(config.keys())}")
        
        print("2. Setting up logging...")
        from chamber_app.utils.logging_config import setup_logging
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        print("✓ Logging configured")
        
        print("3. Importing ChamberApplication...")
        from chamber_app.core.application import ChamberApplication
        print("✓ ChamberApplication imported")
        
        print("4. Creating application instance...")
        app = ChamberApplication(config)
        print("✓ Application instance created")
        
        print("5. Calling app.initialize()...")
        app.initialize()
        print("✓ Application initialized")
        
        print("6. Setting app.is_running = True...")
        app.is_running = True
        print("✓ App running state set")
        
        print("7. Starting task manager...")
        from chamber_app.utils.threading_utils import start_task_manager
        start_task_manager()
        print("✓ Task manager started")
        
        print("8. Starting performance monitoring...")
        from chamber_app.utils.performance_monitor import start_performance_monitoring
        start_performance_monitoring()
        print("✓ Performance monitoring started")
        
        print("9. Starting background services...")
        app._start_background_services()
        print("✓ Background services started")
        
        print("10. Importing NotificationManager...")
        from chamber_app.ui.notifications import NotificationManager
        print("✓ NotificationManager imported")
        
        print("11. Creating NotificationManager instance...")
        app.notification_manager = NotificationManager(app)
        print("✓ NotificationManager created")
        
        print("12. Importing MainWindow...")
        from chamber_app.ui.main_window import MainWindow
        print("✓ MainWindow imported")
        
        print("13. Creating MainWindow instance...")
        main_window = MainWindow(app, config)
        print("✓ MainWindow instance created")
        
        print("14. Setting app.main_window...")
        app.main_window = main_window
        print("✓ MainWindow assigned to app")
        
        print("15. Starting main_window.run()...")
        print("    This should start the GUI mainloop...")
        main_window.run()
        
        print("✓ Application completed normally")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
