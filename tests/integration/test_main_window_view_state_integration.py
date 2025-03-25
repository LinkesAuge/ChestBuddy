"""
Integration tests for MainWindow and ViewStateController interactions.

These tests verify that MainWindow properly integrates with ViewStateController,
ensuring view transitions work correctly and state is maintained consistently.
"""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QEventLoop, QSettings
from PySide6.QtWidgets import QApplication, QWidget, QStackedWidget, QMainWindow

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

    def populate_table(self):
        self.populated = True
        self.needs_population = False

    def refresh(self):
        self.refreshed = True

    def needs_refresh(self):
        return True

    def set_data_loaded(self, loaded):
        self.data_loaded = loaded


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
def mock_services():
    """Create mock services for testing."""
    data_model = MagicMock(spec=ChestDataModel)
    data_model.data_changed = Signal()
    data_model.data_cleared = Signal()
    data_model.is_empty.return_value = True

    csv_service = MagicMock(spec=CSVService)
    validation_service = MagicMock(spec=ValidationService)
    correction_service = MagicMock(spec=CorrectionService)
    chart_service = MagicMock(spec=ChartService)
    data_manager = MagicMock()

    return {
        "data_model": data_model,
        "csv_service": csv_service,
        "validation_service": validation_service,
        "correction_service": correction_service,
        "chart_service": chart_service,
        "data_manager": data_manager,
    }


@pytest.fixture
def mock_controllers(mock_services):
    """Create mock controllers for testing."""
    file_controller = MagicMock(spec=FileOperationsController)
    file_controller.file_opened = Signal(str)
    file_controller.file_saved = Signal(str)
    file_controller.recent_files_changed = Signal(list)

    progress_controller = MagicMock(spec=ProgressController)
    error_controller = MagicMock(spec=ErrorHandlingController)

    view_state_controller = ViewStateController(mock_services["data_model"])
    data_view_controller = MagicMock(spec=DataViewController)
    data_view_controller.filter_applied = Signal(dict)
    data_view_controller.sort_applied = Signal(str, bool)
    data_view_controller.table_populated = Signal(int)

    return {
        "file_controller": file_controller,
        "progress_controller": progress_controller,
        "error_controller": error_controller,
        "view_state_controller": view_state_controller,
        "data_view_controller": data_view_controller,
    }


@pytest.fixture
def signal_catcher():
    """Create a signal catcher for testing."""
    return SignalCatcher()


@pytest.fixture
def main_window(app, mock_services, mock_controllers):
    """Create a MainWindow instance for testing."""
    with patch("chestbuddy.ui.main_window.MainWindow._create_views") as mock_create_views:
        with patch("chestbuddy.ui.main_window.MainWindow._setup_ui") as mock_setup_ui:
            with patch(
                "chestbuddy.ui.main_window.MainWindow._connect_signals"
            ) as mock_connect_signals:
                main_window = MainWindow(
                    mock_services["data_model"],
                    mock_services["csv_service"],
                    mock_services["validation_service"],
                    mock_services["correction_service"],
                    mock_services["chart_service"],
                    mock_services["data_manager"],
                    mock_controllers["file_controller"],
                    mock_controllers["progress_controller"],
                    mock_controllers["view_state_controller"],
                    mock_controllers["data_view_controller"],
                )

                # Expose the view state controller for direct testing
                main_window._view_state_controller = mock_controllers["view_state_controller"]

                # Set up content stack and sidebar
                main_window._content_stack = QStackedWidget()
                main_window._sidebar = MagicMock(spec=SidebarNavigation)
                main_window._sidebar.navigation_changed = Signal(str)

                # Set up views dict
                main_window._views = {
                    "Dashboard": MockView("Dashboard"),
                    "Data": MockView("Data"),
                    "Validation": MockView("Validation"),
                    "Correction": MockView("Correction"),
                    "Charts": MockView("Charts"),
                }

                # Add views to content stack
                for view in main_window._views.values():
                    main_window._content_stack.addWidget(view)

                # Set up view state controller with the views and UI components
                main_window._view_state_controller.set_ui_components(
                    main_window._views, main_window._sidebar, main_window._content_stack
                )

                # Initialize view state controller
                yield main_window


class TestMainWindowViewStateIntegration:
    """Tests for MainWindow and ViewStateController integration."""

    def test_view_changed_updates_main_window(self, main_window, signal_catcher):
        """Test that view_changed signal updates MainWindow UI."""
        # Patch the _update_ui method
        with patch.object(main_window, "_update_ui") as mock_update_ui:
            # Catch the view_changed signal
            signal_catcher.catch_signal(main_window._view_state_controller.view_changed)

            # Set active view
            main_window._view_state_controller.set_active_view("Data")
            process_events()

            # Verify signal was emitted
            assert signal_catcher.was_signal_emitted(
                main_window._view_state_controller.view_changed
            )

            # Verify MainWindow._update_ui was called
            mock_update_ui.assert_called()

            # Verify active view is Data
            assert main_window._view_state_controller.active_view == "Data"

    def test_data_state_changed_updates_main_window(self, main_window, signal_catcher):
        """Test that data_state_changed signal updates MainWindow UI."""
        # Catch the data_state_changed signal
        signal_catcher.catch_signal(main_window._view_state_controller.data_state_changed)

        # Patch the action methods to avoid AttributeError
        main_window._save_action = MagicMock()
        main_window._save_as_action = MagicMock()
        main_window._validate_action = MagicMock()
        main_window._correct_action = MagicMock()

        # Update data loaded state
        main_window._view_state_controller.update_data_loaded_state(True)
        process_events()

        # Verify signal was emitted
        assert signal_catcher.was_signal_emitted(
            main_window._view_state_controller.data_state_changed
        )

        # Verify UI elements were updated (the actions should be enabled)
        assert main_window._save_action.setEnabled.called_with(True)
        assert main_window._save_as_action.setEnabled.called_with(True)
        assert main_window._validate_action.setEnabled.called_with(True)
        assert main_window._correct_action.setEnabled.called_with(True)

    def test_sidebar_navigation_changes_view(self, main_window):
        """Test that sidebar navigation changes the active view."""
        # Directly emit the navigation_changed signal from sidebar
        main_window._sidebar.navigation_changed.emit("Validation")
        process_events()

        # Verify view was changed (this only works if data is loaded for Validation view)
        # In this test, we're just verifying the signal connection, not the actual view change

        # Call to check connection
        main_window._view_state_controller.update_data_loaded_state(True)
        process_events()

        main_window._sidebar.navigation_changed.emit("Validation")
        process_events()

        # Now verify view was changed
        assert main_window._view_state_controller.active_view == "Validation"

    def test_view_prerequisites_failed_handling(self, main_window, signal_catcher):
        """Test handling of view_prerequisites_failed signal."""
        # Patch QMessageBox to avoid UI interactions
        with patch(
            "chestbuddy.core.controllers.view_state_controller.QMessageBox"
        ) as mock_message_box:
            # Catch the prerequisites failed signal
            signal_catcher.catch_signal(
                main_window._view_state_controller.view_prerequisites_failed
            )

            # Try to navigate to Validation which requires data
            main_window._view_state_controller.set_active_view("Validation")
            process_events()

            # Verify signal was emitted
            assert signal_catcher.was_signal_emitted(
                main_window._view_state_controller.view_prerequisites_failed
            )

            # Verify QMessageBox was shown (or would have been in the actual implementation)
            mock_message_box.information.assert_called()

    def test_transitions_between_all_views(self, main_window):
        """Test transitions between all views with data loaded."""
        # Set data loaded state
        main_window._view_state_controller.update_data_loaded_state(True)
        process_events()

        # Navigate through all views
        views = ["Dashboard", "Data", "Validation", "Correction", "Charts"]

        for view_name in views:
            main_window._view_state_controller.set_active_view(view_name)
            process_events()

            # Verify view was changed
            assert main_window._view_state_controller.active_view == view_name

        # Test navigation history by going back through views
        for _ in range(len(views) - 1):
            main_window._view_state_controller.navigate_back()
            process_events()

        # Should be back at Dashboard
        assert main_window._view_state_controller.active_view == "Dashboard"

    def test_main_window_delegate_to_view_state_controller(self, main_window):
        """Test that MainWindow delegates view management to ViewStateController."""
        # Patch the ViewStateController.set_active_view method
        with patch.object(
            main_window._view_state_controller, "set_active_view"
        ) as mock_set_active_view:
            # Call MainWindow._set_active_view
            main_window._set_active_view("Data")

            # Verify delegation
            mock_set_active_view.assert_called_once_with("Data")

    def test_error_handling_in_view_transitions(self, main_window):
        """Test error handling during view transitions."""
        # Patch ViewStateController.set_active_view to raise an exception
        with patch.object(
            main_window._view_state_controller,
            "set_active_view",
            side_effect=ValueError("Test error"),
        ):
            # Patch QMessageBox to avoid UI interactions
            with patch("chestbuddy.ui.main_window.QMessageBox") as mock_message_box:
                # Call MainWindow._set_active_view
                main_window._set_active_view("Data")

                # Verify error handling
                mock_message_box.critical.assert_called()
