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
        self._default_rules_path = Path("data/corrections/correction_rules.csv")

    def load_rules(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """
        Load rules from CSV file.

        Args:
            file_path: Path to the CSV file, uses default path if None

        Note:
            Handles nonexistent files gracefully
            Converts DataFrame rows to CorrectionRule objects
        """
        path = Path(file_path) if file_path else self._default_rules_path

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
            file_path: Path to the CSV file, uses default path if None
        """
        path = Path(file_path) if file_path else self._default_rules_path

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
        self, category: Optional[str] = None, status: Optional[str] = None
    ) -> List[CorrectionRule]:
        """
        Get rules with optional filtering.

        Args:
            category: Filter by rule category (player, chest_type, etc.)
            status: Filter by rule status (enabled, disabled)

        Returns:
            List[CorrectionRule]: Filtered rules
        """
        result = self._rules

        if category:
            result = [rule for rule in result if rule.category == category]

        if status:
            result = [rule for rule in result if rule.status == status]

        return result

    def move_rule(self, from_index: int, to_index: int) -> None:
        """
        Move a rule to change its priority.

        Args:
            from_index: Current index of the rule
            to_index: Target index for the rule

        Raises:
            IndexError: If either index is out of range
        """
        if not (0 <= from_index < len(self._rules) and 0 <= to_index < len(self._rules)):
            raise IndexError(f"Rule index out of range: from={from_index}, to={to_index}")

        rule = self._rules.pop(from_index)
        self._rules.insert(to_index, rule)

    def move_rule_to_top(self, index: int) -> None:
        """
        Move a rule to the top of its category.

        Args:
            index: Index of the rule to move

        Raises:
            IndexError: If index is out of range
        """
        if not (0 <= index < len(self._rules)):
            raise IndexError(f"Rule index out of range: {index}")

        rule = self._rules[index]
        category_rules = [i for i, r in enumerate(self._rules) if r.category == rule.category]

        if category_rules:
            top_index = min(category_rules)
            self.move_rule(index, top_index)

    def move_rule_to_bottom(self, index: int) -> None:
        """
        Move a rule to the bottom of its category.

        Args:
            index: Index of the rule to move

        Raises:
            IndexError: If index is out of range
        """
        if not (0 <= index < len(self._rules)):
            raise IndexError(f"Rule index out of range: {index}")

        rule = self._rules[index]
        category_rules = [i for i, r in enumerate(self._rules) if r.category == rule.category]

        if category_rules:
            bottom_index = max(category_rules)
            self.move_rule(index, bottom_index)

    def toggle_rule_status(self, index: int) -> None:
        """
        Toggle a rule's enabled/disabled status.

        Args:
            index: Index of the rule to toggle

        Raises:
            IndexError: If index is out of range
        """
        if not (0 <= index < len(self._rules)):
            raise IndexError(f"Rule index out of range: {index}")

        rule = self._rules[index]
        new_status = "disabled" if rule.status == "enabled" else "enabled"

        updated_rule = CorrectionRule(
            to_value=rule.to_value,
            from_value=rule.from_value,
            category=rule.category,
            status=new_status,
            order=rule.order,
        )

        self.update_rule(index, updated_rule)

    def get_prioritized_rules(self) -> List[CorrectionRule]:
        """
        Get rules sorted for application priority.

        Returns:
            List[CorrectionRule]: Rules in priority order

        Note:
            Priority order:
            1. General rules first
            2. Category-specific rules
            Within each group, sorted by order
        """
        # Get general rules and category-specific rules
        general_rules = [rule for rule in self._rules if rule.category == "general"]
        category_rules = [rule for rule in self._rules if rule.category != "general"]

        # Sort each group by order
        general_rules.sort(key=lambda rule: rule.order)
        category_rules.sort(key=lambda rule: rule.order)

        # Combine with general rules first
        return general_rules + category_rules
