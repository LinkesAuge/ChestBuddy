"""
Tests for the service classes.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService


@pytest.fixture
def model():
    """Create a fresh ChestDataModel instance for testing."""
    model = ChestDataModel()
    model.initialize()
    return model


@pytest.fixture
def sample_data():
    """Create sample data for testing that matches our input file structure."""
    return pd.DataFrame(
        {
            "Date": ["2025-03-11", "2025-03-11", "2025-03-11", "2025-03-12"],
            "Player Name": ["Feldjäger", "Krümelmonster", "OsmanlıTorunu", "D4rkBlizZ4rD"],
            "Source/Location": [
                "Level 25 Crypt",
                "Level 20 Crypt",
                "Level 15 rare Crypt",
                "Level 30 rare Crypt",
            ],
            "Chest Type": [
                "Fire Chest",
                "Infernal Chest",
                "Rare Dragon Chest",
                "Ancient Bastion Chest",
            ],
            "Value": [275, 84, 350, 550],
            "Clan": ["MY_CLAN", "MY_CLAN", "MY_CLAN", "MY_CLAN"],
        }
    )


@pytest.fixture
def validation_lists_dir():
    """Path to validation lists directory for testing."""
    return Path("data/validation")


@pytest.fixture
def corrections_file():
    """Path to standard corrections file for testing."""
    return Path("data/corrections/standard_corrections.csv")


@pytest.fixture
def input_file():
    """Path to the default input file for testing."""
    return Path("data/input/Chests_input_test.csv")


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
        temp_file_path = temp_file.name

    # Clean up the file after the test
    yield temp_file_path
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


# CSV Service Tests
class TestCSVService:
    """Tests for the CSVService class."""

    def test_initialization(self):
        """Test that service initializes correctly."""
        service = CSVService()
        assert service is not None

    def test_read_csv(self, model, sample_data, temp_csv_file):
        """Test reading a CSV file."""
        # Save sample data to temp CSV
        sample_data.to_csv(temp_csv_file, index=False)

        # Create service
        service = CSVService()

        # Read CSV
        success = service.read_csv(model, temp_csv_file)

        # Verify reading was successful
        assert success
        assert not model.is_empty
        assert model.row_count == len(sample_data)

    def test_write_csv(self, model, sample_data, temp_csv_file):
        """Test writing to a CSV file."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = CSVService()

        # Write CSV
        success = service.write_csv(model, temp_csv_file)

        # Verify writing was successful
        assert success
        assert os.path.exists(temp_csv_file)

        # Load the saved file back and verify content
        saved_data = pd.read_csv(temp_csv_file)
        assert len(saved_data) == len(sample_data)
        assert set(saved_data.columns) == set(sample_data.columns)

    def test_export_validation_issues(self, model, sample_data, temp_csv_file):
        """Test exporting validation issues."""
        # Update model with sample data
        model.update_data(sample_data)

        # Add validation issues
        validation_df = pd.DataFrame(index=model._data.index)
        for col in model.EXPECTED_COLUMNS:
            validation_df[f"{col}_valid"] = True
        validation_df.at[0, "Value_valid"] = False
        model.set_validation_status(validation_df)

        # Create service
        service = CSVService()

        # Export validation issues
        success = service.export_validation_issues(model, temp_csv_file)

        # Verify export was successful
        assert success
        assert os.path.exists(temp_csv_file)


# Validation Service Tests
class TestValidationService:
    """Tests for the ValidationService class."""

    def test_initialization(self, model):
        """Test that service initializes correctly."""
        service = ValidationService(model)
        assert service is not None
        assert len(service._validation_rules) > 0

    def test_load_validation_lists(self, model, validation_lists_dir):
        """Test loading validation lists."""
        if not validation_lists_dir.exists():
            pytest.skip("Validation lists directory not found")

        service = ValidationService(model)

        # Check if validation lists exist
        chest_types_file = validation_lists_dir / "chest_types.txt"
        players_file = validation_lists_dir / "players.txt"
        sources_file = validation_lists_dir / "sources.txt"

        if chest_types_file.exists() and players_file.exists() and sources_file.exists():
            # Load validation lists
            service.load_validation_lists(
                str(chest_types_file), str(players_file), str(sources_file)
            )

            # Check if they were loaded
            assert len(service.chest_types) > 0
            assert len(service.player_names) > 0
            assert len(service.source_locations) > 0

    def test_validate_data(self, model, sample_data):
        """Test validating data."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ValidationService(model)

        # Validate data
        results = service.validate_data()

        # Verify validation worked
        assert isinstance(results, dict)
        assert "total_issues" in results
        assert "rules_applied" in results

    def test_validate_with_specific_rules(self, model, sample_data):
        """Test validating data with specific rules."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ValidationService(model)

        # Get available rules
        rules = list(service._validation_rules.keys())
        if rules:
            # Validate with the first rule only
            results = service.validate_data(specific_rules=[rules[0]])

            # Verify validation worked
            assert isinstance(results, dict)
            assert "total_issues" in results
            assert "rules_applied" in results
            assert results["rules_applied"] == 1


# Correction Service Tests
class TestCorrectionService:
    """Tests for the CorrectionService class."""

    def test_initialization(self, model):
        """Test that service initializes correctly."""
        service = CorrectionService(model)
        assert service is not None
        assert len(service._correction_strategies) > 0

    def test_load_corrections(self, model, corrections_file):
        """Test loading corrections from file."""
        if not corrections_file.exists():
            pytest.skip("Corrections file not found")

        # Create service
        service = CorrectionService(model)

        # Load corrections
        success = service.load_corrections(str(corrections_file))

        # Verify loading was successful
        assert success
        assert len(service.corrections) > 0

    def test_apply_corrections(self, model, sample_data):
        """Test applying corrections to data."""
        # Update model with sample data
        model.update_data(sample_data)

        # Add validation issues
        validation_df = pd.DataFrame(index=model._data.index)
        for col in model.EXPECTED_COLUMNS:
            validation_df[f"{col}_valid"] = True
        validation_df.at[0, "Value_valid"] = False
        model.set_validation_status(validation_df)

        # Create service
        service = CorrectionService(model)

        # Apply a specific correction strategy
        result, _ = service.apply_correction("fill_missing_mean", "Value")

        # Verify corrections were applied
        assert result is True

    def test_multiple_correction_strategies(self, model, sample_data):
        """Test applying multiple correction strategies."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = CorrectionService(model)

        # Create a row with missing value
        new_row = {
            "Date": "2025-03-13",
            "Player Name": "NewPlayer",
            "Source/Location": "Level 35 epic Crypt",
            "Chest Type": "Golden Chest",
            "Value": None,  # Missing value
            "Clan": "MY_CLAN",
        }
        model.add_row(new_row)

        # Apply fill_missing_mean strategy
        result, _ = service.apply_correction("fill_missing_mean", "Value")

        # Verify correction was applied
        assert result is True

        # Check if the value was updated
        filled_row = model.get_row(model.row_count - 1)
        assert not pd.isna(filled_row["Value"])

    def test_correction_history(self, model, sample_data):
        """Test correction history tracking."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = CorrectionService(model)

        # Apply a correction
        service.apply_correction("fill_missing_mean", "Value")

        # Get correction history
        history = service.get_correction_history()

        # Verify history is tracked
        assert len(history) > 0
        assert "strategy" in history[0]
        assert history[0]["strategy"] == "fill_missing_mean"
