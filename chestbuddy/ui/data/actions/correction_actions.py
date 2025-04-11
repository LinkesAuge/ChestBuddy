import typing
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QMenu
from unittest.mock import patch  # Temporary for simulation

from .base_action import AbstractContextAction
from ..context.action_context import ActionContext
from ..models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import CellState
from chestbuddy.ui.dialogs.add_correction_rule_dialog import AddCorrectionRuleDialog
from chestbuddy.ui.dialogs.batch_add_correction_dialog import BatchAddCorrectionDialog
# Placeholder for future dialog and service
# from ...dialogs.add_correction_rule_dialog import AddCorrectionRuleDialog
# from ....core.services.correction_service import CorrectionService


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


class AddToCorrectionListAction(AbstractContextAction):
    """Action to add selected cell value(s) to the correction list."""

    @property
    def id(self) -> str:
        return "add_correction"

    @property
    def text(self) -> str:
        return "Add to Correction List"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("list-add", QIcon(":/icons/list-add.png"))

    def is_applicable(self, context: ActionContext) -> bool:
        return context.model is not None

    def is_enabled(self, context: ActionContext) -> bool:
        return len(context.selection) > 0

    def execute(self, context: ActionContext) -> None:
        """Adds the selected cell data to the correction list."""
        if not context.selection:
            print("AddToCorrectionListAction: No cells selected.")
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
            print("AddToCorrectionListAction: No non-empty values selected.")
            QMessageBox.information(
                context.parent_widget, self.text, "No non-empty values selected to add."
            )
            return

        # --- Get Service from Context (check early) ---
        if not context.correction_service:
            print("Error: CorrectionService not available in context.")
            QMessageBox.critical(
                context.parent_widget,
                self.text,
                "Correction service is unavailable. Cannot add rules.",
            )
            return

        # --- Choose Dialog based on selection count ---
        details = None
        is_batch = len(unique_values) > 1  # Or maybe len(context.selection) > 1?
        # Using unique_values seems better.

        if is_batch:
            print(f"AddToCorrectionListAction: Using Batch Dialog for {len(unique_values)} values.")
            dialog = BatchAddCorrectionDialog(unique_values, context.parent_widget)
            details = dialog.get_batch_details()
        else:
            print(f"AddToCorrectionListAction: Using Single Rule Dialog for 1 value.")
            # For single selection, use the first unique value as default 'from'
            default_from = unique_values[0]
            dialog = AddCorrectionRuleDialog(
                default_from_value=default_from, parent=context.parent_widget
            )
            details = dialog.get_rule_details()

        # --- Handle Dialog Result ---
        if not details:
            print("AddToCorrectionListAction: Rule addition cancelled by user.")
            return

        # --- Call Service ---
        success_count = 0
        total_rules_attempted = 0
        error_occurred = False

        try:
            if is_batch:
                from_values = details["from_values"]
                to_value = details["to_value"]
                category = details["category"]
                enabled = details["enabled"]
                total_rules_attempted = len(from_values)

                print(f"Attempting to add {total_rules_attempted} batch rules...")
                # Call add_rule for each unique value
                for from_val in from_values:
                    if context.correction_service.add_rule(
                        from_value=from_val, to_value=to_value, category=category, enabled=enabled
                    ):
                        success_count += 1
            else:  # Single rule
                from_value = details["from_value"]
                to_value = details["to_value"]
                category = details["category"]
                enabled = details["enabled"]
                total_rules_attempted = 1

                print(f"Attempting to add 1 rule...")
                if context.correction_service.add_rule(
                    from_value=from_value, to_value=to_value, category=category, enabled=enabled
                ):
                    success_count += 1

        except Exception as e:
            print(f"Error calling CorrectionService.add_rule(s): {e}")
            error_occurred = True
            QMessageBox.critical(
                context.parent_widget, self.text, f"An error occurred while adding rule(s): {e}"
            )
            # Don't return yet, show partial success if any

        # --- Show Result Message ---
        if error_occurred:
            # Error message already shown
            if success_count > 0:
                QMessageBox.warning(
                    context.parent_widget,
                    self.text,
                    f"An error occurred, but {success_count} out of {total_rules_attempted} rule(s) might have been added successfully.",
                )
        elif success_count == total_rules_attempted:
            QMessageBox.information(
                context.parent_widget, self.text, f"Successfully added {success_count} rule(s)."
            )
            print(f"AddToCorrectionListAction: {success_count} rule(s) added successfully.")
        else:  # Partial success without exception (e.g., service returned False)
            QMessageBox.warning(
                context.parent_widget,
                self.text,
                f"Successfully added {success_count} out of {total_rules_attempted} rule(s). Some failed.",
            )
            print(
                f"AddToCorrectionListAction: Added {success_count}/{total_rules_attempted} rules."
            )
