"""
correction_rule_manager.py

Description: Manager for loading, saving, and organizing correction rules.
Usage:
    manager = CorrectionRuleManager()
    manager.load_rules('path/to/rules.csv')
    manager.add_rule(CorrectionRule('Correct', 'Incorrect', 'player'))
    manager.save_rules()
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Iterator

from .correction_rule import CorrectionRule


logger = logging.getLogger(__name__)


class CorrectionRuleManager:
    """
    Manager for loading, saving, and organizing correction rules.

    Implements rule storage, CRUD operations, and rule prioritization.

    Attributes:
        _rules (List[CorrectionRule]): List of correction rules
        _config_manager: Optional configuration manager for settings
        _default_rules_path (Path): Default path for saving/loading rules
        _custom_path (Optional[Path]): Custom path for rules if configured

    Implementation Notes:
        - Rules are stored in a plain list for simplicity
        - Duplicates are prevented based on rule equality
        - Rules can be filtered by category and status
        - Priority is maintained by explicit ordering
    """

    def __init__(self, config_manager=None):
        """
        Initialize with optional config manager.

        Args:
            config_manager: Optional configuration manager for settings
        """
        self._rules: List[CorrectionRule] = []
        self._config_manager = config_manager
        self._default_rules_path = Path("data/corrections/default_corrections.csv")

        # If we have a config manager, check for custom path
        self._custom_path = None
        if self._config_manager:
            try:
                custom_path = self._config_manager.get("Corrections", "rules_file_path", None)
                if custom_path and Path(custom_path).exists():
                    self._custom_path = Path(custom_path)
                    logger.info(f"Using custom corrections file path: {self._custom_path}")
            except Exception as e:
                logger.warning(f"Error loading custom corrections path from config: {e}")

    def get_correction_file_path(self):
        """
        Get the current correction file path (custom or default).

        Returns:
            Path: The path to use for correction rules
        """
        return self._custom_path if self._custom_path else self._default_rules_path

    def save_custom_path_to_config(self, path):
        """
        Save a custom correction file path to configuration.

        Args:
            path: Path to save
        """
        if not self._config_manager:
            logger.warning("Cannot save custom path: No config manager available")
            return

        try:
            str_path = str(path)
            self._config_manager.set("Corrections", "rules_file_path", str_path)
            self._custom_path = Path(str_path)
            logger.info(f"Saved custom corrections path to config: {str_path}")
        except Exception as e:
            logger.error(f"Error saving custom corrections path to config: {e}")

    def load_rules(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Load rules from CSV file.

        Args:
            file_path: Path to the CSV file, uses configured path if None

        Note:
            Handles nonexistent files gracefully
            Converts DataFrame rows to CorrectionRule objects
            If no path is specified, uses the custom path (if set) or falls back to default
        """
        path = Path(file_path) if file_path else self.get_correction_file_path()

        if not path.exists():
            logger.warning(f"Rules file not found: {path}")
            return

        try:
            df = pd.read_csv(path)
            self._rules = []

            for _, row in df.iterrows():
                rule = CorrectionRule.from_dict(row.to_dict())
                self.add_rule(rule)

            logger.info(f"Loaded {len(self._rules)} correction rules from {path}")
        except Exception as e:
            logger.error(f"Error loading rules from {path}: {e}")

    def save_rules(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save rules to CSV file.

        Args:
            file_path: Path to the CSV file, uses configured path if None
        """
        path = Path(file_path) if file_path else self.get_correction_file_path()

        try:
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Convert rules to DataFrame
            rules_data = [rule.to_dict() for rule in self._rules]
            df = pd.DataFrame(rules_data)

            # Save to CSV
            df.to_csv(path, index=False)
            logger.info(f"Saved {len(self._rules)} correction rules to {path}")
        except Exception as e:
            logger.error(f"Error saving rules to {path}: {e}")

    def add_rule(self, rule: CorrectionRule) -> None:
        """
        Add a new rule to the manager.

        Args:
            rule: The CorrectionRule to add

        Note:
            Prevents adding duplicate rules
        """
        if rule not in self._rules:
            self._rules.append(rule)

    def update_rule(self, index: int, updated_rule: CorrectionRule) -> None:
        """
        Update an existing rule.

        Args:
            index: Index of the rule to update
            updated_rule: New rule data

        Raises:
            IndexError: If index is out of range
        """
        if 0 <= index < len(self._rules):
            self._rules[index] = updated_rule
        else:
            raise IndexError(f"Rule index out of range: {index}")

    def delete_rule(self, index: int) -> None:
        """
        Delete a rule by index.

        Args:
            index: Index of the rule to delete

        Raises:
            IndexError: If index is out of range
        """
        if 0 <= index < len(self._rules):
            del self._rules[index]
        else:
            raise IndexError(f"Rule index out of range: {index}")

    def get_rule(self, index: int) -> CorrectionRule:
        """
        Get a rule by index.

        Args:
            index: Index of the rule to retrieve

        Returns:
            CorrectionRule: The rule at the specified index

        Raises:
            IndexError: If index is out of range
        """
        if 0 <= index < len(self._rules):
            return self._rules[index]
        else:
            raise IndexError(f"Rule index out of range: {index}")

    def get_rules(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> List[CorrectionRule]:
        """
        Get rules with optional filtering.

        Args:
            category: Filter by rule category (player, chest_type, etc.)
            status: Filter by rule status (enabled, disabled)
            search_term: Filter rules that contain the search term in 'from_value'
                         or 'to_value'. Case-insensitive.

        Returns:
            List[CorrectionRule]: Filtered rules
        """
        result = self._rules

        if category:
            result = [rule for rule in result if rule.category == category]

        if status:
            result = [rule for rule in result if rule.status == status]

        if search_term:
            search_term = search_term.lower()
            result = [
                rule
                for rule in result
                if (
                    (rule.from_value and search_term in rule.from_value.lower())
                    or (rule.to_value and search_term in rule.to_value.lower())
                )
            ]

        return result

    def move_rule(self, from_index: int, to_index: int) -> None:
        """
        Move a rule to change its priority.

        Args:
            from_index (int): Index of rule to move
            to_index (int): Destination index

        Raises:
            IndexError: If either index is out of range
        """
        if not (0 <= from_index < len(self._rules)):
            raise IndexError(f"From index out of range: {from_index}")
        if not (0 <= to_index < len(self._rules)):
            raise IndexError(f"To index out of range: {to_index}")

        # Move the rule by removing it and inserting at the new position
        rule = self._rules.pop(from_index)
        self._rules.insert(to_index, rule)

    def move_rule_to_top(self, index: int) -> None:
        """
        Move a rule to the top of its category.

        Args:
            index (int): Index of rule to move

        Raises:
            IndexError: If index is out of range
        """
        if not (0 <= index < len(self._rules)):
            raise IndexError(f"Rule index out of range: {index}")

        # Get the rule to move
        rule = self._rules[index]

        # Find the first rule with the same category
        category_start_index = 0
        for i, r in enumerate(self._rules):
            if r.category == rule.category and i != index:
                category_start_index = i
                break

        # Move the rule by removing it and inserting at the category start
        self._rules.pop(index)
        self._rules.insert(category_start_index, rule)

    def move_rule_to_bottom(self, index: int) -> None:
        """
        Move a rule to the bottom of its category.

        Args:
            index (int): Index of rule to move

        Raises:
            IndexError: If index is out of range
        """
        if not (0 <= index < len(self._rules)):
            raise IndexError(f"Rule index out of range: {index}")

        # Get the rule to move
        rule = self._rules[index]

        # Find the last rule with the same category
        category_end_index = len(self._rules) - 1
        for i in range(len(self._rules) - 1, -1, -1):
            if self._rules[i].category == rule.category and i != index:
                category_end_index = i
                break

        # Move the rule by removing it and inserting after the category end
        self._rules.pop(index)
        self._rules.insert(category_end_index + 1, rule)

    def toggle_rule_status(self, index: int) -> None:
        """
        Toggle a rule's enabled/disabled status.

        Args:
            index (int): Index of rule to toggle

        Raises:
            IndexError: If index is out of range
        """
        if not (0 <= index < len(self._rules)):
            raise IndexError(f"Rule index out of range: {index}")

        rule = self._rules[index]
        if rule.status == "enabled":
            rule.status = "disabled"
        else:
            rule.status = "enabled"

    def get_prioritized_rules(self) -> List[CorrectionRule]:
        """
        Get rules sorted by priority.

        Returns:
            List[CorrectionRule]: Rules ordered by category and position in the list
        """
        # Rules are already ordered by their position in the list
        # We only need to filter for enabled rules
        return [rule for rule in self._rules if rule.status == "enabled"]

    def import_rules(
        self, file_path: Union[str, Path], replace: bool = False, save_as_default: bool = True
    ) -> None:
        """
        Import rules from a file.

        Args:
            file_path (Path): Path to import file
            replace (bool): Whether to replace existing rules
            save_as_default (bool): Whether to save imported rules as default

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file has invalid format
            pd.errors.ParserError: If CSV parsing fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")

        try:
            # Determine file type by extension
            ext = path.suffix.lower()
            if ext == ".csv":
                df = pd.read_csv(path)
            elif ext == ".txt":
                # For TXT files, assume tab-separated format
                df = pd.read_csv(path, sep="\t")
            else:
                raise ValueError(f"Unsupported file extension: {ext}")

            # Clear existing rules if replace is True
            if replace:
                self._rules = []

            # Process each row
            imported_count = 0
            for _, row in df.iterrows():
                # Convert row to dict and create rule
                row_dict = row.to_dict()

                # Skip rows without required fields
                if "From" not in row_dict or "To" not in row_dict:
                    continue

                rule = CorrectionRule.from_dict(row_dict)

                # Add rule if it doesn't exist
                if rule not in self._rules:
                    self._rules.append(rule)
                    imported_count += 1

            logger.info(f"Imported {imported_count} rules from {path}")

            # Save as default if requested
            if save_as_default:
                self.save_rules()

        except Exception as e:
            logger.error(f"Error importing rules from {path}: {e}")
            raise

    def export_rules(self, file_path: Union[str, Path], only_enabled: bool = False) -> None:
        """
        Export rules to a file.

        Args:
            file_path (Path): Path to export file
            only_enabled (bool): Whether to export only enabled rules

        Raises:
            ValueError: If unsupported file extension
            IOError: If file cannot be written
        """
        path = Path(file_path)

        try:
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Filter rules if only_enabled is True
            rules_to_export = (
                [rule for rule in self._rules if rule.status == "enabled"]
                if only_enabled
                else self._rules
            )

            # Convert rules to DataFrame
            rules_data = [rule.to_dict() for rule in rules_to_export]
            df = pd.DataFrame(rules_data)

            # Determine export format by extension
            ext = path.suffix.lower()
            if ext == ".csv":
                df.to_csv(path, index=False)
            elif ext == ".txt":
                # For TXT files, use tab-separated format
                df.to_csv(path, sep="\t", index=False)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")

            logger.info(f"Exported {len(rules_to_export)} rules to {path}")

        except Exception as e:
            logger.error(f"Error exporting rules to {path}: {e}")
            raise
