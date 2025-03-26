"""
ValidationService module.

This module provides the ValidationService class for validating chest data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set

import pandas as pd
import numpy as np

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for validating chest data.

    The ValidationService is responsible for detecting and flagging issues
    in chest data, such as missing values, outliers, duplicates, and
    inconsistent data types. It also validates against reference lists for
    players, chest types, and sources.

    Implementation Notes:
        - Uses statistical methods for outlier detection
        - Provides customizable validation rules
        - Works with the ChestDataModel to update validation statuses
        - Uses ValidationListModel for reference list validation
    """

    # Define column names for validation
    PLAYER_COLUMN = "PLAYER"
    CHEST_COLUMN = "CHEST"
    SOURCE_COLUMN = "SOURCE"

    def __init__(
        self, data_model: ChestDataModel, config_manager: Optional[ConfigManager] = None
    ) -> None:
        """
        Initialize the ValidationService.

        Args:
            data_model: The ChestDataModel instance to validate.
            config_manager: Optional configuration manager for settings
        """
        self._data_model = data_model
        self._validation_rules = {}
        self._initialize_default_rules()

        # Initialize validation configuration
        self._case_sensitive = False
        self._validate_on_import = True

        # Load settings from configuration if provided
        if config_manager:
            self._case_sensitive = config_manager.get_bool("Validation", "case_sensitive", False)
            self._validate_on_import = config_manager.get_bool(
                "Validation", "validate_on_import", True
            )
            self._config_manager = config_manager
        else:
            self._config_manager = None

        # Initialize validation list models
        self._player_list_model = None
        self._chest_type_list_model = None
        self._source_list_model = None

        # Initialize validation lists
        self._initialize_validation_lists()

    def _initialize_default_rules(self) -> None:
        """Initialize the default validation rules."""
        # Add default validation rules
        self.add_validation_rule("missing_values", self._check_missing_values)
        self.add_validation_rule("outliers", self._check_outliers)
        self.add_validation_rule("duplicates", self._check_duplicates)
        self.add_validation_rule("data_types", self._check_data_types)

        # Add validation list rules
        self.add_validation_rule("player_validation", self._check_players)
        self.add_validation_rule("chest_type_validation", self._check_chest_types)
        self.add_validation_rule("source_validation", self._check_sources)

    def _check_missing_values(self, df: pd.DataFrame) -> Dict[int, str]:
        """
        Check for missing values in the dataframe.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        result = {}

        # Check each row for missing values
        for idx, row in df.iterrows():
            for column in df.columns:
                if pd.isna(row[column]):
                    result[idx] = result.get(idx, "") + f"Missing value in {column}. "

        return result

    def _check_outliers(self, df: pd.DataFrame) -> Dict[int, str]:
        """
        Check for outliers in numerical columns.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        result = {}

        # Find numerical columns
        numerical_columns = df.select_dtypes(include=["number"]).columns

        # Check each numerical column for outliers
        for column in numerical_columns:
            # Calculate Q1, Q3, and IQR
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            iqr = q3 - q1

            # Define outlier bounds
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Find outliers
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]

            # Add outliers to result
            for idx in outliers.index:
                value = df.loc[idx, column]
                result[idx] = result.get(idx, "") + f"Outlier in {column}: {value}. "

        return result

    def _check_duplicates(self, df: pd.DataFrame) -> Dict[int, str]:
        """
        Check for duplicate rows in the dataframe.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        result = {}

        # Find duplicate rows
        duplicates = df.duplicated(keep="first")

        # Add duplicates to result
        for idx in df[duplicates].index:
            result[idx] = "Duplicate row."

        return result

    def _check_data_types(self, df: pd.DataFrame) -> Dict[int, str]:
        """
        Check for inconsistent data types in the dataframe.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        result = {}

        # Define expected types for known columns
        expected_types = {"VALUE": "number", "DATE": "datetime", "SCORE": "number"}

        # Check each column for inconsistent types
        for column, expected_type in expected_types.items():
            if column in df.columns:
                # Check if column is numerical
                if expected_type == "number":
                    try:
                        # Try to convert to numeric, will produce NaN for non-numeric values
                        numeric_values = pd.to_numeric(df[column], errors="coerce")

                        # Find rows where conversion produced NaN but original wasn't NaN
                        for idx in df.index:
                            if pd.isna(numeric_values[idx]) and not pd.isna(df.loc[idx, column]):
                                result[idx] = (
                                    result.get(idx, "")
                                    + f"Non-numeric value in {column}: {df.loc[idx, column]}. "
                                )
                    except Exception as e:
                        logger.error(f"Error checking numeric type for column {column}: {e}")

                # Check if column is datetime
                elif expected_type == "datetime":
                    try:
                        # Try to convert to datetime, will produce NaN for invalid dates
                        datetime_values = pd.to_datetime(df[column], errors="coerce")

                        # Find rows where conversion produced NaN but original wasn't NaN
                        for idx in df.index:
                            if pd.isna(datetime_values[idx]) and not pd.isna(df.loc[idx, column]):
                                result[idx] = (
                                    result.get(idx, "")
                                    + f"Invalid date in {column}: {df.loc[idx, column]}. "
                                )
                    except Exception as e:
                        logger.error(f"Error checking datetime type for column {column}: {e}")

        return result

    def _initialize_validation_lists(self) -> None:
        """Initialize the validation list models."""
        try:
            # Define validation list file paths
            data_dir = Path(__file__).parents[3] / "data" / "validation"

            player_file = data_dir / "players.txt"
            chest_file = data_dir / "chest_types.txt"
            source_file = data_dir / "sources.txt"

            # Create validation list models
            self._player_list_model = ValidationListModel(player_file, self._case_sensitive)
            self._chest_type_list_model = ValidationListModel(chest_file, self._case_sensitive)
            self._source_list_model = ValidationListModel(source_file, self._case_sensitive)

            logger.info(
                f"Initialized validation lists: Players ({len(self._player_list_model.get_entries())} entries), "
                f"Chest Types ({len(self._chest_type_list_model.get_entries())} entries), "
                f"Sources ({len(self._source_list_model.get_entries())} entries)"
            )
        except Exception as e:
            logger.error(f"Error initializing validation lists: {e}")
            self._player_list_model = None
            self._chest_type_list_model = None
            self._source_list_model = None

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
        df = self._data_model.get_dataframe()

        # Determine which rules to run
        rules_to_run = specific_rules or list(self._validation_rules.keys())

        # Run each specified rule
        for rule_name in rules_to_run:
            if rule_name in self._validation_rules:
                try:
                    rule_function = self._validation_rules[rule_name]
                    # Check if the rule requires a dataframe parameter
                    if rule_name in ["missing_values", "outliers", "duplicates", "data_types"]:
                        result = rule_function(df)
                    else:
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

    def _check_players(self) -> Dict[int, str]:
        """
        Check that all player names are in the player validation list.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if not self._player_list_model:
            logger.warning("Player validation list not available.")
            return {}

        try:
            result = {}
            df = self._data_model.get_dataframe()

            if self.PLAYER_COLUMN not in df.columns:
                logger.warning(f"Player column '{self.PLAYER_COLUMN}' not found in dataframe.")
                return {}

            # Check each player name
            for idx, row in df.iterrows():
                player = row.get(self.PLAYER_COLUMN)
                if pd.isna(player) or player == "":
                    result[idx] = f"Missing player name."
                elif not self._player_list_model.contains(player):
                    result[idx] = f"Invalid player name: '{player}'."

            return result
        except Exception as e:
            logger.error(f"Error checking player names: {e}")
            return {}

    def _check_chest_types(self) -> Dict[int, str]:
        """
        Check that all chest types are in the chest type validation list.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if not self._chest_type_list_model:
            logger.warning("Chest type validation list not available.")
            return {}

        try:
            result = {}
            df = self._data_model.get_dataframe()

            if self.CHEST_COLUMN not in df.columns:
                logger.warning(f"Chest column '{self.CHEST_COLUMN}' not found in dataframe.")
                return {}

            # Check each chest type
            for idx, row in df.iterrows():
                chest = row.get(self.CHEST_COLUMN)
                if pd.isna(chest) or chest == "":
                    result[idx] = f"Missing chest type."
                elif not self._chest_type_list_model.contains(chest):
                    result[idx] = f"Invalid chest type: '{chest}'."

            return result
        except Exception as e:
            logger.error(f"Error checking chest types: {e}")
            return {}

    def _check_sources(self) -> Dict[int, str]:
        """
        Check that all sources are in the source validation list.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if not self._source_list_model:
            logger.warning("Source validation list not available.")
            return {}

        try:
            result = {}
            df = self._data_model.get_dataframe()

            if self.SOURCE_COLUMN not in df.columns:
                logger.warning(f"Source column '{self.SOURCE_COLUMN}' not found in dataframe.")
                return {}

            # Check each source
            for idx, row in df.iterrows():
                source = row.get(self.SOURCE_COLUMN)
                if pd.isna(source) or source == "":
                    result[idx] = f"Missing source."
                elif not self._source_list_model.contains(source):
                    result[idx] = f"Invalid source: '{source}'."

            return result
        except Exception as e:
            logger.error(f"Error checking sources: {e}")
            return {}

    def validate_field(self, field_type: str, value: str) -> bool:
        """
        Validate a single field against the appropriate validation list.

        Args:
            field_type (str): Type of field to validate ('player', 'chest', or 'source')
            value (str): Value to validate

        Returns:
            bool: Whether the field is valid
        """
        if not value:
            return False

        if field_type.lower() == "player":
            if not self._player_list_model:
                return False
            return self._player_list_model.contains(value)

        elif field_type.lower() == "chest":
            if not self._chest_type_list_model:
                return False
            return self._chest_type_list_model.contains(value)

        elif field_type.lower() == "source":
            if not self._source_list_model:
                return False
            return self._source_list_model.contains(value)

        else:
            logger.warning(f"Unknown field type: '{field_type}'")
            return False

    def add_to_validation_list(self, field_type: str, value: str) -> bool:
        """
        Add a value to the appropriate validation list.

        Args:
            field_type (str): Type of field ('player', 'chest', or 'source')
            value (str): Value to add

        Returns:
            bool: Whether the value was added successfully
        """
        if not value:
            return False

        if field_type.lower() == "player":
            if not self._player_list_model:
                return False
            return self._player_list_model.add_entry(value)

        elif field_type.lower() == "chest":
            if not self._chest_type_list_model:
                return False
            return self._chest_type_list_model.add_entry(value)

        elif field_type.lower() == "source":
            if not self._source_list_model:
                return False
            return self._source_list_model.add_entry(value)

        else:
            logger.warning(f"Unknown field type: '{field_type}'")
            return False

    def set_case_sensitive(self, case_sensitive: bool) -> None:
        """
        Set whether validation should be case-sensitive.

        Args:
            case_sensitive (bool): Whether validation should be case-sensitive
        """
        if self._case_sensitive != case_sensitive:
            self._case_sensitive = case_sensitive

            # Update validation list models
            if self._player_list_model:
                self._player_list_model.set_case_sensitive(case_sensitive)

            if self._chest_type_list_model:
                self._chest_type_list_model.set_case_sensitive(case_sensitive)

            if self._source_list_model:
                self._source_list_model.set_case_sensitive(case_sensitive)

            # Save to config if available
            if self._config_manager:
                self._config_manager.set("Validation", "case_sensitive", str(case_sensitive))
                self._config_manager.save()

            logger.info(f"Set case sensitivity to: {case_sensitive}")

    def is_case_sensitive(self) -> bool:
        """
        Get whether validation is case-sensitive.

        Returns:
            bool: Whether validation is case-sensitive
        """
        return self._case_sensitive

    def set_validate_on_import(self, validate_on_import: bool) -> None:
        """
        Set whether validation should be performed on import.

        Args:
            validate_on_import (bool): Whether validation should be performed on import
        """
        if self._validate_on_import != validate_on_import:
            self._validate_on_import = validate_on_import

            # Save to config if available
            if self._config_manager:
                self._config_manager.set(
                    "Validation", "validate_on_import", str(validate_on_import)
                )
                self._config_manager.save()

            logger.info(f"Set validate on import to: {validate_on_import}")

    def get_validate_on_import(self) -> bool:
        """
        Get whether validation should be performed on import.

        Returns:
            bool: Whether validation should be performed on import
        """
        return self._validate_on_import

    def get_player_list_model(self) -> ValidationListModel:
        """
        Get the player list model.

        Returns:
            ValidationListModel: The player list model
        """
        return self._player_list_model

    def get_chest_type_list_model(self) -> ValidationListModel:
        """
        Get the chest type list model.

        Returns:
            ValidationListModel: The chest type list model
        """
        return self._chest_type_list_model

    def get_source_list_model(self) -> ValidationListModel:
        """
        Get the source list model.

        Returns:
            ValidationListModel: The source list model
        """
        return self._source_list_model

    def get_validation_preferences(self) -> Dict[str, bool]:
        """
        Get the current validation preferences.

        Returns:
            Dict[str, bool]: Dictionary of validation preferences
        """
        return {
            "case_sensitive": self._case_sensitive,
            "validate_on_import": self._validate_on_import,
        }

    def set_validation_preferences(self, preferences: Dict[str, bool]) -> None:
        """
        Set multiple validation preferences at once.

        Args:
            preferences (Dict[str, bool]): Dictionary of validation preferences
        """
        # Update case sensitivity
        if "case_sensitive" in preferences:
            self.set_case_sensitive(preferences["case_sensitive"])

        # Update validate on import
        if "validate_on_import" in preferences:
            self.set_validate_on_import(preferences["validate_on_import"])

        logger.info(f"Updated validation preferences: {preferences}")

    def _update_validation_status(self, validation_results: Dict[str, Dict[int, str]]) -> None:
        """
        Update the validation status in the data model.

        Args:
            validation_results (Dict[str, Dict[int, str]]): Validation results
        """
        # TODO: Implement method to update validation status in data model
        # This method should be implemented based on how validation status is tracked
        pass

    def get_validation_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the validation status.

        Returns:
            Dict[str, int]: Dictionary with validation statistics
        """
        try:
            if self._data_model.is_empty:
                return {"total": 0, "valid": 0, "invalid": 0, "missing": 0}

            stats = {"total": 0, "valid": 0, "invalid": 0, "missing": 0}

            df = self._data_model.get_dataframe()

            # Count total rows
            stats["total"] = len(df)

            # Count valid, invalid, and missing values for each validation field
            for field, column in [
                ("player", self.PLAYER_COLUMN),
                ("chest_type", self.CHEST_COLUMN),
                ("source", self.SOURCE_COLUMN),
            ]:
                if column not in df.columns:
                    continue

                # Count missing values
                missing_count = df[column].isna().sum() + (df[column] == "").sum()
                stats[f"{field}_missing"] = int(missing_count)
                stats["missing"] += int(missing_count)

                # Count valid values
                valid_count = 0
                invalid_count = 0

                model = self._get_validation_list_model(field)
                if model:
                    # Check each non-empty value
                    non_empty_values = df[df[column].notna() & (df[column] != "")][column]
                    for value in non_empty_values:
                        if model.contains(value):
                            valid_count += 1
                        else:
                            invalid_count += 1

                stats[f"{field}_valid"] = valid_count
                stats[f"{field}_invalid"] = invalid_count
                stats["valid"] += valid_count
                stats["invalid"] += invalid_count

            return stats
        except Exception as e:
            logger.error(f"Error getting validation statistics: {e}")
            return {"total": 0, "valid": 0, "invalid": 0, "missing": 0}

    def _get_validation_list_model(self, list_type: str) -> Optional[ValidationListModel]:
        """
        Get the validation list model for the specified list type.

        Args:
            list_type (str): The type of validation list ('player', 'chest_type', 'source')

        Returns:
            Optional[ValidationListModel]: The validation list model, or None if not found
        """
        if list_type == "player":
            return self._player_list_model
        elif list_type == "chest_type":
            return self._chest_type_list_model
        elif list_type == "source":
            return self._source_list_model
        else:
            logger.warning(f"Unknown validation list type: {list_type}")
            return None

    def get_validation_summary(self) -> Dict[str, int]:
        """
        Get a summary of validation issues.

        Returns:
            A dictionary mapping rule names to the count of issues found.
        """
        summary = {}

        # Get the validation status from the data model
        validation_status = self._data_model.get_validation_status()

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
            validation_status = self._data_model.get_validation_status()

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
