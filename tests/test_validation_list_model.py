"""
test_validation_list_model.py

Description: Tests for the ValidationListModel class
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from chestbuddy.core.models.validation_list_model import ValidationListModel


class TestValidationListModel:
    """Tests for the ValidationListModel class."""

    @pytest.fixture
    def temp_validation_file(self, tmp_path):
        """Create a temporary validation file for testing."""
        file_path = tmp_path / "test_validation.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Entry1\nEntry2\nEntry3\n")
        return file_path

    def test_initialization(self, temp_validation_file):
        """Test that model initializes correctly."""
        model = ValidationListModel(temp_validation_file)
        assert model is not None
        assert len(model.get_entries()) == 3
        assert "Entry1" in model.get_entries()
        assert "Entry2" in model.get_entries()
        assert "Entry3" in model.get_entries()

    def test_add_entry(self, temp_validation_file):
        """Test adding an entry to the model."""
        model = ValidationListModel(temp_validation_file)
        initial_count = len(model.get_entries())

        # Add a new entry
        result = model.add_entry("NewEntry")
        assert result is True
        assert len(model.get_entries()) == initial_count + 1
        assert "NewEntry" in model.get_entries()

    def test_add_duplicate_entry(self, temp_validation_file):
        """Test adding a duplicate entry to the model."""
        model = ValidationListModel(temp_validation_file)
        initial_count = len(model.get_entries())

        # Add a duplicate entry
        result = model.add_entry("Entry1")
        assert result is False
        assert len(model.get_entries()) == initial_count

    def test_remove_entry(self, temp_validation_file):
        """Test removing an entry from the model."""
        model = ValidationListModel(temp_validation_file)
        initial_count = len(model.get_entries())

        # Remove an entry
        result = model.remove_entry("Entry1")
        assert result is True
        assert len(model.get_entries()) == initial_count - 1
        assert "Entry1" not in model.get_entries()

    def test_remove_nonexistent_entry(self, temp_validation_file):
        """Test removing a non-existent entry from the model."""
        model = ValidationListModel(temp_validation_file)
        initial_count = len(model.get_entries())

        # Remove a non-existent entry
        result = model.remove_entry("NonExistentEntry")
        assert result is False
        assert len(model.get_entries()) == initial_count

    def test_contains(self, temp_validation_file):
        """Test checking if an entry exists in the model."""
        model = ValidationListModel(temp_validation_file)

        # Check existing entry
        assert model.contains("Entry1") is True

        # Check non-existent entry
        assert model.contains("NonExistentEntry") is False

    def test_case_sensitivity(self, temp_validation_file):
        """Test case sensitivity settings."""
        # Create model with case sensitivity
        model = ValidationListModel(temp_validation_file, case_sensitive=True)

        # Test case-sensitive contains
        assert model.contains("Entry1") is True
        assert model.contains("entry1") is False

        # Set case-insensitive
        model.set_case_sensitive(False)

        # Test case-insensitive contains
        assert model.contains("Entry1") is True
        assert model.contains("entry1") is True

    def test_find_matching_entries(self, temp_validation_file):
        """Test finding entries that match a query string."""
        model = ValidationListModel(temp_validation_file)

        # Add some entries for testing
        model.add_entry("TestEntry")
        model.add_entry("AnotherTest")
        model.add_entry("SomethingElse")

        # Find entries containing "Test"
        matches = model.find_matching_entries("Test")
        assert len(matches) == 2
        assert "TestEntry" in matches
        assert "AnotherTest" in matches

    def test_clear(self, temp_validation_file):
        """Test clearing all entries from the model."""
        model = ValidationListModel(temp_validation_file)
        assert len(model.get_entries()) > 0

        # Clear entries
        result = model.clear()
        assert result is True
        assert len(model.get_entries()) == 0

    def test_refresh(self, temp_validation_file):
        """Test refreshing entries from the file."""
        model = ValidationListModel(temp_validation_file)

        # Modify the file directly
        with open(temp_validation_file, "w", encoding="utf-8") as f:
            f.write("NewEntry1\nNewEntry2\n")

        # Refresh the model
        model.refresh()

        # Check that entries were updated
        entries = model.get_entries()
        assert len(entries) == 2
        assert "NewEntry1" in entries
        assert "NewEntry2" in entries
        assert "Entry1" not in entries

    def test_save_entries(self, temp_validation_file):
        """Test saving entries to the file."""
        model = ValidationListModel(temp_validation_file)

        # Add a new entry
        model.add_entry("NewSavedEntry")

        # Create a new model instance to read from the same file
        new_model = ValidationListModel(temp_validation_file)

        # Check that the new entry was saved
        assert "NewSavedEntry" in new_model.get_entries()
