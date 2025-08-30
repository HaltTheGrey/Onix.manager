"""
Tests for chamber state management.
"""

import pytest
from datetime import datetime

from chamber_app.core.chamber_state import (
    ChamberState, ChamberStatus, ChamberType, ChamberMetrics, StateManager
)


class TestChamberState:
    """Test chamber state enums."""
    
    def test_chamber_state_values(self):
        """Test chamber state enum values."""
        assert ChamberState.AVAILABLE_EMPTY.value == "available/empty"
        assert ChamberState.STAGING.value == "staging"
        assert ChamberState.SETUP.value == "setup"
        assert ChamberState.TEST_START.value == "test start"
        assert ChamberState.TEST_NOMINAL.value == "test nominal (auto)"
        assert ChamberState.TEST_END.value == "test end"
        assert ChamberState.TEST_TEARDOWN.value == "test teardown"
    
    def test_chamber_status_values(self):
        """Test chamber status enum values."""
        assert ChamberStatus.ENGINEER_NEEDED.value == "engineer needed"
        assert ChamberStatus.ISSUES_HALTED.value == "issues/halted"
        assert ChamberStatus.MAINTENANCE.value == "maintenance"
        assert ChamberStatus.BAKE_OUT.value == "bake out"
        assert ChamberStatus.CHAMBER_DOWN.value == "chamber down"
        assert ChamberStatus.SETUP_ISSUES.value == "setup issues"
        assert ChamberStatus.TEST_ISSUES.value == "test issues"
        assert ChamberStatus.CURRENTLY_BEING_WORKED_ON.value == "currently being worked on"
        assert ChamberStatus.SSL_SUPPORT_NEEDED.value == "SSL support needed"
    
    def test_chamber_type_values(self):
        """Test chamber type enum values."""
        assert ChamberType.TVAC.value == "TVAC"
        assert ChamberType.HASS.value == "HASS"
        assert ChamberType.THERMAL.value == "THERMAL"


class TestChamberMetrics:
    """Test chamber metrics."""
    
    def test_metrics_creation(self):
        """Test creating chamber metrics."""
        metrics = ChamberMetrics(
            temperature=25.0,
            vacuum_level=1e-6,
            humidity=45.0,
            pressure=1013.25,
            elapsed_time=3600.0
        )
        
        assert metrics.temperature == 25.0
        assert metrics.vacuum_level == 1e-6
        assert metrics.humidity == 45.0
        assert metrics.pressure == 1013.25
        assert metrics.elapsed_time == 3600.0
        assert isinstance(metrics.timestamp, datetime)
    
    def test_metrics_default_timestamp(self):
        """Test that timestamp is set by default."""
        metrics = ChamberMetrics()
        assert metrics.timestamp is not None
        assert isinstance(metrics.timestamp, datetime)


class TestStateManager:
    """Test state manager functionality."""
    
    def test_initial_state(self):
        """Test initial state of state manager."""
        manager = StateManager()
        
        assert manager.current_state == ChamberState.AVAILABLE_EMPTY
        assert manager.current_status is None
        assert len(manager.state_history) == 0
        assert len(manager.status_history) == 0
    
    def test_state_change(self):
        """Test changing chamber state."""
        manager = StateManager()
        
        # Change to staging
        transition = manager.change_state(ChamberState.STAGING, "Starting new test", "test_user")
        
        assert manager.current_state == ChamberState.STAGING
        assert len(manager.state_history) == 1
        assert transition.from_value == ChamberState.AVAILABLE_EMPTY.value
        assert transition.to_value == ChamberState.STAGING.value
        assert transition.reason == "Starting new test"
        assert transition.user == "test_user"
    
    def test_status_change(self):
        """Test changing chamber status."""
        manager = StateManager()
        
        # Set a status
        transition = manager.change_status(ChamberStatus.MAINTENANCE, "Scheduled maintenance", "tech_user")
        
        assert manager.current_status == ChamberStatus.MAINTENANCE
        assert len(manager.status_history) == 1
        assert transition.from_value == "none"
        assert transition.to_value == ChamberStatus.MAINTENANCE.value
        assert transition.reason == "Scheduled maintenance"
        assert transition.user == "tech_user"
    
    def test_clear_status(self):
        """Test clearing chamber status."""
        manager = StateManager()
        
        # Set a status first
        manager.change_status(ChamberStatus.MAINTENANCE, "Test", "user")
        
        # Clear the status
        transition = manager.clear_status("Maintenance complete", "user")
        
        assert manager.current_status is None
        assert len(manager.status_history) == 2
        assert transition.from_value == ChamberStatus.MAINTENANCE.value
        assert transition.to_value == "none"
    
    def test_state_duration(self):
        """Test state duration calculation."""
        manager = StateManager()
        
        # Duration should be close to 0 for new state
        duration = manager.get_state_duration()
        assert duration >= 0
        assert duration < 1  # Should be less than 1 second
    
    def test_status_duration(self):
        """Test status duration calculation."""
        manager = StateManager()
        
        # No status set, should return 0
        assert manager.get_status_duration() == 0
        
        # Set a status
        manager.change_status(ChamberStatus.MAINTENANCE, "Test", "user")
        
        # Duration should be close to 0 for new status
        duration = manager.get_status_duration()
        assert duration >= 0
        assert duration < 1
    
    def test_state_statistics(self):
        """Test state statistics calculation."""
        manager = StateManager()
        
        # Change states a few times
        manager.change_state(ChamberState.STAGING, "Test", "user")
        manager.change_state(ChamberState.SETUP, "Test", "user")
        
        stats = manager.get_state_statistics()
        
        # Should have entries for all states
        assert ChamberState.AVAILABLE_EMPTY.value in stats
        assert ChamberState.STAGING.value in stats
        assert ChamberState.SETUP.value in stats
        
        # Current state (SETUP) should have non-zero time
        assert stats[ChamberState.SETUP.value] >= 0
    
    def test_status_statistics(self):
        """Test status statistics calculation."""
        manager = StateManager()
        
        # Set and clear status
        manager.change_status(ChamberStatus.MAINTENANCE, "Test", "user")
        manager.clear_status("Done", "user")
        
        stats = manager.get_status_statistics()
        
        # Should have entry for maintenance
        assert ChamberStatus.MAINTENANCE.value in stats
        assert stats[ChamberStatus.MAINTENANCE.value] >= 0
    
    def test_serialization(self):
        """Test state manager serialization."""
        manager = StateManager()
        
        # Make some changes
        manager.change_state(ChamberState.STAGING, "Test", "user")
        manager.change_status(ChamberStatus.MAINTENANCE, "Test", "user")
        
        # Serialize to dict
        data = manager.to_dict()
        
        # Check structure
        assert 'current_state' in data
        assert 'current_status' in data
        assert 'state_history' in data
        assert 'status_history' in data
        
        # Deserialize
        restored_manager = StateManager.from_dict(data)
        
        # Check restored state
        assert restored_manager.current_state == manager.current_state
        assert restored_manager.current_status == manager.current_status
        assert len(restored_manager.state_history) == len(manager.state_history)
        assert len(restored_manager.status_history) == len(manager.status_history)
