"""
file_operations_controller.py

Description: Controller for file operations in the ChestBuddy application
Usage:
    controller = FileOperationsController(data_manager, config_manager, signal_manager)
    controller.open_file()
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QFileDialog, QApplication, QMessageBox, QDialog, QWidget

from chestbuddy.utils.config import ConfigManager
from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.core.models.chest_data_model import ChestDataModel

# Set up logger
logger = logging.getLogger(__name__)


class FileOperationsController(BaseController):
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
        operation_error (Signal): Emitted when an error occurs, with error message
        file_dialog_canceled (Signal): Emitted when a file dialog is canceled without selection
    """

    # Define signals
    file_opened = Signal(str)  # Path of opened file
    file_saved = Signal(str)  # Path of saved file
    recent_files_changed = Signal(list)  # List of recent files
    load_csv_triggered = Signal(list)  # List of file paths to load
    save_csv_triggered = Signal(str)  # Path to save to
    operation_error = Signal(str)  # Error message
    file_dialog_canceled = Signal()  # Emitted when a file dialog is canceled without selection

    def __init__(self, data_manager, config_manager: ConfigManager, signal_manager=None):
        """
        Initialize the FileOperationsController.

        Args:
            data_manager: The data manager instance
            config_manager: The configuration manager instance
            signal_manager: Optional SignalManager instance for connection tracking
        """
        super().__init__(signal_manager)
        self._data_manager = data_manager
        self._config_manager = config_manager
        self._recent_files = []
        self._current_file_path = None
        self._is_showing_dialog = False  # Flag to prevent duplicate dialogs

        # Connect to data manager
        self.connect_to_model(data_manager)

        # Load recent files
        self._load_recent_files()

    def connect_to_model(self, model) -> None:
        """
        Connect to data manager signals.

        Args:
            model: The data manager to connect to
        """
        super().connect_to_model(model)

        # Add model-specific connections if needed
        logger.debug(f"FileOperationsController connected to model: {model.__class__.__name__}")

    def open_file(self, parent: QWidget = None) -> List[str]:
        """
        Open a file dialog for selecting and opening CSV files.

        Args:
            parent (QWidget, optional): Parent widget for the file dialog. Defaults to None.

        Returns:
            List[str]: List of selected file paths, or empty list if canceled.
        """
        logger.debug(f"FileOperationsController.open_file called with parent={parent}")

        # Prevent duplicate dialogs
        if self._is_showing_dialog:
            logger.debug("File dialog already showing, ignoring duplicate request")
            return []

        try:
            self._is_showing_dialog = True
            logger.debug("About to show file open dialog")

            dialog = QFileDialog(parent)
            dialog.setWindowTitle("Open CSV Files")
            dialog.setFileMode(QFileDialog.ExistingFiles)
            dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")
            dialog.selectNameFilter("CSV Files (*.csv)")

            # Set the initial directory to the last used directory or the default
            last_dir = self._get_last_directory()
            if last_dir and os.path.exists(last_dir):
                dialog.setDirectory(last_dir)

            if dialog.exec() == QDialog.Accepted:
                selected_files = dialog.selectedFiles()
                logger.debug(f"User selected {len(selected_files)} files")

                if selected_files:
                    # Save the directory for next time
                    self._save_last_directory(os.path.dirname(selected_files[0]))

                    # Emit signal to trigger data loading and update current file path
                    if selected_files:
                        self.load_csv_triggered.emit(selected_files)
                        if len(selected_files) == 1:
                            self._current_file_path = selected_files[0]
                            self.file_opened.emit(selected_files[0])
                            # Add to recent files
                            self.add_recent_file(selected_files[0])

                    return selected_files
            else:
                logger.debug("User canceled file dialog")
                self.file_dialog_canceled.emit()

            return []
        finally:
            self._is_showing_dialog = False

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

    def save_file_as(self, parent: QWidget = None, initial_path: str = None) -> str:
        """
        Open a file dialog for saving a file.

        Args:
            parent (QWidget, optional): Parent widget for the file dialog. Defaults to None.
            initial_path (str, optional): Suggested initial path for the save dialog. Defaults to None.

        Returns:
            str: Selected file path, or empty string if canceled.
        """
        # Prevent duplicate dialogs
        if self._is_showing_dialog:
            logger.debug("File dialog already showing, ignoring duplicate request")
            return ""

        try:
            self._is_showing_dialog = True
            logger.debug("About to show save file dialog")

            dialog = QFileDialog(parent)
            dialog.setWindowTitle("Save As CSV File")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setFileMode(QFileDialog.AnyFile)
            dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")
            dialog.selectNameFilter("CSV Files (*.csv)")

            # Set default file name
            if initial_path:
                dialog.selectFile(initial_path)
            else:
                dialog.selectFile("chest_data.csv")

            # Set the initial directory to the last used directory or the default
            last_dir = self._get_last_directory()
            if last_dir and os.path.exists(last_dir):
                dialog.setDirectory(last_dir)

            if dialog.exec() == QDialog.Accepted:
                selected_path = dialog.selectedFiles()[0]
                logger.debug(f"User selected file: {selected_path}")

                # If CSV filter was selected and file doesn't have .csv extension, add it
                selected_filter = dialog.selectedNameFilter()
                if selected_filter == "CSV Files (*.csv)" and not selected_path.lower().endswith(
                    ".csv"
                ):
                    selected_path += ".csv"

                # Save the directory for next time
                self._save_last_directory(os.path.dirname(selected_path))

                # Emit signal to trigger data saving and update current file path
                self.save_csv_triggered.emit(selected_path)
                self._current_file_path = selected_path
                self.file_saved.emit(selected_path)
                # Add to recent files
                self.add_recent_file(selected_path)

                return selected_path
            else:
                logger.debug("User canceled save dialog")
                self.file_dialog_canceled.emit()

            return ""
        finally:
            self._is_showing_dialog = False

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
        recent_files = self._config_manager.get_list("Files", "recent_files", [])
        # Handle case where config returns None
        if recent_files is None:
            recent_files = []
        # Filter out files that don't exist
        self._recent_files = [f for f in recent_files if Path(f).exists()]
        logger.debug(f"Loaded {len(self._recent_files)} recent files from config")

    def _save_recent_files(self):
        """Save recent files to config."""
        self._config_manager.set_list("Files", "recent_files", self._recent_files)
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

    def _get_last_directory(self):
        """
        Get the last directory used for file operations from config.

        Returns:
            str: Path to the last used directory or user's documents folder if not set
        """
        from pathlib import Path

        # Get the last directory from config or default to documents
        last_dir = self._config_manager.get(
            "Files", "last_directory", str(Path.home() / "Documents")
        )

        # Fix: Ensure last_dir is a string, not a list
        if isinstance(last_dir, list):
            last_dir = str(Path.home() / "Documents")

        logger.debug(f"Retrieved last directory: {last_dir}")
        return last_dir

    def _save_last_directory(self, directory):
        """
        Save the last directory used for file operations to config.

        Args:
            directory (str): Path to save
        """
        logger.debug(f"Saving last directory: {directory}")
        self._config_manager.set("Files", "last_directory", directory)
