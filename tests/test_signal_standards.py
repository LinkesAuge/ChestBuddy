"""
Tests for the signal connection standards implementation.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication, QWidget

from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.views.data_view_adapter import DataViewAdapter
from chestbuddy.utils.signal_manager import SignalManager


class MockDataModel(QObject):
    """Mock data model for testing."""

    data_changed = Signal()

    def __init__(self):
        """Initialize the mock data model."""
        super().__init__()
        self.data = []
        self.column_names = []
        self.is_empty = True
        self.data_hash = "mock_hash"


class MockController(QObject):
    """Mock controller for testing."""

    # Operation signals
    operation_started = Signal()
    operation_completed = Signal()
    validation_started = Signal()
    validation_completed = Signal(object)
    correction_started = Signal()
    correction_completed = Signal(str, int)
    operation_error = Signal(str)
    data_changed = Signal()
    table_populated = Signal(int)

    def __init__(self):
        """Initialize the mock controller."""
        super().__init__()

    def set_view(self, view):
        """Set the view for this controller."""
        self._view = view


@pytest.fixture
def app():
    """QApplication fixture for testing Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.processEvents()


@pytest.fixture
def mock_data_model():
    """Create a mock data model for testing."""
    return MockDataModel()


@pytest.fixture
def mock_controller():
    """Create a mock controller for testing."""
    return MockController()


@pytest.fixture
def base_view(app):
    """Create a BaseView instance for testing."""
    view = BaseView("Test View", debug_mode=True)
    yield view
    view.deleteLater()


@pytest.fixture
def data_view_adapter(app, mock_data_model):
    """Create a DataViewAdapter for testing."""
    adapter = DataViewAdapter(mock_data_model, debug_mode=True)
    yield adapter
    adapter.deleteLater()


def test_base_view_signal_manager_initialization(base_view):
    """Test that BaseView initializes SignalManager correctly."""
    assert hasattr(base_view, "_signal_manager")
    assert isinstance(base_view._signal_manager, SignalManager)

    # Debug mode should be passed to the SignalManager
    assert base_view._debug_mode is True
    assert base_view._signal_manager._debug_mode is True


def test_base_view_disconnect_signals(base_view):
    """Test that BaseView properly disconnects signals."""
    # Create a mock for the disconnect_receiver method
    with patch.object(base_view._signal_manager, "disconnect_receiver") as mock_disconnect:
        # Call the disconnect method
        base_view._disconnect_signals()

        # Verify disconnect_receiver was called with the view
        mock_disconnect.assert_called_once_with(base_view)


def test_data_view_adapter_connection_methods(data_view_adapter):
    """Test that DataViewAdapter implements all required connection methods."""
    assert hasattr(data_view_adapter, "_connect_signals")
    assert hasattr(data_view_adapter, "_connect_ui_signals")
    assert hasattr(data_view_adapter, "_connect_controller_signals")
    assert hasattr(data_view_adapter, "_connect_model_signals")
    assert hasattr(data_view_adapter, "_disconnect_signals")


def test_data_view_adapter_controller_connections(data_view_adapter, mock_controller):
    """Test that DataViewAdapter properly connects controller signals."""
    # Create spies for adapter methods
    data_view_adapter._on_validation_started = MagicMock()
    data_view_adapter._on_validation_completed = MagicMock()
    data_view_adapter._on_correction_started = MagicMock()
    data_view_adapter._on_correction_completed = MagicMock()
    data_view_adapter._on_operation_error = MagicMock()
    data_view_adapter._on_table_populated = MagicMock()
    data_view_adapter._on_data_changed = MagicMock()

    # Set the controller
    data_view_adapter.set_controller(mock_controller)

    # Emit signals from the controller
    mock_controller.validation_started.emit()
    mock_controller.validation_completed.emit({})
    mock_controller.correction_started.emit()
    mock_controller.correction_completed.emit("test", 5)
    mock_controller.operation_error.emit("error")
    mock_controller.table_populated.emit(10)
    mock_controller.data_changed.emit()

    # Verify that the adapter methods were called
    data_view_adapter._on_validation_started.assert_called_once()
    data_view_adapter._on_validation_completed.assert_called_once()
    data_view_adapter._on_correction_started.assert_called_once()
    data_view_adapter._on_correction_completed.assert_called_once_with("test", 5)
    data_view_adapter._on_operation_error.assert_called_once_with("error")
    data_view_adapter._on_table_populated.assert_called_once_with(10)
    data_view_adapter._on_data_changed.assert_called_once()


def test_data_view_adapter_model_connections(data_view_adapter, mock_data_model):
    """Test that DataViewAdapter properly connects model signals."""
    # Create spy for adapter method
    data_view_adapter._on_data_changed = MagicMock()

    # Connect model signals (should be done in __init__)

    # Emit signal from the model
    mock_data_model.data_changed.emit()

    # Verify that the adapter method was called
    data_view_adapter._on_data_changed.assert_called_once()


def test_data_view_adapter_import_export_signals(data_view_adapter):
    """Test that DataViewAdapter emits import and export signals."""
    # Create spies for signals
    import_spy = MagicMock()
    export_spy = MagicMock()

    # Connect to signals
    data_view_adapter.import_requested.connect(import_spy)
    data_view_adapter.export_requested.connect(export_spy)

    # Call handler methods
    data_view_adapter._on_import_requested()
    data_view_adapter._on_export_requested()

    # Verify signals were emitted
    import_spy.assert_called_once()
    export_spy.assert_called_once()


def test_data_view_adapter_header_action_signal(data_view_adapter):
    """Test that DataViewAdapter handles header action signals."""
    # Create spy for method
    data_view_adapter._on_header_action_clicked = MagicMock()

    # Connect signal (should be done in _connect_ui_signals)
    data_view_adapter._signal_manager.connect(
        data_view_adapter, "header_action_clicked", data_view_adapter, "_on_header_action_clicked"
    )

    # Emit signal
    data_view_adapter.header_action_clicked.emit("test_action")

    # Verify method was called
    data_view_adapter._on_header_action_clicked.assert_called_once_with("test_action")


def test_view_cleanup_on_close(data_view_adapter):
    """Test that DataViewAdapter properly cleans up signals on close."""
    # Create a mock for the disconnect_receiver method
    with patch.object(data_view_adapter._signal_manager, "disconnect_receiver") as mock_disconnect:
        # Simulate close event
        data_view_adapter.close()

        # Verify disconnect_receiver was called with the adapter
        mock_disconnect.assert_called_once_with(data_view_adapter)
