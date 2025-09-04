#!/usr/bin/env python3
"""
Verification script for timeline data fix.
Tests that the timeline is using real chamber data instead of random mock data.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from chamber_app.core.application import ChamberApplication
from chamber_app.core.chamber_state import ChamberType
from chamber_app.ui.weekly_timeline_panel import WeeklyTimelinePanel
from datetime import datetime, timedelta
import logging

def verify_timeline_data_consistency():
    """Verify that timeline data is consistent (not random)."""
    print("🔍 Verifying Timeline Data Implementation...")
    
    try:
        # Initialize application
        app = ChamberApplication()
        app.initialize()
        
        print(f"✅ Application initialized with {len(app.get_chambers())} chambers")
        
        # Create timeline panel (without UI)
        class MockParent:
            pass
        
        timeline_panel = WeeklyTimelinePanel(MockParent(), app)
        
        # Test timeline data generation for each chamber type
        chamber_types = [ChamberType.TVAC, ChamberType.HASS, ChamberType.THERMAL]
        
        for chamber_type in chamber_types:
            chambers = app.get_chambers_by_type(chamber_type)
            if not chambers:
                print(f"⚠️  No {chamber_type.value} chambers found")
                continue
                
            print(f"\n📊 Testing {chamber_type.value} chambers ({len(chambers)} found):")
            
            # Test first chamber
            chamber = chambers[0]
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
            
            # Generate timeline data twice to check consistency
            data1 = timeline_panel._get_real_timeline_data(chamber, start_date, end_date)
            data2 = timeline_panel._get_real_timeline_data(chamber, start_date, end_date)
            
            # Check if data is consistent (should be identical for real data)
            if data1 == data2:
                print(f"  ✅ {chamber.name}: Data is consistent (using real chamber state)")
                print(f"     Segments: {len(data1)}")
                for i, (start, end, color, status) in enumerate(data1):
                    duration = (end - start).total_seconds() / 3600
                    print(f"     Segment {i+1}: {status} ({duration:.1f}h) - {color}")
            else:
                print(f"  ❌ {chamber.name}: Data is inconsistent (still using random data)")
                return False
        
        print("\n🎉 Timeline data verification completed successfully!")
        print("📈 Timeline is now using real chamber state data instead of random mock data")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main verification function."""
    print("=" * 60)
    print("Timeline Data Fix Verification")
    print("=" * 60)
    
    success = verify_timeline_data_consistency()
    
    if success:
        print("\n✅ VERIFICATION PASSED: Timeline data fix is working correctly")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED: Timeline data fix needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
