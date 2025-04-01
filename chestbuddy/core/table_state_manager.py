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
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

# Set up logger
logger = logging.getLogger(__name__)


class CellState(Enum):
    """
    Enumeration of possible cell states.

    These states determine how cells are displayed in the table view.
    """

    NORMAL = 0  # Default state
    INVALID = 1  # Invalid value (failed validation)
    CORRECTABLE = 2  # Invalid but can be corrected
    CORRECTED = 3  # Has been corrected
    PROCESSING = 4  # Currently being processed


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
    state_changed = Signal()

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
        self._cell_states = {}  # (row, col) -> CellState
        self._cell_details = {}  # (row, col) -> str (additional info/tooltip)
        logger.debug("TableStateManager initialized")

    def set_cell_state(self, row: int, col: int, state: CellState) -> None:
        """
        Set the state of a specific cell.

        Args:
            row: Row index
            col: Column index
            state: The cell state to set
        """
        key = (row, col)
        self._cell_states[key] = state
        logger.debug(f"Cell ({row}, {col}) state set to {state.name}")

    def get_cell_state(self, row: int, col: int) -> CellState:
        """
        Get the state of a specific cell.

        Args:
            row: Row index
            col: Column index

        Returns:
            CellState: The cell's current state (NORMAL if not set)
        """
        return self._cell_states.get((row, col), CellState.NORMAL)

    def set_cell_detail(self, row: int, col: int, detail: str) -> None:
        """
        Set additional details for a cell (used for tooltips).

        Args:
            row: Row index
            col: Column index
            detail: Detail text
        """
        self._cell_details[(row, col)] = detail

    def get_cell_details(self, row: int, col: int) -> str:
        """
        Get the additional details for a cell.

        Args:
            row: Row index
            col: Column index

        Returns:
            str: The cell's detail text (empty string if not set)
        """
        return self._cell_details.get((row, col), "")

    def reset_cell_states(self) -> None:
        """Reset all cell states to NORMAL."""
        self._cell_states = {}
        self._cell_details = {}
        logger.debug("All cell states reset to NORMAL")
        self.state_changed.emit()

    def reset_cell_state(self, row: int, col: int) -> None:
        """
        Reset a specific cell state to NORMAL.

        Args:
            row: Row index
            col: Column index
        """
        if (row, col) in self._cell_states:
            del self._cell_states[(row, col)]
        if (row, col) in self._cell_details:
            del self._cell_details[(row, col)]
        logger.debug(f"Cell ({row}, {col}) state reset to NORMAL")

    def reset_rows(self, rows: List[int]) -> None:
        """
        Reset all cells in the specified rows.

        Args:
            rows: List of row indices to reset
        """
        for key in list(self._cell_states.keys()):
            row, _ = key
            if row in rows:
                del self._cell_states[key]
                if key in self._cell_details:
                    del self._cell_details[key]
        logger.debug(f"Reset states for rows: {rows}")
        self.state_changed.emit()

    def get_cells_by_state(self, state: CellState) -> List[Tuple[int, int]]:
        """
        Get all cells with a specific state.

        Args:
            state: The state to filter by

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples for cells with the given state
        """
        return [
            (row, col)
            for (row, col), cell_state in self._cell_states.items()
            if cell_state == state
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

    def update_cell_states_from_validation(self, validation_status: pd.DataFrame) -> None:
        """
        Update cell states based on validation status.

        Args:
            validation_status: DataFrame with validation results
        """
        if validation_status is None or validation_status.empty:
            logger.debug("Empty validation status, nothing to update")
            return

        # Reset existing validation states
        # First get all cells that are currently marked as invalid or correctable
        invalid_cells = self.get_cells_by_state(CellState.INVALID)
        correctable_cells = self.get_cells_by_state(CellState.CORRECTABLE)

        # Reset these cells to remove their status
        for row, col in invalid_cells + correctable_cells:
            self.reset_cell_state(row, col)

        logger.debug(
            f"Reset {len(invalid_cells) + len(correctable_cells)} existing validation states"
        )

        # Check if the validation status has the expected format (ROW_IDX, COL_IDX, STATUS)
        expected_columns = {"ROW_IDX", "COL_IDX", "STATUS"}
        if all(col in validation_status.columns for col in expected_columns):
            # Standard format - use as is
            logger.debug("Using standard validation status format with ROW_IDX, COL_IDX, STATUS")
            # Set new states based on validation status
            for _, row in validation_status.iterrows():
                row_idx = row["ROW_IDX"]
                col_idx = row["COL_IDX"]
                status = row["STATUS"]

                if status == "invalid":
                    self.set_cell_state(row_idx, col_idx, CellState.INVALID)
                    self.set_cell_detail(row_idx, col_idx, "Invalid value: Failed validation")
                    logger.debug(f"Set cell ({row_idx}, {col_idx}) to INVALID state")
        else:
            # Try to convert from ValidationService format
            # Check for column-specific status fields: PLAYER_status, SOURCE_status, etc.
            logger.debug("Converting from validation service format with *_status columns")
            status_columns = [col for col in validation_status.columns if col.endswith("_status")]
            logger.debug(f"Found status columns: {status_columns}")

            # Build a more accurate column map by looking at the actual model columns
            col_map = {}
            if hasattr(self._data_model, "column_names"):
                # Use column_names if available
                for idx, col_name in enumerate(self._data_model.column_names):
                    status_col = f"{col_name}_status"
                    if status_col in status_columns:
                        col_map[status_col] = idx
                        logger.debug(f"Mapped status column {status_col} to index {idx}")
            else:
                # Fallback to hard-coded mapping
                logger.debug("Using fallback column mapping")
                col_map = {
                    "PLAYER_status": 1,  # Assuming PLAYER is column 1
                    "SOURCE_status": 2,  # Assuming SOURCE is column 2
                    "CHEST_status": 3,  # Assuming CHEST is column 3
                    "SCORE_status": 4,  # Assuming SCORE is column 4
                    "CLAN_status": 5,  # Assuming CLAN is column 5
                }

            # Get rows in the data model
            cells_updated = 0
            for data_row_idx, row in validation_status.iterrows():
                # Process each status column
                for status_col in status_columns:
                    status_value = row[status_col]
                    col_name = status_col.split("_status")[0]  # Extract column name

                    # Get column index from our map
                    col_idx = col_map.get(status_col, -1)

                    # If we don't have the column in our map, try to find it
                    if col_idx == -1:
                        # Try to find column index from data model
                        if hasattr(self._data_model, "get_column_index"):
                            col_idx = self._data_model.get_column_index(col_name)
                            if col_idx >= 0:
                                logger.debug(
                                    f"Found column {col_name} at index {col_idx} using get_column_index"
                                )
                        elif hasattr(self._data_model, "get_columns"):
                            for i, col in enumerate(self._data_model.get_columns()):
                                if col == col_name:
                                    col_idx = i
                                    logger.debug(
                                        f"Found column {col_name} at index {col_idx} using get_columns"
                                    )
                                    break
                        elif hasattr(self._data_model, "columns"):
                            for i, col in enumerate(self._data_model.columns):
                                if col == col_name:
                                    col_idx = i
                                    logger.debug(
                                        f"Found column {col_name} at index {col_idx} using columns attribute"
                                    )
                                    break
                        else:
                            # Try to get columns from dataframe directly
                            try:
                                for i, col in enumerate(self._data_model.data.columns):
                                    if col == col_name:
                                        col_idx = i
                                        logger.debug(
                                            f"Found column {col_name} at index {col_idx} in data.columns"
                                        )
                                        break
                            except Exception as e:
                                logger.error(f"Unable to get columns from data model: {e}")

                    # If we found a valid column index and the status is invalid
                    if col_idx >= 0 and str(status_value).lower() in (
                        "invalid",
                        "validation_status.invalid",
                    ):
                        self.set_cell_state(data_row_idx, col_idx, CellState.INVALID)
                        self.set_cell_detail(
                            data_row_idx, col_idx, f"Invalid {col_name}: Failed validation"
                        )
                        logger.debug(f"Set cell ({data_row_idx}, {col_idx}) to INVALID state")
                        cells_updated += 1

                    # Handle correctable status if present
                    if col_idx >= 0 and str(status_value).lower() in (
                        "correctable",
                        "validation_status.correctable",
                    ):
                        self.set_cell_state(data_row_idx, col_idx, CellState.CORRECTABLE)
                        self.set_cell_detail(
                            data_row_idx,
                            col_idx,
                            f"Correctable {col_name}: Can be fixed automatically",
                        )
                        logger.debug(f"Set cell ({data_row_idx}, {col_idx}) to CORRECTABLE state")
                        cells_updated += 1

        # Notify that states have changed
        logger.debug("Emitting state_changed signal after updating validation states")
        self.state_changed.emit()
        logger.debug(
            f"Updated cell states from validation status: "
            f"{len(validation_status)} entries processed"
        )

    def update_cell_states_from_correction(self, correction_status: Dict[str, Any]) -> None:
        """
        Update cell states based on correction status.

        Args:
            correction_status: Dictionary with correction results containing keys:
                              corrected_cells: List of (row, col) tuples
                              original_values: Dict mapping "(row, col)" to original value
                              new_values: Dict mapping "(row, col)" to new value
        """
        if not correction_status:
            logger.debug("No correction status provided, nothing to update")
            return

        if "corrected_cells" not in correction_status:
            logger.debug("Correction status missing 'corrected_cells' key, nothing to update")
            return

        corrected_cells = correction_status.get("corrected_cells", [])
        original_values = correction_status.get("original_values", {})
        new_values = correction_status.get("new_values", {})

        logger.debug(f"Processing correction status with {len(corrected_cells)} corrected cells")

        cells_updated = 0
        for row, col in corrected_cells:
            # Mark cell as corrected
            self.set_cell_state(row, col, CellState.CORRECTED)

            # Add details for tooltip
            key = f"({row}, {col})"
            if key in original_values and key in new_values:
                detail = f"Corrected from '{original_values[key]}' to '{new_values[key]}'"
                self.set_cell_detail(row, col, detail)
                logger.debug(f"Set cell ({row}, {col}) to CORRECTED state with detail: {detail}")
            else:
                logger.debug(f"Set cell ({row}, {col}) to CORRECTED state")

            cells_updated += 1

        # Notify that states have changed
        logger.debug(
            f"Emitting state_changed signal after updating {cells_updated} corrected cells"
        )
        self.state_changed.emit()
        logger.debug(
            f"Updated cell states from correction status: "
            f"{len(corrected_cells)} cells marked as corrected"
        )

    def update_cell_states_from_correctable(self, correctable_cells: List[Tuple[int, int]]) -> None:
        """
        Update cell states to mark cells as correctable.

        Args:
            correctable_cells: List of (row, col) tuples for cells that can be corrected
        """
        for row, col in correctable_cells:
            # Only mark as correctable if not already corrected
            if self.get_cell_state(row, col) != CellState.CORRECTED:
                self.set_cell_state(row, col, CellState.CORRECTABLE)
                self.set_cell_detail(row, col, "This value can be corrected automatically")

        # Notify that states have changed
        self.state_changed.emit()
        logger.debug(
            f"Updated correctable cell states: {len(correctable_cells)} cells marked as correctable"
        )
