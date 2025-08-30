"""
Tests for chamber model and functionality.
"""

import pytest
from datetime import datetime

from chamber_app.core.chamber import Chamber, WorkRequest
from chamber_app.core.chamber_state import ChamberType, ChamberState, ChamberStatus, ChamberMetrics


class TestWorkRequest:
    """Test work request functionality."""
    
    def test_work_request_creation(self):
        """Test creating a work request."""
        work_request = WorkRequest(
            title="Fix vacuum pump",
            description="Vacuum pump is making noise",
            priority="high",
            assigned_to="tech1",
            created_by="manager1"
        )
        
        assert work_request.title == "Fix vacuum pump"
        assert work_request.description == "Vacuum pump is making noise"
        assert work_request.priority == "high"
        assert work_request.status == "open"
        assert work_request.assigned_to == "tech1"
        assert work_request.created_by == "manager1"
        assert isinstance(work_request.created_at, datetime)
        assert work_request.id is not None
    
    def test_add_note(self):
        """Test adding notes to work request."""
        work_request = WorkRequest(title="Test", created_by="user")
        
        work_request.add_note("Started investigation", "tech1")
        work_request.add_note("Found the issue")
        
        assert len(work_request.notes) == 2
        assert "tech1" in work_request.notes[0]
        assert "Started investigation" in work_request.notes[0]
        assert "Found the issue" in work_request.notes[1]
    
    def test_work_request_serialization(self):
        """Test work request serialization."""
        work_request = WorkRequest(
            title="Test Request",
            description="Test description",
            priority="medium",
            created_by="user1"
        )
        work_request.add_note("Test note", "user1")
        
        # Serialize
        data = work_request.to_dict()
        
        # Check structure
        assert data['title'] == "Test Request"
        assert data['description'] == "Test description"
        assert data['priority'] == "medium"
        assert data['created_by'] == "user1"
        assert len(data['notes']) == 1
        
        # Deserialize
        restored = WorkRequest.from_dict(data)
        
        assert restored.title == work_request.title
        assert restored.description == work_request.description
        assert restored.priority == work_request.priority
        assert restored.created_by == work_request.created_by
        assert len(restored.notes) == len(work_request.notes)


class TestChamber:
    """Test chamber functionality."""
    
    def test_chamber_creation(self):
        """Test creating a chamber."""
        chamber = Chamber("Test TVAC", ChamberType.TVAC)
        
        assert chamber.name == "Test TVAC"
        assert chamber.type == ChamberType.TVAC
        assert chamber.state_manager.current_state == ChamberState.AVAILABLE_EMPTY
        assert chamber.state_manager.current_status is None
        assert chamber.is_connected is False
        assert len(chamber.work_requests) == 0
        assert chamber.id is not None
    
    def test_update_telemetry(self):
        """Test updating chamber telemetry."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        metrics = ChamberMetrics(
            temperature=25.5,
            vacuum_level=1e-6,
            humidity=45.0,
            pressure=1013.25
        )
        
        chamber.update_telemetry(metrics)
        
        assert chamber.last_telemetry == metrics
        assert chamber.last_telemetry.temperature == 25.5
    
    def test_state_change(self):
        """Test changing chamber state."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        transition = chamber.set_state(ChamberState.STAGING, "Starting test", "user1")
        
        assert chamber.state_manager.current_state == ChamberState.STAGING
        assert transition.to_value == ChamberState.STAGING.value
        assert transition.reason == "Starting test"
        assert transition.user == "user1"
    
    def test_status_change(self):
        """Test changing chamber status."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        transition = chamber.set_status(ChamberStatus.MAINTENANCE, "Scheduled maintenance", "tech1")
        
        assert chamber.state_manager.current_status == ChamberStatus.MAINTENANCE
        assert transition.to_value == ChamberStatus.MAINTENANCE.value
        assert transition.reason == "Scheduled maintenance"
        assert transition.user == "tech1"
    
    def test_clear_status(self):
        """Test clearing chamber status."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        # Set status first
        chamber.set_status(ChamberStatus.MAINTENANCE, "Test", "user")
        
        # Clear it
        transition = chamber.clear_status("Maintenance complete", "user")
        
        assert chamber.state_manager.current_status is None
        assert transition.to_value == "none"
    
    def test_work_request_management(self):
        """Test managing work requests."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        # Create work request
        work_request = WorkRequest(
            title="Fix issue",
            description="Something is broken",
            created_by="user1"
        )
        
        # Add to chamber
        request_id = chamber.add_work_request(work_request)
        
        assert request_id == work_request.id
        assert work_request.id in chamber.work_requests
        assert len(chamber.get_active_work_requests()) == 1
        
        # Complete the request
        work_request.status = "completed"
        work_request.completed_at = datetime.now()
        
        assert len(chamber.get_active_work_requests()) == 0
        
        # Remove request
        removed = chamber.remove_work_request(work_request.id)
        
        assert removed is True
        assert work_request.id not in chamber.work_requests
    
    def test_connection_status(self):
        """Test updating connection status."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        assert chamber.is_connected is False
        assert chamber.connection_type is None
        
        chamber.update_connection_status(True, "ethernet")
        
        assert chamber.is_connected is True
        assert chamber.connection_type == "ethernet"
    
    def test_notes(self):
        """Test adding notes to chamber."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        
        chamber.add_note("Chamber calibrated", "tech1")
        chamber.add_note("Ready for use")
        
        assert len(chamber.notes) == 2
        assert "tech1" in chamber.notes[0]
        assert "Chamber calibrated" in chamber.notes[0]
        assert "Ready for use" in chamber.notes[1]
    
    def test_chamber_summary(self):
        """Test getting chamber summary."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        chamber.set_state(ChamberState.TEST_START, "Starting test", "user1")
        chamber.update_connection_status(True, "grafana")
        
        summary = chamber.get_summary()
        
        assert summary['name'] == "Test Chamber"
        assert summary['type'] == "TVAC"
        assert summary['current_state'] == "test start"
        assert summary['current_status'] is None
        assert summary['is_connected'] is True
        assert summary['connection_type'] == "grafana"
        assert summary['active_work_requests'] == 0
        assert 'state_duration' in summary
        assert 'status_duration' in summary
    
    def test_chamber_serialization(self):
        """Test chamber serialization."""
        chamber = Chamber("Test Chamber", ChamberType.TVAC)
        chamber.set_state(ChamberState.STAGING, "Test", "user")
        chamber.location = "Building A"
        chamber.model = "TVAC-2000"
        chamber.serial_number = "SN123456"
        
        # Add telemetry
        metrics = ChamberMetrics(temperature=25.0, vacuum_level=1e-6)
        chamber.update_telemetry(metrics)
        
        # Add work request
        work_request = WorkRequest(title="Test work", created_by="user")
        chamber.add_work_request(work_request)
        
        # Serialize
        data = chamber.to_dict()
        
        # Check structure
        assert data['name'] == "Test Chamber"
        assert data['type'] == "TVAC"
        assert data['location'] == "Building A"
        assert data['model'] == "TVAC-2000"
        assert data['serial_number'] == "SN123456"
        assert 'state_manager' in data
        assert 'work_requests' in data
        assert 'last_telemetry' in data
        
        # Deserialize
        restored = Chamber.from_dict(data)
        
        assert restored.name == chamber.name
        assert restored.type == chamber.type
        assert restored.location == chamber.location
        assert restored.model == chamber.model
        assert restored.serial_number == chamber.serial_number
        assert restored.state_manager.current_state == chamber.state_manager.current_state
        assert len(restored.work_requests) == len(chamber.work_requests)
        assert restored.last_telemetry.temperature == chamber.last_telemetry.temperature
