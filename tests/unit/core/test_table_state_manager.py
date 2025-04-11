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

from PySide6.QtCore import QObject, Signal, Qt

from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState


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

    def test_update_states_new_state(self, table_state_manager, qtbot):
        """Test update_states setting a new state for a cell."""
        key = (0, 1)
        new_state = CellFullState(validation_status=CellState.INVALID, error_details="Bad value")

        # Spy on the signal
        signal_spy = qtbot.createSignalSpy(table_state_manager.state_changed)

        table_state_manager.update_states({key: new_state})

        # Verify internal state
        assert key in table_state_manager._cell_states
        assert table_state_manager._cell_states[key] == new_state
        # Verify signal emission
        assert signal_spy.count() == 1
        assert signal_spy[0] == [{key}]  # Signal emits set of changed keys

    def test_update_states_modify_existing(self, table_state_manager, qtbot):
        """Test update_states modifying different aspects of an existing state."""
        key = (1, 0)
        initial_state = CellFullState(
            validation_status=CellState.INVALID, error_details="Initial error"
        )
        table_state_manager.update_states({key: initial_state})  # Set initial state

        # 1. Update only validation status
        update1 = CellFullState(validation_status=CellState.CORRECTABLE)
        signal_spy1 = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.update_states({key: update1})
        assert table_state_manager._cell_states[key].validation_status == CellState.CORRECTABLE
        assert table_state_manager._cell_states[key].error_details == "Initial error"  # Unchanged
        assert table_state_manager._cell_states[key].correction_suggestions == []  # Unchanged
        assert signal_spy1.count() == 1
        assert signal_spy1[0] == [{key}]

        # 2. Update details and add suggestions
        update2 = CellFullState(
            error_details="Updated error", correction_suggestions=["Suggestion1"]
        )
        signal_spy2 = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.update_states({key: update2})
        assert (
            table_state_manager._cell_states[key].validation_status == CellState.CORRECTABLE
        )  # Unchanged
        assert table_state_manager._cell_states[key].error_details == "Updated error"
        assert table_state_manager._cell_states[key].correction_suggestions == ["Suggestion1"]
        assert signal_spy2.count() == 1
        assert signal_spy2[0] == [{key}]

        # 3. Update multiple cells
        key2 = (0, 0)
        update3 = {
            key: CellFullState(validation_status=CellState.VALID),  # Change status back
            key2: CellFullState(validation_status=CellState.INFO, error_details="Just info"),
        }
        signal_spy3 = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.update_states(update3)
        assert table_state_manager._cell_states[key].validation_status == CellState.VALID
        assert (
            table_state_manager._cell_states[key].error_details == "Updated error"
        )  # Should remain
        assert table_state_manager._cell_states[key2].validation_status == CellState.INFO
        assert table_state_manager._cell_states[key2].error_details == "Just info"
        assert signal_spy3.count() == 1
        assert signal_spy3[0] == [{key, key2}]  # Both keys in the set

    def test_update_states_no_change(self, table_state_manager, qtbot):
        """Test update_states when the new state is the same as the old."""
        key = (0, 1)
        state = CellFullState(validation_status=CellState.INVALID)
        table_state_manager.update_states({key: state})  # Set initial

        signal_spy = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.update_states({key: state})  # Update with same state

        assert signal_spy.count() == 0  # Signal should not be emitted

    def test_get_cell_state_and_full_state(self, table_state_manager):
        """Test getting cell state (validation status only) and full state."""
        key = (0, 1)
        state = CellFullState(
            validation_status=CellState.INVALID, error_details="Bad", correction_suggestions=["Fix"]
        )
        table_state_manager.update_states({key: state})

        # Test get_cell_state (returns only validation status)
        assert table_state_manager.get_cell_state(key[0], key[1]) == CellState.INVALID

        # Test get_full_cell_state
        full_state = table_state_manager.get_full_cell_state(key[0], key[1])
        assert full_state == state

        # Test default state for unset cell
        assert table_state_manager.get_cell_state(1, 1) == CellState.NORMAL
        assert table_state_manager.get_full_cell_state(1, 1) is None  # Default is no state object

    def test_reset_cell_states(self, table_state_manager, qtbot):
        """Test resetting all cell states and signal emission."""
        key1 = (0, 1)
        key2 = (1, 0)
        table_state_manager.update_states(
            {
                key1: CellFullState(validation_status=CellState.INVALID),
                key2: CellFullState(validation_status=CellState.CORRECTABLE),
            }
        )
        assert key1 in table_state_manager._cell_states
        assert key2 in table_state_manager._cell_states

        signal_spy = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.reset_cell_states()

        # Verify internal state is empty
        assert table_state_manager._cell_states == {}
        # Verify signal emitted with previously affected keys
        assert signal_spy.count() == 1
        assert signal_spy[0] == [{key1, key2}]

    def test_reset_cell_state_single(self, table_state_manager, qtbot):
        """Test resetting a single cell's state."""
        key1 = (0, 1)
        key2 = (1, 0)
        table_state_manager.update_states(
            {
                key1: CellFullState(validation_status=CellState.INVALID),
                key2: CellFullState(validation_status=CellState.CORRECTABLE),
            }
        )

        signal_spy = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.reset_cell_state(key1[0], key1[1])

        assert key1 not in table_state_manager._cell_states
        assert key2 in table_state_manager._cell_states  # Other state remains
        assert signal_spy.count() == 1
        assert signal_spy[0] == [{key1}]

    def test_reset_rows(self, table_state_manager, qtbot):
        """Test resetting states for specific rows."""
        key00 = (0, 0)
        key01 = (0, 1)
        key10 = (1, 0)
        table_state_manager.update_states(
            {
                key00: CellFullState(validation_status=CellState.INFO),
                key01: CellFullState(validation_status=CellState.INVALID),
                key10: CellFullState(validation_status=CellState.CORRECTABLE),
            }
        )

        signal_spy = qtbot.createSignalSpy(table_state_manager.state_changed)
        table_state_manager.reset_rows([0])  # Reset row 0

        assert key00 not in table_state_manager._cell_states
        assert key01 not in table_state_manager._cell_states
        assert key10 in table_state_manager._cell_states  # Row 1 remains
        assert signal_spy.count() == 1
        assert signal_spy[0] == [{key00, key01}]

    def test_get_cells_by_state(self, table_state_manager):
        """Test getting cells by validation state."""
        table_state_manager.update_states(
            {
                (0, 1): CellFullState(validation_status=CellState.INVALID),
                (1, 0): CellFullState(validation_status=CellState.INVALID, error_details="Err"),
                (1, 1): CellFullState(validation_status=CellState.CORRECTABLE),
                (2, 0): CellFullState(validation_status=CellState.CORRECTED),
                (2, 1): CellFullState(validation_status=CellState.INVALID),  # Another invalid
            }
        )

        invalid_cells = table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = table_state_manager.get_cells_by_state(CellState.CORRECTED)
        normal_cells = table_state_manager.get_cells_by_state(CellState.NORMAL)  # Should be empty

        assert set(invalid_cells) == {(0, 1), (1, 0), (2, 1)}
        assert set(correctable_cells) == {(1, 1)}
        assert set(corrected_cells) == {(2, 0)}
        assert normal_cells == []  # No cells explicitly set to NORMAL

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

    def test_get_affected_rows_columns(self, table_state_manager):
        """Test getting affected rows and columns from DataFrame comparison (mocked)."""
        # Mock original data
        original_data = pd.DataFrame({"PLAYER": ["A", "B"], "CHEST": ["G", "S"]})
        # Mock current (modified) data in the model
        current_data = pd.DataFrame(
            {
                "PLAYER": ["A", "X"],  # Modified
                "CHEST": ["G", "Y"],  # Modified
            }
        )
        table_state_manager._data_model.data = current_data

        # Use the internal _headers_map which should be {'PLAYER': 0, 'CHEST': 1}
        affected = table_state_manager.get_affected_rows_columns(original_data)

        # Only row 1 was changed in both columns
        assert set(affected["rows"]) == {1}
        assert set(affected["columns"]) == {"PLAYER", "CHEST"}
