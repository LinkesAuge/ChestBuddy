"""
view_state_controller.py

Description: Controller for managing view state in the application
Usage:
    controller = ViewStateController(data_model)
    controller.set_active_view("Dashboard")
"""

import logging
from typing import Dict, Optional, Any, List

from PySide6.QtCore import QObject, Signal, Slot, Qt, QTimer
from PySide6.QtWidgets import QStackedWidget, QWidget, QMessageBox

from chestbuddy.core.models import ChestDataModel
from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation

# Set up logger
logger = logging.getLogger(__name__)


class ViewStateController(QObject):
    """
    Controller for managing view state in the application.

    This controller handles view transitions, updates view state based on data
    availability, and ensures views are properly refreshed when needed.

    Attributes:
        data_model (ChestDataModel): The data model
        _views (Dict[str, QWidget]): Dictionary of views
        _sidebar (SidebarNavigation): The sidebar navigation widget
        _content_stack (QStackedWidget): The content stack widget
        _active_view (str): The name of the currently active view
        _has_data_loaded (bool): Whether data is currently loaded

    Signals:
        view_changed (str): Emitted when the active view changes
        data_state_changed (bool): Emitted when the data loaded state changes
    """

    view_changed = Signal(str)  # view_name
    data_state_changed = Signal(bool)  # has_data

    def __init__(self, data_model: ChestDataModel) -> None:
        """
        Initialize the ViewStateController.

        Args:
            data_model (ChestDataModel): The data model
        """
        super().__init__()

        # Store references
        self._data_model = data_model

        # Initialize state
        self._views = {}
        self._sidebar = None
        self._content_stack = None
        self._active_view = ""
        self._has_data_loaded = False

        # Connect to data model signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to relevant signals."""
        # Connect to data model signals to track data state
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.data_cleared.connect(self._on_data_cleared)

    def set_ui_components(
        self, views: Dict[str, QWidget], sidebar: SidebarNavigation, content_stack: QStackedWidget
    ) -> None:
        """
        Set UI components needed by the controller.

        This method must be called before using the controller.

        Args:
            views (Dict[str, QWidget]): Dictionary of views
            sidebar (SidebarNavigation): The sidebar navigation widget
            content_stack (QStackedWidget): The content stack widget
        """
        self._views = views
        self._sidebar = sidebar
        self._content_stack = content_stack

        # Connect to sidebar signals
        if self._sidebar:
            self._sidebar.navigation_changed.connect(self.set_active_view)

    # ===== Public API =====

    @property
    def active_view(self) -> str:
        """Get the name of the currently active view."""
        return self._active_view

    @property
    def has_data(self) -> bool:
        """Get whether data is currently loaded."""
        return self._has_data_loaded

    @Slot(str)
    def set_active_view(self, view_name: str) -> None:
        """
        Set the active view in the content stack.

        Args:
            view_name (str): The name of the view to activate
        """
        try:
            # Log the view switch for debugging
            logger.info(f"Setting active view to: {view_name}")

            # Validate components
            if not self._views or not self._sidebar or not self._content_stack:
                logger.error("UI components not set, cannot change view")
                return

            # Update sidebar selection
            self._sidebar.set_active_item(view_name)

            # Get the view from the views dictionary
            view = self._views.get(view_name)
            if view is None:
                logger.warning(f"View '{view_name}' not found in views dictionary")
                return

            # Check if the view is already active
            if self._content_stack.currentWidget() == view:
                logger.debug(f"View '{view_name}' is already active")
                return

            # Special handling for DataView to check if it needs population
            if view_name == "Data" and hasattr(view, "needs_population") and view.needs_population:
                logger.info("Data view needs population, populating table")
                view.populate_table()
                view.needs_population = False

            # Set the view as the current widget in the stack
            self._content_stack.setCurrentWidget(view)

            # Update internal state
            self._active_view = view_name

            # Emit view changed signal
            self.view_changed.emit(view_name)

            # Log success
            logger.info(f"View '{view_name}' activated successfully")
        except Exception as e:
            logger.error(f"Error setting active view to '{view_name}': {e}")
            # We'll let the UI handle displaying error messages
            raise

    @Slot(bool)
    def update_data_loaded_state(self, has_data: bool) -> None:
        """
        Update UI components based on whether data is loaded.

        Args:
            has_data (bool): Whether data is loaded
        """
        # Only update if state has changed
        if has_data != self._has_data_loaded:
            logger.info(f"Updating data loaded state: {has_data}")
            self._has_data_loaded = has_data

            # Update sidebar navigation state
            if self._sidebar:
                self._sidebar.set_data_loaded(has_data)

            # Update dashboard if it exists
            if "Dashboard" in self._views:
                dashboard_view = self._views["Dashboard"]
                if hasattr(dashboard_view, "set_data_loaded"):
                    dashboard_view.set_data_loaded(has_data)

            # Emit data state changed signal
            self.data_state_changed.emit(has_data)

            logger.info(f"Data loaded state updated to {has_data}")

    def refresh_active_view(self) -> None:
        """Refresh the currently active view."""
        try:
            # Validate components
            if not self._content_stack:
                logger.error("Content stack not set, cannot refresh view")
                return

            # Get the current widget
            current_index = self._content_stack.currentIndex()
            current_widget = self._content_stack.widget(current_index)

            if current_widget:
                # Special handling for DataViewAdapter
                if (
                    hasattr(current_widget, "__class__")
                    and current_widget.__class__.__name__ == "DataViewAdapter"
                ):
                    if hasattr(current_widget, "needs_refresh") and current_widget.needs_refresh():
                        current_widget.refresh()
                    else:
                        logger.debug("DataViewAdapter doesn't need refresh, skipping refresh")

                # Special handling for DashboardView
                elif (
                    hasattr(current_widget, "__class__")
                    and current_widget.__class__.__name__ == "DashboardView"
                ):
                    current_widget.refresh()

                # For other widgets, call refresh or update method if available
                elif hasattr(current_widget, "refresh"):
                    current_widget.refresh()
                elif hasattr(current_widget, "_update_view"):
                    current_widget._update_view()

            logger.info("Active view refreshed")
        except Exception as e:
            logger.error(f"Error refreshing active view: {e}")
            # We'll let the UI handle displaying error messages
            raise

    def populate_data_view(self) -> None:
        """Populate the data view if needed."""
        try:
            # Check if we have a Data view
            if "Data" not in self._views:
                logger.warning("Data view not found, cannot populate")
                return

            data_view = self._views["Data"]
            if data_view and hasattr(data_view, "populate_table"):
                # Only populate if the view needs a refresh
                if hasattr(data_view, "needs_refresh") and data_view.needs_refresh():
                    # If we're currently on the Data view, populate it immediately
                    if self._content_stack.currentWidget() == data_view:
                        logger.info("Currently on Data view and needs refresh, populating table")
                        data_view.populate_table()
                    else:
                        # Otherwise set the needs_population flag
                        if hasattr(data_view, "needs_population"):
                            logger.info("Not on Data view, setting needs_population flag")
                            data_view.needs_population = True
                else:
                    logger.info("Data view doesn't need refresh, skipping table population")
            else:
                logger.warning("Data view lacks populate_table method")
        except Exception as e:
            logger.error(f"Error populating data view: {e}")
            # We'll let the UI handle displaying error messages
            raise

    # ===== Slots =====

    @Slot()
    def _on_data_changed(self) -> None:
        """Handle data changed event."""
        # Update data loaded state - use a property for simplicity
        has_data = not self._data_model.is_empty()
        self.update_data_loaded_state(has_data)

        # Refresh data view population status
        self.populate_data_view()

        # Refresh active view if it needs to show data
        self.refresh_active_view()

    @Slot()
    def _on_data_cleared(self) -> None:
        """Handle data cleared event."""
        # Update data loaded state
        self.update_data_loaded_state(False)

        # Go back to dashboard when data is cleared
        self.set_active_view("Dashboard")
