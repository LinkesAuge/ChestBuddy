"""
correction_rule.py

Description: Model class representing a correction rule mapping.
Usage:
    rule = CorrectionRule("Correct", "Incorrect", "player")
    rule_dict = rule.to_dict()
    rule_from_dict = CorrectionRule.from_dict(rule_dict)
"""

from typing import Dict, Any


class CorrectionRule:
    """
    Model class representing a correction rule mapping.

    Attributes:
        to_value (str): The correct value that will replace the incorrect value
        from_value (str): The incorrect value to be replaced
        category (str): The category (player, chest_type, source, general)
        status (str): The rule status (enabled or disabled)

    Implementation Notes:
        - Equality is determined by to_value, from_value, and category only
        - Status doesn't affect equality
        - Rules can be serialized to/from dictionary format for CSV storage
        - Order is implicitly handled by position in list/file
    """

    def __init__(
        self,
        to_value: str,
        from_value: str,
        category: str = "general",
        status: str = "enabled",
    ):
        """
        Initialize a correction rule.

        Args:
            to_value (str): The correct value
            from_value (str): The incorrect value to be replaced
            category (str): The category (player, chest_type, source, general)
            status (str): The rule status (enabled or disabled)
        """
        self.to_value = to_value
        self.from_value = from_value
        self.category = category
        self.status = status

    def __eq__(self, other) -> bool:
        """
        Enable equality comparison between rules.

        Args:
            other: Object to compare with

        Returns:
            bool: True if rules are equal, False otherwise

        Note:
            Two rules are considered equal if they have the same to_value,
            from_value, and category. Status doesn't affect equality.
        """
        if not isinstance(other, CorrectionRule):
            return False
        return (
            self.to_value == other.to_value
            and self.from_value == other.from_value
            and self.category == other.category
        )

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: String representation of the rule
        """
        return (
            f"CorrectionRule(to='{self.to_value}', from='{self.from_value}', "
            f"category='{self.category}', status='{self.status}')"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert rule to dictionary for serialization.

        Returns:
            dict: Dictionary representation of the rule
        """
        return {
            "To": self.to_value,
            "From": self.from_value,
            "Category": self.category,
            "Status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrectionRule":
        """
        Create rule from dictionary.

        Args:
            data (dict): Dictionary containing rule data

        Returns:
            CorrectionRule: New correction rule instance
        """
        # Ignore 'Order' and 'Description' fields if present for backward compatibility
        return cls(
            to_value=data.get("To", ""),
            from_value=data.get("From", ""),
            category=data.get("Category", "general"),
            status=data.get("Status", "enabled"),
        )
