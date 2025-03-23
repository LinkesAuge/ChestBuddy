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

from PySide6.QtCore import QObject, Signal, Slot, QThread, QRunnable, QThreadPool
from PySide6.QtWidgets import QApplication

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

    def __init__(self, csv_service, file_paths, chunk_size=1000):
        """
        Initialize the task with multiple CSV files to load.

        Args:
            csv_service: The CSVService instance to use for loading
            file_paths: List of paths to CSV files to load
            chunk_size: Size of chunks to use when loading CSV files
        """
        super().__init__(f"load_multi_csv_{len(file_paths)}_files")
        self.csv_service = csv_service
        self.file_paths = file_paths
        self.chunk_size = chunk_size
        self.dataframes = []
        self._throttle_timer = None
        self._last_update_time = time.time()
        # Min time between progress updates to avoid overloading the UI
        self._min_update_interval = 0.1  # seconds

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
                # Update status with file info if we have it
                status_suffix = ""
                if hasattr(self, "_current_file_index") and hasattr(self, "_num_files"):
                    status_suffix = f" (File {self._current_file_index + 1}/{self._num_files})"

                # Emit progress and status signals within try block to catch Qt errors
                self.progress.emit(percentage, 100)
                self.status_signal.emit(f"Loading CSV data: {percentage}%{status_suffix}")

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

    def run(self):
        """
        Load multiple CSV files and combine them into a single result.

        This method processes each file in sequence, handling errors and
        reporting progress along the way.

        Returns:
            A tuple with (True, combined_dataframe) on success or
            (False, error_message) on failure
        """
        import gc  # Import garbage collector for memory management

        if not self.file_paths:
            return False, "No CSV files provided to load"

        # Track combined data from all files
        combined_df = None
        total_rows = 0
        error_messages = []

        try:
            # Track number of files for progress reporting
            self._num_files = len(self.file_paths)

            # Process each file
            for i, file_path in enumerate(self.file_paths):
                # Store current file index for progress reporting
                self._current_file_index = i

                # Update status with file info
                try:
                    file_name = Path(file_path).name
                    self.status_signal.emit(
                        f"Loading CSV file {i + 1}/{len(self.file_paths)}: {file_name}"
                    )
                except (RuntimeError, AttributeError, ReferenceError) as e:
                    # Handle Qt object deleted gracefully
                    if "C++ object" in str(e):
                        logger.debug("Qt C++ object already deleted during status update")
                    else:
                        logger.warning(f"Error updating status: {e}")

                # Check if cancelled before each file
                if self.is_cancelled:
                    return False, "Operation cancelled"

                # Load the current file with progress callback
                try:
                    df, error = self.csv_service.read_csv_chunked(
                        file_path,
                        chunk_size=self.chunk_size,
                        progress_callback=self._throttled_progress_update,
                    )

                    # If cancelled during file read, return early
                    if self.is_cancelled:
                        # Clean up to free memory
                        if df is not None:
                            del df
                        gc.collect()
                        return False, "Operation cancelled"

                    # Handle errors reading the file
                    if error:
                        error_messages.append(f"Error loading {Path(file_path).name}: {error}")
                        logger.error(f"Error loading CSV file {file_path}: {error}")
                        continue  # Skip this file and try the next

                    # Handle empty file
                    if df is None or len(df) == 0:
                        logger.warning(f"CSV file {file_path} is empty")
                        continue  # Skip empty files

                    # Append to combined result
                    if combined_df is None:
                        combined_df = df
                    else:
                        # Combine dataframes
                        try:
                            combined_df = pd.concat([combined_df, df], ignore_index=True)

                            # Clean up individual DataFrame to free memory
                            del df
                            gc.collect()
                        except Exception as e:
                            error_messages.append(f"Error combining data: {str(e)}")
                            logger.error(f"Error combining DataFrame {file_path}: {e}")

                            # If we can't combine, at least keep what we have
                            if df is not None:
                                del df
                            gc.collect()

                    # Update total row count
                    if combined_df is not None:
                        total_rows = len(combined_df)

                    # Check if cancelled after each file
                    if self.is_cancelled:
                        # Clean up to free memory
                        if combined_df is not None:
                            del combined_df
                        gc.collect()
                        return False, "Operation cancelled"

                except MemoryError as me:
                    error_msg = f"Memory error processing {Path(file_path).name}: {str(me)}"
                    error_messages.append(error_msg)
                    logger.error(error_msg)

                    # If we have partial data but ran out of memory, return what we have
                    if combined_df is not None and not combined_df.empty:
                        return True, combined_df
                    else:
                        return False, "Memory error while processing files"
                except Exception as e:
                    error_msg = f"Error processing {Path(file_path).name}: {str(e)}"
                    error_messages.append(error_msg)
                    logger.error(error_msg)

                    # Continue to the next file

                # Run garbage collection between files
                gc.collect()

            # Final check for cancellation
            if self.is_cancelled:
                # Clean up to free memory before returning
                if combined_df is not None:
                    del combined_df
                gc.collect()
                return False, "Operation cancelled"

            # Final status update
            try:
                percentage = 100
                self.progress.emit(percentage, 100)
                self.status_signal.emit(f"CSV import complete: {total_rows} rows loaded")
            except (RuntimeError, AttributeError, ReferenceError) as e:
                logger.debug(f"Error in final status update (likely shutdown): {e}")

            # Handle final result
            if combined_df is None or combined_df.empty:
                if error_messages:
                    return False, "\n".join(error_messages)
                else:
                    return False, "No data loaded from CSV files"

            # Handle partial success
            if error_messages:
                logger.warning(f"Loaded {total_rows} rows with errors: {'; '.join(error_messages)}")
            else:
                logger.info(
                    f"Successfully loaded {total_rows} rows from {len(self.file_paths)} CSV files"
                )

            return True, combined_df

        except Exception as e:
            logger.error(f"Unexpected error in MultiCSVLoadTask: {e}")
            return False, f"Error loading CSV files: {str(e)}"
        finally:
            # Ensure we clean up all DataFrames to free memory
            if "combined_df" in locals() and combined_df is not None:
                del combined_df
            gc.collect()


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

        # Create a new thread for this worker
        self._thread = QThread()
        self._thread.setObjectName(f"BackgroundWorker-{id(self)}")

        # Move this worker to the thread
        self.moveToThread(self._thread)

        # Connect thread signals
        self._thread.started.connect(self._on_thread_started)
        self._thread.finished.connect(self._on_thread_finished)

        # Initialize variables
        self._task = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """
        Return whether the worker is currently running a task.

        Returns:
            True if a task is running, False otherwise.
        """
        return self._is_running and self._thread.isRunning()

    def execute_task(self, task: BackgroundTask) -> None:
        """
        Execute a background task in a separate thread.

        Args:
            task: The task to execute.
        """
        if self.is_running:
            logger.warning("Cannot execute task: worker is already running")
            return

        # Store the task
        self._task = task

        # Connect task signals
        task.progress.connect(self.progress)

        # Start the thread
        self._thread.start()

    def cancel(self) -> None:
        """
        Cancel the current task if one is running.
        """
        if not self.is_running or self._task is None:
            logger.warning("Cannot cancel: no task running")
            return

        # Cancel the task
        self._task.cancel()

        # Emit cancelled signal
        self.cancelled.emit()

        # Quit the thread (non-blocking)
        self._thread.quit()

    @Slot()
    def _on_thread_started(self) -> None:
        """Handle thread started event."""
        if self._task is None:
            logger.error("Thread started but no task is set")
            self._thread.quit()
            return

        self._is_running = True
        self.started.emit()

        try:
            # Execute the task
            result = self._task.run()

            # If the task wasn't cancelled, emit finished
            if not self._task.is_cancelled:
                self.finished.emit(result)
        except Exception as e:
            # Log the error
            logger.error(f"Error in background task: {e}")
            logger.debug(traceback.format_exc())

            # Emit error signal
            self.error.emit(e)
        finally:
            # Quit the thread
            self._thread.quit()

    @Slot()
    def _on_thread_finished(self) -> None:
        """Handle thread finished event."""
        self._is_running = False

        # Disconnect task signals
        if self._task is not None:
            try:
                self._task.progress.disconnect(self.progress)

                # Check for and disconnect any other signals that might be connected
                if hasattr(self._task, "status_signal") and isinstance(
                    getattr(self._task, "status_signal", None), Signal
                ):
                    try:
                        # Find and disconnect any connections
                        receivers = getattr(self._task.status_signal, "_receivers", [])
                        if receivers:
                            logger.debug(
                                f"Disconnecting status_signal signal with {len(receivers)} receivers"
                            )
                            self._task.status_signal.disconnect()
                    except (TypeError, RuntimeError) as e:
                        logger.debug(f"Error disconnecting status_signal signal: {e}")

            except (TypeError, RuntimeError) as e:
                # Signal wasn't connected or Qt object deleted
                logger.debug(f"Error disconnecting signals: {e}")

        # Clear the task reference to allow garbage collection
        self._task = None

        # Log completion
        logger.debug("Thread finished and task cleanup completed")

    def __del__(self):
        """
        Properly clean up resources when the worker is destroyed.
        This handles Qt thread cleanup even if the application is shutting down.
        """
        try:
            # First try to cancel any running task
            try:
                if hasattr(self, "_task") and self._task:
                    self._task.cancel()
                    logger.debug(
                        f"Cancelled task during BackgroundWorker cleanup: {self._task.__class__.__name__}"
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

        This is a convenience method that creates a FunctionTask and executes it.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            task_id: Optional identifier for the task
            on_success: Optional callback to be called with the result
            on_error: Optional callback to be called with the error
            **kwargs: Keyword arguments for the function

        Returns:
            The created FunctionTask
        """
        # Create a task
        task = FunctionTask(func, args, kwargs, task_id)

        # Connect success/error callbacks if provided
        if on_success:
            self.task_completed.connect(
                lambda tid, result: on_success(result) if tid == task_id else None
            )
        if on_error:
            self.task_failed.connect(lambda tid, error: on_error(error) if tid == task_id else None)

        # Connect task completion/failure signals
        self.finished.connect(lambda result: self.task_completed.emit(task_id, result))
        self.error.connect(lambda error: self.task_failed.emit(task_id, error))

        # Execute the task
        self.execute_task(task)

        return task
