"""
Chamber card component for displaying individual chamber information.
Shows current state, status, telemetry, and provides controls.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Dict, Any

from ..core.chamber_state import ChamberState, ChamberStatus
from ..utils import get_logger


class ChamberCard(ctk.CTkFrame):
    """
    Individual chamber display card with state, status, and controls.
    """
    
    def __init__(self, parent, chamber, app):
        super().__init__(parent)
        
        self.chamber = chamber
        self.app = app
        self.logger = get_logger(__name__)
        
        # UI state
        self.is_highlighted = False
        self.expanded = False
        
        # Setup card UI
        self._setup_ui()
        
        # Update initial data
        self.update_data()
    
    def _setup_ui(self):
        """Setup the chamber card UI."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Header section
        self._create_header()
        
        # Status section
        self._create_status_section()
        
        # Control section
        self._create_control_section()
        
        # Expandable details section
        self._create_details_section()
    
    def _create_header(self):
        """Create the chamber header with name and type."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Chamber icon/indicator
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # Chamber name and type
        info_frame = ctk.CTkFrame(header_frame)
        info_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=self.chamber.name,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.name_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.type_label = ctk.CTkLabel(
            info_frame,
            text=f"{self.chamber.type.value} Chamber",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        self.type_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Expand button
        self.expand_button = ctk.CTkButton(
            header_frame,
            text="▼",
            width=30,
            height=30,
            command=self._toggle_expanded
        )
        self.expand_button.grid(row=0, column=2, padx=(5, 10), pady=10)
    
    def _create_status_section(self):
        """Create the status display section."""
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Current state
        state_frame = ctk.CTkFrame(status_frame)
        state_frame.grid(row=0, column=0, sticky="ew", padx=(5, 2), pady=5)
        
        state_title = ctk.CTkLabel(
            state_frame,
            text="Current State",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        state_title.pack(pady=(5, 0))
        
        self.state_label = ctk.CTkLabel(
            state_frame,
            text=self.chamber.state_manager.current_state.value,
            font=ctk.CTkFont(size=11),
            wraplength=150
        )
        self.state_label.pack(pady=(0, 5))
        
        # Current status
        status_status_frame = ctk.CTkFrame(status_frame)
        status_status_frame.grid(row=0, column=1, sticky="ew", padx=(2, 5), pady=5)
        
        status_title = ctk.CTkLabel(
            status_status_frame,
            text="Status",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        status_title.pack(pady=(5, 0))
        
        self.status_label = ctk.CTkLabel(
            status_status_frame,
            text="None" if not self.chamber.state_manager.current_status else self.chamber.state_manager.current_status.value,
            font=ctk.CTkFont(size=11),
            wraplength=150
        )
        self.status_label.pack(pady=(0, 5))
        
        # Timing information
        timing_frame = ctk.CTkFrame(status_frame)
        timing_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        
        self.timing_label = ctk.CTkLabel(
            timing_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.timing_label.pack(pady=5)
    
    def _create_control_section(self):
        """Create the control buttons section."""
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
        
        # State control
        state_btn = ctk.CTkButton(
            control_frame,
            text="Change State",
            command=self._show_state_dialog,
            width=100,
            height=30
        )
        state_btn.pack(side="left", padx=5, pady=5)
        
        # Status control
        status_btn = ctk.CTkButton(
            control_frame,
            text="Set Status",
            command=self._show_status_dialog,
            width=100,
            height=30
        )
        status_btn.pack(side="left", padx=5, pady=5)
        
        # Work request button
        work_btn = ctk.CTkButton(
            control_frame,
            text="Work Request",
            command=self._show_work_request_dialog,
            width=100,
            height=30,
            fg_color="orange",
            hover_color="dark orange"
        )
        work_btn.pack(side="right", padx=5, pady=5)
    
    def _create_details_section(self):
        """Create the expandable details section."""
        self.details_frame = ctk.CTkFrame(self)
        # Initially hidden
        
        # Telemetry section
        telemetry_frame = ctk.CTkFrame(self.details_frame)
        telemetry_frame.pack(fill="x", padx=5, pady=5)
        
        telemetry_title = ctk.CTkLabel(
            telemetry_frame,
            text="Live Telemetry",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        telemetry_title.pack(pady=(5, 0))
        
        # Telemetry grid
        telemetry_grid = ctk.CTkFrame(telemetry_frame)
        telemetry_grid.pack(fill="x", padx=10, pady=5)
        
        # Temperature
        self.temp_label = self._create_telemetry_item(telemetry_grid, "Temperature:", "-- °C", 0, 0)
        
        # Vacuum
        self.vacuum_label = self._create_telemetry_item(telemetry_grid, "Vacuum:", "-- Torr", 0, 1)
        
        # Humidity
        self.humidity_label = self._create_telemetry_item(telemetry_grid, "Humidity:", "-- %", 1, 0)
        
        # Pressure
        self.pressure_label = self._create_telemetry_item(telemetry_grid, "Pressure:", "-- hPa", 1, 1)
        
        # Work requests section
        work_requests_frame = ctk.CTkFrame(self.details_frame)
        work_requests_frame.pack(fill="x", padx=5, pady=5)
        
        work_title = ctk.CTkLabel(
            work_requests_frame,
            text="Active Work Requests",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        work_title.pack(pady=(5, 0))
        
        self.work_requests_list = ctk.CTkTextbox(
            work_requests_frame,
            height=80,
            wrap="word"
        )
        self.work_requests_list.pack(fill="x", padx=10, pady=5)
        
        # Connection info
        connection_frame = ctk.CTkFrame(self.details_frame)
        connection_frame.pack(fill="x", padx=5, pady=5)
        
        self.connection_label = ctk.CTkLabel(
            connection_frame,
            text="Connection: Disconnected",
            font=ctk.CTkFont(size=12)
        )
        self.connection_label.pack(pady=5)
    
    def _create_telemetry_item(self, parent, label_text, value_text, row, col):
        """Create a telemetry display item."""
        item_frame = ctk.CTkFrame(parent)
        item_frame.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
        parent.grid_columnconfigure(col, weight=1)
        
        label = ctk.CTkLabel(
            item_frame,
            text=label_text,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        label.pack(pady=(5, 0))
        
        value = ctk.CTkLabel(
            item_frame,
            text=value_text,
            font=ctk.CTkFont(size=12)
        )
        value.pack(pady=(0, 5))
        
        return value
    
    def _toggle_expanded(self):
        """Toggle the expanded state of the card."""
        if self.expanded:
            # Collapse
            self.details_frame.grid_forget()
            self.expand_button.configure(text="▼")
            self.expanded = False
        else:
            # Expand
            self.details_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
            self.expand_button.configure(text="▲")
            self.expanded = True
    
    def _show_state_dialog(self):
        """Show dialog to change chamber state."""
        dialog = StateChangeDialog(self.winfo_toplevel(), self.chamber, self.app)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.update_data()
    
    def _show_status_dialog(self):
        """Show dialog to change chamber status."""
        dialog = StatusChangeDialog(self.winfo_toplevel(), self.chamber, self.app)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.update_data()
    
    def _show_work_request_dialog(self):
        """Show dialog to create work request."""
        # This would open a work request creation dialog
        messagebox.showinfo("Work Request", "Work request dialog would open here")
    
    def update_data(self):
        """Update the chamber card with current data."""
        try:
            # Update state and status
            current_state = self.chamber.state_manager.current_state
            current_status = self.chamber.state_manager.current_status
            
            self.state_label.configure(text=current_state.value)
            
            if current_status:
                self.status_label.configure(text=current_status.value)
                self.status_indicator.configure(text_color="orange")  # Has status
            else:
                self.status_label.configure(text="None")
                self.status_indicator.configure(text_color="green")  # Normal
            
            # Update timing
            state_duration = self.chamber.state_manager.get_state_duration()
            status_duration = self.chamber.state_manager.get_status_duration()
            
            timing_text = f"State: {self._format_duration(state_duration)}"
            if current_status:
                timing_text += f" | Status: {self._format_duration(status_duration)}"
            
            self.timing_label.configure(text=timing_text)
            
            # Update telemetry if expanded
            if self.expanded:
                self._update_telemetry()
                self._update_work_requests()
                self._update_connection_status()
            
        except Exception as e:
            self.logger.error(f"Error updating chamber card for {self.chamber.name}: {e}")
    
    def _update_telemetry(self):
        """Update telemetry display."""
        if self.chamber.last_telemetry:
            metrics = self.chamber.last_telemetry
            
            self.temp_label.configure(text=f"{metrics.temperature:.1f} °C")
            self.vacuum_label.configure(text=f"{metrics.vacuum_level:.2e} Torr")
            self.humidity_label.configure(text=f"{metrics.humidity:.1f} %")
            self.pressure_label.configure(text=f"{metrics.pressure:.1f} hPa")
        else:
            self.temp_label.configure(text="-- °C")
            self.vacuum_label.configure(text="-- Torr")
            self.humidity_label.configure(text="-- %")
            self.pressure_label.configure(text="-- hPa")
    
    def _update_work_requests(self):
        """Update work requests display."""
        active_requests = self.chamber.get_active_work_requests()
        
        self.work_requests_list.delete("1.0", "end")
        
        if active_requests:
            for req in active_requests:
                self.work_requests_list.insert("end", f"• {req.title} ({req.priority})\n")
        else:
            self.work_requests_list.insert("end", "No active work requests")
    
    def _update_connection_status(self):
        """Update connection status display."""
        if self.chamber.is_connected:
            conn_text = f"Connected via {self.chamber.connection_type or 'Unknown'}"
            self.connection_label.configure(text=conn_text, text_color="green")
        else:
            self.connection_label.configure(text="Disconnected", text_color="red")
    
    def _format_duration(self, seconds):
        """Format duration in seconds to human readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def highlight(self):
        """Highlight the chamber card temporarily."""
        if not self.is_highlighted:
            self.configure(border_color="yellow", border_width=2)
            self.is_highlighted = True
            
            # Remove highlight after 3 seconds
            self.after(3000, self._remove_highlight)
    
    def _remove_highlight(self):
        """Remove the highlight from the chamber card."""
        self.configure(border_color="gray", border_width=1)
        self.is_highlighted = False


class StateChangeDialog:
    """Dialog for changing chamber state."""
    
    def __init__(self, parent, chamber, app):
        self.chamber = chamber
        self.app = app
        self.result = None
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Change Chamber State")
        self.dialog.geometry("350x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_dialog()
    
    def _setup_dialog(self):
        """Setup the state change dialog."""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text=f"Change State: {self.chamber.name}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Current state
        current_label = ctk.CTkLabel(
            main_frame,
            text=f"Current State: {self.chamber.state_manager.current_state.value}",
            font=ctk.CTkFont(size=12)
        )
        current_label.pack(pady=(0, 15))
        
        # New state selection
        new_state_label = ctk.CTkLabel(main_frame, text="New State:")
        new_state_label.pack(anchor="w", pady=(0, 5))
        
        state_values = [state.value for state in ChamberState]
        self.state_combo = ctk.CTkComboBox(
            main_frame,
            values=state_values,
            state="readonly"
        )
        self.state_combo.pack(fill="x", pady=(0, 15))
        self.state_combo.set(self.chamber.state_manager.current_state.value)
        
        # Reason
        reason_label = ctk.CTkLabel(main_frame, text="Reason (optional):")
        reason_label.pack(anchor="w", pady=(0, 5))
        
        self.reason_entry = ctk.CTkTextbox(main_frame, height=80)
        self.reason_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        ok_btn = ctk.CTkButton(
            button_frame,
            text="Change State",
            command=self._change_state,
            fg_color="green",
            hover_color="dark green"
        )
        ok_btn.pack(side="right")
    
    def _change_state(self):
        """Change the chamber state."""
        new_state_value = self.state_combo.get()
        reason = self.reason_entry.get("1.0", "end").strip()
        
        try:
            new_state = ChamberState(new_state_value)
            success = self.app.update_chamber_state(self.chamber.id, new_state, reason)
            
            if success:
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change chamber state")
                
        except ValueError:
            messagebox.showerror("Error", "Invalid state selected")
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()


class StatusChangeDialog:
    """Dialog for changing chamber status."""
    
    def __init__(self, parent, chamber, app):
        self.chamber = chamber
        self.app = app
        self.result = None
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Set Chamber Status")
        self.dialog.geometry("350x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_dialog()
    
    def _setup_dialog(self):
        """Setup the status change dialog."""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text=f"Set Status: {self.chamber.name}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Current status
        current_status = self.chamber.state_manager.current_status
        current_text = current_status.value if current_status else "None"
        current_label = ctk.CTkLabel(
            main_frame,
            text=f"Current Status: {current_text}",
            font=ctk.CTkFont(size=12)
        )
        current_label.pack(pady=(0, 15))
        
        # New status selection
        new_status_label = ctk.CTkLabel(main_frame, text="New Status:")
        new_status_label.pack(anchor="w", pady=(0, 5))
        
        status_values = ["Clear Status"] + [status.value for status in ChamberStatus]
        self.status_combo = ctk.CTkComboBox(
            main_frame,
            values=status_values,
            state="readonly"
        )
        self.status_combo.pack(fill="x", pady=(0, 15))
        self.status_combo.set("Clear Status" if not current_status else current_status.value)
        
        # Reason
        reason_label = ctk.CTkLabel(main_frame, text="Reason:")
        reason_label.pack(anchor="w", pady=(0, 5))
        
        self.reason_entry = ctk.CTkTextbox(main_frame, height=80)
        self.reason_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        ok_btn = ctk.CTkButton(
            button_frame,
            text="Set Status",
            command=self._change_status,
            fg_color="orange",
            hover_color="dark orange"
        )
        ok_btn.pack(side="right")
    
    def _change_status(self):
        """Change the chamber status."""
        new_status_value = self.status_combo.get()
        reason = self.reason_entry.get("1.0", "end").strip()
        
        if not reason.strip():
            messagebox.showerror("Error", "Reason is required for status changes")
            return
        
        try:
            if new_status_value == "Clear Status":
                success = self.app.clear_chamber_status(self.chamber.id, reason)
            else:
                new_status = ChamberStatus(new_status_value)
                success = self.app.update_chamber_status(self.chamber.id, new_status, reason)
            
            if success:
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change chamber status")
                
        except ValueError:
            messagebox.showerror("Error", "Invalid status selected")
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
