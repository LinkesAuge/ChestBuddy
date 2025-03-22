"""
data_manager.py

Description: Service for managing data file operations including loading, saving, and conversion.
Usage:
    data_manager = DataManager(data_model, csv_service)
    data_manager.load_csv(file_path)
"""

import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any

import pandas as pd
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.config import ConfigManager
from chestbuddy.utils.background_processing import BackgroundWorker

# Set up logger
logger = logging.getLogger(__name__)


class DataManager(QObject):
    """
    Service for managing data file operations.

    This class handles all data file operations including loading,
    saving, and conversion between file formats and data model.

    Attributes:
        _data_model: Data model to be updated
        _csv_service: Service for handling CSV file operations
        _config: Configuration manager instance
        _worker: Background worker for async operations

    Implementation Notes:
        - Manages file loading and saving
        - Updates data model with file contents
        - Tracks recent files
        - Maps file columns to data model columns
    """

    # Define signals
    load_success = Signal(str)  # Path of loaded file
    load_error = Signal(str)  # Error message
    save_success = Signal(str)  # Path of saved file
    save_error = Signal(str)  # Error message

    def __init__(self, data_model, csv_service) -> None:
        """
        Initialize the DataManager service.

        Args:
            data_model: Data model to be updated
            csv_service: Service for handling CSV file operations
        """
        super().__init__()

        self._data_model = data_model
        self._csv_service = csv_service

        # Initialize config and background worker
        self._config = ConfigManager()
        self._worker = BackgroundWorker()

        # Connect worker signals
        self._worker.task_completed.connect(self._on_background_task_completed)
        self._worker.task_failed.connect(self._on_background_task_failed)

    def load_csv(self, file_path: str) -> None:
        """
        Load a CSV file and update the data model.

        Args:
            file_path: Path to the CSV file
        """
        logger.info(f"Loading CSV file: {file_path}")

        # Add the file to the list of recent files
        self._update_recent_files(file_path)

        # Temporarily disconnect data_changed signals during import to prevent cascading updates
        self._data_model.blockSignals(True)
        try:
            # Use the background worker to load the file
            self._worker.run_task(
                self._csv_service.read_csv,
                file_path,
                task_id="load_csv",
                on_success=self._on_csv_load_success,
            )
        except Exception as e:
            # Ensure signals are unblocked even if an error occurs
            self._data_model.blockSignals(False)
            logger.error(f"Error during CSV import: {e}")
            self.load_error.emit(f"Error loading file: {str(e)}")

    def _update_recent_files(self, file_path: str) -> None:
        """
        Update the list of recent files in the configuration.

        Args:
            file_path: Path to add to recent files
        """
        recent_files = self._config.get_list("Files", "recent_files", [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        # Keep only the 5 most recent files
        recent_files = recent_files[:5]
        self._config.set_list("Files", "recent_files", recent_files)
        self._config.set("Files", "last_file", file_path)
        self._config.set_path("Files", "last_directory", os.path.dirname(file_path))

    def _on_csv_load_success(self, result) -> None:
        """
        Handle successful CSV load.

        Args:
            result: Tuple containing DataFrame and error (if any)
        """
        try:
            df, error = result
            if df is not None:
                # Map CSV column names to expected column names in the data model
                df = self._map_columns(df)

                # Update the data model with signals blocked
                self._data_model.update_data(df)
                logger.info(f"CSV file loaded successfully with {len(df)} rows")

                # Emit success signal
                self.load_success.emit(str(df.shape[0]))
            else:
                self.load_error.emit(f"Error loading file: {error}")
        finally:
            # Always unblock signals when done
            self._data_model.blockSignals(False)
            # Emit one controlled data_changed signal
            self._data_model.data_changed.emit()

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map DataFrame columns to expected column names in the data model.

        Args:
            df: DataFrame with columns to map

        Returns:
            DataFrame with mapped column names
        """
        # Define column mapping
        column_mapping = {
            "DATE": "Date",
            "PLAYER": "Player Name",
            "SOURCE": "Source/Location",
            "CHEST": "Chest Type",
            "SCORE": "Value",
            "CLAN": "Clan",
        }

        # Rename columns if they exist in the DataFrame
        for csv_col, model_col in column_mapping.items():
            if csv_col in df.columns:
                df.rename(columns={csv_col: model_col}, inplace=True)
                logger.info(f"Mapped column {csv_col} to {model_col}")

        # Log mapped columns for debugging
        logger.info(f"DataFrame columns after mapping: {df.columns.tolist()}")

        return df

    def save_csv(self, file_path: str) -> None:
        """
        Save data model to a CSV file.

        Args:
            file_path: Path to save the CSV file
        """
        logger.info(f"Saving CSV file: {file_path}")

        # Get the dataframe from the model
        df = self._data_model.data

        # Use the background worker to save the file
        self._worker.run_task(
            self._csv_service.write_csv,
            file_path,
            df,
            task_id="save_csv",
        )

    def _on_background_task_completed(self, task_id: str, result: Any) -> None:
        """
        Handle background task completion.

        Args:
            task_id: Identifier of the completed task
            result: Result of the task
        """
        logger.info(f"Background task completed: {task_id}")

        if task_id == "save_csv":
            success, file_path = result
            if success:
                self.save_success.emit(file_path)
            else:
                self.save_error.emit(f"Error saving file: {file_path}")

    def _on_background_task_failed(self, task_id: str, error: str) -> None:
        """
        Handle background task failure.

        Args:
            task_id: Identifier of the failed task
            error: Error message
        """
        logger.error(f"Background task failed: {task_id}, error: {error}")

        if task_id == "load_csv":
            self.load_error.emit(f"Error loading file: {error}")
        elif task_id == "save_csv":
            self.save_error.emit(f"Error saving file: {error}")
