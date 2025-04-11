"""
Tests for the ValidationDelegate class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QApplication, QWidget, QStyleOptionViewItem
from PySide6.QtGui import QPainter, QColor

from chestbuddy.ui.data.delegates.validation_delegate import ValidationDelegate, ValidationStatus
from chestbuddy.ui.data.models.data_view_model import DataViewModel

# Fixtures like qapp are expected from conftest.py


class TestValidationDelegate:
    """Tests for the ValidationDelegate class."""

    @pytest.fixture
    def delegate(self, qapp):
        """Create a ValidationDelegate instance."""
        return ValidationDelegate()

    def test_initialization(self, delegate):
        """Test that the ValidationDelegate initializes correctly."""
        assert delegate is not None
        # Check if STATUS_COLORS are defined
        assert hasattr(delegate, "STATUS_COLORS")
        assert ValidationStatus.INVALID in delegate.STATUS_COLORS

    def test_paint_valid_cell(self, delegate, mocker):
        """Test painting a cell with VALID status."""
        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        # Mock index.data to return VALID status for ValidationStateRole
        def mock_data(role):
            if role == DataViewModel.ValidationStateRole:
                return ValidationStatus.VALID
            return "Display Data"  # Default for other roles

        mock_index.data = mock_data

        # Mock superclass paint
        mock_super_paint = mocker.patch(
            "chestbuddy.ui.data.delegates.cell_delegate.CellDelegate.paint"
        )

        delegate.paint(mock_painter, mock_option, mock_index)

        # Assert fillRect was NOT called (no background change)
        mock_painter.fillRect.assert_not_called()
        # Assert super().paint was called
        mock_super_paint.assert_called_once_with(mock_painter, mock_option, mock_index)

    @pytest.mark.parametrize(
        "status, expected_color_hex",
        [
            (ValidationStatus.INVALID, "#ffb6b6"),
            (ValidationStatus.CORRECTABLE, "#fff3b6"),
            (ValidationStatus.WARNING, "#ffe4b6"),
            (ValidationStatus.INFO, "#b6e4ff"),
        ],
    )
    def test_paint_other_status_cells(self, delegate, mocker, status, expected_color_hex):
        """Test painting cells with various non-VALID statuses."""
        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_option.rect = mocker.MagicMock()  # Need a mock rect for fillRect
        mock_index = mocker.MagicMock(spec=QModelIndex)

        # Mock index.data to return the specified status
        def mock_data(role):
            if role == DataViewModel.ValidationStateRole:
                return status
            return "Display Data"

        mock_index.data = mock_data

        # Mock superclass paint
        mock_super_paint = mocker.patch(
            "chestbuddy.ui.data.delegates.cell_delegate.CellDelegate.paint"
        )

        delegate.paint(mock_painter, mock_option, mock_index)

        # Assert fillRect was called with the correct color
        mock_painter.fillRect.assert_called_once()
        args, kwargs = mock_painter.fillRect.call_args
        assert args[0] == mock_option.rect
        assert isinstance(args[1], QColor)
        assert args[1].name() == expected_color_hex

        # Assert super().paint was called
        mock_super_paint.assert_called_once_with(mock_painter, mock_option, mock_index)

    def test_paint_no_status(self, delegate, mocker):
        """Test painting a cell where model returns None for status."""
        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        # Mock index.data to return None for ValidationStateRole
        def mock_data(role):
            if role == DataViewModel.ValidationStateRole:
                return None
            return "Display Data"

        mock_index.data = mock_data

        # Mock superclass paint
        mock_super_paint = mocker.patch(
            "chestbuddy.ui.data.delegates.cell_delegate.CellDelegate.paint"
        )

        delegate.paint(mock_painter, mock_option, mock_index)

        # Assert fillRect was NOT called
        mock_painter.fillRect.assert_not_called()
        # Assert super().paint was called
        mock_super_paint.assert_called_once_with(mock_painter, mock_option, mock_index)

    # TODO: Add tests for icon painting when implemented
