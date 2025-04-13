"""
Tests for the CorrectionDelegate class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex, QRect, QSize, QEvent, QPoint, Signal
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem
from PySide6.QtGui import QPainter, QIcon, QColor, QMouseEvent
from PySide6.QtTest import QSignalSpy

from chestbuddy.ui.data.delegates.correction_delegate import (
    CorrectionDelegate,
    CorrectionSuggestion,
)
from chestbuddy.ui.data.delegates.validation_delegate import ValidationDelegate
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.core.enums.validation_enums import ValidationStatus
# Import necessary models or roles if needed later
# from chestbuddy.ui.data.models.data_view_model import DataViewModel

# Fixtures like qapp are expected from conftest.py


class TestCorrectionDelegate:
    """Tests for the CorrectionDelegate class."""

    @pytest.fixture
    def delegate_class(self):
        """Return the CorrectionDelegate class for modification if needed."""
        return CorrectionDelegate

    @pytest.fixture
    def delegate(self, delegate_class, qapp):
        """Create a CorrectionDelegate instance."""
        # Ensure the signal exists on the class before instantiation for QSignalSpy
        if not hasattr(delegate_class, "apply_first_correction_requested"):
            delegate_class.apply_first_correction_requested = Signal(QModelIndex)
        return delegate_class()

    @pytest.fixture
    def mock_painter(self, mocker):
        """Fixture for a mocked QPainter."""
        return mocker.MagicMock(spec=QPainter)

    @pytest.fixture
    def style_option(self):
        """Fixture for a basic QStyleOptionViewItem."""
        option = QStyleOptionViewItem()
        option.rect = QRect(0, 0, 100, 30)
        return option

    @pytest.fixture
    def mock_index(self, mocker):
        """Fixture for a mocked QModelIndex."""
        index = mocker.MagicMock(spec=QModelIndex)
        index.isValid.return_value = True
        # Default data for roles
        index.data.side_effect = lambda role: {
            DataViewModel.ValidationStateRole: ValidationStatus.VALID,
            DataViewModel.CorrectionSuggestionsRole: None,
            Qt.DisplayRole: "Test Value",
        }.get(role, None)
        return index

    def test_initialization(self, delegate):
        """Test that the CorrectionDelegate initializes correctly."""
        assert delegate is not None

    def test_paint_correctable_cell(self, delegate, mock_painter, style_option, mock_index, mocker):
        """Test painting a cell marked as CORRECTABLE."""
        # Configure index for CORRECTABLE state
        mock_index.data.side_effect = (
            lambda role: ValidationStatus.CORRECTABLE
            if role == DataViewModel.ValidationStateRole
            else None
        )

        # Mock the icon paint method to verify it's called
        mock_icon_paint = mocker.patch.object(QIcon, "paint")

        delegate.paint(mock_painter, style_option, mock_index)

        # Verify the correction indicator icon paint was called
        mock_icon_paint.assert_called()
        # Check if the base class (ValidationDelegate) paint was called (important!)
        # This requires careful mocking or checking painter calls if super().paint is complex
        # For simplicity, assume base paint is called correctly if no error

    def test_paint_non_correctable_cell(
        self, delegate, mock_painter, style_option, mock_index, mocker
    ):
        """Test painting a cell not marked as CORRECTABLE."""
        # Configure index for VALID state (or INVALID, etc.)
        mock_index.data.side_effect = (
            lambda role: ValidationStatus.VALID
            if role == DataViewModel.ValidationStateRole
            else None
        )

        mock_icon_paint = mocker.patch.object(QIcon, "paint")

        delegate.paint(mock_painter, style_option, mock_index)

        # Verify the correction indicator icon paint was *not* called
        # Note: This assumes ValidationDelegate doesn't paint the *same* icon.
        # If icons can overlap, this needs adjustment.
        # Let's refine: Check if CorrectionDelegate._paint_correction_indicator was called.
        spy_paint_indicator = mocker.spy(delegate, "_paint_correction_indicator")
        delegate.paint(mock_painter, style_option, mock_index)
        spy_paint_indicator.assert_not_called()

    def test_sizeHint_correctable_no_validation_icon(
        self, delegate, style_option, mock_index, mocker
    ):
        """Test sizeHint adds space for correctable cells without other icons."""
        mock_index.data.side_effect = (
            lambda role: ValidationStatus.CORRECTABLE
            if role == DataViewModel.ValidationStateRole
            else None
        )
        # Mock super().sizeHint
        base_hint = QSize(80, 30)
        mocker.patch.object(ValidationDelegate, "sizeHint", return_value=base_hint)

        hint = delegate.sizeHint(style_option, mock_index)

        # Expect width increased by icon size + margin
        expected_width = base_hint.width() + delegate.ICON_SIZE + 4
        assert hint.width() == expected_width
        assert hint.height() == base_hint.height()

    def test_sizeHint_correctable_with_validation_icon(
        self, delegate, style_option, mock_index, mocker
    ):
        """Test sizeHint does NOT add extra space if validation icon already present."""
        # Simulate INVALID state (which ValidationDelegate adds space for)
        mock_index.data.side_effect = (
            lambda role: ValidationStatus.INVALID
            if role == DataViewModel.ValidationStateRole
            else None
        )
        # Mock super().sizeHint to return a size already accounting for the validation icon
        validation_icon_width = ValidationDelegate.ICON_SIZE + 4
        base_hint_with_val_icon = QSize(80 + validation_icon_width, 30)
        mocker.patch.object(ValidationDelegate, "sizeHint", return_value=base_hint_with_val_icon)

        # Get hint for an INVALID cell (CorrectionDelegate inherits from ValidationDelegate)
        hint = delegate.sizeHint(style_option, mock_index)

        # Expect width to be the same as returned by super (ValidationDelegate)
        assert hint.width() == base_hint_with_val_icon.width()
        assert hint.height() == base_hint_with_val_icon.height()

    def test_sizeHint_valid_cell(self, delegate, style_option, mock_index, mocker):
        """Test sizeHint for a normal VALID cell."""
        mock_index.data.side_effect = (
            lambda role: ValidationStatus.VALID
            if role == DataViewModel.ValidationStateRole
            else None
        )
        base_hint = QSize(80, 30)
        mocker.patch.object(ValidationDelegate, "sizeHint", return_value=base_hint)

        hint = delegate.sizeHint(style_option, mock_index)

        # Expect base size hint
        assert hint == base_hint

    def test_indicator_click_emits_signal(self, delegate, style_option, mock_index, qtbot, mocker):
        """Test clicking the correction indicator emits the correct signal."""
        # Configure index for CORRECTABLE state
        mock_index.data.side_effect = (
            lambda role: ValidationStatus.CORRECTABLE
            if role == DataViewModel.ValidationStateRole
            else None
        )

        # Spy on the *instance's* signal
        spy = QSignalSpy(delegate.apply_first_correction_requested)
        assert spy.isValid()

        # Calculate the indicator rect (assuming a helper method or calculation logic)
        # Replicate potential logic from _paint_correction_indicator or a helper
        indicator_rect = QRect(
            style_option.rect.right() - delegate.ICON_SIZE - 2,  # 2px margin
            style_option.rect.top() + (style_option.rect.height() - delegate.ICON_SIZE) // 2,
            delegate.ICON_SIZE,
            delegate.ICON_SIZE,
        )
        click_pos = indicator_rect.center()

        # Simulate the mouse click event that would trigger editorEvent
        # We need to simulate the view calling editorEvent
        # Mock the view to control the event
        mock_view = mocker.MagicMock()
        # Simulate a MouseButtonPress event within the indicator rect
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            click_pos,  # Local position within the cell
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Call editorEvent - the delegate method that should handle this
        # Assuming editorEvent is overridden to handle this click
        # The base QStyledItemDelegate.editorEvent might return False if no editor is created
        # We expect our override to handle the click and return True, or emit the signal
        # and potentially return False if no editor is meant to be opened.

        # Mock the parent view's viewport for event processing if needed
        mock_view.viewport.return_value = mocker.MagicMock()

        # Call editorEvent
        # Note: We might need to mock the model return value for Qt.EditRole if editorEvent checks it
        delegate.editorEvent(event, mock_index.model(), style_option, mock_index)

        # Assert the signal was emitted once
        assert len(spy) == 1, f"Signal emitted {len(spy)} times, expected 1"

        # Assert the signal was emitted with the correct index
        assert len(spy[0]) == 1, "Signal emitted with incorrect number of arguments"
        assert spy[0][0] == mock_index, "Signal emitted with incorrect QModelIndex"

    # TODO: Add tests for other overridden methods if implemented (e.g., createEditor)
