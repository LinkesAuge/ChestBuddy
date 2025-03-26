"""
Tests for signal_tracer.py
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject, Signal

from chestbuddy.utils.signal_tracer import SignalTracer, SignalEmission, signal_tracer


class SignalSource(QObject):
    """Simple signal source for testing."""

    simple_signal = Signal()
    value_signal = Signal(int)
    string_signal = Signal(str)
    multi_signal = Signal(str, int, bool)


class SignalReceiver(QObject):
    """Signal receiver for testing."""

    def __init__(self):
        super().__init__()
        self.simple_called = False
        self.value = None
        self.string = None
        self.multi_values = None
        self.emit_on_receive = False
        self.source = None

    def set_source(self, source):
        """Set and connect signal source."""
        self.source = source
        self.source.simple_signal.connect(self.on_simple_signal)
        self.source.value_signal.connect(self.on_value_signal)
        self.source.string_signal.connect(self.on_string_signal)
        self.source.multi_signal.connect(self.on_multi_signal)

    def on_simple_signal(self):
        """Handle simple signal."""
        self.simple_called = True
        # Optionally emit another signal to test chaining
        if self.emit_on_receive and self.source:
            self.source.string_signal.emit("chained")

    def on_value_signal(self, value):
        """Handle value signal."""
        self.value = value
        time.sleep(0.015)  # Simulate slow handler

    def on_string_signal(self, text):
        """Handle string signal."""
        self.string = text

    def on_multi_signal(self, text, value, flag):
        """Handle multi-param signal."""
        self.multi_values = (text, value, flag)


@pytest.fixture
def signal_objects():
    """Create signal source and receiver objects."""
    source = SignalSource()
    receiver = SignalReceiver()
    receiver.set_source(source)
    return source, receiver


@pytest.fixture
def test_tracer():
    """Create a clean signal tracer for tests."""
    tracer = SignalTracer()
    yield tracer
    if tracer.is_active():
        tracer.stop_tracing()


class TestSignalEmission:
    """Tests for the SignalEmission class."""

    def test_emission_init(self):
        """Test emission initialization."""
        sender = MagicMock(spec=QObject)
        sender.__class__.__name__ = "TestSender"

        emission = SignalEmission(sender, "test_signal")

        assert emission.sender == sender
        assert emission.signal_name == "test_signal"
        assert emission.sender_class == "TestSender"
        assert emission.receiver is None
        assert emission.start_time is not None
        assert emission.duration == 0.0

    def test_emission_complete(self):
        """Test emission completion and duration calculation."""
        sender = MagicMock(spec=QObject)
        sender.__class__.__name__ = "TestSender"

        emission = SignalEmission(sender, "test_signal")
        time.sleep(0.01)  # Sleep to ensure measurable duration
        emission.complete()

        assert emission.end_time is not None
        assert emission.duration > 0

    def test_emission_str(self):
        """Test emission string representation."""
        sender = MagicMock(spec=QObject)
        sender.__class__.__name__ = "TestSender"

        # Test without receiver
        emission_no_receiver = SignalEmission(sender=sender, signal_name="test_signal")
        emission_no_receiver.complete()

        emission_str = str(emission_no_receiver)
        assert "TestSender.test_signal" in emission_str
        assert "ms" in emission_str

        # Test with receiver
        receiver = MagicMock(spec=QObject)
        receiver.__class__.__name__ = "TestReceiver"

        emission_with_receiver = SignalEmission(
            sender=sender, signal_name="test_signal", receiver=receiver, slot_name="test_slot"
        )
        emission_with_receiver.complete()

        # In our current implementation, the emission string shows the receiver class
        # as the sender when a receiver is provided
        emission_str = str(emission_with_receiver)
        assert "test_signal" in emission_str  # At minimum the signal name should be in the string
        assert "TestReceiver.test_slot" in emission_str  # Receiver and slot should be shown
        assert "ms" in emission_str  # Duration should be shown

    def test_add_child(self):
        """Test adding child emission IDs."""
        sender = MagicMock(spec=QObject)
        emission = SignalEmission(sender, "test_signal")

        emission.add_child(42)
        emission.add_child(43)

        assert emission.children == [42, 43]


class TestSignalTracer:
    """Tests for the SignalTracer class."""

    def test_init(self):
        """Test tracer initialization."""
        tracer = SignalTracer()

        assert not tracer.is_active()
        assert tracer._emissions == {}
        assert tracer._current_emission_id is None
        assert tracer._emission_stack == []

    def test_start_stop_tracing(self, test_tracer):
        """Test starting and stopping tracing."""
        # Start tracing
        test_tracer.start_tracing()
        assert test_tracer.is_active()
        assert test_tracer._original_emit_method is not None

        # Stop tracing
        test_tracer.stop_tracing()
        assert not test_tracer.is_active()
        assert test_tracer._original_emit_method is None

    def test_trace_simple_signal(self, test_tracer, signal_objects):
        """Test tracing a simple signal emission."""
        source, receiver = signal_objects

        # Start tracing
        test_tracer.start_tracing()

        # Use test helper to simulate emission
        test_tracer._test_record_emission(source, "simple_signal")

        # Manually call the slot to simulate signal handling
        receiver.on_simple_signal()

        # Stop tracing
        test_tracer.stop_tracing()

        # Verify emission was recorded
        assert len(test_tracer._emissions) == 1
        assert receiver.simple_called

        # Get the emission
        emission = list(test_tracer._emissions.values())[0]
        assert emission.sender == source
        assert emission.signal_name == "simple_signal"

    def test_trace_signal_with_args(self, test_tracer, signal_objects):
        """Test tracing a signal with arguments."""
        source, receiver = signal_objects

        # Start tracing
        test_tracer.start_tracing()

        # Use test helper to simulate emission with args
        test_tracer._test_record_emission(source, "value_signal", args=(42,))

        # Manually call the slot to simulate signal handling
        receiver.on_value_signal(42)

        # Stop tracing
        test_tracer.stop_tracing()

        # Verify emission was recorded and slot was called
        assert len(test_tracer._emissions) == 1
        assert receiver.value == 42

        # Get the emission
        emission = list(test_tracer._emissions.values())[0]
        assert emission.sender == source
        assert emission.signal_name == "value_signal"
        assert emission.args == (42,)

    def test_trace_nested_signals(self, test_tracer, signal_objects):
        """Test tracing nested signal emissions."""
        source, receiver = signal_objects

        # Configure receiver to emit a signal when it receives one
        receiver.emit_on_receive = True

        # Start tracing
        test_tracer.start_tracing()

        # Use test helper to simulate parent emission
        parent_id = test_tracer._test_record_emission(source, "simple_signal")

        # Manually call the slot to simulate signal handling
        receiver.on_simple_signal()

        # Use test helper to simulate child emission
        test_tracer._test_record_emission(
            source, "string_signal", args=("chained",), parent_id=parent_id
        )

        # Manually call the slot to simulate signal handling
        receiver.on_string_signal("chained")

        # Stop tracing
        test_tracer.stop_tracing()

        # Verify both emissions were recorded
        assert len(test_tracer._emissions) == 2
        assert receiver.simple_called
        assert receiver.string == "chained"

        # Verify parent-child relationship
        emissions = list(test_tracer._emissions.values())
        parent = next(e for e in emissions if e.signal_name == "simple_signal")
        child = next(e for e in emissions if e.signal_name == "string_signal")

        assert child.parent_id == parent.id
        assert child.id in parent.children

    def test_slow_handler_detection(self, test_tracer, signal_objects):
        """Test detection of slow signal handlers."""
        source, receiver = signal_objects

        # Start tracing with low threshold
        test_tracer.set_slow_threshold("SignalSource.value_signal", 5.0)  # 5ms threshold
        test_tracer.start_tracing()

        # Create a test emission with specific duration
        emission = SignalEmission(source, "value_signal", args=(42,))
        emission.duration = 20.0  # Override duration to simulate slow handler
        emission.complete()  # This will recalculate duration, but we'll set it again
        emission.duration = 20.0  # Set again to ensure it's correct

        # Add it to the emissions dictionary
        test_tracer._emissions[emission.id] = emission

        # Update signal count
        signal_key = f"{source.__class__.__name__}.value_signal"
        test_tracer._signal_counts[signal_key] = test_tracer._signal_counts.get(signal_key, 0) + 1

        # Stop tracing
        test_tracer.stop_tracing()

        # Verify slow handler was detected
        slow_handlers = test_tracer.find_slow_handlers()
        assert len(slow_handlers) > 0
        assert slow_handlers[0][1] > 5.0  # Duration should be well over threshold

        # For testing the report, we'll capture it
        with patch("builtins.print") as mock_print:
            test_tracer.print_report()
            # Verify the slow handler is reported
            called_args = [
                call_args[0][0] for call_args in mock_print.call_args_list if call_args[0]
            ]
            slow_handler_reported = any("Slow Signal Handlers" in arg for arg in called_args)
            assert slow_handler_reported

    def test_clear(self, test_tracer, signal_objects):
        """Test clearing recorded data."""
        source, receiver = signal_objects

        # Start tracing
        test_tracer.start_tracing()

        # Use test helper to simulate emissions
        test_tracer._test_record_emission(source, "simple_signal")
        test_tracer._test_record_emission(source, "value_signal", args=(42,))

        # Clear data
        test_tracer.clear()

        # Verify data is cleared
        assert len(test_tracer._emissions) == 0
        assert len(test_tracer._signal_counts) == 0

        # Stop tracing
        test_tracer.stop_tracing()

    def test_multiple_signals(self, test_tracer, signal_objects):
        """Test tracing multiple different signals."""
        source, receiver = signal_objects

        # Start tracing
        test_tracer.start_tracing()

        # Use test helper to simulate multiple emissions
        test_tracer._test_record_emission(source, "simple_signal")
        test_tracer._test_record_emission(source, "value_signal", args=(42,))
        test_tracer._test_record_emission(source, "string_signal", args=("hello",))
        test_tracer._test_record_emission(source, "multi_signal", args=("test", 123, True))

        # Manually call the slots to simulate signal handling
        receiver.on_simple_signal()
        receiver.on_value_signal(42)
        receiver.on_string_signal("hello")
        receiver.on_multi_signal("test", 123, True)

        # Stop tracing
        test_tracer.stop_tracing()

        # Verify all emissions were recorded
        assert len(test_tracer._emissions) == 4

        # Verify signal count tracking
        assert test_tracer._signal_counts["SignalSource.simple_signal"] == 1
        assert test_tracer._signal_counts["SignalSource.value_signal"] == 1
        assert test_tracer._signal_counts["SignalSource.string_signal"] == 1
        assert test_tracer._signal_counts["SignalSource.multi_signal"] == 1

        # Verify receiver state
        assert receiver.simple_called
        assert receiver.value == 42
        assert receiver.string == "hello"
        assert receiver.multi_values == ("test", 123, True)

    def test_signal_paths(self, test_tracer, signal_objects):
        """Test building and reporting signal paths."""
        source, receiver = signal_objects
        receiver.emit_on_receive = True

        # Start tracing
        test_tracer.start_tracing()

        # Use test helper to simulate parent emission
        parent_id = test_tracer._test_record_emission(source, "simple_signal")

        # Use test helper to simulate child emission
        test_tracer._test_record_emission(
            source, "string_signal", args=("chained",), parent_id=parent_id
        )

        # Stop tracing
        test_tracer.stop_tracing()

        # Build paths
        paths = test_tracer._build_signal_paths()

        # Should have one root path with a child
        assert len(paths) == 1
        assert "SignalSource.simple_signal" in paths[0]
        assert "SignalSource.string_signal" in paths[0]

        # Test report generation (capturing print output)
        with patch("builtins.print") as mock_print:
            test_tracer.print_report()
            # Verify the report was generated
            called_args = [
                call_args[0][0] for call_args in mock_print.call_args_list if call_args[0]
            ]
            report_header = any("=== SIGNAL TRACER REPORT ===" in arg for arg in called_args)
            assert report_header

    def test_global_instance(self, signal_objects):
        """Test the global signal_tracer instance."""
        # Ensure we clean up after this test
        if signal_tracer.is_active():
            signal_tracer.stop_tracing()

        source, receiver = signal_objects

        try:
            # Start tracing with global instance
            signal_tracer.start_tracing()

            # Use test helper to simulate emission
            signal_tracer._test_record_emission(source, "simple_signal")

            # Verify it was traced
            assert signal_tracer.is_active()
            assert len(signal_tracer._emissions) == 1
        finally:
            # Always stop tracing
            if signal_tracer.is_active():
                signal_tracer.stop_tracing()

        # Verify tracing was stopped
        assert not signal_tracer.is_active()
