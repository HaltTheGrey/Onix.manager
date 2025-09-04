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
        self.data_tab = self.tabview.add("Data Management")
        self.advanced_tab = self.tabview.add("Advanced")
        
        # Setup each tab
        self._setup_general_tab()
        self._setup_ui_tab()
        self._setup_network_tab()
        self._setup_database_tab()
        self._setup_security_tab()
        self._setup_data_management_tab()
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
            command=self._restore_database_backup        )
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
    
    def _setup_data_management_tab(self):
        """Setup the Data Management tab."""
        scrollable = ctk.CTkScrollableFrame(self.data_tab)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Data Export Section
        self._create_section_header(scrollable, "Data Export")
        
        export_frame = ctk.CTkFrame(scrollable)
        export_frame.pack(fill="x", padx=5, pady=5)
        
        # Export options
        export_options_frame = ctk.CTkFrame(export_frame)
        export_options_frame.pack(fill="x", padx=10, pady=10)
        
        # Export type selection
        ctk.CTkLabel(export_options_frame, text="Export Type:").pack(anchor="w", padx=5, pady=2)
        self.export_type_var = ctk.StringVar(value="all_data")
        export_type_frame = ctk.CTkFrame(export_options_frame)
        export_type_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkRadioButton(export_type_frame, text="All Chamber Data", 
                          variable=self.export_type_var, value="all_data").pack(side="left", padx=5)
        ctk.CTkRadioButton(export_type_frame, text="Configuration Only", 
                          variable=self.export_type_var, value="config").pack(side="left", padx=5)
        ctk.CTkRadioButton(export_type_frame, text="Telemetry Data", 
                          variable=self.export_type_var, value="telemetry").pack(side="left", padx=5)
        
        # Format selection
        ctk.CTkLabel(export_options_frame, text="Export Format:").pack(anchor="w", padx=5, pady=(10, 2))
        self.export_format_combo = ctk.CTkComboBox(
            export_options_frame,
            values=["JSON", "CSV", "Excel", "ZIP Archive"],
            state="readonly"
        )
        self.export_format_combo.pack(fill="x", padx=5, pady=2)
        self.export_format_combo.set("JSON")
          # Chamber selection
        ctk.CTkLabel(export_options_frame, text="Chamber (optional):").pack(anchor="w", padx=5, pady=(10, 2))
        self.export_chamber_combo = ctk.CTkComboBox(
            export_options_frame,
            values=["All Chambers"] + [chamber.name for chamber in self.app.get_chambers()],
            state="readonly"
        )
        self.export_chamber_combo.pack(fill="x", padx=5, pady=2)
        self.export_chamber_combo.set("All Chambers")
        
        # Export buttons
        export_buttons_frame = ctk.CTkFrame(export_frame)
        export_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            export_buttons_frame,
            text="Export Data",
            command=self._export_data,
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            export_buttons_frame,
            text="Schedule Export",
            command=self._schedule_export
        ).pack(side="left", padx=5)
        
        # Data Import Section
        self._create_section_header(scrollable, "Data Import")
        
        import_frame = ctk.CTkFrame(scrollable)
        import_frame.pack(fill="x", padx=5, pady=5)
        
        import_options_frame = ctk.CTkFrame(import_frame)
        import_options_frame.pack(fill="x", padx=10, pady=10)
        
        # Import type selection
        ctk.CTkLabel(import_options_frame, text="Import Type:").pack(anchor="w", padx=5, pady=2)
        self.import_type_var = ctk.StringVar(value="configuration")
        import_type_frame = ctk.CTkFrame(import_options_frame)
        import_type_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkRadioButton(import_type_frame, text="Configuration", 
                          variable=self.import_type_var, value="configuration").pack(side="left", padx=5)
        ctk.CTkRadioButton(import_type_frame, text="Telemetry Data", 
                          variable=self.import_type_var, value="telemetry").pack(side="left", padx=5)
        
        # Import options
        self.import_merge_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            import_options_frame,
            text="Merge with existing data (uncheck to replace)",
            variable=self.import_merge_var
        ).pack(anchor="w", padx=5, pady=5)
        
        self.import_backup_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            import_options_frame,
            text="Create backup before import",
            variable=self.import_backup_var
        ).pack(anchor="w", padx=5, pady=5)
        
        # Import buttons
        import_buttons_frame = ctk.CTkFrame(import_frame)
        import_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            import_buttons_frame,
            text="Import from File",
            command=self._import_data,
            fg_color="blue",
            hover_color="darkblue"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            import_buttons_frame,
            text="Validate File",
            command=self._validate_import_file
        ).pack(side="left", padx=5)
        
        # Data Management Tools
        self._create_section_header(scrollable, "Data Management Tools")
        
        tools_frame = ctk.CTkFrame(scrollable)
        tools_frame.pack(fill="x", padx=5, pady=5)
        
        tools_buttons_frame = ctk.CTkFrame(tools_frame)
        tools_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            tools_buttons_frame,
            text="Clean Old Telemetry",
            command=self._clean_old_telemetry
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            tools_buttons_frame,
            text="Data Statistics",
            command=self._show_data_statistics
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            tools_buttons_frame,
            text="Compress Database",
            command=self._compress_database
        ).pack(side="left", padx=5)
    
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
                    
        except Exception as e:            messagebox.showerror("Error", f"Failed to restore database: {e}")

    # Data Management Methods
    
    def _export_data(self):
        """Export data based on selected options."""
        try:
            from ..utils.data_export import DataExporter
            from tkinter import filedialog
            
            exporter = DataExporter(self.app)
            export_type = self.export_type_var.get()
            format_map = {
                "JSON": "json",
                "CSV": "csv", 
                "Excel": "excel",
                "ZIP Archive": "zip"
            }
            export_format = format_map[self.export_format_combo.get()]
            
            # Get chamber ID if specific chamber selected
            chamber_name = self.export_chamber_combo.get()
            chamber_id = None
            if chamber_name != "All Chambers":
                for chamber in self.app.get_all_chambers():
                    if chamber.name == chamber_name:
                        chamber_id = chamber.id
                        break
            
            # Ask for output location
            file_types = [
                ("JSON files", "*.json") if export_format == "json" else
                ("CSV files", "*.csv") if export_format == "csv" else
                ("Excel files", "*.xlsx") if export_format == "excel" else
                ("ZIP files", "*.zip")
            ]
            
            output_path = filedialog.asksaveasfilename(
                title="Export Data",
                filetypes=file_types + [("All files", "*.*")]
            )
            
            if not output_path:
                return
            
            # Perform export based on type
            if export_type == "all_data":
                result_path = exporter.export_chamber_data(
                    chamber_id=chamber_id,
                    format=export_format,
                    output_path=output_path
                )
            elif export_type == "config":
                result_path = exporter.export_configuration(output_path)
            elif export_type == "telemetry":
                result_path = exporter.export_telemetry_data(
                    chamber_id=chamber_id,
                    format=export_format,
                    output_path=output_path
                )
            
            messagebox.showinfo("Export Complete", f"Data exported successfully to:\n{result_path}")
            self._update_status("Data exported successfully", "green")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    def _schedule_export(self):
        """Schedule automatic data exports."""
        try:
            # Create schedule export dialog
            dialog = ctk.CTkToplevel()
            dialog.title("Schedule Export")
            dialog.geometry("400x500")
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (500 // 2)
            dialog.geometry(f"400x500+{x}+{y}")
            
            main_frame = ctk.CTkFrame(dialog)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(main_frame, text="Schedule Data Export", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
            title_label.pack(pady=(0, 20))
            
            # Export type
            type_frame = ctk.CTkFrame(main_frame)
            type_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(type_frame, text="Export Type:").pack(anchor="w", padx=10, pady=5)
            export_type_var = ctk.StringVar(value="chamber_data")
            type_combo = ctk.CTkComboBox(type_frame, variable=export_type_var,
                                       values=["chamber_data", "telemetry", "work_requests", "report"])
            type_combo.pack(fill="x", padx=10, pady=5)
            
            # Schedule frequency
            freq_frame = ctk.CTkFrame(main_frame)
            freq_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(freq_frame, text="Frequency:").pack(anchor="w", padx=10, pady=5)
            frequency_var = ctk.StringVar(value="daily")
            freq_combo = ctk.CTkComboBox(freq_frame, variable=frequency_var,
                                       values=["daily", "weekly", "monthly"])
            freq_combo.pack(fill="x", padx=10, pady=5)
            
            # Time
            time_frame = ctk.CTkFrame(main_frame)
            time_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(time_frame, text="Time (24h format):").pack(anchor="w", padx=10, pady=5)
            time_var = ctk.StringVar(value="23:00")
            time_entry = ctk.CTkEntry(time_frame, textvariable=time_var, placeholder_text="HH:MM")
            time_entry.pack(fill="x", padx=10, pady=5)
            
            # Format
            format_frame = ctk.CTkFrame(main_frame)
            format_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(format_frame, text="Format:").pack(anchor="w", padx=10, pady=5)
            format_var = ctk.StringVar(value="json")
            format_combo = ctk.CTkComboBox(format_frame, variable=format_var,
                                         values=["json", "csv", "excel", "pdf"])
            format_combo.pack(fill="x", padx=10, pady=5)
            
            # Additional options for weekly/monthly
            options_frame = ctk.CTkFrame(main_frame)
            options_frame.pack(fill="x", pady=10)
            
            # Day of week (for weekly)
            dow_label = ctk.CTkLabel(options_frame, text="Day of Week:")
            dow_var = ctk.StringVar(value="sunday")
            dow_combo = ctk.CTkComboBox(options_frame, variable=dow_var,
                                      values=["monday", "tuesday", "wednesday", "thursday", 
                                            "friday", "saturday", "sunday"])
            
            # Day of month (for monthly)
            dom_label = ctk.CTkLabel(options_frame, text="Day of Month:")
            dom_var = ctk.StringVar(value="1")
            dom_combo = ctk.CTkComboBox(options_frame, variable=dom_var,
                                      values=[str(i) for i in range(1, 29)])
            
            def update_options(*args):
                freq = frequency_var.get()
                for widget in options_frame.winfo_children():
                    widget.pack_forget()
                
                if freq == "weekly":
                    dow_label.pack(anchor="w", padx=10, pady=5)
                    dow_combo.pack(fill="x", padx=10, pady=5)
                elif freq == "monthly":
                    dom_label.pack(anchor="w", padx=10, pady=5)
                    dom_combo.pack(fill="x", padx=10, pady=5)
            
            frequency_var.trace("w", update_options)
            update_options()  # Initial setup
            
            # Retention
            retention_frame = ctk.CTkFrame(main_frame)
            retention_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(retention_frame, text="Retention (days):").pack(anchor="w", padx=10, pady=5)
            retention_var = ctk.StringVar(value="30")
            retention_entry = ctk.CTkEntry(retention_frame, textvariable=retention_var)
            retention_entry.pack(fill="x", padx=10, pady=5)
            
            # Buttons
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill="x", pady=20)
            
            def on_schedule():
                try:
                    # Get the scheduled export manager
                    from ..utils.scheduled_exports import ScheduledExportManager
                    scheduler = ScheduledExportManager(self.app)
                    
                    freq = frequency_var.get()
                    export_type = export_type_var.get()
                    time_str = time_var.get()
                    format_str = format_var.get()
                    retention = int(retention_var.get())
                    
                    if freq == "daily":
                        job_id = scheduler.schedule_daily_export(
                            export_type=export_type,
                            time_str=time_str,
                            format=format_str,
                            retention_days=retention
                        )
                    elif freq == "weekly":
                        job_id = scheduler.schedule_weekly_export(
                            export_type=export_type,
                            day_of_week=dow_var.get(),
                            time_str=time_str,
                            format=format_str,
                            retention_days=retention
                        )
                    elif freq == "monthly":
                        job_id = scheduler.schedule_monthly_export(
                            export_type=export_type,
                            day_of_month=int(dom_var.get()),
                            time_str=time_str,
                            format=format_str,
                            retention_days=retention
                        )
                    
                    # Start the scheduler if not already running
                    scheduler.start()
                    
                    messagebox.showinfo("Success", f"Export scheduled successfully!\nJob ID: {job_id}")
                    dialog.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to schedule export: {e}")
            
            def on_cancel():
                dialog.destroy()
            
            ctk.CTkButton(button_frame, text="Schedule", command=on_schedule).pack(side="left", padx=5)
            ctk.CTkButton(button_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
            
        except Exception as e:
            self.logger.error(f"Error opening schedule export dialog: {e}")
            messagebox.showerror("Error", f"Failed to open schedule dialog: {e}")
    
    def _import_data(self):
        """Import data from file."""
        try:
            from ..utils.data_export import DataImporter
            from tkinter import filedialog
            
            # Ask for import file
            file_types = [
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
            
            file_path = filedialog.askopenfilename(
                title="Import Data",
                filetypes=file_types
            )
            
            if not file_path:
                return
            
            # Confirm import
            import_type = self.import_type_var.get()
            merge = self.import_merge_var.get()
            backup = self.import_backup_var.get()
            
            action = "merge with" if merge else "replace"
            confirm_msg = f"This will {action} current {import_type} data.\n"
            if backup:
                confirm_msg += "A backup will be created first.\n"
            confirm_msg += "\nProceed with import?"
            
            if not messagebox.askyesno("Confirm Import", confirm_msg):
                return
            
            # Perform import
            importer = DataImporter(self.app)
            
            if import_type == "configuration":
                summary = importer.import_configuration(
                    file_path=file_path,
                    merge=merge,
                    backup_current=backup
                )
                
                # Show import summary
                summary_msg = f"Import completed:\n"
                summary_msg += f"• Chambers imported: {summary['chambers_imported']}\n"
                summary_msg += f"• Chambers updated: {summary['chambers_updated']}\n"
                summary_msg += f"• Work requests imported: {summary['work_requests_imported']}\n"
                
                if summary['errors']:
                    summary_msg += f"\nErrors encountered: {len(summary['errors'])}"
                    for error in summary['errors'][:3]:  # Show first 3 errors
                        summary_msg += f"\n• {error}"
                    if len(summary['errors']) > 3:
                        summary_msg += f"\n... and {len(summary['errors']) - 3} more"
                
                messagebox.showinfo("Import Complete", summary_msg)
                
            elif import_type == "telemetry":
                summary = importer.import_telemetry_data(file_path)
                
                summary_msg = f"Telemetry import completed:\n"
                summary_msg += f"• Records imported: {summary['records_imported']}\n"
                summary_msg += f"• Total records processed: {summary['total_records']}"
                
                messagebox.showinfo("Import Complete", summary_msg)
            
            self._update_status("Data imported successfully", "green")
            
            # Refresh UI if configuration was imported
            if import_type == "configuration":
                self._load_current_values()
            
        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            messagebox.showerror("Import Error", f"Failed to import data:\n{str(e)}")
    
    def _validate_import_file(self):
        """Validate an import file without importing."""
        try:
            from tkinter import filedialog
            import json
            
            file_path = filedialog.askopenfilename(
                title="Validate Import File",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            file_ext = Path(file_path).suffix.lower()
            validation_results = []
            
            if file_ext == '.json':
                # Validate JSON structure
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    validation_results.append("✓ Valid JSON format")
                    
                    # Check for expected structure
                    if 'chambers' in data:
                        validation_results.append(f"✓ Found {len(data['chambers'])} chambers")
                    if 'work_requests' in data:
                        validation_results.append(f"✓ Found {len(data['work_requests'])} work requests")
                    if 'app_config' in data:
                        validation_results.append("✓ Found app configuration")
                    if 'export_metadata' in data:
                        metadata = data['export_metadata']
                        validation_results.append(f"✓ Export metadata: {metadata.get('timestamp', 'unknown')}")
                    
                except json.JSONDecodeError as e:
                    validation_results.append(f"✗ Invalid JSON: {e}")
                
            elif file_ext in ['.csv', '.xlsx']:
                # Validate data file structure
                try:
                    import pandas as pd
                    if file_ext == '.csv':
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    
                    validation_results.append(f"✓ Valid {file_ext[1:].upper()} format")
                    validation_results.append(f"✓ Found {len(df)} rows, {len(df.columns)} columns")
                    validation_results.append(f"✓ Columns: {', '.join(df.columns.tolist()[:5])}")
                    
                    # Check for telemetry columns
                    required_telemetry_cols = ['chamber_id', 'timestamp']
                    missing_cols = [col for col in required_telemetry_cols if col not in df.columns]
                    if missing_cols:
                        validation_results.append(f"⚠ Missing telemetry columns: {', '.join(missing_cols)}")
                    else:
                        validation_results.append("✓ All required telemetry columns present")
                        
                except Exception as e:
                    validation_results.append(f"✗ Error reading file: {e}")
            
            else:
                validation_results.append("⚠ Unknown file format")
            
            # Show validation results
            results_text = "\n".join(validation_results)
            messagebox.showinfo("File Validation Results", results_text)
            
        except Exception as e:
            messagebox.showerror("Validation Error", f"Failed to validate file:\n{str(e)}")
    
    def _clean_old_telemetry(self):
        """Clean old telemetry data based on retention policy."""
        try:
            retention_days = self.app.config.get('TELEMETRY_RETENTION_DAYS', 90)
            
            confirm_msg = f"This will delete telemetry data older than {retention_days} days.\n"
            confirm_msg += "This action cannot be undone.\n\nProceed?"
            
            if not messagebox.askyesno("Confirm Cleanup", confirm_msg):
                return
            
            # Calculate cutoff date
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Clean database
            from ..utils.config import get_database_path
            import sqlite3
            
            db_path = get_database_path(self.app.config)
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Count records to be deleted
                cursor.execute(
                    "SELECT COUNT(*) FROM telemetry_data WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                count_to_delete = cursor.fetchone()[0]
                
                if count_to_delete == 0:
                    messagebox.showinfo("Cleanup Complete", "No old telemetry data found to clean.")
                    return
                
                # Delete old records
                cursor.execute(
                    "DELETE FROM telemetry_data WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM")
            
            messagebox.showinfo("Cleanup Complete", 
                              f"Deleted {count_to_delete} old telemetry records.\n"
                              f"Database space has been reclaimed.")
            self._update_status(f"Cleaned {count_to_delete} old telemetry records", "green")
            
        except Exception as e:
            self.logger.error(f"Telemetry cleanup failed: {e}")
            messagebox.showerror("Cleanup Error", f"Failed to clean telemetry data:\n{str(e)}")
    
    def _show_data_statistics(self):
        """Show database statistics."""
        try:
            from ..utils.config import get_database_path
            import sqlite3
            
            db_path = get_database_path(self.app.config)
            stats = []
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Chamber count
                cursor.execute("SELECT COUNT(*) FROM chambers")
                chamber_count = cursor.fetchone()[0]
                stats.append(f"Chambers: {chamber_count}")
                
                # Telemetry data count
                try:
                    cursor.execute("SELECT COUNT(*) FROM telemetry_data")
                    telemetry_count = cursor.fetchone()[0]
                    stats.append(f"Telemetry Records: {telemetry_count:,}")
                    
                    # Oldest and newest telemetry
                    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM telemetry_data")
                    oldest, newest = cursor.fetchone()
                    if oldest and newest:
                        stats.append(f"Telemetry Range: {oldest[:10]} to {newest[:10]}")
                except:
                    stats.append("Telemetry Records: N/A")
                
                # Work requests count
                try:
                    cursor.execute("SELECT COUNT(*) FROM work_requests")
                    wr_count = cursor.fetchone()[0]
                    stats.append(f"Work Requests: {wr_count}")
                except:
                    stats.append("Work Requests: N/A")
                
                # Database file size
                db_size = os.path.getsize(db_path)
                db_size_mb = db_size / (1024 * 1024)
                stats.append(f"Database Size: {db_size_mb:.2f} MB")
            
            stats_text = "Database Statistics:\n\n" + "\n".join(f"• {stat}" for stat in stats)
            messagebox.showinfo("Data Statistics", stats_text)
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            messagebox.showerror("Statistics Error", f"Failed to get data statistics:\n{str(e)}")
    
    def _compress_database(self):
        """Compress and optimize the database."""
        try:
            from ..utils.config import get_database_path
            import sqlite3
            
            db_path = get_database_path(self.app.config)
            original_size = os.path.getsize(db_path)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Analyze and optimize
                cursor.execute("ANALYZE")
                cursor.execute("VACUUM")
                cursor.execute("REINDEX")
                
                conn.commit()
            
            new_size = os.path.getsize(db_path)
            saved_mb = (original_size - new_size) / (1024 * 1024)
            
            if saved_mb > 0:
                messagebox.showinfo("Compression Complete", 
                                  f"Database optimized successfully.\n"
                                  f"Space saved: {saved_mb:.2f} MB")
            else:
                messagebox.showinfo("Compression Complete", 
                                  "Database was already optimized.")
            
            self._update_status("Database compressed", "green")
            
        except Exception as e:
            self.logger.error(f"Database compression failed: {e}")
            messagebox.showerror("Compression Error", f"Failed to compress database:\n{str(e)}")

    def update_data(self):
        """Update panel data (for consistency with other panels)."""
        pass  # Settings don't need regular updates
