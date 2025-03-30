"""
Tests for the SignalManager class.
"""

import logging
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal, Slot

from chestbuddy.utils.signal_manager import SignalManager


class MockSender(QObject):
    """Mock sender class for testing signals."""

    test_signal = Signal(str)
    typed_signal = Signal(int)
    multi_arg_signal = Signal(str, int)


class MockReceiver(QObject):
    """Mock receiver class for testing slots."""

    def __init__(self):
        """Initialize with call tracking."""
        super().__init__()
        self.signal_called = False
        self.signal_value = None
        self.typed_signal_called = False
        self.typed_signal_value = None
        self.multi_arg_called = False
        self.multi_arg_values = None

    @Slot(str)
    def on_signal(self, value):
        """Slot for test_signal."""
        self.signal_called = True
        self.signal_value = value

    @Slot(int)
    def on_typed_signal(self, value):
        """Slot for typed_signal."""
        self.typed_signal_called = True
        self.typed_signal_value = value

    @Slot(str, int)
    def on_multi_arg_signal(self, str_value, int_value):
        """Slot for multi_arg_signal."""
        self.multi_arg_called = True
        self.multi_arg_values = (str_value, int_value)

    def reset(self):
        """Reset all tracking variables."""
        self.signal_called = False
        self.signal_value = None
        self.typed_signal_called = False
        self.typed_signal_value = None
        self.multi_arg_called = False
        self.multi_arg_values = None


@pytest.fixture
def signal_manager():
    """Create a SignalManager instance for testing."""
    return SignalManager()


@pytest.fixture
def mock_sender():
    """Create a MockSender instance for testing."""
    return MockSender()


@pytest.fixture
def mock_receiver():
    """Create a MockReceiver instance for testing."""
    return MockReceiver()


def test_connect(signal_manager, mock_sender, mock_receiver):
    """Test connecting a signal."""
    # Connect the signal
    result = signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Should return True for successful connection
    assert result is True

    # Check connection is tracked
    assert signal_manager.is_connected(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Emit the signal and check if slot was called
    mock_sender.test_signal.emit("test")
    assert mock_receiver.signal_called is True
    assert mock_receiver.signal_value == "test"


def test_connect_duplicate(signal_manager, mock_sender, mock_receiver):
    """Test connecting the same signal twice."""
    # Connect the signal
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Connect again - should return False for duplicate
    result = signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    assert result is False


def test_connect_invalid_signal(signal_manager, mock_sender, mock_receiver):
    """Test connecting an invalid signal."""
    with pytest.raises(AttributeError):
        signal_manager.connect(mock_sender, "invalid_signal", mock_receiver, "on_signal")


def test_connect_invalid_slot(signal_manager, mock_sender, mock_receiver):
    """Test connecting to an invalid slot."""
    with pytest.raises(AttributeError):
        signal_manager.connect(mock_sender, "test_signal", mock_receiver, "invalid_slot")


def test_disconnect_specific(signal_manager, mock_sender, mock_receiver):
    """Test disconnecting a specific signal."""
    # Connect the signal
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Disconnect the specific connection
    count = signal_manager.disconnect(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Should disconnect 1 connection
    assert count == 1

    # Check connection is no longer tracked
    assert not signal_manager.is_connected(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Emit the signal and check slot was not called
    mock_receiver.reset()
    mock_sender.test_signal.emit("test")
    assert mock_receiver.signal_called is False


def test_disconnect_by_receiver(signal_manager, mock_sender, mock_receiver):
    """Test disconnecting all signals for a receiver."""
    # Connect multiple signals
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    signal_manager.connect(mock_sender, "typed_signal", mock_receiver, "on_typed_signal")

    # Disconnect all connections for the receiver
    count = signal_manager.disconnect(mock_sender, "test_signal", mock_receiver)

    # Should disconnect 1 connection
    assert count == 1

    # Check connection is no longer tracked
    assert not signal_manager.is_connected(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Other connection should still be active
    assert signal_manager.is_connected(
        mock_sender, "typed_signal", mock_receiver, "on_typed_signal"
    )


def test_disconnect_all_for_signal(signal_manager, mock_sender, mock_receiver):
    """Test disconnecting all connections for a signal."""
    # Create a second receiver
    second_receiver = MockReceiver()

    # Connect multiple receivers to the same signal
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    signal_manager.connect(mock_sender, "test_signal", second_receiver, "on_signal")

    # Disconnect all connections for the signal
    count = signal_manager.disconnect(mock_sender, "test_signal")

    # Should disconnect 2 connections
    assert count == 2

    # Check connections are no longer tracked
    assert not signal_manager.is_connected(mock_sender, "test_signal", mock_receiver, "on_signal")
    assert not signal_manager.is_connected(mock_sender, "test_signal", second_receiver, "on_signal")


def test_disconnect_all(signal_manager, mock_sender, mock_receiver):
    """Test disconnecting all tracked connections."""
    # Connect multiple signals
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    signal_manager.connect(mock_sender, "typed_signal", mock_receiver, "on_typed_signal")

    # Disconnect all connections
    count = signal_manager.disconnect_all()

    # Should disconnect 2 connections
    assert count == 2

    # Check connections are no longer tracked
    assert not signal_manager.is_connected(mock_sender, "test_signal", mock_receiver, "on_signal")
    assert not signal_manager.is_connected(
        mock_sender, "typed_signal", mock_receiver, "on_typed_signal"
    )


def test_disconnect_receiver_all(signal_manager, mock_sender, mock_receiver):
    """Test disconnecting all signals for a receiver across all signals."""
    # Create a second sender
    second_sender = MockSender()

    # Connect multiple signals from different senders
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    signal_manager.connect(second_sender, "test_signal", mock_receiver, "on_signal")

    # Disconnect all connections for the receiver
    count = signal_manager.disconnect_receiver(mock_receiver)

    # Should disconnect 2 connections
    assert count == 2

    # Check connections are no longer tracked
    assert not signal_manager.is_connected(mock_sender, "test_signal", mock_receiver, "on_signal")
    assert not signal_manager.is_connected(second_sender, "test_signal", mock_receiver, "on_signal")


def test_get_connections(signal_manager, mock_sender, mock_receiver):
    """Test getting connections with various filters."""
    # Create a second sender and receiver
    second_sender = MockSender()
    second_receiver = MockReceiver()

    # Connect multiple signals
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    signal_manager.connect(mock_sender, "typed_signal", mock_receiver, "on_typed_signal")
    signal_manager.connect(second_sender, "test_signal", second_receiver, "on_signal")

    # Get all connections
    all_connections = signal_manager.get_connections()
    assert len(all_connections) == 3

    # Get connections for a specific sender
    sender_connections = signal_manager.get_connections(sender=mock_sender)
    assert len(sender_connections) == 2

    # Get connections for a specific signal
    signal_connections = signal_manager.get_connections(signal_name="test_signal")
    assert len(signal_connections) == 2

    # Get connections for a specific receiver
    receiver_connections = signal_manager.get_connections(receiver=mock_receiver)
    assert len(receiver_connections) == 2

    # Get connections with multiple filters
    filtered_connections = signal_manager.get_connections(
        sender=mock_sender, signal_name="test_signal"
    )
    assert len(filtered_connections) == 1
    assert filtered_connections[0] == (mock_sender, "test_signal", mock_receiver, "on_signal")


def test_blocked_signals_context_manager(signal_manager, mock_sender, mock_receiver):
    """Test the blocked_signals context manager."""
    # Connect the signal
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Use the context manager to block signals
    with signal_manager.blocked_signals(mock_sender):
        # Emit the signal - should be blocked
        mock_sender.test_signal.emit("test")
        assert mock_receiver.signal_called is False

    # After context, signals should be unblocked
    mock_sender.test_signal.emit("test")
    assert mock_receiver.signal_called is True


def test_safe_connect(signal_manager, mock_sender, mock_receiver):
    """Test safe_connect with and without disconnection."""
    # Safe connect without disconnection first
    result = signal_manager.safe_connect(mock_sender, "test_signal", mock_receiver, "on_signal")
    assert result is True

    # Safe connect with disconnection first
    result = signal_manager.safe_connect(
        mock_sender, "test_signal", mock_receiver, "on_signal", safe_disconnect_first=True
    )
    assert result is True

    # Safe connect with invalid signal (should handle exception)
    result = signal_manager.safe_connect(mock_sender, "invalid_signal", mock_receiver, "on_signal")
    assert result is False


def test_debug_mode(signal_manager, mock_sender, mock_receiver, caplog):
    """Test debug mode logging."""
    # Enable debug mode
    signal_manager.set_debug_mode(True)

    with caplog.at_level(logging.DEBUG):
        # Connect and disconnect to generate log messages
        signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")
        signal_manager.disconnect(mock_sender, "test_signal", mock_receiver, "on_signal")

        # Check for debug messages
        assert "Connected:" in caplog.text
        assert "Disconnected:" in caplog.text


def test_print_connections(signal_manager, mock_sender, mock_receiver, capsys):
    """Test print_connections debug utility."""
    # Connect a signal
    signal_manager.connect(mock_sender, "test_signal", mock_receiver, "on_signal")

    # Call print_connections
    signal_manager.print_connections()

    # Check output
    captured = capsys.readouterr()
    assert "Current Signal Connections:" in captured.out
    assert "MockSender.test_signal" in captured.out
    assert "MockReceiver.on_signal" in captured.out
