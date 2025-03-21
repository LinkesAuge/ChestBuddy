"""
Tests for CSV background processing tasks.

This module tests background processing of CSV operations using the
BackgroundWorker and CSV-specific task implementations.
"""

import sys
import time
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pytest
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from chestbuddy.utils.background_processing import BackgroundWorker
from chestbuddy.core.services.csv_service import CSVService, CSVReadTask


@pytest.fixture
def csv_service() -> CSVService:
    """Fixture to create a CSVService instance."""
    return CSVService()


@pytest.fixture
def sample_csv_file() -> Path:
    """Create a sample CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("A,B,C\n")
        for i in range(100):
            f.write(f"{i},{i * 2},{i * 3}\n")
        file_path = f.name

    return Path(file_path)


@pytest.fixture
def large_csv_file() -> Path:
    """Create a larger CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("Date,Player Name,Source/Location,Chest Type,Value,Clan\n")

        for i in range(1000):
            f.write(
                f"2023-01-{(i % 30) + 1},Player{i},Location{i % 10},Chest{i % 5},{i * 10},Clan{i % 3}\n"
            )

        file_path = f.name

    return Path(file_path)


@pytest.fixture
def worker():
    """Fixture to create a worker and ensure it's cleaned up."""
    worker = BackgroundWorker()
    yield worker

    # Clean up the worker after the test
    if worker._thread.isRunning():
        worker._thread.quit()
        worker._thread.wait(1000)  # Wait up to 1 second for thread to finish


def test_csv_read_task_creation(csv_service: CSVService, sample_csv_file: Path):
    """Test that a CSV read task can be created correctly."""
    task = CSVReadTask(file_path=sample_csv_file)
    assert task is not None
    assert task.file_path == sample_csv_file
    assert task.chunk_size == 1000  # Default value
    assert not task.is_cancelled


def test_csv_read_task_execution(
    qtbot: QtBot, worker, csv_service: CSVService, sample_csv_file: Path
):
    """Test that a CSV read task can execute correctly and return the expected result."""
    # Create task
    task = CSVReadTask(file_path=sample_csv_file)

    # Track results
    result_data = [None]
    progress_signals = []

    # Connect signals
    worker.progress.connect(lambda current, total: progress_signals.append((current, total)))
    worker.finished.connect(lambda result: result_data.__setitem__(0, result))

    # Execute task
    worker.execute_task(task)

    # Wait for completion
    with qtbot.waitSignal(worker.finished, timeout=5000):
        pass

    # Check results
    assert result_data[0] is not None
    result_df, error = result_data[0]
    assert error is None
    assert result_df is not None
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 100
    assert "A" in result_df.columns
    assert "B" in result_df.columns
    assert "C" in result_df.columns
    assert len(progress_signals) > 0
    assert (
        progress_signals[-1][0] == progress_signals[-1][1]
    )  # Final progress should show completion


def test_csv_read_task_with_options(
    qtbot: QtBot, worker, csv_service: CSVService, sample_csv_file: Path
):
    """Test CSV read task with custom options (chunk size, encoding, etc.)."""
    # Create task with custom options
    task = CSVReadTask(
        file_path=sample_csv_file,
        chunk_size=10,
        encoding="utf-8",
        normalize_text=True,
        robust_mode=False,
    )

    # Track results
    result_data = [None]

    # Connect signals
    worker.finished.connect(lambda result: result_data.__setitem__(0, result))

    # Execute task
    worker.execute_task(task)

    # Wait for completion
    with qtbot.waitSignal(worker.finished, timeout=5000):
        pass

    # Check results
    assert result_data[0] is not None
    result_df, error = result_data[0]
    assert error is None
    assert result_df is not None
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 100


def test_csv_read_task_with_large_file(
    qtbot: QtBot, worker, csv_service: CSVService, large_csv_file: Path
):
    """Test that a CSV read task can handle larger files efficiently."""
    # Create task
    task = CSVReadTask(
        file_path=large_csv_file,
        chunk_size=100,  # Use smaller chunks to ensure multiple progress updates
    )

    # Track results
    result_data = [None]
    progress_signals = []

    # Connect signals
    worker.progress.connect(lambda current, total: progress_signals.append((current, total)))
    worker.finished.connect(lambda result: result_data.__setitem__(0, result))

    # Execute task
    worker.execute_task(task)

    # Wait for completion
    with qtbot.waitSignal(worker.finished, timeout=10000):
        pass

    # Check results
    assert result_data[0] is not None
    result_df, error = result_data[0]
    assert error is None
    assert result_df is not None
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df) == 1000
    assert len(progress_signals) > 1  # Should have multiple progress updates


def test_csv_read_task_error_handling(qtbot: QtBot, worker, csv_service: CSVService):
    """Test that a CSV read task properly handles errors."""
    # Create task with non-existent file
    task = CSVReadTask(file_path=Path("non_existent_file.csv"))

    # Track results
    finished_data = [None]

    # Connect signals to both finished and error
    # For non-existent files, the task returns (None, "File not found...") on finished signal
    # rather than raising an error
    worker.finished.connect(lambda result: finished_data.__setitem__(0, result))

    # Execute task
    worker.execute_task(task)

    # Wait for completion (not error)
    with qtbot.waitSignal(worker.finished, timeout=5000):
        pass

    # Check error handling through the finished data
    assert finished_data[0] is not None
    df, error_message = finished_data[0]
    assert df is None
    assert error_message is not None
    assert "File not found" in error_message


def test_csv_read_task_cancellation(
    qtbot: QtBot, worker, csv_service: CSVService, large_csv_file: Path
):
    """Test that a CSV read task can be cancelled during execution."""
    # Create task with a large file
    task = CSVReadTask(
        file_path=large_csv_file,
        chunk_size=10,  # Small chunk size to make it process slowly
    )

    # Track task cancellation directly
    task_cancelled = [False]
    original_cancel = task.cancel

    def track_cancel():
        task_cancelled[0] = True
        original_cancel()

    task.cancel = track_cancel

    # Execute task
    worker.execute_task(task)

    # Wait a moment to let task start
    qtbot.wait(100)

    # Cancel manually
    worker.cancel()

    # Wait a moment for cancellation to complete
    qtbot.wait(200)

    # Check cancellation was successful
    assert task_cancelled[0]
    assert task.is_cancelled

    # Wait for thread to clean up
    if worker._thread.isRunning():
        worker._thread.quit()
        worker._thread.wait(1000)


def test_csv_service_read_csv_background(
    qtbot: QtBot, csv_service: CSVService, sample_csv_file: Path
):
    """Test the CSVService read_csv_background method."""
    # Track results
    result_df = [None]
    error_message = [None]
    progress_values = []
    finished_called = [False]

    # Define callbacks
    def on_progress(current: int, total: int):
        progress_values.append((current, total))

    def on_finished(df: Optional[pd.DataFrame], error: Optional[str]):
        result_df[0] = df
        error_message[0] = error
        finished_called[0] = True

    # Call the background method
    worker = csv_service.read_csv_background(
        file_path=sample_csv_file, progress_callback=on_progress, finished_callback=on_finished
    )

    # Wait for completion - need to wait a bit as the callback isn't a signal
    for _ in range(50):  # Try for 5 seconds maximum
        if finished_called[0]:
            break
        qtbot.wait(100)

    # Check results
    assert finished_called[0]
    assert result_df[0] is not None
    assert isinstance(result_df[0], pd.DataFrame)
    assert len(result_df[0]) == 100
    assert error_message[0] is None
    assert len(progress_values) > 0
    assert progress_values[-1][0] == progress_values[-1][1]  # Final progress should show completion

    # Clean up the worker thread
    if worker._thread.isRunning():
        worker._thread.quit()
        worker._thread.wait(1000)
