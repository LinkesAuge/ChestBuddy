"""
ui_state_controller.py

Description: Controller for managing UI state across the application
Usage:
    ui_controller = UIStateController()
    ui_controller.update_status_bar("Ready")
    ui_controller.update_action_states(has_data=True)
"""

import logging
from typing import Dict, Optional, List, Any

from PySide6.QtCore import QObject, Signal, Slot

# Set up logger
logger = logging.getLogger(__name__)


class UIStateController(QObject):
    """
    Controller for managing UI state across the application.

    This controller centralizes UI-specific state management that doesn't fit
    into other controllers like data, file operations, or view state.

    Signals:
        status_message_changed(str): Signal emitted when the status message changes
        actions_state_changed(dict): Signal emitted when the state of actions changes
        ui_theme_changed(str): Signal emitted when the UI theme changes
        ui_refresh_needed(): Signal emitted when the UI needs a complete refresh

    Attributes:
        _status_message (str): Current status message
        _action_states (dict): Dictionary of action states (enabled/disabled)
        _ui_theme (str): Current UI theme
    """

    # Signals
    status_message_changed = Signal(str)
    actions_state_changed = Signal(dict)
    ui_theme_changed = Signal(str)
    ui_refresh_needed = Signal()

    def __init__(self):
        """Initialize the UIStateController."""
        super().__init__()

        # Initialize state
        self._status_message = "Ready"
        self._action_states = {}
        self._ui_theme = "default"

        logger.info("UIStateController initialized")

    def update_status_message(self, message: str) -> None:
        """
        Update the status bar message.

        Args:
            message: The message to display in the status bar
        """
        if message != self._status_message:
            self._status_message = message
            self.status_message_changed.emit(message)
            logger.debug(f"Status message updated: {message}")

    def get_status_message(self) -> str:
        """
        Get the current status message.

        Returns:
            The current status message
        """
        return self._status_message

    def update_action_states(self, **states) -> None:
        """
        Update the state of actions (enabled/disabled).

        Args:
            **states: Keyword arguments mapping action names to boolean states
                     (e.g., save=True, export=False)
        """
        changed = False

        for action_name, state in states.items():
            if action_name not in self._action_states or self._action_states[action_name] != state:
                self._action_states[action_name] = state
                changed = True

        if changed:
            self.actions_state_changed.emit(self._action_states.copy())
            logger.debug(f"Action states updated: {states}")

    def get_action_states(self) -> Dict[str, bool]:
        """
        Get the current action states.

        Returns:
            Dictionary mapping action names to boolean states
        """
        return self._action_states.copy()

    def get_action_state(self, action_name: str, default: bool = False) -> bool:
        """
        Get the state of a specific action.

        Args:
            action_name: The name of the action
            default: Default value to return if the action is not found

        Returns:
            The state of the action (True=enabled, False=disabled)
        """
        return self._action_states.get(action_name, default)

    def set_ui_theme(self, theme_name: str) -> None:
        """
        Set the UI theme.

        Args:
            theme_name: The name of the theme to set
        """
        if theme_name != self._ui_theme:
            self._ui_theme = theme_name
            self.ui_theme_changed.emit(theme_name)
            logger.info(f"UI theme changed to: {theme_name}")

    def get_ui_theme(self) -> str:
        """
        Get the current UI theme.

        Returns:
            The current UI theme name
        """
        return self._ui_theme

    def update_data_dependent_ui(self, has_data: bool) -> None:
        """
        Update UI components that depend on whether data is loaded.

        This method centralizes the logic for updating UI states that
        depend on whether data is loaded in the application.

        Args:
            has_data: Whether data is currently loaded
        """
        # Update action states based on data availability
        self.update_action_states(
            save=has_data,
            save_as=has_data,
            export=has_data,
            validate=has_data,
            correct=has_data,
            chart=has_data,
            filter=has_data,
            sort=has_data,
        )

        # Update status message based on data state
        if has_data:
            self.update_status_message("Data loaded and ready")
        else:
            self.update_status_message("No data loaded")

        logger.debug(f"Updated data-dependent UI state: has_data={has_data}")

    def request_ui_refresh(self) -> None:
        """Request a complete refresh of the UI."""
        self.ui_refresh_needed.emit()
        logger.debug("UI refresh requested")

    @Slot(dict)
    def handle_app_state_update(self, state: Dict[str, Any]) -> None:
        """
        Handle application state updates from other components.

        This method provides a centralized way for other controllers and
        components to update the UI state based on application state changes.

        Args:
            state: Dictionary of application state parameters
        """
        # Update UI based on the provided state
        if "has_data" in state:
            self.update_data_dependent_ui(state["has_data"])

        if "status_message" in state:
            self.update_status_message(state["status_message"])

        if "action_states" in state and isinstance(state["action_states"], dict):
            self.update_action_states(**state["action_states"])

        if "ui_theme" in state:
            self.set_ui_theme(state["ui_theme"])

        if state.get("refresh_ui", False):
            self.request_ui_refresh()

        logger.debug(f"Handled app state update: {state}")
