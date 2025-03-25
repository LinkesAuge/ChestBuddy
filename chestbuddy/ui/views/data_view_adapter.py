"""
data_view_adapter.py

Description: Adapter to integrate the existing DataView with the new BaseView structure
Usage:
    data_view = DataViewAdapter(data_model)
    data_view.set_controller(data_view_controller)
    main_window.add_view(data_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout
import time
import logging

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.utils import get_update_manager

# Set up logger
logger = logging.getLogger(__name__)


class DataViewAdapter(UpdatableView):
    """
    Adapter that wraps the existing DataView component to integrate with the new UI structure.

    Attributes:
        data_model (ChestDataModel): The data model containing chest data
        data_view (DataView): The wrapped DataView instance
        _controller (DataViewController): The controller for data view operations

    Signals:
        import_requested: Emitted when user requests data import
        export_requested: Emitted when user requests data export

    Implementation Notes:
        - Inherits from UpdatableView to maintain UI consistency and use standardized update patterns
        - Wraps the existing DataView component
        - Uses DataViewController for business logic operations
        - Provides the same functionality as DataView but with the new UI styling
        - Uses UpdateManager for scheduling updates
    """

    # Define signals with consistent naming
    import_requested = Signal()
    export_requested = Signal()

    def __init__(
        self, data_model: ChestDataModel, parent: QWidget = None, debug_mode: bool = False
    ):
        """
        Initialize the DataViewAdapter.

        Args:
            data_model (ChestDataModel): The data model to display
            parent (QWidget, optional): The parent widget. Defaults to None.
            debug_mode (bool, optional): Enable debug mode for signal connections. Defaults to False.
        """
        # Store references
        self._data_model = data_model
        self._controller = None

        # State tracking to prevent unnecessary refreshes
        self._last_data_state = {
            "row_count": 0,
            "column_count": 0,
            "data_hash": self._data_model.data_hash
            if hasattr(self._data_model, "data_hash")
            else "",
            "last_update_time": 0,
        }

        # Flag to track if the table needs population when shown
        self._needs_population = False

        # Create the underlying DataView
        self._data_view = DataView(data_model)

        # Initialize the base view with debug mode option
        super().__init__("Data View", parent, debug_mode=debug_mode)
        self.setObjectName("DataViewAdapter")

    def set_controller(self, controller: DataViewController) -> None:
        """
        Set the data view controller for this adapter.

        Args:
            controller: The DataViewController instance to use
        """
        self._controller = controller

        # Register this view with the controller
        if self._controller:
            self._controller.set_view(self)

            # Connect controller signals
            self._connect_controller_signals()

            logger.info("DataViewAdapter: Controller set and signals connected")

    @property
    def needs_population(self) -> bool:
        """Get whether the view needs table population when shown."""
        return self._needs_population

    @needs_population.setter
    def needs_population(self, value: bool) -> None:
        """Set whether the view needs table population when shown."""
        self._needs_population = value

    def _update_view_content(self, data=None) -> None:
        """
        Update the view content with current data.

        This implementation updates the DataView with current model data.

        Args:
            data: Optional data to use for update (unused in this implementation)
        """
        if hasattr(self._data_view, "_update_view"):
            self._data_view._update_view()

        # Update our state tracking
        self._update_data_state()
        logger.debug(f"DataViewAdapter: View content updated")

    def _refresh_view_content(self) -> None:
        """
        Refresh the view content without changing the underlying data.
        """
        if hasattr(self._data_view, "_update_view"):
            self._data_view._update_view()

        logger.debug(f"DataViewAdapter: View content refreshed")

    def _populate_view_content(self, data=None) -> None:
        """
        Populate the view content from scratch.

        This implementation calls the populate_table method to fully populate the table.

        Args:
            data: Optional data to use for population (unused in this implementation)
        """
        self.populate_table()
        logger.debug(f"DataViewAdapter: View content populated")

    def _reset_view_content(self) -> None:
        """
        Reset the view content to its initial state.
        """
        if hasattr(self._data_view, "_table_widget"):
            self._data_view._table_widget.clearContents()
            self._data_view._table_widget.setRowCount(0)

        self._last_data_state = {
            "row_count": 0,
            "column_count": 0,
            "data_hash": "",
            "last_update_time": 0,
        }

        logger.debug(f"DataViewAdapter: View content reset")

    def _setup_ui(self):
        """Set up the UI components."""
        # First call the parent class's _setup_ui method
        super()._setup_ui()

        # Add the DataView to the content widget
        self.get_content_layout().addWidget(self._data_view)

    def _connect_signals(self):
        """Connect signals and slots using standardized pattern."""
        # First call the parent class's _connect_signals method
        super()._connect_signals()

        # Connect UI signals
        try:
            self._connect_ui_signals()
        except Exception as e:
            logger.error(f"Error connecting UI signals in DataViewAdapter: {e}")

        # Connect model signals if model exists
        if self._data_model:
            self._connect_model_signals()

    def _connect_ui_signals(self):
        """Connect UI component signals using safe connection pattern."""
        # Get action toolbar from DataView
        import_button = self._data_view._action_toolbar.get_button_by_name("import")
        export_button = self._data_view._action_toolbar.get_button_by_name("export")
        filter_button = self._data_view._action_toolbar.get_button_by_name("apply_filter")
        clear_filter_button = self._data_view._action_toolbar.get_button_by_name("clear_filter")

        # Connect buttons with safe_connect and disconnect_first for safety
        if import_button:
            self._signal_manager.safe_connect(
                import_button, "clicked", self, "_on_import_requested", True
            )

        if export_button:
            self._signal_manager.safe_connect(
                export_button, "clicked", self, "_on_export_requested", True
            )

        if filter_button and self._controller:
            self._signal_manager.safe_connect(
                filter_button, "clicked", self, "_on_apply_filter_clicked", True
            )

        if clear_filter_button and self._controller:
            self._signal_manager.safe_connect(
                clear_filter_button, "clicked", self, "_on_clear_filter_clicked", True
            )

        # Connect header action signals
        self._signal_manager.safe_connect(
            self, "header_action_clicked", self, "_on_header_action_clicked"
        )

    def _connect_controller_signals(self):
        """Connect controller signals using safe connection pattern."""
        if not self._controller:
            return

        try:
            # Standard operation signals
            self._signal_manager.safe_connect(
                self._controller, "validation_started", self, "_on_validation_started"
            )
            self._signal_manager.safe_connect(
                self._controller, "validation_completed", self, "_on_validation_completed"
            )
            self._signal_manager.safe_connect(
                self._controller, "correction_started", self, "_on_correction_started"
            )
            self._signal_manager.safe_connect(
                self._controller, "correction_completed", self, "_on_correction_completed"
            )
            self._signal_manager.safe_connect(
                self._controller, "operation_error", self, "_on_operation_error"
            )
            self._signal_manager.safe_connect(
                self._controller, "table_populated", self, "_on_table_populated"
            )

            # Data change signal from controller
            self._signal_manager.safe_connect(
                self._controller, "data_changed", self, "_on_data_changed"
            )
        except Exception as e:
            logger.error(f"Error connecting controller signals in DataViewAdapter: {e}")

    def _connect_model_signals(self):
        """Connect model signals using safe connection pattern."""
        try:
            if hasattr(self._data_model, "data_changed"):
                self._signal_manager.safe_connect(
                    self._data_model, "data_changed", self, "_on_data_changed", True
                )
        except Exception as e:
            logger.error(f"Error connecting model signals in DataViewAdapter: {e}")

    def _on_import_requested(self):
        """Handle import button click."""
        self.import_requested.emit()

    def _on_export_requested(self):
        """Handle export button click."""
        self.export_requested.emit()

    @Slot(str)
    def _on_header_action_clicked(self, action_id: str):
        """
        Handle header action button clicks.

        Args:
            action_id (str): The ID of the action button clicked
        """
        logger.debug(f"Header action clicked: {action_id}")
        # Handle specific actions as needed

    def _on_apply_filter_clicked(self):
        """Handle filter button click using controller."""
        if self._controller:
            # Get filter parameters from the data view
            filter_text = ""
            column = ""

            if hasattr(self._data_view, "_filter_bar"):
                filter_text = self._data_view._filter_bar.get_filter_text()
                column = self._data_view._filter_bar.get_selected_column()

            # Apply filter using controller
            self._controller.apply_filter(column, filter_text)

    def _on_clear_filter_clicked(self):
        """Handle clear filter button click using controller."""
        if self._controller:
            self._controller.clear_filter()

    @Slot()
    def _on_validation_started(self):
        """Handle validation started event."""
        # Update UI to show validation in progress
        if hasattr(self, "_set_header_status"):
            self._set_header_status("Validating data...")

    @Slot(object)
    def _on_validation_completed(self, results):
        """Handle validation completed event."""
        # Update UI to show validation results
        if hasattr(self, "_set_header_status"):
            issue_count = len(results) if results else 0
            self._set_header_status(f"Validation complete: {issue_count} issues found")

    @Slot()
    def _on_correction_started(self):
        """Handle correction started event."""
        # Update UI to show correction in progress
        if hasattr(self, "_set_header_status"):
            self._set_header_status("Applying corrections...")

    @Slot(str, int)
    def _on_correction_completed(self, strategy, affected_rows):
        """Handle correction completed event."""
        # Update UI to show correction results
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Corrections applied: {affected_rows} rows affected")

    @Slot(str)
    def _on_operation_error(self, error_message):
        """Handle operation error event."""
        # Update UI to show error
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Error: {error_message}")

    @Slot(int)
    def _on_table_populated(self, row_count):
        """Handle table populated event."""
        # Update UI to show table populated
        if hasattr(self, "_set_header_status"):
            self._set_header_status(f"Data loaded: {row_count} rows")

    def _add_action_buttons(self):
        """Add action buttons to the header."""
        # We'll not add our own action buttons since the DataView already has them
        # in its ActionToolbar
        pass

    def _on_data_changed(self):
        """Handle data model changes."""
        logger.debug("DataViewAdapter: Data model changed, requesting update")
        # Use the standardized update mechanism instead of direct update
        self.request_update()

    def _update_data_state(self):
        """Update our tracking of the data state to detect changes."""
        current_state = {"row_count": 0, "column_count": 0, "data_hash": ""}

        if not self._data_model.is_empty:
            current_state = {
                "row_count": len(self._data_model.data),
                "column_count": len(self._data_model.column_names),
                "data_hash": self._data_model.data_hash
                if hasattr(self._data_model, "data_hash")
                else "",
            }

        # Update state tracking
        self._last_data_state.update(current_state)
        self._last_data_state["last_update_time"] = time.time()

    def needs_update(self) -> bool:
        """
        Check if the view needs updating based on data state.

        Returns:
            bool: True if the view needs to be updated, False otherwise
        """
        # Check if data has changed by comparing with our tracked state
        current_state = {"row_count": 0, "column_count": 0, "data_hash": ""}

        if not self._data_model.is_empty:
            current_state = {
                "row_count": len(self._data_model.data),
                "column_count": len(self._data_model.column_names),
                "data_hash": self._data_model.data_hash
                if hasattr(self._data_model, "data_hash")
                else "",
            }

        needs_refresh = (
            current_state["row_count"] != self._last_data_state["row_count"]
            or current_state["column_count"] != self._last_data_state["column_count"]
            or current_state["data_hash"] != self._last_data_state["data_hash"]
        )

        if needs_refresh:
            logger.debug(
                f"DataViewAdapter.needs_update: TRUE - Data changed. Old: {self._last_data_state}, New: {current_state}"
            )
        else:
            logger.debug(f"DataViewAdapter.needs_update: FALSE - No data changes detected")

        return needs_refresh or super().needs_update()

    def refresh(self):
        """
        Refresh the data view only if the data has changed since the last refresh.
        This prevents unnecessary table repopulation when switching views.
        """
        logger.debug("DataViewAdapter.refresh: Using UpdateManager for refresh")
        # Use the UpdateManager to schedule a refresh
        try:
            self.schedule_update()
        except Exception as e:
            logger.error(f"Error scheduling update via UpdateManager: {e}")
            # Fall back to direct refresh if UpdateManager is not available
            if self.needs_update():
                self._update_view_content()

    def populate_table(self) -> None:
        """
        Populate the table with data from the model.
        This is used for initial population and when data changes completely.
        """
        try:
            if self._controller and not self._data_model.is_empty:
                logger.debug("DataViewAdapter: Populating table via controller")
                self._controller.populate_table()
            else:
                logger.debug("DataViewAdapter: Skipping population (no controller or empty data)")

            # Update our state tracking
            self._update_data_state()
            self._needs_population = False
        except Exception as e:
            logger.error(f"Error populating table: {e}")

    def enable_auto_update(self) -> None:
        """Enable automatic updates when data changes."""
        logger.debug("DataViewAdapter: Auto-update enabled")
        # Connect to data model changes to trigger updates via UpdateManager
        if self._data_model and hasattr(self._data_model, "data_changed"):
            self._signal_manager.connect(self._data_model, "data_changed", self, "request_update")

    def disable_auto_update(self) -> None:
        """Disable automatic updates when data changes."""
        logger.debug("DataViewAdapter: Auto-update disabled")
        # Disconnect from data model changes
        if self._data_model and hasattr(self._data_model, "data_changed"):
            self._signal_manager.disconnect(
                self._data_model, "data_changed", self, "request_update"
            )
