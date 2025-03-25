"""
Integration tests for ValidationViewAdapter and DataViewController interactions.

These tests verify that ValidationViewAdapter properly integrates with DataViewController,
ensuring validation operations work correctly and signals are properly handled.
"""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox

from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.ui.views.validation_view_adapter import ValidationViewAdapter
from chestbuddy.ui.validation_tab import ValidationTab


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

    def wait_for_signal(self, signal, timeout=1000):
        """
        Wait for a signal to be emitted.

        Args:
            signal: The signal to wait for
            timeout: Timeout in milliseconds

        Returns:
            bool: True if the signal was emitted, False if timeout occurred
        """
        if signal in self.received_signals and self.received_signals[signal]:
            return True

        # Create an event loop to wait for the signal
        loop = QEventLoop()

        # Create a timer for timeout
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)

        # Connect the signal to quit the event loop
        signal.connect(loop.quit)

        # Start the timer
        timer.start(timeout)

        # Wait for either the signal or the timeout
        loop.exec()

        # Return True if the signal was emitted, False if timeout occurred
        return signal in self.received_signals and self.received_signals[signal]


def process_events():
    """Process pending Qt events."""
    app = QApplication.instance()
    if app:
        for _ in range(5):  # Process multiple rounds of events
            app.processEvents()
            time.sleep(0.01)  # Small delay to allow events to propagate


@pytest.fixture
def app():
    """Create a QApplication instance for each test function."""
    if QApplication.instance():
        # If there's already an instance, use it but don't yield it
        # as we don't want to destroy an existing application instance
        yield QApplication.instance()
    else:
        # Create a new instance if none exists
        app = QApplication([])
        yield app


@pytest.fixture
def mock_validation_tab():
    """Create a mock ValidationTab for testing."""
    validation_tab = MagicMock(spec=ValidationTab)
    validation_tab.refresh = MagicMock()
    validation_tab.validate = MagicMock()
    validation_tab.clear_validation = MagicMock()
    return validation_tab


@pytest.fixture
def mock_data_model():
    """Create a mock data model for testing."""
    data_model = MagicMock(spec=ChestDataModel)
    data_model.data_changed = Signal()
    data_model.validation_changed = Signal(object)
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
    data_model.get_dataframe.return_value = df

    return data_model


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service for testing."""
    validation_service = MagicMock(spec=ValidationService)
    validation_service.validation_completed = Signal(dict)

    # Mock validation results
    validation_results = {"player_name": ["Player1 is invalid"], "chest_type": []}
    validation_service.validate_data.return_value = validation_results
    validation_service.get_validation_summary.return_value = {"player_name": 1, "chest_type": 0}

    return validation_service


@pytest.fixture
def controller(mock_data_model, mock_validation_service):
    """Create a DataViewController for testing."""
    controller = DataViewController(mock_data_model, mock_validation_service)
    return controller


@pytest.fixture
def signal_catcher():
    """Create a SignalCatcher for testing."""
    return SignalCatcher()


@pytest.fixture
def validation_view(app, mock_data_model, mock_validation_service, mock_validation_tab):
    """Create a ValidationViewAdapter for testing."""
    with patch(
        "chestbuddy.ui.views.validation_view_adapter.ValidationTab",
        return_value=mock_validation_tab,
    ):
        view = ValidationViewAdapter(mock_data_model, mock_validation_service)
        view._set_header_status = MagicMock()
        return view


class TestValidationViewControllerIntegration:
    """Integration tests for ValidationViewAdapter and DataViewController."""

    def test_controller_connection(self, validation_view, controller):
        """Test setting the controller and establishing signal connections."""
        # Set controller
        validation_view.set_controller(controller)

        # Check controller reference
        assert validation_view._controller == controller

        # Process events to allow signal connections to be established
        process_events()

        # Verify correct setup
        assert validation_view._controller is not None

    def test_validate_button_with_controller(
        self, validation_view, controller, mock_validation_service
    ):
        """Test that validate button uses the controller to validate data."""
        # Set controller
        validation_view.set_controller(controller)

        # Mock the validate_data method
        controller.validate_data = MagicMock(return_value=True)

        # Trigger the validation action
        validation_view._on_action_clicked("validate")

        # Check if controller method was called
        controller.validate_data.assert_called_once()

        # Verify tab's validate method wasn't called directly
        validation_view._validation_tab.validate.assert_not_called()

    def test_validation_started_signal(self, validation_view, controller, signal_catcher):
        """Test that validation_started signal is properly handled."""
        # Set controller
        validation_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.validation_started)

        # Emit the signal
        controller.validation_started.emit()

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.validation_started)
        validation_view._set_header_status.assert_called_with("Validating data...")

    def test_validation_completed_signal(
        self, validation_view, controller, signal_catcher, mock_validation_tab
    ):
        """Test that validation_completed signal is properly handled."""
        # Set controller
        validation_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.validation_completed)

        # Create mock validation results
        results = {"player_name": ["Player1 is invalid"], "chest_type": []}

        # Emit the signal
        controller.validation_completed.emit(results)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.validation_completed)
        validation_view._set_header_status.assert_called_with("Validation complete: 1 issues found")
        mock_validation_tab.refresh.assert_called_once()

    def test_validation_error_signal(self, validation_view, controller, signal_catcher):
        """Test that validation_error signal is properly handled."""
        # Set controller
        validation_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.validation_error)

        # Emit the signal
        error_msg = "Validation failed"
        controller.validation_error.emit(error_msg)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.validation_error)
        validation_view._set_header_status.assert_called_with(f"Validation error: {error_msg}")

    def test_operation_error_signal(self, validation_view, controller, signal_catcher):
        """Test that operation_error signal is properly handled."""
        # Set controller
        validation_view.set_controller(controller)

        # Catch the signal
        signal_catcher.catch_signal(controller.operation_error)

        # Emit the signal
        error_msg = "Operation failed"
        controller.operation_error.emit(error_msg)

        # Process events
        process_events()

        # Check if signal was emitted and handler was called
        assert signal_catcher.was_signal_emitted(controller.operation_error)
        validation_view._set_header_status.assert_called_with(f"Error: {error_msg}")

    def test_clear_button_functionality(self, validation_view, controller, mock_validation_tab):
        """Test that clear button functions properly."""
        # Set controller
        validation_view.set_controller(controller)

        # Trigger the clear action
        validation_view._on_action_clicked("clear")

        # Verify clear_validation was called on the validation tab
        mock_validation_tab.clear_validation.assert_called_once()

    def test_refresh_button_functionality(self, validation_view, controller, mock_validation_tab):
        """Test that refresh button functions properly."""
        # Set controller
        validation_view.set_controller(controller)

        # Trigger the refresh action
        validation_view._on_action_clicked("refresh")

        # Verify refresh was called on the validation tab
        mock_validation_tab.refresh.assert_called_once()

    def test_fallback_to_direct_validation(self, validation_view, mock_validation_tab):
        """Test fallback to direct validation when controller not set."""
        # Do not set controller
        assert validation_view._controller is None

        # Trigger the validation action
        validation_view._on_action_clicked("validate")

        # Verify validation tab's validate method was called directly
        mock_validation_tab.validate.assert_called_once()
