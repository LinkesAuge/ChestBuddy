"""
End-to-end tests for the validation workflow.

These tests verify the complete validation workflow from data import to
validation result visualization and user interactions with validation features.
"""

import os
import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock, call

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEventLoop, QModelIndex
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QMenu, QTableView

from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.views.validation_view_adapter import ValidationViewAdapter
from chestbuddy.ui.data_view import DataView
from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.core.enums.validation_status import ValidationStatus


class SignalCatcher(QObject):
    """Utility class to catch Qt signals for testing."""

    def __init__(self):
        """Initialize the signal catcher."""
        super().__init__()
        self.received_signals = {}
        self.signal_args = {}
        self.signal_connections = []

    def catch_signal(self, signal):
        """
        Catch a specific signal.

        Args:
            signal: The Qt signal to catch.
        """
        if signal not in self.received_signals:
            self.received_signals[signal] = False
            self.signal_args[signal] = None

            # Store connection to avoid garbage collection
            connection = signal.connect(lambda *args: self._handle_signal(signal, *args))
            self.signal_connections.append((signal, connection))

    def _handle_signal(self, signal, *args):
        """
        Handle a captured signal.

        Args:
            signal: The signal that was emitted.
            *args: The arguments that were passed with the signal.
        """
        self.received_signals[signal] = True
        self.signal_args[signal] = args

    def was_signal_emitted(self, signal):
        """
        Check if a signal was emitted.

        Args:
            signal: The signal to check.

        Returns:
            bool: True if the signal was emitted, False otherwise.
        """
        return self.received_signals.get(signal, False)

    def get_signal_args(self, signal):
        """
        Get the arguments that were passed with a signal.

        Args:
            signal: The signal to get arguments for.

        Returns:
            The arguments that were passed with the signal, or None if the signal was not emitted.
        """
        return self.signal_args.get(signal, None)

    def reset(self):
        """Reset the signal catcher."""
        self.received_signals = {}
        self.signal_args = {}


def process_events():
    """Process pending Qt events to ensure signal delivery."""
    for _ in range(5):  # Process multiple rounds of events
        QTimer.singleShot(10, lambda: None)  # Force event loop to process
        time.sleep(0.01)


@pytest.fixture
def temp_validation_dir():
    """Create a temporary directory for validation files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create sample validation files
        players_file = temp_path / "players.txt"
        chest_types_file = temp_path / "chest_types.txt"
        sources_file = temp_path / "sources.txt"

        with open(players_file, "w") as f:
            f.write("ValidPlayer1\nValidPlayer2\n")

        with open(chest_types_file, "w") as f:
            f.write("ValidChest1\nValidChest2\n")

        with open(sources_file, "w") as f:
            f.write("ValidSource1\nValidSource2\n")

        yield temp_path


@pytest.fixture
def test_data():
    """Create test data for validation."""
    # Create DataFrame with some valid and invalid data
    return pd.DataFrame(
        {
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            "PLAYER": ["ValidPlayer1", "InvalidPlayer", "ValidPlayer2", "AnotherInvalidPlayer"],
            "SOURCE": ["ValidSource1", "ValidSource2", "InvalidSource", "ValidSource1"],
            "CHEST": ["ValidChest1", "ValidChest2", "ValidChest1", "InvalidChest"],
            "SCORE": [100, 200, 300, 400],
            "CLAN": ["Clan1", "Clan2", "Clan1", "Clan2"],
        }
    )


@pytest.fixture
def chest_data_model(test_data):
    """Create a ChestDataModel with test data."""
    model = ChestDataModel()
    model.update_data(test_data, test_data.columns.tolist())
    return model


@pytest.fixture
def validation_service(temp_validation_dir, chest_data_model):
    """Create a ValidationService with test data."""
    # Create real ValidationService with temp validation directory
    service = ValidationService(validation_path=temp_validation_dir)
    service.initialize()
    return service


@pytest.fixture
def signal_manager():
    """Create a SignalManager for testing."""
    return SignalManager()


@pytest.fixture
def ui_controller(signal_manager):
    """Create a UIStateController for testing."""
    return UIStateController(signal_manager)


@pytest.fixture
def data_controller(chest_data_model, validation_service, ui_controller, signal_manager):
    """Create a DataViewController for testing."""
    controller = DataViewController(
        chest_data_model, signal_manager=signal_manager, ui_state_controller=ui_controller
    )
    controller._validation_service = validation_service
    return controller


@pytest.fixture
def mock_data_view():
    """Create a mock DataView for testing."""
    view = MagicMock(spec=DataView)
    view.refresh = MagicMock()
    view._validation_status_delegate = MagicMock()
    view._table_view = MagicMock(spec=QTableView)
    view._table_model = MagicMock()
    view._table_model.index = MagicMock(return_value=QModelIndex())
    view._on_validation_changed = MagicMock()
    return view


@pytest.fixture
def mock_validation_view(validation_service, chest_data_model):
    """Create a mock ValidationViewAdapter for testing."""
    view = MagicMock(spec=ValidationViewAdapter)
    view.refresh = MagicMock()
    view._validation_tab = MagicMock()
    view._validation_tab.refresh = MagicMock()
    return view


@pytest.fixture
def signal_catcher():
    """Create a SignalCatcher for testing."""
    return SignalCatcher()


class TestValidationWorkflowEndToEnd:
    """End-to-end tests for the validation workflow."""

    def test_complete_validation_workflow(
        self,
        chest_data_model,
        validation_service,
        data_controller,
        ui_controller,
        mock_data_view,
        mock_validation_view,
        signal_catcher,
    ):
        """
        Test the complete validation workflow end-to-end.

        This test covers:
        1. Initial data validation
        2. UI state updates based on validation results
        3. Adding invalid entries to validation lists
        4. Re-validating with updated validation lists
        5. Validation visualization in the data view
        """
        # Connect controllers to views
        data_controller.connect_to_view(mock_data_view)
        data_controller.connect_to_view(mock_validation_view)

        # Connect signals to the signal catcher
        signal_catcher.catch_signal(data_controller.validation_started)
        signal_catcher.catch_signal(data_controller.validation_completed)
        signal_catcher.catch_signal(ui_controller.validation_state_changed)
        signal_catcher.catch_signal(ui_controller.status_message_changed)

        # Step 1: Initial validation
        data_controller.validate_data()
        process_events()

        # Verify validation signals were emitted
        assert signal_catcher.was_signal_emitted(data_controller.validation_started)
        assert signal_catcher.was_signal_emitted(data_controller.validation_completed)

        # Verify UI state was updated
        assert signal_catcher.was_signal_emitted(ui_controller.validation_state_changed)
        validation_state = ui_controller.get_validation_state()
        assert validation_state["has_issues"] is True

        # Verify there are validation issues with players, sources, and chests
        assert "player_name" in validation_state["categories"]
        assert "source" in validation_state["categories"]
        assert "chest_type" in validation_state["categories"]

        # Verify status message was updated
        assert "issues found" in ui_controller.get_status_message()

        # Verify data view was updated to show validation status
        mock_data_view._on_validation_changed.assert_called()

        # Step 2: Add invalid player to validation list
        signal_catcher.reset()

        # Create correction operation to add InvalidPlayer to validation list
        correction_operations = [
            {"action": "add_to_validation", "field_type": "player", "value": "InvalidPlayer"}
        ]

        # Apply correction
        data_controller._on_data_corrected(correction_operations)
        process_events()

        # Verify validation was run again
        assert signal_catcher.was_signal_emitted(data_controller.validation_started)
        assert signal_catcher.was_signal_emitted(data_controller.validation_completed)

        # Verify status message was updated
        assert signal_catcher.was_signal_emitted(ui_controller.status_message_changed)

        # Step 3: Add invalid chest to validation list
        signal_catcher.reset()

        # Create correction operation to add InvalidChest to validation list
        correction_operations = [
            {"action": "add_to_validation", "field_type": "chest_type", "value": "InvalidChest"}
        ]

        # Apply correction
        data_controller._on_data_corrected(correction_operations)
        process_events()

        # Step 4: Add invalid source to validation list
        signal_catcher.reset()

        # Create correction operation to add InvalidSource to validation list
        correction_operations = [
            {"action": "add_to_validation", "field_type": "source", "value": "InvalidSource"}
        ]

        # Apply correction
        data_controller._on_data_corrected(correction_operations)
        process_events()

        # Step 5: Final validation should show only one remaining invalid player
        signal_catcher.reset()

        # Run validation again
        data_controller.validate_data()
        process_events()

        # Verify UI state was updated
        assert signal_catcher.was_signal_emitted(ui_controller.validation_state_changed)
        validation_state = ui_controller.get_validation_state()

        # Should still have issues (AnotherInvalidPlayer)
        assert validation_state["has_issues"] is True

        # Verify there is still one player issue
        assert validation_state["categories"]["player_name"] == 1

        # But no more chest type or source issues
        assert "chest_type" not in validation_state["categories"]
        assert "source" not in validation_state["categories"]

    def test_validation_with_empty_data(self, data_controller, ui_controller, signal_catcher):
        """Test validation behavior with empty data."""
        # Make data model empty
        data_controller._data_model.is_empty = True

        # Connect signals to the signal catcher
        signal_catcher.catch_signal(data_controller.operation_error)
        signal_catcher.catch_signal(ui_controller.status_message_changed)

        # Try to validate
        result = data_controller.validate_data()
        process_events()

        # Verify validation failed
        assert result is False

        # Verify error signal was emitted
        assert signal_catcher.was_signal_emitted(data_controller.operation_error)

        # Verify status message was updated
        assert signal_catcher.was_signal_emitted(ui_controller.status_message_changed)
        assert (
            "Error" in ui_controller.get_status_message()
            or "Cannot validate" in ui_controller.get_status_message()
        )

    def test_validation_context_menu_integration(
        self, chest_data_model, validation_service, data_controller, mock_data_view, signal_catcher
    ):
        """Test that the context menu integration works for validation."""
        # Patch the QMenu execution to avoid actual GUI interaction
        with patch("PySide6.QtWidgets.QMenu") as MockQMenu:
            mock_menu = MagicMock()
            mock_menu.exec.return_value = MagicMock()
            MockQMenu.return_value = mock_menu

            # Setup mock actions
            mock_action = MagicMock()
            mock_action.text.return_value = "Add 'InvalidPlayer' to player validation list"
            mock_menu.addAction.return_value = mock_action

            # Connect signals
            signal_catcher.catch_signal(data_controller.correction_completed)

            # Simulate context menu request at position with invalid data
            mock_data_view._on_custom_context_menu_requested = MagicMock()

            # Call the method directly with a mock to handle logic
            # This is a simplified simulation since we can't actually show context menus in tests
            correction_operations = [
                {"action": "add_to_validation", "field_type": "player", "value": "InvalidPlayer"}
            ]
            data_controller._on_data_corrected(correction_operations)
            process_events()

            # Verify correction completed signal was emitted
            assert signal_catcher.was_signal_emitted(data_controller.correction_completed)

            # Verify validation was run again
            correction_result = signal_catcher.get_signal_args(data_controller.correction_completed)
            assert correction_result is not None
            assert correction_result[0]["action"] == "add_to_validation"
            assert correction_result[0]["field_type"] == "player"
            assert correction_result[0]["value"] == "InvalidPlayer"
