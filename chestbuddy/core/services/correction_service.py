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

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.validation_enums import ValidationStatus


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

    def __init__(self, rule_manager, data_model, validation_service, case_sensitive=True):
        """
        Initialize the CorrectionService.

        Args:
            rule_manager (CorrectionRuleManager): Manager for correction rules
            data_model: Data model containing the data to be corrected
            validation_service: Service for validating data cells
            case_sensitive (bool): Whether to apply case-sensitive matching
        """
        self._rule_manager = rule_manager
        self._data_model = data_model
        self._validation_service = validation_service
        self._case_sensitive = case_sensitive
        self._correction_history = []

        # For mapping column names to rule categories
        self._category_mapping = {"Player": "player", "ChestType": "chest_type", "Source": "source"}

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
        data = self._data_model.get_data()
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

        # Second pass: Apply category-specific rules (which will override general rules)
        for rule in prioritized_rules:
            if rule.status != "enabled" or rule.category == "general":
                continue

            # Apply the rule to the already partially corrected data
            corrections = self._apply_rule_to_data(corrected_data, rule, only_invalid)

            # Apply these corrections
            for row, col, _, new_value in corrections:
                column_name = corrected_data.columns[col]
                corrected_data.at[row, column_name] = new_value
                corrected_rows.add(row)
                corrected_cells.add((row, col))
                total_corrections += 1

        # Update the data model with corrected data
        if total_corrections > 0:
            self._data_model.update_data(corrected_data)

        # Prepare statistics
        stats = {
            "total_corrections": total_corrections,
            "corrected_rows": len(corrected_rows),
            "corrected_cells": len(corrected_cells),
        }

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
        data = self._data_model.get_data()
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

    def _apply_rule_to_data(
        self, data: pd.DataFrame, rule: CorrectionRule, only_invalid: bool
    ) -> List[Tuple[int, int, Any, Any]]:
        """
        Apply a rule to the data and return a list of corrections.

        Args:
            data (pd.DataFrame): Data to apply corrections to
            rule (CorrectionRule): Rule to apply
            only_invalid (bool): If True, only apply to invalid cells

        Returns:
            List[Tuple[int, int, Any, Any]]: List of corrections as (row, col, old_value, new_value)
        """
        corrections = []

        # Determine which columns to check based on rule category
        columns_to_check = []
        if rule.category == "general":
            # General rules apply to all columns
            columns_to_check = list(range(len(data.columns)))
        else:
            # Column-specific rules apply only to their respective column
            for i, col_name in enumerate(data.columns):
                # Map column names to categories
                category_name = self._get_category_for_column(col_name)
                if rule.category == category_name:
                    columns_to_check.append(i)

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
                        if cell_status != ValidationStatus.INVALID:
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

    def _get_category_for_column(self, column_name: str) -> str:
        """
        Get the rule category corresponding to a column name.

        Args:
            column_name (str): The column name

        Returns:
            str: The corresponding rule category
        """
        return self._category_mapping.get(column_name, column_name.lower())

    def get_cells_with_available_corrections(self) -> List[Tuple[int, int]]:
        """
        Get a list of cells that have available corrections.

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples for cells with corrections
        """
        data = self._data_model.get_data()
        if data is None or data.empty:
            return []

        # Get all enabled rules
        rules = [r for r in self._rule_manager.get_rules() if r.status == "enabled"]

        # If no rules, no corrections available
        if not rules:
            return []

        # Track cells with available corrections
        cells_with_corrections = set()

        # Process each rule
        for rule in rules:
            # Apply the rule to get potential corrections (but don't actually apply them)
            corrections = self._apply_rule_to_data(data, rule, False)

            # Add the affected cells to our set
            for row, col, _, _ in corrections:
                cells_with_corrections.add((row, col))

        return list(cells_with_corrections)

    def get_correction_preview(self, rule: CorrectionRule) -> List[Tuple[int, int, Any, Any]]:
        """
        Get a preview of the corrections that would be applied by a rule.

        Args:
            rule (CorrectionRule): Rule to preview

        Returns:
            List[Tuple[int, int, Any, Any]]: List of (row, col, old_value, new_value) tuples
        """
        data = self._data_model.get_data()
        if data is None or data.empty:
            return []

        # Apply the rule to get potential corrections
        return self._apply_rule_to_data(data, rule, False)

    def create_rule_from_cell(
        self, row: int, col: int, to_value: Any, use_general_category: bool = False
    ) -> CorrectionRule:
        """
        Create a correction rule from a specific cell.

        Args:
            row (int): Row index of the cell
            col (int): Column index of the cell
            to_value (Any): Value to correct to
            use_general_category (bool): If True, create a general category rule

        Returns:
            CorrectionRule: Created rule
        """
        data = self._data_model.get_data()

        # Get column name and cell value
        col_name = self._data_model.get_column_name(col)
        cell_value = data.at[row, col_name]

        # Determine category
        if use_general_category:
            category = "general"
        else:
            category = self._get_category_for_column(col_name)

        # Create the rule
        return CorrectionRule(
            to_value=to_value, from_value=cell_value, category=category, status="enabled", order=0
        )

    def get_correction_history(self) -> List[Dict]:
        """
        Get the history of applied corrections.

        Returns:
            List[Dict]: List of history entries with rule and statistics
        """
        return deepcopy(self._correction_history)

    def clear_correction_history(self) -> None:
        """Clear the correction history."""
        self._correction_history = []
