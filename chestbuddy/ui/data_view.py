"""
DataView module.

This module provides the DataView class for displaying and editing CSV data.
"""

import logging
from typing import Dict, List, Optional, Any
import time

import pandas as pd
from PySide6.QtCore import Qt, Signal, Slot
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
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction, QColor

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

        # Apply additional styling to ensure visibility
        self._apply_table_styling()

        splitter.addWidget(self._table_view)

        # Set splitter sizes
        splitter.setSizes([100, 500])

        main_layout.addWidget(splitter)

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
                # Process rows in batches to avoid deep recursion
                BATCH_SIZE = 100
                for start_idx in range(0, len(data), BATCH_SIZE):
                    end_idx = min(start_idx + BATCH_SIZE, len(data))
                    logger.debug(f"Processing batch from index {start_idx} to {end_idx}")

                    # Process this batch of rows
                    for row_idx in range(start_idx, end_idx):
                        # Get row data directly using iloc to avoid itertuples() which can cause recursion
                        row_data = data.iloc[row_idx]

                        # Log sample of row data for debugging
                        if row_idx < 3:  # Only log first few rows to avoid flooding logs
                            logger.debug(f"Row {row_idx} data: {row_data.to_dict()}")

                        for col_idx, column_name in enumerate(column_names):
                            # Get value directly and convert to string
                            value = str(row_data[column_name])
                            if row_idx < 3 and col_idx < 3:  # Only log some values
                                logger.debug(
                                    f"Cell [{row_idx}, {col_idx}] ({column_name}): '{value}'"
                                )

                            item = QStandardItem(value)

                            # Explicitly set foreground color to ensure text visibility
                            item.setForeground(QColor("#FFFFFF"))  # White text

                            # Set validation and correction status as user data
                            val_status = self._data_model.get_cell_validation_status(
                                row_idx, column_name
                            )
                            if val_status:
                                item.setData(val_status, Qt.UserRole + 1)

                            corr_status = self._data_model.get_cell_correction_status(
                                row_idx, column_name
                            )
                            if corr_status:
                                item.setData(corr_status, Qt.UserRole + 2)

                            self._table_model.setItem(row_idx, col_idx, item)

                logger.info(f"Added {self._table_model.rowCount()} rows to table model")
            except Exception as e:
                logger.error(f"Error populating table model: {e}")
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
                # Process rows in batches
                BATCH_SIZE = 100
                # Get the row indices and convert to a plain list to avoid pandas operations
                all_indices = list(zip(range(len(filtered_data)), filtered_data.index))

                for batch_start in range(0, len(all_indices), BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, len(all_indices))
                    batch_indices = all_indices[batch_start:batch_end]

                    for local_row_idx, actual_row_idx in batch_indices:
                        # Get the row data directly
                        row_data = filtered_data.iloc[local_row_idx]

                        for col_idx, column_name in enumerate(column_names):
                            # Convert value to string
                            value = str(row_data[column_name])
                            item = QStandardItem(value)

                            # Explicitly set foreground color to ensure text visibility
                            item.setForeground(QColor("#FFFFFF"))  # White text

                            # Set validation and correction status
                            val_status = self._data_model.get_cell_validation_status(
                                actual_row_idx, column_name
                            )
                            if val_status:
                                item.setData(val_status, Qt.UserRole + 1)

                            corr_status = self._data_model.get_cell_correction_status(
                                actual_row_idx, column_name
                            )
                            if corr_status:
                                item.setData(corr_status, Qt.UserRole + 2)

                            self._table_model.setItem(local_row_idx, col_idx, item)
            except Exception as e:
                logger.error(f"Error populating filtered table model: {e}")
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
        Paste clipboard text to the cell.

        Args:
            index: The index of the cell to paste to.
        """
        if not index.isValid():
            return

        # Get the text from clipboard
        text = QApplication.clipboard().text()

        # Set the value
        self._table_model.setData(index, text, Qt.EditRole)

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
                # Get the new value from the item
                new_value = item.data(Qt.EditRole)

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
                        item.setData(Qt.DisplayRole, str(current_value))
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
