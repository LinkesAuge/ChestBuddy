"""
Tests for verifying that the default files can be loaded correctly.
"""

import pytest
from pathlib import Path

import pandas as pd

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService


@pytest.fixture
def data_model():
    """Create a ChestDataModel instance for testing."""
    model = ChestDataModel()
    model.initialize()
    return model


@pytest.fixture
def csv_service():
    """Create a CSVService instance for testing."""
    return CSVService()


@pytest.fixture
def validation_service(data_model):
    """Create a ValidationService instance for testing."""
    return ValidationService(data_model)


@pytest.fixture
def correction_service(data_model):
    """Create a CorrectionService instance for testing."""
    return CorrectionService(data_model)


@pytest.fixture
def default_input_file():
    """Path to the default input file for testing."""
    return Path("data/input/Chests_input_test.csv")


@pytest.fixture
def validation_lists_dir():
    """Path to validation lists directory for testing."""
    return Path("data/validation")


@pytest.fixture
def corrections_file():
    """Path to standard corrections file for testing."""
    return Path("data/corrections/standard_corrections.csv")


def test_load_default_input_file(data_model, csv_service, default_input_file):
    """Test loading the default input file."""
    if not default_input_file.exists():
        pytest.skip(f"Default input file not found: {default_input_file}")

    # Load the file
    success = csv_service.read_csv(data_model, str(default_input_file))

    # Verify loading was successful
    assert success
    assert not data_model.is_empty
    assert data_model.row_count > 0

    # Verify expected columns
    expected_columns = {"Date", "Player Name", "Source/Location", "Chest Type", "Value", "Clan"}
    assert set(data_model.column_names) == expected_columns


def test_load_validation_lists(validation_service, validation_lists_dir):
    """Test loading the validation lists."""
    if not validation_lists_dir.exists():
        pytest.skip(f"Validation lists directory not found: {validation_lists_dir}")

    # Check for the validation list files
    chest_types_file = validation_lists_dir / "chest_types.txt"
    players_file = validation_lists_dir / "players.txt"
    sources_file = validation_lists_dir / "sources.txt"

    if not (chest_types_file.exists() and players_file.exists() and sources_file.exists()):
        pytest.skip("One or more validation list files not found")

    # Load the validation lists
    success = validation_service.load_validation_lists(
        str(chest_types_file), str(players_file), str(sources_file)
    )

    # Verify loading was successful
    assert success
    assert len(validation_service.chest_types) > 0
    assert len(validation_service.player_names) > 0
    assert len(validation_service.source_locations) > 0


def test_load_correction_list(correction_service, corrections_file):
    """Test loading the correction list."""
    if not corrections_file.exists():
        pytest.skip(f"Corrections file not found: {corrections_file}")

    # Load the corrections
    success = correction_service.load_corrections(str(corrections_file))

    # Verify loading was successful
    assert success
    assert len(correction_service.corrections) > 0


def test_validate_with_default_files(
    data_model, csv_service, validation_service, default_input_file, validation_lists_dir
):
    """Test validating data with default files."""
    if not default_input_file.exists():
        pytest.skip(f"Default input file not found: {default_input_file}")

    if not validation_lists_dir.exists():
        pytest.skip(f"Validation lists directory not found: {validation_lists_dir}")

    # Check for the validation list files
    chest_types_file = validation_lists_dir / "chest_types.txt"
    players_file = validation_lists_dir / "players.txt"
    sources_file = validation_lists_dir / "sources.txt"

    if not (chest_types_file.exists() and players_file.exists() and sources_file.exists()):
        pytest.skip("One or more validation list files not found")

    # Load the input file
    success = csv_service.read_csv(data_model, str(default_input_file))
    assert success

    # Load the validation lists
    success = validation_service.load_validation_lists(
        str(chest_types_file), str(players_file), str(sources_file)
    )
    assert success

    # Validate the data
    results = validation_service.validate_data()

    # Verify validation worked
    assert isinstance(results, dict)
    assert "total_issues" in results
    assert "rules_applied" in results


def test_apply_corrections_with_default_files(
    data_model, csv_service, correction_service, default_input_file, corrections_file
):
    """Test applying corrections with default files."""
    if not default_input_file.exists():
        pytest.skip(f"Default input file not found: {default_input_file}")

    if not corrections_file.exists():
        pytest.skip(f"Corrections file not found: {corrections_file}")

    # Load the input file
    success = csv_service.read_csv(data_model, str(default_input_file))
    assert success

    # Load the corrections
    success = correction_service.load_corrections(str(corrections_file))
    assert success

    # Modify a row to test correction
    row_index = 0
    original_row = data_model.get_row(row_index)
    if "Krümelmonster" in data_model.get_unique_values("Player Name"):
        # Find a row with Krümelmonster
        for i in range(data_model.row_count):
            row = data_model.get_row(i)
            if row["Player Name"] == "Krümelmonster":
                row_index = i
                original_row = row
                break

        # Change it to a value that should be corrected
        modified_row = original_row.copy()
        modified_row["Player Name"] = "Krimelmonster"  # This should be in the correction list
        data_model.update_row(row_index, modified_row)

        # Apply corrections
        correction_service.apply_automatic_corrections()

        # Verify corrections were applied
        corrected_row = data_model.get_row(row_index)
        assert corrected_row["Player Name"] == "Krümelmonster"
