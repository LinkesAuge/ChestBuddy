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
from PySide6.QtCore import Signal, QObject

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager
from chestbuddy.core.enums.validation_enums import ValidationStatus
from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.utils.config import ConfigManager
from chestbuddy.core.table_state_manager import TableStateManager, CellFullState, CellState

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionService(QObject):
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
        correction_suggestions_available (Signal): Emitted with dict of suggestions {(row, col): [suggestions]}
        _state_manager: Optional[TableStateManager] = None
    """

    # Maximum recursive iterations to prevent infinite loops
    MAX_ITERATIONS = 10

    # --- Add Signal Definition ---
    correction_suggestions_available = Signal(dict)
    # ---------------------------

    def __init__(
        self,
        data_model: ChestDataModel,
        config_manager: Optional[ConfigManager] = None,
        state_manager: Optional[TableStateManager] = None,
    ):
        """
        Initialize the CorrectionService.

        Args:
            data_model: Data model containing the data to be corrected
            config_manager: Optional configuration manager for settings
            state_manager: Optional TableStateManager instance
        """
        super().__init__()
        self._data_model = data_model
        self._config_manager = config_manager
        self._state_manager = state_manager
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

    def apply_corrections(
        self, only_invalid: bool = False, recursive: bool = False
    ) -> Dict[str, int]:
        """
        Apply all enabled correction rules to the data.

        Uses a two-pass algorithm:
        1. First pass applies general category rules to all columns
        2. Second pass applies column-specific rules to their respective columns

        When recursive=True, the corrections are applied repeatedly until no more
        changes occur or until MAX_ITERATIONS is reached.

        Args:
            only_invalid (bool): If True, only apply corrections to cells marked as invalid
            recursive (bool): If True, apply corrections recursively until no more changes

        Returns:
            Dict[str, int]: Statistics about the corrections applied, including iterations count
        """
        data = self._data_model.data
        if data is None or data.empty:
            return {
                "total_corrections": 0,
                "corrected_rows": 0,
                "corrected_cells": 0,
                "iterations": 0,
            }

        # Initialize statistics tracking
        total_corrections = 0
        corrected_rows = set()
        corrected_cells = set()
        iteration = 0

        # Track data changes to detect when to stop recursion
        previous_data_str = None

        # Apply corrections iteratively if recursive=True
        while iteration < self.MAX_ITERATIONS:
            # Make a copy of the data to apply corrections
            corrected_data = data.copy()

            # Get all enabled rules, prioritized (general rules first, then column-specific)
            prioritized_rules = self._rule_manager.get_prioritized_rules()

            # First pass: Apply general rule corrections
            general_corrections = []
            for rule in prioritized_rules:
                if rule.status != "enabled":
                    continue

                if rule.category == "general":
                    corrections = self._apply_rule_to_data(corrected_data, rule, only_invalid)
                    general_corrections.extend(corrections)

            # Apply general corrections first
            for row, col, _, new_value in general_corrections:
                column_name = corrected_data.columns[col]
                corrected_data.at[row, column_name] = new_value
                corrected_rows.add(row)
                corrected_cells.add((row, col))
                total_corrections += 1

            # Second pass: Apply category-specific rules
            category_corrections = []
            for rule in prioritized_rules:
                if rule.status != "enabled" or rule.category == "general":
                    continue

                # Get corrections for this rule
                corrections = self._apply_rule_to_data(corrected_data, rule, only_invalid)
                category_corrections.extend(corrections)

            # Apply category-specific corrections
            for row, col, _, new_value in category_corrections:
                column_name = corrected_data.columns[col]
                corrected_data.at[row, column_name] = new_value
                corrected_rows.add(row)
                corrected_cells.add((row, col))
                total_corrections += 1

            # Track the number of corrections in this iteration
            iteration_corrections = len(general_corrections) + len(category_corrections)

            # Update the data model with corrected data
            if iteration_corrections > 0:
                self._data_model.update_data(corrected_data)
                data = corrected_data  # Update data for next iteration

            # Increment iteration counter
            iteration += 1

            # If no corrections were made in this iteration or we're not in recursive mode, stop
            if iteration_corrections == 0 or not recursive:
                break

            # Check if data has changed using string representation
            current_data_str = str(corrected_data)
            if previous_data_str == current_data_str:
                logger.debug("No data changes detected, stopping recursive correction")
                break

            previous_data_str = current_data_str

        # Record in history
        stats = {
            "total_corrections": total_corrections,
            "corrected_rows": len(corrected_rows),
            "corrected_cells": len(corrected_cells),
            "iterations": iteration,
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

        # Apply corrections to the dataframe copy first
        for row, col, _, new_value in corrections:
            column_name = corrected_data.columns[col]
            corrected_data.at[row, column_name] = new_value
            corrected_rows.add(row)
            corrected_cells.add((row, col))

        # Update the data model with corrected data
        if corrections:
            self._data_model.update_data(corrected_data)

            # --- Reset state for corrected cells --- #
            if self._state_manager:
                for row, col, _, _ in corrections:
                    logger.debug(f"Resetting state for corrected cell ({row}, {col})")
                    self._state_manager.reset_cell_state(row, col)
            else:
                logger.warning(
                    "State manager not set in CorrectionService, cannot reset cell state."
                )
            # -------------------------------------- #

        # Record in history
        stats = {
            "total_corrections": len(corrections),
            "corrected_rows": len(corrected_rows),
            "corrected_cells": len(corrected_cells),
        }

        self._correction_history.append({"rule": rule.to_dict(), "stats": stats})

        return stats

    def apply_rule_to_data(
        self, rule: CorrectionRule, only_invalid: bool = False, selected_only: List[int] = None
    ) -> List[Tuple[int, int, Any, Any]]:
        """Applies a correction rule to the data, returning the list of changes.

        Args:
            rule (CorrectionRule): The rule to apply.
            only_invalid (bool): Apply only to invalid cells.
            selected_only (List[int]): Apply only to these row indices.

        Returns:
            List[Tuple[int, int, Any, Any]]: List of (row_idx, col_idx, old_value, new_value)
        """
        data = self._data_model.data
        if data is None or data.empty:
            logger.info("No data available to apply rule to.")
            return []

        if not rule:
            logger.warning("No rule specified for correction")
            return []

        # Get potential corrections from the private helper
        potential_corrections = self._apply_rule_to_data(data, rule, only_invalid)

        # Filter to selected rows if specified
        if selected_only is not None:
            selected_set = set(selected_only)
            corrections_to_apply = [c for c in potential_corrections if c[0] in selected_set]
            logger.debug(
                f"Filtered {len(potential_corrections)} potential corrections to {len(corrections_to_apply)} based on selection."
            )
        else:
            corrections_to_apply = potential_corrections

        if not corrections_to_apply:
            logger.info(f"No corrections to apply for rule: {rule}")
            return []

        # Apply corrections and update state
        applied_corrections_info = []
        state_updates = {}
        reset_state = CellFullState(validation_status=CellState.NOT_VALIDATED)

        # Use a copy for multi-cell updates if DataModel updates immediately
        # If DataModel batches updates, direct modification might be okay.
        # Assuming direct update via set_cell_value for now.
        successful_applications = 0
        for row, col, old_value, new_value in corrections_to_apply:
            try:
                success = self._data_model.set_cell_value(row, col, new_value)
                if success:
                    applied_corrections_info.append((row, col, old_value, new_value))
                    state_updates[(row, col)] = reset_state
                    successful_applications += 1
                else:
                    logger.warning(
                        f"Failed to apply correction for rule {rule} at ({row}, {col}) via DataModel."
                    )
            except Exception as e:
                logger.error(
                    f"Error applying correction for rule {rule} at ({row}, {col}): {e}",
                    exc_info=True,
                )

        # Update state manager in one batch
        if state_updates and self._state_manager:
            self._state_manager.update_states(state_updates)
            logger.debug(f"Reset state for {len(state_updates)} cells corrected by rule: {rule}")
        elif state_updates:
            logger.warning(
                "State manager not available, cannot reset state for cells corrected by rule."
            )

        # Add to history (optional)
        if successful_applications > 0:
            now = datetime.now().isoformat()
            history_entry = {
                "timestamp": now,
                "type": "rule_application",
                "rule": rule.to_dict(),
                "applied_corrections": [
                    {
                        "row": int(row),
                        "column": self._data_model.get_column_name(col),
                        "old_value": str(old_val),
                        "new_value": str(new_val),
                    }
                    for row, col, old_val, new_val in applied_corrections_info
                ],
                "stats": {
                    "successful_applications": successful_applications,
                    "attempted_corrections": len(corrections_to_apply),
                },
            }
            self._correction_history.append(history_entry)
            logger.info(
                f"Applied {successful_applications}/{len(corrections_to_apply)} corrections with rule: {rule}"
            )
            # Optionally emit a signal here if needed
            # self.corrections_applied.emit(successful_applications)

        return applied_corrections_info

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
        Get cells that have available correction rules and are currently invalid.

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples for cells with corrections
        """
        # Get data and validation status
        data = self._data_model.data
        if data is None or data.empty:
            logger.warning("No data available to check for correctable cells")
            return []

        # Get validation status
        validation_status = None
        if self._state_manager:
            # Assume TableStateManager has a method to provide the full status DataFrame
            # This method needs to be implemented in TableStateManager
            validation_status = self._state_manager.get_validation_status_df()
        else:
            logger.warning(
                "TableStateManager not set in CorrectionService, cannot get validation status."
            )

        if validation_status is None or validation_status.empty:
            logger.warning(
                "No validation status available from StateManager to check for correctable cells"
            )
            return []

        # Get enabled rules
        rules = self._rule_manager.get_rules(status="enabled")
        if not rules:
            logger.debug("No enabled correction rules available")
            return []

        # Map column indices to validation status column names
        col_validation_map = {}
        for col_idx, col_name in enumerate(data.columns):
            col_validation_map[col_idx] = f"{col_name}_valid"

        # Check all cells for potential corrections
        correctable_cells = set()

        for col_idx, col_name in enumerate(data.columns):
            # Get validation status column name
            validation_col = col_validation_map.get(col_idx)

            # Skip if validation status not available for this column
            if validation_col not in validation_status.columns:
                continue

            # Get category for this column
            col_category = self._get_column_category(col_name)

            # Get rules applicable to this column
            applicable_rules = [
                r
                for r in rules
                if r.category.lower() == col_category or r.category.lower() == "general"
            ]

            # Skip if no applicable rules
            if not applicable_rules:
                continue

            # Check each cell in this column
            for row_idx in range(len(data)):
                # Skip if the cell is not invalid
                if validation_status.at[row_idx, validation_col] != ValidationStatus.INVALID:
                    continue

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

    def _get_column_category(self, column_name: str) -> str:
        """
        Get the category for a column.

        Args:
            column_name: Column name

        Returns:
            str: Category for the column
        """
        return self._category_mapping.get(column_name.upper(), "general").lower()

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

    def get_validation_service(self):
        """
        Get the validation service used by this correction service.

        Returns:
            ValidationService: The validation service
        """
        return self._validation_service

    def check_correctable_status(self) -> int:
        """
        Check and mark cells that have available corrections as correctable.

        This method uses the validation service to identify invalid cells
        and mark those that can be corrected as CORRECTABLE.

        Returns:
            int: Number of cells marked as correctable
        """
        if not self._validation_service:
            logger.warning("Validation service not available, can't mark correctable cells")
            return 0

        # Get cells with available corrections
        correctable_cells = self.get_cells_with_available_corrections()

        # Update validation status through the validation service
        marked_count = 0
        try:
            # Let the validation service handle the status update
            self._validation_service.update_correctable_status(correctable_cells)
            marked_count = len(correctable_cells)
            logger.info(f"Marked {marked_count} cells as correctable")
        except Exception as e:
            logger.error(f"Error marking correctable cells: {e}")

        return marked_count

    def clear_correction_history(self) -> None:
        """Clear the correction history."""
        self._correction_history = []

    # Add new method to get suggestions for a specific cell
    def get_suggestions_for_cell(self, row_idx: int, col_idx: int) -> List[Dict]:
        """
        Find all applicable correction rule suggestions for a specific cell.

        Args:
            row_idx (int): The row index of the cell.
            col_idx (int): The column index of the cell.

        Returns:
            List[Dict]: A list of suggestion dictionaries.
                      Each dictionary contains keys like 'original', 'corrected',
                      'rule_id', 'category'. Returns empty list if no suggestions found.
        """
        suggestions = []
        data = self._data_model.data
        if data is None or data.empty or row_idx >= len(data) or col_idx >= len(data.columns):
            return suggestions

        col_name = data.columns[col_idx]
        cell_value = data.at[row_idx, col_name]

        # Skip empty or NaN values
        if cell_value is None or (isinstance(cell_value, float) and np.isnan(cell_value)):
            return suggestions

        cell_value_str = str(cell_value)
        col_category = self._get_column_category(col_name)

        # Get enabled rules applicable to this column's category or general
        rules = self._rule_manager.get_rules(status="enabled")
        applicable_rules = [
            r
            for r in rules
            if r.category.lower() == col_category or r.category.lower() == "general"
        ]

        for rule in applicable_rules:
            # Check if the rule's from_value matches the cell value
            if self._values_match(cell_value_str, str(rule.from_value)):
                # Add suggestion based on this rule
                suggestion = {
                    "original": cell_value_str,
                    "corrected": rule.to_value,
                    "rule_id": getattr(rule, "id", None),  # Assuming rule has an ID
                    "category": rule.category,
                    # Add confidence score if available/relevant
                }
                suggestions.append(suggestion)

        return suggestions

    # --- Method to Find and Emit Suggestions ---
    def find_and_emit_suggestions(self) -> None:
        """
        Finds all cells with available corrections based on enabled rules
        and emits the `correction_suggestions_available` signal with the
        detailed suggestions for those cells.
        """
        logger.info("Finding correction suggestions...")
        correctable_cells = self.get_cells_with_available_corrections()

        if not correctable_cells:
            logger.info("No cells found with available corrections.")
            # Emit empty dict? Or maybe only emit if suggestions ARE found?
            # Let's emit only if suggestions exist to avoid empty signals.
            # self.correction_suggestions_available.emit({})
            return

        suggestions_payload: Dict[Tuple[int, int], List[Dict]] = {}
        for row_idx, col_idx in correctable_cells:
            suggestions = self.get_suggestions_for_cell(row_idx, col_idx)
            if suggestions:  # Only add if suggestions were actually found for this cell
                suggestions_payload[(row_idx, col_idx)] = suggestions

        if suggestions_payload:
            logger.info(f"Found suggestions for {len(suggestions_payload)} cells. Emitting signal.")
            try:
                self.correction_suggestions_available.emit(suggestions_payload)
                logger.debug("correction_suggestions_available signal emitted successfully.")
            except Exception as e:
                logger.error(f"Error emitting correction_suggestions_available signal: {e}")
        else:
            logger.info(
                "Found potentially correctable cells, but no specific suggestions generated."
            )

    # --- Add Setter for State Manager (Optional but good practice) ---
    def set_state_manager(self, state_manager: TableStateManager) -> None:
        """
        Set the TableStateManager instance.
        """
        self._state_manager = state_manager
        logger.info("TableStateManager set for CorrectionService")

    # ----------------------------------------------------------------

    def apply_suggestion_to_cell(self, row: int, col: int, suggestion: object) -> bool:
        """Applies a specific correction suggestion to a single cell.

        Args:
            row (int): Row index of the cell.
            col (int): Column index of the cell.
            suggestion (object): The suggestion object (must have 'corrected_value').

        Returns:
            bool: True if successful, False otherwise.
        """
        if not hasattr(suggestion, "corrected_value"):
            logger.error(
                f"Suggestion object lacks 'corrected_value' attribute for cell ({row}, {col})"
            )
            return False

        corrected_value = suggestion.corrected_value
        original_value = None

        try:
            # Get original value for history/logging
            original_value = self._data_model.get_cell_value(row, col)

            # Update the data model
            success = self._data_model.set_cell_value(row, col, corrected_value)
            if not success:
                logger.error(f"DataModel failed to set value for cell ({row}, {col})")
                return False

            logger.info(
                f"Applied suggestion to cell ({row}, {col}): '{original_value}' -> '{corrected_value}'"
            )

            # --- Reset state for the corrected cell --- #
            if self._state_manager:
                reset_state = CellFullState(
                    validation_status=CellState.NOT_VALIDATED  # Or VALID if auto-revalidation is off
                )
                self._state_manager.update_states({(row, col): reset_state})
                logger.debug(f"Reset state for corrected cell ({row}, {col})")
            else:
                logger.warning("TableStateManager not available, cannot reset cell state.")
            # ---------------------------------------- #

            # TODO: Add to correction history?
            # self._correction_history.append({
            #     "type": "suggestion",
            #     "cell": (row, col),
            #     "original": original_value,
            #     "corrected": corrected_value,
            #     "timestamp": datetime.now().isoformat()
            # })

            return True

        except Exception as e:
            logger.error(f"Error applying suggestion to cell ({row}, {col}): {e}", exc_info=True)
            return False

    def apply_ui_correction(self, row: int, col: int, corrected_value: Any) -> bool:
        """
        Applies a single correction initiated directly from the UI.

        Args:
            row: The row index of the cell.
            col: The column index of the cell.
            corrected_value: The new value to set.

        Returns:
            bool: True if the value was changed, False otherwise.
        """
        if self._data_model is None:
            logger.error("Cannot apply UI correction: Data model not available.")
            return False

        try:
            # Get column name from index
            column_name = self._data_model.column_names[col]
            original_value = self._data_model.get_cell_value(row, column_name)

            if original_value == corrected_value:
                logger.debug(
                    f"UI correction skipped: Value at ({row},{column_name}) is already '{corrected_value}'"
                )
                return False  # No change needed

            logger.info(
                f"Applying UI correction at ({row},{column_name}): '{original_value}' -> '{corrected_value}'"
            )
            # Directly update the data model
            # NOTE: This bypasses rule logic, applying the user's choice directly.
            # Consider if validation should be re-run immediately after this.
            success = self._data_model.set_cell_value(row, column_name, corrected_value)

            if success:
                # Optional: Add to a simplified history?
                # self._correction_history.append({"type": "ui", "row": row, "col": col, "old": original_value, "new": corrected_value})
                # TODO: Consider resetting the state of this cell in TableStateManager
                if self._state_manager:
                    logger.debug(f"Resetting state for cell ({row}, {col}) after UI correction.")
                    # Reset state to NORMAL or trigger revalidation
                    reset_state = CellFullState(validation_status=CellState.NORMAL)
                    self._state_manager.update_states({(row, col): reset_state})
                return True
            else:
                logger.warning(
                    f"Data model update failed for UI correction at ({row},{column_name})."
                )
                return False

        except IndexError:
            logger.error(f"Invalid column index {col} provided for UI correction.")
            return False
        except Exception as e:
            logger.error(
                f"Error during UI correction application at ({row},{col}): {e}", exc_info=True
            )
            return False
