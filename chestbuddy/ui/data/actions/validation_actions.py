"""
validation_actions.py

Actions related to data validation.
"""

import typing
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox

from .base_action import AbstractContextAction
from ..context.action_context import ActionContext
from ..models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import CellState


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

        # Get error details using the model's method (which calls state manager)
        error_details = context.model.get_cell_details(
            context.clicked_index.row(), context.clicked_index.column()
        )

        if not error_details:
            error_details = "No specific error details available."

        QMessageBox.warning(
            context.parent_widget,  # Use parent widget from context
            "Validation Error",
            f"Error in cell ({context.clicked_index.row()}, {context.clicked_index.column()}):\n\n{error_details}",
        )
        print(f"ViewErrorAction executed.")  # Debug
