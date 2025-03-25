"""
test_base_controller.py

Description: Tests for the BaseController class
Usage:
    pytest tests/core/test_base_controller.py
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.core.controllers.base_controller import BaseController


# Mock classes for testing
class MockSignalSender(QObject):
    """Mock class that sends signals for testing."""

    test_signal = Signal(str)
    data_signal = Signal(object)


class MockSignalReceiver(QObject):
    """Mock class that receives signals for testing."""

    def __init__(self):
        super().__init__()
        self.test_signal_called = False
        self.test_signal_value = None
        self.data_signal_called = False
        self.data_signal_value = None

    def _on_test_signal(self, value):
        """Test signal handler."""
        self.test_signal_called = True
        self.test_signal_value = value

    def _on_data_signal(self, value):
        """Data signal handler."""
        self.data_signal_called = True
        self.data_signal_value = value


# Test controller inheriting from BaseController
class TestController(BaseController):
    """Test controller for testing BaseController functionality."""

    def __init__(self, signal_manager):
        """Initialize the test controller."""
        super().__init__(signal_manager)

    def connect_to_view(self, view):
        """Connect to view signals."""
        super().connect_to_view(view)
        self._signal_manager.connect(view, "test_signal", self, "_on_test_signal")

    def connect_to_model(self, model):
        """Connect to model signals."""
        super().connect_to_model(model)
        self._signal_manager.connect(model, "data_signal", self, "_on_data_signal")

    def _on_test_signal(self, value):
        """Test signal handler."""
        pass

    def _on_data_signal(self, value):
        """Data signal handler."""
        pass


# Test fixtures
@pytest.fixture
def signal_manager():
    """Create a SignalManager instance for testing."""
    return SignalManager(debug_mode=True)


@pytest.fixture
def base_controller(signal_manager):
    """Create a BaseController instance for testing."""
    return BaseController(signal_manager)


@pytest.fixture
def test_controller(signal_manager):
    """Create a TestController instance for testing."""
    return TestController(signal_manager)


@pytest.fixture
def view():
    """Create a mock view for testing."""
    return MockSignalSender()


@pytest.fixture
def model():
    """Create a mock model for testing."""
    return MockSignalSender()


@pytest.fixture
def receiver():
    """Create a mock receiver for testing."""
    return MockSignalReceiver()


# Test cases
class TestBaseControllerClass:
    """Tests for the BaseController class."""

    def test_initialization(self, base_controller, signal_manager):
        """Test that the controller initializes correctly."""
        assert base_controller._signal_manager == signal_manager
        assert isinstance(base_controller._connected_views, set)
        assert isinstance(base_controller._connected_models, set)
        assert len(base_controller._connected_views) == 0
        assert len(base_controller._connected_models) == 0

    def test_connect_to_view(self, base_controller, view):
        """Test connecting to a view."""
        base_controller.connect_to_view(view)

        # Check that view is in connected_views
        assert view in base_controller._connected_views
        assert len(base_controller._connected_views) == 1

    def test_connect_to_model(self, base_controller, model):
        """Test connecting to a model."""
        base_controller.connect_to_model(model)

        # Check that model is in connected_models
        assert model in base_controller._connected_models
        assert len(base_controller._connected_models) == 1

    def test_disconnect_from_view(self, test_controller, view, signal_manager):
        """Test disconnecting from a view."""
        # Connect to view
        test_controller.connect_to_view(view)

        # Verify connection exists
        assert view in test_controller._connected_views
        assert signal_manager.is_connected(view, "test_signal", test_controller, "_on_test_signal")

        # Disconnect from view
        count = test_controller.disconnect_from_view(view)

        # Verify disconnection
        assert count == 1
        assert view not in test_controller._connected_views
        assert not signal_manager.is_connected(
            view, "test_signal", test_controller, "_on_test_signal"
        )

    def test_disconnect_from_model(self, test_controller, model, signal_manager):
        """Test disconnecting from a model."""
        # Connect to model
        test_controller.connect_to_model(model)

        # Verify connection exists
        assert model in test_controller._connected_models
        assert signal_manager.is_connected(model, "data_signal", test_controller, "_on_data_signal")

        # Disconnect from model
        count = test_controller.disconnect_from_model(model)

        # Verify disconnection
        assert count == 1
        assert model not in test_controller._connected_models
        assert not signal_manager.is_connected(
            model, "data_signal", test_controller, "_on_data_signal"
        )

    def test_disconnect_all(self, test_controller, view, model, signal_manager):
        """Test disconnecting all connections."""
        # Connect to view and model
        test_controller.connect_to_view(view)
        test_controller.connect_to_model(model)

        # Verify connections exist
        assert view in test_controller._connected_views
        assert model in test_controller._connected_models
        assert signal_manager.is_connected(view, "test_signal", test_controller, "_on_test_signal")
        assert signal_manager.is_connected(model, "data_signal", test_controller, "_on_data_signal")

        # Disconnect all
        count = test_controller.disconnect_all()

        # Verify all disconnections
        assert count == 2
        assert len(test_controller._connected_views) == 0
        assert len(test_controller._connected_models) == 0
        assert not signal_manager.is_connected(
            view, "test_signal", test_controller, "_on_test_signal"
        )
        assert not signal_manager.is_connected(
            model, "data_signal", test_controller, "_on_data_signal"
        )

    def test_signal_propagation(self, test_controller, view, model):
        """Test that signals propagate correctly."""
        # Setup signal spies
        test_signal_spy = MagicMock()
        data_signal_spy = MagicMock()

        # Connect signal spies
        test_controller._on_test_signal = test_signal_spy
        test_controller._on_data_signal = data_signal_spy

        # Connect to view and model
        test_controller.connect_to_view(view)
        test_controller.connect_to_model(model)

        # Emit signals
        test_value = "test_value"
        data_value = {"key": "value"}

        view.test_signal.emit(test_value)
        model.data_signal.emit(data_value)

        # Verify signal handlers were called
        test_signal_spy.assert_called_once_with(test_value)
        data_signal_spy.assert_called_once_with(data_value)

    def test_connection_cleanup_on_deletion(self, signal_manager, view, model):
        """Test that connections are cleaned up when controller is deleted."""
        # Create a controller that will be deleted
        controller = TestController(signal_manager)

        # Connect to view and model
        controller.connect_to_view(view)
        controller.connect_to_model(model)

        # Verify connections exist
        assert signal_manager.is_connected(view, "test_signal", controller, "_on_test_signal")
        assert signal_manager.is_connected(model, "data_signal", controller, "_on_data_signal")

        # Delete the controller
        controller.__del__()

        # Verify connections are cleaned up
        assert not signal_manager.is_connected(view, "test_signal", controller, "_on_test_signal")
        assert not signal_manager.is_connected(model, "data_signal", controller, "_on_data_signal")
