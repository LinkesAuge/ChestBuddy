"""
test_validation_service.py

Description: Tests for the ValidationService class
"""

import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import MagicMock, patch

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.utils.config import ConfigManager


class TestValidationService:
    """Tests for the ValidationService class."""

    @pytest.fixture
    def test_dataframe(self):
        """Create a test dataframe for validation."""
        data = {
            "PLAYER": ["Player1", "Player2", "UnknownPlayer", "Player3", None],
            "CHEST": ["Gold Chest", "Bronze Chest", "Unknown Chest", "Silver Chest", "Gold Chest"],
            "SOURCE": ["Dungeon", "Cave", "Unknown Source", "Forest", "Mine"],
            "VALUE": [100, 50, 75, 200, 150],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock ConfigManager."""
        config = MagicMock(spec=ConfigManager)
        config.get_bool.side_effect = lambda section, key, default: {
            ("Validation", "case_sensitive"): False,
            ("Validation", "validate_on_import"): True,
        }.get((section, key), default)
        return config

    @pytest.fixture
    def validation_service(self, test_dataframe, mock_config_manager, tmp_path):
        """Create a ValidationService with test data and config."""
        # Create test validation files with unique names for each test
        test_id = id(test_dataframe)  # Unique identifier for this test run
        validation_dir = tmp_path / f"validation_{test_id}"
        validation_dir.mkdir()

        # Create player validation file
        player_file = validation_dir / "players.txt"
        with open(player_file, "w", encoding="utf-8") as f:
            f.write("Player1\nPlayer2\nPlayer3\n")

        # Create chest type validation file
        chest_file = validation_dir / "chest_types.txt"
        with open(chest_file, "w", encoding="utf-8") as f:
            f.write("Gold Chest\nSilver Chest\nBronze Chest\n")

        # Create source validation file
        source_file = validation_dir / "sources.txt"
        with open(source_file, "w", encoding="utf-8") as f:
            f.write("Dungeon\nCave\nForest\nMine\n")

        # Create data model
        data_model = ChestDataModel()
        data_model.update_data(test_dataframe)  # Use update_data, not set_dataframe

        # Create validation service directly without patching
        service = ValidationService(data_model, mock_config_manager)

        # Set validation list models directly
        service._player_list_model = ValidationListModel(player_file, False)
        service._chest_type_list_model = ValidationListModel(chest_file, False)
        service._source_list_model = ValidationListModel(source_file, False)

        yield service

        # Clean up after the test
        mock_config_manager.reset_mock()
        service._reset_for_testing()

    def test_initialization(self, validation_service):
        """Test that the service initializes correctly."""
        assert validation_service is not None
        assert validation_service._data_model is not None
        assert validation_service._player_list_model is not None
        assert validation_service._chest_type_list_model is not None
        assert validation_service._source_list_model is not None
        assert validation_service.is_case_sensitive() is False
        assert validation_service.get_validate_on_import() is True

    def test_validate_data(self, validation_service):
        """Test the validate_data method."""
        # Reset any state from previous tests
        validation_service._reset_for_testing()

        # Run validation
        results = validation_service.validate_data()

        # Check that player validation found an error
        assert "player_validation" in results
        player_errors = results["player_validation"]
        assert 2 in player_errors  # UnknownPlayer at index 2
        assert 4 in player_errors  # None at index 4

        # Check that chest type validation found an error
        assert "chest_type_validation" in results
        chest_errors = results["chest_type_validation"]
        assert 2 in chest_errors  # Unknown Chest at index 2

        # Check that source validation found an error
        assert "source_validation" in results
        source_errors = results["source_validation"]
        assert 2 in source_errors  # Unknown Source at index 2

    def test_validate_field(self, validation_service):
        """Test the validate_field method."""
        # Reset any state from previous tests
        validation_service._reset_for_testing()

        # Test valid player
        assert validation_service.validate_field("player", "Player1") is True

        # Test invalid player
        assert validation_service.validate_field("player", "UnknownPlayer") is False

        # Test valid chest type
        assert validation_service.validate_field("chest", "Gold Chest") is True

        # Test invalid chest type
        assert validation_service.validate_field("chest", "Unknown Chest") is False

        # Test valid source
        assert validation_service.validate_field("source", "Dungeon") is True

        # Test invalid source
        assert validation_service.validate_field("source", "Unknown Source") is False

        # Test case insensitivity
        assert validation_service.validate_field("player", "player1") is True

    def test_add_to_validation_list(self, validation_service):
        """Test adding entries to validation lists."""
        # Reset any state from previous tests
        validation_service._reset_for_testing()

        # Add new player
        assert validation_service.add_to_validation_list("player", "NewPlayer") is True
        assert validation_service.validate_field("player", "NewPlayer") is True

        # Add new chest type
        assert validation_service.add_to_validation_list("chest", "Diamond Chest") is True
        assert validation_service.validate_field("chest", "Diamond Chest") is True

        # Add new source
        assert validation_service.add_to_validation_list("source", "Mountain") is True
        assert validation_service.validate_field("source", "Mountain") is True

        # Test adding existing entry
        assert validation_service.add_to_validation_list("player", "Player1") is False

    def test_set_case_sensitive(self, validation_service):
        """Test setting case sensitivity."""
        # Reset any state from previous tests
        validation_service._reset_for_testing()

        # Default is case insensitive
        assert validation_service.validate_field("player", "player1") is True

        # Set to case sensitive
        validation_service.set_case_sensitive(True)
        assert validation_service.is_case_sensitive() is True

        # Now validation should be case sensitive
        assert validation_service.validate_field("player", "player1") is False
        assert validation_service.validate_field("player", "Player1") is True

    def test_validation_preferences(self, validation_service):
        """Test getting and setting validation preferences."""
        # Reset any state from previous tests
        validation_service._reset_for_testing()

        # Get current preferences
        prefs = validation_service.get_validation_preferences()
        assert prefs["case_sensitive"] is False
        assert prefs["validate_on_import"] is True

        # Update preferences
        new_prefs = {"case_sensitive": True, "validate_on_import": False}
        validation_service.set_validation_preferences(new_prefs)

        # Check updated preferences
        assert validation_service.is_case_sensitive() is True
        assert validation_service.get_validate_on_import() is False

        # Preferences should be updated in the model
        assert validation_service._player_list_model.is_case_sensitive() is True
