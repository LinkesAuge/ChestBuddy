"""
Tests for the ValidationAdapter class.
"""

import pytest
import pandas as pd
from PySide6.QtCore import QObject, Signal
from unittest.mock import MagicMock, call

from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.core.managers.table_state_manager import TableStateManager, CellFullState
from chestbuddy.core.enums.validation_enums import ValidationStatus


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

    def test_on_validation_complete_updates_manager_with_transformed_data(
        self,
        adapter,
        mock_validation_service,
        mock_table_state_manager,
        mock_validation_results,
        mocker,
    ):
        """Test that receiving validation results updates the state manager with transformed data."""
        # Emit the signal
        mock_validation_service.validation_complete.emit(mock_validation_results)

        # Define validation results
        validation_df = pd.DataFrame(
            {
                "ColA_status": [ValidationStatus.VALID, ValidationStatus.INVALID],
                "ColA_details": [None, "Error A1"],
                "ColB_status": [ValidationStatus.CORRECTABLE, ValidationStatus.VALID],
                "ColB_details": ["Suggestion B0", None],
            }
        )

        # Define expected state changes
        expected_changes = {
            # Row 0, Col 1 (ColB) is CORRECTABLE with details
            (0, 1): CellFullState(
                validation_status=ValidationStatus.CORRECTABLE,
                error_details="Suggestion B0",
                correction_suggestions=None,  # Preserved existing (None in this case)
            ),
            # Row 1, Col 0 (ColA) is INVALID with details
            (1, 0): CellFullState(
                validation_status=ValidationStatus.INVALID,
                error_details="Error A1",
                correction_suggestions=None,  # Preserved existing
            ),
            # Row 0, Col 0 and Row 1, Col 1 are VALID with no details, so no state change entry
        }

        # Verify update_states was called with the correct dictionary
        mock_table_state_manager.update_states.assert_called_once_with(expected_changes)

    def test_on_validation_complete_no_changes(
        self, mock_validation_service, mock_table_state_manager
    ):
        """Test adapter does not call update_states if results show no changes from VALID."""
        # Setup: Manager returns default state
        mock_table_state_manager.get_column_names.return_value = ["ColA"]
        mock_table_state_manager.get_full_cell_state.return_value = CellFullState()

        adapter = ValidationAdapter(
            mock_validation_service,
            mock_table_state_manager,
        )

        # Define validation results that are all VALID and have no details
        validation_df = pd.DataFrame(
            {"ColA_status": [ValidationStatus.VALID, ValidationStatus.VALID]}
        )

        # Simulate signal emission
        mock_validation_service.validation_complete.emit(validation_df)

        # Verify update_states was NOT called
        mock_table_state_manager.update_states.assert_not_called()

    def test_on_validation_complete_preserves_corrections(
        self, mock_validation_service, mock_table_state_manager
    ):
        """Test that validation updates preserve existing correction suggestions."""
        # Setup: Manager returns existing state with correction suggestions
        mock_table_state_manager.get_column_names.return_value = ["ColA"]
        existing_state = CellFullState(
            validation_status=ValidationStatus.VALID,  # Initially valid
            correction_suggestions=["Suggestion1"],
        )
        mock_table_state_manager.get_full_cell_state.return_value = existing_state

        adapter = ValidationAdapter(
            mock_validation_service,
            mock_table_state_manager,
        )

        # Define validation results making the cell INVALID
        validation_df = pd.DataFrame(
            {"ColA_status": [ValidationStatus.INVALID], "ColA_details": ["Validation Error"]}
        )

        # Simulate signal emission
