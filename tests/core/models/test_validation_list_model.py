"""
test_validation_list_model.py

Description: Tests for the ValidationListModel class
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QObject

from chestbuddy.core.models.validation_list_model import ValidationListModel


@pytest.fixture
def temp_validation_file(tmp_path):
    """Create a temporary validation file for testing."""
    file_path = tmp_path / "test_validation.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Entry1\nEntry2\nEntry3\n")
    return file_path


@pytest.fixture
def validation_model(temp_validation_file):
    """Create a ValidationListModel instance for testing."""
    return ValidationListModel(str(temp_validation_file))


def test_initialization(validation_model):
    """Test that the model initializes correctly."""
    assert isinstance(validation_model, QObject)
    assert len(validation_model.get_entries()) == 3
    assert "Entry1" in validation_model.get_entries()


def test_duplicate_entry_case_sensitive(validation_model):
    """Test duplicate entry detection with case sensitivity."""
    validation_model.set_case_sensitive(True)

    # Test exact duplicate
    assert validation_model._is_duplicate_entry("Entry1")
    assert not validation_model._is_duplicate_entry("entry1")

    # Test adding duplicate
    assert not validation_model.add_entry("Entry1")
    assert validation_model.add_entry("entry1")


def test_duplicate_entry_case_insensitive(validation_model):
    """Test duplicate entry detection without case sensitivity."""
    validation_model.set_case_sensitive(False)

    # Test exact and case-insensitive duplicates
    assert validation_model._is_duplicate_entry("Entry1")
    assert validation_model._is_duplicate_entry("entry1")
    assert validation_model._is_duplicate_entry("ENTRY1")

    # Test adding duplicates
    assert not validation_model.add_entry("Entry1")
    assert not validation_model.add_entry("entry1")
    assert not validation_model.add_entry("ENTRY1")


def test_import_file_no_duplicates(tmp_path, validation_model):
    """Test importing a file with no duplicate entries."""
    # Create test import file
    import_file = tmp_path / "import.txt"
    with open(import_file, "w", encoding="utf-8") as f:
        f.write("NewEntry1\nNewEntry2\nNewEntry3\n")

    # Import file
    success, duplicates = validation_model.import_from_file(import_file)

    assert success
    assert not duplicates
    assert len(validation_model.get_entries()) == 3
    assert "NewEntry1" in validation_model.get_entries()
    assert "NewEntry2" in validation_model.get_entries()
    assert "NewEntry3" in validation_model.get_entries()


def test_import_file_with_duplicates(tmp_path, validation_model):
    """Test importing a file with duplicate entries."""
    # Create test import file with duplicates
    import_file = tmp_path / "import.txt"
    with open(import_file, "w", encoding="utf-8") as f:
        f.write("Entry1\nNewEntry1\nEntry2\n")

    # Import file
    success, duplicates = validation_model.import_from_file(import_file)

    assert not success
    assert len(duplicates) == 2
    assert "Entry1" in duplicates
    assert "Entry2" in duplicates
    # Original entries should remain unchanged
    assert len(validation_model.get_entries()) == 3
    assert "Entry1" in validation_model.get_entries()


def test_export_file(tmp_path, validation_model):
    """Test exporting entries to a file."""
    # Export to new file
    export_file = tmp_path / "export.txt"
    success = validation_model.export_to_file(export_file)

    assert success
    assert export_file.exists()

    # Verify file contents
    with open(export_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 3
    assert "Entry1\n" in lines
    assert "Entry2\n" in lines
    assert "Entry3\n" in lines


def test_export_file_sorted(tmp_path, validation_model):
    """Test that exported entries are sorted alphabetically."""
    # Add entries in non-alphabetical order
    validation_model.add_entry("ZEntry")
    validation_model.add_entry("AEntry")

    # Export to file
    export_file = tmp_path / "export.txt"
    validation_model.export_to_file(export_file)

    # Read file and verify order
    with open(export_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Convert to list of stripped strings for easier comparison
    entries = [line.strip() for line in lines]
    sorted_entries = sorted(entries)

    assert entries == sorted_entries


def test_import_empty_file(tmp_path, validation_model):
    """Test importing an empty file."""
    # Create empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()

    # Import file
    success, duplicates = validation_model.import_from_file(empty_file)

    assert success
    assert not duplicates
    assert len(validation_model.get_entries()) == 0


def test_import_whitespace_handling(tmp_path, validation_model):
    """Test importing a file with whitespace and empty lines."""
    # Create test file with whitespace and empty lines
    import_file = tmp_path / "whitespace.txt"
    with open(import_file, "w", encoding="utf-8") as f:
        f.write("\n  NewEntry1  \n\nNewEntry2\n  \n")

    # Import file
    success, duplicates = validation_model.import_from_file(import_file)

    assert success
    assert not duplicates
    entries = validation_model.get_entries()
    assert len(entries) == 2
    assert "NewEntry1" in entries  # Should be stripped
    assert "NewEntry2" in entries


def test_export_to_nonexistent_directory(tmp_path, validation_model):
    """Test exporting to a file in a nonexistent directory."""
    export_file = tmp_path / "nonexistent" / "export.txt"
    success = validation_model.export_to_file(export_file)

    assert success
    assert export_file.exists()
    assert len(list(export_file.read_text().splitlines())) == 3
