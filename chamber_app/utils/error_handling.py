"""
Standardized error handling utilities for the Chamber Management Application.
Provides consistent error handling patterns, logging, and user feedback mechanisms.
"""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, Union, Tuple
from enum import Enum
import logging

from .logging_config import get_logger


class ErrorSeverity(Enum):
    """Error severity levels for consistent categorization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization and handling."""
    DATABASE = "database"
    NETWORK = "network"
    UI = "ui"
    TELEMETRY = "telemetry"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    FILE_IO = "file_io"
    AUTHENTICATION = "authentication"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"


class ChamberError(Exception):
    """Base exception class for chamber application errors."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 context: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.original_exception = original_exception
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'context': self.context,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


class DatabaseError(ChamberError):
    """Database-specific errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, 
                 context: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.DATABASE, severity, context, original_exception)


class NetworkError(ChamberError):
    """Network-related errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.NETWORK, severity, context, original_exception)


class ValidationError(ChamberError):
    """Input validation errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.LOW,
                 context: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.VALIDATION, severity, context, original_exception)


class TelemetryError(ChamberError):
    """Telemetry-related errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[Dict[str, Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, ErrorCategory.TELEMETRY, severity, context, original_exception)


class ErrorHandler:
    """Centralized error handling utility."""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = get_logger(logger_name)
        self.error_counts = {}
        self.error_callbacks = {}
        
    def handle_error(self, error: Union[Exception, ChamberError], 
                    context: Optional[Dict[str, Any]] = None,
                    suppress: bool = False) -> Optional[ChamberError]:
        """
        Handle an error with consistent logging and optional callbacks.
        
        Args:
            error: The exception or ChamberError to handle
            context: Additional context information
            suppress: If True, don't re-raise the error
            
        Returns:
            ChamberError instance for further handling
        """
        # Convert to ChamberError if needed
        if isinstance(error, ChamberError):
            chamber_error = error
        else:
            chamber_error = ChamberError(
                message=str(error),
                category=self._categorize_error(error),
                severity=self._assess_severity(error),
                context=context,
                original_exception=error
            )
        
        # Update error counts
        error_key = f"{chamber_error.category.value}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log the error
        self._log_error(chamber_error)
        
        # Execute callbacks
        self._execute_callbacks(chamber_error)
        
        # Re-raise if not suppressing
        if not suppress:
            raise chamber_error
            
        return chamber_error
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Automatically categorize an error based on its type and message."""
        error_name = type(error).__name__.lower()
        error_message = str(error).lower()
        
        # Database errors
        if any(term in error_name for term in ['database', 'sqlite', 'sql']):
            return ErrorCategory.DATABASE
        if any(term in error_message for term in ['database', 'sql', 'sqlite', 'connection']):
            return ErrorCategory.DATABASE
            
        # Network errors
        if any(term in error_name for term in ['connection', 'network', 'timeout', 'socket']):
            return ErrorCategory.NETWORK
        if any(term in error_message for term in ['connection', 'network', 'timeout', 'websocket']):
            return ErrorCategory.NETWORK
            
        # Validation errors
        if any(term in error_name for term in ['value', 'type', 'attribute']):
            return ErrorCategory.VALIDATION
        if any(term in error_message for term in ['invalid', 'missing', 'required', 'format']):
            return ErrorCategory.VALIDATION
            
        # File I/O errors
        if any(term in error_name for term in ['file', 'io', 'permission']):
            return ErrorCategory.FILE_IO
        if any(term in error_message for term in ['file', 'directory', 'permission', 'not found']):
            return ErrorCategory.FILE_IO
            
        # Telemetry errors
        if any(term in error_message for term in ['telemetry', 'sensor', 'measurement']):
            return ErrorCategory.TELEMETRY
            
        return ErrorCategory.SYSTEM
    
    def _assess_severity(self, error: Exception) -> ErrorSeverity:
        """Assess error severity based on type and context."""
        error_name = type(error).__name__.lower()
        error_message = str(error).lower()
        
        # Critical errors
        if any(term in error_name for term in ['critical', 'fatal', 'system']):
            return ErrorSeverity.CRITICAL
        if any(term in error_message for term in ['critical', 'fatal', 'corrupted']):
            return ErrorSeverity.CRITICAL
            
        # High severity
        if any(term in error_name for term in ['database', 'connection']):
            return ErrorSeverity.HIGH
        if any(term in error_message for term in ['database', 'connection failed', 'cannot connect']):
            return ErrorSeverity.HIGH
            
        # Medium severity (default)
        if any(term in error_name for term in ['runtime', 'key', 'attribute']):
            return ErrorSeverity.MEDIUM
            
        # Low severity
        if any(term in error_name for term in ['value', 'type']):
            return ErrorSeverity.LOW
        if any(term in error_message for term in ['validation', 'invalid input']):
            return ErrorSeverity.LOW
            
        return ErrorSeverity.MEDIUM
    
    def _log_error(self, error: ChamberError):
        """Log error with appropriate level based on severity."""
        error_dict = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {error.message}", extra={'error_details': error_dict})
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY: {error.message}", extra={'error_details': error_dict})
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY: {error.message}", extra={'error_details': error_dict})
        else:
            self.logger.info(f"LOW SEVERITY: {error.message}", extra={'error_details': error_dict})
            
        # Include stack trace for higher severity errors
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and error.original_exception:
            self.logger.error("Stack trace:", exc_info=error.original_exception)
    
    def _execute_callbacks(self, error: ChamberError):
        """Execute registered callbacks for error handling."""
        category_callbacks = self.error_callbacks.get(error.category, [])
        global_callbacks = self.error_callbacks.get('global', [])
        
        for callback in category_callbacks + global_callbacks:
            try:
                callback(error)
            except Exception as callback_error:
                self.logger.error(f"Error in error callback: {callback_error}")
    
    def register_callback(self, category: Union[ErrorCategory, str], callback: Callable[[ChamberError], None]):
        """Register a callback for specific error categories."""
        if isinstance(category, ErrorCategory):
            category = category.value
            
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'categories': {
                category.value: sum(1 for key in self.error_counts.keys() if key.startswith(category.value))
                for category in ErrorCategory
            }
        }


def handle_exceptions(category: ErrorCategory = ErrorCategory.SYSTEM, 
                     severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                     suppress: bool = False,
                     return_value: Any = None):
    """
    Decorator for automatic exception handling.
    
    Args:
        category: Error category for the exceptions
        severity: Default severity level
        suppress: If True, suppress exceptions and return return_value
        return_value: Value to return if exception is suppressed
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ChamberError:
                # Re-raise ChamberErrors as-is
                raise
            except Exception as e:
                error_handler = ErrorHandler(func.__module__)
                context = {
                    'function': func.__name__,
                    'args': str(args)[:100] if args else None,
                    'kwargs': str(kwargs)[:100] if kwargs else None
                }
                
                chamber_error = ChamberError(
                    message=f"Error in {func.__name__}: {str(e)}",
                    category=category,
                    severity=severity,
                    context=context,
                    original_exception=e
                )
                
                if suppress:
                    error_handler.handle_error(chamber_error, suppress=True)
                    return return_value
                else:
                    error_handler.handle_error(chamber_error, suppress=False)
        
        return wrapper
    return decorator


def safe_operation(operation: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[ChamberError]]:
    """
    Execute an operation safely and return success status, result, and any error.
    
    Args:
        operation: Function to execute
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Tuple of (success, result, error)
    """
    try:
        result = operation(*args, **kwargs)
        return True, result, None
    except Exception as e:
        error_handler = ErrorHandler()
        chamber_error = error_handler.handle_error(e, suppress=True)
        return False, None, chamber_error


# Global error handler instance
global_error_handler = ErrorHandler('chamber_app.global')


def log_and_continue(func: Callable) -> Callable:
    """Decorator that logs errors but allows execution to continue."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            global_error_handler.handle_error(e, 
                context={'function': func.__name__}, 
                suppress=True)
            return None
    return wrapper
