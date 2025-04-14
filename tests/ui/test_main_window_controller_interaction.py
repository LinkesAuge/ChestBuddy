"""
test_main_window_controller_interaction.py

Description: Tests for MainWindow interaction with various controllers
Usage:
    pytest tests/ui/test_main_window_controller_interaction.py
"""

import pytest
from unittest.mock import MagicMock, patch, call
import logging

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox

from chestbuddy.ui.main_window import MainWindow
from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.file_operations_controller import FileOperationsController
from chestbuddy.core.controllers.progress_controller import ProgressController
from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.core.models import ChestDataModel


class MockSignal:
    """
    Mock PySide6 Signal for testing.

    This class mimics the behavior of PySide6 signals for testing purposes,
    allowing tests to connect to signals and emit them.
    """

    def __init__(self, *args):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def disconnect(self, callback=None):
        if callback:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
        else:
            self.callbacks = []

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


@pytest.fixture
def mock_data_model():
    """Create a mock data model."""
    model = MagicMock(spec=ChestDataModel)
    model.has_data.return_value = False
    return model


@pytest.fixture
def mock_view_state_controller():
    """Create a mock ViewStateController."""
    controller = MagicMock(spec=ViewStateController)

    # Add mock signals
    controller.view_changed = MockSignal(str)
    controller.data_state_changed = MockSignal(bool)

    return controller


@pytest.fixture
def mock_file_operations_controller():
    """Create a mock FileOperationsController."""
    controller = MagicMock(spec=FileOperationsController)

    # Add mock signals
    controller.file_open_started = MockSignal()
    controller.file_open_completed = MockSignal(bool, str)
    controller.file_save_started = MockSignal()
    controller.file_save_completed = MockSignal(bool, str)
    controller.import_started = MockSignal()
    controller.import_completed = MockSignal(bool, str)
    controller.export_started = MockSignal()
    controller.export_completed = MockSignal(bool, str)

    return controller


@pytest.fixture
def mock_data_view_controller():
    """Create a mock DataViewController."""
    controller = MagicMock(spec=DataViewController)

    # Add mock signals
    controller.data_filtered = MockSignal(dict)
    controller.data_sorted = MockSignal(dict)
    controller.data_selection_changed = MockSignal(list)

    return controller


@pytest.fixture
def mock_progress_controller():
    """Create a mock ProgressController."""
    controller = MagicMock(spec=ProgressController)

    # Add mock signals
    controller.progress_started = MockSignal(str)
    controller.progress_updated = MockSignal(int, int, str)
    controller.progress_completed = MockSignal(bool, str)

    return controller


@pytest.fixture
def mock_ui_state_controller():
    """Create a mock UIStateController."""
    controller = MagicMock(spec=UIStateController)

    # Add mock signals
    controller.theme_changed = MockSignal(str)
    controller.layout_changed = MockSignal(dict)

    return controller


@pytest.fixture
def main_window(
    qtbot,
    mock_data_model,
    mock_file_operations_controller,
    mock_progress_controller,
    mock_view_state_controller,
    mock_data_view_controller,
    mock_ui_state_controller,
):
    """Create a MainWindow instance with mocked controllers."""
    # Mock other services needed by MainWindow
    csv_service = MagicMock()
    validation_service = MagicMock()
    correction_service = MagicMock()
    chart_service = MagicMock()
    data_manager = MagicMock()
    config_manager = MagicMock()

    # Patch QMessageBox to avoid actual dialog display
    with patch("PySide6.QtWidgets.QMessageBox", autospec=True):
        # Create MainWindow instance
        window = MainWindow(
            data_model=mock_data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=mock_file_operations_controller,
            progress_controller=mock_progress_controller,
            view_state_controller=mock_view_state_controller,
            data_view_controller=mock_data_view_controller,
            ui_state_controller=mock_ui_state_controller,
            config_manager=config_manager,
        )

        qtbot.addWidget(window)
        window.show()

        # Reset the mocks to clear any calls during initialization
        mock_view_state_controller.reset_mock()
        mock_file_operations_controller.reset_mock()
        mock_data_view_controller.reset_mock()

        yield window

        # Clean up
        window.close()


class TestMainWindowControllerInteraction:
    """Tests for MainWindow interaction with various controllers."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker, mock_data_model, mock_controllers):
        # ... (existing setup) ...

    def test_file_operations_controller_interactions(
        self, main_window, mock_file_operations_controller, mock_data_model
    ):
        """Test interactions with FileOperationsController."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Test open_file action
        main_window._open_action.trigger()
        mock_file_operations_controller.open_files.assert_called_once()

        # Test save_file action
        mock_file_operations_controller.reset_mock()
        main_window._save_action.trigger()
        mock_file_operations_controller.save_file.assert_called_once()

        # Test save_as_file action
        mock_file_operations_controller.reset_mock()
        main_window._save_as_action.trigger()
        mock_file_operations_controller.save_file_as.assert_called_once()

        # Test import_csv action
        mock_file_operations_controller.reset_mock()
        main_window._import_action.trigger()
        mock_file_operations_controller.import_csv.assert_called_once()

        # Test export_csv action
        mock_file_operations_controller.reset_mock()
        main_window._export_action.trigger()
        mock_file_operations_controller.export_csv.assert_called_once()

    def test_file_operations_signals(
        self, main_window, mock_file_operations_controller, mock_data_model, monkeypatch
    ):
        """Test MainWindow response to FileOperationsController signals."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Mock MainWindow methods to verify they're called
        update_ui_mock = MagicMock()
        monkeypatch.setattr(main_window, "_update_ui", update_ui_mock)

        status_message_mock = MagicMock()
        monkeypatch.setattr(main_window, "_set_status_message", status_message_mock)

        # Test file_open_completed signal
        mock_file_operations_controller.file_open_completed.emit(True, "File opened successfully")
        update_ui_mock.assert_called_once()
        status_message_mock.assert_called_with("File opened successfully")

        # Reset mocks
        update_ui_mock.reset_mock()
        status_message_mock.reset_mock()

        # Test file_save_completed signal
        mock_file_operations_controller.file_save_completed.emit(True, "File saved successfully")
        status_message_mock.assert_called_with("File saved successfully")

    def test_progress_controller_interactions(
        self, main_window, mock_progress_controller, mock_data_model, monkeypatch
    ):
        """Test interactions with ProgressController."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Mock status bar methods
        show_progress_mock = MagicMock()
        update_progress_mock = MagicMock()
        hide_progress_mock = MagicMock()

        monkeypatch.setattr(main_window._status_bar, "show_progress", show_progress_mock)
        monkeypatch.setattr(main_window._status_bar, "update_progress", update_progress_mock)
        monkeypatch.setattr(main_window._status_bar, "hide_progress", hide_progress_mock)

        # Test progress_started signal
        mock_progress_controller.progress_started.emit("Loading data...")
        show_progress_mock.assert_called_once()

        # Test progress_updated signal
        mock_progress_controller.progress_updated.emit(50, 100, "Processing...")
        update_progress_mock.assert_called_with(50, 100, "Processing...")

        # Test progress_completed signal
        mock_progress_controller.progress_completed.emit(True, "Loading complete")
        hide_progress_mock.assert_called_once()

    def test_data_view_controller_interactions(
        self, main_window, mock_data_view_controller, mock_data_model, monkeypatch
    ):
        """Test interactions with DataViewController."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Test data filter signal
        filter_params = {"column": "Age", "operator": ">", "value": 30}
        mock_data_view_controller.data_filtered.emit(filter_params)

        # Test data sort signal
        sort_params = {"column": "Name", "order": "ascending"}
        mock_data_view_controller.data_sorted.emit(sort_params)

        # Test selection change signal
        selected_rows = [1, 3, 5]
        mock_data_view_controller.data_selection_changed.emit(selected_rows)

        # For these signals, we're just testing that they don't cause exceptions
        # In a real application, main_window would do something with these signals
        # but it's difficult to test without knowing exact implementation details

    def test_view_state_controller_signal_connections(
        self, main_window, mock_view_state_controller, mock_data_model
    ):
        """Verify ViewStateController signals are connected."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Ensure the view_changed signal is connected
        assert len(mock_view_state_controller.view_changed.callbacks) > 0

        # Ensure the data_state_changed signal is connected
        assert len(mock_view_state_controller.data_state_changed.callbacks) > 0

    def test_ui_state_controller_interactions(
        self, main_window, mock_ui_state_controller, mock_data_model, monkeypatch
    ):
        """Test interactions with UIStateController."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Test theme_changed signal
        mock_ui_state_controller.theme_changed.emit("dark")

        # Test layout_changed signal
        layout_params = {"sidebar_visible": True, "status_bar_visible": True}
        mock_ui_state_controller.layout_changed.emit(layout_params)

        # For these signals, we're verifying they don't cause exceptions
        # In a real application, MainWindow would update UI based on these signals

    def test_controller_disconnection_during_cleanup(self, qtbot, mock_controllers, mock_data_model):
        """Test that controller signals are disconnected on close."""
        # Explicitly set has_data on the mock
        mock_data_model.has_data = True
        # Create additional methods on controllers to track disconnection
        mock_view_state_controller = mock_controllers["view_state"]
        mock_view_state_controller.disconnect_from_view = MagicMock()

        # Create a MainWindow instance (ensure proper indentation for the following block)
        main_window = MainWindow(
            data_model=mock_data_model,
            # Pass other necessary mocks from mock_controllers
            file_operations_controller=mock_controllers["file"],
            progress_controller=mock_controllers["progress"],
            view_state_controller=mock_controllers["view_state"],
            data_view_controller=mock_controllers["data_view"],
            ui_state_controller=mock_controllers["ui_state"],
            config_manager=MagicMock(),  # Add mock config manager
            table_state_manager=MagicMock(),  # Add mock state manager
            # Add mocks for services if needed by MainWindow init
            csv_service=MagicMock(),
            validation_service=MagicMock(),
            correction_service=MagicMock(),
            chart_service=MagicMock(),
            data_manager=MagicMock(),
        )
        qtbot.addWidget(main_window)

        # Simulate closing the window
        main_window.close()

        # Check if disconnection methods were called (adapt based on actual implementation)
        mock_view_state_controller.disconnect_from_view.assert_called_once()
