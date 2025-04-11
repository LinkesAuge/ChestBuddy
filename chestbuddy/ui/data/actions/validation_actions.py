"""
validation_actions.py

Actions related to data validation.
"""

import typing
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from unittest.mock import patch  # Keep for service sim

from .base_action import AbstractContextAction
from ..context.action_context import ActionContext  # Make sure this is imported
from chestbuddy.ui.dialogs.add_validation_entry_dialog import (
    AddValidationEntryDialog,
)  # Import new dialog
from chestbuddy.ui.dialogs.batch_add_validation_dialog import (
    BatchAddValidationDialog,
)  # Import batch dialog

# from ....core.services.validation_service import ValidationService # Placeholder
from chestbuddy.core.table_state_manager import CellState
from ..models.data_view_model import DataViewModel  # For role access


class ViewErrorAction(AbstractContextAction):
    """Action to view the validation error details for a cell."""

    @property
    def id(self) -> str:
        return "view_error"

    @property
    def text(self) -> str:
        return "View Validation Error"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("dialog-error", QIcon(":/icons/dialog-error.png"))

    def is_applicable(self, context: ActionContext) -> bool:
        if not context.model or not context.clicked_index.isValid():
            return False
        state = context.model.data(context.clicked_index, DataViewModel.ValidationStateRole)
        return state == CellState.INVALID

    def is_enabled(self, context: ActionContext) -> bool:
        # Always enabled if applicable, error details might be empty
        return True

    def execute(self, context: ActionContext) -> None:
        """Shows the validation error details for the clicked cell."""
        if not context.model or not context.clicked_index.isValid():
            return

        row = context.clicked_index.row()
        col = context.clicked_index.column()

        # Use the correct role to get error details
        details = context.model.data(context.clicked_index, DataViewModel.ValidationErrorRole)

        message = (
            f"Error in cell ({row}, {col}):\n\n{details or 'No specific error details available.'}"
        )

        QMessageBox.warning(context.parent_widget, self.text, message)
        print(f"ViewErrorAction executed.")  # Debug


class AddToValidationListAction(AbstractContextAction):
    """Action to add selected cell value(s) to the validation list."""

    @property
    def id(self) -> str:
        return "add_validation"

    @property
    def text(self) -> str:
        return "Add to Validation List"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("list-add", QIcon(":/icons/list-add.png"))

    def is_applicable(self, context: ActionContext) -> bool:
        return context.model is not None

    def is_enabled(self, context: ActionContext) -> bool:
        return len(context.selection) > 0

    # --- Simulated Service Call ---
    @staticmethod
    @patch("builtins.print")
    def _call_validation_service_add(list_type: str, values: typing.List[str]) -> bool:
        """Placeholder function to simulate calling ValidationService.add_entries."""
        print(f"Simulating ValidationService.add_entries('{list_type}', {values})")
        return True  # Assume success

    # --- END SIMULATED ---

    def execute(self, context: ActionContext) -> None:
        """Adds the selected cell data to the validation list."""
        if not context.selection:
            print("AddToValidationListAction: No cells selected.")
            QMessageBox.information(context.parent_widget, self.text, "No cell selected.")
            return

        if not context.model:
            return

        selected_values = []
        for index in context.selection:
            if index.isValid():
                data = context.model.data(index, Qt.DisplayRole)
                selected_values.append(str(data) if data is not None else "")

        unique_values = sorted(list(set(val for val in selected_values if val)))

        if not unique_values:
            print("AddToValidationListAction: No non-empty values selected.")
            QMessageBox.information(
                context.parent_widget, self.text, "No non-empty values selected to add."
            )
            return

        # --- Get Service from Context (check early) ---
        if not context.validation_service:
            print("Error: ValidationService not available in context.")
            QMessageBox.critical(
                context.parent_widget,
                self.text,
                "Validation service is unavailable. Cannot add entries.",
            )
            return

        # --- Choose Dialog based on selection count ---
        details = None
        is_batch = len(unique_values) > 1

        if is_batch:
            print(f"AddToValidationListAction: Using Batch Dialog for {len(unique_values)} values.")
            dialog = BatchAddValidationDialog(unique_values, context.parent_widget)
            details = dialog.get_batch_details()
        else:
            print(f"AddToValidationListAction: Using Single Entry Dialog for 1 value.")
            dialog = AddValidationEntryDialog(unique_values, context.parent_widget)
            details = dialog.get_validation_details()

        # --- Handle Dialog Result ---
        if not details:
            print("AddToValidationListAction: Addition cancelled by user.")
            return

        # --- Call Service ---
        values_to_add = details["values"]
        list_type = details["list_type"]
        success = False
        error_occurred = False

        try:
            # Assuming service method is add_entries(list_type: str, values: List[str])
            # Service handles adding multiple values internally
            print(f"Attempting to add {len(values_to_add)} validation entries...")
            success = context.validation_service.add_entries(
                list_type=list_type, values=values_to_add
            )
        except Exception as e:
            print(f"Error calling ValidationService.add_entries: {e}")
            error_occurred = True
            QMessageBox.critical(
                context.parent_widget, self.text, f"An error occurred while adding entries: {e}"
            )
            # Don't return yet, show appropriate message below

        # --- Show Result Message ---
        if error_occurred:
            # Error message already shown
            pass
        elif success:
            value_str = ", ".join([f'"{v}"' for v in values_to_add[:3]])
            if len(values_to_add) > 3:
                value_str += ", ..."
            QMessageBox.information(
                context.parent_widget,
                self.text,
                f"Successfully added {len(values_to_add)} value(s) to list '{list_type}':\n{value_str}",
            )
            print(f"AddToValidationListAction: Entries added successfully.")
        else:
            QMessageBox.critical(
                context.parent_widget, self.text, f"Failed to add entries to list '{list_type}'."
            )
            print(f"AddToValidationListAction: Failed to add entries.")
