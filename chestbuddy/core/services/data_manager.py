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
        _current_file_path: Track the current file path

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
        self._current_file_path = None  # Track the current file path

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

        # Store the current file path
        self._current_file_path = file_path

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

    def _on_csv_load_success(self, result_tuple: Tuple[pd.DataFrame, str]):
        """
        Handle successful CSV load from background thread.

        Args:
            result_tuple: Tuple containing (DataFrame, message)
        """
        try:
            logger.debug("CSV load success callback triggered")
            # Type check the result tuple
            if not isinstance(result_tuple, tuple) or len(result_tuple) != 2:
                logger.error(f"Invalid result format from CSV load: {type(result_tuple)}")
                self.load_error.emit("Invalid result format from CSV service")
                return

            data, message = result_tuple

            # Validate the DataFrame
            if data is None or not isinstance(data, pd.DataFrame):
                logger.error(f"CSV load did not return valid DataFrame: {type(data)}")
                self.load_error.emit(message or "Failed to load CSV data")
                return

            if data.empty:
                logger.warning("CSV load returned empty DataFrame")
                self.load_error.emit("CSV file is empty")
                return

            logger.info(f"CSV loaded successfully with {len(data)} rows")

            # Store the file path that was successfully loaded
            if self._current_file_path:
                self._update_recent_files(self._current_file_path)

            # Attempt to map columns
            mapped_data = self._map_columns(data)

            # Update the data model with the new data
            self._data_model.update_data(mapped_data)

            # Emit success signal with message
            self.load_success.emit(message or "CSV loaded successfully")

            # Finally, unblock signals and emit a controlled change notification
            self._data_model.blockSignals(False)
            self._data_model.data_changed.emit()
        except Exception as e:
            # Ensure signals are unblocked even if an error occurs
            self._data_model.blockSignals(False)

            logger.error(f"Error in CSV load success callback: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.load_error.emit(f"Error processing CSV data: {str(e)}")

    def _map_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Map columns from CSV to the expected format in the data model.

        Args:
            data: The DataFrame with original CSV columns

        Returns:
            DataFrame with mapped columns
        """
        try:
            # Safety check - ensure we have a DataFrame
            if not isinstance(data, pd.DataFrame):
                logger.error(f"Cannot map columns - invalid data type: {type(data)}")
                return pd.DataFrame()  # Return empty DataFrame as fallback

            # Define default mapping for backward compatibility
            # This maps older column names to the new expected format
            default_mapping = {
                # Old format to new format
                "Date": "DATE",
                "Player Name": "PLAYER",
                "Source/Location": "SOURCE",
                "Chest Type": "CHEST",
                "Value": "SCORE",
                "Clan": "CLAN",
                # Already in the new format - identity mapping
                "DATE": "DATE",
                "PLAYER": "PLAYER",
                "SOURCE": "SOURCE",
                "CHEST": "CHEST",
                "SCORE": "SCORE",
                "CLAN": "CLAN",
            }

            # Get column mapping from config, fall back to default if not found
            column_mapping = self._config.get("column_mapping", {})
            if not column_mapping:
                logger.info("No column mapping found in config, using default mapping")
                column_mapping = default_mapping

            # Check if the mapping applies to this data
            csv_columns = set(data.columns)
            mapping_source_cols = set(column_mapping.keys())

            # If none of the mapping source columns exist in the CSV,
            # we probably have the wrong mapping, so skip it
            if not mapping_source_cols.intersection(csv_columns):
                logger.warning("Column mapping doesn't match CSV columns, skipping mapping")
                return data

            # Create a new DataFrame with mapped columns
            mapped_data = pd.DataFrame()

            # Apply mapping for columns that exist in the CSV
            for csv_col, model_col in column_mapping.items():
                if csv_col in data.columns:
                    mapped_data[model_col] = data[csv_col]
                    logger.debug(f"Mapped column {csv_col} to {model_col}")

            # Copy over any unmapped columns
            for col in data.columns:
                if col not in column_mapping:
                    mapped_data[col] = data[col]
                    logger.debug(f"Copied unmapped column: {col}")

            logger.info(f"Mapped columns: {list(mapped_data.columns)}")
            return mapped_data
        except Exception as e:
            logger.error(f"Error mapping columns: {e}")
            import traceback

            logger.error(traceback.format_exc())
            # Return original data as fallback
            return data

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
