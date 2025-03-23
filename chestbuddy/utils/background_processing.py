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

    def __init__(self) -> None:
        """Initialize the background task."""
        super().__init__()
        self._is_cancelled = False

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
    Background task for loading multiple CSV files with progress reporting.

    This task handles loading multiple CSV files in sequence, combining them,
    and reporting progress both for individual files and overall progress.

    Attributes:
        file_paths: List of paths to CSV files to load
        csv_service: Service for CSV operations
        chunk_size: Number of rows to read in each chunk
        normalize_text: Whether to normalize text in the CSV
        robust_mode: Whether to use robust mode for reading
        encoding: Optional encoding to use (auto-detected if None)
    """

    # Additional signal for file-specific progress
    file_progress = Signal(str, int, int)  # file_path, current, total

    def __init__(
        self,
        file_paths: List[Union[str, Path]],
        csv_service: Any,
        chunk_size: int = 1000,
        normalize_text: bool = True,
        robust_mode: bool = False,
        encoding: Optional[str] = None,
    ) -> None:
        """
        Initialize the multi-CSV load task.

        Args:
            file_paths: List of paths to CSV files to load
            csv_service: Service for CSV operations
            chunk_size: Number of rows to read in each chunk
            normalize_text: Whether to normalize text in the CSV
            robust_mode: Whether to use robust mode for reading
            encoding: Optional encoding to use (auto-detected if None)
        """
        super().__init__()
        self.file_paths = [Path(path) if isinstance(path, str) else path for path in file_paths]
        self.csv_service = csv_service
        self.chunk_size = chunk_size
        self.normalize_text = normalize_text
        self.robust_mode = robust_mode
        self.encoding = encoding
        self.dataframes = []
        self._processed_files = 0
        self._total_files = len(file_paths)

    def run(self) -> Tuple[Optional[Any], str]:
        """
        Run the multi-CSV load task.

        This method loads multiple CSV files in sequence, combines them,
        and reports progress both for individual files and overall progress.

        Returns:
            A tuple containing the combined DataFrame and a success/error message
        """
        import pandas as pd
        import os

        dfs = []
        error_files = []

        # Calculate total files for overall progress
        total_files = len(self.file_paths)
        if total_files == 0:
            return None, "No files to load"

        # Initial progress report - using consistent scale
        self.progress.emit(0, 100)  # Always use 0-100 scale for better UI experience

        # Process each file
        for i, file_path in enumerate(self.file_paths):
            # Check for cancellation
            if self.is_cancelled:
                return None, "Operation cancelled"

            try:
                logger.info(f"Processing file {i + 1}/{total_files}: {file_path}")

                # Calculate progress percentage for this file
                file_progress_percentage = int((i / total_files) * 100)

                # Emit overall progress at start of file (percentage of files completed)
                try:
                    self.progress.emit(file_progress_percentage, 100)
                except RuntimeError as e:
                    # Handle case where the Qt object has been deleted
                    logger.warning(f"Could not emit progress signal: {e}")
                    if "C++ object" in str(e):
                        return None, "Process interrupted - application is shutting down"

                # Define a progress callback for file-specific progress
                def file_progress_callback(current: int, total: int) -> bool:
                    # Check for cancellation first
                    if self.is_cancelled:
                        return False  # Signal to stop processing

                    # Reduce UI update frequency - update only every 1% change or every 100 rows
                    # to avoid overwhelming the event queue with progress updates
                    if total > 0:
                        last_percentage = getattr(file_progress_callback, "last_percentage", -1)
                        current_percentage = int((current / total) * 100)

                        last_row_update = getattr(file_progress_callback, "last_row_update", 0)
                        row_update_interval = min(
                            100, max(1, int(total / 100))
                        )  # Update at least every 1% of rows

                        # Only update if percentage changed or we've processed enough rows
                        should_update = (
                            current_percentage != last_percentage
                            or (current - last_row_update) >= row_update_interval
                        )

                        if not should_update:
                            # Skip this update but continue processing
                            return True

                        # Remember values for next time
                        file_progress_callback.last_percentage = current_percentage
                        file_progress_callback.last_row_update = current

                    # Safe signal emission with error handling
                    try:
                        # Emit file-specific progress signal
                        self.file_progress.emit(str(file_path), current, total)

                        # Calculate overall progress combining file count and row progress
                        if total > 0:
                            file_fraction = 1 / total_files
                            row_progress = current / total

                            # Calculate overall progress: completed files + progress within current file
                            overall_progress = int(
                                ((i / total_files) + (file_fraction * row_progress)) * 100
                            )

                            # Ensure progress is in valid range
                            overall_progress = max(
                                0, min(99, overall_progress)
                            )  # Cap at 99% until complete
                            self.progress.emit(overall_progress, 100)
                    except RuntimeError as e:
                        # Handle case where the Qt object has been deleted or other thread errors
                        logger.warning(f"Runtime error during progress signal emission: {e}")
                        if "C++ object" in str(e):
                            logger.error("Qt object deletion detected during CSV processing")
                            return False  # Signal to stop processing
                    except Exception as e:
                        # Log but don't crash on other errors
                        logger.error(f"Error in progress callback: {e}")

                    # Give the event loop a chance to process cancellation
                    # Reduce frequency of processEvents calls to avoid reentrancy issues
                    if current % 10 == 0:  # Only process events occasionally
                        try:
                            QApplication.processEvents()
                        except Exception as e:
                            logger.warning(f"Error processing events: {e}")

                    # Continue unless cancelled
                    return not self.is_cancelled

                # Read the file with chunking and progress reporting
                try:
                    df, message = self.csv_service.read_csv_chunked(
                        file_path=file_path,
                        chunk_size=self.chunk_size,
                        encoding=self.encoding,
                        normalize_text=self.normalize_text,
                        robust_mode=self.robust_mode,
                        progress_callback=file_progress_callback,
                    )
                except InterruptedError:
                    # Re-raise interruption exceptions to be handled by the outer try-except
                    raise
                except Exception as e:
                    # Log and treat as a file-specific error but continue processing other files
                    logger.error(f"Error reading file {file_path}: {e}")
                    error_files.append(f"{os.path.basename(str(file_path))}: {str(e)}")
                    continue

                # File completed, update overall progress
                try:
                    file_completed_progress = int(((i + 1) / total_files) * 100)
                    self.progress.emit(file_completed_progress, 100)
                except RuntimeError as e:
                    # Handle case where the Qt object has been deleted
                    logger.warning(f"Could not emit progress signal after file completion: {e}")
                    if "C++ object" in str(e):
                        return None, "Process interrupted - application is shutting down"

                if df is not None and not df.empty:
                    dfs.append(df)
                    self.dataframes.append(df)
                    self._processed_files += 1
                    logger.info(f"Successfully processed file {i + 1}/{total_files}")
                else:
                    logger.warning(f"File {file_path} returned empty DataFrame or error: {message}")
                    error_files.append(f"{os.path.basename(str(file_path))}: {message}")

            except InterruptedError as ie:
                # Task was cancelled
                logger.info(f"CSV read operation interrupted: {ie}")
                return None, str(ie)

            except RuntimeError as e:
                # Handle Qt-specific runtime errors (like C++ object deleted)
                logger.error(f"RuntimeError processing file {file_path}: {e}")
                if "C++ object" in str(e):
                    return None, "Process interrupted - application is shutting down"
                error_files.append(f"{os.path.basename(str(file_path))}: {str(e)}")

            except Exception as e:
                # Log and record the error, but continue with other files
                logger.error(f"Error processing file {file_path}: {e}")
                error_files.append(f"{os.path.basename(str(file_path))}: {str(e)}")

        # Final progress update - all files completed
        try:
            self.progress.emit(100, 100)
        except RuntimeError as e:
            # Just log the error, but don't return - we still want to combine the DataFrames we have
            logger.warning(f"Could not emit final progress signal: {e}")

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

    def get_progress(self) -> Tuple[int, int]:
        """
        Get the current progress of the task.

        Returns:
            A tuple containing (current progress, total)
        """
        return self._processed_files, self._total_files


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
        super().__init__()
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.task_id = task_id or str(id(self))

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
                if hasattr(self._task, "file_progress") and isinstance(
                    getattr(self._task, "file_progress", None), Signal
                ):
                    try:
                        # Find and disconnect any connections
                        receivers = getattr(self._task.file_progress, "_receivers", [])
                        if receivers:
                            logger.debug(
                                f"Disconnecting file_progress signal with {len(receivers)} receivers"
                            )
                            self._task.file_progress.disconnect()
                    except (TypeError, RuntimeError) as e:
                        logger.debug(f"Error disconnecting file_progress signal: {e}")

            except (TypeError, RuntimeError) as e:
                # Signal wasn't connected or Qt object deleted
                logger.debug(f"Error disconnecting signals: {e}")

        # Clear the task reference to allow garbage collection
        self._task = None

        # Log completion
        logger.debug("Thread finished and task cleanup completed")

    def __del__(self) -> None:
        """Clean up resources when the worker is deleted."""
        try:
            # Check if thread still exists and is running
            if hasattr(self, "_thread") and self._thread is not None:
                thread = self._thread  # Keep a reference
                logger.debug("Cleaning up BackgroundWorker thread")

                try:
                    # Cancel any running task first
                    if hasattr(self, "_task") and self._task is not None:
                        task = self._task  # Keep a reference
                        try:
                            task.cancel()
                        except RuntimeError as e:
                            # It's ok if we can't cancel the task during shutdown
                            logger.debug(f"Could not cancel task during cleanup: {e}")

                    # Only try to quit if the thread exists and is running
                    if thread.isRunning():
                        # Try to quit the thread gracefully first
                        thread.quit()

                        # Brief wait
                        if not thread.wait(500):  # 500ms timeout
                            logger.debug(
                                "Thread did not quit immediately, allowing application to handle it"
                            )
                            # During application shutdown, it's better to not force termination
                            # as this can cause the "Internal C++ object already deleted" error
                except RuntimeError as e:
                    # This is normal during application shutdown
                    logger.debug(f"RuntimeError during thread cleanup (likely shutdown): {e}")
                except Exception as e:
                    # Other exceptions should be logged
                    logger.warning(f"Error during thread cleanup: {e}")
        except Exception as e:
            # Just log any errors during cleanup, don't raise
            logger.debug(f"Error cleaning up BackgroundWorker (likely during shutdown): {e}")
            # Don't log the traceback during shutdown as it may cause more errors

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
