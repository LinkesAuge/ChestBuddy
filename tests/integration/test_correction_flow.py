"""
Integration tests for the data correction flow.

Verifies the interaction between CorrectionService, CorrectionAdapter,
TableStateManager, and DataViewModel.
"""

import pytest
import pandas as pd
import logging
from unittest.mock import MagicMock, patch
from typing import Dict, Tuple
import numpy as np

# Qt imports
from PySide6.QtCore import QObject, Signal, QModelIndex, Qt
from PySide6.QtTest import QSignalSpy

# Core components
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService, CorrectionService
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.utils.config import ConfigManager
from chestbuddy.core.models.correction_rule import CorrectionRule

# UI components
from chestbuddy.ui.data.adapters import ValidationAdapter, CorrectionAdapter
from chestbuddy.ui.data.models.data_view_model import DataViewModel
# Assuming CorrectionSuggestion might be defined elsewhere or mocked if needed
# from chestbuddy.core.models.correction_models import CorrectionSuggestion

# Import ValidationStatus enum
from chestbuddy.core.enums.validation_enums import ValidationStatus

from chestbuddy.ui.data.delegates.correction_delegate import (
    CorrectionDelegate,
    CorrectionSuggestion,
)  # Add Delegate
from chestbuddy.core.controllers.correction_controller import CorrectionController  # Add Controller
from chestbuddy.core.controllers.data_view_controller import (
    DataViewController,
)  # Add DataViewController
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.utils.signal_manager import SignalManager  # Import SignalManager

# Setup logging for tests
logger = logging.getLogger(__name__)

# pytestmark = pytest.mark.skip(reason="Integration tests are broken due to mocking/terminal issues")

# --- Fixtures ---


# TODO: Consider refactoring the fixture from test_validation_flow into a shared conftest.py
@pytest.fixture(scope="function")
def integration_system_fixture(qapp):  # Renamed and simplified data source
    """Sets up the integrated components for testing data flows."""
    logger.info("Setting up integration_system_fixture...")

    # 1. Config Manager (minimal mock)
    config_manager = MagicMock(spec=ConfigManager)
    config_manager.get = MagicMock(
        side_effect=lambda section, key, default=None: {
            ("Validation", "validation_lists_dir"): None,
            ("Validation", "case_sensitive"): False,
            ("Validation", "validate_on_import"): True,
            ("Validation", "auto_save"): True,
            ("Correction", "rules_file"): None,  # Add correction config if needed
        }.get((section, key), default)
    )
    config_manager.get_bool = MagicMock(
        side_effect=lambda section, key, default=None: {
            ("Validation", "case_sensitive"): False,
            ("Validation", "validate_on_import"): True,
            ("Validation", "auto_save"): True,
        }.get((section, key), default)
    )

    # 2. Data Model (Simple initial data)
    initial_data = pd.DataFrame(
        {"Player": ["Player1", "JohnSmiht"], "Chest": ["Gold", "siver"], "Score": [100, 200]}
    )
    data_model = ChestDataModel()
    data_model.update_data(initial_data)

    # Disable signal throttling for testing
    data_model._emission_rate_limit_ms = 0
    logger.info("Disabled ChestDataModel signal throttling for fixture.")

    # 3. Validation Service
    validation_service = ValidationService(data_model, config_manager)

    # 4. Correction Service
    correction_service = CorrectionService(data_model, config_manager)
    validation_service.set_correction_service(correction_service)

    # 5. DataViewModel (Create first, can use data_model or temp state manager initially)
    # Initialize with a temporary state manager first, or modify if ViewModel can handle None state_manager
    temp_state_manager = TableStateManager(
        data_model
    )  # This still causes the warning, but we replace it
    data_view_model = DataViewModel(data_model, temp_state_manager)
    logger.info("Created initial DataViewModel.")

    # 6. TableStateManager (Initialize with the DataViewModel to get correct headers)
    state_manager = TableStateManager(data_view_model)
    correction_service.set_state_manager(state_manager)
    logger.info("Created TableStateManager with DataViewModel.")

    # Update DataViewModel to use the correctly initialized state manager
    data_view_model.set_table_state_manager(state_manager)
    logger.info("Updated DataViewModel with correct TableStateManager.")

    # 7. Adapters (Use the correctly initialized state_manager)
    validation_adapter = ValidationAdapter(validation_service, state_manager)
    correction_adapter = CorrectionAdapter(correction_service, state_manager)

    # 8. DataViewController (Create and configure)
    mock_signal_manager = MagicMock(spec=SignalManager)
    data_view_controller = DataViewController(
        data_model=data_model, signal_manager=mock_signal_manager
    )
    # Set services on the controller
    data_view_controller.set_services(
        validation_service=validation_service, correction_service=correction_service
    )
    logger.info("Created and configured DataViewController.")

    # Return all components
    system = {
        "config_manager": config_manager,
        "data_model": data_model,
        "validation_service": validation_service,
        "correction_service": correction_service,
        "state_manager": state_manager,
        "data_view_model": data_view_model,
        "validation_adapter": validation_adapter,
        "correction_adapter": correction_adapter,
        "data_view_controller": data_view_controller,
        "logger": logger,
    }

    # Connect signals *after* all components are created
    try:
        # Validation Flow Connections
        validation_service.validation_complete.connect(validation_adapter._on_validation_complete)
        state_manager.state_changed.connect(data_view_model._on_state_manager_state_changed)
        # Correction Flow Connections
        correction_service.correction_suggestions_available.connect(
            correction_adapter._on_corrections_available
        )
        # Data Model Connection (if needed by adapters directly, otherwise handled by view model)
        # data_model.data_changed.connect(...)
        logger.info("Signals connected in fixture.")
    except Exception as e:
        logger.error(f"Error connecting signals in fixture: {e}")

    yield system

    # Teardown
    logger.info("Tearing down integration_system_fixture...")
    try:
        validation_adapter.disconnect_signals()
    except Exception as e:
        logger.error(f"Error disconnecting validation_adapter: {e}")
    try:
        correction_adapter.disconnect_signals()
    except Exception as e:
        logger.error(f"Error disconnecting correction_adapter: {e}")
    logger.info("Fixture teardown complete.")


# --- Test Class ---


class TestCorrectionFlowIntegration:
    """Tests the integration of the data correction flow."""

    def test_correction_suggestion_updates_state(self, integration_system_fixture, qtbot):
        """
        Test that emitting correction_available from CorrectionService updates
        the TableStateManager and DataViewModel correctly.
        """
        # Arrange
        correction_service = integration_system_fixture["correction_service"]
        state_manager = integration_system_fixture["state_manager"]
        view_model = integration_system_fixture["data_view_model"]
        validation_service = integration_system_fixture["validation_service"]
        data_model = integration_system_fixture["data_model"]

        # Define correction suggestions for specific cells
        # Row 1, Col 0 ('JohnSmiht') and Row 1, Col 1 ('siver')
        corrections_payload = {
            (1, 0): [{"original": "JohnSmiht", "corrected": "John Smith", "confidence": 0.9}],
            (1, 1): [{"original": "siver", "corrected": "Silver", "confidence": 0.85}],
        }

        # Spies for signals
        suggestion_spy = QSignalSpy(correction_service.correction_suggestions_available)
        state_change_spy = QSignalSpy(state_manager.state_changed)
        model_data_changed_spy = QSignalSpy(view_model.dataChanged)

        assert state_change_spy.isValid()
        assert model_data_changed_spy.isValid()

        # Act:
        # 1. Run validation first - Let the real validation run to set initial state
        logger.info("Running validation service to set initial state...")
        validation_results = (
            validation_service.validate_data()
        )  # Result not needed here, just run it
        logger.info(f"Validation results (for context): {validation_results}")

        # ... (Keep assertions checking initial validation results if desired, or remove) ...

        # 2. Call the method that finds suggestions based on the actual validation state
        logger.info("Calling find_and_emit_suggestions (will use actual validation status)...")
        correction_service.find_and_emit_suggestions()

        # Assert: Wait for signals
        assert suggestion_spy.wait(1000), (
            "CorrectionService did not emit correction_suggestions_available"
        )
        logger.info("CorrectionService emitted correction_suggestions_available signal.")

        # Further assertions: Check if state_manager and view_model were updated
        assert state_change_spy.wait(1000), "TableStateManager did not emit state_changed"
        # Check specific cell states (should now be CORRECTABLE)
        assert state_manager.get_cell_state(1, 0) == ValidationStatus.CORRECTABLE
        assert state_manager.get_cell_state(1, 1) == ValidationStatus.CORRECTABLE

        assert model_data_changed_spy.wait(1000), "DataViewModel did not emit dataChanged"
        # Check model roles reflect the correctable state
        assert (
            view_model.data(view_model.index(1, 0), DataViewModel.ValidationStateRole)
            == ValidationStatus.CORRECTABLE
        )
        assert (
            view_model.data(view_model.index(1, 1), DataViewModel.ValidationStateRole)
            == ValidationStatus.CORRECTABLE
        )

    # TODO: Add test_correction_application_updates_state
    def test_correction_application_updates_state(self, integration_system_fixture, qtbot):
        """
        Test that applying a correction updates the data model and cell state.
        """
        # Arrange
        correction_service = integration_system_fixture["correction_service"]
        state_manager = integration_system_fixture["state_manager"]
        view_model = integration_system_fixture["data_view_model"]
        data_model = integration_system_fixture["data_model"]
        validation_service = integration_system_fixture["validation_service"]

        # Cell to correct: Row 1, Col 0 ('JohnSmiht')
        test_row, test_col = 1, 0
        target_column = "PLAYER"  # Use uppercase column name
        original_value = "JohnSmiht"
        corrected_value = "John Smith"

        # --- Optional: Mark cell as correctable first for a more realistic scenario ---
        # 1. Add a rule that would trigger a suggestion for this cell
        # (Rule setup remains the same)
        rule_manager = getattr(correction_service, "_rule_manager", None)
        assert rule_manager is not None
        rule = CorrectionRule(
            from_value=original_value, to_value=corrected_value, category="player", status="enabled"
        )
        rule_manager.add_rule(rule)

        # 2. Run Validation first to populate initial state
        logger.info("Running validation to populate initial state...")
        state_change_spy_validation = QSignalSpy(
            state_manager.state_changed
        )  # Spy for validation update
        validation_service.validate_data()
        # --- Add processEvents to try and fix spy --- #
        qtbot.processEvents()
        # -------------------------------------------- #
        # Explicitly check the return value of wait()
        validation_signal_received = state_change_spy_validation.wait(2000)  # Increased timeout
        assert validation_signal_received, (
            "State manager state_changed signal NOT received after validation"
        )
        logger.info("Initial validation ran and state_changed signal received from state manager.")

        # 3. Run suggestion finding to update state manager
        logger.info("Finding suggestions to mark cell as correctable...")
        # Spy for the state change specifically from suggestion finding
        state_change_spy_suggestion = QSignalSpy(state_manager.state_changed)
        correction_service.find_and_emit_suggestions()
        # Wait for the state_changed signal resulting from suggestions
        assert state_change_spy_suggestion.wait(1000), (
            "State manager not updated after suggestion finding"
        )
        # Now check if the cell is correctable
        assert state_manager.get_cell_state(test_row, test_col) == ValidationStatus.CORRECTABLE, (
            "Cell not marked as correctable before test act phase"
        )
        logger.info("Cell successfully marked as CORRECTABLE.")
        # -------------------------------------------------------------------------

        # Spies for state changes AFTER the correction action
        state_change_spy_correction = QSignalSpy(
            state_manager.state_changed
        )  # New spy for correction update
        model_data_changed_spy = QSignalSpy(view_model.dataChanged)
        assert state_change_spy_correction.isValid()  # Check validity of the new spy
        assert model_data_changed_spy.isValid()

        # Prepare for ACT phase: Create index and suggestion object
        test_index = view_model.index(test_row, test_col)
        assert test_index.isValid()
        test_suggestion = CorrectionSuggestion(original_value, corrected_value)

        # Act: Apply the correction using the service directly
        # Option 1: Use apply_single_rule (if appropriate)
        logger.info(f"Applying mock rule: {rule.from_value} -> {rule.to_value}")
        correction_stats = correction_service.apply_single_rule(rule, only_invalid=False)
        logger.info(f"Correction stats: {correction_stats}")

        # Option 2: Call a method on CorrectionAdapter if it exists and is intended for this?
        # adapter = integration_system_fixture["correction_adapter"]
        # adapter.apply_correction(test_row, test_col, corrected_value) # Fictional method

        qtbot.wait(500)  # Increased wait time for signals after single correction

        # Assert
        # 1. Data Model Updated
        assert data_model.get_cell_value(test_row, target_column) == corrected_value, (
            f"Data model not updated. Expected {corrected_value}, got {data_model.get_cell_value(test_row, target_column)}"
        )

        # 2. TableStateManager State Updated
        # Check if state_changed signal was emitted for the corrected cell
        assert state_change_spy_correction.wait(1000), (
            "TableStateManager did not emit state_changed after correction"
        )
        emitted_indices = set().union(
            *[args[0] for args in state_change_spy_correction]
        )  # Combine all emitted sets
        assert (test_row, test_col) in emitted_indices, (
            "state_changed signal did not include the corrected cell"
        )

        # Check the actual state (should ideally be VALID or CORRECTED, depending on design)
        final_state = state_manager.get_full_cell_state(test_row, test_col)
        assert final_state is not None, "Cell state not found after correction"
        # Assuming correction implies validity or a specific 'CORRECTED' state
        assert final_state.validation_status in (
            ValidationStatus.VALID,
            CellState.CORRECTED,
            CellState.NORMAL,
        ), f"Expected VALID/CORRECTED/NORMAL state, got {final_state.validation_status}"
        # Check if suggestions are cleared (design decision)
        # assert not final_state.correction_suggestions

        # 3. DataViewModel Updated
        assert model_data_changed_spy.wait(1000), (
            "DataViewModel did not emit dataChanged after correction"
        )
        # Verify the model reflects the change via DisplayRole and ValidationStateRole
        test_index = view_model.index(test_row, test_col)
        assert view_model.data(test_index, Qt.DisplayRole) == corrected_value
        model_validation_state = view_model.data(test_index, DataViewModel.ValidationStateRole)
        assert model_validation_state in (
            ValidationStatus.VALID,
            CellState.CORRECTED,
            CellState.NORMAL,
        ), f"ViewModel has wrong validation state: {model_validation_state}"

    # TODO: Add test_batch_correction
    def test_batch_correction(self, integration_system_fixture, qtbot):
        """
        Test that applying corrections in batch updates multiple cells.
        """
        # Arrange
        correction_service = integration_system_fixture["correction_service"]
        state_manager = integration_system_fixture["state_manager"]
        data_model = integration_system_fixture["data_model"]
        view_model = integration_system_fixture["data_view_model"]

        # Define multiple potential corrections based on initial data
        # Cell 1: Row 1, Col 0 ('JohnSmiht' -> 'John Smith')
        # Cell 2: Row 1, Col 1 ('siver' -> 'Silver')
        cell1_rc = (1, 0)
        cell2_rc = (1, 1)
        corrected_val1 = "John Smith"
        corrected_val2 = "Silver"

        # Add mock rules to the rule manager used by the service
        # We need access to the rule manager instance
        rule_manager = getattr(correction_service, "_rule_manager", None)
        assert rule_manager is not None, "Could not access RuleManager in CorrectionService"

        rule1 = CorrectionRule(
            from_value="JohnSmiht", to_value=corrected_val1, category="player", status="enabled"
        )
        rule2 = CorrectionRule(
            from_value="siver", to_value=corrected_val2, category="chest", status="enabled"
        )
        rule_manager.add_rule(rule1)
        rule_manager.add_rule(rule2)

        # Pre-assert original values
        assert data_model.get_cell_value(cell1_rc[0], "PLAYER") == "JohnSmiht"
        assert data_model.get_cell_value(cell2_rc[0], "CHEST") == "siver"

        # Spies
        state_change_spy = QSignalSpy(state_manager.state_changed)
        model_data_changed_spy = QSignalSpy(view_model.dataChanged)
        # Optional: Spy on data_model.data_changed if needed
        # data_model_spy = QSignalSpy(data_model.data_changed)

        # Act: Apply corrections using the service's batch method
        # Option 1: apply_corrections (applies *all* enabled rules)
        logger.info("Applying batch corrections (all enabled rules)...")
        batch_stats = correction_service.apply_corrections(
            only_invalid=False
        )  # Apply to all matches
        logger.info(f"Batch correction stats: {batch_stats}")

        qtbot.wait(500)  # Increased wait time for signals after batch correction

        # Assert
        # 1. Stats Verification
        assert batch_stats["total_corrections"] == 2
        assert batch_stats["corrected_cells"] == 2

        # 2. Data Model Updated
        assert data_model.get_cell_value(cell1_rc[0], "PLAYER") == corrected_val1
        assert data_model.get_cell_value(cell2_rc[0], "CHEST") == corrected_val2

        # 3. TableStateManager State Updated
        assert state_change_spy.wait(1000), (
            "TableStateManager did not emit state_changed after batch correction"
        )
        emitted_indices = set().union(*[args[0] for args in state_change_spy])
        assert cell1_rc in emitted_indices
        assert cell2_rc in emitted_indices

        # Check final states (should be reset/valid)
        final_state1 = state_manager.get_full_cell_state(cell1_rc[0], cell1_rc[1])
        assert final_state1 is None or final_state1.validation_status in (
            ValidationStatus.VALID,
            CellState.NORMAL,
        )

        final_state2 = state_manager.get_full_cell_state(cell2_rc[0], cell2_rc[1])
        assert final_state2 is None or final_state2.validation_status in (
            ValidationStatus.VALID,
            CellState.NORMAL,
        )

        # 4. DataViewModel Updated
        assert model_data_changed_spy.wait(1000), (
            "DataViewModel did not emit dataChanged after batch correction"
        )
        # Verify display roles
        assert (
            view_model.data(view_model.index(cell1_rc[0], cell1_rc[1]), Qt.DisplayRole)
            == corrected_val1
        )
        assert (
            view_model.data(view_model.index(cell2_rc[0], cell2_rc[1]), Qt.DisplayRole)
            == corrected_val2
        )
        # Verify state roles
        state_role1 = view_model.data(
            view_model.index(cell1_rc[0], cell1_rc[1]), DataViewModel.ValidationStateRole
        )
        assert state_role1 in (ValidationStatus.VALID, CellState.NORMAL)
        state_role2 = view_model.data(
            view_model.index(cell2_rc[0], cell2_rc[1]), DataViewModel.ValidationStateRole
        )
        assert state_role2 in (ValidationStatus.VALID, CellState.NORMAL)

    def test_delegate_signal_triggers_controller_and_service(
        self, integration_system_fixture, qtbot, mocker
    ):
        """
        Test that CorrectionDelegate.correction_selected signal triggers
        CorrectionController.apply_correction_from_ui slot, which in turn calls
        CorrectionService.apply_ui_correction.
        """
        # Arrange: Get necessary components from fixture
        correction_service = integration_system_fixture["correction_service"]
        rule_manager = getattr(correction_service, "_rule_manager", None)
        config_manager = integration_system_fixture["config_manager"]
        validation_service = integration_system_fixture["validation_service"]
        view_model = integration_system_fixture["data_view_model"]
        logger = integration_system_fixture["logger"]

        # Arrange: Mock the NEW service method we want to verify
        mock_service_apply_ui = mocker.patch.object(
            correction_service,
            "apply_ui_correction",  # Use the correct method name
            autospec=True,
            return_value=True,  # Assume success
        )

        # Arrange: Create a REAL CorrectionController instance
        real_correction_controller = CorrectionController(
            correction_service=correction_service,
            rule_manager=rule_manager,
            config_manager=config_manager,
            validation_service=validation_service,
        )

        # Arrange: Spy on the REAL controller's slot
        spy_apply_slot = mocker.spy(real_correction_controller, "apply_correction_from_ui")

        # Arrange: Mock CorrectionDelegate & Simulate Signal Connection/Emission
        mock_delegate = MagicMock(spec=CorrectionDelegate)

        # --- Custom Signal Simulation ---
        connected_slots = []

        def mock_connect(slot):
            print(f"Mock Connect: Capturing slot {slot}")  # Debug
            connected_slots.append(slot)

        def mock_emit(*args):
            print(f"Mock Emit: Emitting with args {args}")  # Debug
            print(f"Mock Emit: Calling {len(connected_slots)} connected slots")  # Debug
            for slot in connected_slots:
                try:
                    print(f"Mock Emit: Calling slot {slot}")  # Debug
                    slot(*args)  # Call the connected slot
                except Exception as e:
                    print(f"Mock Emit: Error calling slot {slot}: {e}")  # Debug
                    pytest.fail(f"Error calling connected slot {slot}: {e}")

        # Assign custom methods to a mock signal attribute
        mock_signal = MagicMock()
        mock_signal.connect = mock_connect
        mock_signal.emit = mock_emit
        mock_delegate.correction_selected = mock_signal
        # --- End Custom Signal Simulation ---

        # Arrange: Connect the REAL controller slot using the custom mock connect
        try:
            mock_delegate.correction_selected.connect(
                real_correction_controller.apply_correction_from_ui
            )
            assert len(connected_slots) == 1, "Slot was not captured by mock connect"
            logger.info("Successfully connected REAL controller slot via mock connect.")
        except Exception as e:
            pytest.fail(f"Failed to connect mock signal/real slot: {e}")

        # Arrange: Define data for signal emission
        target_row = 1
        target_col = 0  # 'JohnSmiht'
        target_index = view_model.index(target_row, target_col)
        assert target_index.isValid(), "Target index for test is invalid"
        target_suggestion = CorrectionSuggestion("JohnSmiht", "John Smith")
        expected_corrected_value = target_suggestion.corrected_value

        # Act: Emit the mock delegate's signal using the custom mock emit
        logger.info(
            f"Emitting mock correction_selected signal for index ({target_index.row()},{target_index.column()})"
        )
        mock_delegate.correction_selected.emit(target_index, target_suggestion)
        # No qtbot.wait should be needed as the call is now direct

        # Assert 1: Check if the REAL controller's slot (spied) was called
        try:
            spy_apply_slot.assert_called_once()
            logger.info("Real apply_correction_from_ui slot was called.")
        except AssertionError as e:
            pytest.fail(f"Real apply_correction_from_ui slot was not called: {e}")

        # Assert 2: Check the arguments received by the spied slot
        # ... (optional checks for slot args as before) ...

        # Assert 3: Check if the MOCKED service method was called by the controller's slot
        try:
            mock_service_apply_ui.assert_called_once()
            logger.info("Mocked correction_service.apply_ui_correction was called.")
        except AssertionError as e:
            pytest.fail(f"Mocked service method apply_ui_correction was not called: {e}")

        # Assert 4: Check arguments passed to the MOCKED service method
        service_call_args = mock_service_apply_ui.call_args[0]
        assert len(service_call_args) == 3, (
            f"Expected 3 args for service call, got {len(service_call_args)}"
        )
        service_row = service_call_args[0]
        service_col = service_call_args[1]
        service_value = service_call_args[2]
        assert service_row == target_row, "Service called with wrong row"
        assert service_col == target_col, "Service called with wrong column"
        assert service_value == expected_corrected_value, "Service called with wrong value"
        logger.info("Mocked service method apply_ui_correction received correct arguments.")

    # --- New Test for Correction Application Trigger --- #
    def test_correction_action_triggers_service_call(self, integration_system_fixture, qtbot):
        """
        Test that the view's correction_action_triggered signal (simulated by calling the
        controller's slot) results in a call to CorrectionService.apply_ui_correction.
        """
        # Arrange
        controller = integration_system_fixture["data_view_controller"]
        correction_service = integration_system_fixture["correction_service"]
        view_model = integration_system_fixture["data_view_model"]
        logger = integration_system_fixture["logger"]

        # Ensure services are set on the controller (redundant if fixture guarantees it, but safe)
        if not hasattr(controller, "_correction_service") or not controller._correction_service:
            controller.set_services(correction_service=correction_service)

        # Mock the target service method
        with patch.object(
            correction_service, "apply_ui_correction", return_value=True
        ) as mock_apply_correction:
            # Create a valid source model index
            # Use row 1, col 0 ('JohnSmiht' in the fixture data)
            test_row, test_col = 1, 0
            source_index = view_model.index(test_row, test_col)
            assert source_index.isValid()

            # Create a sample suggestion object (mimic what delegate provides)
            test_corrected_value = "John Smith"
            # Use the structure expected by the delegate/adapter if known,
            # otherwise ensure it has 'corrected_value'
            suggestion = type("MockSuggestion", (), {"corrected_value": test_corrected_value})()

            logger.info(
                f"Simulating correction action trigger for index ({test_row}, {test_col}) -> '{test_corrected_value}'"
            )

            # Act: Call the controller's slot directly, simulating the signal connection
            controller._handle_correction_action_triggered(source_index, suggestion)

            # Assert: Check if the mocked service method was called correctly
            logger.info("Checking if CorrectionService.apply_ui_correction was called...")
            mock_apply_correction.assert_called_once_with(test_row, test_col, test_corrected_value)
            logger.info("Assertion passed: apply_ui_correction called correctly.")

    # ----------------------------------------------------- #

    # TODO: Add test_correction_application_updates_state


# Ensure the file ends without trailing syntax errors
