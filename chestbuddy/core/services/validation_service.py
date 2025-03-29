"""
ValidationService module.

This module provides the ValidationService class for validating chest data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set

import pandas as pd
import numpy as np
from PySide6.QtCore import Signal, QObject

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class ValidationService(QObject):
    """
    Service for validating chest data.

    The ValidationService is responsible for detecting and flagging issues
    in chest data, such as missing values, outliers, duplicates, and
    inconsistent data types. It also validates against reference lists for
    players, chest types, and sources.

    Signals:
        validation_preferences_changed (Signal): Emitted when validation preferences change
        validation_changed (Signal): Emitted when validation status changes with the status DataFrame

    Implementation Notes:
        - Uses statistical methods for outlier detection
        - Provides customizable validation rules
        - Works with the ChestDataModel to update validation statuses
        - Uses ValidationListModel for reference list validation
    """

    # Define signals
    validation_preferences_changed = Signal(dict)  # Dict of preferences
    validation_changed = Signal(object)  # Validation status DataFrame

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
        super().__init__()
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

    def _check_missing_values(self, df=None) -> Dict[int, str]:
        """
        Check for missing values in the data.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        try:
            result = {}

            # Check each column
            for column in df.columns:
                # Skip columns that are not used for validation
                if self._should_skip_column(column):
                    continue

                # Check for missing values
                for idx, value in df[column].items():
                    if pd.isna(value) or value == "":
                        result[idx] = result.get(idx, "") + f"Missing value in column: {column}. "

            return result
        except Exception as e:
            logger.error(f"Error checking missing values: {e}")
            return {}

    def _should_skip_column(self, column: str) -> bool:
        """
        Check if a column should be skipped during validation.

        Args:
            column (str): Column name to check

        Returns:
            bool: True if column should be skipped, False otherwise
        """
        # Skip system or internal columns
        if column.startswith("_") or column.endswith("_valid") or column.endswith("_corrected"):
            return True

        return False

    def _check_outliers(self, df=None) -> Dict[int, str]:
        """
        Check for outliers in numerical columns.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        try:
            result = {}
            # Only check numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns

            for column in numeric_cols:
                # Skip columns that are not used for validation
                if self._should_skip_column(column):
                    continue

                # Calculate Q1, Q3, and IQR
                q1 = df[column].quantile(0.25)
                q3 = df[column].quantile(0.75)
                iqr = q3 - q1

                # Define outlier bounds
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                # Find outliers
                for idx, value in df[column].items():
                    if not pd.isna(value) and (value < lower_bound or value > upper_bound):
                        result[idx] = (
                            result.get(idx, "")
                            + f"Outlier detected in {column}: {value} (bounds: {lower_bound:.2f}-{upper_bound:.2f}). "
                        )

            return result
        except Exception as e:
            logger.error(f"Error checking outliers: {e}")
            return {}

    def _check_duplicates(self, df=None) -> Dict[int, str]:
        """
        Check for duplicate rows in the data.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        try:
            result = {}

            # Check for duplicate rows
            duplicates = df.duplicated(keep="first")
            duplicate_indices = duplicates[duplicates].index

            # Add error message for each duplicate row
            for idx in duplicate_indices:
                result[idx] = "Duplicate row detected."

            return result
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return {}

    def _check_data_types(self, df=None) -> Dict[int, str]:
        """
        Check that data types are correct.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        result = {}

        try:
            for column in df.columns:
                try:
                    # Skip columns that don't need type validation
                    if self._should_skip_column(column):
                        continue

                    # Apply specific type checks based on column name
                    if column == "DATE":
                        # Check date format
                        for idx, value in df[column].items():
                            if pd.isna(value) or value == "":
                                continue

                            try:
                                # Try to parse as date
                                pd.to_datetime(value)
                            except:
                                result[idx] = (
                                    result.get(idx, "")
                                    + f"Invalid date format in {column}: {value}. "
                                )

                    elif column == "SCORE":
                        # Check numeric values
                        for idx, value in df[column].items():
                            if pd.isna(value) or value == "":
                                continue

                            try:
                                # Try to convert to numeric
                                float(value)
                            except:
                                result[idx] = (
                                    result.get(idx, "")
                                    + f"Invalid numeric value in {column}: {value}. "
                                )

                except Exception as e:
                    logger.error(f"Error checking data type for column {column}: {e}")

            return result
        except Exception as e:
            logger.error(f"Error checking data types: {e}")
            return {}

    def _initialize_validation_lists(self) -> None:
        """Initialize the validation list models."""
        try:
            # Resolve paths for validation lists
            player_file = self._resolve_validation_path("player")
            chest_file = self._resolve_validation_path("chest_type")
            source_file = self._resolve_validation_path("source")

            # Ensure parent directories exist
            player_file.parent.mkdir(parents=True, exist_ok=True)
            chest_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.parent.mkdir(parents=True, exist_ok=True)

            # Create validation list models
            self._player_list_model = ValidationListModel(str(player_file), self._case_sensitive)
            self._chest_type_list_model = ValidationListModel(str(chest_file), self._case_sensitive)
            self._source_list_model = ValidationListModel(str(source_file), self._case_sensitive)

            logger.info(
                f"Initialized validation lists: Players ({len(self._player_list_model.get_entries())} entries), "
                f"Chest Types ({len(self._chest_type_list_model.get_entries())} entries), "
                f"Sources ({len(self._source_list_model.get_entries())} entries)"
            )
        except Exception as e:
            logger.error(f"Error initializing validation lists: {e}")
            # Create empty validation list models instead of setting to None
            try:
                fallback_dir = Path(__file__).parents[2] / "data" / "validation"
                fallback_dir.mkdir(parents=True, exist_ok=True)

                self._player_list_model = ValidationListModel(
                    str(fallback_dir / "players.txt"), self._case_sensitive
                )
                self._chest_type_list_model = ValidationListModel(
                    str(fallback_dir / "chest_types.txt"), self._case_sensitive
                )
                self._source_list_model = ValidationListModel(
                    str(fallback_dir / "sources.txt"), self._case_sensitive
                )

                logger.warning("Created empty validation list models with fallback paths")
            except Exception as inner_e:
                logger.critical(f"Failed to create fallback validation list models: {inner_e}")
                raise RuntimeError("Could not initialize validation system") from inner_e

    def _resolve_validation_path(self, list_type: str) -> Path:
        """
        Resolve the path to a validation list file.

        Args:
            list_type (str): The type of validation list ('player', 'chest_type', 'source')

        Returns:
            Path: The path to the validation list file
        """
        try:
            # Try to get path from config first
            if self._config_manager:
                validation_dir = self._config_manager.get("Validation", "validation_lists_dir")
                if validation_dir:
                    validation_path = Path(validation_dir)
                else:
                    # Fall back to default path if not configured
                    validation_path = Path(__file__).parents[2] / "data" / "validation"
                    logger.warning(
                        f"No validation_lists_dir configured, using default: {validation_path}"
                    )
            else:
                # Use default path if no config manager
                validation_path = Path(__file__).parents[2] / "data" / "validation"
                logger.warning(
                    f"No config manager available, using default path: {validation_path}"
                )

            # Create directory if it doesn't exist
            validation_path.mkdir(parents=True, exist_ok=True)

            # Return appropriate file path based on list type
            if list_type == "player":
                return validation_path / "players.txt"
            elif list_type == "chest_type":
                return validation_path / "chest_types.txt"
            elif list_type == "source":
                return validation_path / "sources.txt"

            logger.error(f"Unknown validation list type: {list_type}")
            # Return a default path even for unknown types to prevent None
            return validation_path / f"{list_type}.txt"

        except Exception as e:
            logger.error(f"Error resolving validation path for {list_type}: {e}")
            # Return a fallback path in case of errors
            fallback_path = Path(__file__).parents[2] / "data" / "validation" / f"{list_type}.txt"
            logger.warning(f"Using fallback path: {fallback_path}")
            return fallback_path

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
        df = self._data_model.data

        # Determine which rules to run
        rules_to_run = specific_rules or self._validation_rules.keys()

        # Run each validation rule
        for rule_name in rules_to_run:
            if rule_name in self._validation_rules:
                try:
                    # Special case for validation list rules that don't take the dataframe
                    if rule_name in [
                        "player_validation",
                        "chest_type_validation",
                        "source_validation",
                    ]:
                        results = self._validation_rules[rule_name]()
                    else:
                        results = self._validation_rules[rule_name](df)

                    if results:
                        validation_results[rule_name] = results
                except Exception as e:
                    logger.error(f"Error running validation rule {rule_name}: {e}")
                    validation_results[rule_name] = {-1: f"Error running validation rule: {str(e)}"}
            else:
                logger.warning(f"Validation rule {rule_name} not found.")

        # Update the validation status in the data model
        self._update_validation_status(validation_results)

        # Return all validation results
        return validation_results

    def _check_players(self) -> Dict[int, str]:
        """
        Check that player names are in the validation list.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        try:
            # Skip if validation list is not available
            if not self._player_list_model:
                return {}

            result = {}
            df = self._data_model.data

            # Skip if column is not available
            if self.PLAYER_COLUMN not in df.columns:
                return {}

            # Check each player name against validation list
            for idx, player in df[self.PLAYER_COLUMN].items():
                # Skip empty values
                if pd.isna(player) or player == "":
                    continue

                # Check if player is in validation list
                if not self._player_list_model.contains(player):
                    result[idx] = f"Invalid player name: {player}"

            return result
        except Exception as e:
            logger.error(f"Error checking player names: {e}")
            return {}

    def _check_chest_types(self) -> Dict[int, str]:
        """
        Check that chest types are in the validation list.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        try:
            # Skip if validation list is not available
            if not self._chest_type_list_model:
                return {}

            result = {}
            df = self._data_model.data

            # Skip if column is not available
            if self.CHEST_COLUMN not in df.columns:
                return {}

            # Check each chest type against validation list
            for idx, chest_type in df[self.CHEST_COLUMN].items():
                # Skip empty values
                if pd.isna(chest_type) or chest_type == "":
                    continue

                # Check if chest type is in validation list
                if not self._chest_type_list_model.contains(chest_type):
                    result[idx] = f"Invalid chest type: {chest_type}"

            return result
        except Exception as e:
            logger.error(f"Error checking chest types: {e}")
            return {}

    def _check_sources(self) -> Dict[int, str]:
        """
        Check that sources are in the validation list.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        try:
            # Skip if validation list is not available
            if not self._source_list_model:
                return {}

            result = {}
            df = self._data_model.data

            # Skip if column is not available
            if self.SOURCE_COLUMN not in df.columns:
                return {}

            # Check each source against validation list
            for idx, source in df[self.SOURCE_COLUMN].items():
                # Skip empty values
                if pd.isna(source) or source == "":
                    continue

                # Check if source is in validation list
                if not self._source_list_model.contains(source):
                    result[idx] = f"Invalid source: {source}"

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

            # Emit signal
            self.validation_preferences_changed.emit({"case_sensitive": case_sensitive})

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

            # Emit signal
            self.validation_preferences_changed.emit({"validate_on_import": validate_on_import})

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

        # Emit signal
        self.validation_preferences_changed.emit(preferences)

    def _update_validation_status(self, validation_results: Dict[str, Dict[int, str]]) -> None:
        """
        Update the validation status in the data model.

        Args:
            validation_results (Dict[str, Dict[int, str]]): Validation results
        """
        if not validation_results:
            logger.debug("No validation results to update")
            return

        # Get the current data from the model
        df = self._data_model.data

        # Create a DataFrame to store validation status
        # Initialize with default valid status (empty DataFrame)
        status_df = pd.DataFrame(index=df.index)

        # Process each validation rule's results
        for rule_name, rule_results in validation_results.items():
            # For each row with validation issues
            for row_idx, message in rule_results.items():
                # Skip any invalid indices
                if row_idx < 0 or row_idx >= len(df):
                    continue

                # Add the rule and message to the status DataFrame
                status_df.loc[row_idx, rule_name] = message

                # Mark columns as invalid based on rule type
                if rule_name == "player_validation":
                    status_df.loc[row_idx, f"{self.PLAYER_COLUMN}_valid"] = False
                elif rule_name == "chest_type_validation":
                    status_df.loc[row_idx, f"{self.CHEST_COLUMN}_valid"] = False
                elif rule_name == "source_validation":
                    status_df.loc[row_idx, f"{self.SOURCE_COLUMN}_valid"] = False
                elif rule_name == "missing_values":
                    # For missing values, check which columns are mentioned in the message
                    for col in df.columns:
                        if col in message:
                            status_df.loc[row_idx, f"{col}_valid"] = False

        # Set default values for columns not explicitly set
        for col in df.columns:
            col_status = f"{col}_valid"
            if col_status not in status_df.columns:
                status_df[col_status] = True

        # Update the validation status in the data model
        self._data_model.set_validation_status(status_df)
        logger.info(f"Updated validation status for {len(validation_results)} rules")

        # Emit signal
        self.validation_changed.emit(status_df)

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

            df = self._data_model.data

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

    def _reset_for_testing(self) -> None:
        """Reset service state for testing purposes."""
        # Reset validation list models if they exist
        if self._player_list_model:
            self._player_list_model.reset()
        if self._chest_type_list_model:
            self._chest_type_list_model.reset()
        if self._source_list_model:
            self._source_list_model.reset()

        # Clear any cached validation results
        if hasattr(self, "_validation_results"):
            self._validation_results = {}

    def get_validation_list_path(self, filename: str) -> Path:
        """
        Get the path to a validation list file.

        Args:
            filename (str): Name of the validation list file

        Returns:
            Path: Path to the validation list file
        """
        if self._config_manager:
            validation_dir = self._config_manager.get("Validation", "validation_lists_dir")
            if validation_dir:
                return Path(validation_dir) / filename

        # Fall back to default path if no config manager or no path configured
        default_path = Path(__file__).parents[2] / "data" / "validation" / filename
        logger.warning(f"Using default validation list path: {default_path}")
        return default_path
