"""
tests/ui/test_main_window_data_operations.py

Tests for data loading and saving operations in MainWindow using the new view-based architecture.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from chestbuddy.ui.main_window import MainWindow

# from chestbuddy.controllers.file_operations_controller import FileOperationsController # Commented out - controller not found
# from chestbuddy.controllers.view_state_controller import ViewStateController # Commented out
# from chestbuddy.controllers.ui_state_controller import UIStateController # Commented out
# from chestbuddy.controllers.data_view_controller import DataViewController # Commented out
# from chestbuddy.controllers.progress_controller import ProgressController # Commented out


# Mock data state class
class MockDataState:
    def __init__(self, has_data=False, modified=False):
        self.has_data = has_data
        self.is_modified = modified


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


class TestMainWindowDataOperations:
    """Tests for data loading and saving operations in MainWindow."""

    def test_data_changed_signal_handling(self, qtbot, main_window):
        """Test handling of data_changed signal from the data model."""
        with (
            patch.object(main_window, "_update_ui") as mock_update_ui,
            patch.object(main_window, "_update_data_loaded_state") as mock_update_data_loaded,
        ):
            # Create a mock DataState object with data
            mock_data_state = MockDataState(has_data=True, modified=False)

            # Emit the signal with the DataState object
            main_window._data_model.data_changed.emit(mock_data_state)

            # Check if UI methods were called with correct parameters
            mock_update_ui.assert_called_once()
            mock_update_data_loaded.assert_called_once_with(True)

    def test_data_modified_signal_handling(self, qtbot, main_window):
        """Test handling of data_modified signal from the data model."""
        with (
            patch.object(main_window, "_update_ui") as mock_update_ui,
            patch.object(main_window, "_update_modified_state") as mock_update_modified,
        ):
            # Create a mock DataState object with modified data
            mock_data_state = MockDataState(has_data=True, modified=True)

            # Emit the signal with the DataState object
            main_window._data_model.data_modified.emit(mock_data_state)

            # Check if UI methods were called with correct parameters
            mock_update_ui.assert_called_once()
            mock_update_modified.assert_called_once_with(True)

    def test_update_data_loaded_state(self, qtbot, main_window):
        """Test updating UI based on data loaded state."""
        # Mock actions to check enable state
        save_action = MagicMock()
        export_action = MagicMock()
        validate_action = MagicMock()

        # Mock findChildren to return our mock actions
        with patch.object(
            main_window,
            "findChildren",
            side_effect=[[save_action], [export_action], [validate_action]],
        ):
            # Call method with data loaded
            main_window._update_data_loaded_state(True)

            # Verify actions are enabled
            save_action.setEnabled.assert_called_with(True)
            export_action.setEnabled.assert_called_with(True)
            validate_action.setEnabled.assert_called_with(True)

            # Reset mocks
            save_action.setEnabled.reset_mock()
            export_action.setEnabled.reset_mock()
            validate_action.setEnabled.reset_mock()

            # Call method with no data
            main_window._update_data_loaded_state(False)

            # Verify actions are disabled
            save_action.setEnabled.assert_called_with(False)
            export_action.setEnabled.assert_called_with(False)
            validate_action.setEnabled.assert_called_with(False)

    def test_data_reset_handling(self, qtbot, main_window, ui_state_controller):
        """Test handling of data reset event."""
        # Reset mocks to ensure clean state
        ui_state_controller.update_window_title.reset_mock()

        # Mock data changed signal with no data
        mock_data_state = MockDataState(has_data=False, modified=False)

        # Set up patches to verify method calls
        with (
            patch.object(main_window, "_update_data_loaded_state") as mock_update_data_loaded,
            patch.object(main_window, "_update_modified_state") as mock_update_modified,
        ):
            # Emit data changed signal with no data
            main_window._data_model.data_changed.emit(mock_data_state)

            # Verify UI updates
            mock_update_data_loaded.assert_called_with(False)
            mock_update_modified.assert_called_with(False)
            ui_state_controller.update_window_title.assert_called_with(None)

    def test_file_load_progress(self, qtbot, main_window, progress_controller):
        """Test handling of file load progress updates."""
        # Reset mock to ensure clean state
        progress_controller.show_progress.reset_mock()
        progress_controller.update_progress.reset_mock()

        # Simulate load start
        main_window._on_load_started("test.csv")

        # Verify progress dialog shown
        progress_controller.show_progress.assert_called_once()

        # Simulate progress updates
        main_window._on_load_progress(50, "Loading 50%")

        # Verify progress updated
        progress_controller.update_progress.assert_called_with(50, "Loading 50%")

        # Simulate load completion
        main_window._on_load_finished("Complete")

        # Verify progress dialog hidden
        progress_controller.hide_progress.assert_called_once()

    def test_file_loaded_signal(self, qtbot, main_window, view_state_controller):
        """Test file loaded signal triggers view change."""
        # Reset mock to ensure clean state
        view_state_controller.set_active_view.reset_mock()

        # Create a signal catcher for the file_loaded signal
        catcher = SignalCatcher()
        main_window.file_loaded.connect(catcher.handler)

        # Simulate file loaded
        test_file = "test_data.csv"
        main_window._on_file_loaded(test_file)

        # Verify signal was emitted
        assert catcher.signal_received
        assert catcher.signal_args[0] == test_file

        # Verify view switched to Data view
        view_state_controller.set_active_view.assert_called_with("Data")

    def test_auto_save_prompt_on_exit(self, qtbot, main_window, file_operations_controller):
        """Test auto-save prompt on exit with unsaved changes."""
        # Mock data model to indicate unsaved changes
        main_window._data_model.has_unsaved_changes.return_value = True

        # Mock QMessageBox to return "Yes" (save before exit)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            # Set up closeEvent mock
            close_event = MagicMock()

            # Call close event handler
            main_window.closeEvent(close_event)

            # Verify save method was called
            file_operations_controller.save_file.assert_called_once()

            # Verify event was accepted (window closes)
            close_event.accept.assert_called_once()

    def test_discard_changes_on_exit(self, qtbot, main_window, file_operations_controller):
        """Test discarding changes on exit."""
        # Mock data model to indicate unsaved changes
        main_window._data_model.has_unsaved_changes.return_value = True

        # Mock QMessageBox to return "No" (discard changes)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            # Set up closeEvent mock
            close_event = MagicMock()

            # Call close event handler
            main_window.closeEvent(close_event)

            # Verify save method was not called
            file_operations_controller.save_file.assert_not_called()

            # Verify event was accepted (window closes)
            close_event.accept.assert_called_once()

    def test_cancel_exit(self, qtbot, main_window):
        """Test canceling exit when there are unsaved changes."""
        # Mock data model to indicate unsaved changes
        main_window._data_model.has_unsaved_changes.return_value = True

        # Mock QMessageBox to return "Cancel"
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Cancel):
            # Set up closeEvent mock
            close_event = MagicMock()

            # Call close event handler
            main_window.closeEvent(close_event)

            # Verify event was ignored (window stays open)
            close_event.ignore.assert_called_once()

    def test_processing_state_handling(self, qtbot, main_window):
        """Test handling of processing state changes."""
        # Create mocks for UI update methods
        with (
            patch.object(main_window, "_set_actions_enabled") as mock_set_enabled,
        ):
            # Simulate processing started
            main_window._on_processing_started("Processing data")

            # Verify actions disabled during processing
            mock_set_enabled.assert_called_with(False)

            # Reset mock
            mock_set_enabled.reset_mock()

            # Simulate processing finished
            main_window._on_processing_finished()

            # Verify actions re-enabled after processing
            mock_set_enabled.assert_called_with(True)
