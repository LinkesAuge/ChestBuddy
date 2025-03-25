"""
test_signal_utility.py

Tests for the utility methods in SignalManager class.
"""

import pytest
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.signal_manager import SignalManager


class TestObject(QObject):
    """Test object with signals for testing SignalManager utility methods."""

    test_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.last_value = None

    def slot_method(self, value):
        """Slot method to receive signals."""
        self.last_value = value


class TestSignalUtility:
    """Test case for SignalManager utility methods."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.signal_manager = SignalManager()
        self.sender = TestObject()
        self.receiver = TestObject()

    def test_has_connection(self):
        """Test has_connection method correctly identifies existing connections."""
        # Initially there should be no connection
        assert not self.signal_manager.has_connection(
            self.sender, "test_signal", self.receiver, "slot_method"
        )

        # Connect signal to slot
        self.signal_manager.connect(self.sender, "test_signal", self.receiver, "slot_method")

        # Now has_connection should return True
        assert self.signal_manager.has_connection(
            self.sender, "test_signal", self.receiver, "slot_method"
        )

        # Disconnect and check again
        self.signal_manager.disconnect(self.sender, "test_signal", self.receiver, "slot_method")

        # Should return False again
        assert not self.signal_manager.has_connection(
            self.sender, "test_signal", self.receiver, "slot_method"
        )

    def test_get_connection_count(self):
        """Test get_connection_count method returns accurate count of connections."""
        # Initially there should be no connections
        assert self.signal_manager.get_connection_count() == 0

        # Add one connection
        self.signal_manager.connect(self.sender, "test_signal", self.receiver, "slot_method")

        # Count should be 1
        assert self.signal_manager.get_connection_count() == 1

        # Create another test object
        another_receiver = TestObject()

        # Add another connection
        self.signal_manager.connect(self.sender, "test_signal", another_receiver, "slot_method")

        # Count should be 2
        assert self.signal_manager.get_connection_count() == 2

        # Disconnect one
        self.signal_manager.disconnect(self.sender, "test_signal", self.receiver, "slot_method")

        # Count should be 1 again
        assert self.signal_manager.get_connection_count() == 1

        # Disconnect all for the sender
        self.signal_manager.disconnect(self.sender, "test_signal")

        # Count should be 0
        assert self.signal_manager.get_connection_count() == 0
