import typing
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QMenu, QDialog
from unittest.mock import patch  # Temporary for simulation

from .base_action import AbstractContextAction
from ..context.action_context import ActionContext
from ..models.data_view_model import DataViewModel
from chestbuddy.core.table_state_manager import CellState
from chestbuddy.ui.dialogs.add_correction_rule_dialog import AddCorrectionRuleDialog
from chestbuddy.ui.dialogs.batch_add_correction_dialog import BatchAddCorrectionDialog
from chestbuddy.ui.widgets.correction_preview_dialog import CorrectionPreviewDialog
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
        """Applicable only if exactly one cell is clicked and it's correctable."""
        if not context.clicked_index.isValid() or len(context.selection) > 1:
            return False
        # Use the state_manager to check the state
        state = context.get_cell_state(context.clicked_index)  # Use helper method
        return state and state.validation_status == CellState.CORRECTABLE

    def is_enabled(self, context: ActionContext) -> bool:
        """Enabled if applicable and suggestions are actually available."""
        if not self.is_applicable(context):
            return False
        # Use the state_manager (via context helper) to check for suggestions
        state = context.get_cell_state(context.clicked_index)
        return state and bool(state.correction_suggestions)

    def execute(self, context: ActionContext) -> None:
        """Apply the first correction suggestion."""
        if not self.is_enabled(context):
            return

        index = context.clicked_index
        # Get suggestion from state manager via context helper
        state = context.get_cell_state(index)
        if state and state.correction_suggestions:
            suggestion = state.correction_suggestions[0]  # Apply first one
            # Trigger the correction via the adapter/service
            # Requires CorrectionAdapter to be accessible or signal emission
            if context.correction_service:  # Check if service mock is available
                try:
                    # We need the adapter slot here ideally, or call service directly
                    # context.correction_adapter.apply_correction_from_ui(index.row(), index.column(), suggestion)
                    # Calling service directly for now, assuming adapter connection works elsewhere
                    context.correction_service.apply_ui_correction(
                        index.row(),
                        index.column(),
                        suggestion.corrected_value
                        if hasattr(suggestion, "corrected_value")
                        else suggestion,
                    )
                    print(
                        f"ApplyCorrectionAction executed for ({index.row()}, {index.column()})."
                    )  # Debug
                except AttributeError as e:
                    print(f"Error executing ApplyCorrectionAction: {e}")
            else:
                print("Correction service not available in context for ApplyCorrectionAction")
        else:
            print("No suggestion found to apply.")


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


# TODO: Create a BatchApplyCorrectionAction that gathers multiple suggestions
# and passes them to the CorrectionPreviewDialog.


class BatchApplyCorrectionAction(AbstractContextAction):
    """Action to apply the first suggested correction to multiple cells in batch."""

    @property
    def id(self) -> str:
        return "batch_apply_correction"

    @property
    def text(self) -> str:
        return "Batch Apply Corrections"

    @property
    def icon(self) -> QIcon:
        # Consider a different icon, maybe magic wand with plus?
        return QIcon.fromTheme("edit-fix-all", QIcon(":/icons/edit-fix-all.png"))

    def is_applicable(self, context: ActionContext) -> bool:
        # Applicable if there's a model
        return context.model is not None

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled if the model has *any* correctable cells (check might be expensive)
        # For now, let's assume enabled if applicable, execute will check.
        # A better approach might involve the model/state manager caching this.
        if not self.is_applicable(context):
            return False
        # TODO: Maybe add a quick check if CorrectionService has suggestions pending?
        return True  # Optimistically enabled

    def execute(self, context: ActionContext) -> None:
        """Gathers all correctable cells, shows preview, applies corrections if accepted."""
        if not context.model:
            return

        source_model = context.model
        changes_to_preview = []
        print("BatchApplyCorrectionAction: Scanning for correctable cells...")

        # Determine scope: selection or all? For now, let's do all.
        # TODO: Add logic to check context.selection first
        for row in range(source_model.rowCount()):
            for col in range(source_model.columnCount()):
                index = source_model.index(row, col)
                if not index.isValid():
                    continue

                state = source_model.data(index, DataViewModel.ValidationStateRole)
                if state == CellState.CORRECTABLE:
                    suggestions = source_model.get_correction_suggestions(row, col)
                    if suggestions and len(suggestions) > 0:
                        first_suggestion = suggestions[0]
                        corrected_value = getattr(first_suggestion, "corrected_value", None)
                        if corrected_value is not None:
                            original_value = source_model.data(index, Qt.DisplayRole)
                            changes_to_preview.append((index, original_value, corrected_value))

        if not changes_to_preview:
            print("BatchApplyCorrectionAction: No correctable cells with suggestions found.")
            QMessageBox.information(
                context.parent_widget,
                self.text,
                "No correctable cells with suggestions found to apply.",
            )
            return

        print(f"BatchApplyCorrectionAction: Found {len(changes_to_preview)} potential corrections.")

        # Show Preview Dialog
        preview_dialog = CorrectionPreviewDialog(changes_to_preview, context.parent_widget)
        if preview_dialog.exec() == QDialog.Accepted:
            print(f"BatchApplyCorrectionAction: Applying {len(changes_to_preview)} corrections...")
            applied_count = 0
            failed_count = 0
            for index, _, corrected_value in changes_to_preview:
                # Apply correction using model.setData
                # TODO: Replace with service call if appropriate
                if source_model.setData(index, corrected_value, Qt.EditRole):
                    applied_count += 1
                else:
                    failed_count += 1
                    print(
                        f"BatchApplyCorrectionAction: Failed to apply correction at {index.row()},{index.column()}"
                    )

            # Show summary message
            summary_message = f"Applied {applied_count} correction(s)."
            if failed_count > 0:
                summary_message += f"\nFailed to apply {failed_count} correction(s)."
                QMessageBox.warning(context.parent_widget, self.text, summary_message)
            else:
                QMessageBox.information(context.parent_widget, self.text, summary_message)

        else:
            print("BatchApplyCorrectionAction: Batch correction cancelled by user.")

        print(f"BatchApplyCorrectionAction executed.")  # Debug


"""
PreviewCorrectionAction class.
"""


class PreviewCorrectionAction(AbstractContextAction):
    """
    Action to show a preview of the suggested correction for a cell.
    """

    @property
    def id(self) -> str:
        return "preview_correction"

    @property
    def text(self) -> str:
        return "Preview Correction..."

    @property
    def icon(self) -> QIcon | None:
        # TODO: Add an appropriate icon if available
        return None  # QIcon.fromTheme("document-preview")

    @property
    def tooltip(self) -> str:
        return "Show a preview of the suggested correction before applying."

    def is_applicable(self, context: ActionContext) -> bool:
        """Applicable only if exactly one cell is clicked and it's correctable."""
        if not context.clicked_index.isValid() or len(context.selection) > 1:
            return False

        state = context.get_cell_state(context.clicked_index)
        return (
            state
            and state.validation_status == CellState.CORRECTABLE
            and bool(state.correction_suggestions)
        )

    def is_enabled(self, context: ActionContext) -> bool:
        """Enabled if applicable."""
        return self.is_applicable(context)

    def execute(self, context: ActionContext) -> None:
        """Show the Correction Preview dialog."""
        if not self.is_applicable(context):
            return

        index = context.clicked_index
        state = context.get_cell_state(index)
        original_value = context.model.data(index, Qt.DisplayRole)  # Get original value

        # Assume the first suggestion is the primary one for preview
        if state and state.correction_suggestions:
            suggested_value = state.correction_suggestions[0]

            dialog = CorrectionPreviewDialog(
                str(original_value), str(suggested_value), context.parent_widget
            )
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                # If user clicks "Apply Correction", trigger the actual correction action
                # Find the 'ApplyCorrectionAction' and execute it for the first suggestion.
                # This assumes ApplyCorrectionAction can handle a specific suggestion.
                # This might need refinement based on ApplyCorrectionAction's design.
                print(
                    f"Preview accepted for cell ({index.row()}, {index.column()}). Triggering apply..."
                )
                # Option 1: Directly call adapter/service (less ideal from action)
                # context.correction_adapter.apply_correction_from_ui(index.row(), index.column(), suggested_value)

                # Option 2: Trigger the ApplyCorrectionAction (better separation)
                apply_action = ApplyCorrectionAction()
                if apply_action.is_applicable(context):
                    # We might need to pass the specific suggestion to the execute method
                    # or modify ApplyCorrectionAction to handle this scenario.
                    # For now, just call execute, assuming it applies the first suggestion by default.
                    apply_action.execute(context)
                else:
                    print("Could not trigger ApplyCorrectionAction after preview.")
            else:
                print(f"Preview cancelled for cell ({index.row()}, {index.column()})")
        else:
            print("No suggestion found for preview.")
