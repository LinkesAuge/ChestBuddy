"""
Integration tests for the refactored DataView correction flow.

Verifies the interaction between CorrectionDelegate, DataView, CorrectionAdapter,
and CorrectionService.
"""

import pytest
import pandas as pd
import logging
from unittest.mock import MagicMock, patch
from typing import Dict, Tuple, Any
import numpy as np

# Qt imports
from PySide6.QtCore import QObject, Signal, QModelIndex, Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

# Core components
from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService, CorrectionService
from chestbuddy.core.table_state_manager import TableStateManager, CellState, CellFullState
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.utils.config import ConfigManager

# UI components
from chestbuddy.ui.data.adapters import ValidationAdapter, CorrectionAdapter
from chestbuddy.ui.data.models.data_view_model import DataViewModel
from chestbuddy.ui.data.delegates.correction_delegate import (
    CorrectionDelegate,
    CorrectionSuggestion,
)
from chestbuddy.ui.data_view import DataView

# Setup logging for tests
logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def dataview_correction_system(qapp):
    """Sets up the integrated components for testing the refactored DataView correction flow."""
    logger.info("Setting up dataview_correction_system fixture...")

    # 1. Config Manager (minimal mock)
    config_manager = MagicMock(spec=ConfigManager)
    config_manager.get_bool = MagicMock(return_value=False)

    # 2. Data Model with sample data
    initial_data = pd.DataFrame(
        {"Player": ["Player1", "JohnSmiht"], "Chest": ["Gold", "siver"], "Score": [100, 200]}
    )
    data_model = ChestDataModel()
    data_model.update_data(initial_data)

    # 3. Services
    validation_service = ValidationService(data_model, config_manager)
    correction_service = CorrectionService(data_model, config_manager)

    # 4. Create the ViewModel and TableStateManager
    state_manager = TableStateManager(data_model)
    view_model = DataViewModel(data_model, state_manager)

    # 5. Create Adapters
    validation_adapter = ValidationAdapter(validation_service, state_manager)
    correction_adapter = CorrectionAdapter(correction_service, state_manager)

    # 6. Create DataView
    data_view = DataView(data_model)
    data_view.set_table_state_manager(state_manager)

    # 7. Create and set up the delegate
    delegate = CorrectionDelegate()

    # Return all components
    system = {
        "config_manager": config_manager,
        "data_model": data_model,
        "validation_service": validation_service,
        "correction_service": correction_service,
        "state_manager": state_manager,
        "view_model": view_model,
        "validation_adapter": validation_adapter,
        "correction_adapter": correction_adapter,
        "data_view": data_view,
        "delegate": delegate,
    }

    # Connect signals (these are the connections we want to test)
    delegate.correction_selected.connect(data_view._relay_correction_selected)
    data_view.correction_selected.connect(correction_adapter.apply_correction_from_ui)

    # Connect other required signals
    validation_service.validation_changed.connect(validation_adapter._on_validation_complete)
    correction_service.correction_suggestions_available.connect(
        correction_adapter._on_corrections_available
    )

    yield system

    # Teardown
    try:
        validation_adapter.disconnect_signals()
        correction_adapter.disconnect_signals()
    except Exception as e:
        logger.error(f"Error in fixture teardown: {e}")


class TestDataViewCorrectionFlow:
    """Tests for the refactored DataView correction flow."""

    def test_delegate_to_adapter_flow(self, dataview_correction_system, mocker):
        """
        Test that correction selections from the delegate flow through
        the DataView to the CorrectionAdapter and finally to the CorrectionService.
        """
        # Arrange
        delegate = dataview_correction_system["delegate"]
        data_view = dataview_correction_system["data_view"]
        correction_adapter = dataview_correction_system["correction_adapter"]
        correction_service = dataview_correction_system["correction_service"]

        # Mock the CorrectionService method to verify it gets called
        mock_apply_correction = mocker.patch.object(
            correction_service, "apply_ui_correction", return_value=True
        )

        # Create spies for the signals
        relay_spy = mocker.spy(data_view, "_relay_correction_selected")
        adapter_spy = mocker.spy(correction_adapter, "apply_correction_from_ui")

        # Test data
        row = 1
        col = 0
        suggestion = CorrectionSuggestion("JohnSmiht", "John Smith")

        # Act: Emit the delegate signal
        delegate.correction_selected.emit(row, col, suggestion)

        # Assert: The relay method should have been called
        relay_spy.assert_called_once_with(row, col, suggestion)

        # Assert: The adapter method should have been called
        adapter_spy.assert_called_once_with(row, col, suggestion)

        # Assert: The service method should have been called
        mock_apply_correction.assert_called_once_with(row, col, suggestion.corrected_value)

    def test_dataview_correction_selected_connects_to_adapter(
        self, dataview_correction_system, qtbot
    ):
        """
        Test that the DataView.correction_selected signal is properly connected to
        the CorrectionAdapter.apply_correction_from_ui method.
        """
        # Arrange
        data_view = dataview_correction_system["data_view"]
        correction_adapter = dataview_correction_system["correction_adapter"]

        # Spy on the adapter method
        spy = QSignalSpy(data_view.correction_selected)

        # Patch the adapter method to verify it gets called
        original_method = correction_adapter.apply_correction_from_ui
        called_args = []

        def capture_args(row, col, value):
            called_args.append((row, col, value))
            # Don't actually call the original, as it might modify the system state

        correction_adapter.apply_correction_from_ui = capture_args

        # Test data
        row = 1
        col = 0
        suggestion_value = "John Smith"

        # Act: Emit the DataView signal
        data_view.correction_selected.emit(row, col, suggestion_value)

        # Assert: The spy should have recorded the signal
        assert spy.count() == 1

        # Assert: The signal should have emitted the correct arguments
        signal_args = spy[0]
        assert signal_args[0] == row
        assert signal_args[1] == col
        assert signal_args[2] == suggestion_value

        # Assert: The adapter method should have been called with the right arguments
        assert len(called_args) == 1
        assert called_args[0] == (row, col, suggestion_value)

        # Restore the original method
        correction_adapter.apply_correction_from_ui = original_method
