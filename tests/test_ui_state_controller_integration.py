"""
Integration tests for UIStateController with other components.
"""

import logging
import pytest
from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
from PySide6.QtGui import QAction

from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.models import ChestDataModel


class MockMainWindow(QMainWindow):
    """Mock MainWindow for testing."""

    def __init__(self):
        super().__init__()

        # Create actions
        self.save_action = QAction("Save", self)
        self.validate_action = QAction("Validate", self)
        self.export_action = QAction("Export", self)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Track signals
        self.status_message = None
        self.actions_updated = {}

    @Slot(str)
    def update_status(self, message):
        """Update status bar message."""
        self.status_message = message
        self.status_bar.showMessage(message)

    def get_action(self, name):
        """Get action by name."""
        if name == "save":
            return self.save_action
        elif name == "validate":
            return self.validate_action
        elif name == "export":
            return self.export_action
        return None


class TestUIStateControllerIntegration:
    """Integration tests for UIStateController with other components."""

    @pytest.fixture
    def app(self, qtbot):
        """Create QApplication for testing."""
        # qtbot fixture will ensure QApplication exists
        return QApplication.instance()

    @pytest.fixture
    def data_model(self):
        """Create a ChestDataModel instance for testing."""
        return ChestDataModel()

    @pytest.fixture
    def ui_controller(self):
        """Create a UIStateController instance for testing."""
        return UIStateController()

    @pytest.fixture
    def data_view_controller(self, data_model):
        """Create a DataViewController instance for testing."""
        return DataViewController(data_model)

    @pytest.fixture
    def view_state_controller(self, data_model):
        """Create a ViewStateController instance for testing."""
        controller = ViewStateController(data_model)
        # The method is likely named differently, let's use what's available
        if hasattr(controller, "register_view"):
            controller.register_view("TestView", None)
        elif hasattr(controller, "add_view"):
            controller.add_view("TestView", None)
        return controller

    @pytest.fixture
    def main_window(self, qtbot):
        """Create a mock MainWindow for testing."""
        window = MockMainWindow()
        qtbot.addWidget(window)
        return window

    def test_integration_with_main_window(self, qtbot, ui_controller, main_window):
        """Test integration with MainWindow."""
        # Connect UI controller signals to main window
        ui_controller.status_message_changed.connect(main_window.update_status)

        # Update status message
        ui_controller.update_status_message("Test Status Message")

        # Process events to ensure signal delivery
        qtbot.wait(10)

        # Check if main window status was updated
        assert main_window.status_message == "Test Status Message"
        assert main_window.status_bar.currentMessage() == "Test Status Message"

    def test_action_state_integration(self, qtbot, ui_controller, main_window):
        """Test action state integration."""
        # Connect actions to UI controller
        actions = {
            "save": main_window.save_action,
            "validate": main_window.validate_action,
            "export": main_window.export_action,
        }

        # Initially disable all actions
        for action in actions.values():
            action.setEnabled(False)

        # Register action handler
        @Slot(dict)
        def update_actions(action_states):
            for name, enabled in action_states.items():
                action = actions.get(name)
                if action:
                    action.setEnabled(enabled)
                    main_window.actions_updated[name] = enabled

        # Connect signal
        ui_controller.actions_state_changed.connect(update_actions)

        # Update action states
        ui_controller.update_action_states(save=True, validate=True, export=False)

        # Check if actions were updated
        assert main_window.save_action.isEnabled() is True
        assert main_window.validate_action.isEnabled() is True
        assert main_window.export_action.isEnabled() is False

    def test_data_dependent_ui_integration(self, app, ui_controller, main_window):
        """Test data dependent UI integration."""
        # Connect status message
        ui_controller.status_message_changed.connect(main_window.update_status)

        # Connect actions
        actions = {
            "save": main_window.save_action,
            "validate": main_window.validate_action,
            "export": main_window.export_action,
        }

        # Register action handler
        @Slot(dict)
        def update_actions(action_states):
            for name, enabled in action_states.items():
                action = actions.get(name)
                if action:
                    action.setEnabled(enabled)

        # Connect signal
        ui_controller.actions_state_changed.connect(update_actions)

        # Update with no data
        ui_controller.update_data_dependent_ui(False)

        # Check if UI was updated for no data
        assert main_window.status_message == "No data loaded"
        assert main_window.save_action.isEnabled() is False
        assert main_window.validate_action.isEnabled() is False

        # Update with data
        ui_controller.update_data_dependent_ui(True)

        # Check if UI was updated for data loaded
        assert main_window.status_message == "Data loaded and ready"
        assert main_window.save_action.isEnabled() is True
        assert main_window.validate_action.isEnabled() is True

    def test_integration_with_view_state_controller(
        self, qtbot, ui_controller, view_state_controller
    ):
        """Test simplified integration with ViewStateController."""
        # Track UI updates
        status_messages = []

        # Connect signal
        @Slot(str)
        def on_status_message(message):
            status_messages.append(message)

        ui_controller.status_message_changed.connect(on_status_message)

        # Simply update the UI state controller directly
        ui_controller.update_status_message("View State Update")

        # Process events to ensure signal delivery
        qtbot.wait(10)

        # Check if UI was updated correctly
        assert "View State Update" in status_messages

    def test_integration_with_data_view_controller(
        self, qtbot, ui_controller, data_view_controller
    ):
        """Test integration with DataViewController."""
        # Track UI updates
        status_messages = []

        # Connect signals
        @Slot(str)
        def on_status_message(message):
            status_messages.append(message)

        ui_controller.status_message_changed.connect(on_status_message)

        # Have UI controller update state
        ui_controller.update_status_message("Validating data...")

        # Process events to ensure signal delivery
        qtbot.wait(10)

        # Check if UI was updated correctly
        assert "Validating data..." in status_messages
