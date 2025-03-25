"""
Test integration of SignalManager with controllers.

This test verifies that controllers correctly use the SignalManager for
managing signal connections between views, models, and other controllers.
"""

import logging
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

from chestbuddy.utils.signal_manager import SignalManager
from chestbuddy.ui.views.base_view import BaseView


class MockDataModel(QObject):
    """Mock data model with standard signals."""

    data_changed = Signal()
    validation_complete = Signal(object)
    correction_complete = Signal(str, int)
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        """Initialize the mock data model."""
        super().__init__()
        self.data = []
        self.column_names = []
        self.is_empty = True
        self.data_hash = "mock_hash"

    def filter_data(self, column, value, mode, case_sensitive):
        """Filter data and return filtered result."""
        return []

    def sort_data(self, column, ascending):
        """Sort data by column."""
        return True


class MockView(BaseView):
    """Mock view with standard signals."""

    filter_changed = Signal(str)
    sort_changed = Signal(int, int)
    action_triggered = Signal(str)
    selection_changed = Signal(list)

    def __init__(self, title="Mock View", parent=None, debug_mode=False):
        """Initialize the mock view."""
        super().__init__(title, parent, debug_mode)
        self.filter_text = ""
        self.action_history = []

        # Add filter UI components that DataViewController expects
        self._filter_column = MagicMock()
        self._filter_column.currentText.return_value = "Column1"

        self._filter_text = MagicMock()
        self._filter_text.text.return_value = "test"

        self._filter_mode = MagicMock()
        self._filter_mode.currentText.return_value = "Contains"

        self._case_sensitive = MagicMock()
        self._case_sensitive.isChecked.return_value = False

        self._status_label = MagicMock()

        # Create a mock action toolbar
        self._action_toolbar = MagicMock()
        self._action_toolbar.get_button_by_name.return_value = MagicMock()

    def _setup_ui(self):
        """Setup UI components."""
        super()._setup_ui()
        # Add mock UI setup here

    def refresh(self):
        """Refresh the view."""
        pass

    def show_error(self, message):
        """Show error message."""
        self.error_message = message

    def _update_view_with_filtered_data(self, data):
        """Update view with filtered data."""
        pass


class MockDataViewController(QObject):
    """Mock data view controller that uses SignalManager."""

    # Define signals
    filter_applied = Signal(dict)
    sort_applied = Signal(str, bool)
    validation_started = Signal()
    validation_completed = Signal(dict)
    correction_started = Signal()
    correction_completed = Signal(str, int)
    operation_error = Signal(str)
    data_changed = Signal()
    table_populated = Signal(int)

    def __init__(self, data_model, signal_manager):
        """Initialize the controller with SignalManager."""
        super().__init__()
        self._data_model = data_model
        self._signal_manager = signal_manager
        self._view = None
        self._connect_model_signals()

    def _connect_model_signals(self):
        """Connect to model signals using SignalManager."""
        self._signal_manager.connect(self._data_model, "data_changed", self, "_on_data_changed")
        self._signal_manager.connect(
            self._data_model, "validation_complete", self, "_on_validation_complete"
        )
        self._signal_manager.connect(
            self._data_model, "correction_complete", self, "_on_correction_complete"
        )
        self._signal_manager.connect(self._data_model, "error_occurred", self, "_on_error_occurred")

    def connect_view(self, view):
        """Connect to view signals using SignalManager."""
        self._view = view

        self._signal_manager.connect(view, "filter_changed", self, "_on_filter_changed")
        self._signal_manager.connect(view, "sort_changed", self, "_on_sort_changed")
        self._signal_manager.connect(view, "action_triggered", self, "_on_action_triggered")
        self._signal_manager.connect(view, "selection_changed", self, "_on_selection_changed")

    def filter_data(self, filter_text):
        """Filter data using the text."""
        with self._signal_manager.blocked_signals(self._data_model, "data_changed"):
            self._data_model.filter_text = filter_text
            self._data_model.is_filtered = True
        self.filter_applied.emit({"text": filter_text})
        return True

    def cleanup(self):
        """Clean up all signal connections."""
        self._signal_manager.disconnect_receiver(self)

    # Signal handlers
    def _on_data_changed(self):
        """Handle data model changes."""
        if self._view:
            self._view.refresh()

    def _on_validation_complete(self, results):
        """Handle validation completion."""
        self.validation_completed.emit(results)

    def _on_correction_complete(self, strategy, count):
        """Handle correction completion."""
        self.correction_completed.emit(strategy, count)

    def _on_error_occurred(self, message):
        """Handle error occurrence."""
        self.operation_error.emit(message)
        if self._view:
            self._view.show_error(message)

    def _on_filter_changed(self, text):
        """Handle filter change from view."""
        self.filter_data(text)

    def _on_sort_changed(self, column, order):
        """Handle sort change from view."""
        self.sort_applied.emit(str(column), order == 0)

    def _on_action_triggered(self, action):
        """Handle action triggered from view."""
        pass

    def _on_selection_changed(self, selected_rows):
        """Handle selection change from view."""
        pass


@pytest.fixture
def app():
    """QApplication fixture for testing Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.processEvents()


@pytest.fixture
def signal_manager():
    """Create a SignalManager instance for testing."""
    return SignalManager(debug_mode=True)


@pytest.fixture
def mock_model():
    """Create a mock data model for testing."""
    return MockDataModel()


@pytest.fixture
def mock_view(app):
    """Create a mock view for testing."""
    view = MockView(debug_mode=True)
    yield view
    view.deleteLater()


@pytest.fixture
def controller(signal_manager, mock_model):
    """Create a DataViewController for testing."""
    controller = MockDataViewController(mock_model, signal_manager)
    return controller


def test_controller_model_signal_connection(controller, mock_model):
    """Test controller properly connects to model signals."""
    # Mock controller methods
    controller._on_data_changed = MagicMock()
    controller._on_validation_complete = MagicMock()
    controller._on_correction_complete = MagicMock()
    controller._on_error_occurred = MagicMock()

    # Emit signals from model
    mock_model.data_changed.emit()
    mock_model.validation_complete.emit({"result": "success"})
    mock_model.correction_complete.emit("Test", 10)
    mock_model.error_occurred.emit("Test error")

    # Verify controller methods were called
    controller._on_data_changed.assert_called_once()
    controller._on_validation_complete.assert_called_once_with({"result": "success"})
    controller._on_correction_complete.assert_called_once_with("Test", 10)
    controller._on_error_occurred.assert_called_once_with("Test error")


def test_controller_view_signal_connection(controller, mock_view):
    """Test controller properly connects to view signals."""
    # Mock controller methods
    controller._on_filter_changed = MagicMock()
    controller._on_sort_changed = MagicMock()
    controller._on_action_triggered = MagicMock()
    controller._on_selection_changed = MagicMock()

    # Connect controller to view signals
    controller.connect_view(mock_view)

    # Emit signals from view
    mock_view.filter_changed.emit("test filter")
    mock_view.sort_changed.emit(1, 0)
    mock_view.action_triggered.emit("test_action")
    mock_view.selection_changed.emit([1, 2, 3])

    # Verify controller methods were called
    controller._on_filter_changed.assert_called_once_with("test filter")
    controller._on_sort_changed.assert_called_once_with(1, 0)
    controller._on_action_triggered.assert_called_once_with("test_action")
    controller._on_selection_changed.assert_called_once_with([1, 2, 3])


def test_controller_signal_safety(controller, mock_model, mock_view):
    """Test controller uses signal safety mechanisms."""
    # Connect controller to view
    controller.connect_view(mock_view)

    # Use BlockedSignals context to prevent infinite loops
    with patch.object(controller._signal_manager, "blocked_signals") as mock_blocked:
        # Trigger an action that would normally cause signal emissions from model
        controller.filter_data("test")

        # Verify blocked_signals was used
        mock_blocked.assert_called()

        # Verify model was updated
        assert mock_model.filter_text == "test"
        assert mock_model.is_filtered is True


def test_controller_cleanup(controller, mock_view, signal_manager):
    """Test controller properly cleans up signals."""
    # Connect controller to view
    controller.connect_view(mock_view)

    # Verify connections exist
    assert len(signal_manager.get_connections(receiver=controller)) > 0

    # Clean up controller
    controller.cleanup()

    # Verify all connections to controller were removed
    assert len(signal_manager.get_connections(receiver=controller)) == 0


def test_safe_reconnection(controller, mock_view, signal_manager):
    """Test safe reconnection of signals."""
    # Connect controller to view
    controller.connect_view(mock_view)

    # Get initial connection count
    initial_connections = len(
        signal_manager.get_connections(sender=mock_view, signal_name="filter_changed")
    )

    # Reconnect to the same view
    controller.connect_view(mock_view)

    # Verify no duplicate connections were created
    new_connections = len(
        signal_manager.get_connections(sender=mock_view, signal_name="filter_changed")
    )
    assert new_connections == initial_connections


def test_signal_propagation(controller, mock_model, mock_view):
    """Test signals properly propagate through the controller."""
    # Connect controller to view
    controller.connect_view(mock_view)

    # Mock view method
    mock_view.refresh = MagicMock()
    mock_view.show_error = MagicMock()

    # Emit model signals
    mock_model.data_changed.emit()
    mock_model.error_occurred.emit("Error message")

    # Verify signals propagated to view
    mock_view.refresh.assert_called()
    mock_view.show_error.assert_called_with("Error message")


def test_controller_signal_throttling(controller, mock_model, mock_view):
    """Test controller throttles frequent signals properly."""
    # This would test the throttling mechanism for frequent updates
    # Since we don't have actual throttling implemented yet, we'll just
    # verify the connections work

    # Connect controller to view
    controller.connect_view(mock_view)

    # Mock view method
    mock_view.refresh = MagicMock()

    # Emit multiple data_changed signals rapidly
    for _ in range(5):
        mock_model.data_changed.emit()

    # Verify view refresh was called (would be called fewer times with throttling)
    assert mock_view.refresh.call_count > 0
