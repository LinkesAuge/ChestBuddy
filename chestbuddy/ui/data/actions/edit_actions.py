"""
edit_actions.py

Implementation of standard editing actions (Copy, Paste, Cut, Delete)
for the DataView context.
"""

import typing
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QGuiApplication

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
