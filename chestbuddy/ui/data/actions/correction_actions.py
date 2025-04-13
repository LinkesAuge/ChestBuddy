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
        """Shows a preview and applies the selected correction."""
        if not context.model or not context.clicked_index.isValid():
            return

        row = context.clicked_index.row()
        col = context.clicked_index.column()
        suggestions = context.model.get_correction_suggestions(row, col)
        original_value = context.model.data(context.clicked_index, Qt.DisplayRole)

        if not suggestions:
            QMessageBox.information(
                context.parent_widget,
                "Apply Correction",
                "No correction suggestions available for this cell.",
            )
            return

        # --- Prepare for Preview --- #
        # Currently applies first suggestion. If multiple, might need selection first.
        # Let's assume we apply the first one for now.
        first_suggestion = suggestions[0]
        corrected_value = getattr(first_suggestion, "corrected_value", None)
        if corrected_value is None:
            QMessageBox.warning(
                context.parent_widget,
                "Apply Correction",
                "Could not determine corrected value from suggestion.",
            )
            return

        changes_to_preview = [(context.clicked_index, original_value, corrected_value)]

        # --- Show Preview Dialog --- #
        preview_dialog = CorrectionPreviewDialog(changes_to_preview, context.parent_widget)
        if preview_dialog.exec() == QDialog.Accepted:
            print(f"ApplyCorrectionAction: Applying suggestion {first_suggestion} to ({row},{col})")

            # --- Actual application logic --- #
            # Replace placeholder with service call when ready
            # success = context.correction_service.apply_suggestion(row, col, first_suggestion)
            success = context.model.setData(context.clicked_index, corrected_value, Qt.EditRole)
            print(f"setData called, success: {success}")

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
        else:  # User clicked Cancel or closed the dialog
            print(f"ApplyCorrectionAction: Correction cancelled by user for ({row},{col}).")

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
