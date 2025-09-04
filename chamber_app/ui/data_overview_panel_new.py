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
    Overview panel showing chamber statistics and timeline visualizations.
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        self.view_mode = "count"  # "count" or "timeline"
        
        # Timeline parameters
        self.timeline_hours = 24  # Show last 24 hours by default
        self.chamber_graphs = {}  # Store graph references by type
        self.graph_collapsed = {"TVAC": False, "HASS": False, "THERMAL": False}
        
        # State color mapping
        self.state_colors = {
            ChamberState.AVAILABLE_EMPTY.value: '#4CAF50',  # Green
            ChamberState.STAGING.value: '#FF9800',          # Orange
            ChamberState.SETUP.value: '#2196F3',            # Blue
            ChamberState.TEST_START.value: '#9C27B0',       # Purple
            ChamberState.TEST_NOMINAL.value: '#F44336',     # Red
            ChamberState.TEST_END.value: '#795548',         # Brown
            ChamberState.TEST_TEARDOWN.value: '#607D8B'     # Blue Grey
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
        
        # Control frame
        control_frame = ctk.CTkFrame(header_frame)
        control_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        # View mode toggle
        mode_label = ctk.CTkLabel(control_frame, text="View Mode:")
        mode_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.mode_combo = ctk.CTkComboBox(
            control_frame,
            values=["Count Overview", "Timeline View"],
            command=self._on_mode_change,
            width=150
        )
        self.mode_combo.pack(side="left", padx=(0, 10), pady=10)
        self.mode_combo.set("Count Overview")
        
        # Timeline controls (initially hidden)
        self.timeline_controls = ctk.CTkFrame(control_frame)
        
        timeline_label = ctk.CTkLabel(self.timeline_controls, text="Hours:")
        timeline_label.pack(side="left", padx=(10, 5), pady=10)
        
        self.hours_combo = ctk.CTkComboBox(
            self.timeline_controls,
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
        
        # Create scrollable frame for timeline graphs
        self.content_scroll = ctk.CTkScrollableFrame(content_frame)
        self.content_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.content_scroll.grid_columnconfigure(0, weight=1)
        
        # Count graphs (original functionality)
        self._create_count_graphs()
        
        # Timeline graphs (new functionality)
        self._create_timeline_graphs()
    
    def _create_count_graphs(self):
        """Create original count-based graphs."""
        self.count_graphs_frame = ctk.CTkFrame(self.content_scroll)
        self.count_graphs_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.count_graphs_frame.grid_columnconfigure(0, weight=1)
        
        # State count graph
        state_frame = ctk.CTkFrame(self.count_graphs_frame)
        state_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        state_frame.grid_columnconfigure(0, weight=1)
        
        state_title = ctk.CTkLabel(
            state_frame,
            text="Chamber States Distribution",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        state_title.grid(row=0, column=0, pady=(10, 5))
        
        self.state_fig, self.state_ax = plt.subplots(figsize=(10, 4))
        self.state_fig.patch.set_facecolor('#2b2b2b')
        self.state_ax.set_facecolor('#2b2b2b')
        
        self.state_canvas = FigureCanvasTkAgg(self.state_fig, state_frame)
        self.state_canvas.get_tk_widget().grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Status count graph
        status_frame = ctk.CTkFrame(self.count_graphs_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        status_frame.grid_columnconfigure(0, weight=1)
        
        status_title = ctk.CTkLabel(
            status_frame,
            text="Chamber Status Issues",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.grid(row=0, column=0, pady=(10, 5))
        
        self.status_fig, self.status_ax = plt.subplots(figsize=(10, 4))
        self.status_fig.patch.set_facecolor('#2b2b2b')
        self.status_ax.set_facecolor('#2b2b2b')
        
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, status_frame)
        self.status_canvas.get_tk_widget().grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
    
    def _create_timeline_graphs(self):
        """Create timeline-based graphs for each chamber type."""
        self.timeline_graphs_frame = ctk.CTkFrame(self.content_scroll)
        self.timeline_graphs_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.timeline_graphs_frame.grid_columnconfigure(0, weight=1)
        
        # Initially hide timeline graphs
        self.timeline_graphs_frame.grid_remove()
        
        # Create graphs for each chamber type
        chamber_types = ["TVAC", "HASS", "THERMAL"]
        for i, chamber_type in enumerate(chamber_types):
            self._create_chamber_type_timeline(chamber_type, i)
    
    def _create_chamber_type_timeline(self, chamber_type: str, row: int):
        """Create timeline graph for a specific chamber type."""
        # Container frame
        container = ctk.CTkFrame(self.timeline_graphs_frame)
        container.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        container.grid_columnconfigure(0, weight=1)
        
        # Header with collapse button
        header_frame = ctk.CTkFrame(container)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Collapse/expand button
        collapse_btn = ctk.CTkButton(
            header_frame,
            text="▼",
            width=30,
            command=lambda ct=chamber_type: self._toggle_graph_collapse(ct)
        )
        collapse_btn.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{chamber_type} Chambers Timeline",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Chamber count label
        count_label = ctk.CTkLabel(
            header_frame,
            text="0 chambers",
            font=ctk.CTkFont(size=12)
        )
        count_label.grid(row=0, column=2, padx=(5, 10), pady=5)
        
        # Graph frame
        graph_frame = ctk.CTkFrame(container)
        graph_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        graph_frame.grid_columnconfigure(0, weight=1)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        # Configure timeline axis
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Store references
        self.chamber_graphs[chamber_type] = {
            'container': container,
            'header_frame': header_frame,
            'graph_frame': graph_frame,
            'collapse_btn': collapse_btn,
            'title_label': title_label,
            'count_label': count_label,
            'fig': fig,
            'ax': ax,
            'canvas': canvas
        }
        
        # Enable interactive features
        canvas.mpl_connect('motion_notify_event', lambda event, ct=chamber_type: self._on_hover(event, ct))
        canvas.mpl_connect('button_press_event', lambda event, ct=chamber_type: self._on_timeline_click(event, ct))
    
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
        
        # Legend frame for timeline
        self.legend_frame = ctk.CTkFrame(stats_frame)
        self.legend_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        legend_title = ctk.CTkLabel(
            self.legend_frame,
            text="State Legend",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        legend_title.pack(pady=(5, 0))
        
        # Create legend for states
        for state, color in self.state_colors.items():
            legend_item = ctk.CTkFrame(self.legend_frame)
            legend_item.pack(fill="x", padx=5, pady=1)
            
            # Color indicator
            color_label = ctk.CTkLabel(
                legend_item,
                text="█",
                text_color=color,
                font=ctk.CTkFont(size=16)
            )
            color_label.pack(side="left", padx=(5, 10))
            
            # State name
            state_label = ctk.CTkLabel(
                legend_item,
                text=state.replace('_', ' ').title(),
                font=ctk.CTkFont(size=10)
            )
            state_label.pack(side="left")
        
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
            height=100,
            wrap="word"
        )
        self.activity_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _on_mode_change(self, value):
        """Handle view mode change."""
        if value == "Count Overview":
            self.view_mode = "count"
            self.count_graphs_frame.grid()
            self.timeline_graphs_frame.grid_remove()
            self.timeline_controls.pack_forget()
        else:
            self.view_mode = "timeline"
            self.count_graphs_frame.grid_remove()
            self.timeline_graphs_frame.grid()
            self.timeline_controls.pack(side="left", padx=(10, 0), pady=10)
        
        self.update_data()
        self.logger.info(f"Changed view mode to: {self.view_mode}")
    
    def _on_hours_change(self, value):
        """Handle timeline hours change."""
        try:
            self.timeline_hours = int(value)
            if self.view_mode == "timeline":
                self.update_data()
        except ValueError:
            pass
    
    def _toggle_graph_collapse(self, chamber_type: str):
        """Toggle collapse/expand state of a graph."""
        graph_info = self.chamber_graphs[chamber_type]
        is_collapsed = self.graph_collapsed[chamber_type]
        
        if is_collapsed:
            # Expand
            graph_info['graph_frame'].grid()
            graph_info['collapse_btn'].configure(text="▼")
            self.graph_collapsed[chamber_type] = False
        else:
            # Collapse
            graph_info['graph_frame'].grid_remove()
            graph_info['collapse_btn'].configure(text="▶")
            self.graph_collapsed[chamber_type] = True
      def _on_hover(self, event, chamber_type: str):
        """Handle mouse hover over timeline graph."""
        if event.inaxes is None:
            return
        
        # Get hover information and show tooltip
        try:
            # Get the position of the mouse
            x, y = event.xdata, event.ydata
            if x is None or y is None:
                return
                
            # Get chamber information at this position
            graph_info = self.chamber_graphs.get(chamber_type)
            if not graph_info:
                return
                
            # Convert y position to chamber index
            chamber_index = int(round(y))
            chambers = self.app.get_chambers_by_type(ChamberType(chamber_type))
            
            if 0 <= chamber_index < len(chambers):
                chamber = chambers[chamber_index]
                
                # Format hover text
                hover_text = f"""Chamber: {chamber.name}
State: {chamber.state_manager.current_state.value}
Status: {chamber.state_manager.current_status.value if chamber.state_manager.current_status else 'None'}
Connected: {'Yes' if chamber.is_connected else 'No'}"""
                
                # Update tooltip (simple implementation using window title)
                # In a full implementation, you'd create a proper tooltip widget
                graph_info['ax'].set_title(hover_text, fontsize=8, pad=5)
                graph_info['canvas'].draw_idle()
                
        except Exception as e:
            self.logger.debug(f"Error in hover handler: {e}")
      def _on_timeline_click(self, event, chamber_type: str):
        """Handle click on timeline graph."""
        if event.dblclick and event.inaxes is not None:
            # Show detailed chamber information
            self._show_chamber_details(chamber_type)
    
    def _show_chamber_details(self, chamber_type: str):
        """Show detailed information for chambers of a specific type."""
        try:
            from ..core.chamber_state import ChamberType
            
            # Get chambers of the specified type
            chambers = [c for c in self.app.get_chambers() if c.type.value.upper() == chamber_type.upper()]
            
            if not chambers:
                messagebox.showinfo("No Chambers", f"No {chamber_type} chambers found.")
                return
            
            # Create details dialog
            self._create_chamber_details_dialog(chambers, chamber_type)
            
        except Exception as e:
            self.logger.error(f"Error showing chamber details: {e}")
            messagebox.showerror("Error", f"Failed to show chamber details: {e}")
    
    def _create_chamber_details_dialog(self, chambers, chamber_type: str):
        """Create a dialog showing detailed chamber information."""
        import customtkinter as ctk
        from tkinter import ttk
        
        # Create dialog window
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{chamber_type} Chamber Details")
        dialog.geometry("800x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.winfo_width() // 2) - (800 // 2) + self.winfo_rootx()
        y = (self.winfo_height() // 2) - (600 // 2) + self.winfo_rooty()
        dialog.geometry(f"800x600+{x}+{y}")
        
        # Create main frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"{chamber_type} Chambers ({len(chambers)} total)",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create scrollable frame for chamber list
        scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        scrollable_frame.pack(fill="both", expand=True)
        
        # Add chamber cards
        for chamber in chambers:
            self._create_chamber_detail_card(scrollable_frame, chamber)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=dialog.destroy,
            width=100
        )
        close_btn.pack(pady=(20, 0))
    
    def _create_chamber_detail_card(self, parent, chamber):
        """Create a detailed card for a single chamber."""
        import customtkinter as ctk
        
        # Main card frame
        card_frame = ctk.CTkFrame(parent)
        card_frame.pack(fill="x", padx=10, pady=5)
        
        # Header with chamber name and state
        header_frame = ctk.CTkFrame(card_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        name_label = ctk.CTkLabel(
            header_frame,
            text=chamber.name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(side="left")
        
        state_label = ctk.CTkLabel(
            header_frame,
            text=f"State: {chamber.state_manager.current_state.value}",
            font=ctk.CTkFont(size=12)
        )
        state_label.pack(side="right")
        
        # Details grid
        details_frame = ctk.CTkFrame(card_frame)
        details_frame.pack(fill="x", padx=10, pady=(0, 10))
        details_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Status
        status_text = chamber.state_manager.current_status.value if chamber.state_manager.current_status else "None"
        ctk.CTkLabel(details_frame, text="Status:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text=status_text).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Connection
        conn_text = "Connected" if chamber.is_connected else "Disconnected"
        ctk.CTkLabel(details_frame, text="Connection:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text=conn_text).grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        # Work requests
        active_wr = len(chamber.get_active_work_requests())
        ctk.CTkLabel(details_frame, text="Active Work Requests:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text=str(active_wr)).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # State duration
        duration = chamber.state_manager.get_state_duration()
        duration_text = f"{duration // 3600:.0f}h {(duration % 3600) // 60:.0f}m"
        ctk.CTkLabel(details_frame, text="In Current State:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text=duration_text).grid(row=1, column=3, sticky="w", padx=5, pady=2)
        
        # Telemetry status
        if chamber.last_telemetry:
            temp_text = f"{chamber.last_telemetry.temperature:.1f}°C"
            vacuum_text = f"{chamber.last_telemetry.vacuum_level:.2e} Torr"
        else:
            temp_text = "No data"
            vacuum_text = "No data"
            
        ctk.CTkLabel(details_frame, text="Temperature:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text=temp_text).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text="Vacuum:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=2, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(details_frame, text=vacuum_text).grid(row=2, column=3, sticky="w", padx=5, pady=2)
    
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
                self._update_timeline_graphs()
            
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
        """Update count-based graphs."""
        # Update state graph
        self.state_ax.clear()
        by_state = stats.get('by_state', {})
        
        if by_state:
            states = list(by_state.keys())
            counts = list(by_state.values())
            
            # Use state colors
            colors = [self.state_colors.get(state, '#808080') for state in states]
            display_states = [state.replace('_', ' ').title() for state in states]
            
            bars = self.state_ax.bar(display_states, counts, color=colors, alpha=0.8)
            self.state_ax.set_title("Chambers by State", color='white')
            self.state_ax.set_ylabel("Number of Chambers", color='white')
            self.state_ax.tick_params(colors='white')
            
            # Rotate x-axis labels
            plt.setp(self.state_ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
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
            
            colors = ['#ff7f0e' if count > 0 else '#d62728' for count in counts]
            
            bars = self.status_ax.bar(statuses, counts, color=colors, alpha=0.8)
            self.status_ax.set_title("Chambers with Status Issues", color='white')
            self.status_ax.set_ylabel("Number of Chambers", color='white')
            self.status_ax.tick_params(colors='white')
            
            plt.setp(self.status_ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.status_ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                                 f'{count}', ha='center', va='bottom', color='white')
        else:
            self.status_ax.text(0.5, 0.5, "No Status Issues", 
                              transform=self.status_ax.transAxes,
                              ha='center', va='center', color='white', fontsize=14)
        
        self.status_fig.tight_layout()
        self.status_canvas.draw()
    
    def _update_timeline_graphs(self):
        """Update timeline-based graphs for each chamber type."""
        chambers = self.app.get_chambers()
        
        # Group chambers by type
        chambers_by_type = {"TVAC": [], "HASS": [], "THERMAL": []}
        for chamber in chambers:
            chamber_type = chamber.type.value
            if chamber_type in chambers_by_type:
                chambers_by_type[chamber_type].append(chamber)
        
        # Update each graph
        for chamber_type, type_chambers in chambers_by_type.items():
            self._update_chamber_type_timeline(chamber_type, type_chambers)
    
    def _update_chamber_type_timeline(self, chamber_type: str, chambers: List):
        """Update timeline graph for a specific chamber type."""
        if chamber_type not in self.chamber_graphs:
            return
        
        graph_info = self.chamber_graphs[chamber_type]
        ax = graph_info['ax']
        ax.clear()
        
        # Update chamber count
        graph_info['count_label'].configure(text=f"{len(chambers)} chambers")
        
        if not chambers:
            ax.text(0.5, 0.5, f"No {chamber_type} chambers", 
                   transform=ax.transAxes, ha='center', va='center', 
                   color='white', fontsize=14)
            graph_info['canvas'].draw()
            return
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.timeline_hours)
        
        # Prepare timeline data
        y_positions = {}
        y_labels = []
        timeline_data = []
        
        for i, chamber in enumerate(chambers):
            y_positions[chamber.id] = i
            y_labels.append(chamber.name)
            
            # Get state history for the time range
            state_history = self._get_chamber_timeline_data(chamber, start_time, end_time)
            timeline_data.extend(state_history)
        
        # Plot timeline bars
        for data in timeline_data:
            chamber_id, state, start, end, reason, status = data
            if chamber_id in y_positions:
                y_pos = y_positions[chamber_id]
                
                # Calculate duration and position
                duration = (end - start).total_seconds() / 3600  # hours
                start_pos = mdates.date2num(start)
                width = mdates.date2num(end) - start_pos
                
                # Get color for state
                color = self.state_colors.get(state, '#808080')
                
                # Draw bar
                bar = ax.barh(y_pos, width, left=start_pos, height=0.6, 
                            color=color, alpha=0.8, edgecolor='white', linewidth=0.5)
                
                # Add status indicator if present
                if status:
                    ax.barh(y_pos, width, left=start_pos, height=0.1, 
                           color='red', alpha=0.6)
        
        # Configure axes
        ax.set_ylim(-0.5, len(chambers) - 0.5)
        ax.set_yticks(range(len(chambers)))
        ax.set_yticklabels(y_labels)
        ax.set_xlim(mdates.date2num(start_time), mdates.date2num(end_time))
        
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
        
        # Styling
        ax.set_xlabel('Time', color='white')
        ax.set_ylabel('Chambers', color='white')
        ax.set_title(f'{chamber_type} Chambers - Last {self.timeline_hours}h', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        graph_info['fig'].tight_layout()
        graph_info['canvas'].draw()
    
    def _get_chamber_timeline_data(self, chamber, start_time: datetime, end_time: datetime):
        """Get timeline data for a chamber within the specified time range."""
        timeline_data = []
        
        # Get state history
        state_history = chamber.state_manager.state_history
        status_history = chamber.state_manager.status_history
        
        # If no history, create current state entry
        if not state_history:
            timeline_data.append((
                chamber.id,
                chamber.state_manager.current_state.value,
                start_time,
                end_time,
                "No history",
                chamber.state_manager.current_status.value if chamber.state_manager.current_status else None
            ))
            return timeline_data
        
        # Process state transitions within time range
        for i, transition in enumerate(state_history):
            transition_start = max(transition.timestamp, start_time)
            
            # Find next transition or use end_time
            if i < len(state_history) - 1:
                transition_end = min(state_history[i + 1].timestamp, end_time)
            else:
                transition_end = end_time
            
            # Only include if within our time range
            if transition_start < end_time and transition_end > start_time:
                # Find corresponding status
                current_status = None
                for status_transition in status_history:
                    if status_transition.timestamp <= transition.timestamp:
                        current_status = status_transition.to_value
                    else:
                        break
                
                timeline_data.append((
                    chamber.id,
                    transition.to_value,
                    transition_start,
                    transition_end,
                    transition.reason or "",
                    current_status
                ))
        
        return timeline_data
    
    def _update_recent_activity(self):
        """Update recent activity display."""
        self.activity_text.delete("1.0", "end")
        
        # Get recent state transitions from all chambers
        recent_activities = []
        chambers = self.app.get_chambers()
        
        for chamber in chambers:
            # Get recent state transitions
            for transition in chamber.state_manager.state_history[-3:]:  # Last 3 transitions
                recent_activities.append({
                    'chamber': chamber.name,
                    'type': 'state',
                    'transition': transition,
                    'timestamp': transition.timestamp
                })
            
            # Get recent status transitions
            for transition in chamber.state_manager.status_history[-3:]:
                recent_activities.append({
                    'chamber': chamber.name,
                    'type': 'status',
                    'transition': transition,
                    'timestamp': transition.timestamp
                })
        
        # Sort by timestamp (most recent first)
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Display recent activities
        for activity in recent_activities[:8]:  # Show last 8 activities
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
