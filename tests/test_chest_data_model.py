"""
Tests for the ChestDataModel class.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from PySide6.QtCore import QObject

from chestbuddy.core.models.chest_data_model import ChestDataModel


# Simple signal catcher for testing
class SignalCatcher(QObject):
    """Helper class to catch signals for testing."""

    def __init__(self, model):
        """Initialize the signal catcher."""
        super().__init__()
        self.data_changed_called = False
        self.validation_changed_called = False
        self.correction_applied_called = False

        model.data_changed.connect(self.on_data_changed)
        model.validation_changed.connect(self.on_validation_changed)
        model.correction_applied.connect(self.on_correction_applied)

    def on_data_changed(self):
        """Handle data changed signal."""
        self.data_changed_called = True

    def on_validation_changed(self):
        """Handle validation changed signal."""
        self.validation_changed_called = True

    def on_correction_applied(self):
        """Handle correction applied signal."""
        self.correction_applied_called = True


@pytest.fixture
def model():
    """Create a fresh ChestDataModel instance for testing."""
    with patch("PySide6.QtWidgets.QApplication"):
        model = ChestDataModel()
        model.initialize()
        return model


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        "DATE": ["2023-05-15", "2023-05-16"],
        "PLAYER": ["Feldjäger", "Burgmeister"],
        "SOURCE": ["Clan", "Tour"],
        "CHEST": ["Gold Chest", "Silver Chest"],
        "SCORE": [1000, 500],
        "CLAN": ["TestClan1", "TestClan2"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
        temp_file_path = temp_file.name

    # Clean up the file after the test
    yield temp_file_path
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


class TestChestDataModel:
    """Tests for the ChestDataModel class."""

    def test_initialization(self, model):
        """Test that model initializes correctly with empty data."""
        assert model._data is not None
        assert model.is_empty is True
        assert model.row_count == 0
        assert len(model.column_names) > 0

    def test_update_data(self, model, sample_data):
        """Test updating the model with new data."""
        # Update model with sample data
        model.update_data(sample_data)

        # Verify data was updated
        assert not model.is_empty
        assert model.row_count == len(sample_data)
        assert set(model.column_names) == set(sample_data.columns)

    def test_data_property(self, model, sample_data):
        """Test the data property returns a copy of the data."""
        # Update model with sample data
        model.update_data(sample_data)

        # Get data and verify it matches
        data = model.data
        assert data is not None
        assert len(data) == len(sample_data)
        assert set(data.columns) == set(sample_data.columns)

    def test_get_row(self, model, sample_data):
        """Test getting a specific row from the model."""
        # Update model with sample data
        model.update_data(sample_data)

        # Get a row and verify it matches
        row = model.get_row(0)
        assert row is not None
        assert isinstance(row, pd.Series)
        assert row["PLAYER"] == "Feldjäger"

    def test_add_row(self, model):
        """Test adding a new row to the model."""
        # Create initial empty model with columns
        model.init_model()

        # Add a new row
        new_row = {
            "DATE": "2023-05-20",
            "PLAYER": "TestPlayer",
            "SOURCE": "Somewhere",
            "CHEST": "Wooden Chest",
            "SCORE": 500,
            "CLAN": "TestClan",
        }
        model.add_row(new_row)

        # Check model was updated
        assert model.rowCount() == 1
        assert model.get_row(0)["PLAYER"] == "TestPlayer"

    def test_update_cell(self, model, sample_data):
        """Test updating a specific cell in the model."""
        # Update model with sample data
        model.update_data(sample_data)

        # Initial state
        start_value = model.get_row(0)["PLAYER"]

        # Update a cell
        model.update_cell(0, 1, "NewPlayer")  # Assuming column 1 is "PLAYER"

        # Verify cell was updated
        assert model.get_row(0)["PLAYER"] == "NewPlayer"
        assert model.get_row(0)["PLAYER"] != start_value

    def test_filter_data(self, model, sample_data):
        """Test filtering data in the model."""
        # Update model with sample data
        model.update_data(sample_data)

        # Apply filter to Player column
        model.filter_data("PLAYER", "Feldjäger")

        # Check filtered data
        assert model.filtered_rowCount() > 0
        for i in range(model.filtered_rowCount()):
            row_idx = model.mapToSource(model.index(i, 0)).row()
            row = model.get_row(row_idx)
            assert "Feldjäger" in row["PLAYER"]

    def test_validation_status(self, model, sample_data):
        """Test setting and getting validation status."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create validation status DataFrame
        validation_df = pd.DataFrame(
            {
                "Date_valid": [True, True, True, True],
                "Player Name_valid": [True, False, True, True],
                "Source/Location_valid": [True, True, True, True],
                "Chest Type_valid": [True, True, True, True],
                "Value_valid": [True, True, False, True],
                "Clan_valid": [True, True, True, True],
            },
            index=sample_data.index,
        )

        # Set validation status
        model.set_validation_status(validation_df)

        # Get validation status
        status = model.get_validation_status()

        # Verify validation status
        assert status is not None
        assert status.equals(validation_df)

        # We don't test get_invalid_rows as it's not in the API

    def test_correction_status(self, model, sample_data):
        """Test setting and getting correction status."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create correction status DataFrame
        correction_df = pd.DataFrame(
            {
                "Date_corrected": [False, False, False, False],
                "Player Name_corrected": [False, True, False, False],
                "Source/Location_corrected": [False, False, False, False],
                "Chest Type_corrected": [False, False, False, False],
                "Value_corrected": [False, False, True, False],
                "Clan_corrected": [False, False, False, False],
            },
            index=sample_data.index,
        )

        # Set correction status
        model.set_correction_status(correction_df)

        # Get correction status
        status = model.get_correction_status()

        # Verify correction status
        assert status is not None
        assert status.equals(correction_df)

        # We don't test get_corrected_rows as it's not in the API


def test_load_data(model, sample_data, temp_csv_file):
    """Test loading data from a CSV file."""
    # Save sample data to a temp file
    sample_data.to_csv(temp_csv_file, index=False)

    # Mock the read_csv function to avoid file IO and control the return value
    with patch("pandas.read_csv", return_value=sample_data):
        success = model.load_from_csv(temp_csv_file)

        # Verify data was loaded
        assert success
        assert not model.is_empty
        assert model.row_count == len(sample_data)


def test_signals(model, sample_data):
    """Test signal emissions."""
    # Create signal catcher
    catcher = SignalCatcher(model)

    # Emit data changed signal
    model.update_data(sample_data)
    assert catcher.data_changed_called

    # Emit validation changed signal
    validation_df = pd.DataFrame(index=sample_data.index)
    for col in model.EXPECTED_COLUMNS:
        validation_df[f"{col}_valid"] = True
    model.set_validation_status(validation_df)
    assert catcher.validation_changed_called

    # Emit correction applied signal
    correction_df = pd.DataFrame(index=sample_data.index)
    for col in model.EXPECTED_COLUMNS:
        correction_df[f"{col}_corrected"] = False
    model.set_correction_status(correction_df)
    assert catcher.correction_applied_called


def test_save_data(model, sample_data, temp_csv_file):
    """Test saving data to a CSV file."""
    # Update model with sample data
    model.update_data(sample_data)

    # Mock to_csv to avoid actual file IO
    with patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
        success = model.save_to_csv(temp_csv_file)

        # Verify saving was successful
        assert success
        mock_to_csv.assert_called_once()
