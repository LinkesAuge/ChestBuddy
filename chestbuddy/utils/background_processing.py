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
    A task for loading multiple CSV files with progress reporting.

    This task loads multiple CSV files in background, combines them into a single
    DataFrame, and provides progress updates.
    """

    # Add signal for chunk processing phase
    chunk_processed = Signal(int, int)  # current_chunk, total_chunks

    def __init__(
        self,
        csv_service: Any,
        file_paths: List[Union[str, Path]],
        chunk_size: int = 100,  # Default to 100 as requested
        normalize_text: bool = False,
        robust_mode: bool = False,
        task_id: str = None,
    ) -> None:
        """
        Initialize the task.

        Args:
            csv_service: The CSV service to use for loading files
            file_paths: List of paths to CSV files to load
            chunk_size: Number of rows to read in each chunk (default 100)
            normalize_text: Whether to normalize text in the CSV files
            robust_mode: Whether to use robust mode for reading CSV files
            task_id: Optional identifier for the task
        """
        super().__init__(task_id)
        self.csv_service = csv_service
        self.file_paths = file_paths
        self.chunk_size = chunk_size
        self.normalize_text = normalize_text
        self.robust_mode = robust_mode

        # Counters for progress tracking
        self._total_rows_loaded = 0
        self._num_files = len(file_paths) if file_paths else 0
        self._current_file_index = 0
        self._current_file_rows = 0
        self._current_file_total_rows = 1

        # For two-phase progress tracking
        self._loading_phase_complete = False
        self._processing_chunks = []
        self._total_chunks = 0
        self._processed_chunks = 0

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

    def _on_file_progress(self, current: int, total: int, phase: str = "loading") -> None:
        """
        Handle progress updates for a specific file.

        Args:
            current: Current progress value
            total: Total progress value
            phase: Current processing phase ('loading' or 'processing')
        """
        # Update file-specific counters
        self._current_file_rows = current
        self._current_file_total_rows = max(total, 1)  # Avoid division by zero

        # Calculate overall progress
        if phase == "loading":
            # Loading phase (0-50%)
            file_fraction = self._current_file_index / max(self._num_files, 1)
            chunk_fraction = current / max(total, 1)
            progress = int(50 * (file_fraction + chunk_fraction / self._num_files))
        else:
            # Processing phase (50-100%)
            progress = 50 + int(50 * (self._processed_chunks / max(self._total_chunks, 1)))

        # Ensure progress stays within bounds
        progress = max(0, min(100, progress))

        # Update progress
        self._throttled_progress_update(progress, 100)

    def report_chunk_processed(self):
        """Report that a chunk has been processed in the second phase."""
        self._processed_chunks += 1
        chunk_progress = int(50 * (self._processed_chunks / max(self._total_chunks, 1)))
        total_progress = 50 + chunk_progress  # 50% for loading + chunk progress

        # Update progress for the processing phase
        self._throttled_progress_update(total_progress, 100)

        # Emit the chunk processed signal
        self.chunk_processed.emit(self._processed_chunks, self._total_chunks)

    def run(self):
        """
        Execute the task, loading and combining multiple CSV files in chunks.

        This implementation processes data in two phases:
        1. Loading phase (50% of progress): Reading all files from disk in chunks
        2. Processing phase (50% of progress): Combining and preparing data for display

        Returns:
            (True, combined_df) on success,
            (False, error_message) on failure
        """
        if not self.file_paths:
            return False, "No CSV files provided to load"

        # Initialize data storage
        all_chunks = []
        self._total_rows_loaded = 0
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

        # Process each file - Loading Phase (50% of progress)
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

            # Calculate progress as a percentage of the loading phase (0-50%)
            loading_progress = min(50, int((i * 50) / self._num_files))

            # Send an initial progress update for this file
            self._throttled_progress_update(loading_progress, 100)

            try:
                # Create a progress callback for this file
                def file_progress_callback(current, total):
                    # Update file-specific progress information
                    return self._on_file_progress(current, total, phase="loading")

                # Add progress callback to parameters
                csv_params["progress_callback"] = file_progress_callback

                # Use the chunked generator from csv_service
                chunk_generator = self.csv_service.read_csv_chunked(file_path_str, **csv_params)

                # Collect all chunks from this file
                file_chunks = []
                for chunk in chunk_generator:
                    # Check for cancellation during chunk processing
                    if self.is_cancelled:
                        logger.info(f"CSV load task cancelled during chunk processing")
                        gc.collect()
                        return False, "Operation cancelled"

                    # Store chunk for later processing
                    file_chunks.append(chunk)

                    # Update progress within the loading phase (0-50%)
                    # This is approximate since we don't know exactly how many chunks there are yet
                    file_progress = min(50, int(((i + 0.5) * 50) / self._num_files))
                    self._throttled_progress_update(file_progress, 100)

                # Get the final result from the generator
                success, result = next(
                    chunk_generator, (False, "No result returned from generator")
                )

                # Handle file read result
                if not success:
                    error_msg = f"Error reading CSV file {file_path_str}: {result}"
                    logger.error(error_msg)
                    gc.collect()
                    return False, error_msg

                # Add file chunks to the overall collection
                all_chunks.extend(file_chunks)

                # Update total rows from this file
                rows_processed = result if isinstance(result, int) else 0
                self._total_rows_loaded += rows_processed

                # Update progress to show completion of this file
                loading_progress = min(50, int(((i + 1) * 50) / self._num_files))
                self._throttled_progress_update(loading_progress, 100)

            except StopIteration:
                # This is normal - we've consumed all chunks
                pass
            except Exception as e:
                # Catch any unexpected errors
                error_msg = f"Unexpected error processing {file_path_str}: {str(e)}"
                logger.error(error_msg)
                traceback.print_exc()
                gc.collect()
                return False, error_msg

        # Mark loading phase as complete
        self._loading_phase_complete = True
        self._throttled_progress_update(50, 100)  # Loading phase complete (50%)

        # Prepare for processing phase
        self._processing_chunks = all_chunks
        self._total_chunks = len(all_chunks)
        self._processed_chunks = 0

        # Processing Phase (50-100% of progress)
        try:
            # Return success with the collected chunks
            if len(all_chunks) > 0:
                logger.info(
                    f"Successfully loaded {self._total_rows_loaded} rows from {len(self.file_paths)} files in {self._total_chunks} chunks"
                )

                # Final progress update before returning chunks
                self._throttled_progress_update(50, 100)  # Start of processing phase

                return True, all_chunks
            else:
                return False, "No data loaded from CSV files"

        except Exception as e:
            error_msg = f"Error in final data processing: {str(e)}"
            logger.error(error_msg)
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

        # Connect the finished and error signals to task_completed and task_failed
        # These connections will be automatically removed when the thread finishes
        self.finished.connect(lambda result: self.task_completed.emit(task.task_id, result))
        self.error.connect(lambda error: self.task_failed.emit(task.task_id, error))

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
