"""
Tests for the ValidationAdapter class.
"""

import pytest
import pandas as pd
from PySide6.QtCore import QObject, Signal
from unittest.mock import MagicMock

from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter


# Mock classes for dependencies
class MockValidationService(QObject):
    validation_complete = Signal(object)


class MockTableStateManager(QObject):
    def update_cell_states_from_validation(self, updates):
        pass  # Mock method


# Test data
@pytest.fixture
def mock_validation_results():
    """Create mock validation results DataFrame."""
    # Example structure: DataFrame with columns like 'ColumnName_status'
    return pd.DataFrame(
        {
            "Player_status": ["VALID", "INVALID", "VALID"],
            "Chest_status": ["VALID", "VALID", "CORRECTABLE"],
            "Score_status": ["VALID", "VALID", "VALID"],
        }
    )


@pytest.fixture
def mock_validation_service(qtbot):  # Use qtbot for signal testing
    """Create a mock ValidationService instance."""
    return MockValidationService()


@pytest.fixture
def mock_table_state_manager(mocker):  # Use mocker for method spying
    """Create a mock TableStateManager instance."""
    manager = MockTableStateManager()
    mocker.spy(manager, "update_cell_states_from_validation")
    return manager


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

    def test_on_validation_complete_updates_manager(
        self,
        adapter,
        mock_validation_service,
        mock_table_state_manager,
        mock_validation_results,
        mocker,
    ):
        """Test that receiving validation results updates the state manager."""
        # Emit the signal
        mock_validation_service.validation_complete.emit(mock_validation_results)

        # Assert manager update method was called with the DataFrame
        mock_table_state_manager.update_cell_states_from_validation.assert_called_once_with(
            mock_validation_results
        )

    def test_on_validation_complete_handles_none(
        self, adapter, mock_validation_service, mock_table_state_manager, mocker
    ):
        """Test that None results are handled gracefully."""
        # Emit signal with None
        mock_validation_service.validation_complete.emit(None)

        # Assert manager update method was NOT called
        mock_table_state_manager.update_cell_states_from_validation.assert_not_called()

    def test_on_validation_complete_handles_non_dataframe(
        self, adapter, mock_validation_service, mock_table_state_manager, mocker
    ):
        """Test that non-DataFrame results are handled gracefully."""
        # Emit signal with a dictionary instead of DataFrame
        mock_validation_service.validation_complete.emit({"some": "data"})

        # Assert manager update method was NOT called
        mock_table_state_manager.update_cell_states_from_validation.assert_not_called()

    def test_disconnect_signals(self, adapter, mock_validation_service):
        """Test that signals are disconnected."""
        # Hard to verify disconnection directly without causing errors
        # Call the method and check it doesn't raise unexpected exceptions
        try:
            adapter.disconnect_signals()
        except Exception as e:
            pytest.fail(f"disconnect_signals raised an exception: {e}")
