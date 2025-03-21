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
    """Create sample data for testing that matches our input file structure."""
    return pd.DataFrame(
        {
            "Date": ["2025-03-11", "2025-03-11", "2025-03-11", "2025-03-12"],
            "Player Name": ["Feldjäger", "Krümelmonster", "OsmanlıTorunu", "D4rkBlizZ4rD"],
            "Source/Location": [
                "Level 25 Crypt",
                "Level 20 Crypt",
                "Level 15 rare Crypt",
                "Level 30 rare Crypt",
            ],
            "Chest Type": [
                "Fire Chest",
                "Infernal Chest",
                "Rare Dragon Chest",
                "Ancient Bastion Chest",
            ],
            "Value": [275, 84, 350, 550],
            "Clan": ["MY_CLAN", "MY_CLAN", "MY_CLAN", "MY_CLAN"],
        }
    )


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
        assert row["Player Name"] == "Feldjäger"

    def test_add_row(self, model):
        """Test adding a row to the model."""
        # Create new row
        new_row = {
            "Date": "2025-03-13",
            "Player Name": "New Player",
            "Source/Location": "New Location",
            "Chest Type": "New Chest",
            "Value": 999,
            "Clan": "MY_CLAN",
        }

        # Add row
        model.add_row(new_row)

        # Verify row was added
        assert model.row_count == 1
        assert model.get_row(0)["Player Name"] == "New Player"

    def test_filtering(self, model, sample_data):
        """Test filtering the data."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create a filter using a dictionary (current API)
        filtered_data = model.filter_data(
            {"Value": [350, 550]}
        )  # Value range filter for values greater than 300

        # Verify filtering worked
        assert filtered_data is not None
        assert len(filtered_data) == 2  # Two rows where Value is in range [350, 550]
        assert all(filtered_data["Value"].between(350, 550))

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
