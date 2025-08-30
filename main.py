#!/usr/bin/env python3
"""
Chamber Management Application
Main entry point for the chamber tracking and management system.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chamber_app.core.application import ChamberApplication
from chamber_app.utils.config import load_config
from chamber_app.utils.logging_config import setup_logging


def main():
    """Main application entry point."""
    logger = None
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Chamber Management Application")
        logger.info(f"Version: {config.get('APP_VERSION', '1.0.0')}")
        
        # Create and run the application
        app = ChamberApplication(config)
        
        # Run the application (handles both sync and async components)
        app.run()
        
    except KeyboardInterrupt:
        if logger:
            logger.info("Application interrupted by user")
        else:
            print("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        if logger:
            logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
