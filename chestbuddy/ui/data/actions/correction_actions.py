import typing
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QMenu

from .base_action import AbstractContextAction
from ..context.action_context import ActionContext
from ..models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import CellState

# Placeholder for CorrectionSuggestion structure
CorrectionSuggestion = typing.NewType("CorrectionSuggestion", object)


class ApplyCorrectionAction(AbstractContextAction):
    """Action to apply a suggested correction to a cell."""

    @property
    def id(self) -> str:
        return "apply_correction"

    @property
    def text(self) -> str:
        return "Apply Correction"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("edit-fix", QIcon(":/icons/edit-fix.png"))

    def is_applicable(self, context: ActionContext) -> bool:
        if not context.model or not context.clicked_index.isValid():
            return False
        state = context.model.data(context.clicked_index, DataViewModel.ValidationStateRole)
        # Check if it's correctable AND potentially if suggestions exist
        # For now, just check state
        return state == CellState.CORRECTABLE

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled if applicable (correctable state) and suggestions are actually available
        if not self.is_applicable(context):  # Check applicability first
            return False
        # Now check for suggestions
        suggestions = context.model.get_correction_suggestions(
            context.clicked_index.row(), context.clicked_index.column()
        )
        return suggestions is not None and len(suggestions) > 0

    def execute(self, context: ActionContext) -> None:
        """Applies the first available correction suggestion."""
        if not context.model or not context.clicked_index.isValid():
            return

        row = context.clicked_index.row()
        col = context.clicked_index.column()
        suggestions = context.model.get_correction_suggestions(row, col)

        if not suggestions:
            print(f"ApplyCorrectionAction: No suggestions found for ({row},{col}).")
            QMessageBox.information(
                context.parent_widget,
                "Apply Correction",
                "No correction suggestions available for this cell.",
            )
            return

        # For now, apply the first suggestion automatically
        # TODO: Handle multiple suggestions (e.g., show submenu/dialog)
        first_suggestion = suggestions[0]

        print(f"ApplyCorrectionAction: Applying suggestion {first_suggestion} to ({row},{col})")

        # --- Placeholder for actual application logic ---
        # This needs to interact with the model/service to change the data
        # and potentially trigger re-validation.
        # Example:
        # success = context.model.apply_correction(row, col, first_suggestion)
        success = False  # Placeholder
        print(f"Calling model.setData for ({row}, {col})")
        # success = context.model.apply_correction(row, col, first_suggestion)
        # Mock success for now
        # We need to define the structure of CorrectionSuggestion first
        # Assuming suggestion has a 'corrected_value' attribute
        corrected_value = getattr(first_suggestion, "corrected_value", "[Applied Correction]")
        success = context.model.setData(context.clicked_index, corrected_value, Qt.EditRole)
        print(f"setData called, success: {success}")
        # else:
        #      print("Error: DataViewModel does not have an apply_correction method.")
        # --- End Placeholder ---

        if success:
            QMessageBox.information(
                context.parent_widget,
                "Apply Correction",
                f"Correction applied successfully to cell ({row},{col}).",
            )
        else:
            QMessageBox.warning(
                context.parent_widget,
                "Apply Correction",
                f"Failed to apply correction to cell ({row},{col}).",
            )

        print(f"ApplyCorrectionAction executed.")  # Debug
