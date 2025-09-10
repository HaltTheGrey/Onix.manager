"""
Modern Enhanced Chamber Card
Beautiful, functional chamber cards with modern design and improved UX
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Dict, Any, Optional
import tkinter as tk

from ..core.chamber_state import ChamberState, ChamberStatus
from ..utils import get_logger
from ..utils.threading_utils import get_task_manager, ui_thread_only, async_operation
from ..utils.performance_monitor import get_performance_monitor, profile_operation, ui_operation_timer
from .modern_theme import ModernFrame, ModernButton, ModernLabel, ModernEntry, get_theme_manager, apply_modern_styling
from .modern_dialogs import ModernStateChangeDialog, ModernStatusChangeDialog, ModernWorkRequestDialog


class ModernChamberCard(ModernFrame):
    """
    Modern chamber card with enhanced visual design and functionality
    """
    
    def __init__(self, parent, chamber, app):
        super().__init__(parent, style="card")
        
        self.chamber = chamber
        self.app = app
        self.logger = get_logger(__name__)
        self.theme_manager = get_theme_manager()
        
        # Threading and performance monitoring
        self.task_manager = get_task_manager()
        self.performance_monitor = get_performance_monitor()
        
        # UI state
        self.is_highlighted = False
        self.expanded = False
        self._updating = False
        self.animation_state = "collapsed"
        
        # Setup card UI
        self._setup_ui()
        
        # Update initial data
        self.update_data()
    
    def _setup_ui(self):
        """Setup the modern chamber card UI"""
        # Configure main card
        self.configure(
            corner_radius=12,
            border_width=2,
            border_color=self.theme_manager.get_color("border")
        )
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create sections
        self._create_header_section()
        self._create_status_section()
        self._create_metrics_section()
        self._create_action_section()
        self._create_expandable_section()
        
        # Add hover effects
        self._setup_hover_effects()
    
    def _create_header_section(self):
        """Create the modern header section"""
        header_frame = ModernFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator with glow effect
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="●",
            font=ctk.CTkFont(size=24),
            width=30,
            height=30
        )
        self.status_indicator.grid(row=0, column=0, rowspan=2, padx=(5, 10), pady=5)
        
        # Chamber name with modern typography
        self.name_label = ModernLabel(
            header_frame,
            text=self.chamber.name,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_style="primary"
        )
        self.name_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Chamber type with accent color
        self.type_label = ModernLabel(
            header_frame,
            text=f"{self.chamber.type.value} Chamber",
            font=ctk.CTkFont(size=12, weight="normal"),
            text_style="secondary"
        )
        self.type_label.grid(row=1, column=1, sticky="w", padx=5)
        
        # Expand/collapse button with modern icon
        self.expand_button = ModernButton(
            header_frame,
            text="⌄",
            width=35,
            height=35,
            font=ctk.CTkFont(size=16),
            command=self._toggle_expanded,
            style="primary_button"
        )
        self.expand_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
        
        # Connection indicator
        self.connection_indicator = ctk.CTkLabel(
            header_frame,
            text="📶",
            font=ctk.CTkFont(size=12),
            width=20
        )
        self.connection_indicator.grid(row=0, column=3, padx=5)
    
    def _create_status_section(self):
        """Create the status display section with modern styling"""
        status_frame = ModernFrame(self)
        status_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Current state with accent border
        state_container = ModernFrame(status_frame)
        state_container.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=5)
        state_container.configure(border_width=1, border_color=self.theme_manager.get_color("primary"))
        
        state_title = ModernLabel(
            state_container,
            text="STATE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_style="muted"
        )
        state_title.pack(pady=(8, 2))
        
        self.state_label = ModernLabel(
            state_container,
            text=self.chamber.state_manager.current_state.value,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="primary"
        )
        self.state_label.pack(pady=(0, 8))
        
        # Current status 
        status_container = ModernFrame(status_frame)
        status_container.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=5)
        
        status_title = ModernLabel(
            status_container,
            text="STATUS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_style="muted"
        )
        status_title.pack(pady=(8, 2))
        
        self.status_label = ModernLabel(
            status_container,
            text="None",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="secondary"
        )
        self.status_label.pack(pady=(0, 8))
    
    def _create_metrics_section(self):
        """Create metrics display with modern cards"""
        metrics_frame = ModernFrame(self)
        metrics_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=2)
        
        # Configure grid for 4 metrics
        for i in range(4):
            metrics_frame.grid_columnconfigure(i, weight=1)
        
        # Temperature metric
        self.temp_metric = self._create_metric_card(
            metrics_frame, "TEMP", "-- °C", "🌡️", 0
        )
        
        # Pressure metric
        self.pressure_metric = self._create_metric_card(
            metrics_frame, "PRESSURE", "-- hPa", "🔽", 1
        )
        
        # Vacuum metric
        self.vacuum_metric = self._create_metric_card(
            metrics_frame, "VACUUM", "-- Torr", "⚡", 2
        )
        
        # Humidity metric
        self.humidity_metric = self._create_metric_card(
            metrics_frame, "HUMIDITY", "-- %", "💧", 3
        )
    
    def _create_metric_card(self, parent, title: str, value: str, icon: str, column: int):
        """Create a modern metric card"""
        metric_frame = ModernFrame(parent)
        metric_frame.grid(row=0, column=column, sticky="ew", padx=2, pady=5)
        metric_frame.configure(corner_radius=6)
        
        icon_label = ctk.CTkLabel(
            metric_frame,
            text=icon,
            font=ctk.CTkFont(size=16)
        )
        icon_label.pack(pady=(5, 0))
        
        title_label = ModernLabel(
            metric_frame,
            text=title,
            font=ctk.CTkFont(size=8, weight="bold"),
            text_style="muted"
        )
        title_label.pack()
        
        value_label = ModernLabel(
            metric_frame,
            text=value,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_style="primary"
        )
        value_label.pack(pady=(0, 5))
        
        return {
            "frame": metric_frame,
            "icon": icon_label,
            "title": title_label,
            "value": value_label
        }
    
    def _create_action_section(self):
        """Create action buttons with modern styling"""
        action_frame = ModernFrame(self)
        action_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(2, 8))
        
        # Quick action buttons
        self.state_btn = ModernButton(
            action_frame,
            text="⚙️ State",
            height=32,
            command=self._show_state_dialog,
            style="primary_button"
        )
        self.state_btn.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        self.status_btn = ModernButton(
            action_frame,
            text="🔧 Status",
            height=32,
            command=self._show_status_dialog,
            style="accent_button"
        )
        self.status_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.work_btn = ModernButton(
            action_frame,
            text="📋 Work",
            height=32,
            command=self._show_work_request_dialog,
            style="warning_button"
        )
        self.work_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def _create_expandable_section(self):
        """Create expandable details section"""
        self.details_frame = ModernFrame(self)
        # Initially hidden - will be shown when expanded
        
        # Detailed telemetry
        telemetry_section = ModernFrame(self.details_frame)
        telemetry_section.pack(fill="x", padx=8, pady=5)
        
        telemetry_title = ModernLabel(
            telemetry_section,
            text="📊 Detailed Telemetry",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="primary"
        )
        telemetry_title.pack(anchor="w", pady=(5, 10))
        
        # Telemetry grid
        self.telemetry_grid = ModernFrame(telemetry_section)
        self.telemetry_grid.pack(fill="x", padx=10)
        
        # Configure grid
        for i in range(3):
            self.telemetry_grid.grid_columnconfigure(i, weight=1)
        
        # Additional telemetry items will be created dynamically
        
        # Work requests section
        work_section = ModernFrame(self.details_frame)
        work_section.pack(fill="x", padx=8, pady=5)
        
        work_title = ModernLabel(
            work_section,
            text="📋 Active Work Requests",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="primary"
        )
        work_title.pack(anchor="w", pady=(5, 10))
        
        self.work_list_frame = ModernFrame(work_section)
        self.work_list_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Timeline section
        timeline_section = ModernFrame(self.details_frame)
        timeline_section.pack(fill="x", padx=8, pady=5)
        
        timeline_title = ModernLabel(
            timeline_section,
            text="⏱️ Recent Activity",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="primary"
        )
        timeline_title.pack(anchor="w", pady=(5, 10))
        
        self.timeline_frame = ModernFrame(timeline_section)
        self.timeline_frame.pack(fill="x", padx=10, pady=(0, 10))
    
    def _setup_hover_effects(self):
        """Setup hover effects for modern interaction"""
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)
    
    def _on_hover_enter(self, event):
        """Handle hover enter"""
        self.configure(border_color=self.theme_manager.get_color("primary_light"))
    
    def _on_hover_leave(self, event):
        """Handle hover leave"""
        if not self.is_highlighted:
            self.configure(border_color=self.theme_manager.get_color("border"))
    
    def _toggle_expanded(self):
        """Toggle expanded state with smooth animation"""
        if self.expanded:
            # Collapse
            self.details_frame.grid_forget()
            self.expand_button.configure(text="⌄")
            self.expanded = False
            self.animation_state = "collapsed"
        else:
            # Expand
            self.details_frame.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 8))
            self.expand_button.configure(text="⌃")
            self.expanded = True
            self.animation_state = "expanded"
            
            # Update expanded content
            self._update_expanded_details_async()
    
    def _show_state_dialog(self):
        """Show modern state change dialog"""
        from .modern_dialogs import ModernStateChangeDialog
        dialog = ModernStateChangeDialog(self.winfo_toplevel(), self.chamber, self.app)
        dialog.show()
        
        if dialog.result:
            self.update_data()
    
    def _show_status_dialog(self):
        """Show modern status change dialog"""
        from .modern_dialogs import ModernStatusChangeDialog
        dialog = ModernStatusChangeDialog(self.winfo_toplevel(), self.chamber, self.app)
        dialog.show()
        
        if dialog.result:
            self.update_data()
    
    def _show_work_request_dialog(self):
        """Show modern work request dialog"""
        from .modern_dialogs import ModernWorkRequestDialog
        dialog = ModernWorkRequestDialog(self.winfo_toplevel(), self.app, self.chamber)
        dialog.show()
        
        if dialog.result:
            self.update_data()
            messagebox.showinfo("Success", f"Work request '{dialog.result.title}' created successfully!")
    
    @ui_operation_timer(get_performance_monitor())
    def update_data(self):
        """Update chamber card with current data"""
        if self._updating:
            return
            
        self._updating = True
        try:
            self._update_basic_info()
            
            if self.expanded:
                self._update_expanded_details_async()
                
        except Exception as e:
            self.logger.error(f"Error updating chamber card for {self.chamber.name}: {e}")
        finally:
            self._updating = False
    
    @ui_thread_only
    def _update_basic_info(self):
        """Update basic chamber information"""
        # Update state and status
        current_state = self.chamber.state_manager.current_state
        current_status = self.chamber.state_manager.current_status
        
        self.state_label.configure(text=current_state.value)
        
        if current_status:
            self.status_label.configure(text=current_status.value)
            status_color = self._get_status_color(current_status.value)
            self.status_label.configure(text_color=status_color)
        else:
            self.status_label.configure(text="Normal")
            self.status_label.configure(text_color=self.theme_manager.get_color("success"))
        
        # Update status indicator
        state_color = self._get_state_color(current_state.value)
        self.status_indicator.configure(text_color=state_color)
        
        # Update connection indicator
        if self.chamber.is_connected:
            self.connection_indicator.configure(text="📶", text_color=self.theme_manager.get_color("success"))
        else:
            self.connection_indicator.configure(text="📵", text_color=self.theme_manager.get_color("error"))
        
        # Update metrics
        telemetry = self.chamber.telemetry
        self.temp_metric["value"].configure(text=f"{telemetry.get('temperature', '--')} °C")
        self.pressure_metric["value"].configure(text=f"{telemetry.get('pressure', '--')} hPa")
        self.vacuum_metric["value"].configure(text=f"{telemetry.get('vacuum', '--')} Torr")
        self.humidity_metric["value"].configure(text=f"{telemetry.get('humidity', '--')} %")
    
    def _get_state_color(self, state: str) -> str:
        """Get color for chamber state"""
        state_colors = {
            "IDLE": self.theme_manager.get_color("status_idle"),
            "RUNNING": self.theme_manager.get_color("primary"),
            "MAINTENANCE": self.theme_manager.get_color("warning"),
            "ERROR": self.theme_manager.get_color("error"),
            "OFFLINE": self.theme_manager.get_color("status_offline"),
        }
        return state_colors.get(state, self.theme_manager.get_color("status_idle"))
    
    def _get_status_color(self, status: str) -> str:
        """Get color for chamber status"""
        status_colors = {
            "OPERATIONAL": self.theme_manager.get_color("success"),
            "MAINTENANCE": self.theme_manager.get_color("warning"),
            "ERROR": self.theme_manager.get_color("error"),
            "OFFLINE": self.theme_manager.get_color("status_offline"),
        }
        return status_colors.get(status, self.theme_manager.get_color("text_secondary"))
    
    @async_operation(get_task_manager())
    def _update_expanded_details_async(self):
        """Update expanded details asynchronously"""
        try:
            # Prepare data in background
            telemetry_data = self._prepare_detailed_telemetry()
            work_requests_data = self._prepare_work_requests_data()
            timeline_data = self._prepare_timeline_data()
            
            # Update UI on main thread
            self.task_manager.submit_ui_update(
                lambda: self._update_expanded_details_ui(telemetry_data, work_requests_data, timeline_data)
            )
        except Exception as e:
            self.logger.error(f"Error preparing expanded details: {e}")
    
    def _prepare_detailed_telemetry(self):
        """Prepare detailed telemetry data"""
        return {
            'temperature': self.chamber.telemetry.get('temperature', '--'),
            'pressure': self.chamber.telemetry.get('pressure', '--'),
            'vacuum': self.chamber.telemetry.get('vacuum', '--'),
            'humidity': self.chamber.telemetry.get('humidity', '--'),
            'flow_rate': self.chamber.telemetry.get('flow_rate', '--'),
            'power_consumption': self.chamber.telemetry.get('power_consumption', '--')
        }
    
    def _prepare_work_requests_data(self):
        """Prepare work requests data"""
        return self.chamber.get_active_work_requests()
    
    def _prepare_timeline_data(self):
        """Prepare recent activity timeline data"""
        # Get recent state transitions
        recent_transitions = self.chamber.state_manager.state_history[-5:]
        return recent_transitions
    
    @ui_thread_only
    def _update_expanded_details_ui(self, telemetry_data, work_requests_data, timeline_data):
        """Update expanded details UI"""
        try:
            # Update detailed telemetry
            self._update_detailed_telemetry(telemetry_data)
            
            # Update work requests
            self._update_work_requests_list(work_requests_data)
            
            # Update timeline
            self._update_timeline(timeline_data)
            
        except Exception as e:
            self.logger.error(f"Error updating expanded details UI: {e}")
    
    def _update_detailed_telemetry(self, telemetry_data):
        """Update detailed telemetry display"""
        # Clear existing items
        for widget in self.telemetry_grid.winfo_children():
            widget.destroy()
        
        # Create telemetry items
        items = [
            ("Flow Rate", f"{telemetry_data.get('flow_rate', '--')} L/min", "💨"),
            ("Power", f"{telemetry_data.get('power_consumption', '--')} kW", "⚡"),
            ("Uptime", self._format_uptime(), "⏰")
        ]
        
        for i, (title, value, icon) in enumerate(items):
            self._create_detailed_telemetry_item(title, value, icon, i)
    
    def _create_detailed_telemetry_item(self, title: str, value: str, icon: str, column: int):
        """Create detailed telemetry item"""
        item_frame = ModernFrame(self.telemetry_grid)
        item_frame.grid(row=0, column=column, sticky="ew", padx=2, pady=2)
        item_frame.configure(corner_radius=4)
        
        icon_label = ctk.CTkLabel(item_frame, text=icon, font=ctk.CTkFont(size=14))
        icon_label.pack(pady=(5, 0))
        
        title_label = ModernLabel(item_frame, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_style="muted")
        title_label.pack()
        
        value_label = ModernLabel(item_frame, text=value, font=ctk.CTkFont(size=10, weight="bold"), text_style="primary")
        value_label.pack(pady=(0, 5))
    
    def _update_work_requests_list(self, work_requests_data):
        """Update work requests list"""
        # Clear existing items
        for widget in self.work_list_frame.winfo_children():
            widget.destroy()
        
        if not work_requests_data:
            no_work_label = ModernLabel(
                self.work_list_frame,
                text="No active work requests",
                text_style="muted"
            )
            no_work_label.pack(pady=10)
        else:
            for request in work_requests_data[:3]:  # Show max 3
                work_item = ModernFrame(self.work_list_frame)
                work_item.pack(fill="x", pady=2)
                
                title_label = ModernLabel(
                    work_item,
                    text=f"• {request.title}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_style="primary"
                )
                title_label.pack(anchor="w", padx=10, pady=(5, 0))
                
                status_label = ModernLabel(
                    work_item,
                    text=f"Priority: {request.priority} | Due: {request.due_date or 'Not set'}",
                    font=ctk.CTkFont(size=9),
                    text_style="muted"
                )
                status_label.pack(anchor="w", padx=10, pady=(0, 5))
    
    def _update_timeline(self, timeline_data):
        """Update activity timeline"""
        # Clear existing items
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()
        
        if not timeline_data:
            no_activity_label = ModernLabel(
                self.timeline_frame,
                text="No recent activity",
                text_style="muted"
            )
            no_activity_label.pack(pady=10)
        else:
            for transition in timeline_data:
                timeline_item = ModernFrame(self.timeline_frame)
                timeline_item.pack(fill="x", pady=1)
                
                time_label = ModernLabel(
                    timeline_item,
                    text=transition.timestamp.strftime("%H:%M"),
                    font=ctk.CTkFont(size=9),
                    text_style="muted"
                )
                time_label.pack(side="left", padx=(10, 5), pady=3)
                
                event_label = ModernLabel(
                    timeline_item,
                    text=f"Changed to {transition.to_value}",
                    font=ctk.CTkFont(size=10),
                    text_style="secondary"
                )
                event_label.pack(side="left", pady=3)
    
    def _format_uptime(self) -> str:
        """Format chamber uptime"""
        # Get state duration
        duration = self.chamber.state_manager.get_state_duration()
        
        if duration < 60:
            return f"{int(duration)}s"
        elif duration < 3600:
            return f"{int(duration // 60)}m"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def highlight(self):
        """Highlight the chamber card"""
        if not self.is_highlighted:
            self.configure(border_color=self.theme_manager.get_color("accent"), border_width=3)
            self.is_highlighted = True
            
            # Remove highlight after 3 seconds
            self.after(3000, self._remove_highlight)
    
    def _remove_highlight(self):
        """Remove highlight from chamber card"""
        self.configure(border_color=self.theme_manager.get_color("border"), border_width=2)
        self.is_highlighted = False
