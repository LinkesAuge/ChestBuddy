"""
view_state_controller.py

Description: Controller for managing view state in the application
Usage:
    controller = ViewStateController(data_model, signal_manager)
    controller.set_active_view("Dashboard")
"""

import logging
from typing import Optional, Any, Callable, Tuple
import time

from PySide6.QtCore import QObject, Signal, Slot, Qt, QTimer, QSettings
from PySide6.QtWidgets import QStackedWidget, QWidget, QMessageBox

from chestbuddy.core.models import ChestDataModel
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation
from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.ui.interfaces import IUpdatable

# Set up logger
logger = logging.getLogger(__name__)


class ViewStateController(BaseController):
    """
    Controller for managing view state in the application.

    This controller handles view transitions, updates view state based on data
    availability, and ensures views are properly refreshed when needed.

    Attributes:
        data_model (ChestDataModel): The data model
        _views (dict[str, QWidget]): Dictionary of views
        _sidebar (SidebarNavigation): The sidebar navigation widget
        _content_stack (QStackedWidget): The content stack widget
        _active_view (str): The name of the currently active view
        _has_data_loaded (bool): Whether data is currently loaded
        _view_dependencies (dict[str, set[str]]): View dependencies (key depends on values)
        _view_prerequisites (dict[str, list[Callable]]): View prerequisites functions
        _view_availability (dict[str, bool]): Current availability of views
        _navigation_history (list[str]): History of view navigation
        _history_position (int): Current position in navigation history
        _max_history (int): Maximum number of history entries to keep
        _last_states (dict[str, Any]): Last known states for views
        _view_transition_in_progress (bool): Flag to track if a view transition is in progress
        _data_view_controller (Optional[object]): The data view controller, if available
        _update_throttled (bool): Flag to track if updates are being throttled
        _pending_view_change (Optional[str]): Pending view change during asynchronous operations

    Signals:
        view_changed (str): Emitted when the active view changes
        data_state_changed (bool): Emitted when the data loaded state changes
        view_prerequisites_failed (str, str): Emitted when view prerequisites check fails (view_name, reason)
        view_availability_changed (dict): Emitted when view availability changes
        navigation_history_changed (bool, bool): Emitted when navigation history changes (can_go_back, can_go_forward)
        state_persistence_changed (bool): Emitted when state persistence changes
        view_transition_started (str, str): Emitted when view transition starts (from_view, to_view)
        view_transition_completed (str): Emitted when view transition completes (view_name)
    """

    view_changed = Signal(str)  # view_name
    data_state_changed = Signal(bool)
    view_prerequisites_failed = Signal(str, str)  # view_name, reason
    view_availability_changed = Signal(dict)  # dict[view_name, is_available]
    navigation_history_changed = Signal(bool, bool)  # can_go_back, can_go_forward
    state_persistence_changed = Signal(bool)  # is_enabled
    view_transition_started = Signal(str, str)  # from_view, to_view
    view_transition_completed = Signal(str)  # view_name

    def __init__(self, data_model: ChestDataModel, signal_manager=None) -> None:
        """
        Initialize the ViewStateController.

        Args:
            data_model (ChestDataModel): The data model
            signal_manager: Optional SignalManager instance for connection tracking
        """
        super().__init__(signal_manager)

        # Store references
        self._data_model = data_model

        # Initialize state
        self._views = {}
        self._sidebar = None
        self._content_stack = None
        self._active_view = ""
        self._has_data_loaded = False

        # View dependencies and prerequisites
        self._view_dependencies: dict[str, set[str]] = {}
        self._view_prerequisites: dict[str, list[Callable]] = {}
        self._view_availability: dict[str, bool] = {}

        # Navigation history
        self._navigation_history: list[str] = []
        self._history_position: int = -1
        self._max_history: int = 20

        # State persistence
        self._state_persistence_enabled = True
        self._last_states: dict[str, Any] = {}

        # Edge case handling
        self._view_transition_in_progress = False
        self._ignore_history = False
        self._data_view_controller = None
        self._update_throttled = False
        self._pending_view_change = None
        self._last_throttle_time = 0
        self._throttle_interval_ms = 250  # Minimum ms between updates

        # Connect to data model signals
        self.connect_to_model(data_model)

    def connect_to_model(self, model) -> None:
        """
        Connect to data model signals.

        Args:
            model: The data model to connect to
        """
        super().connect_to_model(model)

        # Connect to model signals using signal manager
        if hasattr(model, "data_changed"):
            self._signal_manager.connect(model, "data_changed", self, "_on_data_changed")

        # Check if data_cleared signal exists, otherwise use data_changed
        if hasattr(model, "data_cleared"):
            self._signal_manager.connect(model, "data_cleared", self, "_on_data_cleared")
        else:
            logger.warning(
                "data_cleared signal not found in data model, using data_changed instead"
            )
            # We'll handle data clearing in the data_changed handler

        logger.debug(f"ViewStateController connected to model: {model.__class__.__name__}")

    def set_ui_components(
        self, views: dict[str, QWidget], sidebar: SidebarNavigation, content_stack: QStackedWidget
    ) -> None:
        """
        Set UI components needed by the controller.

        This method must be called before using the controller.

        Args:
            views (dict[str, QWidget]): Dictionary of views
            sidebar (SidebarNavigation): The sidebar navigation widget
            content_stack (QStackedWidget): The content stack widget
        """
        self._views = views
        self._sidebar = sidebar
        self._content_stack = content_stack

        # Connect to sidebar signals using signal manager
        if self._sidebar:
            self.connect_to_view(self._sidebar)
            self._signal_manager.connect(
                self._sidebar, "navigation_changed", self, "set_active_view"
            )
            self._signal_manager.connect(
                self._sidebar,
                "data_dependent_view_clicked",
                self,
                "_on_data_dependent_view_clicked",
            )

            # Check if sidebar implements IUpdatable interface and populate it
            if isinstance(self._sidebar, IUpdatable):
                logger.info("Sidebar implements IUpdatable, populating it")
                self._sidebar.populate()

        # Initialize view availability
        for view_name in self._views:
            self._view_availability[view_name] = True

        # Set up standard view dependencies
        self._setup_default_dependencies()

        # Initialize navigation history tracking
        self._navigation_history = ["Dashboard"]  # Start with Dashboard view
        self._history_position = 0

        # Emit initial navigation history state
        self.navigation_history_changed.emit(False, False)

    def set_data_view_controller(self, data_view_controller) -> None:
        """
        Set the data view controller for coordinated updates.

        Args:
            data_view_controller: The data view controller instance
        """
        self._data_view_controller = data_view_controller

        # Connect relevant signals using signal manager
        if data_view_controller and self._signal_manager:
            if hasattr(data_view_controller, "filter_applied"):
                self._signal_manager.connect(
                    data_view_controller, "filter_applied", self, "_on_data_filter_applied"
                )
            if hasattr(data_view_controller, "sort_applied"):
                self._signal_manager.connect(
                    data_view_controller, "sort_applied", self, "_on_data_sort_applied"
                )
            if hasattr(data_view_controller, "operation_error"):
                self._signal_manager.connect(
                    data_view_controller, "operation_error", self, "_on_data_operation_error"
                )

            logger.info("Data view controller set and signals connected")

    def _setup_default_dependencies(self) -> None:
        """Set up default view dependencies based on standard workflow."""
        # Data view doesn't depend on anything
        # Validation depends on data being loaded
        self.register_view_dependency("Validation", {"Data"})

        # Correction depends on validation being completed
        self.register_view_dependency("Correction", {"Validation"})

        # Charts depends on data being loaded
        self.register_view_dependency("Charts", {"Data"})

        # Register standard prerequisites
        self.register_view_prerequisite(
            "Validation", lambda: (self._has_data_loaded, "Data must be loaded first")
        )
        self.register_view_prerequisite(
            "Correction", lambda: (self._has_data_loaded, "Data must be loaded first")
        )
        self.register_view_prerequisite(
            "Charts", lambda: (self._has_data_loaded, "Data must be loaded first")
        )

    def _on_data_dependent_view_clicked(self, view_name: str, subsection: Optional[str]) -> None:
        """
        Handle when a data-dependent view is clicked without data loaded.

        Args:
            view_name (str): The name of the view
            subsection (Optional[str]): The subsection, if any
        """
        logger.info(f"Data-dependent view '{view_name}' clicked without data loaded")

        # Show message to user
        QMessageBox.information(
            None,
            "Data Required",
            f"The {view_name} view requires data to be loaded first.\n\n"
            "Please load data from the Dashboard or Data view.",
        )

    # ===== Public API =====

    @property
    def active_view(self) -> str:
        """Get the name of the currently active view."""
        return self._active_view

    @property
    def has_data(self) -> bool:
        """Get whether data is currently loaded."""
        return self._has_data_loaded

    @property
    def view_availability(self) -> dict[str, bool]:
        """Get the current availability status of all views."""
        return self._view_availability.copy()

    @property
    def can_go_back(self) -> bool:
        """Check if navigation can go back in history."""
        return self._history_position > 0

    @property
    def can_go_forward(self) -> bool:
        """Check if navigation can go forward in history."""
        return self._history_position < len(self._navigation_history) - 1

    @property
    def state_persistence_enabled(self) -> bool:
        """Check if state persistence is enabled."""
        return self._state_persistence_enabled

    @state_persistence_enabled.setter
    def state_persistence_enabled(self, enabled: bool) -> None:
        """Set whether state persistence is enabled."""
        if self._state_persistence_enabled != enabled:
            self._state_persistence_enabled = enabled
            self.state_persistence_changed.emit(enabled)
            logger.info(f"State persistence {'enabled' if enabled else 'disabled'}")

    @property
    def is_transition_in_progress(self) -> bool:
        """Check if a view transition is currently in progress."""
        return self._view_transition_in_progress

    def register_view_dependency(self, view_name: str, dependencies: set[str]) -> None:
        """
        Register dependencies for a view.

        A view can depend on multiple other views. The view will only be available
        when all its dependencies are satisfied.

        Args:
            view_name (str): The name of the view
            dependencies (set[str]): Set of view names this view depends on
        """
        logger.info(f"Registering dependencies for view '{view_name}': {dependencies}")
        self._view_dependencies[view_name] = dependencies

        # Immediately update availability
        self._update_view_availability()

    def register_view_prerequisite(
        self, view_name: str, check_func: Callable[[], Tuple[bool, str]]
    ) -> None:
        """
        Register a prerequisite check function for a view.

        The function should return (True, "") if the prerequisite is met,
        or (False, "reason") if not met.

        Args:
            view_name (str): The name of the view
            check_func (Callable): Function that returns (is_met, reason)
        """
        if view_name not in self._view_prerequisites:
            self._view_prerequisites[view_name] = []

        self._view_prerequisites[view_name].append(check_func)
        logger.info(f"Registered prerequisite check for view '{view_name}'")

        # Update availability immediately
        self._update_view_availability()

    def check_view_prerequisites(self, view_name: str) -> Tuple[bool, str]:
        """
        Check if prerequisites for a view are met.

        Args:
            view_name (str): The name of the view to check

        Returns:
            Tuple[bool, str]: (prerequisites_met, failure_reason)
        """
        # Check dependencies first
        if view_name in self._view_dependencies:
            for dependency in self._view_dependencies[view_name]:
                if (
                    dependency not in self._view_availability
                    or not self._view_availability[dependency]
                ):
                    return False, f"Dependency '{dependency}' not available"

        # Check custom prerequisites if any
        if view_name in self._view_prerequisites:
            for check_func in self._view_prerequisites[view_name]:
                try:
                    is_met, reason = check_func()
                    if not is_met:
                        return False, reason
                except Exception as e:
                    logger.error(f"Error in prerequisite check for '{view_name}': {e}")
                    return False, f"Error checking prerequisites: {str(e)}"

        return True, ""

    def _update_view_availability(self) -> None:
        """
        Update availability of all views based on their dependencies and prerequisites.
        """
        # Don't update if throttled to avoid UI flicker
        current_time = time.time() * 1000  # Use time.time() instead of QTimer.currentTime()
        if self._update_throttled and (
            current_time - self._last_throttle_time < self._throttle_interval_ms
        ):
            logger.debug("Skipping view availability update (throttled)")
            return

        self._last_throttle_time = current_time
        self._update_throttled = True

        changes = {}

        # First pass: check basic data dependency
        for view_name in self._views:
            # Dashboard is always available
            if view_name == "Dashboard":
                available = True
            # All other views require data to be loaded (if not overridden later)
            elif view_name != "Data" and not self._has_data_loaded:
                available = False
            else:
                available = True

            if (
                view_name in self._view_availability
                and self._view_availability[view_name] != available
            ):
                changes[view_name] = available

            self._view_availability[view_name] = available

        # Second pass: check dependencies and prerequisites
        for view_name in self._views:
            # Skip Dashboard which is always available
            if view_name == "Dashboard":
                continue

            # Check view prerequisites
            prerequisites_met, _ = self.check_view_prerequisites(view_name)

            # Update availability
            if not prerequisites_met and self._view_availability[view_name]:
                self._view_availability[view_name] = False
                changes[view_name] = False
            elif prerequisites_met and not self._view_availability[view_name]:
                self._view_availability[view_name] = True
                changes[view_name] = True

        # Update sidebar if changes were made
        if changes and self._sidebar:
            self._sidebar.update_view_availability(self._view_availability)
            self.view_availability_changed.emit(self._view_availability)
            logger.info(f"View availability changed: {changes}")

        # Reset throttle status after a delay
        QTimer.singleShot(self._throttle_interval_ms, self._reset_throttle)

    def _reset_throttle(self) -> None:
        """Reset throttle status to allow updates again."""
        self._update_throttled = False

    @Slot(str, str)
    def set_active_view(self, view_name: str, subsection: Optional[str] = None) -> None:
        """
        Set the active view.

        Args:
            view_name (str): The name of the view to set as active
            subsection (Optional[str]): The subsection, if any
        """
        # If a transition is already in progress, queue this request
        if self._view_transition_in_progress:
            logger.info(f"View transition already in progress, queuing change to '{view_name}'")
            self._pending_view_change = (view_name, subsection)
            return

        if view_name not in self._views:
            logger.error(f"View '{view_name}' not found in registered views")
            return

        # Check if prerequisites are met
        can_activate, reason = self.check_view_prerequisites(view_name)
        if not can_activate:
            logger.warning(f"Cannot activate view '{view_name}': {reason}")
            self.view_prerequisites_failed.emit(view_name, reason)
            return

        # If we're already on this view, no need to change
        if self._active_view == view_name:
            return

        # Mark transition as started
        old_view = self._active_view
        self._view_transition_in_progress = True
        self.view_transition_started.emit(old_view, view_name)

        # Save current view state if state persistence is enabled
        if self._state_persistence_enabled and self._active_view:
            self._save_view_state(self._active_view)

        # Get the current widget
        current_widget = self._content_stack.currentWidget()

        # Get the target widget
        target_widget = self._views.get(view_name)
        if not target_widget:
            logger.error(f"Widget for view '{view_name}' not found")
            self._view_transition_in_progress = False
            return

        # Check if target view needs populating (if it's the Data view)
        if (
            view_name == "Data"
            and hasattr(target_widget, "needs_population")
            and target_widget.needs_population
        ):
            logger.info(f"Populating data view as it needs population")
            if hasattr(target_widget, "populate_table"):
                try:
                    target_widget.populate_table()
                except Exception as e:
                    logger.error(f"Error populating Data view: {e}")

        # Coordinate with DataViewController if this is Data view
        if view_name == "Data" and self._data_view_controller:
            try:
                # Ensure data view controller is properly set up
                if hasattr(self._data_view_controller, "set_view"):
                    self._data_view_controller.set_view(target_widget)
                # Refresh data if needed
                if hasattr(self._data_view_controller, "needs_refresh"):
                    if self._data_view_controller.needs_refresh():
                        if hasattr(self._data_view_controller, "refresh_data"):
                            self._data_view_controller.refresh_data()
            except Exception as e:
                logger.error(f"Error coordinating with DataViewController: {e}")

        # Update sidebar
        if self._sidebar:
            # Use IUpdatable interface if available
            if isinstance(self._sidebar, IUpdatable) and self._sidebar.needs_update():
                logger.debug(f"Updating sidebar via IUpdatable interface")
                self._sidebar.set_active_item(view_name)
                self._sidebar.update()
            else:
                # Fall back to direct method call
                self._sidebar.set_active_item(view_name)

        # Set widget in stack
        self._content_stack.setCurrentWidget(target_widget)

        # Update state
        self._active_view = view_name

        # Restore view state if available
        if self._state_persistence_enabled:
            self._restore_view_state(view_name)

        # Add to navigation history
        if not self._ignore_history:
            self._add_to_navigation_history(view_name)

        # Log the view change
        logger.info(f"View changed from '{old_view}' to '{view_name}'")

        # Complete transition after a short delay to allow UI to update
        QTimer.singleShot(50, lambda: self._complete_transition(view_name))

    def _complete_transition(self, view_name: str) -> None:
        """
        Complete the view transition after animations or async operations.

        Args:
            view_name (str): The name of the view that was transitioned to
        """
        self._view_transition_in_progress = False
        logger.debug(f"View transition to '{view_name}' completed")

        # Emit view transition completed signal
        self.view_transition_completed.emit(view_name)

        # Process any pending view change
        if self._pending_view_change:
            pending_view, pending_subsection = self._pending_view_change
            self._pending_view_change = None
            logger.info(
                f"Processing pending view change to '{pending_view}' with subsection '{pending_subsection}'"
            )
            self.set_active_view(pending_view, pending_subsection)

    def _save_view_state(self, view_name: str) -> None:
        """
        Save the state of a view for later restoration.

        Args:
            view_name (str): The name of the view to save state for
        """
        view = self._views.get(view_name)
        if not view:
            return

        # Check if view has a get_state method
        if hasattr(view, "get_state") and callable(getattr(view, "get_state")):
            try:
                state = view.get_state()
                self._last_states[view_name] = state
                logger.debug(f"Saved state for view '{view_name}'")
            except Exception as e:
                logger.error(f"Error saving state for view '{view_name}': {e}")

    def _restore_view_state(self, view_name: str) -> None:
        """
        Restore the state of a view if previously saved.

        Args:
            view_name (str): The name of the view to restore state for
        """
        view = self._views.get(view_name)
        if not view:
            return

        # Check if view has a set_state method and we have saved state
        if (
            view_name in self._last_states
            and hasattr(view, "set_state")
            and callable(getattr(view, "set_state"))
        ):
            try:
                view.set_state(self._last_states[view_name])
                logger.debug(f"Restored state for view '{view_name}'")
            except Exception as e:
                logger.error(f"Error restoring state for view '{view_name}': {e}")

    def _add_to_navigation_history(self, view_name: str) -> None:
        """
        Add a view to the navigation history.

        Args:
            view_name (str): The name of the view to add
        """
        # If we're not at the end of the history, truncate the history
        if self._history_position < len(self._navigation_history) - 1:
            self._navigation_history = self._navigation_history[: self._history_position + 1]

        # If the last entry is the same as the new one, don't add it
        if self._navigation_history and self._navigation_history[-1] == view_name:
            return

        # Add the view to the history
        self._navigation_history.append(view_name)
        if len(self._navigation_history) > self._max_history:
            # Remove oldest history item to maintain max size
            self._navigation_history.pop(0)
            # Adjust position to account for removed item
            self._history_position = max(0, self._history_position - 1)
        else:
            self._history_position = len(self._navigation_history) - 1

        # Emit signal about history change
        self.navigation_history_changed.emit(self.can_go_back, self.can_go_forward)
        logger.debug(
            f"Navigation history updated: position={self._history_position}, history={self._navigation_history}"
        )

    def navigate_back(self) -> bool:
        """
        Navigate back in the history.

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        if not self.can_go_back:
            return False

        # Move back in history
        self._history_position -= 1
        view_name = self._navigation_history[self._history_position]

        # Activate the view without adding to history
        self._ignore_history = True
        try:
            self.set_active_view(view_name)
        finally:
            self._ignore_history = False

        # Emit signal about history change
        self.navigation_history_changed.emit(self.can_go_back, self.can_go_forward)
        return True

    def navigate_forward(self) -> bool:
        """
        Navigate forward in the history.

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        if not self.can_go_forward:
            return False

        # Move forward in history
        self._history_position += 1
        view_name = self._navigation_history[self._history_position]

        # Activate the view without adding to history
        self._ignore_history = True
        try:
            self.set_active_view(view_name)
        finally:
            self._ignore_history = False

        # Emit signal about history change
        self.navigation_history_changed.emit(self.can_go_back, self.can_go_forward)
        return True

    @Slot(bool)
    def update_data_loaded_state(self, has_data: bool) -> None:
        """
        Update the data loaded state and propagate it to views.

        Args:
            has_data (bool): Whether data is loaded
        """
        if self._has_data_loaded == has_data:
            return

        logger.info(f"Data loaded state changed: {has_data}")
        self._has_data_loaded = has_data

        # Update sidebar
        if self._sidebar:
            self._sidebar.set_data_loaded(has_data)

        # Propagate data state to all views
        for view_name, view in self._views.items():
            if hasattr(view, "set_data_loaded") and callable(getattr(view, "set_data_loaded")):
                try:
                    view.set_data_loaded(has_data)
                except Exception as e:
                    logger.error(f"Error setting data loaded state for view '{view_name}': {e}")

        # Update view availability
        self._update_view_availability()

        # Emit signal
        self.data_state_changed.emit(has_data)

        # If data is cleared, navigate to Dashboard
        if not has_data and self._active_view != "Dashboard":
            self.set_active_view("Dashboard")

    def refresh_active_view(self) -> None:
        """Refresh the currently active view."""
        if not self._active_view:
            return

        # Get the active widget
        active_widget = self._content_stack.currentWidget()
        if not active_widget:
            logger.warning("No active widget found to refresh")
            return

        # Check if widget implements IUpdatable interface
        if isinstance(active_widget, IUpdatable):
            logger.info(f"Refreshing active view '{self._active_view}' via IUpdatable interface")
            try:
                if active_widget.needs_update():
                    active_widget.refresh()
                else:
                    logger.debug(f"View '{self._active_view}' doesn't need refreshing")
            except Exception as e:
                logger.error(f"Error refreshing view via IUpdatable: {e}")
            return

        # Legacy refresh for widgets that don't implement IUpdatable
        # Check if widget has needs_refresh method to avoid unnecessary refreshes
        needs_refresh = True
        if hasattr(active_widget, "needs_refresh") and callable(
            getattr(active_widget, "needs_refresh")
        ):
            try:
                needs_refresh = active_widget.needs_refresh()
            except Exception as e:
                logger.error(f"Error checking if view needs refresh: {e}")

        # Refresh if needed
        if needs_refresh:
            logger.info(f"Refreshing active view: {self._active_view}")
            if hasattr(active_widget, "refresh") and callable(getattr(active_widget, "refresh")):
                try:
                    active_widget.refresh()
                except Exception as e:
                    logger.error(f"Error refreshing view: {e}")
        else:
            logger.debug(f"View '{self._active_view}' doesn't need refreshing")

    def populate_data_view(self) -> None:
        """
        Populate the data view with current data.

        This is called when new data is loaded.
        """
        if "Data" not in self._views:
            logger.warning("Data view not found in registered views")
            return

        data_view = self._views["Data"]

        # Check if we need to populate the data view
        is_current = self._content_stack.currentWidget() == data_view

        if is_current:
            # If Data view is current, populate it now
            logger.info("Populating Data view (current)")
            if hasattr(data_view, "populate_table") and callable(
                getattr(data_view, "populate_table")
            ):
                try:
                    data_view.populate_table()
                except Exception as e:
                    logger.error(f"Error populating Data view: {e}")
        else:
            # Mark for population when it becomes current
            logger.info("Marking Data view for population (not current)")
            if hasattr(data_view, "needs_population"):
                data_view.needs_population = True

    def save_state(self, settings: QSettings) -> None:
        """
        Save controller state to settings.

        Args:
            settings (QSettings): The settings object to save to
        """
        if not self._state_persistence_enabled:
            return

        settings.beginGroup("ViewStateController")
        settings.setValue("active_view", self._active_view)
        settings.setValue("has_data_loaded", self._has_data_loaded)
        settings.setValue("navigation_history", self._navigation_history)
        settings.setValue("history_position", self._history_position)
        settings.endGroup()

        logger.debug("View state controller state saved to settings")

    def load_state(self, settings: QSettings) -> None:
        """
        Load controller state from settings.

        Args:
            settings (QSettings): The settings object to load from
        """
        if not self._state_persistence_enabled:
            return

        settings.beginGroup("ViewStateController")
        self._navigation_history = settings.value("navigation_history", ["Dashboard"])
        self._history_position = settings.value("history_position", 0, int)

        # Don't directly restore active view, just record it for later
        last_view = settings.value("active_view", "Dashboard")
        settings.endGroup()

        # Emit signal about history change
        self.navigation_history_changed.emit(self.can_go_back, self.can_go_forward)

        logger.debug(f"View state controller state loaded from settings (last view: {last_view})")

        # Restore the view if it exists (don't restore immediately to avoid issues during initialization)
        QTimer.singleShot(
            100, lambda: self.set_active_view(last_view) if last_view in self._views else None
        )

    # ==== DataViewController integration ====

    @Slot(dict)
    def _on_data_filter_applied(self, filter_params: dict) -> None:
        """
        Handle filter applied event from DataViewController.

        Args:
            filter_params (dict): Filter parameters
        """
        logger.debug(f"Data filter applied: {filter_params}")

        # Update Data view state if needed
        if "Data" in self._last_states:
            if "filter" not in self._last_states["Data"]:
                self._last_states["Data"]["filter"] = {}
            self._last_states["Data"]["filter"] = filter_params

    @Slot(str, bool)
    def _on_data_sort_applied(self, column: str, ascending: bool) -> None:
        """
        Handle sort applied event from DataViewController.

        Args:
            column (str): Column name to sort by
            ascending (bool): Sort direction
        """
        logger.debug(f"Data sort applied: column={column}, ascending={ascending}")

        # Update Data view state if needed
        if "Data" in self._last_states:
            self._last_states["Data"]["sort"] = {"column": column, "ascending": ascending}

    @Slot(str)
    def _on_data_operation_error(self, error_message: str) -> None:
        """
        Handle operation error event from DataViewController.

        Args:
            error_message (str): Error message
        """
        logger.error(f"Data operation error: {error_message}")

        # Could integrate with ErrorHandlingController here if available

    @Slot(object)
    def _on_data_changed(self, data_state=None) -> None:
        """
        Handle data changed event from the data model.

        Args:
            data_state: The current DataState (optional)
        """
        has_data = not self._data_model.is_empty

        logger.info(f"Data changed event: has_data={has_data}")

        # Update data loaded state
        self.update_data_loaded_state(has_data)

        # Populate data view for new data
        self.populate_data_view()

        # Refresh active view
        self.refresh_active_view()

    @Slot()
    def _on_data_cleared(self) -> None:
        """Handle data cleared event from the data model."""
        logger.info("Data cleared event")

        # Update data loaded state
        self.update_data_loaded_state(False)

        # Navigate to Dashboard
        self.set_active_view("Dashboard")

    def get_view(self, view_name: str) -> Optional[QWidget]:
        """
        Get a view by name.

        Args:
            view_name: The name of the view to get

        Returns:
            The view widget, or None if not found
        """
        return self._views.get(view_name)
