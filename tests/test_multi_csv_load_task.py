"""
Tests for the MultiCSVLoadTask class.

This module tests the functionality of the MultiCSVLoadTask class,
which is responsible for loading multiple CSV files with progress reporting.
"""

import sys
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
from pytestqt.qtbot import QtBot
from pytestqt.qtbot import SignalSpy

# Add project root to path for importing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from chestbuddy.utils.background_processing import MultiCSVLoadTask


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

        # Create a test DataFrame depending on the file path
        if "file1" in str(file_path):
            df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
            return df, "Successfully loaded file1"
        elif "file2" in str(file_path):
            df = pd.DataFrame({"A": [5, 6], "B": [7, 8]})
            return df, "Successfully loaded file2"
        else:
            return None, "File not found or invalid"

    service.read_csv_chunked.side_effect = mock_read_csv_chunked

    return service


def test_multi_csv_load_task_initialization(csv_service):
    """Test initialization of MultiCSVLoadTask."""
    file_paths = ["file1.csv", "file2.csv"]

    task = MultiCSVLoadTask(file_paths, csv_service)

    # Check that attributes are set correctly
    assert len(task.file_paths) == 2
    assert task.csv_service == csv_service
    assert task.chunk_size == 1000  # Default value
    assert task.normalize_text is True  # Default value
    assert task.robust_mode is False  # Default value
    assert task.encoding is None  # Default value
    assert task.is_cancelled is False

    # Check initial progress state
    current, total = task.get_progress()
    assert current == 0
    assert total == 2


def test_multi_csv_load_task_run(qtbot, csv_service):
    """Test running the MultiCSVLoadTask."""
    file_paths = ["file1.csv", "file2.csv"]

    # Create the task
    task = MultiCSVLoadTask(file_paths, csv_service)

    # Create signal spies to track progress signals
    progress_spy = SignalSpy(task.progress)
    file_progress_spy = SignalSpy(task.file_progress)

    # Run the task
    result_df, message = task.run()

    # Check the result
    assert result_df is not None
    assert isinstance(result_df, pd.DataFrame)
    assert "Successfully loaded" in message
    assert len(result_df) == 4  # Combined DataFrames should have 4 rows

    # Verify dataframe contents
    assert list(result_df["A"]) == [1, 2, 5, 6]
    assert list(result_df["B"]) == [3, 4, 7, 8]

    # Check that progress signals were emitted
    assert len(progress_spy) >= 2  # At least initial and final progress
    assert len(file_progress_spy) >= 2  # At least one signal per file

    # Initial progress should be (0, 2)
    assert progress_spy[0][0] == 0  # current
    assert progress_spy[0][1] == 2  # total

    # Final progress should be (2, 2)
    assert progress_spy[-1][0] == 2  # current
    assert progress_spy[-1][1] == 2  # total

    # Verify CSV service was called with correct parameters
    assert csv_service.read_csv_chunked.call_count == 2


def test_multi_csv_load_task_empty_file_list(csv_service):
    """Test running the MultiCSVLoadTask with an empty file list."""
    file_paths = []

    task = MultiCSVLoadTask(file_paths, csv_service)

    # Run the task
    result_df, message = task.run()

    # Check the result
    assert result_df is None
    assert "No files to load" in message

    # Verify CSV service was not called
    csv_service.read_csv_chunked.assert_not_called()


def test_multi_csv_load_task_cancellation(qtbot, csv_service):
    """Test cancellation of the MultiCSVLoadTask."""
    file_paths = ["file1.csv", "file2.csv", "file3.csv"]

    # Mock the read_csv_chunked method to take time and check cancellation
    def slow_read_csv_chunked(file_path, **kwargs):
        # Get the progress callback if provided
        progress_callback = kwargs.get("progress_callback")

        # Take some time to process
        time.sleep(0.1)

        # Simulate progress if callback is provided
        if progress_callback:
            progress_callback(50, 100)  # Report 50% progress

        # Create a test DataFrame depending on the file path
        if "file1" in str(file_path):
            return pd.DataFrame({"A": [1, 2], "B": [3, 4]}), "Successfully loaded file1"
        else:
            return pd.DataFrame({"A": [5, 6], "B": [7, 8]}), "Successfully loaded file2"

    csv_service.read_csv_chunked.side_effect = slow_read_csv_chunked

    # Create the task
    task = MultiCSVLoadTask(file_paths, csv_service)

    # Create a signal spy for progress
    progress_spy = SignalSpy(task.progress)

    # Start the task in a separate thread
    from threading import Thread

    result = [None, None]

    def run_task():
        result[0], result[1] = task.run()

    thread = Thread(target=run_task)
    thread.start()

    # Wait a moment to let the task start
    time.sleep(0.15)

    # Cancel the task
    task.cancel()

    # Wait for the thread to complete
    thread.join(timeout=2.0)
    assert not thread.is_alive()

    # Check the result
    assert result[0] is None
    assert "cancelled" in result[1].lower()

    # Verify that at least one progress signal was emitted before cancellation
    assert len(progress_spy) > 0


def test_multi_csv_load_task_error_handling(csv_service):
    """Test error handling in the MultiCSVLoadTask."""
    file_paths = ["error_file.csv", "file2.csv"]

    # Mock the read_csv_chunked method to raise an exception for the first file
    def error_read_csv_chunked(file_path, **kwargs):
        if "error_file" in str(file_path):
            raise ValueError("Test error")
        else:
            return pd.DataFrame({"A": [5, 6], "B": [7, 8]}), "Successfully loaded file2"

    csv_service.read_csv_chunked.side_effect = error_read_csv_chunked

    # Create the task
    task = MultiCSVLoadTask(file_paths, csv_service)

    # Run the task
    result_df, message = task.run()

    # Check the result - should still get data from the second file
    assert result_df is not None
    assert isinstance(result_df, pd.DataFrame)
    assert "Successfully loaded" in message
    assert "Some files had errors" in message
    assert "Test error" in message
    assert len(result_df) == 2  # Only the second DataFrame with 2 rows


def test_multi_csv_load_task_all_files_error(csv_service):
    """Test when all files in the task have errors."""
    file_paths = ["error_file1.csv", "error_file2.csv"]

    # Mock the read_csv_chunked method to return errors for all files
    def all_error_read_csv_chunked(file_path, **kwargs):
        return None, f"Error loading {file_path}"

    csv_service.read_csv_chunked.side_effect = all_error_read_csv_chunked

    # Create the task
    task = MultiCSVLoadTask(file_paths, csv_service)

    # Run the task
    result_df, message = task.run()

    # Check the result
    assert result_df is None
    assert "No valid data found" in message
    assert "error_file1.csv" in message.lower()
    assert "error_file2.csv" in message.lower()


def test_multi_csv_load_task_empty_dataframes(csv_service):
    """Test when files return empty DataFrames."""
    file_paths = ["empty1.csv", "empty2.csv"]

    # Mock the read_csv_chunked method to return empty DataFrames
    def empty_read_csv_chunked(file_path, **kwargs):
        return pd.DataFrame(), f"Empty file: {file_path}"

    csv_service.read_csv_chunked.side_effect = empty_read_csv_chunked

    # Create the task
    task = MultiCSVLoadTask(file_paths, csv_service)

    # Run the task
    result_df, message = task.run()

    # Check the result
    assert result_df is None
    assert "No valid data found" in message


def test_multi_csv_load_task_get_progress(qtbot, csv_service):
    """Test the get_progress method of MultiCSVLoadTask."""
    file_paths = ["file1.csv", "file2.csv", "file3.csv"]

    # Create the task
    task = MultiCSVLoadTask(file_paths, csv_service)

    # Check initial progress
    current, total = task.get_progress()
    assert current == 0
    assert total == 3

    # Mock the read_csv_chunked method to allow checking progress
    processed_files = [0]  # Using list to store mutable state

    def progress_tracking_read_csv_chunked(file_path, **kwargs):
        # Get the progress callback if provided
        progress_callback = kwargs.get("progress_callback")

        # Simulate progress if callback is provided
        if progress_callback:
            progress_callback(50, 100)  # Report 50% progress

        # Increment processed files counter
        processed_files[0] += 1

        # Track the progress after each file
        current, total = task._processed_files, task._total_files
        assert current == processed_files[0] - 1  # -1 because task increments after we're called
        assert total == 3

        # Create a test DataFrame
        return pd.DataFrame({"A": [1, 2], "B": [3, 4]}), f"Successfully loaded {file_path}"

    csv_service.read_csv_chunked.side_effect = progress_tracking_read_csv_chunked

    # Run the task
    result_df, message = task.run()

    # Check final progress
    current, total = task.get_progress()
    assert current == 3
    assert total == 3

    # Verify CSV service was called with correct parameters
    assert csv_service.read_csv_chunked.call_count == 3
    assert processed_files[0] == 3
