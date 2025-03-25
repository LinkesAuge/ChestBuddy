"""
test_signal_integration.py

Description: Tests for signal integration between controllers and SignalManager
Usage:
    pytest tests/core/test_signal_integration.py
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal, Slot

from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.core.controllers.base_controller import BaseController


# Mock classes for testing
class MockModel(QObject):
    """Mock model for testing signal integration."""

    data_changed = Signal(object)
    validation_complete = Signal(dict)


class MockView(QObject):
    """Mock view for testing signal integration."""

    filter_changed = Signal(str)
    sort_changed = Signal(object)
    selection_changed = Signal(object)


class TestController(BaseController):
    """Controller class for testing signal integration."""

    # Define signals
    filtered_data_changed = Signal(object)
    validation_result = Signal(dict)

    def __init__(self, model, signal_manager):
        """Initialize test controller."""
        super().__init__(signal_manager)
        self._model = model
        self._filter_text = ""

    def connect_to_model(self, model):
        """Connect to model signals."""
        super().connect_to_model(model)

        # Connect to model signals
        self._signal_manager.connect(model, "data_changed", self, "_on_data_changed")
        self._signal_manager.connect(model, "validation_complete", self, "_on_validation_complete")

    def connect_to_view(self, view):
        """Connect to view signals."""
        super().connect_to_view(view)

        # Connect to view signals
        self._signal_manager.connect(view, "filter_changed", self, "_on_filter_changed")
        self._signal_manager.connect(view, "sort_changed", self, "_on_sort_changed")

    @Slot(object)
    def _on_data_changed(self, data):
        """Handle data changed signal."""
        # Apply filter if needed
        if self._filter_text:
            # Mock filtered data
            filtered_data = f"Filtered: {data}"
            self.filtered_data_changed.emit(filtered_data)
        else:
            self.filtered_data_changed.emit(data)

    @Slot(dict)
    def _on_validation_complete(self, results):
        """Handle validation complete signal."""
        self.validation_result.emit(results)

    @Slot(str)
    def _on_filter_changed(self, filter_text):
        """Handle filter changed signal."""
        self._filter_text = filter_text
        # Re-apply filter with current data
        self._on_data_changed(
            self._model.current_data if hasattr(self._model, "current_data") else None
        )

    @Slot(object)
    def _on_sort_changed(self, sort_criteria):
        """Handle sort changed signal."""
        # Implementation not needed for this test
        pass


# Test fixtures
@pytest.fixture
def signal_manager():
    """Create a SignalManager instance for testing."""
    return SignalManager(debug_mode=True)


@pytest.fixture
def model():
    """Create a mock model for testing."""
    model = MockModel()
    model.current_data = "Test Data"
    return model


@pytest.fixture
def view():
    """Create a mock view for testing."""
    return MockView()


@pytest.fixture
def controller(model, signal_manager):
    """Create a controller for testing."""
    controller = TestController(model, signal_manager)
    controller.connect_to_model(model)
    return controller


# Test cases
class TestSignalIntegration:
    """Tests for signal integration between controllers and SignalManager."""

    def test_model_signal_propagation(self, controller, model):
        """Test that model signals propagate to controller."""
        # Set up signal spy
        signal_spy = MagicMock()
        controller.filtered_data_changed.connect(signal_spy)

        # Emit model signal
        test_data = "Updated Data"
        model.data_changed.emit(test_data)

        # Verify controller handler was called and emitted its signal
        signal_spy.assert_called_once_with(test_data)

    def test_view_signal_propagation(self, controller, view, model):
        """Test that view signals propagate to controller."""
        # Connect controller to view
        controller.connect_to_view(view)

        # Set up signal spy
        signal_spy = MagicMock()
        controller.filtered_data_changed.connect(signal_spy)

        # Emit view signal
        filter_text = "test filter"
        view.filter_changed.emit(filter_text)

        # Verify controller handler was called and filtered data was emitted
        expected_data = f"Filtered: {model.current_data}"
        signal_spy.assert_called_once_with(expected_data)

    def test_signal_cleanup(self, controller, view, model, signal_manager):
        """Test that signals are properly cleaned up."""
        # Connect controller to view
        controller.connect_to_view(view)

        # Verify connections exist
        assert signal_manager.is_connected(model, "data_changed", controller, "_on_data_changed")
        assert signal_manager.is_connected(view, "filter_changed", controller, "_on_filter_changed")

        # Disconnect all
        controller.disconnect_all()

        # Verify connections are removed
        assert not signal_manager.is_connected(
            model, "data_changed", controller, "_on_data_changed"
        )
        assert not signal_manager.is_connected(
            view, "filter_changed", controller, "_on_filter_changed"
        )

    def test_disconnection_selective(self, controller, view, model, signal_manager):
        """Test selective disconnection of signals."""
        # Connect controller to view
        controller.connect_to_view(view)

        # Verify connections exist
        assert signal_manager.is_connected(model, "data_changed", controller, "_on_data_changed")
        assert signal_manager.is_connected(view, "filter_changed", controller, "_on_filter_changed")

        # Disconnect only from view
        controller.disconnect_from_view(view)

        # Verify view connections are removed but model connections remain
        assert signal_manager.is_connected(model, "data_changed", controller, "_on_data_changed")
        assert not signal_manager.is_connected(
            view, "filter_changed", controller, "_on_filter_changed"
        )

    def test_multiple_controllers_same_signal(self, model, signal_manager):
        """Test multiple controllers connecting to the same signal."""
        # Create two controllers connected to the same model
        controller1 = TestController(model, signal_manager)
        controller1.connect_to_model(model)

        controller2 = TestController(model, signal_manager)
        controller2.connect_to_model(model)

        # Set up signal spies
        spy1 = MagicMock()
        spy2 = MagicMock()
        controller1.filtered_data_changed.connect(spy1)
        controller2.filtered_data_changed.connect(spy2)

        # Emit model signal
        test_data = "Shared Data"
        model.data_changed.emit(test_data)

        # Verify both controllers received the signal
        spy1.assert_called_once_with(test_data)
        spy2.assert_called_once_with(test_data)

        # Disconnect one controller
        controller1.disconnect_all()

        # Emit another signal
        test_data2 = "After Disconnect"
        model.data_changed.emit(test_data2)

        # Verify only controller2 received the second signal
        assert spy1.call_count == 1
        spy2.assert_called_with(test_data2)

    def test_connection_tracking(self, controller, view, model, signal_manager):
        """Test that connections are properly tracked."""
        # Connect controller to view
        controller.connect_to_view(view)

        # Get all connections
        connections = signal_manager.get_connections()

        # Verify the expected number of connections
        # 2 model connections + 2 view connections
        assert len(connections) == 4

        # Get connections for specific sender
        model_connections = signal_manager.get_connections(sender=model)
        view_connections = signal_manager.get_connections(sender=view)

        # Verify specific connections
        assert len(model_connections) == 2
        assert len(view_connections) == 2
