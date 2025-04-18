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
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.core.services.correction_service import CorrectionService

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
        validation_complete (Signal): Emitted when validation status changes with the status DataFrame
        status_message_changed (Signal): Emitted when a general status update message changes

    Implementation Notes:
        - Uses statistical methods for outlier detection
        - Provides customizable validation rules
        - Works with the ChestDataModel to update validation statuses
        - Uses ValidationListModel for reference list validation
    """

    # Define signals
    validation_preferences_changed = Signal(dict)  # Dict of preferences
    validation_complete = Signal(
        object
    )  # Validation status DataFrame, Renamed from validation_changed
    status_message_changed = Signal(str)  # For general status updates

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
        self._auto_save = True
        self._config_manager = config_manager

        # Reference to correction service (will be set externally)
        self._correction_service = None

        # Load settings from configuration if provided
        if config_manager:
            # Load with detailed logging
            case_sensitive = config_manager.get_bool("Validation", "case_sensitive", False)
            validate_on_import = config_manager.get_bool("Validation", "validate_on_import", True)
            auto_save = config_manager.get_bool("Validation", "auto_save", True)

            logger.info(
                f"Loading validation settings from config - case_sensitive: {case_sensitive}, validate_on_import: {validate_on_import}, auto_save: {auto_save}"
            )

            self._case_sensitive = case_sensitive
            self._validate_on_import = validate_on_import
            self._auto_save = auto_save
        else:
            logger.warning("No config_manager provided, using default validation settings")

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

        logger.info(f"Starting validation. Running rules: {specific_rules or 'all'}")
        validation_results = {}
        rules_to_run = specific_rules or self._validation_rules.keys()
        current_df = self._data_model.data  # Get current data once

        for rule_name in rules_to_run:
            if rule_name in self._validation_rules:
                try:
                    logger.info(f"Running validation rule: {rule_name}")
                    # Pass current data to the rule function
                    rule_result = self._validation_rules[rule_name](current_df)
                    if rule_result:  # Only store if there are errors
                        validation_results[rule_name] = rule_result
                        logger.info(f"Rule {rule_name} found {len(rule_result)} issues.")
                    else:
                        logger.info(f"Rule {rule_name} found no issues.")
                except Exception as e:
                    logger.error(f"Error executing validation rule {rule_name}: {e}", exc_info=True)
            else:
                logger.warning(f"Validation rule {rule_name} not found.")

        logger.info("Finished running validation rules. Aggregated results:")
        for rule, errors in validation_results.items():
            logger.info(f"  {rule}: {len(errors)} issues")

        # Update the model's validation status
        self._update_validation_status(validation_results)

        return validation_results

    def _check_players(self, df=None) -> Dict[int, str]:
        """
        Check that player names are in the validation list.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        try:
            # Skip if validation list is not available
            if not self._player_list_model:
                logger.warning(
                    "Player validation list model is not available, skipping player validation"
                )
                return {}

            result = {}

            # Skip if column is not available
            if self.PLAYER_COLUMN not in df.columns:
                logger.warning(
                    f"{self.PLAYER_COLUMN} column not found in data, skipping player validation"
                )
                return {}

            # Count tracking variables
            total_players = 0
            invalid_players = 0
            valid_players = 0
            empty_players = 0

            # Debug: List valid players from model for reference
            player_list = self._player_list_model.get_entries()
            first_few_valid = player_list[:5] if player_list else []
            logger.debug(
                f"Player validation using {len(player_list)} entries. First few: {first_few_valid}"
            )

            # Check each player name against validation list
            for idx, player in df[self.PLAYER_COLUMN].items():
                total_players += 1

                # Skip empty values
                if pd.isna(player) or player == "":
                    empty_players += 1
                    continue

                # Check if player is in validation list
                if not self._player_list_model.contains(player):
                    result[idx] = f"Invalid player name: {player}"
                    invalid_players += 1

                    # Log detailed info for the first few invalid players
                    if invalid_players <= 5:
                        logger.debug(f"INVALID PLAYER at row {idx}: '{player}'")
                else:
                    valid_players += 1

            # Log summary of findings
            logger.debug(
                f"Player validation complete: {total_players} total, {valid_players} valid, {invalid_players} invalid, {empty_players} empty"
            )
            logger.debug(f"Found {len(result)} invalid player entries")

            return result
        except Exception as e:
            logger.error(f"Error checking players: {e}")
            return {}

    def _check_chest_types(self, df=None) -> Dict[int, str]:
        """
        Check that chest types are in the validation list.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        try:
            # Skip if validation list is not available
            if not self._chest_type_list_model:
                logger.warning(
                    "Chest type validation list model is not available, skipping chest type validation"
                )
                return {}

            result = {}

            # Skip if column is not available
            if self.CHEST_COLUMN not in df.columns:
                logger.warning(
                    f"{self.CHEST_COLUMN} column not found in data, skipping chest type validation"
                )
                return {}

            # Count tracking variables
            total_chests = 0
            invalid_chests = 0
            valid_chests = 0
            empty_chests = 0

            # Debug: List valid chest types from model for reference
            chest_list = self._chest_type_list_model.get_entries()
            first_few_valid = chest_list[:5] if chest_list else []
            logger.debug(
                f"Chest type validation using {len(chest_list)} entries. First few: {first_few_valid}"
            )

            # Check each chest type against validation list
            for idx, chest_type in df[self.CHEST_COLUMN].items():
                total_chests += 1

                # Skip empty values
                if pd.isna(chest_type) or chest_type == "":
                    empty_chests += 1
                    continue

                # Check if chest type is in validation list
                if not self._chest_type_list_model.contains(chest_type):
                    result[idx] = f"Invalid chest type: {chest_type}"
                    invalid_chests += 1

                    # Log detailed info for the first few invalid chest types
                    if invalid_chests <= 5:
                        logger.debug(f"INVALID CHEST TYPE at row {idx}: '{chest_type}'")
                else:
                    valid_chests += 1

            # Log summary of findings
            logger.debug(
                f"Chest type validation complete: {total_chests} total, {valid_chests} valid, {invalid_chests} invalid, {empty_chests} empty"
            )
            logger.debug(f"Found {len(result)} invalid chest type entries")

            return result
        except Exception as e:
            logger.error(f"Error checking chest types: {e}")
            return {}

    def _check_sources(self, df=None) -> Dict[int, str]:
        """
        Check that sources are in the validation list.

        Args:
            df (pd.DataFrame, optional): The DataFrame to check. If not provided, uses the model's data.

        Returns:
            Dict[int, str]: Dictionary mapping row indices to error messages.
        """
        if df is None:
            df = self._data_model.data

        try:
            # Skip if validation list is not available
            if not self._source_list_model:
                logger.warning(
                    "Source validation list model is not available, skipping source validation"
                )
                return {}

            result = {}

            # Skip if column is not available
            if self.SOURCE_COLUMN not in df.columns:
                logger.warning(
                    f"{self.SOURCE_COLUMN} column not found in data, skipping source validation"
                )
                return {}

            # Count tracking variables
            total_sources = 0
            invalid_sources = 0
            valid_sources = 0
            empty_sources = 0

            # Debug: List valid sources from model for reference
            source_list = self._source_list_model.get_entries()
            first_few_valid = source_list[:5] if source_list else []
            logger.debug(
                f"Source validation using {len(source_list)} entries. First few: {first_few_valid}"
            )

            # Check each source against validation list
            for idx, source in df[self.SOURCE_COLUMN].items():
                total_sources += 1

                # Skip empty values
                if pd.isna(source) or source == "":
                    empty_sources += 1
                    continue

                # Check if source is in validation list
                if not self._source_list_model.contains(source):
                    result[idx] = f"Invalid source: {source}"
                    invalid_sources += 1

                    # Log detailed info for the first few invalid sources
                    if invalid_sources <= 5:
                        logger.debug(f"INVALID SOURCE at row {idx}: '{source}'")
                else:
                    valid_sources += 1

            # Log summary of findings
            logger.debug(
                f"Source validation complete: {total_sources} total, {valid_sources} valid, {invalid_sources} invalid, {empty_sources} empty"
            )
            logger.debug(f"Found {len(result)} invalid source entries")

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

            # Emit signal with a dictionary containing the updated preference
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
        # Convert to proper boolean to avoid string confusion
        validate_on_import = bool(validate_on_import)

        # Log current and new values
        logger.debug(
            f"Setting validate_on_import from {self._validate_on_import} to {validate_on_import}"
        )

        # Only update if the value is changing
        if self._validate_on_import != validate_on_import:
            self._validate_on_import = validate_on_import

            # Save to config if available
            if self._config_manager:
                # Save as string representation of boolean, ensuring consistent format
                value_to_save = "True" if validate_on_import else "False"
                self._config_manager.set("Validation", "validate_on_import", value_to_save)
                self._config_manager.save()
                logger.info(f"Saved validate_on_import={value_to_save} to config")
            else:
                logger.warning(
                    "No config_manager available, validate_on_import setting not saved to config"
                )

            # Emit signal with the new value in a dictionary
            self.validation_preferences_changed.emit({"validate_on_import": validate_on_import})
            logger.info(
                f"Set validate_on_import to: {validate_on_import} and emitted change signal"
            )
        else:
            logger.debug(
                f"validate_on_import already set to {validate_on_import}, no change needed"
            )

    def get_validate_on_import(self) -> bool:
        """
        Get whether validation should be performed on import.

        Returns:
            bool: Whether validation should be performed on import
        """
        # Log current value when requested
        logger.debug(f"Getting validate_on_import: {self._validate_on_import}")

        # If config manager is available, refresh the value to ensure consistency
        # Skip this check if we're in testing mode (after _reset_for_testing was called)
        if self._config_manager and not getattr(self, "_in_testing_mode", False):
            config_value = self._config_manager.get_bool(
                "Validation", "validate_on_import", self._validate_on_import
            )
            if config_value != self._validate_on_import:
                logger.warning(
                    f"validate_on_import value inconsistent: memory={self._validate_on_import}, config={config_value}, using config value"
                )
                self._validate_on_import = config_value

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
            "auto_save": self._auto_save,
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

        # Update auto save
        if "auto_save" in preferences:
            self.set_auto_save(preferences["auto_save"])

        logger.info(f"Updated validation preferences: {preferences}")

        # Emit signal
        self.validation_preferences_changed.emit(preferences)

    def _update_validation_status(self, validation_results: Dict[str, Dict[int, str]]) -> None:
        """
        Update the validation status based on validation results.

        Args:
            validation_results: Dictionary of validation rule results
        """
        try:
            if self._data_model.data.empty:
                return

            # Get column names
            column_names = self._data_model.data.columns.tolist()

            # Initialize a validation status DataFrame
            status_df = self._init_validation_status_df()

            # Add column for overall row status
            status_df["_row_status"] = ValidationStatus.VALID

            # Debug: Count issues before processing
            total_issues = sum(len(rule_issues) for rule_issues in validation_results.values())
            logger.debug(
                f"*** VALIDATION: Processing {total_issues} total issues from {len(validation_results)} rules ***"
            )
            for rule_name, issues in validation_results.items():
                logger.debug(f"Rule '{rule_name}' has {len(issues)} issues")

            # Remember cells that we've explicitly marked as invalid
            explicitly_marked_cells = set()

            # Flag cells as invalid based on validation results
            for rule_name, issues in validation_results.items():
                for row_idx, message in issues.items():
                    if row_idx < 0:
                        logger.warning(
                            f"Skipping negative row index {row_idx} for rule {rule_name}"
                        )
                        continue

                    if "_row_" in message:
                        # Mark the entire row as invalid
                        status_df.at[row_idx, "_row_status"] = ValidationStatus.INVALID_ROW
                        # Update valid flags for all columns in this row
                        for col in column_names:
                            status_df.at[row_idx, f"{col}_valid"] = False
                            status_df.at[row_idx, f"{col}_status"] = ValidationStatus.INVALID_ROW
                            status_df.at[row_idx, f"{col}_message"] = message
                            explicitly_marked_cells.add((row_idx, col))
                    else:
                        # For each column mentioned in the error message, mark it as invalid
                        affected_column = None
                        for col in column_names:
                            if col in message:
                                affected_column = col
                                status_df.at[row_idx, f"{col}_valid"] = False
                                status_df.at[row_idx, f"{col}_status"] = ValidationStatus.INVALID
                                status_df.at[row_idx, f"{col}_message"] = message
                                explicitly_marked_cells.add((row_idx, col))

                                # Update row status to indicate at least one issue
                                if status_df.at[row_idx, "_row_status"] == ValidationStatus.VALID:
                                    status_df.at[row_idx, "_row_status"] = ValidationStatus.INVALID

                        # If we didn't find a column in the message but the message is about validation:
                        if affected_column is None and any(
                            vterm in message.lower()
                            for vterm in ["invalid", "not found", "missing"]
                        ):
                            # This is likely from a validation rule - find what column it's for
                            if "player" in rule_name.lower() or "player" in message.lower():
                                affected_column = "PLAYER"
                            elif "chest" in rule_name.lower() or "chest" in message.lower():
                                affected_column = "CHEST"
                            elif "source" in rule_name.lower() or "source" in message.lower():
                                affected_column = "SOURCE"

                            if affected_column:
                                logger.debug(
                                    f"Inferred affected column {affected_column} for rule {rule_name} with message: {message}"
                                )
                                status_df.at[row_idx, f"{affected_column}_valid"] = False
                                status_df.at[row_idx, f"{affected_column}_status"] = (
                                    ValidationStatus.INVALID
                                )
                                status_df.at[row_idx, f"{affected_column}_message"] = message
                                explicitly_marked_cells.add((row_idx, affected_column))

                                # Update row status to indicate at least one issue
                                if status_df.at[row_idx, "_row_status"] == ValidationStatus.VALID:
                                    status_df.at[row_idx, "_row_status"] = ValidationStatus.INVALID

            # Detect and mark correctable entries
            if self._correction_service is not None:
                status_df = self._mark_correctable_entries(status_df)

            # Debug: Count status types after processing
            status_counts = {
                "valid": 0,
                "invalid": 0,
                "correctable": 0,
                "invalid_row": 0,
                "not_validated": 0,
                "other": 0,
            }

            for col in status_df.columns:
                if col.endswith("_status"):
                    for status in status_df[col]:
                        if status == ValidationStatus.VALID:
                            status_counts["valid"] += 1
                        elif status == ValidationStatus.INVALID:
                            status_counts["invalid"] += 1
                        elif status == ValidationStatus.CORRECTABLE:
                            status_counts["correctable"] += 1
                        elif status == ValidationStatus.INVALID_ROW:
                            status_counts["invalid_row"] += 1
                        elif status == ValidationStatus.NOT_VALIDATED:
                            status_counts["not_validated"] += 1
                        else:
                            status_counts["other"] += 1

            logger.debug(f"*** VALIDATION: Final status count in status_df: {status_counts} ***")
            logger.debug(
                f"*** VALIDATION: Explicitly marked {len(explicitly_marked_cells)} cells as invalid/correctable ***"
            )

            # Log a sample of invalid or correctable rows
            for idx in range(min(5, len(status_df))):
                row_data = status_df.iloc[idx]
                row_status = row_data.get("_row_status", "Unknown")
                if row_status != ValidationStatus.VALID:
                    logger.debug(f"Sample invalid row {idx}: {row_status}")
                    for col in column_names:
                        status_col = f"{col}_status"
                        if (
                            status_col in row_data
                            and row_data[status_col] != ValidationStatus.VALID
                        ):
                            logger.debug(f"  - {col}: {row_data[status_col]}")

            # Update the validation status in the data model
            self._data_model.set_validation_status(status_df)

            # Emit the signal with the final status DataFrame
            logger.info(
                f"ValidationService emitting validation_complete with status_df:\n{status_df}"
            )
            try:
                self.validation_complete.emit(status_df)
                logger.info("ValidationService validation_complete signal emitted successfully.")
            except Exception as e:
                logger.error(f"Error emitting validation_complete signal: {e}")

        except Exception as e:
            logger.error(f"Error updating validation status: {e}")

    def _mark_correctable_entries(self, status_df: pd.DataFrame) -> pd.DataFrame:
        """
        Mark entries that have available corrections as correctable.

        Args:
            status_df: Validation status DataFrame

        Returns:
            Updated validation status DataFrame with correctable entries marked
        """
        if self._correction_service is None:
            logger.warning("No correction service available for marking correctable entries")
            return status_df

        # Get the data columns
        if self._data_model.data.empty:
            return status_df

        column_names = self._data_model.data.columns.tolist()

        # Get cells with available corrections
        correctable_cells = self.detect_correctable_entries()

        # Mark each correctable cell
        for row_idx, col_idx in correctable_cells:
            # Skip if row index or column index is out of bounds
            if row_idx >= len(status_df) or col_idx >= len(column_names):
                continue

            col_name = column_names[col_idx]

            # Mark as correctable if it has corrections available
            # For invalid cells, this indicates they can be fixed
            # For valid cells, this indicates optional improvement
            status_df.at[row_idx, f"{col_name}_status"] = ValidationStatus.CORRECTABLE

            # Add an indication that corrections are available
            current_message = status_df.at[row_idx, f"{col_name}_message"]
            if pd.notna(current_message) and current_message:
                status_df.at[row_idx, f"{col_name}_message"] = (
                    current_message + " (Corrections available)"
                )
            else:
                status_df.at[row_idx, f"{col_name}_message"] = "Corrections available"

        return status_df

    def _init_validation_status_df(self) -> pd.DataFrame:
        """
        Initialize a validation status DataFrame.

        Returns:
            DataFrame with validation status columns for each data column
        """
        data_df = self._data_model.data
        status_df = pd.DataFrame(index=data_df.index)

        # Add validation status columns for each data column, defaulting to NOT_VALIDATED
        for col in data_df.columns:
            status_df[f"{col}_valid"] = False  # Default to False (reflecting NOT_VALIDATED)
            status_df[f"{col}_status"] = ValidationStatus.NOT_VALIDATED
            status_df[f"{col}_message"] = ""

        return status_df

    def detect_correctable_entries(self) -> List[Tuple[int, int]]:
        """
        Detect entries that have available corrections.

        Uses the correction service to find cells with available corrections.

        Returns:
            List of (row, col) tuples for cells with available corrections
        """
        if self._correction_service is None:
            logger.warning("No correction service available for detecting correctable entries")
            return []

        return self._correction_service.get_cells_with_available_corrections()

    def update_correctable_status(self, correctable_cells: List[Tuple[int, int]]) -> None:
        """
        Update the validation status of cells with available corrections.

        Args:
            correctable_cells: List of (row, col) tuples for cells with available corrections
        """
        if not correctable_cells:
            logger.debug("No correctable cells to update")
            return

        # Get the current validation status
        status_df = self._data_model.get_validation_status()
        if status_df.empty:
            logger.warning("No validation status available to update")
            return

        # Update the validation status with correctable cells
        status_df = self._mark_correctable_entries(status_df)

        # Update the validation status in the data model
        self._data_model.set_validation_status(status_df)

        # Emit the validation changed signal
        self.validation_complete.emit(status_df)

        logger.info(f"Updated validation status with {len(correctable_cells)} correctable cells")

    def set_correction_service(self, correction_service: CorrectionService) -> None:
        """
        Set the correction service reference.

        Args:
            correction_service: The correction service to use for detecting correctable entries
        """
        self._correction_service = correction_service
        logger.info("Correction service reference set in ValidationService")

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
            Dictionary with counts of validation issues by type
        """
        try:
            validation_status = self._data_model.get_validation_status()
            if validation_status.empty:
                return {
                    "total": 0,
                    "valid": 0,
                    "invalid": 0,
                    "warning": 0,
                    "not_validated": 0,
                    "invalid_row": 0,
                    "correctable": 0,
                }

            # Initialize counters
            valid_count = 0
            invalid_count = 0
            warning_count = 0
            not_validated_count = 0
            invalid_row_count = 0
            correctable_count = 0

            # Count statuses
            for col in validation_status.columns:
                if col.endswith("_status"):
                    for status in validation_status[col]:
                        if status == ValidationStatus.VALID:
                            valid_count += 1
                        elif status == ValidationStatus.INVALID:
                            invalid_count += 1
                        elif status == ValidationStatus.WARNING:
                            warning_count += 1
                        elif status == ValidationStatus.NOT_VALIDATED:
                            not_validated_count += 1
                        elif status == ValidationStatus.INVALID_ROW:
                            invalid_row_count += 1
                        elif status == ValidationStatus.CORRECTABLE:
                            correctable_count += 1

            # Calculate total issues
            total_issues = invalid_count + warning_count + invalid_row_count + correctable_count

            return {
                "total": total_issues,
                "valid": valid_count,
                "invalid": invalid_count,
                "warning": warning_count,
                "not_validated": not_validated_count,
                "invalid_row": invalid_row_count,
                "correctable": correctable_count,
            }
        except Exception as e:
            logger.error(f"Error getting validation summary: {e}")
            return {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "warning": 0,
                "not_validated": 0,
                "invalid_row": 0,
                "correctable": 0,
            }

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
        """Reset the validation service for testing."""
        self._case_sensitive = False
        self._validate_on_import = True
        self._auto_save = True

        # Set a flag to indicate we're in testing mode
        self._in_testing_mode = True

        # Reset validation lists
        if self._player_list_model:
            self._player_list_model.reset()
        if self._chest_type_list_model:
            self._chest_type_list_model.reset()
        if self._source_list_model:
            self._source_list_model.reset()

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

    def set_auto_save(self, auto_save: bool) -> None:
        """
        Set whether validation lists should be automatically saved when modified.

        Args:
            auto_save (bool): Whether validation lists should be auto-saved
        """
        # Convert to proper boolean to avoid string confusion
        auto_save = bool(auto_save)

        # Log current and new values
        logger.debug(f"Setting auto_save from {self._auto_save} to {auto_save}")

        # Only update if the value is changing
        if self._auto_save != auto_save:
            self._auto_save = auto_save

            # Save to config if available
            if self._config_manager:
                # Save as string representation of boolean, ensuring consistent format
                value_to_save = "True" if auto_save else "False"
                self._config_manager.set("Validation", "auto_save", value_to_save)
                self._config_manager.save()
                logger.info(f"Saved auto_save={value_to_save} to config")
            else:
                logger.warning("No config_manager available, auto_save setting not saved to config")

            # Emit signal with the new value
            self.validation_preferences_changed.emit({"auto_save": auto_save})
            logger.info(f"Set auto_save to: {auto_save} and emitted change signal")
        else:
            logger.debug(f"auto_save already set to {auto_save}, no change needed")

    def get_auto_save(self) -> bool:
        """
        Get whether validation lists should be automatically saved when modified.

        Returns:
            bool: Whether validation lists should be auto-saved
        """
        # Log current value when requested
        logger.debug(f"Getting auto_save: {self._auto_save}")

        # If config manager is available, refresh the value to ensure consistency
        if self._config_manager:
            config_value = self._config_manager.get_bool("Validation", "auto_save", self._auto_save)
            if config_value != self._auto_save:
                logger.warning(
                    f"auto_save value inconsistent: memory={self._auto_save}, config={config_value}, using config value"
                )
                self._auto_save = config_value

        return self._auto_save

    def validate_single_entry(self, column_name: str, value: str) -> Tuple[ValidationStatus, str]:
        """
        Validate a single value against the appropriate validation list.

        Args:
            column_name: The name of the column (determines which list to use).
            value: The value to validate.

        Returns:
            A tuple containing the ValidationStatus and a message (empty if valid).
        """
        logger.debug(f"Validating single entry for column '{column_name}', value: '{value}'")
        list_model = self._get_validation_list_model(column_name)

        if list_model is None:
            logger.warning(f"No validation list model found for column: {column_name}")
            # If no list exists for the column, treat as valid or handle as per requirements
            return ValidationStatus.VALID, ""

        try:
            status, message = list_model.validate(value, column_name)
            logger.debug(f"Validation result: Status={status}, Message='{message}'")
            return status, message
        except Exception as e:
            logger.error(f"Error during single entry validation for column {column_name}: {e}")
            # Return INVALID status in case of error during validation
            return ValidationStatus.INVALID, f"Error during validation: {e}"

    def set_correction_service(self, correction_service: "CorrectionService") -> None:
        """Set the correction service instance."""
