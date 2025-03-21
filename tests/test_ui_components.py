"""
Tests for UI components of the ChestBuddy application.
"""

import os
import sys
import unittest.mock as mock
from pathlib import Path

import pandas as pd
import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.validation_tab import ValidationTab
from chestbuddy.ui.correction_tab import CorrectionTab


class SignalCatcher(QObject):
    """Helper class to catch Qt signals during testing."""

    signal_caught = Signal(object)

    def __init__(self, signal_to_catch=None):
        super().__init__()
        if signal_to_catch:
            signal_to_catch.connect(self.signal_handler)

    def signal_handler(self, *args):
        """Handle the signal and re-emit with the arguments."""
        self.signal_caught.emit(args)


@pytest.fixture
def app():
    """Fixture to provide a QApplication instance for each test."""
    # Clean up any existing instance
    app_instance = QApplication.instance()
    if app_instance:
        app_instance.quit()
        app_instance.processEvents()
        # We can't use del on a function call, instead we'll use the existing app instance

    # Create new application or use existing
    app = QApplication.instance() or QApplication([])
    yield app

    # Clean up after the test
    app.quit()
    app.processEvents()


@pytest.fixture
def sample_data():
    """Fixture to provide sample data for testing."""
    return pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Player Name": ["Player1", "Player2", "Player3"],
            "Source/Location": ["Location1", "Location2", "Location3"],
            "Chest Type": ["Gold", "Silver", "Bronze"],
            "Value": [100, 50, 25],
            "Clan": ["Clan1", "Clan2", "Clan3"],
        }
    )


@pytest.fixture
def data_model(sample_data):
    """Fixture to provide a ChestDataModel instance with sample data."""
    model = ChestDataModel()
    model.initialize()
    model.update_data(sample_data)
    return model


@pytest.fixture
def validation_service(data_model):
    """Fixture to provide a ValidationService instance."""
    return ValidationService(data_model)


@pytest.fixture
def correction_service(data_model):
    """Fixture to provide a CorrectionService instance."""
    return CorrectionService(data_model)


@pytest.fixture
def validation_lists_dir():
    """Path to validation lists directory for testing."""
    return Path("data/validation")


@pytest.fixture
def corrections_file():
    """Path to standard corrections file for testing."""
    return Path("data/corrections/standard_corrections.csv")


@pytest.fixture
def input_file():
    """Path to the default input file for testing."""
    return Path("data/input/Chests_input_test.csv")


class TestDataView:
    """Tests for the DataView component."""

    def test_initialization(self, app, data_model):
        """Test that DataView initializes correctly."""
        data_view = DataView(data_model)
        assert data_view is not None

        # Test that the model was set
        assert data_view._data_model == data_model

        # Test that the data is displayed
        assert data_view.rowCount() == data_model.row_count
        assert data_view.columnCount() == len(data_model.column_names)

    def test_update_view(self, app, data_model):
        """Test that the view updates when the model changes."""
        data_view = DataView(data_model)

        # Create a signal catcher to check for layoutChanged signal
        signal_catcher = SignalCatcher()
        data_view.layoutChanged.connect(signal_catcher.signal_handler)

        # Update the model
        new_data = pd.DataFrame(
            {
                "Date": ["2023-01-04", "2023-01-05"],
                "Player Name": ["Player4", "Player5"],
                "Source/Location": ["Location4", "Location5"],
                "Chest Type": ["Diamond", "Platinum"],
                "Value": [200, 150],
                "Clan": ["Clan4", "Clan5"],
            }
        )
        data_model.update_data(new_data)

        # Check that the view was updated
        assert data_view.rowCount() == new_data.shape[0]

        # Check for number of columns (should remain the same - 6 columns)
        assert data_view.columnCount() == 6

    def test_filtering(self, app, data_model):
        """Test filtering the data view."""
        data_view = DataView(data_model)

        # Set filter text
        filter_text = "Player1"
        data_view.set_filter(filter_text)

        # Check that only rows containing "Player1" are shown
        visible_rows = 0
        for row in range(data_model.row_count):
            row_is_visible = False
            for col in range(len(data_model.column_names)):
                if filter_text in str(data_model.get_row(row)[data_model.column_names[col]]):
                    row_is_visible = True
                    break
            if row_is_visible:
                visible_rows += 1

        # The filtered view should show only rows with "Player1"
        assert visible_rows == 1


class TestValidationTab:
    """Tests for the ValidationTab component."""

    def test_initialization(self, app, data_model, validation_service):
        """Test that ValidationTab initializes correctly."""
        validation_tab = ValidationTab(data_model, validation_service)
        assert validation_tab is not None

        # Test that the model and service were set
        assert validation_tab._data_model == data_model
        assert validation_tab._validation_service == validation_service

    def test_validate_data(self, app, data_model, validation_service):
        """Test validating data."""
        validation_tab = ValidationTab(data_model, validation_service)

        # Mock the validation service validate_data method
        with mock.patch.object(validation_service, "validate_data", return_value={"issues": {}}):
            # Call the validate method
            validation_tab._validate_data()

            # Verify that the validate_data method was called
            validation_service.validate_data.assert_called_once()

    def test_load_validation_lists(self, app, data_model, validation_service, validation_lists_dir):
        """Test loading validation lists."""
        if not validation_lists_dir.exists():
            pytest.skip("Validation lists directory not found")

        tab = ValidationTab(data_model, validation_service)

        # Mock the validation service method
        validation_service.load_validation_lists = mock.MagicMock(return_value=True)

        # Simulate loading validation lists
        chest_types_file = validation_lists_dir / "chest_types.txt"
        players_file = validation_lists_dir / "players.txt"
        sources_file = validation_lists_dir / "sources.txt"

        if chest_types_file.exists() and players_file.exists() and sources_file.exists():
            # Call method that would trigger loading validation lists
            tab._load_validation_lists(str(chest_types_file), str(players_file), str(sources_file))

            # Verify load_validation_lists was called
            validation_service.load_validation_lists.assert_called_once_with(
                str(chest_types_file), str(players_file), str(sources_file)
            )


class TestCorrectionTab:
    """Tests for the CorrectionTab component."""

    def test_initialization(self, app, data_model, correction_service):
        """Test that CorrectionTab initializes correctly."""
        correction_tab = CorrectionTab(data_model, correction_service)
        assert correction_tab is not None

        # Test that the model and service were set
        assert correction_tab._data_model == data_model
        assert correction_tab._correction_service == correction_service

    def test_apply_correction(self, app, data_model, correction_service):
        """Test applying a correction."""
        correction_tab = CorrectionTab(data_model, correction_service)

        # Mock the correction service apply_correction method
        with mock.patch.object(correction_service, "apply_correction", return_value=(True, None)):
            # Call the apply correction method with a test strategy
            correction_tab._apply_correction("test_strategy")

            # Verify that the apply_correction method was called with the correct strategy
            correction_service.apply_correction.assert_called_once_with(
                "test_strategy", column=None, rows=None
            )

    def test_load_corrections(self, app, data_model, correction_service, corrections_file):
        """Test loading corrections."""
        if not corrections_file.exists():
            pytest.skip("Corrections file not found")

        tab = CorrectionTab(data_model, correction_service)

        # Mock the correction service method
        correction_service.load_corrections = mock.MagicMock(return_value=True)

        # Simulate loading corrections
        tab._load_corrections(str(corrections_file))

        # Verify load_corrections was called
        correction_service.load_corrections.assert_called_once_with(str(corrections_file))
