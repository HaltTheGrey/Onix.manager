# -*- coding: utf-8 -*-
"""
Enhanced filtering system for the Chamber Management Application.
Provides advanced filtering capabilities for chambers, telemetry data, and work requests.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
import tkinter as tk
from tkinter import ttk

from ..utils.logging_config import get_logger


class FilterType(Enum):
    """Types of filters available."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CHOICE = "choice"
    BOOLEAN = "boolean"
    RANGE = "range"


class FilterOperator(Enum):
    """Filter operators for different data types."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class FilterCondition:
    """Represents a single filter condition."""
    
    def __init__(self, field: str, operator: FilterOperator, value: Any, field_type: FilterType = FilterType.TEXT):
        self.field = field
        self.operator = operator
        self.value = value
        self.field_type = field_type
    
    def apply(self, item: Dict[str, Any]) -> bool:
        """Apply this filter condition to an item."""
        try:
            item_value = self._get_field_value(item, self.field)
            
            if self.operator == FilterOperator.IS_NULL:
                return item_value is None
            elif self.operator == FilterOperator.IS_NOT_NULL:
                return item_value is not None
            
            if item_value is None:
                return False
            
            # Convert values for comparison
            if self.field_type == FilterType.NUMBER:
                item_value = float(item_value) if item_value != "" else 0.0
                compare_value = float(self.value) if self.value != "" else 0.0
            elif self.field_type == FilterType.DATE:
                if isinstance(item_value, str):
                    item_value = datetime.fromisoformat(item_value.replace('Z', '+00:00'))
                if isinstance(self.value, str):
                    compare_value = datetime.fromisoformat(self.value.replace('Z', '+00:00'))
                else:
                    compare_value = self.value
            else:
                item_value = str(item_value).lower()
                compare_value = str(self.value).lower()
              # Apply operator with proper type checking
            if self.operator == FilterOperator.EQUALS:
                return item_value == compare_value
            elif self.operator == FilterOperator.NOT_EQUALS:
                return item_value != compare_value
            elif self.operator == FilterOperator.CONTAINS:
                # Only string types support 'in' for substring checking
                if isinstance(item_value, str) and isinstance(compare_value, str):
                    return compare_value in item_value
                return False
            elif self.operator == FilterOperator.NOT_CONTAINS:
                # Only string types support 'not in' for substring checking
                if isinstance(item_value, str) and isinstance(compare_value, str):
                    return compare_value not in item_value
                return True
            elif self.operator == FilterOperator.STARTS_WITH:
                # Only string types support startswith
                if isinstance(item_value, str) and isinstance(compare_value, str):
                    return item_value.startswith(compare_value)
                return False
            elif self.operator == FilterOperator.ENDS_WITH:                # Only string types support endswith
                if isinstance(item_value, str) and isinstance(compare_value, str):
                    return item_value.endswith(compare_value)
                return False
            elif self.operator == FilterOperator.GREATER_THAN:
                # Only comparable types (same type) support comparison
                try:
                    if type(item_value) == type(compare_value):
                        return item_value > compare_value  # type: ignore
                except TypeError:
                    pass
                return False
            elif self.operator == FilterOperator.LESS_THAN:
                # Only comparable types (same type) support comparison
                try:
                    if type(item_value) == type(compare_value):
                        return item_value < compare_value  # type: ignore
                except TypeError:
                    pass
                return False
            elif self.operator == FilterOperator.GREATER_EQUAL:
                # Only comparable types (same type) support comparison
                try:
                    if type(item_value) == type(compare_value):
                        return item_value >= compare_value  # type: ignore
                except TypeError:
                    pass
                return False
            elif self.operator == FilterOperator.LESS_EQUAL:
                # Only comparable types (same type) support comparison
                try:
                    if type(item_value) == type(compare_value):
                        return item_value <= compare_value  # type: ignore
                except TypeError:
                    pass
                return False
            elif self.operator == FilterOperator.BETWEEN:
                if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                    min_val, max_val = self.value
                    if self.field_type == FilterType.NUMBER:
                        try:
                            min_val = float(min_val)
                            max_val = float(max_val)
                            item_val = float(item_value) if isinstance(item_value, (int, float, str)) else item_value
                            return isinstance(item_val, (int, float)) and min_val <= item_val <= max_val
                        except (ValueError, TypeError):
                            return False
                    elif self.field_type == FilterType.DATE:
                        try:
                            # Ensure all values are datetime objects
                            if isinstance(min_val, str):
                                min_val = datetime.fromisoformat(min_val.replace('Z', '+00:00'))
                            if isinstance(max_val, str):
                                max_val = datetime.fromisoformat(max_val.replace('Z', '+00:00'))
                            if isinstance(item_value, str):
                                item_value = datetime.fromisoformat(item_value.replace('Z', '+00:00'))
                            return isinstance(item_value, datetime) and min_val <= item_value <= max_val
                        except (ValueError, TypeError):
                            return False
                    else:
                        # String comparison
                        min_str = str(min_val).lower()
                        max_str = str(max_val).lower()
                        item_str = str(item_value).lower()
                        return min_str <= item_str <= max_str
                return False
            elif self.operator == FilterOperator.IN:
                if isinstance(self.value, (list, tuple)):
                    compare_values = [str(v).lower() for v in self.value]
                    item_str = str(item_value).lower()
                    return item_str in compare_values
                return False
            elif self.operator == FilterOperator.NOT_IN:
                if isinstance(self.value, (list, tuple)):
                    compare_values = [str(v).lower() for v in self.value]
                    item_str = str(item_value).lower()
                    return item_str not in compare_values
                return True
            
            return False
            
        except Exception as e:
            # Log error and return False for safety
            return False
    
    def _get_field_value(self, item: Dict[str, Any], field: str) -> Any:
        """Get field value from item, supporting nested fields with dot notation."""
        keys = field.split('.')
        value = item
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


class FilterGroup:
    """Represents a group of filter conditions with AND/OR logic."""
    
    def __init__(self, logic: str = "AND"):
        self.logic = logic.upper()  # "AND" or "OR"
        self.conditions: List[FilterCondition] = []
        self.groups: List['FilterGroup'] = []
    
    def add_condition(self, condition: FilterCondition):
        """Add a filter condition to this group."""
        self.conditions.append(condition)
    
    def add_group(self, group: 'FilterGroup'):
        """Add a nested filter group."""
        self.groups.append(group)
    
    def apply(self, item: Dict[str, Any]) -> bool:
        """Apply all conditions and groups in this filter group."""
        results = []
        
        # Apply conditions
        for condition in self.conditions:
            results.append(condition.apply(item))
        
        # Apply nested groups
        for group in self.groups:
            results.append(group.apply(item))
        
        if not results:
            return True  # No conditions means no filtering
        
        # Apply logic
        if self.logic == "AND":
            return all(results)
        elif self.logic == "OR":
            return any(results)
        else:
            return True


class FilterWidget(ctk.CTkFrame):
    """Widget for creating and editing filter conditions."""
    
    def __init__(self, parent, field_definitions: Dict[str, Dict], on_change: Optional[Callable] = None):
        super().__init__(parent)
        
        self.field_definitions = field_definitions
        self.on_change = on_change
        self.logger = get_logger(__name__)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the filter widget UI."""
        # Field selection
        self.field_label = ctk.CTkLabel(self, text="Field:")
        self.field_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.field_var = ctk.StringVar()
        self.field_combo = ctk.CTkComboBox(
            self, 
            variable=self.field_var,
            values=list(self.field_definitions.keys()),
            command=self._on_field_change
        )
        self.field_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Operator selection
        self.operator_label = ctk.CTkLabel(self, text="Operator:")
        self.operator_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        self.operator_var = ctk.StringVar()
        self.operator_combo = ctk.CTkComboBox(
            self,
            variable=self.operator_var,
            command=self._on_operator_change
        )
        self.operator_combo.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Value input
        self.value_label = ctk.CTkLabel(self, text="Value:")
        self.value_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        self.value_frame = ctk.CTkFrame(self)
        self.value_frame.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        
        # Remove button
        self.remove_btn = ctk.CTkButton(
            self,
            text="×",
            width=30,
            command=self._on_remove
        )
        self.remove_btn.grid(row=0, column=6, padx=5, pady=5)
        
        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(5, weight=2)
        
        self._create_value_widget()
        
    def _on_field_change(self, value: str):
        """Handle field selection change."""
        self._update_operators()
        self._create_value_widget()
        if self.on_change:
            self.on_change()
    
    def _on_operator_change(self, value: str):
        """Handle operator selection change."""
        self._create_value_widget()
        if self.on_change:
            self.on_change()
    
    def _on_remove(self):
        """Handle remove button click."""
        self.destroy()
        if self.on_change:
            self.on_change()
    
    def _update_operators(self):
        """Update available operators based on selected field."""
        field_name = self.field_var.get()
        if not field_name or field_name not in self.field_definitions:
            return
        
        field_def = self.field_definitions[field_name]
        field_type = FilterType(field_def.get('type', 'text'))
        
        # Define operators for each field type
        if field_type == FilterType.TEXT:
            operators = ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with"]
        elif field_type == FilterType.NUMBER:
            operators = ["equals", "not_equals", "greater_than", "less_than", "greater_equal", "less_equal", "between"]
        elif field_type == FilterType.DATE:
            operators = ["equals", "not_equals", "greater_than", "less_than", "between"]
        elif field_type == FilterType.CHOICE:
            operators = ["equals", "not_equals", "in", "not_in"]
        elif field_type == FilterType.BOOLEAN:
            operators = ["equals"]
        else:
            operators = ["equals", "not_equals"]
        
        # Add null operators
        operators.extend(["is_null", "is_not_null"])
        
        self.operator_combo.configure(values=operators)
        if operators:
            self.operator_var.set(operators[0])
    
    def _create_value_widget(self):
        """Create appropriate value input widget based on field type and operator."""
        # Clear existing widgets
        for widget in self.value_frame.winfo_children():
            widget.destroy()
        
        field_name = self.field_var.get()
        operator = self.operator_var.get()
        
        if not field_name or field_name not in self.field_definitions:
            return
        
        field_def = self.field_definitions[field_name]
        field_type = FilterType(field_def.get('type', 'text'))
        
        # Handle special operators that don't need values
        if operator in ["is_null", "is_not_null"]:
            label = ctk.CTkLabel(self.value_frame, text="(no value needed)")
            label.pack(pady=5)
            return
        
        # Create appropriate widget based on field type and operator
        if field_type == FilterType.BOOLEAN:
            self.value_var = ctk.StringVar(value="True")
            widget = ctk.CTkComboBox(
                self.value_frame,
                variable=self.value_var,
                values=["True", "False"]
            )
            widget.pack(pady=5, fill="x")
            
        elif field_type == FilterType.CHOICE:
            choices = field_def.get('choices', [])
            if operator in ["in", "not_in"]:
                # Multi-select for IN/NOT IN operators
                self._create_multi_select(choices)
            else:
                self.value_var = ctk.StringVar()
                widget = ctk.CTkComboBox(
                    self.value_frame,
                    variable=self.value_var,
                    values=choices
                )
                widget.pack(pady=5, fill="x")
                
        elif field_type == FilterType.DATE:
            if operator == "between":
                self._create_date_range_widget()
            else:
                self._create_date_widget()
                
        elif field_type == FilterType.NUMBER:
            if operator == "between":
                self._create_number_range_widget()
            else:
                self.value_var = ctk.StringVar()
                widget = ctk.CTkEntry(self.value_frame, textvariable=self.value_var)
                widget.pack(pady=5, fill="x")
                
        else:  # TEXT
            self.value_var = ctk.StringVar()
            widget = ctk.CTkEntry(self.value_frame, textvariable=self.value_var)
            widget.pack(pady=5, fill="x")
    
    def _create_multi_select(self, choices: List[str]):
        """Create a multi-select widget for IN/NOT IN operators."""
        self.selected_values = []
        
        frame = ctk.CTkScrollableFrame(self.value_frame, height=100)
        frame.pack(pady=5, fill="both", expand=True)
        
        self.choice_vars = {}
        for choice in choices:
            var = ctk.BooleanVar()
            self.choice_vars[choice] = var
            checkbox = ctk.CTkCheckBox(
                frame,
                text=choice,
                variable=var,
                command=lambda c=choice: self._update_selected_values()
            )
            checkbox.pack(anchor="w", pady=2)
    
    def _create_date_widget(self):
        """Create a date input widget."""
        self.value_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        widget = ctk.CTkEntry(self.value_frame, textvariable=self.value_var)
        widget.pack(pady=5, fill="x")
        
        # Add date picker button
        date_btn = ctk.CTkButton(
            self.value_frame,
            text="📅",
            width=30,
            command=self._open_date_picker
        )
        date_btn.pack(pady=2)
    
    def _create_date_range_widget(self):
        """Create date range input widgets."""
        range_frame = ctk.CTkFrame(self.value_frame)
        range_frame.pack(pady=5, fill="x")
        
        # Start date
        ctk.CTkLabel(range_frame, text="From:").pack(side="left", padx=5)
        self.start_date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        start_widget = ctk.CTkEntry(range_frame, textvariable=self.start_date_var, width=100)
        start_widget.pack(side="left", padx=5)
        
        # End date
        ctk.CTkLabel(range_frame, text="To:").pack(side="left", padx=5)
        self.end_date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        end_widget = ctk.CTkEntry(range_frame, textvariable=self.end_date_var, width=100)
        end_widget.pack(side="left", padx=5)
    
    def _create_number_range_widget(self):
        """Create number range input widgets."""
        range_frame = ctk.CTkFrame(self.value_frame)
        range_frame.pack(pady=5, fill="x")
        
        # Min value
        ctk.CTkLabel(range_frame, text="Min:").pack(side="left", padx=5)
        self.min_value_var = ctk.StringVar()
        min_widget = ctk.CTkEntry(range_frame, textvariable=self.min_value_var, width=80)
        min_widget.pack(side="left", padx=5)
        
        # Max value
        ctk.CTkLabel(range_frame, text="Max:").pack(side="left", padx=5)
        self.max_value_var = ctk.StringVar()
        max_widget = ctk.CTkEntry(range_frame, textvariable=self.max_value_var, width=80)
        max_widget.pack(side="left", padx=5)
    
    def _update_selected_values(self):
        """Update the list of selected values for multi-select."""
        self.selected_values = [
            choice for choice, var in self.choice_vars.items() 
            if var.get()
        ]
    def _open_date_picker(self):
        """Open a date picker dialog."""
        try:
            # Create a simple date picker dialog
            dialog = ctk.CTkToplevel()
            dialog.title("Select Date")
            dialog.geometry("300x200")
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
            y = (dialog.winfo_screenheight() // 2) - (200 // 2)
            dialog.geometry(f"300x200+{x}+{y}")
            
            # Current date
            current_date = datetime.now()
            
            # Year selection
            year_frame = ctk.CTkFrame(dialog)
            year_frame.pack(pady=10, padx=20, fill="x")
            ctk.CTkLabel(year_frame, text="Year:").pack(side="left", padx=5)
            year_var = ctk.StringVar(value=str(current_date.year))
            year_combo = ctk.CTkComboBox(year_frame, variable=year_var, width=80,
                                       values=[str(y) for y in range(current_date.year - 5, current_date.year + 6)])
            year_combo.pack(side="left", padx=5)
            
            # Month selection
            month_frame = ctk.CTkFrame(dialog)
            month_frame.pack(pady=10, padx=20, fill="x")
            ctk.CTkLabel(month_frame, text="Month:").pack(side="left", padx=5)
            month_var = ctk.StringVar(value=str(current_date.month))
            month_combo = ctk.CTkComboBox(month_frame, variable=month_var, width=80,
                                        values=[str(m) for m in range(1, 13)])
            month_combo.pack(side="left", padx=5)
            
            # Day selection
            day_frame = ctk.CTkFrame(dialog)
            day_frame.pack(pady=10, padx=20, fill="x")
            ctk.CTkLabel(day_frame, text="Day:").pack(side="left", padx=5)
            day_var = ctk.StringVar(value=str(current_date.day))
            day_combo = ctk.CTkComboBox(day_frame, variable=day_var, width=80,
                                      values=[str(d) for d in range(1, 32)])
            day_combo.pack(side="left", padx=5)
            
            # Buttons
            button_frame = ctk.CTkFrame(dialog)
            button_frame.pack(pady=20, padx=20, fill="x")
            
            def on_ok():
                try:
                    selected_date = f"{year_var.get()}-{month_var.get().zfill(2)}-{day_var.get().zfill(2)}"
                    # Validate the date
                    datetime.strptime(selected_date, "%Y-%m-%d")
                    self.value_var.set(selected_date)
                    dialog.destroy()
                except ValueError:
                    # Invalid date, show error
                    error_label = ctk.CTkLabel(dialog, text="Invalid date selected!", text_color="red")
                    error_label.pack(pady=5)
            
            def on_cancel():
                dialog.destroy()
            
            ctk.CTkButton(button_frame, text="OK", command=on_ok).pack(side="left", padx=5)
            ctk.CTkButton(button_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)
            
        except Exception as e:
            self.logger.error(f"Error opening date picker: {e}")
            # Fallback: just log the attempt
            self.logger.info("Date picker dialog creation failed, using text entry only")
    
    def get_condition(self) -> Optional[FilterCondition]:
        """Get the filter condition from this widget."""
        field_name = self.field_var.get()
        operator_name = self.operator_var.get()
        
        if not field_name or not operator_name:
            return None
        
        if field_name not in self.field_definitions:
            return None
        
        field_def = self.field_definitions[field_name]
        field_type = FilterType(field_def.get('type', 'text'))
        
        try:
            operator = FilterOperator(operator_name)
        except ValueError:
            return None
        
        # Get value based on operator and field type
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            value = None
        elif operator == FilterOperator.BETWEEN:
            if field_type == FilterType.DATE:
                value = [self.start_date_var.get(), self.end_date_var.get()]
            elif field_type == FilterType.NUMBER:
                value = [self.min_value_var.get(), self.max_value_var.get()]
            else:
                return None
        elif operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            value = getattr(self, 'selected_values', [])
        else:
            value = getattr(self, 'value_var', ctk.StringVar()).get()
        
        return FilterCondition(field_name, operator, value, field_type)


class AdvancedFilterPanel(ctk.CTkFrame):
    """Advanced filtering panel with multiple conditions and groups."""
    
    def __init__(self, parent, field_definitions: Dict[str, Dict], on_filter_change: Optional[Callable] = None):
        super().__init__(parent)
        
        self.field_definitions = field_definitions
        self.on_filter_change = on_filter_change
        self.filter_widgets: List[FilterWidget] = []
        self.logger = get_logger(__name__)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the advanced filter panel UI."""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = ctk.CTkLabel(header_frame, text="Advanced Filters", font=("", 16, "bold"))
        title_label.pack(side="left", padx=10, pady=5)
        
        # Logic selection
        self.logic_var = ctk.StringVar(value="AND")
        logic_combo = ctk.CTkComboBox(
            header_frame,
            variable=self.logic_var,
            values=["AND", "OR"],
            width=80,
            command=self._on_logic_change
        )
        logic_combo.pack(side="right", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Logic:").pack(side="right", padx=5, pady=5)
        
        # Filter widgets container
        self.filters_frame = ctk.CTkScrollableFrame(self)
        self.filters_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(
            controls_frame,
            text="Add Filter",
            command=self._add_filter
        )
        add_btn.pack(side="left", padx=5, pady=5)
        
        clear_btn = ctk.CTkButton(
            controls_frame,
            text="Clear All",
            command=self._clear_filters
        )
        clear_btn.pack(side="left", padx=5, pady=5)
        
        apply_btn = ctk.CTkButton(
            controls_frame,
            text="Apply Filters",
            command=self._apply_filters
        )
        apply_btn.pack(side="right", padx=5, pady=5)
        
        # Add initial filter
        self._add_filter()
    
    def _add_filter(self):
        """Add a new filter widget."""
        filter_widget = FilterWidget(
            self.filters_frame,
            self.field_definitions,
            on_change=self._on_filter_change
        )
        filter_widget.pack(fill="x", pady=2)
        self.filter_widgets.append(filter_widget)
    
    def _clear_filters(self):
        """Clear all filter widgets."""
        for widget in self.filter_widgets:
            widget.destroy()
        self.filter_widgets.clear()
        self._add_filter()  # Add one empty filter
        self._on_filter_change()
    
    def _apply_filters(self):
        """Apply current filters."""
        if self.on_filter_change:
            self.on_filter_change()
    
    def _on_logic_change(self, value: str):
        """Handle logic selection change."""
        self._on_filter_change()
    
    def _on_filter_change(self):
        """Handle filter change."""
        if self.on_filter_change:
            self.on_filter_change()
    
    def get_filter_group(self) -> FilterGroup:
        """Get the current filter group."""
        group = FilterGroup(self.logic_var.get())
        
        for widget in self.filter_widgets:
            condition = widget.get_condition()
            if condition:
                group.add_condition(condition)
        
        return group
    
    def apply_filters(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply current filters to a list of items."""
        filter_group = self.get_filter_group()
        
        if not filter_group.conditions and not filter_group.groups:
            return items  # No filters, return all items
        
        return [item for item in items if filter_group.apply(item)]


class QuickFilterBar(ctk.CTkFrame):
    """Quick filter bar for common filtering operations."""
    
    def __init__(self, parent, on_filter_change: Optional[Callable] = None):
        super().__init__(parent)
        
        self.on_filter_change = on_filter_change
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the quick filter bar UI."""
        # Search box
        search_label = ctk.CTkLabel(self, text="Search:")
        search_label.pack(side="left", padx=5, pady=5)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        search_entry = ctk.CTkEntry(self, textvariable=self.search_var, width=200)
        search_entry.pack(side="left", padx=5, pady=5)
        
        # Status filter
        status_label = ctk.CTkLabel(self, text="Status:")
        status_label.pack(side="left", padx=(20, 5), pady=5)
        
        self.status_var = ctk.StringVar(value="All")
        status_combo = ctk.CTkComboBox(
            self,
            variable=self.status_var,
            values=["All", "Active", "Inactive", "Error", "Maintenance"],
            command=self._on_status_change
        )
        status_combo.pack(side="left", padx=5, pady=5)
        
        # Date range filter
        date_label = ctk.CTkLabel(self, text="Date Range:")
        date_label.pack(side="left", padx=(20, 5), pady=5)
        
        self.date_range_var = ctk.StringVar(value="All Time")
        date_combo = ctk.CTkComboBox(
            self,
            variable=self.date_range_var,
            values=["All Time", "Today", "This Week", "This Month", "Last 30 Days"],
            command=self._on_date_range_change
        )
        date_combo.pack(side="left", padx=5, pady=5)
        
        # Clear button
        clear_btn = ctk.CTkButton(
            self,
            text="Clear",
            width=80,
            command=self._clear_filters
        )
        clear_btn.pack(side="right", padx=5, pady=5)
    
    def _on_search_change(self, *args):
        """Handle search text change."""
        if self.on_filter_change:
            self.on_filter_change()
    
    def _on_status_change(self, value: str):
        """Handle status filter change."""
        if self.on_filter_change:
            self.on_filter_change()
    
    def _on_date_range_change(self, value: str):
        """Handle date range filter change."""
        if self.on_filter_change:
            self.on_filter_change()
    
    def _clear_filters(self):
        """Clear all quick filters."""
        self.search_var.set("")
        self.status_var.set("All")
        self.date_range_var.set("All Time")
        if self.on_filter_change:
            self.on_filter_change()
    
    def get_quick_filters(self) -> FilterGroup:
        """Get filter group representing current quick filters."""
        group = FilterGroup("AND")
        
        # Search filter
        search_text = self.search_var.get().strip()
        if search_text:
            search_condition = FilterCondition(
                "name",
                FilterOperator.CONTAINS,
                search_text,
                FilterType.TEXT
            )
            group.add_condition(search_condition)
        
        # Status filter
        status = self.status_var.get()
        if status != "All":
            status_condition = FilterCondition(
                "status",
                FilterOperator.EQUALS,
                status.lower(),
                FilterType.TEXT
            )
            group.add_condition(status_condition)
        
        # Date range filter
        date_range = self.date_range_var.get()
        if date_range != "All Time":
            end_date = datetime.now()
            
            if date_range == "Today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == "This Week":
                days_since_monday = end_date.weekday()
                start_date = end_date - timedelta(days=days_since_monday)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == "This Month":
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif date_range == "Last 30 Days":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = None
            
            if start_date:
                date_condition = FilterCondition(
                    "created_at",
                    FilterOperator.BETWEEN,
                    [start_date, end_date],
                    FilterType.DATE
                )
                group.add_condition(date_condition)
        
        return group
