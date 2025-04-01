"""
Test suite for TableStateManager.

This module contains test cases for the TableStateManager class that is responsible
for managing cell states and correction visualization.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import pandas as pd
from enum import Enum
from typing import Dict, List, Any, Tuple

from PySide6.QtCore import QObject, Signal

from chestbuddy.core.table_state_manager import TableStateManager, CellState


class TestTableStateManager:
    """Test cases for the TableStateManager class."""

    @pytest.fixture
    def mock_data_model(self):
        """Create a mock data model with sample data."""
        data_model = MagicMock()
        data_model.data = pd.DataFrame(
            {"PLAYER": ["player1", "player2", "player3"], "CHEST": ["Gold", "Silver", "Bronze"]}
        )
        return data_model

    @pytest.fixture
    def table_state_manager(self, mock_data_model):
        """Create a table state manager for testing."""
        return TableStateManager(mock_data_model)

    def test_initialization(self, table_state_manager, mock_data_model):
        """Test that manager initializes correctly with dependencies."""
        assert table_state_manager._data_model == mock_data_model
        assert table_state_manager._cell_states == {}
        assert table_state_manager.BATCH_SIZE == 100

    def test_cell_state_enum(self):
        """Test that CellState enum has the expected values."""
        assert CellState.NORMAL.value == 0
        assert CellState.INVALID.value == 1
        assert CellState.CORRECTABLE.value == 2
        assert CellState.CORRECTED.value == 3
        assert CellState.PROCESSING.value == 4

    def test_set_cell_state(self, table_state_manager):
        """Test setting a cell state."""
        # Set a cell state
        table_state_manager.set_cell_state(0, 1, CellState.INVALID)

        # Verify the state was set
        assert table_state_manager._cell_states.get((0, 1)) == CellState.INVALID

        # Override with a new state
        table_state_manager.set_cell_state(0, 1, CellState.CORRECTED)
        assert table_state_manager._cell_states.get((0, 1)) == CellState.CORRECTED

    def test_get_cell_state(self, table_state_manager):
        """Test getting a cell state."""
        # Initially cells should have NORMAL state
        assert table_state_manager.get_cell_state(0, 1) == CellState.NORMAL

        # Set a cell state
        table_state_manager.set_cell_state(0, 1, CellState.INVALID)

        # Verify the state can be retrieved
        assert table_state_manager.get_cell_state(0, 1) == CellState.INVALID

    def test_reset_cell_states(self, table_state_manager):
        """Test resetting all cell states."""
        # Set some cell states
        table_state_manager.set_cell_state(0, 1, CellState.INVALID)
        table_state_manager.set_cell_state(1, 0, CellState.CORRECTABLE)

        # Verify states were set
        assert table_state_manager.get_cell_state(0, 1) == CellState.INVALID
        assert table_state_manager.get_cell_state(1, 0) == CellState.CORRECTABLE

        # Reset all states
        table_state_manager.reset_cell_states()

        # Verify all states were reset
        assert table_state_manager.get_cell_state(0, 1) == CellState.NORMAL
        assert table_state_manager.get_cell_state(1, 0) == CellState.NORMAL

    def test_get_cells_by_state(self, table_state_manager):
        """Test getting cells by state."""
        # Set cell states
        table_state_manager.set_cell_state(0, 1, CellState.INVALID)
        table_state_manager.set_cell_state(1, 0, CellState.INVALID)
        table_state_manager.set_cell_state(1, 1, CellState.CORRECTABLE)
        table_state_manager.set_cell_state(2, 0, CellState.CORRECTED)

        # Get cells by state
        invalid_cells = table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = table_state_manager.get_cells_by_state(CellState.CORRECTED)

        # Verify correct cells were returned
        assert set(invalid_cells) == {(0, 1), (1, 0)}
        assert set(correctable_cells) == {(1, 1)}
        assert set(corrected_cells) == {(2, 0)}

    def test_process_in_batches(self, table_state_manager):
        """Test processing data in batches."""
        # Create a test function to track processing
        processed_rows = []

        def process_func(row_idx):
            processed_rows.append(row_idx)
            return True

        # Process with 3 rows, batch size 2
        table_state_manager.BATCH_SIZE = 2
        result = table_state_manager.process_in_batches(
            process_func, total_rows=3, progress_callback=lambda current, total: None
        )

        # Verify all rows were processed in order
        assert processed_rows == [0, 1, 2]
        assert result == [True, True, True]

    def test_get_affected_rows_columns(self, table_state_manager, mock_data_model):
        """Test getting affected rows and columns from DataFrame."""

        # Create a test function that modifies the DataFrame
        def test_func():
            # Simulate changes to the DataFrame
            mock_data_model.data.loc[0, "PLAYER"] = "Modified Player"
            mock_data_model.data.loc[1, "CHEST"] = "Modified Chest"

        # Get original data snapshot
        original_data = mock_data_model.data.copy()

        # Run the function
        test_func()

        # Get affected rows and columns
        affected = table_state_manager.get_affected_rows_columns(original_data)

        # Verify correct rows and columns were identified
        assert set(affected["rows"]) == {0, 1}
        assert set(affected["columns"]) == {"PLAYER", "CHEST"}

    def test_update_cell_states_from_validation(self, table_state_manager):
        """Test updating cell states from validation status."""
        # Create validation status dataframe
        validation_status = pd.DataFrame(
            {"ROW_IDX": [0, 1, 2], "COL_IDX": [0, 1, 0], "STATUS": ["invalid", "invalid", "valid"]}
        )

        # Update cell states from validation
        table_state_manager.update_cell_states_from_validation(validation_status)

        # Verify states were updated correctly
        assert table_state_manager.get_cell_state(0, 0) == CellState.INVALID
        assert table_state_manager.get_cell_state(1, 1) == CellState.INVALID
        assert (
            table_state_manager.get_cell_state(2, 0) == CellState.NORMAL
        )  # Valid cells remain normal
