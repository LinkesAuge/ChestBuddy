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
from PySide6.QtWidgets import QApplication

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
    load_finished = Signal(str)  # Include a message parameter

    # Signal for synchronous table population
    populate_table_requested = Signal(pd.DataFrame)

    # New signal to indicate data is loaded and ready for display
    data_loaded = Signal()

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

        # Set up additional signal connections
        self._connect_signals()

    def load_csv(self, file_paths: Union[str, List[str]]) -> None:
        """
        Load CSV data from file(s) into the data store.

        Args:
            file_paths: Path to CSV file(s) to load
        """
        logger.info(f"Loading CSV data: {file_paths}")

        # Convert single string path to list
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        # Store the files to load for progress tracking
        self._files_to_load = file_paths

        # Signal that loading has started
        logger.debug("Emitting load_started signal")
        self.load_started.emit()

        # Block signals from data model to prevent multiple updates
        self._data_model.blockSignals(True)

        # Create the task
        try:
            logger.debug(f"Creating MultiCSVLoadTask for {len(file_paths)} files")
            task = MultiCSVLoadTask(
                csv_service=self._csv_service,
                file_paths=file_paths,
                chunk_size=100,  # Use smaller chunk size for more granular progress updates
                normalize_text=True,
                robust_mode=True,
            )

            # Connect progress signals to forward them to the UI
            task.progress.connect(self._on_load_progress)
            task.file_progress.connect(self._on_file_progress)
            task.status_signal.connect(lambda status: logger.debug(f"Task status: {status}"))

            # Store the task for potential cancellation
            self._current_task = task

            # Execute the task in the background
            logger.debug(f"Executing MultiCSVLoadTask")
            self._worker.execute_task(task)
        except Exception as e:
            logger.error(f"Error setting up CSV loading task: {e}")
            # Unblock signals if error occurs
            self._data_model.blockSignals(False)
            self.load_error.emit(f"Error setting up CSV loading: {str(e)}")
            self.load_finished.emit(f"Error: {str(e)}")

    def cancel_loading(self) -> None:
        """Cancel any ongoing loading operation."""
        logger.info("DataManager.cancel_loading called")

        # Set the cancellation flag
        self._cancel_requested = True

        # If there's an active task, try to cancel it
        if self._current_task:
            try:
                logger.debug(f"Cancelling current task: {self._current_task}")
                # Signal task to cancel
                self._current_task.cancel()

                # Signal progress completion to clean up any UI
                self.load_finished.emit("Loading cancelled")
            except Exception as e:
                logger.error(f"Error cancelling task: {e}")

        # Reset state variables
        self._current_file_path = None
        self._cancel_requested = False

        # Clean up the task reference
        self._current_task = None

        logger.debug("Loading operation cancelled successfully")

    def _on_load_progress(self, current: int, total: int) -> None:
        """
        Handle progress updates from the worker.

        Args:
            current: Current progress value
            total: Total progress value
        """
        # Check if we're receiving valid progress values
        if total <= 0:
            # Avoid division by zero and show indeterminate progress
            logger.debug("Received invalid progress values: current=%s, total=%s", current, total)
            # Forward a placeholder progress value to indicate activity without percentage
            self.load_progress.emit("", 0, 0)
            return

        # Calculate percentage for consistent progress display
        percentage = min(100, int((current / total) * 100))

        # Log progress at useful intervals to avoid log spam
        if percentage % 10 == 0 or percentage >= 100:
            logger.debug(f"CSV loading progress: {percentage}% ({current}/{total})")

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
        # Forward the file progress signal with the file path
        self.load_progress.emit(file_path, current, total)

    def _on_load_cancelled(self) -> None:
        """Handle task cancellation."""
        logger.info("CSV loading operation cancelled")

        # Unblock data model signals
        self._data_model.blockSignals(False)

        # Clear the current task
        self._current_task = None

        # Emit finished signal with cancellation message
        self.load_finished.emit("Operation cancelled by user")

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
            # Type check the result tuple
            if not isinstance(result_tuple, tuple) or len(result_tuple) != 2:
                logger.error(f"Invalid result format from CSV load: {type(result_tuple)}")
                self.load_error.emit("Invalid result format from CSV service")
                self._data_model.blockSignals(False)
                self.load_finished.emit("Invalid result format from CSV service")
                return

            data, message = result_tuple

            # Validate the DataFrame
            if data is None or not isinstance(data, pd.DataFrame):
                logger.error(f"CSV load did not return valid DataFrame: {type(data)}")
                self.load_error.emit(message or "Failed to load CSV data")
                self._data_model.blockSignals(False)
                self.load_finished.emit(message or "Failed to load CSV data")
                return

            if data.empty:
                logger.warning("CSV load returned empty DataFrame")
                self.load_error.emit("CSV file is empty")
                self._data_model.blockSignals(False)
                self.load_finished.emit("CSV file is empty")
                return

            # Log successful load
            logger.info(f"CSV loaded successfully with {len(data)} rows")

            # Store the file path that was successfully loaded
            if self._current_file_path:
                self._update_recent_files(self._current_file_path)

            # Complete the file loading phase with a success message
            success_message = f"Successfully loaded {len(data):,} rows of data"
            self.load_finished.emit(success_message)

            # Map columns
            mapped_data = self._map_columns(data)

            # Update the data model with the new data - this will trigger data_changed signal
            self._data_model.update_data(mapped_data)

            # Always emit data_loaded signal regardless of whether it's the first file
            # This signal indicates that data is loaded and ready for display
            logger.info("Emitting data_loaded signal")
            self.data_loaded.emit()

            # Unblock signals after data loading
            self._data_model.blockSignals(False)

            # Clear the current task
            self._current_task = None

            # Always emit final success signal to ensure UI is updated
            # This is important for subsequent file loads too
            self.load_success.emit(success_message)
            logger.info("Emitted load_success signal")

        except Exception as e:
            # Ensure signals are unblocked
            self._data_model.blockSignals(False)

            # Log and emit error
            logger.error(f"Error in CSV load success handler: {e}")
            self.load_error.emit(f"Error processing CSV data: {str(e)}")
            self.load_finished.emit(f"Error: {str(e)}")

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
        recent_files = self._config.get("Files", "recent_files", "")
        # Convert to list if needed
        if not isinstance(recent_files, list):
            if recent_files:
                try:
                    import json

                    recent_files = json.loads(recent_files)
                except:
                    recent_files = []
            else:
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
            if Path(file_path).exists():
                valid_files.append(file_path)

        # Update the config if files were removed
        if len(valid_files) != len(recent_files):
            self._config.set_list("Files", "recent_files", valid_files)

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

    def save_csv(self, file_path: str) -> bool:
        """
        Save data model to a CSV file.

        Args:
            file_path: Path to save the CSV file

        Returns:
            True if saving was successful, False otherwise
        """
        # Check if a loading operation is in progress
        if hasattr(self, "_worker") and hasattr(self._worker, "is_running"):
            if self._worker.is_running and self._current_task:
                logger.warning("Cannot save while loading is in progress")
                self.save_error.emit("Cannot save while files are being loaded")
                return False

        logger.info(f"Saving CSV file: {file_path}")

        # Get the dataframe from the model
        df = self._data_model.data

        if df is None or df.empty:
            logger.warning("No data to save")
            self.save_error.emit("No data to save")
            return False

        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save the DataFrame to CSV
            df.to_csv(file_path, index=False)
            logger.info(f"Successfully saved {len(df)} rows to {file_path}")
            self.save_success.emit(file_path)
            return True
        except Exception as e:
            error_msg = f"Error saving to {file_path}: {str(e)}"
            logger.error(error_msg)
            self.save_error.emit(error_msg)
            return False

    def _on_background_task_completed(self, task_id: str, result: Any) -> None:
        """
        Handle completion of a background task.

        Args:
            task_id (str): ID of the completed task
            result (Any): Result of the task
        """
        logger.debug(f"Background task {task_id} completed with result: {type(result)}")

        # Clear current task reference
        self._current_task = None

        # Process the result based on task type
        # If it's a MultiCSVLoadTask, the result will be from the CSV load operation
        if isinstance(result, tuple) and len(result) == 2:
            success, data_or_error = result
            if success and isinstance(data_or_error, pd.DataFrame):
                # Handle successful CSV load
                self._on_csv_load_success((data_or_error, None))
            else:
                # Handle CSV load error
                error_msg = data_or_error if isinstance(data_or_error, str) else str(data_or_error)
                self._on_csv_load_success((None, error_msg))
        else:
            # For other task types or unexpected results
            logger.warning(f"Unhandled task result: {type(result)} for task {task_id}")
            # Try to adapt the result format if possible
            try:
                self._adapt_task_result(result)
            except Exception as e:
                logger.error(f"Error adapting task result: {e}")
                self.load_error.emit(f"Error processing task result: {str(e)}")
                self.load_finished.emit(f"Error: {str(e)}")

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
            self.load_finished.emit("Error: {str(error)}")

            # Clear current task
            self._current_task = None

        elif task_id == "save_csv":
            self.save_error.emit(f"Error saving file: {error}")

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Connect worker signals with better error handling
        try:
            # Use robust connections with try/except blocks for each
            try:
                self._worker.started.connect(lambda: self.load_started.emit())
            except Exception as e:
                logger.error(f"Error connecting worker.started signal: {e}")

            try:
                self._worker.progress.connect(self._on_load_progress)
            except Exception as e:
                logger.error(f"Error connecting worker.progress signal: {e}")

            try:
                # Don't directly connect - use an adapter function
                self._worker.finished.connect(self._adapt_task_result)
            except Exception as e:
                logger.error(f"Error connecting worker.finished signal: {e}")

            # Error handling
            try:
                self._worker.error.connect(
                    lambda e: self.load_error.emit(f"Error loading file: {str(e)}")
                )
            except Exception as e:
                logger.error(f"Error connecting worker.error signal: {e}")

            try:
                self._worker.error.connect(lambda e: self.load_finished.emit(f"Error: {str(e)}"))
            except Exception as e:
                logger.error(f"Error connecting worker.error to load_finished signal: {e}")

            # Cancellation handling
            try:
                self._worker.cancelled.connect(self._on_load_cancelled)
            except Exception as e:
                logger.error(f"Error connecting worker.cancelled signal: {e}")

        except Exception as e:
            logger.error(f"Error in _connect_signals: {e}")

    def _adapt_task_result(self, result):
        """
        Adapt the result from MultiCSVLoadTask to the format expected by _on_csv_load_success.

        The MultiCSVLoadTask returns (success: bool, result: Union[DataFrame, str])
        but _on_csv_load_success expects (DataFrame, str) tuple.

        Args:
            result: Result tuple from the MultiCSVLoadTask
        """
        try:
            logger.debug(f"Adapting task result: {type(result)}")

            # Check if result is the expected tuple format
            if not isinstance(result, tuple):
                logger.error(f"Task result is not a tuple: {type(result)}")
                self._on_csv_load_success((None, f"Invalid result format: {type(result)}"))
                return

            # Unpack the tuple
            success, data_or_error = result

            if success and isinstance(data_or_error, pd.DataFrame):
                # Success case - pass DataFrame and empty message
                self._on_csv_load_success((data_or_error, None))
            else:
                # Error case - pass None and error message
                error_msg = data_or_error if isinstance(data_or_error, str) else str(data_or_error)
                self._on_csv_load_success((None, error_msg))

        except Exception as e:
            logger.error(f"Error adapting task result: {e}")
            self._on_csv_load_success((None, f"Error processing result: {str(e)}"))

    @property
    def total_files(self):
        """Get the total number of files being loaded."""
        # Use our current setting if we have files being loaded
        if hasattr(self, "_files_to_load") and self._files_to_load:
            return len(self._files_to_load)
        # Otherwise return 0
        return 0

    def _handle_generic_error(self, error: Exception, context: str = "") -> None:
        """
        Handle a generic error during data operations.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        # Create an informative error message
        error_message = f"{context}: {str(error)}" if context else str(error)
        logger.error(f"Data manager error: {error_message}")

        # Check if this might be a non-critical error
        is_critical = True

        # Some errors don't warrant stopping the process
        if "warning" in str(error).lower() or "non-critical" in str(error).lower():
            is_critical = False
            logger.warning(f"Non-critical error encountered: {error_message}")

        # File format warnings or parsing issues might be non-critical if some data was loaded
        if "format" in str(error).lower() or "parse" in str(error).lower():
            # Check if we have any data loaded
            if hasattr(self, "_data_model") and self._data_model and not self._data_model.is_empty:
                is_critical = False
                logger.warning(
                    f"Format error but data exists - treating as non-critical: {error_message}"
                )

        # Only emit error for critical errors
        if is_critical:
            self.load_error.emit(error_message)
        else:
            # For non-critical, still log but don't stop the process
            logger.warning(f"Non-critical error: {error_message}")

        # Always make sure signals are unblocked
        if hasattr(self, "_data_model"):
            try:
                self._data_model.blockSignals(False)
            except Exception as e:
                logger.error(f"Error unblocking signals: {e}")

        # Always clear the current task
        self._current_task = None
