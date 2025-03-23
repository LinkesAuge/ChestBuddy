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
from typing import Callable, Dict, List, Optional, Tuple, Any, Union, Generator
import inspect

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
    load_finished = Signal()

    # Add new signals for chunk processing phase
    chunk_processing_started = Signal()
    chunk_processed = Signal(int, int)  # current_chunk, total_chunks

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
        Load data from one or more CSV files.

        Args:
            file_paths: Path or list of paths to CSV files to load
        """
        # Convert single path to list for unified handling
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        # Convert to list of strings if any are Path objects
        file_paths = [str(path) for path in file_paths]

        logger.info(f"Loading CSV files: {file_paths}")

        # Create a task for loading the CSV files
        self._current_task = "load_csv"
        self._current_file_path = file_paths[0] if file_paths else None

        # Block signals during load to prevent multiple updates
        self._data_model.blockSignals(True)

        # Create a task for loading multiple CSV files
        task = MultiCSVLoadTask(
            csv_service=self._csv_service,
            file_paths=file_paths,
            chunk_size=100,  # Use 100 as requested
            normalize_text=True,
            robust_mode=True,
            task_id="load_csv",
        )

        # Connect to chunk processed signal
        task.chunk_processed.connect(self._on_chunk_processed)

        # Emit load started signal
        self.load_started.emit()

        # Run the task in a background worker
        self._worker.execute_task(task)

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

    def _on_csv_load_success(self, result: Union[Tuple[bool, Union[pd.DataFrame, Generator, str]], Tuple[pd.DataFrame, str]]) -> None:
        """
        Handle successful CSV loading.
        
        Args:
            result: Tuple containing load result information. Can be either:
                   - (success_flag, data_or_error_message)
                   - (dataframe, message) [legacy format]
        """
        try:
            # Stop the task to clean up resources
            self._current_task = None
            
            # Extract result based on format (handle both formats for compatibility)
            success = True
            message = ""
            data_or_generator = None
            
            # Check the result format and extract data accordingly
            if isinstance(result, tuple) and len(result) == 2:
                if isinstance(result[0], bool):
                    # New format: (success_flag, data_or_error_message)
                    success, data_or_generator = result
                    message = "Data loaded successfully" if success else str(data_or_generator)
                else:
                    # Legacy format: (dataframe, message)
                    data_or_generator, message = result
                    success = True if isinstance(data_or_generator, (pd.DataFrame, Generator)) else False
            else:
                # Invalid format
                success = False
                message = "Invalid result format from CSV loading task"
            
            # Check if the operation was successful
            if not success:
                logger.error(f"CSV load failed: {message if message else 'Unknown error'}")
                self.load_error.emit(message if message else "Failed to load CSV data")
                self.load_finished.emit()
                return
                
            # If we received a generator, process chunks incrementally
            if inspect.isgenerator(data_or_generator):
                logger.debug("Received a generator of data chunks, processing incrementally")
                # Signal the start of the processing phase
                self.chunk_processing_started.emit()
                
                # Process in a background thread to keep UI responsive
                self._process_chunks(data_or_generator)
                return
                
            # Otherwise process as a single DataFrame
            elif isinstance(data_or_generator, pd.DataFrame):
                logger.debug(f"Received DataFrame with {len(data_or_generator)} rows")
                # Set the new data
                self._data_model.update_data(data_or_generator)
                # Update the model
                self._data_model.data_changed.emit()
                # Emit signals
                self.load_success.emit(message)
                self.load_finished.emit()
            else:
                # Unknown data type
                error_msg = f"Unknown data type from CSV loading task: {type(data_or_generator)}"
                logger.error(error_msg)
                self.load_error.emit(error_msg)
                self.load_finished.emit()
                
        except Exception as e:
            logger.error(f"Error handling CSV load success: {e}")
            self.load_error.emit(f"Error processing CSV data: {e}")
            self.load_finished.emit()

    def _process_chunks(self, chunks_generator: Generator) -> None:
        """
        Process data chunks from the generator.
        
        Args:
            chunks_generator: Generator yielding DataFrame chunks
        """
        try:
            # Create a local copy of the views list to avoid modification during iteration
            data_views = self._data_model.views.copy() if hasattr(self._data_model, "views") else []
            
            # Clear any existing data in views
            for view in data_views:
                if hasattr(view, "clear_table"):
                    view.clear_table()
                    
            # Initialize counters
            chunk_count = 0
            total_chunks = 0  # This will be updated if available
            combined_data = None
            
            # Process each chunk
            try:
                # Initialize combined data for aggregation
                all_chunks = []
                
                # Process each chunk from the generator
                for result in chunks_generator:
                    # Ensure we haven't been cancelled
                    if self._current_task is None:
                        logger.info("Chunk processing cancelled")
                        break
                        
                    # Check if this is a progress update or a data chunk
                    if isinstance(result, tuple) and len(result) == 3 and isinstance(result[0], str):
                        # This is a progress update (file_path, current, total)
                        continue
                        
                    # This is a data chunk
                    chunk = result
                    chunk_count += 1
                    
                    # Add to combined data
                    all_chunks.append(chunk)
                    
                    # Update data views with this chunk
                    for view in data_views:
                        if hasattr(view, "append_data_chunk"):
                            view.append_data_chunk(chunk)
                    
                    # Emit chunk processed signal
                    total_chunks = max(total_chunks, chunk_count)
                    self.chunk_processed.emit(chunk_count, total_chunks)
                    
                    # Process events to keep UI responsive
                    QApplication.processEvents()
                    
                # Combine all chunks into a single DataFrame
                if all_chunks:
                    combined_data = pd.concat(all_chunks, ignore_index=True)
                    
            except Exception as e:
                logger.error(f"Error processing data chunks: {e}")
                self.load_error.emit(f"Error processing data chunks: {e}")
                combined_data = None
                
            # Final processing after all chunks
            if combined_data is not None and not combined_data.empty:
                # Set the combined data
                self._data_model.update_data(combined_data)
                # Update the model with combined data
                self._data_model.data_changed.emit()
                # Emit success signal
                self.load_success.emit(f"Loaded {len(combined_data)} records")
            else:
                # No data or error occurred
                self.load_error.emit("No data loaded or processing was cancelled")
                
        except Exception as e:
            logger.error(f"Error in chunk processing: {e}")
            self.load_error.emit(f"Error processing data chunks: {e}")
        finally:
            # Always emit load finished
            self.load_finished.emit()

    def _on_chunk_processed(self, current_chunk: int, total_chunks: int) -> None:
        """
        Handle chunk processed signal from MultiCSVLoadTask.

        Args:
            current_chunk: Current chunk number being processed
            total_chunks: Total number of chunks to process
        """
        # Forward the signal to any listeners (like MainWindow)
        self.chunk_processed.emit(current_chunk, total_chunks)

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
        elif task_id == "load_csv" or task_id.startswith("load_multi_csv_"):
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

        if task_id == "load_csv" or task_id.startswith("load_multi_csv_"):
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
