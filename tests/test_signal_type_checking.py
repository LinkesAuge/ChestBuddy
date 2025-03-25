"""
test_signal_type_checking.py

Description: Tests for the signal type checking features of the SignalManager
"""

import pytest
from PySide6.QtCore import QObject, Signal
import inspect

from chestbuddy.utils.signal_manager import SignalManager


class TypeSignalSender(QObject):
    """Test signal sender class with different signal types."""

    # Signal with no arguments
    zero_args_signal = Signal()

    # Signal with one argument
    one_arg_signal = Signal(str)

    # Signal with two arguments
    two_args_signal = Signal(str, int)

    # Signal with three arguments
    three_args_signal = Signal(str, int, bool)


class TypeSignalReceiver(QObject):
    """Test signal receiver class with different slot types."""

    def __init__(self):
        """Initialize the receiver."""
        super().__init__()
        self.last_called = None

    def zero_args_slot(self):
        """Slot with no arguments."""
        self.last_called = "zero_args_slot"

    def one_arg_slot(self, arg1=None):
        """Slot with one argument."""
        self.last_called = f"one_arg_slot: {arg1}"

    def two_args_slot(self, arg1, arg2=None):
        """Slot with two arguments."""
        self.last_called = f"two_args_slot: {arg1}, {arg2}"

    def three_args_slot(self, arg1, arg2=None, arg3=None):
        """Slot with three arguments."""
        self.last_called = f"three_args_slot: {arg1}, {arg2}, {arg3}"

    def var_args_slot(self, *args):
        """Slot with variable arguments."""
        self.last_called = f"var_args_slot: {args}"


class TestSignalTypeChecking:
    """Test the type checking features of the SignalManager class."""

    def setup_method(self):
        """Set up the test environment."""
        self.signal_manager = SignalManager(debug_mode=True)
        self.sender = TypeSignalSender()
        self.receiver = TypeSignalReceiver()

        # Debug parameter counts
        # Test TypeSignalReceiver.zero_args_slot
        slot = getattr(self.receiver, "zero_args_slot")
        sig = inspect.signature(slot)
        print(f"\nDebug: zero_args_slot parameters: {sig.parameters}")
        print(f"Debug: zero_args_slot is method: {hasattr(slot, '__self__')}")

        # Test TypeSignalReceiver.one_arg_slot
        slot = getattr(self.receiver, "one_arg_slot")
        sig = inspect.signature(slot)
        print(f"Debug: one_arg_slot parameters: {sig.parameters}")
        print(f"Debug: one_arg_slot is method: {hasattr(slot, '__self__')}")

        # Test signals
        zero_sig = getattr(self.sender.__class__, "zero_args_signal")
        one_sig = getattr(self.sender.__class__, "one_arg_signal")
        print(f"Debug: zero_args_signal: {zero_sig}")
        print(f"Debug: one_arg_signal: {one_sig}")

    def teardown_method(self):
        """Clean up after tests."""
        self.signal_manager.disconnect_all()

    def test_compatible_connections(self):
        """Test that compatible signal-slot connections are allowed."""
        # Zero args signal to zero args slot
        assert self.signal_manager.connect(
            self.sender, "zero_args_signal", self.receiver, "zero_args_slot"
        )

        # One arg signal to one arg slot
        assert self.signal_manager.connect(
            self.sender, "one_arg_signal", self.receiver, "one_arg_slot"
        )

        # Two args signal to two args slot
        assert self.signal_manager.connect(
            self.sender, "two_args_signal", self.receiver, "two_args_slot"
        )

        # Three args signal to three args slot
        assert self.signal_manager.connect(
            self.sender, "three_args_signal", self.receiver, "three_args_slot"
        )

    def test_variable_args_slot(self):
        """Test that signals can connect to variable argument slots."""
        # Any signal should work with var_args_slot
        assert self.signal_manager.connect(
            self.sender, "zero_args_signal", self.receiver, "var_args_slot"
        )
        assert self.signal_manager.connect(
            self.sender, "one_arg_signal", self.receiver, "var_args_slot"
        )
        assert self.signal_manager.connect(
            self.sender, "two_args_signal", self.receiver, "var_args_slot"
        )
        assert self.signal_manager.connect(
            self.sender, "three_args_signal", self.receiver, "var_args_slot"
        )

    def test_slot_with_extra_parameters(self):
        """Test that slots with extra parameters can accept signals with fewer parameters."""
        # Zero args signal to one arg slot (should work with default value)
        assert self.signal_manager.connect(
            self.sender, "zero_args_signal", self.receiver, "one_arg_slot"
        )

        # One arg signal to two args slot (should work with default value)
        assert self.signal_manager.connect(
            self.sender, "one_arg_signal", self.receiver, "two_args_slot"
        )

        # Two args signal to three args slot (should work with default value)
        assert self.signal_manager.connect(
            self.sender, "two_args_signal", self.receiver, "three_args_slot"
        )

    def test_incompatible_connections(self):
        """Test that incompatible signal-slot connections raise TypeError."""
        # One arg signal to zero args slot (should fail)
        with pytest.raises(TypeError):
            self.signal_manager.connect(
                self.sender, "one_arg_signal", self.receiver, "zero_args_slot"
            )

        # Two args signal to one arg slot (should fail)
        with pytest.raises(TypeError):
            self.signal_manager.connect(
                self.sender, "two_args_signal", self.receiver, "one_arg_slot"
            )

        # Three args signal to two args slot (should fail)
        with pytest.raises(TypeError):
            self.signal_manager.connect(
                self.sender, "three_args_signal", self.receiver, "two_args_slot"
            )

    def test_prioritized_connections_type_checking(self):
        """Test that prioritized connections also perform type checking."""
        # Compatible connection
        assert self.signal_manager.connect_prioritized(
            self.sender, "one_arg_signal", self.receiver, "one_arg_slot"
        )

        # Incompatible connection
        with pytest.raises(TypeError):
            self.signal_manager.connect_prioritized(
                self.sender, "two_args_signal", self.receiver, "one_arg_slot"
            )

    def test_throttled_connections_type_checking(self):
        """Test that throttled connections also perform type checking."""
        # Compatible connection
        assert self.signal_manager.connect_throttled(
            self.sender, "one_arg_signal", self.receiver, "one_arg_slot"
        )

        # Incompatible connection
        with pytest.raises(TypeError):
            self.signal_manager.connect_throttled(
                self.sender, "two_args_signal", self.receiver, "one_arg_slot"
            )

    def test_disable_type_checking(self):
        """Test that type checking can be disabled."""
        # Create a signal manager with type checking disabled
        no_check_manager = SignalManager(debug_mode=True, type_checking=False)

        # This should work even though it's incompatible
        assert no_check_manager.connect(
            self.sender, "two_args_signal", self.receiver, "one_arg_slot"
        )

        # Cleanup
        no_check_manager.disconnect_all()
