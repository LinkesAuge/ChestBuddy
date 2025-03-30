"""
Tests for SettingsTabView UI functionality.

This module tests the SettingsTabView UI component, focusing on initialization,
settings changes, and tab functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget

from chestbuddy.ui.views.settings_tab_view import SettingsTabView
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

    # Set some test values
    config.set("General", "theme", "Dark")
    config.set("General", "language", "English")
    config.set("Validation", "case_sensitive", "False")
    config.set("Validation", "validate_on_import", "True")
    config.set("UI", "window_width", "1024")
    config.set("UI", "window_height", "768")

    return config


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


def test_initialization(settings_view, config_manager):
    """Test that SettingsTabView initializes correctly."""
    # Check that the view was created
    assert settings_view is not None

    # Check that it has a tab widget
    assert hasattr(settings_view, "_tab_widget")

    # Check that all tabs are created
    tabs = settings_view._tab_widget
    assert tabs.count() >= 4  # Should have at least General, Validation, UI, and Backup tabs

    # Check tab titles (this might need adjustment based on actual implementation)
    tab_names = [tabs.tabText(i) for i in range(tabs.count())]
    assert "General" in tab_names
    assert "Validation" in tab_names
    assert "UI" in tab_names


def test_settings_loaded(settings_view, config_manager):
    """Test that settings are loaded correctly into UI elements."""
    # Check that settings were loaded into UI elements
    general_widgets = settings_view._settings_widgets.get("General", {})

    # Check theme dropdown
    theme_widget = general_widgets.get("theme")
    if theme_widget:
        assert theme_widget.currentText() == "Dark"

    # Check language dropdown
    language_widget = general_widgets.get("language")
    if language_widget:
        assert language_widget.currentText() == "English"

    # Check validation settings
    validation_widgets = settings_view._settings_widgets.get("Validation", {})

    # Check case_sensitive checkbox
    case_sensitive_widget = validation_widgets.get("case_sensitive")
    if case_sensitive_widget:
        assert case_sensitive_widget.isChecked() is False

    # Check validate_on_import checkbox
    validate_on_import_widget = validation_widgets.get("validate_on_import")
    if validate_on_import_widget:
        assert validate_on_import_widget.isChecked() is True


def test_setting_change_signal(settings_view, qtbot):
    """Test that changing a setting emits the correct signal."""
    # Create a signal spy
    signal_spy = QSignalSpy(settings_view.settings_changed)

    # Change a setting
    general_widgets = settings_view._settings_widgets.get("General", {})
    theme_widget = general_widgets.get("theme")

    if theme_widget:
        # Select a different theme
        index = theme_widget.findText("Light")
        if index >= 0:
            theme_widget.setCurrentIndex(index)

            # Check that the signal was emitted with correct parameters
            assert signal_spy.count() == 1
            args = signal_spy[0]
            assert args[0] == "General"
            assert args[1] == "theme"
            assert args[2] == "Light"


def test_export_import_signals(settings_view, qtbot, temp_config_dir):
    """Test that export/import buttons emit the correct signals."""
    # Create signal spies
    export_spy = QSignalSpy(settings_view.settings_exported)
    import_spy = QSignalSpy(settings_view.settings_imported)

    # Create a mock for QFileDialog
    with patch("PySide6.QtWidgets.QFileDialog") as mock_dialog:
        # Mock file selection for export
        export_path = str(Path(temp_config_dir) / "exported_config.json")
        mock_dialog.getSaveFileName.return_value = (export_path, "JSON Files (*.json)")

        # Trigger export
        settings_view._on_export_clicked()

        # Check that the signal was emitted with correct path
        assert export_spy.count() == 1
        assert export_spy[0][0] == export_path

        # Mock file selection for import
        mock_dialog.getOpenFileName.return_value = (export_path, "JSON Files (*.json)")

        # Trigger import
        settings_view._on_import_clicked()

        # Check that the signal was emitted with correct path
        assert import_spy.count() == 1
        assert import_spy[0][0] == export_path


def test_reset_signals(settings_view, qtbot):
    """Test that reset buttons emit the correct signals."""
    # Create a signal spy
    reset_spy = QSignalSpy(settings_view.settings_reset)

    # Mock confirmation dialog to return True
    with patch("PySide6.QtWidgets.QMessageBox.question") as mock_question:
        mock_question.return_value = QMessageBox.Yes

        # Trigger reset for a specific section
        settings_view._on_reset_section_clicked("Validation")

        # Check that the signal was emitted with correct section
        assert reset_spy.count() == 1
        assert reset_spy[0][0] == "Validation"

        # Trigger reset for all sections
        settings_view._on_reset_all_clicked()

        # Check that the signal was emitted with "all"
        assert reset_spy.count() == 2
        assert reset_spy[1][0] == "all"


def test_refresh(settings_view, config_manager):
    """Test that refresh reloads settings from config."""
    # Change a setting in config manager
    config_manager.set("General", "theme", "Light")

    # Initial value in UI should still be "Dark"
    general_widgets = settings_view._settings_widgets.get("General", {})
    theme_widget = general_widgets.get("theme")
    if theme_widget:
        assert theme_widget.currentText() == "Dark"

    # Refresh the settings
    settings_view.refresh()

    # Check that the UI was updated
    if theme_widget:
        assert theme_widget.currentText() == "Light"


# Utility class for signal testing
class QSignalSpy:
    """Simple utility class to capture Qt signals for testing."""

    def __init__(self, signal):
        self.signal = signal
        self.args = []
        self.signal.connect(self._slot)

    def _slot(self, *args):
        self.args.append(args)

    def __getitem__(self, index):
        return self.args[index]

    def count(self):
        return len(self.args)
