"""
Example end-to-end test.

This is a sample end-to-end test to demonstrate testing complete workflows.
"""

import pytest
import csv
import json
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal
from tests.utils.helpers import temp_directory, process_events
from tests.data import TestDataFactory


class SimpleData:
    """
    Simple data container for testing.

    Designed to avoid recursion issues when used in signals.
    """

    def __init__(self, data=None):
        """Initialize with simple data."""
        self.data = data or {}

    def copy(self):
        """Create a safe copy of the data."""
        return SimpleData({k: v for k, v in self.data.items()})

    def __repr__(self):
        """String representation for debugging."""
        return f"SimpleData({self.data})"

    def to_csv(self, file_path):
        """Save data to a CSV file."""
        with open(file_path, "w", newline="") as csvfile:
            if not self.data:
                return

            fieldnames = self.data.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            # If the data values are lists, write each row
            if any(isinstance(v, list) for v in self.data.values()):
                # Determine how many rows based on the length of the first list
                num_rows = len(next((v for v in self.data.values() if isinstance(v, list)), []))

                for i in range(num_rows):
                    row = {
                        k: (v[i] if isinstance(v, list) and i < len(v) else v)
                        for k, v in self.data.items()
                    }
                    writer.writerow(row)
            else:
                # Write a single row
                writer.writerow(self.data)

    @classmethod
    def from_csv(cls, file_path):
        """Create instance from a CSV file."""
        data = {}
        try:
            with open(file_path, "r", newline="") as csvfile:
                reader = csv.DictReader(csvfile)

                # Read all rows
                rows = list(reader)

                if not rows:
                    return cls({})

                # If there's only one row, return it directly
                if len(rows) == 1:
                    return cls(dict(rows[0]))

                # Otherwise, organize into columns
                for key in rows[0].keys():
                    data[key] = [row[key] for row in rows]

                return cls(data)
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return cls({})


# This would be the actual application class in a real test
class MockChestBuddyApp(QObject):
    """Mock ChestBuddy application for testing."""

    dataLoaded = Signal(bool)
    dataProcessed = Signal(bool)
    dataExported = Signal(bool)

    def __init__(self):
        """Initialize the mock application."""
        super().__init__()
        self.loaded_data = None
        self.exported_data = None
        self.current_filename = None

    def load_data(self, file_path):
        """Mock loading data from a file."""
        self.current_filename = file_path
        try:
            # Simulate loading data
            self.loaded_data = SimpleData.from_csv(file_path)
            success = True
        except Exception as e:
            print(f"Error loading data: {e}")
            success = False

        self.dataLoaded.emit(success)
        return success

    def export_data(self, file_path):
        """Mock exporting data to a file."""
        if self.loaded_data is None:
            self.dataExported.emit(False)
            return False

        try:
            # Simulate exporting data
            self.loaded_data.to_csv(file_path)
            self.exported_data = file_path
            success = True
        except Exception as e:
            print(f"Error exporting data: {e}")
            success = False

        self.dataExported.emit(success)
        return success

    def process_data(self):
        """Mock processing data."""
        if self.loaded_data is None:
            self.dataProcessed.emit(False)
            return False

        # Simulate processing data
        self.loaded_data.data["processed"] = True

        self.dataProcessed.emit(True)
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
        # Create test data with simple data structure
        data = SimpleData({"id": [1, 2, 3], "value": ["a", "b", "c"]})

        # Save to a CSV file
        file_path = temp_data_dir / "test_data.csv"
        data.to_csv(file_path)

        return file_path

    def test_complete_workflow(self, app, test_data_file):
        """Test a complete data processing workflow."""
        # Setup signal capture
        signal_results = {"loaded": False, "processed": False, "exported": False}

        # Connect signals
        app.dataLoaded.connect(lambda success: signal_results.update({"loaded": success}))
        app.dataProcessed.connect(lambda success: signal_results.update({"processed": success}))
        app.dataExported.connect(lambda success: signal_results.update({"exported": success}))

        # Load data
        assert app.load_data(test_data_file)
        assert app.loaded_data is not None
        assert app.current_filename == test_data_file

        # Process events to allow signals to be delivered
        process_events()

        # Validate data
        is_valid, _ = app.validate_data()
        assert is_valid

        # Process data
        assert app.process_data()
        assert "processed" in app.loaded_data.data

        # Process events
        process_events()

        # Export data
        export_path = Path(test_data_file).parent / "exported_data.csv"
        assert app.export_data(export_path)
        assert export_path.exists()

        # Process events
        process_events()

        # Verify exported data
        exported_data = SimpleData.from_csv(export_path)
        assert "processed" in exported_data.data

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
