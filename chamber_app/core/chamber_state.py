"""
Chamber state definitions and management.
Defines the possible states and statuses for chambers.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class ChamberState(Enum):
    """Defined chamber states that can be selected by technicians."""
    AVAILABLE_EMPTY = "available/empty"
    STAGING = "staging"
    SETUP = "setup"
    TEST_START = "test start"
    TEST_NOMINAL = "test nominal (auto)"
    TEST_END = "test end"
    TEST_TEARDOWN = "test teardown"


class ChamberStatus(Enum):
    """Status labels for complications and maintenance."""
    ENGINEER_NEEDED = "engineer needed"
    ISSUES_HALTED = "issues/halted"
    MAINTENANCE = "maintenance"
    BAKE_OUT = "bake out"
    CHAMBER_DOWN = "chamber down"
    SETUP_ISSUES = "setup issues"
    TEST_ISSUES = "test issues"
    CURRENTLY_BEING_WORKED_ON = "currently being worked on"
    SSL_SUPPORT_NEEDED = "SSL support needed"


class ChamberType(Enum):
    """Types of chambers supported by the system."""
    TVAC = "TVAC"
    HASS = "HASS"
    THERMAL = "THERMAL"


@dataclass
class StateTransition:
    """Represents a state or status change with timestamp."""
    from_value: str
    to_value: str
    timestamp: datetime
    duration_seconds: float
    reason: str = ""
    user: str = ""


@dataclass
class ChamberMetrics:
    """Real-time telemetry data from chambers."""
    temperature: float = 0.0
    vacuum_level: float = 0.0
    humidity: float = 0.0
    pressure: float = 0.0
    elapsed_time: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class StateManager:
    """Manages chamber state transitions and history."""
    
    def __init__(self):
        self.state_history: List[StateTransition] = []
        self.status_history: List[StateTransition] = []
        self.current_state = ChamberState.AVAILABLE_EMPTY
        self.current_status = None
        self.state_start_time = datetime.now()
        self.status_start_time = None
    
    def change_state(self, new_state: ChamberState, reason: str = "", user: str = "") -> StateTransition:
        """
        Change chamber state and record the transition.
        
        Args:
            new_state: The new state to transition to
            reason: Optional reason for the state change
            user: User making the change
            
        Returns:
            StateTransition object representing the change
        """
        now = datetime.now()
        duration = (now - self.state_start_time).total_seconds()
        
        transition = StateTransition(
            from_value=self.current_state.value,
            to_value=new_state.value,
            timestamp=now,
            duration_seconds=duration,
            reason=reason,
            user=user
        )
        
        self.state_history.append(transition)
        self.current_state = new_state
        self.state_start_time = now
        
        # Auto-transition logic
        if new_state == ChamberState.TEST_START:
            # Automatically move to test nominal after test start
            self._schedule_auto_transition(ChamberState.TEST_NOMINAL)
        
        return transition
    
    def change_status(self, new_status: ChamberStatus, reason: str = "", user: str = "") -> StateTransition:
        """
        Change chamber status and record the transition.
        
        Args:
            new_status: The new status to set
            reason: Reason for the status change
            user: User making the change
            
        Returns:
            StateTransition object representing the change
        """
        now = datetime.now()
        duration = 0.0
        
        if self.current_status is not None and self.status_start_time is not None:        duration = (now - self.status_start_time).total_seconds()
        
        from_value = self.current_status.value if self.current_status else "none"
        
        transition = StateTransition(
            from_value=from_value,
            to_value=new_status.value,
            timestamp=now,
            duration_seconds=duration,
            reason=reason,
            user=user
        )
        
        self.status_history.append(transition)
        self.current_status = new_status
        self.status_start_time = now
        
        return transition
    
    def clear_status(self, reason: str = "", user: str = "") -> Optional[StateTransition]:
        """Clear the current status."""
        if self.current_status is None:
            return None
        
        now = datetime.now()
        duration = 0.0
        if self.status_start_time is not None:
            duration = (now - self.status_start_time).total_seconds()
        
        transition = StateTransition(
            from_value=self.current_status.value,
            to_value="none",
            timestamp=now,
            duration_seconds=duration,
            reason=reason,
            user=user
        )
        
        self.status_history.append(transition)
        self.current_status = None
        self.status_start_time = None
        
        return transition
    
    def get_state_duration(self) -> float:
        """Get duration in current state (seconds)."""
        return (datetime.now() - self.state_start_time).total_seconds()
    
    def get_status_duration(self) -> float:
        """Get duration in current status (seconds)."""
        if self.status_start_time is None:
            return 0.0
        return (datetime.now() - self.status_start_time).total_seconds()
    
    def get_state_statistics(self) -> Dict[str, float]:
        """Get time spent in each state."""
        stats = {}
        
        for state in ChamberState:
            total_time = 0.0
            for transition in self.state_history:
                if transition.to_value == state.value:
                    total_time += transition.duration_seconds
            
            # Add current state time if applicable
            if self.current_state == state:
                total_time += self.get_state_duration()
            
            stats[state.value] = total_time
        
        return stats
    
    def get_status_statistics(self) -> Dict[str, float]:
        """Get time spent in each status."""
        stats = {}
        
        for status in ChamberStatus:
            total_time = 0.0
            for transition in self.status_history:
                if transition.to_value == status.value:
                    total_time += transition.duration_seconds
            
            # Add current status time if applicable
            if self.current_status == status:
                total_time += self.get_status_duration()
            
            stats[status.value] = total_time
        
        return stats
    
    def _schedule_auto_transition(self, target_state: ChamberState, delay_seconds: int = 5):
        """Schedule an automatic state transition (simplified implementation)."""
        # In a full implementation, this would use a timer or async scheduler
        # For now, this is a placeholder for the auto-transition logic
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state manager to dictionary for serialization."""
        return {
            'current_state': self.current_state.value,
            'current_status': self.current_status.value if self.current_status else None,
            'state_start_time': self.state_start_time.isoformat(),
            'status_start_time': self.status_start_time.isoformat() if self.status_start_time else None,
            'state_history': [
                {
                    'from_value': t.from_value,
                    'to_value': t.to_value,
                    'timestamp': t.timestamp.isoformat(),
                    'duration_seconds': t.duration_seconds,
                    'reason': t.reason,
                    'user': t.user
                }
                for t in self.state_history
            ],
            'status_history': [
                {
                    'from_value': t.from_value,
                    'to_value': t.to_value,
                    'timestamp': t.timestamp.isoformat(),
                    'duration_seconds': t.duration_seconds,
                    'reason': t.reason,
                    'user': t.user
                }
                for t in self.status_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateManager':
        """Create StateManager from dictionary."""
        manager = cls()
        
        # Set current state and status
        manager.current_state = ChamberState(data['current_state'])
        if data['current_status']:
            manager.current_status = ChamberStatus(data['current_status'])
        
        # Set timestamps
        manager.state_start_time = datetime.fromisoformat(data['state_start_time'])
        if data['status_start_time']:
            manager.status_start_time = datetime.fromisoformat(data['status_start_time'])
        
        # Restore history
        manager.state_history = [
            StateTransition(
                from_value=t['from_value'],
                to_value=t['to_value'],
                timestamp=datetime.fromisoformat(t['timestamp']),
                duration_seconds=t['duration_seconds'],
                reason=t['reason'],
                user=t['user']
            )
            for t in data['state_history']
        ]
        
        manager.status_history = [
            StateTransition(
                from_value=t['from_value'],
                to_value=t['to_value'],
                timestamp=datetime.fromisoformat(t['timestamp']),
                duration_seconds=t['duration_seconds'],
                reason=t['reason'],
                user=t['user']
            )
            for t in data['status_history']
        ]
        
        return manager
