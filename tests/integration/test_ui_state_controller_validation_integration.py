"""
Integration tests for UIStateController and DataViewController validation integration.

These tests verify that the UIStateController properly integrates with the DataViewController
for validation-related functionality.
"""

import os
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEventLoop

from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.utils.signal_manager import SignalManager


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
def signal_manager():
    """Create a SignalManager instance for testing."""
    return SignalManager()


@pytest.fixture
def ui_controller(signal_manager):
    """Create a UIStateController instance for testing."""
    return UIStateController(signal_manager)


@pytest.fixture
def mock_data_model():
    """Create a mock data model for testing."""
    data_model = MagicMock(spec=ChestDataModel)
    data_model.data_changed = Signal()
    data_model.validation_changed = Signal()
    data_model.is_empty = False

    # Create a simple DataFrame for testing
    df = pd.DataFrame(
        {
            "DATE": ["2023-01-01", "2023-01-02"],
            "PLAYER": ["Player1", "Player2"],
            "SOURCE": ["Source1", "Source2"],
            "CHEST": ["Chest1", "Chest2"],
            "SCORE": [100, 200],
            "CLAN": ["Clan1", "Clan2"],
        }
    )

    # Use the data property instead of get_dataframe
    type(data_model).data = PropertyMock(return_value=df)

    return data_model


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service for testing."""
    validation_service = MagicMock(spec=ValidationService)
    validation_service.validation_completed = Signal(dict)

    # Mock validation results
    validation_results = {
        "player_name": ["Player1 is invalid"],
        "chest_type": ["Chest1 is invalid"],
        "source": [],
    }
    validation_service.validate_data.return_value = validation_results
    validation_service.get_validation_summary.return_value = {
        "player_name": 1,
        "chest_type": 1,
        "source": 0,
    }
    validation_service.add_to_validation_list = MagicMock(return_value=True)

    return validation_service


@pytest.fixture
def data_controller(mock_data_model, mock_validation_service, ui_controller, signal_manager):
    """Create a DataViewController with UIStateController for testing."""
    controller = DataViewController(
        mock_data_model, signal_manager=signal_manager, ui_state_controller=ui_controller
    )
    controller._validation_service = mock_validation_service
    return controller


@pytest.fixture
def signal_catcher():
    """Create a SignalCatcher for testing."""
    return SignalCatcher()


class TestUIStateControllerValidationIntegration:
    """
    Integration tests for UIStateController and DataViewController validation integration.
    """

    def test_validation_results_update_ui_state(
        self, data_controller, ui_controller, signal_catcher
    ):
        """Test that validation results update UI state correctly."""
        # Connect signals to signal catcher
        signal_catcher.catch_signal(ui_controller.validation_state_changed)
        signal_catcher.catch_signal(ui_controller.status_message_changed)
        signal_catcher.catch_signal(data_controller.validation_completed)

        # Perform validation
        data_controller.validate_data()
        process_events()

        # Verify UIStateController received validation state update
        assert signal_catcher.was_signal_emitted(ui_controller.validation_state_changed)

        # Verify validation state is correct
        validation_state = ui_controller.get_validation_state()
        assert validation_state["has_issues"] is True
        assert validation_state["issue_count"] == 2  # One player issue + one chest type issue
        assert validation_state["categories"]["player_name"] == 1
        assert validation_state["categories"]["chest_type"] == 1
        assert "source" not in validation_state["categories"]

        # Verify status message was updated
        assert signal_catcher.was_signal_emitted(ui_controller.status_message_changed)
        assert ui_controller.get_status_message() == "Validation complete: 2 issues found"

    def test_validation_error_updates_ui_state(
        self, data_controller, ui_controller, signal_catcher
    ):
        """Test that validation errors update UI state correctly."""
        # Connect signals to signal catcher
        signal_catcher.catch_signal(ui_controller.status_message_changed)

        # Mock validation service to raise an exception
        data_controller._validation_service.validate_data.side_effect = Exception(
            "Test validation error"
        )

        # Perform validation
        data_controller.validate_data()
        process_events()

        # Verify status message was updated
        assert signal_catcher.was_signal_emitted(ui_controller.status_message_changed)
        assert "Validation error" in ui_controller.get_status_message()

    def test_add_to_validation_list_updates_ui_state(
        self, data_controller, ui_controller, signal_catcher
    ):
        """Test that adding to validation list updates UI state correctly."""
        # Connect signals to signal catcher
        signal_catcher.catch_signal(ui_controller.status_message_changed)

        # Create correction operation
        correction_operations = [
            {"action": "add_to_validation", "field_type": "player", "value": "TestPlayer"}
        ]

        # Apply correction
        data_controller._on_data_corrected(correction_operations)
        process_events()

        # Verify status message was updated
        assert signal_catcher.was_signal_emitted(ui_controller.status_message_changed)
        assert "Added 'TestPlayer' to player validation list" in ui_controller.get_status_message()

    def test_add_to_validation_list_failure_updates_ui_state(
        self, data_controller, ui_controller, signal_catcher
    ):
        """Test that adding to validation list failure updates UI state correctly."""
        # Connect signals to signal catcher
        signal_catcher.catch_signal(ui_controller.status_message_changed)

        # Mock validation service to fail when adding to list
        data_controller._validation_service.add_to_validation_list.return_value = False

        # Create correction operation
        correction_operations = [
            {"action": "add_to_validation", "field_type": "player", "value": "TestPlayer"}
        ]

        # Apply correction
        data_controller._on_data_corrected(correction_operations)
        process_events()

        # Verify status message was updated
        assert signal_catcher.was_signal_emitted(ui_controller.status_message_changed)
        assert (
            "Failed to add 'TestPlayer' to player validation list"
            in ui_controller.get_status_message()
        )

    def test_data_dependent_ui_with_validation(
        self, data_controller, ui_controller, signal_catcher
    ):
        """Test that data dependent UI updates affect validation state."""
        # Connect signals to signal catcher
        signal_catcher.catch_signal(ui_controller.validation_state_changed)
        signal_catcher.catch_signal(ui_controller.actions_state_changed)

        # Set some validation state
        ui_controller.update_validation_state(has_issues=True, issue_count=5)

        # Reset signal catcher
        signal_catcher.reset()

        # Update data dependent UI to no data
        ui_controller.update_data_dependent_ui(False)
        process_events()

        # Verify validation state was reset
        assert signal_catcher.was_signal_emitted(ui_controller.validation_state_changed)
        validation_state = ui_controller.get_validation_state()
        assert validation_state["has_issues"] is False
        assert validation_state["issue_count"] == 0

        # Verify validation-related action states are properly set
        assert signal_catcher.was_signal_emitted(ui_controller.actions_state_changed)
        action_states = ui_controller.get_action_states()
        assert action_states["validate"] is False
        assert action_states["add_to_validation"] is False
        assert action_states["clear_validation"] is False
