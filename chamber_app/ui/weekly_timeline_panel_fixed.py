"""
Weekly Timeline Panel for Chamber Management System.
Provides Gantt-style timeline graphs for TVAC, HASS, and THERMAL chambers.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import tkinter as tk

from ..core.chamber_state import ChamberState, ChamberStatus, ChamberType
from ..utils import get_logger


class WeeklyTimelinePanel(ctk.CTkFrame):
    """
    Panel displaying weekly timeline graphs for chamber types.
    Shows Gantt-style visualization with color-coded status segments.
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        
        # Timeline configuration
        self.days_to_show = 7  # Last 7 days by default
        self.refresh_interval = 30000  # 30 seconds
        
        # Color scheme matching the screenshot
        self.status_colors = {
            # Main status colors from the legend
            'Available': '#90EE90',           # Light Green
            'In Use': '#32CD32',              # Lime Green
            'In Test': '#FFD700',             # Gold/Yellow
            'Bake Out': '#FF8C00',            # Dark Orange
            'Waiting for Engineer': '#B0C4DE', # Light Steel Blue
            'Maintenance': '#FF4500',         # Red Orange
            'Offline': '#8B0000',             # Dark Red
            
            # Fallback colors for chamber states
            ChamberState.AVAILABLE_EMPTY.value: '#90EE90',      # Light Green
            ChamberState.STAGING.value: '#32CD32',              # Lime Green  
            ChamberState.SETUP.value: '#B0C4DE',                # Light Steel Blue
            ChamberState.TEST_START.value: '#FFD700',           # Gold
            ChamberState.TEST_NOMINAL.value: '#FFD700',         # Gold
            ChamberState.TEST_END.value: '#FFD700',             # Gold
            ChamberState.TEST_TEARDOWN.value: '#FF8C00',        # Dark Orange
            
            # Status colors
            ChamberStatus.ENGINEER_NEEDED.value: '#B0C4DE',     # Light Steel Blue
            ChamberStatus.ISSUES_HALTED.value: '#FF4500',       # Red Orange
            ChamberStatus.MAINTENANCE.value: '#FF4500',         # Red Orange
            ChamberStatus.BAKE_OUT.value: '#FF8C00',            # Dark Orange
            ChamberStatus.CHAMBER_DOWN.value: '#8B0000',        # Dark Red
            ChamberStatus.SETUP_ISSUES.value: '#FF4500',        # Red Orange
            ChamberStatus.TEST_ISSUES.value: '#FF4500',         # Red Orange
            ChamberStatus.CURRENTLY_BEING_WORKED_ON.value: '#32CD32',  # Lime Green
            ChamberStatus.SSL_SUPPORT_NEEDED.value: '#FF4500',  # Red Orange
        }
        
        # Store graph widgets for updates
        self.graph_widgets = {}
        self.canvas_widgets = {}
        
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self._setup_ui()
        self._start_refresh_timer()
        
    def _setup_ui(self):
        """Setup the timeline panel UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Header with controls
        self._create_header()
        
        # Scrollable content area
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create timeline graphs for each chamber type
        self._create_timeline_graphs()
        
    def _create_header(self):
        """Create header with time range controls and refresh button."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="Chamber Status Timeline",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Controls frame
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        # Time range dropdown
        range_label = ctk.CTkLabel(controls_frame, text="Time Range:")
        range_label.pack(side="left", padx=(10, 5))
        
        self.time_range_combo = ctk.CTkComboBox(
            controls_frame,
            values=["Last 7 Days", "Last 14 Days", "Last 30 Days"],
            state="readonly",
            command=self._on_time_range_change
        )
        self.time_range_combo.set("Last 7 Days")
        self.time_range_combo.pack(side="left", padx=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="Refresh",
            command=self._refresh_timeline,
            width=80,
            height=30
        )
        refresh_btn.pack(side="left", padx=(10, 10))
        
    def _create_timeline_graphs(self):
        """Create timeline graphs for each chamber type."""
        chamber_types = [("HASS", "HASS Chambers - Status Timeline"),
                        ("TVAC", "TVAC Chambers - Status Timeline"), 
                        ("THERMAL", "THERMAL Chambers - Status Timeline")]
        
        for i, (chamber_type, title) in enumerate(chamber_types):
            self._create_chamber_timeline(chamber_type, title, i)
            
    def _create_chamber_timeline(self, chamber_type: str, title: str, row: int):
        """Create timeline graph for a specific chamber type."""
        # Container frame
        container_frame = ctk.CTkFrame(self.scroll_frame)
        container_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=10)
        container_frame.grid_columnconfigure(0, weight=1)
        
        # Header with title and View Details button
        header_frame = ctk.CTkFrame(container_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Chamber type title
        type_title = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        type_title.grid(row=0, column=0, sticky="w", padx=10)
        
        # View details button
        details_btn = ctk.CTkButton(
            header_frame,
            text="View Details",
            command=lambda: self._show_timeline_details(chamber_type),
            width=100,
            height=30,
            fg_color="gray",
            hover_color="dark gray"
        )
        details_btn.grid(row=0, column=1, padx=10, sticky="e")
        
        # Graph frame
        graph_frame = ctk.CTkFrame(container_frame)
        graph_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        graph_frame.grid_columnconfigure(0, weight=1)
        
        # Create matplotlib figure
        fig, ax = self._create_gantt_chart(chamber_type)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Store references
        self.graph_widgets[chamber_type] = {
            'container': container_frame,
            'header': header_frame,
            'graph_frame': graph_frame,
            'figure': fig,
            'axis': ax
        }
        self.canvas_widgets[chamber_type] = canvas
        
    def _create_gantt_chart(self, chamber_type: str):
        """Create a Gantt-style timeline chart matching the screenshot."""
        # Get chambers of this type
        chambers = self.app.get_chambers_by_type(ChamberType(chamber_type))
        
        if not chambers:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(14, 3))
            ax.text(0.5, 0.5, f"No {chamber_type} chambers available", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig, ax
            
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_to_show)
        
        # Create figure with appropriate height
        fig, ax = plt.subplots(figsize=(14, max(3, len(chambers) * 0.8 + 1)))
        fig.patch.set_facecolor('#2b2b2b')  # Dark background
        ax.set_facecolor('#2b2b2b')
        
        # Generate timeline data for each chamber
        y_labels = []
        
        for i, chamber in enumerate(chambers):
            y_pos = len(chambers) - i - 1  # Reverse order to match screenshot
            y_labels.append(chamber.name)
            
            # Generate mock timeline segments (since we don't have real history data)
            segments = self._generate_mock_timeline_segments(chamber, start_date, end_date)
            
            # Draw segments
            for start_time, end_time, color, status_text in segments:
                # Convert to matplotlib dates
                start_num = mdates.date2num(start_time)
                end_num = mdates.date2num(end_time)
                width = end_num - start_num
                
                # Create rectangle
                rect = Rectangle(
                    (start_num, y_pos - 0.35),
                    width,
                    0.7,
                    facecolor=color,
                    edgecolor='#333333',
                    linewidth=0.5,
                    alpha=0.9
                )
                ax.add_patch(rect)
                
        # Configure axes
        ax.set_xlim(mdates.date2num(start_date), mdates.date2num(end_date))
        ax.set_ylim(-0.5, len(chambers) - 0.5)
        
        # Format x-axis (days of week)
        days = mdates.DayLocator(interval=1)
        days_fmt = mdates.DateFormatter('%a')  # Mon, Tue, Wed, etc.
        ax.xaxis.set_major_locator(days)
        ax.xaxis.set_major_formatter(days_fmt)
        
        # Y-axis (chamber names)
        ax.set_yticks(range(len(chambers)))
        ax.set_yticklabels(reversed(y_labels))  # Reverse to match layout
        
        # Styling to match screenshot
        ax.tick_params(colors='white', labelsize=10)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        
        # Grid
        ax.grid(True, axis='x', alpha=0.3, color='gray')
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        
        # Tight layout
        fig.tight_layout()
        
        return fig, ax
        
    def _generate_mock_timeline_segments(self, chamber, start_date: datetime, end_date: datetime) -> List[Tuple]:
        """Generate mock timeline segments for demonstration."""
        segments = []
        
        # Create some realistic timeline segments
        current_time = start_date
        total_duration = end_date - start_date
        
        # Generate 3-5 segments per chamber
        num_segments = np.random.randint(3, 6)
        
        for i in range(num_segments):
            # Random segment duration (4-24 hours)
            segment_hours = np.random.randint(4, 25)
            segment_end = current_time + timedelta(hours=segment_hours)
            
            if segment_end > end_date:
                segment_end = end_date
            
            # Choose status based on chamber type and position
            if chamber.type == ChamberType.TVAC:
                if i % 3 == 0:
                    status = 'In Test'
                    color = self.status_colors['In Test']
                elif i % 3 == 1:
                    status = 'Bake Out'
                    color = self.status_colors['Bake Out']
                else:
                    status = 'Available'
                    color = '#666666'  # Gray for inactive periods
            elif chamber.type == ChamberType.HASS:
                # HASS chambers are mostly inactive in the screenshot
                status = 'Available'
                color = '#666666'  # Gray
            else:  # THERMAL
                if i % 2 == 0:
                    status = 'Bake Out'
                    color = self.status_colors['Bake Out']
                else:
                    status = 'Available'
                    color = '#666666'  # Gray
            
            segments.append((current_time, segment_end, color, status))
            
            # Gap between segments
            current_time = segment_end + timedelta(hours=np.random.randint(1, 4))
            
            if current_time >= end_date:
                break
                
        return segments
        
    def _show_timeline_details(self, chamber_type: str):
        """Show detailed timeline view for chamber type."""
        # Placeholder for detailed view
        import tkinter.messagebox as msgbox
        msgbox.showinfo("Timeline Details", f"Detailed view for {chamber_type} chambers coming soon!")
        
    def _on_time_range_change(self, value: str):
        """Handle time range dropdown change."""
        range_mapping = {
            "Last 7 Days": 7,
            "Last 14 Days": 14,
            "Last 30 Days": 30
        }
        
        self.days_to_show = range_mapping.get(value, 7)
        self._refresh_timeline()
        
    def _refresh_timeline(self):
        """Refresh all timeline graphs."""
        try:
            for chamber_type in ["HASS", "TVAC", "THERMAL"]:
                if chamber_type in self.graph_widgets:
                    # Close existing figure to prevent memory leaks
                    widgets = self.graph_widgets[chamber_type]
                    if 'figure' in widgets:
                        plt.close(widgets['figure'])
                    
                    # Recreate chart
                    fig, ax = self._create_gantt_chart(chamber_type)
                    
                    # Update references
                    widgets['figure'] = fig
                    widgets['axis'] = ax
                    
                    # Update canvas
                    if chamber_type in self.canvas_widgets:
                        self.canvas_widgets[chamber_type].figure = fig
                        self.canvas_widgets[chamber_type].draw()
                        
            self.logger.info("Timeline graphs refreshed successfully")
            
        except Exception as e:
            self.logger.error(f"Error refreshing timeline: {e}")
            
    def _start_refresh_timer(self):
        """Start automatic refresh timer."""
        self.after(self.refresh_interval, self._periodic_refresh)
        
    def _periodic_refresh(self):
        """Periodic refresh callback."""
        self._refresh_timeline()
        self._start_refresh_timer()


# Create a legend panel to show in the sidebar
class TimelineLegendPanel(ctk.CTkFrame):
    """Legend panel showing status color meanings."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._create_legend()
        
    def _create_legend(self):
        """Create the legend with color indicators."""
        title = ctk.CTkLabel(
            self,
            text="Status Legend",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=(10, 5))
        
        legend_items = [
            ("Available", "#90EE90"),
            ("In Use", "#32CD32"),
            ("In Test", "#FFD700"),
            ("Bake Out", "#FF8C00"),
            ("Waiting for Engineer", "#B0C4DE"),
            ("Maintenance", "#FF4500"),
            ("Offline", "#8B0000")
        ]
        
        for status, color in legend_items:
            item_frame = ctk.CTkFrame(self)
            item_frame.pack(fill="x", padx=10, pady=2)
            
            # Color indicator
            color_box = ctk.CTkFrame(item_frame, width=20, height=15, fg_color=color)
            color_box.pack(side="left", padx=(5, 10), pady=5)
            
            # Status label
            label = ctk.CTkLabel(item_frame, text=status)
            label.pack(side="left", padx=5)
