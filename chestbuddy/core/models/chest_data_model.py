"""
ChestDataModel module.

This module provides the ChestDataModel class for managing chest data.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import time

import pandas as pd
from PySide6.QtCore import Signal

from chestbuddy.core.models.base_model import BaseModel
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class ChestDataModel(BaseModel):
    """
    Manages the chest data using pandas DataFrames.

    The ChestDataModel is responsible for storing and managing the chest data,
    providing methods for filtering, updating, and manipulating the data.
    Follows the Observer pattern by emitting signals when the data changes.

    Attributes:
        data_changed (Signal): Signal emitted when the data is changed.
        validation_changed (Signal): Signal emitted when validation status changes.
        correction_applied (Signal): Signal emitted when corrections are applied.

    Implementation Notes:
        - Uses pandas DataFrame as the primary data structure
        - Emits signals to notify observers of changes
        - Provides methods for filtering and manipulating data
    """

    # Define signals
    data_changed = Signal()
    validation_changed = Signal()
    correction_applied = Signal()

    # Define expected columns
    EXPECTED_COLUMNS = ["Date", "Player Name", "Source/Location", "Chest Type", "Value", "Clan"]

    def __init__(self) -> None:
        """Initialize the ChestDataModel with an empty DataFrame."""
        super().__init__()

        # Initialize the data DataFrame
        self._data = pd.DataFrame(columns=self.EXPECTED_COLUMNS)

        # Initialize validation and correction status DataFrames
        self._validation_status = pd.DataFrame()
        self._correction_status = pd.DataFrame()

        # Get the config manager
        self._config = ConfigManager()

    def initialize(self) -> None:
        """Initialize the model with an empty DataFrame."""
        self._data = pd.DataFrame(columns=self.EXPECTED_COLUMNS)
        self._validation_status = pd.DataFrame()
        self._correction_status = pd.DataFrame()
        self._notify_change()

    def clear(self) -> None:
        """Clear all data and status DataFrames."""
        self._data = pd.DataFrame(columns=self.EXPECTED_COLUMNS)
        self._validation_status = pd.DataFrame()
        self._correction_status = pd.DataFrame()
        self._notify_change()

    def _notify_change(self) -> None:
        """Emit the data changed signal."""
        # Only emit if not explicitly blocked
        if not hasattr(self, "_block_signals") or not self._block_signals:
            # Add protection against cyclic emissions
            try:
                # Use a signal rate limiter to prevent rapid repeated emissions
                current_time = time.time()

                # Initialize last emit time if it doesn't exist
                if not hasattr(self, "_last_notify_time"):
                    self._last_notify_time = 0.0

                # Only emit if sufficient time has passed since last emission (500ms minimum)
                if current_time - self._last_notify_time > 0.5:
                    # Use a careful approach to emit the signal
                    self.data_changed.emit()
                    self._last_notify_time = current_time
                else:
                    logger.debug(
                        f"Skipping rapid data_changed signal emission (elapsed: {current_time - self._last_notify_time:.3f}s)"
                    )
            except Exception as e:
                logger.error(f"Error in _notify_change: {e}")

    @property
    def data(self) -> pd.DataFrame:
        """
        Get a copy of the chest data DataFrame.

        Returns:
            A copy of the chest data DataFrame.
        """
        return self._data.copy()

    @property
    def is_empty(self) -> bool:
        """
        Check if the data is empty.

        Returns:
            True if the data is empty, False otherwise.
        """
        return self._data.empty

    @property
    def row_count(self) -> int:
        """
        Get the number of rows in the data.

        Returns:
            The number of rows in the data.
        """
        return len(self._data)

    @property
    def column_names(self) -> List[str]:
        """
        Get the column names in the data.

        Returns:
            The list of column names.
        """
        return list(self._data.columns)

    @property
    def file_path(self) -> Optional[Path]:
        """
        Get the last loaded file path.

        Returns:
            The path to the last loaded file, or None if no file has been loaded.
        """
        last_file = self._config.get("Files", "last_file", None)
        return Path(last_file) if last_file else None

    def load_from_csv(self, file_path: Union[str, Path]) -> bool:
        """
        Load chest data from a CSV file.

        Args:
            file_path: The path to the CSV file.

        Returns:
            True if the data was loaded successfully, False otherwise.
        """
        try:
            # Convert to Path object
            path = Path(file_path)

            # Attempt to read the CSV file
            df = pd.read_csv(path, encoding="utf-8")

            # Check if the required columns are present
            missing_columns = set(self.EXPECTED_COLUMNS) - set(df.columns)
            if missing_columns:
                logger.warning(f"Missing required columns: {missing_columns}")
                return False

            # Ensure all expected columns are present (add empty ones if missing)
            for col in self.EXPECTED_COLUMNS:
                if col not in df.columns:
                    df[col] = ""

            # Keep only the expected columns in the specified order
            self._data = df[self.EXPECTED_COLUMNS].copy()

            # Initialize validation and correction status DataFrames
            self._init_status_dataframes()

            # Add the file to recent files
            self._config.add_recent_file(file_path)

            # Update the last import directory
            self._config.set_path("Files", "last_import_dir", path.parent)

            # Emit the data changed signal
            self._notify_change()

            return True

        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return False

    def save_to_csv(self, file_path: Union[str, Path]) -> bool:
        """
        Save chest data to a CSV file.

        Args:
            file_path: The path to save the CSV file.

        Returns:
            True if the data was saved successfully, False otherwise.
        """
        try:
            # Convert to Path object
            path = Path(file_path)

            # Create parent directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Save the data to the CSV file
            self._data.to_csv(path, index=False, encoding="utf-8")

            # Update the last export directory
            self._config.set_path("Files", "last_export_dir", path.parent)

            return True

        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")
            return False

    def update_data(self, df: pd.DataFrame) -> None:
        """
        Update the chest data with a new DataFrame.

        Args:
            df: The new DataFrame to use.
        """
        # Track whether we were already blocking signals
        already_blocking = self.signalsBlocked()

        # If signals weren't already blocked, block them now
        if not already_blocking:
            self.blockSignals(True)

        try:
            # Cancel any current operations to prevent signal cascades
            self._block_signals = True

            try:
                # Ensure all expected columns are present
                for col in self.EXPECTED_COLUMNS:
                    if col not in df.columns:
                        df[col] = ""

                # Keep only the expected columns in the specified order
                self._data = df[self.EXPECTED_COLUMNS].copy()

                # Initialize validation and correction status DataFrames
                self._init_status_dataframes()
            finally:
                # Always unblock internal signals
                self._block_signals = False

            # Only notify change if we weren't already blocking signals
            if not already_blocking:
                # Unblock signals before emitting
                self.blockSignals(False)
                self._notify_change()
        except Exception as e:
            # Ensure signals are unblocked on exception
            if not already_blocking:
                self.blockSignals(False)
            logger.error(f"Error updating data: {e}")
            raise

    def get_row(self, index: int) -> pd.Series:
        """
        Get a specific row from the data.

        Args:
            index: The row index.

        Returns:
            The row as a pandas Series.
        """
        if 0 <= index < len(self._data):
            return self._data.iloc[index].copy()
        return pd.Series()

    def update_row(self, index: int, row_data: Dict[str, Any]) -> bool:
        """
        Update a specific row in the data.

        Args:
            index: The row index.
            row_data: The new data for the row.

        Returns:
            True if the row was updated successfully, False otherwise.
        """
        if 0 <= index < len(self._data):
            for col, value in row_data.items():
                if col in self._data.columns:
                    self._data.at[index, col] = value

            # Emit the data changed signal
            self._notify_change()
            return True
        return False

    def update_cell(self, row_index: int, column_name: str, value: Any) -> None:
        """
        Update a single cell in the data.

        Args:
            row_index: The row index
            column_name: The column name
            value: The new value
        """
        if 0 <= row_index < len(self._data) and column_name in self._data.columns:
            # Handle date columns specifically
            if column_name == "Date" and not isinstance(value, str):
                value = str(value)  # Convert to string to avoid type inference issues

            # Update the main data
            self._data.at[row_index, column_name] = value

            # Update validation status - mark as needing revalidation
            if (
                not self._validation_status.empty
                and f"{column_name}_valid" in self._validation_status.columns
            ):
                self._validation_status.at[row_index, f"{column_name}_valid"] = True

            # Update correction status - track the change
            if not self._correction_status.empty:
                if f"{column_name}_corrected" in self._correction_status.columns:
                    self._correction_status.at[row_index, f"{column_name}_corrected"] = True

            # Emit the data changed signal
            self._notify_change()

    def add_row(self, row_data: Dict[str, Any]) -> int:
        """
        Add a new row to the data.

        Args:
            row_data: The data for the new row.

        Returns:
            The index of the new row.
        """
        # Create a new row with default values
        new_row = {col: "" for col in self.EXPECTED_COLUMNS}

        # Update with provided values
        for col, value in row_data.items():
            if col in new_row:
                new_row[col] = value

        # Add the row to the DataFrame
        self._data = pd.concat([self._data, pd.DataFrame([new_row])], ignore_index=True)

        # Update status DataFrames
        self._add_status_row()

        # Emit the data changed signal
        self._notify_change()

        return len(self._data) - 1

    def delete_row(self, index: int) -> bool:
        """
        Delete a specific row from the data.

        Args:
            index: The row index.

        Returns:
            True if the row was deleted successfully, False otherwise.
        """
        if 0 <= index < len(self._data):
            self._data = self._data.drop(index).reset_index(drop=True)

            # Update status DataFrames
            if not self._validation_status.empty:
                self._validation_status = self._validation_status.drop(index).reset_index(drop=True)

            if not self._correction_status.empty:
                self._correction_status = self._correction_status.drop(index).reset_index(drop=True)

            # Emit the data changed signal
            self._notify_change()
            return True
        return False

    def filter_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter the data based on the provided filters.

        Args:
            filters: Dictionary of column names and filter values.

        Returns:
            Filtered DataFrame.
        """
        df = self._data.copy()

        for col, value in filters.items():
            if col in df.columns:
                if isinstance(value, list):
                    # If the value is a list, filter for rows where the column value is in the list
                    df = df[df[col].isin(value)]
                else:
                    # Otherwise, filter for exact matches
                    df = df[df[col] == value]

        return df

    def get_unique_values(self, column: str) -> List[str]:
        """
        Get unique values for a specific column.

        Args:
            column: The column name.

        Returns:
            List of unique values in the column.
        """
        if column in self._data.columns:
            # Get unique values and remove any NaN values
            values = self._data[column].dropna().unique().tolist()
            return [str(val) for val in values]
        return []

    def get_column_statistics(self, column: str) -> Dict[str, Any]:
        """
        Get statistics for a specific column.

        Args:
            column: The column name.

        Returns:
            Dictionary of statistics for the column.
        """
        stats = {}

        if column in self._data.columns:
            if self._data[column].dtype in ["int64", "float64"]:
                # Numeric column
                stats["min"] = self._data[column].min()
                stats["max"] = self._data[column].max()
                stats["mean"] = self._data[column].mean()
                stats["median"] = self._data[column].median()
                stats["sum"] = self._data[column].sum()
            else:
                # Non-numeric column
                value_counts = self._data[column].value_counts()
                stats["unique_count"] = len(value_counts)
                stats["most_common"] = value_counts.index[0] if not value_counts.empty else ""
                stats["most_common_count"] = value_counts.iloc[0] if not value_counts.empty else 0

        return stats

    def get_validation_status(self) -> pd.DataFrame:
        """
        Get the validation status DataFrame.

        Returns:
            The validation status DataFrame.
        """
        if self._validation_status.empty:
            # Return a completely empty DataFrame with no columns to avoid pandas operations
            return pd.DataFrame()

        # Avoid recursion by creating a completely new DataFrame manually
        try:
            # Construct the DataFrame manually without using to_dict or copy operations
            new_df = pd.DataFrame()

            # Copy basic data without any inference or complex operations
            for col in self._validation_status.columns:
                # Convert values to simple Python objects to avoid pandas complexity
                values = [
                    str(x) if col.endswith("_original") else bool(x)
                    for x in self._validation_status[col].values
                ]
                new_df[col] = values

            return new_df
        except RecursionError:
            logger.warning("Recursion detected in get_validation_status, returning empty DataFrame")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error in get_validation_status: {e}")
            return pd.DataFrame()

    def set_validation_status(self, status_df: pd.DataFrame) -> None:
        """
        Set the validation status DataFrame.

        Args:
            status_df: The new validation status DataFrame.
        """
        self._validation_status = status_df.copy()
        self.validation_changed.emit()

    def get_correction_status(self) -> pd.DataFrame:
        """
        Get the correction status DataFrame.

        Returns:
            The correction status DataFrame.
        """
        if self._correction_status.empty:
            # Return a completely empty DataFrame with no columns to avoid pandas operations
            return pd.DataFrame()

        # Avoid recursion by creating a completely new DataFrame manually
        try:
            # Construct the DataFrame manually without using to_dict or copy operations
            new_df = pd.DataFrame()

            # Copy basic data without any inference or complex operations
            for col in self._correction_status.columns:
                # Convert values to simple Python objects to avoid pandas complexity
                values = [
                    str(x) if col.endswith("_original") else bool(x)
                    for x in self._correction_status[col].values
                ]
                new_df[col] = values

            return new_df
        except RecursionError:
            logger.warning("Recursion detected in get_correction_status, returning empty DataFrame")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error in get_correction_status: {e}")
            return pd.DataFrame()

    def set_correction_status(self, status_df: pd.DataFrame) -> None:
        """
        Set the correction status DataFrame.

        Args:
            status_df: The new correction status DataFrame.
        """
        self._correction_status = status_df.copy()
        self.correction_applied.emit()

    def _init_status_dataframes(self) -> None:
        """Initialize the validation and correction status DataFrames."""
        if not self._data.empty:
            # Create DataFrames with the same number of rows as the data
            row_count = len(self._data)
            self._validation_status = pd.DataFrame(index=range(row_count))
            self._correction_status = pd.DataFrame(index=range(row_count))

            # Add status columns for each data column
            for col in self.EXPECTED_COLUMNS:
                # Set validation status
                self._validation_status[f"{col}_valid"] = True

                # Set correction status
                self._correction_status[f"{col}_corrected"] = False

                # Convert ALL columns to strings to prevent pandas type inference issues
                # This is crucial for avoiding recursion errors with date columns
                self._correction_status[f"{col}_original"] = self._data[col].astype(str)

    def _add_status_row(self) -> None:
        """Add a new row to the status DataFrames when a row is added to the data."""
        if not self._validation_status.empty:
            # Create a new row for validation status
            new_validation_row = {f"{col}_valid": True for col in self.EXPECTED_COLUMNS}
            self._validation_status = pd.concat(
                [self._validation_status, pd.DataFrame([new_validation_row])], ignore_index=True
            )

        if not self._correction_status.empty:
            # Create a new row for correction status
            new_correction_row = {f"{col}_corrected": False for col in self.EXPECTED_COLUMNS}
            for col in self.EXPECTED_COLUMNS:
                # Convert ALL values to strings to prevent type inference issues
                new_correction_row[f"{col}_original"] = str(self._data.iloc[-1][col])

            self._correction_status = pd.concat(
                [self._correction_status, pd.DataFrame([new_correction_row])], ignore_index=True
            )

    def get_cell_validation_status(self, row_idx: int, column_name: str) -> Dict[str, Any]:
        """
        Get the validation status for a specific cell.

        Args:
            row_idx: The index of the row.
            column_name: The name of the column.

        Returns:
            Dictionary with validation status for the cell.
        """
        if self._validation_status.empty or row_idx >= len(self._validation_status):
            return {"valid": True}

        status_col = f"{column_name}_valid"
        if status_col in self._validation_status.columns:
            # Access the value directly without DataFrame operations
            try:
                is_valid = self._validation_status.iloc[row_idx][status_col]
                return {"valid": bool(is_valid)}
            except Exception as e:
                logger.error(f"Error getting cell validation status: {e}")
                return {"valid": True}

        return {"valid": True}

    def get_cell_correction_status(self, row_idx: int, column_name: str) -> Dict[str, Any]:
        """
        Get the correction status for a specific cell.

        Args:
            row_idx: The index of the row.
            column_name: The name of the column.

        Returns:
            Dictionary with correction status for the cell.
        """
        if self._correction_status.empty or row_idx >= len(self._correction_status):
            return {"corrected": False, "original": ""}

        status_col = f"{column_name}_corrected"
        original_col = f"{column_name}_original"
        result = {"corrected": False, "original": ""}

        try:
            if status_col in self._correction_status.columns:
                result["corrected"] = bool(self._correction_status.iloc[row_idx][status_col])

            if original_col in self._correction_status.columns:
                result["original"] = str(self._correction_status.iloc[row_idx][original_col])
        except Exception as e:
            logger.error(f"Error getting cell correction status: {e}")

        return result

    def get_row_validation_status(self, row_idx: int) -> Optional[Dict[str, str]]:
        """
        Get the validation status for a specific row.

        Args:
            row_idx: The row index to get the validation status for.

        Returns:
            A dictionary mapping rule names to error messages, or None if there are no issues.
        """
        try:
            if self._validation_status is None or row_idx >= len(self._validation_status):
                return None

            # Check if the row exists in the validation status
            if row_idx not in self._validation_status.index:
                return None

            # Get the row from the validation status
            row = self._validation_status.loc[row_idx]

            # Extract rule names and messages
            result = {}
            for column in row.index:
                if pd.notna(row[column]) and row[column]:
                    result[column] = row[column]

            return result if result else None
        except Exception as e:
            logger.error(f"Error getting row validation status: {e}")
            return None

    def get_row_correction_status(self, row_idx: int) -> Optional[Dict[str, Tuple[Any, Any]]]:
        """
        Get the correction status for a specific row.

        Args:
            row_idx: The row index to get the correction status for.

        Returns:
            A dictionary mapping column names to tuples of (original, corrected) values,
            or None if there are no corrections.
        """
        try:
            if self._correction_status is None or row_idx >= len(self._correction_status):
                return None

            # Check if the row exists in the correction status
            if row_idx not in self._correction_status.index:
                return None

            # Get the row from the correction status
            row = self._correction_status.loc[row_idx]

            # Extract column names and correction information
            result = {}
            for column in row.index:
                if pd.notna(row[column]) and row[column]:
                    # Parse the correction info from the string
                    try:
                        parts = row[column].split(" -> ")
                        if len(parts) == 2:
                            original = parts[0]
                            corrected = parts[1]
                            result[column] = (original, corrected)
                    except Exception:
                        # If parsing fails, just use the raw string
                        result[column] = (row[column], row[column])

            return result if result else None
        except Exception as e:
            logger.error(f"Error getting row correction status: {e}")
            return None

    def get_correction_row_count(self) -> int:
        """
        Get the count of rows that have corrections applied.

        This method avoids returning a full DataFrame which can cause recursion issues.

        Returns:
            The number of rows with corrections applied.
        """
        if self._correction_status.empty:
            return 0

        try:
            # Count rows that have at least one correction applied
            correction_columns = [
                col for col in self._correction_status.columns if col.endswith("_corrected")
            ]

            if not correction_columns:
                return 0

            # Count rows where any correction column is True
            row_count = 0
            for i in range(len(self._correction_status)):
                row = self._correction_status.iloc[i]
                if any(row[col] for col in correction_columns):
                    row_count += 1

            return row_count
        except Exception as e:
            logger.error(f"Error getting correction row count: {e}")
            return 0

    def get_invalid_rows(self) -> List[int]:
        """
        Get the list of row indices that have validation issues.

        This method avoids returning a full DataFrame which can cause recursion issues.

        Returns:
            List of row indices with validation issues.
        """
        if self._validation_status.empty:
            return []

        try:
            # Get all validation columns
            validation_columns = [
                col for col in self._validation_status.columns if col.endswith("_valid")
            ]

            if not validation_columns:
                return []

            # Find rows where any validation column is False
            invalid_rows = []
            for i in range(len(self._validation_status)):
                row = self._validation_status.iloc[i]
                if any(not row[col] for col in validation_columns):
                    invalid_rows.append(i)

            return invalid_rows
        except Exception as e:
            logger.error(f"Error getting invalid rows: {e}")
            return []
