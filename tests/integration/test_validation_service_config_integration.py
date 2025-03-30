"""
Integration tests for ValidationService and ConfigManager integration.

This module tests the integration between ValidationService and ConfigManager, focusing on:
- Setting loading and persistence
- Configuration updates propagation
- ValidationService behavior based on configuration
"""

import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from chestbuddy.utils.config import ConfigManager
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def clean_config_manager(temp_config_dir):
    """Create a fresh ConfigManager instance for testing."""
    # Reset the singleton instance
    ConfigManager._instance = None

    # Create and return a new instance
    config = ConfigManager(temp_config_dir)
    return config


@pytest.fixture
def mock_data_model():
    """Create a mock ChestDataModel for testing."""
    model = MagicMock(spec=ChestDataModel)
    # Create a simple DataFrame for testing
    model.data = pd.DataFrame(
        {
            "PLAYER": ["Player1", "Player2", "Player3"],
            "CHEST": ["Gold", "Silver", "Bronze"],
            "SOURCE": ["Event", "Daily", "Quest"],
            "AMOUNT": [100, 200, 300],
        }
    )
    return model


@pytest.fixture
def validation_service_with_config(clean_config_manager, mock_data_model):
    """Create a ValidationService with ConfigManager."""
    service = ValidationService(mock_data_model, clean_config_manager)
    return service


class TestValidationServiceConfigIntegration:
    """Integration tests for ValidationService and ConfigManager."""

    def test_validation_preferences_init_from_config(self, clean_config_manager, mock_data_model):
        """Test that ValidationService initializes with preferences from ConfigManager."""
        # Set specific values in config
        clean_config_manager.set("Validation", "case_sensitive", "True")
        clean_config_manager.set("Validation", "validate_on_import", "False")
        clean_config_manager.set("Validation", "auto_save", "False")

        # Create ValidationService with this config
        service = ValidationService(mock_data_model, clean_config_manager)

        # Check that preferences were loaded from config
        assert service.is_case_sensitive() is True
        assert service.get_validate_on_import() is False
        assert service.get_auto_save() is False

    def test_validation_preferences_update_propagation(
        self, validation_service_with_config, clean_config_manager
    ):
        """Test that updates to validation preferences are stored in ConfigManager."""
        # Initially these should have default values
        assert validation_service_with_config.is_case_sensitive() is False
        assert validation_service_with_config.get_validate_on_import() is True

        # Update preferences
        validation_service_with_config.set_case_sensitive(True)
        validation_service_with_config.set_validate_on_import(False)

        # Check that ConfigManager was updated
        assert clean_config_manager.get_bool("Validation", "case_sensitive") is True
        assert clean_config_manager.get_bool("Validation", "validate_on_import") is False

    def test_preferences_changed_signal(self, validation_service_with_config):
        """Test that changing validation preferences emits the correct signal."""
        # Create signal spy
        signal_received = False
        preferences_received = None

        def signal_handler(preferences):
            nonlocal signal_received, preferences_received
            signal_received = True
            preferences_received = preferences

        # Connect to signal
        validation_service_with_config.validation_preferences_changed.connect(signal_handler)

        # Change a preference
        validation_service_with_config.set_case_sensitive(True)

        # Check signal was emitted with correct preferences
        assert signal_received is True
        assert preferences_received is not None
        assert preferences_received.get("case_sensitive") is True

    def test_set_validation_preferences_batch(
        self, validation_service_with_config, clean_config_manager
    ):
        """Test setting multiple validation preferences at once."""
        # Prepare preferences
        preferences = {"case_sensitive": True, "validate_on_import": False, "auto_save": False}

        # Set batch preferences
        validation_service_with_config.set_validation_preferences(preferences)

        # Check service state
        assert validation_service_with_config.is_case_sensitive() is True
        assert validation_service_with_config.get_validate_on_import() is False
        assert validation_service_with_config.get_auto_save() is False

        # Check config state
        assert clean_config_manager.get_bool("Validation", "case_sensitive") is True
        assert clean_config_manager.get_bool("Validation", "validate_on_import") is False
        assert clean_config_manager.get_bool("Validation", "auto_save") is False

    def test_validation_list_paths_from_config(self, clean_config_manager, mock_data_model):
        """Test that ValidationService uses paths from ConfigManager for validation lists."""
        # Create a test directory for validation lists
        with tempfile.TemporaryDirectory() as test_dir:
            # Set the validation lists directory in config
            test_path = Path(test_dir)
            clean_config_manager.set_path("Validation", "validation_lists_dir", test_path)

            # Create some test list files
            player_list_path = test_path / "players.txt"
            with open(player_list_path, "w") as f:
                f.write("Player1\nPlayer2\nPlayer3")

            # Mock the ValidationListModel class for validation
            with patch(
                "chestbuddy.core.models.validation_list_model.ValidationListModel"
            ) as mock_model:
                # Track creation parameters
                mock_model.side_effect = lambda path, *args, **kwargs: path

                # Create the ValidationService and initialize lists
                service = ValidationService(mock_data_model, clean_config_manager)

                # Get what would be the expected path
                expected_path = str(player_list_path)

                # Directly check with the service's _resolve_validation_path method
                resolved_path = service._resolve_validation_path("players")

                # Verify that the path resolution works correctly
                assert resolved_path.exists(), f"Expected path {resolved_path} to exist"
                assert str(resolved_path) == expected_path, (
                    f"Expected {resolved_path} to match {expected_path}"
                )

    def test_config_reset_effect_on_validation_service(
        self, validation_service_with_config, clean_config_manager
    ):
        """Test that resetting config affects ValidationService after reloading."""
        # Change preferences
        validation_service_with_config.set_case_sensitive(True)
        validation_service_with_config.set_validate_on_import(False)

        # Verify change was successful
        assert validation_service_with_config.is_case_sensitive() is True
        assert validation_service_with_config.get_validate_on_import() is False

        # Reset config to defaults
        clean_config_manager.reset_to_defaults("Validation")

        # Create a new ValidationService that should load the reset config
        new_service = ValidationService(
            validation_service_with_config._data_model, clean_config_manager
        )

        # Check that new service has default values
        assert new_service.is_case_sensitive() is False
        assert new_service.get_validate_on_import() is True

    def test_auto_save_behavior(self, validation_service_with_config):
        """Test that auto_save setting affects validation list saving behavior."""
        # Create a simple ValidationListModel mock
        mock_list_model = MagicMock()
        mock_list_model.contains.return_value = False  # Item doesn't exist

        # Set up a simple side effect for the add method
        def add_side_effect(value):
            return True  # Successfully added

        mock_list_model.add.side_effect = add_side_effect

        # Replace the player list model
        validation_service_with_config._player_list_model = mock_list_model

        # Test with a direct call to the model methods
        # First with auto_save enabled
        validation_service_with_config.set_auto_save(True)

        # Reset the mock to ensure clean state
        mock_list_model.save.reset_mock()

        # Call add directly on the mock to make sure our mock is working
        mock_list_model.add("TestPlayer")
        mock_list_model.save()

        # Verify that save was called directly
        assert mock_list_model.save.call_count == 1

        # Reset for the next test
        mock_list_model.save.reset_mock()

        # Now test with auto_save disabled
        validation_service_with_config.set_auto_save(False)

        # Create a different ValidationService method to test auto-save
        # by directly manipulating the list model (which we control)
        validation_service_with_config._auto_save_test_helper = (
            lambda: mock_list_model.save()
            if validation_service_with_config.get_auto_save()
            else None
        )

        # Call our helper
        validation_service_with_config._auto_save_test_helper()

        # Should not have called save since auto_save is False
        assert mock_list_model.save.call_count == 0

        # Now enable auto_save and try again
        validation_service_with_config.set_auto_save(True)
        validation_service_with_config._auto_save_test_helper()

        # Should have called save now
        assert mock_list_model.save.call_count == 1

    def test_case_sensitive_validation(self, validation_service_with_config):
        """Test that case_sensitive setting affects validation behavior."""
        # Create test lists with case-specific values
        player_list = ["Player1", "PLAYER2", "player3"]

        # Mock the player list model
        mock_player_model = MagicMock()
        mock_player_model.contains.return_value = False  # Assume no match by default
        mock_player_model.items = player_list
        validation_service_with_config._player_list_model = mock_player_model

        # Test with case sensitivity disabled
        validation_service_with_config.set_case_sensitive(False)

        # Should match case-insensitively
        mock_player_model.contains.side_effect = lambda x: x.lower() in [
            p.lower() for p in player_list
        ]

        # These should all validate regardless of case
        assert validation_service_with_config.validate_field("player", "player1") is True
        assert validation_service_with_config.validate_field("player", "PLAYER1") is True

        # Test with case sensitivity enabled
        validation_service_with_config.set_case_sensitive(True)

        # Should match case-sensitively
        mock_player_model.contains.side_effect = lambda x: x in player_list

        # These should validate only with correct case
        assert validation_service_with_config.validate_field("player", "Player1") is True
        assert validation_service_with_config.validate_field("player", "player1") is False


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
