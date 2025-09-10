#!/usr/bin/env python3
"""
Debug version of main.py to identify where it hangs
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("1. Imports completed")

def main():
    """Main application entry point with debug output."""
    logger = None
    try:
        print("2. Starting main function")
        
        # Load configuration
        print("3. Loading configuration...")
        from chamber_app.utils.config import load_config
        config = load_config()
        print("   ✓ Configuration loaded")
        
        # Setup logging
        print("4. Setting up logging...")
        from chamber_app.utils.logging_config import setup_logging
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        logger = logging.getLogger(__name__)
        print("   ✓ Logging setup complete")
        
        logger.info("Starting Chamber Management Application")
        logger.info(f"Version: {config.get('APP_VERSION', '1.0.0')}")
        
        # Create and run the application
        print("5. Creating application...")
        from chamber_app.core.application import ChamberApplication
        app = ChamberApplication(config)
        print("   ✓ Application created")
        
        # Run the application (handles both sync and async components)
        print("6. Starting application.run()...")
        app.run()
        print("   ✓ Application.run() completed")
        
    except KeyboardInterrupt:
        print("   ! Application interrupted by user")
        if logger:
            logger.info("Application interrupted by user")
        else:
            print("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"   ! Fatal error: {e}")
        if logger:
            logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("0. Starting debug main...")
    main()
    print("7. Main function completed")
