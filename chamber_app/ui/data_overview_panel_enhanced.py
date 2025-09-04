# filepath: c:\Users\jessneug\onix#3\chamber_app\ui\data_overview_panel_enhanced.py
"""
Enhanced data overview panel with expandable graphs and improved readability.
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
import tkinter as tk

from ..core.chamber_state import ChamberState, ChamberStatus, ChamberType
from ..utils import get_logger


class DataOverviewPanel(ctk.CTkFrame):
    """Enhanced overview panel with expandable graphs and better visualization."""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        self.view_mode = "count"  # "count" or "time"
        
        # Extended timeline properties with more time ranges
        self.timeline_hours = 24  # Show last 24 hours by default
        self.extended_timeline_options = {
            "1h": 1, "6h": 6, "12h": 12, "24h": 24, 
            "2d": 48, "3d": 72, "7d": 168, "30d": 720
        }
        
        # Enhanced state colors for better readability
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
        
        # Track detail windows for expandable views
        self.detail_windows = {}
        
        # Pack to fill parent
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup UI
        self._setup_ui()
        
        # Initial data update
        self.update_data()
    
    def _setup_ui(self):
        """Setup the enhanced overview panel UI with better organization."""
        # Configure main grid - give more space to content
        self.grid_columnconfigure(1, weight=3)  # More weight to main content
        self.grid_columnconfigure(0, weight=1)  # Less weight to sidebar
        self.grid_rowconfigure(1, weight=1)
        
        # Header with enhanced controls
        self._create_enhanced_header()
        
        # Main content area with better organization
        self._create_enhanced_content_area()
        
        # Compact statistics sidebar
        self._create_compact_statistics_sidebar()
    
    def _create_enhanced_header(self):
        """Create enhanced header with more time range options and view details buttons."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(2, weight=1)
        
        # Title section
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        title_label = ctk.CTkLabel(title_frame, text="Chamber Overview", 
                                 font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(side="left", padx=5)
        
        # View mode selection
        mode_frame = ctk.CTkFrame(header_frame)
        mode_frame.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(mode_frame, text="View:").pack(side="left", padx=5)
        
        self.mode_selector = ctk.CTkSegmentedButton(
            mode_frame,
            values=["Count", "Timeline"],
            command=self._on_view_mode_change
        )
        self.mode_selector.set("Count")
        self.mode_selector.pack(side="left", padx=5)
        
        # Enhanced time range selection for timeline mode
        self.time_frame = ctk.CTkFrame(header_frame)
        self.time_frame.grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        ctk.CTkLabel(self.time_frame, text="Time Range:").pack(side="left", padx=5)
        
        self.time_selector = ctk.CTkSegmentedButton(
            self.time_frame,
            values=list(self.extended_timeline_options.keys()),
            command=self._on_time_range_change
        )
        self.time_selector.set("24h")
        self.time_selector.pack(side="left", padx=5)
        
        # Initially hide time controls
        self.time_frame.grid_remove()
    
    def _create_enhanced_content_area(self):
        """Create main content area with larger graphs and expandable views."""
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(2, weight=1)
        
        # Create expandable graph sections
        self._create_expandable_state_section()
        self._create_expandable_status_section() 
        self._create_expandable_activity_section()
    
    def _create_expandable_state_section(self):
        """Create expandable chamber state visualization section."""
        state_section = ctk.CTkFrame(self.content_frame)
        state_section.grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
        state_section.grid_columnconfigure(0, weight=1)
        state_section.grid_rowconfigure(1, weight=1)
        
        # Header with expand button
        state_header = ctk.CTkFrame(state_section)
        state_header.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        state_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(state_header, text="Chamber States", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
        
        self.state_expand_btn = ctk.CTkButton(state_header, text="📊 View Details", width=100,
                                            command=self._expand_state_graph)
        self.state_expand_btn.grid(row=0, column=1, sticky="e", padx=5)
        
        # Graph area
        self.state_graph_frame = ctk.CTkFrame(state_section)
        self.state_graph_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        # Create matplotlib figure for states
        self.state_fig, self.state_ax = plt.subplots(figsize=(8, 3))
        self.state_fig.patch.set_facecolor('#212121')
        self.state_ax.set_facecolor('#212121')
        
        self.state_canvas = FigureCanvasTkAgg(self.state_fig, self.state_graph_frame)
        self.state_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _create_expandable_status_section(self):
        """Create expandable chamber status visualization section."""
        status_section = ctk.CTkFrame(self.content_frame)
        status_section.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        status_section.grid_columnconfigure(0, weight=1)
        status_section.grid_rowconfigure(1, weight=1)
        
        # Header with expand button
        status_header = ctk.CTkFrame(status_section)
        status_header.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        status_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(status_header, text="Chamber Status", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
        
        self.status_expand_btn = ctk.CTkButton(status_header, text="📊 View Details", width=100,
                                             command=self._expand_status_graph)
        self.status_expand_btn.grid(row=0, column=1, sticky="e", padx=5)
        
        # Graph area
        self.status_graph_frame = ctk.CTkFrame(status_section)
        self.status_graph_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        # Create matplotlib figure for status
        self.status_fig, self.status_ax = plt.subplots(figsize=(8, 3))
        self.status_fig.patch.set_facecolor('#212121')
        self.status_ax.set_facecolor('#212121')
        
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, self.status_graph_frame)
        self.status_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _create_expandable_activity_section(self):
        """Create expandable recent activity section."""
        activity_section = ctk.CTkFrame(self.content_frame)
        activity_section.grid(row=2, column=0, sticky="nsew", padx=5, pady=2)
        activity_section.grid_columnconfigure(0, weight=1)
        activity_section.grid_rowconfigure(1, weight=1)
        
        # Header with expand button
        activity_header = ctk.CTkFrame(activity_section)
        activity_header.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        activity_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(activity_header, text="Recent Activity", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=5)
        
        self.activity_expand_btn = ctk.CTkButton(activity_header, text="📋 View Details", width=100,
                                               command=self._expand_activity_view)
        self.activity_expand_btn.grid(row=0, column=1, sticky="e", padx=5)
        
        # Activity display area
        self.activity_frame = ctk.CTkScrollableFrame(activity_section, height=120)
        self.activity_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
    
    def _create_compact_statistics_sidebar(self):
        """Create compact statistics sidebar."""
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Header
        stats_header = ctk.CTkLabel(self.stats_frame, text="Quick Stats", 
                                  font=ctk.CTkFont(size=14, weight="bold"))
        stats_header.pack(pady=10)
        
        # Stats display
        self.stats_display = ctk.CTkFrame(self.stats_frame)
        self.stats_display.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _expand_state_graph(self):
        """Create expanded window for detailed state visualization."""
        if "state" in self.detail_windows:
            # Bring existing window to front
            self.detail_windows["state"].lift()
            return
        
        # Create new detail window
        detail_window = tk.Toplevel(self)
        detail_window.title("Chamber States - Detailed View")
        detail_window.geometry("1000x600")
        detail_window.configure(bg='#212121')
        
        # Create larger matplotlib figure
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#212121')
        ax.set_facecolor('#212121')
        
        # Enhanced visualization with more detail
        self._create_detailed_state_graph(ax)
        
        canvas = FigureCanvasTkAgg(fig, detail_window)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Store reference and setup cleanup
        self.detail_windows["state"] = detail_window
        detail_window.protocol("WM_DELETE_WINDOW", lambda: self._close_detail_window("state"))
    
    def _expand_status_graph(self):
        """Create expanded window for detailed status visualization."""
        if "status" in self.detail_windows:
            self.detail_windows["status"].lift()
            return
        
        detail_window = tk.Toplevel(self)
        detail_window.title("Chamber Status - Detailed View")
        detail_window.geometry("1000x600")
        detail_window.configure(bg='#212121')
        
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#212121')
        ax.set_facecolor('#212121')
        
        self._create_detailed_status_graph(ax)
        
        canvas = FigureCanvasTkAgg(fig, detail_window)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.detail_windows["status"] = detail_window
        detail_window.protocol("WM_DELETE_WINDOW", lambda: self._close_detail_window("status"))
    
    def _expand_activity_view(self):
        """Create expanded window for detailed activity view."""
        if "activity" in self.detail_windows:
            self.detail_windows["activity"].lift()
            return
        
        detail_window = tk.Toplevel(self)
        detail_window.title("Recent Activity - Detailed View")
        detail_window.geometry("800x600")
        detail_window.configure(bg='#212121')
        
        # Create enhanced activity view with filtering
        self._create_detailed_activity_view(detail_window)
        
        self.detail_windows["activity"] = detail_window
        detail_window.protocol("WM_DELETE_WINDOW", lambda: self._close_detail_window("activity"))
    
    def _close_detail_window(self, window_type):
        """Close and cleanup detail window."""
        if window_type in self.detail_windows:
            self.detail_windows[window_type].destroy()
            del self.detail_windows[window_type]
    
    def _create_detailed_state_graph(self, ax):
        """Create detailed state graph with enhanced features."""
        # Get chamber data
        chambers = self.app.data_manager.get_all_chambers()
        
        if self.view_mode == "count":
            self._create_detailed_count_state_graph(ax, chambers)
        else:
            self._create_detailed_timeline_state_graph(ax, chambers)
    
    def _create_detailed_status_graph(self, ax):
        """Create detailed status graph with enhanced features.""" 
        chambers = self.app.data_manager.get_all_chambers()
        
        if self.view_mode == "count":
            self._create_detailed_count_status_graph(ax, chambers)
        else:
            self._create_detailed_timeline_status_graph(ax, chambers)
    
    def _create_detailed_activity_view(self, parent):
        """Create detailed activity view with filtering and search."""
        # Header with search and filters
        header_frame = ctk.CTkFrame(parent)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Search
        search_frame = ctk.CTkFrame(header_frame)
        search_frame.pack(side="left", padx=5)
        
        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Filter activities...")
        search_entry.pack(side="left", padx=5)
        
        # Filters
        filter_frame = ctk.CTkFrame(header_frame)
        filter_frame.pack(side="right", padx=5)
        
        ctk.CTkLabel(filter_frame, text="Type:").pack(side="left", padx=5)
        type_filter = ctk.CTkComboBox(filter_frame, values=["All", "State Changes", "Status Updates", "Alerts"])
        type_filter.set("All")
        type_filter.pack(side="left", padx=5)
        
        # Activity list with enhanced display
        activity_frame = ctk.CTkScrollableFrame(parent)
        activity_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Populate with recent activities
        self._populate_detailed_activity_list(activity_frame)
    
    def _populate_detailed_activity_list(self, parent):
        """Populate detailed activity list."""
        # Get recent activities (mock data for now)
        activities = [
            {"time": "2024-01-15 14:30", "chamber": "TVAC-001", "event": "State changed to TEST_NOMINAL", "type": "State Change"},
            {"time": "2024-01-15 14:25", "chamber": "HASS-002", "event": "Test started", "type": "Status Update"},
            {"time": "2024-01-15 14:20", "chamber": "THERMAL-001", "event": "Temperature alert", "type": "Alert"},
            {"time": "2024-01-15 14:15", "chamber": "TVAC-003", "event": "Setup completed", "type": "State Change"},
        ]
        
        for i, activity in enumerate(activities):
            activity_item = ctk.CTkFrame(parent)
            activity_item.pack(fill="x", padx=5, pady=2)
            
            # Time
            time_label = ctk.CTkLabel(activity_item, text=activity["time"], width=120)
            time_label.pack(side="left", padx=5)
            
            # Chamber
            chamber_label = ctk.CTkLabel(activity_item, text=activity["chamber"], width=100)
            chamber_label.pack(side="left", padx=5)
            
            # Event
            event_label = ctk.CTkLabel(activity_item, text=activity["event"])
            event_label.pack(side="left", padx=5, fill="x", expand=True)
            
            # Type badge
            type_color = {"State Change": "#2196F3", "Status Update": "#4CAF50", "Alert": "#FF5722"}
            type_label = ctk.CTkLabel(activity_item, text=activity["type"], 
                                    fg_color=type_color.get(activity["type"], "#607D8B"),
                                    corner_radius=10, width=100)
            type_label.pack(side="right", padx=5)
    
    def _on_view_mode_change(self, value):
        """Handle view mode change."""
        self.view_mode = value.lower()
        
        if self.view_mode == "timeline":
            self.time_frame.grid()
        else:
            self.time_frame.grid_remove()
        
        self.update_data()
    
    def _on_time_range_change(self, value):
        """Handle time range change."""
        self.timeline_hours = self.extended_timeline_options[value]
        if self.view_mode == "timeline":
            self.update_data()
    
    def update_data(self):
        """Update all visualizations with current data."""
        try:
            # Get current chamber statistics
            stats = self._calculate_chamber_stats()
            
            # Update main graphs
            if self.view_mode == "count":
                self._update_count_graphs(stats)
            else:
                self._update_timeline_graphs()
            
            # Update statistics sidebar
            self._update_statistics_display(stats)
            
            # Update recent activity
            self._update_recent_activity()
            
        except Exception as e:
            self.logger.error(f"Error updating overview data: {e}")
    
    def _calculate_chamber_stats(self):
        """Calculate chamber statistics."""
        chambers = self.app.data_manager.get_all_chambers()
        
        stats = {
            'total_chambers': len(chambers),
            'by_type': {},
            'by_state': {},
            'by_status': {}
        }
        
        for chamber in chambers:
            # Count by type
            chamber_type = chamber.get('type', 'Unknown')
            stats['by_type'][chamber_type] = stats['by_type'].get(chamber_type, 0) + 1
            
            # Count by state
            chamber_state = chamber.get('state', 'Unknown')
            stats['by_state'][chamber_state] = stats['by_state'].get(chamber_state, 0) + 1
            
            # Count by status
            chamber_status = chamber.get('status', 'Unknown')
            stats['by_status'][chamber_status] = stats['by_status'].get(chamber_status, 0) + 1
        
        return stats
    
    def _update_count_graphs(self, stats):
        """Update count-based graphs."""
        # Update state graph
        self._update_state_count_graph(stats['by_state'])
        
        # Update status graph  
        self._update_status_count_graph(stats['by_status'])
    
    def _update_state_count_graph(self, state_counts):
        """Update state count graph."""
        self.state_ax.clear()
        
        if not state_counts:
            self.state_ax.text(0.5, 0.5, 'No chamber data available', 
                             ha='center', va='center', transform=self.state_ax.transAxes,
                             color='white', fontsize=12)
        else:
            states = list(state_counts.keys())
            counts = list(state_counts.values())
            colors = [self.state_colors.get(state, self.state_colors['default']) for state in states]
            
            bars = self.state_ax.bar(states, counts, color=colors, alpha=0.8)
            
            # Styling
            self.state_ax.set_title('Chambers by State', color='white', fontsize=12, pad=10)
            self.state_ax.set_ylabel('Count', color='white')
            self.state_ax.tick_params(colors='white')
            
            # Rotate x-axis labels for better readability
            self.state_ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.state_ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                 f'{count}', ha='center', va='bottom', color='white')
        
        self.state_fig.tight_layout()
        self.state_canvas.draw()
    
    def _update_status_count_graph(self, status_counts):
        """Update status count graph."""
        self.status_ax.clear()
        
        if not status_counts:
            self.status_ax.text(0.5, 0.5, 'No chamber data available',
                              ha='center', va='center', transform=self.status_ax.transAxes,
                              color='white', fontsize=12)
        else:
            statuses = list(status_counts.keys())
            counts = list(status_counts.values())
            
            # Use pie chart for status distribution
            colors = plt.cm.Set3(np.linspace(0, 1, len(statuses)))
            wedges, texts, autotexts = self.status_ax.pie(counts, labels=statuses, colors=colors,
                                                        autopct='%1.1f%%', startangle=90)
            
            # Styling
            self.status_ax.set_title('Chambers by Status', color='white', fontsize=12, pad=10)
            for text in texts:
                text.set_color('white')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        self.status_fig.tight_layout()
        self.status_canvas.draw()
    
    def _update_timeline_graphs(self):
        """Update timeline-based graphs."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.timeline_hours)
        
        chambers = self.app.data_manager.get_all_chambers()
        
        # Update state timeline
        self._update_state_timeline_graph(chambers, start_time, end_time)
        
        # Update status timeline
        self._update_status_timeline_graph(chambers, start_time, end_time)
    
    def _update_state_timeline_graph(self, chambers, start_time, end_time):
        """Update state timeline graph."""
        self.state_ax.clear()
        
        # Group chambers by type for timeline display
        chambers_by_type = {}
        for chamber in chambers:
            chamber_type = chamber.get('type', 'Unknown')
            if chamber_type not in chambers_by_type:
                chambers_by_type[chamber_type] = []
            chambers_by_type[chamber_type].append(chamber)
        
        y_pos = 0
        y_labels = []
        
        for chamber_type, type_chambers in chambers_by_type.items():
            for chamber in type_chambers:
                chamber_id = chamber.get('id', 'Unknown')
                y_labels.append(f"{chamber_type}-{chamber_id}")
                
                # Get chamber history for this time period
                history = self._get_chamber_history(chamber, start_time, end_time, 'state')
                
                # Plot state periods as horizontal bars
                for period in history:
                    period_start = max(period['start_time'], start_time)
                    period_end = min(period.get('end_time', end_time), end_time)
                    
                    if period_start < period_end:
                        duration = (period_end - period_start).total_seconds() / 3600
                        color = self.state_colors.get(period['value'], self.state_colors['default'])
                        
                        self.state_ax.barh(y_pos, duration, 
                                         left=mdates.date2num(period_start),
                                         height=0.8, color=color, alpha=0.8)
                
                y_pos += 1
        
        # Styling
        if y_labels:
            self.state_ax.set_yticks(range(len(y_labels)))
            self.state_ax.set_yticklabels(y_labels, color='white')
            self.state_ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
            
            # Format x-axis with proper time labels
            if self.timeline_hours <= 24:
                self.state_ax.xaxis.set_major_locator(HourLocator(interval=max(1, self.timeline_hours // 8)))
                self.state_ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            else:
                self.state_ax.xaxis.set_major_locator(HourLocator(interval=max(12, self.timeline_hours // 8)))
                self.state_ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
        
        self.state_ax.set_title(f'Chamber States Timeline ({self.timeline_hours}h)', 
                              color='white', fontsize=12, pad=10)
        self.state_ax.set_xlabel('Time', color='white')
        self.state_ax.tick_params(colors='white')
        
        self.state_fig.tight_layout()
        self.state_canvas.draw()
    
    def _update_status_timeline_graph(self, chambers, start_time, end_time):
        """Update status timeline graph."""
        self.status_ax.clear()
        
        # Similar implementation to state timeline but for status
        y_pos = 0
        y_labels = []
        
        for chamber in chambers:
            chamber_id = chamber.get('id', 'Unknown')
            chamber_type = chamber.get('type', 'Unknown')
            y_labels.append(f"{chamber_type}-{chamber_id}")
            
            # Get chamber history for status changes
            history = self._get_chamber_history(chamber, start_time, end_time, 'status')
            
            # Plot status periods
            for period in history:
                period_start = max(period['start_time'], start_time)
                period_end = min(period.get('end_time', end_time), end_time)
                
                if period_start < period_end:
                    duration = (period_end - period_start).total_seconds() / 3600
                    
                    # Use different colors for different statuses
                    status_colors = {
                        'OPERATIONAL': '#4CAF50',
                        'MAINTENANCE': '#FF9800', 
                        'ERROR': '#F44336',
                        'OFFLINE': '#9E9E9E'
                    }
                    color = status_colors.get(period['value'], '#607D8B')
                    
                    self.status_ax.barh(y_pos, duration,
                                      left=mdates.date2num(period_start),
                                      height=0.8, color=color, alpha=0.8)
            
            y_pos += 1
        
        # Styling
        if y_labels:
            self.status_ax.set_yticks(range(len(y_labels)))
            self.status_ax.set_yticklabels(y_labels, color='white')
            self.status_ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
            
            # Format x-axis
            if self.timeline_hours <= 24:
                self.status_ax.xaxis.set_major_locator(HourLocator(interval=max(1, self.timeline_hours // 8)))
                self.status_ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            else:
                self.status_ax.xaxis.set_major_locator(HourLocator(interval=max(12, self.timeline_hours // 8)))
                self.status_ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
        
        self.status_ax.set_title(f'Chamber Status Timeline ({self.timeline_hours}h)',
                               color='white', fontsize=12, pad=10)
        self.status_ax.set_xlabel('Time', color='white')
        self.status_ax.tick_params(colors='white')
        
        self.status_fig.tight_layout()
        self.status_canvas.draw()
    
    def _get_chamber_history(self, chamber, start_time, end_time, data_type):
        """Get chamber history for the specified time period."""
        # Mock implementation - in real app this would query the database
        chamber_id = chamber.get('id', 'Unknown')
        current_state = chamber.get('state', ChamberState.AVAILABLE_EMPTY.value)
        current_status = chamber.get('status', 'OPERATIONAL')
        
        if data_type == 'state':
            return [{
                'start_time': start_time,
                'end_time': end_time,
                'value': current_state
            }]
        else:
            return [{
                'start_time': start_time,
                'end_time': end_time,
                'value': current_status
            }]
    
    def _update_statistics_display(self, stats):
        """Update the statistics sidebar display."""
        # Clear existing widgets
        for widget in self.stats_display.winfo_children():
            widget.destroy()
        
        # Total chambers
        total_frame = ctk.CTkFrame(self.stats_display)
        total_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(total_frame, text="Total Chambers", 
                    font=ctk.CTkFont(weight="bold")).pack()
        ctk.CTkLabel(total_frame, text=str(stats['total_chambers']), 
                    font=ctk.CTkFont(size=20)).pack()
        
        # By type
        if stats['by_type']:
            type_frame = ctk.CTkFrame(self.stats_display)
            type_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(type_frame, text="By Type", 
                        font=ctk.CTkFont(weight="bold")).pack(pady=(5,0))
            
            for chamber_type, count in stats['by_type'].items():
                type_item = ctk.CTkFrame(type_frame)
                type_item.pack(fill="x", padx=5, pady=2)
                
                ctk.CTkLabel(type_item, text=chamber_type).pack(side="left")
                ctk.CTkLabel(type_item, text=str(count)).pack(side="right")
    
    def _update_recent_activity(self):
        """Update recent activity display."""
        # Clear existing widgets
        for widget in self.activity_frame.winfo_children():
            widget.destroy()
        
        # Mock recent activities
        activities = [
            "TVAC-001: State changed to TEST_NOMINAL",
            "HASS-002: Test started",
            "THERMAL-001: Temperature alert",
            "TVAC-003: Setup completed"
        ]
        
        for activity in activities:
            activity_label = ctk.CTkLabel(self.activity_frame, text=activity, 
                                        anchor="w", justify="left")
            activity_label.pack(fill="x", padx=5, pady=2)
    
    def _create_detailed_count_state_graph(self, ax, chambers):
        """Create detailed count-based state graph."""
        # Enhanced version of the count graph with more details
        state_counts = {}
        for chamber in chambers:
            state = chamber.get('state', 'Unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        if state_counts:
            states = list(state_counts.keys())
            counts = list(state_counts.values())
            colors = [self.state_colors.get(state, self.state_colors['default']) for state in states]
            
            bars = ax.bar(states, counts, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
            
            # Enhanced styling for detailed view
            ax.set_title('Chamber States Distribution - Detailed View', 
                        color='white', fontsize=16, pad=20)
            ax.set_ylabel('Number of Chambers', color='white', fontsize=12)
            ax.tick_params(colors='white', labelsize=10)
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels and percentages
            total = sum(counts)
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                percentage = (count / total) * 100
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}\n({percentage:.1f}%)', 
                       ha='center', va='bottom', color='white', fontweight='bold')
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3, color='white')
            ax.set_axisbelow(True)
    
    def _create_detailed_count_status_graph(self, ax, chambers):
        """Create detailed count-based status graph."""
        status_counts = {}
        for chamber in chambers:
            status = chamber.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            statuses = list(status_counts.keys())
            counts = list(status_counts.values())
            
            # Enhanced pie chart with better styling
            colors = plt.cm.Set3(np.linspace(0, 1, len(statuses)))
            wedges, texts, autotexts = ax.pie(counts, labels=statuses, colors=colors,
                                            autopct='%1.1f%%', startangle=90,
                                            textprops={'color': 'white', 'fontsize': 12})
            
            ax.set_title('Chamber Status Distribution - Detailed View', 
                        color='white', fontsize=16, pad=20)
            
            # Enhanced text styling
            for text in texts:
                text.set_color('white')
                text.set_fontsize(12)
                text.set_fontweight('bold')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)
    
    def _create_detailed_timeline_state_graph(self, ax, chambers):
        """Create detailed timeline state graph."""
        # Enhanced version with more detailed timeline visualization
        # Implementation similar to _update_state_timeline_graph but with enhanced features
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.timeline_hours)
        
        chambers_by_type = {}
        for chamber in chambers:
            chamber_type = chamber.get('type', 'Unknown')
            if chamber_type not in chambers_by_type:
                chambers_by_type[chamber_type] = []
            chambers_by_type[chamber_type].append(chamber)
        
        y_pos = 0
        y_labels = []
        
        for chamber_type, type_chambers in chambers_by_type.items():
            for chamber in type_chambers:
                chamber_id = chamber.get('id', 'Unknown')
                y_labels.append(f"{chamber_type}-{chamber_id}")
                
                history = self._get_chamber_history(chamber, start_time, end_time, 'state')
                
                for period in history:
                    period_start = max(period['start_time'], start_time)
                    period_end = min(period.get('end_time', end_time), end_time)
                    
                    if period_start < period_end:
                        duration = (period_end - period_start).total_seconds() / 3600
                        color = self.state_colors.get(period['value'], self.state_colors['default'])
                        
                        bar = ax.barh(y_pos, duration, 
                                    left=mdates.date2num(period_start),
                                    height=0.8, color=color, alpha=0.8,
                                    edgecolor='white', linewidth=0.5)
                
                y_pos += 1
        
        # Enhanced styling for detailed view
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels, color='white', fontsize=10)
            ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
            
            # Better time formatting
            if self.timeline_hours <= 24:
                ax.xaxis.set_major_locator(HourLocator(interval=max(1, self.timeline_hours // 12)))
                ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            else:
                ax.xaxis.set_major_locator(HourLocator(interval=max(6, self.timeline_hours // 12)))
                ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
            
            # Add grid
            ax.grid(True, alpha=0.3, color='white', axis='x')
            ax.set_axisbelow(True)
        
        ax.set_title(f'Chamber States Timeline - Detailed View ({self.timeline_hours}h)', 
                    color='white', fontsize=16, pad=20)
        ax.set_xlabel('Time', color='white', fontsize=12)
        ax.tick_params(colors='white')
    
    def _create_detailed_timeline_status_graph(self, ax, chambers):
        """Create detailed timeline status graph."""
        # Similar enhanced implementation for status timeline
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.timeline_hours)
        
        y_pos = 0
        y_labels = []
        
        for chamber in chambers:
            chamber_id = chamber.get('id', 'Unknown')
            chamber_type = chamber.get('type', 'Unknown')
            y_labels.append(f"{chamber_type}-{chamber_id}")
            
            history = self._get_chamber_history(chamber, start_time, end_time, 'status')
            
            for period in history:
                period_start = max(period['start_time'], start_time)
                period_end = min(period.get('end_time', end_time), end_time)
                
                if period_start < period_end:
                    duration = (period_end - period_start).total_seconds() / 3600
                    
                    status_colors = {
                        'OPERATIONAL': '#4CAF50',
                        'MAINTENANCE': '#FF9800', 
                        'ERROR': '#F44336',
                        'OFFLINE': '#9E9E9E'
                    }
                    color = status_colors.get(period['value'], '#607D8B')
                    
                    ax.barh(y_pos, duration,
                          left=mdates.date2num(period_start),
                          height=0.8, color=color, alpha=0.8,
                          edgecolor='white', linewidth=0.5)
            
            y_pos += 1
        
        # Enhanced styling
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels, color='white', fontsize=10)
            ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
            
            if self.timeline_hours <= 24:
                ax.xaxis.set_major_locator(HourLocator(interval=max(1, self.timeline_hours // 12)))
                ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            else:
                ax.xaxis.set_major_locator(HourLocator(interval=max(6, self.timeline_hours // 12)))
                ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
            
            ax.grid(True, alpha=0.3, color='white', axis='x')
            ax.set_axisbelow(True)
        
        ax.set_title(f'Chamber Status Timeline - Detailed View ({self.timeline_hours}h)',
                   color='white', fontsize=16, pad=20)
        ax.set_xlabel('Time', color='white', fontsize=12)
        ax.tick_params(colors='white')
