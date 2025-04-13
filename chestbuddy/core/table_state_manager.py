"""
table_state_manager.py

Description: Manages cell states and facilitates batch processing for the data view
Usage:
    manager = TableStateManager(data_model)
    manager.set_cell_state(0, 1, CellState.INVALID)
    manager.process_in_batches(process_func, total_rows, progress_callback)
"""

import logging
import time
from enum import Enum
from typing import Dict, List, Tuple, Callable, Any, Set, Optional
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication
from dataclasses import dataclass, field

# Set up logger
logger = logging.getLogger(__name__)


class CellState(Enum):
    """
    Enumeration of possible cell states.

    These states determine how cells are displayed in the table view.
    """

    UNKNOWN = 0
    VALID = 1
    NORMAL = 2  # Default state
    INVALID = 3  # Invalid value (failed validation)
    CORRECTABLE = 4  # Invalid but can be corrected
    CORRECTED = 5  # Has been corrected
    PROCESSING = 6  # Currently being processed
    WARNING = 7  # Indicates a potential issue, but data is valid
    INFO = 8  # Informational state, data is valid


# --- New Dataclass for Full Cell State ---
@dataclass
class CellFullState:
    """Holds the complete state information for a single cell."""

    validation_status: CellState = CellState.NORMAL
    error_details: Optional[str] = None
    # Using field to default to an empty list for suggestions
    correction_suggestions: List[Any] = field(default_factory=list)

    # You could add other state aspects here later, e.g.:
    # is_dirty: bool = False
    # formatting: Optional[dict] = None


class TableStateManager(QObject):
    """
    Manages cell states and facilitates batch processing for the data view.

    This class tracks the state of each cell in the table and provides
    methods for batch processing data operations with progress updates.

    Attributes:
        state_changed (Signal): Emitted when cell states change
        BATCH_SIZE (int): Number of rows to process in each batch
    """

    # Signals
    state_changed = Signal(set)

    # Default batch size
    BATCH_SIZE = 100

    def __init__(self, data_model):
        """
        Initialize the TableStateManager with a data model.

        Args:
            data_model: The data model containing the table data
        """
        super().__init__()
        self._data_model = data_model
        # Store CellFullState objects instead of just CellState enum
        self._cell_states: Dict[Tuple[int, int], CellFullState] = {}
        # _cell_details is now part of CellFullState
        # self._cell_details = {}
        self._headers_map = self._create_headers_map()
        logger.debug("TableStateManager initialized")

    def _create_headers_map(self) -> Dict[str, int]:
        """Create a mapping from column names to column indices."""
        headers_map = {}
        model = self._data_model  # Use local var for clarity
        logger.debug(f"_create_headers_map: Checking model type: {type(model)}")
        has_model = model is not None
        has_col_count = hasattr(model, "columnCount")
        has_header_data = hasattr(model, "headerData")
        logger.debug(
            f"_create_headers_map: has_model={has_model}, has_col_count={has_col_count}, has_header_data={has_header_data}"
        )

        if has_model and has_col_count and has_header_data:
            try:
                num_cols = model.columnCount()
                logger.debug(f"_create_headers_map: Found {num_cols} columns.")
                for col_idx in range(num_cols):
                    # Assuming headerData with Qt.Horizontal orientation gives the name
                    header_name = model.headerData(col_idx, Qt.Horizontal, Qt.DisplayRole)
                    logger.debug(f"_create_headers_map: Header for col {col_idx} = {header_name}")
                    if header_name:
                        headers_map[str(header_name)] = col_idx
                logger.debug(f"Created headers map: {headers_map}")
            except Exception as e:
                logger.error(f"Failed to create headers map from data model: {e}")
        else:
            logger.warning("Data model not suitable for creating headers map in TableStateManager")
        return headers_map

    # Add a method to update the map if headers change
    def update_headers_map(self) -> None:
        """Update the internal headers map based on the current data model headers."""
        self._headers_map = self._create_headers_map()
        logger.info("TableStateManager headers map updated.")

    def set_cell_state(self, row: int, col: int, state: CellState) -> None:
        """DEPRECATED - Use update_states. Sets only the validation status part of the state."""
        logger.warning("set_cell_state is deprecated, use update_states for full state management.")
        key = (row, col)
        current_full_state = self._cell_states.get(key, CellFullState())
        if current_full_state.validation_status != state:
            current_full_state.validation_status = state
            self._cell_states[key] = current_full_state
            self.state_changed.emit({key})
            logger.debug(f"Cell ({row}, {col}) validation state set to {state.name}")

    def get_cell_state(self, row: int, col: int) -> CellState:
        """Gets only the validation status part of the cell's state."""
        return self._cell_states.get((row, col), CellFullState()).validation_status

    def set_cell_detail(self, row: int, col: int, detail: str) -> None:
        """DEPRECATED - Use update_states. Sets only the error details part of the state."""
        logger.warning(
            "set_cell_detail is deprecated, use update_states for full state management."
        )
        key = (row, col)
        current_full_state = self._cell_states.get(key, CellFullState())
        if current_full_state.error_details != detail:
            current_full_state.error_details = detail
            self._cell_states[key] = current_full_state
            self.state_changed.emit({key})
            logger.debug(f"Cell ({row}, {col}) details set.")

    def get_cell_details(self, row: int, col: int) -> str:
        """Gets only the error details part of the cell's state."""
        return self._cell_states.get((row, col), CellFullState()).error_details or ""

    def get_full_cell_state(self, row: int, col: int) -> Optional[CellFullState]:
        """
        Gets the full state object for a specific cell, including validation,
        details, and correction info.

        Returns:
            Optional[CellFullState]: The full state object, or None if no specific state is stored.
        """
        # Return a copy to prevent external modification?
        # For performance, returning direct reference might be okay if callers are trusted.
        return self._cell_states.get((row, col))

    def update_states(self, changes: Dict[Tuple[int, int], CellFullState]) -> None:
        """
        Updates the state for multiple cells at once.

        Merges the provided changes with the existing state for each cell.
        Emits the state_changed signal *once* with the set of affected cells.

        Args:
            changes: A dictionary where keys are (row, col) tuples and values
                     are CellFullState objects containing the state aspects to update.
                     If a state aspect in the value is None, it's ignored (not cleared).
                     To clear details/suggestions, provide an empty string/list.
        """
        affected_cells: Set[Tuple[int, int]] = set()
        for key, change_state in changes.items():
            current_state = self._cell_states.get(key, CellFullState())
            changed = False

            # Merge validation status if provided in change
            if change_state.validation_status != current_state.validation_status:
                current_state.validation_status = change_state.validation_status
                changed = True

            # Merge error details if provided in change (allow setting to None/empty)
            if change_state.error_details != current_state.error_details:
                current_state.error_details = change_state.error_details
                changed = True

            # Merge correction suggestions if provided (allow setting to empty list)
            if change_state.correction_suggestions != current_state.correction_suggestions:
                current_state.correction_suggestions = change_state.correction_suggestions
                changed = True

            if changed:
                self._cell_states[key] = current_state
                affected_cells.add(key)
            # Remove state entry if it's back to default normal state with no details/suggestions?
            # Maybe add this later if memory becomes an issue.
            # elif current_state == CellFullState(): # Check if default
            #    if key in self._cell_states:
            #        del self._cell_states[key]
            #        affected_cells.add(key) # Still needs UI update

        if affected_cells:
            logger.debug(f"Updated state for {len(affected_cells)} cells.")
            self.state_changed.emit(affected_cells)
        else:
            logger.debug("No state changes detected in update_states call.")

    def reset_cell_states(self) -> None:
        """Reset all cell states to default."""
        # Get all previously affected cells to notify UI
        affected_cells = set(self._cell_states.keys())
        self._cell_states = {}
        # self._cell_details = {} # Removed
        logger.debug("All cell states reset")
        if affected_cells:
            self.state_changed.emit(affected_cells)

    def reset_cell_state(self, row: int, col: int) -> None:
        """Reset a specific cell state to default."""
        key = (row, col)
        if key in self._cell_states:
            del self._cell_states[key]
            # if key in self._cell_details: # Removed
            #     del self._cell_details[key]
            logger.debug(f"Cell ({row}, {col}) state reset")
            self.state_changed.emit({key})

    def reset_rows(self, rows: List[int]) -> None:
        """
        Reset all cells in the specified rows.
        """
        affected_cells = set()
        rows_set = set(rows)
        for key in list(self._cell_states.keys()):  # Iterate over a copy of keys
            row, _ = key
            if row in rows_set:
                del self._cell_states[key]
                affected_cells.add(key)
                # if key in self._cell_details: # Removed
                #     del self._cell_details[key]
        logger.debug(f"Reset states for rows: {rows}")
        if affected_cells:
            self.state_changed.emit(affected_cells)

    def get_cells_by_state(self, state: CellState) -> List[Tuple[int, int]]:
        """
        Get all cells with a specific validation state.

        Args:
            state: The validation state (CellState enum) to filter by

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples for cells with the given state
        """
        return [
            key
            for key, full_state in self._cell_states.items()
            if full_state.validation_status == state
        ]

    def process_in_batches(
        self,
        process_func: Callable[[int], Any],
        total_rows: int,
        progress_callback: Callable[[int, int], None] = None,
    ) -> List[Any]:
        """
        Process data in batches with progress updates.

        This method divides the processing into batches and provides
        progress updates during processing.

        Args:
            process_func: Function to process each row, takes row index as parameter
            total_rows: Total number of rows to process
            progress_callback: Function to report progress (current, total)

        Returns:
            List[Any]: List of results from process_func for each row
        """
        results = []
        processed = 0

        # Report initial progress
        if progress_callback:
            progress_callback(0, total_rows)

        # Process in batches
        for batch_start in range(0, total_rows, self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, total_rows)
            batch_size = batch_end - batch_start

            logger.debug(
                f"Processing batch {batch_start // self.BATCH_SIZE + 1}: "
                f"rows {batch_start} to {batch_end - 1}"
            )

            # Process each row in the batch
            for row_idx in range(batch_start, batch_end):
                result = process_func(row_idx)
                results.append(result)
                processed += 1

                # Update progress every 10 rows or at the end of a batch
                if progress_callback and (processed % 10 == 0 or processed == batch_end):
                    progress_callback(processed, total_rows)

                # Process UI events to keep the application responsive
                QApplication.processEvents()

            # Add a small delay between batches to keep UI responsive
            time.sleep(0.01)

        # Report final progress
        if progress_callback:
            progress_callback(total_rows, total_rows)

        logger.debug(f"Batch processing completed: {total_rows} rows processed")
        return results

    def get_affected_rows_columns(self, original_data: pd.DataFrame) -> Dict[str, List]:
        """
        Get rows and columns that have changed compared to original data.

        Args:
            original_data: DataFrame with original data before changes

        Returns:
            Dict with 'rows' and 'columns' keys containing lists of affected indices
        """
        if self._data_model is None or not hasattr(self._data_model, "data"):
            return {"rows": [], "columns": []}

        current_data = self._data_model.data
        if current_data is None or original_data is None:
            return {"rows": [], "columns": []}

        # Ensure we're comparing DataFrames with the same shape
        if original_data.shape != current_data.shape:
            logger.warning("Cannot compare DataFrames with different shapes")
            affected_rows = set(range(min(len(original_data), len(current_data))))
            affected_columns = set(
                col for col in current_data.columns if col in original_data.columns
            )
            return {"rows": list(affected_rows), "columns": list(affected_columns)}

        # Find rows with any differences
        mask = original_data != current_data
        affected_rows = set()
        affected_columns = set()

        # Collect affected rows and columns
        for col in mask.columns:
            rows_with_changes = mask.index[mask[col]].tolist()
            if rows_with_changes:
                affected_rows.update(rows_with_changes)
                affected_columns.add(col)

        logger.debug(
            f"Identified {len(affected_rows)} affected rows and "
            f"{len(affected_columns)} affected columns"
        )

        return {"rows": list(affected_rows), "columns": list(affected_columns)}

    # --- Add method for adapters to get column names --- #
    def get_column_names(self) -> List[str]:
        """Returns the list of current column names based on the headers map."""
        # Sort by index to maintain order
        return sorted(self._headers_map, key=self._headers_map.get)

    # --- New Method for CorrectionService ---
    def get_validation_status_df(self) -> pd.DataFrame:
        """
        Constructs and returns a DataFrame representing the current validation
        status of all cells.

        Returns:
            pd.DataFrame: A DataFrame indexed by row, with columns like
                          'ColumnName_status' containing ValidationStatus enums.
                          Returns an empty DataFrame if no states are stored or if
                          the header map is not available.
        """
        if not self._cell_states or not self._headers_map:
            return pd.DataFrame()

        # Determine max row and col index from stored states
        max_row = 0
        max_col = 0
        if self._cell_states:
            rows, cols = zip(*self._cell_states.keys())
            max_row = max(rows) if rows else -1
            max_col = max(cols) if cols else -1

        # Need column names to create the DataFrame columns
        # Invert the headers map: index -> name
        idx_to_name = {idx: name for name, idx in self._headers_map.items()}
        if not idx_to_name or max_col >= len(idx_to_name):
            logger.warning(
                "Header map seems inconsistent with stored cell states. Cannot create status DF."
            )
            return pd.DataFrame()

        # Prepare data for the DataFrame
        data = {}
        for col_idx in range(max_col + 1):
            col_name = idx_to_name.get(col_idx)
            if not col_name:
                continue  # Should not happen if map is correct
            status_col_name = f"{col_name}_status"  # Naming convention
            # Initialize column with default state
            col_data = [CellState.NORMAL] * (max_row + 1)
            for row_idx in range(max_row + 1):
                full_state = self._cell_states.get((row_idx, col_idx))
                if full_state:
                    col_data[row_idx] = full_state.validation_status
            data[status_col_name] = col_data

        status_df = pd.DataFrame(data)
        return status_df

    # --- End New Method ---
