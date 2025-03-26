"""
test_validation_list_model.py

Description: Tests for the ValidationListModel class
"""

import pytest
from pathlib import Path
import os

from chestbuddy.core.models.validation_list_model import ValidationListModel


class TestValidationListModel:
    """Tests for the ValidationListModel class."""

    @pytest.fixture
    def tmp_validation_file(self, tmp_path):
        """Create a temporary validation file for testing."""
        validation_file = tmp_path / "test_validation.txt"
        with open(validation_file, "w") as f:
            f.write("Entry1\nEntry2\nEntry3\n")
        return validation_file

    def test_initialization(self, tmp_validation_file):
        """Test that the model initializes correctly."""
        model = ValidationListModel(tmp_validation_file)

        # Check that the model loaded the entries
        assert model is not None
        assert len(model.get_entries()) == 3
        assert "Entry1" in model.get_entries()
        assert "Entry2" in model.get_entries()
        assert "Entry3" in model.get_entries()

    def test_add_entry(self, tmp_validation_file):
        """Test adding entries to the validation list."""
        model = ValidationListModel(tmp_validation_file)

        # Add new entry
        assert model.add_entry("NewEntry") is True
        assert "NewEntry" in model.get_entries()
        assert len(model.get_entries()) == 4

        # Try adding duplicate
        assert model.add_entry("Entry1") is False
        assert len(model.get_entries()) == 4

    def test_remove_entry(self, tmp_validation_file):
        """Test removing entries from the validation list."""
        model = ValidationListModel(tmp_validation_file)

        # Remove entry
        assert model.remove_entry("Entry2") is True
        assert "Entry2" not in model.get_entries()
        assert len(model.get_entries()) == 2

        # Try removing non-existent entry
        assert model.remove_entry("NonExistent") is False
        assert len(model.get_entries()) == 2

    def test_contains(self, tmp_validation_file):
        """Test checking if entries exist in the validation list."""
        model = ValidationListModel(tmp_validation_file)

        # Check existing entry
        assert model.contains("Entry1") is True
        assert model.contains("NonExistent") is False

        # Test case sensitivity
        model.set_case_sensitive(False)
        assert model.contains("entry1") is True

        model.set_case_sensitive(True)
        assert model.contains("entry1") is False
        assert model.contains("Entry1") is True

    def test_find_matching_entries(self, tmp_validation_file):
        """Test finding entries that match a query."""
        model = ValidationListModel(tmp_validation_file)

        # Add more entries for testing
        model.add_entry("TestEntry")
        model.add_entry("TestValue")
        model.add_entry("SampleEntry")

        # Test finding entries
        results = model.find_matching_entries("Entry")
        assert len(results) == 5  # Entry1, Entry2, Entry3, TestEntry, SampleEntry
        assert "Entry1" in results
        assert "Entry2" in results
        assert "Entry3" in results
        assert "TestEntry" in results
        assert "SampleEntry" in results

        # Test case sensitivity in search
        model.set_case_sensitive(True)
        assert len(model.find_matching_entries("entry")) == 0
        assert len(model.find_matching_entries("Entry")) == 5

    def test_save_entries(self, tmp_validation_file):
        """Test saving entries to the validation file."""
        model = ValidationListModel(tmp_validation_file)

        # Modify entries
        model.add_entry("NewEntry")
        model.remove_entry("Entry2")

        # Save changes
        assert model.save_entries() is True

        # Create a new model with the same file to verify changes persisted
        new_model = ValidationListModel(tmp_validation_file)
        entries = new_model.get_entries()

        assert len(entries) == 3
        assert "Entry1" in entries
        assert "Entry3" in entries
        assert "NewEntry" in entries
        assert "Entry2" not in entries
