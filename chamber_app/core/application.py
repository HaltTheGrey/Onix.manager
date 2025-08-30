"""
Main application controller.
Coordinates all subsystems and manages the application lifecycle.
"""

import asyncio
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..utils import get_logger, StructuredLogger
from ..data.database import DatabaseManager
from ..core.chamber import Chamber, WorkRequest
from ..core.chamber_state import ChamberType, ChamberState, ChamberStatus
from ..ui.main_window import MainWindow
from ..network.multi_user import MultiUserManager
from ..sdk.telemetry_manager import TelemetryManager


class ChamberApplication:
    """
    Main application class that orchestrates all components.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = StructuredLogger(__name__)
        self.logger.set_context(app_version=config.get('APP_VERSION', '1.0.0'))
        
        # Core components
        self.database = DatabaseManager(config)
        self.chambers: Dict[str, Chamber] = {}
        self.telemetry_manager = None
        self.multi_user_manager = None
        self.main_window = None
        
        # Application state
        self.is_running = False
        self.current_user = "default_user"  # TODO: Implement proper authentication
        
        # Event loop for async operations
        self.event_loop = None
        self.background_thread = None
        
        self.logger.info("Chamber Application initialized")
    
    def initialize(self):
        """Initialize all application components."""
        try:
            self.logger.info("Initializing application components")
            
            # Initialize database
            self.database.initialize()
            
            # Load existing chambers from database
            self._load_chambers()
            
            # Initialize telemetry manager
            self.telemetry_manager = TelemetryManager(self.config)
            
            # Initialize multi-user manager
            self.multi_user_manager = MultiUserManager(self.config)
            
            # Create default chambers if none exist
            if not self.chambers:
                self._create_default_chambers()
            
            self.logger.info("Application components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}", exc_info=True)
            raise
    
    def run(self):
        """Run the application."""
        try:
            self.initialize()
            self.is_running = True
            
            # Start background services
            self._start_background_services()
            
            # Initialize and run UI
            self.main_window = MainWindow(self, self.config)
            self.main_window.run()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully."""
        self.logger.info("Shutting down application")
        self.is_running = False
        
        # Save all chamber data
        self._save_chambers()
        
        # Stop background services
        if self.telemetry_manager:
            self.telemetry_manager.stop()
        
        if self.multi_user_manager:
            self.multi_user_manager.stop()
        
        # Close database
        if self.database:
            self.database.close()
          # Stop background thread
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=5)
        
        self.logger.info("Application shutdown complete")
    
    def _start_background_services(self):
        """Start background services in a separate thread."""
        def background_worker():
            # Create event loop for background tasks
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            try:
                # Start telemetry collection
                if self.telemetry_manager:
                    self.event_loop.run_until_complete(self.telemetry_manager.start())
                
                # Start multi-user services
                if self.multi_user_manager:
                    self.multi_user_manager.start()
                
                # Run periodic tasks
                self.event_loop.run_until_complete(self._run_periodic_tasks())
                
            except Exception as e:
                self.logger.error(f"Background service error: {e}", exc_info=True)
            finally:
                self.event_loop.close()
        
        self.background_thread = threading.Thread(target=background_worker, daemon=True)
        self.background_thread.start()
        self.logger.info("Background services started")
    
    async def _run_periodic_tasks(self):
        """Run periodic maintenance tasks."""
        while self.is_running:
            try:
                # Auto-save chambers periodically
                await asyncio.sleep(60)  # Save every minute
                if self.is_running:
                    self._save_chambers()
                
                # Update telemetry for connected chambers
                await self._update_telemetry()
                
                # Clean up old data
                await self._cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"Periodic task error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _update_telemetry(self):
        """Update telemetry for all connected chambers."""
        if not self.telemetry_manager:
            return
        
        for chamber in self.chambers.values():
            if chamber.is_connected:
                try:
                    metrics = await self.telemetry_manager.get_chamber_metrics(chamber.id)
                    if metrics:
                        chamber.update_telemetry(metrics)
                except Exception as e:
                    self.logger.error(f"Failed to update telemetry for chamber {chamber.name}: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old telemetry data based on retention policy."""
        retention_days = self.config.get('TELEMETRY_RETENTION_DAYS', 90)
        try:
            await self.database.cleanup_old_telemetry(retention_days)
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def _load_chambers(self):
        """Load chambers from database."""
        try:
            chamber_data = self.database.get_all_chambers()
            for data in chamber_data:
                chamber = Chamber.from_dict(data)
                self.chambers[chamber.id] = chamber
            
            self.logger.info(f"Loaded {len(self.chambers)} chambers from database")
            
        except Exception as e:
            self.logger.error(f"Failed to load chambers: {e}", exc_info=True)
    
    def _save_chambers(self):
        """Save all chambers to database."""
        try:
            for chamber in self.chambers.values():
                self.database.save_chamber(chamber.to_dict())
            
            self.logger.debug(f"Saved {len(self.chambers)} chambers to database")
            
        except Exception as e:
            self.logger.error(f"Failed to save chambers: {e}", exc_info=True)
    
    def _create_default_chambers(self):
        """Create default chambers for each type."""
        chamber_types = self.config.get('DEFAULT_CHAMBER_TYPES', ['TVAC', 'HASS', 'THERMAL'])
        
        for chamber_type_str in chamber_types:
            try:
                chamber_type = ChamberType(chamber_type_str)
                chamber = Chamber(
                    name=f"{chamber_type_str} Chamber 1",
                    chamber_type=chamber_type
                )
                self.chambers[chamber.id] = chamber
                
            except ValueError:
                self.logger.warning(f"Invalid chamber type: {chamber_type_str}")
        
        self.logger.info(f"Created {len(self.chambers)} default chambers")
    
    # Public API methods for UI interaction
    
    def get_chambers(self) -> List[Chamber]:
        """Get all chambers."""
        return list(self.chambers.values())
    
    def get_chambers_by_type(self, chamber_type: ChamberType) -> List[Chamber]:
        """Get chambers of a specific type."""
        return [c for c in self.chambers.values() if c.type == chamber_type]
    
    def get_chamber(self, chamber_id: str) -> Optional[Chamber]:
        """Get a specific chamber by ID."""
        return self.chambers.get(chamber_id)
    
    def add_chamber(self, name: str, chamber_type: ChamberType) -> Chamber:
        """Add a new chamber."""
        chamber = Chamber(name=name, chamber_type=chamber_type)
        self.chambers[chamber.id] = chamber
        
        # Save immediately
        self.database.save_chamber(chamber.to_dict())
        
        self.logger.info(f"Added new chamber: {name} ({chamber_type.value})")
        return chamber
    
    def remove_chamber(self, chamber_id: str) -> bool:
        """Remove a chamber."""
        if chamber_id in self.chambers:
            chamber = self.chambers[chamber_id]
            del self.chambers[chamber_id]
            
            # Remove from database
            self.database.delete_chamber(chamber_id)
            
            self.logger.info(f"Removed chamber: {chamber.name}")
            return True
        return False
    
    def update_chamber_state(self, chamber_id: str, new_state: ChamberState, reason: str = "") -> bool:
        """Update chamber state."""
        chamber = self.chambers.get(chamber_id)
        if chamber:
            chamber.set_state(new_state, reason, self.current_user)
            self.logger.info(f"Chamber {chamber.name} state changed to {new_state.value}")
            return True
        return False
    
    def update_chamber_status(self, chamber_id: str, new_status: ChamberStatus, reason: str = "") -> bool:
        """Update chamber status."""
        chamber = self.chambers.get(chamber_id)
        if chamber:
            chamber.set_status(new_status, reason, self.current_user)
            self.logger.info(f"Chamber {chamber.name} status changed to {new_status.value}")
            return True
        return False
    
    def clear_chamber_status(self, chamber_id: str, reason: str = "") -> bool:
        """Clear chamber status."""
        chamber = self.chambers.get(chamber_id)
        if chamber:
            chamber.clear_status(reason, self.current_user)
            self.logger.info(f"Chamber {chamber.name} status cleared")
            return True
        return False
    
    def add_work_request(self, chamber_id: str, work_request: WorkRequest) -> bool:
        """Add a work request to a chamber."""
        chamber = self.chambers.get(chamber_id)
        if chamber:
            chamber.add_work_request(work_request)
            self.logger.info(f"Added work request '{work_request.title}' to chamber {chamber.name}")
            return True
        return False
    
    def get_chamber_statistics(self) -> Dict[str, Any]:
        """Get overall chamber statistics."""
        stats = {
            'total_chambers': len(self.chambers),
            'by_type': {},
            'by_state': {},
            'by_status': {},
            'connected_chambers': 0,
            'active_work_requests': 0
        }
        
        for chamber in self.chambers.values():
            # Count by type
            type_key = chamber.type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
            
            # Count by state
            state_key = chamber.state_manager.current_state.value
            stats['by_state'][state_key] = stats['by_state'].get(state_key, 0) + 1
            
            # Count by status
            if chamber.state_manager.current_status:
                status_key = chamber.state_manager.current_status.value
                stats['by_status'][status_key] = stats['by_status'].get(status_key, 0) + 1
            
            # Count connections
            if chamber.is_connected:
                stats['connected_chambers'] += 1
            
            # Count active work requests
            stats['active_work_requests'] += len(chamber.get_active_work_requests())
        
        return stats
