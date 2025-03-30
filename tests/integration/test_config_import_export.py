"""
Integration tests for configuration import/export functionality.

This module tests the end-to-end workflow for configuration import/export,
ensuring that settings are properly saved, loaded, and applied across components.
"""

import os
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox

from chestbuddy.utils.config import ConfigManager
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.ui.views.settings_tab_view import SettingsTabView
from chestbuddy.ui.views.settings_view_adapter import SettingsViewAdapter


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

    # Set some test values
    config.set("General", "theme", "Dark")
    config.set("General", "language", "English")
    config.set("Validation", "case_sensitive", "False")
    config.set("Validation", "validate_on_import", "True")
    config.set("UI", "window_width", "1024")
    config.set("UI", "window_height", "768")

    return config


@pytest.fixture
def data_model():
    """Create a ChestDataModel instance for testing."""
    return ChestDataModel()


@pytest.fixture
def validation_service(data_model, config_manager):
    """Create a ValidationService instance for testing."""
    return ValidationService(data_model, config_manager)


@pytest.fixture
def qtbot(qapp):
    """Provide qtbot fixture with QApplication."""
    from pytestqt.qtbot import QtBot

    return QtBot(qapp)


@pytest.fixture
def settings_view(config_manager, qtbot):
    """Create a SettingsTabView instance for testing."""
    view = SettingsTabView(config_manager)
    qtbot.addWidget(view)
    return view


@pytest.fixture
def settings_adapter(config_manager, qtbot):
    """Create a SettingsViewAdapter instance for testing."""
    adapter = SettingsViewAdapter(config_manager)
    qtbot.addWidget(adapter)
    return adapter


def test_export_import_workflow(config_manager, settings_adapter, temp_config_dir, qtbot):
    """Test the complete export-modify-import workflow."""
    # Create an export file path
    export_file = Path(temp_config_dir) / "exported_config.json"

    # Mock file dialog to return our path
    with patch("PySide6.QtWidgets.QFileDialog") as mock_dialog:
        # Mock export dialog
        mock_dialog.getSaveFileName.return_value = (str(export_file), "JSON Files (*.json)")

        # Get the settings tab view from the adapter
        settings_tab = settings_adapter._settings_tab

        # Export the configuration
        settings_tab._on_export_clicked()

        # Verify that the file was created
        assert export_file.exists()

        # Check file contents
        with open(export_file, "r") as f:
            exported_data = json.load(f)

        assert "General" in exported_data
        assert exported_data["General"]["theme"] == "Dark"
        assert "Validation" in exported_data
        assert exported_data["Validation"]["validate_on_import"] == "True"

        # Modify the configuration
        config_manager.set("General", "theme", "Light")
        config_manager.set("Validation", "validate_on_import", "False")
        config_manager.save()

        # Check that settings were updated
        assert config_manager.get("General", "theme") == "Light"
        assert config_manager.get("Validation", "validate_on_import") == "False"

        # Refresh the settings view to ensure UI is updated
        settings_tab.refresh()

        # Verify that UI shows the new values
        general_widgets = settings_tab._settings_widgets.get("General", {})
        theme_widget = general_widgets.get("theme")
        if theme_widget:
            assert theme_widget.currentText() == "Light"

        validation_widgets = settings_tab._settings_widgets.get("Validation", {})
        validate_on_import_widget = validation_widgets.get("validate_on_import")
        if validate_on_import_widget:
            assert validate_on_import_widget.isChecked() is False

        # Mock import dialog
        mock_dialog.getOpenFileName.return_value = (str(export_file), "JSON Files (*.json)")

        # Import the configuration
        settings_tab._on_import_clicked()

        # Check that settings were restored from the exported file
        assert config_manager.get("General", "theme") == "Dark"
        assert config_manager.get("Validation", "validate_on_import") == "True"

        # Refresh the settings view
        settings_tab.refresh()

        # Verify that UI shows the restored values
        if theme_widget:
            assert theme_widget.currentText() == "Dark"

        if validate_on_import_widget:
            assert validate_on_import_widget.isChecked() is True


def test_reset_integration(config_manager, settings_adapter, validation_service, qtbot):
    """Test the integration of reset functionality across components."""
    # Set up initial values in config
    config_manager.set("General", "theme", "Dark")
    config_manager.set("Validation", "case_sensitive", "True")
    config_manager.set("Validation", "validate_on_import", "False")
    config_manager.save()

    # Create a new ValidationService to load these settings
    validation_service = ValidationService(ChestDataModel(), config_manager)

    # Verify initial settings in ValidationService
    assert validation_service._case_sensitive is True
    assert validation_service._validate_on_import is False

    # Mock message box to confirm reset
    with patch("PySide6.QtWidgets.QMessageBox.question") as mock_question:
        mock_question.return_value = QMessageBox.Yes

        # Get the settings tab view from the adapter
        settings_tab = settings_adapter._settings_tab

        # Reset just the Validation section
        settings_tab._on_reset_section_clicked("Validation")

        # Check that Validation settings were reset in config
        assert config_manager.get("Validation", "case_sensitive") == "False"
        assert config_manager.get("Validation", "validate_on_import") == "True"

        # Check that General settings were NOT reset
        assert config_manager.get("General", "theme") == "Dark"

        # Create a new ValidationService to load the reset settings
        validation_service = ValidationService(ChestDataModel(), config_manager)

        # Verify that ValidationService loaded the reset settings
        assert validation_service._case_sensitive is False
        assert validation_service._validate_on_import is True

        # Reset all settings
        settings_tab._on_reset_all_clicked()

        # Check that ALL settings were reset
        assert config_manager.get("General", "theme") == "Light"
        assert config_manager.get("Validation", "case_sensitive") == "False"
        assert config_manager.get("Validation", "validate_on_import") == "True"


def test_config_validation_integration(config_manager, temp_config_dir):
    """Test validation integration across components when config is corrupted."""
    # Create a corrupted config file
    config_file = Path(temp_config_dir) / "config.ini"
    with open(config_file, "w") as f:
        f.write("[Invalid\nThis is not a valid INI file")

    # Reset the singleton instance
    ConfigManager._instance = None

    # Create a new config manager that will load the corrupted file
    config = ConfigManager(temp_config_dir)

    # Check that the invalid file is detected
    assert config.validate_config() is False

    # Reset to defaults
    config.reset_to_defaults()

    # Check that the configuration is now valid
    assert config.validate_config() is True

    # Verify default values were set
    assert config.get("General", "theme") == "Light"
    assert config.get("Validation", "case_sensitive") == "False"
    assert config.get("Validation", "validate_on_import") == "True"


def test_default_list_integration(config_manager, data_model, temp_config_dir):
    """Test the integration of default validation lists."""
    # Set up default list directory
    default_dir = Path(temp_config_dir) / "default_lists"
    default_dir.mkdir(exist_ok=True)

    # Create default list files
    players_default = default_dir / "players.txt"
    players_default.write_text("DefaultPlayer1\nDefaultPlayer2\nDefaultPlayer3")

    # Create validation service and patch default lists dir
    with patch(
        "chestbuddy.core.services.validation_service.ValidationService._get_default_lists_dir"
    ) as mock_dir:
        mock_dir.return_value = default_dir

        # Create validation service
        validation_service = ValidationService(data_model, config_manager)

        # Check that player list path exists in the user's config directory
        player_list_path = validation_service.get_validation_list_path("players")
        assert player_list_path.exists()

        # Check content of the file
        with open(player_list_path, "r") as f:
            content = f.read()

        # Should contain default players
        assert "DefaultPlayer1" in content
