"""
chart_view_adapter.py

Description: Adapter to integrate the existing ChartTab with the new BaseView structure
Usage:
    chart_view = ChartViewAdapter(data_model, chart_service)
    chart_view.set_data_view_controller(data_view_controller)
    main_window.add_view(chart_view)
"""

import time
import logging
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.chart_tab import ChartTab
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class ChartViewAdapter(UpdatableView):
    """
    Adapter that wraps the existing ChartTab component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        chart_service (ChartService): The service for chart generation
        chart_tab (ChartTab): The wrapped ChartTab instance
        data_view_controller (DataViewController): Controller for data operations

    Signals:
        chart_creation_started: Emitted when chart creation starts
        chart_creation_completed: Emitted when chart creation completes successfully
        chart_creation_error: Emitted when chart creation encounters an error
        chart_export_started: Emitted when chart export starts
        chart_export_completed: Emitted when chart export completes successfully
        chart_export_error: Emitted when chart export encounters an error

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and implement IUpdatable
        - Wraps the existing ChartTab component
        - Uses DataViewController for chart operations when available
        - Falls back to direct data_model/chart_service interaction when controller not available
        - Uses UpdateManager for scheduling updates
    """

    # Signals
    chart_creation_started = Signal()
    chart_creation_completed = Signal(str)  # chart type
    chart_creation_error = Signal(str)  # error message
    chart_export_started = Signal()
    chart_export_completed = Signal(str)  # file path
    chart_export_error = Signal(str)  # error message

    def __init__(
        self,
        data_model: ChestDataModel,
        chart_service: ChartService,
        data_view_controller: DataViewController = None,
        parent: QWidget = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the ChartViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to visualize
            chart_service (ChartService): The chart service to use
            data_view_controller (DataViewController, optional): Controller for data operations. Defaults to None.
            parent (QWidget, optional): The parent widget. Defaults to None.
            debug_mode (bool, optional): Enable debug mode for signal connections. Defaults to False.
        """
        # Store references
        self._data_model = data_model
        self._chart_service = chart_service
        self._data_view_controller = data_view_controller

        # State tracking to prevent unnecessary updates
        self._last_chart_state = {
            "chart_type": "",
            "x_column": "",
            "y_column": "",
            "chart_title": "",
            "group_by": "",
            "last_update_time": 0,
        }

        # Create the underlying ChartTab
        self._chart_tab = ChartTab(data_model, chart_service)

        # Initialize the base view
        super().__init__("Chart View", parent, debug_mode=debug_mode)
        self.setObjectName("ChartViewAdapter")

    def set_data_view_controller(self, controller: DataViewController):
        """
        Set the data view controller for this adapter.

        Args:
            controller (DataViewController): The controller to use
        """
        self._data_view_controller = controller
        self._connect_controller_signals()

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the ChartTab to the content widget
        self.get_content_layout().addWidget(self._chart_tab)

    def _connect_signals(self):
        """Connect signals and slots."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect ChartTab signals
        self._chart_tab.create_chart_button.clicked.connect(self._on_create_chart)
        self._chart_tab.export_button.clicked.connect(self._on_export_chart)

        # Connect header action signals
        self.header_action_clicked.connect(self._on_header_action_clicked)

        # Connect to controller signals if controller is set
        if self._data_view_controller:
            self._connect_controller_signals()

        # Connect to data model changes
        if self._data_model and hasattr(self._data_model, "data_changed"):
            self._signal_manager.connect(self._data_model, "data_changed", self, "request_update")

    def _connect_controller_signals(self):
        """Connect to data view controller signals."""
        if self._data_view_controller:
            self._data_view_controller.operation_started.connect(self._on_operation_started)
            self._data_view_controller.operation_completed.connect(self._on_operation_completed)
            self._data_view_controller.operation_error.connect(self._on_operation_error)

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # Add action buttons for common chart operations
        self.add_header_action("create", "Create Chart")
        self.add_header_action("export", "Export Chart")
        self.add_header_action("refresh", "Refresh")

    @Slot(str)
    def _on_header_action_clicked(self, action_id: str):
        """
        Handle header action button clicks.

        Args:
            action_id (str): The ID of the action button clicked
        """
        if action_id == "create":
            self._on_create_chart()
        elif action_id == "export":
            self._on_export_chart()
        elif action_id == "refresh":
            self._chart_tab._update_column_combos()
            if self._chart_tab._current_chart is not None:
                self._on_create_chart()

    @Slot()
    def _on_create_chart(self):
        """Handle chart creation request."""
        try:
            # Emit signal to indicate chart creation started
            self.chart_creation_started.emit()

            # Get chart parameters from UI
            chart_type = self._chart_tab.chart_type_combo.currentText()
            x_column = self._chart_tab.x_axis_combo.currentText()
            y_column = self._chart_tab.y_axis_combo.currentText()
            chart_title = self._chart_tab.chart_title_input.currentText()
            group_by = self._chart_tab.group_by_combo.currentText()
            if group_by == "None":
                group_by = None

            # Use controller if available, otherwise fallback to direct chart creation
            if self._data_view_controller:
                # Delegate to controller
                self._data_view_controller.create_chart(
                    chart_type=chart_type,
                    x_column=x_column,
                    y_column=y_column,
                    title=chart_title,
                    group_by=group_by,
                )
            else:
                # Direct chart creation
                self._chart_tab._create_chart()
                self.chart_creation_completed.emit(chart_type)

            # Update our state tracking
            self._update_chart_state()

        except Exception as e:
            # Handle errors
            error_message = f"Error creating chart: {str(e)}"
            self.chart_creation_error.emit(error_message)

    @Slot()
    def _on_export_chart(self):
        """Handle chart export request."""
        try:
            # Emit signal to indicate export started
            self.chart_export_started.emit()

            # Use controller if available, otherwise fallback to direct export
            if self._data_view_controller:
                # Delegate to controller
                self._data_view_controller.export_chart()
            else:
                # Direct export
                self._chart_tab._export_chart()

        except Exception as e:
            # Handle errors
            error_message = f"Error exporting chart: {str(e)}"
            self.chart_export_error.emit(error_message)

    @Slot(str)
    def _on_operation_started(self, operation: str):
        """
        Handle operation started signal from controller.

        Args:
            operation (str): The operation that started
        """
        if operation == "chart_creation":
            self.chart_creation_started.emit()
        elif operation == "chart_export":
            self.chart_export_started.emit()

    @Slot(str, str)
    def _on_operation_completed(self, operation: str, result: str):
        """
        Handle operation completed signal from controller.

        Args:
            operation (str): The operation that completed
            result (str): Operation result information
        """
        if operation == "chart_creation":
            self.chart_creation_completed.emit(result)
        elif operation == "chart_export":
            self.chart_export_completed.emit(result)

    @Slot(str, str)
    def _on_operation_error(self, operation: str, error_message: str):
        """
        Handle operation error signal from controller.

        Args:
            operation (str): The operation that encountered an error
            error_message (str): Error message
        """
        if operation == "chart_creation":
            self.chart_creation_error.emit(error_message)
        elif operation == "chart_export":
            self.chart_export_error.emit(error_message)

    def _update_view_content(self, data=None) -> None:
        """
        Update the view content with current data.

        Args:
            data: Optional data for the update (unused in this implementation)
        """
        # If we have a chart, refresh it
        if (
            hasattr(self._chart_tab, "_current_chart")
            and self._chart_tab._current_chart is not None
        ):
            # Recreate the chart with current parameters
            self._on_create_chart()

        # Update column combos for data model changes
        if hasattr(self._chart_tab, "_update_column_combos"):
            self._chart_tab._update_column_combos()

        # Update our state tracking
        self._update_chart_state()
        logger.debug(f"ChartViewAdapter: View content updated")

    def _refresh_view_content(self) -> None:
        """
        Refresh the view content without changing the underlying data.
        """
        # Just update the column combos to reflect data model changes
        if hasattr(self._chart_tab, "_update_column_combos"):
            self._chart_tab._update_column_combos()
        logger.debug(f"ChartViewAdapter: View content refreshed")

    def _populate_view_content(self, data=None) -> None:
        """
        Populate the view content from scratch.

        Args:
            data: Optional data to use for population (unused in this implementation)
        """
        # Update column combos
        if hasattr(self._chart_tab, "_update_column_combos"):
            self._chart_tab._update_column_combos()

        # If there's a current chart, recreate it
        if (
            hasattr(self._chart_tab, "_current_chart")
            and self._chart_tab._current_chart is not None
        ):
            self._on_create_chart()

        # Update our state tracking
        self._update_chart_state()
        logger.debug(f"ChartViewAdapter: View content populated")

    def _reset_view_content(self) -> None:
        """
        Reset the view content to its initial state.
        """
        # Clear the current chart
        if hasattr(self._chart_tab, "_clear_chart"):
            self._chart_tab._clear_chart()
        elif hasattr(self._chart_tab, "_current_chart"):
            self._chart_tab._current_chart = None

        # Reset UI elements to defaults
        if hasattr(self._chart_tab, "chart_type_combo"):
            self._chart_tab.chart_type_combo.setCurrentIndex(0)
        if hasattr(self._chart_tab, "x_axis_combo"):
            self._chart_tab.x_axis_combo.setCurrentIndex(0)
        if hasattr(self._chart_tab, "y_axis_combo"):
            self._chart_tab.y_axis_combo.setCurrentIndex(0)
        if hasattr(self._chart_tab, "chart_title_input"):
            self._chart_tab.chart_title_input.setCurrentText("")
        if hasattr(self._chart_tab, "group_by_combo"):
            self._chart_tab.group_by_combo.setCurrentIndex(0)

        # Reset our state tracking
        self._last_chart_state = {
            "chart_type": "",
            "x_column": "",
            "y_column": "",
            "chart_title": "",
            "group_by": "",
            "last_update_time": 0,
        }
        logger.debug(f"ChartViewAdapter: View content reset")

    def _update_chart_state(self) -> None:
        """Update tracking of the chart state to detect changes."""
        current_state = {
            "chart_type": self._chart_tab.chart_type_combo.currentText()
            if hasattr(self._chart_tab, "chart_type_combo")
            else "",
            "x_column": self._chart_tab.x_axis_combo.currentText()
            if hasattr(self._chart_tab, "x_axis_combo")
            else "",
            "y_column": self._chart_tab.y_axis_combo.currentText()
            if hasattr(self._chart_tab, "y_axis_combo")
            else "",
            "chart_title": self._chart_tab.chart_title_input.currentText()
            if hasattr(self._chart_tab, "chart_title_input")
            else "",
            "group_by": self._chart_tab.group_by_combo.currentText()
            if hasattr(self._chart_tab, "group_by_combo")
            else "",
        }

        # Update state tracking
        self._last_chart_state.update(current_state)
        self._last_chart_state["last_update_time"] = time.time()

    def needs_update(self) -> bool:
        """
        Check if the view needs updating based on chart state.

        Returns:
            bool: True if the view needs to be updated, False otherwise
        """
        # If data model is empty, we don't need an update
        if self._data_model.is_empty:
            return False

        # If we have a current chart, check if parameters have changed
        if (
            hasattr(self._chart_tab, "_current_chart")
            and self._chart_tab._current_chart is not None
        ):
            current_state = {
                "chart_type": self._chart_tab.chart_type_combo.currentText()
                if hasattr(self._chart_tab, "chart_type_combo")
                else "",
                "x_column": self._chart_tab.x_axis_combo.currentText()
                if hasattr(self._chart_tab, "x_axis_combo")
                else "",
                "y_column": self._chart_tab.y_axis_combo.currentText()
                if hasattr(self._chart_tab, "y_axis_combo")
                else "",
                "chart_title": self._chart_tab.chart_title_input.currentText()
                if hasattr(self._chart_tab, "chart_title_input")
                else "",
                "group_by": self._chart_tab.group_by_combo.currentText()
                if hasattr(self._chart_tab, "group_by_combo")
                else "",
            }

            needs_refresh = (
                current_state["chart_type"] != self._last_chart_state["chart_type"]
                or current_state["x_column"] != self._last_chart_state["x_column"]
                or current_state["y_column"] != self._last_chart_state["y_column"]
                or current_state["chart_title"] != self._last_chart_state["chart_title"]
                or current_state["group_by"] != self._last_chart_state["group_by"]
            )

            if needs_refresh:
                logger.debug(f"ChartViewAdapter.needs_update: TRUE - Chart parameters changed")
                return True

        # Also check if the base implementation thinks we need an update
        return super().needs_update()

    def refresh(self):
        """
        Refresh the chart view only if needed.

        Uses the UpdateManager to schedule a refresh.
        """
        logger.debug("ChartViewAdapter.refresh: Using UpdateManager for refresh")
        # Use the UpdateManager to schedule a refresh
        try:
            self.schedule_update()
        except Exception as e:
            logger.error(f"Error scheduling update via UpdateManager: {e}")
            # Fall back to direct refresh if UpdateManager is not available
            if self.needs_update():
                self._update_view_content()
