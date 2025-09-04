# -*- coding: utf-8 -*-
"""
Notification and alert system for the Chamber Management Application.
Provides real-time notifications, alerts, and system messages.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
import threading
import queue
import json
from pathlib import Path
from tkinter import messagebox

from ..utils.logging_config import get_logger


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Notification:
    """Represents a single notification."""
    
    def __init__(self, 
                 title: str,
                 message: str,
                 notification_type: NotificationType = NotificationType.INFO,
                 priority: NotificationPriority = NotificationPriority.NORMAL,
                 chamber_id: Optional[str] = None,
                 category: str = "general",
                 data: Optional[Dict[str, Any]] = None,
                 auto_dismiss: bool = True,
                 dismiss_after: int = 5000):  # milliseconds
        
        self.id = f"notif_{datetime.now().timestamp()}"
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.chamber_id = chamber_id
        self.category = category
        self.data = data or {}
        self.auto_dismiss = auto_dismiss
        self.dismiss_after = dismiss_after
        self.created_at = datetime.now()
        self.read = False
        self.dismissed = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'priority': self.priority.value,
            'chamber_id': self.chamber_id,
            'category': self.category,
            'data': self.data,
            'auto_dismiss': self.auto_dismiss,
            'dismiss_after': self.dismiss_after,
            'created_at': self.created_at.isoformat(),
            'read': self.read,
            'dismissed': self.dismissed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary."""
        notif = cls(
            title=data['title'],
            message=data['message'],
            notification_type=NotificationType(data['type']),
            priority=NotificationPriority(data['priority']),
            chamber_id=data.get('chamber_id'),
            category=data.get('category', 'general'),
            data=data.get('data', {}),
            auto_dismiss=data.get('auto_dismiss', True),
            dismiss_after=data.get('dismiss_after', 5000)
        )
        
        notif.id = data['id']
        notif.created_at = datetime.fromisoformat(data['created_at'])
        notif.read = data.get('read', False)
        notif.dismissed = data.get('dismissed', False)
        
        return notif


class NotificationRule:
    """Rule for automatic notification generation."""
    
    def __init__(self,
                 name: str,
                 condition: Callable[[Dict[str, Any]], bool],
                 notification_template: Dict[str, Any],
                 enabled: bool = True,
                 cooldown_minutes: int = 5):
        
        self.name = name
        self.condition = condition
        self.notification_template = notification_template
        self.enabled = enabled
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered = None
    
    def should_trigger(self, data: Dict[str, Any]) -> bool:
        """Check if this rule should trigger a notification."""
        if not self.enabled:
            return False
        
        # Check cooldown
        if self.last_triggered:
            time_since_last = datetime.now() - self.last_triggered
            if time_since_last < timedelta(minutes=self.cooldown_minutes):
                return False
        
        # Check condition
        try:
            return self.condition(data)
        except Exception:
            return False
    
    def create_notification(self, data: Dict[str, Any]) -> Notification:
        """Create notification from template with data."""
        template = self.notification_template.copy()
        
        # Replace placeholders in template
        for key, value in template.items():
            if isinstance(value, str) and '{' in value:
                try:
                    template[key] = value.format(**data)
                except (KeyError, ValueError):
                    pass  # Keep original value if formatting fails
        
        self.last_triggered = datetime.now()
        
        return Notification(
            title=template.get('title', 'Alert'),
            message=template.get('message', 'An event occurred'),
            notification_type=NotificationType(template.get('type', 'info')),
            priority=NotificationPriority(template.get('priority', 'normal')),
            chamber_id=template.get('chamber_id'),
            category=template.get('category', 'rule'),
            data=data
        )


class NotificationManager:
    """Manages notifications and alerts for the application."""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        
        self.notifications: List[Notification] = []
        self.rules: List[NotificationRule] = []
        self.subscribers: List[Callable[[Notification], None]] = []
        
        self.notification_queue = queue.Queue()
        self.running = False
        
        self._load_rules()
        self._load_notifications()
    
    def start(self):
        """Start the notification manager."""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Notification manager started")
    
    def stop(self):
        """Stop the notification manager."""
        self.running = False
        self._save_notifications()
        self.logger.info("Notification manager stopped")
    
    def add_notification(self, notification: Notification):
        """Add a new notification."""
        self.notifications.append(notification)
        self._notify_subscribers(notification)
        self.logger.info(f"Notification added: {notification.title}")
    
    def create_notification(self,
                          title: str,
                          message: str,
                          notification_type: NotificationType = NotificationType.INFO,
                          priority: NotificationPriority = NotificationPriority.NORMAL,
                          chamber_id: Optional[str] = None,
                          category: str = "manual") -> Notification:
        """Create and add a new notification."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            chamber_id=chamber_id,
            category=category
        )
        
        self.add_notification(notification)
        return notification
    
    def subscribe(self, callback: Callable[[Notification], None]):
        """Subscribe to notification events."""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[Notification], None]):
        """Unsubscribe from notification events."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def mark_read(self, notification_id: str):
        """Mark a notification as read."""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                self.logger.debug(f"Notification marked as read: {notification_id}")
                break
    
    def dismiss(self, notification_id: str):
        """Dismiss a notification."""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.dismissed = True
                self.logger.debug(f"Notification dismissed: {notification_id}")
                break
    
    def get_notifications(self, 
                         include_dismissed: bool = False,
                         category: Optional[str] = None,
                         chamber_id: Optional[str] = None) -> List[Notification]:
        """Get notifications with optional filters."""
        notifications = self.notifications
        
        if not include_dismissed:
            notifications = [n for n in notifications if not n.dismissed]
        
        if category:
            notifications = [n for n in notifications if n.category == category]
        
        if chamber_id:
            notifications = [n for n in notifications if n.chamber_id == chamber_id]
        
        # Sort by priority and creation time
        notifications.sort(key=lambda n: (n.priority.value, n.created_at), reverse=True)
        
        return notifications
    
    def get_unread_count(self, chamber_id: Optional[str] = None) -> int:
        """Get count of unread notifications."""
        notifications = self.get_notifications(chamber_id=chamber_id)
        return len([n for n in notifications if not n.read])
    
    def clear_old_notifications(self, days: int = 30):
        """Clear notifications older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_notifications = [
            n for n in self.notifications 
            if n.created_at < cutoff_date and n.dismissed
        ]
        
        for notification in old_notifications:
            self.notifications.remove(notification)
        
        self.logger.info(f"Cleared {len(old_notifications)} old notifications")
    
    def add_rule(self, rule: NotificationRule):
        """Add a notification rule."""
        self.rules.append(rule)
        self.logger.info(f"Notification rule added: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a notification rule."""
        self.rules = [r for r in self.rules if r.name != rule_name]
        self.logger.info(f"Notification rule removed: {rule_name}")
    
    def check_rules(self, data: Dict[str, Any]):
        """Check all rules against provided data."""
        for rule in self.rules:
            if rule.should_trigger(data):
                notification = rule.create_notification(data)
                self.add_notification(notification)
    
    def _notify_subscribers(self, notification: Notification):
        """Notify all subscribers of a new notification."""
        for callback in self.subscribers:
            try:
                callback(notification)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber: {e}")
    
    def _worker_loop(self):
        """Worker loop for processing notifications."""
        while self.running:
            try:
                # Process any queued notifications
                while not self.notification_queue.empty():
                    notification = self.notification_queue.get_nowait()
                    self.add_notification(notification)
                
                # Clean up old notifications periodically
                if datetime.now().minute % 30 == 0:  # Every 30 minutes
                    self.clear_old_notifications()
                
                threading.Event().wait(1)  # Sleep for 1 second
                
            except Exception as e:
                self.logger.error(f"Error in notification worker loop: {e}")
    
    def _load_rules(self):
        """Load notification rules from configuration."""
        # Add default rules
        self._add_default_rules()
          # Load custom rules from file if it exists
        rules_file = Path("config/notification_rules.json")
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                
                for rule_data in rules_data:
                    try:
                        # Create rule from configuration data
                        # Only load basic rule metadata, not functions (which can't be serialized)
                        rule_name = rule_data.get('name', 'unknown_rule')
                        self.logger.info(f"Loaded notification rule configuration: {rule_name}")
                        
                        # In a real implementation, you would:
                        # 1. Parse rule conditions from a DSL or predefined condition types
                        # 2. Map rule names to predefined condition functions
                        # 3. Validate and instantiate NotificationRule objects
                        
                        # For now, we log that the rule was found but defer to default rules
                        # since function serialization is complex
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing notification rule: {e}")
                        continue
                    
            except Exception as e:
                self.logger.error(f"Error loading notification rules: {e}")
    
    def _add_default_rules(self):
        """Add default notification rules."""
        # High temperature alert
        temp_rule = NotificationRule(
            name="high_temperature",
            condition=lambda data: data.get('temperature', 0) > 80,
            notification_template={
                'title': 'High Temperature Alert',
                'message': 'Chamber {chamber_id} temperature is {temperature}°C',
                'type': 'warning',
                'priority': 'high',
                'category': 'temperature'
            }
        )
        self.add_rule(temp_rule)
        
        # Low pressure alert
        pressure_rule = NotificationRule(
            name="low_pressure",
            condition=lambda data: data.get('pressure', 100) < 10,
            notification_template={
                'title': 'Low Pressure Alert',
                'message': 'Chamber {chamber_id} pressure is {pressure} mbar',
                'type': 'warning',
                'priority': 'high',
                'category': 'pressure'
            }
        )
        self.add_rule(pressure_rule)
        
        # Chamber error state
        error_rule = NotificationRule(
            name="chamber_error",
            condition=lambda data: data.get('status', '').lower() == 'error',
            notification_template={
                'title': 'Chamber Error',
                'message': 'Chamber {chamber_id} has entered error state',
                'type': 'error',
                'priority': 'critical',
                'category': 'status'
            }
        )
        self.add_rule(error_rule)
    
    def _load_notifications(self):
        """Load saved notifications from file."""
        notifications_file = Path("data/notifications.json")
        if notifications_file.exists():
            try:
                with open(notifications_file, 'r') as f:
                    notifications_data = json.load(f)
                
                for notif_data in notifications_data:
                    notification = Notification.from_dict(notif_data)
                    self.notifications.append(notification)
                
                self.logger.info(f"Loaded {len(self.notifications)} notifications")
                
            except Exception as e:
                self.logger.error(f"Error loading notifications: {e}")
    
    def _save_notifications(self):
        """Save notifications to file."""
        try:
            notifications_file = Path("data/notifications.json")
            notifications_file.parent.mkdir(exist_ok=True)
            
            # Only save last 1000 notifications to prevent file from growing too large
            recent_notifications = self.notifications[-1000:]
            
            notifications_data = [n.to_dict() for n in recent_notifications]
            
            with open(notifications_file, 'w') as f:
                json.dump(notifications_data, f, indent=2)
            
            self.logger.debug("Notifications saved to file")
            
        except Exception as e:
            self.logger.error(f"Error saving notifications: {e}")


class NotificationToast(ctk.CTkToplevel):
    """Toast notification widget."""
    
    def __init__(self, parent, notification: Notification):
        super().__init__(parent)
        
        self.notification = notification
        self._setup_window()
        self._setup_ui()
        
        if notification.auto_dismiss:
            self.after(notification.dismiss_after, self.destroy)
    
    def _setup_window(self):
        """Set up the toast window."""
        self.withdraw()  # Hide initially
        
        # Configure window
        self.title("")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Position at bottom right
        window_width = 350
        window_height = 120
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Style based on notification type
        if self.notification.type == NotificationType.ERROR:
            bg_color = "#ff4444"
        elif self.notification.type == NotificationType.WARNING:
            bg_color = "#ff8800"
        elif self.notification.type == NotificationType.SUCCESS:
            bg_color = "#44aa44"
        else:
            bg_color = "#4488cc"
        
        self.configure(fg_color=bg_color)
        
        # Show with fade-in effect
        self.after(10, self._fade_in)
    
    def _setup_ui(self):
        """Set up the toast UI."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="×",
            width=20,
            height=20,
            command=self.destroy
        )
        close_btn.pack(anchor="ne", padx=5, pady=5)
        
        # Icon (based on type)
        icon_text = {
            NotificationType.INFO: "ℹ️",
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.CRITICAL: "🚨"
        }.get(self.notification.type, "ℹ️")
        
        icon_label = ctk.CTkLabel(
            main_frame,
            text=icon_text,
            font=("", 20)
        )
        icon_label.pack(side="left", padx=10, pady=10)
        
        # Text content
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=5, pady=10)
        
        title_label = ctk.CTkLabel(
            content_frame,
            text=self.notification.title,
            font=("", 12, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x")
        
        message_label = ctk.CTkLabel(
            content_frame,
            text=self.notification.message,
            font=("", 10),
            anchor="w",
            wraplength=250
        )
        message_label.pack(fill="x", pady=(2, 0))
        
        # Timestamp
        time_text = self.notification.created_at.strftime("%H:%M:%S")
        time_label = ctk.CTkLabel(
            content_frame,
            text=time_text,
            font=("", 8),
            anchor="w"
        )
        time_label.pack(fill="x", pady=(2, 0))
    
    def _fade_in(self):
        """Fade in the toast."""
        self.deiconify()
        self.attributes("-alpha", 0.0)
          # Animate fade-in
        alpha = 0.0
        while alpha < 1.0:
            alpha += 0.1
            self.attributes("-alpha", alpha)
            self.update()
            # Small delay for smooth animation
            self.after(20, lambda: None)


class NotificationPanel(ctk.CTkFrame):
    """Panel for displaying and managing notifications."""
    
    def __init__(self, parent, notification_manager: NotificationManager, app=None):
        super().__init__(parent)
        
        self.notification_manager = notification_manager
        self.app = app  # Store app reference for chamber operations
        self.logger = get_logger(__name__)
        
        self._setup_ui()
        self._refresh_notifications()
        
        # Subscribe to new notifications
        self.notification_manager.subscribe(self._on_new_notification)
    
    def _setup_ui(self):
        """Set up the notification panel UI."""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = ctk.CTkLabel(header_frame, text="Notifications", font=("", 16, "bold"))
        title_label.pack(side="left", padx=10, pady=5)
        
        # Controls
        self.unread_count_label = ctk.CTkLabel(header_frame, text="")
        self.unread_count_label.pack(side="left", padx=10, pady=5)
        
        clear_all_btn = ctk.CTkButton(
            header_frame,
            text="Clear All",
            width=80,
            command=self._clear_all
        )
        clear_all_btn.pack(side="right", padx=5, pady=5)
        
        mark_all_read_btn = ctk.CTkButton(
            header_frame,
            text="Mark All Read",
            width=100,
            command=self._mark_all_read
        )
        mark_all_read_btn.pack(side="right", padx=5, pady=5)
        
        # Filter options
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Filter:").pack(side="left", padx=5, pady=5)
        
        self.filter_var = ctk.StringVar(value="All")
        filter_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.filter_var,
            values=["All", "Unread", "Errors", "Warnings", "Info"],
            command=self._on_filter_change
        )
        filter_combo.pack(side="left", padx=5, pady=5)
        
        # Notifications list
        self.notifications_frame = ctk.CTkScrollableFrame(self)
        self.notifications_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _refresh_notifications(self):
        """Refresh the notifications display."""
        # Clear existing widgets
        for widget in self.notifications_frame.winfo_children():
            widget.destroy()
        
        # Get filtered notifications
        notifications = self._get_filtered_notifications()
        
        # Update unread count
        unread_count = self.notification_manager.get_unread_count()
        self.unread_count_label.configure(text=f"({unread_count} unread)")
        
        # Display notifications
        for notification in notifications:
            self._create_notification_widget(notification)
    
    def _get_filtered_notifications(self) -> List[Notification]:
        """Get notifications based on current filter."""
        filter_value = self.filter_var.get()
        notifications = self.notification_manager.get_notifications()
        
        if filter_value == "Unread":
            return [n for n in notifications if not n.read]
        elif filter_value == "Errors":
            return [n for n in notifications if n.type in [NotificationType.ERROR, NotificationType.CRITICAL]]
        elif filter_value == "Warnings":
            return [n for n in notifications if n.type == NotificationType.WARNING]
        elif filter_value == "Info":
            return [n for n in notifications if n.type in [NotificationType.INFO, NotificationType.SUCCESS]]
        else:
            return notifications
    
    def _create_notification_widget(self, notification: Notification):
        """Create a widget for a single notification."""
        # Main frame
        frame = ctk.CTkFrame(self.notifications_frame)
        frame.pack(fill="x", pady=2)
        
        # Style based on type and read status
        if not notification.read:
            frame.configure(border_width=2, border_color="#4488cc")
        
        # Content frame
        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header with title and timestamp
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x")
        
        title_text = notification.title
        if not notification.read:
            title_text = f"● {title_text}"
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=("", 12, "bold"),
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True)
        
        time_label = ctk.CTkLabel(
            header_frame,
            text=notification.created_at.strftime("%m/%d %H:%M"),
            font=("", 10),
            anchor="e"
        )
        time_label.pack(side="right", padx=5)
        
        # Type indicator
        type_colors = {
            NotificationType.INFO: "#4488cc",
            NotificationType.SUCCESS: "#44aa44",
            NotificationType.WARNING: "#ff8800",
            NotificationType.ERROR: "#ff4444",
            NotificationType.CRITICAL: "#cc2222"
        }
        
        type_indicator = ctk.CTkFrame(
            header_frame,
            width=10,
            height=10,
            fg_color=type_colors.get(notification.type, "#4488cc")
        )
        type_indicator.pack(side="right", padx=5)
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=notification.message,
            font=("", 10),
            anchor="w",
            wraplength=400
        )
        message_label.pack(fill="x", pady=(5, 0))
        
        # Action buttons
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(5, 0))
        
        if not notification.read:
            read_btn = ctk.CTkButton(
                actions_frame,                text="Mark Read",
                width=80,
                height=25,
                command=lambda: self._mark_read(notification)
            )
            read_btn.pack(side="left", padx=2)
            
            dismiss_btn = ctk.CTkButton(
                actions_frame,
                text="Dismiss",
                width=60,
                height=25,
                command=lambda: self._dismiss(notification)
            )
            dismiss_btn.pack(side="left", padx=2)
          # Chamber link if applicable
        if notification.chamber_id:
            chamber_btn = ctk.CTkButton(
                actions_frame,
                text=f"View Chamber {notification.chamber_id}",
                width=120,
                height=25,
                command=lambda: self._view_chamber(notification.chamber_id) if notification.chamber_id else None
            )
            chamber_btn.pack(side="right", padx=2)
    
    def _mark_read(self, notification: Notification):
        """Mark a notification as read."""
        self.notification_manager.mark_read(notification.id)
        self._refresh_notifications()
    
    def _dismiss(self, notification: Notification):
        """Dismiss a notification."""
        self.notification_manager.dismiss(notification.id)
        self._refresh_notifications()
    
    def _mark_all_read(self):
        """Mark all notifications as read."""
        for notification in self.notification_manager.get_notifications():
            if not notification.read:
                self.notification_manager.mark_read(notification.id)
        self._refresh_notifications()
    
    def _clear_all(self):
        """Clear all notifications."""
        for notification in self.notification_manager.get_notifications():
            self.notification_manager.dismiss(notification.id)
        self._refresh_notifications()
    
    def _view_chamber(self, chamber_id: str):
        """Navigate to chamber view."""
        try:
            # Check if app is available
            if not self.app:
                messagebox.showerror("Error", "Application reference not available")
                return
                
            # Get the chamber information
            chamber = self.app.get_chamber(chamber_id)
            if not chamber:
                messagebox.showerror("Error", f"Chamber {chamber_id} not found")
                return
            
            # Create chamber detail dialog
            self._show_chamber_detail_dialog(chamber)
            
        except Exception as e:
            self.logger.error(f"Error in chamber view: {e}")
            messagebox.showerror("Error", f"Failed to view chamber: {e}")
    
    def _show_chamber_detail_dialog(self, chamber):
        """Show detailed chamber information dialog."""
        import customtkinter as ctk
          # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Chamber Details - {chamber.name}")
        dialog.geometry("700x600")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (self.winfo_width() // 2) - (700 // 2) + self.winfo_rootx()
        y = (self.winfo_height() // 2) - (600 // 2) + self.winfo_rooty()
        dialog.geometry(f"700x600+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{chamber.name} ({chamber.type.value})",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Status indicator
        status_text = chamber.state_manager.current_status.value if chamber.state_manager.current_status else "No Status"
        status_color = "red" if chamber.state_manager.current_status else "green"
        
        status_label = ctk.CTkLabel(
            header_frame,
            text=f"●  {chamber.state_manager.current_state.value.title()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=status_color
        )
        status_label.pack()
        
        # Scrollable content
        scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        scrollable_frame.pack(fill="both", expand=True)
        
        # Basic Information Section
        self._add_info_section(scrollable_frame, "Basic Information", [
            ("ID", chamber.id),
            ("Type", chamber.type.value),
            ("Current State", chamber.state_manager.current_state.value),
            ("Current Status", status_text),
            ("Connection", "Connected" if chamber.is_connected else "Disconnected"),
            ("Connection Type", chamber.connection_type or "None")
        ])
        
        # Timing Information
        state_duration = chamber.state_manager.get_state_duration()
        state_duration_text = f"{state_duration // 3600:.0f}h {(state_duration % 3600) // 60:.0f}m"
        
        status_duration = chamber.state_manager.get_status_duration()
        status_duration_text = f"{status_duration // 3600:.0f}h {(status_duration % 3600) // 60:.0f}m" if status_duration else "N/A"
        
        self._add_info_section(scrollable_frame, "Timing", [
            ("In Current State", state_duration_text),
            ("In Current Status", status_duration_text),
            ("Created", chamber.created_at.strftime("%Y-%m-%d %H:%M:%S")),
            ("Last Updated", chamber.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
        ])
        
        # Telemetry Information
        if chamber.last_telemetry:
            telemetry_info = [
                ("Temperature", f"{chamber.last_telemetry.temperature:.2f}°C"),
                ("Vacuum Level", f"{chamber.last_telemetry.vacuum_level:.2e} Torr"),
                ("Humidity", f"{chamber.last_telemetry.humidity:.1f}%"),
                ("Pressure", f"{chamber.last_telemetry.pressure:.2f} hPa"),
                ("Elapsed Time", f"{chamber.last_telemetry.elapsed_time:.0f} seconds"),
                ("Last Reading", chamber.last_telemetry.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            ]
        else:
            telemetry_info = [("Status", "No telemetry data available")]
        
        self._add_info_section(scrollable_frame, "Telemetry", telemetry_info)
        
        # Work Requests
        active_requests = chamber.get_active_work_requests()
        if active_requests:
            wr_info = []
            for wr in active_requests[:5]:  # Show up to 5 requests
                wr_info.append((f"WR-{wr.id[:8]}", f"{wr.title} ({wr.status})"))
            if len(active_requests) > 5:
                wr_info.append(("...", f"And {len(active_requests) - 5} more"))
        else:
            wr_info = [("Status", "No active work requests")]
        
        self._add_info_section(scrollable_frame, "Work Requests", wr_info)
        
        # Action buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Navigate to chamber (close this dialog and switch main view)
        nav_btn = ctk.CTkButton(
            button_frame,
            text="Go to Chamber",
            command=lambda: self._navigate_to_chamber(chamber, dialog),
            fg_color="blue",
            hover_color="dark blue"
        )
        nav_btn.pack(side="left", padx=(0, 10))
        
        # Create work request
        wr_btn = ctk.CTkButton(
            button_frame,
            text="Create Work Request",
            command=lambda: self._create_work_request_for_chamber(chamber),
            fg_color="orange",
            hover_color="dark orange"
        )
        wr_btn.pack(side="left", padx=(0, 10))
          # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=dialog.destroy
        )
        close_btn.pack(side="right")
    
    def _add_info_section(self, parent, title: str, info_list: list):
        """Add an information section to the dialog."""
        import customtkinter as ctk
        
        # Section frame
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15), padx=10)
        
        # Section title
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Information grid
        info_frame = ctk.CTkFrame(section_frame)
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        info_frame.grid_columnconfigure(1, weight=1)
        
        for i, (label, value) in enumerate(info_list):
            # Label
            label_widget = ctk.CTkLabel(
                info_frame,
                text=f"{label}:",
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            )
            label_widget.grid(row=i, column=0, sticky="w", padx=(10, 5), pady=2)
            
            # Value
            value_widget = ctk.CTkLabel(
                info_frame,
                text=str(value),
                anchor="w"
            )
            value_widget.grid(row=i, column=1, sticky="w", padx=(5, 10), pady=2)
    
    def _navigate_to_chamber(self, chamber, dialog):
        """Navigate to the chamber in the main application."""
        try:
            # Close the dialog
            dialog.destroy()
              # For now, just show an informational message about where to find the chamber
            # This could be enhanced later with proper panel navigation
            messagebox.showinfo("Chamber Location", f"Chamber {chamber.name} is located in the {chamber.type.value} section.")
                
        except Exception as e:
            self.logger.error(f"Error navigating to chamber: {e}")
            messagebox.showerror("Error", f"Failed to navigate to chamber: {e}")
    
    def _create_work_request_for_chamber(self, chamber):
        """Create a work request for the specified chamber."""
        try:
            # Check if app is available
            if not self.app:
                messagebox.showerror("Error", "Application reference not available")
                return
                
            # Import the work request dialog
            from .work_requests_panel import NewWorkRequestDialog
            
            # Create the dialog 
            dialog = NewWorkRequestDialog(self, self.app)
            self.wait_window(dialog.dialog)
            
            if dialog.result:
                messagebox.showinfo("Success", f"Work request '{dialog.result.title}' created for {chamber.name}")
                # Refresh notifications to show any new notifications
                self._refresh_notifications()
                
        except Exception as e:
            self.logger.error(f"Error creating work request: {e}")
            messagebox.showerror("Error", f"Failed to create work request: {e}")
    
    def _on_filter_change(self, value: str):
        """Handle filter change."""
        self._refresh_notifications()
    
    def _on_new_notification(self, notification: Notification):
        """Handle new notification."""
        # Refresh display in UI thread
        self.after(10, self._refresh_notifications)
        
        # Show toast for high priority notifications
        if notification.priority.value >= NotificationPriority.HIGH.value:
            self.after(10, lambda: NotificationToast(self, notification))
