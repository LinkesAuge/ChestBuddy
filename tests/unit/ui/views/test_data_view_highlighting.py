"""
test_data_view_highlighting.py

This module contains tests for the cell highlighting functionality in the DataView
related to the correction feature.
"""

import pytest
from PySide6.QtCore import Qt
from unittest.mock import MagicMock, patch

from chestbuddy.ui.data_view import DataView


@pytest.fixture
def mock_data_model():
    """Create a mock ChestDataModel."""
    model = MagicMock()
    model.is_empty = False
    model.column_names = ["PLAYER", "CHEST", "SOURCE", "STATUS"]
    model.row_count = 5
    return model


@pytest.fixture
def mock_table_model():
    """Create a mock QStandardItemModel."""
    model = MagicMock()
    model.rowCount.return_value = 5
    model.columnCount.return_value = 4
    return model


@pytest.fixture
def data_view(qtbot, mock_data_model):
    """Create a DataView instance for testing."""
    view = DataView(mock_data_model)

    # Mock the table model
    view._table_model = MagicMock()
    view._table_model.item.return_value = MagicMock()

    # Mock the highlight_cell method
    view._highlight_cell = MagicMock()

    qtbot.addWidget(view)
    view.show()
    return view


def test_update_cell_highlighting(data_view):
    """Test that update_cell_highlighting calls the right methods."""
    # Setup the mock methods
    data_view._get_invalid_cells = MagicMock(return_value=[(0, 1), (2, 3)])
    data_view._get_corrected_cells = MagicMock(return_value=[(1, 2)])
    data_view._get_correctable_cells = MagicMock(return_value=[(0, 1), (3, 0)])

    # Call the method being tested
    data_view.update_cell_highlighting()

    # Verify that the get methods were called
    data_view._get_invalid_cells.assert_called_once()
    data_view._get_corrected_cells.assert_called_once()
    data_view._get_correctable_cells.assert_called_once()

    # Verify that highlight_cell was called with the right parameters
    assert data_view._highlight_cell.call_count >= 3  # At least 3 calls

    # Invalid with correction rule (orange)
    data_view._highlight_cell.assert_any_call(0, 1, "orange")

    # Invalid without correction rule (red)
    data_view._highlight_cell.assert_any_call(2, 3, "red")

    # Corrected cell (green)
    data_view._highlight_cell.assert_any_call(1, 2, "green")

    # Correctable but not invalid or corrected (purple)
    data_view._highlight_cell.assert_any_call(3, 0, "purple")


def test_highlight_cell_method(data_view):
    """Test that the _highlight_cell method sets the correct colors."""
    # Replace the mock with the actual implementation for this test
    data_view._highlight_cell = DataView._highlight_cell.__get__(data_view, DataView)

    # Create a mock item that will be returned by _table_model.item
    mock_item = MagicMock()
    data_view._table_model.item.return_value = mock_item

    # Call the method with different colors
    data_view._highlight_cell(0, 1, "red")
    data_view._highlight_cell(1, 2, "green")
    data_view._highlight_cell(2, 3, "orange")
    data_view._highlight_cell(3, 0, "purple")

    # Verify that setData was called with the right parameters
    assert mock_item.setData.call_count == 4

    # For each color, verify the call
    calls = mock_item.setData.call_args_list

    # Extract just the color part from each call
    colors = [str(call[0][0]) if call[0][0] is not None else "" for call in calls]

    # Check that each expected color is in the list using more flexible checks
    assert any(c for c in colors if "red" in str(c).lower())
    assert any(c for c in colors if "green" in str(c).lower())
    assert any(c for c in colors if "yellow" in str(c).lower())  # We're using yellow for orange
    assert any(c for c in colors if "magenta" in str(c).lower())  # We're using magenta for purple


def test_get_invalid_cells(data_view):
    """Test that _get_invalid_cells returns the correct cells."""
    # Setup
    data_view._controller = MagicMock()
    data_view._controller.get_invalid_cells.return_value = [(0, 1), (2, 3)]

    # Call the method
    result = data_view._get_invalid_cells()

    # Verify
    assert result == [(0, 1), (2, 3)]
    data_view._controller.get_invalid_cells.assert_called_once()


def test_get_corrected_cells(data_view):
    """Test that _get_corrected_cells returns the correct cells."""
    # Setup
    data_view._controller = MagicMock()
    data_view._controller.get_corrected_cells.return_value = [(1, 2)]

    # Call the method
    result = data_view._get_corrected_cells()

    # Verify
    assert result == [(1, 2)]
    data_view._controller.get_corrected_cells.assert_called_once()


def test_get_correctable_cells(data_view):
    """Test that _get_correctable_cells returns the correct cells."""
    # Setup
    data_view._controller = MagicMock()
    data_view._controller.get_cells_with_available_corrections.return_value = [(0, 1), (3, 0)]

    # Call the method
    result = data_view._get_correctable_cells()

    # Verify
    assert result == [(0, 1), (3, 0)]
    data_view._controller.get_cells_with_available_corrections.assert_called_once()


def test_on_correction_applied(data_view):
    """Test that _on_correction_applied updates the highlighting."""
    # Mock the update_cell_highlighting method
    data_view.update_cell_highlighting = MagicMock()

    # Call the method
    data_view._on_correction_applied({})

    # Verify that update_cell_highlighting was called
    data_view.update_cell_highlighting.assert_called_once()
