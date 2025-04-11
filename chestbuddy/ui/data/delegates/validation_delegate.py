"""
validation_delegate.py

Delegate responsible for visualizing validation status in cells.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QPainter, QColor, QIcon

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
    # STATUS_ICONS = {
    #     ValidationStatus.INVALID: QIcon(":/icons/invalid.png"),
    #     ValidationStatus.CORRECTABLE: QIcon(":/icons/correctable.png"),
    #     ValidationStatus.WARNING: QIcon(":/icons/warning.png"),
    #     ValidationStatus.INFO: QIcon(":/icons/info.png"),
    # }

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

        # TODO: Draw status icon if status is not VALID
        # if validation_status and validation_status != ValidationStatus.VALID:
        #     icon = self.STATUS_ICONS.get(validation_status)
        #     if icon:
        #         icon_rect = QRect(option.rect.right() - 18, option.rect.top() + (option.rect.height() - 16) // 2, 16, 16)
        #         icon.paint(painter, icon_rect)
