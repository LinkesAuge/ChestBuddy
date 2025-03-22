import os
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path

from chestbuddy.core.services.data_manager import DataManager


@pytest.fixture
def data_model():
    """Create a mock data model."""
    model = MagicMock()
    model.data = pd.DataFrame()
    model.is_empty = False
    model.update_data = MagicMock()
    model.blockSignals = MagicMock()
    return model


@pytest.fixture
def csv_service():
    """Create a mock CSV service."""
    service = MagicMock()
    service.read_csv = MagicMock(return_value=(pd.DataFrame(), "Success"))
    service.write_csv = MagicMock(return_value=(True, "Success"))
    return service


@pytest.fixture
def data_manager(data_model, csv_service):
    """Create a DataManager instance with mock dependencies."""
    return DataManager(data_model, csv_service)


def test_load_single_csv(data_manager, csv_service, data_model):
    """Test loading a single CSV file."""
    # Create test data
    test_df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    csv_service.read_csv.return_value = (test_df, "Successfully loaded")

    # Run the method with a single file path
    file_path = "/path/to/file.csv"
    data_manager.load_csv(file_path)

    # Verify the background worker was used with the correct parameters
    # This is hard to test directly, so we'll just verify that blockSignals was called
    data_model.blockSignals.assert_called_with(True)


def test_load_multiple_csv(data_manager, csv_service, data_model):
    """Test loading multiple CSV files."""
    # Mock the _worker.run_task method
    data_manager._worker.run_task = MagicMock()

    # Run the method with multiple file paths
    file_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
    data_manager.load_csv(file_paths)

    # Verify run_task was called with _load_multiple_files as the first argument
    run_task_args = data_manager._worker.run_task.call_args[0]
    assert run_task_args[0] == data_manager._load_multiple_files
    assert run_task_args[1] == file_paths

    # Verify blockSignals was called
    data_model.blockSignals.assert_called_with(True)


def test_load_multiple_csv_integration(data_manager, csv_service, data_model):
    """Test the actual implementation of loading multiple files."""
    # Create test dataframes
    df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    df2 = pd.DataFrame({"A": [7, 8, 9], "B": [10, 11, 12]})

    # Set up the CSV service to return different dataframes for different files
    def mock_read_csv(file_path):
        if "file1" in file_path:
            return df1, "Loaded file1"
        else:
            return df2, "Loaded file2"

    csv_service.read_csv.side_effect = mock_read_csv

    # Override _map_columns to return the dataframe unchanged
    data_manager._map_columns = lambda df: df

    # Call the method directly
    result = data_manager._load_multiple_files(["/path/to/file1.csv", "/path/to/file2.csv"])

    # Check the result
    combined_df, message = result
    assert combined_df is not None
    assert "Successfully loaded" in message
    assert len(combined_df) == 6  # Combined length of both dataframes
    assert list(combined_df["A"]) == [1, 2, 3, 7, 8, 9]  # Values from both dataframes


def test_load_multiple_csv_with_errors(data_manager, csv_service, data_model):
    """Test handling errors when loading multiple files."""
    # Create one valid dataframe and one error
    df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

    # Set up the CSV service to return a dataframe for one file and error for another
    def mock_read_csv(file_path):
        if "file1" in file_path:
            return df1, "Loaded file1"
        else:
            return None, "Error with file2"

    csv_service.read_csv.side_effect = mock_read_csv

    # Override _map_columns to return the dataframe unchanged
    data_manager._map_columns = lambda df: df

    # Call the method directly
    result = data_manager._load_multiple_files(["/path/to/file1.csv", "/path/to/file2.csv"])

    # Check the result
    combined_df, message = result
    assert combined_df is not None  # Should still get a dataframe from the successful file
    assert "Successfully loaded" in message
    assert "Some files had errors" in message
    assert len(combined_df) == 3  # Length of the one successful dataframe
