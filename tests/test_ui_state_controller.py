"""
Tests for the UIStateController.
"""

import logging
import pytest
import time
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

from chestbuddy.core.controllers.ui_state_controller import UIStateController


class SignalCatcher:
    """Utility class for catching signals in tests."""

    def __init__(self):
        """Initialize the signal catcher."""
        self.status_message = None
        self.action_states = None
        self.ui_theme = None
        self.ui_refresh_requested = False
        self.validation_state = None

    def on_status_message_changed(self, message):
        """Handle status message changed signal."""
        self.status_message = message

    def on_actions_state_changed(self, states):
        """Handle actions state changed signal."""
        self.action_states = states

    def on_ui_theme_changed(self, theme):
        """Handle UI theme changed signal."""
        self.ui_theme = theme

    def on_ui_refresh_needed(self):
        """Handle UI refresh needed signal."""
        self.ui_refresh_requested = True

    def on_validation_state_changed(self, state):
        """Handle validation state changed signal."""
        self.validation_state = state

    def reset(self):
        """Reset all tracked signal values."""
        self.status_message = None
        self.action_states = None
        self.ui_theme = None
        self.ui_refresh_requested = False
        self.validation_state = None


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

    def test_update_validation_state(self, ui_controller, signal_catcher):
        """Test updating validation state emits a signal."""
        # Connect signal
        ui_controller.validation_state_changed.connect(signal_catcher.on_validation_state_changed)

        # Update validation state
        ui_controller.update_validation_state(has_issues=True, issue_count=5)

        # Check internal state
        validation_state = ui_controller.get_validation_state()
        assert validation_state["has_issues"] is True
        assert validation_state["issue_count"] == 5
        assert validation_state["last_validation_time"] is not None

        # Check signal emission
        assert signal_catcher.validation_state["has_issues"] is True
        assert signal_catcher.validation_state["issue_count"] == 5

        # Check status message update
        assert signal_catcher.status_message == "Validation complete: 5 issues found"

        # Reset validation state
        signal_catcher.reset()
        ui_controller.update_validation_state(reset=True)

        # Check internal state
        validation_state = ui_controller.get_validation_state()
        assert validation_state["has_issues"] is False
        assert validation_state["issue_count"] == 0
        assert validation_state["last_validation_time"] is None

        # Check signal emission
        assert signal_catcher.validation_state["has_issues"] is False
        assert signal_catcher.validation_state["issue_count"] == 0

    def test_handle_validation_results(self, ui_controller, signal_catcher):
        """Test handling validation results."""
        # Connect signals
        ui_controller.validation_state_changed.connect(signal_catcher.on_validation_state_changed)
        ui_controller.actions_state_changed.connect(signal_catcher.on_actions_state_changed)
        ui_controller.status_message_changed.connect(signal_catcher.on_status_message_changed)

        # Create mock validation results
        validation_results = {
            "player_name": ["Player1 is invalid", "Player2 is invalid"],
            "chest_type": ["Chest1 is invalid"],
            "source": [],
        }

        # Handle validation results
        ui_controller.handle_validation_results(validation_results)

        # Check validation state
        assert signal_catcher.validation_state["has_issues"] is True
        assert signal_catcher.validation_state["issue_count"] == 3
        assert signal_catcher.validation_state["categories"]["player_name"] == 2
        assert signal_catcher.validation_state["categories"]["chest_type"] == 1
        assert "source" not in signal_catcher.validation_state["categories"]

        # Check action states
        assert signal_catcher.action_states["add_to_validation"] is True
        assert signal_catcher.action_states["clear_validation"] is True

        # Check status message
        assert signal_catcher.status_message == "Validation complete: 3 issues found"

        # Test with no issues
        signal_catcher.reset()
        validation_results = {"player_name": [], "chest_type": [], "source": []}

        ui_controller.handle_validation_results(validation_results)

        # Check validation state
        assert signal_catcher.validation_state["has_issues"] is False
        assert signal_catcher.validation_state["issue_count"] == 0
        assert signal_catcher.validation_state["categories"] == {}

        # Check status message
        assert signal_catcher.status_message == "Validation complete: No issues found"

    def test_data_dependent_ui_resets_validation(self, ui_controller, signal_catcher):
        """Test that setting data_dependent_ui to False resets validation state."""
        # Connect signals
        ui_controller.validation_state_changed.connect(signal_catcher.on_validation_state_changed)

        # Set some validation state
        ui_controller.update_validation_state(has_issues=True, issue_count=5)

        # Reset signal catcher
        signal_catcher.reset()

        # Update data dependent UI to no data
        ui_controller.update_data_dependent_ui(False)

        # Check validation state was reset
        assert signal_catcher.validation_state["has_issues"] is False
        assert signal_catcher.validation_state["issue_count"] == 0
        assert signal_catcher.validation_state["last_validation_time"] is None

        # Check validation-related action states are properly set
        assert signal_catcher.action_states["validate"] is False
        assert signal_catcher.action_states["add_to_validation"] is False
        assert signal_catcher.action_states["clear_validation"] is False
        assert signal_catcher.action_states["refresh_validation"] is False
