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

from chestbuddy.core.enums.validation_enums import ValidationStatus

# Set up logger
logger = logging.getLogger(__name__)

# Log the available validation statuses for debugging
logger.debug(f"ValidationStatus enum loaded: {[status.name for status in ValidationStatus]}")


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
    INVALID_ROW_COLOR = QColor(255, 220, 220, 120)  # Light pink for invalid rows
    NOT_VALIDATED_COLOR = QColor(200, 200, 200, 40)  # Light gray for not validated
    CORRECTABLE_COLOR = QColor(255, 140, 0, 120)  # Distinct orange for correctable entries
    CORRECTABLE_BORDER_COLOR = QColor(180, 95, 6, 255)  # Darker orange border

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
        Custom paint method to apply validation status styling.

        Args:
            painter: The QPainter instance
            option: The style options for the item
            index: The model index of the item being painted
        """
        # Use default painting if index is invalid
        if not index.isValid():
            super().paint(painter, option, index)
            return

        # Get cell-specific invalid status (True if invalid, False otherwise)
        # This is stored in Qt.UserRole + 1 by DataView._highlight_invalid_rows
        is_cell_invalid = index.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(is_cell_invalid, bool):
            # self.logger.debug(f"Cell [{index.row()},{index.column()}] UserRole+1 data is not bool: {is_cell_invalid}")
            is_cell_invalid = False  # Default to not invalid if data is missing or not boolean

        # Get the validation status enum from model data if available
        # This is stored in Qt.UserRole + 2 by DataView._highlight_invalid_rows
        validation_status = index.data(Qt.ItemDataRole.UserRole + 2)

        # Check for specific validation statuses
        is_correctable = validation_status == ValidationStatus.CORRECTABLE
        is_invalid = validation_status == ValidationStatus.INVALID
        is_invalid_row = validation_status == ValidationStatus.INVALID_ROW

        # Get model and column name
        model = index.model()
        if model is None:
            super().paint(painter, option, index)
            return

        column_name = model.headerData(index.column(), Qt.Horizontal)
        is_validatable_column = column_name in self.VALIDATABLE_COLUMNS

        # Get row's overall validation status from the STATUS column
        row_status_text = "Unknown"
        status_col_index = -1
        for col in range(model.columnCount()):
            if model.headerData(col, Qt.Horizontal) == self.STATUS_COLUMN:
                status_col_index = col
                break

        if status_col_index != -1:
            status_index = model.index(index.row(), status_col_index)
            row_status_text = status_index.data(Qt.DisplayRole)
            if row_status_text is None:
                row_status_text = "Unknown"

        # Save painter state
        painter.save()

        # Store original options
        opt = QStyleOptionViewItem(option)
        opt.state &= ~QStyle.State_HasFocus  # Disable focus rectangle

        # Handle selection separately
        if option.state & QStyle.State_Selected:
            painter.restore()
            super().paint(painter, option, index)
            return

        # Determine background color based on cell and row status
        background_color = None
        border_color = None
        border_width = 1

        # Priority in determining cell appearance (highest to lowest):
        # 1. Specific cell status (CORRECTABLE or INVALID)
        # 2. Is this cell specifically invalid (from is_cell_invalid flag)
        # 3. Row status text (Invalid, Correctable, etc.)

        # First check specific validation status for this cell
        if is_validatable_column:
            if is_correctable:
                # Highest priority: Correctable cell
                background_color = self.CORRECTABLE_COLOR
                border_color = self.CORRECTABLE_BORDER_COLOR
                border_width = 2
                self.logger.debug(
                    f"Painting correctable cell [{index.row()},{index.column()}], col={column_name}, value={repr(index.data())}"
                )
            elif is_invalid or is_invalid_row:
                # Next priority: Specifically invalid cell
                background_color = self.INVALID_COLOR
                border_color = self.INVALID_BORDER_COLOR
                border_width = 2
                self.logger.debug(
                    f"Painting specifically invalid cell [{index.row()},{index.column()}], col={column_name}, value={repr(index.data())}"
                )
            elif is_cell_invalid:
                # Next priority: Cell marked as invalid but without specific status
                background_color = self.INVALID_COLOR
                border_color = self.INVALID_BORDER_COLOR
                border_width = 2

        # If no specific cell status, use row status text
        if background_color is None:
            if row_status_text == "Invalid":
                # Cell is in an invalid row
                background_color = self.INVALID_ROW_COLOR
            elif row_status_text == "Correctable":
                # Cell is in a correctable row
                background_color = self.CORRECTABLE_COLOR
            elif row_status_text == "Valid":
                # Cell is valid and in a valid row
                background_color = self.VALID_COLOR
            elif row_status_text == "Not validated":
                # Cell is in a row that hasn't been validated
                background_color = self.NOT_VALIDATED_COLOR

        # Apply background if determined
        if background_color:
            painter.fillRect(opt.rect, background_color)

        # Apply border if determined
        if border_color:
            pen = painter.pen()
            pen.setColor(border_color)
            pen.setWidth(border_width)
            painter.setPen(pen)
            border_rect = opt.rect.adjusted(
                0, 0, -border_width, -border_width
            )  # Adjust for pen width
            painter.drawRect(border_rect)

        # Restore painter before drawing text
        painter.restore()

        # Draw text using standard delegate paint
        painter.save()
        super().paint(painter, opt, index)
        painter.restore()

    def updateEditorGeometry(self, editor, option, index):
        """
        Update the geometry of the editor.

        Args:
            editor: The editor widget
            option: Style options for the item
            index: Model index of the item being edited
        """
        # Make the editor exactly fit the cell
        editor.setGeometry(option.rect)
