"""
validation_delegate.py

Description: Custom table delegate for visualizing validation status
Usage:
    table_view.setItemDelegate(ValidationStatusDelegate(parent))
"""

import logging
from typing import Optional, Any

from PySide6.QtCore import Qt, QModelIndex, QRect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem

from chestbuddy.core.validation_enums import ValidationStatus

# Set up logger
logger = logging.getLogger(__name__)


class ValidationStatusDelegate(QStyledItemDelegate):
    """
    Delegate for displaying validation status in table cells.

    This delegate provides visual highlighting of cells based on their validation status.
    Valid cells are displayed normally, warning cells are highlighted in yellow,
    and invalid cells are highlighted in red.

    Attributes:
        VALID_COLOR: Background color for valid cells (transparent)
        WARNING_COLOR: Background color for cells with warnings (light yellow)
        INVALID_COLOR: Background color for invalid cells (dark red)
        INVALID_ROW_COLOR: Background color for rows with invalid cells (light red)
    """

    # Define colors for different validation states
    VALID_COLOR = QColor(0, 255, 0, 30)  # Light green transparent
    WARNING_COLOR = QColor(255, 240, 0, 80)  # Light yellow
    INVALID_COLOR = QColor(200, 0, 0, 150)  # Darker red with more opacity
    INVALID_ROW_COLOR = QColor(255, 200, 200, 70)  # Light red for row highlighting
    NOT_VALIDATED_COLOR = QColor(200, 200, 200, 40)  # Light gray for not validated

    # Column name constants
    STATUS_COLUMN = "STATUS"

    def __init__(self, parent=None):
        """
        Initialize the ValidationStatusDelegate.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the cell with validation status indication.

        Args:
            painter: Painter to use for drawing
            option: Style options for the item
            index: Model index of the item to paint
        """
        # Save painter state
        painter.save()

        # Get the text content to determine if this is a status column
        model = index.model()
        if model is None:
            super().paint(painter, option, index)
            painter.restore()
            return

        # Get column header name
        column_name = None
        try:
            column_name = model.headerData(index.column(), Qt.Horizontal)
        except Exception as e:
            self.logger.debug(f"Could not get column header: {e}")

        # Check if this is the status column
        is_status_column = column_name == self.STATUS_COLUMN

        # If this is the status column, paint based on the text value
        if is_status_column:
            # Get the display text
            text = index.data(Qt.DisplayRole)
            self.logger.debug(f"Status column text: {text}")

            if text == "Valid":
                # Use light green for valid status
                painter.fillRect(option.rect, self.VALID_COLOR)
            elif text == "Invalid":
                # Paint with error background
                painter.fillRect(option.rect, self.INVALID_COLOR)
            elif text == "Not validated":
                # Light gray for not validated
                painter.fillRect(option.rect, self.NOT_VALIDATED_COLOR)
        else:
            # Get validation status from model data (Qt.UserRole + 1)
            validation_status = index.data(Qt.ItemDataRole.UserRole + 1)

            # Check if any cell in this row is invalid - look for the STATUS column
            status_col_idx = -1
            for col in range(model.columnCount()):
                col_header = model.headerData(col, Qt.Horizontal)
                if col_header == self.STATUS_COLUMN:
                    status_col_idx = col
                    break

            # If status column found, check its value
            if status_col_idx >= 0:
                status_idx = model.index(index.row(), status_col_idx)
                status_text = status_idx.data(Qt.DisplayRole)

                # If the status is "Invalid" and this isn't the status column itself,
                # highlight with row invalid color
                if status_text == "Invalid" and not is_status_column:
                    painter.fillRect(option.rect, self.INVALID_ROW_COLOR)

            # Additionally, check cell-specific validation status
            if validation_status == ValidationStatus.INVALID:
                # Draw with error highlighting
                painter.fillRect(option.rect, self.INVALID_COLOR)
            elif validation_status == ValidationStatus.WARNING:
                # Draw with warning highlighting
                painter.fillRect(option.rect, self.WARNING_COLOR)

        # Restore painter state before calling the parent paint method
        painter.restore()

        # Draw the text content using the standard painter
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        """
        Create an editor for editing the item.

        Args:
            parent: Parent widget
            option: Style options for the item
            index: Model index of the item to edit

        Returns:
            Editor widget
        """
        # Use the standard editor creation
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        """
        Set the editor data.

        Args:
            editor: Editor widget
            index: Model index of the item being edited
        """
        # Use the standard editor data setting
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """
        Set the model data from the editor.

        Args:
            editor: Editor widget
            model: Data model
            index: Model index of the item being edited
        """
        # Use the standard model data setting
        super().setModelData(editor, model, index)
