#!/usr/bin/env python3
"""
Test script to run the application without GUI
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_non_gui():
    """Test the application without starting the GUI."""
    try:
        print("Testing core application without GUI...")
        
        # Import and setup
        from chamber_app.core.application import ChamberApplication
        from chamber_app.utils.config import load_config
        from chamber_app.utils.logging_config import setup_logging
        
        # Load configuration
        config = load_config()
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        
        print("✓ Configuration and logging setup complete")
        
        # Create application instance
        app = ChamberApplication(config)
        print("✓ Application instance created")
        
        # Initialize without running UI
        app.initialize()
        print("✓ Application initialized")
        
        # Test some basic functionality
        chambers = app.get_chambers()
        print(f"✓ Found {len(chambers)} chambers")
        
        stats = app.get_chamber_statistics()
        print(f"✓ Statistics: {stats}")
        
        print("\n🎉 Core application functionality works!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_non_gui()
    if success:
        print("\nThe core application works. The issue is likely in the GUI components.")
    else:
        print("\nThere's an issue with the core application.")
    sys.exit(0 if success else 1)
