"""
ChestDataModel module.

This module provides the ChestDataModel class for managing chest data.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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
        """Emit the model_changed and data_changed signals."""
        super()._notify_change()
        self.data_changed.emit()

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
        # Ensure all expected columns are present
        for col in self.EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        # Keep only the expected columns in the specified order
        self._data = df[self.EXPECTED_COLUMNS].copy()

        # Initialize validation and correction status DataFrames
        self._init_status_dataframes()

        # Emit the data changed signal
        self._notify_change()

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
        return (
            self._validation_status.copy() if not self._validation_status.empty else pd.DataFrame()
        )

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
        return (
            self._correction_status.copy() if not self._correction_status.empty else pd.DataFrame()
        )

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
            self._validation_status = pd.DataFrame(index=self._data.index)
            self._correction_status = pd.DataFrame(index=self._data.index)

            # Add status columns for each data column
            for col in self.EXPECTED_COLUMNS:
                self._validation_status[f"{col}_valid"] = True
                self._correction_status[f"{col}_corrected"] = False
                self._correction_status[f"{col}_original"] = self._data[col].copy()

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
                new_correction_row[f"{col}_original"] = self._data.iloc[-1][col]

            self._correction_status = pd.concat(
                [self._correction_status, pd.DataFrame([new_correction_row])], ignore_index=True
            )
