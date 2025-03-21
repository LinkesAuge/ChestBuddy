"""
Tests for the ChestDataModel class.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from PySide6.QtCore import QObject

from chestbuddy.core.models.chest_data_model import ChestDataModel


class SignalCatcher(QObject):
    """Helper class to catch signals emitted by the model."""

    def __init__(self):
        super().__init__()
        self.data_changed_called = False
        self.validation_changed_called = False
        self.correction_applied_called = False

    def on_data_changed(self):
        self.data_changed_called = True

    def on_validation_changed(self):
        self.validation_changed_called = True

    def on_correction_applied(self):
        self.correction_applied_called = True


@pytest.fixture
def model():
    """Create a fresh ChestDataModel instance for testing."""
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
def default_input_file():
    """Path to the default input file for testing."""
    return Path("data/input/Chests_input_test.csv")


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
        temp_file_path = temp_file.name

    # Clean up the file after the test
    yield temp_file_path
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


def test_initialization(model):
    """Test that model initializes with empty data."""
    assert model.is_empty
    assert model.row_count == 0
    assert isinstance(model.column_names, list)
    assert set(model.EXPECTED_COLUMNS) == {
        "Date",
        "Player Name",
        "Source/Location",
        "Chest Type",
        "Value",
        "Clan",
    }


def test_load_data(model, sample_data, temp_csv_file):
    """Test loading data into the model."""
    # Save sample data to temp CSV
    sample_data.to_csv(temp_csv_file, index=False)

    # Load data from CSV
    success = model.load_from_csv(temp_csv_file)

    # Verify loading was successful
    assert success
    assert not model.is_empty
    assert model.row_count == len(sample_data)
    assert set(model.column_names) == set(sample_data.columns)


def test_load_default_data(model, default_input_file):
    """Test loading the default input file."""
    if default_input_file.exists():
        success = model.load_from_csv(default_input_file)
        assert success
        assert not model.is_empty
        assert model.row_count > 0
        assert set(model.column_names) == set(model.EXPECTED_COLUMNS)


def test_data_manipulation(model, sample_data):
    """Test basic data manipulation methods."""
    # Set model data directly
    model.update_data(sample_data)

    # Test getting a row
    row = model.get_row(1)
    assert row is not None
    assert row["Player Name"] == "Krümelmonster"

    # Test updating a row
    updated_row = row.copy()
    updated_row["Value"] = 250
    model.update_row(1, updated_row)

    # Verify the update
    assert model.get_row(1)["Value"] == 250

    # Test adding a row
    new_row = {
        "Date": "2025-03-13",
        "Player Name": "NewPlayer",
        "Source/Location": "Level 35 epic Crypt",
        "Chest Type": "Golden Chest",
        "Value": 300,
        "Clan": "MY_CLAN",
    }
    model.add_row(new_row)

    # Verify row was added
    assert model.row_count == len(sample_data) + 1
    assert model.get_row(model.row_count - 1)["Player Name"] == "NewPlayer"

    # Test deleting a row
    model.delete_row(0)

    # Verify row was deleted
    assert model.row_count == len(sample_data)
    assert model.get_row(0)["Player Name"] == "Krümelmonster"


def test_filtering(model, sample_data):
    """Test data filtering functionality."""
    model.update_data(sample_data)

    # Filter by chest type
    filtered_data = model.filter_data({"Chest Type": "Infernal Chest"})
    assert len(filtered_data) == 1
    assert filtered_data.iloc[0]["Player Name"] == "Krümelmonster"

    # Filter by value greater than
    filtered_data = model.filter_data(lambda df: df["Value"] > 300)
    assert len(filtered_data) == 2
    assert "Rare Dragon Chest" in filtered_data["Chest Type"].values
    assert "Ancient Bastion Chest" in filtered_data["Chest Type"].values


def test_unique_values(model, sample_data):
    """Test getting unique values for a column."""
    model.update_data(sample_data)

    unique_chest_types = model.get_unique_values("Chest Type")
    assert set(unique_chest_types) == {
        "Fire Chest",
        "Infernal Chest",
        "Rare Dragon Chest",
        "Ancient Bastion Chest",
    }


def test_column_stats(model, sample_data):
    """Test getting statistics for a column."""
    model.update_data(sample_data)

    value_stats = model.get_column_statistics("Value")
    assert value_stats["min"] == 84
    assert value_stats["max"] == 550
    assert value_stats["mean"] == (275 + 84 + 350 + 550) / 4


def test_signals(model, sample_data):
    """Test that signals are emitted when data changes."""
    # Create signal catcher
    catcher = SignalCatcher()
    model.data_changed.connect(catcher.on_data_changed)
    model.validation_changed.connect(catcher.on_validation_changed)
    model.correction_applied.connect(catcher.on_correction_applied)

    # Update data and check signal
    model.update_data(sample_data)
    assert catcher.data_changed_called

    # Reset flags
    catcher.data_changed_called = False

    # Update row and check signal
    row = model.get_row(0)
    row["Value"] = 150
    model.update_row(0, row)
    assert catcher.data_changed_called

    # Set validation status
    catcher.data_changed_called = False
    validation_df = pd.DataFrame(index=model._data.index)
    for col in model.EXPECTED_COLUMNS:
        validation_df[f"{col}_valid"] = True
    validation_df.at[0, "Value_valid"] = False
    model.set_validation_status(validation_df)
    assert catcher.validation_changed_called

    # Set correction status
    catcher.validation_changed_called = False
    correction_df = pd.DataFrame(index=model._data.index)
    for col in model.EXPECTED_COLUMNS:
        correction_df[f"{col}_corrected"] = False
        correction_df[f"{col}_original"] = model._data[col].copy()
    correction_df.at[0, "Value_corrected"] = True
    model.set_correction_status(correction_df)
    assert catcher.correction_applied_called


def test_validation_status(model, sample_data):
    """Test setting and getting validation status."""
    model.update_data(sample_data)

    # Set validation status
    validation_df = pd.DataFrame(index=model._data.index)
    for col in model.EXPECTED_COLUMNS:
        validation_df[f"{col}_valid"] = True
    validation_df.at[0, "Value_valid"] = False
    model.set_validation_status(validation_df)

    # Get validation status
    status_df = model.get_validation_status()
    assert not status_df.empty
    assert status_df.at[0, "Value_valid"] == False
    assert status_df.at[1, "Value_valid"] == True


def test_correction_status(model, sample_data):
    """Test setting and getting correction status."""
    model.update_data(sample_data)

    # Set correction status
    correction_df = pd.DataFrame(index=model._data.index)
    for col in model.EXPECTED_COLUMNS:
        correction_df[f"{col}_corrected"] = False
        correction_df[f"{col}_original"] = model._data[col].copy()
    correction_df.at[0, "Value_corrected"] = True
    correction_df.at[0, "Value_original"] = 200
    model.set_correction_status(correction_df)

    # Get correction status
    status_df = model.get_correction_status()
    assert not status_df.empty
    assert status_df.at[0, "Value_corrected"] == True
    assert status_df.at[0, "Value_original"] == 200
    assert status_df.at[1, "Value_corrected"] == False


def test_save_data(model, sample_data, temp_csv_file):
    """Test saving data to CSV."""
    model.update_data(sample_data)

    # Save to CSV
    success = model.save_to_csv(temp_csv_file)
    assert success

    # Verify the file exists
    assert os.path.exists(temp_csv_file)

    # Load the saved file back and verify content
    saved_data = pd.read_csv(temp_csv_file)
    assert len(saved_data) == len(sample_data)
    assert set(saved_data.columns) == set(sample_data.columns)
