"""
data_view_adapter.py

Description: Adapter to integrate the existing DataView with the new BaseView structure
Usage:
    data_view = DataViewAdapter(data_model)
    data_view.set_controller(data_view_controller)
    main_window.add_view(data_view)
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
import time
import logging
from typing import Optional

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.data_view import DataView
from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.utils import get_update_manager
from chestbuddy.utils.signal_manager import SignalManager

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
        correction_selected: Emitted when a correction is selected

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
    correction_selected = Signal(int, int, object)

    def __init__(
        self,
        data_model: Optional[ChestDataModel] = None,
        controller: Optional[DataViewController] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the DataViewAdapter.

        Args:
            data_model: The data model
            controller: The data view controller
            parent: The parent widget
        """
        # Store adapter-specific settings
        self._data_model = data_model
        self._controller = controller
        self._update_manager = None
        self._needs_population = False
        self._last_data_state = {
            "row_count": 0,
            "column_count": 0,
            "data_hash": "",
            "last_update_time": 0,
        }
        self._signal_manager = SignalManager(debug_mode=True)

        # Create DataView first before initializing inherited view
        try:
            if data_model is None:
                logger.warning("DataViewAdapter created with no data model")

            logger.debug("Creating DataView instance")
            self._data_view = DataView(data_model=data_model)
            # We track the DataView instance with a unique ID to help debug multiple instances
            self._data_view_id = id(self._data_view)
            logger.debug(f"Created DataView instance with ID: {self._data_view_id}")

            # Initialize the BaseView with a title
            super().__init__(title="Data View", parent=parent)

            # Set up the adapter
            self._setup_adapted_view()
            self._connect_signals()

            # Get update manager if available
            self._try_get_update_manager()

            # Connect controller signals if controller provided
            if controller:
                self._connect_controller_signals()
                logger.debug("Connected to controller signals")

            # Connect data model signals
            if data_model:
                self._connect_model_signals()
                logger.debug("Connected to data model signals")

            # Disable update handling temporarily during initialization
            was_enabled = False
            if hasattr(self, "disable_auto_update"):
                was_enabled = True
                self.disable_auto_update()

            # Populate the table if we have data
            if data_model and not data_model.is_empty:
                self._needs_population = True
                if hasattr(self, "request_update"):
                    self.request_update()

            # Re-enable update handling if it was previously enabled
            if was_enabled and hasattr(self, "enable_auto_update"):
                self.enable_auto_update()

            # As a last resort, if the content widget doesn't contain the DataView,
            # directly make it the central widget
            if hasattr(self, "centralWidget") and self._data_view.parent() is None:
                logger.info("FALLBACK: Setting DataView as central widget of adapter")
                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self._data_view)

                central_widget = QWidget()
                central_widget.setLayout(layout)
                self.setCentralWidget(central_widget)

            logger.info("DataViewAdapter initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DataViewAdapter: {e}")
            import traceback

            logger.error(traceback.format_exc())

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

    def set_table_state_manager(self, manager) -> None:
        """
        Set the table state manager and pass it to the wrapped DataView.

        Args:
            manager: The TableStateManager instance
        """
        # Store the reference at the adapter level
        self._table_state_manager = manager

        # Pass it to the wrapped DataView if available
        if hasattr(self._data_view, "set_table_state_manager"):
            self._data_view.set_table_state_manager(manager)
            logger.info("TableStateManager passed to wrapped DataView")
        else:
            logger.warning("DataView does not implement set_table_state_manager method")

        # Connect to the TableStateManager's state_changed signal if it exists
        if manager and hasattr(manager, "state_changed"):
            try:
                # Connect to state changes
                self._signal_manager.connect(
                    manager, "state_changed", self, "_on_table_state_changed"
                )
                logger.info("Connected to TableStateManager's state_changed signal")
            except Exception as e:
                logger.error(f"Error connecting to TableStateManager signals: {e}")
                import traceback

                logger.error(traceback.format_exc())

    @Slot(set)
    def _on_table_state_changed(self, changed_cells: set):
        """Handle state changes in the TableStateManager."""
        logger.debug(f"TableStateManager state changed for {len(changed_cells)} cells.")

        # Forward to the DataView if it has the update_cell_highlighting_from_state method
        if hasattr(self._data_view, "update_cell_highlighting_from_state"):
            logger.debug("Forwarding table state change to DataView")
            self._data_view.update_cell_highlighting_from_state()

        # Also update tooltips if the method exists
        if hasattr(self._data_view, "update_tooltips_from_state"):
            logger.debug("Updating tooltips from state")
            self._data_view.update_tooltips_from_state()

        # Request an update to refresh the view
        self.request_update()

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
        try:
            # Check if we need full population
            if self._needs_population and hasattr(self._data_view, "populate_table"):
                logger.debug("DataViewAdapter: View needs population, calling populate_table")
                self._data_view.populate_table()
                self._needs_population = False
            # Otherwise just update the view
            elif hasattr(self._data_view, "_update_view"):
                logger.debug("DataViewAdapter: Updating view")
                self._data_view._update_view()

            # Update our state tracking
            self._update_data_state()
            logger.debug("DataViewAdapter: View content updated")
        except Exception as e:
            logger.error(f"Error updating view content: {e}")

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
        try:
            # Check if population is already in progress in the underlying DataView
            if (
                hasattr(self._data_view, "_population_in_progress")
                and self._data_view._population_in_progress
            ):
                logger.debug(
                    "DataViewAdapter: Skipping population (already in progress in DataView)"
                )
                return

            # First try using the controller
            if self._controller and not self._data_model.is_empty:
                logger.debug("DataViewAdapter: Populating table via controller")
                self._controller.populate_table()
            # If controller didn't work, call directly on the DataView
            elif hasattr(self._data_view, "populate_table") and not self._data_model.is_empty:
                logger.debug("DataViewAdapter: Directly calling populate_table on DataView")
                self._data_view.populate_table()
            else:
                logger.debug("DataViewAdapter: Skipping population (no controller or empty data)")

            # Update our state tracking
            self._update_data_state()
            self._needs_population = False
            logger.debug("DataViewAdapter: View content populated")
        except Exception as e:
            logger.error(f"Error populating view content: {e}")
            # Reset the needs_population flag even on error to avoid getting stuck
            self._needs_population = False

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

    def _setup_adapted_view(self) -> None:
        """Set up the adapted view in the content area."""
        try:
            # Get the content widget
            content_widget = self.get_content_widget()
            if not content_widget:
                logger.error("Cannot set up adapted view: content widget is not available")
                return

            # Clear any existing layout to prevent the "widget already has a layout" error
            if content_widget.layout():
                logger.debug("Removing existing layout from content widget")
                existing_layout = content_widget.layout()
                # Remove all widgets from the existing layout
                while existing_layout and existing_layout.count():
                    item = existing_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                # Safely delete the old layout
                QWidget().setLayout(existing_layout)

            # Create a new layout
            layout = QVBoxLayout(content_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Check if the DataView exists and is valid
            if not hasattr(self, "_data_view") or self._data_view is None:
                logger.error("Cannot set up adapted view: DataView is not available")
                error_label = QLabel("Error: Data view not available")
                error_label.setStyleSheet("color: red; padding: 20px;")
                layout.addWidget(error_label)
                return

            logger.debug(f"Setting up DataView (ID: {self._data_view_id}) in adapter")

            # Ensure DataView is visible and has correct parent
            self._data_view.setVisible(True)
            self._data_view.setParent(content_widget)

            # Disable the data view's auto-update to prevent double updates
            if hasattr(self._data_view, "disable_auto_update"):
                self._data_view.disable_auto_update()
                logger.info("DataView auto-update disabled")

            # Add the data view to the layout with stretch
            layout.addWidget(self._data_view, 1)  # Add with stretch to fill the available space
            logger.debug("Added DataView to adapter's layout with stretch")

            # Force layout update
            content_widget.setLayout(layout)
            content_widget.updateGeometry()

            # Verify layout setup
            if layout.count() == 0:
                logger.warning("DataView was not added to layout - layout is empty")
            else:
                logger.debug(f"Layout has {layout.count()} widgets")
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    logger.debug(f"Widget {i} type: {type(widget).__name__}, ID: {id(widget)}")

            # Set title
            self.set_title("Data View")
            self.setObjectName("DataViewAdapter")
        except Exception as e:
            logger.error(f"Error setting up adapted view: {e}")
            import traceback

            logger.error(traceback.format_exc())

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
        """Connect signals from the wrapped DataView UI components."""
        if not self._data_view:
            logger.error("Cannot connect UI signals: DataView is not initialized.")
            return

        logger.debug(f"Connecting UI signals for DataView ID: {self._data_view_id}")

        # Connect import/export buttons
        if hasattr(self._data_view, "import_button") and hasattr(
            self._data_view.import_button, "clicked"
        ):
            self._signal_manager.connect(
                self._data_view.import_button, "clicked", self, "_on_import_requested"
            )

        if hasattr(self._data_view, "export_button") and hasattr(
            self._data_view.export_button, "clicked"
        ):
            self._signal_manager.connect(
                self._data_view.export_button, "clicked", self, "_on_export_requested"
            )

        # Relay the correction_selected signal from the actual DataView/delegate
        if hasattr(self._data_view, "correction_selected"):
            self._signal_manager.connect(
                self._data_view,  # Source is the wrapped DataView
                "correction_selected",
                self.correction_selected,  # Target is the adapter's own signal
            )
            logger.info("Relaying correction_selected signal from DataView to DataViewAdapter")
        else:
            logger.warning("Wrapped DataView does not have a correction_selected signal to relay.")

        # Connect filter buttons using signal manager
        filter_button = self._data_view._action_toolbar.get_button_by_name("apply_filter")
        clear_filter_button = self._data_view._action_toolbar.get_button_by_name("clear_filter")

        if filter_button and self._controller:
            self._signal_manager.safe_connect(
                filter_button, "clicked", self, "_on_apply_filter_clicked"
            )

        if clear_filter_button and self._controller:
            self._signal_manager.safe_connect(
                clear_filter_button, "clicked", self, "_on_clear_filter_clicked"
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
                    self._data_model, "data_changed", self, "_on_data_changed"
                )

            # Connect to validation_changed signal for validation updates
            if hasattr(self._data_model, "validation_changed"):
                self._signal_manager.safe_connect(
                    self._data_model, "validation_changed", self, "_on_validation_changed"
                )
                logger.debug("Connected to validation_changed signal")

            # Connect to correction_applied signal for correction updates
            if hasattr(self._data_model, "correction_applied"):
                self._signal_manager.safe_connect(
                    self._data_model, "correction_applied", self, "_on_correction_applied"
                )
                logger.debug("Connected to correction_applied signal")
        except Exception as e:
            logger.error(f"Error connecting model signals in DataViewAdapter: {e}")

    def _on_import_requested(self):
        """Handle import button click."""
        # Simply emit the signal to be handled by MainWindow
        self.import_requested.emit()

    def _on_export_requested(self):
        """Handle export button click."""
        # Simply emit the signal to be handled by MainWindow
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

        # Forward to the underlying DataView if it has the appropriate method
        if hasattr(self._data_view, "_on_validation_changed"):
            logger.debug("Forwarding validation results to DataView from controller")
            self._data_view._on_validation_changed(results)

        # Request an update to refresh the view
        self.request_update()

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

        # Forward to the underlying DataView if it has the appropriate method
        if hasattr(self._data_view, "_on_correction_applied"):
            logger.debug("Forwarding correction results to DataView from controller")
            # Create a correction status object that DataView can process
            correction_status = {"strategy": strategy, "affected_rows": affected_rows}
            self._data_view._on_correction_applied(correction_status)

        # Request an update to refresh the view
        self.request_update()

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

    @Slot(object)
    def _on_data_changed(self, data_state=None):
        """
        Handle data model changes.

        Args:
            data_state: The DataState object containing information about the change
        """
        try:
            logger.debug("DataViewAdapter: Data model changed, requesting update")

            # Mark as needing population
            self._needs_population = True

            # Don't try to access has_data on data_state since it might not exist
            # Always force population if the data model has data
            if self._data_model and not self._data_model.is_empty:
                logger.debug("DataViewAdapter: Data model has data, forcing population")
                # Direct population as most reliable method
                if hasattr(self._data_view, "populate_table"):
                    logger.debug("DataViewAdapter: Directly calling populate_table on DataView")
                    self._data_view.populate_table()
                    self._needs_population = False

            # Use the standardized update mechanism as backup
            self.request_update()
        except Exception as e:
            logger.error(f"Error handling data changed in DataViewAdapter: {e}")
            import traceback

            logger.error(traceback.format_exc())

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
            logger.info("DataViewAdapter.populate_table: Directly populating DataView")

            # Skip checks and directly call populate_table on DataView
            if hasattr(self._data_view, "populate_table"):
                logger.info(f"Calling populate_table on DataView ID: {id(self._data_view)}")
                self._data_view.populate_table()
                logger.info("DataView.populate_table called successfully")

                # Force the DataView to be visible
                self._data_view.setVisible(True)

                # If there's a parent QWidget, make sure it's also visible
                if self._data_view.parent():
                    self._data_view.parent().setVisible(True)

                # Update our state tracking
                self._update_data_state()
                self._needs_population = False
                logger.info("Table population completed successfully")
            else:
                logger.error("DataView doesn't have populate_table method")
        except Exception as e:
            logger.error(f"Error in DataViewAdapter.populate_table: {e}")
            import traceback

            logger.error(traceback.format_exc())

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

    def _on_validation_changed(self, validation_status=None):
        """
        Handle validation status changes in the data model.

        Args:
            validation_status (pd.DataFrame, optional): The validation status DataFrame.
                If None, will try to get it from the data_model.
        """
        logger.debug(
            f"DataViewAdapter: _on_validation_changed called with status: {validation_status}"
        )

        # If no validation_status is provided, try to get it from the data model
        if validation_status is None and hasattr(self._data_model, "get_validation_status"):
            try:
                validation_status = self._data_model.get_validation_status()
                logger.debug(
                    f"Retrieved validation status from model: shape {validation_status.shape if validation_status is not None else 'None'}"
                )
            except Exception as e:
                logger.error(f"Error getting validation status from model: {e}")

        # Make sure to update the underlying DataView with validation changes
        if hasattr(self._data_view, "_on_validation_changed"):
            logger.debug("Forwarding validation status to DataView")
            self._data_view._on_validation_changed(validation_status)

        # Request update from the UpdateManager
        self.request_update()
        logger.debug("Handled validation changed signal")

    def _on_correction_applied(self, correction_status=None):
        """
        Handle correction status changes in the data model.

        Args:
            correction_status: The correction status information.
                If None, will try to get current correction status from the data_model.
        """
        logger.debug(
            f"DataViewAdapter: _on_correction_applied called with status: {correction_status}"
        )

        # If no correction_status is provided, try to get it from the data model if possible
        if correction_status is None and hasattr(self._data_model, "get_correction_status"):
            try:
                correction_status = self._data_model.get_correction_status()
                logger.debug(f"Retrieved correction status from model: {correction_status}")
            except Exception as e:
                logger.error(f"Error getting correction status from model: {e}")

        # Forward to the underlying DataView
        if hasattr(self._data_view, "_on_correction_applied"):
            logger.debug("Forwarding correction status to DataView")
            self._data_view._on_correction_applied(correction_status)

        # Request update from the UpdateManager
        self.request_update()
        logger.debug("Handled correction applied signal")

    def _try_get_update_manager(self):
        """Try to get the update manager from utils, if available."""
        try:
            self._update_manager = get_update_manager()
            logger.debug("Successfully retrieved update manager")
        except Exception as e:
            logger.debug(f"Could not get update manager: {e}")
            self._update_manager = None
