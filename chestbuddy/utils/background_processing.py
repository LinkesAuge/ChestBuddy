"""
Background processing utilities.

This module provides utilities for running operations in the background
while maintaining UI responsiveness. It includes a BackgroundWorker
class that handles thread management and signal coordination, and a
BackgroundTask base class that defines the interface for tasks.
"""

import logging
import traceback
from pathlib import Path
from typing import Any, Optional, Callable, TypeVar, Generic, Dict, List, Tuple, Type, Union
import time
import gc
import pandas as pd

from PySide6.QtCore import QObject, Signal, Slot, QThread, QRunnable, QThreadPool
from PySide6.QtWidgets import QApplication

# Import UI State Management components
from chestbuddy.utils.ui_state import (
    UIStateManager,
    OperationContext,
    UIOperations,
    UIElementGroups,
)

# Setup logger
logger = logging.getLogger(__name__)

# Type variables for task return types
T = TypeVar("T")


class BackgroundTask(QObject, Generic[T]):
    """
    Base class for background tasks.

    A background task is a unit of work that can be executed in a separate thread.
    It provides signals for progress reporting and error handling, and manages
    cancellation state.

    Subclasses must implement the run() method to perform the actual work.
    """

    # Signals
    progress = Signal(int, int)  # current, total
    status_signal = Signal(str)  # status message

    def __init__(self, task_id: str = None) -> None:
        """Initialize the background task."""
        super().__init__()
        self._is_cancelled = False
        self.task_id = task_id or str(id(self))

    @property
    def is_cancelled(self) -> bool:
        """
        Return whether the task has been cancelled.

        Returns:
            True if the task has been cancelled, False otherwise.
        """
        return self._is_cancelled

    def cancel(self) -> None:
        """
        Cancel the task.

        This sets the is_cancelled flag, which the run method should check
        periodically to determine if it should stop execution.
        """
        self._is_cancelled = True
        logger.debug(f"Task {self.__class__.__name__} cancelled")

    def run(self) -> T:
        """
        Execute the task and return the result.

        This method should be implemented by subclasses to perform the actual work.
        It should check is_cancelled periodically and return early if it's True.

        Returns:
            The result of the task.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement run() method")


class MultiCSVLoadTask(BackgroundTask):
    """
    Task to load multiple CSV files, with progress reporting.

    This task loads each CSV file in sequence, emitting progress signals
    along the way. It handles cancellation and error reporting.
    """

    # Additional signal for file-specific progress
    file_progress = Signal(str, int, int)  # file_path, current, total

    def __init__(self, *args, **kwargs):
        """
        Initialize the task with multiple CSV files to load.

        Args:
            Can be called in two ways:
            1. (csv_service, file_paths, chunk_size=1000, ...)
            2. (file_paths=paths, csv_service=service, chunk_size=size, ...)

            csv_service: The CSVService instance to use for loading
            file_paths: List of paths to CSV files to load
            chunk_size: Size of chunks to use when loading CSV files
            normalize_text: Whether to normalize text in CSV files (passed to CSVService)
            robust_mode: Whether to use robust mode for handling corrupt files (passed to CSVService)
            encoding: Optional encoding to use for CSV files (passed to CSVService)
        """
        # Handle different ways this can be called (positional or keyword)
        if args and len(args) >= 2:
            # Called as (csv_service, file_paths, ...)
            csv_service = args[0]
            file_paths = args[1]
            chunk_size = args[2] if len(args) > 2 else kwargs.get("chunk_size", 1000)
        else:
            # Called with keywords: (file_paths=paths, csv_service=service, ...)
            csv_service = kwargs.get("csv_service")
            file_paths = kwargs.get("file_paths")
            chunk_size = kwargs.get("chunk_size", 1000)

        if not csv_service:
            raise ValueError("csv_service is required")
        if not file_paths:
            raise ValueError("file_paths is required")

        # Get other parameters with defaults
        normalize_text = kwargs.get("normalize_text", True)
        robust_mode = kwargs.get("robust_mode", False)
        encoding = kwargs.get("encoding", None)

        # Initialize with task_id based on number of files
        super().__init__(f"load_multi_csv_{len(file_paths)}_files")

        # Store parameters
        self.csv_service = csv_service
        self.file_paths = file_paths
        self.chunk_size = chunk_size
        self.normalize_text = normalize_text
        self.robust_mode = robust_mode
        self.encoding = encoding

        # Initialize other attributes
        self.dataframes = []
        self._throttle_timer = None
        self._last_update_time = time.time()
        # Min time between progress updates to avoid overloading the UI
        self._min_update_interval = 0.1  # seconds

        # Initialize progress tracking variables
        self._total_rows_loaded = 0
        self._total_rows_estimated = 0
        self._current_file_rows = 0
        self._current_file_total_rows = 0

    def _throttled_progress_update(self, current, total):
        """
        Update progress signals with throttling to avoid UI overload.

        Args:
            current: Current progress value
            total: Total expected value for 100% progress

        Returns:
            False if the task was cancelled, True otherwise
        """
        # Check cancellation first - return immediately if cancelled
        if self.is_cancelled:
            return False

        # Handle division by zero and calculate percentage
        if total <= 0:
            percentage = 0
        else:
            percentage = min(100, int((current / total) * 100))

        # Get current time for throttling check
        current_time = time.time()
        time_since_last = current_time - self._last_update_time

        # Only update if sufficient time has passed or we're at 100%
        if time_since_last >= self._min_update_interval or percentage >= 100:
            try:
                # Update status with file info and total row count
                file_info = ""
                current_file_path = ""

                if hasattr(self, "_current_file_index") and hasattr(self, "_num_files"):
                    file_info = f" (File {self._current_file_index + 1}/{self._num_files})"

                    # Get the current file path for file_progress signal
                    if hasattr(self, "_current_file_index") and self._current_file_index < len(
                        self.file_paths
                    ):
                        current_file_path = str(self.file_paths[self._current_file_index])

                # Calculate progress across all files
                if self._total_rows_estimated > 0:
                    # Show progress as loaded rows out of total estimated
                    total_progress = (
                        f"{self._total_rows_loaded:,} of {self._total_rows_estimated:,} rows"
                    )
                else:
                    # Fall back to percentage if no row estimate
                    total_progress = f"{percentage}%"

                # Emit progress and status signals within try block to catch Qt errors
                self.progress.emit(percentage, 100)
                self.status_signal.emit(f"Loading CSV data: {total_progress}{file_info}")

                # Emit file_progress signal if we have a current file path
                if current_file_path:
                    self.file_progress.emit(
                        current_file_path, self._current_file_rows, self._current_file_total_rows
                    )

                # Update last update time
                self._last_update_time = current_time
            except (RuntimeError, AttributeError, ReferenceError) as e:
                # Handle a deleted C++ object gracefully - just log and continue
                if "C++ object" in str(e):
                    logger.debug("Qt C++ object already deleted during progress update")
                else:
                    logger.warning(f"Error during progress update: {e}")
                # Continue processing even if we can't update progress

        # Continue processing
        return not self.is_cancelled

    def _on_file_progress(self, current, total):
        """
        Handle progress updates from the CSV service for the current file.

        Args:
            current: Current rows processed in the file
            total: Total rows estimated in the file

        Returns:
            False if the task was cancelled, True otherwise
        """
        # Update current file progress
        self._current_file_rows = current
        self._current_file_total_rows = total

        # Update total progress
        if self._total_rows_estimated == 0:
            # If this is the first progress update, initialize total estimate
            self._total_rows_estimated = total * self._num_files

        # Calculate overall progress percentage
        if self._num_files > 0:
            # Calculate what percentage one file represents
            file_weight = 1.0 / self._num_files

            # Calculate current file's progress (0.0-1.0)
            file_progress = min(1.0, current / total) if total > 0 else 0

            # Calculate overall progress
            # Previous files (100% each) + current file's progress
            overall_progress = (self._current_file_index * file_weight) + (
                file_progress * file_weight
            )

            # Convert to percentage (0-100)
            progress_percent = int(overall_progress * 100)

            # Update the UI
            self._throttled_progress_update(progress_percent, 100)

        # Return not cancelled
        return not self.is_cancelled

    def run(self):
        """
        Execute the task, loading and combining multiple CSV files.

        Returns:
            (True, combined_df) on success,
            (False, error_message) on failure
        """
        if not self.file_paths:
            return False, "No CSV files provided to load"

        # Initialize counters and storage
        self._total_rows_loaded = 0
        combined_df = None
        self._num_files = len(self.file_paths)

        # Create parameters dict for read_csv_chunked calls
        csv_params = {
            "chunk_size": self.chunk_size,
            "normalize_text": getattr(self, "normalize_text", False),
            "robust_mode": getattr(self, "robust_mode", False),
        }

        # Add encoding if it exists
        if hasattr(self, "encoding") and self.encoding:
            csv_params["encoding"] = self.encoding

        # Process each file
        for i, file_path in enumerate(self.file_paths):
            # Check for cancellation before starting each file
            if self.is_cancelled:
                logger.info(f"CSV load task cancelled after processing {i} files")
                gc.collect()  # Force garbage collection
                return False, "Operation cancelled"

            # Set current file info for progress updates
            self._current_file_index = i
            self._current_file_rows = 0
            self._current_file_total_rows = 1  # Will be updated by callback
            file_path_str = str(file_path)

            # Send an initial progress update for this file
            self._throttled_progress_update(i * (100 // self._num_files), 100)

            try:
                # Create a progress callback for this file
                def file_progress_callback(current, total):
                    # Update file-specific progress information
                    return self._on_file_progress(current, total)

                # Add progress callback to parameters
                csv_params["progress_callback"] = file_progress_callback

                # Try to read the file - returns tuple of (dataframe, error_message)
                result_tuple = self.csv_service.read_csv_chunked(file_path_str, **csv_params)

                # Unpack the tuple
                file_df, error_msg = result_tuple

                # Handle file read result
                if error_msg is not None:
                    error_msg = f"Error reading CSV file {file_path_str}: {error_msg}"
                    logger.error(error_msg)

                    # Clean up and return error
                    if combined_df is not None:
                        del combined_df
                    gc.collect()
                    return False, error_msg

                # Get the DataFrame from successful read
                if file_df is None:
                    error_msg = f"No data returned from CSV file {file_path_str}"
                    logger.error(error_msg)
                    continue

                # Update total rows loaded
                file_rows = len(file_df)
                self._total_rows_loaded += file_rows

                # First file becomes the initial combined DataFrame
                if combined_df is None:
                    combined_df = file_df
                else:
                    # Combine with existing data
                    try:
                        # Use pandas concat
                        combined_df = pd.concat([combined_df, file_df], ignore_index=True)

                        # Clean up individual file DataFrame to save memory
                        del file_df
                        gc.collect()
                    except Exception as e:
                        error_msg = f"Error combining DataFrame {file_path_str}: {str(e)}"
                        logger.error(error_msg)

                        # We'll continue with what we have, but report the error
                        if i == len(self.file_paths) - 1:
                            # If this was the last file, log warning and return partial data
                            logger.warning(
                                f"Loaded {self._total_rows_loaded} rows with errors: Error combining data: {str(e)}"
                            )
                            if combined_df is not None and len(combined_df) > 0:
                                return True, combined_df
                            else:
                                return False, f"Error combining data: {str(e)}"

                # Check for cancellation after each file
                if self.is_cancelled:
                    logger.info(f"CSV load task cancelled after processing {i + 1} files")
                    if combined_df is not None:
                        del combined_df
                    gc.collect()
                    return False, "Operation cancelled"

            except Exception as e:
                # Catch any unexpected errors
                error_msg = f"Unexpected error processing {file_path_str}: {str(e)}"
                logger.error(error_msg)
                traceback.print_exc()

                # Clean up and return
                if combined_df is not None:
                    del combined_df
                gc.collect()
                return False, error_msg

        # Final cleanup and check
        try:
            # Return success if we have data
            if combined_df is not None and len(combined_df) > 0:
                logger.info(
                    f"Successfully loaded {self._total_rows_loaded} rows from {len(self.file_paths)} files"
                )

                # Final progress update - show 100% with total rows loaded
                self._throttled_progress_update(100, 100)

                return True, combined_df
            else:
                return False, "No data loaded from CSV files"

        except Exception as e:
            error_msg = f"Error in final data processing: {str(e)}"
            logger.error(error_msg)

            # Clean up
            if combined_df is not None:
                del combined_df
            gc.collect()

            return False, error_msg


class FunctionTask(BackgroundTask):
    """
    A task that wraps a function to be executed in a background thread.

    This task takes a function and its arguments, and executes the function
    when the task is run. It provides progress reporting if the function
    supports it.
    """

    def __init__(
        self, func: Callable, args: Tuple = None, kwargs: Dict = None, task_id: str = None
    ) -> None:
        """
        Initialize the function task.

        Args:
            func: The function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Optional identifier for the task
        """
        super().__init__(task_id)
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}

    def run(self) -> Any:
        """
        Run the wrapped function.

        Returns:
            The result of the function call.
        """
        try:
            # Execute the function with its arguments
            return self.func(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Error in function task {self.task_id}: {e}")
            raise


class BackgroundWorker(QObject):
    """
    Worker for executing background tasks in a separate thread.

    The BackgroundWorker manages the lifetime of a background task and its thread,
    handles signal connections, and takes care of thread cleanup.
    """

    # Signals
    started = Signal()
    progress = Signal(int, int)  # current, total
    finished = Signal(object)  # result
    error = Signal(Exception)  # error
    cancelled = Signal()
    task_completed = Signal(str, object)  # task_id, result
    task_failed = Signal(str, Exception)  # task_id, error

    def __init__(self) -> None:
        """Initialize the background worker."""
        super().__init__()
        self._thread = QThread()
        self._thread.setObjectName("BackgroundWorkerThread")
        self._current_task = None
        self._operation_context = None  # Store the operation context

        # Move worker to thread
        self.moveToThread(self._thread)

        # Connect thread signals
        self._thread.started.connect(self._on_thread_started)
        self._thread.finished.connect(self._on_thread_finished)

        # Get UI state manager
        self._ui_state_manager = UIStateManager()

    @property
    def is_running(self) -> bool:
        """
        Return whether the worker is currently running a task.

        Returns:
            True if a task is running, False otherwise.
        """
        return self._thread.isRunning()

    def execute_task(self, task: BackgroundTask) -> None:
        """
        Execute a background task in a separate thread.

        Args:
            task: The background task to execute.
        """
        if self.is_running:
            logger.warning("Cannot execute task: another task is already running")
            return

        # Store the task
        self._current_task = task

        # Create operation context to block UI
        self._operation_context = OperationContext(
            self._ui_state_manager,
            UIOperations.BACKGROUND_TASK,
            groups=[UIElementGroups.MAIN_WINDOW],
            auto_enter=False,  # Don't enter context yet
        )

        # Connect signals
        task.progress.connect(self.progress)

        # Start the thread
        self._thread.start()

    def cancel(self) -> None:
        """
        Cancel the current task.

        This requests cancellation of the current task, but it's up to the
        task implementation to honor this request by checking is_cancelled.
        """
        if self._current_task and not self._current_task.is_cancelled:
            logger.debug("Cancelling background task")
            self._current_task.cancel()

    @Slot()
    def _on_thread_started(self) -> None:
        """Handle thread started event."""
        # Enter the operation context to block UI
        if self._operation_context:
            self._operation_context.__enter__()

        logger.debug("Background worker thread started")
        self.started.emit()

        # Execute the task
        task = self._current_task
        if task:
            logger.debug(f"Executing task {task.__class__.__name__}")
            try:
                result = task.run()
                self.finished.emit(result)
                if hasattr(task, "task_id") and task.task_id:
                    self.task_completed.emit(task.task_id, result)
            except Exception as error:
                logger.error(f"Error executing task: {error}")
                self.error.emit(error)
                if hasattr(task, "task_id") and task.task_id:
                    self.task_failed.emit(task.task_id, error)
            finally:
                # Clean up the operation context
                if self._operation_context:
                    self._operation_context.__exit__(None, None, None)
                    self._operation_context = None

        # Quit the thread
        self._thread.quit()

    @Slot()
    def _on_thread_finished(self) -> None:
        """Handle thread finished event."""
        self._thread.quit()

    def __del__(self):
        """
        Properly clean up resources when the worker is destroyed.
        This handles Qt thread cleanup even if the application is shutting down.
        """
        try:
            # First try to cancel any running task
            try:
                if hasattr(self, "_current_task") and self._current_task:
                    self._current_task.cancel()
                    logger.debug(
                        f"Cancelled task during BackgroundWorker cleanup: {self._current_task.__class__.__name__}"
                    )
            except (RuntimeError, AttributeError, ReferenceError) as e:
                # Don't raise errors during cleanup - just log them
                logger.debug(f"Error cancelling task during cleanup: {e}")
                pass

            # Check if thread exists and is running before trying to quit it
            if hasattr(self, "_thread") and self._thread is not None:
                try:
                    if self._thread.isRunning():
                        logger.debug("Quitting thread during BackgroundWorker cleanup")
                        self._thread.quit()

                        # Reduced wait time for faster app shutdown
                        if not self._thread.wait(100):  # Wait 100ms instead of 500ms
                            logger.debug("Thread did not respond to quit in time")
                    else:
                        logger.debug("Thread was not running during cleanup")
                except (RuntimeError, AttributeError, ReferenceError) as e:
                    # Handle the case where the C++ object is deleted
                    if "C++ object" in str(e):
                        logger.debug("Qt C++ object already deleted during thread cleanup")
                    else:
                        logger.debug(f"Error during thread cleanup: {e}")
            else:
                logger.debug("No thread to clean up")

        except Exception as e:
            # Catch all other exceptions during cleanup - we don't want to raise
            # exceptions in __del__ as they can cause unpredictable behavior
            logger.error(f"Error cleaning up BackgroundWorker: {e}")
            # Don't raise the error - just log it

    def run_task(self, func, *args, task_id=None, on_success=None, on_error=None, **kwargs):
        """
        Run a function as a background task.

        This is a convenience method for running a simple function in the background.

        Args:
            func: The function to run.
            args: Positional arguments to pass to the function.
            task_id: Optional ID for the task. If not provided, a random ID will be generated.
            on_success: Optional callback to call with the result when the task completes.
            on_error: Optional callback to call with the exception when the task fails.
            kwargs: Keyword arguments to pass to the function.
        """
        # Create the task
        task = FunctionTask(func, args, kwargs, task_id)

        # Connect success callback if provided
        if on_success:

            def success_callback(task_id, result):
                if task_id == task.task_id:
                    on_success(result)

            self.task_completed.connect(success_callback)

        # Connect error callback if provided
        if on_error:

            def error_callback(task_id, error):
                if task_id == task.task_id:
                    on_error(error)

            self.task_failed.connect(error_callback)

        # Use operation context to block UI
        with OperationContext(
            self._ui_state_manager,
            UIOperations.BACKGROUND_TASK,
            groups=[UIElementGroups.MAIN_WINDOW],
        ):
            # Execute the task
            self.execute_task(task)
