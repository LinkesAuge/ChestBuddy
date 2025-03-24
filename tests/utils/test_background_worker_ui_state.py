"""
test_background_worker_ui_state.py

Description: Tests for the BackgroundWorker integration with UI State Management
"""

import pytest
from unittest.mock import MagicMock, patch, call
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chestbuddy.utils.background_processing import BackgroundWorker, BackgroundTask
from chestbuddy.utils.ui_state import UIOperations, UIElementGroups, OperationContext


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

    def run(self):
        """Run the sample task."""
        # Simulate work
        time.sleep(self.duration)

        # Optionally fail the task
        if self.should_fail:
            raise ValueError("Task failed as requested")

        # Return a result
        self.result_data = {"status": "completed", "value": 42}
        return self.result_data


@pytest.fixture
def mock_ui_state_manager():
    """Mock the UIStateManager to avoid singleton issues in tests."""
    with patch("chestbuddy.utils.ui_state.UIStateManager", autospec=True) as mock:
        # Configure the mock to return itself when instantiated
        instance = mock.return_value
        yield instance


@pytest.fixture
def mock_operation_context():
    """Mock the OperationContext to verify it's properly used."""
    with patch("chestbuddy.utils.ui_state.OperationContext", autospec=True) as mock:
        # Return a MagicMock instance when instantiated
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.__exit__.return_value = None
        yield mock


@pytest.fixture
def worker():
    """Fixture to create a worker and ensure it's cleaned up."""
    worker = BackgroundWorker()
    yield worker

    # Clean up the worker after the test
    if worker._thread and worker._thread.isRunning():
        worker._thread.quit()
        worker._thread.wait(1000)  # Wait up to 1 second for thread to finish


@pytest.fixture
def sample_task():
    """Fixture to create a sample task."""
    return SampleTask()


@pytest.fixture
def failing_task():
    """Fixture to create a task that will fail."""
    return SampleTask(should_fail=True)


class TestBackgroundWorkerUIState:
    """Tests for the BackgroundWorker UI State Management integration."""

    def test_execute_task_blocks_ui(self, qtbot, worker, sample_task, mock_operation_context):
        """Test that execute_task uses OperationContext to block the UI."""
        # Execute task
        worker.execute_task(sample_task)

        # Wait for task to complete
        with qtbot.waitSignal(worker.finished, timeout=1000):
            pass

        # Check that OperationContext was created with the correct operation
        mock_operation_context.assert_called_once()
        args, kwargs = mock_operation_context.call_args
        assert UIOperations.BACKGROUND_TASK in args

        # Check that the context was entered and exited
        mock_operation_context.return_value.__enter__.assert_called_once()
        mock_operation_context.return_value.__exit__.assert_called_once()

    def test_ui_unblocked_on_error(self, qtbot, worker, failing_task, mock_operation_context):
        """Test that UI is unblocked even when the task fails."""
        # Execute task that will fail
        worker.execute_task(failing_task)

        # Wait for error signal
        with qtbot.waitSignal(worker.error, timeout=1000):
            pass

        # Check that OperationContext was created and used
        mock_operation_context.assert_called_once()

        # Most importantly, check that __exit__ was called to unblock UI
        mock_operation_context.return_value.__exit__.assert_called_once()

    def test_run_task_blocks_ui(self, qtbot, worker, mock_operation_context):
        """Test that run_task blocks the UI."""
        # Define a simple function to run
        result = [None]

        def test_func():
            return "success"

        # Run the task
        worker.run_task(
            test_func, task_id="test_task", on_success=lambda r: result.__setitem__(0, r)
        )

        # Wait for task to complete
        while result[0] is None:
            qtbot.wait(100)

        # Check that task completed successfully
        assert result[0] == "success"

        # Check that OperationContext was created and used
        mock_operation_context.assert_called_once()
        args, kwargs = mock_operation_context.call_args
        assert UIOperations.BACKGROUND_TASK in args

        # Check that context was entered and exited
        mock_operation_context.return_value.__enter__.assert_called_once()
        mock_operation_context.return_value.__exit__.assert_called_once()

    def test_cancel_unblocks_ui(self, qtbot, worker, mock_operation_context):
        """Test that cancelling a task unblocks the UI."""
        # Create a long-running task
        long_task = SampleTask(duration=1.0)

        # Execute task
        worker.execute_task(long_task)

        # Short wait to ensure task is running
        qtbot.wait(100)

        # Cancel the task
        worker.cancel()

        # Wait for cancelled signal
        with qtbot.waitSignal(worker.cancelled, timeout=1000):
            pass

        # Check that context was exited to unblock UI
        mock_operation_context.return_value.__exit__.assert_called_once()
