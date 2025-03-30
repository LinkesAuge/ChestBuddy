"""
Tests for ValidationService configuration integration.

This module tests the integration between ValidationService and ConfigManager,
focusing on validation preferences, list paths, and configuration persistence.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.utils.config import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def config_manager(temp_config_dir):
    """Create a ConfigManager instance for testing."""
    # Reset the singleton instance
    ConfigManager._instance = None

    # Create and return a new instance
    config = ConfigManager(temp_config_dir)

    # Set some initial values
    config.set("Validation", "case_sensitive", "False")
    config.set("Validation", "validate_on_import", "True")

    return config


@pytest.fixture
def data_model():
    """Create a ChestDataModel instance for testing."""
    return ChestDataModel()


@pytest.fixture
def validation_service(data_model, config_manager):
    """Create a ValidationService instance for testing."""
    return ValidationService(data_model, config_manager)


def test_validation_preferences_loading(config_manager, data_model):
    """Test loading validation preferences from ConfigManager."""
    # Set some values in config
    config_manager.set("Validation", "case_sensitive", "True")
    config_manager.set("Validation", "validate_on_import", "False")

    # Create validation service with this config
    service = ValidationService(data_model, config_manager)

    # Check that preferences were loaded correctly
    assert service._case_sensitive is True
    assert service._validate_on_import is False

    # Check that get_validation_preferences returns correct values
    prefs = service.get_validation_preferences()
    assert prefs["case_sensitive"] is True
    assert prefs["validate_on_import"] is False


def test_validation_preferences_defaults(data_model):
    """Test default validation preferences when no config is provided."""
    # Create validation service without config
    service = ValidationService(data_model)

    # Check that default preferences are used
    assert service._case_sensitive is False
    assert service._validate_on_import is True

    # Check that get_validation_preferences returns correct defaults
    prefs = service.get_validation_preferences()
    assert prefs["case_sensitive"] is False
    assert prefs["validate_on_import"] is True


def test_set_case_sensitive(validation_service, config_manager):
    """Test setting case_sensitive preference."""
    # Initial state should be False (from fixture)
    assert validation_service._case_sensitive is False

    # Change the setting
    validation_service.set_case_sensitive(True)

    # Check that the setting was updated in the service
    assert validation_service._case_sensitive is True

    # Check that the setting was saved to config
    assert config_manager.get_bool("Validation", "case_sensitive") is True

    # Check that the signal was emitted with correct values
    # This would require a signal spy, but we'll skip for this example
    # and assume the signal connection is tested elsewhere


def test_set_validate_on_import(validation_service, config_manager):
    """Test setting validate_on_import preference."""
    # Initial state should be True (from fixture)
    assert validation_service._validate_on_import is True

    # Change the setting
    validation_service.set_validate_on_import(False)

    # Check that the setting was updated in the service
    assert validation_service._validate_on_import is False

    # Check that the setting was saved to config
    assert config_manager.get_bool("Validation", "validate_on_import") is False


def test_validation_list_path_resolution(validation_service, config_manager, temp_config_dir):
    """Test resolving validation list paths."""
    # Get validation list path through the service
    players_path = validation_service.get_validation_list_path("players")

    # Check that it's a valid path
    assert isinstance(players_path, Path)
    assert players_path.name == "players.txt"

    # The path should be within our temp directory
    assert Path(temp_config_dir) in players_path.parents


def test_validation_list_initialization(validation_service, temp_config_dir):
    """Test initialization of validation lists."""
    # Create validation dir in temp directory
    validation_dir = Path(temp_config_dir) / "validation"
    validation_dir.mkdir(exist_ok=True)

    # Create default lists directory (simulate package data)
    with patch.object(validation_service, "_get_default_lists_dir") as mock_default_dir:
        default_dir = Path(temp_config_dir) / "default_lists"
        default_dir.mkdir(exist_ok=True)

        # Create a default list file
        default_players = default_dir / "players.txt"
        default_players.write_text("DefaultPlayer1\nDefaultPlayer2\nDefaultPlayer3")

        # Set the mock to return our default directory
        mock_default_dir.return_value = default_dir

        # Initialize validation lists
        validation_service._initialize_validation_lists()

        # Get the player list path
        player_list_path = validation_service.get_validation_list_path("players")

        # Check that the file was created in user directory
        assert player_list_path.exists()

        # Check that it contains the default content
        with open(player_list_path, "r") as f:
            content = f.read()

        assert "DefaultPlayer1" in content
        assert "DefaultPlayer2" in content
        assert "DefaultPlayer3" in content


def test_settings_persistence(data_model, temp_config_dir):
    """Test that validation settings persist between service instances."""
    # Reset the singleton instance
    ConfigManager._instance = None

    # Create a config manager
    config = ConfigManager(temp_config_dir)

    # Create first validation service
    service1 = ValidationService(data_model, config)

    # Change settings
    service1.set_case_sensitive(True)
    service1.set_validate_on_import(False)

    # Create second validation service
    service2 = ValidationService(data_model, config)

    # Check that settings were loaded from config
    assert service2._case_sensitive is True
    assert service2._validate_on_import is False


def test_validation_preferences_signal(validation_service):
    """Test that changing validation preferences emits the correct signal."""
    # Create a mock to capture the signal
    signal_receiver = MagicMock()
    validation_service.validation_preferences_changed.connect(signal_receiver)

    # Change a preference
    validation_service.set_case_sensitive(True)

    # Check that the signal was emitted with correct values
    signal_receiver.assert_called_once()
    args = signal_receiver.call_args[0][0]  # Get the first positional argument

    assert isinstance(args, dict)
    assert "case_sensitive" in args
    assert args["case_sensitive"] is True
