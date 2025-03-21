"""
Tests for the ChestBuddy application.
"""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from chestbuddy.app import ChestBuddyApp


@pytest.fixture
def app():
    """QApplication fixture that ensures a clean application instance for each test."""
    # Clean up any existing QApplication instance
    app_instance = QApplication.instance()
    if app_instance:
        app_instance.quit()
        app_instance.processEvents()
        # We can't use del on a function call, instead we'll use the existing app instance

    # Create new application instance
    app = QApplication.instance() or QApplication([])
    yield app

    # Clean up after the test
    app.quit()
    app.processEvents()


@pytest.fixture
def chest_buddy_app(app):
    """Create a ChestBuddyApp instance for testing."""
    # Mock to avoid creating a new QApplication
    with patch("chestbuddy.app.QApplication", return_value=app):
        # Initialize the application without starting the UI
        chest_app = ChestBuddyApp()
        chest_app.initialize()
        yield chest_app


@pytest.fixture
def default_input_file():
    """Path to the default input file for testing."""
    return Path("data/input/Chests_input_test.csv")


@pytest.fixture
def validation_lists_dir():
    """Path to validation lists directory for testing."""
    return Path("data/validation")


@pytest.fixture
def corrections_file():
    """Path to standard corrections file for testing."""
    return Path("data/corrections/standard_corrections.csv")


def test_app_initialization(chest_buddy_app):
    """Test that the application initializes correctly."""
    # Check that key attributes are set
    assert hasattr(chest_buddy_app, "_data_model")
    assert hasattr(chest_buddy_app, "_csv_service")
    assert hasattr(chest_buddy_app, "_validation_service")
    assert hasattr(chest_buddy_app, "_correction_service")
    assert hasattr(chest_buddy_app, "_main_window")


def test_start_app(chest_buddy_app, monkeypatch):
    """Test starting the application."""
    # Mock the main window show method
    mock_show = MagicMock()
    monkeypatch.setattr(chest_buddy_app._main_window, "show", mock_show)

    # Start the application
    chest_buddy_app.start()

    # Verify that the main window show method was called
    mock_show.assert_called_once()


@patch("chestbuddy.core.services.csv_service.CSVService.read_csv")
def test_load_csv(mock_read_csv, chest_buddy_app, default_input_file):
    """Test loading a CSV file."""
    mock_read_csv.return_value = True

    # Call the method with default input file
    if default_input_file.exists():
        result = chest_buddy_app.load_csv(str(default_input_file))

        # Verify the result and that the service was called
        assert result
        mock_read_csv.assert_called_once_with(chest_buddy_app._data_model, str(default_input_file))


@patch("chestbuddy.core.services.csv_service.CSVService.write_csv")
def test_save_csv(mock_write_csv, chest_buddy_app):
    """Test saving to a CSV file."""
    mock_write_csv.return_value = True

    # Create a temporary output file path
    temp_output = "temp_output.csv"

    # Call the method
    result = chest_buddy_app.save_csv(temp_output)

    # Verify the result and that the service was called
    assert result
    mock_write_csv.assert_called_once_with(chest_buddy_app._data_model, temp_output)


@patch("chestbuddy.core.services.validation_service.ValidationService.load_validation_lists")
@patch("chestbuddy.core.services.validation_service.ValidationService.validate_data")
def test_validate_data(mock_validate_data, mock_load_lists, chest_buddy_app, validation_lists_dir):
    """Test validating data."""
    mock_load_lists.return_value = True
    mock_validate_data.return_value = {"total_issues": 0, "rules_applied": 4}

    # Check if validation lists exist
    if validation_lists_dir.exists():
        chest_types_file = validation_lists_dir / "chest_types.txt"
        players_file = validation_lists_dir / "players.txt"
        sources_file = validation_lists_dir / "sources.txt"

        if chest_types_file.exists() and players_file.exists() and sources_file.exists():
            # Load validation lists
            chest_buddy_app.load_validation_lists(
                str(chest_types_file), str(players_file), str(sources_file)
            )

            # Call validate method
            result = chest_buddy_app.validate_data()

            # Verify validation was called
            assert result
            mock_validate_data.assert_called_once()


@patch("chestbuddy.core.services.correction_service.CorrectionService.load_corrections")
@patch("chestbuddy.core.services.correction_service.CorrectionService.apply_correction")
def test_apply_correction(
    mock_apply_correction, mock_load_corrections, chest_buddy_app, corrections_file
):
    """Test applying corrections."""
    mock_load_corrections.return_value = True
    mock_apply_correction.return_value = (True, None)

    # Check if corrections file exists
    if corrections_file.exists():
        # Load corrections
        chest_buddy_app.load_corrections(str(corrections_file))

        # Apply a correction
        result = chest_buddy_app.apply_correction("fill_missing_mean", "Value")

        # Verify correction was applied
        assert result
        mock_apply_correction.assert_called_once_with("fill_missing_mean", "Value", rows=None)


@patch("chestbuddy.core.services.csv_service.CSVService.export_validation_issues")
def test_export_validation_issues(mock_export, chest_buddy_app):
    """Test exporting validation issues."""
    mock_export.return_value = True

    # Create a temporary output file path
    temp_output = "validation_issues.csv"

    # Call the method
    result = chest_buddy_app.export_validation_issues(temp_output)

    # Verify the result and that the service was called
    assert result
    mock_export.assert_called_once_with(chest_buddy_app._data_model, temp_output)
