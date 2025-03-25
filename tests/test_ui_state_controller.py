"""
Tests for the UIStateController.
"""

import logging
import pytest
from PySide6.QtCore import QObject, Signal, Slot

from chestbuddy.core.controllers.ui_state_controller import UIStateController


class SignalCatcher(QObject):
    """Helper class to catch signals for testing."""

    def __init__(self):
        super().__init__()
        self.status_message = None
        self.action_states = None
        self.ui_theme = None
        self.ui_refresh_requested = False

    @Slot(str)
    def on_status_message_changed(self, message):
        self.status_message = message

    @Slot(dict)
    def on_actions_state_changed(self, states):
        self.action_states = states

    @Slot(str)
    def on_ui_theme_changed(self, theme):
        self.ui_theme = theme

    @Slot()
    def on_ui_refresh_needed(self):
        self.ui_refresh_requested = True


class TestUIStateController:
    """Tests for the UIStateController class."""

    @pytest.fixture
    def ui_controller(self):
        """Create a UIStateController instance for testing."""
        return UIStateController()

    @pytest.fixture
    def signal_catcher(self):
        """Create a SignalCatcher instance for testing."""
        return SignalCatcher()

    def test_initialization(self, ui_controller):
        """Test that UIStateController initializes with default values."""
        assert ui_controller.get_status_message() == "Ready"
        assert ui_controller.get_action_states() == {}
        assert ui_controller.get_ui_theme() == "default"

    def test_update_status_message(self, ui_controller, signal_catcher):
        """Test updating the status message emits a signal."""
        # Connect signal
        ui_controller.status_message_changed.connect(signal_catcher.on_status_message_changed)

        # Update message
        ui_controller.update_status_message("Test Message")

        # Check internal state
        assert ui_controller.get_status_message() == "Test Message"

        # Check signal emission
        assert signal_catcher.status_message == "Test Message"

        # Updating with same message should not emit signal
        signal_catcher.status_message = None
        ui_controller.update_status_message("Test Message")
        assert signal_catcher.status_message is None

    def test_update_action_states(self, ui_controller, signal_catcher):
        """Test updating action states emits a signal."""
        # Connect signal
        ui_controller.actions_state_changed.connect(signal_catcher.on_actions_state_changed)

        # Update action states
        ui_controller.update_action_states(save=True, export=False)

        # Check internal state
        states = ui_controller.get_action_states()
        assert states["save"] is True
        assert states["export"] is False

        # Check signal emission
        assert signal_catcher.action_states["save"] is True
        assert signal_catcher.action_states["export"] is False

        # Updating with same states should not emit signal
        signal_catcher.action_states = None
        ui_controller.update_action_states(save=True, export=False)
        assert signal_catcher.action_states is None

        # Updating one state should emit signal with all states
        ui_controller.update_action_states(save=False)
        assert signal_catcher.action_states["save"] is False
        assert signal_catcher.action_states["export"] is False

    def test_get_action_state(self, ui_controller):
        """Test getting individual action states."""
        # Set some states
        ui_controller.update_action_states(save=True, export=False)

        # Check specific states
        assert ui_controller.get_action_state("save") is True
        assert ui_controller.get_action_state("export") is False

        # Check default for non-existent state
        assert ui_controller.get_action_state("unknown") is False
        assert ui_controller.get_action_state("unknown", default=True) is True

    def test_set_ui_theme(self, ui_controller, signal_catcher):
        """Test setting the UI theme emits a signal."""
        # Connect signal
        ui_controller.ui_theme_changed.connect(signal_catcher.on_ui_theme_changed)

        # Set theme
        ui_controller.set_ui_theme("dark")

        # Check internal state
        assert ui_controller.get_ui_theme() == "dark"

        # Check signal emission
        assert signal_catcher.ui_theme == "dark"

        # Setting same theme should not emit signal
        signal_catcher.ui_theme = None
        ui_controller.set_ui_theme("dark")
        assert signal_catcher.ui_theme is None

    def test_update_data_dependent_ui(self, ui_controller, signal_catcher):
        """Test updating data-dependent UI components."""
        # Connect signals
        ui_controller.status_message_changed.connect(signal_catcher.on_status_message_changed)
        ui_controller.actions_state_changed.connect(signal_catcher.on_actions_state_changed)

        # Update with data loaded
        ui_controller.update_data_dependent_ui(True)

        # Check status message
        assert signal_catcher.status_message == "Data loaded and ready"

        # Check action states
        assert signal_catcher.action_states["save"] is True
        assert signal_catcher.action_states["validate"] is True

        # Update with no data
        ui_controller.update_data_dependent_ui(False)

        # Check status message
        assert signal_catcher.status_message == "No data loaded"

        # Check action states
        assert signal_catcher.action_states["save"] is False
        assert signal_catcher.action_states["validate"] is False

    def test_request_ui_refresh(self, ui_controller, signal_catcher):
        """Test requesting a UI refresh emits a signal."""
        # Connect signal
        ui_controller.ui_refresh_needed.connect(signal_catcher.on_ui_refresh_needed)

        # Request refresh
        ui_controller.request_ui_refresh()

        # Check signal emission
        assert signal_catcher.ui_refresh_requested is True

    def test_handle_app_state_update(self, ui_controller, signal_catcher):
        """Test handling application state updates."""
        # Connect signals
        ui_controller.status_message_changed.connect(signal_catcher.on_status_message_changed)
        ui_controller.actions_state_changed.connect(signal_catcher.on_actions_state_changed)
        ui_controller.ui_theme_changed.connect(signal_catcher.on_ui_theme_changed)
        ui_controller.ui_refresh_needed.connect(signal_catcher.on_ui_refresh_needed)

        # Update with multiple state parameters
        ui_controller.handle_app_state_update(
            {
                "has_data": True,
                "status_message": "Custom Status",
                "action_states": {"custom_action": True},
                "ui_theme": "custom_theme",
                "refresh_ui": True,
            }
        )

        # Check status message
        assert signal_catcher.status_message == "Custom Status"

        # Check action states (should include both data-dependent and custom)
        assert signal_catcher.action_states["save"] is True  # From has_data=True
        assert signal_catcher.action_states["custom_action"] is True

        # Check theme
        assert signal_catcher.ui_theme == "custom_theme"

        # Check refresh request
        assert signal_catcher.ui_refresh_requested is True
