"""
Test suite for the CorrectionRuleManager class.

This module contains tests for loading, saving, and managing correction rules.
"""

import pytest
import tempfile
import pandas as pd
import os
from pathlib import Path
import sys
from unittest.mock import MagicMock

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.models.correction_rule_manager import CorrectionRuleManager


@pytest.fixture
def sample_rules():
    """Fixture providing a list of sample correction rules for testing."""
    return [
        CorrectionRule("Player1", "player1", "player", "enabled"),
        CorrectionRule("Player2", "player2", "player", "enabled"),
        CorrectionRule("Chest1", "chest1", "chest_type", "enabled"),
        CorrectionRule("Source1", "source1", "source", "enabled"),
        CorrectionRule("General1", "general1", "general", "enabled"),
        CorrectionRule("General2", "general2", "general", "disabled"),
    ]


@pytest.fixture
def temp_csv_file():
    """Fixture providing a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
        temp_path = temp_file.name

    yield temp_path

    # Clean up after the test
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestCorrectionRuleManager:
    """Test cases for the CorrectionRuleManager class."""

    def test_initialization(self):
        """Test initializing the manager with default values."""
        manager = CorrectionRuleManager()

        assert manager._rules == []
        assert isinstance(manager._default_rules_path, Path)
        assert "correction_rules.csv" in str(manager._default_rules_path)

    def test_initialization_with_config(self, monkeypatch):
        """Test initializing the manager with a config manager."""
        mock_config = MagicMock()
        manager = CorrectionRuleManager(config_manager=mock_config)

        assert manager._config_manager == mock_config

    def test_add_rule(self):
        """Test adding a rule to the manager."""
        manager = CorrectionRuleManager()
        rule = CorrectionRule("Correct", "Incorrect", "player")

        manager.add_rule(rule)

        assert len(manager._rules) == 1
        assert manager._rules[0] == rule

    def test_add_duplicate_rule(self):
        """Test adding a duplicate rule to the manager."""
        manager = CorrectionRuleManager()
        rule1 = CorrectionRule("Correct", "Incorrect", "player")
        rule2 = CorrectionRule("Correct", "Incorrect", "player")

        manager.add_rule(rule1)
        manager.add_rule(rule2)

        # Should only have one rule (no duplicates)
        assert len(manager._rules) == 1

    def test_get_rule(self, sample_rules):
        """Test getting a rule by index."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        retrieved_rule = manager.get_rule(2)

        assert retrieved_rule == sample_rules[2]

    def test_get_rule_invalid_index(self, sample_rules):
        """Test getting a rule with an invalid index."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        with pytest.raises(IndexError):
            manager.get_rule(len(sample_rules) + 1)

    def test_get_rules_all(self, sample_rules):
        """Test getting all rules."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        rules = manager.get_rules()

        assert len(rules) == len(sample_rules)
        for rule in sample_rules:
            assert rule in rules

    def test_get_rules_by_category(self, sample_rules):
        """Test getting rules filtered by category."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        player_rules = manager.get_rules(category="player")

        assert len(player_rules) == 2
        for rule in player_rules:
            assert rule.category == "player"

    def test_get_rules_by_status(self, sample_rules):
        """Test getting rules filtered by status."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        disabled_rules = manager.get_rules(status="disabled")

        assert len(disabled_rules) == 1
        for rule in disabled_rules:
            assert rule.status == "disabled"

    def test_get_rules_by_category_and_status(self, sample_rules):
        """Test getting rules filtered by both category and status."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        general_enabled_rules = manager.get_rules(category="general", status="enabled")

        assert len(general_enabled_rules) == 1
        assert general_enabled_rules[0].category == "general"
        assert general_enabled_rules[0].status == "enabled"

    def test_update_rule(self, sample_rules):
        """Test updating a rule."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        updated_rule = CorrectionRule("UpdatedValue", "general1", "general", "enabled")
        manager.update_rule(4, updated_rule)

        # Check that the rule was updated
        retrieved_rule = manager.get_rule(4)
        assert retrieved_rule.to_value == "UpdatedValue"
        assert retrieved_rule.from_value == "general1"

    def test_delete_rule(self, sample_rules):
        """Test deleting a rule."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        initial_count = len(manager._rules)
        rule_to_delete = manager.get_rule(2)

        manager.delete_rule(2)

        assert len(manager._rules) == initial_count - 1
        assert rule_to_delete not in manager._rules

    def test_move_rule(self, sample_rules):
        """Test moving a rule to change its priority."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # Move the third rule to the first position
        rule_to_move = manager.get_rule(2)
        manager.move_rule(2, 0)

        # Check that the rule is now at the first position
        assert manager.get_rule(0) == rule_to_move

    def test_move_rule_to_top(self, sample_rules):
        """Test moving a rule to the top of its category."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # There are 2 player rules, move the second one to the top
        second_player_rule = manager.get_rule(1)
        manager.move_rule_to_top(1)

        # The rule should now be the first player rule
        player_rules = manager.get_rules(category="player")
        assert player_rules[0] == second_player_rule

    def test_move_rule_to_bottom(self, sample_rules):
        """Test moving a rule to the bottom of its category."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # There are 2 player rules, move the first one to the bottom
        first_player_rule = manager.get_rule(0)
        manager.move_rule_to_bottom(0)

        # The rule should now be the second player rule
        player_rules = manager.get_rules(category="player")
        assert player_rules[-1] == first_player_rule

    def test_toggle_rule_status(self, sample_rules):
        """Test toggling a rule's enabled/disabled status."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # Toggle an enabled rule
        enabled_rule = manager.get_rule(0)
        assert enabled_rule.status == "enabled"

        manager.toggle_rule_status(0)
        assert manager.get_rule(0).status == "disabled"

        # Toggle a disabled rule
        disabled_rule = manager.get_rule(5)
        assert disabled_rule.status == "disabled"

        manager.toggle_rule_status(5)
        assert manager.get_rule(5).status == "enabled"

    def test_get_prioritized_rules(self, sample_rules):
        """Test getting rules sorted by application priority."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        prioritized_rules = manager.get_prioritized_rules()

        # General rules should come first
        assert prioritized_rules[0].category == "general"
        assert prioritized_rules[1].category == "general"

        # Category-specific rules should follow
        # The exact order within categories depends on implementation details
        category_rules = prioritized_rules[2:]
        assert all(rule.category in ["player", "chest_type", "source"] for rule in category_rules)

    def test_save_and_load_rules(self, sample_rules, temp_csv_file):
        """Test saving rules to CSV and loading them back."""
        # Create a manager and add rules
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # Save rules to temporary file
        manager.save_rules(temp_csv_file)

        # Create a new manager and load the rules
        new_manager = CorrectionRuleManager()
        new_manager.load_rules(temp_csv_file)

        # Check that the loaded rules match the original ones
        loaded_rules = new_manager.get_rules()
        assert len(loaded_rules) == len(sample_rules)

        # Check each rule was loaded correctly
        for original_rule in sample_rules:
            assert any(
                original_rule.to_value == loaded_rule.to_value
                and original_rule.from_value == loaded_rule.from_value
                and original_rule.category == loaded_rule.category
                and original_rule.status == loaded_rule.status
                for loaded_rule in loaded_rules
            )

    def test_load_rules_nonexistent_file(self):
        """Test loading rules from a nonexistent file."""
        manager = CorrectionRuleManager()

        # Should not raise an exception, just result in empty rules
        manager.load_rules("nonexistent_file.csv")
        assert manager._rules == []

    def test_save_rules_default_path(self, sample_rules, monkeypatch):
        """Test saving rules to the default path."""
        # Create mock objects
        mock_parent = MagicMock()
        mock_dataframe = MagicMock()

        # Set up monkeypatching
        monkeypatch.setattr(Path, "parent", mock_parent)
        monkeypatch.setattr(pd.DataFrame, "to_csv", MagicMock())

        # Create a new dataframe constructor that returns our mock
        def mock_dataframe_constructor(*args, **kwargs):
            return mock_dataframe

        # Replace the original DataFrame constructor with our mock
        monkeypatch.setattr(pd, "DataFrame", mock_dataframe_constructor)

        # Set up manager and add rules
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # Save rules without specifying a path
        manager.save_rules()

        # Verify that to_csv was called
        assert mock_dataframe.to_csv.called

    def test_get_rules_by_search_term(self, sample_rules):
        """Test getting rules filtered by search term."""
        manager = CorrectionRuleManager()
        for rule in sample_rules:
            manager.add_rule(rule)

        # Add a rule with a specific search term in from_value
        search_rule_from = CorrectionRule(
            "SearchFromResult", "SearchFromTerm", "general", "enabled"
        )
        manager.add_rule(search_rule_from)

        # Add another rule with a specific search term in to_value
        search_rule_to = CorrectionRule("SearchToTerm", "SearchToSource", "general", "enabled")
        manager.add_rule(search_rule_to)

        # Test search in from_value
        result = manager.get_rules(search_term="SearchFrom")
        assert len(result) == 1
        assert result[0].to_value == "SearchFromResult"
        assert result[0].from_value == "SearchFromTerm"

        # Test search in to_value
        result = manager.get_rules(search_term="SearchTo")
        assert len(result) == 1
        assert result[0].to_value == "SearchToTerm"
        assert result[0].from_value == "SearchToSource"

        # Test combining search with category and status
        player_rule = CorrectionRule("PlayerSearch", "PlayerTarget", "player", "enabled")
        manager.add_rule(player_rule)

        result = manager.get_rules(category="player", status="enabled", search_term="Search")
        assert len(result) == 1
        assert result[0].to_value == "PlayerSearch"
        assert result[0].category == "player"
        assert result[0].status == "enabled"
