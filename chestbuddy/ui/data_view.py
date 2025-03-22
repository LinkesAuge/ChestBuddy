"""
DataView module.

This module provides the DataView class for displaying and editing CSV data.
"""

import logging
from typing import Dict, List, Optional, Any
import time

import pandas as pd
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QHeaderView,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QMenu,
    QSplitter,
    QApplication,
)
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QAction,
    QColor,
    QKeySequence,
    QShortcut,
    QKeyEvent,
)

from chestbuddy.core.models import ChestDataModel

# Set up logger
logger = logging.getLogger(__name__)


class DataView(QWidget):
    """
    Widget for displaying and editing CSV data.

    The DataView provides a table view of the data and controls for
    filtering, sorting, and editing.

    Implementation Notes:
        - Uses Qt's model/view architecture
        - Provides filtering and sorting capabilities
        - Highlights validation issues and corrections
        - Allows editing of cell values
    """

    # Add class variable to track last update time
    _last_update_time = 0.0
    _update_debounce_ms = 500  # Minimum time between updates in milliseconds

    def __init__(self, data_model: ChestDataModel, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the DataView.

        Args:
            data_model: The data model to display.
            parent: The parent widget.
        """
        super().__init__(parent)

        # Initialize class variables
        self._data_model = data_model
        self._table_model = QStandardItemModel()
        self._filtered_rows: List[int] = []
        self._current_filter: Dict[str, str] = {}
        self._is_updating = False  # Guard against recursive updates

        # Set up UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Initial update
        self._update_view()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Create splitter for filter panel and table
        splitter = QSplitter(Qt.Vertical)

        # Filter panel
        filter_group = QGroupBox("Filter Data")
        filter_layout = QVBoxLayout(filter_group)

        # Filter controls
        filter_form = QFormLayout()

        # Column selector
        self._filter_column = QComboBox()
        self._filter_column.setMinimumWidth(150)
        filter_form.addRow("Column:", self._filter_column)

        # Filter text
        self._filter_text = QLineEdit()
        self._filter_text.setPlaceholderText("Enter filter text...")
        filter_form.addRow("Value:", self._filter_text)

        # Filter mode
        self._filter_mode = QComboBox()
        self._filter_mode.addItems(["Contains", "Equals", "Starts with", "Ends with"])
        filter_form.addRow("Mode:", self._filter_mode)

        # Case sensitive
        self._case_sensitive = QCheckBox("Case sensitive")
        filter_form.addRow("", self._case_sensitive)

        filter_layout.addLayout(filter_form)

        # Filter buttons
        filter_buttons = QHBoxLayout()

        self._apply_filter_btn = QPushButton("Apply Filter")
        self._clear_filter_btn = QPushButton("Clear Filter")

        filter_buttons.addWidget(self._apply_filter_btn)
        filter_buttons.addWidget(self._clear_filter_btn)

        filter_layout.addLayout(filter_buttons)

        # Status label
        self._status_label = QLabel("No data loaded")
        filter_layout.addWidget(self._status_label)

        splitter.addWidget(filter_group)

        # Table view
        self._table_view = QTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(True)

        # Install event filter on table view to capture key events
        self._table_view.installEventFilter(self)
        logger.info("Installed event filter on table view")

        # Enable keyboard shortcuts for copy/paste
        self._setup_shortcuts()

        # Apply additional styling to ensure visibility
        self._apply_table_styling()

        splitter.addWidget(self._table_view)

        # Set splitter sizes
        splitter.setSizes([100, 500])

        main_layout.addWidget(splitter)

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for common operations."""
        # Copy shortcut (Ctrl+C)
        copy_shortcut = QShortcut(QKeySequence.Copy, self._table_view)
        copy_shortcut.activated.connect(self._copy_selected_cells)
        copy_shortcut.setContext(Qt.WidgetShortcut)  # Only active when table has focus
        logger.info("Registered Ctrl+C shortcut for copying (table-specific)")

        # We're removing redundant Ctrl+V shortcuts and only keeping one at the widget level
        # This helps avoid the "Ambiguous shortcut overload" error
        widget_paste_shortcut = QShortcut(QKeySequence.Paste, self)
        widget_paste_shortcut.activated.connect(self._paste_to_selected_cells)
        widget_paste_shortcut.setContext(
            Qt.WidgetWithChildrenShortcut
        )  # Active for widget and children
        logger.info("Registered widget-level Ctrl+V shortcut for pasting (widget hierarchy)")

        # Remove global action - it's causing ambiguity
        # paste_action = QAction("Paste", self)
        # paste_action.setShortcut(QKeySequence.Paste)
        # paste_action.triggered.connect(self._paste_to_selected_cells)
        # self.addAction(paste_action)
        # logger.info("Added global paste action to widget")

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.validation_changed.connect(self._on_validation_changed)
        self._data_model.correction_applied.connect(self._on_correction_applied)

        # Connect UI signals
        self._apply_filter_btn.clicked.connect(self._apply_filter)
        self._clear_filter_btn.clicked.connect(self._clear_filter)
        self._filter_text.returnPressed.connect(self._apply_filter)
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Connect table model signals
        self._table_model.itemChanged.connect(self._on_item_changed)

    def _update_view(self) -> None:
        """Update the view with current data."""
        # Guard against recursive calls
        if self._is_updating:
            logger.debug("Skipping recursive _update_view call")
            return

        try:
            self._is_updating = True
            logger.info("Starting _update_view method")

            # Clear the table model
            self._table_model.clear()

            # Check if data is empty
            if self._data_model.is_empty:
                logger.warning("Data model is empty, no data to display")
                self._status_label.setText("No data loaded")
                self._filtered_rows = []  # Initialize to empty list when no data
                return

            # Get data from model - get a shallow copy to avoid modifying original
            try:
                data = self._data_model.data
                logger.info(
                    f"Got data from model: {len(data)} rows, columns: {data.columns.tolist()}"
                )

                # Store the column names separately to avoid repeated access
                column_names = self._data_model.column_names
                logger.info(f"Column names: {column_names}")
            except Exception as e:
                logger.error(f"Error getting data: {e}")
                self._status_label.setText("Error loading data")
                return

            # Initialize filtered_rows with all row indices
            self._filtered_rows = list(
                range(len(data))
            )  # Use simple range instead of data.index.tolist()

            # Explicitly set model dimensions - important for proper initialization
            row_count = len(data)
            col_count = len(column_names)
            logger.info(
                f"Setting table model dimensions to {row_count} rows and {col_count} columns"
            )
            self._table_model.setRowCount(row_count)
            self._table_model.setColumnCount(col_count)

            # Set headers
            self._table_model.setHorizontalHeaderLabels(column_names)
            logger.info(f"Set horizontal headers with {len(column_names)} columns")

            # Populate filter column combo box
            current_column = self._filter_column.currentText()
            self._filter_column.clear()
            self._filter_column.addItems(column_names)

            # Restore selected column if it exists
            if current_column in column_names:
                self._filter_column.setCurrentText(current_column)

            # Add data to the table model - use a safer approach
            try:
                # Simplified direct population - no batching or complex access patterns
                logger.info("Populating table model with data (simplified approach)")

                # Ensure the model has the right dimensions
                row_count = len(data)
                col_count = len(column_names)
                self._table_model.setRowCount(row_count)
                self._table_model.setColumnCount(col_count)

                # Convert the entire DataFrame to a list of lists for direct access
                # This avoids repeated DataFrame accesses which can cause recursion
                data_array = data.values.tolist()

                # Pre-fetch validation and correction status to avoid repeated calls
                # This reduces the risk of recursion by doing all data access upfront
                try:
                    validation_status = self._data_model.get_validation_status()
                    correction_status = self._data_model.get_correction_status()
                    has_validation = not validation_status.empty
                    has_correction = not correction_status.empty
                    logger.debug(
                        f"Pre-fetched validation status ({has_validation}) and correction status ({has_correction})"
                    )
                except Exception as e:
                    logger.warning(f"Could not pre-fetch status data: {e}")
                    has_validation = False
                    has_correction = False

                # Process all rows at once
                for row_idx in range(row_count):
                    # Log progress for large datasets
                    if row_idx % 1000 == 0 and row_idx > 0:
                        logger.debug(f"Processing row {row_idx}/{row_count}")

                    for col_idx, column_name in enumerate(column_names):
                        # Get value directly from the pre-converted array
                        cell_value = data_array[row_idx][col_idx]
                        # Convert to string with proper None/NaN handling
                        value = (
                            ""
                            if cell_value is None
                            or (isinstance(cell_value, float) and pd.isna(cell_value))
                            else str(cell_value)
                        )

                        # Create item with explicit text
                        item = QStandardItem(value)

                        # Set foreground explicitly - changed from white to black for visibility
                        item.setForeground(QColor("#000000"))  # Black text

                        # Set validation and correction status as user data
                        # Use pre-fetched data instead of making method calls for each cell
                        if has_validation:
                            try:
                                val_status = self._data_model.get_cell_validation_status(
                                    row_idx, column_name
                                )
                                if val_status:
                                    item.setData(val_status, Qt.UserRole + 1)
                            except Exception as vs_error:
                                # Don't let validation status errors block the display
                                logger.debug(f"Validation status access error: {vs_error}")

                        if has_correction:
                            try:
                                corr_status = self._data_model.get_cell_correction_status(
                                    row_idx, column_name
                                )
                                if corr_status:
                                    item.setData(corr_status, Qt.UserRole + 2)
                            except Exception as cs_error:
                                # Don't let correction status errors block the display
                                logger.debug(f"Correction status access error: {cs_error}")

                        # Set the item directly
                        self._table_model.setItem(row_idx, col_idx, item)

                # Log detailed info about first few rows for debugging
                for row_idx in range(min(3, row_count)):
                    row_values = [str(data_array[row_idx][col_idx]) for col_idx in range(col_count)]
                    logger.debug(f"Row {row_idx} values: {row_values}")

                logger.info(
                    f"Successfully populated model with {row_count} rows and {col_count} columns"
                )
            except Exception as e:
                logger.error(f"Error populating table model: {e}", exc_info=True)
                self._status_label.setText("Error displaying data")

            # Resize columns to contents
            self._table_view.resizeColumnsToContents()
            logger.info("Resized columns to contents")

            # Update status label
            row_count = len(data)
            self._status_label.setText(f"Loaded {row_count} rows")
            logger.info(f"View update complete, loaded {row_count} rows")

            # Force the table to refresh - use the correct approach for QTableView
            self._table_view.reset()
            self._table_view.viewport().update()

            # Select the first row to ensure data is visible
            if self._table_model.rowCount() > 0:
                self._table_view.selectRow(0)

            # Add final verification of model state for debugging
            logger.info(
                f"Final table model state: {self._table_model.rowCount()} rows, {self._table_model.columnCount()} columns"
            )
            if self._table_model.rowCount() > 0 and self._table_model.columnCount() > 0:
                # Log a sample item to verify content
                sample_item = self._table_model.item(0, 0)
                sample_text = sample_item.text() if sample_item else "None"
                logger.info(f"Sample cell [0,0] content: '{sample_text}'")
        finally:
            self._is_updating = False

    def _apply_filter(self) -> None:
        """Apply the current filter to the data."""
        if self._data_model.is_empty:
            return

        column = self._filter_column.currentText()
        filter_text = self._filter_text.text()
        filter_mode = self._filter_mode.currentText()
        case_sensitive = self._case_sensitive.isChecked()

        # Apply filter to data model
        filtered_data = self._data_model.filter_data(
            column, filter_text, filter_mode, case_sensitive
        )

        if filtered_data is None:
            QMessageBox.warning(
                self, "Filter Error", f"Failed to apply filter to column '{column}'"
            )
            return

        # Update table with filtered data
        self._update_view_with_filtered_data(filtered_data)

        # Save current filter
        self._current_filter = {
            "column": column,
            "text": filter_text,
            "mode": filter_mode,
            "case_sensitive": case_sensitive,
        }

        # Update status label
        row_count = len(filtered_data)
        total_count = len(self._data_model.data)
        self._status_label.setText(f"Showing {row_count} of {total_count} rows")

    def _update_view_with_filtered_data(self, filtered_data: pd.DataFrame) -> None:
        """
        Update the view with filtered data.

        Args:
            filtered_data: The filtered data to display.
        """
        # Guard against recursive calls
        if self._is_updating:
            logger.debug("Skipping recursive _update_view_with_filtered_data call")
            return

        try:
            self._is_updating = True

            # Store filtered data
            self._filtered_data = filtered_data

            # Clear the table model
            self._table_model.clear()

            # Check if filtered data is empty
            if filtered_data.empty:
                self._status_label.setText("No data matches the filter")
                self._filtered_rows = []
                return

            # Store the column names to avoid repeated access
            column_names = self._data_model.column_names

            # Explicitly set model dimensions - important for proper initialization
            row_count = len(filtered_data)
            col_count = len(column_names)
            logger.info(
                f"Setting filtered table model dimensions to {row_count} rows and {col_count} columns"
            )
            self._table_model.setRowCount(row_count)
            self._table_model.setColumnCount(col_count)

            # Set headers
            self._table_model.setHorizontalHeaderLabels(column_names)

            # Store the filtered row indices - convert to plain Python list to avoid DataFrame operations
            self._filtered_rows = list(filtered_data.index)

            # Show filter status
            filter_text = self._filter_text.text()
            if filter_text:
                filter_count = len(filtered_data)
                total_count = len(self._data_model.data)
                self._status_label.setText(
                    f"Showing {filter_count} of {total_count} records matching '{filter_text}'"
                )

            # Add filtered data to the table model using a safer approach
            try:
                logger.info("Populating filtered table model (simplified approach)")

                # Ensure the model has the right dimensions
                row_count = len(filtered_data)
                col_count = len(column_names)
                self._table_model.setRowCount(row_count)
                self._table_model.setColumnCount(col_count)

                # Convert filtered data to a list of lists for direct access
                # This avoids repeated DataFrame accesses which can cause recursion
                data_array = filtered_data.values.tolist()

                # Store the filtered row indices for data model access
                self._filtered_rows = filtered_data.index.tolist()

                # Pre-fetch validation and correction status to avoid repeated calls
                # This reduces the risk of recursion by doing all data access upfront
                try:
                    validation_status = self._data_model.get_validation_status()
                    correction_status = self._data_model.get_correction_status()
                    has_validation = not validation_status.empty
                    has_correction = not correction_status.empty
                    logger.debug(
                        f"Pre-fetched validation status ({has_validation}) and correction status ({has_correction})"
                    )
                except Exception as e:
                    logger.warning(f"Could not pre-fetch status data: {e}")
                    has_validation = False
                    has_correction = False

                # Process all rows at once
                for local_row_idx in range(row_count):
                    # Get the actual row index from the original data
                    actual_row_idx = self._filtered_rows[local_row_idx]

                    for col_idx, column_name in enumerate(column_names):
                        # Get value directly from the pre-converted array
                        cell_value = data_array[local_row_idx][col_idx]
                        # Convert to string with proper None/NaN handling
                        value = (
                            ""
                            if cell_value is None
                            or (isinstance(cell_value, float) and pd.isna(cell_value))
                            else str(cell_value)
                        )

                        # Create item with explicit text
                        item = QStandardItem(value)

                        # Set foreground explicitly - changed from white to black for visibility
                        item.setForeground(QColor("#000000"))  # Black text

                        # Set validation and correction status as user data
                        # Use pre-fetched data instead of making method calls for each cell
                        if has_validation:
                            try:
                                val_status = self._data_model.get_cell_validation_status(
                                    actual_row_idx,
                                    column_name,  # Use actual_row_idx here
                                )
                                if val_status:
                                    item.setData(val_status, Qt.UserRole + 1)
                            except Exception as vs_error:
                                # Don't let validation status errors block the display
                                logger.debug(f"Validation status access error: {vs_error}")

                        if has_correction:
                            try:
                                corr_status = self._data_model.get_cell_correction_status(
                                    actual_row_idx,
                                    column_name,  # Use actual_row_idx here
                                )
                                if corr_status:
                                    item.setData(corr_status, Qt.UserRole + 2)
                            except Exception as cs_error:
                                # Don't let correction status errors block the display
                                logger.debug(f"Correction status access error: {cs_error}")

                        # Set the item directly
                        self._table_model.setItem(local_row_idx, col_idx, item)

                # Log detailed info about first few rows for debugging
                if row_count > 0:
                    logger.debug(f"First filtered row values: {data_array[0]}")

                logger.info(
                    f"Successfully populated filtered model with {row_count} rows and {col_count} columns"
                )
            except Exception as e:
                logger.error(f"Error populating filtered table model: {e}", exc_info=True)
                self._status_label.setText("Error displaying filtered data")

            # Resize columns to contents
            self._table_view.resizeColumnsToContents()

            # Force the table to refresh - use the correct approach for QTableView
            self._table_view.reset()
            self._table_view.viewport().update()

            # Select the first row to ensure data is visible
            if self._table_model.rowCount() > 0:
                self._table_view.selectRow(0)

            # Add final verification of model state for debugging
            logger.info(
                f"Final table model state: {self._table_model.rowCount()} rows, {self._table_model.columnCount()} columns"
            )
            if self._table_model.rowCount() > 0 and self._table_model.columnCount() > 0:
                # Log a sample item to verify content
                sample_item = self._table_model.item(0, 0)
                sample_text = sample_item.text() if sample_item else "None"
                logger.info(f"Sample cell [0,0] content: '{sample_text}'")
        finally:
            self._is_updating = False

    def _clear_filter(self) -> None:
        """Clear the current filter."""
        self._filter_text.clear()
        self._current_filter = {}
        self._filtered_rows = []

        # Reset the view
        self._update_view()

    def _show_context_menu(self, position) -> None:
        """
        Show context menu on right-click.

        Args:
            position: The position where the context menu should be shown.
        """
        if self._data_model.is_empty:
            return

        # Get the index at the position
        index = self._table_view.indexAt(position)
        if not index.isValid():
            return

        # Create context menu
        context_menu = QMenu(self)

        # Add actions
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self._copy_cell(index))
        context_menu.addAction(copy_action)

        # Get selected cells to determine context menu options
        selected_indexes = self._table_view.selectedIndexes()

        # Add paste option with appropriate text based on selection
        if len(selected_indexes) > 1:
            paste_action = QAction(f"Paste to all {len(selected_indexes)} selected cells", self)
        else:
            paste_action = QAction("Paste", self)

        paste_action.triggered.connect(lambda: self._paste_cell(index))
        context_menu.addAction(paste_action)

        # Show the menu
        context_menu.exec_(self._table_view.viewport().mapToGlobal(position))

    def _copy_cell(self, index) -> None:
        """
        Copy the cell value to clipboard.

        Args:
            index: The index of the cell to copy.
        """
        if not index.isValid():
            return

        # Get the value
        value = self._table_model.data(index, Qt.DisplayRole)

        # Copy to clipboard
        QApplication.clipboard().setText(value)

    def _paste_cell(self, index) -> None:
        """
        Paste clipboard text to the cell(s).

        Args:
            index: The index of the clicked cell (when using context menu).
                   If multiple cells are selected, they will all be updated.
                   Can be an invalid index when called from keyboard shortcuts.
        """
        # Get the text from clipboard
        text = QApplication.clipboard().text()
        logger.info(f"Clipboard text: '{text[:20]}{'...' if len(text) > 20 else ''}'")

        # Check if there are multiple cells selected
        selected_indexes = self._table_view.selectedIndexes()

        if selected_indexes:
            # Multiple cells selected, paste to all of them
            for sel_index in selected_indexes:
                # Set the value for each selected cell
                self._table_model.setData(sel_index, text, Qt.EditRole)

                # Also update the data model directly to ensure it's updated properly
                try:
                    row = sel_index.row()
                    col = sel_index.column()
                    if (
                        0 <= row < self._table_model.rowCount()
                        and 0 <= col < self._table_model.columnCount()
                    ):
                        # Get the actual row index if we're using filtered data
                        actual_row = row
                        if self._filtered_rows and row < len(self._filtered_rows):
                            actual_row = self._filtered_rows[row]

                        column_name = self._data_model.column_names[col]
                        self._data_model.update_cell(actual_row, column_name, text)
                except Exception as e:
                    logger.error(f"Error updating data model directly: {e}")

            logger.info(f"Pasted value to {len(selected_indexes)} selected cells")
        elif index.isValid():
            # Single cell via context menu, just paste to that
            self._table_model.setData(index, text, Qt.EditRole)

            # Also update the data model directly
            try:
                row = index.row()
                col = index.column()
                if (
                    0 <= row < self._table_model.rowCount()
                    and 0 <= col < self._table_model.columnCount()
                ):
                    # Get the actual row index if we're using filtered data
                    actual_row = row
                    if self._filtered_rows and row < len(self._filtered_rows):
                        actual_row = self._filtered_rows[row]

                    column_name = self._data_model.column_names[col]
                    self._data_model.update_cell(actual_row, column_name, text)
            except Exception as e:
                logger.error(f"Error updating data model directly: {e}")

            logger.info(
                f"Pasted value to single cell at row {index.row()}, column {index.column()}"
            )
        else:
            logger.warning("Paste operation failed: No valid cell selected")
            return

    @Slot()
    def _on_data_changed(self) -> None:
        """
        Update the view when the data model changes.

        This method ensures the view is always updated when the data model changes,
        with protections against recursive updates.
        """
        try:
            # Ignore the signal if we're already updating to avoid recursion
            if self._is_updating:
                logger.debug("Ignoring data_changed signal - UI already updating")
                return

            # Force view update on data change - remove debouncing for initial load
            logger.info("Processing data_changed signal - updating view")
            self._update_view()

        except Exception as e:
            logger.error(f"Error updating view on data change: {str(e)}")

    @Slot(object)
    def _on_validation_changed(self, validation_status) -> None:
        """
        Handle validation changed signal.

        Args:
            validation_status: The validation status.
        """
        # Update the view to reflect validation changes
        self._on_data_changed()

    @Slot(object)
    def _on_correction_applied(self, correction_status) -> None:
        """
        Handle correction applied signal.

        Args:
            correction_status: The correction status.
        """
        # Update the view to reflect correction changes
        self._on_data_changed()

    @Slot(QStandardItem)
    def _on_item_changed(self, item: QStandardItem) -> None:
        """
        Update the data model when an item in the view changes.

        Args:
            item: The item that changed.
        """
        try:
            # Ignore item changes if we're currently updating
            if self._is_updating:
                logger.debug("Ignoring item change during view update")
                return

            # Get the row and column of the changed item
            row = item.row()
            column = item.column()

            # If we have a valid row and column
            if row >= 0 and column >= 0 and column < len(self._data_model.column_names):
                # Get the new value from the item - use item.text() instead of item.data()
                # This avoids the Qt.EditRole vs int role issue
                new_value = item.text()

                # Get the column name for this column index
                column_name = self._data_model.column_names[column]

                # Get the current value from the model first
                try:
                    current_value = self._data_model.get_cell_value(row, column_name)
                except Exception as e:
                    logger.error(f"Error getting current cell value: {str(e)}")
                    return

                # Check if the value has actually changed
                if str(current_value) == str(new_value):
                    logger.debug(
                        f"Skipping cell update at [{row}, {column_name}] - value unchanged"
                    )
                    return

                logger.debug(
                    f"Updating cell at [{row}, {column_name}] from '{current_value}' to '{new_value}'"
                )

                # Use a more efficient update method that doesn't recreate the DataFrame
                success = self._data_model.update_cell(row, column_name, new_value)

                if not success:
                    logger.error(f"Failed to update cell at [{row}, {column_name}]")
                    # Reload the item to show the original value
                    self._is_updating = True
                    try:
                        # Use setText instead of setData to avoid the role issue
                        item.setText(str(current_value))
                    finally:
                        self._is_updating = False

        except Exception as e:
            logger.error(f"Error handling item change: {str(e)}")

    def _apply_table_styling(self) -> None:
        """Apply additional styling to ensure table content is visible."""
        # Set text color explicitly via stylesheet
        self._table_view.setStyleSheet("""
            QTableView {
                color: white;
                background-color: #1A2C42;
                gridline-color: #4A5568;
                selection-background-color: #D4AF37;
                selection-color: #1A2C42;
            }
            QTableView::item {
                color: white;
                background-color: #1A2C42;
            }
            QTableView::item:alternate {
                background-color: #2D3748;
            }
            QTableView::item:selected {
                color: #1A2C42;
                background-color: #D4AF37;
            }
        """)

        # Make sure the model has appropriate default foreground color
        self._table_model.setItemPrototype(QStandardItem())
        prototype = self._table_model.itemPrototype()
        if prototype:
            prototype.setForeground(QColor("white"))

    def _copy_selected_cells(self) -> None:
        """Copy the currently selected cell(s) to clipboard."""
        selected_indexes = self._table_view.selectedIndexes()
        if not selected_indexes:
            return

        # If only one cell is selected, use the existing copy function
        if len(selected_indexes) == 1:
            self._copy_cell(selected_indexes[0])
            return

        # For multiple cells, we could implement more advanced copying in the future
        # For now, just copy the first selected cell
        self._copy_cell(selected_indexes[0])
        logger.info(f"Copied first of {len(selected_indexes)} selected cells")

    def _paste_to_selected_cells(self) -> None:
        """Paste clipboard content to the currently selected cell(s)."""
        logger.info("Paste shortcut activated")

        # First check if we have data in the table
        if self._data_model.is_empty or self._table_model.rowCount() == 0:
            logger.warning("Paste operation failed: No data in table")
            self._status_label.setText("Cannot paste: No data in table")
            return

        # Ensure table has focus for proper visual feedback
        self._table_view.setFocus()

        # Get currently selected cells
        selected_indexes = self._table_view.selectedIndexes()

        # Get the clipboard text
        clipboard_text = QApplication.clipboard().text().strip()
        if not clipboard_text:
            logger.warning("Paste operation failed: Clipboard is empty")
            self._status_label.setText("Cannot paste: Clipboard is empty")
            return

        # If no cells are selected, try to use the current cell or select the first cell
        if not selected_indexes:
            logger.warning("No cells explicitly selected for paste operation")

            current_index = self._table_view.currentIndex()
            if current_index.isValid():
                logger.info(
                    f"Using current cell at [{current_index.row()}, {current_index.column()}]"
                )
                self._paste_cell(current_index)
                self._status_label.setText("Pasted to current cell")
            else:
                # If no current cell, select the first cell if data exists
                if self._table_model.rowCount() > 0 and self._table_model.columnCount() > 0:
                    logger.info("Selecting first cell for paste operation")
                    first_index = self._table_model.index(0, 0)
                    self._table_view.setCurrentIndex(first_index)
                    self._table_view.selectionModel().select(
                        first_index, self._table_view.selectionModel().SelectCurrent
                    )
                    self._paste_cell(first_index)
                    self._status_label.setText("Pasted to first cell")
                else:
                    logger.warning("No data in table - cannot paste")
                    self._status_label.setText("Cannot paste: No valid target cells")
            return

        # Log number of cells that will receive the pasted value
        logger.info(f"Pasting to {len(selected_indexes)} selected cells")

        # Use an empty QModelIndex for the first parameter because we're not
        # responding to a context menu click but to a keyboard shortcut
        self._paste_cell(QModelIndex())

        # Update status label with paste confirmation
        if len(selected_indexes) == 1:
            self._status_label.setText("Pasted to selected cell")
        else:
            self._status_label.setText(f"Pasted to {len(selected_indexes)} selected cells")

    def eventFilter(self, watched, event):
        """
        Event filter to capture keyboard events from table view.

        Args:
            watched: The object being watched.
            event: The event that occurred.

        Returns:
            True if the event was handled, False to pass it on.
        """
        # Only process events for the table view
        if watched is self._table_view:
            # Check for key press events
            if event.type() == event.Type.KeyPress:
                key_event = event
                # Check for Ctrl+V (paste)
                if key_event.matches(QKeySequence.Paste):
                    logger.info("Captured Ctrl+V via table view event filter")
                    self._paste_to_selected_cells()
                    return True
                # Check for Ctrl+C (copy)
                elif key_event.matches(QKeySequence.Copy):
                    logger.info("Captured Ctrl+C via table view event filter")
                    self._copy_selected_cells()
                    return True

        # Pass the event on to the standard event processing
        return super().eventFilter(watched, event)
