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
from chestbuddy.ui.widgets.action_toolbar import ActionToolbar
from chestbuddy.ui.widgets.action_button import ActionButton

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

    # Define signals
    import_clicked = Signal()  # Emitted when the import button is clicked
    export_clicked = Signal()  # Emitted when the export button is clicked
    selection_changed = Signal(list)  # Emitted when selection changes with list of selected rows
    filter_changed = Signal(dict)  # Emitted when filter criteria change
    data_edited = Signal(int, int, object)  # Row, column, new value
    data_corrected = Signal(list)  # List of correction operations
    data_removed = Signal(list)  # List of row indices removed
    status_updated = Signal(str, bool)  # Status message, is_error

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
        self._auto_update_enabled = True  # Enable auto-update by default
        self._population_in_progress = False  # Track if table population is in progress

        # Set up UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Initial update
        self._update_view()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for a more compact look

        # Create a container for the toolbar and filters
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(8)

        # Create ActionToolbar for grouped actions
        self._action_toolbar = ActionToolbar(spacing=8)

        # Data operations group
        self._action_toolbar.start_group("Data")
        self._action_toolbar.add_button(
            ActionButton("Import", name="import", tooltip="Import new data")
        )
        self._action_toolbar.add_button(
            ActionButton("Export", name="export", tooltip="Export current data")
        )
        self._action_toolbar.end_group()

        # Filter operations group
        self._action_toolbar.start_group("Filter")
        self._action_toolbar.add_button(
            ActionButton("Apply", name="apply_filter", tooltip="Apply the current filter")
        )
        self._action_toolbar.add_button(
            ActionButton("Clear", name="clear_filter", tooltip="Clear all filters")
        )
        self._action_toolbar.end_group()

        # View operations group
        self._action_toolbar.start_group("View")
        self._action_toolbar.add_button(
            ActionButton("Refresh", name="refresh", tooltip="Refresh the data view")
        )
        self._action_toolbar.end_group()

        header_layout.addWidget(self._action_toolbar)

        # Compact filter controls in a horizontal layout
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        # Column selector with label
        column_container = QWidget()
        column_layout = QHBoxLayout(column_container)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(4)
        column_layout.addWidget(QLabel("Column:"))
        self._filter_column = QComboBox()
        self._filter_column.setMinimumWidth(150)
        column_layout.addWidget(self._filter_column)
        filter_layout.addWidget(column_container)

        # Filter text with label
        text_container = QWidget()
        text_layout = QHBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        text_layout.addWidget(QLabel("Value:"))
        self._filter_text = QLineEdit()
        self._filter_text.setPlaceholderText("Enter filter text...")
        self._filter_text.setMinimumWidth(200)
        text_layout.addWidget(self._filter_text)
        filter_layout.addWidget(text_container)

        # Filter mode with label
        mode_container = QWidget()
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(4)
        mode_layout.addWidget(QLabel("Mode:"))
        self._filter_mode = QComboBox()
        self._filter_mode.addItems(["Contains", "Equals", "Starts with", "Ends with"])
        mode_layout.addWidget(self._filter_mode)
        filter_layout.addWidget(mode_container)

        # Case sensitive checkbox
        self._case_sensitive = QCheckBox("Case sensitive")
        filter_layout.addWidget(self._case_sensitive)

        # Add flexible space
        filter_layout.addStretch()

        # Status label aligned to the right
        self._status_label = QLabel("No data loaded")
        filter_layout.addWidget(self._status_label)

        header_layout.addWidget(filter_container)

        # Add header container to main layout
        main_layout.addWidget(header_container)

        # Table view with minimal spacing
        self._table_view = QTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.verticalHeader().setDefaultSectionSize(24)  # Compact rows
        self._table_view.verticalHeader().setVisible(True)

        # Install event filter on table view to capture key events
        self._table_view.installEventFilter(self)
        logger.info("Installed event filter on table view")

        # Enable keyboard shortcuts for copy/paste
        self._setup_shortcuts()

        # Apply additional styling to ensure visibility
        self._apply_table_styling()

        # Add table view directly to main layout for maximum space
        main_layout.addWidget(self._table_view)
        main_layout.setStretch(1, 1)  # Give table view all available space

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

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect action buttons
        import_button = self._action_toolbar.get_button_by_name("import")
        if import_button:
            logger.debug("Connecting import button clicked signal to _on_import_clicked handler")
            import_button.clicked.connect(self._on_import_clicked)

        export_button = self._action_toolbar.get_button_by_name("export")
        if export_button:
            logger.debug("Connecting export button clicked signal to _on_export_clicked handler")
            export_button.clicked.connect(self._on_export_clicked)

        # Connect filter controls
        filter_button = self._action_toolbar.get_button_by_name("apply_filter")
        if filter_button:
            filter_button.clicked.connect(self._apply_filter)

        clear_button = self._action_toolbar.get_button_by_name("clear_filter")
        if clear_button:
            clear_button.clicked.connect(self._clear_filter)

        # Connect and install event filter on the table view for key events
        self._table_view.installEventFilter(self)
        logger.info("Installed event filter on table view")

        # Register custom shortcuts since the event filter might not capture all key combinations
        # Create a shortcut for copying (table-specific)
        self._copy_shortcut = QShortcut(QKeySequence.Copy, self._table_view)
        self._copy_shortcut.activated.connect(self._copy_selected_cells)
        logger.info("Registered Ctrl+C shortcut for copying (table-specific)")

        # Create a shortcut for pasting (widget-level)
        self._paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self._paste_shortcut.activated.connect(self._paste_to_selected_cells)
        logger.info("Registered widget-level Ctrl+V shortcut for pasting (widget hierarchy)")

        # Connect table model for data editing
        if isinstance(self._table_model, QStandardItemModel):
            self._table_model.itemChanged.connect(self._on_item_changed)

        # Connect to model signals for updates
        if hasattr(self._data_model, "data_changed"):
            self._data_model.data_changed.connect(self._on_data_changed)
        if hasattr(self._data_model, "validation_changed"):
            self._data_model.validation_changed.connect(self._on_validation_changed)
        if hasattr(self._data_model, "correction_applied"):
            self._data_model.correction_applied.connect(self._on_correction_applied)

    def _update_view(self) -> None:
        """Update the view with current data."""
        # Guard against recursive calls
        if self._is_updating:
            print("Skipping recursive _update_view call")
            logger.debug("Skipping recursive _update_view call")
            return

        # Skip if population is already in progress
        if self._population_in_progress:
            print("Skipping _update_view call - population already in progress")
            logger.debug("Skipping _update_view call - population already in progress")
            return

        try:
            self._is_updating = True
            self._population_in_progress = True  # Set flag that population is starting
            print("Starting _update_view method")
            logger.info("Starting _update_view method")

            # Clear the table model
            self._table_model.clear()
            print("Cleared table model")

            # Check if data is empty
            if self._data_model.is_empty:
                print("Data model is empty, no data to display")
                logger.info("Data model is empty, no data to display")
                self._status_label.setText("No data loaded")
                self._filtered_rows = []  # Initialize to empty list when no data
                self._is_updating = False
                self._population_in_progress = False  # Clear flag when aborting early
                print("_update_view aborted: No data in model")
                return

            # Temporarily disable sorting and selection during population
            self._table_view.setSortingEnabled(False)
            self._table_view.setEnabled(False)

            try:
                # Get data from model - get a shallow copy to avoid modifying original
                data = self._data_model.data
                print(f"Got data from model: {len(data)} rows, columns: {list(data.columns)}")
                logger.info(f"Got data from model: {len(data)} rows, columns: {list(data.columns)}")

                # Get column names
                column_names = list(data.columns)

                # Set table dimensions
                self._table_model.setColumnCount(len(column_names))
                self._table_model.setRowCount(len(data))
                print(f"Set table model dimensions: {len(data)} rows, {len(column_names)} columns")
                logger.info(
                    f"Set table model dimensions: {len(data)} rows, {len(column_names)} columns"
                )

                # Set headers
                self._table_model.setHorizontalHeaderLabels(column_names)
                print(f"Set horizontal headers: {column_names}")

                # Update status to show we're populating the table
                self._status_label.setText(f"Populating table with {len(data)} records...")
                QApplication.processEvents()  # Process events to update status

                # Define chunk size for table population
                CHUNK_SIZE = 500  # Number of rows to process before yielding to UI
                UPDATE_FREQUENCY = 50  # Update progress display every N rows

                # Populate table with data in chunks
                total_rows = len(data)
                processed_rows = 0

                print(
                    f"Starting to populate table with {total_rows} rows in chunks of {CHUNK_SIZE}"
                )
                logger.info(
                    f"Starting to populate table with {total_rows} rows in chunks of {CHUNK_SIZE}"
                )

                # Process data in chunks to maintain UI responsiveness
                try:
                    # Check visibility once at the beginning and store it
                    should_continue = True
                    print(
                        f"Initial widget visibility check: Widget exists={bool(self)}, isVisible={self.isVisible() if self else False}"
                    )

                    # Track if application is shutting down
                    app = QApplication.instance()

                    for chunk_start in range(0, total_rows, CHUNK_SIZE):
                        # Check if application is shutting down
                        if not app or app.closingDown():
                            print("Application is shutting down, stopping table population")
                            should_continue = False
                            break

                        # Calculate end of chunk (bounded by total rows)
                        chunk_end = min(chunk_start + CHUNK_SIZE, total_rows)

                        print(f"Processing chunk from {chunk_start} to {chunk_end}")

                        # Process this chunk of rows
                        for row_idx in range(chunk_start, chunk_end):
                            # Only do emergency visibility checks every 100 rows to avoid overhead
                            if row_idx % 100 == 0:
                                # Check if application is shutting down
                                if not app or app.closingDown():
                                    print("Application is shutting down, stopping table population")
                                    should_continue = False
                                    break

                                # Use a much more conservative check - only abort for complete widget destruction
                                if not self:
                                    print("Widget completely destroyed, stopping population")
                                    should_continue = False
                                    break

                            try:
                                for col_idx, col_name in enumerate(column_names):
                                    value = data.iloc[row_idx, col_idx]
                                    text = "" if pd.isna(value) else str(value)
                                    self._table_model.setItem(row_idx, col_idx, QStandardItem(text))

                                # Update processed count
                                processed_rows += 1

                                # Update progress display at regular intervals
                                if (
                                    processed_rows % UPDATE_FREQUENCY == 0
                                    or processed_rows == total_rows
                                ):
                                    progress_pct = int((processed_rows / total_rows) * 100)
                                    self._status_label.setText(
                                        f"Populating table: {progress_pct}% ({processed_rows}/{total_rows})"
                                    )
                                    # Let the UI update more frequently for progress display
                                    QApplication.processEvents()
                            except Exception as row_error:
                                print(f"Error processing row {row_idx}: {row_error}")
                                # Continue with next row
                                continue

                        # Check if we should continue after this chunk
                        if not should_continue:
                            break

                        # Let the UI update between chunks
                        QApplication.processEvents()
                        print(f"Finished chunk, processed {processed_rows}/{total_rows} rows")

                except Exception as chunk_error:
                    print(f"Error during chunk processing: {chunk_error}")
                    import traceback

                    traceback.print_exc()
                    # Continue with what we have

                print(f"Table population complete. Processed {processed_rows}/{total_rows} rows")

                # Store filtered rows
                self._filtered_rows = list(range(len(data)))

                # Update filter column combo
                self._filter_column.clear()
                self._filter_column.addItems(column_names)

                # Update status
                if processed_rows < total_rows:
                    self._status_label.setText(
                        f"Loaded {processed_rows} of {total_rows} records (incomplete)"
                    )
                else:
                    self._status_label.setText(f"Loaded {processed_rows} records")

            except Exception as e:
                print(f"Error getting/displaying data: {e}")
                self._status_label.setText("Error loading data")
                import traceback

                traceback.print_exc()
            finally:
                # ALWAYS re-enable the table view when done, even if there was an error
                if self:  # Just check if the widget still exists
                    try:
                        self._table_view.setEnabled(True)
                        self._table_view.setSortingEnabled(True)
                        print("Table view re-enabled")
                    except Exception as enable_error:
                        print(f"Error re-enabling table: {enable_error}")
                        traceback.print_exc()

        except Exception as e:
            logger.error(f"Error in _update_view: {e}")
            print(f"Error in _update_view: {e}")
        finally:
            self._is_updating = False
            self._population_in_progress = False  # Clear flag when population is done
            print("_update_view completed")
            logger.info("_update_view completed")

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
        """Handle data model changes."""
        logger.debug("DataView._on_data_changed called")
        print("DataView._on_data_changed called!")

        # Skip if auto-update is disabled
        if not self._auto_update_enabled:
            logger.debug("Auto-update disabled, skipping table update")
            print("Auto-update disabled, skipping table update")
            return

        # Add debug logging to verify data model state
        has_data = not self._data_model.is_empty
        data_shape = (
            "empty"
            if self._data_model.is_empty
            else f"{len(self._data_model.data)} rows x {len(self._data_model.column_names)} columns"
        )
        print(f"Data model state in _on_data_changed: has_data={has_data}, shape={data_shape}")
        logger.debug(
            f"Data model state in _on_data_changed: has_data={has_data}, shape={data_shape}"
        )

        # Rate-limit updates to prevent UI freezing
        current_time = time.time() * 1000
        time_since_last_update = current_time - self._last_update_time

        if time_since_last_update < self._update_debounce_ms:
            logger.debug(
                f"Skipping update due to rate limiting: {time_since_last_update}ms < {self._update_debounce_ms}ms"
            )
            print(
                f"Skipping update due to rate limiting: {time_since_last_update}ms < {self._update_debounce_ms}ms"
            )
            return

        print("Forcing _update_view call from _on_data_changed")
        # Force update the view
        self._update_view()
        self._last_update_time = current_time
        print("_update_view completed from _on_data_changed")
        logger.debug("_update_view completed from _on_data_changed")

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

    def _on_import_clicked(self):
        """Handle import button click."""
        # Simply emit the signal to be handled by the adapter
        self.import_clicked.emit()

    def _on_export_clicked(self):
        """Handle export button click."""
        # Simply emit the signal to be handled by the adapter
        self.export_clicked.emit()

    def populate_table(self) -> None:
        """Populate the table with data from the data model."""
        # Check if population is already in progress
        if self._population_in_progress:
            logger.debug("Table population already in progress, skipping duplicate call")
            return

        # Use the existing _update_view method to do the actual population
        self._update_view()

    def enable_auto_update(self) -> None:
        """Enable automatic table updates on data changes."""
        logger.info("DataView auto-update enabled")
        self._auto_update_enabled = True

    def disable_auto_update(self) -> None:
        """Disable automatic table updates on data changes."""
        logger.info("DataView auto-update disabled")
        self._auto_update_enabled = False
