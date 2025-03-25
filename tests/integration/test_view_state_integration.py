"""
Integration tests for ViewStateController interactions with other components.

These tests verify that ViewStateController properly integrates with MainWindow
and DataViewController, ensuring signals are properly propagated and state
is maintained consistently across components.
"""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEventLoop, QSettings
from PySide6.QtWidgets import QApplication, QWidget, QStackedWidget

from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.error_handling_controller import ErrorHandlingController
from chestbuddy.core.controllers.file_operations_controller import FileOperationsController
from chestbuddy.core.controllers.progress_controller import ProgressController
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation


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


class MockView(QWidget):
    """Mock view class for testing."""

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.populated = False
        self.refreshed = False
        self.needs_population = False
        self.data_loaded = False
        self.state = {}

    def populate_table(self):
        self.populated = True
        self.needs_population = False

    def refresh(self):
        self.refreshed = True

    def needs_refresh(self):
        return True

    def set_data_loaded(self, loaded):
        self.data_loaded = loaded

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state


class MockSidebar(QObject):
    """Mock sidebar class for testing."""

    navigation_changed = Signal(str)
    data_dependent_view_clicked = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.active_item = None
        self.data_loaded_state = None
        self.view_availability = {}

    def set_active_item(self, item):
        self.active_item = item

    def set_data_loaded(self, has_data):
        self.data_loaded_state = has_data

    def update_view_availability(self, availability):
        self.view_availability = availability


class MockDataViewController(QObject):
    """Mock data view controller class for testing."""

    filter_applied = Signal(dict)
    sort_applied = Signal(str, bool)
    table_populated = Signal(int)
    operation_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.view = None
        self.refresh_called = False
        self.needs_refresh_result = True
        self.filter_params = {}
        self.sort_params = {"column": "", "ascending": True}

    def set_view(self, view):
        self.view = view

    def refresh_data(self):
        self.refresh_called = True
        return True

    def needs_refresh(self):
        return self.needs_refresh_result


@pytest.fixture
def data_model():
    """Create a data model for testing."""
    model = ChestDataModel()
    # Monkey patch signals to allow direct emitting
    model.data_changed = Signal()
    model.data_cleared = Signal()
    return model


@pytest.fixture
def mock_content_stack():
    """Create a mock content stack widget."""
    stack = QStackedWidget()
    return stack


@pytest.fixture
def mock_views():
    """Create mock views for testing."""
    return {
        "Dashboard": MockView("Dashboard"),
        "Data": MockView("Data"),
        "Validation": MockView("Validation"),
        "Correction": MockView("Correction"),
        "Charts": MockView("Charts"),
    }


@pytest.fixture
def mock_sidebar():
    """Create a mock sidebar for testing."""
    return MockSidebar()


@pytest.fixture
def mock_data_view_controller():
    """Create a mock data view controller for testing."""
    return MockDataViewController()


@pytest.fixture
def signal_manager():
    """Create a SignalManager instance for testing."""
    from chestbuddy.utils.signal_manager import SignalManager

    return SignalManager(debug_mode=True)


@pytest.fixture
def view_state_controller(data_model, mock_content_stack, mock_views, mock_sidebar, signal_manager):
    """Create a ViewStateController instance for testing."""
    controller = ViewStateController(data_model, signal_manager)
    controller.set_ui_components(mock_views, mock_sidebar, mock_content_stack)
    return controller


@pytest.fixture
def signal_catcher():
    """Create a signal catcher for testing."""
    return SignalCatcher()


@pytest.fixture
def setup_integration(view_state_controller, mock_data_view_controller, signal_catcher):
    """Set up integration between controllers for testing."""
    view_state_controller.set_data_view_controller(mock_data_view_controller)

    # Catch signals from ViewStateController
    signal_catcher.catch_signal(view_state_controller.view_changed)
    signal_catcher.catch_signal(view_state_controller.data_state_changed)
    signal_catcher.catch_signal(view_state_controller.view_prerequisites_failed)
    signal_catcher.catch_signal(view_state_controller.view_availability_changed)
    signal_catcher.catch_signal(view_state_controller.navigation_history_changed)
    signal_catcher.catch_signal(view_state_controller.view_transition_started)
    signal_catcher.catch_signal(view_state_controller.view_transition_completed)

    return view_state_controller, mock_data_view_controller, signal_catcher


class TestViewStateIntegration:
    """Tests for ViewStateController integration with other components."""

    def test_view_transition_signals(self, setup_integration, mock_views):
        """Test that view transition signals are properly emitted."""
        view_state_controller, _, signal_catcher = setup_integration

        # First navigate to Dashboard
        view_state_controller.set_active_view("Dashboard")
        process_events()

        # Reset signals
        signal_catcher.reset()

        # Navigate to Data view
        view_state_controller.set_active_view("Data")
        process_events()

        # Verify signals
        assert signal_catcher.was_signal_emitted(view_state_controller.view_transition_started)
        assert signal_catcher.was_signal_emitted(view_state_controller.view_transition_completed)
        assert signal_catcher.was_signal_emitted(view_state_controller.view_changed)

        # Verify view was changed
        assert view_state_controller.active_view == "Data"

        # Verify signal arguments
        transition_args = signal_catcher.get_signal_args(
            view_state_controller.view_transition_started
        )
        assert transition_args[0] == "Dashboard"  # from_view
        assert transition_args[1] == "Data"  # to_view

        # Verify completed signal
        completed_args = signal_catcher.get_signal_args(
            view_state_controller.view_transition_completed
        )
        assert completed_args[0] == "Data"  # view_name

    def test_data_state_propagation(self, setup_integration, data_model):
        """Test that data state changes are properly propagated."""
        view_state_controller, _, signal_catcher = setup_integration

        # Verify initial state
        assert view_state_controller.has_data is False

        # Reset signals
        signal_catcher.reset()

        # Trigger data loaded
        data_model.data_changed.emit()
        process_events()

        # Verify signal was emitted
        assert signal_catcher.was_signal_emitted(view_state_controller.data_state_changed)

        # Verify state was updated
        data_state_args = signal_catcher.get_signal_args(view_state_controller.data_state_changed)
        # Note: The default mock for is_empty returns True, which means has_data would be False
        # In a real application, this would be inverted - has_data would be True when is_empty is False
        assert data_state_args[0] is True  # has_data

    def test_data_view_controller_integration(self, setup_integration, mock_views):
        """Test integration between ViewStateController and DataViewController."""
        view_state_controller, data_view_controller, _ = setup_integration

        # Set Data view and verify DataViewController is updated
        view_state_controller.set_active_view("Data")
        process_events()

        # Verify DataViewController was updated
        assert data_view_controller.view == mock_views["Data"]

        # Verify refresh was called
        assert data_view_controller.refresh_called is True

    def test_view_prerequisites(self, setup_integration, data_model):
        """Test view prerequisites checking."""
        view_state_controller, _, signal_catcher = setup_integration

        # Reset signals
        signal_catcher.reset()

        # Try to navigate to Validation which requires data
        view_state_controller.set_active_view("Validation")
        process_events()

        # Verify prerequisites failed signal was emitted
        assert signal_catcher.was_signal_emitted(view_state_controller.view_prerequisites_failed)

        # Verify we didn't navigate to Validation
        assert view_state_controller.active_view != "Validation"

        # Set data loaded state
        data_model.is_empty = MagicMock(return_value=False)
        view_state_controller.update_data_loaded_state(True)
        process_events()

        # Reset signals
        signal_catcher.reset()

        # Try again to navigate to Validation
        view_state_controller.set_active_view("Validation")
        process_events()

        # Verify we navigated to Validation
        assert view_state_controller.active_view == "Validation"

        # Verify prerequisites failed signal was not emitted
        assert not signal_catcher.was_signal_emitted(
            view_state_controller.view_prerequisites_failed
        )

    def test_view_availability_updates(self, setup_integration, mock_sidebar):
        """Test view availability updates."""
        view_state_controller, _, signal_catcher = setup_integration

        # Reset signals
        signal_catcher.reset()

        # Update data loaded state
        view_state_controller.update_data_loaded_state(True)
        process_events()

        # Verify view availability signal was emitted
        assert signal_catcher.was_signal_emitted(view_state_controller.view_availability_changed)

        # Verify sidebar was updated
        availability = mock_sidebar.view_availability
        assert "Validation" in availability and availability["Validation"] is True
        assert "Correction" in availability and availability["Correction"] is True
        assert "Charts" in availability and availability["Charts"] is True

    def test_navigation_history(self, setup_integration):
        """Test navigation history tracking."""
        view_state_controller, _, signal_catcher = setup_integration

        # Enable data
        view_state_controller.update_data_loaded_state(True)

        # Navigate to a series of views
        view_state_controller.set_active_view("Dashboard")
        view_state_controller.set_active_view("Data")
        view_state_controller.set_active_view("Validation")
        process_events()

        # Reset signals
        signal_catcher.reset()

        # Navigate back
        view_state_controller.navigate_back()
        process_events()

        # Verify we navigated back to Data
        assert view_state_controller.active_view == "Data"

        # Verify history signal was emitted
        assert signal_catcher.was_signal_emitted(view_state_controller.navigation_history_changed)

        # Verify history state
        history_args = signal_catcher.get_signal_args(
            view_state_controller.navigation_history_changed
        )
        assert history_args[0] is True  # can_go_back
        assert history_args[1] is True  # can_go_forward

    def test_state_persistence(self, setup_integration, mock_views):
        """Test state persistence between views."""
        view_state_controller, _, _ = setup_integration

        # Set state in Data view
        data_view = mock_views["Data"]
        data_view.state = {"filter": "test", "sort": "column1"}

        # Navigate to Data view
        view_state_controller.set_active_view("Data")
        process_events()

        # Navigate to another view
        view_state_controller.set_active_view("Dashboard")
        process_events()

        # Change state
        data_view.state = {}

        # Navigate back to Data view
        view_state_controller.set_active_view("Data")
        process_events()

        # Verify state was restored
        assert data_view.state == {"filter": "test", "sort": "column1"}

    def test_async_view_transitions(self, setup_integration, monkeypatch):
        """Test asynchronous view transitions."""
        view_state_controller, _, signal_catcher = setup_integration

        # Create a delayed transition by mocking QTimer.singleShot
        original_single_shot = QTimer.singleShot
        delayed_callbacks = []

        def delayed_single_shot(ms, callback):
            # Store callback for later execution
            delayed_callbacks.append((ms, callback))

        monkeypatch.setattr(QTimer, "singleShot", delayed_single_shot)

        # Start view transition
        view_state_controller.set_active_view("Data")

        # Verify transition is in progress
        assert view_state_controller._view_transition_in_progress is True

        # Try to navigate to another view during transition
        view_state_controller.set_active_view("Validation")

        # Verify pending view is set
        assert view_state_controller._pending_view_change == "Validation"

        # Reset QTimer.singleShot
        monkeypatch.setattr(QTimer, "singleShot", original_single_shot)

        # Execute the delayed callbacks
        for _, callback in delayed_callbacks:
            callback()
            process_events()

        # Verify final view is Validation
        assert view_state_controller.active_view == "Validation"
        assert view_state_controller._view_transition_in_progress is False
        assert view_state_controller._pending_view_change is None

    def test_error_handling_during_transitions(self, setup_integration, mock_views, monkeypatch):
        """Test error handling during view transitions."""
        view_state_controller, _, _ = setup_integration

        # Make populate_table raise an exception
        original_populate = mock_views["Data"].populate_table

        def raising_populate():
            raise ValueError("Test error")

        mock_views["Data"].populate_table = raising_populate
        mock_views["Data"].needs_population = True

        # Mock QTimer.singleShot to execute callback immediately
        def mock_single_shot(ms, callback):
            callback()

        monkeypatch.setattr(QTimer, "singleShot", mock_single_shot)

        # Attempt to navigate to Data view
        view_state_controller.set_active_view("Data")
        process_events()

        # Verify view was still changed despite the error
        assert view_state_controller.active_view == "Data"
        assert view_state_controller._view_transition_in_progress is False

        # Restore original populate_table
        mock_views["Data"].populate_table = original_populate

        # Navigate to Dashboard, then back to Data to test recovery
        view_state_controller.set_active_view("Dashboard")
        process_events()

        view_state_controller.set_active_view("Data")
        process_events()

        # Verify recovery was successful
        assert view_state_controller.active_view == "Data"
        assert mock_views["Data"].populated is True
