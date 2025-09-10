#!/usr/bin/env python3
"""
Step-by-step initialization test
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_step_by_step():
    """Test each initialization step individually."""
    try:
        print("Step 1: Basic imports...")
        from chamber_app.core.application import ChamberApplication
        from chamber_app.utils.config import load_config
        from chamber_app.utils.logging_config import setup_logging
        print("✓ Imports successful")
        
        print("Step 2: Load config...")
        config = load_config()
        print("✓ Config loaded")
        
        print("Step 3: Setup logging...")
        setup_logging(config.get('LOG_LEVEL', 'INFO'))
        print("✓ Logging setup")
        
        print("Step 4: Create application instance...")
        app = ChamberApplication(config)
        print("✓ Application instance created")
        
        print("Step 5: Initialize database...")
        app.database.initialize()
        print("✓ Database initialized")
        
        print("Step 6: Load chambers...")
        app._load_chambers()
        print("✓ Chambers loaded")
        
        print("Step 7: Initialize telemetry manager...")
        from chamber_app.sdk.telemetry_manager import TelemetryManager
        app.telemetry_manager = TelemetryManager(app.config)
        print("✓ Telemetry manager created")
        
        print("Step 8: Initialize multi-user manager...")
        from chamber_app.network.multi_user import MultiUserManager
        app.multi_user_manager = MultiUserManager(app.config)
        print("✓ Multi-user manager created")
        
        print("Step 9: Create default chambers...")
        if not app.chambers:
            app._create_default_chambers()
        print("✓ Default chambers created")
        
        print(f"\n🎉 All steps completed! Found {len(app.chambers)} chambers")
        return True
        
    except Exception as e:
        print(f"❌ Error at current step: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_step_by_step()
    sys.exit(0 if success else 1)
