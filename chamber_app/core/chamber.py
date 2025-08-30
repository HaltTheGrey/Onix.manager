"""
Chamber model and management.
Core chamber representation and business logic.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .chamber_state import (
    ChamberState, ChamberStatus, ChamberType, ChamberMetrics, 
    StateManager, StateTransition
)


@dataclass
class WorkRequest:
    """Represents a work request/ticket for a chamber."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    priority: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, in_progress, completed, cancelled
    assigned_to: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    notes: List[str] = field(default_factory=list)
    
    def add_note(self, note: str, user: str = ""):
        """Add a note to the work request."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_note = f"[{timestamp}] {user}: {note}" if user else f"[{timestamp}] {note}"
        self.notes.append(formatted_note)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkRequest':
        """Create WorkRequest from dictionary."""
        work_request = cls()
        work_request.id = data['id']
        work_request.title = data['title']
        work_request.description = data['description']
        work_request.priority = data['priority']
        work_request.status = data['status']
        work_request.assigned_to = data['assigned_to']
        work_request.created_by = data['created_by']
        work_request.created_at = datetime.fromisoformat(data['created_at'])
        work_request.updated_at = datetime.fromisoformat(data['updated_at'])
        if data['completed_at']:
            work_request.completed_at = datetime.fromisoformat(data['completed_at'])
        work_request.estimated_hours = data['estimated_hours']
        work_request.actual_hours = data['actual_hours']
        work_request.notes = data['notes']
        return work_request


class Chamber:
    """
    Core chamber model representing a physical chamber unit.
    """
    
    def __init__(
        self, 
        name: str, 
        chamber_type: ChamberType, 
        chamber_id: Optional[str] = None
    ):
        self.id = chamber_id or str(uuid.uuid4())
        self.name = name
        self.type = chamber_type
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # State management
        self.state_manager = StateManager()
        
        # Telemetry and connection
        self.connection_config = {}
        self.last_telemetry = None
        self.is_connected = False
        self.connection_type = None  # ethernet, serial, grafana
        
        # Work requests
        self.work_requests: Dict[str, WorkRequest] = {}
          # Additional metadata
        self.location = ""
        self.model = ""
        self.serial_number = ""
        self.calibration_date = None
        self.notes = []
    
    def update_telemetry(self, metrics: ChamberMetrics):
        """Update chamber telemetry data."""
        self.last_telemetry = metrics
        self.updated_at = datetime.now()
    
    def set_state(self, new_state: ChamberState, reason: str = "", user: str = "") -> StateTransition:
        """Change chamber state."""
        transition = self.state_manager.change_state(new_state, reason, user)
        self.updated_at = datetime.now()
        return transition
    
    def set_status(self, new_status: ChamberStatus, reason: str = "", user: str = "") -> StateTransition:
        """Change chamber status."""
        transition = self.state_manager.change_status(new_status, reason, user)
        self.updated_at = datetime.now()
        return transition
    
    def clear_status(self, reason: str = "", user: str = "") -> Optional[StateTransition]:
        """Clear chamber status."""
        transition = self.state_manager.clear_status(reason, user)
        if transition:        self.updated_at = datetime.now()
        return transition
    
    def add_work_request(self, work_request: WorkRequest) -> str:
        """Add a work request to the chamber."""
        self.work_requests[work_request.id] = work_request
        self.updated_at = datetime.now()
        return work_request.id
    
    def remove_work_request(self, work_request_id: str) -> bool:
        """Remove a work request from the chamber."""
        if work_request_id in self.work_requests:
            del self.work_requests[work_request_id]
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_active_work_requests(self) -> List[WorkRequest]:
        """Get all active (non-completed) work requests."""
        return [
            wr for wr in self.work_requests.values()
            if wr.status not in ['completed', 'cancelled']
        ]
    
    def update_connection_status(self, is_connected: bool, connection_type: Optional[str] = None):
        """Update chamber connection status."""
        self.is_connected = is_connected
        if connection_type:
            self.connection_type = connection_type
        self.updated_at = datetime.now()
    
    def add_note(self, note: str, user: str = ""):
        """Add a note to the chamber."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_note = f"[{timestamp}] {user}: {note}" if user else f"[{timestamp}] {note}"
        self.notes.append(formatted_note)
        self.updated_at = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of chamber information."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'current_state': self.state_manager.current_state.value,
            'current_status': self.state_manager.current_status.value if self.state_manager.current_status else None,
            'state_duration': self.state_manager.get_state_duration(),
            'status_duration': self.state_manager.get_status_duration(),
            'is_connected': self.is_connected,
            'connection_type': self.connection_type,
            'active_work_requests': len(self.get_active_work_requests()),
            'last_updated': self.updated_at.isoformat(),
            'telemetry_available': self.last_telemetry is not None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chamber to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'state_manager': self.state_manager.to_dict(),
            'connection_config': self.connection_config,
            'is_connected': self.is_connected,
            'connection_type': self.connection_type,
            'work_requests': {k: v.to_dict() for k, v in self.work_requests.items()},
            'location': self.location,
            'model': self.model,
            'serial_number': self.serial_number,
            'calibration_date': self.calibration_date.isoformat() if self.calibration_date else None,
            'notes': self.notes,            'last_telemetry': {
                'temperature': self.last_telemetry.temperature,
                'vacuum_level': self.last_telemetry.vacuum_level,
                'humidity': self.last_telemetry.humidity,
                'pressure': self.last_telemetry.pressure,
                'elapsed_time': self.last_telemetry.elapsed_time,
                'timestamp': self.last_telemetry.timestamp.isoformat() if self.last_telemetry.timestamp else None
            } if self.last_telemetry else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chamber':
        """Create Chamber from dictionary."""
        chamber = cls(
            name=data['name'],
            chamber_type=ChamberType(data['type']),
            chamber_id=data['id']
        )
        
        chamber.created_at = datetime.fromisoformat(data['created_at'])
        chamber.updated_at = datetime.fromisoformat(data['updated_at'])
        chamber.state_manager = StateManager.from_dict(data['state_manager'])
        chamber.connection_config = data['connection_config']
        chamber.is_connected = data['is_connected']
        chamber.connection_type = data['connection_type']
        chamber.location = data['location']
        chamber.model = data['model']
        chamber.serial_number = data['serial_number']
        if data['calibration_date']:
            chamber.calibration_date = datetime.fromisoformat(data['calibration_date'])
        chamber.notes = data['notes']
        
        # Restore work requests
        chamber.work_requests = {
            k: WorkRequest.from_dict(v) 
            for k, v in data['work_requests'].items()
        }
        
        # Restore telemetry
        if data['last_telemetry']:
            telemetry_data = data['last_telemetry']
            chamber.last_telemetry = ChamberMetrics(
                temperature=telemetry_data['temperature'],
                vacuum_level=telemetry_data['vacuum_level'],
                humidity=telemetry_data['humidity'],
                pressure=telemetry_data['pressure'],
                elapsed_time=telemetry_data['elapsed_time'],
                timestamp=datetime.fromisoformat(telemetry_data['timestamp'])
            )
        
        return chamber
