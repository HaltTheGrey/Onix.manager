"""
Main application window using CustomTkinter.
Creates the primary UI with dockable menu and main display panel.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..core.chamber_state import ChamberType, ChamberState, ChamberStatus
from ..utils import get_logger
from .chamber_card import ChamberCard
from .data_overview_panel import DataOverviewPanel
from .work_requests_panel import WorkRequestsPanel


class MainWindow:
    """
    Main application window with dockable menu and display panels.
    """
    def __init__(self, app, config: Dict[str, Any]):
        self.app = app
        self.config = config
        self.logger = get_logger(__name__)
        
        # UI state
        self.menu_expanded = True
        self.current_panel = "overview"
        self.chamber_cards: Dict[str, ChamberCard] = {}
        self.refresh_running = False
        
        # Setup UI theme
        ctk.set_appearance_mode(config.get('UI_THEME', 'dark'))
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title(config.get('APP_NAME', 'Chamber Management System'))
        self.root.geometry(f"{config.get('WINDOW_WIDTH', 1400)}x{config.get('WINDOW_HEIGHT', 900)}")
        
        # Setup close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Setup UI components
        self._setup_ui()
        
        # Start UI refresh timer
        self._start_refresh_timer()
        
        self.logger.info("Main window initialized")
    
    def _on_closing(self):
        """Handle window closing event."""
        self.refresh_running = False
        self.root.destroy()
    
    def shutdown(self):
        """Shutdown the UI cleanly."""
        self.refresh_running = False

    def _setup_ui(self):
        """Setup the main UI layout."""
        # Configure grid weights
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create left menu panel
        self._create_menu_panel()
        
        # Create main display area
        self._create_main_panel()
        
        # Create status bar
        self._create_status_bar()
        
        # Load initial data
        self._refresh_data()
    
    def _create_menu_panel(self):
        """Create the left-side dockable menu panel."""
        self.menu_frame = ctk.CTkFrame(self.root, width=250)
        self.menu_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 2), pady=5)
        self.menu_frame.grid_propagate(False)
        
        # Menu header with toggle button
        header_frame = ctk.CTkFrame(self.menu_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        self.menu_title = ctk.CTkLabel(
            header_frame, 
            text="Chamber Control", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.menu_title.pack(side="left", padx=10, pady=10)
        
        self.toggle_button = ctk.CTkButton(
            header_frame,
            text="◀",
            width=30,
            command=self._toggle_menu
        )
        self.toggle_button.pack(side="right", padx=10, pady=10)
        
        # Menu content frame
        self.menu_content = ctk.CTkFrame(self.menu_frame)
        self.menu_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Navigation buttons
        nav_frame = ctk.CTkFrame(self.menu_content)
        nav_frame.pack(fill="x", padx=10, pady=10)
        
        nav_buttons = [
            ("Overview", "overview"),
            ("TVAC Chambers", "tvac"),
            ("HASS Chambers", "hass"),
            ("THERMAL Chambers", "thermal"),
            ("Work Requests", "work_requests"),
            ("Settings", "settings")
        ]
        
        self.nav_buttons = {}
        for text, panel_id in nav_buttons:
            btn = ctk.CTkButton(
                nav_frame,
                text=text,
                command=lambda p=panel_id: self._switch_panel(p),
                height=35
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[panel_id] = btn
        
        # Chamber sections
        self._create_chamber_sections()
    
    def _create_chamber_sections(self):
        """Create chamber sections in the menu."""
        # TVAC Section
        self.tvac_frame = ctk.CTkFrame(self.menu_content)
        self.tvac_frame.pack(fill="x", padx=10, pady=5)
        
        tvac_header = ctk.CTkLabel(
            self.tvac_frame, 
            text="TVAC Chambers", 
            font=ctk.CTkFont(weight="bold")
        )
        tvac_header.pack(pady=5)
        
        self.tvac_list = ctk.CTkScrollableFrame(self.tvac_frame, height=100)
        self.tvac_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # HASS Section
        self.hass_frame = ctk.CTkFrame(self.menu_content)
        self.hass_frame.pack(fill="x", padx=10, pady=5)
        
        hass_header = ctk.CTkLabel(
            self.hass_frame, 
            text="HASS Chambers", 
            font=ctk.CTkFont(weight="bold")
        )
        hass_header.pack(pady=5)
        
        self.hass_list = ctk.CTkScrollableFrame(self.hass_frame, height=100)
        self.hass_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # THERMAL Section
        self.thermal_frame = ctk.CTkFrame(self.menu_content)
        self.thermal_frame.pack(fill="x", padx=10, pady=5)
        
        thermal_header = ctk.CTkLabel(
            self.thermal_frame, 
            text="THERMAL Chambers", 
            font=ctk.CTkFont(weight="bold")
        )
        thermal_header.pack(pady=5)
        
        self.thermal_list = ctk.CTkScrollableFrame(self.thermal_frame, height=100)
        self.thermal_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add Chamber button
        add_chamber_btn = ctk.CTkButton(
            self.menu_content,
            text="+ Add Chamber",
            command=self._show_add_chamber_dialog,
            fg_color="green",
            hover_color="dark green"
        )
        add_chamber_btn.pack(fill="x", padx=10, pady=10)
    
    def _create_main_panel(self):
        """Create the main display panel."""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 5), pady=5)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Create notebook for different panels
        self.notebook = ctk.CTkTabview(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Overview panel
        self.overview_tab = self.notebook.add("Overview")
        self.overview_panel = DataOverviewPanel(self.overview_tab, self.app)
        
        # Chamber panels will be created dynamically
        self.chamber_panels = {}
        
        # Work requests panel
        self.work_requests_tab = self.notebook.add("Work Requests")
        self.work_requests_panel = WorkRequestsPanel(self.work_requests_tab, self.app)
    
    def _create_status_bar(self):
        """Create the bottom status bar."""
        self.status_frame = ctk.CTkFrame(self.root, height=30)
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        
        # Status labels
        self.status_left = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            anchor="w"
        )
        self.status_left.pack(side="left", padx=10, pady=5)
        
        self.status_right = ctk.CTkLabel(
            self.status_frame,
            text="Connected: 0 users",
            anchor="e"
        )
        self.status_right.pack(side="right", padx=10, pady=5)
    
    def _toggle_menu(self):
        """Toggle the menu panel expanded/collapsed state."""
        if self.menu_expanded:
            # Collapse menu
            self.menu_frame.configure(width=50)
            self.toggle_button.configure(text="▶")
            self.menu_title.pack_forget()
            self.menu_content.pack_forget()
            self.menu_expanded = False
        else:
            # Expand menu
            self.menu_frame.configure(width=250)
            self.toggle_button.configure(text="◀")
            self.menu_title.pack(side="left", padx=10, pady=10)
            self.menu_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.menu_expanded = True
    
    def _switch_panel(self, panel_id: str):
        """Switch to a different panel."""
        self.current_panel = panel_id
        
        # Update button states
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == panel_id:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color=("gray70", "gray30"))
        
        # Switch to appropriate tab
        if panel_id == "overview":
            self.notebook.set("Overview")
        elif panel_id == "work_requests":
            self.notebook.set("Work Requests")
        elif panel_id in ["tvac", "hass", "thermal"]:
            chamber_type = panel_id.upper()
            if chamber_type not in self.chamber_panels:
                self._create_chamber_panel(chamber_type)
            self.notebook.set(chamber_type)
        
        self.logger.info(f"Switched to panel: {panel_id}")
    
    def _create_chamber_panel(self, chamber_type: str):
        """Create a panel for a specific chamber type."""
        tab = self.notebook.add(chamber_type)
        
        # Create scrollable frame for chamber cards
        chamber_frame = ctk.CTkScrollableFrame(tab)
        chamber_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.chamber_panels[chamber_type] = chamber_frame
        
        # Add chambers of this type
        chamber_type_enum = ChamberType(chamber_type)
        chambers = self.app.get_chambers_by_type(chamber_type_enum)
        
        for chamber in chambers:
            self._add_chamber_card(chamber)
    
    def _add_chamber_card(self, chamber):
        """Add a chamber card to the appropriate panel."""
        chamber_type = chamber.type.value
        
        if chamber_type not in self.chamber_panels:
            self._create_chamber_panel(chamber_type)
        
        panel = self.chamber_panels[chamber_type]
        
        # Create chamber card
        card = ChamberCard(panel, chamber, self.app)
        card.pack(fill="x", padx=5, pady=5)
        
        self.chamber_cards[chamber.id] = card
        
        # Also add to menu list
        self._add_chamber_to_menu(chamber)
    
    def _add_chamber_to_menu(self, chamber):
        """Add chamber to the menu list."""
        chamber_type = chamber.type.value.lower()
        
        if chamber_type == "tvac":
            parent = self.tvac_list
        elif chamber_type == "hass":
            parent = self.hass_list
        elif chamber_type == "thermal":
            parent = self.thermal_list
        else:
            return
        
        # Create chamber button in menu
        chamber_btn = ctk.CTkButton(
            parent,
            text=chamber.name,
            height=25,
            command=lambda: self._select_chamber(chamber.id)
        )
        chamber_btn.pack(fill="x", pady=1)
    
    def _select_chamber(self, chamber_id: str):
        """Select and highlight a specific chamber."""
        # Switch to the appropriate chamber panel
        chamber = self.app.get_chamber(chamber_id)
        if chamber:
            self._switch_panel(chamber.type.value.lower())
            
            # Highlight the chamber card
            if chamber_id in self.chamber_cards:
                card = self.chamber_cards[chamber_id]
                card.highlight()
    
    def _show_add_chamber_dialog(self):
        """Show dialog to add a new chamber."""
        dialog = AddChamberDialog(self.root, self.app)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            chamber = dialog.result
            self._add_chamber_card(chamber)
            self._refresh_data()
    
    def _refresh_data(self):
        """Refresh all data displays."""
        try:
            # Update overview panel
            if hasattr(self, 'overview_panel'):
                self.overview_panel.update_data()
            
            # Update work requests panel
            if hasattr(self, 'work_requests_panel'):
                self.work_requests_panel.update_data()
            
            # Update chamber cards
            for card in self.chamber_cards.values():
                card.update_data()
            
            # Update status bar
            self._update_status_bar()
            
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
    
    def _update_status_bar(self):
        """Update the status bar information."""
        try:
            # Get application statistics
            stats = self.app.get_chamber_statistics()
            
            # Update left status
            total_chambers = stats.get('total_chambers', 0)
            connected = stats.get('connected_chambers', 0)
            self.status_left.configure(text=f"Chambers: {total_chambers} | Connected: {connected}")
            
            # Update right status
            if hasattr(self.app, 'multi_user_manager') and self.app.multi_user_manager:
                user_count = self.app.multi_user_manager.get_user_count()
                self.status_right.configure(text=f"Connected users: {user_count}")
            else:
                self.status_right.configure(text="Single user mode")
                
        except Exception as e:
            self.logger.error(f"Error updating status bar: {e}")
    
    def _start_refresh_timer(self):
        """Start the automatic refresh timer."""
        self.refresh_running = True
        
        def refresh_loop():
            while self.refresh_running:
                try:
                    # Check if root still exists and is valid
                    if hasattr(self, 'root') and self.root.winfo_exists():
                        # Schedule refresh on main thread
                        self.root.after(0, self._refresh_data)
                    else:
                        break
                    
                    # Wait for refresh interval
                    refresh_interval = self.config.get('AUTO_REFRESH_INTERVAL', 5)
                    threading.Event().wait(refresh_interval)
                    
                except Exception as e:
                    if self.refresh_running:  # Only log if not shutting down
                        self.logger.error(f"Refresh timer error: {e}")
                    break
        
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    def run(self):
        """Run the main application loop."""
        try:
            self.logger.info("Starting main UI loop")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Main UI error: {e}", exc_info=True)
            raise
        finally:
            self.logger.info("Main UI loop ended")


class AddChamberDialog:
    """Dialog for adding a new chamber."""
    
    def __init__(self, parent, app):
        self.app = app
        self.result = None
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Add New Chamber")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_width() // 2) - (400 // 2) + parent.winfo_x()
        y = (parent.winfo_height() // 2) - (300 // 2) + parent.winfo_y()
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        self._setup_dialog()
    
    def _setup_dialog(self):
        """Setup the dialog UI."""
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Add New Chamber",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Chamber name
        name_label = ctk.CTkLabel(main_frame, text="Chamber Name:")
        name_label.pack(anchor="w", pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter chamber name")
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Chamber type
        type_label = ctk.CTkLabel(main_frame, text="Chamber Type:")
        type_label.pack(anchor="w", pady=(0, 5))
        
        self.type_combo = ctk.CTkComboBox(
            main_frame,
            values=["TVAC", "HASS", "THERMAL"],
            state="readonly"
        )
        self.type_combo.pack(fill="x", pady=(0, 20))
        self.type_combo.set("TVAC")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="gray",
            hover_color="dark gray"
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        ok_btn = ctk.CTkButton(
            button_frame,
            text="Add Chamber",
            command=self._add_chamber,
            fg_color="green",
            hover_color="dark green"
        )
        ok_btn.pack(side="right")
        
        # Focus on name entry
        self.name_entry.focus()
    
    def _add_chamber(self):
        """Add the new chamber."""
        name = self.name_entry.get().strip()
        chamber_type_str = self.type_combo.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter a chamber name.")
            return
        
        try:
            chamber_type = ChamberType(chamber_type_str)
            chamber = self.app.add_chamber(name, chamber_type)
            self.result = chamber
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add chamber: {e}")
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
