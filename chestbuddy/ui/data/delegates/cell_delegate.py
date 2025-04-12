"""
cell_delegate.py

Base delegate for rendering and editing cells in the DataTableView.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget, QLineEdit
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel, Signal, QObject, QEvent
from PySide6.QtGui import QPainter, QColor, QIcon
import typing
from typing import Any, Optional

# Import role from view model
from ..models.data_view_model import DataViewModel

# --- Assume ValidationService is available somehow ---
# Option 1: Import directly (if singleton or module-level instance)
# from chestbuddy.core.services import ValidationService
# validation_service = ValidationService.instance() # Example

# Option 2: Get from parent (if parent provides it)
# parent.validation_service

# Option 3: Pass during init
# self.validation_service = validation_service


# For now, let's mock a validation function
# In real implementation, replace this with actual service call
def _mock_validate_data(index: QModelIndex, value: Any) -> tuple[bool, Optional[str]]:
    # Mock validation: Check if column is 'Score' and value is numeric
    if index.column() == 2:  # Assuming 'Score' is column 2
        try:
            float(value)
            return True, None  # Valid
        except (ValueError, TypeError):
            return False, "Score must be a number."
    return True, None  # Assume other columns are valid for now


class CellDelegate(QStyledItemDelegate):
    """
    Base delegate for rendering and editing cells in the DataTableView.
    Handles basic rendering and editor creation.
    Subclasses can override painting for specific states (validation, etc.).
    """

    # Signal emitted when editor data needs validation before committing
    # Arguments: value (editor content), index (model index)
    validationRequested = Signal(object, QModelIndex)
    # Add a signal for validation failure notification
    validationFailed = Signal(QModelIndex, str)

    def __init__(self, parent: QObject | None = None):
        """
        Initialize the CellDelegate.

        Args:
            parent (QObject, optional): Parent object. Defaults to None.
        """
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Renders the delegate using the given painter and style option for the item specified by index.

        Args:
            painter (QPainter): The painter to use.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.
        """
        # TODO: Add custom painting logic based on cell state (validation, etc.)
        # For now, just call the base implementation
        super().paint(painter, option, index)
        # Call the superclass implementation directly to avoid issues with super() in tests
        # QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> typing.Optional[QWidget]:
        """
        Creates the editor to be used for editing the data item specified by index.

        Args:
            parent (QWidget): The parent widget for the editor.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.

        Returns:
            Optional[QWidget]: The editor widget, or None if no editor is needed.
        """
        # TODO: Create editors based on data type (e.g., QSpinBox for ints)
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """
        Sets the data to be displayed and edited by the editor from the data model item specified by index.

        Args:
            editor (QWidget): The editor widget.
            index (QModelIndex): The model index.
        """
        value = index.model().data(index, Qt.EditRole)
        if isinstance(editor, QLineEdit):
            editor.setText(str(value))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        """
        Get data from the editor and emit validationRequested signal.
        The actual setting of data to the model is deferred until validation passes.
        """
        value = None
        if isinstance(editor, QLineEdit):
            value = editor.text()
        # TODO: Handle other editor types

        if value is not None:
            print(
                f"CellDelegate: Emitting validationRequested for value '{value}' at index {index.row()},{index.column()}"
            )  # Debug
            # Emit signal instead of calling model.setData directly
            self.validationRequested.emit(value, index)
        # We do NOT call model.setData here. The handler for validationRequested will do it.
        # The old validation logic here is removed.

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        """
        Updates the editor for the item specified by index according to the style option given.

        Args:
            editor (QWidget): The editor widget.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.
        """
        super().updateEditorGeometry(editor, option, index)

    # --- Custom methods can be added here ---

    # --- Helper Methods for Subclasses (Optional) ---
    def _draw_background(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # ... (existing _draw_background) ...
        pass

    def _draw_text(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        # ... (existing _draw_text) ...
        pass

    def _get_cell_state(self, index: QModelIndex):
        # ... (existing _get_cell_state) ...
        pass
