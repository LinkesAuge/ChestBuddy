"""
ValidationService module.

This module provides the ValidationService class for validating chest data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import pandas as pd
import numpy as np

from chestbuddy.core.models.chest_data_model import ChestDataModel

# Set up logger
logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for validating chest data.

    The ValidationService is responsible for detecting and flagging issues
    in chest data, such as missing values, outliers, duplicates, and
    inconsistent data types.

    Implementation Notes:
        - Uses statistical methods for outlier detection
        - Provides customizable validation rules
        - Works with the ChestDataModel to update validation statuses
    """

    def __init__(self, data_model: ChestDataModel) -> None:
        """
        Initialize the ValidationService.

        Args:
            data_model: The ChestDataModel instance to validate.
        """
        self._data_model = data_model
        self._validation_rules = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize the default validation rules."""
        # Add default validation rules
        self.add_validation_rule("missing_values", self._check_missing_values)
        self.add_validation_rule("outliers", self._check_outliers)
        self.add_validation_rule("duplicates", self._check_duplicates)
        self.add_validation_rule("data_types", self._check_data_types)

    def add_validation_rule(self, rule_name: str, rule_function: callable) -> None:
        """
        Add a custom validation rule.

        Args:
            rule_name: The name of the rule.
            rule_function: The function that implements the rule.
        """
        self._validation_rules[rule_name] = rule_function

    def remove_validation_rule(self, rule_name: str) -> bool:
        """
        Remove a validation rule.

        Args:
            rule_name: The name of the rule to remove.

        Returns:
            True if the rule was removed, False if it didn't exist.
        """
        if rule_name in self._validation_rules:
            del self._validation_rules[rule_name]
            return True
        return False

    def validate_data(
        self, specific_rules: Optional[List[str]] = None
    ) -> Dict[str, Dict[int, str]]:
        """
        Validate the data using the defined rules.

        Args:
            specific_rules: Optional list of specific rule names to run.
                            If None, all rules are run.

        Returns:
            A dictionary mapping rule names to dictionaries of row indices
            and error messages.
        """
        if self._data_model.is_empty:
            logger.warning("Cannot validate empty data.")
            return {}

        validation_results = {}

        # Determine which rules to run
        rules_to_run = specific_rules or list(self._validation_rules.keys())

        # Run each specified rule
        for rule_name in rules_to_run:
            if rule_name in self._validation_rules:
                try:
                    rule_function = self._validation_rules[rule_name]
                    result = rule_function()
                    if result:  # If there are validation issues
                        validation_results[rule_name] = result
                except Exception as e:
                    logger.error(f"Error running validation rule '{rule_name}': {e}")
            else:
                logger.warning(f"Validation rule '{rule_name}' not found.")

        # Update the validation status in the data model
        self._update_validation_status(validation_results)

        return validation_results

    def _update_validation_status(self, validation_results: Dict[str, Dict[int, str]]) -> None:
        """
        Update the validation status in the data model.

        Args:
            validation_results: The validation results to set.
        """
        # Reset validation status
        self._data_model.clear_validation_status()

        # Update with new validation results
        for rule_name, issues in validation_results.items():
            for row_idx, message in issues.items():
                self._data_model.set_validation_status(row_idx, rule_name, message)

    def _check_missing_values(self) -> Dict[int, str]:
        """
        Check for missing values in the data.

        Returns:
            A dictionary mapping row indices to error messages.
        """
        issues = {}
        data = self._data_model.data

        # Check each row for missing values
        for idx, row in data.iterrows():
            missing_cols = row.index[row.isna()]
            if len(missing_cols) > 0:
                missing_str = ", ".join(missing_cols)
                issues[idx] = f"Missing values in columns: {missing_str}"

        return issues

    def _check_outliers(self) -> Dict[int, str]:
        """
        Check for outliers in numeric columns using Z-score method.

        Returns:
            A dictionary mapping row indices to error messages.
        """
        issues = {}
        data = self._data_model.data

        # Get numeric columns
        numeric_cols = data.select_dtypes(include=["number"]).columns

        # Check each numeric column for outliers
        for col in numeric_cols:
            # Skip columns with too few values
            if data[col].count() < 4:
                continue

            # Calculate Z-scores
            mean = data[col].mean()
            std = data[col].std()

            if std == 0:  # Skip columns with zero standard deviation
                continue

            z_scores = (data[col] - mean) / std

            # Flag rows with absolute Z-score > 3 (common threshold for outliers)
            outlier_rows = data.index[abs(z_scores) > 3]

            for idx in outlier_rows:
                if pd.notna(data.loc[idx, col]):  # Only flag non-NA values
                    value = data.loc[idx, col]
                    if idx in issues:
                        issues[idx] += f", Outlier in {col}: {value}"
                    else:
                        issues[idx] = f"Outlier in {col}: {value}"

        return issues

    def _check_duplicates(self) -> Dict[int, str]:
        """
        Check for duplicate rows in the data.

        Returns:
            A dictionary mapping row indices to error messages.
        """
        issues = {}
        data = self._data_model.data

        # Find duplicate rows
        duplicated = data.duplicated(keep="first")
        duplicate_indices = data.index[duplicated]

        # Flag duplicate rows
        for idx in duplicate_indices:
            issues[idx] = "Duplicate row"

        return issues

    def _check_data_types(self) -> Dict[int, str]:
        """
        Check for inconsistent data types within columns.

        Returns:
            A dictionary mapping row indices to error messages.
        """
        issues = {}
        data = self._data_model.data

        # Check each column for inconsistent data types
        for col in data.columns:
            # Skip columns that are entirely NaN
            if data[col].isna().all():
                continue

            # Get the majority data type (excluding NaN)
            non_null_values = data[col].dropna()
            if len(non_null_values) == 0:
                continue

            # Try to infer the dominant data type
            try:
                # Check if column can be converted to numeric
                numeric_col = pd.to_numeric(non_null_values, errors="coerce")
                if numeric_col.notna().all():
                    # All values can be converted to numeric, so check each row
                    for idx, val in data[col].items():
                        if pd.notna(val):
                            try:
                                float(val)  # Test if convertible to float
                            except (ValueError, TypeError):
                                issues[idx] = (
                                    f"Type mismatch in {col}: expected numeric, got {type(val).__name__}"
                                )
                    continue

                # If not all numeric, check for datetime
                datetime_col = pd.to_datetime(non_null_values, errors="coerce")
                if datetime_col.notna().all():
                    # All values can be converted to datetime, so check each row
                    for idx, val in data[col].items():
                        if pd.notna(val):
                            try:
                                pd.to_datetime(val)  # Test if convertible to datetime
                            except (ValueError, TypeError):
                                issues[idx] = (
                                    f"Type mismatch in {col}: expected datetime, got {type(val).__name__}"
                                )
                    continue

                # If neither numeric nor datetime, assume string and no type inconsistency
            except Exception as e:
                logger.debug(f"Error in data type check for column {col}: {e}")

        return issues

    def get_validation_summary(self) -> Dict[str, int]:
        """
        Get a summary of validation issues.

        Returns:
            A dictionary mapping rule names to the count of issues found.
        """
        summary = {}

        # Get the validation status from the data model
        validation_status = self._data_model.get_all_validation_status()

        # Count issues by rule name
        for rule_name in self._validation_rules.keys():
            count = sum(1 for status in validation_status.values() if rule_name in status)
            summary[rule_name] = count

        return summary

    def export_validation_report(self, file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """
        Export a validation report to a CSV file.

        Args:
            file_path: The path to save the report to.

        Returns:
            A tuple containing:
                - True if the operation was successful, False otherwise.
                - An error message, or None if the operation was successful.
        """
        try:
            path = Path(file_path)

            # Get the validation status
            validation_status = self._data_model.get_all_validation_status()

            # Create a DataFrame for the report
            data = self._data_model.data.copy()

            # Add validation issues as a column
            data["validation_issues"] = data.index.map(
                lambda idx: "; ".join(
                    [f"{rule}: {msg}" for rule, msg in validation_status.get(idx, {}).items()]
                )
                if idx in validation_status
                else ""
            )

            # Write to CSV
            data.to_csv(path, index=False)

            return True, None

        except Exception as e:
            logger.error(f"Error exporting validation report: {e}")
            return False, f"Error exporting validation report. Error: {e}"
