"""
Tests for CSV chunked reading and performance optimization.

This module tests the ability of the CSVService to handle large files efficiently.
"""

import os
import tempfile
import time
import gc
from pathlib import Path
from typing import Dict, List, Generator, Callable, Optional

import pandas as pd
import pytest

from chestbuddy.core.services.csv_service import CSVService


@pytest.fixture
def csv_service() -> CSVService:
    """Return a CSVService instance for testing."""
    return CSVService()


@pytest.fixture
def large_csv_file(tmp_path: Path) -> Path:
    """Create a large CSV file for testing."""
    # Create a large CSV file with random data
    file_path = tmp_path / "large_file.csv"
    rows = 10000  # Moderate size for testing

    # Create DataFrame with random data
    data = {
        "Date": pd.date_range(start="2020-01-01", periods=rows).astype(str),
        "Player Name": [f"Player{i}" for i in range(rows)],
        "Source/Location": [f"Location{i % 100}" for i in range(rows)],
        "Chest Type": [f"Chest{i % 20}" for i in range(rows)],
        "Value": [i % 1000 for i in range(rows)],
        "Clan": [f"Clan{i % 10}" for i in range(rows)],
    }

    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

    return file_path


def test_chunked_reading_basic(csv_service: CSVService, tmp_path: Path):
    """Test that chunked reading works correctly for basic CSV files."""
    # Create a test CSV file
    file_path = tmp_path / "test_chunked.csv"
    data = pd.DataFrame({"A": range(100), "B": [f"value_{i}" for i in range(100)]})
    data.to_csv(file_path, index=False)

    # Track progress callback calls
    progress_calls = []

    def progress_callback(current: int, total: int) -> None:
        progress_calls.append((current, total))

    # Read the file in chunks
    result_df, error = csv_service.read_csv_chunked(
        file_path, chunk_size=10, progress_callback=progress_callback
    )

    # Verify the results
    assert error is None
    assert result_df is not None
    assert len(result_df) == 100
    assert len(progress_calls) > 0

    # Verify data integrity
    assert list(result_df["A"]) == list(range(100))

    # Verify progress reporting
    assert progress_calls[-1][0] == progress_calls[-1][1]  # Last call should be at 100%


def test_large_file_performance(csv_service: CSVService, large_csv_file: Path):
    """Test performance with large CSV files."""
    # Measure time for chunked reading
    start_time = time.time()
    chunked_df, error = csv_service.read_csv_chunked(large_csv_file, chunk_size=1000)
    chunked_time = time.time() - start_time

    # Verify results
    assert error is None
    assert chunked_df is not None
    assert len(chunked_df) == 10000

    # We don't strictly test performance here as it's environment-dependent
    # But we can log it for information
    print(f"Chunked read time: {chunked_time:.2f}s")


def test_memory_efficiency(csv_service: CSVService, large_csv_file: Path):
    """Test that memory usage is controlled during chunked reading."""
    # We can't reliably test absolute memory usage in a unit test
    # But we can verify that the function completes successfully with a small chunk size
    # which indicates it's not loading the entire file at once

    # Use a very small chunk size to ensure chunking is happening
    chunked_df, error = csv_service.read_csv_chunked(large_csv_file, chunk_size=100)

    # Verify results
    assert error is None
    assert chunked_df is not None
    assert len(chunked_df) == 10000


def test_progress_reporting(csv_service: CSVService, large_csv_file: Path):
    """Test that progress callback is called correctly."""
    progress_values = []

    def progress_callback(current: int, total: int) -> None:
        progress_values.append((current, total))

    chunked_df, error = csv_service.read_csv_chunked(
        large_csv_file, chunk_size=1000, progress_callback=progress_callback
    )

    # Verify that callback was called multiple times
    assert len(progress_values) > 1

    # Verify progress reporting
    assert progress_values[0][0] > 0
    assert progress_values[-1][0] == progress_values[-1][1]  # Last call should be at 100%


def test_encoding_with_chunked_reading(csv_service: CSVService, tmp_path: Path):
    """Test that chunked reading handles different encodings correctly."""
    # Create test files with different encodings
    utf8_file = tmp_path / "utf8_chunked.csv"
    cp1252_file = tmp_path / "cp1252_chunked.csv"

    # Data with special characters
    data = pd.DataFrame(
        {"Name": ["Jürgen", "François", "Zoë"], "City": ["München", "Orléans", "Zürich"]}
    )

    # Save with different encodings
    data.to_csv(utf8_file, index=False, encoding="utf-8")
    data.to_csv(cp1252_file, index=False, encoding="cp1252")

    # Test UTF-8 file
    utf8_df, utf8_error = csv_service.read_csv_chunked(utf8_file, chunk_size=1)
    assert utf8_error is None
    assert utf8_df is not None
    assert utf8_df["Name"][0] == "Jürgen"

    # Test CP1252 file
    cp1252_df, cp1252_error = csv_service.read_csv_chunked(cp1252_file, chunk_size=1)
    assert cp1252_error is None
    assert cp1252_df is not None
    assert cp1252_df["Name"][0] == "Jürgen"


def test_error_handling_in_chunks(csv_service: CSVService, tmp_path: Path):
    """Test that errors during chunk processing are handled correctly."""
    # Create a CSV file with an error in the middle
    file_path = tmp_path / "error_in_middle.csv"

    with open(file_path, "w") as f:
        f.write("A,B,C\n")
        for i in range(50):
            f.write(f"{i},value_{i},x\n")
        # Add a line with too few columns (error)
        f.write("error_line,missing_column\n")
        for i in range(50, 100):
            f.write(f"{i},value_{i},y\n")

    # Test with robust_mode=True (skip bad lines)
    result_df, error = csv_service.read_csv_chunked(file_path, chunk_size=10, robust_mode=True)

    # Should complete and return data, possibly with a warning
    assert result_df is not None
    # We might not get an error message with robust_mode as pandas just warns
    # So just checking the data was loaded
    assert len(result_df) > 0

    # Test with robust_mode=False (fail on bad lines)
    result_df, error = csv_service.read_csv_chunked(file_path, chunk_size=10, robust_mode=False)

    # Should fail with an error
    assert error is not None
    assert "error" in error.lower() or "expected" in error.lower()
