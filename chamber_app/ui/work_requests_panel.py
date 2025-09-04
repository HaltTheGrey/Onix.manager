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
          # Action buttons with better styling and layout
        action_frame = ctk.CTkFrame(self.details_content)
        action_frame.pack(fill="x", padx=5, pady=10)
        
        # Status-specific actions
        if work_request.status == "open":
            start_btn = ctk.CTkButton(
                action_frame,
                text="🚀 Start Work",
                command=lambda: self._start_request(work_request),
                fg_color="#4A90E2",
                hover_color="#357ABD",
                width=120,
                height=35
            )
            start_btn.pack(side="left", padx=10, pady=10)
        
        if work_request.status in ["open", "in_progress"]:
            complete_btn = ctk.CTkButton(
                action_frame,
                text="✅ Complete",
                command=lambda: self._complete_request(work_request),
                fg_color="#7ED321",
                hover_color="#65A91A",
                width=100,
                height=35
            )
            complete_btn.pack(side="left", padx=5, pady=10)
        
        # Always available actions
        edit_btn = ctk.CTkButton(
            action_frame,
            text="✏️ Edit",
            command=lambda: self._edit_request(work_request),
            fg_color="#F5A623",
            hover_color="#E1941B",
            width=80,
            height=35
        )
        edit_btn.pack(side="left", padx=5, pady=10)
        
        add_note_btn = ctk.CTkButton(
            action_frame,
            text="📝 Add Note",
            command=lambda: self._add_note_request(work_request),
            fg_color="#9013FE",
            hover_color="#7C4DFF",
            width=100,
            height=35
        )
        add_note_btn.pack(side="left", padx=5, pady=10)
        
        # Time tracking for in-progress requests
        if work_request.status == "in_progress":
            log_time_btn = ctk.CTkButton(
                action_frame,
                text="⏱️ Log Time",
                command=lambda: self._log_time_request(work_request),
                fg_color="#FF9800",
                hover_color="#E68900",
                width=100,
                height=35
            )
            log_time_btn.pack(side="left", padx=5, pady=10)
          # Dangerous actions on the right
        delete_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ Delete",
            command=lambda: self._delete_request(work_request),
            fg_color="#D0021B",
            hover_color="#B8001A",
            width=80,
            height=35
        )
        delete_btn.pack(side="right", padx=10, pady=10)
    
    def _start_request(self, work_request: WorkRequest):
        """Start work on a request."""
        # Find the chamber associated with this work request
        associated_chamber = None
        for chamber in self.app.get_chambers():
            if work_request.id in chamber.work_requests:
                associated_chamber = chamber
                break
        
        if not associated_chamber:
            messagebox.showerror("Error", "Could not find chamber for this work request")
            return
        
        # Update work request status
        work_request.status = "in_progress"
        work_request.updated_at = datetime.now()
        work_request.add_note(f"Work started by {self.app.current_user}", self.app.current_user)
        
        # Update chamber status to indicate work is being performed
        from ..core.chamber_state import ChamberStatus
        work_status = ChamberStatus.CURRENTLY_BEING_WORKED_ON
        reason = f"Work in progress: {work_request.title}"        
        try:
            status_success = self.app.update_chamber_status(
                associated_chamber.id,
                work_status,
                reason
            )
            
            if status_success:
                work_request.add_note(f"Chamber status set to '{work_status.value}'", "system")
            
            self.update_data()
            self._show_request_details(work_request, self._get_chamber_name_for_request(work_request))
            messagebox.showinfo("Work Started", f"Started work on '{work_request.title}'")
            
        except Exception as e:
            self.logger.error(f"Error updating chamber state when starting work: {e}")
            work_request.add_note(f"Error updating chamber state: {e}", "system")
            self.update_data()
            self._show_request_details(work_request, self._get_chamber_name_for_request(work_request))
            messagebox.showwarning(
                "Work Started with Issues", 
                f"Started work on '{work_request.title}' but failed to update chamber state."
            )
    
    def _add_note_request(self, work_request: WorkRequest):
        """Add a note to a work request."""
        from tkinter import simpledialog
        note = simpledialog.askstring(
            "Add Note", 
            f"Add a note to '{work_request.title}':",
            parent=self.winfo_toplevel()
        )
        if note and note.strip():
            work_request.add_note(note.strip(), "current_user")
            self.update_data()
            self._show_request_details(work_request, self._get_chamber_name_for_request(work_request))
            messagebox.showinfo("Note Added", "Note added successfully")
    
    def _log_time_request(self, work_request: WorkRequest):
        """Log time for a work request."""
        from tkinter import simpledialog
        try:
            hours = simpledialog.askfloat(
                "Log Time", 
                f"Hours worked on '{work_request.title}':",
                minvalue=0.1,
                maxvalue=24.0,
                parent=self.winfo_toplevel()
            )
            if hours:
                work_request.actual_hours += hours
                work_request.updated_at = datetime.now()
                work_request.add_note(f"Logged {hours} hours of work", "current_user")
                self.update_data()
                self._show_request_details(work_request, self._get_chamber_name_for_request(work_request))
                messagebox.showinfo("Time Logged", f"Logged {hours} hours successfully")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of hours")
    
    def _get_chamber_name_for_request(self, work_request: WorkRequest) -> str:
        """Get chamber name for a work request."""
        for chamber in self.app.get_chambers():
            if work_request.id in chamber.work_requests:
                return chamber.name
        return "Unknown Chamber"
    
    def _edit_request(self, work_request: WorkRequest):
        """Edit a work request."""
        dialog = EditWorkRequestDialog(self.winfo_toplevel(), self.app, work_request)
        self.wait_window(dialog.dialog)
        
        if dialog.result:
            self.update_data()
            # Show updated details
            chamber_name = self._get_chamber_name_for_request(work_request)
            self._show_request_details(work_request, chamber_name)
    
    def _complete_request(self, work_request: WorkRequest):
        """Mark a work request as complete."""
        # Find the chamber associated with this work request
        associated_chamber = None
        for chamber in self.app.get_chambers():
            if work_request.id in chamber.work_requests:
                associated_chamber = chamber
                break
        
        if not associated_chamber:
            messagebox.showerror("Error", "Could not find chamber for this work request")
            return
        
        # Update work request status
        work_request.status = "completed"
        work_request.completed_at = datetime.now()
        work_request.updated_at = datetime.now()
        work_request.add_note(f"Work completed by current_user", "current_user")
        
        # Integrate chamber state management:
        # When completing work, transition chamber to appropriate state and clear status
        from ..core.chamber_state import ChamberState, ChamberStatus
        
        current_state = associated_chamber.state_manager.current_state
        current_status = associated_chamber.state_manager.current_status
        
        # Determine appropriate chamber state after work completion
        new_state = None
        reason = f"Work completed: {work_request.title}"
        
        # Check if there are other active work requests on this chamber
        other_active_requests = [
            req for req in associated_chamber.work_requests.values()
            if req.id != work_request.id and req.status in ['open', 'in_progress']
        ]
        
        try:
            # If this was the last active work request, clean up chamber state
            if not other_active_requests:
                # Clear the "CURRENTLY_BEING_WORKED_ON" status if it's set
                if current_status == ChamberStatus.CURRENTLY_BEING_WORKED_ON:
                    clear_success = self.app.clear_chamber_status(
                        associated_chamber.id,
                        f"Work completed: {work_request.title}"
                    )
                    
                    if clear_success:
                        work_request.add_note("Chamber status cleared (work completed)", "system")
                    else:                        work_request.add_note("Failed to clear chamber status", "system")
                
                # Transition to appropriate state based on work completion
                if current_state in [ChamberState.SETUP, ChamberState.STAGING]:
                    # For setup/staging work, transition to available_empty when done
                    new_state = ChamberState.AVAILABLE_EMPTY
                    reason = f"Work completed, chamber available: {work_request.title}"
                elif current_state in [ChamberState.TEST_NOMINAL, ChamberState.TEST_START, ChamberState.TEST_END]:
                    # For test-related chambers, keep in test state but note work completion
                    new_state = None
                    reason = f"Work completed (chamber remains in test): {work_request.title}"
                
                # Update chamber state if applicable
                if new_state:
                    success = self.app.update_chamber_state(
                        associated_chamber.id, 
                        new_state, 
                        reason
                    )
                    if success:
                        state_name = new_state.value if hasattr(new_state, 'value') else str(new_state)
                        work_request.add_note(f"Chamber transitioned to {state_name}", "system")
                    else:
                        work_request.add_note("Failed to update chamber state", "system")
            else:
                # Other work requests are still active, just note completion
                work_request.add_note(f"Work completed. {len(other_active_requests)} other work request(s) still active on chamber.", "system")
            
            self.update_data()
            self._show_request_details(work_request, self._get_chamber_name_for_request(work_request))
            
            # Show comprehensive success message
            success_msg = f"Completed work on '{work_request.title}'\n"
            if not other_active_requests:
                if new_state:
                    success_msg += f"Chamber transitioned to: {new_state.value}\n"
                if current_status == ChamberStatus.CURRENTLY_BEING_WORKED_ON:
                    success_msg += "Chamber status cleared"
            else:
                success_msg += f"{len(other_active_requests)} other work request(s) still active on this chamber"
            
            messagebox.showinfo("Work Completed", success_msg)
            
        except Exception as e:
            # If something fails, still update the work request but show warning
            self.logger.error(f"Error updating chamber state when completing work: {e}")
            work_request.add_note(f"Error updating chamber state: {e}", "system")
            self.update_data()
            self._show_request_details(work_request, self._get_chamber_name_for_request(work_request))
            messagebox.showwarning(
                "Work Completed with Issues", 
                f"Completed work on '{work_request.title}' but failed to update chamber state.\nSee work request notes for details."
            )
    
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
        card_frame = ctk.CTkFrame(
            self.requests_list, 
            border_width=2, 
            border_color="gray",
            corner_radius=8
        )
        card_frame.pack(fill="x", padx=5, pady=3)
        
        # Store original colors for hover effects
        original_border_color = "gray"
        hover_border_color = "lightblue"
        selected_border_color = "blue"
        
        # Make card clickable with improved visual feedback
        def on_click():
            self.selected_request = work_request
            self._show_request_details(work_request, chamber_name)
            # Highlight selected card
            for widget in self.requests_list.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(border_width=2, border_color="gray")
            card_frame.configure(border_width=3, border_color=selected_border_color)
        
        def on_enter(event):
            if card_frame.cget("border_color") != selected_border_color:
                card_frame.configure(border_color=hover_border_color)
        
        def on_leave(event):
            if card_frame.cget("border_color") != selected_border_color:
                card_frame.configure(border_color=original_border_color)
        
        # Bind hover and click events
        card_frame.bind("<Button-1>", lambda e: on_click())
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        
        # Header with title and status
        header_frame = ctk.CTkFrame(card_frame)
        header_frame.pack(fill="x", padx=8, pady=8)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=work_request.title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.pack(side="left", padx=10, pady=5)
        
        # Priority badge (more prominent)
        priority_colors = {
            'critical': ('#FF4444', 'white'),
            'high': ('#FF8800', 'white'), 
            'medium': ('#FFAA00', 'black'),
            'low': ('#00AA00', 'white')
        }
        priority_bg, priority_fg = priority_colors.get(work_request.priority.lower(), ('#666666', 'white'))
        
        priority_badge = ctk.CTkLabel(
            header_frame,
            text=f"  {work_request.priority.upper()}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=priority_bg,
            text_color=priority_fg,
            corner_radius=12
        )
        priority_badge.pack(side="right", padx=(5, 10), pady=5)
        
        # Status badge
        status_colors = {
            'open': ('#4A90E2', 'white'),
            'in_progress': ('#F5A623', 'black'),
            'completed': ('#7ED321', 'black'),
            'cancelled': ('#D0021B', 'white')
        }
        status_bg, status_fg = status_colors.get(work_request.status, ('#9B9B9B', 'white'))
        
        status_badge = ctk.CTkLabel(
            header_frame,
            text=f"  {work_request.status.replace('_', ' ').title()}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=status_bg,
            text_color=status_fg,
            corner_radius=12
        )
        status_badge.pack(side="right", padx=5, pady=5)
        
        # Info line with better formatting
        info_frame = ctk.CTkFrame(card_frame)
        info_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        # Chamber and assignment info
        chamber_info = f"🏢 {chamber_name}"
        if work_request.assigned_to:
            chamber_info += f"  •  👤 {work_request.assigned_to}"
        
        chamber_label = ctk.CTkLabel(
            info_frame,
            text=chamber_info,
            font=ctk.CTkFont(size=11),
            text_color="gray70",
            anchor="w"
        )
        chamber_label.pack(side="left", padx=10, pady=5)
        
        # Created date
        created_text = f"📅 {work_request.created_at.strftime('%m/%d/%Y')}"
        if work_request.estimated_hours > 0:
            created_text += f"  •  ⏱️ {work_request.estimated_hours}h"
        
        date_label = ctk.CTkLabel(
            info_frame,
            text=created_text,
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            anchor="e"
        )
        date_label.pack(side="right", padx=10, pady=5)
        
        # Add description preview if available
        if work_request.description:
            desc_preview = work_request.description[:80] + "..." if len(work_request.description) > 80 else work_request.description
            desc_frame = ctk.CTkFrame(card_frame)
            desc_frame.pack(fill="x", padx=8, pady=(0, 8))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=f"💭 {desc_preview}",
                font=ctk.CTkFont(size=10),
                text_color="gray50",
                anchor="w",
                wraplength=400
            )
            desc_label.pack(fill="x", padx=10, pady=3)
            
        # Bind click events to child widgets too for better UX
        for widget in [header_frame, info_frame, title_label, chamber_label, date_label]:
            widget.bind("<Button-1>", lambda e: on_click())
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    child.bind("<Button-1>", lambda e: on_click())


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
            title=title,            description=description,
            priority=priority,
            assigned_to=assigned_to,
            created_by=self.app.current_user,
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


class EditWorkRequestDialog:
    """Dialog for editing an existing work request."""
    
    def __init__(self, parent, app, work_request: WorkRequest):
        self.app = app
        self.work_request = work_request
        self.result = None
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Edit Work Request")
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
        """Setup the edit work request dialog."""
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Edit Work Request",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Form fields
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Title:", anchor="w")
        title_label.pack(fill="x", pady=(0, 5))
        
        self.title_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter request title")
        self.title_entry.pack(fill="x", pady=(0, 15))
        self.title_entry.insert(0, self.work_request.title)
        
        # Chamber selection (read-only for edits)
        chamber_label = ctk.CTkLabel(main_frame, text="Chamber:", anchor="w")
        chamber_label.pack(fill="x", pady=(0, 5))
        
        chamber_name = self._get_chamber_name_for_request()
        chamber_display = ctk.CTkLabel(
            main_frame, 
            text=f"🏢 {chamber_name}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="gray90",
            corner_radius=5,
            height=30
        )
        chamber_display.pack(fill="x", pady=(0, 15))
        
        # Priority
        priority_label = ctk.CTkLabel(main_frame, text="Priority:", anchor="w")
        priority_label.pack(fill="x", pady=(0, 5))
        
        self.priority_combo = ctk.CTkComboBox(
            main_frame,
            values=["Low", "Medium", "High", "Critical"],
            state="readonly"
        )
        self.priority_combo.pack(fill="x", pady=(0, 15))
        self.priority_combo.set(self.work_request.priority.title())
        
        # Assigned to
        assigned_label = ctk.CTkLabel(main_frame, text="Assigned to:", anchor="w")
        assigned_label.pack(fill="x", pady=(0, 5))
        
        self.assigned_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter assignee name")
        self.assigned_entry.pack(fill="x", pady=(0, 15))
        if self.work_request.assigned_to:
            self.assigned_entry.insert(0, self.work_request.assigned_to)
        
        # Estimated hours
        hours_label = ctk.CTkLabel(main_frame, text="Estimated hours:", anchor="w")
        hours_label.pack(fill="x", pady=(0, 5))
        
        self.hours_entry = ctk.CTkEntry(main_frame, placeholder_text="0.0")
        self.hours_entry.pack(fill="x", pady=(0, 15))
        self.hours_entry.insert(0, str(self.work_request.estimated_hours))
        
        # Description
        desc_label = ctk.CTkLabel(main_frame, text="Description:", anchor="w")
        desc_label.pack(fill="x", pady=(0, 5))
        
        self.desc_text = ctk.CTkTextbox(main_frame, height=120)
        self.desc_text.pack(fill="x", pady=(0, 20))
        if self.work_request.description:
            self.desc_text.insert("1.0", self.work_request.description)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self._save_changes,
            fg_color="green",
            hover_color="dark green"
        )
        save_btn.pack(side="right")
        
        # Focus on title entry
        self.title_entry.focus()
    
    def _get_chamber_name_for_request(self) -> str:
        """Get chamber name for the work request."""
        for chamber in self.app.get_chambers():
            if self.work_request.id in chamber.work_requests:
                return chamber.name
        return "Unknown Chamber"
    
    def _save_changes(self):
        """Save changes to the work request."""
        title = self.title_entry.get().strip()
        priority = self.priority_combo.get().lower()
        assigned_to = self.assigned_entry.get().strip()
        description = self.desc_text.get("1.0", "end").strip()
        
        if not title:
            messagebox.showerror("Error", "Please enter a title.")
            return
        
        # Parse estimated hours
        try:
            estimated_hours = float(self.hours_entry.get() or "0.0")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for estimated hours.")
            return
        
        # Update work request
        self.work_request.title = title
        self.work_request.priority = priority
        self.work_request.assigned_to = assigned_to if assigned_to else ""
        self.work_request.description = description
        self.work_request.estimated_hours = estimated_hours
        self.work_request.updated_at = datetime.now()
        
        # Add note about edit
        self.work_request.add_note(f"Work request updated", "current_user")
        
        self.result = True
        messagebox.showinfo("Success", "Work request updated successfully!")
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()
