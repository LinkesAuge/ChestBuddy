"""
Tests for the CorrectionAdapter class.
"""

import pytest
from PySide6.QtCore import QObject, Signal
from unittest.mock import MagicMock

from chestbuddy.ui.data.adapters.correction_adapter import CorrectionAdapter


# Mock classes for dependencies
class MockCorrectionService(QObject):
    # Define the signal assumed in the adapter
    correction_suggestions_available = Signal(object)


class MockTableStateManager(QObject):
    # Define the method assumed in the adapter
    def update_cell_states_from_correction(self, updates):
        pass  # Mock method

    def update_cell_states_from_correctable(self, correctable_cells):
        pass  # Mock method


# Test data
@pytest.fixture
def mock_correction_suggestions():
    """Create mock correction suggestions dictionary."""
    # Example structure: dict mapping (row, col) to list of suggestions
    return {
        (1, 0): [{"original": "Orig1", "corrected": "Corr1"}],  # Suggestions for cell (1,0)
        (2, 2): [
            {"original": "Orig2", "corrected": "Corr2a"},
            {"original": "Orig2", "corrected": "Corr2b"},
        ],  # Multiple suggestions
        (3, 1): [],  # No suggestions for this cell (e.g., correction applied/invalidated)
    }


@pytest.fixture
def mock_correction_service(qtbot):
    """Create a mock CorrectionService instance."""
    return MockCorrectionService()


@pytest.fixture
def mock_table_state_manager(mocker):
    """Create a mock TableStateManager instance."""
    manager = MockTableStateManager()
    mocker.spy(manager, "update_cell_states_from_correction")
    mocker.spy(manager, "update_cell_states_from_correctable")
    return manager


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

    def test_on_corrections_available_updates_manager(
        self,
        adapter,
        mock_correction_service,
        mock_table_state_manager,
        mock_correction_suggestions,
        mocker,
    ):
        """Test that receiving correction suggestions calls the correct manager method."""
        # Spy on the manager's method
        update_spy = mock_table_state_manager.update_cell_states_from_correctable

        # Emit the signal
        mock_correction_service.correction_suggestions_available.emit(mock_correction_suggestions)

        # Assert manager update method was called with the correct list of tuples
        expected_correctable_cells = [
            (1, 0),  # Cell with suggestions
            (2, 2),  # Cell with suggestions
            # Cell (3, 1) had empty suggestions, so it's excluded
        ]
        # Convert to sets for order-independent comparison if needed
        update_spy.assert_called_once()
        call_args = update_spy.call_args[0][0]
        assert isinstance(call_args, list)
        assert sorted(call_args) == sorted(expected_correctable_cells)

    def test_on_corrections_available_handles_none_or_empty(
        self, adapter, mock_correction_service, mock_table_state_manager, mocker
    ):
        """Test that None or empty suggestions are handled gracefully."""
        update_spy = mock_table_state_manager.update_cell_states_from_correctable

        # Emit signal with None
        mock_correction_service.correction_suggestions_available.emit(None)
        update_spy.assert_not_called()

        # Emit signal with empty dict
        mock_correction_service.correction_suggestions_available.emit({})
        update_spy.assert_not_called()

        # Emit signal with dict containing only empty suggestions
        mock_correction_service.correction_suggestions_available.emit({(0, 0): [], (1, 1): []})
        update_spy.assert_not_called()

    def test_disconnect_signals(self, adapter, mock_correction_service):
        """Test that signals are disconnected without errors."""
        try:
            adapter.disconnect_signals()
        except Exception as e:
            pytest.fail(f"disconnect_signals raised an exception: {e}")
