"""
Tests for the ConfigManager class.
"""

import os
import tempfile
from pathlib import Path

import pytest

from chestbuddy.utils.config import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_singleton_pattern():
    """Test that ConfigManager follows the singleton pattern."""
    # Create two instances
    config1 = ConfigManager()
    config2 = ConfigManager()

    # Check that they are the same instance
    assert config1 is config2


def test_get_set_values(temp_config_dir):
    """Test getting and setting configuration values."""
    # Reset the singleton instance for testing with a clean config
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Test setting and getting a string value
    config.set("Test", "string_value", "test_string")
    assert config.get("Test", "string_value") == "test_string"

    # Test setting and getting a boolean value
    config.set("Test", "bool_value", True)
    assert config.get_bool("Test", "bool_value") is True

    # Test setting and getting an integer value
    config.set("Test", "int_value", 42)
    assert config.get_int("Test", "int_value") == 42

    # Test setting and getting a float value
    config.set("Test", "float_value", 3.14)
    assert config.get_float("Test", "float_value") == 3.14

    # Test setting and getting a list value
    test_list = ["item1", "item2", "item3"]
    config.set_list("Test", "list_value", test_list)
    assert config.get_list("Test", "list_value") == test_list


def test_fallback_values():
    """Test fallback values for get methods."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance
    config = ConfigManager()

    # Test fallback for string
    assert config.get("NonExistent", "option", "fallback") == "fallback"

    # Test fallback for boolean
    assert config.get_bool("NonExistent", "option", True) is True

    # Test fallback for integer
    assert config.get_int("NonExistent", "option", 42) == 42

    # Test fallback for float
    assert config.get_float("NonExistent", "option", 3.14) == 3.14

    # Test fallback for list
    fallback_list = ["default1", "default2"]
    assert config.get_list("NonExistent", "option", fallback_list) == fallback_list


def test_get_set_path(temp_config_dir):
    """Test getting and setting path values."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Test setting and getting a path
    test_path = Path(temp_config_dir) / "test_folder" / "test_file.txt"
    config.set_path("Test", "path_value", test_path)

    # Get and compare paths
    retrieved_path = config.get_path("Test", "path_value")
    assert retrieved_path == test_path

    # Test creating directory with create_if_missing
    test_dir = Path(temp_config_dir) / "created_dir"
    config.set_path("Test", "dir_path", test_dir, create_if_missing=True)
    assert test_dir.exists()
    assert test_dir.is_dir()


def test_recent_files():
    """Test adding and retrieving recent files."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance
    config = ConfigManager()

    # Use platform-agnostic paths for testing
    file1 = str(Path("/path/to/file1.csv"))
    file2 = str(Path("/path/to/file2.csv"))
    file3 = str(Path("/path/to/file3.csv"))

    # Add some recent files
    config.add_recent_file(file1)
    config.add_recent_file(file2)
    config.add_recent_file(file3)

    # Get recent files (will return empty list because files don't exist)
    recent_files = config.get_recent_files()
    assert isinstance(recent_files, list)

    # Add the same file again (should move to the top)
    config.add_recent_file(file2)

    # Check the raw list ordering in config
    raw_list = config.get_list("Files", "recent_files")

    # Convert paths for comparison to ensure platform-independence
    normalized_file1 = str(Path(file1))
    normalized_file2 = str(Path(file2))
    normalized_file3 = str(Path(file3))

    assert raw_list[0] == normalized_file2
    assert normalized_file1 in raw_list
    assert normalized_file3 in raw_list


def test_persistence(temp_config_dir):
    """Test that configuration persists between instances."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config1 = ConfigManager(temp_config_dir)

    # Set some values
    config1.set("Test", "persist_string", "test_string")
    config1.set("Test", "persist_int", 42)

    # Save the configuration
    config1.save()

    # Reset the singleton instance
    ConfigManager._instance = None

    # Create a new instance with the same temp directory
    config2 = ConfigManager(temp_config_dir)

    # Check that values persist
    assert config2.get("Test", "persist_string") == "test_string"
    assert config2.get_int("Test", "persist_int") == 42
