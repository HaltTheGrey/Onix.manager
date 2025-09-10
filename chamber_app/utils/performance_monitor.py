"""
Performance monitoring and metrics collection for Chamber Management Application.
Tracks system performance, UI responsiveness, and resource usage.
"""

import time
import threading
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
import weakref
import functools

from . import get_logger


@dataclass
class PerformanceMetric:
    """Container for a single performance metric."""
    name: str
    value: float
    timestamp: datetime
    category: str = "general"
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OperationProfile:
    """Profile data for a monitored operation."""
    name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_called: Optional[datetime] = None
    error_count: int = 0
    
    def add_execution(self, duration: float, has_error: bool = False):
        """Add execution data to the profile."""
        self.total_calls += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.total_calls
        self.last_called = datetime.now()
        
        if has_error:
            self.error_count += 1


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    Tracks UI responsiveness, resource usage, and operation performance.
    """
    
    def __init__(self, history_size: int = 1000):
        self.logger = get_logger(__name__)
        self.history_size = history_size
        
        # Metric storage
        self.metrics_history: deque = deque(maxlen=history_size)
        self.operation_profiles: Dict[str, OperationProfile] = {}
        self.ui_responsiveness_history: deque = deque(maxlen=100)
        
        # System monitoring
        self.process = psutil.Process()
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_lock = threading.Lock()
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage_warning': 80.0,
            'memory_usage_warning': 80.0,
            'ui_response_warning': 100.0,  # milliseconds
            'operation_slow_warning': 1000.0,  # milliseconds
        }
        
        # Callbacks for alerts
        self.alert_callbacks: List[Callable] = []
        
    def start_monitoring(self, interval: float = 1.0):
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self._collect_system_metrics()
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Error in performance monitoring: {e}")
                    
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Performance monitoring stopped")
    
    def _collect_system_metrics(self):
        """Collect system-level performance metrics."""
        try:
            timestamp = datetime.now()
            
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self._add_metric("cpu_usage", cpu_percent, timestamp, "system")
            
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()
            self._add_metric("memory_usage_mb", memory_mb, timestamp, "system")
            self._add_metric("memory_usage_percent", memory_percent, timestamp, "system")
            
            # Thread count
            thread_count = threading.active_count()
            self._add_metric("thread_count", thread_count, timestamp, "system")
            
            # GC statistics
            gc_stats = gc.get_stats()
            if gc_stats:
                self._add_metric("gc_collections_gen0", gc_stats[0]['collections'], timestamp, "gc")
                self._add_metric("gc_collected_gen0", gc_stats[0]['collected'], timestamp, "gc")
            
            # Check thresholds and trigger alerts
            self._check_thresholds(cpu_percent, memory_percent)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _add_metric(self, name: str, value: float, timestamp: datetime, category: str = "general", 
                   tags: Dict[str, str] = None):
        """Add a metric to the history."""
        metric = PerformanceMetric(name, value, timestamp, category, tags or {})
        with self.monitor_lock:
            self.metrics_history.append(metric)
    
    def _check_thresholds(self, cpu_percent: float, memory_percent: float):
        """Check performance thresholds and trigger alerts."""
        alerts = []
        
        if cpu_percent > self.thresholds['cpu_usage_warning']:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
            
        if memory_percent > self.thresholds['memory_usage_warning']:
            alerts.append(f"High memory usage: {memory_percent:.1f}%")
        
        # Check UI responsiveness
        if self.ui_responsiveness_history:
            recent_ui_times = list(self.ui_responsiveness_history)[-10:]
            avg_ui_time = sum(recent_ui_times) / len(recent_ui_times)
            if avg_ui_time > self.thresholds['ui_response_warning']:
                alerts.append(f"Slow UI responsiveness: {avg_ui_time:.1f}ms")
        
        # Trigger alert callbacks
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable[[str], None]):
        """Add a callback for performance alerts."""
        self.alert_callbacks.append(callback)
    
    def record_ui_operation(self, duration_ms: float):
        """Record UI operation duration for responsiveness tracking."""
        self.ui_responsiveness_history.append(duration_ms)
        self._add_metric("ui_responsiveness", duration_ms, datetime.now(), "ui")
    
    def get_operation_profile(self, operation_name: str) -> OperationProfile:
        """Get or create an operation profile."""
        if operation_name not in self.operation_profiles:
            self.operation_profiles[operation_name] = OperationProfile(operation_name)
        return self.operation_profiles[operation_name]
    
    def get_metrics_summary(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if time_window is None:
            time_window = timedelta(minutes=5)
            
        cutoff_time = datetime.now() - time_window
        
        with self.monitor_lock:
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.name].append(metric.value)
        
        summary = {}
        for name, values in metric_groups.items():
            summary[name] = {
                'current': values[-1] if values else 0,
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        # Add operation profiles
        summary['operations'] = {
            name: {
                'total_calls': profile.total_calls,
                'avg_time_ms': profile.avg_time * 1000,
                'max_time_ms': profile.max_time * 1000,
                'error_rate': profile.error_count / max(profile.total_calls, 1) * 100
            }
            for name, profile in self.operation_profiles.items()
        }
        
        return summary
    
    def get_system_health(self) -> Dict[str, str]:
        """Get overall system health assessment."""
        summary = self.get_metrics_summary()
        
        if not summary:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        health_issues = []
        
        # Check CPU
        if 'cpu_usage' in summary:
            cpu_current = summary['cpu_usage']['current']
            if cpu_current > 90:
                health_issues.append(f"Critical CPU usage: {cpu_current:.1f}%")
            elif cpu_current > 70:
                health_issues.append(f"High CPU usage: {cpu_current:.1f}%")
        
        # Check memory
        if 'memory_usage_percent' in summary:
            mem_current = summary['memory_usage_percent']['current']
            if mem_current > 90:
                health_issues.append(f"Critical memory usage: {mem_current:.1f}%")
            elif mem_current > 70:
                health_issues.append(f"High memory usage: {mem_current:.1f}%")
        
        # Check UI responsiveness
        if 'ui_responsiveness' in summary:
            ui_avg = summary['ui_responsiveness']['average']
            if ui_avg > 200:
                health_issues.append(f"Poor UI responsiveness: {ui_avg:.1f}ms")
            elif ui_avg > 100:
                health_issues.append(f"Slow UI responsiveness: {ui_avg:.1f}ms")
        
        if not health_issues:
            return {'status': 'healthy', 'message': 'All systems operating normally'}
        elif len(health_issues) > 3:
            return {'status': 'critical', 'message': f"Multiple issues detected: {'; '.join(health_issues[:3])}..."}
        else:
            return {'status': 'warning', 'message': '; '.join(health_issues)}


def profile_operation(monitor: PerformanceMonitor, operation_name: str):
    """
    Decorator to profile function execution time and track performance.
    
    Usage:
        @profile_operation(monitor, "data_update")
        def update_data(self):
            # This operation will be profiled
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error_occurred = False
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                raise
            finally:
                duration = time.time() - start_time
                profile = monitor.get_operation_profile(operation_name)
                profile.add_execution(duration, error_occurred)
                
                # Log slow operations
                duration_ms = duration * 1000
                if duration_ms > monitor.thresholds['operation_slow_warning']:
                    monitor.logger.warning(f"Slow operation '{operation_name}': {duration_ms:.1f}ms")
                
        return wrapper
    return decorator


def ui_operation_timer(monitor: PerformanceMonitor):
    """
    Decorator to time UI operations and track responsiveness.
    
    Usage:
        @ui_operation_timer(monitor)
        def update_ui(self):
            # UI update will be timed
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start_time) * 1000
                monitor.record_ui_operation(duration_ms)
        return wrapper
    return decorator


class MemoryLeakDetector:
    """Detects potential memory leaks by tracking object creation and destruction."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.object_counts = defaultdict(int)
        self.tracked_objects = weakref.WeakSet()
        
    def track_object(self, obj, category: str = "general"):
        """Track an object for potential memory leaks."""
        self.tracked_objects.add(obj)
        self.object_counts[category] += 1
    
    def check_leaks(self) -> Dict[str, int]:
        """Check for potential memory leaks and return object counts."""
        # Force garbage collection
        gc.collect()
        
        # Count surviving objects
        surviving_counts = defaultdict(int)
        for obj in self.tracked_objects:
            obj_type = type(obj).__name__
            surviving_counts[obj_type] += 1
        
        # Log significant object counts
        for obj_type, count in surviving_counts.items():
            if count > 100:  # Threshold for concern
                self.logger.warning(f"High object count for {obj_type}: {count}")
        
        return dict(surviving_counts)


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def start_performance_monitoring():
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_performance_monitoring():
    """Stop global performance monitoring."""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()


def get_performance_summary() -> Dict[str, Any]:
    """Get a summary of current performance metrics."""
    monitor = get_performance_monitor()
    return monitor.get_metrics_summary()


def get_system_health() -> Dict[str, str]:
    """Get overall system health status."""
    monitor = get_performance_monitor()
    return monitor.get_system_health()
