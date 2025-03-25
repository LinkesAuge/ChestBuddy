"""
test_file_operations_controller.py

Description: Tests for the FileOperationsController class
"""

import unittest
from unittest.mock import MagicMock, patch
import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QFileDialog

from chestbuddy.core.controllers import FileOperationsController
from chestbuddy.utils.config import ConfigManager


class TestFileOperationsController(unittest.TestCase):
    """Tests for the FileOperationsController class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock data manager
        self.data_manager = MagicMock()

        # Create mock config manager
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get.return_value = []

        # Create controller
        self.controller = FileOperationsController(self.data_manager, self.config_manager)

        # Mock signal handlers
        self.file_opened_handler = MagicMock()
        self.file_saved_handler = MagicMock()
        self.recent_files_changed_handler = MagicMock()
        self.load_csv_triggered_handler = MagicMock()
        self.save_csv_triggered_handler = MagicMock()

        # Connect signals to handlers
        self.controller.file_opened.connect(self.file_opened_handler)
        self.controller.file_saved.connect(self.file_saved_handler)
        self.controller.recent_files_changed.connect(self.recent_files_changed_handler)
        self.controller.load_csv_triggered.connect(self.load_csv_triggered_handler)
        self.controller.save_csv_triggered.connect(self.save_csv_triggered_handler)

    @pytest.fixture(autouse=True)
    def qtbot_fixture(self, qtbot):
        """Fixture to provide qtbot for all tests."""
        self.qtbot = qtbot
        return qtbot

    def test_init_empty_recent_files(self):
        """Test initialization with empty recent files."""
        # Config manager returns empty list
        self.config_manager.get.return_value = []

        # Create controller
        controller = FileOperationsController(self.data_manager, self.config_manager)

        # Check recent files
        self.assertEqual(controller.get_recent_files(), [])

        # Check that config manager was called
        self.config_manager.get.assert_called_with("recent_files", [])

    def test_init_with_recent_files(self):
        """Test initialization with existing recent files."""
        # Set up mock files that exist
        mock_files = [str(Path.home() / "file1.csv"), str(Path.home() / "file2.csv")]

        # Config manager returns mock files
        self.config_manager.get.return_value = mock_files

        # Patch Path.exists to return True
        with patch("pathlib.Path.exists", return_value=True):
            # Create controller
            controller = FileOperationsController(self.data_manager, self.config_manager)

            # Check recent files
            self.assertEqual(controller.get_recent_files(), mock_files)

            # Check that config manager was called
            self.config_manager.get.assert_called_with("recent_files", [])

    @patch("PySide6.QtWidgets.QFileDialog.exec")
    def test_open_file(self, mock_dialog_exec):
        """Test open_file method."""
        # Set up mock return value
        mock_files = ["/path/to/file1.csv", "/path/to/file2.csv"]
        mock_dialog_exec.return_value = True

        # Mock the QFileDialog.selectedFiles
        with patch("PySide6.QtWidgets.QFileDialog.selectedFiles", return_value=mock_files):
            # Patch Path.exists to return True
            with patch("pathlib.Path.exists", return_value=True):
                # Call method
                self.controller.open_file()

                # Check that file dialog was called
                mock_dialog_exec.assert_called_once()

                # Check that signals were emitted
                self.load_csv_triggered_handler.assert_called_once_with(
                    [str(path) for path in mock_files]
                )

                # Check that recent files were updated
                for file_path in mock_files:
                    self.assertIn(file_path, self.controller.get_recent_files())

                # Check that recent_files_changed signal was emitted
                self.recent_files_changed_handler.assert_called()

                # Check that file_opened signal was emitted (for a single file)
                if len(mock_files) == 1:
                    self.file_opened_handler.assert_called_with(mock_files[0])

                # Check that config was updated
                self.config_manager.set.assert_called()

    def test_open_recent_file_existing(self):
        """Test open_recent_file with existing file."""
        # Set up file path
        file_path = "/path/to/file.csv"

        # Patch Path.exists to return True
        with patch("pathlib.Path.exists", return_value=True):
            # Call method
            self.controller.open_recent_file(file_path)

            # Check that signals were emitted
            self.load_csv_triggered_handler.assert_called_once_with([file_path])
            self.file_opened_handler.assert_called_once_with(file_path)

            # Check that recent files were updated
            self.assertEqual(self.controller.get_recent_files()[0], file_path)

            # Check that recent_files_changed signal was emitted
            self.recent_files_changed_handler.assert_called()

    @patch("PySide6.QtWidgets.QMessageBox.warning")
    def test_open_recent_file_nonexistent(self, mock_warning):
        """Test open_recent_file with non-existent file."""
        # Set up file path
        file_path = "/path/to/nonexistent.csv"

        # Patch Path.exists to return False
        with patch("pathlib.Path.exists", return_value=False):
            # Add file to recent files
            self.controller._recent_files = [file_path]

            # Call method
            self.controller.open_recent_file(file_path)

            # Check that warning was shown
            mock_warning.assert_called_once()

            # Check that no signals were emitted
            self.load_csv_triggered_handler.assert_not_called()
            self.file_opened_handler.assert_not_called()

            # Check that recent files were updated (file removed)
            self.assertEqual(self.controller.get_recent_files(), [])

            # Check that recent_files_changed signal was emitted
            self.recent_files_changed_handler.assert_called()

    def test_save_file_with_path(self):
        """Test save_file with existing file path."""
        # Set up current file path
        file_path = "/path/to/file.csv"
        self.controller._current_file_path = file_path

        # Call method
        self.controller.save_file()

        # Check that signals were emitted
        self.save_csv_triggered_handler.assert_called_once_with(file_path)
        self.file_saved_handler.assert_called_once_with(file_path)

    @patch(
        "chestbuddy.core.controllers.file_operations_controller.FileOperationsController.save_file_as"
    )
    def test_save_file_without_path(self, mock_save_as):
        """Test save_file without file path."""
        # Ensure no current file path
        self.controller._current_file_path = None

        # Call method
        self.controller.save_file()

        # Check that save_file_as was called
        mock_save_as.assert_called_once()

        # Check that no signals were emitted directly (they would be through save_file_as)
        self.save_csv_triggered_handler.assert_not_called()
        self.file_saved_handler.assert_not_called()

    @patch("PySide6.QtWidgets.QFileDialog.exec")
    def test_save_file_as(self, mock_dialog_exec):
        """Test save_file_as method."""
        # Set up mock return value
        file_path = "/path/to/new_file.csv"
        mock_dialog_exec.return_value = True

        # Mock the QFileDialog.selectedFiles
        with patch("PySide6.QtWidgets.QFileDialog.selectedFiles", return_value=[file_path]):
            # Call method
            self.controller.save_file_as()

            # Check that file dialog was called
            mock_dialog_exec.assert_called_once()

            # Check that signals were emitted
            self.save_csv_triggered_handler.assert_called_once_with(file_path)
            self.file_saved_handler.assert_called_once_with(file_path)

            # Check that current file path was updated
            self.assertEqual(self.controller._current_file_path, file_path)

            # Check that recent files were updated
            self.assertEqual(self.controller.get_recent_files()[0], file_path)

            # Check that recent_files_changed signal was emitted
            self.recent_files_changed_handler.assert_called()

    def test_add_recent_file(self):
        """Test add_recent_file method."""
        # Set up file path
        file_path = "/path/to/file.csv"

        # Call method
        self.controller.add_recent_file(file_path)

        # Check that recent files were updated
        self.assertEqual(self.controller.get_recent_files()[0], file_path)

        # Check that recent_files_changed signal was emitted
        self.recent_files_changed_handler.assert_called_once()

        # Check that config was updated
        self.config_manager.set.assert_called_with("recent_files", [file_path])

    def test_add_recent_file_moves_to_top(self):
        """Test that adding an existing file moves it to the top."""
        # Set up initial recent files
        file1 = "/path/to/file1.csv"
        file2 = "/path/to/file2.csv"
        self.controller._recent_files = [file1, file2]

        # Reset mock
        self.recent_files_changed_handler.reset_mock()

        # Add file2 (already in list)
        self.controller.add_recent_file(file2)

        # Check that file2 is now at the top
        self.assertEqual(self.controller.get_recent_files()[0], file2)
        self.assertEqual(self.controller.get_recent_files()[1], file1)

        # Check that recent_files_changed signal was emitted
        self.recent_files_changed_handler.assert_called_once()

    def test_recent_files_limit(self):
        """Test that recent files list is limited to 10 items."""
        # Add 11 files
        for i in range(11):
            self.controller.add_recent_file(f"/path/to/file{i}.csv")

        # Check that only 10 files are stored
        self.assertEqual(len(self.controller.get_recent_files()), 10)

        # Check that the first file added was removed
        self.assertNotIn("/path/to/file0.csv", self.controller.get_recent_files())

        # Check that the last file added is at the top
        self.assertEqual(self.controller.get_recent_files()[0], "/path/to/file10.csv")

    def test_get_current_file_path(self):
        """Test get_current_file_path method."""
        # Set up current file path
        file_path = "/path/to/file.csv"
        self.controller._current_file_path = file_path

        # Check that get_current_file_path returns the correct path
        self.assertEqual(self.controller.get_current_file_path(), file_path)

    def test_set_current_file_path(self):
        """Test set_current_file_path method."""
        # Set up file path
        file_path = "/path/to/file.csv"

        # Call method
        self.controller.set_current_file_path(file_path)

        # Check that current file path was updated
        self.assertEqual(self.controller._current_file_path, file_path)

        # Check that we can clear it
        self.controller.set_current_file_path(None)
        self.assertIsNone(self.controller._current_file_path)


if __name__ == "__main__":
    unittest.main()
