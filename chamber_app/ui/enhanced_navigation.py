"""
Enhanced Navigation System
Modern navigation with breadcrumbs, search, and improved user experience
"""

import customtkinter as ctk
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from .modern_theme import ModernFrame, ModernButton, ModernLabel, ModernEntry, get_theme_manager

class NavigationManager:
    """Advanced navigation system with history and breadcrumbs"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.current_index = -1
        self.navigation_callbacks: Dict[str, Callable] = {}
        self.breadcrumb_widgets: List[Any] = []
        
    def register_navigation_callback(self, panel_id: str, callback: Callable):
        """Register a callback for panel navigation"""
        self.navigation_callbacks[panel_id] = callback
    
    def navigate_to(self, panel_id: str, panel_data: Optional[Dict[str, Any]] = None):
        """Navigate to a panel and update history"""
        navigation_item = {
            "panel_id": panel_id,
            "timestamp": datetime.now(),
            "data": panel_data or {}
        }
        
        # Remove any items after current index (when going back then forward)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        self.history.append(navigation_item)
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > 50:
            self.history = self.history[-50:]
            self.current_index = len(self.history) - 1
        
        # Execute navigation
        if panel_id in self.navigation_callbacks:
            self.navigation_callbacks[panel_id](panel_data)
    
    def go_back(self):
        """Navigate back in history"""
        if self.can_go_back():
            self.current_index -= 1
            current_item = self.history[self.current_index]
            panel_id = current_item["panel_id"]
            
            if panel_id in self.navigation_callbacks:
                self.navigation_callbacks[panel_id](current_item["data"])
    
    def go_forward(self):
        """Navigate forward in history"""
        if self.can_go_forward():
            self.current_index += 1
            current_item = self.history[self.current_index]
            panel_id = current_item["panel_id"]
            
            if panel_id in self.navigation_callbacks:
                self.navigation_callbacks[panel_id](current_item["data"])
    
    def can_go_back(self) -> bool:
        """Check if can navigate back"""
        return self.current_index > 0
    
    def can_go_forward(self) -> bool:
        """Check if can navigate forward"""
        return self.current_index < len(self.history) - 1
    
    def get_current_panel(self) -> Optional[str]:
        """Get current panel ID"""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]["panel_id"]
        return None

class SearchManager:
    """Advanced search system for global application search"""
    
    def __init__(self, app):
        self.app = app
        self.search_providers: Dict[str, Callable] = {}
        self.recent_searches: List[str] = []
        
    def register_search_provider(self, provider_name: str, search_func: Callable):
        """Register a search provider"""
        self.search_providers[provider_name] = search_func
    
    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Perform global search across all providers"""
        results = {}
        
        if not query.strip():
            return results
        
        # Add to recent searches
        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            self.recent_searches = self.recent_searches[:10]  # Keep last 10
        
        # Search across all providers
        for provider_name, search_func in self.search_providers.items():
            try:
                provider_results = search_func(query)
                if provider_results:
                    results[provider_name] = provider_results
            except Exception as e:
                print(f"Search error in {provider_name}: {e}")
        
        return results

class ModernNavigationBar(ModernFrame):
    """Modern navigation bar with breadcrumbs, search, and controls"""
    
    def __init__(self, parent, app):
        super().__init__(parent, style="card")
        
        self.app = app
        self.theme_manager = get_theme_manager()
        self.navigation_manager = NavigationManager()
        self.search_manager = SearchManager(app)
        
        self._setup_navigation_providers()
        self._setup_search_providers()
        self._create_navigation_ui()
    
    def _setup_navigation_providers(self):
        """Setup navigation providers for different panels"""
        panels = {
            "overview": lambda data: self.app.main_window.notebook.set("Overview"),
            "timeline": lambda data: self.app.main_window.notebook.set("Weekly Timeline"),
            "chambers": lambda data: self._navigate_to_chamber(data),
            "work_requests": lambda data: self.app.main_window.notebook.set("Work Requests"),
            "performance": lambda data: self.app.main_window.notebook.set("Performance"),
            "settings": lambda data: self.app.main_window.notebook.set("Settings"),
        }
        
        for panel_id, callback in panels.items():
            self.navigation_manager.register_navigation_callback(panel_id, callback)
    
    def _setup_search_providers(self):
        """Setup search providers for different data types"""
        self.search_manager.register_search_provider("chambers", self._search_chambers)
        self.search_manager.register_search_provider("work_requests", self._search_work_requests)
        self.search_manager.register_search_provider("settings", self._search_settings)
    
    def _create_navigation_ui(self):
        """Create the navigation UI components"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Left section - Navigation controls
        nav_controls = ModernFrame(self)
        nav_controls.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Back/Forward buttons
        self.back_btn = ModernButton(
            nav_controls,
            text="◀",
            width=40,
            height=30,
            command=self.navigation_manager.go_back,
            style="primary_button"
        )
        self.back_btn.pack(side="left", padx=(0, 2))
        
        self.forward_btn = ModernButton(
            nav_controls,
            text="▶", 
            width=40,
            height=30,
            command=self.navigation_manager.go_forward,
            style="primary_button"
        )
        self.forward_btn.pack(side="left", padx=2)
        
        # Breadcrumb frame
        self.breadcrumb_frame = ModernFrame(nav_controls)
        self.breadcrumb_frame.pack(side="left", padx=(10, 0))
        
        # Center section - Search
        search_frame = ModernFrame(self)
        search_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ModernEntry(
            search_frame,
            placeholder_text="Search chambers, work requests, settings..."
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self._on_search_change)
        self.search_entry.bind("<Return>", self._on_search_enter)
        
        self.search_btn = ModernButton(
            search_frame,
            text="🔍",
            width=40,
            height=30,
            command=self._perform_search,
            style="accent_button"
        )
        self.search_btn.grid(row=0, column=1)
        
        # Right section - Quick actions
        actions_frame = ModernFrame(self)
        actions_frame.grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        # Quick add button
        self.quick_add_btn = ModernButton(
            actions_frame,
            text="+ Quick Add",
            height=30,
            command=self._show_quick_add_menu,
            style="success_button"
        )
        self.quick_add_btn.pack(side="right", padx=(5, 0))
        
        # Notifications indicator
        self.notifications_btn = ModernButton(
            actions_frame,
            text="🔔",
            width=40,
            height=30,
            command=self._show_notifications,
            style="primary_button"
        )
        self.notifications_btn.pack(side="right", padx=2)
        
        # Update navigation state
        self._update_navigation_state()
    
    def _navigate_to_chamber(self, data):
        """Navigate to specific chamber"""
        if data and "chamber_id" in data:
            chamber_id = data["chamber_id"]
            # Implementation for chamber navigation
            pass
    
    def _search_chambers(self, query: str) -> List[Dict[str, Any]]:
        """Search chambers by name, type, state, etc."""
        results = []
        chambers = self.app.get_chambers()
        
        query_lower = query.lower()
        
        for chamber in chambers:
            # Search in chamber name
            if query_lower in chamber.name.lower():
                results.append({
                    "title": chamber.name,
                    "subtitle": f"{chamber.type.value} Chamber",
                    "description": f"State: {chamber.state_manager.current_state.value}",
                    "action": lambda c=chamber: self._select_chamber(c.id),
                    "icon": "🏭"
                })
            
            # Search in chamber type
            elif query_lower in chamber.type.value.lower():
                results.append({
                    "title": chamber.name,
                    "subtitle": f"{chamber.type.value} Chamber",
                    "description": f"State: {chamber.state_manager.current_state.value}",
                    "action": lambda c=chamber: self._select_chamber(c.id),
                    "icon": "🏭"
                })
        
        return results[:10]  # Limit results
    
    def _search_work_requests(self, query: str) -> List[Dict[str, Any]]:
        """Search work requests"""
        results = []
        # Implementation for work request search
        return results
    
    def _search_settings(self, query: str) -> List[Dict[str, Any]]:
        """Search settings and configuration options"""
        results = []
        # Implementation for settings search
        return results
    
    def _on_search_change(self, event):
        """Handle search text change"""
        # Implement live search suggestions
        pass
    
    def _on_search_enter(self, event):
        """Handle search enter key"""
        self._perform_search()
    
    def _perform_search(self):
        """Perform global search"""
        query = self.search_entry.get()
        if not query.strip():
            return
            
        results = self.search_manager.search(query)
        self._show_search_results(results)
    
    def _show_search_results(self, results: Dict[str, List[Dict[str, Any]]]):
        """Show search results in a popup"""
        if not results:
            return
            
        # Create search results dialog
        dialog = SearchResultsDialog(self.winfo_toplevel(), results)
        dialog.show()
    
    def _show_quick_add_menu(self):
        """Show quick add menu"""
        # Create quick add menu
        menu = QuickAddMenu(self, self.app)
        menu.show()
    
    def _show_notifications(self):
        """Show notifications panel"""
        self.navigation_manager.navigate_to("notifications")
    
    def _select_chamber(self, chamber_id: str):
        """Select and navigate to a specific chamber"""
        self.navigation_manager.navigate_to("chambers", {"chamber_id": chamber_id})
    
    def _update_navigation_state(self):
        """Update navigation button states"""
        self.back_btn.configure(
            state="normal" if self.navigation_manager.can_go_back() else "disabled"
        )
        self.forward_btn.configure(
            state="normal" if self.navigation_manager.can_go_forward() else "disabled"
        )
    
    def update_breadcrumbs(self, breadcrumbs: List[str]):
        """Update breadcrumb display"""
        # Clear existing breadcrumbs
        for widget in self.breadcrumb_frame.winfo_children():
            widget.destroy()
        
        for i, crumb in enumerate(breadcrumbs):
            if i > 0:
                separator = ModernLabel(self.breadcrumb_frame, text=">", text_style="muted")
                separator.pack(side="left", padx=5)
            
            crumb_btn = ModernButton(
                self.breadcrumb_frame,
                text=crumb,
                height=25,
                style="primary_button"
            )
            crumb_btn.pack(side="left", padx=2)

class SearchResultsDialog:
    """Dialog for displaying search results"""
    
    def __init__(self, parent, results: Dict[str, List[Dict[str, Any]]]):
        self.parent = parent
        self.results = results
        self.dialog: Optional[ctk.CTkToplevel] = None
    
    def show(self):
        """Show the search results dialog"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Search Results")
        self.dialog.geometry("600x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.parent.winfo_width() // 2) - (600 // 2) + self.parent.winfo_rootx()
        y = (self.parent.winfo_height() // 2) - (400 // 2) + self.parent.winfo_rooty()
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        self._create_results_ui()
    
    def _create_results_ui(self):
        """Create the results UI"""
        main_frame = ModernFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ModernLabel(
            main_frame,
            text="Search Results",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Results by category
        for category, items in self.results.items():
            if not items:
                continue
                
            # Category header
            category_label = ModernLabel(
                main_frame,
                text=f"{category.title()} ({len(items)})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_style="secondary"
            )
            category_label.pack(anchor="w", pady=(10, 5))
            
            # Results list
            for item in items[:5]:  # Show max 5 per category
                result_frame = ModernFrame(main_frame)
                result_frame.pack(fill="x", pady=2)
                
                result_btn = ModernButton(
                    result_frame,
                    text=f"{item.get('icon', '')} {item['title']}",
                    anchor="w",
                    command=item.get('action'),
                    style="primary_button"
                )
                result_btn.pack(fill="x", padx=5, pady=2)
        
        # Close button
        close_btn = ModernButton(
            main_frame,
            text="Close",
            command=lambda: self.dialog.destroy() if self.dialog else None,
            width=100,
            style="accent_button"
        )
        close_btn.pack(pady=(15, 0))

class QuickAddMenu:
    """Quick add menu for common actions"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.menu: Optional[ctk.CTkToplevel] = None
    
    def show(self):
        """Show the quick add menu"""
        self.menu = ctk.CTkToplevel(self.parent)
        self.menu.title("Quick Add")
        self.menu.geometry("300x250")
        self.menu.transient(self.parent.winfo_toplevel())
        self.menu.grab_set()
        
        # Position near the button
        x = self.parent.winfo_rootx() + self.parent.winfo_width() - 300
        y = self.parent.winfo_rooty() + self.parent.winfo_height()
        self.menu.geometry(f"300x250+{x}+{y}")
        
        self._create_menu_ui()
    
    def _create_menu_ui(self):
        """Create the menu UI"""
        main_frame = ModernFrame(self.menu)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Quick add options
        options = [
            ("Add TVAC Chamber", lambda: self._add_chamber("TVAC")),
            ("Add HASS Chamber", lambda: self._add_chamber("HASS")),
            ("Add THERMAL Chamber", lambda: self._add_chamber("THERMAL")),
            ("Create Work Request", self._create_work_request),
            ("Schedule Maintenance", self._schedule_maintenance),
        ]
        
        for text, command in options:
            btn = ModernButton(
                main_frame,
                text=text,
                command=lambda cmd=command: self._execute_and_close(cmd),
                height=35,
                style="primary_button"
            )
            btn.pack(fill="x", pady=3)
    
    def _execute_and_close(self, command):
        """Execute command and close menu"""
        if self.menu:
            self.menu.destroy()
        command()
    
    def _add_chamber(self, chamber_type: str):
        """Add a new chamber"""
        self.app.main_window._show_add_chamber_dialog(chamber_type)
    
    def _create_work_request(self):
        """Create a new work request"""
        self.app.main_window.navigation_manager.navigate_to("work_requests", {"action": "new"})
    
    def _schedule_maintenance(self):
        """Schedule maintenance"""
        # Implementation for maintenance scheduling
        pass
