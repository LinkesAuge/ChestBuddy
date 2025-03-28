"""
DataView module.

This module provides the DataView class for displaying and editing CSV data.
"""

import logging
from typing import Dict, List, Optional, Any
import time

import pandas as pd
from PySide6.QtCore import Qt, Signal, Slot, QModelIndex, QTimer, QSortFilterProxyModel
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
from chestbuddy.ui.widgets.validation_delegate import ValidationStatusDelegate
from chestbuddy.core.validation_enums import ValidationStatus

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

    # Column names used across the application
    PLAYER_COLUMN = "PLAYER"
    SOURCE_COLUMN = "SOURCE"
    CHEST_COLUMN = "CHEST"
    SCORE_COLUMN = "SCORE"
    CLAN_COLUMN = "CLAN"
    STATUS_COLUMN = "STATUS"
    DATE_COLUMN = "DATE"

    # Filter delay in milliseconds
    FILTER_DELAY_MS = 300

    def __init__(self, data_model: ChestDataModel, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the DataView widget.

        Args:
            data_model: Data model to display
            parent: Parent widget
        """
        # Call parent init first
        super().__init__(parent)

        # Initialize the data model
        self._data_model = data_model

        # Create a QStandardItemModel for the table
        self._table_model = QStandardItemModel(self)

        # Initialize filter state
        self._filter_text = ""
        self._filtered_data = None
        self._filtered_rows = None

        # Initialize state tracking variables
        self._is_updating = False
        self._population_in_progress = False
        self._initial_load = True

        # Initialize the table header columns based on data_model columns
        self._columns = (
            self._data_model.column_names if hasattr(self._data_model, "column_names") else []
        )
        self._columns.append(self.STATUS_COLUMN)

        # Track which columns are visible (initially all)
        self._visible_columns = [
            self.DATE_COLUMN,
            self.PLAYER_COLUMN,
            self.SOURCE_COLUMN,
            self.CHEST_COLUMN,
            self.SCORE_COLUMN,
            self.CLAN_COLUMN,
            self.STATUS_COLUMN,
        ]

        # Set up the UI components
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Set up the table view
        self.populate_table()

    @Slot()
    def _on_data_cleared(self) -> None:
        """Handle data cleared signal."""
        # Reset the table model
        if self._table_model:
            self._table_model.clear()
            self._table_model.setHorizontalHeaderLabels(self._visible_columns)

        # Reset filter
        self._filter_text = ""
        self._filtered_data = None
        self._filtered_rows = None

        # Reset UI elements
        if hasattr(self, "_filter_input") and self._filter_input:
            self._filter_input.setText("")

        # Reset the validation status of all cells to None - no styling
        for row in range(self._table_model.rowCount()):
            for col in range(self._table_model.columnCount()):
                item = self._table_model.item(row, col)
                if item:
                    item.setData(None, Qt.UserRole + 1)

        logger.debug("Data view reset after data cleared")

    @Slot()
    def _on_data_changed(self, data_state=None) -> None:
        """
        Handle data changed signal.

        Args:
            data_state: The current data state
        """
        try:
            logger.debug("Handling data changed in DataView")

            # Get data from the model
            if not hasattr(self._data_model, "data") or self._data_model.data is None:
                logger.warning("No data available in data model")
                return

            # Update the view
            self._update_view()

        except Exception as e:
            logger.error(f"Error handling data changed: {e}")

    def _apply_filter(self) -> None:
        """Apply the current filter text to the data."""
        try:
            # Cancel if no data model
            if not self._has_valid_models():
                return

            # Emit the filter changed signal with the current filter text
            self.filter_changed.emit(self._filter_text)

            # Get the data to filter
            if not hasattr(self._data_model, "data") or self._data_model.data is None:
                logger.warning("No data available to filter")
                return

            # Start with a copy of the original data
            original_data = self._data_model.data

            # If no filter, use all data
            if not self._filter_text:
                self._filtered_data = None
                self._filtered_rows = None
                self._update_view_with_filtered_data(original_data)
                return

            # Apply the filter across all columns
            filtered_rows = []
            filter_lower = self._filter_text.lower()

            # For each row in the data
            for i, row in original_data.iterrows():
                # Check if any cell in this row contains the filter text
                match_found = False
                for col, value in row.items():
                    # Convert value to string and check if it contains the filter text
                    if pd.notna(value):
                        str_value = str(value).lower()
                        if filter_lower in str_value:
                            match_found = True
                            break

                # If a match was found, add this row to the filtered list
                if match_found:
                    filtered_rows.append(i)

            # No matches found
            if not filtered_rows:
                # Show empty table
                self._filtered_data = original_data.iloc[0:0]
                self._filtered_rows = []
                self._update_view_with_filtered_data(self._filtered_data)
                logger.debug("No matches found for filter")
                return

            # Update with filtered data
            self._filtered_data = original_data.iloc[filtered_rows]
            self._filtered_rows = filtered_rows
            self._update_view_with_filtered_data(self._filtered_data)
            logger.debug(f"Applied filter, showing {len(filtered_rows)} rows")

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            # Reset filter state
            self._filtered_data = None
            self._filtered_rows = None

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
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.horizontalHeader().setStretchLastSection(
            False
        )  # Change to False to allow manual sizing
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.verticalHeader().setDefaultSectionSize(24)  # Compact rows
        self._table_view.verticalHeader().setVisible(True)

        # Enable sorting on the table view
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSortIndicatorShown(True)

        # Disable text wrapping in the view
        self._table_view.setWordWrap(False)
        self._table_view.setTextElideMode(Qt.ElideRight)  # Show ellipsis for cut-off text

        # Set up custom delegate for validation visualization
        self._validation_delegate = ValidationStatusDelegate(self)
        self._table_view.setItemDelegate(self._validation_delegate)

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

        # Connect table view for sorting
        self._table_view.horizontalHeader().sortIndicatorChanged.connect(
            self._on_sort_indicator_changed
        )

        # Connect to model signals for updates
        if hasattr(self._data_model, "data_changed"):
            self._data_model.data_changed.connect(self._on_data_changed)
        if hasattr(self._data_model, "validation_changed"):
            self._data_model.validation_changed.connect(self._on_validation_changed)
        if hasattr(self._data_model, "correction_applied"):
            self._data_model.correction_applied.connect(self._on_correction_applied)

    def _update_view(self) -> None:
        """
        Update the view with the current data model content.
        Handles data display, filtering, and highlighting.
        """
        if self._is_updating:
            logger.debug("Already updating, skipping _update_view call")
            return

        # Process before starting update
        QApplication.processEvents()

        try:
            self._is_updating = True
            print("DataView._update_view: Starting update")

            # Check if the model is empty
            if self._data_model.is_empty:
                self._table_model.clear()
                self._update_status("No data loaded")
                return

            # Use the populate_table method to fully populate the table
            self.populate_table()

            print("DataView._update_view: Update complete")

        except Exception as e:
            msg = f"Error updating view: {str(e)}"
            logger.error(msg)
            self._update_status(msg, True)

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
                                    # Get validation columns from validation_status DataFrame if available
                                    validation_columns = []
                                    validation_status = None
                                    if hasattr(self._data_model, "get_validation_status"):
                                        validation_status = self._data_model.get_validation_status()
                                        if (
                                            isinstance(validation_status, pd.DataFrame)
                                            and not validation_status.empty
                                        ):
                                            validation_columns = [
                                                col
                                                for col in validation_status.columns
                                                if col.endswith("_valid")
                                            ]

                                    # Debug logging for validation status
                                    logger.debug(
                                        f"Cell [{actual_row_idx},{column_name}] validation status: {val_status}"
                                    )
                                    logger.debug(
                                        f"Validation columns available: {validation_columns}"
                                    )
                                    if validation_status is not None and isinstance(
                                        validation_status, pd.DataFrame
                                    ):
                                        logger.debug(
                                            f"Validation status DataFrame shape: {validation_status.shape}"
                                        )

                                    # Convert the validation status dictionary to a ValidationStatus enum value
                                    # Check if there's a validation column for this column
                                    val_column = f"{column_name}_valid"
                                    if val_column in validation_columns:
                                        # Check if we have validation data for this cell
                                        if val_column in validation_status.columns and not pd.isna(
                                            validation_status.iloc[actual_row_idx].get(
                                                val_column, None
                                            )
                                        ):
                                            cell_is_valid = validation_status.iloc[actual_row_idx][
                                                val_column
                                            ]
                                            logger.debug(
                                                f"Cell [{actual_row_idx},{column_name}] has validation data: valid={cell_is_valid}"
                                            )

                                            # If the validation status is False, set as INVALID
                                            if not cell_is_valid:
                                                # Only mark validatable columns as INVALID
                                                if column_name in ["PLAYER", "SOURCE", "CHEST"]:
                                                    logger.debug(
                                                        f"Setting cell [{actual_row_idx},{column_name}] to INVALID"
                                                    )
                                                    item.setData(
                                                        ValidationStatus.INVALID, Qt.UserRole + 1
                                                    )
                                                else:
                                                    # Non-validatable columns should never be INVALID
                                                    logger.debug(
                                                        f"Setting non-validatable cell [{actual_row_idx},{column_name}] to INVALID_ROW instead of INVALID"
                                                    )
                                                    item.setData(
                                                        ValidationStatus.INVALID_ROW,
                                                        Qt.UserRole + 1,
                                                    )
                                            else:
                                                logger.debug(
                                                    f"Setting cell [{actual_row_idx},{column_name}] to VALID"
                                                )
                                                item.setData(
                                                    ValidationStatus.VALID, Qt.UserRole + 1
                                                )
                                        else:
                                            # No validation status available
                                            logger.debug(
                                                f"No validation data for cell [{actual_row_idx},{column_name}]"
                                            )
                                            item.setData(None, Qt.UserRole + 1)
                                    else:
                                        # Just store the original validation status dictionary
                                        logger.debug(
                                            f"Using original validation status for cell [{actual_row_idx},{column_name}]: {val_status}"
                                        )
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
            else:
                logger.warning("No data in table - cannot verify content")
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

        # Add validation-related options
        if index.isValid():
            # Get column and value
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
                cell_value = self._table_model.data(index, Qt.DisplayRole)

                # Get validation status for this cell
                validation_status = index.data(Qt.ItemDataRole.UserRole + 1)

                # Add option to add to validation list if this is a validation-related column
                validation_columns = {
                    "PLAYER": "player",
                    "CHEST": "chest",
                    "SOURCE": "source",
                }

                if (
                    column_name in validation_columns
                    and validation_status == ValidationStatus.INVALID
                ):
                    # Add separator
                    context_menu.addSeparator()

                    # Add action to add to validation list
                    field_type = validation_columns[column_name]
                    add_action = QAction(
                        f"Add '{cell_value}' to {field_type.title()} validation list", self
                    )
                    add_action.triggered.connect(
                        lambda checked=False,
                        ft=field_type,
                        val=cell_value: self._add_to_validation_list(ft, val)
                    )
                    context_menu.addAction(add_action)

        # Show the menu
        context_menu.exec_(self._table_view.viewport().mapToGlobal(position))

    def _add_to_validation_list(self, field_type: str, value: str) -> None:
        """
        Add a value to the validation list.

        Args:
            field_type: The type of field (player, chest, source)
            value: The value to add to the validation list
        """
        if not value or not field_type:
            return

        # Emit signal for adding to validation list
        # This will be connected to a controller or service that handles the actual addition
        self.status_updated.emit(f"Adding '{value}' to {field_type} validation list...", False)

        # The actual addition will happen in the controller or service
        # We'll emit a signal that will be handled by the data view controller
        self.data_corrected.emit(
            [{"action": "add_to_validation", "field_type": field_type, "value": value}]
        )

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

    @Slot(int, Qt.SortOrder)
    def _on_sort_indicator_changed(self, logical_index: int, order: Qt.SortOrder) -> None:
        """
        Handle changes in the sort indicator using the built-in QTableView sorting capability.

        Args:
            logical_index: The column index being sorted
            order: The sort order (ascending or descending)
        """
        # Skip sorting during initial load or if population is in progress
        if self._initial_load or self._population_in_progress:
            logger.debug("Skipping sort during initial load or population")
            return

        # Set flag to indicate this is a user-initiated sort
        self._user_initiated_sort = True

        try:
            # Get the column name for the logical index
            column_name = self._table_model.headerData(logical_index, Qt.Horizontal)
            if not column_name:
                logger.warning(f"Cannot sort: No column name for index {logical_index}")
                return

            logger.debug(
                f"User requested sorting by column {column_name} (index {logical_index}), order: {order}"
            )

            # Let the built-in sorting handle the display
            # The table is already in sortable state because setSortingEnabled(True) was called in _init_ui

        except Exception as e:
            logger.error(f"Error during sort indicator change: {e}")
        finally:
            self._user_initiated_sort = False  # Reset the user-initiated sort flag

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
                    actual_row = row
                    if self._filtered_rows and row < len(self._filtered_rows):
                        actual_row = self._filtered_rows[row]

                    current_value = self._data_model.get_cell_value(actual_row, column_name)
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
                actual_row = row
                if self._filtered_rows and row < len(self._filtered_rows):
                    actual_row = self._filtered_rows[row]

                success = self._data_model.update_cell(actual_row, column_name, new_value)

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
                gridline-color: transparent;
                selection-background-color: #D4AF37;
                selection-color: #1A2C42;
            }
            QTableView::item {
                color: white;
                /* No background color to allow delegate painting to show through */
                padding: 12px;
            }
            QTableView::item:alternate {
                /* Very subtle alternating row color that won't interfere with validation highlighting */
                background-color: rgba(45, 55, 72, 40);
            }
            QTableView::item:selected {
                color: #1A2C42;
                background-color: #D4AF37;
            }
        """)

        # Re-enable alternating row colors with subtle effect
        self._table_view.setAlternatingRowColors(True)

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
        """Populate the table with data from the data model, using chunking for performance."""
        if self._is_updating or self._population_in_progress:
            logger.debug("Skipping population since update or population is in progress")
            return

        try:
            self._is_updating = True
            self._population_in_progress = True
            self._initial_load = True  # Set initial load flag to true

            # Get the data and columns to use
            data = self._data_model.data
            columns = self._data_model.column_names

            if data is None or data.empty or not columns:
                logger.warning("No data or columns available to populate table")
                self._update_status("No data available")
                self._is_updating = False
                self._population_in_progress = False
                return

            # Clear the model and reset it with correct dimensions
            self._table_model.clear()
            self._table_model.setHorizontalHeaderLabels(columns)

            # Set dimensions for the table model
            row_count = len(data)
            col_count = len(columns)
            self._table_model.setRowCount(row_count)
            self._table_model.setColumnCount(col_count)

            # Prepare for chunked population
            self._chunk_columns = columns
            self._chunk_data = data
            self._chunk_row_count = row_count
            self._chunk_col_count = col_count
            self._chunk_size = min(500, row_count)  # Process 500 rows at a time
            self._chunk_start = 0

            # Start the chunked population process - use immediate processing for the first chunk
            self._populate_chunk()

        except Exception as e:
            logger.error(f"Error populating table: {e}")
            self._update_status(f"Error: {str(e)}", True)
            self._is_updating = False
            self._population_in_progress = False

    def _populate_chunk(self):
        """Populate one chunk of data to the table."""
        try:
            if not hasattr(self, "_chunk_start"):
                logger.error("Error in _populate_chunk: _chunk_start attribute not found")
                self._is_updating = False
                self._population_in_progress = False
                return

            # Get current chunk boundaries
            chunk_start = self._chunk_start
            chunk_end = min(chunk_start + self._chunk_size, self._chunk_row_count)

            logger.debug(
                f"Populating chunk from {chunk_start} to {chunk_end} of {self._chunk_row_count} rows"
            )

            # Get the data for the current chunk
            column_names = self._chunk_columns

            # Process only the current chunk of data
            if hasattr(self, "_chunk_data") and self._chunk_data is not None:
                data_subset = self._chunk_data.iloc[chunk_start:chunk_end]

                # Convert to a format that's faster to iterate
                values = data_subset.to_dict("records")

                # Batch creation of items for better performance
                for i, row_data in enumerate(values):
                    row_idx = chunk_start + i
                    for col_idx, col_name in enumerate(column_names):
                        # Get value with proper None/NaN handling
                        cell_value = row_data.get(col_name, "")
                        str_value = (
                            ""
                            if cell_value is None
                            or (isinstance(cell_value, float) and pd.isna(cell_value))
                            else str(cell_value)
                        )

                        # Create the item and add it to the model
                        item = QStandardItem(str_value)
                        self._table_model.setItem(row_idx, col_idx, item)
            else:
                logger.error("_chunk_data attribute is missing or None")
                self._is_updating = False
                self._population_in_progress = False
                return

            # Check if we've processed all rows
            if chunk_end >= self._chunk_row_count:
                logger.debug(f"Chunk population complete: {self._chunk_row_count} rows processed")
                self._is_updating = False
                self._population_in_progress = False
                self._finalize_population()
                return

            # Update for next chunk
            self._chunk_start = chunk_end

            # Schedule the next chunk with a small delay to keep UI responsive
            QTimer.singleShot(5, self._populate_chunk)

        except Exception as e:
            logger.error(f"Error in chunk population: {e}")
            self._update_status(f"Error: {str(e)}", True)
            self._is_updating = False
            self._population_in_progress = False

    def _finalize_population(self):
        """Finalize the population process."""
        self._ensure_no_text_wrapping()
        self._customize_column_widths()
        self._update_status_from_row_count()
        self._initial_load = False  # Reset initial load flag

    def _ensure_no_text_wrapping(self):
        """Ensure that text does not wrap in table cells."""
        # Disable word wrap at the view level
        if hasattr(self, "_table_view") and self._table_view is not None:
            # Set the text elide mode for the header to ensure no wrapping
            header = self._table_view.horizontalHeader()
            if header is not None:
                # Set a reasonable default section size to reduce need for wrapping
                header.setDefaultSectionSize(120)
                # Ensure header text does not wrap
                header.setTextElideMode(Qt.ElideRight)

            # Set word wrap to false for the table view
            self._table_view.setWordWrap(False)
            # Set text elide mode to ensure text is ellipsized
            self._table_view.setTextElideMode(Qt.ElideRight)

    def _customize_column_widths(self):
        """
        Customize column widths based on content type.

        Sets appropriate widths for each column type:
        - Fixed width for player, source, and chest columns
        - Smaller width for status, score and clan columns
        - Default width for other columns
        """
        if not hasattr(self, "_table_view") or self._table_view is None:
            logger.warning("Cannot customize column widths: TableView not available")
            return

        # Get the header view
        header = self._table_view.horizontalHeader()
        if not header:
            logger.warning("Cannot customize column widths: Header view not available")
            return

        # Make sure the header sections can be resized by the user
        header.setSectionResizeMode(QHeaderView.Interactive)

        # Define default widths
        default_column_widths = {
            self.PLAYER_COLUMN: 200,
            self.SOURCE_COLUMN: 200,
            self.CHEST_COLUMN: 200,
            self.STATUS_COLUMN: 60,
            self.SCORE_COLUMN: 80,
            self.CLAN_COLUMN: 80,
        }

        # First, try to set column widths by indices from the model
        for col in range(self._table_model.columnCount()):
            column_name = self._table_model.headerData(col, Qt.Horizontal)
            if column_name in default_column_widths:
                width = default_column_widths[column_name]
                self._table_view.setColumnWidth(col, width)
                logger.debug(f"Set {column_name} column (index {col}) width to {width}px")

        # If we have the PLAYER column in our list but it's not in the model,
        # make sure the STATUS column is still properly sized if it exists
        status_col = self._get_column_index(self.STATUS_COLUMN)
        if status_col >= 0:
            self._table_view.setColumnWidth(status_col, default_column_widths[self.STATUS_COLUMN])
            logger.debug(
                f"Set STATUS column (index {status_col}) width to {default_column_widths[self.STATUS_COLUMN]}px"
            )

    def _get_column_index(self, column_name: str, default: int = -1) -> int:
        """
        Get the index of a column by name.

        Args:
            column_name: Name of the column to find
            default: Default value to return if column not found

        Returns:
            Index of the column or default value if not found
        """
        if not hasattr(self, "_table_model") or self._table_model is None:
            return default

        # Search for column in the model
        for col in range(self._table_model.columnCount()):
            header_data = self._table_model.headerData(col, Qt.Horizontal)
            if header_data == column_name:
                return col

        # If column not found in model but exists in columns list
        if column_name in self._columns:
            return self._columns.index(column_name)

        return default

    def _update_status(self, message: str, is_error: bool = False) -> None:
        """
        Update the status message displayed in the view.

        Args:
            message: Status message to display
            is_error: Whether this is an error message (adds styling)
        """
        if not hasattr(self, "_status_label"):
            logger.warning("Status label not available, cannot update status")
            return

        try:
            # Set the text
            self._status_label.setText(message)

            # Apply error styling if needed
            if is_error:
                self._status_label.setStyleSheet("color: #FF5555; font-weight: bold;")
            else:
                self._status_label.setStyleSheet("")

            logger.debug(f"Status updated: {message}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")

    def enable_auto_update(self) -> None:
        """Enable automatic table updates on data changes."""
        logger.info("DataView auto-update enabled")
        self._auto_update_enabled = True

    def disable_auto_update(self) -> None:
        """Disable automatic table updates on data changes."""
        logger.info("DataView auto-update disabled")
        self._auto_update_enabled = False

    def _update_status_from_row_count(self):
        """Update the status display based on the current row count."""
        if hasattr(self, "_table_model") and self._table_model is not None:
            row_count = self._table_model.rowCount()
            if row_count > 0:
                self._update_status(f"Showing all {row_count} rows")
            else:
                self._update_status("No data loaded")

    def _ensure_status_column(self) -> None:
        """Ensure the status column exists in the table model."""
        if not hasattr(self, "_table_model") or self._table_model is None:
            return

        # Check if STATUS_COLUMN exists in columns
        if self.STATUS_COLUMN not in self._columns:
            self._columns.append(self.STATUS_COLUMN)

        # Get the current column count
        col_idx = self._table_model.columnCount()

        # If there are no columns yet, add a header with just the STATUS_COLUMN
        # This ensures STATUS_COLUMN exists even when no data is loaded
        if col_idx == 0:
            logger.debug("No columns in table model, adding STATUS_COLUMN header")
            self._table_model.setColumnCount(1)
            self._table_model.setHeaderData(0, Qt.Horizontal, self.STATUS_COLUMN)
            return

        # Check if the STATUS_COLUMN already exists
        has_status_column = False
        for i in range(col_idx):
            if self._table_model.headerData(i, Qt.Horizontal) == self.STATUS_COLUMN:
                has_status_column = True
                break

        # If STATUS_COLUMN doesn't exist, add it
        if not has_status_column:
            logger.debug(f"Adding STATUS_COLUMN at column index {col_idx}")
            self._table_model.insertColumn(col_idx)
            self._table_model.setHeaderData(col_idx, Qt.Horizontal, self.STATUS_COLUMN)

            # Populate with "Not validated" values
            for row in range(self._table_model.rowCount()):
                index = self._table_model.index(row, col_idx)
                self._table_model.setData(index, "Not validated")

    def _has_valid_models(self) -> bool:
        """Check if both data model and table model are valid.

        Returns:
            bool: True if both models are valid, False otherwise.
        """
        return (
            hasattr(self, "_data_model")
            and self._data_model is not None
            and hasattr(self, "_table_model")
            and self._table_model is not None
        )

    @Slot(object)
    def _on_validation_changed(self, validation_status=None) -> None:
        """
        Handle validation changed signal with optimized updates.

        Args:
            validation_status: The validation status.
        """
        try:
            # Check if we have valid models
            if not self._has_valid_models():
                logger.warning("Cannot update validation status: Invalid models")
                return

            logger.debug("Handling validation changed in DataView")

            # Get the model's validation status if not provided
            if validation_status is None and hasattr(self._data_model, "get_validation_status"):
                try:
                    validation_status = self._data_model.get_validation_status()
                    logger.debug(f"Got validation status: {type(validation_status)}")
                except Exception as e:
                    logger.error(f"Error getting validation status: {e}")
                    return

            # Ensure status column exists
            self._ensure_status_column()

            # Get status column index
            status_col = self._get_column_index(self.STATUS_COLUMN)
            if status_col < 0:
                logger.error("Status column not found in table model")
                return

            # Initialize dictionary to track cells that need updating
            cells_to_update = {}

            # Track rows with invalid status
            invalid_rows = []

            # Define validatable columns (for specifically invalid cells)
            validatable_columns = ["PLAYER", "SOURCE", "CHEST"]

            # Process the validation status
            if isinstance(validation_status, pd.DataFrame) and not validation_status.empty:
                # Get validation columns (ending with _valid)
                validation_columns = [
                    col for col in validation_status.columns if col.endswith("_valid")
                ]
                logger.debug(f"Found validation columns: {validation_columns}")

                # Create a set to track which rows we've processed
                processed_rows = set()

                # For each row in the validation DataFrame
                for row_idx in range(len(validation_status)):
                    # Track if this row has any invalid value
                    row_has_invalid = False
                    invalid_column_names = []

                    # Check each validation column for this row
                    for val_col in validation_columns:
                        # Skip NaN values
                        if pd.isna(validation_status.iloc[row_idx].get(val_col, None)):
                            continue

                        # Check if this validation column failed
                        if not validation_status.iloc[row_idx][val_col]:
                            row_has_invalid = True
                            # Get the original column name by removing _valid suffix
                            orig_column = val_col.replace("_valid", "")
                            invalid_column_names.append(orig_column)

                    # Use a filtered index for display row lookup
                    filtered_idx = self._get_filtered_row_index(row_idx)
                    if filtered_idx < 0:
                        continue  # Skip if not in filtered view

                    # Mark this row as processed
                    processed_rows.add(filtered_idx)

                    # Update status column for all rows
                    if row_has_invalid:
                        # Add row to invalid rows list
                        invalid_rows.append(row_idx)

                        # Update status cell to "Invalid"
                        if status_col >= 0:
                            # Only update if needed
                            status_item = self._table_model.item(filtered_idx, status_col)
                            if status_item and status_item.data(Qt.DisplayRole) != "Invalid":
                                cells_to_update[(filtered_idx, status_col)] = ("Invalid", None)

                        # Process each column in the row
                        for col_idx in range(self._table_model.columnCount()):
                            if col_idx == status_col:
                                continue  # Skip status column

                            column_name = self._table_model.headerData(col_idx, Qt.Horizontal)
                            item = self._table_model.item(filtered_idx, col_idx)
                            if not item:
                                continue  # Skip if item doesn't exist

                            # Get current validation status for this cell
                            current_status = item.data(Qt.UserRole + 1)

                            # Check if this column has validation issues
                            if column_name in invalid_column_names:
                                # This is a specifically invalid cell
                                if column_name in validatable_columns:
                                    # Only update if needed (status changed)
                                    if current_status != ValidationStatus.INVALID:
                                        cells_to_update[(filtered_idx, col_idx)] = (
                                            None,
                                            ValidationStatus.INVALID,
                                        )
                                else:
                                    # Non-validatable columns should never be INVALID
                                    if current_status != ValidationStatus.INVALID_ROW:
                                        cells_to_update[(filtered_idx, col_idx)] = (
                                            None,
                                            ValidationStatus.INVALID_ROW,
                                        )
                            else:
                                # This is just a cell in an invalid row
                                if current_status != ValidationStatus.INVALID_ROW:
                                    cells_to_update[(filtered_idx, col_idx)] = (
                                        None,
                                        ValidationStatus.INVALID_ROW,
                                    )
                    else:
                        # This row is valid
                        # Only update status column to "Valid"
                        if status_col >= 0:
                            status_item = self._table_model.item(filtered_idx, status_col)
                            if status_item and status_item.data(Qt.DisplayRole) != "Valid":
                                cells_to_update[(filtered_idx, status_col)] = ("Valid", None)

                        # For cells that were previously marked as invalid, just clear the status
                        # Don't set to ValidationStatus.VALID - let them use normal table styling
                        for col_idx in range(self._table_model.columnCount()):
                            if col_idx == status_col:
                                continue  # Skip status column

                            item = self._table_model.item(filtered_idx, col_idx)
                            if not item:
                                continue  # Skip if item doesn't exist

                            # Get current validation status for this cell
                            current_status = item.data(Qt.UserRole + 1)

                            # Only clear the status if it was previously set
                            if current_status is not None:
                                cells_to_update[(filtered_idx, col_idx)] = (None, None)

                # For any processed valid rows, clear validation status from cells
                # This ensures any rows that were previously invalid but are now valid have their styling cleared
                for row in range(self._table_model.rowCount()):
                    if row in processed_rows:
                        continue  # Skip rows we've already processed

                    # Get the actual row index in the data model
                    if self._filtered_rows:
                        if row >= len(self._filtered_rows):
                            continue
                        actual_row_idx = self._filtered_rows[row]
                    else:
                        actual_row_idx = row

                    # If the row is in the validation status DataFrame, ensure it appears as valid
                    if actual_row_idx < len(validation_status):
                        # Set status to Valid
                        if status_col >= 0:
                            status_item = self._table_model.item(row, status_col)
                            if status_item and status_item.data(Qt.DisplayRole) != "Valid":
                                cells_to_update[(row, status_col)] = ("Valid", None)

                        # Clear any existing validation status from cells
                        for col_idx in range(self._table_model.columnCount()):
                            if col_idx == status_col:
                                continue  # Skip status column

                            item = self._table_model.item(row, col_idx)
                            if not item:
                                continue

                            # Get current validation status for this cell
                            current_status = item.data(Qt.UserRole + 1)

                            # Only clear status if it was previously set
                            if current_status is not None:
                                cells_to_update[(row, col_idx)] = (None, None)
            else:
                # Unknown validation_status type, log error
                logger.error(f"Unknown validation_status type: {type(validation_status)}")
                # Set all to "Not validated" - being selective even in this case
                for row in range(self._table_model.rowCount()):
                    status_item = self._table_model.item(row, status_col)
                    if status_item and status_item.data(Qt.DisplayRole) != "Not validated":
                        cells_to_update[(row, status_col)] = ("Not validated", None)

                    # Reset validation status for all cells in this row, but only if needed
                    for col in range(self._table_model.columnCount()):
                        if col == status_col:
                            continue  # Skip status column

                        item = self._table_model.item(row, col)
                        if item:
                            current_status = item.data(Qt.UserRole + 1)
                            # Only update if the cell has a validation status
                            if current_status is not None:
                                cells_to_update[(row, col)] = (None, None)

            # Now apply all the updates we've collected
            logger.debug(f"Applying {len(cells_to_update)} selective updates to cells")
            for (row, col), (display_value, user_role_value) in cells_to_update.items():
                item = self._table_model.item(row, col)
                if not item:
                    continue

                # Update display value if provided
                if display_value is not None:
                    self._table_model.setData(self._table_model.index(row, col), display_value)

                # Update user role value if provided
                if (
                    user_role_value is not None
                    or user_role_value is None
                    and item.data(Qt.UserRole + 1) is not None
                ):
                    item.setData(user_role_value, Qt.UserRole + 1)

            # Additional diagnostic logging
            logger.debug(
                f"Found {len(invalid_rows)} invalid rows: {invalid_rows[:10]}{'...' if len(invalid_rows) > 10 else ''}"
            )

            # Make the view update - just once after all changes
            self._table_view.viewport().update()
            logger.debug("Optimized validation status update complete")

        except Exception as e:
            logger.error(f"Error updating validation status in data view: {e}", exc_info=True)

    @Slot(object)
    def _on_correction_applied(self, correction_status) -> None:
        """
        Handle correction applied signal.

        Args:
            correction_status: The correction status.
        """
        # Update the view to reflect correction changes
        self._on_data_changed()

    def _highlight_invalid_rows(self, invalid_rows: List[int]) -> None:
        """
        Highlight rows with validation issues using selective updates.

        Args:
            invalid_rows: List of row indices that have validation issues
        """
        try:
            if not self._has_valid_models() or not invalid_rows:
                return

            logger.debug(f"Highlighting {len(invalid_rows)} invalid rows")

            # Get status column index
            status_col = self._get_column_index(self.STATUS_COLUMN)

            # Define validatable columns
            validatable_columns = ["PLAYER", "SOURCE", "CHEST"]

            # Get validation status dataframe if available
            validation_status_df = None
            validation_columns = []
            if hasattr(self._data_model, "get_validation_status"):
                try:
                    validation_status_df = self._data_model.get_validation_status()
                    if (
                        isinstance(validation_status_df, pd.DataFrame)
                        and not validation_status_df.empty
                    ):
                        validation_columns = [
                            col for col in validation_status_df.columns if col.endswith("_valid")
                        ]
                        logger.debug(f"Found validation columns: {validation_columns}")
                except Exception as e:
                    logger.error(f"Error getting validation status: {e}")

            # Track cells that need to be updated
            cells_to_update = {}

            # For each invalid row, we need to process it
            for row_idx in invalid_rows:
                # Convert from data model row index to view row index
                filtered_idx = self._get_filtered_row_index(row_idx)
                if filtered_idx < 0:
                    continue  # Skip if not in filtered view

                # Make sure the status cell shows "Invalid" if it's not already set
                if status_col >= 0:
                    status_item = self._table_model.item(filtered_idx, status_col)
                    if status_item and status_item.data(Qt.DisplayRole) != "Invalid":
                        cells_to_update[(filtered_idx, status_col)] = ("Invalid", None)

                # Find which specific columns are invalid
                specific_invalid_columns = []
                if validation_status_df is not None and not validation_status_df.empty:
                    try:
                        # Check which specific columns are invalid in this row
                        for val_col in validation_columns:
                            # Only proceed if this validation column exists and the row exists in the validation data
                            if (
                                val_col in validation_status_df.columns
                                and row_idx < len(validation_status_df)
                                and not pd.isna(
                                    validation_status_df.iloc[row_idx].get(val_col, None)
                                )
                            ):
                                # Check if this specific validation failed (is False)
                                if not validation_status_df.iloc[row_idx][val_col]:
                                    # Get the original column name by removing _valid suffix
                                    orig_column = val_col.replace("_valid", "")
                                    specific_invalid_columns.append(orig_column)
                                    value = self._data_model.data.iloc[row_idx].get(
                                        orig_column, "N/A"
                                    )
                                    # Use repr() for safe logging of Unicode values
                                    safe_value = repr(value) if value is not None else "None"
                                    logger.debug(
                                        f"Row {row_idx} has invalid column: {orig_column}={safe_value}"
                                    )
                    except Exception as e:
                        logger.error(f"Error processing validation status for row {row_idx}: {e}")

                # If we couldn't identify specific invalid columns but the row is invalid,
                # mark the row as invalid but don't mark any specific cells
                if not specific_invalid_columns:
                    logger.debug(
                        f"No specific invalid columns identified for row {row_idx}, marking row as invalid"
                    )

                # Now update the cells with the appropriate status
                for col in range(self._table_model.columnCount()):
                    if col == status_col:
                        continue  # Skip status column

                    item = self._table_model.item(filtered_idx, col)
                    if not item:
                        continue  # Skip if item doesn't exist

                    # Get current validation status
                    current_status = item.data(Qt.UserRole + 1)
                    column_name = self._table_model.headerData(col, Qt.Horizontal)

                    if column_name in specific_invalid_columns:
                        # This is a specifically invalid cell
                        if column_name in validatable_columns:
                            # Only update if needed
                            if current_status != ValidationStatus.INVALID:
                                value = item.data(Qt.DisplayRole)
                                # Use repr() for safe logging of Unicode values
                                safe_value = repr(value) if value is not None else "None"
                                logger.debug(
                                    f"Setting ValidationStatus.INVALID for cell [{filtered_idx},{col}] ({column_name}={safe_value})"
                                )
                                cells_to_update[(filtered_idx, col)] = (
                                    None,
                                    ValidationStatus.INVALID,
                                )
                        else:
                            # Non-validatable columns should never be INVALID
                            if current_status != ValidationStatus.INVALID_ROW:
                                logger.debug(
                                    f"Setting ValidationStatus.INVALID_ROW for non-validatable cell [{filtered_idx},{col}] ({column_name})"
                                )
                                cells_to_update[(filtered_idx, col)] = (
                                    None,
                                    ValidationStatus.INVALID_ROW,
                                )
                    else:
                        # This is just a cell in an invalid row, but not specifically invalid
                        if current_status != ValidationStatus.INVALID_ROW:
                            value = item.data(Qt.DisplayRole)
                            # Use repr() for safe logging of Unicode values
                            safe_value = repr(value) if value is not None else "None"
                            logger.debug(
                                f"Setting ValidationStatus.INVALID_ROW for cell [{filtered_idx},{col}] ({column_name}={safe_value})"
                            )
                            cells_to_update[(filtered_idx, col)] = (
                                None,
                                ValidationStatus.INVALID_ROW,
                            )

            # Apply all the updates we've collected
            logger.debug(
                f"Applying {len(cells_to_update)} selective updates to cells for highlighting"
            )
            for (row, col), (display_value, user_role_value) in cells_to_update.items():
                item = self._table_model.item(row, col)
                if not item:
                    continue

                # Update display value if provided
                if display_value is not None:
                    self._table_model.setData(self._table_model.index(row, col), display_value)

                # Update user role value if provided
                if (
                    user_role_value is not None
                    or user_role_value is None
                    and item.data(Qt.UserRole + 1) is not None
                ):
                    item.setData(user_role_value, Qt.UserRole + 1)

            # Force a single redraw of the view
            self._table_view.viewport().update()
            logger.debug("Optimized invalid row highlighting complete")

        except Exception as e:
            logger.error(f"Error highlighting invalid rows: {e}", exc_info=True)

    def _get_filtered_row_index(self, model_row_idx: int) -> int:
        """
        Convert a data model row index to a view row index, accounting for filtering.

        Args:
            model_row_idx: The row index in the data model

        Returns:
            The corresponding row index in the filtered view, or -1 if the row is not in the view
        """
        # Skip rows outside the data range
        if model_row_idx < 0 or (
            hasattr(self._data_model, "data") and model_row_idx >= len(self._data_model.data)
        ):
            return -1

        # If filtering is active, map the data model index to the filtered index
        if self._filtered_rows:
            try:
                # Find this row in the filtered rows list
                filtered_idx = self._filtered_rows.index(model_row_idx)
                return filtered_idx
            except ValueError:
                # Row is not in filtered view
                return -1
        else:
            # No filtering, use the row index directly
            return model_row_idx

    def _clear_validation_cache(self) -> None:
        """
        Clear the validation state cache to prevent memory leaks.
        This should be called when data is reset, filtered, or any other operation
        that might change the row indices.
        """
        logger.debug("Clearing validation state cache")
        self._previous_validation_states = {}

    @Slot()
    def _on_data_cleared(self) -> None:
        """Handle data cleared signal."""
        # Reset the table model
        if self._table_model:
            self._table_model.clear()
            self._table_model.setHorizontalHeaderLabels(self._visible_columns)

        # Reset filter
        self._filter_text = ""
        self._filtered_data = None
        self._filtered_rows = None

        # Clear validation cache
        self._clear_validation_cache()

        # Reset UI elements
        if hasattr(self, "_filter_input") and self._filter_input:
            self._filter_input.setText("")

        # Reset the validation status of all cells to None - no styling
        for row in range(self._table_model.rowCount()):
            for col in range(self._table_model.columnCount()):
                item = self._table_model.item(row, col)
                if item:
                    item.setData(None, Qt.UserRole + 1)

        logger.debug("Data view reset after data cleared")

    @Slot()
    def _on_data_changed(self, data_state=None) -> None:
        """
        Handle data changed signal.

        Args:
            data_state: The current data state
        """
        try:
            logger.debug("Handling data changed in DataView")

            # Clear validation cache when data changes
            self._clear_validation_cache()

            # Get data from the model
            if not hasattr(self._data_model, "data") or self._data_model.data is None:
                logger.warning("No data available in data model")
                return

            # Update the view
            self._update_view()

        except Exception as e:
            logger.error(f"Error handling data changed: {e}")

    def _apply_filter(self) -> None:
        """Apply the current filter text to the data."""
        try:
            # Cancel if no data model
            if not self._has_valid_models():
                return

            # Emit the filter changed signal with the current filter text
            self.filter_changed.emit(self._filter_text)

            # Get the data to filter
            if not hasattr(self._data_model, "data") or self._data_model.data is None:
                logger.warning("No data available to filter")
                return

            # Start with a copy of the original data
            original_data = self._data_model.data

            # If no filter, use all data
            if not self._filter_text:
                self._filtered_data = None
                self._filtered_rows = None
                self._update_view_with_filtered_data(original_data)
                return

            # Clear validation cache when filter changes
            self._clear_validation_cache()

            # Apply the filter across all columns
            filtered_rows = []
            filter_lower = self._filter_text.lower()

            # For each row in the data
            for i, row in original_data.iterrows():
                # Check if any cell in this row contains the filter text
                match_found = False
                for col, value in row.items():
                    # Convert value to string and check if it contains the filter text
                    if pd.notna(value):
                        str_value = str(value).lower()
                        if filter_lower in str_value:
                            match_found = True
                            break

                # If a match was found, add this row to the filtered list
                if match_found:
                    filtered_rows.append(i)

            # No matches found
            if not filtered_rows:
                # Show empty table
                self._filtered_data = original_data.iloc[0:0]
                self._filtered_rows = []
                self._update_view_with_filtered_data(self._filtered_data)
                logger.debug("No matches found for filter")
                return

            # Update with filtered data
            self._filtered_data = original_data.iloc[filtered_rows]
            self._filtered_rows = filtered_rows
            self._update_view_with_filtered_data(self._filtered_data)
            logger.debug(f"Applied filter, showing {len(filtered_rows)} rows")

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            # Reset filter state
            self._filtered_data = None
            self._filtered_rows = None
