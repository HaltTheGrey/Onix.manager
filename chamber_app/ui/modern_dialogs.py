"""
Modern Dialog Components
Beautiful, functional dialogs with modern design patterns
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..core.chamber_state import ChamberState, ChamberStatus
from .modern_theme import ModernFrame, ModernButton, ModernLabel, ModernEntry, get_theme_manager, apply_modern_styling


class ModernBaseDialog:
    """Base class for modern dialogs with consistent styling"""
    
    def __init__(self, parent, title: str, size: tuple = (400, 300)):
        self.parent = parent
        self.title = title
        self.size = size
        self.result = None
        self.dialog: Optional[ctk.CTkToplevel] = None
        self.theme_manager = get_theme_manager()
        
    def show(self):
        """Show the dialog"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry(f"{self.size[0]}x{self.size[1]}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self._center_dialog()
        
        # Create UI
        self._create_ui()
        
        # Focus handling
        self._setup_focus()
        
        return self.dialog
    
    def _center_dialog(self):
        """Center the dialog on parent"""
        self.dialog.update_idletasks()
        x = (self.parent.winfo_width() // 2) - (self.size[0] // 2) + self.parent.winfo_rootx()
        y = (self.parent.winfo_height() // 2) - (self.size[1] // 2) + self.parent.winfo_rooty()
        self.dialog.geometry(f"{self.size[0]}x{self.size[1]}+{x}+{y}")
    
    def _create_ui(self):
        """Override in subclasses"""
        pass
    
    def _setup_focus(self):
        """Setup focus handling"""
        pass
    
    def _create_header(self, icon: str, title: str, subtitle: str = ""):
        """Create a modern dialog header"""
        header_frame = ModernFrame(self.dialog)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Icon
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(0, 10))
        
        # Title
        title_label = ModernLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_style="primary"
        )
        title_label.pack()
        
        # Subtitle
        if subtitle:
            subtitle_label = ModernLabel(
                header_frame,
                text=subtitle,
                font=ctk.CTkFont(size=12),
                text_style="secondary"
            )
            subtitle_label.pack(pady=(5, 0))
    
    def _create_button_frame(self, buttons: List[Dict[str, Any]]):
        """Create button frame with modern styling"""
        button_frame = ModernFrame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        for button_config in buttons:
            btn = ModernButton(
                button_frame,
                text=button_config["text"],
                command=button_config["command"],
                style=button_config.get("style", "primary_button"),
                width=button_config.get("width", 100)
            )
            btn.pack(side=button_config.get("side", "right"), padx=5)


class ModernStateChangeDialog(ModernBaseDialog):
    """Modern dialog for changing chamber state"""
    
    def __init__(self, parent, chamber, app):
        super().__init__(parent, "Change Chamber State", (450, 400))
        self.chamber = chamber
        self.app = app
        self.selected_state = None
        self.reason = ""
    
    def _create_ui(self):
        """Create the state change dialog UI"""
        # Header
        self._create_header(
            "⚙️",
            "Change Chamber State",
            f"Currently: {self.chamber.state_manager.current_state.value}"
        )
        
        # Main content
        content_frame = ModernFrame(self.dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Chamber info
        info_frame = ModernFrame(content_frame)
        info_frame.pack(fill="x", pady=(0, 20))
        info_frame.configure(border_width=1, border_color=self.theme_manager.get_color("border"))
        
        chamber_label = ModernLabel(
            info_frame,
            text=f"📍 {self.chamber.name} ({self.chamber.type.value})",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="primary"
        )
        chamber_label.pack(pady=10)
        
        # New state selection
        state_label = ModernLabel(
            content_frame,
            text="Select New State:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        state_label.pack(anchor="w", pady=(0, 10))
        
        # State options with icons
        states_frame = ModernFrame(content_frame)
        states_frame.pack(fill="x", pady=(0, 20))
        
        self.state_var = ctk.StringVar(value=self.chamber.state_manager.current_state.value)
        
        state_options = {
            "IDLE": "💤",
            "RUNNING": "🔄", 
            "MAINTENANCE": "🔧",
            "ERROR": "❌",
            "OFFLINE": "📴"
        }
        
        for state_value, icon in state_options.items():
            state_frame = ModernFrame(states_frame)
            state_frame.pack(fill="x", pady=2)
            
            radio_btn = ctk.CTkRadioButton(
                state_frame,
                text=f"{icon} {state_value}",
                variable=self.state_var,
                value=state_value,
                font=ctk.CTkFont(size=12)
            )
            radio_btn.pack(anchor="w", padx=10, pady=5)
        
        # Reason input
        reason_label = ModernLabel(
            content_frame,
            text="Reason (optional):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        reason_label.pack(anchor="w", pady=(0, 5))
        
        self.reason_entry = ctk.CTkTextbox(
            content_frame,
            height=80,
            wrap="word"
        )
        self.reason_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        buttons = [
            {"text": "Cancel", "command": self._cancel, "style": "accent_button", "side": "left"},
            {"text": "Apply State", "command": self._apply_state, "style": "success_button", "side": "right"}
        ]
        self._create_button_frame(buttons)
    
    def _apply_state(self):
        """Apply the selected state"""
        new_state = self.state_var.get()
        reason = self.reason_entry.get("1.0", "end-1c").strip()
        
        if new_state == self.chamber.state_manager.current_state.value:
            messagebox.showwarning("No Change", "The selected state is the same as current state.")
            return
        
        try:
            # Apply state change
            state_enum = ChamberState(new_state)
            success = self.chamber.state_manager.change_state(state_enum, reason)
            
            if success:
                self.result = {"state": new_state, "reason": reason}
                if self.dialog:
                    self.dialog.destroy()
                messagebox.showinfo("Success", f"Chamber state changed to {new_state}")
            else:
                messagebox.showerror("Error", "Failed to change chamber state")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error changing state: {e}")
    
    def _cancel(self):
        """Cancel the dialog"""
        if self.dialog:
            self.dialog.destroy()


class ModernStatusChangeDialog(ModernBaseDialog):
    """Modern dialog for changing chamber status"""
    
    def __init__(self, parent, chamber, app):
        super().__init__(parent, "Set Chamber Status", (450, 350))
        self.chamber = chamber
        self.app = app
    
    def _create_ui(self):
        """Create the status change dialog UI"""
        # Header
        current_status = self.chamber.state_manager.current_status
        current_text = current_status.value if current_status else "None"
        
        self._create_header(
            "🔧",
            "Set Chamber Status",
            f"Currently: {current_text}"
        )
        
        # Main content
        content_frame = ModernFrame(self.dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Chamber info
        info_frame = ModernFrame(content_frame)
        info_frame.pack(fill="x", pady=(0, 20))
        info_frame.configure(border_width=1, border_color=self.theme_manager.get_color("border"))
        
        chamber_label = ModernLabel(
            info_frame,
            text=f"📍 {self.chamber.name} ({self.chamber.type.value})",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_style="primary"
        )
        chamber_label.pack(pady=10)
        
        # Status selection
        status_label = ModernLabel(
            content_frame,
            text="Select Status:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        status_label.pack(anchor="w", pady=(0, 10))
        
        status_values = ["None"] + [status.value for status in ChamberStatus]
        self.status_combo = ctk.CTkComboBox(
            content_frame,
            values=status_values,
            state="readonly",
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.status_combo.pack(fill="x", pady=(0, 20))
        self.status_combo.set(current_text)
        
        # Notes
        notes_label = ModernLabel(
            content_frame,
            text="Notes (optional):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        notes_label.pack(anchor="w", pady=(0, 5))
        
        self.notes_entry = ctk.CTkTextbox(
            content_frame,
            height=80,
            wrap="word"
        )
        self.notes_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        buttons = [
            {"text": "Cancel", "command": self._cancel, "style": "accent_button", "side": "left"},
            {"text": "Set Status", "command": self._set_status, "style": "success_button", "side": "right"}
        ]
        self._create_button_frame(buttons)
    
    def _set_status(self):
        """Set the selected status"""
        new_status = self.status_combo.get()
        notes = self.notes_entry.get("1.0", "end-1c").strip()
        
        try:
            if new_status == "None":
                success = self.chamber.state_manager.clear_status(notes)
                status_text = "cleared"
            else:
                status_enum = ChamberStatus(new_status)
                success = self.chamber.state_manager.set_status(status_enum, notes)
                status_text = f"set to {new_status}"
            
            if success:
                self.result = {"status": new_status, "notes": notes}
                if self.dialog:
                    self.dialog.destroy()
                messagebox.showinfo("Success", f"Chamber status {status_text}")
            else:
                messagebox.showerror("Error", "Failed to change chamber status")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error changing status: {e}")
    
    def _cancel(self):
        """Cancel the dialog"""
        if self.dialog:
            self.dialog.destroy()


class ModernWorkRequestDialog(ModernBaseDialog):
    """Modern dialog for creating work requests"""
    
    def __init__(self, parent, app, chamber=None):
        super().__init__(parent, "Create Work Request", (500, 600))
        self.app = app
        self.chamber = chamber
    
    def _create_ui(self):
        """Create the work request dialog UI"""
        # Header
        self._create_header(
            "📋",
            "Create Work Request",
            "Schedule maintenance or repair work"
        )
        
        # Main content with scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Chamber selection (if not pre-selected)
        if not self.chamber:
            chamber_label = ModernLabel(
                main_frame,
                text="Select Chamber:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_style="primary"
            )
            chamber_label.pack(anchor="w", pady=(0, 5))
            
            chambers = self.app.get_chambers()
            chamber_names = [f"{c.name} ({c.type.value})" for c in chambers]
            
            self.chamber_combo = ctk.CTkComboBox(
                main_frame,
                values=chamber_names,
                state="readonly",
                height=35
            )
            self.chamber_combo.pack(fill="x", pady=(0, 15))
        else:
            # Show selected chamber info
            chamber_info = ModernFrame(main_frame)
            chamber_info.pack(fill="x", pady=(0, 15))
            chamber_info.configure(border_width=1, border_color=self.theme_manager.get_color("border"))
            
            chamber_label = ModernLabel(
                chamber_info,
                text=f"📍 {self.chamber.name} ({self.chamber.type.value})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_style="primary"
            )
            chamber_label.pack(pady=10)
        
        # Title
        title_label = ModernLabel(
            main_frame,
            text="Title:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        title_label.pack(anchor="w", pady=(0, 5))
        
        self.title_entry = ModernEntry(
            main_frame,
            placeholder_text="Enter work request title"
        )
        self.title_entry.pack(fill="x", pady=(0, 15))
        
        # Description
        desc_label = ModernLabel(
            main_frame,
            text="Description:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        desc_label.pack(anchor="w", pady=(0, 5))
        
        self.description_entry = ctk.CTkTextbox(
            main_frame,
            height=100,
            wrap="word"
        )
        self.description_entry.pack(fill="x", pady=(0, 15))
        
        # Priority and urgency in a row
        priority_frame = ModernFrame(main_frame)
        priority_frame.pack(fill="x", pady=(0, 15))
        priority_frame.grid_columnconfigure(0, weight=1)
        priority_frame.grid_columnconfigure(1, weight=1)
        
        # Priority
        priority_label = ModernLabel(
            priority_frame,
            text="Priority:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        priority_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.priority_combo = ctk.CTkComboBox(
            priority_frame,
            values=["Low", "Medium", "High", "Critical"],
            state="readonly",
            height=35
        )
        self.priority_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.priority_combo.set("Medium")
        
        # Urgency
        urgency_label = ModernLabel(
            priority_frame,
            text="Urgency:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        urgency_label.grid(row=0, column=1, sticky="w")
        
        self.urgency_combo = ctk.CTkComboBox(
            priority_frame,
            values=["Routine", "Soon", "ASAP", "Emergency"],
            state="readonly",
            height=35
        )
        self.urgency_combo.grid(row=1, column=1, sticky="ew")
        self.urgency_combo.set("Routine")
        
        # Assigned to
        assigned_label = ModernLabel(
            main_frame,
            text="Assign to (optional):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        assigned_label.pack(anchor="w", pady=(0, 5))
        
        self.assigned_entry = ModernEntry(
            main_frame,
            placeholder_text="Enter assignee name or team"
        )
        self.assigned_entry.pack(fill="x", pady=(0, 15))
        
        # Estimated time and due date in a row
        time_frame = ModernFrame(main_frame)
        time_frame.pack(fill="x", pady=(0, 15))
        time_frame.grid_columnconfigure(0, weight=1)
        time_frame.grid_columnconfigure(1, weight=1)
        
        # Estimated hours
        hours_label = ModernLabel(
            time_frame,
            text="Estimated Hours:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        hours_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        self.hours_entry = ModernEntry(
            time_frame,
            placeholder_text="0.0"
        )
        self.hours_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        # Due date
        due_label = ModernLabel(
            time_frame,
            text="Due Date:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        due_label.grid(row=0, column=1, sticky="w")
        
        self.due_entry = ModernEntry(
            time_frame,
            placeholder_text="YYYY-MM-DD (optional)"
        )
        self.due_entry.grid(row=1, column=1, sticky="ew")
        
        # Tags
        tags_label = ModernLabel(
            main_frame,
            text="Tags (comma-separated):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_style="primary"
        )
        tags_label.pack(anchor="w", pady=(15, 5))
        
        self.tags_entry = ModernEntry(
            main_frame,
            placeholder_text="maintenance, repair, inspection..."
        )
        self.tags_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = ModernFrame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = ModernButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            style="accent_button",
            width=100
        )
        cancel_btn.pack(side="left")
        
        create_btn = ModernButton(
            button_frame,
            text="Create Request",
            command=self._create_request,
            style="success_button",
            width=120
        )
        create_btn.pack(side="right")
    
    def _setup_focus(self):
        """Setup focus on title entry"""
        if hasattr(self, 'title_entry'):
            self.title_entry.focus()
    
    def _create_request(self):
        """Create the work request"""
        title = self.title_entry.get().strip()
        description = self.description_entry.get("1.0", "end-1c").strip()
        
        if not title:
            messagebox.showerror("Error", "Please enter a title for the work request")
            return
        
        # Get chamber
        chamber = self.chamber
        if not chamber and hasattr(self, 'chamber_combo'):
            chamber_text = self.chamber_combo.get()
            if not chamber_text:
                messagebox.showerror("Error", "Please select a chamber")
                return
            # Find chamber by name (simplified)
            chamber_name = chamber_text.split(" (")[0]
            chambers = self.app.get_chambers()
            chamber = next((c for c in chambers if c.name == chamber_name), None)
            
            if not chamber:
                messagebox.showerror("Error", "Selected chamber not found")
                return
        
        # Create work request data
        work_request_data = {
            "title": title,
            "description": description,
            "priority": self.priority_combo.get(),
            "urgency": self.urgency_combo.get(),
            "assigned_to": self.assigned_entry.get().strip() or None,
            "estimated_hours": float(self.hours_entry.get() or "0.0"),
            "due_date": self.due_entry.get().strip() or None,
            "tags": [tag.strip() for tag in self.tags_entry.get().split(",") if tag.strip()],
            "chamber_id": chamber.id
        }
        
        try:
            # Create work request through app
            work_request = self.app.create_work_request(**work_request_data)
            self.result = work_request
            
            if self.dialog:
                self.dialog.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create work request: {e}")
    
    def _cancel(self):
        """Cancel the dialog"""
        if self.dialog:
            self.dialog.destroy()
