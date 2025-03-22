"""
Tests for the service classes.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from PySide6.QtCore import QObject

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.core.services.correction_service import CorrectionService


@pytest.fixture
def model():
    """Create a fresh ChestDataModel instance for testing."""
    with patch("PySide6.QtWidgets.QApplication"):
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

    def test_read_csv(self, sample_data, temp_csv_file):
        """Test reading a CSV file."""
        # Save sample data to temp CSV
        sample_data.to_csv(temp_csv_file, index=False)

        # Create service
        service = CSVService()

        # Read CSV
        df, error = service.read_csv(temp_csv_file)

        # Verify reading was successful
        assert df is not None
        assert error is None
        assert not df.empty
        assert len(df) == len(sample_data)

    def test_write_csv(self, sample_data, temp_csv_file):
        """Test writing to a CSV file."""
        # Create service
        service = CSVService()

        # Write CSV
        result, error = service.write_csv(temp_csv_file, sample_data)

        # Verify writing was successful
        assert result is True
        assert error is None
        assert os.path.exists(temp_csv_file)

        # Load the saved file back and verify content
        saved_data = pd.read_csv(temp_csv_file)
        assert len(saved_data) == len(sample_data)
        assert set(saved_data.columns) == set(sample_data.columns)

    def test_csv_preview(self, sample_data, temp_csv_file):
        """Test getting a CSV preview."""
        # Save sample data to temp CSV
        sample_data.to_csv(temp_csv_file, index=False)

        # Create service
        service = CSVService()

        # Get preview
        preview, error = service.get_csv_preview(temp_csv_file, max_rows=2)

        # Verify preview was successful
        assert preview is not None
        assert error is None
        assert len(preview) <= 2


# Validation Service Tests
class TestValidationService:
    """Tests for the ValidationService class."""

    def test_initialization(self, model):
        """Test that service initializes correctly."""
        service = ValidationService(model)
        assert service is not None
        assert len(service._validation_rules) > 0

    def test_add_remove_validation_rule(self, model):
        """Test adding and removing a validation rule."""
        service = ValidationService(model)

        # Define a test rule
        def test_rule(data=None):
            return {}

        # Add rule
        service.add_validation_rule("test_rule", test_rule)
        assert "test_rule" in service._validation_rules

        # Remove rule
        result = service.remove_validation_rule("test_rule")
        assert result is True
        assert "test_rule" not in service._validation_rules

    def test_validate_data(self, model, sample_data):
        """Test validating data."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ValidationService(model)

        # Mock the validation methods to return empty dicts
        with patch.object(service, "_check_missing_values", return_value={}):
            with patch.object(service, "_check_outliers", return_value={}):
                with patch.object(service, "_check_duplicates", return_value={}):
                    with patch.object(service, "_check_data_types", return_value={}):
                        with patch.object(service, "_update_validation_status"):
                            # Validate data
                            results = service.validate_data()

                            # Verify validation returned something
                            assert isinstance(results, dict)

    def test_validate_with_specific_rules(self, model, sample_data):
        """Test validating data with specific rules."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ValidationService(model)

        # Get available rules
        rules = list(service._validation_rules.keys())
        if rules:
            # Mock the validation methods and update_validation_status
            with patch.object(service, "_check_missing_values", return_value={}):
                with patch.object(service, "_check_outliers", return_value={}):
                    with patch.object(service, "_check_duplicates", return_value={}):
                        with patch.object(service, "_check_data_types", return_value={}):
                            with patch.object(service, "_update_validation_status"):
                                # Validate with the first rule only
                                results = service.validate_data(specific_rules=[rules[0]])

                                # Verify validation returned something
                                assert isinstance(results, dict)

    def test_validations(self, model, sample_data):
        """Test specific validation methods."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ValidationService(model)

        # Test missing values check
        missing_issues = service._check_missing_values()
        assert isinstance(missing_issues, dict)

        # Test outliers check
        outlier_issues = service._check_outliers()
        assert isinstance(outlier_issues, dict)

        # Test duplicates check
        duplicate_issues = service._check_duplicates()
        assert isinstance(duplicate_issues, dict)

        # Test data types check
        type_issues = service._check_data_types()
        assert isinstance(type_issues, dict)

    def test_date_parsing_warnings(self, model):
        """Test date parsing functionality in ValidationService."""
        # Create data with dates in different formats and some non-numeric, non-date values
        # to ensure we trigger the datetime parsing branch
        data = pd.DataFrame(
            {
                "numeric_col": [1, 2, 3, 4],  # Numeric column
                "mixed_col": [
                    "text",
                    "1",
                    "2",
                    "3",
                ],  # Mixed types (will not be identified as dates)
                "date_col": [
                    "2023-01-01",
                    "2023/02/02",
                    "01.03.2023",
                    "04/05/2023",
                ],  # Various date formats
                "timestamp_col": [
                    "2023-01-01 10:30:00",
                    "2023-01-02 11:45:00",
                    "2023-01-03 12:15:00",
                    "2023-01-04 14:20:00",
                ],
            }
        )

        # Update model with sample data
        model.update_data(data)

        # Create service
        service = ValidationService(model)

        # Run the method that validates data types
        issues = service._check_data_types()

        # Verify functionality is working correctly for date columns
        # The mixed_col will likely have issues because it contains non-numeric text
        # but date_col and timestamp_col should be recognized as valid dates

        # Check that none of the date rows have issues
        for row_idx in range(4):
            assert (
                row_idx not in issues
                or "date_col" not in issues.get(row_idx, "")
                and "timestamp_col" not in issues.get(row_idx, "")
            )

        # Directly test pd.to_datetime with format='mixed' to ensure it works with our test data
        try:
            result = pd.to_datetime(data["date_col"], format="mixed")
            # Verify all dates were parsed correctly (no NaT values)
            assert not result.isna().any()
        except ValueError as e:
            pytest.fail(f"Failed to parse dates with format='mixed': {e}")

        # Test with dayfirst parameter for format flexibility
        try:
            result = pd.to_datetime(data["date_col"], format="mixed", dayfirst=True)
            # Verify all dates were parsed correctly (no NaT values)
            assert not result.isna().any()
        except ValueError as e:
            pytest.fail(f"Failed to parse dates with format='mixed' and dayfirst=True: {e}")


# Correction Service Tests
class TestCorrectionService:
    """Tests for the CorrectionService class."""

    def test_initialization(self, model):
        """Test that service initializes correctly."""
        service = CorrectionService(model)
        assert service is not None
        assert len(service._correction_strategies) > 0

    def test_add_remove_correction_strategy(self, model):
        """Test adding and removing a correction strategy."""
        service = CorrectionService(model)

        # Define a test strategy with the correct signature
        def test_strategy(column=None, rows=None, **kwargs):
            return True, None

        # Add strategy
        service.add_correction_strategy("test_strategy", test_strategy)
        assert "test_strategy" in service._correction_strategies

        # Remove strategy
        result = service.remove_correction_strategy("test_strategy")
        assert result is True
        assert "test_strategy" not in service._correction_strategies

    def test_apply_correction(self, model, sample_data):
        """Test applying a correction strategy."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = CorrectionService(model)

        # Define a mock strategy with the correct signature
        def mock_strategy(column=None, rows=None, **kwargs):
            # Just return True and None
            return True, None

        # Add the mock strategy
        service.add_correction_strategy("mock_strategy", mock_strategy)

        # Mock the _update_correction_status method
        with patch.object(service, "_update_correction_status"):
            # Apply the mock strategy
            result, message = service.apply_correction("mock_strategy")

            # Verify correction was successful
            assert result is True
            assert message is None

    def test_correction_history(self, model, sample_data):
        """Test correction history tracking."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = CorrectionService(model)

        # Check initial history
        assert service._correction_history == []

        # Define a mock strategy that will be added to history
        def mock_strategy(column=None, rows=None, **kwargs):
            # Just return True and None
            return True, None

        # Add the mock strategy
        service.add_correction_strategy("mock_strategy", mock_strategy)

        # Mock the _update_correction_status and _record_correction methods
        with patch.object(service, "_update_correction_status"):
            with patch.object(service, "_record_correction") as mock_record:
                # Apply the mock strategy
                service.apply_correction("mock_strategy")

                # Verify record_correction was called
                mock_record.assert_called_once()
