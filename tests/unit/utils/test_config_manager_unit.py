"""
Unit tests for the ConfigManager class focusing on recent enhancements.

This module tests the ConfigManager functionality at the unit level, with a focus on:
- Boolean value handling
- Error recovery
- Migration functionality
- Performance with large configurations
"""

import os
import tempfile
import json
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from chestbuddy.utils.config import ConfigManager

# Set up the logger for this test module
logger = logging.getLogger(__name__)


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


class TestBooleanValueHandling:
    """Test suite for boolean value handling in ConfigManager."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("True", True),
            ("true", True),
            ("TRUE", True),
            ("1", True),
            ("Yes", True),
            ("yes", True),
            ("Y", True),
            ("False", False),
            ("false", False),
            ("FALSE", False),
            ("0", False),
            ("No", False),
            ("no", False),
            ("N", False),
            ("invalid", False),  # Default to False for invalid values
        ],
    )
    def test_get_bool_values(self, clean_config_manager, value, expected):
        """Test the get_bool method with various string representations of boolean values."""
        # Set the value
        clean_config_manager.set("Test", "bool_option", value)

        # Check that it's correctly converted to bool
        result = clean_config_manager.get_bool("Test", "bool_option")
        assert result is expected

    def test_set_bool_direct(self, clean_config_manager):
        """Test setting boolean values directly."""
        # Set using boolean values
        clean_config_manager.set("Test", "bool_true", True)
        clean_config_manager.set("Test", "bool_false", False)

        # Check the stored string representation
        assert clean_config_manager.get("Test", "bool_true") == "True"
        assert clean_config_manager.get("Test", "bool_false") == "False"

        # Check the retrieved boolean values
        assert clean_config_manager.get_bool("Test", "bool_true") is True
        assert clean_config_manager.get_bool("Test", "bool_false") is False

    def test_bool_roundtrip(self, clean_config_manager):
        """Test setting and getting boolean values repeatedly."""
        # Set initial value
        clean_config_manager.set("Test", "bool_option", True)

        # Multiple get/set cycles should maintain the value
        for _ in range(5):
            value = clean_config_manager.get_bool("Test", "bool_option")
            clean_config_manager.set("Test", "bool_option", value)

        # Final value should still be True
        assert clean_config_manager.get_bool("Test", "bool_option") is True


class TestErrorHandling:
    """Test suite for error handling in ConfigManager."""

    def test_missing_config_file(self, temp_config_dir):
        """Test handling of missing config file."""
        # Ensure no config exists
        config_file = Path(temp_config_dir) / "config.ini"
        if config_file.exists():
            os.remove(config_file)

        # Reset singleton
        ConfigManager._instance = None

        # Creating a new instance should create default config
        config = ConfigManager(temp_config_dir)

        # Check that the file was created
        assert config_file.exists()

        # And contains default values
        assert config.get("General", "theme") == "Light"

    def test_corrupted_config_file(self, temp_config_dir):
        """Test handling of corrupted config file."""
        # Create a corrupted config file
        config_file = Path(temp_config_dir) / "config.ini"
        with open(config_file, "w") as f:
            f.write("[Invalid Section\nThis is not valid INI syntax")

        # Reset singleton
        ConfigManager._instance = None

        # Creating a new instance should handle the corrupted file
        with patch("logging.Logger.error") as mock_error:
            config = ConfigManager(temp_config_dir)

            # Should log an error
            assert mock_error.called

            # But still create a valid instance with defaults
            assert config.get("General", "theme") == "Light"

    def test_invalid_section(self, clean_config_manager):
        """Test getting values from non-existent sections."""
        # Get from non-existent section
        value = clean_config_manager.get("NonExistentSection", "option", "default")

        # Should return the fallback value
        assert value == "default"

        # Same for get_bool
        bool_value = clean_config_manager.get_bool("NonExistentSection", "option", True)
        assert bool_value is True

    def test_permission_error_on_save(self, temp_config_dir):
        """Test handling of permission errors when saving."""
        # Create a config manager
        ConfigManager._instance = None
        config = ConfigManager(temp_config_dir)

        # Set a value
        config.set("Test", "option", "value")

        # Make the config file read-only
        config_file = Path(temp_config_dir) / "config.ini"
        os.chmod(config_file, 0o444)  # Read-only for all users

        # Attempt to save should handle the error
        with patch("logging.Logger.error") as mock_error:
            try:
                # This might fail due to permissions
                config.save()
            except Exception:
                # We expect an exception, but it should be logged
                assert mock_error.called

        # Make the file writable again for cleanup
        os.chmod(config_file, 0o666)


class TestMigration:
    """Test suite for configuration migration functionality."""

    def test_auto_validate_migration(self, temp_config_dir):
        """Test migration from auto_validate to validate_on_import."""
        # Create a config file with the old setting
        config_file = Path(temp_config_dir) / "config.ini"
        with open(config_file, "w") as f:
            f.write("[Validation]\nauto_validate = False\n")

        # Reset singleton
        ConfigManager._instance = None

        # Create a new instance that should perform migration
        config = ConfigManager(temp_config_dir)

        # Check that the new setting exists and has the correct value
        assert config.has_option("Validation", "validate_on_import")
        assert config.get_bool("Validation", "validate_on_import") is False

    def test_version_upgrade(self, temp_config_dir):
        """Test handling of configuration version upgrades."""
        # Create an old version config
        config_file = Path(temp_config_dir) / "config.ini"
        with open(config_file, "w") as f:
            f.write("[General]\nversion = 1.0\n")

        # Reset singleton
        ConfigManager._instance = None

        # Create a new instance that should handle the version difference
        config = ConfigManager(temp_config_dir)

        # Should have updated the version
        assert config.get("General", "version") != "1.0"


class TestPerformance:
    """Test suite for ConfigManager performance."""

    def test_large_config_performance(self, temp_config_dir):
        """Test performance with a large number of config entries."""
        # Reset singleton
        ConfigManager._instance = None

        # Create a new instance
        config = ConfigManager(temp_config_dir)

        # Create a large number of settings
        start_time = time.time()

        for i in range(100):
            section = f"Section{i}"
            for j in range(100):
                config.set(section, f"option{j}", f"value{j}")

        # Measure time to save
        save_start = time.time()
        config.save()
        save_time = time.time() - save_start

        # Reload the config
        load_start = time.time()
        config.load()
        load_time = time.time() - load_start

        # Count our test sections and options
        section_count = 0
        option_count = 0
        test_sections_found = 0

        for section in config._config.sections():
            section_count += 1
            # Check if this is one of our test sections
            if section.startswith("Section"):
                test_sections_found += 1
                for option in config._config.options(section):
                    option_count += 1

        # We should have at least 100 test sections (plus default sections)
        # and approximately 10,000 options (100 sections x 100 options)
        assert test_sections_found == 100
        assert option_count >= 10000
        assert section_count >= 100  # Total sections including defaults

        # Log performance metrics
        logger.info(f"Config save time: {save_time:.4f}s")
        logger.info(f"Config load time: {load_time:.4f}s")
        logger.info(f"Total time: {time.time() - start_time:.4f}s")
        logger.info(f"Sections: {section_count}, Options: {option_count}")

        # Performance should be reasonable - these are somewhat arbitrary limits
        # that may need adjusting based on the test environment
        assert save_time < 10.0  # Saving should take less than 10 seconds
        assert load_time < 10.0  # Loading should take less than 10 seconds

    def test_export_import_performance(self, clean_config_manager):
        """Test performance of export/import with a large configuration."""
        # Create a temporary export file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            export_path = temp_file.name

        # Create a large number of settings
        for i in range(50):
            section = f"Section{i}"
            for j in range(50):
                clean_config_manager.set(section, f"option{j}", f"value{j}")

        # Time the export
        export_start = time.time()
        clean_config_manager.export_config(export_path)
        export_time = time.time() - export_start

        # Modify some values
        for i in range(10):
            section = f"Section{i}"
            for j in range(10):
                clean_config_manager.set(section, f"option{j}", f"new_value{j}")

        # Time the import
        import_start = time.time()
        clean_config_manager.import_config(export_path)
        import_time = time.time() - import_start

        # Cleanup
        os.remove(export_path)

        # Performance assertions
        assert export_time < 1.0, f"Export took too long: {export_time:.2f}s"
        assert import_time < 1.0, f"Import took too long: {import_time:.2f}s"

        # Verify the import restored values
        assert clean_config_manager.get("Section0", "option0") == "value0"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
