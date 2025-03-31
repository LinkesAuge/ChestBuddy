"""
tests/ui/test_main_window_file_operations.py

Tests for file operation functionality in MainWindow using the new view-based architecture.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from PySide6.QtWidgets import QAction, QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from chestbuddy.ui.main_window import MainWindow
from chestbuddy.controllers.file_operations_controller import FileOperationsController
from chestbuddy.controllers.view_state_controller import ViewStateController
from chestbuddy.controllers.ui_state_controller import UIStateController
from chestbuddy.controllers.data_view_controller import DataViewController
from chestbuddy.controllers.progress_controller import ProgressController


# Helper class for catching signals
class SignalCatcher:
    def __init__(self):
        self.signal_received = False
        self.signal_args = None

    def handler(self, *args):
        self.signal_received = True
        self.signal_args = args


# Controller fixtures
@pytest.fixture
def file_operations_controller():
    """Create a mock file operations controller."""
    controller = MagicMock(spec=FileOperationsController)
    return controller


@pytest.fixture
def view_state_controller():
    """Create a mock view state controller."""
    controller = MagicMock(spec=ViewStateController)
    return controller


@pytest.fixture
def ui_state_controller():
    """Create a mock UI state controller."""
    controller = MagicMock(spec=UIStateController)
    return controller


@pytest.fixture
def progress_controller():
    """Create a mock progress controller."""
    controller = MagicMock(spec=ProgressController)
    return controller


@pytest.fixture
def data_view_controller():
    """Create a mock data view controller."""
    controller = MagicMock(spec=DataViewController)
    return controller


# Basic fixtures
@pytest.fixture
def test_csv_path(tmp_path):
    """Create a test CSV file path."""
    file_path = tmp_path / "test_data.csv"
    return file_path


@pytest.fixture
def main_window(
    qtbot,
    data_model,
    csv_service,
    validation_service,
    correction_service,
    chart_service,
    data_manager,
    file_operations_controller,
    progress_controller,
    view_state_controller,
    data_view_controller,
    ui_state_controller,
    config_mock,
):
    """Create a MainWindow instance for testing with mocked controllers."""
    with patch("chestbuddy.utils.config.ConfigManager", return_value=config_mock):
        window = MainWindow(
            data_model=data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=file_operations_controller,
            progress_controller=progress_controller,
            view_state_controller=view_state_controller,
            data_view_controller=data_view_controller,
            ui_state_controller=ui_state_controller,
            config_manager=config_mock,
        )
        qtbot.addWidget(window)
        window.show()
        # Allow time for the window to fully initialize
        qtbot.wait(50)
        yield window
        # Proper cleanup to avoid signal disconnection warnings
        window.close()
        QApplication.processEvents()  # Process any pending events


class TestMainWindowFileOperations:
    """Tests for file operation functionality in MainWindow."""

    def test_open_file_action(self, qtbot, main_window, file_operations_controller, test_csv_path):
        """Test the open file action using the file operations controller."""
        # Reset mock to check calls
        file_operations_controller.open_file.reset_mock()

        # Mock QFileDialog to return our test path
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(test_csv_path)], "")):
            # Find and trigger the open action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Open..." or action.text() == "&Open":
                    action.trigger()
                    break

        # Verify controller method was called with correct paths
        file_operations_controller.open_file.assert_called_once_with([str(test_csv_path)])

    def test_save_file_action(self, qtbot, main_window, file_operations_controller):
        """Test the save file action using the file operations controller."""
        # Reset mock to check calls
        file_operations_controller.save_file.reset_mock()

        # Enable the save action (it's disabled by default)
        for action in main_window.findChildren(QAction):
            if action.text() == "&Save":
                action.setEnabled(True)
                action.trigger()
                break

        # Verify controller method was called
        file_operations_controller.save_file.assert_called_once()

    def test_save_as_file_action(self, qtbot, main_window, file_operations_controller):
        """Test the save as file action using the file operations controller."""
        # Reset mock to check calls
        file_operations_controller.save_file_as.reset_mock()

        # Mock file dialog to return a path
        test_save_path = "/path/to/save.csv"
        with patch.object(QFileDialog, "getSaveFileName", return_value=(test_save_path, "")):
            # Enable and trigger the save as action
            for action in main_window.findChildren(QAction):
                if action.text() == "Save &As...":
                    action.setEnabled(True)
                    action.trigger()
                    break

        # Verify controller method was called with correct path
        file_operations_controller.save_file_as.assert_called_once_with(test_save_path)

    def test_export_file_action(self, qtbot, main_window, file_operations_controller):
        """Test the export file action using the file operations controller."""
        # Reset mock to check calls
        file_operations_controller.export_file.reset_mock()

        # Mock file dialog to return a path
        test_export_path = "/path/to/export.csv"
        with patch.object(QFileDialog, "getSaveFileName", return_value=(test_export_path, "")):
            # Enable and trigger the export action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Export...":
                    action.setEnabled(True)
                    action.trigger()
                    break

        # Verify controller method was called with correct path
        file_operations_controller.export_file.assert_called_once_with(test_export_path)

    def test_open_multiple_files(self, qtbot, main_window, file_operations_controller):
        """Test opening multiple files using the file operations controller."""
        # Reset mock to check calls
        file_operations_controller.open_file.reset_mock()

        # Create test file paths
        file_paths = ["/path/to/file1.csv", "/path/to/file2.csv", "/path/to/file3.csv"]

        # Mock QFileDialog to return multiple paths
        with patch.object(QFileDialog, "getOpenFileNames", return_value=(file_paths, "")):
            # Find and trigger the open action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Open..." or action.text() == "&Open":
                    action.trigger()
                    break

        # Verify controller method was called with correct paths
        file_operations_controller.open_file.assert_called_once_with(file_paths)

    def test_file_load_success_signal(self, qtbot, main_window, ui_state_controller):
        """Test handling of file load success signal."""
        # Reset mock to ensure clean state
        ui_state_controller.update_window_title.reset_mock()

        # Simulate file loaded signal
        test_file = "test_data.csv"
        main_window._on_file_loaded(test_file)

        # Verify UI state controller was called to update window title
        ui_state_controller.update_window_title.assert_called_with(test_file)

    def test_recent_files_menu(self, qtbot, main_window, file_operations_controller, config_mock):
        """Test the recent files menu functionality."""
        # Mock recent files in config
        recent_files = ["/path/to/file1.csv", "/path/to/file2.csv", "/path/to/file3.csv"]
        config_mock.get_recent_files.return_value = recent_files

        # Force recent files menu update
        main_window._update_recent_files_menu()

        # Reset mock to check calls
        file_operations_controller.open_file.reset_mock()

        # Find and trigger the first recent file action
        for action in main_window.findChildren(QAction):
            if hasattr(action, "data") and action.data() == recent_files[0]:
                action.trigger()
                break

        # Verify controller method was called with correct path
        file_operations_controller.open_file.assert_called_once_with([recent_files[0]])

    def test_file_operations_with_view_switching(
        self, qtbot, main_window, file_operations_controller, view_state_controller
    ):
        """Test file operations with view switching."""
        # Reset mocks to ensure clean state
        file_operations_controller.open_file.reset_mock()
        view_state_controller.set_active_view.reset_mock()

        # Mock QFileDialog to return a test path
        test_file_path = "/path/to/test.csv"
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([test_file_path], "")):
            # Find and trigger the open action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Open..." or action.text() == "&Open":
                    action.trigger()
                    break

        # Verify file operations controller was called
        file_operations_controller.open_file.assert_called_once_with([test_file_path])

        # Simulate file loaded event that should trigger view switch
        main_window._on_file_loaded(test_file_path)

        # Verify view state controller was called (assuming it switches to Data view on load)
        view_state_controller.set_active_view.assert_called_with("Data")

    def test_file_dialog_cancellation(self, qtbot, main_window, file_operations_controller):
        """Test handling of file dialog cancellation."""
        # Reset mock to check calls
        file_operations_controller.open_file.reset_mock()

        # Mock QFileDialog to return empty paths (cancel was clicked)
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([], "")):
            # Find and trigger the open action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Open..." or action.text() == "&Open":
                    action.trigger()
                    break

        # Verify controller method was not called
        file_operations_controller.open_file.assert_not_called()
