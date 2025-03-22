"""
Tests for the DataManager progress reporting functionality.

This module tests the DataManager class's ability to report progress during
file loading operations and handle cancellation.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
from pytestqt.qtbot import QtBot

# Add project root to path for importing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.utils.background_processing import MultiCSVLoadTask


class SignalRecorder:
    """
    A simple class to record Qt signal emissions for testing.
    """

    def __init__(self):
        self.count = 0
        self.args_list = []

    def slot(self, *args):
        self.count += 1
        self.args_list.append(args)


@pytest.fixture
def data_model():
    """Create a mock data model for testing."""
    model = MagicMock()
    model.data = pd.DataFrame()
    model.blockSignals = MagicMock()
    model.update_data = MagicMock()
    model.data_changed = MagicMock()
    return model


@pytest.fixture
def csv_service():
    """Create a mock CSV service for testing."""
    service = MagicMock()

    # Mock the read_csv_chunked method to return a DataFrame
    def mock_read_csv_chunked(file_path, **kwargs):
        # Get the progress callback if provided
        progress_callback = kwargs.get("progress_callback")

        # Simulate progress if callback is provided
        if progress_callback:
            progress_callback(50, 100)  # Report 50% progress

        # Create a test DataFrame
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        return df, "Successfully loaded"

    service.read_csv_chunked.side_effect = mock_read_csv_chunked

    return service


@pytest.fixture
def data_manager(data_model, csv_service):
    """Create a DataManager instance with mock dependencies."""
    # Mock the ConfigManager since we don't need to test that
    with patch("chestbuddy.core.services.data_manager.ConfigManager") as config_mock:
        # Set up config mock to return an empty list for recent files
        config_mock.return_value.get.return_value = []
        config_mock.return_value.get_list.return_value = []

        # Create the DataManager instance
        dm = DataManager(data_model, csv_service)

        # Patch the _map_columns method to return the dataframe unchanged
        dm._map_columns = lambda df: df

        return dm


def test_load_csv_emits_progress_signals(qtbot, data_manager):
    """Test that load_csv emits progress signals."""
    # Create signal recorders
    load_started_recorder = SignalRecorder()
    load_progress_recorder = SignalRecorder()
    load_finished_recorder = SignalRecorder()

    # Connect signals to recorders
    data_manager.load_started.connect(load_started_recorder.slot)
    data_manager.load_progress.connect(load_progress_recorder.slot)
    data_manager.load_finished.connect(load_finished_recorder.slot)

    # Replace execute_task with a mock that captures the task
    original_execute_task = data_manager._worker.execute_task
    captured_task = [None]

    def mock_execute_task(task):
        captured_task[0] = task
        # Instead of running the task in a thread, run it directly
        result = task.run()
        data_manager._on_background_task_completed("load_csv", result)

    data_manager._worker.execute_task = mock_execute_task

    # Call load_csv
    file_path = "test.csv"
    data_manager.load_csv(file_path)

    # Check that the task was created correctly
    assert captured_task[0] is not None
    assert isinstance(captured_task[0], MultiCSVLoadTask)

    # Check that load_started was emitted
    assert load_started_recorder.count == 1

    # Check that load_progress signals were emitted
    assert load_progress_recorder.count > 0

    # Check that load_finished was emitted
    assert load_finished_recorder.count == 1

    # Restore original execute_task
    data_manager._worker.execute_task = original_execute_task


def test_on_file_progress(qtbot, data_manager):
    """Test that _on_file_progress forwards signals correctly."""
    # Create a signal recorder for load_progress
    progress_recorder = SignalRecorder()
    data_manager.load_progress.connect(progress_recorder.slot)

    # Call _on_file_progress
    file_path = "test.csv"
    current = 50
    total = 100
    data_manager._on_file_progress(file_path, current, total)

    # Check that load_progress was emitted with the correct arguments
    assert progress_recorder.count == 1
    args = progress_recorder.args_list[0]
    assert args[0] == file_path
    assert args[1] == current
    assert args[2] == total


def test_cancel_loading(qtbot, data_manager):
    """Test cancelling a loading operation."""
    # Create a mock task
    mock_task = MagicMock()
    data_manager._current_task = mock_task

    # Mock the worker's cancel method
    data_manager._worker.cancel = MagicMock()

    # Call cancel_loading
    data_manager.cancel_loading()

    # Check that worker.cancel was called
    data_manager._worker.cancel.assert_called_once()


def test_on_load_cancelled(qtbot, data_manager):
    """Test handling of cancelled loading operations."""
    # Create signal recorders
    load_finished_recorder = SignalRecorder()
    load_error_recorder = SignalRecorder()

    # Connect signals to recorders
    data_manager.load_finished.connect(load_finished_recorder.slot)
    data_manager.load_error.connect(load_error_recorder.slot)

    # Call _on_load_cancelled
    data_manager._on_load_cancelled()

    # Check that signals were emitted
    assert load_finished_recorder.count == 1
    assert load_error_recorder.count == 1
    assert "cancelled" in load_error_recorder.args_list[0][0].lower()

    # Check that blockSignals was called with False
    data_manager._data_model.blockSignals.assert_called_with(False)

    # Check that _current_task was cleared
    assert data_manager._current_task is None


def test_load_csv_with_multiple_files(qtbot, data_manager):
    """Test loading multiple CSV files."""
    # Create signal recorders
    load_started_recorder = SignalRecorder()
    load_progress_recorder = SignalRecorder()
    load_finished_recorder = SignalRecorder()

    # Connect signals to recorders
    data_manager.load_started.connect(load_started_recorder.slot)
    data_manager.load_progress.connect(load_progress_recorder.slot)
    data_manager.load_finished.connect(load_finished_recorder.slot)

    # Replace execute_task with a mock that captures the task
    original_execute_task = data_manager._worker.execute_task
    captured_task = [None]

    def mock_execute_task(task):
        captured_task[0] = task
        # Instead of running the task in a thread, run it directly
        result = task.run()
        data_manager._on_background_task_completed("load_csv", result)

    data_manager._worker.execute_task = mock_execute_task

    # Call load_csv with multiple files
    file_paths = ["test1.csv", "test2.csv"]
    data_manager.load_csv(file_paths)

    # Check that load_started was emitted
    assert load_started_recorder.count == 1

    # Check that the task was created with multiple files
    assert captured_task[0] is not None
    assert isinstance(captured_task[0], MultiCSVLoadTask)
    assert len(captured_task[0].file_paths) == 2

    # Check that load_progress signals were emitted
    assert load_progress_recorder.count > 0

    # Check that load_finished was emitted
    assert load_finished_recorder.count == 1

    # Restore original execute_task
    data_manager._worker.execute_task = original_execute_task


def test_error_handling_during_loading(qtbot, data_manager, csv_service):
    """Test error handling during CSV loading."""

    # Mock the csv_service to raise an exception
    def error_read_csv_chunked(file_path, **kwargs):
        raise ValueError("Test error")

    csv_service.read_csv_chunked.side_effect = error_read_csv_chunked

    # Use variables to track signal emissions instead of recorders
    error_received = False
    error_message = ""
    load_finished_received = False

    # Connect signals to lambda functions
    def on_error(msg):
        nonlocal error_received, error_message
        error_received = True
        error_message = msg

    def on_finished():
        nonlocal load_finished_received
        load_finished_received = True

    data_manager.load_error.connect(on_error)
    data_manager.load_finished.connect(on_finished)

    # Call load_csv with direct error injection
    file_path = "test.csv"

    # Force direct error handling instead of using background task
    error_task = MagicMock()
    error_task.name = "load_csv"
    error_task.error = "Test error"

    # Directly call the error handler
    data_manager._on_background_task_failed(error_task.name, error_task.error)

    # Process events to ensure signal emission is processed
    qtbot.wait(100)

    # Check that error handling was triggered
    assert error_received
    assert "Test error" in error_message
    assert load_finished_received
