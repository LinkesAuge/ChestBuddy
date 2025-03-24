"""
test_ui_state_signals.py

Description: Comprehensive tests for signal propagation in the UI State Management System.
This module focuses on verifying that signals are properly emitted, received, and processed.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from mock_main_window
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow

# Import UI state components
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
    OperationContext,
    UIElementGroups,
    UIOperations,
    UIStateManager,
    UIStateSignals,
)


class SignalCounter(QObject):
    """Helper class to count signal emissions."""

    def __init__(self, signals):
        """Initialize with a signals object to monitor."""
        super().__init__()
        self.signals = signals
        self.reset_counters()
        self._connect_signals()

    def reset_counters(self):
        """Reset all signal counters."""
        self.element_blocked_count = 0
        self.element_unblocked_count = 0
        self.operation_started_count = 0
        self.operation_ended_count = 0
        self.blocking_state_changed_count = 0
        self.state_debug_count = 0

        # Detailed records for analysis
        self.element_blocked_records = []
        self.element_unblocked_records = []
        self.operation_started_records = []
        self.operation_ended_records = []
        self.blocking_state_changed_records = []
        self.state_debug_records = []

    def _connect_signals(self):
        """Connect to all signals."""
        self.signals.element_blocked.connect(self._on_element_blocked)
        self.signals.element_unblocked.connect(self._on_element_unblocked)
        self.signals.operation_started.connect(self._on_operation_started)
        self.signals.operation_ended.connect(self._on_operation_ended)
        self.signals.blocking_state_changed.connect(self._on_blocking_state_changed)
        self.signals.state_debug.connect(self._on_state_debug)

    def _on_element_blocked(self, element, operation):
        self.element_blocked_count += 1
        self.element_blocked_records.append((element, operation))

    def _on_element_unblocked(self, element, operation):
        self.element_unblocked_count += 1
        self.element_unblocked_records.append((element, operation))

    def _on_operation_started(self, operation, affected_elements):
        self.operation_started_count += 1
        self.operation_started_records.append((operation, affected_elements))

    def _on_operation_ended(self, operation, affected_elements):
        self.operation_ended_count += 1
        self.operation_ended_records.append((operation, affected_elements))

    def _on_blocking_state_changed(self, element, is_blocked, blocking_operations):
        self.blocking_state_changed_count += 1
        self.blocking_state_changed_records.append((element, is_blocked, blocking_operations))

    def _on_state_debug(self, message, details):
        self.state_debug_count += 1
        self.state_debug_records.append((message, details))


class CustomSignalHandler(QObject):
    """Custom signal handler for testing signal connectivity."""

    received_signal = Signal(str, object)  # Signal name, data

    def __init__(self, signals):
        """Initialize with a signals object to monitor."""
        super().__init__()
        self.signals = signals
        self.received_signals = []
        self._connect_signals()

    def _connect_signals(self):
        """Connect to all signals."""
        self.signals.element_blocked.connect(
            lambda element, operation: self._on_signal("element_blocked", (element, operation))
        )
        self.signals.element_unblocked.connect(
            lambda element, operation: self._on_signal("element_unblocked", (element, operation))
        )
        self.signals.operation_started.connect(
            lambda operation, affected_elements: self._on_signal(
                "operation_started", (operation, affected_elements)
            )
        )
        self.signals.operation_ended.connect(
            lambda operation, affected_elements: self._on_signal(
                "operation_ended", (operation, affected_elements)
            )
        )
        self.signals.blocking_state_changed.connect(
            lambda element, is_blocked, blocking_operations: self._on_signal(
                "blocking_state_changed", (element, is_blocked, blocking_operations)
            )
        )
        self.signals.state_debug.connect(
            lambda message, details: self._on_signal("state_debug", (message, details))
        )

    def _on_signal(self, signal_name, data):
        """Handle a received signal."""
        self.received_signals.append((signal_name, data))
        self.received_signal.emit(signal_name, data)


@pytest.fixture
def app():
    """Create a QApplication for UI testing."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def ui_state_setup(qtbot):
    """Create a UIStateManager with signal monitoring."""
    # Create the UIStateManager
    ui_state_manager = UIStateManager()

    # Create signal counter
    signal_counter = SignalCounter(ui_state_manager.signals)

    # Create custom signal handler
    signal_handler = CustomSignalHandler(ui_state_manager.signals)

    # Create blockable widgets
    widgets = []
    for i in range(5):
        widget = QWidget()
        # Make it blockable
        blockable_widget = type(
            f"BlockableWidget{i}",
            (QWidget, BlockableElementMixin),
            {"__init__": lambda self, parent=None: self._init(parent)},
        )

        def _init(self, parent=None):
            QWidget.__init__(self, parent)
            BlockableElementMixin.__init__(self)

        blockable_widget._init = _init

        widget = blockable_widget()
        widget.setObjectName(f"widget_{i}")
        widget.register_with_manager(ui_state_manager)
        widgets.append(widget)

    # Add widgets to different groups
    ui_state_manager.add_element_to_group(widgets[0], UIElementGroups.MAIN_WINDOW)
    ui_state_manager.add_element_to_group(widgets[1], UIElementGroups.DATA_VIEW)
    ui_state_manager.add_element_to_group(widgets[2], UIElementGroups.TOOLBAR)
    ui_state_manager.add_element_to_group(widgets[3], UIElementGroups.MAIN_WINDOW)
    ui_state_manager.add_element_to_group(widgets[4], UIElementGroups.DATA_VIEW)

    return {
        "ui_state_manager": ui_state_manager,
        "signal_counter": signal_counter,
        "signal_handler": signal_handler,
        "widgets": widgets,
    }


class TestSignalEmission:
    """Tests for signal emission during UI state changes."""

    def test_block_element_signals(self, qtbot, app, ui_state_setup):
        """Test signals emitted when blocking an element."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_counter = ui_state_setup["signal_counter"]
        widgets = ui_state_setup["widgets"]

        # Reset signal counters
        signal_counter.reset_counters()

        # Block a widget
        ui_state_manager.block_element(widgets[0], UIOperations.IMPORT)

        # Check signal emissions
        assert signal_counter.element_blocked_count == 1
        assert signal_counter.blocking_state_changed_count == 1

        # Check signal data
        element, operation = signal_counter.element_blocked_records[0]
        assert element == widgets[0]
        assert operation == UIOperations.IMPORT

        element, is_blocked, operations = signal_counter.blocking_state_changed_records[0]
        assert element == widgets[0]
        assert is_blocked is True
        assert UIOperations.IMPORT in operations

    def test_unblock_element_signals(self, qtbot, app, ui_state_setup):
        """Test signals emitted when unblocking an element."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_counter = ui_state_setup["signal_counter"]
        widgets = ui_state_setup["widgets"]

        # Block a widget first
        ui_state_manager.block_element(widgets[0], UIOperations.IMPORT)

        # Reset signal counters
        signal_counter.reset_counters()

        # Unblock the widget
        ui_state_manager.unblock_element(widgets[0], UIOperations.IMPORT)

        # Check signal emissions
        assert signal_counter.element_unblocked_count == 1
        assert signal_counter.blocking_state_changed_count == 1

        # Check signal data
        element, operation = signal_counter.element_unblocked_records[0]
        assert element == widgets[0]
        assert operation == UIOperations.IMPORT

        element, is_blocked, operations = signal_counter.blocking_state_changed_records[0]
        assert element == widgets[0]
        assert is_blocked is False
        assert not operations  # Should be empty

    def test_operation_context_signals(self, qtbot, app, ui_state_setup):
        """Test signals emitted during an operation context."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_counter = ui_state_setup["signal_counter"]
        widgets = ui_state_setup["widgets"]

        # Reset signal counters
        signal_counter.reset_counters()

        # Start an operation
        with OperationContext(
            ui_state_manager, UIOperations.IMPORT, elements=[widgets[0], widgets[1]]
        ):
            # Check signal emissions
            assert signal_counter.operation_started_count == 1
            assert signal_counter.element_blocked_count == 2
            assert signal_counter.blocking_state_changed_count == 2

            # Check operation_started signal data
            operation, affected_elements = signal_counter.operation_started_records[0]
            assert operation == UIOperations.IMPORT
            assert widgets[0] in affected_elements
            assert widgets[1] in affected_elements

        # Check signal emissions after operation
        assert signal_counter.operation_ended_count == 1
        assert signal_counter.element_unblocked_count == 2

        # Check operation_ended signal data
        operation, affected_elements = signal_counter.operation_ended_records[0]
        assert operation == UIOperations.IMPORT

    def test_group_operation_signals(self, qtbot, app, ui_state_setup):
        """Test signals emitted when operating on groups."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_counter = ui_state_setup["signal_counter"]

        # Reset signal counters
        signal_counter.reset_counters()

        # Start an operation on a group
        with OperationContext(
            ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.DATA_VIEW]
        ):
            # Check signal emissions
            assert signal_counter.operation_started_count == 1

            # We should have signals for the group and all elements in the group
            # DATA_VIEW contains widgets[1] and widgets[4]
            assert signal_counter.element_blocked_count >= 3  # Group + 2 elements

            # We should have blocking_state_changed signals for all elements in the group
            expected_elements_affected = 2  # widgets[1] and widgets[4]
            assert signal_counter.blocking_state_changed_count >= expected_elements_affected


class TestSignalConnectivity:
    """Tests for signal connectivity and propagation."""

    def test_custom_signal_handler(self, qtbot, app, ui_state_setup):
        """Test that custom signal handlers receive signals correctly."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_handler = ui_state_setup["signal_handler"]
        widgets = ui_state_setup["widgets"]

        # Clear signal records
        signal_handler.received_signals.clear()

        # Perform operations to generate signals
        ui_state_manager.block_element(widgets[0], UIOperations.IMPORT)
        ui_state_manager.unblock_element(widgets[0], UIOperations.IMPORT)

        with OperationContext(ui_state_manager, UIOperations.PROCESSING, elements=[widgets[1]]):
            pass

        # Check that signals were received
        received_signal_names = [name for name, _ in signal_handler.received_signals]

        assert "element_blocked" in received_signal_names
        assert "element_unblocked" in received_signal_names
        assert "operation_started" in received_signal_names
        assert "operation_ended" in received_signal_names
        assert "blocking_state_changed" in received_signal_names

    def test_multiple_handlers(self, qtbot, app, ui_state_setup):
        """Test that multiple handlers can receive the same signals."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        widgets = ui_state_setup["widgets"]

        # Create additional handlers
        handler1 = CustomSignalHandler(ui_state_manager.signals)
        handler2 = CustomSignalHandler(ui_state_manager.signals)

        # Create recorded signal records
        handler1_received = []
        handler2_received = []

        # Connect to the handlers' received_signal signals
        handler1.received_signal.connect(lambda name, data: handler1_received.append(name))
        handler2.received_signal.connect(lambda name, data: handler2_received.append(name))

        # Perform an operation
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[widgets[0]]):
            pass

        # Check that both handlers received the signals
        assert "operation_started" in handler1_received
        assert "element_blocked" in handler1_received

        assert "operation_started" in handler2_received
        assert "element_blocked" in handler2_received


class TestSignalOrdering:
    """Tests for the order of signal emissions."""

    def test_operation_signal_order(self, qtbot, app, ui_state_setup):
        """Test that operation signals are emitted in the correct order."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_handler = ui_state_setup["signal_handler"]
        widgets = ui_state_setup["widgets"]

        # Clear signal records
        signal_handler.received_signals.clear()

        # Perform an operation
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[widgets[0]]):
            pass

        # Get the signal order
        signal_order = [name for name, _ in signal_handler.received_signals]

        # The expected order:
        # 1. operation_started
        # 2. element_blocked (and blocking_state_changed)
        # 3. element_unblocked (and blocking_state_changed)
        # 4. operation_ended

        # Find indices of key signals
        try:
            operation_started_idx = signal_order.index("operation_started")
            element_blocked_idx = signal_order.index("element_blocked")
            element_unblocked_idx = signal_order.index("element_unblocked")
            operation_ended_idx = signal_order.index("operation_ended")

            # Check order
            assert operation_started_idx < element_blocked_idx
            assert element_blocked_idx < element_unblocked_idx
            assert element_unblocked_idx < operation_ended_idx
        except ValueError:
            # If any signal is missing, the test should fail
            assert False, f"Missing expected signals. Signal order: {signal_order}"


class TestSignalDataIntegrity:
    """Tests for ensuring signal data is correct and complete."""

    def test_affected_elements_correctness(self, qtbot, app, ui_state_setup):
        """Test that affected elements in signals are correct."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_counter = ui_state_setup["signal_counter"]
        widgets = ui_state_setup["widgets"]

        # Reset signal counters
        signal_counter.reset_counters()

        # Start an operation on specific elements
        target_widgets = [widgets[0], widgets[2]]
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=target_widgets):
            pass

        # Check operation_started signal data
        operation, affected_elements = signal_counter.operation_started_records[0]
        assert len(affected_elements) == len(target_widgets)
        for widget in target_widgets:
            assert widget in affected_elements

        # Check operation_ended signal data
        operation, affected_elements = signal_counter.operation_ended_records[0]
        assert len(affected_elements) == len(target_widgets)
        for widget in target_widgets:
            assert widget in affected_elements

    def test_nested_operation_signal_data(self, qtbot, app, ui_state_setup):
        """Test signal data in nested operations."""
        # Get the setup
        ui_state_manager = ui_state_setup["ui_state_manager"]
        signal_counter = ui_state_setup["signal_counter"]
        widgets = ui_state_setup["widgets"]

        # Reset signal counters
        signal_counter.reset_counters()

        # Start nested operations
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[widgets[0]]):
            # Check first operation signals
            assert signal_counter.operation_started_count == 1
            assert signal_counter.element_blocked_count == 1

            # Reset counters for second operation
            first_op_signals = signal_counter.operation_started_records.copy()
            signal_counter.reset_counters()

            # Start second operation
            with OperationContext(ui_state_manager, UIOperations.PROCESSING, elements=[widgets[1]]):
                # Check second operation signals
                assert signal_counter.operation_started_count == 1
                assert signal_counter.element_blocked_count == 1

                # Verify second operation has different data
                second_op = signal_counter.operation_started_records[0][0]
                assert second_op == UIOperations.PROCESSING
                assert second_op != first_op_signals[0][0]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
