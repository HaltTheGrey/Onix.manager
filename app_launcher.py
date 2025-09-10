#!/usr/bin/env python3
"""
Minimal application launcher with error handling and GUI fallback
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gui_availability():
    """Test if GUI components are available"""
    try:
        import tkinter as tk
        # Try to create a minimal window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        return True
    except Exception as e:
        print(f"GUI not available: {e}")
        return False

def launch_gui_mode():
    """Launch application with GUI"""
    try:
        print("Attempting to launch GUI mode...")
        
        # Load configuration and setup logging
        from chamber_app.utils.config import load_config
        from chamber_app.utils.logging_config import setup_logging
        
        config = load_config()
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        
        # Create and run application
        from chamber_app.core.application import ChamberApplication
        app = ChamberApplication(config)
        app.run()
        
        return True
        
    except Exception as e:
        print(f"GUI mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def launch_console_mode():
    """Launch application in console mode"""
    try:
        print("Launching console mode...")
        
        from chamber_app.utils.config import load_config
        from chamber_app.utils.logging_config import setup_logging
        from chamber_app.core.application import ChamberApplication
        from chamber_app.utils.threading_utils import start_task_manager
        from chamber_app.utils.performance_monitor import start_performance_monitoring
        
        config = load_config()
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        
        # Create application
        app = ChamberApplication(config)
        app.initialize()
        app.is_running = True
        
        # Start only background services
        start_task_manager()
        start_performance_monitoring()
        app._start_background_services()
        
        # Create notification manager without GUI
        from chamber_app.ui.notifications import NotificationManager
        app.notification_manager = NotificationManager(app)
        
        chambers = app.get_all_chambers()
        print(f"\n=== CHAMBER MANAGEMENT APPLICATION (CONSOLE MODE) ===")
        print(f"Application initialized with {len(chambers)} chambers")
        print("Available commands:")
        print("  status - Show application status")
        print("  chambers - List all chambers")
        print("  quit - Exit application")
        
        # Simple command loop
        while app.is_running:
            try:
                cmd = input("\nchamber> ").strip().lower()
                
                if cmd == "quit":
                    break
                elif cmd == "status":
                    stats = app.get_chamber_statistics()
                    print(f"Total chambers: {stats.get('total_chambers', 0)}")
                    print(f"Connected: {stats.get('connected_chambers', 0)}")
                elif cmd == "chambers":
                    for chamber in chambers:
                        print(f"  {chamber.name} ({chamber.type.value}) - {chamber.state_manager.current_state.value}")
                elif cmd == "help":
                    print("Available commands: status, chambers, quit")
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        print("\nShutting down...")
        app.shutdown()
        return True
        
    except Exception as e:
        print(f"Console mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main launcher with fallback modes"""
    print("Chamber Management Application Launcher")
    print("=" * 50)
    
    # Test if GUI is available
    gui_available = test_gui_availability()
    
    if gui_available:
        print("GUI components detected. Attempting GUI mode...")
        if launch_gui_mode():
            return 0
        else:
            print("\nGUI mode failed. Falling back to console mode...")
    else:
        print("GUI not available. Starting in console mode...")
    
    # Fallback to console mode
    if launch_console_mode():
        return 0
    else:
        print("\nBoth GUI and console modes failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
