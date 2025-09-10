#!/usr/bin/env python3
"""
Application diagnostics and repair script
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")
    
    required_packages = [
        'customtkinter',
        'matplotlib',
        'numpy',
        'asyncio'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    return missing

def check_chamber_app_structure():
    """Check if chamber_app package structure is intact"""
    print("\nChecking application structure...")
    
    required_files = [
        'chamber_app/__init__.py',
        'chamber_app/core/application.py',
        'chamber_app/ui/main_window.py',
        'chamber_app/ui/notifications.py',
        'chamber_app/utils/config.py',
        'chamber_app/data/database.py'
    ]
    
    missing = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            missing.append(file_path)
    
    return missing

def test_basic_imports():
    """Test basic chamber_app imports"""
    print("\nTesting basic imports...")
    
    try:
        from chamber_app.utils.config import load_config
        print("✓ config module")
        
        from chamber_app.core.application import ChamberApplication
        print("✓ application module")
        
        # Test configuration loading
        config = load_config()
        print("✓ configuration loading")
        
        # Test application creation
        app = ChamberApplication(config)
        print("✓ application creation")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def check_database():
    """Check database status"""
    print("\nChecking database...")
    
    try:
        from chamber_app.utils.config import load_config
        from chamber_app.data.database import DatabaseManager
        
        config = load_config()
        db = DatabaseManager(config)
        db.initialize()
        
        print("✓ Database accessible")
        return True
        
    except Exception as e:
        print(f"✗ Database check failed: {e}")
        return False

def run_diagnostics():
    """Run complete diagnostics"""
    print("Chamber Management Application Diagnostics")
    print("=" * 50)
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    # Check file structure
    missing_files = check_chamber_app_structure()
    
    # Test imports
    imports_ok = test_basic_imports()
    
    # Check database
    db_ok = check_database()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if missing_deps:
        print(f"✗ Missing dependencies: {', '.join(missing_deps)}")
        print("  Run: pip install " + " ".join(missing_deps))
    else:
        print("✓ All dependencies available")
    
    if missing_files:
        print(f"✗ Missing files: {len(missing_files)} files missing")
    else:
        print("✓ All required files present")
    
    if imports_ok:
        print("✓ Basic imports working")
    else:
        print("✗ Import issues detected")
    
    if db_ok:
        print("✓ Database accessible")
    else:
        print("✗ Database issues detected")
    
    # Overall status
    if not missing_deps and not missing_files and imports_ok and db_ok:
        print("\n🎉 All diagnostics passed!")
        print("The application should be able to run.")
        print("\nTry running: python app_launcher.py")
        return True
    else:
        print("\n⚠️  Some issues detected.")
        print("Please resolve the issues above before running the application.")
        return False

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
