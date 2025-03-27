"""
ui_state_controller.py

Description: Controller for managing UI state across the application
Usage:
    ui_controller = UIStateController(signal_manager)
    ui_controller.update_status_bar("Ready")
    ui_controller.update_action_states(has_data=True)
"""

import logging
from typing import Dict, Optional, List, Any
import time

from PySide6.QtCore import QObject, Signal, Slot

from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class UIStateController(BaseController):
    """
    Controller for managing UI state across the application.

    This controller centralizes UI-specific state management that doesn't fit
    into other controllers like data, file operations, or view state.

    Signals:
        status_message_changed(str): Signal emitted when the status message changes
        actions_state_changed(dict): Signal emitted when the state of actions changes
        ui_theme_changed(str): Signal emitted when the UI theme changes
        ui_refresh_needed(): Signal emitted when the UI needs a complete refresh
        validation_state_changed(dict): Signal emitted when validation state changes

    Attributes:
        _status_message (str): Current status message
        _action_states (dict): Dictionary of action states (enabled/disabled)
        _ui_theme (str): Current UI theme
        _validation_state (dict): Current validation state information
    """

    # Signals
    status_message_changed = Signal(str)
    actions_state_changed = Signal(dict)
    ui_theme_changed = Signal(str)
    ui_refresh_needed = Signal()
    validation_state_changed = Signal(dict)

    def __init__(self, signal_manager=None):
        """
        Initialize the UIStateController.

        Args:
            signal_manager: Optional SignalManager instance for connection tracking
        """
        super().__init__(signal_manager)

        # Get config manager instance
        self._config_manager = ConfigManager()

        # Initialize state
        self._status_message = "Ready"
        self._action_states = {
            "save": False,
            "save_as": False,
            "export": False,
            "validate": False,
            "correct": False,
            "chart": False,
            "filter": False,
            "sort": False,
            "add_to_validation": False,
            "clear_validation": False,
            "refresh_validation": False,
            "auto_validate": self._config_manager.get_bool(
                "Validation", "auto_validate", True
            ),  # Load from config
        }
        self._ui_theme = "default"
        self._validation_state = {
            "has_issues": False,
            "issue_count": 0,
            "categories": {},
            "last_validation_time": None,
        }

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

                # Save auto_validate setting to config if it changed
                if action_name == "auto_validate":
                    try:
                        self._config_manager.set("Validation", "auto_validate", str(state))
                        logger.debug(f"Saved auto_validate setting to config: {state}")
                    except Exception as e:
                        logger.error(f"Error saving auto_validate setting to config: {e}")

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
        # Store current auto_validate state
        auto_validate = self._action_states.get("auto_validate", True)

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
            add_to_validation=has_data,
            clear_validation=has_data,
            refresh_validation=has_data,
            auto_validate=auto_validate,  # Preserve auto_validate setting
        )

        # Update status message based on data state
        if has_data:
            self.update_status_message("Data loaded and ready")
        else:
            self.update_status_message("No data loaded")
            # Reset validation state when no data
            self.update_validation_state(reset=True)

        logger.debug(f"Updated data-dependent UI state: has_data={has_data}")

    def request_ui_refresh(self) -> None:
        """Request a complete refresh of the UI."""
        self.ui_refresh_needed.emit()
        logger.debug("UI refresh requested")

    def update_validation_state(self, **validation_info) -> None:
        """
        Update validation state information and notify listeners.

        Args:
            **validation_info: Keyword arguments containing validation state information
                - has_issues (bool): Whether there are validation issues
                - issue_count (int): Number of validation issues
                - categories (dict): Validation issues by category
                - reset (bool): Whether to reset validation state to default
        """
        changed = False

        if validation_info.get("reset", False):
            new_state = {
                "has_issues": False,
                "issue_count": 0,
                "categories": {},
                "last_validation_time": None,
            }
            if self._validation_state != new_state:
                self._validation_state = new_state
                changed = True
        else:
            # Update individual state items
            for key, value in validation_info.items():
                if key != "reset" and (
                    key not in self._validation_state or self._validation_state[key] != value
                ):
                    self._validation_state[key] = value
                    changed = True

            # Update last validation time if anything changed
            if changed:
                self._validation_state["last_validation_time"] = time.time()

        if changed:
            self.validation_state_changed.emit(self._validation_state.copy())
            logger.debug(f"Validation state updated: {validation_info}")

            # Update status message based on validation state
            if self._validation_state["has_issues"]:
                issues = self._validation_state["issue_count"]
                self.update_status_message(f"Validation complete: {issues} issues found")
            elif self._validation_state["last_validation_time"] is not None:
                self.update_status_message("Validation complete: No issues found")

    def get_validation_state(self) -> dict:
        """
        Get current validation state information.

        Returns:
            Dictionary containing validation state information
        """
        return self._validation_state.copy()

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

    @Slot(dict)
    def handle_validation_results(self, results: dict) -> None:
        """
        Handle validation results and update UI state accordingly.

        Args:
            results: Dictionary of validation results by category
        """
        # Calculate issue count and categories
        has_issues = False
        issue_count = 0
        categories = {}

        for category, issues in results.items():
            cat_count = len(issues) if issues else 0
            if cat_count > 0:
                has_issues = True
                issue_count += cat_count
                categories[category] = cat_count

        # Update validation state
        self.update_validation_state(
            has_issues=has_issues, issue_count=issue_count, categories=categories
        )

        # Update action states based on validation results
        self.update_action_states(
            add_to_validation=has_issues,
            clear_validation=has_issues
            or self._validation_state["last_validation_time"] is not None,
        )

        logger.debug(f"Handled validation results: {issue_count} issues found")

    def toggle_auto_validate(self) -> bool:
        """
        Toggle the auto-validate state.

        Returns:
            bool: The new auto-validate state
        """
        current_state = self._action_states.get("auto_validate", True)
        new_state = not current_state

        # Update state and emit signal
        self.update_action_states(auto_validate=new_state)

        # Save to config
        try:
            self._config_manager.set("Validation", "auto_validate", str(new_state))
            logger.info(f"Saved auto_validate toggle to config: {new_state}")
        except Exception as e:
            logger.error(f"Error saving auto_validate toggle to config: {e}")

        logger.info(f"Auto-validate toggled from {current_state} to {new_state}")
        return new_state

    def set_auto_validate(self, enabled: bool) -> None:
        """
        Set the auto-validate state.

        Args:
            enabled: Whether auto-validation should be enabled
        """
        if self._action_states.get("auto_validate") != enabled:
            self.update_action_states(auto_validate=enabled)

            # Save to config
            try:
                self._config_manager.set("Validation", "auto_validate", str(enabled))
                logger.info(f"Saved auto_validate setting to config: {enabled}")
            except Exception as e:
                logger.error(f"Error saving auto_validate setting to config: {e}")

            logger.info(f"Auto-validate set to {enabled}")

    def get_auto_validate(self) -> bool:
        """
        Get the current auto-validate state.

        Returns:
            bool: Whether auto-validation is enabled
        """
        return self._action_states.get("auto_validate", True)
