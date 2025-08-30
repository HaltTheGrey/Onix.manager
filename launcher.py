"""
Application launcher with error handling and setup validation.
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n📦 Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies are installed")
    return True

def check_environment():
    """Check environment setup."""
    # Check if .env file exists
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  No .env file found. Creating one from template...")
        try:
            template_file = project_root / ".env.example"
            if template_file.exists():
                import shutil
                shutil.copy(template_file, env_file)
                print("✅ Created .env file from template")
            else:
                print("❌ No .env.example template found")
                return False
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("✅ Environment file found")
    
    # Check if data directory exists
    data_dir = project_root / "data"
    if not data_dir.exists():
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Created data directory")
        except Exception as e:
            print(f"❌ Failed to create data directory: {e}")
            return False
    
    return True

def main():
    """Main launcher function."""
    print("🏭 Chamber Management System Launcher")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install required packages.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment setup failed.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("\n🚀 Starting Chamber Management Application...")
    
    try:
        # Import and run the main application
        from main import main as app_main
        app_main()
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("Make sure all application files are present.")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 Application Error: {e}")
        print("\nFull error details:")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
