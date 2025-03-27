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
    VALID_COLOR = QColor(0, 255, 0, 40)  # Light green transparent
    WARNING_COLOR = QColor(255, 240, 0, 80)  # Light yellow
    INVALID_COLOR = QColor(180, 0, 0, 255)  # Darker red, fully opaque
    INVALID_BORDER_COLOR = QColor(0, 0, 0, 255)  # Black border
    INVALID_ROW_COLOR = QColor(255, 230, 230, 100)  # Light pink with low opacity
    NOT_VALIDATED_COLOR = QColor(200, 200, 200, 40)  # Light gray for not validated

    # Column name constants
    STATUS_COLUMN = "STATUS"
    PLAYER_COLUMN = "PLAYER"
    SOURCE_COLUMN = "SOURCE"
    CHEST_COLUMN = "CHEST"

    # List of columns that can be validated
    VALIDATABLE_COLUMNS = [PLAYER_COLUMN, SOURCE_COLUMN, CHEST_COLUMN]

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

        # Check if this is a validatable column
        is_validatable_column = column_name in self.VALIDATABLE_COLUMNS

        # Get cell-specific validation status from model data (Qt.UserRole + 1)
        validation_status = index.data(Qt.ItemDataRole.UserRole + 1)

        # More verbose logging to diagnose the issue (only when debug logging is enabled)
        if logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                f"Cell [{index.row()},{index.column()}]: column={column_name}, "
                f"validation_status={validation_status}, "
                f"is_validatable={is_validatable_column}"
            )

        # If this is the status column, paint based on the text value
        if is_status_column:
            # Get the display text
            text = index.data(Qt.DisplayRole)

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
            # Apply styling based on validation status
            if validation_status == ValidationStatus.INVALID:
                # This is a cell with a specific validation error (highlight prominently)
                self.logger.debug(f"Painting cell [{index.row()},{index.column()}] as INVALID")

                # Draw with dark red background
                painter.fillRect(option.rect, self.INVALID_COLOR)

                # Draw a simple border
                pen = painter.pen()
                pen.setColor(self.INVALID_BORDER_COLOR)
                pen.setWidth(1)  # Thinner border
                painter.setPen(pen)

                # Draw the border
                painter.drawRect(option.rect)
            elif validation_status == ValidationStatus.INVALID_ROW:
                # This is just a cell in an invalid row (but not the specific invalid cell)
                # Use a subtle background to indicate this is in an invalid row
                painter.fillRect(option.rect, self.INVALID_ROW_COLOR)
            elif validation_status == ValidationStatus.WARNING:
                # Draw with warning highlighting
                painter.fillRect(option.rect, self.WARNING_COLOR)
            elif validation_status == ValidationStatus.VALID:
                # Use light green for valid status
                painter.fillRect(option.rect, self.VALID_COLOR)
            elif validation_status == ValidationStatus.NOT_VALIDATED:
                # Light gray for not validated
                painter.fillRect(option.rect, self.NOT_VALIDATED_COLOR)

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
