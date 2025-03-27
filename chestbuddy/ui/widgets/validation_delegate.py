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
    INVALID_COLOR = QColor(170, 0, 0, 255)  # Deep crimson, fully opaque
    INVALID_BORDER_COLOR = QColor(0, 0, 0, 255)  # Black border
    INVALID_ROW_COLOR = QColor(255, 230, 230, 120)  # Light pink with low opacity
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
            value = index.data(Qt.DisplayRole)
            # Use repr() to safely handle potentially problematic Unicode characters
            safe_value = repr(value) if value is not None else "None"
            self.logger.debug(
                f"Cell [{index.row()},{index.column()}]: column={column_name}, "
                f"validation_status={validation_status}, "
                f"is_validatable={is_validatable_column}, "
                f"value={safe_value}"
            )

        # Copy the style option for modifications
        opt = QStyleOptionViewItem(option)

        # Draw any selections, focus, or other basic styling using the parent style
        # This ensures selections still work properly
        opt.state &= ~QStyle.State_Selected  # Clear the selection state to draw our own background

        # Special handling for specifically invalid cells in validatable columns
        if validation_status == ValidationStatus.INVALID and is_validatable_column:
            # This is a specifically invalid cell (in a validatable column)
            value = index.data(Qt.DisplayRole)
            # Use repr() for safe Unicode handling
            safe_value = repr(value) if value is not None else "None"
            self.logger.debug(
                f"Painting invalid cell [{index.row()},{index.column()}], col={column_name}, value={safe_value}"
            )

            # Draw with dark red background - fill completely
            painter.fillRect(opt.rect, self.INVALID_COLOR)

            # Draw a more visible border to make invalid cells stand out
            pen = painter.pen()
            pen.setColor(self.INVALID_BORDER_COLOR)
            pen.setWidth(2)  # Thicker border
            painter.setPen(pen)

            # Draw the border - inset slightly to ensure it's visible
            border_rect = opt.rect.adjusted(0, 0, -1, -1)
            painter.drawRect(border_rect)

            # Add a small indicator in the corner of invalid cells to make them more visible
            indicator_size = 6
            indicator_rect = QRect(
                opt.rect.right() - indicator_size - 2,
                opt.rect.top() + 2,
                indicator_size,
                indicator_size,
            )
            painter.fillRect(indicator_rect, self.INVALID_BORDER_COLOR)

        # If this is the status column, paint based on the text value
        elif is_status_column:
            # Get the display text
            text = index.data(Qt.DisplayRole)

            if text == "Valid":
                # Use light green for valid status
                painter.fillRect(opt.rect, self.VALID_COLOR)
            elif text == "Invalid":
                # Paint with error background
                painter.fillRect(opt.rect, self.INVALID_COLOR)
            elif text == "Not validated":
                # Light gray for not validated
                painter.fillRect(opt.rect, self.NOT_VALIDATED_COLOR)
        else:
            # Apply styling based on validation status (for non-invalid validatable columns)
            if validation_status == ValidationStatus.INVALID:
                # Handle non-validatable columns
                self.logger.debug(
                    f"Non-validatable column {column_name} has INVALID status, treating as INVALID_ROW"
                )
                painter.fillRect(opt.rect, self.INVALID_ROW_COLOR)
            elif validation_status == ValidationStatus.INVALID_ROW:
                # This is just a cell in an invalid row (but not the specific invalid cell)
                # Use a subtle background to indicate this is in an invalid row
                painter.fillRect(opt.rect, self.INVALID_ROW_COLOR)
            elif validation_status == ValidationStatus.WARNING:
                # Draw with warning highlighting
                painter.fillRect(opt.rect, self.WARNING_COLOR)
            elif validation_status == ValidationStatus.VALID:
                # Use light green for valid status
                painter.fillRect(opt.rect, self.VALID_COLOR)
            elif validation_status == ValidationStatus.NOT_VALIDATED:
                # Light gray for not validated
                painter.fillRect(opt.rect, self.NOT_VALIDATED_COLOR)

        # Restore painter state before drawing the text
        painter.restore()

        # Draw the text content using the standard delegate's paint method
        # This needs to be outside the saved painter state to ensure it's drawn on top
        super().paint(painter, opt, index)

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
