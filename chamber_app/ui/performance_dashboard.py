"""
Performance Dashboard for Chamber Management Application.
Provides real-time monitoring of system performance, threading operations, and resource usage.
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import tkinter as tk
from collections import deque

from ..utils import get_logger
from ..utils.threading_utils import get_task_manager, ui_thread_only, async_operation
from ..utils.performance_monitor import get_performance_monitor, PerformanceMetric, OperationProfile


class PerformanceDashboard(ctk.CTkFrame):
    """
    Real-time performance monitoring dashboard.
    Shows system metrics, operation profiles, and performance alerts.
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        
        # Performance monitoring
        self.performance_monitor = get_performance_monitor()
        self.task_manager = get_task_manager()
        
        # Data storage for graphs
        self.metrics_history = deque(maxlen=100)  # Last 100 data points
        self.time_history = deque(maxlen=100)
        
        # Update control
        self.auto_refresh = True
        self.refresh_interval = 2000  # 2 seconds
        self.update_job = None
        
        # Setup UI
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self):
        """Setup the performance dashboard UI."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with controls
        self._create_header()
        
        # Main content area
        self._create_content_area()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create header with dashboard controls."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Performance Dashboard",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Controls frame
        controls_frame = ctk.CTkFrame(header_frame)
        controls_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Auto-refresh toggle
        self.auto_refresh_var = ctk.BooleanVar(value=True)
        auto_refresh_cb = ctk.CTkCheckBox(
            controls_frame,
            text="Auto Refresh",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        )
        auto_refresh_cb.pack(side="left", padx=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="Refresh Now",
            command=self._manual_refresh,
            width=100,
            height=30
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Export button
        export_btn = ctk.CTkButton(
            controls_frame,
            text="Export Data",
            command=self._export_performance_data,
            width=100,
            height=30,
            fg_color="green",
            hover_color="dark green"
        )
        export_btn.pack(side="left", padx=5)
    
    def _create_content_area(self):
        """Create main content area with performance metrics."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - Current metrics
        self._create_metrics_panel(main_frame)
        
        # Right panel - Graphs and details
        self._create_graphs_panel(main_frame)
    
    def _create_metrics_panel(self, parent):
        """Create left panel with current performance metrics."""
        metrics_frame = ctk.CTkFrame(parent)
        metrics_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        metrics_frame.grid_columnconfigure(0, weight=1)
        
        # Metrics title
        metrics_title = ctk.CTkLabel(
            metrics_frame,
            text="Current Metrics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        metrics_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # System metrics
        self._create_system_metrics(metrics_frame)
        
        # Threading metrics
        self._create_threading_metrics(metrics_frame)
        
        # Operation profiles
        self._create_operation_profiles(metrics_frame)
        
        # Memory metrics
        self._create_memory_metrics(metrics_frame)
    
    def _create_system_metrics(self, parent):
        """Create system performance metrics display."""
        system_frame = ctk.CTkFrame(parent)
        system_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        system_frame.grid_columnconfigure(1, weight=1)
        
        # Section title
        system_title = ctk.CTkLabel(
            system_frame,
            text="System Performance",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        system_title.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="w")
        
        # CPU Usage
        self.cpu_label = self._create_metric_item(system_frame, "CPU Usage:", "-- %", 1)
        
        # Memory Usage
        self.memory_label = self._create_metric_item(system_frame, "Memory Usage:", "-- %", 2)
        
        # UI Responsiveness
        self.ui_response_label = self._create_metric_item(system_frame, "UI Response:", "-- ms", 3)
    
    def _create_threading_metrics(self, parent):
        """Create threading performance metrics display."""
        threading_frame = ctk.CTkFrame(parent)
        threading_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        threading_frame.grid_columnconfigure(1, weight=1)
        
        # Section title
        threading_title = ctk.CTkLabel(
            threading_frame,
            text="Threading Performance",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        threading_title.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="w")
        
        # Active Tasks
        self.active_tasks_label = self._create_metric_item(threading_frame, "Active Tasks:", "-- ", 1)
        
        # Completed Tasks
        self.completed_tasks_label = self._create_metric_item(threading_frame, "Completed:", "-- ", 2)
        
        # Failed Tasks
        self.failed_tasks_label = self._create_metric_item(threading_frame, "Failed:", "-- ", 3)
    
    def _create_operation_profiles(self, parent):
        """Create operation profiles display."""
        profiles_frame = ctk.CTkFrame(parent)
        profiles_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        profiles_frame.grid_columnconfigure(0, weight=1)
        
        # Section title
        profiles_title = ctk.CTkLabel(
            profiles_frame,
            text="Operation Profiles",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        profiles_title.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        
        # Scrollable profiles list
        self.profiles_textbox = ctk.CTkTextbox(
            profiles_frame,
            height=150,
            wrap="word"
        )
        self.profiles_textbox.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    
    def _create_memory_metrics(self, parent):
        """Create memory metrics display."""
        memory_frame = ctk.CTkFrame(parent)
        memory_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        memory_frame.grid_columnconfigure(1, weight=1)
        
        # Section title
        memory_title = ctk.CTkLabel(
            memory_frame,
            text="Memory Analysis",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        memory_title.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="w")
        
        # Memory Usage
        self.memory_used_label = self._create_metric_item(memory_frame, "Used:", "-- MB", 1)
        
        # Memory Available
        self.memory_available_label = self._create_metric_item(memory_frame, "Available:", "-- MB", 2)
        
        # GC Collections
        self.gc_collections_label = self._create_metric_item(memory_frame, "GC Collections:", "-- ", 3)
    
    def _create_metric_item(self, parent, label_text, value_text, row):
        """Create a metric display item."""
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        label.grid(row=row, column=0, padx=5, pady=2, sticky="w")
        
        value = ctk.CTkLabel(
            parent,
            text=value_text,
            font=ctk.CTkFont(size=12)
        )
        value.grid(row=row, column=1, padx=5, pady=2, sticky="e")
        
        return value
    
    def _create_graphs_panel(self, parent):
        """Create right panel with performance graphs."""
        graphs_frame = ctk.CTkFrame(parent)
        graphs_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        graphs_frame.grid_columnconfigure(0, weight=1)
        graphs_frame.grid_rowconfigure(1, weight=1)
        
        # Graphs title
        graphs_title = ctk.CTkLabel(
            graphs_frame,
            text="Performance Trends",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        graphs_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # System metrics graph
        self.ax1.set_title("System Performance", fontsize=12, fontweight='bold')
        self.ax1.set_ylabel("Usage (%)")
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(['CPU', 'Memory'], loc='upper right')
        
        # Operation timing graph
        self.ax2.set_title("Operation Performance", fontsize=12, fontweight='bold')
        self.ax2.set_ylabel("Response Time (ms)")
        self.ax2.set_xlabel("Time")
        self.ax2.grid(True, alpha=0.3)
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, graphs_frame)
        self.canvas.draw()
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    
    def _create_status_bar(self):
        """Create status bar with monitoring information."""
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Monitoring status
        self.monitoring_status_label = ctk.CTkLabel(
            status_frame,
            text="Monitoring: Active",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        self.monitoring_status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Last update time
        self.last_update_label = ctk.CTkLabel(
            status_frame,
            text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.last_update_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
    
    def _start_monitoring(self):
        """Start performance monitoring."""
        # Start the performance monitor
        self.performance_monitor.start_monitoring(interval=1.0)
        
        # Start UI update timer
        self._schedule_update()
    
    def _schedule_update(self):
        """Schedule next UI update."""
        if self.auto_refresh:
            self.update_job = self.after(self.refresh_interval, self._update_dashboard)
    
    @ui_thread_only
    def _update_dashboard(self):
        """Update dashboard with current performance data."""
        try:
            # Get current metrics
            metrics = self.performance_monitor.get_metrics_summary()
            
            # Update metric displays
            self._update_metric_displays(metrics)
            
            # Update graphs
            self._update_performance_graphs(metrics)
            
            # Update operation profiles
            self._update_operation_profiles()
            
            # Update status bar
            self.last_update_label.configure(
                text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Schedule next update
            self._schedule_update()
            
        except Exception as e:
            self.logger.error(f"Error updating performance dashboard: {e}")
    
    def _update_metric_displays(self, metrics: Dict[str, Any]):
        """Update metric display labels."""
        # System metrics
        self.cpu_label.configure(text=f"{metrics.get('cpu_usage', 0):.1f} %")
        self.memory_label.configure(text=f"{metrics.get('memory_usage', 0):.1f} %")
        self.ui_response_label.configure(text=f"{metrics.get('ui_response_time', 0):.0f} ms")
        
        # Threading metrics
        task_stats = self.task_manager.get_task_statistics() if hasattr(self.task_manager, 'get_task_statistics') else {}
        self.active_tasks_label.configure(text=f"{task_stats.get('active', 0)}")
        self.completed_tasks_label.configure(text=f"{task_stats.get('completed', 0)}")
        self.failed_tasks_label.configure(text=f"{task_stats.get('failed', 0)}")
        
        # Memory metrics
        self.memory_used_label.configure(text=f"{metrics.get('memory_used_mb', 0):.0f} MB")
        self.memory_available_label.configure(text=f"{metrics.get('memory_available_mb', 0):.0f} MB")
        self.gc_collections_label.configure(text=f"{metrics.get('gc_collections', 0)}")
    
    def _update_performance_graphs(self, metrics: Dict[str, Any]):
        """Update performance graphs with current data."""
        # Add current data point
        current_time = datetime.now()
        self.time_history.append(current_time)
        self.metrics_history.append(metrics)
        
        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        
        if len(self.metrics_history) > 1:
            times = list(self.time_history)
            
            # System performance graph
            cpu_data = [m.get('cpu_usage', 0) for m in self.metrics_history]
            memory_data = [m.get('memory_usage', 0) for m in self.metrics_history]
            
            self.ax1.plot(times, cpu_data, label='CPU', color='blue', linewidth=2)
            self.ax1.plot(times, memory_data, label='Memory', color='red', linewidth=2)
            self.ax1.set_title("System Performance", fontsize=12, fontweight='bold')
            self.ax1.set_ylabel("Usage (%)")
            self.ax1.grid(True, alpha=0.3)
            self.ax1.legend()
            
            # Operation timing graph
            ui_response_data = [m.get('ui_response_time', 0) for m in self.metrics_history]
            
            self.ax2.plot(times, ui_response_data, label='UI Response', color='green', linewidth=2)
            self.ax2.set_title("Operation Performance", fontsize=12, fontweight='bold')
            self.ax2.set_ylabel("Response Time (ms)")
            self.ax2.set_xlabel("Time")
            self.ax2.grid(True, alpha=0.3)
            
            # Format x-axis
            self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.ax2.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
            
        # Refresh canvas
        self.canvas.draw()
    
    def _update_operation_profiles(self):
        """Update operation profiles display."""
        try:
            profiles = self.performance_monitor.operation_profiles
            
            # Clear existing content
            self.profiles_textbox.delete("1.0", "end")
            
            if profiles:
                profile_lines = []
                for name, profile in sorted(profiles.items(), key=lambda x: x[1].avg_time, reverse=True)[:10]:
                    line = f"{name}: {profile.avg_time:.1f}ms avg ({profile.total_calls} calls)"
                    if profile.error_count > 0:
                        line += f" [{profile.error_count} errors]"
                    profile_lines.append(line)
                
                self.profiles_textbox.insert("1.0", "\n".join(profile_lines))
            else:
                self.profiles_textbox.insert("1.0", "No operation profiles available")
                
        except Exception as e:
            self.logger.error(f"Error updating operation profiles: {e}")
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        self.auto_refresh = self.auto_refresh_var.get()
        
        if self.auto_refresh:
            self._schedule_update()
            self.monitoring_status_label.configure(text="Monitoring: Active", text_color="green")
        else:
            if self.update_job:
                self.after_cancel(self.update_job)
                self.update_job = None
            self.monitoring_status_label.configure(text="Monitoring: Paused", text_color="orange")
    
    def _manual_refresh(self):
        """Manually refresh the dashboard."""
        self._update_dashboard()
    
    def _export_performance_data(self):
        """Export performance data to file."""
        try:
            from tkinter import filedialog
            import json
            
            # Get export location
            filename = filedialog.asksaveasfilename(
                title="Export Performance Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                # Prepare export data
                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'metrics_history': [
                        {
                            'timestamp': time.isoformat(),
                            'metrics': metrics
                        }
                        for time, metrics in zip(self.time_history, self.metrics_history)
                    ],
                    'operation_profiles': {
                        name: {
                            'total_calls': profile.total_calls,
                            'total_time': profile.total_time,
                            'avg_time': profile.avg_time,
                            'min_time': profile.min_time,
                            'max_time': profile.max_time,
                            'error_count': profile.error_count
                        }
                        for name, profile in self.performance_monitor.operation_profiles.items()
                    }
                }
                
                # Write to file
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                from tkinter import messagebox
                messagebox.showinfo("Export Complete", f"Performance data exported to:\n{filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting performance data: {e}")
            from tkinter import messagebox
            messagebox.showerror("Export Error", f"Failed to export performance data:\n{str(e)}")
    
    def destroy(self):
        """Clean up when dashboard is destroyed."""
        # Cancel scheduled updates
        if self.update_job:
            self.after_cancel(self.update_job)
        
        # Stop performance monitoring
        self.performance_monitor.stop_monitoring()
        
        # Close matplotlib figure
        plt.close(self.fig)
        
        super().destroy()
