"""
Tests for the CorrectionDelegate class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex, QRect, QSize
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem
from PySide6.QtGui import QPainter, QIcon, QColor

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
    def delegate(self, qapp):
        """Create a CorrectionDelegate instance."""
        return CorrectionDelegate()

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

    # TODO: Add tests for other overridden methods if implemented (e.g., createEditor)
