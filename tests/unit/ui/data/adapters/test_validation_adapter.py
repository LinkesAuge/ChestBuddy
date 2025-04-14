"""
test_validation_adapter.py

Description:
    Unit tests for the ValidationAdapter class.

Usage:
    pytest tests/unit/ui/data/adapters/test_validation_adapter.py
"""

import pytest
from unittest.mock import MagicMock, call
import pandas as pd
from PySide6.QtCore import Signal, QObject

# Assuming these imports are correct based on the project structure
from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.core.table_state_manager import (
    TableStateManager,
    CellState,
    CellFullState,
)
from chestbuddy.core.enums.validation_enums import ValidationStatus


# Mock the actual ValidationService signature more closely
class MockValidationService(QObject):
    """Mock implementation of ValidationService for testing."""

    validation_complete = Signal(object)  # Emits a pandas DataFrame

    def __init__(self):
        """Initializes the mock service."""
        super().__init__()


@pytest.fixture
def mock_state_manager() -> MagicMock:
    """Provides a mock TableStateManager."""
    mock = MagicMock(spec=TableStateManager)
    # Setup a default headers_map for tests
    mock.headers_map = {"COL_A": 0, "COL_B": 1}
    # Mock get_full_cell_state to return a default state (NORMAL)
    mock.get_full_cell_state.return_value = CellFullState(
        validation_status=CellState.NORMAL, error_details="", correction_suggestions=[]
    )
    return mock


@pytest.fixture
def mock_validation_service() -> MockValidationService:
    """Provides a mock ValidationService."""
    return MockValidationService()


@pytest.fixture
def validation_adapter(
    mock_state_manager: MagicMock, mock_validation_service: MockValidationService
) -> ValidationAdapter:
    """Provides an instance of ValidationAdapter with mocked dependencies."""
    # Corrected initialization order based on ValidationAdapter's __init__ signature
    adapter = ValidationAdapter(
        validation_service=mock_validation_service,
        table_state_manager=mock_state_manager,
    )
    # Mock the disconnect method to avoid errors during test cleanup if signals weren't connected
    adapter.disconnect_signals = MagicMock()
    return adapter


def test_validation_adapter_initialization(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that ValidationAdapter initializes and connects signals correctly."""
    assert validation_adapter._validation_service is mock_validation_service
    assert validation_adapter._table_state_manager is mock_state_manager
    # We can check if the slot is connected by checking the receiver list (requires Qt test utils ideally)
    # For now, rely on functional tests


def test_validation_complete_updates_state_manager(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that TableStateManager.update_states is called correctly."""
    # Prepare a sample status_df as emitted by ValidationService
    test_status_df = pd.DataFrame(
        {
            "COL_A_status": [ValidationStatus.VALID, ValidationStatus.INVALID],
            "COL_A_message": ["", "Error A2"],
            "COL_B_status": [ValidationStatus.CORRECTABLE, ValidationStatus.VALID],
            "COL_B_message": ["Suggestion B1", ""],
        },
        index=[0, 1],
    )

    # Define the expected states dictionary to be passed to update_states
    # Based on the test_status_df and default initial state (NORMAL)
    expected_new_states = {
        (0, 0): CellFullState(
            validation_status=CellState.VALID, error_details="", correction_suggestions=[]
        ),
        (0, 1): CellFullState(
            validation_status=CellState.CORRECTABLE,
            error_details="Suggestion B1",
            correction_suggestions=[],
        ),
        (1, 0): CellFullState(
            validation_status=CellState.INVALID,
            error_details="Error A2",
            correction_suggestions=[],
        ),
        (1, 1): CellFullState(
            validation_status=CellState.VALID, error_details="", correction_suggestions=[]
        ),
    }

    # Mock the get_full_cell_state to return the default state (NORMAL)
    mock_state_manager.get_full_cell_state.side_effect = lambda r, c: CellFullState(
        validation_status=CellState.NORMAL, error_details="", correction_suggestions=[]
    )

    # Emit the signal
    mock_validation_service.validation_complete.emit(test_status_df)

    # Assert update_states was called once with the expected dictionary
    mock_state_manager.update_states.assert_called_once_with(expected_new_states)


def test_validation_complete_no_update_if_no_change(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that update_states is not called if validation status hasn't changed."""
    # Prepare status_df where the status matches the default mock state (NORMAL)
    # Map ValidationStatus.NOT_VALIDATED from service to CellState.NORMAL
    test_status_df = pd.DataFrame(
        {
            "COL_A_status": [ValidationStatus.NOT_VALIDATED, ValidationStatus.NOT_VALIDATED],
            "COL_A_message": ["", ""],
            "COL_B_status": [ValidationStatus.NOT_VALIDATED, ValidationStatus.NOT_VALIDATED],
            "COL_B_message": ["", ""],
        },
        index=[0, 1],
    )

    # Set the mock get_full_cell_state to return NORMAL, matching the mapped input
    mock_state_manager.get_full_cell_state.return_value = CellFullState(
        validation_status=CellState.NORMAL, error_details="", correction_suggestions=[]
    )

    # Emit the signal
    mock_validation_service.validation_complete.emit(test_status_df)

    # Assert update_states was NOT called
    mock_state_manager.update_states.assert_not_called()


def test_validation_complete_clears_error_on_valid(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that error message is cleared when status becomes VALID."""
    # Prepare status_df marking cell (0, 0) as VALID
    test_status_df = pd.DataFrame(
        {
            "COL_A_status": [ValidationStatus.VALID],
            "COL_A_message": [""],  # Service provides empty message for VALID
            "COL_B_status": [ValidationStatus.NOT_VALIDATED],
            "COL_B_message": [""],
        },
        index=[0],
    )

    # Mock get_full_cell_state for cell (0, 0) to have a pre-existing error
    mock_state_manager.get_full_cell_state.side_effect = (
        lambda r, c: CellFullState(
            validation_status=CellState.INVALID,
            error_details="Old Error",
            correction_suggestions=[],
        )
        if (r, c) == (0, 0)
        else CellFullState(
            validation_status=CellState.NORMAL,
            error_details="",
            correction_suggestions=[],  # Default is NORMAL
        )
    )

    # Expected state for cell (0, 0) should now be VALID with empty error
    expected_new_states = {
        (0, 0): CellFullState(
            validation_status=CellState.VALID, error_details="", correction_suggestions=[]
        ),
        # Cell (0, 1) state doesn't change from default NORMAL (was NOT_VALIDATED in status_df but maps to NORMAL)
    }

    # Emit the signal
    mock_validation_service.validation_complete.emit(test_status_df)

    # Assert update_states was called with the state for (0, 0) having the error cleared
    mock_state_manager.update_states.assert_called_once_with(expected_new_states)


def test_validation_complete_ignores_missing_columns(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that processing skips columns missing in the status_df."""
    # Prepare status_df missing COL_B columns
    test_status_df = pd.DataFrame(
        {
            "COL_A_status": [ValidationStatus.INVALID],
            "COL_A_message": ["Error A1"],
            # Missing COL_B_status, COL_B_message
        },
        index=[0],
    )

    # Expected state update only for COL_A
    expected_new_states = {
        (0, 0): CellFullState(
            validation_status=CellState.INVALID,
            error_details="Error A1",
            correction_suggestions=[],
        )
    }
    # Mock the default state (NORMAL)
    mock_state_manager.get_full_cell_state.return_value = CellFullState(
        validation_status=CellState.NORMAL, error_details="", correction_suggestions=[]
    )

    # Emit the signal
    mock_validation_service.validation_complete.emit(test_status_df)

    # Assert update_states was called only with the state for COL_A
    mock_state_manager.update_states.assert_called_once_with(expected_new_states)


def test_validation_complete_handles_nan_status(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that NaN status values are treated as NOT_VALIDATED."""
    # Prepare status_df with NaN status
    test_status_df = pd.DataFrame(
        {
            "COL_A_status": [None],  # Use None for NaN in creation
            "COL_A_message": ["Some message"],
            "COL_B_status": [ValidationStatus.VALID],
            "COL_B_message": [""],
        },
        index=[0],
    )
    test_status_df["COL_A_status"] = test_status_df["COL_A_status"].astype(
        object
    )  # Ensure correct dtype for None

    # Expected state for COL_A should be NORMAL (mapped from NaN/None)
    expected_new_states = {
        (0, 0): CellFullState(
            validation_status=CellState.NORMAL,  # Mapped from None
            error_details="Some message",  # Message should still be preserved
            correction_suggestions=[],
        ),
        (0, 1): CellFullState(
            validation_status=CellState.VALID,
            error_details="",
            correction_suggestions=[],
        ),
    }
    # Mock the default state (can be anything other than NORMAL for this test)
    mock_state_manager.get_full_cell_state.return_value = CellFullState(
        validation_status=CellState.INVALID, error_details="OldError", correction_suggestions=[]
    )

    # Emit the signal
    mock_validation_service.validation_complete.emit(test_status_df)

    # Assert update_states was called with the expected states
    mock_state_manager.update_states.assert_called_once_with(expected_new_states)


def test_validation_complete_handles_invalid_row_status(
    validation_adapter: ValidationAdapter,
    mock_validation_service: MockValidationService,
    mock_state_manager: MagicMock,
):
    """Test that INVALID_ROW status is mapped to CellState.INVALID."""
    test_status_df = pd.DataFrame(
        {
            "COL_A_status": [ValidationStatus.INVALID_ROW],
            "COL_A_message": ["Row level error"],
            "COL_B_status": [ValidationStatus.VALID],
            "COL_B_message": [""],
        },
        index=[0],
    )

    expected_new_states = {
        (0, 0): CellFullState(
            validation_status=CellState.INVALID,  # Mapped from INVALID_ROW
            error_details="Row level error",
            correction_suggestions=[],
        ),
        (0, 1): CellFullState(
            validation_status=CellState.VALID,
            error_details="",
            correction_suggestions=[],
        ),
    }
    mock_state_manager.get_full_cell_state.return_value = CellFullState(
        validation_status=CellState.NORMAL, error_details="", correction_suggestions=[]
    )

    mock_validation_service.validation_complete.emit(test_status_df)
    mock_state_manager.update_states.assert_called_once_with(expected_new_states)


# Removed tests related to the old _process_validation_results method
# Removed: test_process_validation_results_logic
# Removed: test_process_validation_results_empty_df
# Removed: test_process_validation_results_missing_column
