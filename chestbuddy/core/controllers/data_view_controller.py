"""
data_view_controller.py

Description: Controller for data view operations in the ChestBuddy application
Usage:
    controller = DataViewController(data_model)
    controller.filter_data("Player Name", "Player1", "Contains", False)
"""

import logging
import time
from typing import Dict, Optional, Any, Tuple, List

from PySide6.QtCore import QObject, Signal, Slot, QModelIndex
import pandas as pd

from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService
from chestbuddy.core.controllers.base_controller import BaseController
from chestbuddy.utils.service_locator import ServiceLocator

# Set up logger
logger = logging.getLogger(__name__)


class DataViewController(BaseController):
    """
    Controller for data view operations in ChestBuddy.

    This class handles data filtering, sorting, and table population,
    coordinating between the data model and UI components.

    Attributes:
        filter_applied (Signal): Emitted when a filter is applied
        sort_applied (Signal): Emitted when sort is applied
        table_populated (Signal): Emitted when the table is populated
        operation_error (Signal): Emitted when an error occurs
        validation_started (Signal): Emitted when validation starts
        validation_completed (Signal): Emitted when validation completes
        validation_error (Signal): Emitted when validation fails
        correction_started (Signal): Emitted when correction starts
        correction_completed (Signal): Emitted when correction completes
        correction_error (Signal): Emitted when correction fails
        operation_started (Signal): Emitted when an operation starts
        operation_completed (Signal): Emitted when an operation completes
        chart_created (Signal): Emitted when a chart is created
    """

    # Define signals
    filter_applied = Signal(dict)  # Filter parameters
    sort_applied = Signal(str, bool)  # Column, ascending
    table_populated = Signal(int)  # Number of rows
    operation_error = Signal(str)
    validation_started = Signal()
    validation_completed = Signal(dict)  # Results
    validation_error = Signal(str)
    correction_started = Signal()
    correction_completed = Signal(dict)  # Results
    correction_error = Signal(str)
    operation_started = Signal(str)  # Operation name
    operation_completed = Signal(str)  # Operation name
    chart_created = Signal(object)  # Chart data

    def __init__(self, data_model, signal_manager=None, ui_state_controller=None):
        """
        Initialize the data view controller.

        Args:
            data_model: The data model to control
            signal_manager: Optional SignalManager instance for connection tracking
            ui_state_controller: Optional UIStateController for UI state updates
        """
        super().__init__(signal_manager)
        self._data_model = data_model
        self._current_filters = {}
        self._current_sort_column = None
        self._current_sort_ascending = True
        self._ui_state_controller = ui_state_controller

        # Connect to model signals
        self.connect_to_model(data_model)

        # Connect to UI state controller if provided
        if self._ui_state_controller:
            self._connect_to_ui_state_controller()

        logger.debug("DataViewController initialized")

    def connect_to_model(self, model):
        """
        Connect to data model signals.

        Args:
            model: The data model to connect to
        """
        super().connect_to_model(model)

        # Connect to model signals using signal manager
        if hasattr(model, "data_changed"):
            self._signal_manager.connect(model, "data_changed", self, "_on_data_changed")

        if hasattr(model, "validation_complete"):
            self._signal_manager.connect(
                model, "validation_complete", self, "_on_validation_complete"
            )

        logger.debug(f"DataViewController connected to model: {model.__class__.__name__}")

    def connect_to_view(self, view):
        """
        Connect to view signals.

        Args:
            view: The view to connect to
        """
        super().connect_to_view(view)

        # Connect to view signals using signal manager
        if hasattr(view, "filter_changed"):
            self._signal_manager.connect(view, "filter_changed", self, "_on_filter_changed")

        if hasattr(view, "sort_changed"):
            self._signal_manager.connect(view, "sort_changed", self, "_on_sort_changed")

        if hasattr(view, "selection_changed"):
            self._signal_manager.connect(view, "selection_changed", self, "_on_selection_changed")

        if hasattr(view, "validate_requested"):
            self._signal_manager.connect(view, "validate_requested", self, "_on_validate_requested")

        if hasattr(view, "correct_requested"):
            self._signal_manager.connect(view, "correct_requested", self, "_on_correct_requested")

        # Connect to data correction signal for validation list additions
        if hasattr(view, "data_corrected"):
            self._signal_manager.connect(view, "data_corrected", self, "_on_data_corrected")

        logger.debug(f"DataViewController connected to view: {view.__class__.__name__}")

    def set_view(self, view):
        """
        Set the data view for this controller.

        Args:
            view: The data view component
        """
        logger.debug(
            f"=== DataViewController.set_view called with view of type: {type(view).__name__} ==="
        )
        logger.debug(f"View instance ID: {id(view)}")

        # Check if we already have a view
        if hasattr(self, "_view") and self._view is not None:
            old_view_id = id(self._view)
            logger.warning(
                f"Replacing existing view (ID: {old_view_id}) with new view (ID: {id(view)})"
            )

            # Check if the view types match
            if type(self._view) != type(view):
                logger.warning(
                    f"View type changing from {type(self._view).__name__} to {type(view).__name__}"
                )

            # Disconnect from old view if needed
            if hasattr(self, "_disconnect_from_view"):
                try:
                    self._disconnect_from_view(self._view)
                    logger.debug("Disconnected from old view")
                except Exception as e:
                    logger.error(f"Error disconnecting from old view: {e}")

        # Store the view reference
        self._view = view

        # Check for DataView within DataViewAdapter
        if hasattr(view, "_data_view") and view._data_view:
            logger.debug(f"View contains internal DataView with ID: {id(view._data_view)}")

            # Log TableStateManager status on DataView
            if hasattr(view._data_view, "_table_state_manager"):
                tsm = view._data_view._table_state_manager
                logger.debug(
                    f"Internal DataView has TableStateManager: {tsm is not None}, ID: {id(tsm) if tsm else 'None'}"
                )
            else:
                logger.debug("Internal DataView does not have _table_state_manager attribute")

        # Connect view signals if available
        if hasattr(view, "_action_toolbar"):
            logger.debug("View has _action_toolbar, connecting buttons")
            if hasattr(view._action_toolbar, "get_button_by_name"):
                filter_button = view._action_toolbar.get_button_by_name("apply_filter")
                clear_button = view._action_toolbar.get_button_by_name("clear_filter")

                if filter_button and hasattr(filter_button, "clicked"):
                    filter_button.clicked.connect(self._handle_filter_button_clicked)
                    logger.debug("Connected to filter button click")

                if clear_button and hasattr(clear_button, "clicked"):
                    clear_button.clicked.connect(self._handle_clear_filter_button_clicked)
                    logger.debug("Connected to clear filter button click")
            else:
                logger.debug("Action toolbar doesn't have get_button_by_name method")
        else:
            logger.debug("View does not have _action_toolbar attribute")

        # Connect to view signals
        self.connect_to_view(view)
        logger.debug("Connected to view signals through connect_to_view method")

    def set_services(self, validation_service=None, correction_service=None):
        """
        Set or update the validation and correction services.

        Args:
            validation_service: The validation service to use
            correction_service: The correction service to use
        """
        if validation_service:
            self._validation_service = validation_service

        if correction_service:
            self._correction_service = correction_service

        # Reconnect signals with new services
        self._connect_signals()

        logger.info("Validation and correction services updated")

    def _connect_signals(self):
        """
        Connect signals between the controller and services.

        Establishes signal connections between:
        - ValidationService and this controller
        - CorrectionService and this controller
        """
        # Connect ValidationService signals if available
        if hasattr(self, "_validation_service") and self._validation_service:
            # Connect validation_preferences_changed to validate_data
            self._signal_manager.connect(
                self._validation_service, "validation_preferences_changed", self, "validate_data"
            )
            logger.debug("Connected ValidationService signals to DataViewController")

        # Note: CorrectionService doesn't emit signals directly that the controller needs to listen to
        # But we can log that services are connected
        if hasattr(self, "_correction_service") and self._correction_service:
            logger.debug("CorrectionService connected to DataViewController")

    @Slot()
    def _handle_filter_button_clicked(self):
        """Handle the filter button clicked in the view."""
        if not self._view:
            return

        try:
            # Get filter parameters from view
            column = self._view._filter_column.currentText()
            filter_text = self._view._filter_text.text()
            filter_mode = self._view._filter_mode.currentText()
            case_sensitive = self._view._case_sensitive.isChecked()

            # Apply filter
            self.filter_data(column, filter_text, filter_mode, case_sensitive)
        except Exception as e:
            logger.error(f"Error handling filter button click: {e}")
            self.operation_error.emit(f"Error applying filter: {str(e)}")

    @Slot()
    def _handle_clear_filter_button_clicked(self):
        """Handle the clear filter button clicked in the view."""
        self.clear_filter()

    @Slot(object)
    def _on_data_changed(self, data_state=None):
        """
        Handle data model changes.

        Args:
            data_state: The current DataState (optional)
        """
        # Update our state tracking
        self._update_data_state()

    def _update_data_state(self):
        """Update the state tracking with current data model state."""
        try:
            if not self._data_model.is_empty:
                self._last_data_state = {
                    "row_count": len(self._data_model.data),
                    "column_count": len(self._data_model.column_names),
                    "data_hash": self._data_model.data_hash
                    if hasattr(self._data_model, "data_hash")
                    else "",
                    "last_update_time": int(time.time() * 1000),
                }
            else:
                self._last_data_state = {
                    "row_count": 0,
                    "column_count": 0,
                    "data_hash": "",
                    "last_update_time": int(time.time() * 1000),
                }
        except Exception as e:
            logger.error(f"Error updating data state: {e}")

    def filter_data(self, column: str, value: str, mode: str, case_sensitive: bool) -> bool:
        """
        Filter the data based on the specified criteria.

        Args:
            column: Column to filter on
            value: Filter value
            mode: Filter mode (contains, equals, etc.)
            case_sensitive: Whether to use case-sensitive filtering

        Returns:
            bool: Success status
        """
        try:
            if self._data_model.is_empty:
                logger.warning("Cannot filter: Data model is empty")
                return False

            if not column or column not in self._data_model.column_names:
                logger.warning(f"Invalid filter column: {column}")
                self.operation_error.emit(f"Invalid filter column: {column}")
                return False

            # Apply filter to data model
            filtered_data = self._data_model.filter_data(column, value, mode, case_sensitive)

            if filtered_data is None:
                logger.error(f"Failed to apply filter to column '{column}'")
                self.operation_error.emit(f"Failed to apply filter to column '{column}'")
                return False

            # Store filtered data
            self._filtered_data = filtered_data

            # Save current filter
            self._current_filters = {
                "column": column,
                "text": value,
                "mode": mode,
                "case_sensitive": case_sensitive,
            }

            # Update view if attached
            if self._view and hasattr(self._view, "_update_view_with_filtered_data"):
                self._view._update_view_with_filtered_data(filtered_data)

                # Update status label if exists
                if hasattr(self._view, "_status_label"):
                    row_count = len(filtered_data)
                    total_count = len(self._data_model.data)
                    self._view._status_label.setText(f"Showing {row_count} of {total_count} rows")

            # Emit filter applied signal
            self.filter_applied.emit(self._current_filters)

            logger.info(
                f"Filter applied: {column}={value} ({mode}), showing {len(filtered_data)} of {len(self._data_model.data)} rows"
            )
            return True

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            self.operation_error.emit(f"Error applying filter: {str(e)}")
            return False

    def clear_filter(self) -> bool:
        """
        Clear the current filter.

        Returns:
            bool: Success status
        """
        try:
            if self._data_model.is_empty:
                return False

            # Clear filtered data
            self._filtered_data = self._data_model.data

            # Clear current filter
            self._current_filters = {}

            # Update view if attached
            if self._view:
                # Clear filter controls
                if hasattr(self._view, "_filter_text"):
                    self._view._filter_text.clear()

                # Update view with all data
                if hasattr(self._view, "_update_view"):
                    self._view._update_view()

                # Update status label if exists
                if hasattr(self._view, "_status_label"):
                    row_count = len(self._data_model.data)
                    self._view._status_label.setText(f"Loaded {row_count} rows")

            # Emit filter applied signal with empty filter
            self.filter_applied.emit({})

            logger.info("Filter cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing filter: {e}")
            self.operation_error.emit(f"Error clearing filter: {str(e)}")
            return False

    def sort_data(self, column: str, ascending: bool = True) -> bool:
        """
        Sort the data by the specified column.

        Args:
            column: Column to sort by
            ascending: Sort direction

        Returns:
            bool: Success status
        """
        try:
            if self._data_model.is_empty:
                logger.warning("Cannot sort: Data model is empty")
                return False

            if not column or column not in self._data_model.column_names:
                logger.warning(f"Invalid sort column: {column}")
                self.operation_error.emit(f"Invalid sort column: {column}")
                return False

            # Save current sort
            self._current_sort_column = column
            self._current_sort_ascending = ascending

            # Sort data - handle in view for now as it's UI-specific with Qt's sorting
            if self._view and hasattr(self._view, "_table_view"):
                # Find column index
                col_idx = self._data_model.column_names.index(column)

                # Apply sort
                self._view._table_view.sortByColumn(
                    col_idx,
                    0 if ascending else 1,  # Qt.AscendingOrder=0, Qt.DescendingOrder=1
                )

            # Emit sort applied signal
            self.sort_applied.emit(column, ascending)

            logger.info(f"Sort applied: {column} ({'ascending' if ascending else 'descending'})")
            return True

        except Exception as e:
            logger.error(f"Error sorting data: {e}")
            self.operation_error.emit(f"Error sorting data: {str(e)}")
            return False

    def populate_table(self) -> bool:
        """
        Populate the data table with current data.

        Returns:
            bool: Success status
        """
        try:
            if self._data_model.is_empty:
                logger.warning("Cannot populate table: Data model is empty")
                return False

            # Check if view exists
            if not self._view:
                logger.warning("Cannot populate table: View not set")
                return False

            # Populate the table
            if hasattr(self._view, "populate_table"):
                self._view.populate_table()
            elif hasattr(self._view, "_update_view"):
                self._view._update_view()
            else:
                logger.warning("View does not have populate_table or _update_view method")
                return False

            # Update our state tracking
            self._update_data_state()

            # Emit table populated signal
            self.table_populated.emit(len(self._data_model.data))

            logger.info(f"Table populated with {len(self._data_model.data)} rows")
            return True

        except Exception as e:
            logger.error(f"Error populating table: {e}")
            self.operation_error.emit(f"Error populating table: {str(e)}")
            return False

    def needs_refresh(self) -> bool:
        """
        Determine if the view needs to be refreshed.

        This checks if the data has changed since the last refresh.

        Returns:
            bool: True if refresh is needed, False otherwise
        """
        if self._data_model.is_empty:
            return False

        try:
            # Check if data hash has changed
            current_hash = (
                self._data_model.data_hash if hasattr(self._data_model, "data_hash") else ""
            )
            last_hash = self._last_data_state.get("data_hash", "")

            if current_hash != last_hash:
                logger.debug(f"Needs refresh: data hash changed ({last_hash} -> {current_hash})")
                return True

            # Check if row count has changed
            current_rows = len(self._data_model.data)
            last_rows = self._last_data_state.get("row_count", 0)

            if current_rows != last_rows:
                logger.debug(f"Needs refresh: row count changed ({last_rows} -> {current_rows})")
                return True

            # Check if column count has changed
            current_cols = len(self._data_model.column_names)
            last_cols = self._last_data_state.get("column_count", 0)

            if current_cols != last_cols:
                logger.debug(f"Needs refresh: column count changed ({last_cols} -> {current_cols})")
                return True

            # No need to refresh
            return False

        except Exception as e:
            logger.error(f"Error checking if refresh is needed: {e}")
            return True  # Refresh anyway to be safe

    def refresh_data(self) -> bool:
        """
        Refresh the data view if needed.

        Returns:
            bool: Success status
        """
        try:
            # Check if view exists
            if not self._view:
                logger.warning("Cannot refresh data: View not set")
                return False

            # Check if refresh is needed
            if not self.needs_refresh():
                logger.info("Skipping refresh: No data changes detected")
                return True

            # Refresh the view
            if hasattr(self._view, "refresh"):
                self._view.refresh()
            elif hasattr(self._view, "_update_view"):
                self._view._update_view()
            else:
                logger.warning("View does not have refresh or _update_view method")
                return False

            # Reapply filter if there's an active filter
            if self._current_filters and self._current_filters.get("column"):
                self.filter_data(
                    self._current_filters["column"],
                    self._current_filters["text"],
                    self._current_filters["mode"],
                    self._current_filters["case_sensitive"],
                )

            # Update our state tracking
            self._update_data_state()

            logger.info("Data view refreshed")
            return True

        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            self.operation_error.emit(f"Error refreshing data: {str(e)}")
            return False

    def get_current_filter(self) -> Dict:
        """
        Get the current filter parameters.

        Returns:
            Dict: Current filter parameters
        """
        return self._current_filters.copy()

    def get_current_sort(self) -> Dict:
        """
        Get the current sort parameters.

        Returns:
            Dict: Current sort parameters
        """
        return {
            "column": self._current_sort_column,
            "ascending": self._current_sort_ascending,
        }

    def validate_data(self, specific_rules: Optional[List[str]] = None) -> bool:
        """
        Validate the data using the validation service.

        Args:
            specific_rules: Optional list of specific rule names to run

        Returns:
            bool: Success status
        """
        try:
            if not self._validation_service:
                logger.warning("Cannot validate: Validation service not available")
                self.operation_error.emit("Validation service not available")
                return False

            if self._data_model.is_empty:
                logger.warning("Cannot validate: Data model is empty")
                self.operation_error.emit("Cannot validate empty data")
                return False

            # Emit validation started signal
            self.validation_started.emit()

            # Update UI state if controller is available
            if self._ui_state_controller:
                self._ui_state_controller.update_status_message("Validating data...")

            # Run validation
            results = self._validation_service.validate_data(specific_rules)

            # Emit validation completed signal
            self.validation_completed.emit(results)

            # Update view if attached
            if self._view and hasattr(self._view, "refresh"):
                self._view.refresh()

            logger.info(f"Validation completed with {len(results)} rule results")
            return True

        except Exception as e:
            logger.error(f"Error validating data: {e}")
            self.validation_error.emit(f"Error validating data: {str(e)}")
            self.operation_error.emit(f"Error validating data: {str(e)}")
            return False

    def get_validation_summary(self) -> Dict[str, int]:
        """
        Get a summary of validation issues.

        Returns:
            Dict[str, int]: A dictionary mapping rule names to the count of issues found
        """
        try:
            if not self._validation_service:
                logger.warning("Cannot get validation summary: Validation service not available")
                return {}

            return self._validation_service.get_validation_summary()

        except Exception as e:
            logger.error(f"Error getting validation summary: {e}")
            self.operation_error.emit(f"Error getting validation summary: {str(e)}")
            return {}

    @Slot(dict)
    def _on_validation_completed(self, results):
        """
        Handle validation completed signal from the validation service.

        Args:
            results: The validation results
        """
        try:
            # Update the view if attached
            if self._view and hasattr(self._view, "refresh"):
                self._view.refresh()

            # Highlight invalid rows in the view
            self.highlight_invalid_rows()

            # Check for correctable cells and mark them
            try:
                correction_controller = ServiceLocator.get("correction_controller")
                if correction_controller and hasattr(correction_controller, "_correction_service"):
                    correction_service = correction_controller._correction_service
                    if correction_service and hasattr(
                        correction_service, "check_correctable_status"
                    ):
                        num_correctable = correction_service.check_correctable_status()
                        logger.info(
                            f"Checked for correctable cells: {num_correctable} cells marked as correctable"
                        )
                        # Refresh view again with correctable status
                        if self._view and hasattr(self._view, "refresh"):
                            self._view.refresh()
                else:
                    logger.warning(
                        "CorrectionController not available for checking correctable status"
                    )
            except Exception as e:
                logger.error(f"Error checking for correctable cells: {e}")

            # Apply auto-correction if enabled
            # Get correction controller from ServiceLocator
            try:
                correction_controller = ServiceLocator.get("correction_controller")
                if correction_controller:
                    # Apply auto-correction after validation
                    if correction_controller.auto_correct_after_validation():
                        logger.info("Auto-correction after validation applied")
                    else:
                        logger.debug("Auto-correction after validation is disabled or failed")
                else:
                    logger.warning("CorrectionController not available for auto-correction")
            except Exception as e:
                logger.error(f"Error applying auto-correction after validation: {e}")

            logger.info(f"Handled validation completion with {len(results)} rule results")

        except Exception as e:
            logger.error(f"Error handling validation completion: {e}")
            self.operation_error.emit(f"Error handling validation completion: {str(e)}")

    def apply_correction(
        self,
        strategy_name: str,
        column: Optional[str] = None,
        rows: Optional[List[int]] = None,
        **strategy_args,
    ) -> bool:
        """
        Apply a correction strategy to the data.

        Args:
            strategy_name: The name of the correction strategy to apply
            column: Optional column name to apply the correction to
            rows: Optional list of row indices to apply the correction to
            **strategy_args: Additional arguments to pass to the strategy function

        Returns:
            bool: Success status
        """
        try:
            if not self._correction_service:
                logger.warning("Cannot apply correction: Correction service not available")
                self.operation_error.emit("Correction service not available")
                return False

            if self._data_model.is_empty:
                logger.warning("Cannot apply correction: Data model is empty")
                self.operation_error.emit("Cannot apply correction to empty data")
                return False

            # Emit correction started signal
            self.correction_started.emit(strategy_name)

            # Apply correction
            result, error = self._correction_service.apply_correction(
                strategy_name, column, rows, **strategy_args
            )

            if result:
                # Emit correction completed signal
                affected_rows = len(rows) if rows else self._data_model.row_count
                self.correction_completed.emit(strategy_name, affected_rows)

                # Update view if attached
                if self._view and hasattr(self._view, "refresh"):
                    self._view.refresh()

                logger.info(f"Correction {strategy_name} applied successfully")
                return True
            else:
                self.correction_error.emit(error if error else f"Failed to apply {strategy_name}")
                self.operation_error.emit(error if error else f"Failed to apply {strategy_name}")
                return False

        except Exception as e:
            logger.error(f"Error applying correction: {e}")
            self.correction_error.emit(f"Error applying correction: {str(e)}")
            self.operation_error.emit(f"Error applying correction: {str(e)}")
            return False

    def get_correction_history(self) -> List[Dict[str, Any]]:
        """
        Get the correction history.

        Returns:
            List[Dict[str, Any]]: A list of correction records
        """
        try:
            if not self._correction_service:
                logger.warning("Cannot get correction history: Correction service not available")
                return []

            return self._correction_service.get_correction_history()

        except Exception as e:
            logger.error(f"Error getting correction history: {e}")
            self.operation_error.emit(f"Error getting correction history: {str(e)}")
            return []

    @Slot(str, int)
    def _on_correction_completed(self, strategy_name, affected_rows):
        """
        Handle correction completed signal from the correction service.

        Args:
            strategy_name: The name of the applied correction strategy
            affected_rows: The number of affected rows
        """
        try:
            # Update the view if attached
            if self._view and hasattr(self._view, "refresh"):
                self._view.refresh()

            logger.info(
                f"Handled correction completion: {strategy_name} affected {affected_rows} rows"
            )

        except Exception as e:
            logger.error(f"Error handling correction completion: {e}")
            self.operation_error.emit(f"Error handling correction completion: {str(e)}")

    def get_invalid_rows(self) -> List[int]:
        """
        Get the list of row indices that have validation issues.

        Returns:
            List[int]: Row indices with validation issues
        """
        try:
            if self._data_model.is_empty:
                return []

            return self._data_model.get_invalid_rows()

        except Exception as e:
            logger.error(f"Error getting invalid rows: {e}")
            self.operation_error.emit(f"Error getting invalid rows: {str(e)}")
            return []

    def get_corrected_rows(self) -> List[int]:
        """
        Get the list of row indices that have been corrected.

        Returns:
            List[int]: Row indices that have been corrected
        """
        try:
            if self._data_model.is_empty:
                return []

            corrected_rows = []
            correction_status = self._data_model.get_correction_status()

            for row_idx, status in correction_status.items():
                if status:  # If any corrections have been applied to this row
                    corrected_rows.append(row_idx)

            return corrected_rows

        except Exception as e:
            logger.error(f"Error getting corrected rows: {e}")
            self.operation_error.emit(f"Error getting corrected rows: {str(e)}")
            return []

    def highlight_invalid_rows(self) -> bool:
        """
        Highlight rows with validation issues in the view.

        Returns:
            bool: Success status
        """
        try:
            if self._data_model.is_empty:
                return False

            if not self._view:
                return False

            # Get rows with validation issues
            invalid_rows = self.get_invalid_rows()

            # First check if view has access to TableStateManager
            if hasattr(self._view, "_table_state_manager") and self._view._table_state_manager:
                # Convert invalid_rows to the format TableStateManager expects
                validation_status = pd.DataFrame(
                    {
                        "ROW_IDX": [row for row in invalid_rows],
                        "COL_IDX": [0 for _ in invalid_rows],  # Just a placeholder
                        "STATUS": ["invalid" for _ in invalid_rows],
                    }
                )
                # Use TableStateManager to update cell states
                self._view._table_state_manager.update_cell_states_from_validation(
                    validation_status
                )
                return True
            # Fallback options for backward compatibility
            elif hasattr(self._view, "highlight_rows"):
                self._view.highlight_rows(invalid_rows, "invalid")
                return True
            elif hasattr(self._view, "_highlight_invalid_rows"):
                # This call might need adjustment based on what _highlight_invalid_rows expects
                logger.warning(
                    "Using legacy _highlight_invalid_rows method which may not be maintained"
                )
                self._view._highlight_invalid_rows(invalid_rows)
                return True

            return False

        except Exception as e:
            logger.error(f"Error highlighting invalid rows: {e}")
            self.operation_error.emit(f"Error highlighting invalid rows: {str(e)}")
            return False

    def highlight_corrected_rows(self) -> bool:
        """
        Highlight rows that have been corrected in the view.

        Returns:
            bool: Success status
        """
        try:
            if self._data_model.is_empty:
                return False

            if not self._view:
                return False

            # Get rows that have been corrected
            corrected_rows = self.get_corrected_rows()

            # If the view has a highlight_rows method, call it
            if hasattr(self._view, "highlight_rows"):
                self._view.highlight_rows(corrected_rows, "corrected")
                return True
            elif hasattr(self._view, "_highlight_corrected_rows"):
                self._view._highlight_corrected_rows(corrected_rows)
                return True

            return False

        except Exception as e:
            logger.error(f"Error highlighting corrected rows: {e}")
            self.operation_error.emit(f"Error highlighting corrected rows: {str(e)}")
            return False

    def export_validation_report(self, file_path) -> Tuple[bool, Optional[str]]:
        """
        Export a validation report to a file.

        Args:
            file_path: The path to save the report to

        Returns:
            Tuple[bool, Optional[str]]: Success status and error message if any
        """
        try:
            if not self._validation_service:
                error_msg = "Validation service not available"
                logger.warning(error_msg)
                self.operation_error.emit(error_msg)
                return False, error_msg

            if self._data_model.is_empty:
                error_msg = "Cannot export validation report: Data model is empty"
                logger.warning(error_msg)
                self.operation_error.emit(error_msg)
                return False, error_msg

            result, error = self._validation_service.export_validation_report(file_path)

            if not result:
                self.operation_error.emit(error if error else "Failed to export validation report")

            return result, error

        except Exception as e:
            error_msg = f"Error exporting validation report: {e}"
            logger.error(error_msg)
            self.operation_error.emit(error_msg)
            return False, error_msg

    def export_correction_report(self, file_path) -> Tuple[bool, Optional[str]]:
        """
        Export a correction report to a file.

        Args:
            file_path: The path to save the report to

        Returns:
            Tuple[bool, Optional[str]]: Success status and error message if any
        """
        try:
            if not self._correction_service:
                error_msg = "Correction service not available"
                logger.warning(error_msg)
                self.operation_error.emit(error_msg)
                return False, error_msg

            if self._data_model.is_empty:
                error_msg = "Cannot export correction report: Data model is empty"
                logger.warning(error_msg)
                self.operation_error.emit(error_msg)
                return False, error_msg

            result, error = self._correction_service.export_correction_report(file_path)

            if not result:
                self.operation_error.emit(error if error else "Failed to export correction report")

            return result, error

        except Exception as e:
            error_msg = f"Error exporting correction report: {e}"
            logger.error(error_msg)
            self.operation_error.emit(error_msg)
            return False, error_msg

    # ===== Chart Operations =====

    def create_chart(
        self,
        chart_type: str,
        x_column: str,
        y_column: str,
        title: str = "Chart",
        group_by: Optional[str] = None,
    ) -> bool:
        """
        Create a chart using the chart service.

        Args:
            chart_type (str): Type of chart to create (Bar Chart, Pie Chart, Line Chart)
            x_column (str): Column to use for x-axis or categories
            y_column (str): Column to use for y-axis or values
            title (str, optional): Chart title. Defaults to "Chart".
            group_by (str, optional): Column to group by for line charts. Defaults to None.

        Returns:
            bool: Success status
        """
        try:
            # Signal chart creation started
            self.operation_started.emit("chart_creation")

            # Validate data model
            if self._data_model.is_empty:
                logger.warning("Cannot create chart: Data model is empty")
                self.operation_error.emit("No data available for chart creation")
                return False

            # Validate columns
            if not x_column or not y_column:
                logger.warning(f"Invalid chart columns: x={x_column}, y={y_column}")
                self.operation_error.emit("Invalid chart columns")
                return False

            # Get the chart service from the view
            chart_service = None
            if hasattr(self._view, "_chart_service"):
                chart_service = self._view._chart_service
            elif (
                self._view
                and hasattr(self._view, "_chart_tab")
                and hasattr(self._view._chart_tab, "chart_service")
            ):
                chart_service = self._view._chart_tab.chart_service

            if not chart_service:
                logger.warning("Chart service not available")
                self.operation_error.emit("Chart service not available")
                return False

            # Create the chart based on chart type
            chart = None
            if chart_type == "Bar Chart":
                chart = chart_service.create_bar_chart(x_column, y_column, title)
            elif chart_type == "Pie Chart":
                chart = chart_service.create_pie_chart(x_column, y_column, title)
            elif chart_type == "Line Chart":
                chart = chart_service.create_line_chart(
                    x_column, y_column, title, group_by=group_by
                )
            else:
                logger.warning(f"Unsupported chart type: {chart_type}")
                self.operation_error.emit(f"Unsupported chart type: {chart_type}")
                return False

            # If the view has the chart tab and chart view, set the chart
            if (
                self._view
                and hasattr(self._view, "_chart_tab")
                and hasattr(self._view._chart_tab, "chart_view")
            ):
                self._view._chart_tab.chart_view.setChart(chart)
                self._view._chart_tab.export_button.setEnabled(True)

            # Emit signals
            self.chart_created.emit(chart)
            self.operation_completed.emit("chart_creation", chart_type)

            logger.info(f"Chart created: {chart_type}, {title}")
            return True

        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            self.operation_error.emit("chart_creation", f"Error creating chart: {str(e)}")
            return False

    def export_chart(self) -> bool:
        """
        Export the currently displayed chart to a file.

        Returns:
            bool: Success status
        """
        try:
            # Signal chart export started
            self.operation_started.emit("chart_export")

            # Check if view exists
            if not self._view:
                logger.warning("Cannot export chart: View not set")
                self.operation_error.emit("View not set")
                return False

            # Check if chart tab exists and has a current chart
            if (
                not hasattr(self._view, "_chart_tab")
                or not hasattr(self._view._chart_tab, "_current_chart")
                or not self._view._chart_tab._current_chart
            ):
                logger.warning("No chart available for export")
                self.operation_error.emit("No chart available for export")
                return False

            # Call export method on chart tab
            file_path = self._view._chart_tab._export_chart()

            if file_path:
                # Emit signal
                self.operation_completed.emit("chart_export", file_path)
                logger.info(f"Chart exported to {file_path}")
                return True
            else:
                self.operation_error.emit("chart_export", "Chart export cancelled or failed")
                return False

        except Exception as e:
            logger.error(f"Error exporting chart: {e}")
            self.operation_error.emit("chart_export", f"Error exporting chart: {str(e)}")
            return False

    def _on_data_corrected(self, correction_operations: List[Dict]) -> None:
        """
        Handle data correction operations from the view.

        Args:
            correction_operations: List of correction operations to apply
        """
        if not correction_operations:
            return

        try:
            for operation in correction_operations:
                operation_type = operation.get("action", "")

                # Handle add_to_validation action
                if operation_type == "add_to_validation":
                    field_type = operation.get("field_type", "")
                    value = operation.get("value", "")

                    if field_type and value and hasattr(self, "_validation_service"):
                        # Add to validation list
                        success = self._validation_service.add_to_validation_list(field_type, value)

                        if success:
                            # Validate data again to update validation status
                            self.validate_data()

                            # Emit signal that correction was completed
                            self.correction_completed.emit(
                                {
                                    "action": "add_to_validation",
                                    "field_type": field_type,
                                    "value": value,
                                    "success": True,
                                }
                            )

                            # Update UI state if controller is available
                            if self._ui_state_controller:
                                self._ui_state_controller.update_status_message(
                                    f"Added '{value}' to {field_type} validation list"
                                )

                            # Log the success
                            logger.info(f"Added '{value}' to {field_type} validation list")
                        else:
                            # Emit error signal
                            self.correction_error.emit(
                                f"Failed to add '{value}' to {field_type} validation list"
                            )

                            # Update UI state if controller is available
                            if self._ui_state_controller:
                                self._ui_state_controller.update_status_message(
                                    f"Failed to add '{value}' to {field_type} validation list"
                                )

                            logger.error(f"Failed to add '{value}' to {field_type} validation list")
                else:
                    # Handle other correction operations (existing implementation)
                    logger.debug(f"Received unhandled correction operation: {operation_type}")
        except Exception as e:
            self.correction_error.emit(f"Error processing correction operation: {str(e)}")
            logger.error(f"Error in _on_data_corrected: {str(e)}")

    def _connect_to_ui_state_controller(self):
        """Connect to UI state controller signals."""
        if not self._ui_state_controller:
            return

        # Connect validation completed signal to UI state controller
        self.validation_completed.connect(self._ui_state_controller.handle_validation_results)

        # Connect validation started signal to update status message
        self.validation_started.connect(
            lambda: self._ui_state_controller.update_status_message("Validating data...")
        )

        # Connect validation error signal to update status message
        self.validation_error.connect(
            lambda msg: self._ui_state_controller.update_status_message(f"Validation error: {msg}")
        )

        # Connect action states to monitor auto-validate state
        self._ui_state_controller.actions_state_changed.connect(self._handle_action_states_changed)

        logger.debug("DataViewController connected to UIStateController")

    @Slot(dict)
    def _handle_action_states_changed(self, action_states: dict) -> None:
        """
        Handle changes in UI action states.

        Args:
            action_states: Dictionary of action states
        """
        try:
            # Validation service is required for this method
            validation_service = ServiceLocator.get("validation_service")
            if not validation_service:
                logger.warning("ValidationService not available for action state updates")
                return

            # Update validation service based on action states
            # Check if auto_validate is in the action states
            if "auto_validate" in action_states:
                auto_validate = action_states["auto_validate"]
                logger.debug(f"Auto-validate action state changed to: {auto_validate}")

                # Update validation service with new auto-validate state
                # This ensures validation happens automatically after import if enabled
                self._validation_service.set_validate_on_import(auto_validate)
                logger.debug(
                    f"Updated validation service auto-validate setting to: {auto_validate}"
                )
        except Exception as e:
            logger.error(f"Error handling action states changed: {e}")
            self.operation_error.emit(str(e))

    def set_auto_validate(self, enabled: bool) -> None:
        """
        Set the auto validation state.

        Args:
            enabled: Whether auto-validation should be enabled
        """
        try:
            # Update validation service
            if self._validation_service:
                self._validation_service.set_validate_on_import(enabled)
                logger.info(f"Set validate_on_import to {enabled}")
            else:
                logger.warning("ValidationService not available for setting auto-validate")

            # Update UI state
            if self._ui_state_controller:
                self._ui_state_controller.update_action_states(auto_validate=enabled)
            else:
                logger.warning("UIStateController not available for setting auto-validate")
        except Exception as e:
            logger.error(f"Error setting auto-validate: {e}")
            self.operation_error.emit(str(e))

    def get_auto_validate(self) -> bool:
        """
        Get the current auto-validate state.

        Returns:
            Whether auto-validation is enabled
        """
        try:
            # Try to get from validation service first
            if self._validation_service:
                return self._validation_service.get_validate_on_import()

            # Fall back to UI state controller
            if self._ui_state_controller:
                return self._ui_state_controller.get_auto_validate()

            # Default if neither is available
            return True
        except Exception as e:
            logger.error(f"Error getting auto-validate state: {e}")
            return True

    @Slot()
    def _validate_after_import(self) -> None:
        """
        Validate data after import if auto-validate is enabled.
        This method is connected to the data_loaded signal from DataManager.
        """
        try:
            # First check for auto-correction on import (regardless of validation)
            try:
                correction_controller = ServiceLocator.get("correction_controller")
                if correction_controller:
                    # Apply auto-correction on import
                    if correction_controller.auto_correct_on_import():
                        logger.info("Auto-correction on import applied")
                    else:
                        logger.debug("Auto-correction on import is disabled or failed")
                else:
                    logger.warning(
                        "CorrectionController not available for auto-correction on import"
                    )
            except Exception as e:
                logger.error(f"Error applying auto-correction on import: {e}")

            # Get validation service from ServiceLocator
            validation_service = ServiceLocator.get("validation_service")

            if not validation_service:
                logger.warning("ValidationService not available for auto-validation")
                return

            # Check if auto-validate is enabled
            if validation_service.get_validate_on_import():
                logger.info("Auto-validation is enabled, validating data after import")
                # Set status message before validation starts
                if self._ui_state_controller:
                    self._ui_state_controller.update_status_message("Validating...")

                # Run validation
                self.validate_data()
            else:
                logger.info("Auto-validation is disabled, skipping validation after import")
                # Don't update status message when auto-validation is disabled
        except Exception as e:
            logger.error(f"Error in auto-validation after import: {e}")
            self.operation_error.emit(str(e))

    # --- Slot for Correction Application ---
    @Slot(QModelIndex, object)
    def _handle_apply_correction(
        self, source_index: QModelIndex, suggestion: object
    ) -> None:
        """Handles the request to apply a specific correction suggestion.

        Args:
            source_index: The QModelIndex of the cell in the source model.
            suggestion: The CorrectionSuggestion object selected by the user.
        """
        if not source_index.isValid():
            logger.warning("_handle_apply_correction received invalid index.")
            return

        if not hasattr(suggestion, "original_value") or not hasattr(
            suggestion, "corrected_value"
        ):
            logger.error(
                f"Invalid suggestion object received: {suggestion}. Missing required attributes."
            )
            self.operation_error.emit("Invalid suggestion object received.")
            return

        row = source_index.row()
        col = source_index.column()
        column_name = self._data_model.get_column_name(col)
        original_value = getattr(suggestion, "original_value", "Unknown")
        corrected_value = getattr(suggestion, "corrected_value", "Unknown")

        logger.info(
            f"Applying correction for cell ({row}, {col} - {column_name}): 
            '{original_value}' -> '{corrected_value}'"
        )

        # Get the CorrectionService
        correction_service = ServiceLocator.get_service("correction_service")
        if not correction_service:
            logger.error("CorrectionService not found in ServiceLocator.")
            self.operation_error.emit("Correction service is unavailable.")
            return

        try:
            # Call the dedicated CorrectionService method
            success = correction_service.apply_suggestion_to_cell(row, col, suggestion)
            if not success:
                raise ValueError("CorrectionService.apply_suggestion_to_cell returned False.")

            logger.info(f"Correction applied successfully for cell ({row}, {col}).")

        except Exception as e:
            logger.error(f"Error applying correction to cell ({row}, {col}): {e}", exc_info=True)
            self.operation_error.emit(f"Failed to apply correction: {e}")
