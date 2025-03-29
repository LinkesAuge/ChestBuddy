"""
Example integration test.

This is a sample integration test to demonstrate testing component interactions.
"""

import pytest
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot


class DataModel(QObject):
    """Example data model."""

    dataChanged = Signal(pd.DataFrame)

    def __init__(self):
        """Initialize the model."""
        super().__init__()
        self._data = pd.DataFrame()

    def set_data(self, data: pd.DataFrame):
        """Set the data and notify observers."""
        self._data = data
        self.dataChanged.emit(data)

    def get_data(self) -> pd.DataFrame:
        """Get the current data."""
        return self._data


class DataService(QObject):
    """Example service for processing data."""

    processingComplete = Signal(pd.DataFrame)

    def __init__(self):
        """Initialize the service."""
        super().__init__()

    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process the data and return the result."""
        # Simple processing: add a column
        result = data.copy()
        result["processed"] = True
        self.processingComplete.emit(result)
        return result


class Controller(QObject):
    """Example controller that connects model and service."""

    def __init__(self, model: DataModel, service: DataService):
        """Initialize the controller."""
        super().__init__()
        self.model = model
        self.service = service

        # Connect signals and slots
        self.model.dataChanged.connect(self.on_data_changed)
        self.service.processingComplete.connect(self.on_processing_complete)

    @Slot(pd.DataFrame)
    def on_data_changed(self, data: pd.DataFrame):
        """Handle data changes from the model."""
        self.service.process_data(data)

    @Slot(pd.DataFrame)
    def on_processing_complete(self, processed_data: pd.DataFrame):
        """Handle processed data from the service."""
        self.model.set_data(processed_data)


@pytest.mark.integration
class TestComponentIntegration:
    """Test interactions between components."""

    def test_data_flow_between_components(self):
        """Test that data flows correctly between model, service, and controller."""
        # Create the components
        model = DataModel()
        service = DataService()
        controller = Controller(model, service)

        # Need to monitor signals
        processed_data_received = []

        # Connect to a test slot
        def on_data_changed(data):
            processed_data_received.append(data)

        model.dataChanged.connect(on_data_changed)

        # Set initial data
        initial_data = pd.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})

        # Trigger the chain of events
        model.set_data(initial_data)

        # Check that we received processed data
        assert len(processed_data_received) == 2  # Initial data + processed data

        # Verify the data was processed correctly
        final_data = processed_data_received[-1]
        assert "processed" in final_data.columns
        assert all(final_data["processed"])

    def test_with_mocked_service(self, mocker):
        """Test controller with a mocked service."""
        # Create model and mock service
        model = DataModel()
        service = DataService()

        # Mock the process_data method
        mock_process = mocker.patch.object(
            service, "process_data", side_effect=lambda x: pd.DataFrame({"mocked": True})
        )

        # Create controller with the mocked service
        controller = Controller(model, service)

        # Set initial data
        initial_data = pd.DataFrame({"id": [1, 2, 3]})
        model.set_data(initial_data)

        # Check that the mock was called with the correct argument
        mock_process.assert_called_once()
        pd.testing.assert_frame_equal(mock_process.call_args[0][0], initial_data)
