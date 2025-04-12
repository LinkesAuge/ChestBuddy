"""
correction_delegate.py

Delegate responsible for visualizing correction status and handling correction actions.
"""

from PySide6.QtWidgets import QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, Qt, QRect, QSize, QEvent, QObject, QPoint
from PySide6.QtGui import QPainter, QIcon, QColor, QMouseEvent
from PySide6.QtCore import QAbstractItemModel
from PySide6.QtWidgets import QMenu

# Use CellState from core, ValidationDelegate should also use it
from chestbuddy.core.table_state_manager import CellState
from .validation_delegate import ValidationDelegate  # ValidationDelegate should import CellState

# Assuming DataViewModel provides CorrectionInfoRole or similar
from ..models.data_view_model import DataViewModel


# Placeholder for actual correction suggestion structure
class CorrectionSuggestion:
    def __init__(self, original, corrected):
        self.original = original
        self.corrected = corrected

    def __str__(self):  # For display in menu
        return f'" {self.corrected}"'


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
            index.data(DataViewModel.ValidationStateRole) == CellState.CORRECTABLE  # Use CellState
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
        is_correctable = validation_status == CellState.CORRECTABLE  # Use CellState
        # If correctable AND no validation icon is shown, add space
        if is_correctable and validation_status not in [
            CellState.INVALID,  # Use CellState
            CellState.WARNING,  # Use CellState
            CellState.INFO,  # Use CellState
        ]:
            hint.setWidth(hint.width() + self.ICON_SIZE + 4)
        # If correctable AND a validation icon is already shown, the space is likely sufficient
        # This logic assumes correction indicator might overlap or replace validation icon
        # If they need separate space, adjust logic here.
        return hint

    def editorEvent(
        self,
        event: QEvent,
        model: QAbstractItemModel,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        """
        Handle events within the delegate, specifically mouse clicks on the indicator.
        """
        if not index.isValid():
            return False

        # Check if the cell is correctable
        is_correctable = index.data(DataViewModel.ValidationStateRole) == CellState.CORRECTABLE
        if not is_correctable:
            return super().editorEvent(event, model, option, index)

        # Check for left mouse button release
        if event.type() == QEvent.Type.MouseButtonRelease:
            mouse_event = QMouseEvent(event)  # Cast to QMouseEvent
            if mouse_event.button() == Qt.MouseButton.LeftButton:
                # Calculate indicator rect
                icon_margin = 2
                indicator_rect = QRect(
                    option.rect.right() - self.ICON_SIZE - icon_margin,
                    option.rect.top() + (option.rect.height() - self.ICON_SIZE) // 2,
                    self.ICON_SIZE,
                    self.ICON_SIZE,
                )

                # Check if click was inside the indicator
                if indicator_rect.contains(mouse_event.pos()):
                    print(
                        f"Correction indicator clicked for index {index.row()},{index.column()}"
                    )  # Debug
                    self._show_correction_menu(model, index, mouse_event.globalPos())
                    return True  # Event handled

        return super().editorEvent(event, model, option, index)

    def _show_correction_menu(
        self, model: QAbstractItemModel, index: QModelIndex, global_pos: QPoint
    ):
        """Shows a context menu with correction suggestions."""
        suggestions = index.data(DataViewModel.CorrectionSuggestionsRole)

        if not suggestions:
            print("No suggestions found to show menu.")  # Debug
            return

        menu = QMenu()
        for suggestion in suggestions:
            action = menu.addAction(str(suggestion))  # Use __str__ for display
            # Connect action to a placeholder handler
            action.triggered.connect(
                lambda checked=False,
                idx=index,
                sugg=suggestion: self._apply_correction_placeholder(idx, sugg)
            )

        if menu.isEmpty():
            print("Correction menu is empty after processing suggestions.")  # Debug
            return

        menu.exec(global_pos)

    def _apply_correction_placeholder(self, index: QModelIndex, suggestion: CorrectionSuggestion):
        """Placeholder function to be called when a correction suggestion is selected."""
        # Simplified print statement for debugging linter
        print(f"Applying correction placeholder for {index.row()}, {index.column()}")
        # In a real implementation, this would likely involve:
        # 1. Getting the CorrectionService instance
        # 2. Calling correction_service.apply_correction(index.row(), index.column(), suggestion)

    # TODO: Override editorEvent or add button handling to show suggestions
    # when the indicator area is clicked.
