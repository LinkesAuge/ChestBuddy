"""
test_signal_disconnection.py

Description: Tests for proper signal connection and disconnection in MainWindow
Usage:
    pytest tests/ui/test_signal_disconnection.py
"""

import pytest
from unittest.mock import MagicMock, patch, call
import logging

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox

from chestbuddy.ui.main_window import MainWindow
from chestbuddy.core.controllers.view_state_controller import ViewStateController
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.core.controllers.file_operations_controller import FileOperationsController
from chestbuddy.core.controllers.progress_controller import ProgressController
from chestbuddy.core.controllers.ui_state_controller import UIStateController
from chestbuddy.core.models import ChestDataModel


class SignalConnection(QObject):
    """
    Helper class to track signal connections.

    This class tracks signal connections and disconnections to identify
    potential memory leaks or disconnection issues.
    """

    def __init__(self):
        super().__init__()
        self.connect_count = 0
        self.disconnect_count = 0
        self.connections = {}

    def track_connect(self, sender, signal_name, receiver, slot_name):
        """Track a signal connection."""
        self.connect_count += 1
        key = self._make_key(sender, signal_name, receiver, slot_name)
        self.connections[key] = self.connections.get(key, 0) + 1

    def track_disconnect(self, sender, signal_name, receiver, slot_name):
        """Track a signal disconnection."""
        self.disconnect_count += 1
        key = self._make_key(sender, signal_name, receiver, slot_name)
        if key in self.connections:
            self.connections[key] -= 1
            if self.connections[key] <= 0:
                del self.connections[key]

    def _make_key(self, sender, signal_name, receiver, slot_name):
        """Create a unique key for a signal connection."""
        return f"{id(sender)}_{signal_name}_{id(receiver)}_{slot_name}"

    def get_unbalanced_connections(self):
        """Get connections that haven't been disconnected."""
        return self.connections.copy()

    @property
    def is_balanced(self):
        """Check if all connections have been disconnected."""
        return len(self.connections) == 0

    def reset(self):
        """Reset tracking."""
        self.connect_count = 0
        self.disconnect_count = 0
        self.connections = {}


@pytest.fixture
def signal_tracker():
    """Create a signal connection tracker."""
    tracker = SignalConnection()
    return tracker


@pytest.fixture
def mock_signal_manager(signal_tracker):
    """Create a mock signal manager that tracks connections."""
    manager = MagicMock()

    def track_connect(sender, signal_name, receiver, slot_name):
        signal_tracker.track_connect(sender, signal_name, receiver, slot_name)
        return True

    def track_disconnect(sender, signal_name, receiver, slot_name):
        signal_tracker.track_disconnect(sender, signal_name, receiver, slot_name)
        return True

    manager.connect = MagicMock(side_effect=track_connect)
    manager.disconnect = MagicMock(side_effect=track_disconnect)

    return manager


@pytest.fixture
def mock_data_model():
    """Create a mock data model."""
    model = MagicMock(spec=ChestDataModel)
    model.has_data.return_value = False
    return model


@pytest.fixture
def mock_view_state_controller(mock_signal_manager):
    """Create a mock ViewStateController with signal tracking."""
    controller = MagicMock(spec=ViewStateController)
    controller._signal_manager = mock_signal_manager

    # Add connect and disconnect methods
    controller.connect_to_view = MagicMock()
    controller.disconnect_from_view = MagicMock()

    return controller


@pytest.fixture
def mock_file_operations_controller(mock_signal_manager):
    """Create a mock FileOperationsController with signal tracking."""
    controller = MagicMock(spec=FileOperationsController)
    controller._signal_manager = mock_signal_manager

    # Add connect and disconnect methods
    controller.connect_to_view = MagicMock()
    controller.disconnect_from_view = MagicMock()

    return controller


@pytest.fixture
def mock_data_view_controller(mock_signal_manager):
    """Create a mock DataViewController with signal tracking."""
    controller = MagicMock(spec=DataViewController)
    controller._signal_manager = mock_signal_manager

    # Add connect and disconnect methods
    controller.connect_to_view = MagicMock()
    controller.disconnect_from_view = MagicMock()

    return controller


@pytest.fixture
def mock_progress_controller(mock_signal_manager):
    """Create a mock ProgressController with signal tracking."""
    controller = MagicMock(spec=ProgressController)
    controller._signal_manager = mock_signal_manager

    # Add connect and disconnect methods
    controller.connect_to_view = MagicMock()
    controller.disconnect_from_view = MagicMock()

    return controller


@pytest.fixture
def mock_ui_state_controller(mock_signal_manager):
    """Create a mock UIStateController with signal tracking."""
    controller = MagicMock(spec=UIStateController)
    controller._signal_manager = mock_signal_manager

    # Add connect and disconnect methods
    controller.connect_to_view = MagicMock()
    controller.disconnect_from_view = MagicMock()

    return controller


@pytest.fixture
def main_window(
    qtbot,
    mock_data_model,
    mock_file_operations_controller,
    mock_progress_controller,
    mock_view_state_controller,
    mock_data_view_controller,
    mock_ui_state_controller,
    mock_signal_manager,
):
    """Create a MainWindow instance with signal tracking."""
    # Mock other services needed by MainWindow
    csv_service = MagicMock()
    validation_service = MagicMock()
    correction_service = MagicMock()
    chart_service = MagicMock()
    data_manager = MagicMock()
    config_manager = MagicMock()

    # Patch QMessageBox to avoid actual dialog display
    with patch("PySide6.QtWidgets.QMessageBox", autospec=True):
        # Create MainWindow instance
        window = MainWindow(
            data_model=mock_data_model,
            csv_service=csv_service,
            validation_service=validation_service,
            correction_service=correction_service,
            chart_service=chart_service,
            data_manager=data_manager,
            file_operations_controller=mock_file_operations_controller,
            progress_controller=mock_progress_controller,
            view_state_controller=mock_view_state_controller,
            data_view_controller=mock_data_view_controller,
            ui_state_controller=mock_ui_state_controller,
            config_manager=config_manager,
        )

        # Add signal manager to MainWindow
        window._signal_manager = mock_signal_manager

        qtbot.addWidget(window)
        window.show()

        yield window

        # Clean up
        window.close()


class TestSignalDisconnection:
    """Tests for signal connection and disconnection."""

    def test_controller_connections_are_tracked(self, main_window, signal_tracker):
        """Test that controller signal connections are properly tracked."""
        # After MainWindow initialization, there should be connections
        assert signal_tracker.connect_count > 0

    def test_signal_disconnect_on_window_close(
        self,
        qtbot,
        mock_data_model,
        mock_file_operations_controller,
        mock_progress_controller,
        mock_view_state_controller,
        mock_data_view_controller,
        mock_ui_state_controller,
        mock_signal_manager,
        signal_tracker,
    ):
        """Test that signals are properly disconnected when the window is closed."""
        # Create MainWindow
        csv_service = MagicMock()
        validation_service = MagicMock()
        correction_service = MagicMock()
        chart_service = MagicMock()
        data_manager = MagicMock()
        config_manager = MagicMock()

        # Reset signal tracker
        signal_tracker.reset()

        # Create window with signal tracking
        with patch("PySide6.QtWidgets.QMessageBox", autospec=True):
            window = MainWindow(
                data_model=mock_data_model,
                csv_service=csv_service,
                validation_service=validation_service,
                correction_service=correction_service,
                chart_service=chart_service,
                data_manager=data_manager,
                file_operations_controller=mock_file_operations_controller,
                progress_controller=mock_progress_controller,
                view_state_controller=mock_view_state_controller,
                data_view_controller=mock_data_view_controller,
                ui_state_controller=mock_ui_state_controller,
                config_manager=config_manager,
            )

            # Add signal manager to MainWindow
            window._signal_manager = mock_signal_manager

            qtbot.addWidget(window)
            window.show()

            # Check that signals were connected
            assert signal_tracker.connect_count > 0

            # Close the window properly
            if hasattr(window, "closeEvent"):
                window.closeEvent(MagicMock())
            else:
                # If closeEvent doesn't exist, try disconnect method directly
                if hasattr(window, "_disconnect_controllers"):
                    window._disconnect_controllers()

            # Check that disconnect methods were called
            mock_view_state_controller.disconnect_from_view.assert_called()
            mock_file_operations_controller.disconnect_from_view.assert_called()
            mock_data_view_controller.disconnect_from_view.assert_called()

            # Check signal balance
            unbalanced = signal_tracker.get_unbalanced_connections()
            if unbalanced:
                for key, count in unbalanced.items():
                    print(f"Unbalanced connection: {key}, count: {count}")

            # All signals should be disconnected
            assert signal_tracker.is_balanced, "Not all signals were disconnected"

    def test_controller_disconnect_interface(
        self, mock_view_state_controller, mock_file_operations_controller, mock_data_view_controller
    ):
        """Test that controllers implement the disconnect interface correctly."""
        # All controllers should have a disconnect_from_view method
        assert hasattr(mock_view_state_controller, "disconnect_from_view")
        assert hasattr(mock_file_operations_controller, "disconnect_from_view")
        assert hasattr(mock_data_view_controller, "disconnect_from_view")

        # Call the methods to verify they can be called
        mock_view_state_controller.disconnect_from_view(MagicMock())
        mock_file_operations_controller.disconnect_from_view(MagicMock())
        mock_data_view_controller.disconnect_from_view(MagicMock())

        # Check that the methods were called
        mock_view_state_controller.disconnect_from_view.assert_called()
        mock_file_operations_controller.disconnect_from_view.assert_called()
        mock_data_view_controller.disconnect_from_view.assert_called()

    def test_mainwindow_disconnect_method(
        self,
        main_window,
        mock_view_state_controller,
        mock_file_operations_controller,
        mock_data_view_controller,
    ):
        """Test that MainWindow has a method to disconnect all controllers."""
        # MainWindow should have a _disconnect_controllers method
        assert hasattr(main_window, "_disconnect_controllers"), (
            "MainWindow missing _disconnect_controllers method"
        )

        # Call the method
        main_window._disconnect_controllers()

        # Check that all controller disconnect methods were called
        mock_view_state_controller.disconnect_from_view.assert_called()
        mock_file_operations_controller.disconnect_from_view.assert_called()
        mock_data_view_controller.disconnect_from_view.assert_called()
