"""
Tests for the MainWindow class of the ChestBuddy application.

This module contains tests for the MainWindow class, which is the main window of the
ChestBuddy application. It includes tests for initialization, menu actions, toolbar actions,
tab switching, signal emission, and state persistence.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import shutil

import pandas as pd
import pytest
from PySide6.QtCore import QSize, Qt, QByteArray, Signal, QFile, QTimer
from PySide6.QtGui import QAction, QSurfaceFormat, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QTabWidget,
    QMessageBox,
    QDialog,
    QTextEdit,
    QWidget,
)
from pytestqt.qtbot import QtBot

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.views.validation_tab_view import ValidationTabView
from chestbuddy.ui.correction_tab import CorrectionTab
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.controllers.file_operations_controller import FileOperationsController
from chestbuddy.core.controllers.progress_controller import ProgressController
from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.ui_state_controller import UIStateController


class SignalCatcher:
    """Helper class to catch Qt signals."""

    def __init__(self):
        """Initialize the signal catcher."""
        self.signal_received = False
        self.signal_args = None

    def handler(self, *args):
        """Handle a signal emission."""
        self.signal_received = True
        self.signal_args = args


@pytest.fixture
def app():
    """Create a QApplication instance."""
    # Check if there's already a QApplication instance
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    # Create sample data
    data = pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Player Name": ["Player1", "Player2", "Player3"],
            "Source/Location": ["Location1", "Location2", "Location3"],
            "Chest Type": ["Wood", "Silver", "Gold"],
            "Value": [100, 250, 500],
            "Clan": ["Clan1", "Clan2", "Clan3"],
        }
    )
    return data


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_csv_path(temp_dir):
    """Create a path for a test CSV file."""
    return temp_dir / "test_data.csv"


@pytest.fixture
def data_model(app, sample_data):
    """Create a data model with sample data."""
    model = ChestDataModel()
    model.update_data(sample_data)
    return model


@pytest.fixture
def validation_service(data_model):
    """Create a validation service."""
    return ValidationService(data_model)


@pytest.fixture
def rule_manager():
    """Create a correction rule manager."""
    return CorrectionRuleManager()


@pytest.fixture
def correction_service(rule_manager, data_model, validation_service):
    """Create a correction service."""
    return CorrectionService(rule_manager, data_model, validation_service)


@pytest.fixture
def config_mock():
    """Create a mock ConfigManager."""
    config = MagicMock()

    # Mock methods to return reasonable defaults
    config.get.return_value = ""
    config.get_path.return_value = Path.home()
    config.get_recent_files.return_value = []

    # Mock byte array for window geometry
    mock_geometry = QByteArray()
    config.set = MagicMock()
    config.save = MagicMock()

    return config


@pytest.fixture
def csv_service():
    """Create a mock CSV service."""
    return MagicMock(spec=CSVService)


@pytest.fixture
def chart_service():
    """Create a mock chart service."""
    return MagicMock(spec=ChartService)


@pytest.fixture
def data_manager():
    """Create a mock data manager."""
    return MagicMock()


@pytest.fixture
def file_operations_controller():
    """Create a mock file operations controller."""
    return MagicMock(spec=FileOperationsController)


@pytest.fixture
def progress_controller():
    """Create a mock progress controller."""
    return MagicMock(spec=ProgressController)


@pytest.fixture
def view_state_controller():
    """Create a mock view state controller."""
    return MagicMock(spec=ViewStateController)


@pytest.fixture
def data_view_controller():
    """Create a mock data view controller."""
    return MagicMock(spec=DataViewController)


@pytest.fixture
def ui_state_controller():
    """Create a mock UI state controller."""
    return MagicMock(spec=UIStateController)


@pytest.fixture
def main_window(
    qtbot,
    app,
    data_model,
    csv_service,
    validation_service,
    correction_service,
    chart_service,
    data_manager,
    file_operations_controller,
    progress_controller,
    view_state_controller,
    data_view_controller,
    ui_state_controller,
    config_mock,
):
    """Create a MainWindow instance for testing."""
    with patch("chestbuddy.utils.config.ConfigManager", return_value=config_mock):
        window = MainWindow(
            data_model=data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=file_operations_controller,
            progress_controller=progress_controller,
            view_state_controller=view_state_controller,
            data_view_controller=data_view_controller,
            ui_state_controller=ui_state_controller,
            config_manager=config_mock,
        )
        qtbot.addWidget(window)
        window.show()
        yield window
        window.close()


class TestMainWindow:
    """Tests for the MainWindow class."""

    def test_initialization(self, main_window, data_model, validation_service, correction_service):
        """Test that MainWindow initializes correctly."""
        # Test window properties
        assert "ChestBuddy" in main_window.windowTitle()
        assert main_window.size().width() >= 1024
        assert main_window.size().height() >= 768

        # Test model and service references
        assert main_window._data_model == data_model
        assert main_window._validation_service == validation_service
        assert main_window._correction_service == correction_service

        # Test menu bar exists
        assert main_window.menuBar() is not None

    def test_menu_file_actions_exist(self, main_window):
        """Test that File menu actions exist."""
        file_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        assert file_menu is not None

        # Get all actions in the file menu
        actions = [action.text() for action in file_menu.actions() if action.text()]

        # Check for expected actions
        assert "&Open" in actions
        assert "&Save" in actions
        assert "Save &As..." in actions
        assert "Export &Validation Issues..." in actions
        assert "E&xit" in actions

        # Check for recent files menu
        recent_files_menu_found = False
        for action in file_menu.actions():
            if action.menu() and action.text() == "Recent Files":
                recent_files_menu_found = True
                break
        assert recent_files_menu_found

    def test_menu_tools_actions_exist(self, main_window):
        """Test that Tools menu actions exist."""
        tools_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&Tools":
                tools_menu = action.menu()
                break

        assert tools_menu is not None

        # Get all actions in the tools menu
        actions = [action.text() for action in tools_menu.actions()]

        # Check for expected actions
        assert "&Validate Data" in actions
        assert "Apply &Corrections" in actions

    def test_menu_help_actions_exist(self, main_window):
        """Test that Help menu actions exist."""
        help_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&Help":
                help_menu = action.menu()
                break

        assert help_menu is not None

        # Get all actions in the help menu
        actions = [action.text() for action in help_menu.actions()]

        # Check for expected actions
        assert "&About" in actions

    def test_menu_actions_exist(self, main_window):
        """Test that essential actions exist in menus."""
        # Test Open action
        open_action = False
        for action in main_window.findChildren(QAction):
            if action.text() == "&Open...":
                open_action = True
                break
        assert open_action

        # Test Save action
        save_action = False
        for action in main_window.findChildren(QAction):
            if action.text() == "&Save":
                save_action = True
                break
        assert save_action

        # Test Validate action
        validate_action = False
        for action in main_window.findChildren(QAction):
            if action.text() == "&Validate":
                validate_action = True
                break
        assert validate_action

        # Test Correct action
        correct_action = False
        for action in main_window.findChildren(QAction):
            if action.text() == "&Correct":
                correct_action = True
                break
        assert correct_action

    def test_open_file_action(self, qtbot, main_window, test_csv_path, config_mock):
        """Test the open file action."""
        # Create a signal catcher for the load_csv_triggered signal
        catcher = SignalCatcher()
        main_window.load_csv_triggered.connect(catcher.handler)

        # Mock QFileDialog.getOpenFileNames to return our test file path
        with patch.object(QFileDialog, "getOpenFileNames", return_value=([str(test_csv_path)], "")):
            # Find and trigger the open action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Open":
                    action.trigger()
                    break

        # Check if the signal was emitted with the correct path list
        assert catcher.signal_received
        assert isinstance(catcher.signal_args[0], list)
        assert catcher.signal_args[0][0] == str(test_csv_path)

        # Check if config was updated
        config_mock.add_recent_file.assert_called_with(str(test_csv_path))

    def test_save_file_action(self, qtbot, main_window, test_csv_path, config_mock):
        """Test the save file action."""
        # Mock the current file setting
        config_mock.get.return_value = str(test_csv_path)

        # Create a signal catcher for the save_csv_triggered signal
        catcher = SignalCatcher()
        main_window.save_csv_triggered.connect(catcher.handler)

        # Find and trigger the save action
        for action in main_window.findChildren(QAction):
            if action.text() == "&Save":
                action.trigger()
                break

        # Check if the signal was emitted with the correct path
        assert catcher.signal_received
        assert catcher.signal_args[0] == str(test_csv_path)

    def test_save_as_file_action(self, qtbot, main_window, test_csv_path, config_mock):
        """Test the save as file action."""
        # Create a signal catcher for the save_csv_triggered signal
        catcher = SignalCatcher()
        main_window.save_csv_triggered.connect(catcher.handler)

        # Mock QFileDialog.getSaveFileName to return our test file path
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(test_csv_path), "")):
            # Find and trigger the save as action
            for action in main_window.findChildren(QAction):
                if action.text() == "Save &As...":
                    action.trigger()
                    break

        # Check if the signal was emitted with the correct path
        assert catcher.signal_received
        assert catcher.signal_args[0] == str(test_csv_path)

        # Check if config was updated
        config_mock.set.assert_called()
        config_mock.set_path.assert_called()

    @pytest.mark.skip(reason="ConfigManager attribute not found in main_window module")
    def test_export_validation_issues_action(self, qtbot, main_window, test_csv_path, config_mock):
        """Test the export validation issues action."""
        # Create a signal catcher for the export_validation_issues_triggered signal
        catcher = SignalCatcher()
        main_window.export_validation_issues_triggered.connect(catcher.handler)

        # Mock QFileDialog.getSaveFileName to return our test file path
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(test_csv_path), "")):
            # Find and trigger the export validation issues action
            for action in main_window.findChildren(QAction):
                if action.text() == "Export &Validation Issues...":
                    action.trigger()
                    break

        # Check if the signal was emitted with the correct path
        assert catcher.signal_received
        assert catcher.signal_args[0] == str(test_csv_path)

        # Check if config was updated
        config_mock.set_path.assert_called()

    def test_validate_data_action(self, qtbot, main_window):
        """Test the validate data action."""
        # Create a signal catcher for the validate_data_triggered signal
        catcher = SignalCatcher()
        main_window.validate_data_triggered.connect(catcher.handler)

        # Store the current tab
        initial_tab = main_window._tab_widget.currentWidget()

        # Find and trigger the validate data action
        for action in main_window.findChildren(QAction):
            if action.text() == "&Validate Data":
                action.trigger()
                break

        # Check if the signal was emitted
        assert catcher.signal_received

        # Check if the tab was changed to the validation tab
        assert main_window._tab_widget.currentWidget() == main_window._validation_tab

    def test_apply_corrections_action(self, qtbot, main_window):
        """Test the apply corrections action."""
        # Create a signal catcher for the apply_corrections_triggered signal
        catcher = SignalCatcher()
        main_window.apply_corrections_triggered.connect(catcher.handler)

        # Store the current tab
        initial_tab = main_window._tab_widget.currentWidget()

        # Find and trigger the apply corrections action
        for action in main_window.findChildren(QAction):
            if action.text() == "Apply &Corrections":
                action.trigger()
                break

        # Check if the signal was emitted
        assert catcher.signal_received

        # Check if the tab was changed to the correction tab
        assert main_window._tab_widget.currentWidget() == main_window._correction_tab

    def test_about_action(self, qtbot, main_window):
        """Test the about action."""
        # Mock QMessageBox.about to avoid dialog display
        with patch.object(QMessageBox, "about") as mock_about:
            # Find and trigger the about action
            for action in main_window.findChildren(QAction):
                if action.text() == "&About":
                    action.trigger()
                    break

        # Check if QMessageBox.about was called
        mock_about.assert_called_once()

        # Check the arguments
        args = mock_about.call_args[0]
        assert args[0] == main_window
        assert args[1] == "About ChestBuddy"
        assert "ChestBuddy - Chest Tracker Correction Tool" in args[2]

    def test_tab_switching(self, qtbot, main_window):
        """Test switching between tabs."""
        # Initial tab should be Data tab
        assert main_window._tab_widget.currentIndex() == 0
        assert main_window._tab_widget.currentWidget() == main_window._data_view

        # Switch to Validation tab
        main_window._tab_widget.setCurrentIndex(1)
        assert main_window._tab_widget.currentIndex() == 1
        assert main_window._tab_widget.currentWidget() == main_window._validation_tab

        # Switch to Correction tab
        main_window._tab_widget.setCurrentIndex(2)
        assert main_window._tab_widget.currentIndex() == 2
        assert main_window._tab_widget.currentWidget() == main_window._correction_tab

        # Switch back to Data tab
        main_window._tab_widget.setCurrentIndex(0)
        assert main_window._tab_widget.currentIndex() == 0
        assert main_window._tab_widget.currentWidget() == main_window._data_view

    def test_window_title_update(self, qtbot, main_window, config_mock):
        """Test window title update when the current file changes."""
        # Initial title without a file
        assert "ChestBuddy - Chest Tracker Correction Tool" in main_window.windowTitle()

        # Set a current file and update title
        test_file = "test_data.csv"
        config_mock.get.return_value = test_file
        main_window._update_window_title()

        # Check that the title includes the file name
        assert f"ChestBuddy - {test_file}" in main_window.windowTitle()

    def test_recent_files_menu(self, qtbot, main_window, config_mock):
        """Test the recent files menu."""
        # Mock some recent files
        recent_files = [
            "/path/to/file1.csv",
            "/path/to/file2.csv",
            "/path/to/file3.csv",
        ]
        config_mock.get_recent_files.return_value = recent_files

        # Update the recent files menu
        main_window._update_recent_files_menu()

        # Check the recent files menu
        actions = main_window._recent_files_menu.actions()

        # Should have 3 files + separator + clear action = 5 actions
        assert len(actions) == 5

        # Create a signal catcher for the load_csv_triggered signal
        catcher = SignalCatcher()
        main_window.load_csv_triggered.connect(catcher.handler)

        # Trigger the first recent file action
        actions[0].trigger()

        # Check if the signal was emitted with the correct path
        assert catcher.signal_received
        assert catcher.signal_args[0] == recent_files[0]

        # Test clear recent files
        actions[-1].trigger()
        config_mock.set_list.assert_called_with("Files", "recent_files", [])

    def test_window_geometry_persistence(self, qtbot, main_window, config_mock):
        """Test window geometry persistence."""
        # Mock geometry
        mock_geometry = QByteArray(b"\x01\x02\x03\x04")
        config_mock.get.return_value = mock_geometry.hex()

        # Create a new window to test loading geometry
        with patch("chestbuddy.utils.config.ConfigManager", return_value=config_mock):
            with patch.object(QMainWindow, "restoreGeometry") as mock_restore:
                # Initialize a new window to trigger geometry loading
                window = MainWindow(MagicMock(), MagicMock(), MagicMock())

                # Check if restoreGeometry was called with the right argument
                mock_restore.assert_called_once()

        # Test saving geometry on close
        with patch.object(QMainWindow, "saveGeometry", return_value=mock_geometry):
            # Simulate window close
            main_window.closeEvent(MagicMock())

            # Check if config was updated with geometry
            config_mock.set.assert_called_with("Window", "geometry", mock_geometry.hex())
            config_mock.save.assert_called_once()

    def test_data_changed_signal(self, qtbot, main_window):
        """Test handling of data_changed signal from data model."""
        # Mock the window title update method
        with patch.object(main_window, "_update_window_title") as mock_update:
            # Emit the data_changed signal
            main_window._data_model.data_changed.emit()

            # Check if window was marked as modified
            assert main_window.isWindowModified()

            # Check if the window title was updated
            mock_update.assert_called_once()

    def test_open_multiple_files(self, qtbot, main_window, test_csv_path, config_mock, tmp_path):
        """Test opening multiple CSV files."""
        # Create a second test file
        second_file = tmp_path / "second_test.csv"
        with open(second_file, "w") as f:
            f.write("Date,Player Name,Source/Location,Chest Type,Value,Clan\n")
            f.write("2023-01-01,Player1,Location1,Common,100,Clan1\n")

        # List of test files
        test_files = [str(test_csv_path), str(second_file)]

        # Create a signal catcher for the load_csv_triggered signal
        catcher = SignalCatcher()
        main_window.load_csv_triggered.connect(catcher.handler)

        # Mock QFileDialog.getOpenFileNames to return our test files
        with patch.object(QFileDialog, "getOpenFileNames", return_value=(test_files, "")):
            # Find and trigger the open action
            for action in main_window.findChildren(QAction):
                if action.text() == "&Open":
                    action.trigger()
                    break

        # Check if the signal was emitted with the correct path list
        assert catcher.signal_received
        assert isinstance(catcher.signal_args[0], list)
        assert len(catcher.signal_args[0]) == 2
        assert catcher.signal_args[0][0] == str(test_csv_path)
        assert catcher.signal_args[0][1] == str(second_file)

        # Check if both files were added to recent files
        assert config_mock.add_recent_file.call_count == 2
        config_mock.add_recent_file.assert_any_call(str(test_csv_path))
        config_mock.add_recent_file.assert_any_call(str(second_file))
