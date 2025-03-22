"""
test_column_mapping.py

Tests for CSV column mapping functionality in DataManager
"""

import pytest
import pandas as pd
from pathlib import Path

from chestbuddy.core.services.data_manager import DataManager
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.utils.config import ConfigManager


@pytest.fixture
def config_manager():
    """Create a test config manager."""
    return ConfigManager()


@pytest.fixture
def data_manager(config_manager):
    """Create a test data manager."""
    return DataManager(config_manager)


@pytest.fixture
def old_format_data():
    """Create sample data with old format column names."""
    data = {
        "Date": ["2023-05-15", "2023-05-16"],
        "Player Name": ["Feldjäger", "Burgmeister"],
        "Source/Location": ["Clan", "Tour"],
        "Chest Type": ["Gold Chest", "Silver Chest"],
        "Value": [1000, 500],
        "Clan": ["TestClan1", "TestClan2"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def new_format_data():
    """Create sample data with new format column names."""
    data = {
        "DATE": ["2023-05-15", "2023-05-16"],
        "PLAYER": ["Feldjäger", "Burgmeister"],
        "SOURCE": ["Clan", "Tour"],
        "CHEST": ["Gold Chest", "Silver Chest"],
        "SCORE": [1000, 500],
        "CLAN": ["TestClan1", "TestClan2"],
    }
    return pd.DataFrame(data)


def test_map_columns_with_old_format(data_manager, old_format_data):
    """Test mapping from old format to expected column names."""
    result = data_manager._map_columns(old_format_data)

    # Check result is not None
    assert result is not None

    # Check that new column names exist in the result
    for col in ChestDataModel.EXPECTED_COLUMNS:
        assert col in result.columns

    # Check data was preserved
    assert len(result) == len(old_format_data)
    assert result["PLAYER"].iloc[0] == "Feldjäger"
    assert result["SCORE"].iloc[0] == 1000


def test_map_columns_with_new_format(data_manager, new_format_data):
    """Test mapping when columns already match expected format."""
    result = data_manager._map_columns(new_format_data)

    # Check result is not None
    assert result is not None

    # Check columns remain the same
    for col in ChestDataModel.EXPECTED_COLUMNS:
        assert col in result.columns

    # Check data was preserved
    assert len(result) == len(new_format_data)
    assert result["PLAYER"].iloc[0] == "Feldjäger"
    assert result["SCORE"].iloc[0] == 1000


def test_map_columns_with_custom_mapping(data_manager, config_manager, old_format_data):
    """Test mapping with custom mapping from config."""
    # Set up custom mapping in config
    config_manager.set(
        "ColumnMapping",
        "mapping",
        {
            "Date": "DATE",
            "Player Name": "PLAYER_CUSTOM",
            "Source/Location": "SOURCE_LOCATION",
            "Chest Type": "CHEST_TYPE",
            "Value": "VALUE",
            "Clan": "CLAN",
        },
    )

    result = data_manager._map_columns(old_format_data)

    # Check custom column names exist in the result
    assert "PLAYER_CUSTOM" in result.columns
    assert "SOURCE_LOCATION" in result.columns

    # Check data was preserved
    assert len(result) == len(old_format_data)
    assert result["PLAYER_CUSTOM"].iloc[0] == "Feldjäger"
    assert result["VALUE"].iloc[0] == 1000
