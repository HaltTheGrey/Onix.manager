"""
Work requests panel for managing chamber work tickets.
Allows creating, tracking, and managing work requests.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import List, Dict, Any

from ..core.chamber import WorkRequest
from ..utils import get_logger


class WorkRequestsPanel(ctk.CTkFrame):
    """
    Panel for managing work requests and tickets.
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        
        self.app = app
        self.logger = get_logger(__name__)
        self.selected_request = None
        
        # Pack to fill parent
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup UI
        self._setup_ui()
        
        # Initial data update
        self.update_data()
    
    def _setup_ui(self):
        """Setup the work requests panel UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Main content area
        self._create_content_area()
    
    def _create_header(self):
        """Create the header with title and controls."""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Work Requests",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Control buttons
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        new_request_btn = ctk.CTkButton(
            button_frame,
            text="+ New Request",
            command=self._show_new_request_dialog,
            fg_color="green",
            hover_color="dark green",
            width=120
        )
        new_request_btn.pack(side="left", padx=(0, 10))
        
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Refresh",
            command=self.update_data,
            width=80
        )
        refresh_btn.pack(side="left")
        
        # Filter controls
        filter_frame = ctk.CTkFrame(header_frame)
        filter_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        
        # Status filter
        status_label = ctk.CTkLabel(filter_frame, text="Filter by Status:")
        status_label.pack(side="left", padx=(10, 5))
        
        self.status_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All", "Open", "In Progress", "Completed", "Cancelled"],
            command=self._on_filter_change,
            width=120
        )
        self.status_filter.pack(side="left", padx=(0, 15))
        self.status_filter.set("All")
        
        # Priority filter
        priority_label = ctk.CTkLabel(filter_frame, text="Filter by Priority:")
        priority_label.pack(side="left", padx=(0, 5))
        
        self.priority_filter = ctk.CTkComboBox(
            filter_frame,
            values=["All", "Critical", "High", "Medium", "Low"],
            command=self._on_filter_change,
            width=120
        )
        self.priority_filter.pack(side="left")
        self.priority_filter.set("All")
    
    def _create_content_area(self):
        """Create the main content area."""
        # Work requests list
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 2), pady=(0, 5))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        list_title = ctk.CTkLabel(
            list_frame,
            text="Work Requests",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Scrollable list of work requests
        self.requests_list = ctk.CTkScrollableFrame(list_frame)
        self.requests_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Details panel
        details_frame = ctk.CTkFrame(self)
        details_frame.grid(row=1, column=1, sticky="nsew", padx=(2, 5), pady=(0, 5))
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(1, weight=1)
        
        details_title = ctk.CTkLabel(
            details_frame,
            text="Request Details",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        details_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.details_content = ctk.CTkScrollableFrame(details_frame)
        self.details_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Initially show empty state
        self._show_empty_details()
    
    def _on_filter_change(self, value=None):
        """Handle filter change."""
        self.update_data()
    
    def _show_new_request_dialog(self):
        """Show dialog to create a new work request."""
        dialog = NewWorkRequestDialog(self.winfo_toplevel(), self.app)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.update_data()
    
    def _show_empty_details(self):
        """Show empty state in details panel."""
        # Clear existing content
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        empty_label = ctk.CTkLabel(
            self.details_content,
            text="Select a work request to view details",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        empty_label.pack(expand=True, pady=50)
    
    def _show_request_details(self, work_request: WorkRequest, chamber_name: str):
        """Show details for a selected work request."""
        # Clear existing content
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        # Request info
        info_frame = ctk.CTkFrame(self.details_content)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        # Title
        title_label = ctk.CTkLabel(
            info_frame,
            text=work_request.title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Chamber
        chamber_label = ctk.CTkLabel(
            info_frame,
            text=f"Chamber: {chamber_name}",
            font=ctk.CTkFont(size=12)
        )
        chamber_label.pack(anchor="w", padx=10, pady=2)
        
        # Status and Priority
        status_priority_frame = ctk.CTkFrame(info_frame)
        status_priority_frame.pack(fill="x", padx=10, pady=5)
        
        status_label = ctk.CTkLabel(
            status_priority_frame,
            text=f"Status: {work_request.status.title()}",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side="left", padx=(0, 20))
        
        priority_color = {
            'critical': 'red',
            'high': 'orange', 
            'medium': 'yellow',
            'low': 'green'
        }.get(work_request.priority.lower(), 'gray')
        
        priority_label = ctk.CTkLabel(
            status_priority_frame,
            text=f"Priority: {work_request.priority.title()}",
            font=ctk.CTkFont(size=12),
            text_color=priority_color
        )
        priority_label.pack(side="left")
        
        # Assigned to
        if work_request.assigned_to:
            assigned_label = ctk.CTkLabel(
                info_frame,
                text=f"Assigned to: {work_request.assigned_to}",
                font=ctk.CTkFont(size=12)
            )
            assigned_label.pack(anchor="w", padx=10, pady=2)
        
        # Created info
        created_label = ctk.CTkLabel(
            info_frame,
            text=f"Created: {work_request.created_at.strftime('%Y-%m-%d %H:%M')} by {work_request.created_by}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        created_label.pack(anchor="w", padx=10, pady=(2, 10))
        
        # Description
        desc_frame = ctk.CTkFrame(self.details_content)
        desc_frame.pack(fill="x", padx=5, pady=5)
        
        desc_title = ctk.CTkLabel(
            desc_frame,
            text="Description",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        desc_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        desc_text = ctk.CTkTextbox(desc_frame, height=100, wrap="word")
        desc_text.pack(fill="x", padx=10, pady=(0, 10))
        desc_text.insert("1.0", work_request.description)
        desc_text.configure(state="disabled")
        
        # Time tracking
        time_frame = ctk.CTkFrame(self.details_content)
        time_frame.pack(fill="x", padx=5, pady=5)
        
        time_title = ctk.CTkLabel(
            time_frame,
            text="Time Tracking",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        time_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        estimated_label = ctk.CTkLabel(
            time_frame,
            text=f"Estimated: {work_request.estimated_hours:.1f} hours",
            font=ctk.CTkFont(size=12)
        )
        estimated_label.pack(anchor="w", padx=10, pady=2)
        
        actual_label = ctk.CTkLabel(
            time_frame,
            text=f"Actual: {work_request.actual_hours:.1f} hours",
            font=ctk.CTkFont(size=12)
        )
        actual_label.pack(anchor="w", padx=10, pady=(2, 10))
        
        # Notes
        notes_frame = ctk.CTkFrame(self.details_content)
        notes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        notes_title = ctk.CTkLabel(
            notes_frame,
            text="Notes",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        notes_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        notes_text = ctk.CTkTextbox(notes_frame, wrap="word")
        notes_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        if work_request.notes:
            notes_content = "\n".join(work_request.notes)
            notes_text.insert("1.0", notes_content)
        else:
            notes_text.insert("1.0", "No notes available")
        
        notes_text.configure(state="disabled")
        
        # Action buttons
        action_frame = ctk.CTkFrame(self.details_content)
        action_frame.pack(fill="x", padx=5, pady=5)
        
        edit_btn = ctk.CTkButton(
            action_frame,
            text="Edit Request",
            command=lambda: self._edit_request(work_request),
            width=100
        )
        edit_btn.pack(side="left", padx=10, pady=10)
        
        if work_request.status != "completed":
            complete_btn = ctk.CTkButton(
                action_frame,
                text="Mark Complete",
                command=lambda: self._complete_request(work_request),
                fg_color="green",
                hover_color="dark green",
                width=120
            )
            complete_btn.pack(side="left", padx=10, pady=10)
        
        delete_btn = ctk.CTkButton(
            action_frame,
            text="Delete",
            command=lambda: self._delete_request(work_request),
            fg_color="red",
            hover_color="dark red",
            width=80
        )
        delete_btn.pack(side="right", padx=10, pady=10)
    
    def _edit_request(self, work_request: WorkRequest):
        """Edit a work request."""
        # This would open an edit dialog
        messagebox.showinfo("Edit Request", f"Would edit request: {work_request.title}")
    
    def _complete_request(self, work_request: WorkRequest):
        """Mark a work request as complete."""
        work_request.status = "completed"
        work_request.completed_at = datetime.now()
        work_request.updated_at = datetime.now()
        self.update_data()
        messagebox.showinfo("Request Completed", f"Request '{work_request.title}' marked as completed")
    
    def _delete_request(self, work_request: WorkRequest):
        """Delete a work request."""
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the work request '{work_request.title}'?"
        )
        
        if result:
            # Find and remove from chamber
            for chamber in self.app.get_chambers():
                if work_request.id in chamber.work_requests:
                    chamber.remove_work_request(work_request.id)
                    break
            
            self.update_data()
            messagebox.showinfo("Request Deleted", "Work request deleted successfully")
    
    def update_data(self):
        """Update the work requests display."""
        try:
            # Clear existing requests
            for widget in self.requests_list.winfo_children():
                widget.destroy()
            
            # Get all work requests from all chambers
            all_requests = []
            chambers = self.app.get_chambers()
            
            for chamber in chambers:
                for work_request in chamber.work_requests.values():
                    all_requests.append((work_request, chamber.name))
            
            # Apply filters
            filtered_requests = self._apply_filters(all_requests)
            
            # Sort by created date (newest first)
            filtered_requests.sort(key=lambda x: x[0].created_at, reverse=True)
            
            # Create request cards
            for work_request, chamber_name in filtered_requests:
                self._create_request_card(work_request, chamber_name)
            
            if not filtered_requests:
                empty_label = ctk.CTkLabel(
                    self.requests_list,
                    text="No work requests found",
                    font=ctk.CTkFont(size=14),
                    text_color="gray"
                )
                empty_label.pack(expand=True, pady=50)
            
        except Exception as e:
            self.logger.error(f"Error updating work requests: {e}", exc_info=True)
    
    def _apply_filters(self, requests_list: List[tuple]) -> List[tuple]:
        """Apply status and priority filters to requests."""
        filtered = requests_list
        
        # Apply status filter
        status_filter = self.status_filter.get()
        if status_filter != "All":
            filtered = [
                (req, chamber) for req, chamber in filtered
                if req.status.lower() == status_filter.lower().replace(" ", "_")
            ]
        
        # Apply priority filter
        priority_filter = self.priority_filter.get()
        if priority_filter != "All":
            filtered = [
                (req, chamber) for req, chamber in filtered
                if req.priority.lower() == priority_filter.lower()
            ]
        
        return filtered
    
    def _create_request_card(self, work_request: WorkRequest, chamber_name: str):
        """Create a card for a work request."""
        card_frame = ctk.CTkFrame(self.requests_list)
        card_frame.pack(fill="x", padx=5, pady=2)
        
        # Make card clickable
        def on_click():
            self.selected_request = work_request
            self._show_request_details(work_request, chamber_name)
            # Highlight selected card
            for widget in self.requests_list.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(border_width=1, border_color="gray")
            card_frame.configure(border_width=2, border_color="blue")
        
        card_frame.bind("<Button-1>", lambda e: on_click())
        
        # Header with title and status
        header_frame = ctk.CTkFrame(card_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=work_request.title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        title_label.pack(side="left", padx=10, pady=5)
        
        # Status badge
        status_color = {
            'open': 'blue',
            'in_progress': 'orange',
            'completed': 'green',
            'cancelled': 'red'
        }.get(work_request.status, 'gray')
        
        status_label = ctk.CTkLabel(
            header_frame,
            text=work_request.status.replace('_', ' ').title(),
            font=ctk.CTkFont(size=10),
            text_color=status_color,
            corner_radius=10
        )
        status_label.pack(side="right", padx=10, pady=5)
        
        # Info line
        info_frame = ctk.CTkFrame(card_frame)
        info_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        info_text = f"Chamber: {chamber_name} | Priority: {work_request.priority.title()}"
        if work_request.assigned_to:
            info_text += f" | Assigned: {work_request.assigned_to}"
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        info_label.pack(fill="x", padx=10, pady=5)


class NewWorkRequestDialog:
    """Dialog for creating a new work request."""
    
    def __init__(self, parent, app):
        self.app = app
        self.result = None
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("New Work Request")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_width() // 2) - (500 // 2) + parent.winfo_x()
        y = (parent.winfo_height() // 2) - (600 // 2) + parent.winfo_y()
        self.dialog.geometry(f"500x600+{x}+{y}")
        
        self._setup_dialog()
    
    def _setup_dialog(self):
        """Setup the new work request dialog."""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Create New Work Request",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Form fields
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Title:", anchor="w")
        title_label.pack(fill="x", pady=(0, 5))
        
        self.title_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter request title")
        self.title_entry.pack(fill="x", pady=(0, 15))
        
        # Chamber selection
        chamber_label = ctk.CTkLabel(main_frame, text="Chamber:", anchor="w")
        chamber_label.pack(fill="x", pady=(0, 5))
        
        chambers = self.app.get_chambers()
        chamber_names = [f"{chamber.name} ({chamber.type.value})" for chamber in chambers]
        
        self.chamber_combo = ctk.CTkComboBox(
            main_frame,
            values=chamber_names,
            state="readonly"
        )
        self.chamber_combo.pack(fill="x", pady=(0, 15))
        if chamber_names:
            self.chamber_combo.set(chamber_names[0])
        
        # Priority
        priority_label = ctk.CTkLabel(main_frame, text="Priority:", anchor="w")
        priority_label.pack(fill="x", pady=(0, 5))
        
        self.priority_combo = ctk.CTkComboBox(
            main_frame,
            values=["Low", "Medium", "High", "Critical"],
            state="readonly"
        )
        self.priority_combo.pack(fill="x", pady=(0, 15))
        self.priority_combo.set("Medium")
        
        # Assigned to
        assigned_label = ctk.CTkLabel(main_frame, text="Assigned to (optional):", anchor="w")
        assigned_label.pack(fill="x", pady=(0, 5))
        
        self.assigned_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter assignee name")
        self.assigned_entry.pack(fill="x", pady=(0, 15))
        
        # Estimated hours
        hours_label = ctk.CTkLabel(main_frame, text="Estimated hours:", anchor="w")
        hours_label.pack(fill="x", pady=(0, 5))
        
        self.hours_entry = ctk.CTkEntry(main_frame, placeholder_text="0.0")
        self.hours_entry.pack(fill="x", pady=(0, 15))
        
        # Description
        desc_label = ctk.CTkLabel(main_frame, text="Description:", anchor="w")
        desc_label.pack(fill="x", pady=(0, 5))
        
        self.desc_text = ctk.CTkTextbox(main_frame, height=120)
        self.desc_text.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        create_btn = ctk.CTkButton(
            button_frame,
            text="Create Request",
            command=self._create_request,
            fg_color="green",
            hover_color="dark green"
        )
        create_btn.pack(side="right")
        
        # Focus on title entry
        self.title_entry.focus()
    
    def _create_request(self):
        """Create the new work request."""
        title = self.title_entry.get().strip()
        chamber_selection = self.chamber_combo.get()
        priority = self.priority_combo.get().lower()
        assigned_to = self.assigned_entry.get().strip()
        description = self.desc_text.get("1.0", "end").strip()
        
        if not title:
            messagebox.showerror("Error", "Please enter a title.")
            return
        
        if not chamber_selection:
            messagebox.showerror("Error", "Please select a chamber.")
            return
        
        # Parse estimated hours
        try:
            estimated_hours = float(self.hours_entry.get() or "0.0")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for estimated hours.")
            return
        
        # Find selected chamber
        chamber_name = chamber_selection.split(" (")[0]
        chambers = self.app.get_chambers()
        selected_chamber = None
        
        for chamber in chambers:
            if chamber.name == chamber_name:
                selected_chamber = chamber
                break
        
        if not selected_chamber:
            messagebox.showerror("Error", "Selected chamber not found.")
            return
        
        # Create work request
        work_request = WorkRequest(
            title=title,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
            created_by="current_user",  # TODO: Get actual current user
            estimated_hours=estimated_hours
        )
        
        # Add to chamber
        success = self.app.add_work_request(selected_chamber.id, work_request)
        
        if success:
            self.result = work_request
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to create work request.")
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
