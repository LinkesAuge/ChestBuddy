"""
Example integration test that demonstrates component interaction.
"""

import pytest
from PySide6.QtCore import QObject, Signal, Slot, QCoreApplication, QTimer, QEventLoop
from typing import Any, Dict, List, Optional


class SimpleData:
    """
    Simple data container that avoids recursion issues.

    Properly implements copy to avoid recursion problems when
    used in signals.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Initialize with simple data."""
        self.data = data or {}

    def copy(self):
        """Create a safe copy of the data."""
        return SimpleData({k: v for k, v in self.data.items()})

    def __repr__(self):
        """String representation for debugging."""
        return f"SimpleData({self.data})"


class DataModel(QObject):
    """Example data model component."""

    # Signal emitted when data changes
    dataChanged = Signal(object)

    def __init__(self):
        """Initialize the data model."""
        super().__init__()
        self._data = None

    def set_data(self, data):
        """Set the data and emit signal."""
        self._data = data
        self.dataChanged.emit(data)

    def get_data(self):
        """Get the current data."""
        return self._data


class DataService(QObject):
    """Example service component."""

    # Signal emitted when processing completes
    processingComplete = Signal(object)

    def __init__(self):
        """Initialize the service."""
        super().__init__()

    def process_data(self, data):
        """Process data and emit result."""
        # Create a copy to avoid reference issues
        result = SimpleData(data.data.copy())

        # Add processed flag
        result.data["processed"] = True

        # Emit the processing complete signal
        self.processingComplete.emit(result)
        return result


class Controller(QObject):
    """Example controller component that connects model and service."""

    def __init__(self, model, service):
        """Initialize with model and service."""
        super().__init__()
        self.model = model
        self.service = service
        self._connections = []

        # Connect signals
        self._setup_connections()

    def _setup_connections(self):
        """Set up signal connections with tracking."""
        # Connect model to service
        connection = self.model.dataChanged.connect(self.on_data_changed)
        self._connections.append(connection)

        # Connect service back to model
        connection = self.service.processingComplete.connect(self.on_processing_complete)
        self._connections.append(connection)

    def on_data_changed(self, data):
        """Handle data changed in model."""
        self.service.process_data(data)

    def on_processing_complete(self, result):
        """Handle processing complete from service."""
        pass  # In a real application, this would update the model or UI

    def cleanup(self):
        """Disconnect all signals."""
        for connection in self._connections:
            QObject.disconnect(connection)
        self._connections.clear()

    def __del__(self):
        """Clean up on deletion."""
        self.cleanup()


def process_events():
    """Process Qt events to allow signals to be delivered."""
    QCoreApplication.processEvents()


def wait_for_signal(signal, timeout=1000):
    """
    Wait for a signal to be emitted.

    Args:
        signal: The Qt signal to wait for
        timeout: Maximum time to wait in milliseconds

    Returns:
        Dict with 'success' (bool) and 'args' (list of emitted args if success)
    """
    loop = QEventLoop()
    result = {"success": False, "args": []}

    # Setup timer for timeout
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)

    # Connect the signal
    def signal_handler(*args):
        result["success"] = True
        result["args"] = args
        loop.quit()

    connection = signal.connect(signal_handler)

    # Start the timer and event loop
    timer.start(timeout)
    loop.exec()

    # Cleanup
    signal.disconnect(connection)

    return result


class MockDataService(DataService):
    """Mocked data service for testing."""

    def process_data(self, data):
        """Mock implementation that emits a fixed result."""
        # Using simple data with a literal dictionary
        result = SimpleData({"mocked": True})
        # Make sure to emit the signal!
        self.processingComplete.emit(result)
        return result


@pytest.fixture
def mock_service():
    """Fixture that provides a mocked service."""
    return MockDataService()


@pytest.mark.integration
class TestComponentIntegration:
    """Test integration between components."""

    def test_data_flow_between_components(self):
        """Test that data flows correctly between model, service, and controller."""
        # Create the components
        model = DataModel()
        service = DataService()
        controller = Controller(model, service)

        try:
            # Track service processing completion
            processed_results = []

            # Connect to the service's output signal
            def on_processing_complete(result):
                processed_results.append(result)

            connection = service.processingComplete.connect(on_processing_complete)

            # Set initial data with simple values
            initial_data = SimpleData({"id": 1, "value": "test"})

            # Trigger the chain of events
            model.set_data(initial_data)

            # Process events to allow signals to be delivered
            process_events()

            # Check that data was processed
            assert len(processed_results) == 1, (
                f"Expected 1 processed result, got {len(processed_results)}"
            )

            # Verify result content
            result = processed_results[0]
            assert isinstance(result, SimpleData)
            assert result.data["id"] == 1
            assert result.data["value"] == "test"
            assert result.data["processed"] is True

            # Clean up connection
            service.processingComplete.disconnect(connection)

        finally:
            # Clean up controller connections
            controller.cleanup()

    def test_with_mocked_service(self, mock_service):
        """Test controller with a mocked service."""
        # Create model and controller with the mocked service
        model = DataModel()
        controller = Controller(model, mock_service)

        try:
            # Track processing completion
            processed_results = []

            # Connect to the service's output signal
            def on_processing_complete(result):
                processed_results.append(result)

            connection = mock_service.processingComplete.connect(on_processing_complete)

            # Set initial data with simple values
            initial_data = SimpleData({"id": 1})

            # Trigger the event
            model.set_data(initial_data)

            # Process events to allow signals to be delivered
            process_events()

            # Check that mock service processed the data
            assert len(processed_results) == 1, (
                f"Expected 1 processed result, got {len(processed_results)}"
            )

            # Verify mocked result
            result = processed_results[0]
            assert isinstance(result, SimpleData)
            assert result.data.get("mocked") is True

            # Clean up connection
            mock_service.processingComplete.disconnect(connection)

        finally:
            # Clean up controller connections
            controller.cleanup()
