"""
validation_state_tracker.py

Description: Class for tracking validation states of cells in a table.
Usage:
    tracker = ValidationStateTracker()
    changes = tracker.update_from_validation_results(invalid_rows, validation_columns)
"""

import logging
from typing import Dict, List, Set, Tuple, Optional, Any, Union

import pandas as pd
from PySide6.QtCore import Qt

from chestbuddy.core.validation_enums import ValidationStatus

# Set up logger
logger = logging.getLogger(__name__)


class ValidationStateTracker:
    """
    Tracks validation states for table cells.

    This class maintains a persistent map of cell validation states and
    efficiently calculates which cells need updates when validation changes.

    Attributes:
        _invalid_cells: Dictionary tracking invalid cells by (row, col_name)
    """

    def __init__(self):
        """Initialize the ValidationStateTracker."""
        # Dictionary tracking invalid cells: {(row, col_name): ValidationStatus}
        self._invalid_cells = {}

    def set_invalid(
        self, row: int, col_name: str, status: ValidationStatus = ValidationStatus.INVALID
    ) -> None:
        """
        Mark a cell as invalid with specific status.

        Args:
            row: Row index
            col_name: Column name
            status: Validation status to set (default: ValidationStatus.INVALID)
        """
        self._invalid_cells[(row, col_name)] = status

    def clear_invalid(self, row: int, col_name: str) -> None:
        """
        Clear invalid status for a cell.

        Args:
            row: Row index
            col_name: Column name
        """
        if (row, col_name) in self._invalid_cells:
            del self._invalid_cells[(row, col_name)]

    def is_invalid(self, row: int, col_name: str) -> bool:
        """
        Check if a cell is marked invalid.

        Args:
            row: Row index
            col_name: Column name

        Returns:
            True if the cell is marked invalid, False otherwise
        """
        return (row, col_name) in self._invalid_cells

    def get_status(self, row: int, col_name: str) -> Optional[ValidationStatus]:
        """
        Get validation status for a cell.

        Args:
            row: Row index
            col_name: Column name

        Returns:
            Validation status of the cell, or None if not set
        """
        return self._invalid_cells.get((row, col_name), None)

    def get_invalid_cells(self) -> List[Tuple[int, str]]:
        """
        Get all invalid cells.

        Returns:
            List of (row, col_name) tuples for all invalid cells
        """
        return list(self._invalid_cells.keys())

    def clear_all(self) -> None:
        """Clear all validation states."""
        self._invalid_cells.clear()

    def process_validation_results(
        self, validation_data: pd.DataFrame, validation_cols: List[str]
    ) -> Dict:
        """
        Process validation data from a DataFrame and track changes.

        This method is used to update the validation state from a DataFrame
        containing validation results, where each column ending with '_valid'
        indicates whether a specific field is valid.

        Args:
            validation_data: DataFrame containing validation results
            validation_cols: List of column names ending with '_valid'

        Returns:
            Dictionary with keys 'new_invalid', 'fixed', and 'unchanged' containing
            sets of (row, col_name) tuples for cells in each category
        """
        logger.debug(
            f"Processing validation results for {len(validation_data)} rows with {len(validation_cols)} validation columns"
        )

        # Track cells before update
        old_invalid_cells = set(self._invalid_cells.keys())
        new_invalid_cells = set()

        # Define validatable columns (uppercase because they'll be compared to display column names)
        validatable_columns = ["PLAYER", "SOURCE", "CHEST"]
        logger.debug(f"Validatable columns: {validatable_columns}")

        # Process each row in the validation DataFrame
        invalid_count = 0
        for row_idx, row_data in validation_data.iterrows():
            row_invalid_count = 0

            for val_col in validation_cols:
                # Skip if this validation column has NaN value
                if pd.isna(row_data.get(val_col, None)):
                    continue

                # Check if this validation column failed (False means invalid)
                if not row_data[val_col]:
                    # Get the original column name by removing _valid suffix and converting to uppercase
                    orig_column = val_col.replace("_valid", "").upper()

                    # Only track invalid cells for validatable columns
                    if orig_column in validatable_columns:
                        new_invalid_cells.add((row_idx, orig_column))
                        self.set_invalid(row_idx, orig_column)
                        row_invalid_count += 1

            if row_invalid_count > 0:
                invalid_count += 1

        # Find cells that were invalid but are now valid (fixed)
        fixed_cells = old_invalid_cells - new_invalid_cells
        for row, col in fixed_cells:
            self.clear_invalid(row, col)

        # Calculate cells that remain unchanged
        unchanged_cells = old_invalid_cells.intersection(new_invalid_cells)

        # Log detailed summary
        logger.debug(
            f"Validation summary: {len(new_invalid_cells - old_invalid_cells)} newly invalid cells, "
            f"{len(fixed_cells)} fixed cells, {len(unchanged_cells)} unchanged cells "
            f"across {invalid_count} invalid rows"
        )

        # Return changes for efficient UI updates
        return {
            "new_invalid": new_invalid_cells - old_invalid_cells,
            "fixed": fixed_cells,
            "unchanged": unchanged_cells,
        }

    def update_from_validation_results(
        self, invalid_rows: Dict, validation_columns: List[str]
    ) -> Dict:
        """
        Calculate cell updates from validation results.

        Args:
            invalid_rows: Dictionary of {row_idx: {col_valid: bool}} validation results
            validation_columns: List of column names that can be validated

        Returns:
            Dictionary with keys 'new_invalid', 'fixed', and 'unchanged' containing
            sets of (row, col_name) tuples for cells in each category
        """
        # Track cells before update
        old_invalid_cells = set(self._invalid_cells.keys())
        new_invalid_cells = set()

        # Calculate new invalid cells
        for row_idx in invalid_rows:
            for col_name in validation_columns:
                # Get the validation column name (e.g., player_valid)
                val_col = f"{col_name.lower()}_valid"

                # Skip if this validation column isn't in the results
                if val_col not in invalid_rows[row_idx]:
                    continue

                # Check if this column is invalid in this row
                col_valid = invalid_rows[row_idx].get(val_col, True)
                if not col_valid:
                    new_invalid_cells.add((row_idx, col_name))
                    self.set_invalid(row_idx, col_name)

        # Find cells that were invalid but are now valid
        fixed_cells = old_invalid_cells - new_invalid_cells
        for row, col in fixed_cells:
            self.clear_invalid(row, col)

        # Return changes for efficient UI updates
        return {
            "new_invalid": new_invalid_cells - old_invalid_cells,
            "fixed": fixed_cells,
            "unchanged": old_invalid_cells & new_invalid_cells,
        }
