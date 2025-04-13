"""
Integration tests for the full data validation flow.

Verifies interaction between DataModel, ValidationService, ValidationAdapter,
TableStateManager, and DataViewModel.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock
import logging

from PySide6.QtCore import QObject, Signal, QModelIndex
from PySide6.QtTest import QSignalSpy

# Core Components
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService, CorrectionService
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState
from chestbuddy.core.enums.validation_enums import (
    ValidationStatus,
)  # Ensure this matches CellState if used interchangeably

# UI Components / Adapters
from chestbuddy.ui.data.adapters.validation_adapter import ValidationAdapter
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.ui.data.delegates.correction_delegate import CorrectionSuggestion
from chestbuddy.ui.data.adapters.correction_adapter import CorrectionAdapter

# Utils
from chestbuddy.utils.config import ConfigManager


# --- Fixtures ---


@pytest.fixture(scope="function")  # Use function scope for isolation
def test_data_simple():
    """Provides a simple DataFrame for validation tests."""
    return pd.DataFrame(
        {
            "Player": ["Player1", "Player2", "Player3"],
            "Chest": ["Gold", "Silver", "BadChest"],  # One invalid
            "Score": [100, "abc", 300],  # One invalid
        }
    )


@pytest.fixture(scope="function")
def validation_flow_system(test_data_simple, qapp):
    """Sets up the integrated components for validation flow testing."""
    logger = logging.getLogger(__name__)

    # 1. Config Manager (minimal mock)
    config_manager = MagicMock(spec=ConfigManager)

    # Mock necessary config methods used by ValidationService
    config_manager.get = MagicMock(
        side_effect=lambda section, key, default=None: {
            ("Validation", "validation_lists_dir"): None,  # Ensure fallback path is used
            ("Validation", "case_sensitive"): False,  # Default
            ("Validation", "validate_on_import"): True,  # Default
            ("Validation", "auto_save"): True,  # Default
        }.get((section, key), default)
    )

    # Mock get_bool as well, since it might be called directly
    config_manager.get_bool = MagicMock(
        side_effect=lambda section, key, default=None: {
            ("Validation", "case_sensitive"): False,  # Default
            ("Validation", "validate_on_import"): True,  # Default
            ("Validation", "auto_save"): True,  # Default
        }.get((section, key), default)
    )

    # 2. Data Model
    data_model = ChestDataModel()
    data_model.update_data(test_data_simple)

    # 3. Validation Service
    validation_service = ValidationService(data_model, config_manager)

    # 4. Correction Service
    correction_service = CorrectionService(data_model, config_manager)
    validation_service.set_correction_service(correction_service)

    # --- Instantiation Order Change ---
    # 5. Data View Model (Acts as the Qt model source)
    # This needs state_manager, but state_manager needs a model for headers...
    # Let's create state_manager FIRST, but pass the view_model to it later if needed?
    # No, init state_manager with the model that PROVIDES the headers correctly.

    # Create a temporary bare state_manager first, just for the ViewModel init
    temp_state_manager = TableStateManager(data_model)  # Will have empty headers
    data_view_model = DataViewModel(data_model, temp_state_manager)

    # NOW create the *real* state manager, initializing it with the DataViewModel
    # so its _create_headers_map uses the correct headerData method.
    state_manager = TableStateManager(data_view_model)

    # Update the view_model to use the correctly initialized state_manager
    data_view_model.set_table_state_manager(state_manager)
    logger.info("Initialized TableStateManager with DataViewModel for correct headers.")
    # ----------------------------------

    # 6. Validation Adapter (Now uses the correctly initialized state_manager)
    validation_adapter = ValidationAdapter(validation_service, state_manager)

    # 7. Correction Adapter
    correction_adapter = CorrectionAdapter(correction_service, state_manager)

    # Remove the manual header update block as it's no longer needed
    # if hasattr(state_manager, '_data_model') ...

    # Return all components for the test
    system = {
        "config_manager": config_manager,
        "data_model": data_model,
        "validation_service": validation_service,
        "correction_service": correction_service,
        "state_manager": state_manager,  # Return the *real* one
        "data_view_model": data_view_model,
        "validation_adapter": validation_adapter,
        "correction_adapter": correction_adapter,
    }

    # Connect signals between components *after* all are created
    # ... (signal connections remain the same)

    yield system  # Use yield for setup/teardown

    # Teardown: Disconnect signals or clean up if necessary
    # (Example, adapt as needed for your components)
    try:
        validation_adapter.disconnect_signals()
    except Exception as e:
        logger.error(f"Error disconnecting validation_adapter: {e}")
    try:
        correction_adapter.disconnect_signals()
    except Exception as e:
        logger.error(f"Error disconnecting correction_adapter: {e}")


# --- Test Class ---


class TestValidationFlowIntegration:
    """Tests the integration of the validation data flow."""

    def test_invalid_data_updates_state_and_model(self, validation_flow_system, qtbot):
        """
        Test that running validation on invalid data correctly updates
        TableStateManager and DataViewModel.
        """
        # Arrange: Get components from fixture
        service = validation_flow_system["validation_service"]
        state_manager = validation_flow_system["state_manager"]
        view_model = validation_flow_system["data_view_model"]

        # Spies for signals
        state_change_spy = QSignalSpy(state_manager.state_changed)
        model_data_changed_spy = QSignalSpy(view_model.dataChanged)

        assert state_change_spy.isValid()
        assert model_data_changed_spy.isValid()

        # Act: Trigger validation using the correct method name
        service.validate_data()

        # Assert: Wait for signals and verify state
        # 1. ValidationService signal processing (implicitly checked by downstream effects)

        # 2. TableStateManager emitted signal
        assert state_change_spy.wait(1000), "TableStateManager did not emit state_changed"
        assert len(state_change_spy) >= 1  # Can emit multiple times for diff cells

        # 3. DataViewModel emitted dataChanged signal
        # Check if dataChanged was emitted for the specific invalid cells
        assert model_data_changed_spy.wait(1000), "DataViewModel did not emit dataChanged"
        assert len(model_data_changed_spy) >= 1

        # Verify state manager has the correct states (based on test_data_simple)
        # Row 1, Col 2 ('Score': 'abc') should be INVALID
        assert state_manager.get_cell_state(1, 2) == ValidationStatus.INVALID
        # Row 2, Col 1 ('Chest': 'BadChest') should be INVALID
        assert state_manager.get_cell_state(2, 1) == ValidationStatus.INVALID
        # Example: Row 0, Col 0 ('Player': 'Player1') should be VALID
        assert state_manager.get_cell_state(0, 0) == ValidationStatus.VALID

        # Verify view_model reflects the state changes (e.g., through roles)
        invalid_score_index = view_model.index(1, 2)
        invalid_score_state = view_model.data(
            invalid_score_index, DataViewModel.ValidationStateRole
        )
        assert invalid_score_state == ValidationStatus.INVALID

        invalid_chest_index = view_model.index(2, 1)
        invalid_chest_state = view_model.data(
            invalid_chest_index, DataViewModel.ValidationStateRole
        )
        assert invalid_chest_state == ValidationStatus.INVALID

        valid_index = view_model.index(0, 0)
        valid_state = view_model.data(valid_index, DataViewModel.ValidationStateRole)
        assert valid_state == ValidationStatus.VALID

    def test_validation_preserves_correction_state(self, validation_flow_system, qtbot):
        """
        Test that validation updates status but preserves existing correction suggestions.
        """
        # Arrange: Get components
        service = validation_flow_system["validation_service"]
        state_manager = validation_flow_system["state_manager"]
        view_model = validation_flow_system["data_view_model"]
        data_model = validation_flow_system["data_model"]

        # Target cell - Player1 (should become VALID)
        test_row, test_col = 0, 0
        test_index = view_model.index(test_row, test_col)  # Correct: Get index from the view model

        # Create mock suggestion and initial state
        mock_suggestion = MagicMock(spec=CorrectionSuggestion)
        mock_suggestion.corrected_value = "Suggestion1"
        initial_full_state = CellFullState(
            validation_status=CellState.CORRECTABLE,  # Start as correctable
            correction_suggestions=[mock_suggestion],
            error_details="Initial Test Detail",
        )

        # Manually set initial state in state manager
        state_manager.update_states({(test_row, test_col): initial_full_state})

        # Verify initial state
        retrieved_initial_state = state_manager.get_full_cell_state(test_row, test_col)
        assert retrieved_initial_state is not None
        assert retrieved_initial_state.validation_status == CellState.CORRECTABLE
        assert retrieved_initial_state.correction_suggestions == [mock_suggestion]
        assert retrieved_initial_state.error_details == "Initial Test Detail"
        # Also check ViewModel initial state
        assert (
            view_model.data(test_index, DataViewModel.ValidationStateRole) == CellState.CORRECTABLE
        )
        assert view_model.data(test_index, DataViewModel.CorrectionSuggestionsRole) == [
            mock_suggestion
        ]

        # Spies for signals
        state_change_spy = QSignalSpy(state_manager.state_changed)
        model_data_changed_spy = QSignalSpy(view_model.dataChanged)

        # Act: Trigger validation (Player1 should be VALID)
        service.validate_data()

        # Assert: Wait for signals
        assert state_change_spy.wait(1000), "TableStateManager did not emit state_changed"
        assert model_data_changed_spy.wait(1000), "DataViewModel did not emit dataChanged"

        # Verify final state in TableStateManager
        final_full_state = state_manager.get_full_cell_state(test_row, test_col)
        assert final_full_state is not None, "Final state not found in state manager"
        # Status should be updated to VALID by the validation service run
        assert final_full_state.validation_status == CellState.VALID, (
            f"Expected final status VALID, got {final_full_state.validation_status}"
        )
        # Correction suggestions should be preserved
        assert final_full_state.correction_suggestions == [mock_suggestion], (
            "Correction suggestions were not preserved"
        )
        # Error details should likely be cleared or updated by validation service
        # Check based on ValidationAdapter._on_validation_complete logic
        # Current logic preserves details if status is set, so it should remain?
        # Let's assert it's None for now, assuming validation clears details on VALID.
        # This depends on the exact desired behavior of ValidationAdapter.update_states
        # Modify this assertion if needed based on adapter logic.
        assert final_full_state.error_details is None, (
            f"Expected error details to be cleared, got {final_full_state.error_details}"
        )

        # Verify final state exposed by DataViewModel
        assert view_model.data(test_index, DataViewModel.ValidationStateRole) == CellState.VALID
        assert view_model.data(test_index, DataViewModel.CorrectionSuggestionsRole) == [
            mock_suggestion
        ]

    # TODO: Add test_validation_preserves_correction_state
    # Setup: Manually set a CellFullState with correction suggestions in TableStateManager
    # Act: Run validation (ensure results only have VALID/INVALID status)
    # Assert: Check the updated CellFullState in TableStateManager - validation status
    #         should be updated, but correction_suggestions should remain untouched.
    pass  # Placeholder for future tests
