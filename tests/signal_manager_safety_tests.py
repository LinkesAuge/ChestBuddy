"""
Tests for the safety features of the SignalManager.

This module specifically tests the signal safety enhancements
added to the SignalManager in Phase 5 of the implementation plan.
"""

import logging
import pytest
import time
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication

from chestbuddy.utils.signal_manager import SignalManager


class SignalEmitter(QObject):
    """Class that emits signals for testing."""

    test_signal = Signal(str)
    frequent_signal = Signal(int)

    def __init__(self):
        """Initialize the emitter."""
        super().__init__()
        self.emit_count = 0

    def emit_test_signal(self, value):
        """Emit the test signal."""
        self.test_signal.emit(value)

    def start_frequent_emissions(self, interval=10, count=10):
        """Start emitting signals frequently."""
        self.remaining_count = count
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(interval)

    def _on_timer(self):
        """Handle timer event."""
        if self.remaining_count > 0:
            self.emit_count += 1
            self.frequent_signal.emit(self.emit_count)
            self.remaining_count -= 1
        else:
            self.timer.stop()


class SignalReceiver(QObject):
    """Class that receives signals for testing."""

    def __init__(self):
        """Initialize the receiver."""
        super().__init__()
        self.received_values = []
        self.receive_count = 0

    @Slot(str)
    def on_test_signal(self, value):
        """Handle test signal."""
        self.received_values.append(value)

    @Slot(int)
    def on_frequent_signal(self, value):
        """Handle frequent signal."""
        self.receive_count += 1
        self.last_value = value


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
def emitter():
    """Create a signal emitter for testing."""
    return SignalEmitter()


@pytest.fixture
def receiver():
    """Create a signal receiver for testing."""
    return SignalReceiver()


def test_blocked_signals_context_manager(signal_manager, emitter, receiver, app):
    """Test blocked_signals context manager."""
    # Connect signals
    signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")

    # Emit signal normally
    emitter.emit_test_signal("test1")
    app.processEvents()

    # Emit signal with blocked signals
    with signal_manager.blocked_signals(emitter, "test_signal"):
        emitter.emit_test_signal("test2")
        app.processEvents()

    # Emit signal after context manager
    emitter.emit_test_signal("test3")
    app.processEvents()

    # Check results
    assert len(receiver.received_values) == 2
    assert "test1" in receiver.received_values
    assert "test2" not in receiver.received_values
    assert "test3" in receiver.received_values


def test_blocked_signals_with_exception(signal_manager, emitter, receiver, app):
    """Test blocked_signals context manager with exception."""
    # Connect signals
    signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")

    # Emit signal with blocked signals and exception
    try:
        with signal_manager.blocked_signals(emitter, "test_signal"):
            emitter.emit_test_signal("test1")
            app.processEvents()
            raise RuntimeError("Test exception")
    except RuntimeError:
        pass

    # Emit signal after context manager
    emitter.emit_test_signal("test2")
    app.processEvents()

    # Check results - signal blocking should be restored even after exception
    assert len(receiver.received_values) == 1
    assert "test1" not in receiver.received_values
    assert "test2" in receiver.received_values


def test_safe_connect(signal_manager, emitter, receiver):
    """Test safe_connect method."""
    # Connect with safe_connect
    result1 = signal_manager.safe_connect(
        emitter, "test_signal", receiver, "on_test_signal", safe_disconnect_first=False
    )

    # Try to connect again with safe_connect
    result2 = signal_manager.safe_connect(
        emitter, "test_signal", receiver, "on_test_signal", safe_disconnect_first=False
    )

    # Connect again with safe_disconnect_first=True
    result3 = signal_manager.safe_connect(
        emitter, "test_signal", receiver, "on_test_signal", safe_disconnect_first=True
    )

    # Check results
    assert result1 is True  # First connection successful
    assert result2 is False  # Second connection failed (already connected)
    assert result3 is True  # Third connection successful (disconnected first)


def test_disconnection_during_signal_emission(signal_manager, emitter, receiver, app):
    """Test safe disconnection during signal emission."""

    # Create a callback that disconnects the signal
    def disconnect_callback(value):
        receiver.received_values.append(value)
        signal_manager.disconnect(emitter, "test_signal", receiver, "on_test_signal")

    # Replace the receiver's callback with our custom one
    receiver.on_test_signal = disconnect_callback

    # Connect signals
    signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")

    # Emit multiple signals
    emitter.emit_test_signal("test1")
    emitter.emit_test_signal("test2")
    app.processEvents()

    # Check results - only the first signal should be received
    assert len(receiver.received_values) == 1
    assert "test1" in receiver.received_values
    assert "test2" not in receiver.received_values


def test_cleanup_on_object_destruction(signal_manager, emitter, app):
    """Test connections are cleaned up when objects are destroyed."""
    # Create a temporary receiver
    temp_receiver = SignalReceiver()

    # Connect signals
    signal_manager.connect(emitter, "test_signal", temp_receiver, "on_test_signal")

    # Verify connection exists
    assert signal_manager.is_connected(emitter, "test_signal", temp_receiver, "on_test_signal")

    # Destroy the receiver
    temp_receiver.deleteLater()
    app.processEvents()

    # Check connections are no longer tracked
    connections = signal_manager.get_connections(sender=emitter, signal_name="test_signal")
    assert len(connections) == 0


def test_signal_connection_leak_prevention(signal_manager, emitter, receiver):
    """Test prevention of signal connection leaks."""
    # Connect and disconnect multiple times
    for _ in range(10):
        signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")
        signal_manager.disconnect(emitter, "test_signal", receiver, "on_test_signal")

    # Connect one more time
    signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")

    # Check only one connection exists
    connections = signal_manager.get_connections(
        sender=emitter, signal_name="test_signal", receiver=receiver
    )
    assert len(connections) == 1


def test_debugging_output(signal_manager, emitter, receiver, caplog):
    """Test debug mode logging."""
    # Enable debug mode
    signal_manager.set_debug_mode(True)

    # Capture logs
    caplog.set_level(logging.DEBUG)

    # Connect and disconnect
    signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")
    signal_manager.disconnect(emitter, "test_signal", receiver, "on_test_signal")

    # Check logs contain connection info
    assert any("Connected:" in record.message for record in caplog.records)
    assert any("Disconnected:" in record.message for record in caplog.records)


def test_print_connections(signal_manager, emitter, receiver, capsys):
    """Test print_connections method."""
    # Connect signals
    signal_manager.connect(emitter, "test_signal", receiver, "on_test_signal")
    signal_manager.connect(emitter, "frequent_signal", receiver, "on_frequent_signal")

    # Print connections
    signal_manager.print_connections()

    # Check output
    captured = capsys.readouterr()
    assert "test_signal" in captured.out
    assert "frequent_signal" in captured.out
    assert "SignalEmitter" in captured.out
    assert "SignalReceiver" in captured.out
