#!/usr/bin/env python3
"""
Diagnostic script to identify startup issues
"""

import sys
import traceback
from pathlib import Path

def test_step(step_name, test_func):
    """Test a step and report results."""
    try:
        print(f"Testing {step_name}...", end="", flush=True)
        result = test_func()
        print(" ✓ OK")
        return True
    except Exception as e:
        print(f" ✗ FAILED: {e}")
        traceback.print_exc()
        return False

def test_basic_imports():
    """Test basic Python imports."""
    import os
    import sys
    import asyncio
    import logging
    return True

def test_package_import():
    """Test chamber_app package import."""
    import chamber_app
    return True

def test_config_import():
    """Test config utilities."""
    from chamber_app.utils.config import load_config
    config = load_config()
    return config is not None

def test_application_import():
    """Test application import."""
    from chamber_app.core.application import ChamberApplication
    return True

def test_application_creation():
    """Test creating application instance."""
    from chamber_app.core.application import ChamberApplication
    from chamber_app.utils.config import load_config
    config = load_config()
    app = ChamberApplication(config)
    return app is not None

def main():
    """Run diagnostic tests."""
    print("=== Chamber Application Diagnostic ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    tests = [
        ("Basic imports", test_basic_imports),
        ("Package import", test_package_import),
        ("Config import", test_config_import),
        ("Application import", test_application_import),
        ("Application creation", test_application_creation),
    ]
    
    passed = 0
    for name, test_func in tests:
        if test_step(name, test_func):
            passed += 1
        else:
            break  # Stop at first failure
    
    print(f"\nPassed: {passed}/{len(tests)} tests")
    
    if passed == len(tests):
        print("✓ All diagnostic tests passed!")
        print("The application should be able to start normally.")
    else:
        print("✗ Some tests failed. Check the errors above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
