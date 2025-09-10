"""
Threading utilities for Chamber Management Application.
Provides thread-safe operations for UI updates and background processing.
"""

import threading
import queue
import time
from typing import Callable, Any, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, Future
import weakref
from functools import wraps
import tkinter as tk

from .error_handling import handle_exceptions, ErrorHandler
from . import get_logger


class ThreadSafeOperation:
    """Container for thread-safe operation with callback handling."""
    
    def __init__(self, operation: Callable, args: tuple = (), kwargs: Dict = None, 
                 callback: Optional[Callable] = None, error_callback: Optional[Callable] = None):
        self.operation = operation
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.callback = callback
        self.error_callback = error_callback
        self.result = None
        self.error = None
        self.completed = False


class BackgroundTaskManager:
    """
    Manages background tasks with thread-safe UI updates.
    Handles heavy operations like matplotlib drawing and database queries.
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = get_logger(__name__)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ChamberApp")
        self.ui_queue = queue.Queue()
        self.running = True
        
        # Thread-safe tracking
        self._active_tasks = {}
        self._task_lock = threading.Lock()
        
        # UI update thread
        self._ui_thread = None
        self._start_ui_processor()
        
    def _start_ui_processor(self):
        """Start the UI update processor thread."""
        def process_ui_updates():
            while self.running:
                try:
                    # Process UI updates from background threads
                    try:
                        ui_update = self.ui_queue.get(timeout=0.1)
                        if ui_update is None:  # Shutdown signal
                            break
                        
                        # Execute UI update on main thread
                        if callable(ui_update):
                            ui_update()
                        else:
                            # Handle operation object
                            if hasattr(ui_update, 'callback') and ui_update.callback:
                                if ui_update.error:
                                    if ui_update.error_callback:
                                        ui_update.error_callback(ui_update.error)
                                else:
                                    ui_update.callback(ui_update.result)
                                    
                    except queue.Empty:
                        continue
                        
                except Exception as e:
                    self.logger.error(f"Error processing UI update: {e}")
                    
        self._ui_thread = threading.Thread(target=process_ui_updates, daemon=True)
        self._ui_thread.start()
    
    def submit_background_task(self, operation: Callable, args: tuple = (), kwargs: Dict = None,
                             callback: Optional[Callable] = None, 
                             error_callback: Optional[Callable] = None,
                             task_id: Optional[str] = None) -> Future:
        """
        Submit a task to run in background thread with optional UI callback.
        
        Args:
            operation: Function to execute in background
            args: Arguments for the operation
            kwargs: Keyword arguments for the operation
            callback: Function to call on UI thread with result
            error_callback: Function to call on UI thread with error
            task_id: Optional task identifier for tracking
            
        Returns:
            Future object for the submitted task
        """
        if not self.running:
            raise RuntimeError("TaskManager is shutting down")
            
        task_op = ThreadSafeOperation(operation, args, kwargs, callback, error_callback)
        
        def execute_task():
            try:
                # Execute the operation
                result = operation(*args, **(kwargs or {}))
                task_op.result = result
                task_op.completed = True
                
                # Queue UI update if callback provided
                if callback:
                    self.ui_queue.put(task_op)
                    
                return result
                
            except Exception as e:
                task_op.error = e
                task_op.completed = True
                
                # Queue error callback
                if error_callback:
                    self.ui_queue.put(task_op)
                else:
                    self.logger.error(f"Background task error: {e}", exc_info=True)
                    
                raise
        
        future = self.executor.submit(execute_task)
        
        # Track active tasks
        if task_id:
            with self._task_lock:
                self._active_tasks[task_id] = future
                
        return future
    
    def submit_ui_update(self, ui_callback: Callable):
        """Queue a UI update to be executed on the main thread."""
        if self.running:
            self.ui_queue.put(ui_callback)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by ID if it hasn't started yet."""
        with self._task_lock:
            if task_id in self._active_tasks:
                future = self._active_tasks.pop(task_id)
                return future.cancel()
        return False
    
    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        with self._task_lock:
            # Clean up completed tasks
            completed = [tid for tid, future in self._active_tasks.items() if future.done()]
            for tid in completed:
                self._active_tasks.pop(tid, None)
            return len(self._active_tasks)
    
    def get_task_statistics(self) -> Dict[str, int]:
        """Get task statistics for monitoring."""
        with self._task_lock:
            active_count = len(self._active_tasks)
            
        # Approximate completed and failed counts
        # In a full implementation, you would track these properly
        return {
            'active': active_count,
            'completed': max(0, len(self._active_tasks) * 2),  # Rough estimate
            'failed': 0  # Would need proper tracking
        }
    
    def shutdown(self, wait: bool = True):
        """Shutdown the task manager and clean up resources."""
        self.running = False
        
        # Signal UI processor to stop
        self.ui_queue.put(None)
        
        # Shutdown executor
        self.executor.shutdown(wait=wait)
        
        # Wait for UI thread
        if wait and self._ui_thread and self._ui_thread.is_alive():
            self._ui_thread.join(timeout=5.0)
        
        self.logger.info("Background task manager shutdown complete")


class MatplotlibThreadHelper:
    """Helper for thread-safe matplotlib operations."""
    
    def __init__(self, task_manager: BackgroundTaskManager):
        self.task_manager = task_manager
        self.logger = get_logger(__name__)
        
    def async_canvas_draw(self, canvas, figure, callback: Optional[Callable] = None):
        """Perform canvas drawing in background thread."""
        def draw_operation():
            try:
                # Prepare figure in background
                figure.tight_layout()
                return True
            except Exception as e:
                self.logger.error(f"Error preparing figure: {e}")
                raise
                
        def ui_callback(success):
            try:
                # Update canvas on UI thread
                if success and callback:
                    canvas.draw_idle()
                    callback()
            except Exception as e:
                self.logger.error(f"Error updating canvas: {e}")
                
        def error_callback(error):
            self.logger.error(f"Canvas draw error: {error}")
            
        return self.task_manager.submit_background_task(
            draw_operation,
            callback=ui_callback,
            error_callback=error_callback
        )
    
    def async_figure_creation(self, create_func: Callable, callback: Callable):
        """Create matplotlib figure in background thread."""
        def error_callback(error):
            self.logger.error(f"Figure creation error: {error}")
            
        return self.task_manager.submit_background_task(
            create_func,
            callback=callback,
            error_callback=error_callback
        )


class DatabaseThreadHelper:
    """Helper for thread-safe database operations."""
    
    def __init__(self, task_manager: BackgroundTaskManager):
        self.task_manager = task_manager
        self.logger = get_logger(__name__)
    
    def async_query(self, query_func: Callable, callback: Callable, 
                   error_callback: Optional[Callable] = None):
        """Execute database query in background thread."""
        def default_error_callback(error):
            self.logger.error(f"Database query error: {error}")
            
        return self.task_manager.submit_background_task(
            query_func,
            callback=callback,
            error_callback=error_callback or default_error_callback
        )
    
    def async_bulk_operation(self, operation_func: Callable, 
                           progress_callback: Optional[Callable] = None,
                           completion_callback: Optional[Callable] = None):
        """Execute bulk database operation with progress updates."""
        def wrapped_operation():
            def progress_update(current, total):
                if progress_callback:
                    self.task_manager.submit_ui_update(
                        lambda: progress_callback(current, total)
                    )
            
            return operation_func(progress_update)
        
        return self.task_manager.submit_background_task(
            wrapped_operation,
            callback=completion_callback
        )


def async_operation(task_manager: BackgroundTaskManager):
    """
    Decorator to make a method run asynchronously with UI callback.
    
    Usage:
        @async_operation(task_manager)
        def heavy_computation(self, data):
            # This runs in background thread
            result = process_data(data)
            return result
            
        # The decorated method will accept additional parameters:
        # callback: function to call with result on UI thread
        # error_callback: function to call with error on UI thread
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, callback=None, error_callback=None, **kwargs):
            return task_manager.submit_background_task(
                func, args, kwargs, callback, error_callback
            )
        return wrapper
    return decorator


def ui_thread_only(func):
    """
    Decorator to ensure a function only runs on the main UI thread.
    Raises an exception if called from a background thread.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() != threading.main_thread():
            raise RuntimeError(f"{func.__name__} must be called from the main UI thread")
        return func(*args, **kwargs)
    return wrapper


class ProgressTracker:
    """Thread-safe progress tracking for long-running operations."""
    
    def __init__(self, total_steps: int, update_callback: Optional[Callable] = None):
        self.total_steps = total_steps
        self.current_step = 0
        self.update_callback = update_callback
        self._lock = threading.Lock()
        
    def update(self, steps: int = 1, message: str = ""):
        """Update progress by specified number of steps."""
        with self._lock:
            self.current_step = min(self.current_step + steps, self.total_steps)
            percentage = (self.current_step / self.total_steps) * 100
            
            if self.update_callback:
                self.update_callback(self.current_step, self.total_steps, percentage, message)
                
    def set_progress(self, current: int, message: str = ""):
        """Set absolute progress value."""
        with self._lock:
            self.current_step = min(max(current, 0), self.total_steps)
            percentage = (self.current_step / self.total_steps) * 100
            
            if self.update_callback:
                self.update_callback(self.current_step, self.total_steps, percentage, message)
    
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        with self._lock:
            return self.current_step >= self.total_steps


# Global task manager instance
_global_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Get or create the global task manager instance."""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = BackgroundTaskManager()
    return _global_task_manager


def shutdown_task_manager():
    """Shutdown the global task manager."""
    global _global_task_manager
    if _global_task_manager:
        _global_task_manager.shutdown()
        _global_task_manager = None


def start_task_manager():
    """Start the global task manager."""
    # Task manager starts automatically when first accessed
    get_task_manager()


def stop_task_manager():
    """Stop the global task manager."""
    shutdown_task_manager()
