#!/usr/bin/env python3
"""
Test specific UI imports one by one
"""
import sys
import os
from pathlib import Path

# Redirect stdout to a file to capture output
import sys
sys.stdout = open('debug_output.txt', 'w', buffering=1)
sys.stderr = sys.stdout

print("Starting UI import test...")

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("1. Testing basic imports...")
    import tkinter as tk
    print("✓ tkinter")
    
    import customtkinter as ctk
    print("✓ customtkinter")
    
    print("2. Testing chamber_app imports...")
    from chamber_app.utils import get_logger
    print("✓ utils.get_logger")
    
    from chamber_app.core.chamber_state import ChamberType, ChamberState, ChamberStatus
    print("✓ chamber_state")
    
    print("3. Testing specific UI panel imports...")
    
    print("3a. Testing data_overview_panel...")
    from chamber_app.ui.data_overview_panel import DataOverviewPanel
    print("✓ data_overview_panel")
    
    print("3b. Testing notifications...")
    from chamber_app.ui.notifications import NotificationPanel
    print("✓ notifications.NotificationPanel")
    
    print("3c. Testing filters...")
    from chamber_app.ui.filters import AdvancedFilterPanel, QuickFilterBar
    print("✓ filters")
    
    print("3d. Testing performance_dashboard...")
    from chamber_app.ui.performance_dashboard import PerformanceDashboard
    print("✓ performance_dashboard")
    
    print("3e. Testing weekly_timeline_panel...")
    from chamber_app.ui.weekly_timeline_panel import WeeklyTimelinePanel, TimelineLegendPanel
    print("✓ weekly_timeline_panel")
    
    print("4. All UI imports successful!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print("Test completed - check debug_output.txt")
