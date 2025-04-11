"""
correction_delegate.py

Delegate responsible for visualizing correction status and handling correction actions.
"""

from PySide6.QtWidgets import QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, Qt, QRect
from PySide6.QtGui import QPainter, QIcon, QColor

from .validation_delegate import ValidationDelegate

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
    # For testing, we can use a colored rect instead of a real icon
    CORRECTION_INDICATOR_COLOR = QColor(Qt.GlobalColor.yellow)  # Example color
    INDICATOR_SIZE = 8  # Small square indicator

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
        # Use CorrectionStateRole which is defined in DataViewModel
        correction_state = index.data(DataViewModel.CorrectionStateRole)

        # If correction state exists (and indicates correctability), draw indicator
        # The exact check depends on what CorrectionStateRole returns
        # Assuming non-None means correctable for now
        if correction_state:
            self._paint_correction_indicator(painter, option)

    def _paint_correction_indicator(self, painter: QPainter, option: QStyleOptionViewItem):
        """
        Paint a simple indicator for correctable cells.

        Args:
            painter: The QPainter to use for drawing.
            option: Style options for the item.
        """
        painter.save()
        # Position indicator in top-right corner (adjust as needed)
        indicator_rect = QRect(
            option.rect.right() - self.INDICATOR_SIZE - 2,
            option.rect.top() + 2,
            self.INDICATOR_SIZE,
            self.INDICATOR_SIZE,
        )
        painter.fillRect(indicator_rect, self.CORRECTION_INDICATOR_COLOR)
        painter.restore()

    # TODO: Potentially override createEditor, setEditorData, setModelData
    # to integrate correction suggestions or actions directly into editing.
