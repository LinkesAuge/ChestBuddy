"""
DataView module.

This module provides the DataView class for displaying and editing CSV data.
"""

import logging
import time
import re
from typing import Dict, List, Optional, Tuple, Set, Any
import pandas as pd

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QTimer,
    QModelIndex,
    QSortFilterProxyModel,
    QRegularExpression,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QPushButton,
    QMenu,
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QGroupBox,
    QMessageBox,
    QDialog,
    QApplication,
)
from PySide6.QtGui import (
    QColor,
    QBrush,
    QPalette,
    QFont,
    QStandardItemModel,
    QStandardItem,
    QClipboard,
    QKeySequence,
    QShortcut,
    QAction,
)

from chestbuddy.core.enums.validation_enums import ValidationStatus, ValidationMode
from chestbuddy.ui.widgets.action_toolbar import ActionToolbar, ActionButton
from chestbuddy.ui.widgets.validation_delegate import ValidationStatusDelegate
from chestbuddy.ui.dialogs.add_edit_rule_dialog import AddEditRuleDialog
from chestbuddy.ui.dialogs.batch_correction_dialog import BatchCorrectionDialog
from chestbuddy.ui.dialogs.import_export_dialog import ImportExportDialog
from chestbuddy.ui.resources.style import Colors
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.table_state_manager import TableStateManager, CellState

# Set up logger
logger = logging.getLogger(__name__)

# Constants


class CustomFilterProxyModel(QSortFilterProxyModel):
    """
    Custom filter proxy model for QTableView that provides more flexible filtering.

    This proxy model allows filtering by specific column or across all columns,
    with support for different filter modes (contains, equals, etc.) and
    case sensitivity.

    Implementation Notes:
        - Extends QSortFilterProxyModel
        - Provides custom filtering logic
        - Optimized for large datasets
    """

    def __init__(self, parent=None):
        """Initialize the proxy model."""
        super().__init__(parent)
        self._filter_column = -1  # -1 means filter all columns
        self._filter_text = ""
        self._filter_mode = "Contains"  # Contains, Equals, Starts with, Ends with
        self._case_sensitive = False
        self._regex = QRegularExpression()
        self._regex.setPatternOptions(QRegularExpression.CaseInsensitiveOption)

    def set_filter_settings(
        self, column_index: int, filter_text: str, filter_mode: str, case_sensitive: bool
    ):
        """
        Set the filter settings for this proxy model.

        Args:
            column_index: The column to filter on (-1 for all columns)
            filter_text: The text to filter by
            filter_mode: The filter mode (Contains, Equals, Starts with, Ends with)
            case_sensitive: Whether the filter is case sensitive
        """
        self._filter_column = column_index
        self._filter_text = filter_text
        self._filter_mode = filter_mode
        self._case_sensitive = case_sensitive

        # Set regex pattern options
        self._regex.setPattern(self._get_regex_pattern())
        options = QRegularExpression.NoPatternOption
        if not self._case_sensitive:
            options |= QRegularExpression.CaseInsensitiveOption
        self._regex.setPatternOptions(options)

        # Apply filter
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determine if a row should be included in the filtered data.

        Args:
            source_row: The row in the source model
            source_parent: The parent index

        Returns:
            True if the row should be included, False otherwise
        """
        # If no filter text, show all rows
        if not self._filter_text:
            return True

        # Get source model
        source_model = self.sourceModel()
        if not source_model:
            return True

        # Specific column filter
        if self._filter_column >= 0 and self._filter_column < source_model.columnCount():
            index = source_model.index(source_row, self._filter_column, source_parent)
            return self._text_matches(index)

        # All columns filter - return True if any column matches
        for col in range(source_model.columnCount()):
            index = source_model.index(source_row, col, source_parent)
            if self._text_matches(index):
                return True

        return False

    def _get_regex_pattern(self) -> str:
        """
        Get the regex pattern based on the current filter mode.

        Returns:
            The regex pattern string
        """
        # Escape special characters in filter text
        escaped_text = QRegularExpression.escape(self._filter_text)

        # Create pattern based on filter mode
        if self._filter_mode == "Contains":
            return escaped_text
        elif self._filter_mode == "Equals":
            return f"^{escaped_text}$"
        elif self._filter_mode == "Starts with":
            return f"^{escaped_text}"
        elif self._filter_mode == "Ends with":
            return f"{escaped_text}$"
        else:
            return escaped_text  # Default to Contains

    def _text_matches(self, index: QModelIndex) -> bool:
        """
        Check if the text at the given index matches the filter criteria.

        Args:
            index: The index to check

        Returns:
            True if the text matches, False otherwise
        """
        # Get the text from the model
        data = self.sourceModel().data(index, Qt.DisplayRole)
        if data is None:
            return False

        text = str(data)

        # Empty filter text always matches
        if not self._filter_text:
            return True

        # Use regex for matching (more efficient than multiple string operations)
        match = self._regex.match(text)
        return match.hasMatch()


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
            data_model: The data model to use
            parent: The parent widget
        """
        super().__init__(parent)

        self._data_model = data_model
        self._proxy_model = None
        self._table_model = None
        self._table_view = None
        self._filter_bar = None
        self._search_edit = None
        self._column_selector = None
        self._case_sensitive_checkbox = None
        self._filter_mode_combo = None
        self._status_label = None
        self._validation_tooltip_cache = {}
        self._clear_filter_button = None
        self._refresh_button = None
        self._export_button = None
        self._import_button = None
        self._validation_colors = {}  # Status -> QColor
        self._filtered_row_cache = {}  # Map model rows to filtered rows
        self._model_row_cache = {}  # Map filtered rows to model rows
        self._auto_update_enabled = True
        self._chunk_size = 1000
        self._current_chunk = 0
        self._total_chunks = 0
        self._population_timer = QTimer(self)
        self._table_state_manager = None  # TableStateManager integration
        self._is_updating = False
        self._population_in_progress = False
        self._initial_load = True
        self._visible_columns = []
        self._filtered_rows = None
        self._filtered_data = None
        self._filter_text = ""
        self._filter_criteria = ""
        self._chunk_columns = []
        self._chunk_data = None
        self._chunk_row_count = 0
        self._chunk_col_count = 0
        self._chunk_start = 0

        # Configure timer for chunked population
        self._population_timer.setInterval(10)  # 10ms between chunks
        self._population_timer.timeout.connect(self._populate_chunk)

        # Set up logging
        self._logger = logging.getLogger(__name__)

        # Initialize the User Interface
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Populate the table
        self.populate_table()

    def set_table_state_manager(self, manager):
        """
        Set the table state manager for cell state tracking.

        Args:
            manager: The TableStateManager instance to use
        """
        logger.debug("==== DataView.set_table_state_manager called ====")

        if manager is None:
            logger.warning("Attempted to set None TableStateManager")
            return

        self._table_state_manager = manager
        logger.debug("TableStateManager reference set in DataView")

        # Connect to state_changed signal if available
        if hasattr(manager, "state_changed"):
            try:
                manager.state_changed.connect(self.update_cell_highlighting_from_state)
                logger.debug("Connected to TableStateManager.state_changed signal successfully")
            except Exception as e:
                logger.error(f"Error connecting to TableStateManager.state_changed: {e}")
                import traceback

                logger.error(traceback.format_exc())
        else:
            logger.warning("TableStateManager does not have state_changed signal")

        # Log the integration
        logger.debug("TableStateManager integration with DataView complete")

        # Debug current cell states
        self._debug_print_cell_states()

    def _debug_print_cell_states(self):
        """Debug method to print current cell states."""
        if not hasattr(self, "_table_state_manager") or not self._table_state_manager:
            logger.debug("No TableStateManager available to print cell states")
            return

        invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)

        logger.debug(
            f"Current cell states: {len(invalid_cells)} invalid, "
            f"{len(correctable_cells)} correctable, "
            f"{len(corrected_cells)} corrected"
        )

    def update_cell_highlighting_from_state(self):
        """Update cell highlighting based on the table state manager."""
        logger.debug("==== DataView.update_cell_highlighting_from_state called ====")

        if not self._table_state_manager:
            logger.warning("Cannot update cell highlighting: TableStateManager not available")
            return

        logger.debug("Updating cell highlighting from table state manager")

        # Get cells in different states
        invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)
        processing_cells = self._table_state_manager.get_cells_by_state(CellState.PROCESSING)

        logger.debug(
            f"Found cells to highlight: {len(invalid_cells)} invalid, "
            f"{len(correctable_cells)} correctable, "
            f"{len(corrected_cells)} corrected, "
            f"{len(processing_cells)} processing"
        )

        # Log some sample cells for debugging
        if invalid_cells:
            logger.debug(f"Sample invalid cells (first 3): {invalid_cells[:3]}")
        if correctable_cells:
            logger.debug(f"Sample correctable cells (first 3): {correctable_cells[:3]}")
        if corrected_cells:
            logger.debug(f"Sample corrected cells (first 3): {corrected_cells[:3]}")

        # Define color constants matching our color legend
        invalid_color = QColor(255, 182, 182)  # Light red
        correctable_color = QColor(255, 214, 165)  # Light orange
        corrected_color = QColor(182, 255, 182)  # Light green
        processing_color = QColor(214, 182, 255)  # Light purple

        # Count successfully highlighted cells
        highlighted_count = 0

        # Apply highlighting for each cell type
        for row, col in invalid_cells:
            logger.debug(f"Highlighting invalid cell at ({row}, {col})")
            if self._highlight_cell(row, col, invalid_color):
                highlighted_count += 1

        for row, col in correctable_cells:
            logger.debug(f"Highlighting correctable cell at ({row}, {col})")
            if self._highlight_cell(row, col, correctable_color):
                highlighted_count += 1

        for row, col in corrected_cells:
            logger.debug(f"Highlighting corrected cell at ({row}, {col})")
            if self._highlight_cell(row, col, corrected_color):
                highlighted_count += 1

        for row, col in processing_cells:
            logger.debug(f"Highlighting processing cell at ({row}, {col})")
            if self._highlight_cell(row, col, processing_color):
                highlighted_count += 1

        logger.debug(
            f"Successfully highlighted {highlighted_count} cells out of "
            f"{len(invalid_cells) + len(correctable_cells) + len(corrected_cells) + len(processing_cells)} total"
        )

        # Force the view to refresh after all highlighting is applied
        if hasattr(self, "_table_view") and self._table_view:
            logger.debug("Forcing table view update after highlighting")
            self._table_view.viewport().update()

        logger.debug("Cell highlighting update complete")

    def _highlight_cell(self, row, col, color):
        """
        Highlight a cell with the specified color.

        Args:
            row: Source row index
            col: Source column index
            color: QColor for highlighting

        Returns:
            bool: True if cell was successfully highlighted, False otherwise
        """
        logger.debug(f"_highlight_cell called for ({row}, {col}) with color {color.name()}")

        # Check if we have a valid table model
        if not hasattr(self, "_table_model") or not self._table_model:
            logger.warning("Cannot highlight cell: table model not available")
            return False

        # Check if we have valid row/column indices
        if row < 0 or col < 0:
            logger.warning(f"Invalid negative indices for cell ({row}, {col})")
            return False

        # Track model state
        model_row_count = self._table_model.rowCount()
        model_col_count = self._table_model.columnCount()
        logger.debug(
            f"Current table dimensions: {model_row_count} rows x {model_col_count} columns"
        )

        # Check if row/col are within bounds
        if row >= model_row_count:
            logger.warning(f"Row index {row} is out of bounds (max: {model_row_count - 1})")
            return False

        if col >= model_col_count:
            logger.warning(f"Column index {col} is out of bounds (max: {model_col_count - 1})")
            return False

        # Create the source model index
        source_index = self._table_model.index(row, col)
        if not source_index.isValid():
            logger.warning(f"Invalid source index for cell ({row}, {col})")
            logger.debug(f"Source index validity check failed: {source_index}")
            return False

        # Log index details
        logger.debug(
            f"Source index: row={source_index.row()}, col={source_index.column()}, valid={source_index.isValid()}"
        )

        # Get the item directly from source model first
        try:
            item = self._table_model.itemFromIndex(source_index)
            if not item:
                logger.warning(f"Item not found for valid index at ({row}, {col})")
                # Additional debug to check model state
                logger.debug(
                    f"Model item check: row={row}, col={col}, index valid={source_index.isValid()}"
                )

                # Try to get data directly from model
                data = self._table_model.data(source_index, role=Qt.DisplayRole)
                logger.debug(
                    f"Model contains data at this index: {data is not None}, value: {data}"
                )
                return False

            logger.debug(f"Found item for cell ({row}, {col}): {item}")
        except Exception as e:
            logger.error(f"Exception getting item from index ({row}, {col}): {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

        # Apply highlighting color to the source model item
        try:
            before_color = item.data(Qt.BackgroundRole)
            logger.debug(f"Before setting color - background role data: {before_color}")

            item.setData(color, Qt.BackgroundRole)
            after_color = item.data(Qt.BackgroundRole)
            logger.debug(f"After setting color - background role data: {after_color}")

            logger.debug(f"Applied highlighting to cell ({row}, {col}) with color {color.name()}")

            # Force update for this item
            if hasattr(self, "_table_view") and self._table_view:
                try:
                    # If we have proxy model, map the index
                    if hasattr(self, "_proxy_model") and self._proxy_model:
                        view_index = self._proxy_model.mapFromSource(source_index)
                        logger.debug(
                            f"Mapped to proxy index: valid={view_index.isValid()}, row={view_index.row()}, col={view_index.column()}"
                        )
                        if view_index.isValid():
                            # Update the specific item in the view
                            self._table_view.update(view_index)
                            logger.debug(
                                f"Updated view at proxy index ({view_index.row()}, {view_index.column()})"
                            )
                        else:
                            logger.warning(
                                f"Invalid proxy index after mapping from source index ({row}, {col})"
                            )
                    else:
                        # Update the specific item in the view
                        self._table_view.update(source_index)
                        logger.debug(f"Updated view at source index ({row}, {col})")
                except Exception as e:
                    logger.error(f"Error updating view for cell ({row}, {col}): {e}")
                    import traceback

                    logger.error(traceback.format_exc())
            else:
                logger.warning("No table view available to update")

            return True
        except Exception as e:
            logger.error(f"Error highlighting cell ({row}, {col}): {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def update_tooltips_from_state(self):
        """Update cell tooltips based on the table state manager."""
        if not self._table_state_manager:
            return

        # Get cells with states
        invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
        correctable_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTABLE)
        corrected_cells = self._table_state_manager.get_cells_by_state(CellState.CORRECTED)

        # Update tooltips for cells with details
        for row, col in invalid_cells + correctable_cells + corrected_cells:
            detail = self._table_state_manager.get_cell_details(row, col)
            if detail:
                self._set_cell_tooltip(row, col, detail)

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

    @Slot(object)
    def _on_validation_changed(self, validation_status: pd.DataFrame) -> None:
        """
        Handle validation status changes from the data model.

        Args:
            validation_status (pd.DataFrame): The DataFrame containing validation status.
        """
        try:
            logger.debug("==== DataView._on_validation_changed called ====")

            if validation_status is None or validation_status.empty:
                logger.debug("Validation status is None or empty, nothing to do")
                return

            logger.debug(f"Received validation_status DataFrame shape: {validation_status.shape}")
            logger.debug(f"Validation status columns: {validation_status.columns.tolist()}")

            # Log a sample of the validation data for debugging
            if not validation_status.empty:
                logger.debug(f"Sample validation data (first 3 rows):\n{validation_status.head(3)}")

            # Update the TableStateManager with validation results
            if hasattr(self, "_table_state_manager") and self._table_state_manager:
                logger.debug("Updating TableStateManager with validation results")
                self._table_state_manager.update_cell_states_from_validation(validation_status)
                # Update tooltips based on the updated states
                self.update_tooltips_from_state()

                # Get the counts of cells in different states for debugging
                invalid_cells = self._table_state_manager.get_cells_by_state(CellState.INVALID)
                correctable_cells = self._table_state_manager.get_cells_by_state(
                    CellState.CORRECTABLE
                )
                logger.debug(
                    f"After updating TableStateManager: {len(invalid_cells)} invalid cells, "
                    f"{len(correctable_cells)} correctable cells"
                )

                # Force update after handling validation
                if hasattr(self, "_table_view") and self._table_view:
                    logger.debug("Forcing table view update after validation")
                    self._table_view.viewport().update()
            else:
                logger.warning(
                    "TableStateManager not available - validation highlighting will not be applied"
                )

        except Exception as e:
            logger.error(f"Error handling validation changed: {e}")
            import traceback

            logger.error(traceback.format_exc())

    @Slot(object)
    def _on_correction_applied(self, correction_status) -> None:
        """
        Handle correction applied signal.

        Args:
            correction_status: The correction status.
        """
        try:
            logger.debug("Handling correction applied")

            if correction_status is None:
                logger.debug("Correction status is None, nothing to do")
                return

            # Update the TableStateManager with correction results
            if hasattr(self, "_table_state_manager") and self._table_state_manager:
                logger.debug("Updating TableStateManager with correction results")
                self._table_state_manager.update_cell_states_from_correction(correction_status)
                # Update tooltips based on the updated states
                self.update_tooltips_from_state()
            else:
                logger.warning(
                    "TableStateManager not available - correction highlighting will not be applied"
                )
                self._on_data_changed()

        except Exception as e:
            logger.error(f"Error handling correction applied: {e}")

    def _apply_filter(self) -> None:
        """Apply the current filter to the data."""
        if (
            not hasattr(self, "_data_model")
            or self._data_model is None
            or self._data_model.is_empty
        ):
            logger.warning("Cannot apply filter: No data in model")
            self._status_label.setText("No data to filter")
            return

        try:
            # Get filter parameters from UI elements
            column_name = self._filter_column.currentText()
            filter_text = self._filter_text.text().strip()
            filter_mode = self._filter_mode.currentText()
            case_sensitive = self._case_sensitive.isChecked()

            # Store the filter criteria for later reference
            self._filter_criteria = filter_text

            # Get column index from name
            column_index = -1  # Default to all columns
            if column_name != "All Columns":
                for i in range(self._table_model.columnCount()):
                    if self._table_model.headerData(i, Qt.Horizontal) == column_name:
                        column_index = i
                        break

            # Apply filter using the proxy model
            self._proxy_model.set_filter_settings(
                column_index, filter_text, filter_mode, case_sensitive
            )

            # Update status label with row counts
            filtered_count = self._proxy_model.rowCount()
            total_count = self._table_model.rowCount()

            if filter_text:
                if filtered_count == 0:
                    self._status_label.setText(f"No matches found for '{filter_text}'")
                else:
                    self._status_label.setText(f"Showing {filtered_count} of {total_count} rows")
            else:
                self._status_label.setText(f"Showing all {total_count} rows")

            logger.info(
                f"Applied filter: column='{column_name}', text='{filter_text}', mode='{filter_mode}', case_sensitive={case_sensitive}"
            )
            logger.info(f"Filter result: {filtered_count} of {total_count} rows visible")

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            self._status_label.setText(f"Filter error: {str(e)}")

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
        self._filter_text = QLineEdit()  # UI element for filter text
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

        # Initialize the table model before using it
        self._table_model = QStandardItemModel(self)

        # Initialize the proxy model
        self._proxy_model = CustomFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._table_model)

        # Table view with minimal spacing
        self._table_view = QTableView()
        self._table_view.setModel(self._proxy_model)  # Set the proxy model instead of direct model
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.horizontalHeader().setStretchLastSection(
            False
        )  # Change to False to allow manual sizing
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.verticalHeader().setDefaultSectionSize(24)  # Compact rows
        self._table_view.verticalHeader().setVisible(True)

        # Explicitly enable editing with all triggers for better user experience
        self._table_view.setEditTriggers(
            QTableView.DoubleClicked | QTableView.EditKeyPressed | QTableView.AnyKeyPressed
        )

        # Allow selection of multiple items for batch operations
        self._table_view.setSelectionMode(QTableView.ExtendedSelection)

        # Enable tab key navigation between cells
        self._table_view.setTabKeyNavigation(True)

        # Ensure the table can accept focus for editing
        self._table_view.setFocusPolicy(Qt.StrongFocus)

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

        # Enable keyboard shortcuts for copy/paste - moved to a dedicated method
        self._setup_shortcuts()

        # Apply additional styling to ensure visibility
        self._apply_table_styling()

        # Create a container for the table view and color legend
        table_container = QWidget()
        table_layout = QHBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Create and add the color legend
        self._color_legend = self._create_color_legend()
        self._color_legend.setMaximumWidth(200)  # Limit width of the legend

        # Add table view and color legend to the container
        table_layout.addWidget(self._table_view, 5)  # Give table 5x the space
        table_layout.addWidget(self._color_legend, 1)  # Give legend 1x the space

        # Add the table container to the main layout
        main_layout.addWidget(table_container)
        main_layout.setStretch(1, 1)  # Give table container all available space

        # Now populate the column selector after the table and model are initialized
        self._populate_column_selector()

        # Set up context menu for table view
        self._setup_context_menu()

    def _create_color_legend(self) -> QGroupBox:
        """
        Create the color legend widget explaining the cell highlighting colors.

        Returns:
            QGroupBox: A group box containing the color legend
        """
        # Create group box with title
        legend = QGroupBox("Color Legend")
        layout = QVBoxLayout(legend)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(4)

        # Add each color with its explanation

        # Red - Invalid
        invalid_row = QHBoxLayout()
        invalid_color = QLabel()
        invalid_color.setObjectName("invalid_color")
        invalid_color.setFixedSize(16, 16)
        invalid_color.setStyleSheet("background-color: #FFB6B6; border: 1px solid #D32F2F;")
        invalid_row.addWidget(invalid_color)
        invalid_row.addWidget(QLabel("Invalid"))
        invalid_row.addStretch()
        layout.addLayout(invalid_row)

        # Orange - Invalid (correctable)
        invalid_corr_row = QHBoxLayout()
        invalid_corr_color = QLabel()
        invalid_corr_color.setObjectName("invalid_correctable_color")
        invalid_corr_color.setFixedSize(16, 16)
        invalid_corr_color.setStyleSheet("background-color: #FFD6A5; border: 1px solid #F57C00;")
        invalid_corr_row.addWidget(invalid_corr_color)
        invalid_corr_row.addWidget(QLabel("Invalid (correctable)"))
        invalid_corr_row.addStretch()
        layout.addLayout(invalid_corr_row)

        # Green - Corrected
        corrected_row = QHBoxLayout()
        corrected_color = QLabel()
        corrected_color.setObjectName("corrected_color")
        corrected_color.setFixedSize(16, 16)
        corrected_color.setStyleSheet("background-color: #B6FFB6; border: 1px solid #4CAF50;")
        corrected_row.addWidget(corrected_color)
        corrected_row.addWidget(QLabel("Corrected"))
        corrected_row.addStretch()
        layout.addLayout(corrected_row)

        # Purple - Correctable
        correctable_row = QHBoxLayout()
        correctable_color = QLabel()
        correctable_color.setObjectName("correctable_color")
        correctable_color.setFixedSize(16, 16)
        correctable_color.setStyleSheet("background-color: #D6B6FF; border: 1px solid #7E57C2;")
        correctable_row.addWidget(correctable_color)
        correctable_row.addWidget(QLabel("Correctable"))
        correctable_row.addStretch()
        layout.addLayout(correctable_row)

        return legend

    def _populate_column_selector(self) -> None:
        """Populate the column selector dropdown with available columns."""
        if not hasattr(self, "_filter_column") or self._filter_column is None:
            return

        # Clear the current items
        self._filter_column.clear()

        # Get the available columns from the data model
        available_columns = []
        if hasattr(self._data_model, "column_names") and self._data_model.column_names:
            available_columns = self._data_model.column_names
        elif self._columns:
            available_columns = self._columns

        # Add an "All Columns" option first
        self._filter_column.addItem("All Columns")

        # Add the column names
        for column in available_columns:
            self._filter_column.addItem(column)

        logger.debug(f"Populated column selector with {len(available_columns)} columns")

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for common operations."""
        # Copy shortcut (Ctrl+C)
        self._copy_shortcut = QShortcut(QKeySequence.Copy, self._table_view)
        self._copy_shortcut.activated.connect(self._copy_selected_cells)
        self._copy_shortcut.setContext(
            Qt.WidgetWithChildrenShortcut
        )  # Active for the table view and its children
        logger.info("Registered Ctrl+C shortcut for copying")

        # Paste shortcut (Ctrl+V)
        self._paste_shortcut = QShortcut(QKeySequence.Paste, self._table_view)
        self._paste_shortcut.activated.connect(self._paste_to_selected_cells)
        self._paste_shortcut.setContext(
            Qt.WidgetWithChildrenShortcut
        )  # Active for the table view and its children
        logger.info("Registered Ctrl+V shortcut for pasting")

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

        # Connect Enter key press in filter text field to apply filter
        if hasattr(self, "_filter_text") and self._filter_text is not None:
            self._filter_text.returnPressed.connect(self._apply_filter)
            logger.debug("Connected filter text Enter key to apply filter")

        # Connect custom context menu
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)
        logger.info("Connected custom context menu")

        # Connect double-click signal for starting edit directly
        self._table_view.doubleClicked.connect(self._on_cell_double_clicked)
        logger.info("Connected double-click handler for direct editing")

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

        # Connect refresh button
        refresh_button = self._action_toolbar.get_button_by_name("refresh")
        if refresh_button:
            refresh_button.clicked.connect(self._on_refresh_clicked)
            logger.debug("Connected refresh button")

        # Connect to correction signals if available
        correction_controller = self._get_correction_controller()
        if correction_controller:
            correction_controller.correction_completed.connect(self._on_correction_completed)

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

    def _clear_filter(self) -> None:
        """Clear the current filter."""
        # Clear the filter text field
        if hasattr(self, "_filter_text") and self._filter_text is not None:
            self._filter_text.clear()

        # Reset the filter criteria
        self._filter_criteria = ""

        # Reset filter data
        self._filtered_data = None
        self._filtered_rows = None

        # Reset to first column ("All Columns")
        if hasattr(self, "_filter_column") and self._filter_column is not None:
            self._filter_column.setCurrentIndex(0)

        # Reset filter mode to first option ("Contains")
        if hasattr(self, "_filter_mode") and self._filter_mode is not None:
            self._filter_mode.setCurrentIndex(0)

        # Uncheck case sensitivity
        if hasattr(self, "_case_sensitive") and self._case_sensitive is not None:
            self._case_sensitive.setChecked(False)

        # Clear the proxy model filter
        if hasattr(self, "_proxy_model") and self._proxy_model is not None:
            self._proxy_model.set_filter_settings(-1, "", "Contains", False)

        # Update status label
        if hasattr(self, "_status_label") and self._status_label is not None:
            if hasattr(self._table_model, "rowCount"):
                row_count = self._table_model.rowCount()
                self._status_label.setText(f"Showing all {row_count} rows")
            else:
                self._status_label.setText("No data loaded")

        logger.info("Filter cleared")

    def _get_original_row_index(self, proxy_row_index):
        """
        Convert a proxy model row index to the original source model row index.

        Args:
            proxy_row_index: The row index in the proxy model

        Returns:
            The corresponding row index in the source model
        """
        proxy_index = self._proxy_model.index(proxy_row_index, 0)
        source_index = self._proxy_model.mapToSource(proxy_index)
        return source_index.row()

    def _get_data_model_row_index(self, proxy_row_index):
        """
        Convert a proxy model row index to the data model row index.

        Args:
            proxy_row_index: The row index in the proxy model

        Returns:
            The corresponding row index in the data model
        """
        # First map to source model (table model)
        source_row = self._get_original_row_index(proxy_row_index)

        # Then map to data model if filtered
        if self._filtered_rows and source_row < len(self._filtered_rows):
            return self._filtered_rows[source_row]

        # If no filtering in the data model, return the source row
        return source_row

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
            # Map to source index for accessing model data
            source_index = self._proxy_model.mapToSource(index)

            # Get column and value
            source_row = source_index.row()
            source_col = source_index.column()

            if (
                0 <= source_row < self._table_model.rowCount()
                and 0 <= source_col < self._table_model.columnCount()
            ):
                # Get the actual row index if we're using filtered data
                actual_row = source_row
                if self._filtered_rows and source_row < len(self._filtered_rows):
                    actual_row = self._filtered_rows[source_row]

                column_name = self._data_model.column_names[source_col]
                cell_value = self._table_model.data(source_index, Qt.DisplayRole)

                # Get validation status for this cell
                validation_status = self._table_model.data(
                    source_index, Qt.ItemDataRole.UserRole + 1
                )

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

        # Get the value from the proxy model
        value = self._proxy_model.data(index, Qt.DisplayRole)

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
                # Map to source index for model update
                source_index = self._proxy_model.mapToSource(sel_index)

                # Set the value in the source model
                self._table_model.setData(source_index, text, Qt.EditRole)

                # Also update the data model directly to ensure it's updated properly
                try:
                    # Get the row in the original model
                    source_row = source_index.row()
                    source_col = source_index.column()

                    if (
                        0 <= source_row < self._table_model.rowCount()
                        and 0 <= source_col < self._table_model.columnCount()
                    ):
                        # Get the actual row index in the data model if we're using filtered data
                        actual_row = source_row
                        if self._filtered_rows and source_row < len(self._filtered_rows):
                            actual_row = self._filtered_rows[source_row]

                        column_name = self._data_model.column_names[source_col]
                        self._data_model.update_cell(actual_row, column_name, text)
                except Exception as e:
                    logger.error(f"Error updating data model directly: {e}")

            logger.info(f"Pasted value to {len(selected_indexes)} selected cells")
        elif index.isValid():
            # Single cell via context menu, just paste to that
            # Map to source index for model update
            source_index = self._proxy_model.mapToSource(index)

            # Set the value in the source model
            self._table_model.setData(source_index, text, Qt.EditRole)

            # Also update the data model directly
            try:
                source_row = source_index.row()
                source_col = source_index.column()

                if (
                    0 <= source_row < self._table_model.rowCount()
                    and 0 <= source_col < self._table_model.columnCount()
                ):
                    # Get the actual row index if we're using filtered data
                    actual_row = source_row
                    if self._filtered_rows and source_row < len(self._filtered_rows):
                        actual_row = self._filtered_rows[source_row]

                    column_name = self._data_model.column_names[source_col]
                    self._data_model.update_cell(actual_row, column_name, text)
            except Exception as e:
                logger.error(f"Error updating data model directly: {e}")

            logger.info(
                f"Pasted value to single cell at row {index.row()}, column {index.column()}"
            )
        else:
            logger.warning("Paste operation failed: No valid cell selected")
            return

    def _paste_structured_data(self, clipboard_text: str, selected_indexes: list) -> None:
        """
        Paste structured data (tab-delimited, newline-separated) to the grid.

        Args:
            clipboard_text: The structured clipboard text
            selected_indexes: The currently selected cells
        """
        # Split the text into rows and columns
        rows = clipboard_text.split("\n")
        grid_data = [row.split("\t") for row in rows]

        # Get dimensions of the paste data
        paste_height = len(grid_data)
        paste_width = max(len(row) for row in grid_data)

        logger.info(f"Structured paste: {paste_width}x{paste_height} grid of cells")

        # Find the top-left cell of the selection
        if not selected_indexes:
            logger.warning("No cells selected for structured paste")
            return

        # Get the top-left cell position in the proxy model
        top_left_row = min(index.row() for index in selected_indexes)
        top_left_col = min(index.column() for index in selected_indexes)

        # For each cell in the paste data, update the corresponding cell in the table
        cells_updated = 0
        for r, row_data in enumerate(grid_data):
            for c, cell_value in enumerate(row_data):
                # Calculate target position in the proxy model
                target_row = top_left_row + r
                target_col = top_left_col + c

                # Get the proxy model index
                proxy_index = self._proxy_model.index(target_row, target_col)
                if not proxy_index.isValid():
                    continue

                # Map to source index
                source_index = self._proxy_model.mapToSource(proxy_index)
                source_row = source_index.row()
                source_col = source_index.column()

                # Skip if outside table bounds
                if (
                    source_row >= self._table_model.rowCount()
                    or source_col >= self._table_model.columnCount()
                ):
                    continue

                # Set the value in the source model
                self._table_model.setData(source_index, cell_value, Qt.EditRole)

                # Also update the data model directly
                try:
                    # Get the actual row index if we're using filtered data
                    actual_row = source_row
                    if self._filtered_rows and source_row < len(self._filtered_rows):
                        actual_row = self._filtered_rows[source_row]

                    column_name = self._data_model.column_names[source_col]
                    self._data_model.update_cell(actual_row, column_name, cell_value)
                    cells_updated += 1
                except Exception as e:
                    logger.error(f"Error updating data model during structured paste: {e}")

        logger.info(f"Updated {cells_updated} cells with structured paste data")
        self._status_label.setText(f"Pasted {cells_updated} cells from clipboard")

    def _copy_selected_cells(self) -> None:
        """Copy the currently selected cell(s) to clipboard."""
        selected_indexes = self._table_view.selectedIndexes()
        if not selected_indexes:
            logger.debug("No cells selected for copy operation")
            return

        # Log the copy operation
        logger.info(f"Copying {len(selected_indexes)} selected cells")

        # If only one cell is selected, use the simple copy function
        if len(selected_indexes) == 1:
            self._copy_cell(selected_indexes[0])
            return

        # For multiple cells, we need to create a structured text representation
        # First, organize the selected cells by row and column
        cells_by_position = {}
        min_row = min_col = float("inf")
        max_row = max_col = -1

        for index in selected_indexes:
            row, col = index.row(), index.column()
            # Track min/max row and column to determine the selection rectangle
            min_row = min(min_row, row)
            max_row = max(max_row, row)
            min_col = min(min_col, col)
            max_col = max(max_col, col)

            # Store the cell value indexed by position
            value = self._proxy_model.data(index, Qt.DisplayRole) or ""
            cells_by_position[(row, col)] = str(value)

        # Build a tab-delimited text representation of the selection
        buffer = []
        for row in range(min_row, max_row + 1):
            row_texts = []
            for col in range(min_col, max_col + 1):
                value = cells_by_position.get((row, col), "")
                row_texts.append(value)
            buffer.append("\t".join(row_texts))

        # Join rows with newlines
        clipboard_text = "\n".join(buffer)

        # Copy to clipboard
        QApplication.clipboard().setText(clipboard_text)
        logger.info(f"Copied structured data from {len(selected_indexes)} cells to clipboard")

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

        # Get the clipboard text
        clipboard_text = QApplication.clipboard().text().strip()
        if not clipboard_text:
            logger.warning("Paste operation failed: Clipboard is empty")
            self._status_label.setText("Cannot paste: Clipboard is empty")
            return

        # Get currently selected cells
        selected_indexes = self._table_view.selectedIndexes()

        # If no cells are selected, try to use the current cell
        if not selected_indexes:
            logger.warning("No cells selected for paste operation")

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
                    first_index = self._proxy_model.index(0, 0)
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

        # Check if we have structured data with tabs and newlines
        has_tabs = "\t" in clipboard_text
        has_newlines = "\n" in clipboard_text

        # If we have structured data, handle as a grid paste
        if has_tabs or has_newlines:
            self._paste_structured_data(clipboard_text, selected_indexes)
        else:
            # Simple paste to all selected cells
            logger.info(f"Pasting '{clipboard_text}' to {len(selected_indexes)} selected cells")

            # Set the value for each selected cell
            for sel_index in selected_indexes:
                # Map to source index for model update
                source_index = self._proxy_model.mapToSource(sel_index)

                # Set the value in the source model
                self._table_model.setData(source_index, clipboard_text, Qt.EditRole)

                # Also update the data model directly
                try:
                    # Get the row in the original model
                    source_row = source_index.row()
                    source_col = source_index.column()

                    if (
                        0 <= source_row < self._table_model.rowCount()
                        and 0 <= source_col < self._table_model.columnCount()
                    ):
                        # Get the actual row index if we're using filtered data
                        actual_row = source_row
                        if self._filtered_rows and source_row < len(self._filtered_rows):
                            actual_row = self._filtered_rows[source_row]

                        column_name = self._data_model.column_names[source_col]
                        self._data_model.update_cell(actual_row, column_name, clipboard_text)
                except Exception as e:
                    logger.error(f"Error updating data model directly: {e}")

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
                # Check for F2 key (explicit edit start)
                if key_event.key() == Qt.Key_F2:
                    logger.info("F2 pressed, explicitly starting edit")
                    self._start_editing_current_cell()
                    return True
                # Let the shortcuts handle Ctrl+C and Ctrl+V
                # The event filter should not interfere with them
            # Check for double-click events separately
            elif event.type() == event.Type.MouseButtonDblClick:
                logger.info("Double-click captured, explicitly starting edit")
                index = self._table_view.indexAt(event.pos())
                if index.isValid():
                    QTimer.singleShot(0, lambda idx=index: self._table_view.edit(idx))
                    return True

        # Pass the event on to the standard event processing
        return super().eventFilter(watched, event)

    def _start_editing_current_cell(self):
        """Explicitly start editing the current cell if it's valid."""
        current_index = self._table_view.currentIndex()
        if current_index.isValid() and (current_index.flags() & Qt.ItemIsEditable):
            logger.info(
                f"Starting edit for cell at [{current_index.row()}, {current_index.column()}]"
            )
            self._table_view.edit(current_index)

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

            # Make sure the status column is included in the columns list
            if self.STATUS_COLUMN not in columns:
                columns = list(columns) + [self.STATUS_COLUMN]
                logger.debug(f"Added STATUS_COLUMN to columns list: {columns}")

            # Temporarily disconnect the proxy model to prevent filtering during population
            if hasattr(self, "_table_view") and hasattr(self, "_proxy_model"):
                logger.debug("Temporarily setting proxy model's source model to None")
                self._proxy_model.setSourceModel(None)

            # Clear the model and reset it with correct dimensions
            self._table_model.clear()
            self._table_model.setHorizontalHeaderLabels(columns)

            # Set dimensions for the table model
            row_count = len(data)
            col_count = len(columns)
            self._table_model.setRowCount(row_count)
            self._table_model.setColumnCount(col_count)

            # Reset filters to ensure all rows are visible once data is loaded
            if hasattr(self, "_proxy_model"):
                self._proxy_model.set_filter_settings(-1, "", "Contains", False)

            # Prepare for chunked population
            self._chunk_columns = columns
            self._chunk_data = data
            self._chunk_row_count = row_count
            self._chunk_col_count = col_count
            self._chunk_size = min(500, row_count)  # Process 500 rows at a time
            self._chunk_start = 0

            logger.debug(f"Starting chunked population: {row_count} rows, {col_count} columns")

            # Process events before starting the chunking process
            QApplication.processEvents()

            # Start the chunked population process - use immediate processing for the first chunk
            self._populate_chunk()

            # NOTE: We moved the proxy model reconnection to _finalize_population
            # It will be reconnected after ALL chunks are loaded, not just the first one

        except Exception as e:
            logger.error(f"Error populating table: {e}")
            self._update_status(f"Error: {str(e)}", True)
            self._is_updating = False
            self._population_in_progress = False

            # Make sure proxy model is reconnected even in case of error
            if hasattr(self, "_table_view") and hasattr(self, "_proxy_model"):
                self._proxy_model.setSourceModel(self._table_model)

    def _populate_chunk(self):
        """Populate one chunk of data to the table."""
        try:
            if not hasattr(self, "_chunk_start"):
                logger.error("Error in _populate_chunk: _chunk_start attribute not found")
                self._is_updating = False
                self._population_in_progress = False
                self._finalize_population()
                return

            # Get current chunk boundaries
            chunk_start = self._chunk_start
            chunk_end = min(chunk_start + self._chunk_size, self._chunk_row_count)

            logger.debug(
                f"Populating chunk from {chunk_start} to {chunk_end} of {self._chunk_row_count} rows"
            )

            # Process only the current chunk of data
            if hasattr(self, "_chunk_data") and self._chunk_data is not None:
                try:
                    # For large dataframes, accessing a subset might be faster than iloc
                    start_idx = self._chunk_data.index[chunk_start]
                    end_idx = self._chunk_data.index[chunk_end - 1]
                    data_subset = self._chunk_data.loc[start_idx:end_idx]

                    # Convert to a format that's faster to iterate
                    values = data_subset.to_dict("records")

                    # Batch creation of items for better performance
                    for i, row_data in enumerate(values):
                        row_idx = chunk_start + i
                        for col_idx, col_name in enumerate(self._chunk_columns):
                            # Handle STATUS column specially
                            if col_name == self.STATUS_COLUMN:
                                # Create a default "Not validated" status cell
                                status_item = QStandardItem("Not validated")
                                status_item.setFlags(
                                    status_item.flags() & ~Qt.ItemIsEditable
                                )  # Make non-editable
                                self._table_model.setItem(row_idx, col_idx, status_item)
                                continue

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
                            item.setFlags(
                                item.flags() | Qt.ItemIsEditable
                            )  # Make the item editable
                            self._table_model.setItem(row_idx, col_idx, item)

                    # Process events after each chunk to keep UI responsive
                    QApplication.processEvents()

                except Exception as chunk_error:
                    logger.error(f"Error processing data chunk: {chunk_error}")
                    # Continue with next chunk despite error
            else:
                logger.error("_chunk_data attribute is missing or None")
                self._is_updating = False
                self._population_in_progress = False
                self._finalize_population()  # Still try to finalize even with error
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

            # Explicitly update the UI before scheduling the next chunk
            QApplication.processEvents()

            # Schedule the next chunk with a small delay to keep UI responsive
            # Use a direct call instead of QTimer for more reliable processing
            if not self._is_updating and not self._population_in_progress:
                logger.warning("Population flags were reset unexpectedly, stopping chunking")
                self._finalize_population()
                return

            self._populate_chunk()

        except Exception as e:
            logger.error(f"Error in chunk population: {e}")
            self._update_status(f"Error: {str(e)}", True)
            self._is_updating = False
            self._population_in_progress = False
            self._finalize_population()  # Try to finalize what we've got

    def _finalize_population(self):
        """Finalize the population process."""
        try:
            logger.debug("Finalizing data population")

            # Make sure the proxy model is reconnected
            if hasattr(self, "_proxy_model") and hasattr(self, "_table_model"):
                logger.debug("Reconnecting proxy model to source model during finalization")
                self._proxy_model.setSourceModel(self._table_model)

                # Apply any pending filters after model is connected
                if hasattr(self, "_filter_criteria") and self._filter_criteria:
                    logger.debug(f"Reapplying filter: {self._filter_criteria}")
                    self._apply_filter()

            # Apply table styling
            self._ensure_no_text_wrapping()
            self._customize_column_widths()
            self._update_status_from_row_count()

            # Reset state flags
            self._initial_load = False
            self._is_updating = False
            self._population_in_progress = False

            # Explicitly clear any chunking artifacts
            self._chunk_start = 0
            self._chunk_size = 0
            self._chunk_row_count = 0
            self._chunk_data = None

            logger.debug("Data population completed successfully")

            # Process events to ensure UI updates
            QApplication.processEvents()

        except Exception as e:
            logger.error(f"Error in _finalize_population: {e}")
            self._is_updating = False
            self._population_in_progress = False
            self._initial_load = False

            # Still try to reconnect proxy model in case of error
            if hasattr(self, "_proxy_model") and hasattr(self, "_table_model"):
                if self._proxy_model.sourceModel() is None:
                    logger.debug("Reconnecting proxy model to source model despite error")
                    self._proxy_model.setSourceModel(self._table_model)

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

    def _on_cell_double_clicked(self, index):
        """
        Handle double-click on a cell to start editing.

        Args:
            index (QModelIndex): The index of the clicked cell
        """
        logger.info(f"Double-clicked cell at row {index.row()}, column {index.column()}")
        if index.isValid() and (index.flags() & Qt.ItemIsEditable):
            logger.info(f"Starting edit for cell at [{index.row()}, {index.column()}]")
            self._table_view.edit(index)

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        logger.info("Refresh button clicked")
        # Repopulate column selector in case columns changed
        self._populate_column_selector()
        # Update the view
        self._update_view()

    def _apply_table_styling(self) -> None:
        """Apply additional styling to ensure table content is visible."""
        logger.debug("Applying table styling in DataView")

        # Set text color explicitly via stylesheet but DO NOT SET BACKGROUND COLOR on items
        # to allow cell-specific highlighting to work
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
                /* NO BACKGROUND COLOR HERE - allows item-specific background colors to work */
                padding: 12px;
            }
            QTableView::item:selected {
                color: #1A2C42;
                background-color: #D4AF37;
            }
        """)

        # Make sure the alternating row colors feature is DISABLED as it can override our highlighting
        self._table_view.setAlternatingRowColors(False)
        logger.debug("Disabled alternating row colors to prevent highlighting issues")

        # Make sure the model has appropriate default foreground color
        if self._table_model:  # Check that table model exists before using it
            self._table_model.setItemPrototype(QStandardItem())
            prototype = self._table_model.itemPrototype()
            if prototype:
                prototype.setForeground(QColor("white"))
                logger.debug("Set default item foreground color to white")

    def _on_item_changed(self, item):
        """
        Handle changes to items in the table model.

        Args:
            item: The QStandardItem that changed
        """
        # Skip processing if currently updating the table
        if self._is_updating:
            return

        try:
            # Get the row and column of the changed item
            row = item.row()
            col = item.column()

            # Map from proxy model to source model if needed
            if hasattr(self, "_proxy_model") and self._proxy_model:
                proxy_index = self._proxy_model.index(row, col)
                source_index = self._proxy_model.mapToSource(proxy_index)
                row = source_index.row()
                col = source_index.column()

            # Map to data model row if filtered
            data_model_row = row
            if (
                hasattr(self, "_filtered_rows")
                and self._filtered_rows
                and row < len(self._filtered_rows)
            ):
                data_model_row = self._filtered_rows[row]

            # Get the column name from the header
            column_name = self._table_model.headerData(col, Qt.Horizontal)

            # Get the new value
            new_value = item.data(Qt.DisplayRole)

            logger.debug(f"Item changed at ({row}, {col}) - column '{column_name}': '{new_value}'")

            # Skip STATUS column updates - this is a display-only column handled by validation
            if column_name == self.STATUS_COLUMN:
                logger.debug(f"Skipping update for STATUS column (display-only)")
                return

            # Verify that the column exists in the data model before updating
            if (
                hasattr(self._data_model, "column_names")
                and column_name in self._data_model.column_names
            ):
                # Check that the row is within range
                if data_model_row < len(self._data_model.data):
                    # Update the data model
                    if hasattr(self._data_model, "update_cell"):
                        self._data_model.update_cell(data_model_row, column_name, new_value)

                        # Emit the data_edited signal
                        self.data_edited.emit(data_model_row, col, new_value)
                else:
                    logger.warning(
                        f"Row index {data_model_row} out of range ({len(self._data_model.data)} rows)"
                    )
            else:
                logger.warning(
                    f"Column '{column_name}' not found in data model columns: {self._data_model.column_names if hasattr(self._data_model, 'column_names') else 'N/A'}"
                )

        except Exception as e:
            logger.error(f"Error handling item change: {e}")

    def _on_sort_indicator_changed(self, logical_index, order):
        """
        Handle changes to sort indicator in the table header.

        Args:
            logical_index: The index of the column being sorted
            order: The sort order (ascending or descending)
        """
        try:
            # Convert Qt.SortOrder to string for logging
            order_str = "Ascending" if order == Qt.AscendingOrder else "Descending"

            # Get the column name
            column_name = self._table_model.headerData(logical_index, Qt.Horizontal)

            logger.info(f"Sorting by column {column_name} ({order_str})")

            # Let the proxy model handle the actual sorting
            # No need to implement custom sorting logic here as the proxy model handles it

        except Exception as e:
            logger.error(f"Error handling sort indicator change: {e}")

    @Slot(object)
    def _on_data_changed(self, data_state=None) -> None:
        """
        Handle data changed signal from the data model.

        This slot is triggered when the underlying data in ChestDataModel changes.
        It typically triggers a view update.

        Args:
            data_state: The current DataState object (optional, depends on signal emission).
        """
        try:
            logger.debug(f"DataView received _on_data_changed. DataState: {data_state}")
            # Clear validation cache since data has changed
            # self._clear_validation_cache()
            # ^ Consider if this is needed. If validation runs automatically, maybe not.

            # Repopulate column selector in case columns changed
            # This might be redundant if populate_table handles it
            # self._populate_column_selector()

            # Trigger a full table repopulation or update
            # Use populate_table for now, assuming it handles efficiency
            self.populate_table()

        except Exception as e:
            logger.error(f"Error handling data changed in DataView: {e}")

    def _setup_context_menu(self) -> None:
        """Set up the context menu for the data table."""
        # Create context menu
        self._context_menu = QMenu(self)

        # Add copy action
        self._copy_action = QAction("Copy", self)
        self._copy_action.triggered.connect(self._on_copy_to_clipboard)
        self._context_menu.addAction(self._copy_action)

        # Add copy row action
        self._copy_row_action = QAction("Copy Row", self)
        self._copy_row_action.triggered.connect(self._on_copy_row_to_clipboard)
        self._context_menu.addAction(self._copy_row_action)

        # Add separator before correction actions
        self._context_menu.addSeparator()

        # Add correction-related items
        self._add_correction_rule_action = QAction("Add Correction Rule", self)
        self._add_correction_rule_action.triggered.connect(self._on_add_correction_rule)
        self._context_menu.addAction(self._add_correction_rule_action)

        self._add_batch_correction_action = QAction("Create Batch Correction Rules", self)
        self._add_batch_correction_action.triggered.connect(self._on_add_batch_correction)
        self._context_menu.addAction(self._add_batch_correction_action)

        # Add enhanced correction actions
        self._context_menu.addSeparator()

        # Action to apply all correction rules to selected cells
        self._apply_correction_rules_action = QAction(
            "Apply Correction Rules to Selected Cells", self
        )
        self._apply_correction_rules_action.triggered.connect(self._on_apply_correction_rules)
        self._context_menu.addAction(self._apply_correction_rules_action)

        # Submenu for applying specific rules
        self._apply_specific_rule_menu = QMenu("Apply Specific Rule", self)
        self._context_menu.addMenu(self._apply_specific_rule_menu)

        # Action to view validation details
        self._view_validation_details_action = QAction("View Validation Details", self)
        self._view_validation_details_action.triggered.connect(self._on_view_validation_details)
        self._context_menu.addAction(self._view_validation_details_action)

        # Set context menu policy
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._on_context_menu_requested)

    def _on_context_menu_requested(self, position):
        """
        Handle the context menu request and show the menu.

        Args:
            position (QPoint): The position where the context menu was requested
        """
        if self._data_model.is_empty:
            return

        # Get the index at the position
        index = self._table_view.indexAt(position)
        if not index.isValid():
            return

        # Update menu actions based on current selection
        self._update_context_menu_actions()

        # Update the specific rule submenu
        self._update_specific_rule_submenu()

        # Show the menu
        self._context_menu.exec_(self._table_view.viewport().mapToGlobal(position))

    def _update_context_menu_actions(self):
        """
        Update the enabled/disabled state of context menu actions based on current selection.
        """
        # Get the current selection
        selected_indices = self._table_view.selectedIndexes()
        has_selection = len(selected_indices) > 0

        # Enable/disable actions based on selection
        self._add_correction_rule_action.setEnabled(has_selection)
        self._add_batch_correction_action.setEnabled(has_selection)
        self._apply_correction_rules_action.setEnabled(has_selection)
        self._apply_specific_rule_menu.setEnabled(has_selection)
        self._view_validation_details_action.setEnabled(has_selection)

        # Additional logic based on correction status could be added here
        # For example, disabling "Apply Correction Rules" if no rules are applicable

    def _update_specific_rule_submenu(self):
        """
        Update the specific rule submenu with applicable rules for the current selection.
        """
        # Clear the submenu
        self._apply_specific_rule_menu.clear()

        # Get selected cells
        selected_cells = self._get_selected_cells()
        if not selected_cells:
            return

        # Get the first selected cell for determining applicable rules
        # In the future, this could be enhanced to handle multiple selections better
        first_cell = selected_cells[0]
        value = first_cell.get("value", "")
        column_name = first_cell.get("column_name", "")

        # Get applicable rules from the correction controller
        correction_controller = self._get_correction_controller()
        if not correction_controller:
            return

        applicable_rules = correction_controller.get_applicable_rules(value, column_name)

        # Add an action for each applicable rule
        for rule in applicable_rules:
            rule_text = f"'{rule.from_value}' → '{rule.to_value}'"
            action = QAction(rule_text, self)
            # Use a lambda with default argument to capture the current rule
            action.triggered.connect(lambda checked=False, r=rule: self._on_apply_specific_rule(r))
            self._apply_specific_rule_menu.addAction(action)

        # If no rules are applicable, add a disabled action indicating this
        if not applicable_rules:
            no_rules_action = QAction("No applicable rules", self)
            no_rules_action.setEnabled(False)
            self._apply_specific_rule_menu.addAction(no_rules_action)

    def _on_copy_to_clipboard(self):
        """Copy the selected cell content to clipboard."""
        selected_indices = self._table_view.selectedIndexes()
        if not selected_indices:
            return

        # Use the first selected index
        index = selected_indices[0]
        if not index.isValid():
            return

        # Get the data
        source_index = self._proxy_model.mapToSource(index) if self._proxy_model else index
        value = self._table_model.data(source_index, Qt.DisplayRole)

        # Copy to clipboard
        if value:
            clipboard = QApplication.clipboard()
            clipboard.setText(str(value))
            self._update_status(f"Copied value to clipboard: {value}", False)

    def _on_copy_row_to_clipboard(self):
        """Copy the selected row content to clipboard as tab-separated values."""
        selected_indices = self._table_view.selectedIndexes()
        if not selected_indices:
            return

        # Get the row of the first selected cell
        row = selected_indices[0].row()

        # Get all cells in that row
        row_data = []
        for col in range(self._table_view.model().columnCount()):
            index = self._table_view.model().index(row, col)
            value = self._table_view.model().data(index, Qt.DisplayRole)
            row_data.append(str(value) if value else "")

        # Copy to clipboard as tab-separated values
        clipboard = QApplication.clipboard()
        clipboard.setText("\t".join(row_data))
        self._update_status(f"Copied row to clipboard", False)

    def _on_apply_correction_rules(self):
        """Apply all applicable correction rules to the selected cells."""
        selected_cells = self._get_selected_cells()
        if not selected_cells:
            QMessageBox.warning(self, "Warning", "No cells selected.")
            return

        # Get the correction controller
        correction_controller = self._get_correction_controller()
        if not correction_controller:
            QMessageBox.warning(self, "Error", "Correction controller not available.")
            return

        # Apply rules to the selection
        result = correction_controller.apply_rules_to_selection(selected_cells)

        # Show results
        corrected_count = len(result.get("corrected_cells", []))
        errors = len(result.get("errors", []))

        # Update status
        if corrected_count > 0:
            self._update_status(
                f"Applied correction rules: {corrected_count} cells corrected, {errors} errors",
                False,
            )
        else:
            self._update_status("No corrections applied", False)

        # Refresh to show changes
        self.refresh()

    def _on_apply_specific_rule(self, rule):
        """
        Apply a specific correction rule to the selected cells.

        Args:
            rule: The CorrectionRule to apply
        """
        selected_cells = self._get_selected_cells()
        if not selected_cells:
            QMessageBox.warning(self, "Warning", "No cells selected.")
            return

        # Get the correction controller
        correction_controller = self._get_correction_controller()
        if not correction_controller:
            QMessageBox.warning(self, "Error", "Correction controller not available.")
            return

        # Apply the specific rule to all selected cells
        corrected_count = 0
        for cell in selected_cells:
            # Check if the rule is applicable to this cell
            cell_value = cell.get("value", "")
            cell_column = cell.get("column_name", "")

            if rule.category.lower() == cell_column.lower() or rule.category.lower() == "general":
                # Apply the rule to this cell
                success = correction_controller.apply_single_rule(rule, [cell])
                if success:
                    corrected_count += 1

        # Update status
        if corrected_count > 0:
            self._update_status(
                f"Applied rule '{rule.from_value}' → '{rule.to_value}' to {corrected_count} cells",
                False,
            )
        else:
            self._update_status("No corrections applied", False)

        # Refresh to show changes
        self.refresh()

    def _on_view_validation_details(self):
        """Show validation details for the selected cell."""
        # Get the current index
        current_index = self._table_view.currentIndex()
        if not current_index.isValid():
            QMessageBox.warning(self, "Warning", "No cell selected.")
            return

        # Map to source index
        source_index = (
            self._proxy_model.mapToSource(current_index) if self._proxy_model else current_index
        )
        source_row = source_index.row()
        source_col = source_index.column()

        # Get the correction controller
        correction_controller = self._get_correction_controller()
        if not correction_controller:
            QMessageBox.warning(self, "Error", "Correction controller not available.")
            return

        # Get validation service from the correction controller
        validation_service = correction_controller.get_validation_service()
        if not validation_service:
            QMessageBox.warning(self, "Error", "Validation service not available.")
            return

        # Get validation details
        details = validation_service.get_cell_validation_details(source_row, source_col)

        # Show details in a message box
        column_name = self._table_model.headerData(source_col, Qt.Horizontal, Qt.DisplayRole)
        value = self._table_model.data(source_index, Qt.DisplayRole)

        message = f"Validation Details for Cell ({source_row}, {source_col}):\n\n"
        message += f"Column: {column_name}\n"
        message += f"Value: {value}\n\n"

        if details:
            message += f"Status: {details.get('status', 'Unknown')}\n"
            message += f"Validation Details: {details.get('details', 'No details available')}\n"
            if "rules" in details and details["rules"]:
                message += "\nApplicable Correction Rules:\n"
                for rule in details["rules"]:
                    message += f"- '{rule.from_value}' → '{rule.to_value}'\n"
            else:
                message += "\nNo applicable correction rules found."
        else:
            message += "No validation details available for this cell."

        QMessageBox.information(self, "Validation Details", message)

    def _get_selected_cells(self):
        """Get information about selected cells."""
        selected_cells = []

        # Get selected indexes from the table view
        selected_indexes = self._table_view.selectedIndexes()
        if not selected_indexes:
            return selected_cells

        # Process each selected index
        for index in selected_indexes:
            # Skip if it's a header or non-data cell
            if not index.isValid():
                continue

            # Get row and column indices
            row = index.row()
            column = index.column()

            # Get the model index for the source data (handle proxy model if present)
            source_index = index
            source_row = row
            source_column = column
            if hasattr(self, "_proxy_model") and self._proxy_model:
                source_index = self._proxy_model.mapToSource(index)
                source_row = source_index.row()
                source_column = source_index.column()

            # Get the value and column name
            value = self._table_model.data(source_index, Qt.DisplayRole)
            column_name = self._table_model.headerData(source_column, Qt.Horizontal, Qt.DisplayRole)

            # Add to selected cells list
            selected_cells.append(
                {
                    "row": source_row,
                    "col": source_column,
                    "value": value if value else "",
                    "column_name": column_name if column_name else f"Column {source_column}",
                }
            )

        return selected_cells

    def _on_add_correction_rule(self):
        """Handle add correction rule action."""
        selected_cells = self._get_selected_cells()
        if not selected_cells:
            QMessageBox.warning(self, "Warning", "No cells selected.")
            return

        # If multiple cells selected, ask whether to create individual rules or batch rules
        if len(selected_cells) > 1:
            response = QMessageBox.question(
                self,
                "Multiple Cells Selected",
                "Create individual rules for each cell or use batch correction?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if response == QMessageBox.No:
                # Use batch correction instead
                self._on_add_batch_correction()
                return

        # For single cell or if user chose individual rules
        # Create a rule for the first selected cell
        cell = selected_cells[0]
        self._show_add_rule_dialog(cell)

    def _show_add_rule_dialog(self, cell_data):
        """Show dialog to add a correction rule for a cell."""
        # Get the correction controller
        correction_controller = self._get_correction_controller()
        if not correction_controller:
            QMessageBox.warning(self, "Error", "Correction controller not available.")
            return

        # Create empty rule with cell data
        from chestbuddy.core.models.correction_rule import CorrectionRule

        rule = CorrectionRule(
            from_value=cell_data["value"],
            to_value="",
            category=cell_data["column_name"],
            status="enabled",
            order=100,
        )

        # Show the dialog to edit the rule
        dialog = AddEditRuleDialog(
            validation_service=correction_controller.get_validation_service(),
            parent=self,
            rule=rule,
        )

        if dialog.exec():
            rule = dialog.get_rule()
            correction_controller.add_rule(rule)
            self._logger.info(f"Added rule: {rule.from_value} -> {rule.to_value}")

            # Refresh data view to show changes
            self.refresh()

    def _on_add_batch_correction(self):
        """Handle batch correction action."""
        selected_cells = self._get_selected_cells()
        if not selected_cells:
            QMessageBox.warning(self, "Warning", "No cells selected.")
            return

        # Open BatchCorrectionDialog with selected cells
        self._show_batch_correction_dialog(selected_cells)

    def _show_batch_correction_dialog(self, selected_cells):
        """Show the batch correction dialog."""
        # Get CorrectionController from the application
        correction_controller = self._get_correction_controller()
        if not correction_controller:
            QMessageBox.warning(self, "Error", "Correction controller not available.")
            return

        dialog = BatchCorrectionDialog(
            selected_cells=selected_cells,
            validation_service=correction_controller.get_validation_service(),
            parent=self,
        )

        if dialog.exec():
            rules = dialog.get_rules()
            for rule in rules:
                correction_controller.add_rule(rule)
            self._logger.info(f"Added {len(rules)} rules from batch correction")

            # Refresh data view to show changes
            self.refresh()

    def _get_correction_controller(self):
        """Get the correction controller from the application."""
        # This is a simplified approach - the actual implementation would depend
        # on how controllers are managed in the application
        from chestbuddy.app import ChestBuddyApp

        app = QApplication.instance()
        if isinstance(app, ChestBuddyApp):
            return app.get_correction_controller()
        return None

    def _on_correction_completed(self, stats):
        """
        Handle correction completed signal.

        Args:
            stats: Correction statistics
        """
        # Update highlighting and tooltips
        self._highlight_correction_cells()
        self._update_correction_tooltips()

        # Refresh the view
        self.refresh()

        # Log completion
        self._logger.info(f"Correction completed: {stats}")

    def _highlight_correction_cells(self):
        """
        Highlight cells based on correction status.

        This method now simply forwards to the TableStateManager functionality.
        """
        if hasattr(self, "_table_state_manager") and self._table_state_manager:
            logger.debug("Using TableStateManager for correction highlighting")
            # The state manager should already have the correction status applied
            # Just refresh the visual highlighting based on current state
            self.update_cell_highlighting_from_state()
        else:
            logger.warning("Unable to highlight correction cells - TableStateManager not available")

    def _update_correction_tooltips(self):
        """
        Update tooltips with correction information.

        This is now a wrapper around update_tooltips_from_state.
        """
        if hasattr(self, "_table_state_manager") and self._table_state_manager:
            self.update_tooltips_from_state()
        else:
            logger.warning("Cannot update correction tooltips: TableStateManager not available")

    def _set_cell_tooltip(self, row, col, tooltip):
        """
        Set tooltip for a cell.

        Args:
            row: Source row index
            col: Source column index
            tooltip: Tooltip text
        """
        if not hasattr(self, "_table_model") or not self._table_model:
            return

        # Map to view indices if needed
        view_index = None
        if hasattr(self, "_proxy_model") and self._proxy_model:
            model_index = self._table_model.index(row, col)
            view_index = self._proxy_model.mapFromSource(model_index)
        else:
            view_index = self._table_model.index(row, col)

        if not view_index or not view_index.isValid():
            return

        # Apply tooltip
        item = self._table_model.itemFromIndex(view_index)
        if item:
            item.setToolTip(tooltip)

    def update_cell_highlighting(self):
        """
        Update cell highlighting based on validation and correction status.

        Uses TableStateManager to highlight cells based on their state.
        """
        if hasattr(self, "_table_state_manager") and self._table_state_manager:
            self.update_cell_highlighting_from_state()
        else:
            logger.warning("Cannot update cell highlighting: TableStateManager not available")
