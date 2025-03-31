"""
CorrectionService for applying correction rules to data.

This service applies correction rules to data using a two-pass algorithm:
1. First pass applies general category rules to all columns
2. Second pass applies column-specific rules

The service also supports selective correction of only invalid cells.
"""

from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from copy import deepcopy
from datetime import datetime
import logging

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.utils.config import ConfigManager

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionService:
    """
    Service for applying correction rules to data.

    The service applies rules using a two-pass algorithm, first applying general rules
    and then column-specific rules. It can selectively apply corrections to only
    invalid cells or all matching cells.

    Attributes:
        _rule_manager (CorrectionRuleManager): Manager for correction rules
        _data_model: Data model containing the data to be corrected
        _validation_service: Service for validating data cells
        _case_sensitive (bool): Whether to apply case-sensitive matching
        _correction_history (List[Dict]): History of applied corrections
    """

    def __init__(self, data_model: ChestDataModel, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the CorrectionService.

        Args:
            data_model: Data model containing the data to be corrected
            config_manager: Optional configuration manager for settings
        """
        self._data_model = data_model
        self._config_manager = config_manager
        self._rule_manager = CorrectionRuleManager(config_manager)
        self._validation_service = None  # Will be set separately
        self._case_sensitive = False
        self._correction_history = []

        # Map column names to categories
        self._category_mapping = {
            "PLAYER": "player",
            "CHEST": "chest",
            "SOURCE": "source",
            "SCORE": "score",
            "DATE": "date",
            "CLAN": "clan",
        }

        # Load settings from configuration if provided
        if config_manager:
            self._case_sensitive = config_manager.get_bool("Corrections", "case_sensitive", False)
            logger.info(f"Loaded correction case_sensitive setting: {self._case_sensitive}")

    def apply_corrections(self, only_invalid: bool = False) -> Dict[str, int]:
        """
        Apply all enabled correction rules to the data.

        Uses a two-pass algorithm:
        1. First pass applies general category rules to all columns
        2. Second pass applies column-specific rules to their respective columns

        Args:
            only_invalid (bool): If True, only apply corrections to cells marked as invalid

        Returns:
            Dict[str, int]: Statistics about the corrections applied
        """
        data = self._data_model.data
        if data is None or data.empty:
            return {
                "total_corrections": 0,
                "corrected_rows": 0,
                "corrected_cells": 0,
            }

        # Make a copy of the data to apply corrections
        corrected_data = data.copy()

        # Get all enabled rules, prioritized (general rules first, then column-specific)
        prioritized_rules = self._rule_manager.get_prioritized_rules()

        # First get all rules that match
        all_potential_corrections = []

        # First pass: Plan all general rule corrections
        general_corrections = []
        for rule in prioritized_rules:
            if rule.status != "enabled":
                continue

            if rule.category == "general":
                corrections = self._apply_rule_to_data(corrected_data, rule, only_invalid)
                general_corrections.extend(corrections)

        # Apply general corrections first
        # Track statistics
        total_corrections = 0
        corrected_rows = set()
        corrected_cells = set()

        # Apply general corrections
        for row, col, _, new_value in general_corrections:
            column_name = corrected_data.columns[col]
            corrected_data.at[row, column_name] = new_value
            corrected_rows.add(row)
            corrected_cells.add((row, col))
            total_corrections += 1

        # Second pass: Apply category-specific rules
        for rule in prioritized_rules:
            if rule.status != "enabled" or rule.category == "general":
                continue

            # Get corrections for this rule
            corrections = self._apply_rule_to_data(corrected_data, rule, only_invalid)

            # Apply corrections
            for row, col, _, new_value in corrections:
                column_name = corrected_data.columns[col]
                corrected_data.at[row, column_name] = new_value
                corrected_rows.add(row)
                corrected_cells.add((row, col))
                total_corrections += 1

        # Update the data model with corrected data
        if total_corrections > 0:
            self._data_model.update_data(corrected_data)

        # Record in history
        stats = {
            "total_corrections": total_corrections,
            "corrected_rows": len(corrected_rows),
            "corrected_cells": len(corrected_cells),
        }

        self._correction_history.append({"stats": stats})

        return stats

    def apply_single_rule(self, rule: CorrectionRule, only_invalid: bool = False) -> Dict[str, int]:
        """
        Apply a single correction rule to the data.

        Args:
            rule (CorrectionRule): Rule to apply
            only_invalid (bool): If True, only apply corrections to cells marked as invalid

        Returns:
            Dict[str, int]: Statistics about the corrections applied
        """
        data = self._data_model.data
        if data is None or data.empty:
            return {
                "total_corrections": 0,
                "corrected_rows": 0,
                "corrected_cells": 0,
            }

        # Make a copy of the data to apply corrections
        corrected_data = data.copy()

        # Apply the rule to get corrections
        corrections = self._apply_rule_to_data(corrected_data, rule, only_invalid)

        # Track statistics
        corrected_rows = set()
        corrected_cells = set()

        # Apply corrections to the dataframe
        for row, col, _, new_value in corrections:
            column_name = corrected_data.columns[col]
            corrected_data.at[row, column_name] = new_value
            corrected_rows.add(row)
            corrected_cells.add((row, col))

        # Update the data model with corrected data
        if corrections:
            self._data_model.update_data(corrected_data)

        # Record in history
        stats = {
            "total_corrections": len(corrections),
            "corrected_rows": len(corrected_rows),
            "corrected_cells": len(corrected_cells),
        }

        self._correction_history.append({"rule": rule, "stats": stats})

        return stats

    def apply_rule_to_data(
        self, rule: CorrectionRule, only_invalid: bool = False, selected_only: List[int] = None
    ) -> List[Tuple[int, int, Any, Any]]:
        """
        Apply a correction rule to the data.

        Args:
            rule: Rule to apply
            only_invalid: Whether to only apply to invalid cells
            selected_only: List of selected row indices to apply to (if None, apply to all rows)

        Returns:
            List of (row, col, old_value, new_value) tuples representing applied corrections
        """
        data = self._data_model.data
        if data is None or data.empty:
            return []

        if not rule:
            logger.warning("No rule specified for correction")
            return []

        # Get corrections
        corrections = self._apply_rule_to_data(data, rule, only_invalid)

        # Filter to selected rows if specified
        if selected_only is not None:
            selected_set = set(selected_only)
            corrections = [c for c in corrections if c[0] in selected_set]

        # Apply corrections
        if corrections:
            # Track history
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_entry = {
                "timestamp": now,
                "rule": {
                    "from_value": rule.from_value,
                    "to_value": rule.to_value,
                    "category": rule.category,
                },
                "corrections": [
                    {
                        "row": int(row),
                        "column": self._data_model.data.columns[col],
                        "old_value": str(old_val),
                        "new_value": str(new_val),
                    }
                    for row, col, old_val, new_val in corrections
                ],
            }
            self._correction_history.append(history_entry)

            # Apply corrections to data
            for row, col, _, new_val in corrections:
                col_name = data.columns[col]
                self._data_model.update_cell(row, col_name, new_val)

                # Update correction status
                self._update_correction_status(row, col, new_val)

            # Notify of the change
            self.corrections_applied.emit(len(corrections))
            logger.info(f"Applied {len(corrections)} corrections with rule: {rule}")

        return corrections

    def _apply_rule_to_data(
        self, data: pd.DataFrame, rule: CorrectionRule, only_invalid: bool = False
    ) -> List[Tuple[int, int, Any, Any]]:
        """
        Apply a rule to data without modifying it.

        Args:
            data (pd.DataFrame): Data to check against the rule
            rule (CorrectionRule): Rule to apply
            only_invalid (bool): Whether to only consider invalid cells

        Returns:
            List[Tuple[int, int, Any, Any]]: List of (row, col, old_value, new_value) tuples
        """
        corrections = []

        # First, determine which columns to check
        columns_to_check = []

        if rule.category == "general":
            # For general rules, check all columns
            columns_to_check = list(range(len(data.columns)))
        else:
            # For category-specific rules, check only matching columns
            for col_idx, col_name in enumerate(data.columns):
                # Get category for this column
                col_category = self._category_mapping.get(col_name, "").lower()
                if col_category == rule.category.lower():
                    columns_to_check.append(col_idx)

        # Check each cell in the applicable columns
        for col_idx in columns_to_check:
            for row_idx in range(len(data)):
                # Get column name for accessing the cell
                col_name = data.columns[col_idx]
                cell_value = data.at[row_idx, col_name]

                # Skip empty or NaN values
                if cell_value is None or (isinstance(cell_value, float) and np.isnan(cell_value)):
                    continue

                # Check if value matches the rule's from_value
                if self._values_match(str(cell_value), str(rule.from_value)):
                    # If only applying to invalid cells, check validation status
                    if only_invalid:
                        cell_status = self._validation_service.get_validation_status(
                            row_idx, col_idx
                        )
                        # Apply to invalid or correctable cells
                        if (
                            cell_status != ValidationStatus.INVALID
                            and cell_status != ValidationStatus.CORRECTABLE
                        ):
                            continue

                    # Add to corrections list
                    corrections.append((row_idx, col_idx, cell_value, rule.to_value))

        return corrections

    def _values_match(self, value1: str, value2: str) -> bool:
        """
        Check if two values match, respecting case sensitivity setting.

        Args:
            value1 (str): First value to compare
            value2 (str): Second value to compare

        Returns:
            bool: True if values match according to case sensitivity rules
        """
        if value1 is None or value2 is None:
            return value1 is None and value2 is None

        if self._case_sensitive:
            return value1 == value2
        else:
            return value1.lower() == value2.lower()

    def get_correction_history(self) -> List[Dict]:
        """
        Get the history of applied corrections.

        Returns:
            List[Dict]: History of corrections
        """
        return self._correction_history

    def set_case_sensitive(self, case_sensitive: bool) -> None:
        """
        Set whether correction matching should be case-sensitive.

        Args:
            case_sensitive (bool): Whether to use case-sensitive matching
        """
        self._case_sensitive = case_sensitive

    def get_case_sensitive(self) -> bool:
        """
        Get whether correction matching is case-sensitive.

        Returns:
            bool: Whether correction matching is case-sensitive
        """
        return self._case_sensitive

    def get_cells_with_available_corrections(self) -> List[Tuple[int, int]]:
        """
        Get list of cells that have available corrections.

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples for cells with corrections
        """
        data = self._data_model.data
        if data is None or data.empty:
            return []

        # Get all enabled rules
        rules = [r for r in self._rule_manager.get_rules() if r.status == "enabled"]
        if not rules:
            return []

        # Check all cells for potential corrections
        correctable_cells = set()

        for col_idx, col_name in enumerate(data.columns):
            col_category = self._category_mapping.get(col_name, "").lower()

            # Get rules applicable to this column
            applicable_rules = [
                r for r in rules if r.category.lower() == col_category or r.category == "general"
            ]

            # Skip if no applicable rules
            if not applicable_rules:
                continue

            # Check each cell in this column
            for row_idx in range(len(data)):
                cell_value = data.at[row_idx, col_name]

                # Skip empty or NaN values
                if cell_value is None or (isinstance(cell_value, float) and np.isnan(cell_value)):
                    continue

                # Check if any rule matches this cell
                for rule in applicable_rules:
                    if self._values_match(str(cell_value), str(rule.from_value)):
                        correctable_cells.add((row_idx, col_idx))
                        break

        return list(correctable_cells)

    def get_correction_preview(self, rule: CorrectionRule) -> List[Tuple[int, int, Any, Any]]:
        """
        Get preview of corrections that would be applied by a rule.

        Args:
            rule (CorrectionRule): Rule to preview

        Returns:
            List[Tuple[int, int, Any, Any]]: List of (row, col, old_value, new_value) tuples
        """
        data = self._data_model.data
        if data is None or data.empty:
            return []

        # Apply the rule (without modifying data)
        return self._apply_rule_to_data(data, rule, False)

    def create_correction_rule_from_cell(self, row: int, col: int) -> CorrectionRule:
        """
        Create a correction rule from a cell's value.

        Args:
            row (int): Row index
            col (int): Column index

        Returns:
            CorrectionRule: Created rule
        """
        data = self._data_model.data

        # Get column name and cell value
        col_name = data.columns[col]
        cell_value = data.at[row, col_name]

        # Determine category from column name
        category = self._category_mapping.get(col_name, "general").lower()

        # Create rule (from_value=current value, to_value needs to be set by user)
        rule = CorrectionRule(
            from_value=str(cell_value), to_value="", category=category, status="enabled"
        )

        return rule

    def clear_correction_history(self) -> None:
        """Clear the correction history."""
        self._correction_history = []
