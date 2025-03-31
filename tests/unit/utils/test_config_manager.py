import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from chestbuddy.utils.config import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_singleton():
    """Test that ConfigManager is a singleton."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create new instances
    config1 = ConfigManager()
    config2 = ConfigManager()

    # Check they are the same object
    assert config1 is config2


def test_auto_correction_settings(temp_config_dir):
    """Test auto-correction settings in ConfigManager."""
    # Reset the singleton instance for testing
    ConfigManager._instance = None

    # Create a new instance with the temp directory
    config = ConfigManager(temp_config_dir)

    # Test default values
    assert config.get_auto_correct_on_validation() is False
    assert config.get_auto_correct_on_import() is False

    # Test setting values
    config.set_auto_correct_on_validation(True)
    assert config.get_auto_correct_on_validation() is True

    config.set_auto_correct_on_import(True)
    assert config.get_auto_correct_on_import() is True

    # Test setting back to false
    config.set_auto_correct_on_validation(False)
    assert config.get_auto_correct_on_validation() is False

    # Verify settings were saved to file
    config.save()

    # Create a new instance to verify persistence
    ConfigManager._instance = None
    config2 = ConfigManager(temp_config_dir)
    assert config2.get_auto_correct_on_import() is True
    assert config2.get_auto_correct_on_validation() is False
