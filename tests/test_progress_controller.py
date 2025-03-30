"""
test_progress_controller.py

Description: Tests for the ProgressController class
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from chestbuddy.core.controllers.progress_controller import ProgressController


class TestProgressController:
    """Test suite for the ProgressController class."""

    def test_init(self):
        """Test controller initialization."""
        controller = ProgressController()
        assert controller._progress_dialog is None
        assert controller._cancel_callback is None
        assert controller._is_cancelable is False
        assert controller._loading_state == controller._init_loading_state()
        assert controller._total_rows_loaded == 0
        assert controller._last_progress_current == 0
        assert controller._file_loading_complete is False
        assert controller._file_sizes == {}

    def test_init_loading_state(self):
        """Test loading state initialization."""
        controller = ProgressController()
        loading_state = controller._init_loading_state()

        assert isinstance(loading_state, dict)
        assert "current_file" in loading_state
        assert "current_file_index" in loading_state
        assert "processed_files" in loading_state
        assert "total_files" in loading_state
        assert "total_rows" in loading_state

        assert loading_state["current_file"] == ""
        assert loading_state["current_file_index"] == 0
        assert loading_state["processed_files"] == []
        assert loading_state["total_files"] == 0
        assert loading_state["total_rows"] == 0

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_start_progress(self, mock_dialog_class):
        """Test starting a progress operation."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Mock callback
        mock_callback = MagicMock()

        # Start progress
        result = controller.start_progress(
            "Test Title", "Test Message", cancelable=True, cancel_callback=mock_callback
        )

        # Verify dialog was created with correct parameters
        mock_dialog_class.assert_called_once()
        args, kwargs = mock_dialog_class.call_args
        assert args[0] == "Test Message"  # label_text
        assert args[1] == "Cancel"  # cancel_button_text

        # Verify result and connections
        assert result is True
        assert controller._cancel_callback == mock_callback
        assert controller._is_cancelable is True
        mock_dialog.canceled.connect.assert_called_once()
        mock_dialog.show.assert_called_once()

        # Verify loading state was reset
        assert controller._loading_state == controller._init_loading_state()
        assert controller._total_rows_loaded == 0
        assert controller._last_progress_current == 0
        assert controller._file_loading_complete is False
        assert controller._file_sizes == {}

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_update_progress(self, mock_dialog_class):
        """Test updating progress."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Start progress first
        controller.start_progress("Test", "Initial message")

        # Update progress
        controller.update_progress(
            50, 100, message="Updated message", file_info="File 1 of 2", status_text="50% complete"
        )

        # Verify dialog properties were updated
        mock_dialog.setValue.assert_called_with(50)
        mock_dialog.setLabelText.assert_called_with("Updated message")
        mock_dialog.setFileInfo.assert_called_with("File 1 of 2")
        mock_dialog.setStatusText.assert_called_with("50% complete")

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_update_file_progress_new_file(self, mock_dialog_class):
        """Test updating file progress with a new file."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Start progress first
        controller.start_progress("Test", "Initial message")

        # Set total files
        controller.set_total_files(2)

        # Update progress with a file
        controller.update_file_progress("file1.csv", 50, 100)

        # Verify loading state was updated
        assert controller._loading_state["current_file"] == "file1.csv"
        assert controller._loading_state["current_file_index"] == 1
        assert "file1.csv" in controller._loading_state["processed_files"]
        assert controller._loading_state["total_rows"] == 100
        assert controller._total_rows_loaded == 50
        assert controller._last_progress_current == 50

        # Verify dialog was updated with proper formatting
        mock_dialog.setValue.assert_called_with(50)
        mock_dialog.setLabelText.assert_called()  # Message formatting tested separately

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_update_file_progress_multiple_files(self, mock_dialog_class):
        """Test updating file progress with multiple files."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Start progress first
        controller.start_progress("Test", "Initial message")

        # Set total files
        controller.set_total_files(2)

        # Update progress with first file
        controller.update_file_progress("file1.csv", 100, 100)

        # Update progress with second file
        controller.update_file_progress("file2.csv", 50, 200)

        # Verify loading state was updated
        assert controller._loading_state["current_file"] == "file2.csv"
        assert controller._loading_state["current_file_index"] == 2
        assert len(controller._loading_state["processed_files"]) == 2
        assert "file1.csv" in controller._loading_state["processed_files"]
        assert "file2.csv" in controller._loading_state["processed_files"]
        assert controller._loading_state["total_rows"] == 200
        assert controller._file_sizes["file1.csv"] == 100  # Size of completed file

        # When moving from file1 to file2, the last_progress_current is reset to 0
        # So only the current progress of file2 is counted (50), not the sum
        assert controller._total_rows_loaded == 100

        # Verify dialog was updated
        mock_dialog.setValue.assert_called_with(25)  # 50/200 = 25%

    def test_format_progress_messages(self):
        """Test formatting of progress messages."""
        controller = ProgressController()

        # Set up loading state
        controller._loading_state = {
            "current_file": "test.csv",
            "current_file_index": 1,
            "processed_files": ["test.csv"],
            "total_files": 2,
            "total_rows": 100,
        }
        controller._total_rows_loaded = 50

        # Test formatting with normal progress
        message, file_info, total_progress = controller._format_progress_messages(50, 100)

        assert "File 1 of 2: test.csv" in message
        assert "50,000 rows" not in message  # Should use current value, not total
        assert "50 rows read" in message
        assert file_info == "File 1 of 2: test.csv"
        assert total_progress == "Total: 50 rows"

        # Test with no total files
        controller._loading_state["total_files"] = 0
        message, file_info, total_progress = controller._format_progress_messages(50, 100)

        assert "Loading test.csv" in message
        assert "50 rows" in message
        assert file_info is None
        assert total_progress == ""

        # Test with no file
        controller._loading_state["current_file"] = ""
        message, file_info, total_progress = controller._format_progress_messages(50, 100)

        assert "Loading files" in message
        assert "50 rows" in message
        assert file_info is None
        assert total_progress == ""

    def test_set_total_files(self):
        """Test setting total files."""
        controller = ProgressController()

        controller.set_total_files(5)
        assert controller._loading_state["total_files"] == 5

        controller.set_total_files(10)
        assert controller._loading_state["total_files"] == 10

    def test_mark_file_loading_complete(self):
        """Test marking file loading as complete."""
        controller = ProgressController()

        assert not controller.is_file_loading_complete()

        controller.mark_file_loading_complete()
        assert controller.is_file_loading_complete()

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_finish_progress(self, mock_dialog_class):
        """Test finishing progress."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Create a spy for the signal
        signal_spy = MagicMock()
        controller.progress_completed.connect(signal_spy)

        # Start progress first
        controller.start_progress("Test", "Initial message")

        # Finish progress
        controller.finish_progress("Operation completed successfully")

        # Verify dialog properties were updated
        if hasattr(mock_dialog, "setState"):
            mock_dialog.setState.assert_called()
        mock_dialog.setLabelText.assert_called_with("Operation complete")
        mock_dialog.setStatusText.assert_called_with("Operation completed successfully")
        mock_dialog.setValue.assert_called()
        mock_dialog.setCancelButtonText.assert_called_with("Confirm")
        mock_dialog.setCancelButtonEnabled.assert_called_with(True)

        # Verify signal was emitted (via our connected spy)
        signal_spy.assert_called_once()

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_finish_progress_with_error(self, mock_dialog_class):
        """Test finishing progress with an error."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Start progress first
        controller.start_progress("Test", "Initial message")

        # Finish progress with error
        controller.finish_progress("An error occurred", is_error=True)

        # Verify dialog properties were updated
        if hasattr(mock_dialog, "setState"):
            mock_dialog.setState.assert_called()
        mock_dialog.setLabelText.assert_called_with("Operation failed")
        mock_dialog.setStatusText.assert_called_with("An error occurred")
        mock_dialog.setValue.assert_called()
        mock_dialog.setCancelButtonText.assert_called_with("Close")
        mock_dialog.setCancelButtonEnabled.assert_called_with(True)

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_close_progress(self, mock_dialog_class):
        """Test closing progress dialog."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Start progress first
        controller.start_progress("Test", "Initial message")

        # Verify dialog is created
        assert controller._progress_dialog is not None

        # Close progress
        controller.close_progress()

        # Verify dialog is closed and references cleared
        mock_dialog.close.assert_called_once()
        assert controller._progress_dialog is None
        assert controller._cancel_callback is None

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_is_progress_showing(self, mock_dialog_class):
        """Test is_progress_showing method."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Initially no dialog
        assert controller.is_progress_showing() is False

        # Start progress
        controller.start_progress("Test", "Initial message")

        # Now dialog is showing
        assert controller.is_progress_showing() is True

        # Close dialog
        controller.close_progress()

        # Dialog is no longer showing
        assert controller.is_progress_showing() is False

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_cancel_signal(self, mock_dialog_class):
        """Test cancel signal is emitted when cancel button is clicked."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Create a spy for the signal
        signal_spy = MagicMock()
        controller.progress_canceled.connect(signal_spy)

        # Start progress
        controller.start_progress("Test", "Initial message", cancelable=True)

        # Simulate cancel
        controller._on_cancel_clicked()

        # Verify signal was emitted (via our connected spy)
        signal_spy.assert_called_once()

    @patch("chestbuddy.core.controllers.progress_controller.ProgressDialog")
    def test_cancel_callback(self, mock_dialog_class):
        """Test cancel callback is called when cancel button is clicked."""
        # Setup mock
        mock_dialog = MagicMock()
        mock_dialog_class.return_value = mock_dialog

        controller = ProgressController()

        # Mock callback
        mock_callback = MagicMock()

        # Start progress with callback
        controller.start_progress(
            "Test", "Initial message", cancelable=True, cancel_callback=mock_callback
        )

        # Simulate cancel button click
        controller._on_cancel_clicked()

        # Verify callback was called
        mock_callback.assert_called_once()
