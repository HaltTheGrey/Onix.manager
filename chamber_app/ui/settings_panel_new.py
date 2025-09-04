# -*- coding: utf-8 -*-
"""
Settings panel for the Chamber Management Application.
Provides a comprehensive user interface for configuring application settings.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os
from pathlib import Path
from typing import Dict, Any, Union

from ..utils.logging_config import get_logger


class SettingsPanel(ctk.CTkFrame):
    """
    Panel for managing application settings and configuration.
    Provides a tabbed interface for different setting categories.
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        
        # Store original values for reset functionality
        self.original_values = {}
        self.modified_values = {}
        self.entry_widgets = {}
        
        # Pack to fill parent
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup UI
        self._setup_ui()
        self._load_current_values()
    
    def _setup_ui(self):
        """Setup the settings panel UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Tabbed interface
        self._create_tabbed_interface()
        
        # Action buttons at bottom
        self._create_action_buttons()
    
    def _create_header(self):
        """Create the header with title and status."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Application Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        self.status_label.grid(row=0, column=1, padx=10, pady=10, sticky="e")
    
    def _create_tabbed_interface(self):
        """Create the tabbed interface for different setting categories."""
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add tabs
        self.general_tab = self.tabview.add("General")
        self.ui_tab = self.tabview.add("User Interface")
        self.network_tab = self.tabview.add("Network")
        self.database_tab = self.tabview.add("Database")
        self.security_tab = self.tabview.add("Security")
        self.advanced_tab = self.tabview.add("Advanced")
        
        # Setup each tab
        self._setup_general_tab()
        self._setup_ui_tab()
        self._setup_network_tab()
        self._setup_database_tab()
        self._setup_security_tab()
        self._setup_advanced_tab()
    
    def _setup_general_tab(self):
        """Setup the General settings tab."""
        # Create scrollable frame
        scrollable = ctk.CTkScrollableFrame(self.general_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        # App information section
        self._create_section_header(scrollable, "Application Information")
        
        self._create_setting_entry(scrollable, "APP_NAME", "Application Name", "text")
        self._create_setting_entry(scrollable, "APP_VERSION", "Version", "text")
        self._create_setting_entry(scrollable, "DEBUG", "Debug Mode", "boolean")
        self._create_setting_entry(scrollable, "LOG_LEVEL", "Log Level", "choice", 
                                 ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        
        # Chamber defaults section
        self._create_section_header(scrollable, "Chamber Defaults")
        
        self._create_setting_entry(scrollable, "DEFAULT_CHAMBER_TYPES", "Default Chamber Types", "text")
        self._create_setting_entry(scrollable, "MAX_CHAMBERS_PER_TYPE", "Max Chambers per Type", "integer")
        self._create_setting_entry(scrollable, "TELEMETRY_RETENTION_DAYS", "Telemetry Retention (Days)", "integer")
    
    def _setup_ui_tab(self):
        """Setup the User Interface settings tab."""
        scrollable = ctk.CTkScrollableFrame(self.ui_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_section_header(scrollable, "Interface Settings")
        
        self._create_setting_entry(scrollable, "UI_THEME", "Theme", "choice", ["dark", "light", "system"])
        self._create_setting_entry(scrollable, "WINDOW_WIDTH", "Window Width", "integer")
        self._create_setting_entry(scrollable, "WINDOW_HEIGHT", "Window Height", "integer")
        self._create_setting_entry(scrollable, "AUTO_REFRESH_INTERVAL", "Auto Refresh Interval (seconds)", "integer")
    
    def _setup_network_tab(self):
        """Setup the Network settings tab."""
        scrollable = ctk.CTkScrollableFrame(self.network_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_section_header(scrollable, "Network Configuration")
        
        self._create_setting_entry(scrollable, "SOCKET_PORT", "Socket Port", "integer")
        self._create_setting_entry(scrollable, "MULTICAST_GROUP", "Multicast Group", "text")
        self._create_setting_entry(scrollable, "ETHERNET_TIMEOUT", "Ethernet Timeout (seconds)", "integer")
        self._create_setting_entry(scrollable, "SERIAL_TIMEOUT", "Serial Timeout (seconds)", "integer")
        
        self._create_section_header(scrollable, "External Services")
        
        self._create_setting_entry(scrollable, "GRAFANA_URL", "Grafana URL", "text")
        self._create_setting_entry(scrollable, "GRAFANA_API_KEY", "Grafana API Key", "password")
        self._create_setting_entry(scrollable, "ATLAS_SDK_ENDPOINT", "Atlas SDK Endpoint", "text")
    
    def _setup_database_tab(self):
        """Setup the Database settings tab."""
        scrollable = ctk.CTkScrollableFrame(self.database_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_section_header(scrollable, "Database Configuration")
        
        self._create_setting_entry(scrollable, "DATABASE_PATH", "Database Path", "text")
        self._create_setting_entry(scrollable, "BACKUP_INTERVAL", "Backup Interval (seconds)", "integer")
        
        # Database tools section
        self._create_section_header(scrollable, "Database Tools")
        
        tools_frame = ctk.CTkFrame(scrollable)
        tools_frame.pack(fill="x", padx=5, pady=5)
        
        backup_btn = ctk.CTkButton(
            tools_frame,
            text="Create Backup",
            command=self._create_database_backup
        )
        backup_btn.pack(side="left", padx=5, pady=5)
        
        restore_btn = ctk.CTkButton(
            tools_frame,
            text="Restore from Backup",
            command=self._restore_database_backup
        )
        restore_btn.pack(side="left", padx=5, pady=5)
    
    def _setup_security_tab(self):
        """Setup the Security settings tab."""
        scrollable = ctk.CTkScrollableFrame(self.security_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_section_header(scrollable, "Security Settings")
        
        self._create_setting_entry(scrollable, "SESSION_TIMEOUT", "Session Timeout (seconds)", "integer")
        self._create_setting_entry(scrollable, "ENCRYPTION_KEY", "Encryption Key", "password")
        self._create_setting_entry(scrollable, "ENABLE_AUDIT_LOG", "Enable Audit Log", "boolean")
        self._create_setting_entry(scrollable, "REQUIRE_COMPANY_LOGIN", "Require Company Login", "boolean")
        self._create_setting_entry(scrollable, "DEVELOPER_OVERRIDE", "Developer Override", "boolean")
        
        self._create_section_header(scrollable, "AWS Configuration")
        
        self._create_setting_entry(scrollable, "AWS_PROFILE", "AWS Profile", "text")
        self._create_setting_entry(scrollable, "AWS_REGION", "AWS Region", "text")
    
    def _setup_advanced_tab(self):
        """Setup the Advanced settings tab."""
        scrollable = ctk.CTkScrollableFrame(self.advanced_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_section_header(scrollable, "Configuration Management")
        
        # Import/Export buttons
        import_export_frame = ctk.CTkFrame(scrollable)
        import_export_frame.pack(fill="x", padx=5, pady=5)
        
        export_btn = ctk.CTkButton(
            import_export_frame,
            text="Export Settings",
            command=self._export_settings
        )
        export_btn.pack(side="left", padx=5, pady=5)
        
        import_btn = ctk.CTkButton(
            import_export_frame,
            text="Import Settings",
            command=self._import_settings
        )
        import_btn.pack(side="left", padx=5, pady=5)
        
        reset_btn = ctk.CTkButton(
            import_export_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        )
        reset_btn.pack(side="left", padx=5, pady=5)
        
        # Raw configuration view
        self._create_section_header(scrollable, "Raw Configuration")
        
        self.raw_config_text = ctk.CTkTextbox(scrollable, height=200)
        self.raw_config_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _create_action_buttons(self):
        """Create action buttons at the bottom."""
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self._save_changes,
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(side="left", padx=5, pady=5)
        
        # Apply button
        apply_btn = ctk.CTkButton(
            button_frame,
            text="Apply",
            command=self._apply_changes
        )
        apply_btn.pack(side="left", padx=5, pady=5)
        
        # Reset button
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset",
            command=self._reset_changes,
            fg_color="orange",
            hover_color="darkorange"
        )
        reset_btn.pack(side="left", padx=5, pady=5)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="Refresh",
            command=self._refresh_values
        )
        refresh_btn.pack(side="right", padx=5, pady=5)
    
    def _create_section_header(self, parent, title):
        """Create a section header with title."""
        header_label = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(anchor="w", padx=5, pady=(15, 5))
    
    def _create_setting_entry(self, parent, key, label, entry_type, choices=None):
        """Create a setting entry widget."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        
        # Label
        label_widget = ctk.CTkLabel(frame, text=label, width=200)
        label_widget.pack(side="left", padx=5, pady=5)
        
        # Entry widget based on type
        if entry_type == "boolean":
            widget = ctk.CTkCheckBox(frame, text="")
            widget.pack(side="right", padx=5, pady=5)
        elif entry_type == "choice" and choices:
            widget = ctk.CTkOptionMenu(frame, values=choices)
            widget.pack(side="right", padx=5, pady=5)
        elif entry_type == "password":
            widget = ctk.CTkEntry(frame, show="*", width=200)
            widget.pack(side="right", padx=5, pady=5)
        elif entry_type == "integer":
            widget = ctk.CTkEntry(frame, width=100)
            widget.pack(side="right", padx=5, pady=5)
        else:  # text
            widget = ctk.CTkEntry(frame, width=200)
            widget.pack(side="right", padx=5, pady=5)
        
        # Store widget reference
        self.entry_widgets[key] = {
            'widget': widget,
            'type': entry_type,
            'choices': choices
        }
    
    def _load_current_values(self):
        """Load current configuration values into the entry widgets."""
        self.original_values = self.app.config.copy()
        
        for key, widget_info in self.entry_widgets.items():
            widget = widget_info['widget']
            entry_type = widget_info['type']
            value = self.app.config.get(key, "")
            
            if entry_type == "boolean":
                widget.select() if value else widget.deselect()
            elif entry_type == "choice":
                try:
                    widget.set(str(value))
                except:
                    pass  # Value not in choices
            else:
                if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                    widget.delete(0, 'end')
                    widget.insert(0, str(value))
        
        # Update raw config view
        if hasattr(self, 'raw_config_text'):
            self._update_raw_config_view()
    
    def _update_raw_config_view(self):
        """Update the raw configuration text view."""
        config_json = json.dumps(self.app.config, indent=2, default=str)
        self.raw_config_text.delete("1.0", "end")
        self.raw_config_text.insert("1.0", config_json)
    
    def _get_widget_values(self):
        """Get current values from all entry widgets."""
        values = {}
        
        for key, widget_info in self.entry_widgets.items():
            widget = widget_info['widget']
            entry_type = widget_info['type']
            
            try:
                if entry_type == "boolean":
                    values[key] = widget.get()
                elif entry_type == "integer":
                    value = widget.get().strip()
                    values[key] = int(value) if value else 0
                else:
                    values[key] = widget.get()
            except (ValueError, TypeError):
                # Keep original value if conversion fails
                values[key] = self.original_values.get(key, "")
        
        return values
    
    def _validate_values(self, values):
        """Validate the configuration values."""
        errors = []
        
        # Check required fields
        required_fields = ['APP_NAME', 'DATABASE_PATH']
        for field in required_fields:
            if not values.get(field, "").strip():
                errors.append(f"{field} is required")
        
        # Check positive integers
        integer_fields = ['WINDOW_WIDTH', 'WINDOW_HEIGHT', 'SOCKET_PORT', 
                         'AUTO_REFRESH_INTERVAL', 'BACKUP_INTERVAL']
        for field in integer_fields:
            if field in values and values[field] <= 0:
                errors.append(f"{field} must be a positive number")
        
        # Check port range
        if 'SOCKET_PORT' in values:
            port = values['SOCKET_PORT']
            if not (1024 <= port <= 65535):
                errors.append("Socket port must be between 1024 and 65535")
        
        return errors
    
    def _save_changes(self):
        """Save changes to the .env file."""
        try:
            values = self._get_widget_values()
            errors = self._validate_values(values)
            
            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return
            
            # Update .env file
            env_path = Path(self.app.config['PROJECT_ROOT']) / '.env'
            self._write_env_file(env_path, values)
            
            # Update app config
            self.app.config.update(values)
            self.original_values = values.copy()
            
            self._update_status("Changes saved successfully", "green")
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _apply_changes(self):
        """Apply changes without saving to file."""
        try:
            values = self._get_widget_values()
            errors = self._validate_values(values)
            
            if errors:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return
            
            # Update app config temporarily
            self.app.config.update(values)
            self._update_status("Changes applied (not saved)", "orange")
            
        except Exception as e:
            self.logger.error(f"Error applying settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def _reset_changes(self):
        """Reset changes to original values."""
        self._load_current_values()
        self._update_status("Changes reset", "blue")
    
    def _refresh_values(self):
        """Refresh values from current app config."""
        self._load_current_values()
        self._update_status("Values refreshed", "blue")
    
    def _update_status(self, message, color="green"):
        """Update the status indicator."""
        self.status_label.configure(text=f"{message}", text_color=color)
        self.after(3000, lambda: self.status_label.configure(text="Ready", text_color="green"))
    
    def _write_env_file(self, env_path, values):
        """Write values to .env file."""
        lines = []
        
        # Read existing file to preserve comments and structure
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_lines = f.readlines()
        else:
            existing_lines = []
        
        # Process existing lines
        written_keys = set()
        for line in existing_lines:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                # Keep comments and empty lines
                lines.append(line)
            else:
                # Update existing key-value pairs
                key = line.split('=')[0].strip()
                if key in values:
                    lines.append(f"{key}={values[key]}")
                    written_keys.add(key)
                else:
                    lines.append(line)
        
        # Add new keys
        for key, value in values.items():
            if key not in written_keys:
                lines.append(f"{key}={value}")
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.write('\n'.join(lines))
    
    def _export_settings(self):
        """Export settings to a JSON file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(self.app.config, f, indent=2, default=str)
                messagebox.showinfo("Success", f"Settings exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export settings: {e}")
    
    def _import_settings(self):
        """Import settings from a JSON file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r') as f:
                    imported_config = json.load(f)
                
                # Validate imported config
                errors = self._validate_values(imported_config)
                if errors:
                    messagebox.showerror("Validation Error", "\n".join(errors))
                    return
                
                # Update widgets with imported values
                for key, value in imported_config.items():
                    if key in self.entry_widgets:
                        widget_info = self.entry_widgets[key]
                        widget = widget_info['widget']
                        entry_type = widget_info['type']
                        
                        if entry_type == "boolean":
                            widget.select() if value else widget.deselect()
                        elif entry_type == "choice":
                            try:
                                widget.set(str(value))
                            except:
                                pass
                        else:
                            if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                                widget.delete(0, 'end')
                                widget.insert(0, str(value))
                
                messagebox.showinfo("Success", "Settings imported successfully!")
                self._update_status("Settings imported", "blue")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import settings: {e}")
    
    def _reset_to_defaults(self):
        """Reset all settings to default values."""
        if messagebox.askyesno("Confirm Reset", "This will reset all settings to default values. Continue?"):
            try:
                from ..utils.config import load_config
                
                # Load default config (without .env file)
                env_path = Path(self.app.config['PROJECT_ROOT']) / '.env'
                env_backup = env_path.with_suffix('.env.backup')
                
                # Backup current .env
                if env_path.exists():
                    env_path.rename(env_backup)
                
                # Load defaults
                default_config = load_config()
                
                # Update widgets
                for key, value in default_config.items():
                    if key in self.entry_widgets:
                        widget_info = self.entry_widgets[key]
                        widget = widget_info['widget']
                        entry_type = widget_info['type']
                        
                        if entry_type == "boolean":
                            widget.select() if value else widget.deselect()
                        elif entry_type == "choice":
                            try:
                                widget.set(str(value))
                            except:
                                pass
                        else:
                            if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                                widget.delete(0, 'end')
                                widget.insert(0, str(value))
                
                messagebox.showinfo("Success", f"Settings reset to defaults. Original .env backed up to {env_backup}")
                self._update_status("Reset to defaults", "orange")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset settings: {e}")
    
    def _create_database_backup(self):
        """Create a database backup."""
        try:
            from datetime import datetime
            
            db_path = Path(self.app.config['PROJECT_ROOT']) / self.app.config['DATABASE_PATH']
            if not db_path.exists():
                messagebox.showerror("Error", "Database file not found")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = db_path.with_name(f"{db_path.stem}_backup_{timestamp}{db_path.suffix}")
            
            import shutil
            shutil.copy2(db_path, backup_path)
            
            messagebox.showinfo("Success", f"Database backed up to {backup_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {e}")
    
    def _restore_database_backup(self):
        """Restore database from backup."""
        try:
            backup_path = filedialog.askopenfilename(
                title="Select Database Backup",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            
            if backup_path:
                if messagebox.askyesno("Confirm Restore", "This will replace the current database. Continue?"):
                    db_path = Path(self.app.config['PROJECT_ROOT']) / self.app.config['DATABASE_PATH']
                    
                    import shutil
                    shutil.copy2(backup_path, db_path)
                    
                    messagebox.showinfo("Success", "Database restored successfully!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {e}")

    def update_data(self):
        """Update panel data (for consistency with other panels)."""
        pass  # Settings don't need regular updates
