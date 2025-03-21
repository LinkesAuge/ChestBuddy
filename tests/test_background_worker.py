"""
Tests for background processing functionality.

This module tests the background processing utilities that enable
running operations in separate threads while maintaining UI responsiveness.
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pytest
from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from chestbuddy.utils.background_processing import BackgroundWorker, BackgroundTask


class SampleTask(BackgroundTask):
    """A sample task for testing background processing."""

    def __init__(self, should_fail: bool = False, duration: float = 0.1):
        """
        Initialize the sample task.

        Args:
            should_fail: Whether the task should fail with an exception
            duration: How long the task should take to complete (in seconds)
        """
        super().__init__()
        self.should_fail = should_fail
        self.duration = duration
        self.result_data = None

    def run(self) -> Any:
        """Run the sample task."""
        # Report initial progress
        self.progress.emit(0, 100)

        # Simulate work with progress reporting
        total_steps = 10
        for i in range(total_steps):
            # Simulate work
            time.sleep(self.duration / total_steps)

            # Check for cancellation
            if self.is_cancelled:
                return None

            # Report progress
            progress = int((i + 1) * 100 / total_steps)
            self.progress.emit(progress, 100)

        # Optionally fail the task
        if self.should_fail:
            raise ValueError("Task failed as requested")

        # Return a result
        self.result_data = {"status": "completed", "value": 42}
        return self.result_data


@pytest.fixture
def sample_task() -> SampleTask:
    """Fixture to create a sample task."""
    return SampleTask()


@pytest.fixture
def failing_task() -> SampleTask:
    """Fixture to create a task that will fail."""
    return SampleTask(should_fail=True)


@pytest.fixture
def worker():
    """Fixture to create a worker and ensure it's cleaned up."""
    worker = BackgroundWorker()
    yield worker

    # Clean up the worker after the test
    if worker._thread.isRunning():
        worker._thread.quit()
        worker._thread.wait(1000)  # Wait up to 1 second for thread to finish


def test_background_worker_initialization(worker):
    """Test that the background worker can be initialized correctly."""
    assert worker is not None
    assert worker.thread() is not None
    assert not worker.is_running


def test_background_worker_signals(qtbot: QtBot, worker, sample_task: SampleTask):
    """Test that the background worker signals are properly emitted."""
    # Setup signal tracking
    progress_signals = []
    finished_signal_received = [False]  # Use a list to allow modification in lambda

    # Connect signals
    worker.progress.connect(lambda current, total: progress_signals.append((current, total)))
    worker.finished.connect(lambda result: setattr(worker, "result", result))
    worker.finished.connect(lambda _: finished_signal_received.__setitem__(0, True))

    # Execute task
    worker.execute_task(sample_task)

    # Wait for completion with timeout
    with qtbot.waitSignal(worker.finished, timeout=2000):
        pass

    # Check signals were emitted
    assert len(progress_signals) > 0
    assert progress_signals[0][0] == 0  # First progress should be 0
    assert progress_signals[-1][0] == 100  # Last progress should be 100
    assert hasattr(worker, "result")
    assert worker.result == sample_task.result_data
    assert finished_signal_received[0]  # Check that finished signal was received


def test_background_worker_error_handling(qtbot: QtBot, worker, failing_task: SampleTask):
    """Test that the background worker properly handles errors."""
    # Setup signal tracking
    error_received = [False]  # Use a list to allow modification in lambda
    error_message = [""]  # Use a list to store the error message

    # Connect signals
    worker.error.connect(lambda error: error_received.__setitem__(0, True))
    worker.error.connect(lambda error: error_message.__setitem__(0, str(error)))

    # Execute task
    worker.execute_task(failing_task)

    # Wait for error with timeout
    with qtbot.waitSignal(worker.error, timeout=2000):
        pass

    # Check error was handled
    assert error_received[0]
    assert error_message[0] != ""
    assert "Task failed as requested" in error_message[0]


def test_background_worker_cancellation(qtbot: QtBot, worker):
    """Test that the background worker can be cancelled."""
    # Create a longer task for cancellation
    long_task = SampleTask(duration=1.0)

    # Track task cancellation directly
    task_cancelled = [False]
    original_cancel = long_task.cancel

    def track_cancel():
        task_cancelled[0] = True
        original_cancel()

    long_task.cancel = track_cancel

    # Execute task
    worker.execute_task(long_task)

    # Wait a moment to let task start
    qtbot.wait(100)

    # Cancel manually (not using a signal)
    worker.cancel()

    # Wait a moment for cancellation to complete
    qtbot.wait(200)

    # Check cancellation was successful
    assert task_cancelled[0]
    assert long_task.is_cancelled

    # Wait for thread to clean up
    if worker._thread.isRunning():
        worker._thread.quit()
        worker._thread.wait(1000)


def test_threads_are_different(qtbot: QtBot, worker, sample_task: SampleTask):
    """Test that the worker runs in a different thread than the main thread."""
    # Track completion
    finished = [False]
    worker.finished.connect(lambda _: finished.__setitem__(0, True))

    # Check if we're in the main thread
    main_thread = QThread.currentThread()

    # Check if worker is in a different thread
    worker_thread = worker._thread
    assert worker_thread != main_thread

    # Execute task
    worker.execute_task(sample_task)

    # Wait for completion
    with qtbot.waitSignal(worker.finished, timeout=2000):
        pass

    # Verify task completed
    assert finished[0]

    # Give thread time to clean up
    qtbot.wait(100)
