"""
Tests for enhanced ConfigManager functionality.

This module tests the new features added to ConfigManager during the configuration system rework:
- Configuration reset functionality
- Configuration validation
- Validation list path handling
"""

import os
import tempfile
import json
from pathlib import Path

import pytest

from chestbuddy.utils.config import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def config_with_defaults(temp_config_dir):
    """Create a ConfigManager with some default values for testing reset functionality."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Set some values that we'll later reset
    config.set("General", "theme", "Dark")
    config.set("General", "language", "English")
    config.set("Validation", "case_sensitive", "True")
    config.set("Validation", "validate_on_import", "False")
    config.set("UI", "window_width", "1024")
    config.set("UI", "window_height", "768")

    # Save the configuration
    config.save()

    yield config


def test_reset_to_defaults_section(config_with_defaults, temp_config_dir):
    """Test resetting a specific section to defaults."""
    # First verify our test values are set
    assert config_with_defaults.get("Validation", "case_sensitive") == "True"
    assert config_with_defaults.get("Validation", "validate_on_import") == "False"

    # Reset the Validation section
    config_with_defaults.reset_to_defaults("Validation")

    # Check that Validation settings are back to defaults
    assert config_with_defaults.get("Validation", "case_sensitive") == "False"
    assert config_with_defaults.get("Validation", "validate_on_import") == "True"

    # Check that other sections remain unchanged
    assert config_with_defaults.get("General", "theme") == "Dark"
    assert config_with_defaults.get("UI", "window_width") == "1024"


def test_reset_to_defaults_all(config_with_defaults, temp_config_dir):
    """Test resetting the entire configuration to defaults."""
    # First verify our test values are set
    assert config_with_defaults.get("General", "theme") == "Dark"
    assert config_with_defaults.get("Validation", "case_sensitive") == "True"
    assert config_with_defaults.get("UI", "window_width") == "1024"

    # Reset all sections
    config_with_defaults.reset_to_defaults()

    # Check that all settings are back to defaults
    assert config_with_defaults.get("General", "theme") == "Light"
    assert config_with_defaults.get("Validation", "case_sensitive") == "False"
    assert config_with_defaults.get("Validation", "validate_on_import") == "True"
    assert config_with_defaults.get("UI", "window_width") == "1024"  # Assuming 1024 is the default


def test_reset_persistence(config_with_defaults, temp_config_dir):
    """Test that reset changes persist between instances."""
    # Reset the Validation section
    config_with_defaults.reset_to_defaults("Validation")

    # Save the configuration
    config_with_defaults.save()

    # Reset the singleton instance
    ConfigManager._instance = None

    # Create a new instance with the same temp directory
    config2 = ConfigManager(temp_config_dir)

    # Check that reset values persisted
    assert config2.get("Validation", "case_sensitive") == "False"
    assert config2.get("Validation", "validate_on_import") == "True"

    # While other sections remain unchanged
    assert config2.get("General", "theme") == "Dark"


def test_validate_config(config_with_defaults, temp_config_dir):
    """Test the config validation functionality."""
    # Configuration should be valid after normal initialization
    assert config_with_defaults.validate_config() is True

    # Create a corrupted config file
    config_file = Path(temp_config_dir) / "config.ini"
    with open(config_file, "w") as f:
        f.write("[Invalid\nThis is not a valid INI file")

    # Reset the singleton instance
    ConfigManager._instance = None

    # Create a new instance that will load the corrupted file
    corrupted_config = ConfigManager(temp_config_dir)

    # Validation should fail
    assert corrupted_config.validate_config() is False

    # Reset to defaults
    corrupted_config.reset_to_defaults()

    # Now validation should pass
    assert corrupted_config.validate_config() is True


def test_get_validation_list_path(temp_config_dir):
    """Test retrieving validation list paths."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Create test directories
    user_validation_dir = Path(temp_config_dir) / "validation_lists"
    user_validation_dir.mkdir(exist_ok=True)

    # Test getting a validation list path
    list_path = config.get_validation_list_path("players.txt")

    # The path should point to the user's validation directory
    assert user_validation_dir in list_path.parents
    assert list_path.name == "players.txt"


def test_validation_list_path_precedence(temp_config_dir):
    """Test that user validation lists take precedence over default lists."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Create user validation directory and file
    user_validation_dir = Path(temp_config_dir) / "validation_lists"
    user_validation_dir.mkdir(exist_ok=True)

    user_list_file = user_validation_dir / "players.txt"
    user_list_file.write_text("User player list")

    # Get the validation list path
    list_path = config.get_validation_list_path("players.txt")

    # Check that we get the user file
    assert list_path == user_list_file
    assert list_path.exists()
    with open(list_path, "r") as f:
        assert f.read() == "User player list"


def test_config_export_import(temp_config_dir):
    """Test exporting and importing configuration."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Set some test values
    config.set("General", "theme", "Dark")
    config.set("Validation", "case_sensitive", "True")

    # Export the configuration
    export_file = Path(temp_config_dir) / "exported_config.json"
    config.export_config(export_file)

    # Check that the export file exists and contains the correct settings
    assert export_file.exists()
    with open(export_file, "r") as f:
        exported_data = json.load(f)

    assert "General" in exported_data
    assert exported_data["General"]["theme"] == "Dark"
    assert "Validation" in exported_data
    assert exported_data["Validation"]["case_sensitive"] == "True"

    # Change some settings
    config.set("General", "theme", "Light")
    config.set("Validation", "case_sensitive", "False")

    # Import the configuration back
    config.import_config(export_file)

    # Check that the settings were restored
    assert config.get("General", "theme") == "Dark"
    assert config.get("Validation", "case_sensitive") == "True"
