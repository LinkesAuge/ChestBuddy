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

from PySide6.QtCore import QObject, Signal, Slot
import pandas as pd

# Set up logger
logger = logging.getLogger(__name__)


class DataViewController(QObject):
    """
    Controller for data view operations in ChestBuddy.

    This class handles data filtering, sorting, and table population,
    coordinating between the data model and UI components.

    Attributes:
        filter_applied (Signal): Emitted when a filter is applied
        sort_applied (Signal): Emitted when sort is applied
        table_populated (Signal): Emitted when the table is populated
        operation_error (Signal): Emitted when an error occurs
    """

    # Define signals
    filter_applied = Signal(dict)  # Filter parameters
    sort_applied = Signal(str, bool)  # Column, ascending
    table_populated = Signal(int)  # Number of rows
    operation_error = Signal(str)  # Error message

    def __init__(self, data_model):
        """
        Initialize the DataViewController.

        Args:
            data_model: The data model
        """
        super().__init__()
        self._data_model = data_model
        self._view = None
        self._filtered_data = None
        self._current_filter = {}
        self._current_sort = {"column": "", "ascending": True}

        # State tracking to avoid unnecessary updates
        self._last_data_state = {
            "row_count": 0,
            "column_count": 0,
            "data_hash": "",
            "last_update_time": 0,
        }

        # Connect to data model signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect to relevant signals from the data model."""
        if hasattr(self._data_model, "data_changed"):
            self._data_model.data_changed.connect(self._on_data_changed)

    def set_view(self, view):
        """
        Set the data view for this controller.

        Args:
            view: The data view component
        """
        self._view = view

        # Connect view signals if available
        if hasattr(view, "_action_toolbar"):
            if hasattr(view._action_toolbar, "get_button_by_name"):
                filter_button = view._action_toolbar.get_button_by_name("apply_filter")
                clear_button = view._action_toolbar.get_button_by_name("clear_filter")

                if filter_button and hasattr(filter_button, "clicked"):
                    filter_button.clicked.connect(self._handle_filter_button_clicked)

                if clear_button and hasattr(clear_button, "clicked"):
                    clear_button.clicked.connect(self._handle_clear_filter_button_clicked)

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

    @Slot()
    def _on_data_changed(self):
        """Handle data model changes."""
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
            self._current_filter = {
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
            self.filter_applied.emit(self._current_filter)

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
            self._current_filter = {}

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
            self._current_sort = {
                "column": column,
                "ascending": ascending,
            }

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
        Check if the view needs refreshing based on data state.

        Returns:
            bool: True if the view needs to be refreshed, False otherwise
        """
        try:
            # Check if data has changed
            current_state = {"row_count": 0, "column_count": 0, "data_hash": ""}

            if not self._data_model.is_empty:
                current_state = {
                    "row_count": len(self._data_model.data),
                    "column_count": len(self._data_model.column_names),
                    "data_hash": self._data_model.data_hash
                    if hasattr(self._data_model, "data_hash")
                    else "",
                }

            # Check for dimension changes or data content changes via hash
            dimensions_changed = (
                current_state["row_count"] != self._last_data_state["row_count"]
                or current_state["column_count"] != self._last_data_state["column_count"]
            )

            content_changed = current_state["data_hash"] != self._last_data_state.get(
                "data_hash", ""
            )

            needs_refresh = dimensions_changed or content_changed

            if needs_refresh:
                logger.debug(
                    f"View needs refresh: Data changed. Old: {self._last_data_state}, New: {current_state}"
                )
            else:
                logger.debug("View doesn't need refresh: No data changes detected")

            return needs_refresh

        except Exception as e:
            logger.error(f"Error checking if view needs refresh: {e}")
            # Default to refresh if there's an error
            return True

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
            if self._current_filter and self._current_filter.get("column"):
                self.filter_data(
                    self._current_filter["column"],
                    self._current_filter["text"],
                    self._current_filter["mode"],
                    self._current_filter["case_sensitive"],
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
        return self._current_filter.copy()

    def get_current_sort(self) -> Dict:
        """
        Get the current sort parameters.

        Returns:
            Dict: Current sort parameters
        """
        return self._current_sort.copy()
