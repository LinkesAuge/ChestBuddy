"""
test_signal_priority.py

Description: Tests for the signal priority features of the SignalManager
"""

import pytest
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.signal_manager import SignalManager


class TestSignalSender(QObject):
    """Test signal sender class."""

    test_signal = Signal(str)


class TestSignalReceiver(QObject):
    """Test signal receiver class."""

    def __init__(self):
        """Initialize the test signal receiver."""
        super().__init__()
        self.received_values = []
        self.call_order = []

    def reset(self):
        """Reset the received values and call order."""
        self.received_values = []
        self.call_order = []

    def slot1(self, value):
        """First test slot."""
        self.received_values.append(value)
        self.call_order.append("slot1")

    def slot2(self, value):
        """Second test slot."""
        self.received_values.append(value)
        self.call_order.append("slot2")

    def slot3(self, value):
        """Third test slot."""
        self.received_values.append(value)
        self.call_order.append("slot3")


class TestSignalPriority:
    """Test the priority features of the SignalManager class."""

    def setup_method(self):
        """Set up the test environment."""
        self.signal_manager = SignalManager(debug_mode=True)
        self.sender = TestSignalSender()
        self.receiver = TestSignalReceiver()

    def teardown_method(self):
        """Clean up after tests."""
        self.signal_manager.disconnect_all()

    def test_priority_connection(self):
        """Test that we can create prioritized connections."""
        # Connect with various priorities
        result1 = self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )
        result2 = self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2", priority=25
        )
        result3 = self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot3", priority=50
        )

        # Check that connections were successful
        assert result1 is True
        assert result2 is True
        assert result3 is True

        # Check that connections are tracked
        connections = self.signal_manager.get_prioritized_connections()
        assert len(connections) == 3

        # Check the connection status
        assert self.signal_manager.is_connected(self.sender, "test_signal", self.receiver, "slot1")
        assert self.signal_manager.is_connected(self.sender, "test_signal", self.receiver, "slot2")
        assert self.signal_manager.is_connected(self.sender, "test_signal", self.receiver, "slot3")

    def test_duplicate_priority_connection(self):
        """Test that duplicate prioritized connections are rejected."""
        # Connect once
        result1 = self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )

        # Try to connect again
        result2 = self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=50
        )

        # First connection should succeed, second should fail
        assert result1 is True
        assert result2 is False

        # Only one connection should be tracked
        connections = self.signal_manager.get_prioritized_connections()
        assert len(connections) == 1

    def test_priority_order(self):
        """Test that signals are executed in priority order."""
        # Connect in reverse priority order to ensure sorting works
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot3", priority=25
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2", priority=50
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )

        # Emit the signal
        self.sender.test_signal.emit("test")

        # Check that slots were called in priority order (highest first)
        assert self.receiver.call_order == ["slot1", "slot2", "slot3"]

    def test_same_priority_order(self):
        """Test that signals with same priority are executed in connection order."""
        # Connect with the same priority
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=50
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2", priority=50
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot3", priority=50
        )

        # Emit the signal
        self.sender.test_signal.emit("test")

        # Check that slots were called in connection order
        assert self.receiver.call_order == ["slot1", "slot2", "slot3"]

    def test_priority_constants(self):
        """Test the priority constants provided by the SignalManager."""
        # Connect using priority constants
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot3", priority=SignalManager.PRIORITY_LOW
        )
        self.signal_manager.connect_prioritized(
            self.sender,
            "test_signal",
            self.receiver,
            "slot2",
            priority=SignalManager.PRIORITY_NORMAL,
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=SignalManager.PRIORITY_HIGH
        )

        # Emit the signal
        self.sender.test_signal.emit("test")

        # Check that slots were called in priority order
        assert self.receiver.call_order == ["slot1", "slot2", "slot3"]

    def test_disconnect_prioritized(self):
        """Test that we can disconnect prioritized connections."""
        # Connect signals
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2", priority=50
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot3", priority=25
        )

        # Disconnect one connection
        count = self.signal_manager.disconnect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2"
        )

        # Should have disconnected one signal
        assert count == 1

        # Emit the signal
        self.sender.test_signal.emit("test")

        # Only slot1 and slot3 should have been called
        assert self.receiver.call_order == ["slot1", "slot3"]

    def test_disconnect_prioritized_by_receiver(self):
        """Test that we can disconnect all prioritized connections for a receiver."""
        # Connect signals to the same receiver
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2", priority=50
        )

        # Create another receiver
        receiver2 = TestSignalReceiver()
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", receiver2, "slot1", priority=25
        )

        # Disconnect all connections for the first receiver
        count = self.signal_manager.disconnect_prioritized(
            self.sender, "test_signal", self.receiver
        )

        # Should have disconnected two signals
        assert count == 2

        # Emit the signal
        self.sender.test_signal.emit("test")

        # First receiver should not have been called
        assert self.receiver.call_order == []

        # Second receiver should have been called
        assert receiver2.call_order == ["slot1"]

    def test_disconnect_all_prioritized(self):
        """Test that disconnect_all removes prioritized connections."""
        # Connect some prioritized signals
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot2", priority=50
        )

        # Connect some regular signals
        self.signal_manager.connect(self.sender, "test_signal", self.receiver, "slot3")

        # Disconnect all
        count = self.signal_manager.disconnect_all()

        # Should have disconnected three signals
        assert count == 3

        # Emit the signal
        self.sender.test_signal.emit("test")

        # No slots should have been called
        assert self.receiver.call_order == []

    def test_disconnect_receiver_prioritized(self):
        """Test that disconnect_receiver removes prioritized connections."""
        # Connect prioritized signals
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", self.receiver, "slot1", priority=75
        )

        # Create another receiver
        receiver2 = TestSignalReceiver()
        self.signal_manager.connect_prioritized(
            self.sender, "test_signal", receiver2, "slot1", priority=25
        )

        # Disconnect the first receiver
        count = self.signal_manager.disconnect_receiver(self.receiver)

        # Should have disconnected one signal
        assert count == 1

        # Emit the signal
        self.sender.test_signal.emit("test")

        # First receiver should not have been called
        assert self.receiver.call_order == []

        # Second receiver should have been called
        assert receiver2.call_order == ["slot1"]

    def test_invalid_priority(self):
        """Test that invalid priorities are rejected."""
        # Try with priority below 0
        with pytest.raises(ValueError):
            self.signal_manager.connect_prioritized(
                self.sender, "test_signal", self.receiver, "slot1", priority=-10
            )

        # Try with priority above 100
        with pytest.raises(ValueError):
            self.signal_manager.connect_prioritized(
                self.sender, "test_signal", self.receiver, "slot1", priority=110
            )
