"""UI package initialization."""

# Import only what's needed to avoid circular imports
# ChamberCard and other UI components will be imported directly where needed
from .work_requests_panel import WorkRequestsPanel
from .notifications import NotificationManager, NotificationPanel, NotificationToast
from .filters import AdvancedFilterPanel, QuickFilterBar, FilterWidget

# MainWindow and other components will be imported directly where needed
__all__ = [
    'WorkRequestsPanel',
    'NotificationManager',
    'NotificationPanel', 
    'NotificationToast',
    'AdvancedFilterPanel',
    'QuickFilterBar',
    'FilterWidget'
]
