"""
validation_delegate.py

Delegate responsible for visualizing validation status in cells.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QPainter, QColor, QIcon, QHelpEvent
from PySide6.QtWidgets import (
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
    QApplication,
)

from .cell_delegate import CellDelegate

# Assuming DataViewModel provides the ValidationStateRole
from ..models.data_view_model import DataViewModel


# Placeholder for actual validation status enum/constants
# from chestbuddy.core.enums import ValidationStatus
class ValidationStatus:
    VALID = "VALID"
    INVALID = "INVALID"
    CORRECTABLE = "CORRECTABLE"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationDelegate(CellDelegate):
    """
    Extends CellDelegate to provide visual feedback for validation status.

    Overrides the paint method to draw background colors and status icons
    based on the data retrieved from the model's ValidationStateRole.
    """

    # Define colors and icons for different states (customize as needed)
    STATUS_COLORS = {
        ValidationStatus.INVALID: QColor("#ffb6b6"),  # Light Red
        ValidationStatus.CORRECTABLE: QColor("#fff3b6"),  # Light Yellow
        ValidationStatus.WARNING: QColor("#ffe4b6"),  # Light Orange
        ValidationStatus.INFO: QColor("#b6e4ff"),  # Light Blue
    }
    STATUS_ICONS = {
        ValidationStatus.INVALID: QIcon("icons:error.svg"),  # Example using resource path
        # ValidationStatus.CORRECTABLE: QIcon("icons:correction_available.svg"), # CorrectionDelegate handles this
        ValidationStatus.WARNING: QIcon("icons:warning.svg"),
        ValidationStatus.INFO: QIcon("icons:info.svg"),
    }

    ICON_SIZE = 16  # Size for the status icons

    def __init__(self, parent=None):
        """
        Initialize the ValidationDelegate.

        Args:
            parent (QObject, optional): Parent object. Defaults to None.
        """
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Renders the cell with validation status visualization.

        Args:
            painter (QPainter): The painter to use.
            option (QStyleOptionViewItem): The style options.
            index (QModelIndex): The model index.
        """
        # Get validation status from the model
        validation_status = index.data(DataViewModel.ValidationStateRole)

        # Apply background color if status is not VALID
        if validation_status and validation_status != ValidationStatus.VALID:
            color = self.STATUS_COLORS.get(validation_status)
            if color:
                painter.fillRect(option.rect, color)

        # Call the base class paint method to draw text and standard elements
        super().paint(painter, option, index)

        # Draw status icon if status is not VALID or CORRECTABLE
        if validation_status and validation_status not in [
            ValidationStatus.VALID,
            ValidationStatus.CORRECTABLE,
        ]:
            icon = self.STATUS_ICONS.get(validation_status)
            if icon:
                # Calculate icon position (e.g., top-right corner)
                icon_margin = 2
                icon_rect = option.rect.adjusted(0, 0, 0, 0)  # Copy rect
                icon_rect.setLeft(option.rect.right() - self.ICON_SIZE - icon_margin)
                icon_rect.setTop(option.rect.top() + (option.rect.height() - self.ICON_SIZE) // 2)
                icon_rect.setWidth(self.ICON_SIZE)
                icon_rect.setHeight(self.ICON_SIZE)
                # Draw icon respecting the application style
                icon.paint(painter, icon_rect, Qt.AlignRight | Qt.AlignVCenter)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Provides size hint, potentially adding space for icons."""
        hint = super().sizeHint(option, index)
        # Add space if an icon might be drawn
        validation_status = index.data(DataViewModel.ValidationStateRole)
        if validation_status and validation_status != ValidationStatus.VALID:
            # Add width for icon and margin
            hint.setWidth(hint.width() + self.ICON_SIZE + 4)
        return hint

    # Override helpEvent to show detailed tooltips
    def helpEvent(self, event: QHelpEvent, view, option: QStyleOptionViewItem, index: QModelIndex):
        """Handles tooltip events to show detailed error messages."""
        if event.type() == QHelpEvent.ToolTip and index.isValid():
            error_details = index.data(DataViewModel.ErrorDetailsRole)
            if error_details:
                QToolTip.showText(event.globalPos(), str(error_details), view)
                return True  # Event handled
            else:
                # Fallback to default tooltip if no specific details
                default_tooltip = index.data(Qt.ToolTipRole)
                if default_tooltip:
                    QToolTip.showText(event.globalPos(), str(default_tooltip), view)
                    return True

        return super().helpEvent(event, view, option, index)
