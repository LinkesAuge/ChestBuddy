"""
correction_delegate.py

Delegate responsible for visualizing correction status and handling correction actions.
"""

from PySide6.QtWidgets import QStyleOptionViewItem, QMenu, QToolTip
from functools import partial

# Import QAbstractItemView
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtCore import QModelIndex, Qt, QRect, QSize, QEvent, QObject, QPoint, Signal, Slot
from PySide6.QtGui import QPainter, QIcon, QColor, QMouseEvent, QHelpEvent
from PySide6.QtCore import QAbstractItemModel

# Use CellState from core, ValidationDelegate should also use it
from chestbuddy.core.table_state_manager import CellState
from .validation_delegate import ValidationDelegate  # ValidationDelegate should import CellState

# Assuming DataViewModel provides CorrectionInfoRole or similar
from ..models.data_view_model import DataViewModel


# Placeholder for actual correction suggestion structure
# Ensure this matches the structure provided by CorrectionAdapter/Service
class CorrectionSuggestion:
    def __init__(self, original, corrected):
        self.original_value = original  # Match the name used in helpEvent
        self.corrected_value = corrected

    def __str__(self):  # For display in menu
        # Provide a more descriptive string if possible
        return f'Correct to: "{self.corrected_value}"'


class CorrectionDelegate(ValidationDelegate):
    """
    Extends ValidationDelegate to provide visual feedback for correctable cells
    and handle correction actions via a context menu on the indicator.

    Overrides the paint method to draw correction indicators (e.g., icons).
    Overrides editorEvent to show a correction menu when the indicator is clicked.

    Signals:
        correction_selected (QModelIndex, CorrectionSuggestion): Emitted when the user
            selects a correction suggestion from the menu.
    """

    # Define the new signal
    correction_selected = Signal(QModelIndex, object)  # Use object type for suggestion

    # Define icons or visual elements for correction
    CORRECTION_INDICATOR_ICON = QIcon("icons:correction_available.svg")  # Ensure this icon exists
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
        suggestions = index.data(
            DataViewModel.CorrectionSuggestionsRole
        )  # Needed for logic, not drawing
        is_correctable = index.data(DataViewModel.ValidationStateRole) == CellState.CORRECTABLE

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
            # Calculate indicator rect based on option.rect
            indicator_rect = self._get_indicator_rect(option.rect)
            icon.paint(painter, indicator_rect, Qt.AlignRight | Qt.AlignVCenter)

    # Helper method to calculate the indicator rect
    def _get_indicator_rect(self, cell_rect: QRect) -> QRect:
        icon_margin = 2
        return QRect(
            cell_rect.right() - self.ICON_SIZE - icon_margin,
            cell_rect.top() + (cell_rect.height() - self.ICON_SIZE) // 2,
            self.ICON_SIZE,
            self.ICON_SIZE,
        )

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Provides size hint, potentially adding space for icons."""
        # Get hint from ValidationDelegate ONCE
        hint = super().sizeHint(option, index)
        base_width = hint.width()  # Store base width

        # Add space if correction icon might be drawn (only if not already added by validation)
        validation_status = index.data(DataViewModel.ValidationStateRole)
        is_correctable = validation_status == CellState.CORRECTABLE
        # Check if validation delegate already added space
        has_validation_icon = validation_status in [
            CellState.INVALID,
            CellState.WARNING,
            # INFO does not exist
        ]

        if is_correctable and not has_validation_icon:
            # Add space only if the current hint width is not already larger than the base
            if hint.width() <= base_width:
                hint.setWidth(base_width + self.ICON_SIZE + 4)
            # If hint is already wider (e.g., due to text), just ensure enough space for icon
            else:
                hint.setWidth(max(hint.width(), base_width + self.ICON_SIZE + 4))

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
        Shows the correction menu if the indicator is left-clicked.
        """
        if not index.isValid():
            return False

        # Check if the cell is correctable
        is_correctable = index.data(DataViewModel.ValidationStateRole) == CellState.CORRECTABLE

        # Check for left mouse button press
        if event.type() == QEvent.Type.MouseButtonPress and is_correctable:
            # Use QEvent.Type.MouseButtonPress check first for type safety
            if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                # Calculate indicator rect
                indicator_rect = self._get_indicator_rect(option.rect)

                # Check if click was inside the indicator
                if indicator_rect.contains(event.pos()):
                    # Get the view associated with the option to map position correctly
                    view = (
                        self.parent()
                        if isinstance(self.parent(), QAbstractItemView)
                        else option.widget
                    )

                    if view and hasattr(view, "viewport"):
                        global_pos = view.viewport().mapToGlobal(event.pos())
                        self._show_correction_menu(model, index, global_pos)
                        return True  # Event handled, stop processing
                    else:
                        # Fallback using event global pos if view is not available
                        self._show_correction_menu(model, index, event.globalPos())
                        print(
                            "Warning: Could not get view to map position, using globalPos."
                        )  # Debug
                        return True  # Event handled, stop processing

        # IMPORTANT: If the click wasn't handled above (e.g., not on indicator),
        # pass the event to the base class implementation.
        # The previous TypeError likely occurred because we passed a QMouseEvent
        # when the signature expects a generic QEvent. We should pass the original event.
        return super().editorEvent(event, model, option, index)

    def _show_correction_menu(
        self, model: QAbstractItemModel, index: QModelIndex, global_pos: QPoint
    ):
        """Shows a context menu with correction suggestions."""
        suggestions = index.data(DataViewModel.CorrectionSuggestionsRole)

        if not suggestions:
            print(f"No suggestions found for index {index.row()},{index.column()}")  # Debug
            return

        menu = QMenu()
        for suggestion in suggestions:
            action_text = str(suggestion)
            if hasattr(suggestion, "corrected_value"):
                action_text = f'Apply: "{suggestion.corrected_value}"'

            action = menu.addAction(action_text)
            # Connect using functools.partial to bind the current index and suggestion
            action.triggered.connect(partial(self.correction_selected.emit, index, suggestion))

        if menu.isEmpty():
            print("Menu is empty, not showing.")  # Debug
            return

        menu.exec(global_pos)

    def helpEvent(
        self,
        event: QHelpEvent,
        view,  # QAbstractItemView
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        """Handles tooltip events to show detailed correction suggestions."""
        if event.type() == QHelpEvent.Type.ToolTip and index.isValid():
            suggestions = index.data(DataViewModel.CorrectionSuggestionsRole)
            if suggestions:
                # Ensure suggestions have 'corrected_value' or adapt as needed
                # Corrected f-string formatting
                suggestions_list = []
                for s in suggestions:
                    suggestion_str = getattr(s, "corrected_value", str(s))
                    suggestions_list.append(f"- {suggestion_str}")
                suggestions_text = "Suggestions:\n" + "\n".join(suggestions_list)

                QToolTip.showText(event.globalPos(), suggestions_text, view)
                return True  # Event handled

        # Call the base class (ValidationDelegate) helpEvent for its tooltip logic
        return super().helpEvent(event, view, option, index)
