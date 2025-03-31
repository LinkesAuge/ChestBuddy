"""
tests/ui/test_main_window_menu_interactions.py

Tests for menu interactions in MainWindow using the new view-based architecture.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from PySide6.QtWidgets import QAction, QApplication, QFileDialog, QMessageBox, QMenu
from PySide6.QtCore import Qt, QPoint

from chestbuddy.ui.main_window import MainWindow
from chestbuddy.controllers.file_operations_controller import FileOperationsController
from chestbuddy.controllers.view_state_controller import ViewStateController
from chestbuddy.controllers.ui_state_controller import UIStateController
from chestbuddy.controllers.data_view_controller import DataViewController
from chestbuddy.controllers.progress_controller import ProgressController


# Helper class for catching signals
class SignalCatcher:
    def __init__(self):
        self.signal_received = False
        self.signal_args = None

    def handler(self, *args):
        self.signal_received = True
        self.signal_args = args


# Controller fixtures
@pytest.fixture
def file_operations_controller():
    """Create a mock file operations controller."""
    controller = MagicMock(spec=FileOperationsController)
    return controller


@pytest.fixture
def view_state_controller():
    """Create a mock view state controller."""
    controller = MagicMock(spec=ViewStateController)
    return controller


@pytest.fixture
def ui_state_controller():
    """Create a mock UI state controller."""
    controller = MagicMock(spec=UIStateController)
    return controller


@pytest.fixture
def progress_controller():
    """Create a mock progress controller."""
    controller = MagicMock(spec=ProgressController)
    return controller


@pytest.fixture
def data_view_controller():
    """Create a mock data view controller."""
    controller = MagicMock(spec=DataViewController)
    return controller


@pytest.fixture
def main_window(
    qtbot,
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
    """Create a MainWindow instance for testing with mocked controllers."""
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
        # Allow time for the window to fully initialize
        qtbot.wait(50)
        yield window
        # Proper cleanup to avoid signal disconnection warnings
        window.close()
        QApplication.processEvents()  # Process any pending events


class TestMainWindowMenuInteractions:
    """Tests for menu interactions in MainWindow."""

    def test_menu_file_actions_exist(self, main_window):
        """Test that all required File menu actions exist in the new menu structure."""
        # Find the File menu
        file_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        assert file_menu is not None, "File menu not found"

        # Get all actions in the File menu
        file_actions = [action.text() for action in file_menu.actions() if not action.isSeparator()]

        # Verify essential file actions exist
        essential_actions = ["&Open...", "&Save", "Save &As...", "&Export...", "E&xit"]
        for action_text in essential_actions:
            assert any(action_text == text for text in file_actions), (
                f"File action '{action_text}' not found"
            )

    def test_menu_view_actions_exist(self, main_window):
        """Test that all required View menu actions exist in the new menu structure."""
        # Find the View menu
        view_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        assert view_menu is not None, "View menu not found"

        # Get all actions in the View menu
        view_actions = [action.text() for action in view_menu.actions() if not action.isSeparator()]

        # Verify essential view actions exist
        essential_actions = ["&Dashboard", "&Data", "&Validation", "&Correction", "&Charts"]
        for action_text in essential_actions:
            assert any(action_text in text for text in view_actions), (
                f"View action for '{action_text}' not found"
            )

    def test_menu_tools_actions_exist(self, main_window):
        """Test that all required Tools menu actions exist in the new menu structure."""
        # Find the Tools menu
        tools_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&Tools":
                tools_menu = action.menu()
                break

        assert tools_menu is not None, "Tools menu not found"

        # Get all actions in the Tools menu
        tools_actions = [
            action.text() for action in tools_menu.actions() if not action.isSeparator()
        ]

        # Verify essential tools actions exist
        essential_actions = ["&Validate Data", "&Apply Corrections", "&Settings"]
        for action_text in essential_actions:
            assert any(action_text in text for text in tools_actions), (
                f"Tools action '{action_text}' not found"
            )

    def test_menu_help_actions_exist(self, main_window):
        """Test that all required Help menu actions exist in the new menu structure."""
        # Find the Help menu
        help_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&Help":
                help_menu = action.menu()
                break

        assert help_menu is not None, "Help menu not found"

        # Get all actions in the Help menu
        help_actions = [action.text() for action in help_menu.actions() if not action.isSeparator()]

        # Verify essential help actions exist
        essential_actions = ["&About"]
        for action_text in essential_actions:
            assert any(action_text in text for text in help_actions), (
                f"Help action '{action_text}' not found"
            )

    def test_view_menu_actions(self, qtbot, main_window, view_state_controller):
        """Test that view menu actions trigger view changes."""
        # Reset mock to ensure clean state
        view_state_controller.set_active_view.reset_mock()

        # Find the View menu
        view_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&View":
                view_menu = action.menu()
                break

        assert view_menu is not None, "View menu not found"

        # Map of view names to expected controller arguments
        view_name_map = {
            "Dashboard": "Dashboard",
            "Data": "Data",
            "Validation": "Validation",
            "Correction": "Correction",
            "Charts": "Charts",
        }

        # Test each view action
        for action in view_menu.actions():
            if action.isSeparator():
                continue

            # Extract view name from action text
            for name in view_name_map:
                if name in action.text():
                    view_name = view_name_map[name]

                    # Reset mock before triggering action
                    view_state_controller.set_active_view.reset_mock()

                    # Trigger the action
                    action.trigger()
                    qtbot.wait(50)  # Allow time for signal propagation

                    # Verify controller was called with correct view name
                    view_state_controller.set_active_view.assert_called_with(view_name)
                    break

    def test_tools_menu_actions(self, qtbot, main_window, view_state_controller):
        """Test that tools menu actions trigger appropriate signals and view changes."""
        # Reset mock to ensure clean state
        view_state_controller.set_active_view.reset_mock()

        # Find the Tools menu
        tools_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&Tools":
                tools_menu = action.menu()
                break

        assert tools_menu is not None, "Tools menu not found"

        # Test validate data action
        validate_catcher = SignalCatcher()
        main_window.validate_data_triggered.connect(validate_catcher.handler)

        for action in tools_menu.actions():
            if "Validate Data" in action.text():
                # Reset mock before triggering action
                view_state_controller.set_active_view.reset_mock()

                # Trigger action
                action.setEnabled(True)  # Ensure the action is enabled
                action.trigger()
                qtbot.wait(50)  # Allow time for signal propagation

                # Verify signal was emitted and view changed
                assert validate_catcher.signal_received
                view_state_controller.set_active_view.assert_called_with("Validation")
                break

        # Test apply corrections action
        corrections_catcher = SignalCatcher()
        main_window.apply_corrections_triggered.connect(corrections_catcher.handler)

        for action in tools_menu.actions():
            if "Apply Corrections" in action.text():
                # Reset mock and signal catcher
                view_state_controller.set_active_view.reset_mock()
                corrections_catcher.signal_received = False

                # Trigger action
                action.setEnabled(True)  # Ensure the action is enabled
                action.trigger()
                qtbot.wait(50)  # Allow time for signal propagation

                # Verify signal was emitted and view changed
                assert corrections_catcher.signal_received
                view_state_controller.set_active_view.assert_called_with("Correction")
                break

    def test_help_menu_about_action(self, qtbot, main_window):
        """Test the About dialog is shown when the About action is triggered."""
        # Find the Help menu
        help_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&Help":
                help_menu = action.menu()
                break

        assert help_menu is not None, "Help menu not found"

        # Mock QMessageBox.about to prevent dialog from actually showing
        with patch.object(QMessageBox, "about") as mock_about:
            # Find and trigger the About action
            for action in help_menu.actions():
                if action.text() == "&About":
                    action.trigger()
                    break

            # Verify the About dialog was shown
            mock_about.assert_called_once()
            # Verify dialog title contains "ChestBuddy"
            assert "ChestBuddy" in mock_about.call_args[0][1]

    def test_file_menu_exit_action(self, qtbot, main_window):
        """Test the Exit action triggers close."""
        # Find the File menu
        file_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        assert file_menu is not None, "File menu not found"

        # Mock the close method to prevent window from actually closing
        with patch.object(main_window, "close") as mock_close:
            # Find and trigger the Exit action
            for action in file_menu.actions():
                if action.text() == "E&xit":
                    action.trigger()
                    break

            # Verify close was called
            mock_close.assert_called_once()

    def test_menu_action_keyboard_shortcuts(self, qtbot, main_window, file_operations_controller):
        """Test that menu actions respond to keyboard shortcuts."""
        # Reset mock to ensure clean state
        file_operations_controller.open_file.reset_mock()

        # Find the Open action to get its shortcut
        open_action = None
        for action in main_window.findChildren(QAction):
            if action.text() == "&Open..." or action.text() == "&Open":
                open_action = action
                break

        assert open_action is not None, "Open action not found"

        # Mock QFileDialog to prevent dialog from showing
        with patch.object(QFileDialog, "getOpenFileNames", return_value=(["test.csv"], "")):
            # Simulate keyboard shortcut (typically Ctrl+O)
            shortcut = open_action.shortcut()
            if shortcut:
                qtbot.keyClick(main_window, shortcut.toString()[-1], Qt.ControlModifier)
                qtbot.wait(50)  # Allow time for signal propagation

                # Verify controller method was called
                file_operations_controller.open_file.assert_called_once()

    def test_menu_items_enable_disable(self, qtbot, main_window):
        """Test that menu items are properly enabled/disabled based on data state."""
        # Define data-dependent actions
        data_dependent_actions = [
            "&Save",
            "Save &As...",
            "&Export...",
            "&Validate Data",
            "&Apply Corrections",
        ]

        # Define function to find an action by text
        def find_action(text):
            for action in main_window.findChildren(QAction):
                if action.text() == text:
                    return action
            return None

        # Test with no data
        with patch.object(main_window, "_update_data_loaded_state") as mock_update:
            main_window._update_data_loaded_state(False)

            # Force the method to run for real
            mock_update.side_effect = lambda state: MainWindow._update_data_loaded_state(
                main_window, state
            )
            main_window._update_data_loaded_state(False)

            # Verify actions are disabled
            for action_text in data_dependent_actions:
                action = find_action(action_text)
                if action:
                    assert not action.isEnabled(), (
                        f"Action '{action_text}' should be disabled with no data"
                    )

            # Reset side effect for next test
            mock_update.side_effect = None

        # Test with data
        with patch.object(main_window, "_update_data_loaded_state") as mock_update:
            # Force the method to run for real
            mock_update.side_effect = lambda state: MainWindow._update_data_loaded_state(
                main_window, state
            )
            main_window._update_data_loaded_state(True)

            # Verify actions are enabled
            for action_text in data_dependent_actions:
                action = find_action(action_text)
                if action:
                    assert action.isEnabled(), f"Action '{action_text}' should be enabled with data"

    def test_recent_files_menu_update(self, qtbot, main_window, config_mock):
        """Test that the recent files menu is properly updated."""
        # Mock recent files in config
        recent_files = ["/path/to/file1.csv", "/path/to/file2.csv", "/path/to/file3.csv"]
        config_mock.get_recent_files.return_value = recent_files

        # Find the File menu
        file_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break

        assert file_menu is not None, "File menu not found"

        # Find the Recent Files menu
        recent_menu = None
        for action in file_menu.actions():
            if "Recent" in action.text():
                recent_menu = action.menu()
                break

        # If the menu isn't found, it might need to be updated first
        if recent_menu is None:
            main_window._update_recent_files_menu()
            for action in file_menu.actions():
                if "Recent" in action.text():
                    recent_menu = action.menu()
                    break

        assert recent_menu is not None, "Recent Files menu not found"

        # Force recent files menu update
        main_window._update_recent_files_menu()

        # Verify recent files menu contains correct items
        recent_actions = [action for action in recent_menu.actions() if not action.isSeparator()]
        assert len(recent_actions) == len(recent_files), (
            "Recent files menu has wrong number of items"
        )

        # Verify action data matches file paths
        for i, action in enumerate(recent_actions):
            assert hasattr(action, "data") and action.data() == recent_files[i], (
                f"Recent file action data mismatch: {action.data()} != {recent_files[i]}"
            )
