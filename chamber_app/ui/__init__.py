"""UI package initialization."""

# Import only what's needed to avoid circular imports
from .chamber_card import ChamberCard
from .work_requests_panel import WorkRequestsPanel

# MainWindow and DataOverviewPanel will be imported directly where needed
__all__ = [
    'ChamberCard',
    'WorkRequestsPanel',
]
