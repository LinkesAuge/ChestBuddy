"""
DataView module.

This module provides the DataView class for displaying and editing CSV data.
"""

import logging
from typing import Dict, List, Optional, Any

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
        # Clear the table model
        self._table_model.clear()

        # Check if data is empty
        if self._data_model.is_empty:
            self._status_label.setText("No data loaded")
            self._filtered_rows = []  # Initialize to empty list when no data
            return

        # Get data from model
        data = self._data_model.data

        # Initialize filtered_rows with all row indices
        self._filtered_rows = data.index.tolist()

        # Set headers
        self._table_model.setHorizontalHeaderLabels(self._data_model.column_names)

        # Populate filter column combo box
        current_column = self._filter_column.currentText()
        self._filter_column.clear()
        self._filter_column.addItems(self._data_model.column_names)

        # Restore selected column if it exists
        if current_column in self._data_model.column_names:
            self._filter_column.setCurrentText(current_column)

        # Add data to the table model
        for row_idx, row in enumerate(data.itertuples()):
            # Skip the first element (index)
            row_data = list(row)[1:]
            for col_idx, value in enumerate(row_data):
                item = QStandardItem(str(value))

                # Get column name
                column_name = self._data_model.column_names[col_idx]

                # Set validation and correction status as user data
                # Use cell-specific methods to avoid getting entire DataFrames
                # This prevents recursion issues
                val_status = self._data_model.get_cell_validation_status(row_idx, column_name)
                if val_status:
                    item.setData(val_status, Qt.UserRole + 1)

                corr_status = self._data_model.get_cell_correction_status(row_idx, column_name)
                if corr_status:
                    item.setData(corr_status, Qt.UserRole + 2)

                self._table_model.setItem(row_idx, col_idx, item)

        # Resize columns to contents
        self._table_view.resizeColumnsToContents()

        # Update status label
        row_count = len(data)
        self._status_label.setText(f"Loaded {row_count} rows")

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
        # Store filtered data
        self._filtered_data = filtered_data

        # Clear the table model
        self._table_model.clear()

        # Check if filtered data is empty
        if filtered_data.empty:
            self._status_label.setText("No data matches the filter")
            self._filtered_rows = []
            return

        # Set headers
        self._table_model.setHorizontalHeaderLabels(self._data_model.column_names)

        # Store the filtered row indices
        self._filtered_rows = filtered_data.index.tolist()

        # Show filter status
        filter_text = self._filter_text.text()
        if filter_text:
            filter_count = len(filtered_data)
            total_count = len(self._data_model.data)
            self._status_label.setText(
                f"Showing {filter_count} of {total_count} records matching '{filter_text}'"
            )

        # Add filtered data to the table model
        for local_row_idx, (actual_row_idx, row) in enumerate(
            zip(filtered_data.index, filtered_data.itertuples())
        ):
            # Skip the first element (index)
            row_data = list(row)[1:]
            for col_idx, value in enumerate(row_data):
                item = QStandardItem(str(value))

                # Get column name
                column_name = self._data_model.column_names[col_idx]

                # Set validation and correction status as user data
                # Use cell-specific methods to avoid getting entire DataFrames
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

        # Resize columns to contents
        self._table_view.resizeColumnsToContents()

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
        Handle data changed signal.
        """
        # Update the view
        if self._current_filter:
            # Reapply filter
            column = self._current_filter.get("column", "")
            filter_text = self._current_filter.get("text", "")
            filter_mode = self._current_filter.get("mode", "Contains")
            case_sensitive = self._current_filter.get("case_sensitive", False)

            filtered_data = self._data_model.filter_data(
                column, filter_text, filter_mode, case_sensitive
            )

            if filtered_data is not None:
                self._update_view_with_filtered_data(filtered_data)
        else:
            # Update with all data
            self._update_view()

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
        Handle changes to items in the table.

        Args:
            item: The changed item.
        """
        # Get the row and column index
        row = item.row()
        col = item.column()

        # If we're using a filtered view, we need to map the row to the actual row
        actual_row = row
        if hasattr(self, "_filtered_data") and self._filtered_data is not None:
            # Map from visible row to actual row
            actual_row = self._filtered_data.index[row]
        else:
            actual_row = row

        # Get the column name
        column_name = self._data_model.column_names[col]

        # Get the new value
        value = item.text()

        # Use the more efficient update_cell method instead of creating a whole new DataFrame
        # This prevents the pandas recursion issue by avoiding full DataFrame recreation
        self._data_model.update_cell(actual_row, column_name, value)
