"""
data_state.py

Description: Provides the DataState class for efficiently tracking data state.
Usage:
    from chestbuddy.core.state.data_state import DataState

    # Create a state from a DataFrame
    state = DataState(dataframe)

    # Compare with another state
    changes = state.get_changes(other_state)

    # Check if specific column changed
    if changes["column_changes"]["PLAYER"]:
        # Handle column change
"""

import time
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Set

import pandas as pd

logger = logging.getLogger(__name__)


class DataState:
    """
    Represents the state of data for efficient change tracking.

    This class captures the essential state information from a DataFrame
    and provides methods for comparing states to detect specific changes.

    Attributes:
        _row_count (int): Number of rows in the data
        _column_names (List[str]): List of column names
        _last_updated (float): Timestamp of last update
        _column_stats (Dict[str, Dict[str, Any]]): Statistics for each column
        _hash_value (str): Hash of the data state for quick comparison

    Implementation Notes:
        - More efficient than serializing entire DataFrames
        - Allows detection of specific changes in data
        - Supports column-specific change tracking
        - Uses statistical summaries for change detection
    """

    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize a DataState object.

        Args:
            data: Optional DataFrame to initialize the state from
        """
        # Core state properties
        self._row_count: int = 0
        self._column_names: List[str] = []
        self._last_updated: float = time.time()
        self._column_stats: Dict[str, Dict[str, Any]] = {}
        self._hash_value: str = ""

        # Initialize state from data if provided
        if data is not None:
            self.update_from_data(data)

    def update_from_data(self, data: pd.DataFrame) -> None:
        """
        Update state from a DataFrame.

        Args:
            data: The DataFrame to update state from
        """
        self._row_count = len(data)
        self._column_names = list(data.columns)
        self._last_updated = time.time()

        # Calculate column statistics for change detection
        self._calculate_column_stats(data)

        # Calculate overall hash for quick equality checks
        self._hash_value = self._calculate_hash(data)

        logger.debug(
            f"DataState updated: {self._row_count} rows, {len(self._column_names)} columns"
        )

    def _calculate_column_stats(self, data: pd.DataFrame) -> None:
        """
        Calculate statistics for each column.

        Args:
            data: The DataFrame to calculate statistics from
        """
        self._column_stats = {}

        for column in data.columns:
            self._column_stats[column] = self._get_column_stats(data, column)

    def _get_column_stats(self, data: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Get statistics for a specific column.

        Args:
            data: The DataFrame containing the column
            column: The column name

        Returns:
            Dictionary of statistics for the column
        """
        stats = {}

        # Different stats depending on column type
        if pd.api.types.is_numeric_dtype(data[column]):
            # For numeric columns
            if not data.empty:
                stats["min"] = float(data[column].min())
                stats["max"] = float(data[column].max())
                stats["mean"] = float(data[column].mean())
                stats["sum"] = float(data[column].sum())
                stats["null_count"] = int(data[column].isna().sum())
            else:
                stats["empty"] = True
        else:
            # For string/categorical columns
            if not data.empty:
                value_counts = data[column].value_counts()
                stats["unique_count"] = int(len(value_counts))
                stats["null_count"] = int(data[column].isna().sum())

                if not value_counts.empty:
                    stats["most_common"] = str(value_counts.index[0])
                    stats["most_common_count"] = int(value_counts.iloc[0])
                else:
                    stats["most_common"] = None
                    stats["most_common_count"] = 0
            else:
                stats["empty"] = True

        return stats

    def _calculate_hash(self, data: pd.DataFrame) -> str:
        """
        Calculate hash for quick comparison.

        Args:
            data: The DataFrame to calculate hash from

        Returns:
            Hash string representing the data state
        """
        if data.empty:
            return hashlib.md5(f"empty:{list(data.columns)}".encode()).hexdigest()

        # Sample data for hashing (first, middle, last rows)
        sample_indices = [0]
        if len(data) > 1:
            sample_indices.append(len(data) - 1)
        if len(data) > 2:
            sample_indices.append(len(data) // 2)

        # Create hash data structure
        hash_data = {"row_count": len(data), "columns": list(data.columns), "samples": {}}

        # Add sample data
        for idx in sample_indices:
            row_data = {}
            for col in data.columns:
                val = data.iloc[idx][col]
                # Convert values to strings to ensure hashability
                row_data[col] = str(val)
            hash_data["samples"][str(idx)] = row_data

        # Convert to JSON and hash
        json_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()

    def equals(self, other: "DataState") -> bool:
        """
        Check if this state equals another state.

        Args:
            other: The other DataState to compare with

        Returns:
            True if states are equal, False otherwise
        """
        # Fast path: hash comparison
        return self._hash_value == other._hash_value

    def get_changes(self, other: "DataState") -> Dict[str, Any]:
        """
        Get detailed changes between this state and another state.

        Args:
            other: The other DataState to compare with

        Returns:
            Dictionary with change information
        """
        changes = {
            "row_count_changed": self._row_count != other._row_count,
            "columns_changed": set(self._column_names) != set(other._column_names),
            "column_changes": {},
            "has_changes": False,
            "new_columns": list(set(self._column_names) - set(other._column_names)),
            "removed_columns": list(set(other._column_names) - set(self._column_names)),
        }

        # Check for changes in each column that exists in both states
        common_columns = set(self._column_names) & set(other._column_names)
        for column in common_columns:
            column_changed = self._column_stats.get(column, {}) != other._column_stats.get(
                column, {}
            )
            changes["column_changes"][column] = column_changed
            if column_changed:
                changes["has_changes"] = True

        # Set overall change flag
        if changes["row_count_changed"] or changes["columns_changed"]:
            changes["has_changes"] = True

        return changes

    @property
    def row_count(self) -> int:
        """
        Get the number of rows in the state.

        Returns:
            The number of rows
        """
        return self._row_count

    @property
    def column_names(self) -> List[str]:
        """
        Get the column names in the state.

        Returns:
            List of column names
        """
        return self._column_names.copy()

    @property
    def last_updated(self) -> float:
        """
        Get the timestamp of the last update.

        Returns:
            Timestamp (seconds since epoch)
        """
        return self._last_updated

    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """
        Get statistics for a specific column.

        Args:
            column: The column name

        Returns:
            Dictionary of statistics or empty dict if column doesn't exist
        """
        return self._column_stats.get(column, {}).copy()

    def __repr__(self) -> str:
        """
        Get string representation of the state.

        Returns:
            String representation
        """
        return (
            f"DataState(rows={self._row_count}, "
            f"columns={len(self._column_names)}, "
            f"hash={self._hash_value[:8]})"
        )
