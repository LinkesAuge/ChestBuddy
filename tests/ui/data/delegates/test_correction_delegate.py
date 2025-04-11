"""
Tests for the CorrectionDelegate class.
"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem
from PySide6.QtGui import QPainter

from chestbuddy.ui.data.delegates.correction_delegate import (
    CorrectionDelegate,
    CorrectionSuggestion,
)
from chestbuddy.ui.data.delegates.validation_delegate import ValidationDelegate
from chestbuddy.ui.data.models.data_view_model import DataViewModel
# Import necessary models or roles if needed later
# from chestbuddy.ui.data.models.data_view_model import DataViewModel

# Fixtures like qapp are expected from conftest.py


class TestCorrectionDelegate:
    """Tests for the CorrectionDelegate class."""

    @pytest.fixture
    def delegate(self, qapp):
        """Create a CorrectionDelegate instance."""
        return CorrectionDelegate()

    def test_initialization(self, delegate):
        """Test that the CorrectionDelegate initializes correctly."""
        assert delegate is not None

    def test_paint_correctable_cell_draws_indicator(self, delegate, mocker):
        """Test that paint calls the indicator drawing method when correction info exists."""
        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        # Mock the index.data method to return correction info for the specific role
        def mock_data(role):
            if role == DataViewModel.CorrectionStateRole:
                # Return some non-empty data to indicate correctability
                return {
                    "status": "correctable",
                    "suggestions": [CorrectionSuggestion("original", "corrected")],
                }
            return None  # Return None for other roles

        mock_index.data = mock_data

        # Patch the superclass's paint method directly
        mock_super_paint = mocker.patch.object(ValidationDelegate, "paint", autospec=True)

        # Spy on the internal indicator painting method
        paint_indicator_spy = mocker.spy(delegate, "_paint_correction_indicator")

        # Call the main paint method
        delegate.paint(mock_painter, mock_option, mock_index)

        # Assert that superclass paint was called
        mock_super_paint.assert_called_once_with(delegate, mock_painter, mock_option, mock_index)

        # Assert that the indicator painting method was called
        paint_indicator_spy.assert_called_once_with(mock_painter, mock_option)

    def test_paint_non_correctable_cell_does_not_draw_indicator(self, delegate, mocker):
        """Test that paint does NOT call indicator drawing method if no correction info."""
        mock_painter = mocker.MagicMock(spec=QPainter)
        mock_option = mocker.MagicMock(spec=QStyleOptionViewItem)
        mock_index = mocker.MagicMock(spec=QModelIndex)

        # Mock the index.data method to return None for the correction role
        def mock_data(role):
            if role == DataViewModel.CorrectionStateRole:
                return None  # No correction info
            return None

        mock_index.data = mock_data

        # Patch the superclass's paint method directly
        mock_super_paint = mocker.patch.object(ValidationDelegate, "paint", autospec=True)

        # Spy on the internal indicator painting method
        paint_indicator_spy = mocker.spy(delegate, "_paint_correction_indicator")

        # Call the main paint method
        delegate.paint(mock_painter, mock_option, mock_index)

        # Assert that superclass paint was called
        mock_super_paint.assert_called_once_with(delegate, mock_painter, mock_option, mock_index)

        # Assert that the indicator painting method was NOT called
        paint_indicator_spy.assert_not_called()

    # TODO: Add tests for other overridden methods if implemented (e.g., createEditor)
