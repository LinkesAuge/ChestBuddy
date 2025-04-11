"""
Tests for the ValidationAdapter class.
"""

import pytest
import pandas as pd
from PySide6.QtCore import QObject, Signal
from unittest.mock import MagicMock, call, ANY
from typing import Dict, Tuple, List, Optional

from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.core.managers.table_state_manager import TableStateManager, CellFullState, CellState


# Mock classes for dependencies
class MockValidationService(QObject):
    validation_complete = Signal(object)


class MockTableStateManager(QObject):
    """Mock TableStateManager with new methods."""

    def __init__(self):
        self.states: Dict[Tuple[int, int], CellFullState] = {}
        self.column_names = ["Player", "Chest", "Score"]  # Example column names
        self.update_states_calls = []  # Track calls to update_states

    def get_column_names(self) -> List[str]:
        return self.column_names

    def get_full_cell_state(self, row: int, col: int) -> Optional[CellFullState]:
        return self.states.get((row, col))

    def update_states(self, changes: Dict[Tuple[int, int], CellFullState]):
        """Mock update_states, just record the call."""
        self.update_states_calls.append(changes)
        # Simulate merging for get_full_cell_state calls later in the test
        for key, state in changes.items():
            self.states[key] = state


# Test data
@pytest.fixture
def mock_validation_results_df():
    """Create mock validation results DataFrame."""
    return pd.DataFrame(
        {
            "Player_status": [CellState.VALID, CellState.INVALID, CellState.VALID],
            "Player_details": [None, "Invalid Player Name", None],
            "Chest_status": [CellState.VALID, CellState.VALID, CellState.CORRECTABLE],
            "Chest_details": [None, None, "Typo? Suggest 'Silver'"],
            "Score_status": [CellState.VALID, CellState.VALID, CellState.VALID],
            # Missing Score_details column
        }
    )


@pytest.fixture
def mock_validation_service(qtbot):  # Use qtbot for signal testing
    """Create a mock ValidationService instance."""
    return MockValidationService()


@pytest.fixture
def mock_table_state_manager():  # Remove mocker spy here, use internal tracking
    return MockTableStateManager()


@pytest.fixture
def adapter(mock_validation_service, mock_table_state_manager):
    """Create a ValidationAdapter instance with mocks."""
    adapter_instance = ValidationAdapter(mock_validation_service, mock_table_state_manager)
    yield adapter_instance
    # Cleanup: Disconnect signals
    adapter_instance.disconnect_signals()


# --- Tests ---


class TestValidationAdapter:
    """Tests for the ValidationAdapter functionality."""

    def test_initialization(self, adapter, mock_validation_service, mock_table_state_manager):
        """Test adapter initialization and signal connection."""
        assert adapter._validation_service == mock_validation_service
        assert adapter._table_state_manager == mock_table_state_manager
        # Signal connection attempt is verified implicitly by teardown not failing

    def test_on_validation_complete_calls_update_states(
        self,
        adapter,
        mock_validation_service,
        mock_table_state_manager,
        mock_validation_results_df,
    ):
        """Test that receiving validation results calls manager.update_states correctly."""
        # Emit the signal
        mock_validation_service.validation_complete.emit(mock_validation_results_df)

        # Assert manager update method was called once
        assert len(mock_table_state_manager.update_states_calls) == 1

        # Get the changes dictionary passed to update_states
        changes_dict = mock_table_state_manager.update_states_calls[0]

        # Verify the content of the changes dictionary
        # Expected changes based on mock_validation_results_df and mock columns:
        # Row 1, Col 0 (Player): INVALID, with details
        # Row 2, Col 1 (Chest): CORRECTABLE, with details
        expected_changes = {
            (1, 0): CellFullState(
                validation_status=CellState.INVALID,
                error_details="Invalid Player Name",
                correction_suggestions=[],
            ),  # Defaults preserved
            (2, 1): CellFullState(
                validation_status=CellState.CORRECTABLE,
                error_details="Typo? Suggest 'Silver'",
                correction_suggestions=[],
            ),  # Defaults preserved
        }

        assert changes_dict == expected_changes

    def test_on_validation_complete_preserves_corrections(
        self, adapter, mock_validation_service, mock_table_state_manager
    ):
        """Test that validation updates preserve existing correction suggestions."""
        # Setup: Manager has existing state with correction suggestions
        key = (0, 0)  # Player column
        existing_state = CellFullState(
            validation_status=CellState.VALID,  # Initially valid
            correction_suggestions=["SuggestionA", "SuggestionB"],
        )
        mock_table_state_manager.states[key] = existing_state

        # Define validation results making the cell INVALID
        validation_df = pd.DataFrame(
            {
                "Player_status": [CellState.INVALID],
                "Player_details": ["Validation Error"],
                "Chest_status": [CellState.VALID],
                "Score_status": [CellState.VALID],
            }
        )

        # Emit signal
        mock_validation_service.validation_complete.emit(validation_df)

        # Check call to update_states
        assert len(mock_table_state_manager.update_states_calls) == 1
        changes_dict = mock_table_state_manager.update_states_calls[0]

        # Verify the state for the key includes the preserved suggestions
        assert key in changes_dict
        updated_state = changes_dict[key]
        assert updated_state.validation_status == CellState.INVALID
        assert updated_state.error_details == "Validation Error"
        assert updated_state.correction_suggestions == ["SuggestionA", "SuggestionB"]  # Preserved

    def test_on_validation_complete_handles_none(
        self, adapter, mock_validation_service, mock_table_state_manager
    ):
        """Test that None results are handled gracefully."""
        # Emit signal with None
        mock_validation_service.validation_complete.emit(None)

        # Assert manager update method was NOT called
        assert len(mock_table_state_manager.update_states_calls) == 0  # Check calls list

    def test_on_validation_complete_handles_empty_dataframe(
        self, adapter, mock_validation_service, mock_table_state_manager
    ):
        """Test that empty DataFrame results are handled gracefully."""
        empty_df = pd.DataFrame()
        mock_validation_service.validation_complete.emit(empty_df)
        assert len(mock_table_state_manager.update_states_calls) == 0

    def test_on_validation_complete_handles_non_dataframe(
        self, adapter, mock_validation_service, mock_table_state_manager
    ):
        """Test that non-DataFrame results are handled gracefully."""
        # Emit signal with a dictionary instead of DataFrame
        mock_validation_service.validation_complete.emit({"some": "data"})

        # Assert manager update method was NOT called
        assert len(mock_table_state_manager.update_states_calls) == 0  # Check calls list

    def test_on_validation_complete_handles_missing_columns(
        self, adapter, mock_validation_service, mock_table_state_manager
    ):
        """Test that missing status/details columns are handled."""
        validation_df = pd.DataFrame(
            {
                "Player_status": [CellState.INVALID],
                # Missing Player_details, Chest_status, Chest_details, Score_status
            }
        )

        mock_validation_service.validation_complete.emit(validation_df)

        assert len(mock_table_state_manager.update_states_calls) == 1
        changes_dict = mock_table_state_manager.update_states_calls[0]
        # Only Player state should be updated
        assert (0, 0) in changes_dict
        assert changes_dict[(0, 0)].validation_status == CellState.INVALID
        assert changes_dict[(0, 0)].error_details is None
        assert len(changes_dict) == 1

    def test_on_validation_complete_handles_mismatched_columns(
        self, adapter, mock_validation_service, mock_table_state_manager
    ):
        """Test results with columns not present in the state manager."""
        validation_df = pd.DataFrame(
            {"Player_status": [CellState.VALID], "NonExistentColumn_status": [CellState.INVALID]}
        )
        mock_validation_service.validation_complete.emit(validation_df)
        # Should not raise an error, and update_states should not be called
        # because the only potential change (Player_status=VALID) doesn't require an update
        # if the default state is also VALID/NORMAL
        assert len(mock_table_state_manager.update_states_calls) == 0

    def test_disconnect_signals(self, adapter, mock_validation_service):
        """Test that signals are disconnected."""
        # Hard to verify disconnection directly without causing errors
        # Call the method and check it doesn't raise unexpected exceptions
        try:
            adapter.disconnect_signals()
        except Exception as e:
            pytest.fail(f"disconnect_signals raised an exception: {e}")
