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
            except TypeError:
                # Signal wasn't connected
                pass

        # Clear the task
        self._task = None

    def __del__(self) -> None:
        """Clean up resources when the worker is deleted."""
        # Make sure the thread is properly cleaned up
        if self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
