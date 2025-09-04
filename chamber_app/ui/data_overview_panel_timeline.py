"""
Data overview panel showing chamber statistics and visualizations.
Displays timeline graphs showing chamber states over time by type.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, HourLocator
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import matplotlib.dates as mdates
from tkinter import messagebox

from ..core.chamber_state import ChamberState, ChamberStatus, ChamberType
from ..utils import get_logger


class DataOverviewPanel(ctk.CTkFrame):
    """
    Overview panel showing chamber statistics and visualizations.
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        self.view_mode = "count"  # "count" or "time"
        
        # Timeline properties
        self.timeline_hours = 24  # Show last 24 hours by default
        self.chamber_graphs = {}  # Store graph references by type
        self.graph_collapsed = {"TVAC": False, "HASS": False, "THERMAL": False}
        self.state_colors = {
            ChamberState.AVAILABLE_EMPTY.value: '#4CAF50',       # Green
            ChamberState.STAGING.value: '#FF9800',               # Orange
            ChamberState.SETUP.value: '#2196F3',                 # Blue
            ChamberState.TEST_START.value: '#9C27B0',            # Purple
            ChamberState.TEST_NOMINAL.value: '#3F51B5',          # Indigo
            ChamberState.TEST_END.value: '#FF5722',              # Deep Orange
            ChamberState.TEST_TEARDOWN.value: '#795548',         # Brown
            'default': '#607D8B'                                 # Blue grey
        }
        
        # Pack to fill parent
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup UI
        self._setup_ui()
        
        # Initial data update
        self.update_data()
    
    def _setup_ui(self):
        """Setup the overview panel UI."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with controls
        self._create_header()
        
        # Main content area
        self._create_content_area()
        
        # Statistics sidebar
        self._create_statistics_sidebar()
    
    def _create_header(self):
        """Create the header with title and controls."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Chamber Overview",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # View mode toggle
        mode_frame = ctk.CTkFrame(header_frame)
        mode_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        self.mode_label = ctk.CTkLabel(mode_frame, text="View Mode:")
        self.mode_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.mode_combo = ctk.CTkComboBox(
            mode_frame,
            values=["Count Overview", "Timeline View"],
            command=self._on_mode_change,
            width=150
        )
        self.mode_combo.pack(side="left", padx=(0, 10), pady=10)
        self.mode_combo.set("Count Overview")
        
        # Timeline hours control (only visible in timeline mode)
        self.hours_frame = ctk.CTkFrame(mode_frame)
        
        self.hours_label = ctk.CTkLabel(self.hours_frame, text="Hours:")
        self.hours_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.hours_combo = ctk.CTkComboBox(
            self.hours_frame,
            values=["1", "6", "12", "24", "48", "72"],
            command=self._on_hours_change,
            width=80
        )
        self.hours_combo.pack(side="left", padx=(0, 10), pady=10)
        self.hours_combo.set("24")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            command=self.update_data,
            width=80
        )
        refresh_btn.grid(row=0, column=3, sticky="e", padx=(5, 10), pady=10)
    
    def _create_content_area(self):
        """Create the main content area with graphs."""
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 5), pady=(0, 5))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # State graph
        self.state_graph_frame = ctk.CTkFrame(content_frame)
        self.state_graph_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        state_title = ctk.CTkLabel(
            self.state_graph_frame,
            text="Chamber States",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        state_title.pack(pady=(10, 5))
        
        # Create matplotlib figure for state graph
        self.state_fig, self.state_ax = plt.subplots(figsize=(8, 4))
        self.state_fig.patch.set_facecolor('#2b2b2b')  # Dark theme
        self.state_ax.set_facecolor('#2b2b2b')
        
        self.state_canvas = FigureCanvasTkAgg(self.state_fig, self.state_graph_frame)
        self.state_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Status graph
        self.status_graph_frame = ctk.CTkFrame(content_frame)
        self.status_graph_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        status_title = ctk.CTkLabel(
            self.status_graph_frame,
            text="Chamber Status Issues",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.pack(pady=(10, 5))
        
        # Create matplotlib figure for status graph
        self.status_fig, self.status_ax = plt.subplots(figsize=(8, 4))
        self.status_fig.patch.set_facecolor('#2b2b2b')
        self.status_ax.set_facecolor('#2b2b2b')
        
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, self.status_graph_frame)
        self.status_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Bind double-click events
        self.state_canvas.mpl_connect('button_press_event', self._on_state_graph_click)
        self.status_canvas.mpl_connect('button_press_event', self._on_status_graph_click)
    
    def _create_statistics_sidebar(self):
        """Create the statistics sidebar."""
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5))
        stats_frame.configure(width=250)
        stats_frame.grid_propagate(False)
        
        # Statistics title
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_title.pack(pady=(10, 15))
        
        # Overall stats
        self.overall_stats_frame = ctk.CTkFrame(stats_frame)
        self.overall_stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        overall_title = ctk.CTkLabel(
            self.overall_stats_frame,
            text="Overall",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        overall_title.pack(pady=(5, 0))
        
        self.total_chambers_label = ctk.CTkLabel(self.overall_stats_frame, text="Total Chambers: 0")
        self.total_chambers_label.pack(pady=2)
        
        self.connected_label = ctk.CTkLabel(self.overall_stats_frame, text="Connected: 0")
        self.connected_label.pack(pady=2)
        
        self.active_work_label = ctk.CTkLabel(self.overall_stats_frame, text="Active Work Requests: 0")
        self.active_work_label.pack(pady=(2, 5))
        
        # By type stats
        self.type_stats_frame = ctk.CTkFrame(stats_frame)
        self.type_stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        type_title = ctk.CTkLabel(
            self.type_stats_frame,
            text="By Type",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        type_title.pack(pady=(5, 0))
        
        self.type_labels = {}
        for chamber_type in ["TVAC", "HASS", "THERMAL"]:
            label = ctk.CTkLabel(self.type_stats_frame, text=f"{chamber_type}: 0")
            label.pack(pady=2)
            self.type_labels[chamber_type] = label
        
        # Recent activity
        self.activity_frame = ctk.CTkFrame(stats_frame)
        self.activity_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        activity_title = ctk.CTkLabel(
            self.activity_frame,
            text="Recent Activity",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        activity_title.pack(pady=(5, 0))
        
        self.activity_text = ctk.CTkTextbox(
            self.activity_frame,
            height=150,
            wrap="word"
        )
        self.activity_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _on_mode_change(self, value):
        """Handle view mode change."""
        if value == "Count Overview":
            self.view_mode = "count"
            self.hours_frame.pack_forget()  # Hide hours control
        else:
            self.view_mode = "time"
            self.hours_frame.pack(side="left", padx=(10, 0), pady=10)  # Show hours control
        
        self.update_data()
        self.logger.info(f"Changed view mode to: {self.view_mode}")
    
    def _on_hours_change(self, value):
        """Handle timeline hours change."""
        self.timeline_hours = int(value)
        if self.view_mode == "time":
            self.update_data()
        self.logger.info(f"Changed timeline hours to: {self.timeline_hours}")
    
    def _on_state_graph_click(self, event):
        """Handle click on state graph."""
        if event.dblclick:
            # Get clicked bar and show chambers in that state
            if hasattr(self, 'state_bars') and event.inaxes == self.state_ax:
                self._show_chambers_by_state(event)
    
    def _on_status_graph_click(self, event):
        """Handle click on status graph."""
        if event.dblclick:
            # Get clicked bar and show chambers with that status
            if hasattr(self, 'status_bars') and event.inaxes == self.status_ax:
                self._show_chambers_by_status(event)
    
    def _show_chambers_by_state(self, event):
        """Show list of chambers in a specific state."""        # Show chambers by state with detailed dialog
        try:
            # Get the clicked bar to determine the state
            if hasattr(event, 'artist') and hasattr(event.artist, 'get_label'):
                state_name = event.artist.get_label()
                self._show_chamber_list_dialog("state", state_name)
            else:
                # Fallback - show all states
                self._show_all_states_dialog()
        except Exception as e:
            self.logger.error(f"Error showing chambers by state: {e}")
    
    def _show_chambers_by_status(self, event):
        """Show list of chambers with a specific status."""
        # Show chambers by status with detailed dialog
        try:
            # Get the clicked bar to determine the status
            if hasattr(event, 'artist') and hasattr(event.artist, 'get_label'):
                status_name = event.artist.get_label()
                self._show_chamber_list_dialog("status", status_name)
            else:
                # Fallback - show all statuses
                self._show_all_statuses_dialog()
        except Exception as e:
            self.logger.error(f"Error showing chambers by status: {e}")
    
    def _show_chamber_list_dialog(self, filter_type: str, filter_value: str):
        """Show a dialog with chambers filtered by state or status."""
        import customtkinter as ctk
        from ..core.chamber_state import ChamberState, ChamberStatus
        
        # Get chambers based on filter
        if filter_type == "state":
            chambers = [c for c in self.app.get_chambers() 
                       if c.state_manager.current_state.value == filter_value]
            title = f"Chambers in '{filter_value}' State"
        else:  # status
            chambers = [c for c in self.app.get_chambers() 
                       if c.state_manager.current_status and c.state_manager.current_status.value == filter_value]
            title = f"Chambers with '{filter_value}' Status"
        
        if not chambers:
            messagebox.showinfo("No Chambers", f"No chambers found with {filter_type}: {filter_value}")
            return
        
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("600x500")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.winfo_width() // 2) - (600 // 2) + self.winfo_rootx()
        y = (self.winfo_height() // 2) - (500 // 2) + self.winfo_rooty()
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"{title} ({len(chambers)} chambers)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Scrollable list
        scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        scrollable_frame.pack(fill="both", expand=True)
        
        # Add chamber entries
        for chamber in chambers:
            self._create_chamber_list_item(scrollable_frame, chamber)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=dialog.destroy,
            width=100
        )
        close_btn.pack(pady=(15, 0))
    
    def _create_chamber_list_item(self, parent, chamber):
        """Create a list item for a chamber."""
        import customtkinter as ctk
        
        # Item frame
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", padx=5, pady=2)
        
        # Chamber info
        info_frame = ctk.CTkFrame(item_frame)
        info_frame.pack(fill="x", padx=10, pady=8)
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Name and type
        name_label = ctk.CTkLabel(
            info_frame,
            text=f"{chamber.name} ({chamber.type.value})",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # State
        state_label = ctk.CTkLabel(
            info_frame,
            text=f"State: {chamber.state_manager.current_state.value}",
            font=ctk.CTkFont(size=12)
        )
        state_label.grid(row=1, column=0, sticky="w")
        
        # Status
        status_text = chamber.state_manager.current_status.value if chamber.state_manager.current_status else "None"
        status_label = ctk.CTkLabel(
            info_frame,
            text=f"Status: {status_text}",
            font=ctk.CTkFont(size=12)
        )
        status_label.grid(row=1, column=1, sticky="w", padx=(20, 0))
        
        # Connection and work requests
        conn_text = "Connected" if chamber.is_connected else "Disconnected"
        active_wr = len(chamber.get_active_work_requests())
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=f"Connection: {conn_text} | Active Work Requests: {active_wr}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        details_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))
    
    def _show_all_states_dialog(self):
        """Show dialog with all chamber states and counts."""
        stats = self.app.get_chamber_statistics()
        state_counts = stats.get('by_state', {})
        
        import customtkinter as ctk
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Chambers by State")
        dialog.geometry("400x400")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.winfo_width() // 2) - (400 // 2) + self.winfo_rootx()
        y = (self.winfo_height() // 2) - (400 // 2) + self.winfo_rooty()
        dialog.geometry(f"400x400+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Chambers by State",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        scrollable_frame.pack(fill="both", expand=True)
        
        for state, count in state_counts.items():
            if count > 0:
                btn = ctk.CTkButton(
                    scrollable_frame,
                    text=f"{state}: {count} chambers",
                    command=lambda s=state: self._show_chamber_list_dialog("state", s),
                    anchor="w"
                )
                btn.pack(fill="x", pady=2, padx=5)
        
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=dialog.destroy,
            width=100
        )
        close_btn.pack(pady=(15, 0))
    
    def _show_all_statuses_dialog(self):
        """Show dialog with all chamber statuses and counts."""
        stats = self.app.get_chamber_statistics()
        status_counts = stats.get('by_status', {})
        
        import customtkinter as ctk
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Chambers by Status")
        dialog.geometry("400x400")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.winfo_width() // 2) - (400 // 2) + self.winfo_rootx()
        y = (self.winfo_height() // 2) - (400 // 2) + self.winfo_rooty()
        dialog.geometry(f"400x400+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Chambers by Status",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        scrollable_frame.pack(fill="both", expand=True)
        
        for status, count in status_counts.items():
            if count > 0:
                btn = ctk.CTkButton(
                    scrollable_frame,
                    text=f"{status}: {count} chambers",
                    command=lambda s=status: self._show_chamber_list_dialog("status", s),
                    anchor="w"
                )
                btn.pack(fill="x", pady=2, padx=5)
        
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=dialog.destroy,
            width=100
        )
        close_btn.pack(pady=(15, 0))
    
    def update_data(self):
        """Update all data displays."""
        try:
            # Get application statistics
            stats = self.app.get_chamber_statistics()
            
            # Update statistics sidebar
            self._update_statistics(stats)
            
            # Update graphs based on view mode
            if self.view_mode == "count":
                self._update_count_graphs(stats)
            else:
                self._update_time_graphs()
            
            # Update recent activity
            self._update_recent_activity()
            
        except Exception as e:
            self.logger.error(f"Error updating overview data: {e}", exc_info=True)
    
    def _update_statistics(self, stats: Dict[str, Any]):
        """Update the statistics sidebar."""
        # Overall stats
        self.total_chambers_label.configure(text=f"Total Chambers: {stats.get('total_chambers', 0)}")
        self.connected_label.configure(text=f"Connected: {stats.get('connected_chambers', 0)}")
        self.active_work_label.configure(text=f"Active Work Requests: {stats.get('active_work_requests', 0)}")
        
        # By type stats
        by_type = stats.get('by_type', {})
        for chamber_type, label in self.type_labels.items():
            count = by_type.get(chamber_type, 0)
            label.configure(text=f"{chamber_type}: {count}")
    
    def _update_count_graphs(self, stats: Dict[str, Any]):
        """Update graphs with count data."""
        # Update state graph
        self.state_ax.clear()
        by_state = stats.get('by_state', {})
        
        if by_state:
            states = list(by_state.keys())
            counts = list(by_state.values())
            
            # Truncate state names for better display
            display_states = [state.replace('test ', '').replace(' (auto)', '') for state in states]
            
            self.state_bars = self.state_ax.bar(display_states, counts, color='#1f77b4', alpha=0.8)
            self.state_ax.set_title("Chambers by State", color='white')
            self.state_ax.set_ylabel("Number of Chambers", color='white')
            self.state_ax.tick_params(colors='white')
            
            # Rotate x-axis labels for better readability
            plt.setp(self.state_ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(self.state_bars, counts):
                height = bar.get_height()
                self.state_ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                                 f'{count}', ha='center', va='bottom', color='white')
        
        self.state_fig.tight_layout()
        self.state_canvas.draw()
        
        # Update status graph
        self.status_ax.clear()
        by_status = stats.get('by_status', {})
        
        if by_status:
            statuses = list(by_status.keys())
            counts = list(by_status.values())
            
            # Use orange/red colors for status issues
            colors = ['#ff7f0e' if count > 0 else '#d62728' for count in counts]
            
            self.status_bars = self.status_ax.bar(statuses, counts, color=colors, alpha=0.8)
            self.status_ax.set_title("Chambers with Status Issues", color='white')
            self.status_ax.set_ylabel("Number of Chambers", color='white')
            self.status_ax.tick_params(colors='white')
            
            # Rotate x-axis labels
            plt.setp(self.status_ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(self.status_bars, counts):
                height = bar.get_height()
                self.status_ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                                 f'{count}', ha='center', va='bottom', color='white')
        else:
            self.status_ax.text(0.5, 0.5, "No Status Issues", 
                              transform=self.status_ax.transAxes,
                              ha='center', va='center', color='white', fontsize=14)
        
        self.status_fig.tight_layout()
        self.status_canvas.draw()
    
    def _update_time_graphs(self):
        """Update graphs with timeline data showing horizontal bars by chamber type."""
        chambers = self.app.get_chambers()
        
        # Group chambers by type
        chambers_by_type = {"TVAC": [], "HASS": [], "THERMAL": []}
        for chamber in chambers:
            chamber_type = chamber.chamber_type.value if hasattr(chamber, 'chamber_type') else "TVAC"
            if chamber_type in chambers_by_type:
                chambers_by_type[chamber_type].append(chamber)
        
        # Set up time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.timeline_hours)
        
        # Clear both axes
        self.state_ax.clear()
        self.status_ax.clear()
        
        # Create timeline for state graph
        self._create_timeline_graph(
            self.state_ax, 
            chambers_by_type, 
            start_time, 
            end_time, 
            "Chamber States Timeline", 
            "state"
        )
        
        # Create timeline for status graph (if there are status issues)
        self._create_timeline_graph(
            self.status_ax, 
            chambers_by_type, 
            start_time, 
            end_time, 
            "Chamber Status Issues Timeline", 
            "status"
        )
        
        self.state_fig.tight_layout()
        self.state_canvas.draw()
        self.status_fig.tight_layout()
        self.status_canvas.draw()
    
    def _create_timeline_graph(self, ax, chambers_by_type, start_time, end_time, title, data_type):
        """Create a timeline graph with horizontal bars for each chamber."""
        ax.set_facecolor('#2b2b2b')
        
        y_position = 0
        y_labels = []
        
        # Iterate through chamber types
        for chamber_type, chambers in chambers_by_type.items():
            if not chambers:
                continue
                
            # Add type separator
            if y_position > 0:
                ax.axhline(y=y_position - 0.5, color='white', linestyle='--', alpha=0.3)
            
            # Add chambers of this type
            for chamber in chambers:                # Get state/status history for the time range
                history = self._get_chamber_history(chamber, start_time, end_time, data_type)
                
                # Create horizontal bars for each state/status period
                for period in history:
                    color = self.state_colors.get(period['state'], self.state_colors['default'])
                    
                    # Calculate position and width using matplotlib dates
                    start_pos = mdates.date2num(period['start_time'])
                    end_pos = mdates.date2num(period['end_time'])
                    width = end_pos - start_pos
                    
                    # Only show bars that are long enough to be visible
                    duration = (period['end_time'] - period['start_time']).total_seconds() / 3600  # Convert to hours
                    if duration > 0.1:  # Minimum 6 minutes
                        ax.barh(
                            y_position, 
                            width, 
                            left=start_pos,
                            height=0.8,
                            color=color,
                            alpha=0.8,
                            edgecolor='black',
                            linewidth=0.5
                        )
                
                y_labels.append(f"{chamber_type[:2]}-{chamber.name}")
                y_position += 1
        
        # Configure axes
        ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
        ax.set_ylim(-0.5, y_position - 0.5)
        
        # Format x-axis for time
        if self.timeline_hours <= 6:
            ax.xaxis.set_major_locator(HourLocator(interval=1))
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
        elif self.timeline_hours <= 24:
            ax.xaxis.set_major_locator(HourLocator(interval=3))
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
        else:
            ax.xaxis.set_major_locator(HourLocator(interval=12))
            ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
        
        ax.set_xlabel("Time", color='white')
        ax.set_ylabel("Chambers", color='white')
        ax.set_title(title, color='white')
        ax.tick_params(colors='white')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Set y-axis labels
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels)
        
        # Add legend for states
        if data_type == "state":
            self._add_state_legend(ax)
    
    def _get_chamber_history(self, chamber, start_time, end_time, data_type):
        """Get chamber state or status history for the given time range."""
        history = []
        
        # Get the appropriate history list
        if data_type == "state":
            transitions = getattr(chamber.state_manager, 'state_history', [])
            current_value = chamber.current_state.value if hasattr(chamber, 'current_state') else ChamberState.AVAILABLE_EMPTY.value
        else:
            transitions = getattr(chamber.state_manager, 'status_history', [])
            current_value = chamber.current_status.value if hasattr(chamber, 'current_status') else ""
        
        # If no history, show current state for entire period
        if not transitions:
            if current_value:
                history.append({
                    'state': current_value,
                    'start_time': start_time,
                    'end_time': end_time
                })
            return history
        
        # Process transitions
        current_start = start_time
        current_state = None
        
        for transition in transitions:
            if transition.timestamp >= start_time:
                # Add period before this transition
                if current_state:
                    history.append({
                        'state': current_state,
                        'start_time': current_start,
                        'end_time': min(transition.timestamp, end_time)
                    })
                
                current_state = transition.to_value
                current_start = transition.timestamp
                
                if transition.timestamp >= end_time:
                    break
        
        # Add final period to end_time
        if current_state and current_start < end_time:
            history.append({
                'state': current_state,
                'start_time': current_start,
                'end_time': end_time
            })
        
        return history
    
    def _add_state_legend(self, ax):
        """Add a legend showing state colors."""
        legend_elements = []
        for state, color in self.state_colors.items():
            if state != 'default':
                # Clean up state name for display
                display_name = state.replace('test ', '').replace(' (auto)', '').title()
                legend_elements.append(mpatches.Patch(color=color, label=display_name))
        
        if legend_elements:
            ax.legend(handles=legend_elements[:6], loc='upper right', 
                     fancybox=True, shadow=True, ncol=2, fontsize=8)
    
    def _update_recent_activity(self):
        """Update recent activity display."""
        self.activity_text.delete("1.0", "end")
        
        # Get recent state transitions from all chambers
        recent_activities = []
        chambers = self.app.get_chambers()
        
        for chamber in chambers:
            # Get recent state transitions
            for transition in chamber.state_manager.state_history[-5:]:  # Last 5 transitions
                recent_activities.append({
                    'chamber': chamber.name,
                    'type': 'state',
                    'transition': transition,
                    'timestamp': transition.timestamp
                })
            
            # Get recent status transitions
            for transition in chamber.state_manager.status_history[-5:]:
                recent_activities.append({
                    'chamber': chamber.name,
                    'type': 'status',
                    'transition': transition,
                    'timestamp': transition.timestamp
                })
        
        # Sort by timestamp (most recent first)
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Display recent activities
        for activity in recent_activities[:10]:  # Show last 10 activities
            chamber_name = activity['chamber']
            transition = activity['transition']
            time_str = transition.timestamp.strftime("%H:%M:%S")
            
            if activity['type'] == 'state':
                text = f"{time_str} - {chamber_name}: {transition.from_value} → {transition.to_value}\n"
            else:
                text = f"{time_str} - {chamber_name} status: {transition.from_value} → {transition.to_value}\n"
            
            self.activity_text.insert("end", text)
        
        if not recent_activities:
            self.activity_text.insert("end", "No recent activity")
