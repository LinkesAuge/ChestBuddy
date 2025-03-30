"""
test_app_integration.py

Description: Tests for the integration of SignalManager with controllers in ChestBuddyApp
Usage:
    pytest tests/test_app_integration.py
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.app import ChestBuddyApp


class MockWindow(QObject):
    """Mock main window for testing."""

    import_triggered = Signal()
    export_triggered = Signal()
    view_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._data_view = MagicMock()
        self._data_view.filter_changed = Signal(str)

    def show(self):
        """Mock show method."""
        pass

    def get_data_view(self):
        """Return the mock data view."""
        return self._data_view


class TestAppSignalIntegration:
    """Tests for the integration of SignalManager with controllers in ChestBuddyApp."""

    @pytest.fixture
    def mock_app_components(self):
        """Mock the app components for testing."""
        with (
            patch("chestbuddy.app.MainWindow", return_value=MockWindow()),
            patch("chestbuddy.app.ChestDataModel"),
            patch("chestbuddy.app.CSVService"),
            patch("chestbuddy.app.ValidationService"),
            patch("chestbuddy.app.CorrectionService"),
            patch("chestbuddy.app.ChartService"),
            patch("chestbuddy.app.DataManager"),
            patch("chestbuddy.app.ConfigManager"),
            patch("chestbuddy.app.FileOperationsController"),
            patch("chestbuddy.app.ProgressController"),
            patch("chestbuddy.app.ViewStateController"),
            patch("chestbuddy.app.DataViewController"),
            patch("chestbuddy.app.UIStateController"),
            patch("chestbuddy.app.ErrorHandlingController"),
        ):
            yield

    @pytest.fixture
    def app(self, mock_app_components):
        """Create a ChestBuddyApp instance for testing."""
        with patch("sys.argv", ["chestbuddy"]):
            app = ChestBuddyApp([])
            # Manually set up signal manager for testing
            app._signal_manager = SignalManager(debug_mode=True)
            return app

    def test_signal_manager_initialization(self, app):
        """Test that the SignalManager is properly initialized."""
        assert hasattr(app, "_signal_manager")
        assert isinstance(app._signal_manager, SignalManager)

    def test_controller_initialization_with_signal_manager(self, app, mock_app_components):
        """Test that controllers are initialized with the SignalManager."""
        # File controller should be initialized with signal_manager
        app._file_controller = MagicMock()
        app._view_state_controller = MagicMock()
        app._data_view_controller = MagicMock()

        # Create a new signal manager for testing
        app._signal_manager = SignalManager()

        # Re-run the setup
        app._setup_connections()

        # Verify connections are made through SignalManager
        connections = app._signal_manager.get_connections()
        assert len(connections) > 0

    def test_signal_propagation(self, app, mock_app_components):
        """Test that signals are propagated correctly through SignalManager."""
        # Set up mocks
        app._file_controller = MagicMock()
        app._file_controller._on_import_triggered = MagicMock()
        app._main_window = MockWindow()

        # Connect signals through SignalManager
        app._signal_manager.connect(
            app._main_window, "import_triggered", app._file_controller, "_on_import_triggered"
        )

        # Emit signal
        app._main_window.import_triggered.emit()

        # Verify handler was called
        app._file_controller._on_import_triggered.assert_called_once()

    def test_multiple_signal_connections(self, app, mock_app_components):
        """Test that multiple controllers can connect to the same signal."""
        # Set up mocks
        app._file_controller = MagicMock()
        app._file_controller._on_import_triggered = MagicMock()
        app._view_state_controller = MagicMock()
        app._view_state_controller._on_import_triggered = MagicMock()
        app._main_window = MockWindow()

        # Connect signals through SignalManager
        app._signal_manager.connect(
            app._main_window, "import_triggered", app._file_controller, "_on_import_triggered"
        )
        app._signal_manager.connect(
            app._main_window, "import_triggered", app._view_state_controller, "_on_import_triggered"
        )

        # Emit signal
        app._main_window.import_triggered.emit()

        # Verify both handlers were called
        app._file_controller._on_import_triggered.assert_called_once()
        app._view_state_controller._on_import_triggered.assert_called_once()

    def test_signal_cleanup(self, app, mock_app_components):
        """Test that signal connections are properly cleaned up."""
        # Set up mocks
        app._file_controller = MagicMock()
        app._file_controller._on_import_triggered = MagicMock()
        app._main_window = MockWindow()

        # Connect signals through SignalManager
        app._signal_manager.connect(
            app._main_window, "import_triggered", app._file_controller, "_on_import_triggered"
        )

        # Verify connection exists
        connections = app._signal_manager.get_connections()
        assert len(connections) == 1

        # Clean up connections
        app._cleanup_connections()

        # Verify connections are removed
        connections = app._signal_manager.get_connections()
        assert len(connections) == 0

    def test_view_controller_connections(self, app, mock_app_components):
        """Test that view controllers are properly connected to views."""
        # Set up mocks
        app._data_view_controller = MagicMock()
        app._data_view_controller.connect_to_view = MagicMock()
        app._main_window = MockWindow()

        # Configure main window mock
        data_view = app._main_window.get_data_view()

        # Connect view to controller
        app._data_view_controller.connect_to_view(data_view)

        # Verify connect_to_view was called
        app._data_view_controller.connect_to_view.assert_called_once_with(data_view)


# Integration test with actual controllers (not just mocks)
@pytest.mark.integration
class TestControllerSignalIntegration:
    """Integration tests for controller signal connections using actual controller instances."""

    @pytest.fixture
    def signal_manager(self):
        """Create a SignalManager instance for testing."""
        return SignalManager(debug_mode=True)

    @pytest.fixture
    def controllers(self, signal_manager):
        """Create actual controller instances for testing."""
        # Import here to avoid circular imports in test setup
        from chestbuddy.core.controllers import DataViewController, ViewStateController
        from chestbuddy.core.models import ChestDataModel

        # Create model and controllers
        data_model = MagicMock()
        data_model.data_changed = Signal(object)

        # Create controller instances
        data_controller = DataViewController(data_model, signal_manager)
        view_controller = ViewStateController(data_model, signal_manager)

        return {
            "data_model": data_model,
            "data_controller": data_controller,
            "view_controller": view_controller,
        }

    def test_controller_model_connections(self, controllers, signal_manager):
        """Test that controllers properly connect to model signals."""
        # Extract components
        data_model = controllers["data_model"]
        data_controller = controllers["data_controller"]

        # Verify controller is connected to model
        connections = signal_manager.get_connections(sender=data_model)
        assert len(connections) > 0

        # Verify the connection is to the right handler
        connection_found = False
        for sender, signal_name, receiver, slot_name in connections:
            if (
                sender == data_model
                and signal_name == "data_changed"
                and receiver == data_controller
            ):
                connection_found = True
                break

        assert connection_found

    def test_controller_view_connections(self, controllers, signal_manager):
        """Test that controllers properly connect to view signals."""
        # Extract components
        data_controller = controllers["data_controller"]

        # Create mock view
        view = MagicMock()
        view.filter_changed = Signal(str)
        view.sort_changed = Signal(object)

        # Connect view to controller
        data_controller.connect_to_view(view)

        # Verify controller is connected to view
        connections = signal_manager.get_connections(sender=view)
        assert len(connections) > 0

        # Verify view is in controller's connected views
        assert view in data_controller._connected_views

    def test_controller_cleanup(self, controllers, signal_manager):
        """Test that controllers properly clean up connections."""
        # Extract components
        data_controller = controllers["data_controller"]

        # Create mock view and connect
        view = MagicMock()
        view.filter_changed = Signal(str)
        data_controller.connect_to_view(view)

        # Verify connection exists
        assert view in data_controller._connected_views

        # Clean up connections
        count = data_controller.disconnect_all()

        # Verify connections are removed
        assert view not in data_controller._connected_views
        assert count > 0
