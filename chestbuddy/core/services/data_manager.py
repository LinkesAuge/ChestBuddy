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
from typing import Callable, Dict, List, Optional, Tuple, Any, Union

import pandas as pd
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.config import ConfigManager
from chestbuddy.utils.background_processing import BackgroundWorker, MultiCSVLoadTask

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
    save_error = Signal(str)

    # New signals for progress reporting
    load_progress = Signal(str, int, int)  # file_path, current progress, total
    load_started = Signal()
    load_finished = Signal()

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
        self._current_task = None  # Track the current task for potential cancellation

        # Initialize config and background worker
        self._config = ConfigManager()
        self._worker = BackgroundWorker()

        # Connect worker signals
        self._worker.task_completed.connect(self._on_background_task_completed)
        self._worker.task_failed.connect(self._on_background_task_failed)
        self._worker.progress.connect(self._on_load_progress)
        self._worker.cancelled.connect(self._on_load_cancelled)

    def load_csv(self, file_paths: Union[str, List[str]]) -> None:
        """
        Load one or more CSV files and update the data model.

        Args:
            file_paths: Path to single CSV file or list of paths
        """
        # Convert single file path to list for consistent handling
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        if not file_paths:
            logger.warning("No files provided to load")
            return

        logger.info(f"Loading {len(file_paths)} CSV file(s)")

        # Store the most recent file path
        self._current_file_path = file_paths[0]

        # Add files to the list of recent files
        for file_path in file_paths:
            self._update_recent_files(file_path)

        # Temporarily disconnect data_changed signals during import to prevent cascading updates
        self._data_model.blockSignals(True)

        try:
            # Emit load started signal
            self.load_started.emit()

            # Create and configure the task
            task = MultiCSVLoadTask(
                file_paths=file_paths,
                csv_service=self._csv_service,
                chunk_size=1000,  # Default chunk size
                normalize_text=True,
                robust_mode=True,
            )

            # Connect file progress signal
            task.file_progress.connect(self._on_file_progress)

            # Store the task for potential cancellation
            self._current_task = task

            # Execute the task
            self._worker.execute_task(task)

        except Exception as e:
            # Ensure signals are unblocked even if an error occurs
            self._data_model.blockSignals(False)
            logger.error(f"Error during CSV import: {e}")
            self.load_error.emit(f"Error loading files: {str(e)}")
            self.load_finished.emit()

    def cancel_loading(self) -> None:
        """
        Cancel the current loading operation if one is in progress.
        """
        if self._current_task is not None and hasattr(self._worker, "cancel"):
            logger.info("Cancelling CSV loading operation")
            self._worker.cancel()

    def _on_load_progress(self, current: int, total: int) -> None:
        """
        Handle progress updates from the worker.

        Args:
            current: Current progress value
            total: Total progress value
        """
        # Forward the progress signal without a file path (overall progress)
        self.load_progress.emit("", current, total)

    def _on_file_progress(self, file_path: str, current: int, total: int) -> None:
        """
        Handle file-specific progress updates from the task.

        Args:
            file_path: Path of the file being processed
            current: Current progress value
            total: Total progress value
        """
        # Forward the file progress signal
        self.load_progress.emit(file_path, current, total)

    def _on_load_cancelled(self) -> None:
        """Handle task cancellation."""
        logger.info("CSV loading operation cancelled")

        # Unblock data model signals
        self._data_model.blockSignals(False)

        # Clear the current task
        self._current_task = None

        # Emit finished signal
        self.load_finished.emit()

        # Emit error signal with cancellation message
        self.load_error.emit("Operation cancelled by user")

    def _load_multiple_files(self, file_paths: List[str]) -> Tuple[pd.DataFrame, str]:
        """
        Load multiple CSV files and combine them into a single DataFrame.

        Args:
            file_paths: List of paths to CSV files

        Returns:
            Tuple containing combined DataFrame and success message
        """
        dfs = []
        error_files = []

        # Process each file
        for file_path in file_paths:
            try:
                logger.info(f"Processing file: {file_path}")
                df, message = self._csv_service.read_csv(file_path)

                if df is not None and not df.empty:
                    # Map columns before combining
                    mapped_df = self._map_columns(df)
                    dfs.append(mapped_df)
                else:
                    logger.warning(f"File {file_path} returned empty DataFrame or error: {message}")
                    error_files.append(f"{os.path.basename(file_path)}: {message}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                error_files.append(f"{os.path.basename(file_path)}: {str(e)}")

        # Check if we have any valid DataFrames
        if not dfs:
            error_message = "No valid data found in the selected files"
            if error_files:
                error_message += f": {', '.join(error_files)}"
            return None, error_message

        # Combine all DataFrames
        try:
            combined_df = pd.concat(dfs, ignore_index=True)

            # Generate success message
            if error_files:
                message = f"Successfully loaded {len(dfs)} file(s). Some files had errors: {', '.join(error_files)}"
            else:
                message = (
                    f"Successfully loaded {len(dfs)} file(s) with {len(combined_df)} total rows."
                )

            return combined_df, message

        except Exception as e:
            logger.error(f"Error combining DataFrames: {e}")
            return None, f"Error combining files: {str(e)}"

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

            # Clear the current task
            self._current_task = None

            # Emit load finished signal
            self.load_finished.emit()

        except Exception as e:
            # Ensure signals are unblocked
            self._data_model.blockSignals(False)

            # Log and emit error
            logger.error(f"Error in CSV load success handler: {e}")
            self.load_error.emit(f"Error processing CSV data: {str(e)}")

            # Emit load finished signal
            self.load_finished.emit()

    def _update_recent_files(self, file_path: str) -> None:
        """
        Update the list of recent files.

        Args:
            file_path: Path to add to recent files
        """
        # Convert to Path for consistent handling
        path = Path(file_path)
        if not path.exists():
            return

        # Normalize the path to absolute
        abs_path = str(path.resolve())

        # Get the current list of recent files
        recent_files = self._config.get_list("Files", "recent_files", [])
        if not isinstance(recent_files, list):
            recent_files = []

        # Remove the path if it's already in the list
        if abs_path in recent_files:
            recent_files.remove(abs_path)

        # Add the path to the beginning of the list
        recent_files.insert(0, abs_path)

        # Limit the list to 10 items
        recent_files = recent_files[:10]

        # Update the config
        self._config.set_list("Files", "recent_files", recent_files)

    def get_recent_files(self) -> List[str]:
        """
        Get the list of recent files.

        Returns:
            List of paths to recent files
        """
        recent_files = self._config.get_list("Files", "recent_files", [])
        if not isinstance(recent_files, list):
            return []

        # Filter out files that no longer exist
        valid_files = []
        for file_path in recent_files:
            try:
                if Path(file_path).exists():
                    valid_files.append(file_path)
            except Exception:
                # Skip invalid paths
                pass

        return valid_files

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map DataFrame columns to the expected column names.

        This method handles different column naming conventions:
        - Uppercase (e.g., 'PLAYER')
        - Title case (e.g., 'Player')
        - Mixed case (e.g., 'playerName')

        Args:
            df: DataFrame to map

        Returns:
            DataFrame with mapped columns
        """
        # Make a copy to avoid modifying the original
        result = df.copy()

        # If the DataFrame is empty, return as is
        if result.empty:
            return result

        # Get the expected columns from the data model
        from chestbuddy.core.models.chest_data_model import ChestDataModel

        expected_columns = ChestDataModel.EXPECTED_COLUMNS

        # Create a mapping of actual column names to expected column names
        # The approach is to:
        # 1. Convert all column names to uppercase
        # 2. Match against expected columns in uppercase
        # 3. When a match is found, rename the column to the expected case (from EXPECTED_COLUMNS)

        # Dictionary to store the mappings
        column_map = {}

        # Upper-case versions of expected columns for matching
        expected_upper = [col.upper() for col in expected_columns]

        # Convert DataFrame column names to uppercase for comparison
        df_cols_upper = [col.upper() for col in result.columns]

        # Look for matches
        for i, col in enumerate(df_cols_upper):
            if col in expected_upper:
                # Get the index of the match in expected_upper
                idx = expected_upper.index(col)
                # Map the actual column name to the expected column name (preserving case)
                column_map[result.columns[i]] = expected_columns[idx]

        # Apply the mapping if any was found
        if column_map:
            result = result.rename(columns=column_map)

        return result

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
        elif task_id == "load_csv":
            # Handle load_csv task completion
            self._on_csv_load_success(result)

    def _on_background_task_failed(self, task_id: str, error: str) -> None:
        """
        Handle background task failure.

        Args:
            task_id: Identifier of the failed task
            error: Error message
        """
        logger.error(f"Background task failed: {task_id}, error: {error}")

        if task_id == "load_csv":
            # Unblock signals
            self._data_model.blockSignals(False)

            # Emit error signal
            self.load_error.emit(f"Error loading file: {error}")

            # Emit finished signal
            self.load_finished.emit()

            # Clear current task
            self._current_task = None

        elif task_id == "save_csv":
            self.save_error.emit(f"Error saving file: {error}")
