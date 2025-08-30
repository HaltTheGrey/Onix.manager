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
            values=["Count Overview", "Time Overview"],
            command=self._on_mode_change,
            width=150
        )
        self.mode_combo.pack(side="left", padx=(0, 10), pady=10)
        self.mode_combo.set("Count Overview")
        
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
        else:
            self.view_mode = "time"
        
        self.update_data()
        self.logger.info(f"Changed view mode to: {self.view_mode}")
    
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
        """Show list of chambers in a specific state."""
        # This would open a dialog showing chambers in the selected state
        # For now, just show a message
        ctk.messagebox.showinfo("Chambers by State", "Would show chambers in selected state")
    
    def _show_chambers_by_status(self, event):
        """Show list of chambers with a specific status."""
        # This would open a dialog showing chambers with the selected status
        ctk.messagebox.showinfo("Chambers by Status", "Would show chambers with selected status")
    
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
        """Update graphs with time data."""
        chambers = self.app.get_chambers()
        
        # Aggregate time spent in each state
        state_times = {}
        for chamber in chambers:
            chamber_stats = chamber.state_manager.get_state_statistics()
            for state, time_seconds in chamber_stats.items():
                state_times[state] = state_times.get(state, 0) + time_seconds
        
        # Update state graph
        self.state_ax.clear()
        
        if state_times:
            states = list(state_times.keys())
            times_hours = [time_seconds / 3600 for time_seconds in state_times.values()]
            
            display_states = [state.replace('test ', '').replace(' (auto)', '') for state in states]
            
            self.state_bars = self.state_ax.bar(display_states, times_hours, color='#2ca02c', alpha=0.8)
            self.state_ax.set_title("Time Spent in Each State", color='white')
            self.state_ax.set_ylabel("Hours", color='white')
            self.state_ax.tick_params(colors='white')
            
            plt.setp(self.state_ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, hours in zip(self.state_bars, times_hours):
                height = bar.get_height()
                self.state_ax.text(bar.get_x() + bar.get_width()/2., height + max(times_hours) * 0.01,
                                 f'{hours:.1f}h', ha='center', va='bottom', color='white')
        
        self.state_fig.tight_layout()
        self.state_canvas.draw()
        
        # Aggregate time spent in each status
        status_times = {}
        for chamber in chambers:
            chamber_stats = chamber.state_manager.get_status_statistics()
            for status, time_seconds in chamber_stats.items():
                status_times[status] = status_times.get(status, 0) + time_seconds
        
        # Update status graph
        self.status_ax.clear()
        
        if status_times:
            statuses = list(status_times.keys())
            times_hours = [time_seconds / 3600 for time_seconds in status_times.values()]
            
            colors = ['#ff7f0e'] * len(statuses)
            
            self.status_bars = self.status_ax.bar(statuses, times_hours, color=colors, alpha=0.8)
            self.status_ax.set_title("Time Spent in Status Issues", color='white')
            self.status_ax.set_ylabel("Hours", color='white')
            self.status_ax.tick_params(colors='white')
            
            plt.setp(self.status_ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, hours in zip(self.status_bars, times_hours):
                height = bar.get_height()
                self.status_ax.text(bar.get_x() + bar.get_width()/2., height + max(times_hours) * 0.01,
                                 f'{hours:.1f}h', ha='center', va='bottom', color='white')
        else:
            self.status_ax.text(0.5, 0.5, "No Status Time Data", 
                              transform=self.status_ax.transAxes,
                              ha='center', va='center', color='white', fontsize=14)
        
        self.status_fig.tight_layout()
        self.status_canvas.draw()
    
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
