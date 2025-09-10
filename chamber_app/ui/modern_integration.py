"""
Modern Main Window Integration
Upgrades the existing main window with modern UI components
"""

import customtkinter as ctk
from typing import Dict, Any, Optional
from datetime import datetime

from .modern_theme import ModernThemeManager, ModernFrame, ModernButton, ModernLabel, get_theme_manager, apply_modern_styling
from .enhanced_navigation import NavigationManager, SearchManager, ModernNavigationBar
from .modern_chamber_card import ModernChamberCard
from .modern_dialogs import ModernWorkRequestDialog
from ..utils import get_logger


class ModernMainWindowIntegration:
    """
    Integration layer that adds modern UI components to the existing main window
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.app = main_window.app
        self.logger = get_logger(__name__)
        
        # Initialize modern components
        self.theme_manager = get_theme_manager()
        self.navigation_manager = NavigationManager()
        self.search_manager = SearchManager(self.app)
        
        # State
        self.modern_enabled = True
        self.modern_chamber_cards: Dict[str, ModernChamberCard] = {}
        self.modern_navigation_bar: Optional[ModernNavigationBar] = None
        
        self.logger.info("Modern UI integration initialized")
    
    def initialize_modern_ui(self):
        """Initialize modern UI components on top of existing interface"""
        try:
            # Apply modern theme to main window
            self._apply_modern_theme_to_window()
            
            # Add modern navigation if enabled
            if self.modern_enabled:
                self._add_modern_navigation()
            
            # Convert existing chamber cards to modern versions
            self._modernize_chamber_cards()
            
            # Setup modern interactions
            self._setup_modern_interactions()
            
            self.logger.info("Modern UI components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize modern UI: {e}")
    
    def _apply_modern_theme_to_window(self):
        """Apply modern theming to the main window"""
        try:
            # Apply theme to main window
            self.theme_manager.apply_theme("modern_dark")
            
            # Apply modern styling to existing frames
            if hasattr(self.main_window, 'root'):
                apply_modern_styling(self.main_window.root, "main_window")
            
            if hasattr(self.main_window, 'main_container'):
                apply_modern_styling(self.main_window.main_container, "container")
            
            if hasattr(self.main_window, 'menu_frame'):
                apply_modern_styling(self.main_window.menu_frame, "sidebar")
                
        except Exception as e:
            self.logger.error(f"Error applying modern theme: {e}")
    
    def _add_modern_navigation(self):
        """Add modern navigation bar"""
        try:
            if not hasattr(self.main_window, 'root'):
                return
            
            # Create modern navigation bar at the top
            nav_frame = ModernFrame(self.main_window.root)
            nav_frame.pack(fill="x", padx=10, pady=5, before=self.main_window.main_container)
            
            self.modern_navigation_bar = ModernNavigationBar(
                nav_frame,
                self.app
            )
            
            # Register navigation callbacks
            self._register_navigation_callbacks()
            
        except Exception as e:
            self.logger.error(f"Error adding modern navigation: {e}")
    
    def _register_navigation_callbacks(self):
        """Register navigation callbacks for modern navigation"""
        try:
            # Map panel names to callback functions
            panel_callbacks = {
                "overview": lambda: self.main_window.switch_panel("overview"),
                "timeline": lambda: self.main_window.switch_panel("timeline"),
                "work_requests": lambda: self.main_window.switch_panel("work_requests"),
                "performance": lambda: self.main_window.switch_panel("performance"),
                "thermal": lambda: self.main_window.switch_panel("thermal"),
                "hass": lambda: self.main_window.switch_panel("hass"),
            }
            
            for panel_id, callback in panel_callbacks.items():
                self.navigation_manager.register_navigation_callback(panel_id, callback)
                
        except Exception as e:
            self.logger.error(f"Error registering navigation callbacks: {e}")
    
    def _modernize_chamber_cards(self):
        """Convert existing chamber cards to modern versions"""
        try:
            if not hasattr(self.main_window, 'chamber_cards'):
                return
            
            # Get the chamber display area
            if hasattr(self.main_window, 'chamber_display_frame'):
                container = self.main_window.chamber_display_frame
            else:
                # Find the container where chambers are displayed
                container = self._find_chamber_container()
                
            if not container:
                self.logger.warning("Could not find chamber container for modernization")
                return
            
            # Create modern chamber cards
            chambers = self.app.get_chambers()
            for chamber in chambers:
                modern_card = ModernChamberCard(container, chamber, self.app)
                self.modern_chamber_cards[chamber.id] = modern_card
                
                # Position the modern card (you may need to adjust this based on layout)
                modern_card.pack(fill="x", padx=5, pady=3)
            
            self.logger.info(f"Created {len(self.modern_chamber_cards)} modern chamber cards")
            
        except Exception as e:
            self.logger.error(f"Error modernizing chamber cards: {e}")
    
    def _find_chamber_container(self):
        """Find the container where chamber cards are displayed"""
        try:
            # Look for common chamber container names
            potential_containers = [
                'chamber_display_frame', 
                'chambers_frame',
                'main_panel_frame',
                'content_frame'
            ]
            
            for attr_name in potential_containers:
                if hasattr(self.main_window, attr_name):
                    return getattr(self.main_window, attr_name)
            
            # If not found, create a new container
            if hasattr(self.main_window, 'main_container'):
                chamber_frame = ModernFrame(self.main_window.main_container)
                chamber_frame.pack(fill="both", expand=True, padx=10, pady=10)
                return chamber_frame
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding chamber container: {e}")
            return None
    
    def _setup_modern_interactions(self):
        """Setup modern interactions and hotkeys"""
        try:
            if not hasattr(self.main_window, 'root'):
                return
            
            # Modern keyboard shortcuts
            self.main_window.root.bind("<Control-f>", self._show_search)
            self.main_window.root.bind("<Control-n>", self._create_work_request)
            self.main_window.root.bind("<F5>", self._refresh_all)
            self.main_window.root.bind("<Control-t>", self._toggle_theme)
            
            # Focus handling
            self.main_window.root.bind("<Button-1>", self._handle_click)
            
        except Exception as e:
            self.logger.error(f"Error setting up modern interactions: {e}")
    
    def _show_search(self, event=None):
        """Show global search"""
        try:
            if self.modern_navigation_bar and hasattr(self.modern_navigation_bar, 'search_entry'):
                self.modern_navigation_bar.search_entry.focus()
        except Exception as e:
            self.logger.error(f"Error showing search: {e}")
    
    def _create_work_request(self, event=None):
        """Show work request creation dialog"""
        try:
            dialog = ModernWorkRequestDialog(self.main_window.root, self.app)
            dialog.show()
        except Exception as e:
            self.logger.error(f"Error creating work request: {e}")
    
    def _refresh_all(self, event=None):
        """Refresh all data"""
        try:
            # Use existing refresh mechanism
            if hasattr(self.main_window, 'refresh_all_data'):
                self.main_window.refresh_all_data()
            elif hasattr(self.main_window, 'refresh_ui'):
                self.main_window.refresh_ui()
                
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
    
    def _toggle_theme(self, event=None):
        """Toggle between dark and light themes"""
        try:
            current_theme = self.theme_manager.current_theme
            new_theme = "modern_light" if current_theme == "modern_dark" else "modern_dark"
            self.theme_manager.apply_theme(new_theme)
            
            # Refresh UI to apply new theme
            self._refresh_modern_styling()
            
        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")
    
    def _handle_click(self, event=None):
        """Handle global click events"""
        try:
            # Close search suggestions if clicking outside
            # Modern navigation bar will handle its own click events
            pass
                
        except Exception as e:
            self.logger.error(f"Error handling click: {e}")
    
    def _refresh_modern_styling(self):
        """Refresh modern styling on all components"""
        try:
            # Re-apply theme to main components
            self._apply_modern_theme_to_window()
            
            # Update modern chamber cards
            for card in self.modern_chamber_cards.values():
                # Cards will automatically pick up new theme from theme manager
                pass
            
            # Update navigation bar  
            if self.modern_navigation_bar:
                # Navigation bar will automatically pick up new theme from theme manager
                pass
                
        except Exception as e:
            self.logger.error(f"Error refreshing modern styling: {e}")
    
    def update_chamber_card(self, chamber_id: str):
        """Update a specific modern chamber card"""
        try:
            if chamber_id in self.modern_chamber_cards:
                card = self.modern_chamber_cards[chamber_id]
                # Chamber card will automatically update with chamber data changes
                pass
                    
        except Exception as e:
            self.logger.error(f"Error updating chamber card {chamber_id}: {e}")
    
    def update_all_chamber_cards(self):
        """Update all modern chamber cards"""
        try:
            for chamber_id in self.modern_chamber_cards:
                self.update_chamber_card(chamber_id)
                
        except Exception as e:
            self.logger.error(f"Error updating all chamber cards: {e}")
    
    def add_navigation_entry(self, title: str, panel_id: str):
        """Add a navigation entry"""
        try:
            if self.navigation_manager:
                panel_data = {"title": title, "panel_id": panel_id}
                self.navigation_manager.navigate_to(panel_id, panel_data)
                
        except Exception as e:
            self.logger.error(f"Error adding navigation entry: {e}")
    
    def show_modern_features_tutorial(self):
        """Show a tutorial for modern features"""
        try:
            features = [
                "🔍 Ctrl+F: Global search across chambers and work requests",
                "📋 Ctrl+N: Create new work request",
                "⚡ F5: Refresh all data",
                "🎨 Ctrl+T: Toggle between dark and light themes",
                "📍 Click chamber cards for detailed information",
                "🧭 Use navigation breadcrumbs to track your location",
                "🔔 Check notifications panel for important updates"
            ]
            
            from tkinter import messagebox
            messagebox.showinfo(
                "Modern UI Features",
                "Welcome to the modernized chamber management interface!\n\n" +
                "\n".join(features) +
                "\n\nEnjoy the improved user experience!"
            )
            
        except Exception as e:
            self.logger.error(f"Error showing tutorial: {e}")


def integrate_modern_ui(main_window):
    """
    Main function to integrate modern UI with existing main window
    """
    try:
        # Create and initialize modern integration
        modern_integration = ModernMainWindowIntegration(main_window)
        modern_integration.initialize_modern_ui()
        
        # Store reference for later use
        main_window.modern_integration = modern_integration
        
        # Show tutorial on first run
        modern_integration.show_modern_features_tutorial()
        
        return modern_integration
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to integrate modern UI: {e}")
        return None
