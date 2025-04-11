"""
edit_actions.py

Implementation of standard editing actions (Copy, Paste, Cut, Delete)
for the DataView context.
"""

import typing
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QGuiApplication
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel

from .base_action import AbstractContextAction

# Import real ActionContext
from ..context.action_context import ActionContext

# from ..menus.context_menu_factory import ContextMenuInfo as ActionContext
# ActionContext = typing.NewType("ActionContext", object)  # Placeholder

# --- Copy Action ---


class CopyAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "copy"

    @property
    def text(self) -> str:
        return "Copy"

    @property
    def icon(self) -> QIcon:
        # Use QIcon.fromTheme with a fallback path
        return QIcon.fromTheme("edit-copy", QIcon(":/icons/edit-copy.png"))

    @property
    def shortcut(self) -> QKeySequence:
        return QKeySequence.StandardKey.Copy

    def is_applicable(self, context: ActionContext) -> bool:
        # Copy is generally always applicable if there's a view
        return context.model is not None

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled only if there is a selection
        return len(context.selection) > 0

    def execute(self, context: ActionContext) -> None:
        """Copies the selected data to the clipboard."""
        selection = context.selection
        model = context.model
        if not selection or not model:
            return

        # Sort by row, then column using a key
        selection.sort(key=lambda idx: (idx.row(), idx.column()))

        # Create a set of (row, col) tuples for efficient lookup
        selection_coords = {(idx.row(), idx.column()) for idx in selection}

        min_row = min(idx.row() for idx in selection)
        max_row = max(idx.row() for idx in selection)
        min_col = min(idx.column() for idx in selection)
        max_col = max(idx.column() for idx in selection)

        rows_data = []
        for r in range(min_row, max_row + 1):
            cols_data = []
            for c in range(min_col, max_col + 1):
                # Check coordinates instead of mock objects
                if (r, c) in selection_coords:
                    index_to_check = model.index(r, c)  # Get index only if needed
                    data = model.data(index_to_check, Qt.DisplayRole)
                    cols_data.append(str(data) if data is not None else "")
                else:
                    # Add empty string for cells within bounds but not selected
                    cols_data.append("")
            rows_data.append("\t".join(cols_data))

        copied_text = "\n".join(rows_data)
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(copied_text)
            print(f"CopyAction executed.")  # Debug


# --- Paste Action ---


class PasteAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "paste"

    @property
    def text(self) -> str:
        return "Paste"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("edit-paste", QIcon(":/icons/edit-paste.png"))

    @property
    def shortcut(self) -> QKeySequence:
        return QKeySequence.StandardKey.Paste

    def is_applicable(self, context: ActionContext) -> bool:
        return context.model is not None

    def is_enabled(self, context: ActionContext) -> bool:
        clipboard = QGuiApplication.clipboard()
        if not clipboard or not clipboard.text():
            return False  # No text to paste

        # Determine target cell
        target_index = context.clicked_index
        if context.selection:
            # Pasting usually targets the top-left of current selection
            # or just the active cell if no block selection
            target_index = min(context.selection)

        if not target_index.isValid():
            # Cannot paste if there's no valid target cell
            # (e.g., right-click outside table after clearing selection)
            return False

        # Check if target cell is editable
        return bool(context.model.flags(target_index) & Qt.ItemIsEditable)

    def execute(self, context: ActionContext) -> None:
        """Pastes data from the clipboard into the table."""
        clipboard = QGuiApplication.clipboard()
        if not clipboard or not clipboard.text() or not context.model:
            return

        pasted_text = clipboard.text()
        pasted_lines = pasted_text.strip("\n").split("\n")
        pasted_data = [line.split("\t") for line in pasted_lines]

        if not pasted_data:
            return

        target_index = context.clicked_index
        if context.selection:
            target_index = min(context.selection)

        if not target_index.isValid():
            return

        start_row = target_index.row()
        start_col = target_index.column()
        model = context.model

        num_rows_to_paste = len(pasted_data)
        num_cols_to_paste = max(len(row) for row in pasted_data)

        max_target_row = min(start_row + num_rows_to_paste, model.rowCount())
        max_target_col = min(start_col + num_cols_to_paste, model.columnCount())

        for r_offset, row_data in enumerate(pasted_data):
            target_row = start_row + r_offset
            if target_row >= max_target_row:
                break
            for c_offset, cell_value in enumerate(row_data):
                target_col = start_col + c_offset
                if target_col >= max_target_col:
                    break  # Stop processing columns beyond the limit for this row

                idx = model.index(target_row, target_col)
                if bool(model.flags(idx) & Qt.ItemIsEditable):
                    model.setData(idx, cell_value, Qt.EditRole)

        print(f"PasteAction executed.")  # Debug


# --- Delete Action ---


class DeleteAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "delete"

    @property
    def text(self) -> str:
        return "Delete"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("edit-delete", QIcon(":/icons/edit-delete.png"))

    @property
    def shortcut(self) -> QKeySequence:
        return QKeySequence.StandardKey.Delete

    def is_applicable(self, context: ActionContext) -> bool:
        return context.model is not None

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled if there is a selection and at least one selected cell is editable
        return len(context.selection) > 0 and any(
            bool(context.model.flags(idx) & Qt.ItemIsEditable) for idx in context.selection
        )

    def execute(self, context: ActionContext) -> None:
        """Deletes the content of the selected cells."""
        selection = context.selection
        model = context.model
        if not selection or not model:
            return

        deleted_count = 0
        for index in selection:
            if bool(model.flags(index) & Qt.ItemIsEditable):
                if model.setData(index, "", Qt.EditRole):  # Set to empty string
                    deleted_count += 1
        print(f"DeleteAction executed. Cleared {deleted_count} cells.")  # Debug


# --- Cut Action ---


class CutAction(AbstractContextAction):
    @property
    def id(self) -> str:
        return "cut"

    @property
    def text(self) -> str:
        return "Cut"

    @property
    def icon(self) -> QIcon:
        return QIcon.fromTheme("edit-cut", QIcon(":/icons/edit-cut.png"))

    @property
    def shortcut(self) -> QKeySequence:
        return QKeySequence.StandardKey.Cut

    def is_applicable(self, context: ActionContext) -> bool:
        # Applicable if Copy and Delete are applicable
        return CopyAction().is_applicable(context) and DeleteAction().is_applicable(context)

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled if Copy and Delete are enabled
        return CopyAction().is_enabled(context) and DeleteAction().is_enabled(context)

    def execute(self, context: ActionContext) -> None:
        """Performs a cut operation (Copy + Delete)."""
        CopyAction().execute(context)  # Copy first
        DeleteAction().execute(context)  # Then delete
        print(f"CutAction executed.")  # Debug


# --- Edit Cell Action (In-Place) ---


class EditCellAction(AbstractContextAction):
    """Action to trigger editing of the selected cell."""

    @property
    def id(self) -> str:
        return "edit_cell"

    @property
    def text(self) -> str:
        return "Edit Cell"

    @property
    def icon(self) -> QIcon:
        # Use a standard edit icon
        return QIcon.fromTheme("document-edit", QIcon(":/icons/edit.png"))

    @property
    def shortcut(self) -> typing.Optional[QKeySequence]:
        # Standard shortcut for editing
        return QKeySequence(Qt.Key_F2)

    def is_applicable(self, context: ActionContext) -> bool:
        # Applicable if there is a model and exactly one cell selected
        return context.model is not None and len(context.selection) == 1

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled if the selected cell is editable
        if len(context.selection) != 1:
            return False
        index = context.selection[0]
        return bool(context.model.flags(index) & Qt.ItemIsEditable)

    def execute(self, context: ActionContext) -> None:
        """Triggers the edit operation on the selected cell in the parent view."""
        if not self.is_applicable(context) or not self.is_enabled(context):
            print("EditCellAction: Cannot execute, not applicable or enabled.")
            return

        index_to_edit = context.selection[0]
        parent_view = context.parent_widget  # Assuming parent_widget is the QTableView

        if parent_view and hasattr(parent_view, "edit"):
            print(
                f"EditCellAction: Triggering edit for index {index_to_edit.row()},{index_to_edit.column()})"
            )
            # Call the view's edit slot
            parent_view.edit(index_to_edit)
        else:
            # Remove debug print
            # print(f"EditCellAction: In else block. parent_view is {parent_view}")
            print("EditCellAction: Parent widget is not a view or does not support edit().")
            QMessageBox.warning(
                context.parent_widget,
                self.text,
                "Cannot initiate edit operation on the current view.",
            )


# --- Edit Cell Action (Dialog) ---


# Placeholder Dialog - Needs refinement for context-awareness
class ComplexEditDialog(QDialog):
    """
    A dialog for more complex or multi-line editing.
    Currently a placeholder, will be made context-aware.
    """

    def __init__(self, context: ActionContext, parent=None):
        """
        Initialize the dialog.

        Args:
            context: The ActionContext containing model, index, etc.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Cell Value")
        self.setMinimumSize(400, 200)  # Give it a reasonable default size

        self.context = context
        self.new_value = None  # Store accepted value

        # Get initial value from context
        self.initial_value = ""
        if (
            self.context.clicked_index
            and self.context.clicked_index.isValid()
            and self.context.model
        ):
            self.initial_value = str(
                self.context.model.data(self.context.clicked_index, Qt.DisplayRole) or ""
            )

        # --- UI Setup ---
        layout = QVBoxLayout(self)

        # TODO: Dynamically choose editor based on context.model and context.clicked_index column type
        # For now, always use QTextEdit
        self.editor = QTextEdit()
        self.editor.setPlainText(self.initial_value)  # Set initial value
        layout.addWidget(QLabel("Enter new value:"))
        layout.addWidget(self.editor)

        # Standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.editor.setFocus()  # Focus the editor initially

    def accept(self):
        """Store the new value when OK is clicked."""
        # TODO: Get value based on the actual editor widget used
        self.new_value = self.editor.toPlainText()
        super().accept()

    def get_new_value(self) -> typing.Optional[str]:
        """Return the accepted new value, or None if cancelled."""
        return self.new_value


class ShowEditDialogAction(AbstractContextAction):
    """Action to show a more complex editing dialog."""

    @property
    def id(self) -> str:
        return "show_edit_dialog"

    @property
    def text(self) -> str:
        return "Edit (Dialog)"  # Distinguish from simple edit

    @property
    def icon(self) -> QIcon:
        # Maybe a different edit icon?
        # For now, use the same as EditCellAction
        return QIcon.fromTheme("document-edit", QIcon(":/icons/edit.png"))

    def is_applicable(self, context: ActionContext) -> bool:
        # Applicable if there is a model and exactly one cell selected
        # Same logic as EditCellAction for now
        return context.model is not None and len(context.selection) == 1

    def is_enabled(self, context: ActionContext) -> bool:
        # Enabled if applicable and the cell is editable
        # Same logic as EditCellAction for now
        if not self.is_applicable(context):
            return False
        index = context.selection[0]
        return bool(context.model.flags(index) & Qt.ItemIsEditable)

    def execute(self, context: ActionContext) -> None:
        """Shows the complex edit dialog for the selected cell."""
        if not self.is_enabled(context):
            return

        index = context.selection[0]
        model = context.model

        # Pass the whole context to the dialog
        dialog = ComplexEditDialog(context=context, parent=context.parent_widget)

        if dialog.exec() == QDialog.Accepted:
            new_value = dialog.get_new_value()
            if new_value is not None:  # Check if not cancelled
                if model.setData(index, new_value, Qt.EditRole):
                    print(
                        f"ShowEditDialogAction: Set data '{new_value}' to {index.row()},{index.column()}"
                    )
                else:
                    print(
                        f"ShowEditDialogAction: setData failed for {index.row()},{index.column()}"
                    )
                    # Optionally show an error message
                    QMessageBox.warning(
                        context.parent_widget, "Edit Failed", "Could not set the new value."
                    )
            else:
                print(f"ShowEditDialogAction: Dialog cancelled or returned None.")
        else:
            print(f"ShowEditDialogAction: Dialog rejected.")
