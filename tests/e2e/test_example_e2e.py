"""
Example end-to-end test.

This is a sample end-to-end test to demonstrate testing complete workflows.
"""

import pytest
import pandas as pd
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox
from tests.utils.helpers import temp_directory
from tests.data import TestDataFactory


# This would be the actual application class in a real test
class MockChestBuddyApp(QMainWindow):
    """Mock ChestBuddy application for testing."""

    def __init__(self):
        """Initialize the mock application."""
        super().__init__()
        self.loaded_data = None
        self.exported_data = None
        self.current_filename = None

    def load_data(self, file_path):
        """Mock loading data from a file."""
        self.current_filename = file_path
        # Simulate loading data
        self.loaded_data = pd.read_csv(file_path)
        return True

    def export_data(self, file_path):
        """Mock exporting data to a file."""
        if self.loaded_data is None:
            return False

        # Simulate exporting data
        self.loaded_data.to_csv(file_path, index=False)
        self.exported_data = file_path
        return True

    def process_data(self):
        """Mock processing data."""
        if self.loaded_data is None:
            return False

        # Simulate processing data
        self.loaded_data["processed"] = True
        return True

    def validate_data(self):
        """Mock data validation."""
        if self.loaded_data is None:
            return False, "No data loaded"

        # Simulate validation
        return True, "Data validated successfully"


@pytest.mark.e2e
class TestWorkflows:
    """Test end-to-end workflows."""

    @pytest.fixture
    def app(self):
        """Create a mock application for testing."""
        return MockChestBuddyApp()

    @pytest.fixture
    def test_data_file(self, temp_data_dir):
        """Create a test data file."""
        # Create test data
        data = TestDataFactory.create_small_data()

        # Save to a CSV file
        file_path = temp_data_dir / "test_data.csv"
        data.to_csv(file_path, index=False)

        return file_path

    def test_complete_workflow(self, app, test_data_file):
        """Test a complete data processing workflow."""
        # Load data
        assert app.load_data(test_data_file)
        assert app.loaded_data is not None
        assert app.current_filename == test_data_file

        # Validate data
        is_valid, _ = app.validate_data()
        assert is_valid

        # Process data
        assert app.process_data()
        assert "processed" in app.loaded_data.columns

        # Export data
        export_path = Path(test_data_file).parent / "exported_data.csv"
        assert app.export_data(export_path)
        assert export_path.exists()

        # Verify exported data
        exported_data = pd.read_csv(export_path)
        assert "processed" in exported_data.columns
        assert len(exported_data) == len(app.loaded_data)

    def test_error_handling_workflow(self, app):
        """Test error handling in the workflow."""
        # Try to process without loading data
        assert not app.process_data()

        # Try to validate without loading data
        is_valid, message = app.validate_data()
        assert not is_valid
        assert message == "No data loaded"

        # Try to export without loading data
        assert not app.export_data("nonexistent_file.csv")
