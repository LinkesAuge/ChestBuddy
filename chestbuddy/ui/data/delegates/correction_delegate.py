"""
correction_delegate.py

Delegate responsible for visualizing correction status and handling correction actions.
"""

from PySide6.QtWidgets import QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, Qt, QRect, QSize
from PySide6.QtGui import QPainter, QIcon, QColor

from .validation_delegate import ValidationDelegate, ValidationStatus

# Assuming DataViewModel provides CorrectionInfoRole or similar
from ..models.data_view_model import DataViewModel


# Placeholder for actual correction suggestion structure
class CorrectionSuggestion:
    def __init__(self, original, corrected):
        self.original = original
        self.corrected = corrected


class CorrectionDelegate(ValidationDelegate):
    """
    Extends ValidationDelegate to provide visual feedback for correctable cells
    and potentially handle correction actions.

    Overrides the paint method to draw correction indicators (e.g., icons).
    May override createEditor or other methods to facilitate corrections.
    """

    # Define icons or visual elements for correction
    # Example using a resource path for the icon
    CORRECTION_INDICATOR_ICON = QIcon("icons:correction_available.svg")
    ICON_SIZE = 16  # Shared icon size

    def __init__(self, parent=None):
        """Initialize the CorrectionDelegate."""
        super().__init__(parent)
        # Add any correction-specific initializations here

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the cell, adding indicators for correction status.

        Args:
            painter: The QPainter to use for drawing.
            option: Style options for the item.
            index: Model index of the item being painted.
        """
        # First, let the ValidationDelegate paint the validation status
        super().paint(painter, option, index)

        # Retrieve correction info from the model
        # Use CorrectionSuggestionsRole which is defined in DataViewModel
        suggestions = index.data(DataViewModel.CorrectionSuggestionsRole)
        is_correctable = (
            index.data(DataViewModel.ValidationStateRole) == ValidationStatus.CORRECTABLE
        )

        # If the cell is marked as correctable, draw the indicator
        if is_correctable:
            self._paint_correction_indicator(painter, option)

    def _paint_correction_indicator(self, painter: QPainter, option: QStyleOptionViewItem):
        """
        Paint the correction indicator icon.

        Args:
            painter: The QPainter to use for drawing.
            option: Style options for the item.
        """
        icon = self.CORRECTION_INDICATOR_ICON
        if not icon.isNull():
            icon_margin = 2
            icon_rect = option.rect.adjusted(0, 0, 0, 0)
            icon_rect.setLeft(option.rect.right() - self.ICON_SIZE - icon_margin)
            icon_rect.setTop(option.rect.top() + (option.rect.height() - self.ICON_SIZE) // 2)
            icon_rect.setWidth(self.ICON_SIZE)
            icon_rect.setHeight(self.ICON_SIZE)
            icon.paint(painter, icon_rect, Qt.AlignRight | Qt.AlignVCenter)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Provides size hint, potentially adding space for icons."""
        # Get hint from ValidationDelegate (which considers its icons)
        hint = super().sizeHint(option, index)
        # Add space if correction icon might be drawn (only if not already added by validation)
        validation_status = index.data(DataViewModel.ValidationStateRole)
        is_correctable = validation_status == ValidationStatus.CORRECTABLE
        # If correctable AND no validation icon is shown, add space
        if is_correctable and validation_status not in [
            ValidationStatus.INVALID,
            ValidationStatus.WARNING,
            ValidationStatus.INFO,
        ]:
            hint.setWidth(hint.width() + self.ICON_SIZE + 4)
        # If correctable AND a validation icon is already shown, the space is likely sufficient
        # This logic assumes correction indicator might overlap or replace validation icon
        # If they need separate space, adjust logic here.
        return hint

    # TODO: Override editorEvent or add button handling to show suggestions
    # when the indicator area is clicked.
