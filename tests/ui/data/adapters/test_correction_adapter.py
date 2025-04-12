"""
Tests for the CorrectionAdapter class.
"""

import pytest
from PySide6.QtCore import QObject, Signal
from unittest.mock import MagicMock, call
from typing import Dict, Tuple, List, Optional

from chestbuddy.core.table_state_manager import TableStateManager, CellFullState, CellState
from chestbuddy.ui.data.adapters.correction_adapter import CorrectionAdapter


# Mock classes for dependencies
class MockCorrectionService(QObject):
    # Define the signal assumed in the adapter
    correction_suggestions_available = Signal(object)


class MockTableStateManager(QObject):
    """Mock TableStateManager with updated methods for CorrectionAdapter tests."""

    def __init__(self):
        self.states: Dict[Tuple[int, int], CellFullState] = {}
        self.update_states_calls = []  # Track calls

    def get_full_cell_state(self, row: int, col: int) -> Optional[CellFullState]:
        # Return a copy to mimic getting immutable state
        state = self.states.get((row, col))
        return state  # Return state or None

    def update_states(self, changes: Dict[Tuple[int, int], CellFullState]):
        """Mock update_states, record the call."""
        self.update_states_calls.append(changes)
        # Simulate merging for subsequent get_full_cell_state calls
        for key, state in changes.items():
            # In a real scenario, merging might be more complex
            self.states[key] = state


# Test data
@pytest.fixture
def mock_correction_suggestions_dict():
    """Create mock correction suggestions dictionary."""
    return {
        (1, 0): ["Player1Fixed"],  # Single suggestion
        (2, 2): ["ChestA", "ChestB"],  # Multiple suggestions
        (3, 1): [],  # Empty suggestions (should be ignored)
    }


@pytest.fixture
def mock_correction_service(qtbot):
    """Create a mock CorrectionService instance."""
    return MockCorrectionService()


@pytest.fixture
def mock_table_state_manager():
    """Create a mock TableStateManager instance."""
    return MockTableStateManager()


@pytest.fixture
def adapter(mock_correction_service, mock_table_state_manager):
    """Create a CorrectionAdapter instance with mocks."""
    adapter_instance = CorrectionAdapter(mock_correction_service, mock_table_state_manager)
    yield adapter_instance
    # Cleanup: Disconnect signals
    adapter_instance.disconnect_signals()


# --- Tests ---


class TestCorrectionAdapter:
    """Tests for the CorrectionAdapter functionality."""

    def test_initialization(self, adapter, mock_correction_service, mock_table_state_manager):
        """Test adapter initialization and signal connection attempt."""
        assert adapter._correction_service == mock_correction_service
        assert adapter._table_state_manager == mock_table_state_manager
        # Signal connection is attempted in __init__

    def test_on_corrections_available_calls_update_states(
        self,
        adapter,
        mock_correction_service,
        mock_table_state_manager,
        mock_correction_suggestions_dict,
    ):
        """Test receiving suggestions calls manager.update_states with correct states."""
        # Emit the signal
        mock_correction_service.correction_suggestions_available.emit(
            mock_correction_suggestions_dict
        )

        # Assert update_states was called once
        assert len(mock_table_state_manager.update_states_calls) == 1
        changes_dict = mock_table_state_manager.update_states_calls[0]

        # Verify the content for cells with suggestions
        # Cell (3, 1) with empty suggestions should be ignored
        assert len(changes_dict) == 2

        # Check cell (1, 0)
        key10 = (1, 0)
        assert key10 in changes_dict
        state10 = changes_dict[key10]
        assert isinstance(state10, CellFullState)
        assert state10.validation_status == CellState.CORRECTABLE
        assert state10.correction_suggestions == ["Player1Fixed"]
        assert state10.error_details is None  # Preserved default

        # Check cell (2, 2)
        key22 = (2, 2)
        assert key22 in changes_dict
        state22 = changes_dict[key22]
        assert isinstance(state22, CellFullState)
        assert state22.validation_status == CellState.CORRECTABLE
        assert state22.correction_suggestions == ["ChestA", "ChestB"]
        assert state22.error_details is None  # Preserved default

    def test_on_corrections_available_preserves_validation_state(
        self, adapter, mock_correction_service, mock_table_state_manager
    ):
        """Test correction suggestions preserve existing validation error details."""
        # Setup: Manager has existing state with validation error
        key = (0, 1)
        existing_state = CellFullState(
            validation_status=CellState.INVALID,  # Initially invalid
            error_details="Existing validation error",
        )
        mock_table_state_manager.states[key] = existing_state

        # Define correction suggestions for this cell
        suggestions = {(key): ["CorrectionA"]}

        # Emit signal
        mock_correction_service.correction_suggestions_available.emit(suggestions)

        # Check call to update_states
        assert len(mock_table_state_manager.update_states_calls) == 1
        changes_dict = mock_table_state_manager.update_states_calls[0]

        # Verify the state for the key includes preserved details
        assert key in changes_dict
        updated_state = changes_dict[key]
        assert updated_state.validation_status == CellState.CORRECTABLE  # Status updated
        assert updated_state.error_details == "Existing validation error"  # Details preserved
        assert updated_state.correction_suggestions == ["CorrectionA"]  # Suggestions added

    def test_on_corrections_available_handles_none_or_empty(
        self, adapter, mock_correction_service, mock_table_state_manager
    ):
        """Test that None or empty suggestions are handled gracefully."""
        # Emit signal with None
        mock_correction_service.correction_suggestions_available.emit(None)
        assert len(mock_table_state_manager.update_states_calls) == 0  # Check calls list

        # Emit signal with empty dict
        mock_correction_service.correction_suggestions_available.emit({})
        assert len(mock_table_state_manager.update_states_calls) == 0  # Still 0

        # Emit signal with dict containing only empty suggestions
        mock_correction_service.correction_suggestions_available.emit({(0, 0): [], (1, 1): []})
        assert len(mock_table_state_manager.update_states_calls) == 0  # Still 0

    def test_disconnect_signals(self, adapter, mock_correction_service):
        """Test that signals are disconnected without errors."""
        try:
            adapter.disconnect_signals()
        except Exception as e:
            pytest.fail(f"disconnect_signals raised an exception: {e}")
