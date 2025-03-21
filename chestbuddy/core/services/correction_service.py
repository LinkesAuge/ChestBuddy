"""
CorrectionService module.

This module provides the CorrectionService class for correcting issues in chest data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import pandas as pd
import numpy as np

from chestbuddy.core.models.chest_data_model import ChestDataModel

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionService:
    """
    Service for correcting issues in chest data.

    The CorrectionService is responsible for applying corrections to
    chest data based on validation results, providing automated and
    semi-automated correction strategies.

    Implementation Notes:
        - Provides methods for common corrections (missing values, outliers, etc.)
        - Tracks correction history for audit purposes
        - Works with the ChestDataModel to update data and correction statuses
    """

    def __init__(self, data_model: ChestDataModel) -> None:
        """
        Initialize the CorrectionService.

        Args:
            data_model: The ChestDataModel instance to apply corrections to.
        """
        self._data_model = data_model
        self._correction_strategies = {}
        self._correction_history = []
        self._initialize_default_strategies()

    def _initialize_default_strategies(self) -> None:
        """Initialize the default correction strategies."""
        # Add default correction strategies
        self.add_correction_strategy("fill_missing_mean", self._fill_missing_mean)
        self.add_correction_strategy("fill_missing_median", self._fill_missing_median)
        self.add_correction_strategy("fill_missing_mode", self._fill_missing_mode)
        self.add_correction_strategy("fill_missing_constant", self._fill_missing_constant)
        self.add_correction_strategy("remove_duplicates", self._remove_duplicates)
        self.add_correction_strategy("fix_outliers_mean", self._fix_outliers_mean)
        self.add_correction_strategy("fix_outliers_median", self._fix_outliers_median)
        self.add_correction_strategy("fix_outliers_winsorize", self._fix_outliers_winsorize)

    def add_correction_strategy(self, strategy_name: str, strategy_function: Callable) -> None:
        """
        Add a custom correction strategy.

        Args:
            strategy_name: The name of the strategy.
            strategy_function: The function that implements the strategy.
        """
        self._correction_strategies[strategy_name] = strategy_function

    def remove_correction_strategy(self, strategy_name: str) -> bool:
        """
        Remove a correction strategy.

        Args:
            strategy_name: The name of the strategy to remove.

        Returns:
            True if the strategy was removed, False if it didn't exist.
        """
        if strategy_name in self._correction_strategies:
            del self._correction_strategies[strategy_name]
            return True
        return False

    def apply_correction(
        self,
        strategy_name: str,
        column: Optional[str] = None,
        rows: Optional[List[int]] = None,
        **strategy_args,
    ) -> Tuple[bool, Optional[str]]:
        """
        Apply a correction strategy to the data.

        Args:
            strategy_name: The name of the correction strategy to apply.
            column: Optional column name to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            **strategy_args: Additional arguments to pass to the strategy function.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        if self._data_model.is_empty:
            error_msg = "Cannot apply correction to empty data."
            logger.warning(error_msg)
            return False, error_msg

        if strategy_name not in self._correction_strategies:
            error_msg = f"Correction strategy '{strategy_name}' not found."
            logger.warning(error_msg)
            return False, error_msg

        try:
            # Get the strategy function
            strategy_function = self._correction_strategies[strategy_name]

            # Apply the correction
            result, error = strategy_function(column=column, rows=rows, **strategy_args)

            if result:
                # Record the correction in the history
                self._record_correction(strategy_name, column, rows, strategy_args)

                # Update the correction status in the data model
                self._update_correction_status(strategy_name, column, rows)

            return result, error

        except Exception as e:
            error_msg = f"Error applying correction strategy '{strategy_name}': {e}"
            logger.error(error_msg)
            return False, error_msg

    def _record_correction(
        self,
        strategy_name: str,
        column: Optional[str],
        rows: Optional[List[int]],
        strategy_args: Dict[str, Any],
    ) -> None:
        """
        Record a correction in the history.

        Args:
            strategy_name: The name of the correction strategy.
            column: The column the correction was applied to, or None if all columns.
            rows: The row indices the correction was applied to, or None if all rows.
            strategy_args: Additional arguments passed to the strategy function.
        """
        correction_record = {
            "strategy": strategy_name,
            "column": column,
            "rows": rows,
            "args": strategy_args,
            "timestamp": pd.Timestamp.now(),
        }

        self._correction_history.append(correction_record)

    def _update_correction_status(
        self, strategy_name: str, column: Optional[str], rows: Optional[List[int]]
    ) -> None:
        """
        Update the correction status in the data model.

        Args:
            strategy_name: The name of the correction strategy.
            column: The column the correction was applied to, or None if all columns.
            rows: The row indices the correction was applied to, or None if all rows.
        """
        # Determine affected rows
        affected_rows = rows if rows is not None else self._data_model.data.index

        # Update correction status for each affected row
        for row_idx in affected_rows:
            status_msg = f"{strategy_name} applied"
            if column:
                status_msg += f" to column '{column}'"

            self._data_model.set_correction_status(row_idx, strategy_name, status_msg)

    def get_correction_history(self) -> List[Dict[str, Any]]:
        """
        Get the correction history.

        Returns:
            A list of correction records, each containing strategy, column,
            rows, args, and timestamp.
        """
        return self._correction_history

    def export_correction_report(self, file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """
        Export a correction report to a CSV file.

        Args:
            file_path: The path to save the report to.

        Returns:
            A tuple containing:
                - True if the operation was successful, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            path = Path(file_path)

            # Get the correction status
            correction_status = self._data_model.get_all_correction_status()

            # Create a DataFrame for the report
            data = self._data_model.data.copy()

            # Add correction history as a column
            data["correction_history"] = data.index.map(
                lambda idx: "; ".join(
                    [
                        f"{strategy}: {msg}"
                        for strategy, msg in correction_status.get(idx, {}).items()
                    ]
                )
                if idx in correction_status
                else ""
            )

            # Write to CSV
            data.to_csv(path, index=False)

            return True, None

        except Exception as e:
            logger.error(f"Error exporting correction report: {e}")
            return False, f"Error exporting correction report. Error: {e}"

    # ====== Correction Strategy Implementations ======

    def _fill_missing_mean(
        self, column: Optional[str] = None, rows: Optional[List[int]] = None, **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Fill missing values with the mean of the column.

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fill_missing_mean strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            # Calculate mean (only for numeric columns)
            if not pd.api.types.is_numeric_dtype(data[column]):
                error_msg = f"Column '{column}' is not numeric, cannot apply mean filling."
                logger.warning(error_msg)
                return False, error_msg

            mean_value = data[column].mean()

            # Determine which rows to update
            if rows is not None:
                update_mask = data.index.isin(rows) & data[column].isna()
            else:
                update_mask = data[column].isna()

            # Create updated data
            updated_data = data.copy()
            updated_data.loc[update_mask, column] = mean_value

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fill_missing_mean: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _fill_missing_median(
        self, column: Optional[str] = None, rows: Optional[List[int]] = None, **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Fill missing values with the median of the column.

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fill_missing_median strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            # Calculate median (only for numeric columns)
            if not pd.api.types.is_numeric_dtype(data[column]):
                error_msg = f"Column '{column}' is not numeric, cannot apply median filling."
                logger.warning(error_msg)
                return False, error_msg

            median_value = data[column].median()

            # Determine which rows to update
            if rows is not None:
                update_mask = data.index.isin(rows) & data[column].isna()
            else:
                update_mask = data[column].isna()

            # Create updated data
            updated_data = data.copy()
            updated_data.loc[update_mask, column] = median_value

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fill_missing_median: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _fill_missing_mode(
        self, column: Optional[str] = None, rows: Optional[List[int]] = None, **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Fill missing values with the mode (most frequent value) of the column.

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fill_missing_mode strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            # Calculate mode
            mode_result = data[column].mode()
            if len(mode_result) == 0:
                error_msg = f"No mode found for column '{column}'."
                logger.warning(error_msg)
                return False, error_msg

            mode_value = mode_result[0]  # Take the first mode if there are multiple

            # Determine which rows to update
            if rows is not None:
                update_mask = data.index.isin(rows) & data[column].isna()
            else:
                update_mask = data[column].isna()

            # Create updated data
            updated_data = data.copy()
            updated_data.loc[update_mask, column] = mode_value

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fill_missing_mode: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _fill_missing_constant(
        self,
        column: Optional[str] = None,
        rows: Optional[List[int]] = None,
        value: Any = None,
        **kwargs,
    ) -> Tuple[bool, Optional[str]]:
        """
        Fill missing values with a constant value.

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            value: The value to fill missing values with.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fill_missing_constant strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            if value is None:
                error_msg = "Value must be specified for fill_missing_constant strategy."
                logger.warning(error_msg)
                return False, error_msg

            # Determine which rows to update
            if rows is not None:
                update_mask = data.index.isin(rows) & data[column].isna()
            else:
                update_mask = data[column].isna()

            # Create updated data
            updated_data = data.copy()
            updated_data.loc[update_mask, column] = value

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fill_missing_constant: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _remove_duplicates(
        self, column: Optional[str] = None, rows: Optional[List[int]] = None, **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Remove duplicate rows from the data.

        Args:
            column: Optional column to consider when identifying duplicates.
            rows: Optional list of row indices to check for duplicates.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            # Determine which subset of columns to use for duplicate detection
            subset = [column] if column is not None else None

            # Create a new DataFrame with duplicates removed
            if rows is not None:
                # Filter to the specified rows
                filtered_data = data.loc[data.index.isin(rows)]
                # Get duplicate indices within the filtered data
                duplicated = filtered_data.duplicated(subset=subset, keep="first")
                duplicate_indices = filtered_data.index[duplicated]
                # Remove the duplicates
                updated_data = data.drop(duplicate_indices)
            else:
                # Get all duplicate indices
                duplicated = data.duplicated(subset=subset, keep="first")
                # Create new DataFrame without duplicates
                updated_data = data[~duplicated]

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying remove_duplicates: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _fix_outliers_mean(
        self,
        column: Optional[str] = None,
        rows: Optional[List[int]] = None,
        threshold: float = 3.0,
        **kwargs,
    ) -> Tuple[bool, Optional[str]]:
        """
        Replace outliers with the mean value.

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            threshold: Z-score threshold for identifying outliers (default: 3.0).
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fix_outliers_mean strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(data[column]):
                error_msg = f"Column '{column}' is not numeric, cannot apply outlier correction."
                logger.warning(error_msg)
                return False, error_msg

            # Calculate Z-scores
            mean = data[column].mean()
            std = data[column].std()

            if std == 0:
                return True, "No outliers found (standard deviation is zero)."

            z_scores = (data[column] - mean) / std

            # Identify outliers
            if rows is not None:
                # Only consider specified rows for outlier correction
                outlier_mask = data.index.isin(rows) & (abs(z_scores) > threshold)
            else:
                outlier_mask = abs(z_scores) > threshold

            if not any(outlier_mask):
                return True, "No outliers found within the specified threshold."

            # Create updated data
            updated_data = data.copy()
            updated_data.loc[outlier_mask, column] = mean

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fix_outliers_mean: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _fix_outliers_median(
        self,
        column: Optional[str] = None,
        rows: Optional[List[int]] = None,
        threshold: float = 3.0,
        **kwargs,
    ) -> Tuple[bool, Optional[str]]:
        """
        Replace outliers with the median value.

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            threshold: Z-score threshold for identifying outliers (default: 3.0).
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fix_outliers_median strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(data[column]):
                error_msg = f"Column '{column}' is not numeric, cannot apply outlier correction."
                logger.warning(error_msg)
                return False, error_msg

            # Calculate Z-scores
            mean = data[column].mean()
            std = data[column].std()
            median = data[column].median()

            if std == 0:
                return True, "No outliers found (standard deviation is zero)."

            z_scores = (data[column] - mean) / std

            # Identify outliers
            if rows is not None:
                # Only consider specified rows for outlier correction
                outlier_mask = data.index.isin(rows) & (abs(z_scores) > threshold)
            else:
                outlier_mask = abs(z_scores) > threshold

            if not any(outlier_mask):
                return True, "No outliers found within the specified threshold."

            # Create updated data
            updated_data = data.copy()
            updated_data.loc[outlier_mask, column] = median

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fix_outliers_median: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _fix_outliers_winsorize(
        self,
        column: Optional[str] = None,
        rows: Optional[List[int]] = None,
        threshold: float = 3.0,
        **kwargs,
    ) -> Tuple[bool, Optional[str]]:
        """
        Winsorize outliers (cap extreme values at a threshold).

        Args:
            column: The column to apply the correction to.
            rows: Optional list of row indices to apply the correction to.
            threshold: Z-score threshold for identifying outliers (default: 3.0).
            **kwargs: Additional arguments.

        Returns:
            A tuple containing:
                - True if the correction was applied successfully, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            data = self._data_model.data

            if column is None:
                error_msg = "Column must be specified for fix_outliers_winsorize strategy."
                logger.warning(error_msg)
                return False, error_msg

            if column not in data.columns:
                error_msg = f"Column '{column}' not found in the data."
                logger.warning(error_msg)
                return False, error_msg

            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(data[column]):
                error_msg = f"Column '{column}' is not numeric, cannot apply outlier correction."
                logger.warning(error_msg)
                return False, error_msg

            # Calculate Z-scores
            mean = data[column].mean()
            std = data[column].std()

            if std == 0:
                return True, "No outliers found (standard deviation is zero)."

            z_scores = (data[column] - mean) / std

            # Calculate winsorization bounds
            lower_bound = mean - threshold * std
            upper_bound = mean + threshold * std

            # Create updated data
            updated_data = data.copy()

            # Apply winsorization based on rows filter
            if rows is not None:
                # Only consider specified rows for outlier correction
                rows_mask = updated_data.index.isin(rows)
                # Apply lower bound to specified rows
                low_outliers = updated_data.loc[rows_mask, column] < lower_bound
                updated_data.loc[rows_mask & low_outliers, column] = lower_bound
                # Apply upper bound to specified rows
                high_outliers = updated_data.loc[rows_mask, column] > upper_bound
                updated_data.loc[rows_mask & high_outliers, column] = upper_bound
            else:
                # Apply lower bound to all rows
                updated_data.loc[updated_data[column] < lower_bound, column] = lower_bound
                # Apply upper bound to all rows
                updated_data.loc[updated_data[column] > upper_bound, column] = upper_bound

            # Update the data model
            self._data_model.update_data(updated_data)

            return True, None

        except Exception as e:
            error_msg = f"Error applying fix_outliers_winsorize: {e}"
            logger.error(error_msg)
            return False, error_msg
