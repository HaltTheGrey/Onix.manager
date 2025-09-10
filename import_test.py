#!/usr/bin/env python3
"""
Test individual imports to find what's causing the hang
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("Testing imports step by step...")
    
    print("1. Basic imports...")
    import tkinter as tk
    print("✓ tkinter imported")
    
    import customtkinter as ctk
    print("✓ customtkinter imported")
    
    print("2. Application imports...")
    from chamber_app.utils.config import load_config
    print("✓ config imported")
    
    from chamber_app.core.application import ChamberApplication
    print("✓ ChamberApplication imported")
    
    print("3. MainWindow imports...")
    try:
        from chamber_app.ui.main_window import MainWindow
        print("✓ MainWindow imported successfully")
    except Exception as e:
        print(f"✗ MainWindow import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("4. Creating test config...")
    config = {
        'DATABASE_URL': 'sqlite:///test.db',
        'APP_VERSION': '1.0.0',
        'DEVELOPER_OVERRIDE': True,
        'UI_THEME': 'dark',
        'WINDOW_WIDTH': 800,
        'WINDOW_HEIGHT': 600,
        'AUTO_REFRESH_INTERVAL': 5
    }
    print("✓ Config created")
    
    print("5. Creating application...")
    app = ChamberApplication(config)
    print("✓ Application created")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
