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
        
        # Extended timeline properties with more time ranges
        self.timeline_hours = 24  # Show last 24 hours by default
        self.extended_timeline_options = {
            "1h": 1, "6h": 6, "12h": 12, "24h": 24, 
            "2d": 48, "3d": 72, "7d": 168, "30d": 720
        }
        self.chamber_graphs = {}  # Store graph references by type
        self.graph_collapsed = {"TVAC": False, "HASS": False, "THERMAL": False}
        
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
        }
        
        # Track detail windows
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
        title_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Chamber Overview",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=(10, 5))
        
        # Quick stats in header
        self.header_stats_label = ctk.CTkLabel(
            title_frame,
            text="Loading...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.header_stats_label.pack(side="left", padx=(10, 10))
        
        # Enhanced controls section
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=3, sticky="e", padx=10, pady=10)
        
        # View mode toggle
        mode_label = ctk.CTkLabel(controls_frame, text="View:")
        mode_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        self.mode_combo = ctk.CTkComboBox(
            controls_frame,
            values=["Count Overview", "Timeline View"],
            command=self._on_mode_change,
            width=130
        )
        self.mode_combo.grid(row=0, column=1, padx=5, pady=5)
        self.mode_combo.set("Count Overview")
        
        # Extended timeline hours control
        self.hours_label = ctk.CTkLabel(controls_frame, text="Range:")
        self.hours_label.grid(row=0, column=2, padx=(15, 5), pady=5)
        
        self.hours_combo = ctk.CTkComboBox(
            controls_frame,
            values=list(self.extended_timeline_options.keys()),
            command=self._on_hours_change,
            width=80
        )
        self.hours_combo.grid(row=0, column=3, padx=5, pady=5)
        self.hours_combo.set("24h")
        
        # Initially hide timeline controls
        self.hours_label.grid_remove()
        self.hours_combo.grid_remove()
        
        # Action buttons
        action_frame = ctk.CTkFrame(controls_frame)
        action_frame.grid(row=0, column=4, padx=(15, 10), pady=5)
        
        refresh_btn = ctk.CTkButton(
            action_frame,
            text="🔄",
            command=self.update_data,
            width=40,
            height=32
        )
        refresh_btn.pack(side="left", padx=(5, 2))
        
        self.expand_state_btn = ctk.CTkButton(
            action_frame,
            text="📊 States",
            command=self._expand_state_graph,
            width=80,
            height=32
        )
        self.expand_state_btn.pack(side="left", padx=2)
        
        self.expand_status_btn = ctk.CTkButton(
            action_frame,
            text="⚠️ Status",
            command=self._expand_status_graph,
            width=80,
            height=32
        )
        self.expand_status_btn.pack(side="left", padx=2)
    
    def _create_enhanced_content_area(self):
        """Create enhanced main content area with larger, more readable graphs."""
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 5), pady=(0, 5))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Enhanced state graph with larger size
        self.state_graph_frame = ctk.CTkFrame(content_frame)
        self.state_graph_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # State graph header with expand button
        state_header = ctk.CTkFrame(self.state_graph_frame)
        state_header.pack(fill="x", padx=10, pady=(10, 5))
        
        state_title = ctk.CTkLabel(
            state_header,
            text="Chamber States Distribution",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        state_title.pack(side="left")
        
        state_expand_btn = ctk.CTkButton(
            state_header,
            text="🔍 View Details",
            command=self._expand_state_graph,
            width=100,
            height=28
        )
        state_expand_btn.pack(side="right", padx=(10, 0))
        
        # Create larger matplotlib figure for state graph
        self.state_fig, self.state_ax = plt.subplots(figsize=(12, 5))  # Larger size
        self.state_fig.patch.set_facecolor('#2b2b2b')
        self.state_ax.set_facecolor('#2b2b2b')
        
        self.state_canvas = FigureCanvasTkAgg(self.state_fig, self.state_graph_frame)
        self.state_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Enhanced status graph with larger size
        self.status_graph_frame = ctk.CTkFrame(content_frame)
        self.status_graph_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Status graph header with expand button
        status_header = ctk.CTkFrame(self.status_graph_frame)
        status_header.pack(fill="x", padx=10, pady=(10, 5))
        
        status_title = ctk.CTkLabel(
            status_header,
            text="Chamber Status Issues",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.pack(side="left")
        
        status_expand_btn = ctk.CTkButton(
            status_header,
            text="🔍 View Details",
            command=self._expand_status_graph,
            width=100,
            height=28
        )
        status_expand_btn.pack(side="right", padx=(10, 0))
        
        # Create larger matplotlib figure for status graph
        self.status_fig, self.status_ax = plt.subplots(figsize=(12, 5))  # Larger size
        self.status_fig.patch.set_facecolor('#2b2b2b')
        self.status_ax.set_facecolor('#2b2b2b')
        
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, self.status_graph_frame)
        self.status_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Bind double-click events
        self.state_canvas.mpl_connect('button_press_event', self._on_state_graph_click)
        self.status_canvas.mpl_connect('button_press_event', self._on_status_graph_click)
    
    def _create_compact_statistics_sidebar(self):
        """Create a more compact statistics sidebar to give more room to graphs."""
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5))
        stats_frame.configure(width=200)  # Reduced from 250
        stats_frame.grid_propagate(False)
        
        # Statistics title
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="Live Stats",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_title.pack(pady=(10, 10))
        
        # Compact overall stats
        self.overall_stats_frame = ctk.CTkFrame(stats_frame)
        self.overall_stats_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        overall_title = ctk.CTkLabel(
            self.overall_stats_frame,
            text="📊 Overview",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        overall_title.pack(pady=(8, 5))
        
        self.total_chambers_label = ctk.CTkLabel(
            self.overall_stats_frame, 
            text="Chambers: 0",
            font=ctk.CTkFont(size=11)
        )
        self.total_chambers_label.pack(pady=1)
        
        self.connected_label = ctk.CTkLabel(
            self.overall_stats_frame, 
            text="Connected: 0",
            font=ctk.CTkFont(size=11)
        )
        self.connected_label.pack(pady=1)
        
        self.active_work_label = ctk.CTkLabel(
            self.overall_stats_frame, 
            text="Active WR: 0",
            font=ctk.CTkFont(size=11)
        )
        self.active_work_label.pack(pady=(1, 8))
        
        # Compact type stats
        self.type_stats_frame = ctk.CTkFrame(stats_frame)
        self.type_stats_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        type_title = ctk.CTkLabel(
            self.type_stats_frame,
            text="🏭 By Type",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        type_title.pack(pady=(8, 5))
        
        self.type_labels = {}
        for chamber_type in ["TVAC", "HASS", "THERMAL"]:
            label = ctk.CTkLabel(
                self.type_stats_frame, 
                text=f"{chamber_type}: 0",
                font=ctk.CTkFont(size=11)
            )
            label.pack(pady=1)
            self.type_labels[chamber_type] = label
        
        # Compact recent activity with expand button
        activity_header = ctk.CTkFrame(stats_frame)
        activity_header.pack(fill="x", padx=8, pady=(8, 0))
        
        activity_title = ctk.CTkLabel(
            activity_header,
            text="📈 Activity",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        activity_title.pack(side="left", pady=5)
        
        activity_expand_btn = ctk.CTkButton(
            activity_header,
            text="⤴",
            command=self._expand_activity_view,
            width=30,
            height=24,
            font=ctk.CTkFont(size=12)
        )
        activity_expand_btn.pack(side="right", pady=5)
        
        self.activity_frame = ctk.CTkFrame(stats_frame)
        self.activity_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        
        self.activity_text = ctk.CTkTextbox(
            self.activity_frame,
            height=120,  # Reduced height
            wrap="word",
            font=ctk.CTkFont(size=10)
        )
        self.activity_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _on_mode_change(self, value):
        """Handle view mode change with enhanced controls."""
        if value == "Count Overview":
            self.view_mode = "count"
            self.hours_label.grid_remove()
            self.hours_combo.grid_remove()
        else:
            self.view_mode = "time"
            self.hours_label.grid()
            self.hours_combo.grid()
        
        self.update_data()
        self.logger.info(f"Changed view mode to: {self.view_mode}")
    
    def _on_hours_change(self, value):
        """Handle timeline hours change with extended options."""
        self.timeline_hours = self.extended_timeline_options.get(value, 24)
        if self.view_mode == "time":
            self.update_data()
        self.logger.info(f"Changed timeline hours to: {self.timeline_hours}")
        
    def _expand_state_graph(self):
        """Open state graph in a detailed, expandable window."""
        if "state_detail" in self.detail_windows and self.detail_windows["state_detail"].winfo_exists():
            self.detail_windows["state_detail"].lift()
            return
            
        # Create detailed state graph window
        detail_window = ctk.CTkToplevel(self)
        detail_window.title("Chamber States - Detailed View")
        detail_window.geometry("1000x700")
        detail_window.transient(self.winfo_toplevel())
        
        # Center the window
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (700 // 2)
        detail_window.geometry(f"1000x700+{x}+{y}")
        
        self.detail_windows["state_detail"] = detail_window
        
        # Create detailed content
        self._create_detailed_state_view(detail_window)
    
    def _expand_status_graph(self):
        """Open status graph in a detailed, expandable window."""
        if "status_detail" in self.detail_windows and self.detail_windows["status_detail"].winfo_exists():
            self.detail_windows["status_detail"].lift()
            return
            
        # Create detailed status graph window
        detail_window = ctk.CTkToplevel(self)
        detail_window.title("Chamber Status Issues - Detailed View")
        detail_window.geometry("1000x700")
        detail_window.transient(self.winfo_toplevel())
        
        # Center the window
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (700 // 2)
        detail_window.geometry(f"1000x700+{x}+{y}")
        
        self.detail_windows["status_detail"] = detail_window
        
        # Create detailed content
        self._create_detailed_status_view(detail_window)
    
    def _expand_activity_view(self):
        """Open activity log in a detailed, expandable window."""
        if "activity_detail" in self.detail_windows and self.detail_windows["activity_detail"].winfo_exists():
            self.detail_windows["activity_detail"].lift()
            return
            
        # Create detailed activity window
        detail_window = ctk.CTkToplevel(self)
        detail_window.title("Recent Activity - Detailed View")
        detail_window.geometry("800x600")
        detail_window.transient(self.winfo_toplevel())
        
        # Center the window
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (600 // 2)
        detail_window.geometry(f"800x600+{x}+{y}")
        
        self.detail_windows["activity_detail"] = detail_window
        
        # Create detailed content
        self._create_detailed_activity_view(detail_window)
        
    def _create_detailed_state_view(self, window):
        """Create detailed state graph view with enhanced features."""
        # Header
        header_frame = ctk.CTkFrame(window)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Chamber States - Detailed Analysis",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Time range controls for detailed view
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        range_label = ctk.CTkLabel(controls_frame, text="Time Range:")
        range_label.pack(side="left", padx=(10, 5))
        
        detail_hours_combo = ctk.CTkComboBox(
            controls_frame,
            values=list(self.extended_timeline_options.keys()),
            width=100
        )
        detail_hours_combo.pack(side="left", padx=5)
        detail_hours_combo.set(f"{self.timeline_hours}h" if self.timeline_hours < 48 
                             else f"{self.timeline_hours//24}d")
        
        refresh_detail_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            width=80,
            command=lambda: self._refresh_detailed_view(window, "state", detail_hours_combo)
        )
        refresh_detail_btn.pack(side="left", padx=(10, 5))
        
        # Large graph area
        graph_frame = ctk.CTkFrame(window)
        graph_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create large matplotlib figure
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store references for updates
        window.graph_fig = fig
        window.graph_ax = ax
        window.graph_canvas = canvas
        window.hours_combo = detail_hours_combo
        
        # Initial data load
        self._update_detailed_state_graph(window)
        
    def _create_detailed_status_view(self, window):
        """Create detailed status graph view with enhanced features."""
        # Similar to state view but for status
        # Header
        header_frame = ctk.CTkFrame(window)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Chamber Status Issues - Detailed Analysis",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Time range controls
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        range_label = ctk.CTkLabel(controls_frame, text="Time Range:")
        range_label.pack(side="left", padx=(10, 5))
        
        detail_hours_combo = ctk.CTkComboBox(
            controls_frame,
            values=list(self.extended_timeline_options.keys()),
            width=100
        )
        detail_hours_combo.pack(side="left", padx=5)
        detail_hours_combo.set(f"{self.timeline_hours}h" if self.timeline_hours < 48 
                             else f"{self.timeline_hours//24}d")
        
        refresh_detail_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            width=80,
            command=lambda: self._refresh_detailed_view(window, "status", detail_hours_combo)
        )
        refresh_detail_btn.pack(side="left", padx=(10, 5))
        
        # Large graph area
        graph_frame = ctk.CTkFrame(window)
        graph_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create large matplotlib figure
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store references
        window.graph_fig = fig
        window.graph_ax = ax
        window.graph_canvas = canvas
        window.hours_combo = detail_hours_combo
        
        # Initial data load
        self._update_detailed_status_graph(window)
        
    def _create_detailed_activity_view(self, window):
        """Create detailed activity view with filtering and search."""
        # Header
        header_frame = ctk.CTkFrame(window)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Recent Activity - Detailed Log",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # Controls
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.pack(side="right", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(controls_frame, text="Filter:")
        search_label.pack(side="left", padx=(10, 5))
        
        search_entry = ctk.CTkEntry(controls_frame, placeholder_text="Chamber name or state...")
        search_entry.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄",
            width=40,
            command=lambda: self._refresh_activity_detail(window, search_entry.get())
        )
        refresh_btn.pack(side="left", padx=(10, 5))
        
        # Activity content
        content_frame = ctk.CTkFrame(window)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        activity_text = ctk.CTkTextbox(
            content_frame,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        activity_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store reference
        window.activity_text = activity_text
        window.search_entry = search_entry
        
        # Load initial data
        self._refresh_activity_detail(window, "")
        
    def _refresh_detailed_view(self, window, view_type, hours_combo):
        """Refresh detailed view with new time range."""
        # Update timeline hours from combo
        selected_range = hours_combo.get()
        self.timeline_hours = self.extended_timeline_options.get(selected_range, 24)
        
        if view_type == "state":
            self._update_detailed_state_graph(window)
        elif view_type == "status":
            self._update_detailed_status_graph(window)
    
    def _update_detailed_state_graph(self, window):
        """Update the detailed state graph with current data."""
        if not hasattr(window, 'graph_ax'):
            return
            
        # Clear and update
        window.graph_ax.clear()
        
        # Get current stats
        stats = self.app.get_chamber_statistics()
        
        if self.view_mode == "count":
            self._update_detailed_count_graph(window.graph_ax, stats, "state")
        else:
            self._update_detailed_time_graph(window.graph_ax, "state")
            
        window.graph_fig.tight_layout()
        window.graph_canvas.draw()
    
    def _update_detailed_status_graph(self, window):
        """Update the detailed status graph with current data."""
        if not hasattr(window, 'graph_ax'):
            return
            
        # Clear and update
        window.graph_ax.clear()
        
        # Get current stats
        stats = self.app.get_chamber_statistics()
        
        if self.view_mode == "count":
            self._update_detailed_count_graph(window.graph_ax, stats, "status")
        else:
            self._update_detailed_time_graph(window.graph_ax, "status")
            
        window.graph_fig.tight_layout()
        window.graph_canvas.draw()
    
    def _update_detailed_count_graph(self, ax, stats, graph_type):
        """Update detailed count graph with enhanced visualization."""
        if graph_type == "state":
            data = stats.get('by_state', {})
            title = "Chamber States Distribution - Detailed View"
            colors = [self.state_colors.get(state, '#808080') for state in data.keys()]
        else:
            data = stats.get('by_status', {})
            title = "Chamber Status Issues - Detailed View"
            colors = ['#ff7f0e' if count > 0 else '#d62728' for count in data.values()]
        
        if data:
            labels = list(data.keys())
            values = list(data.values())
            
            # Create enhanced bar chart
            bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
            
            # Enhance appearance
            ax.set_title(title, color='white', fontsize=16, pad=20)
            ax.set_ylabel("Number of Chambers", color='white', fontsize=14)
            ax.tick_params(colors='white', labelsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{value}', ha='center', va='bottom', color='white', fontsize=12)
            
            # Rotate labels if needed
            if len(max(labels, key=len)) > 8:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, f"No {graph_type} data available", 
                   transform=ax.transAxes, ha='center', va='center', 
                   color='white', fontsize=16)
    
    def _update_detailed_time_graph(self, ax, graph_type):
        """Update detailed timeline graph with enhanced visualization."""
        # Use existing timeline creation logic but with enhanced styling
        chambers = self.app.get_chambers()
        
        # Group chambers by type
        chambers_by_type = {"TVAC": [], "HASS": [], "THERMAL": []}
        for chamber in chambers:
            chamber_type = chamber.chamber_type.value if hasattr(chamber, 'chamber_type') else "TVAC"
            if chamber_type in chambers_by_type:
                chambers_by_type[chamber_type].append(chamber)
        
        # Set up extended time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.timeline_hours)
        
        # Create enhanced timeline
        title = f"Chamber {graph_type.title()} Timeline - Last {self._format_time_range()}"
        self._create_enhanced_timeline_graph(ax, chambers_by_type, start_time, end_time, title, graph_type)
    
    def _create_enhanced_timeline_graph(self, ax, chambers_by_type, start_time, end_time, title, data_type):
        """Create enhanced timeline graph with better styling and more information."""
        ax.set_facecolor('#2b2b2b')
        
        y_position = 0
        y_labels = []
        
        # Enhanced timeline with better spacing and styling
        for chamber_type, chambers in chambers_by_type.items():
            if not chambers:
                continue
                
            # Add type separator with enhanced styling
            if y_position > 0:
                ax.axhline(y=y_position - 0.5, color='white', linestyle='--', alpha=0.5, linewidth=2)
            
            # Add type label
            if chambers:
                ax.text(-0.02, y_position + len(chambers)/2 - 0.5, chamber_type, 
                       transform=ax.get_yaxis_transform(), ha='right', va='center',
                       color='white', fontsize=12, weight='bold')
            
            # Add chambers with enhanced visualization
            for chamber in chambers:
                history = self._get_chamber_history(chamber, start_time, end_time, data_type)
                
                for period in history:
                    color = self.state_colors.get(period['state'], self.state_colors['default'])
                    
                    # Calculate position and width using matplotlib dates
                    start_pos = mdates.date2num(period['start_time'])
                    end_pos = mdates.date2num(period['end_time'])
                    width = end_pos - start_pos
                    
                    duration = (period['end_time'] - period['start_time']).total_seconds() / 3600
                    if duration > 0.05:  # Show even shorter periods in detailed view
                        bar = ax.barh(
                            y_position, 
                            width, 
                            left=start_pos,
                            height=0.8,
                            color=color,
                            alpha=0.9,
                            edgecolor='white',
                            linewidth=1
                        )
                        
                        # Add state label for longer periods
                        if duration > 2:  # Only for periods longer than 2 hours
                            bar_center = start_pos + width/2
                            ax.text(bar_center, y_position, period['state'][:4], 
                                   ha='center', va='center', color='white', 
                                   fontsize=8, weight='bold')
                
                y_labels.append(f"{chamber.name}")
                y_position += 1
        
        # Enhanced axis configuration
        ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
        ax.set_ylim(-0.5, y_position - 0.5)
        
        # Enhanced time formatting based on range
        if self.timeline_hours <= 6:
            ax.xaxis.set_major_locator(HourLocator(interval=1))
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
        elif self.timeline_hours <= 24:
            ax.xaxis.set_major_locator(HourLocator(interval=3))
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
        elif self.timeline_hours <= 168:  # 7 days
            ax.xaxis.set_major_locator(HourLocator(interval=12))
            ax.xaxis.set_major_formatter(DateFormatter('%m/%d %H:%M'))
        else:  # 30 days
            ax.xaxis.set_major_locator(HourLocator(interval=24))
            ax.xaxis.set_major_formatter(DateFormatter('%m/%d'))
        
        # Enhanced styling
        ax.set_xlabel("Time", color='white', fontsize=14)
        ax.set_ylabel("Chambers", color='white', fontsize=14)
        ax.set_title(title, color='white', fontsize=16, pad=20)
        ax.tick_params(colors='white', labelsize=11)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Rotate labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Set y-axis labels
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels, fontsize=10)
        
        # Add enhanced legend
        if data_type == "state":
            self._add_enhanced_state_legend(ax)
    
    def _add_enhanced_state_legend(self, ax):
        """Add enhanced state legend with better styling."""
        legend_elements = []
        for state, color in self.state_colors.items():
            if state != 'default':
                legend_elements.append(mpatches.Patch(color=color, label=state.replace('_', ' ').title()))
        
        if legend_elements:
            legend = ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1),
                             fancybox=True, shadow=True, fontsize=10)
            legend.get_frame().set_facecolor('#2b2b2b')
            legend.get_frame().set_edgecolor('white')
            for text in legend.get_texts():
                text.set_color('white')
    
    def _refresh_activity_detail(self, window, filter_text=""):
        """Refresh detailed activity view with filtering."""
        if not hasattr(window, 'activity_text'):
            return
            
        window.activity_text.delete("1.0", "end")
        
        # Get comprehensive activity data
        recent_activities = []
        chambers = self.app.get_chambers()
        
        for chamber in chambers:
            # Filter by chamber name if specified
            if filter_text and filter_text.lower() not in chamber.name.lower():
                continue
                
            # Get more state transitions
            for transition in chamber.state_manager.state_history[-20:]:
                recent_activities.append({
                    'chamber': chamber.name,
                    'type': 'state',
                    'transition': transition,
                    'timestamp': transition.timestamp
                })
            
            # Get more status transitions
            for transition in chamber.state_manager.status_history[-20:]:
                if filter_text and filter_text.lower() not in transition.to_value.lower():
                    continue
                recent_activities.append({
                    'chamber': chamber.name,
                    'type': 'status',
                    'transition': transition,
                    'timestamp': transition.timestamp
                })
        
        # Sort by timestamp (most recent first)
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Display activities with enhanced formatting
        for i, activity in enumerate(recent_activities[:50]):  # Show more activities
            chamber_name = activity['chamber']
            transition = activity['transition']
            time_str = transition.timestamp.strftime("%m/%d %H:%M:%S")
            
            if activity['type'] == 'state':
                text = f"🔄 {time_str} - {chamber_name}: {transition.from_value} → {transition.to_value}"
                if hasattr(transition, 'reason') and transition.reason:
                    text += f" ({transition.reason})"
            else:
                text = f"⚠️  {time_str} - {chamber_name} status: {transition.from_value} → {transition.to_value}"
            
            window.activity_text.insert("end", text + "\n")
            
            # Add separator every 5 entries
            if i % 5 == 4:
                window.activity_text.insert("end", "─" * 60 + "\n")
        
        if not recent_activities:
            if filter_text:
                window.activity_text.insert("end", f"No activities found matching '{filter_text}'")
            else:
                window.activity_text.insert("end", "No recent activity")
    
    def _format_time_range(self):
        """Format the current time range for display."""
        if self.timeline_hours < 48:
            return f"{self.timeline_hours}h"
        else:
            days = self.timeline_hours // 24
            return f"{days}d"
    
    def update_data(self):
        """Update all data displays with enhanced statistics."""
        try:
            # Get application statistics
            stats = self.app.get_chamber_statistics()
            
            # Update enhanced header stats
            total_chambers = stats.get('total_chambers', 0)
            connected = stats.get('connected_chambers', 0)
            active_wr = stats.get('active_work_requests', 0)
            self.header_stats_label.configure(
                text=f"🏭 {total_chambers} chambers • 🔗 {connected} connected • 📋 {active_wr} active WR"
            )
            
            # Update sidebar statistics  
            self._update_enhanced_statistics(stats)
            
            # Update graphs based on view mode
            if self.view_mode == "count":
                self._update_count_graphs(stats)
            else:
                self._update_time_graphs()
            
            # Update recent activity
            self._update_recent_activity()
            
            # Update any open detail windows
            for window_type, window in self.detail_windows.items():
                if window.winfo_exists():
                    if window_type == "state_detail":
                        self._update_detailed_state_graph(window)
                    elif window_type == "status_detail":
                        self._update_detailed_status_graph(window)
                    elif window_type == "activity_detail":
                        self._refresh_activity_detail(window, window.search_entry.get())
            
        except Exception as e:
            self.logger.error(f"Error updating enhanced overview data: {e}", exc_info=True)
    
    def _update_enhanced_statistics(self, stats: Dict[str, Any]):
        """Update statistics with enhanced formatting."""
        # Update overall stats
        total_chambers = stats.get('total_chambers', 0)
        connected = stats.get('connected_chambers', 0)
        active_wr = stats.get('active_work_requests', 0)
        
        self.total_chambers_label.configure(text=f"Chambers: {total_chambers}")
        self.connected_label.configure(text=f"Connected: {connected}")
        self.active_work_label.configure(text=f"Active WR: {active_wr}")
        
        # Update type statistics
        by_type = stats.get('by_type', {})
        for chamber_type, label in self.type_labels.items():
            count = by_type.get(chamber_type, 0)
            label.configure(text=f"{chamber_type}: {count}")
