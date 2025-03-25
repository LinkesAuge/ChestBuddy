"""
file_operations_controller.py

Description: Controller for file operations in the ChestBuddy application
Usage:
    controller = FileOperationsController(data_manager, config_manager)
    controller.open_file()
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QFileDialog, QApplication, QMessageBox

from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class FileOperationsController(QObject):
    """
    Controller for file operations in the ChestBuddy application.

    This class handles file dialogs and operations, manages the recent files list,
    and coordinates with DataManager for actual file operations.

    Attributes:
        file_opened (Signal): Emitted when a file is opened
        file_saved (Signal): Emitted when a file is saved
        recent_files_changed (Signal): Emitted when the recent files list changes
        load_csv_triggered (Signal): Emitted when CSV load is triggered
        save_csv_triggered (Signal): Emitted when CSV save is triggered
    """

    # Define signals
    file_opened = Signal(str)  # Path of opened file
    file_saved = Signal(str)  # Path of saved file
    recent_files_changed = Signal(list)  # List of recent files
    load_csv_triggered = Signal(list)  # List of file paths to load
    save_csv_triggered = Signal(str)  # Path to save to

    def __init__(self, data_manager, config_manager: ConfigManager):
        """
        Initialize the FileOperationsController.

        Args:
            data_manager: The data manager instance
            config_manager: The configuration manager instance
        """
        super().__init__()
        self._data_manager = data_manager
        self._config_manager = config_manager
        self._recent_files = []
        self._current_file_path = None
        self._load_recent_files()

    def open_file(self, parent=None):
        """
        Show a file dialog to open one or more CSV files.

        Args:
            parent: Parent widget for the dialog
        """
        file_dialog = QFileDialog(parent)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("CSV files (*.csv);;All files (*.*)")
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if self._current_file_path:
            file_dialog.setDirectory(str(Path(self._current_file_path).parent))
        else:
            # Use the last directory from config or default to documents
            last_dir = self._config_manager.get(
                "last_import_directory", str(Path.home() / "Documents")
            )
            # Fix: Ensure last_dir is a string, not a list
            if isinstance(last_dir, list):
                last_dir = str(Path.home() / "Documents")
            file_dialog.setDirectory(last_dir)

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                # Save the directory for next time
                self._config_manager.set("last_import_directory", str(Path(file_paths[0]).parent))

                # Trigger file load
                self.load_csv_triggered.emit([str(path) for path in file_paths])

                # Update recent files
                for file_path in file_paths:
                    self.add_recent_file(file_path)

                # Update current file path if single file
                if len(file_paths) == 1:
                    self._current_file_path = file_paths[0]
                    self.file_opened.emit(file_paths[0])

    def open_recent_file(self, file_path: str):
        """
        Open a file from the recent files list.

        Args:
            file_path: Path to the file to open
        """
        path = Path(file_path)
        if not path.exists():
            QMessageBox.warning(
                QApplication.activeWindow(),
                "File Not Found",
                f"The file {file_path} does not exist or has been moved.",
            )
            # Remove from recent files
            self._recent_files = [f for f in self._recent_files if f != file_path]
            self._save_recent_files()
            self.recent_files_changed.emit(self._recent_files)
            return

        # Trigger file load
        self.load_csv_triggered.emit([file_path])
        self._current_file_path = file_path
        self.file_opened.emit(file_path)

        # Move to top of recent files
        self.add_recent_file(file_path)

    def save_file(self, parent=None):
        """
        Save the current file or show a save dialog if no current file.

        Args:
            parent: Parent widget for the dialog
        """
        if self._current_file_path:
            self.save_csv_triggered.emit(self._current_file_path)
            self.file_saved.emit(self._current_file_path)
        else:
            self.save_file_as(parent)

    def save_file_as(self, parent=None):
        """
        Show a save dialog to save the current data.

        Args:
            parent: Parent widget for the dialog
        """
        file_dialog = QFileDialog(parent)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("CSV files (*.csv);;All files (*.*)")
        file_dialog.setDefaultSuffix("csv")

        if self._current_file_path:
            file_dialog.setDirectory(str(Path(self._current_file_path).parent))
            file_dialog.selectFile(str(Path(self._current_file_path).name))
        else:
            # Use the last directory from config or default to documents
            last_dir = self._config_manager.get(
                "last_export_directory", str(Path.home() / "Documents")
            )
            # Fix: Ensure last_dir is a string, not a list
            if isinstance(last_dir, list):
                last_dir = str(Path.home() / "Documents")
            file_dialog.setDirectory(last_dir)
            file_dialog.selectFile("chest_data.csv")

        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]

                # Save the directory for next time
                self._config_manager.set("last_export_directory", str(Path(file_path).parent))

                # Trigger file save
                self.save_csv_triggered.emit(file_path)
                self._current_file_path = file_path
                self.file_saved.emit(file_path)

                # Update recent files
                self.add_recent_file(file_path)

    def add_recent_file(self, file_path: str):
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to add to recent files
        """
        # Remove if already exists (to move to top)
        self._recent_files = [f for f in self._recent_files if f != file_path]

        # Add to top of list
        self._recent_files.insert(0, file_path)

        # Limit to 10 recent files
        self._recent_files = self._recent_files[:10]

        # Save to config
        self._save_recent_files()

        # Notify listeners
        self.recent_files_changed.emit(self._recent_files)

    def get_recent_files(self) -> List[str]:
        """
        Get the list of recent files.

        Returns:
            List of recent file paths
        """
        return self._recent_files.copy()

    def _load_recent_files(self):
        """Load recent files from config."""
        recent_files = self._config_manager.get("recent_files", [])
        # Filter out files that don't exist
        self._recent_files = [f for f in recent_files if Path(f).exists()]
        logger.debug(f"Loaded {len(self._recent_files)} recent files from config")

    def _save_recent_files(self):
        """Save recent files to config."""
        self._config_manager.set("recent_files", self._recent_files)
        logger.debug(f"Saved {len(self._recent_files)} recent files to config")

    def get_current_file_path(self) -> Optional[str]:
        """
        Get the current file path.

        Returns:
            Current file path or None if no file is open
        """
        return self._current_file_path

    def set_current_file_path(self, file_path: Optional[str]):
        """
        Set the current file path.

        Args:
            file_path: New current file path or None to clear
        """
        self._current_file_path = file_path
