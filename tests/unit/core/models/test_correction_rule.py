"""
Test suite for the CorrectionRule model class.

This module contains tests for creating, comparing, and serializing correction rules.
"""

import pytest
from pathlib import Path
import sys

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from chestbuddy.core.models.correction_rule import CorrectionRule


class TestCorrectionRule:
    """Test cases for the CorrectionRule model class."""

    def test_creation_with_defaults(self):
        """Test creating a rule with minimal parameters and default values."""
        rule = CorrectionRule(to_value="Correct", from_value="Incorrect", category="player")

        assert rule.to_value == "Correct"
        assert rule.from_value == "Incorrect"
        assert rule.category == "player"
        assert rule.status == "enabled"  # default value

    def test_creation_with_all_parameters(self):
        """Test creating a rule with all parameters specified."""
        rule = CorrectionRule(
            to_value="Correct",
            from_value="Incorrect",
            category="chest_type",
            status="disabled",
        )

        assert rule.to_value == "Correct"
        assert rule.from_value == "Incorrect"
        assert rule.category == "chest_type"
        assert rule.status == "disabled"

    def test_equality_comparison_equal(self):
        """Test that two rules with same values are considered equal."""
        rule1 = CorrectionRule("Correct", "Incorrect", "player")
        rule2 = CorrectionRule("Correct", "Incorrect", "player")

        assert rule1 == rule2
        assert not (rule1 != rule2)

    def test_equality_comparison_different(self):
        """Test that rules with different values are not equal."""
        rule1 = CorrectionRule("Correct", "Incorrect", "player")

        # Different to_value
        rule2 = CorrectionRule("Different", "Incorrect", "player")
        assert rule1 != rule2

        # Different from_value
        rule3 = CorrectionRule("Correct", "Different", "player")
        assert rule1 != rule3

        # Different category
        rule4 = CorrectionRule("Correct", "Incorrect", "chest_type")
        assert rule1 != rule4

        # Different status doesn't affect equality
        rule5 = CorrectionRule("Correct", "Incorrect", "player", status="disabled")
        assert rule1 == rule5

    def test_equality_with_non_rule(self):
        """Test equality comparison with non-CorrectionRule objects."""
        rule = CorrectionRule("Correct", "Incorrect", "player")

        assert rule != "Not a rule"
        assert rule != 123
        assert rule != ["Correct", "Incorrect", "player"]
        assert rule != {"to": "Correct", "from": "Incorrect", "category": "player"}

    def test_to_dict(self):
        """Test converting a rule to a dictionary."""
        rule = CorrectionRule(
            to_value="Correct",
            from_value="Incorrect",
            category="source",
            status="disabled",
        )

        rule_dict = rule.to_dict()

        assert rule_dict["To"] == "Correct"
        assert rule_dict["From"] == "Incorrect"
        assert rule_dict["Category"] == "source"
        assert rule_dict["Status"] == "disabled"
        assert "Order" not in rule_dict

    def test_from_dict_with_all_fields(self):
        """Test creating a rule from a dictionary with all fields (including ignored Order)."""
        rule_dict = {
            "To": "Correct",
            "From": "Incorrect",
            "Category": "general",
            "Status": "enabled",
            "Order": 3,
        }

        rule = CorrectionRule.from_dict(rule_dict)

        assert rule.to_value == "Correct"
        assert rule.from_value == "Incorrect"
        assert rule.category == "general"
        assert rule.status == "enabled"
        assert not hasattr(rule, "order")

    def test_from_dict_with_minimal_fields(self):
        """Test creating a rule from a dictionary with minimal fields."""
        rule_dict = {"To": "Correct", "From": "Incorrect"}

        rule = CorrectionRule.from_dict(rule_dict)

        assert rule.to_value == "Correct"
        assert rule.from_value == "Incorrect"
        assert rule.category == "general"
        assert rule.status == "enabled"
        assert not hasattr(rule, "order")

    def test_from_dict_with_empty_order(self):
        """Test creating a rule from a dictionary with empty order string (ignored)."""
        rule_dict = {"To": "Correct", "From": "Incorrect", "Order": ""}

        rule = CorrectionRule.from_dict(rule_dict)

        assert rule.to_value == "Correct"
        assert rule.from_value == "Incorrect"
        assert rule.category == "general"
        assert rule.status == "enabled"
        assert not hasattr(rule, "order")

    def test_string_representation(self):
        """Test the string representation of a rule."""
        rule = CorrectionRule("Correct", "Incorrect", "player", "enabled")
        representation = repr(rule)

        assert "CorrectionRule" in representation
        assert "to='Correct'" in representation
        assert "from='Incorrect'" in representation
        assert "category='player'" in representation
        assert "status='enabled'" in representation
        assert "order=" not in representation
