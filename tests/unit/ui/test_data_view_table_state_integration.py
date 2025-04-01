"""
Test suite for integration between DataView and TableStateManager.

This module contains test cases for the integration between DataView and TableStateManager,
focusing on how validation and correction states are visualized.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from chestbuddy.core.table_state_manager import TableStateManager, CellState


# Create a minimal mock version of DataView that emulates the methods we need
class MockDataView:
    """A mock implementation of DataView with just the methods we need for testing."""

    # Add necessary signals
    validation_changed = Signal(object)
    correction_applied = Signal(object)
    data_changed = Signal(object)

    def __init__(self, data_model):
        """Initialize the mock data view."""
        self._data_model = data_model
        self._table_state_manager = None
        self._highlight_cell = MagicMock()
        self._set_cell_tooltip = MagicMock()

    def set_table_state_manager(self, manager):
        """Set the table state manager."""
        self._table_state_manager = manager

    def update_cell_highlighting_from_state(self):
        """Update cell highlighting based on the table state manager."""
        if not self._table_state_manager:
            return

        # Get cells in different states
        invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)
        processing_cells = self._table_state_manager.get_cells_by_state(CellState.PROCESSING)

        # Define color constants matching our color legend
        invalid_color = QColor(255, 182, 182)  # Light red
        correctable_color = QColor(255, 214, 165)  # Light orange
        corrected_color = QColor(182, 255, 182)  # Light green
        processing_color = QColor(214, 182, 255)  # Light purple

        # Apply highlighting for each cell type
        for row, col in invalid_cells:
            self._highlight_cell(row, col, invalid_color)

        for row, col in correctable_cells:
            self._highlight_cell(row, col, correctable_color)

        for row, col in corrected_cells:
            self._highlight_cell(row, col, corrected_color)

        for row, col in processing_cells:
            self._highlight_cell(row, col, processing_color)

    def update_tooltips_from_state(self):
        """Update cell tooltips based on the table state manager."""
        if not self._table_state_manager:
            return

        # Get cells with states
        invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)

        # Update tooltips for cells with details
        for row, col in invalid_cells + correctable_cells + corrected_cells:
            detail = self._table_state_manager.get_cell_details(row, col)
            if detail:
                self._set_cell_tooltip(row, col, detail)

    def _on_validation_changed(self, validation_status):
        """Handle validation status changes."""
        if self._table_state_manager:
            self._table_state_manager.update_cell_states_from_validation(validation_status)

    def _on_correction_applied(self, correction_status):
        """Handle correction application."""
        if self._table_state_manager and correction_status:
            self._table_state_manager.update_cell_states_from_correction(correction_status)

        # Update tooltips
        self.update_tooltips_from_state()

    def _on_data_changed(self, data_state=None):
        """Handle data changes."""
        if data_state and self._table_state_manager:
            # If we have information about affected rows, reset just those rows
            if "rows" in data_state and data_state["rows"]:
                self._table_state_manager.reset_rows(data_state["rows"])


class TestDataViewTableStateIntegration:
    """Test cases for the integration between DataView and TableStateManager."""

    @pytest.fixture
    def mock_data_model(self):
        """Create a mock data model with sample data."""
        data = pd.DataFrame(
            {"PLAYER": ["player1", "player2", "player3"], "CHEST": ["Gold", "Silver", "Bronze"]}
        )

        # Create a mock with the necessary methods
        model = MagicMock()
        model.data = data

        # Add commonly used methods
        model.get_data = MagicMock(return_value=data)
        model.column_names = list(data.columns)
        model.data_changed = MagicMock()
        model.validation_changed = MagicMock()
        model.correction_applied = MagicMock()
        model.data_cleared = MagicMock()
        model.is_empty = False
        model.row_count = len(data)

        return model

    @pytest.fixture
    def table_state_manager(self, mock_data_model):
        """Create a table state manager for testing."""
        return TableStateManager(mock_data_model)

    @pytest.fixture
    def data_view(self, mock_data_model):
        """Create a mock data view for testing."""
        return MockDataView(mock_data_model)

    @pytest.fixture
    def integrated_view(self, data_view, table_state_manager):
        """Create a data view with table state manager integrated."""
        # Set the table state manager on the data view
        data_view.set_table_state_manager(table_state_manager)
        return data_view

    def test_set_table_state_manager(self, data_view, table_state_manager):
        """Test setting the table state manager on the data view."""
        # Initially no table state manager (we're setting it in the fixture, so reset it first)
        data_view._table_state_manager = None
        assert data_view._table_state_manager is None

        # Set the table state manager
        data_view.set_table_state_manager(table_state_manager)

        # Verify it was set
        assert data_view._table_state_manager == table_state_manager

    def test_update_cell_highlighting_from_state(self, integrated_view, table_state_manager):
        """Test that cell highlighting is updated based on table state."""
        # Set some cell states
        table_state_manager.set_cell_state(0, 0, CellState.INVALID)
        table_state_manager.set_cell_state(1, 1, CellState.CORRECTABLE)
        table_state_manager.set_cell_state(2, 0, CellState.CORRECTED)

        # Trigger cell highlighting update
        integrated_view.update_cell_highlighting_from_state()

        # Verify highlight_cell was called with correct parameters
        assert integrated_view._highlight_cell.call_count == 3

        # Verify calls include the expected cell coordinates and colors
        calls = integrated_view._highlight_cell.call_args_list
        cell_coords = [(call_args[0][0], call_args[0][1]) for call_args in calls]

        # Verify all expected coordinates are present
        assert (0, 0) in cell_coords
        assert (1, 1) in cell_coords
        assert (2, 0) in cell_coords

    def test_validation_updates_table_state(self, integrated_view, table_state_manager):
        """Test that validation status updates trigger table state updates."""
        # Create a validation status DataFrame
        validation_status = pd.DataFrame(
            {"ROW_IDX": [0, 1], "COL_IDX": [0, 1], "STATUS": ["invalid", "invalid"]}
        )

        # Mock the update_cell_states_from_validation method
        table_state_manager.update_cell_states_from_validation = MagicMock()

        # Trigger validation changed signal
        integrated_view._on_validation_changed(validation_status)

        # Verify table state manager was updated with validation status
        table_state_manager.update_cell_states_from_validation.assert_called_once_with(
            validation_status
        )

    def test_correction_updates_table_state(self, integrated_view, table_state_manager):
        """Test that correction updates trigger table state updates."""
        # Create a correction status dictionary
        correction_status = {
            "corrected_cells": [(0, 1), (1, 0)],
            "original_values": {"(0, 1)": "player1", "(1, 0)": "Silver"},
            "new_values": {"(0, 1)": "Player 1", "(1, 0)": "SILVER"},
        }

        # Mock the update_cell_states_from_correction method
        table_state_manager.update_cell_states_from_correction = MagicMock()

        # Trigger correction applied signal
        integrated_view._on_correction_applied(correction_status)

        # Verify table state manager was updated with correction status
        table_state_manager.update_cell_states_from_correction.assert_called_once_with(
            correction_status
        )

    def test_synchronizes_with_data_changes(self, integrated_view, table_state_manager):
        """Test that table state is synchronized when data changes."""
        # Set initial cell states
        table_state_manager.set_cell_state(0, 0, CellState.INVALID)
        table_state_manager.set_cell_state(1, 1, CellState.CORRECTABLE)

        # Create a data changes event that affects the cells
        data_changes = {"rows": [0, 1], "columns": ["PLAYER", "CHEST"]}

        # Mock reset_rows method
        table_state_manager.reset_rows = MagicMock()

        # Trigger data changed signal with changes
        integrated_view._on_data_changed(data_changes)

        # Verify cell states were reset for changed rows
        table_state_manager.reset_rows.assert_called_once_with(data_changes["rows"])

    def test_cell_tooltips_from_state(self, integrated_view, table_state_manager):
        """Test that cell tooltips are updated based on table state."""
        # Set some cell states
        table_state_manager.set_cell_state(0, 0, CellState.INVALID)
        table_state_manager.set_cell_state(1, 1, CellState.CORRECTABLE)
        table_state_manager.set_cell_state(2, 0, CellState.CORRECTED)

        # Set the get_cell_details method to return mock details
        table_state_manager.get_cell_details = MagicMock(
            side_effect=lambda row, col: f"Details for cell {row},{col}"
        )

        # Trigger tooltip update
        integrated_view.update_tooltips_from_state()

        # Verify _set_cell_tooltip was called with correct parameters
        assert integrated_view._set_cell_tooltip.call_count == 3

        # Get cell coordinates that were passed to _set_cell_tooltip
        calls = integrated_view._set_cell_tooltip.call_args_list
        cell_coords = [(call_args[0][0], call_args[0][1]) for call_args in calls]

        # Verify all expected coordinates are present
        assert (0, 0) in cell_coords
        assert (1, 1) in cell_coords
        assert (2, 0) in cell_coords
