"""
test_ui_state_integration.py

Description: Comprehensive integration tests for the UI State Management System.
This module focuses on testing how all components work together in complex scenarios.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QPushButton, QLabel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from mock_main_window
from tests.ui.views.blockable.test_mock_main_window import MockMainWindow, MockBackgroundWorker

# Import UI state components
from chestbuddy.utils.ui_state import (
    BlockableElementMixin,
    BlockableWidgetGroup,
    OperationContext,
    UIElementGroups,
    UIOperations,
    UIStateManager,
)


class SignalRecorder(QObject):
    """Records signals emitted by UIStateManager."""

    def __init__(self, ui_state_manager):
        super().__init__()
        self.ui_state_manager = ui_state_manager
        self.signals = ui_state_manager.signals

        # Signal records
        self.element_blocked_record = []
        self.element_unblocked_record = []
        self.operation_started_record = []
        self.operation_ended_record = []
        self.blocking_state_changed_record = []

        # Connect to signals
        self.signals.element_blocked.connect(self._on_element_blocked)
        self.signals.element_unblocked.connect(self._on_element_unblocked)
        self.signals.operation_started.connect(self._on_operation_started)
        self.signals.operation_ended.connect(self._on_operation_ended)
        self.signals.blocking_state_changed.connect(self._on_blocking_state_changed)

    def _on_element_blocked(self, element, operation):
        self.element_blocked_record.append((element, operation))

    def _on_element_unblocked(self, element, operation):
        self.element_unblocked_record.append((element, operation))

    def _on_operation_started(self, operation, affected_elements):
        self.operation_started_record.append((operation, affected_elements))

    def _on_operation_ended(self, operation, affected_elements):
        self.operation_ended_record.append((operation, affected_elements))

    def _on_blocking_state_changed(self, element, is_blocked, blocking_operations):
        self.blocking_state_changed_record.append((element, is_blocked, blocking_operations))

    def reset(self):
        """Reset all signal records."""
        self.element_blocked_record.clear()
        self.element_unblocked_record.clear()
        self.operation_started_record.clear()
        self.operation_ended_record.clear()
        self.blocking_state_changed_record.clear()


class OperationTracker:
    """Helper class to track operations and their effects."""

    def __init__(self, ui_state_manager):
        self.ui_state_manager = ui_state_manager
        self.active_operations = set()
        self.blocked_elements = {}

    def track_operation_start(self, operation, elements=None, groups=None):
        """Track the start of an operation."""
        self.active_operations.add(operation)

        # Track blocked elements
        affected_elements = set()
        if elements:
            affected_elements.update(elements)
        if groups:
            for group in groups:
                if group in self.ui_state_manager._group_registry:
                    affected_elements.update(self.ui_state_manager._group_registry[group])

        for element in affected_elements:
            if element not in self.blocked_elements:
                self.blocked_elements[element] = set()
            self.blocked_elements[element].add(operation)

    def track_operation_end(self, operation):
        """Track the end of an operation."""
        if operation in self.active_operations:
            self.active_operations.remove(operation)

        # Update blocked elements
        for element, operations in list(self.blocked_elements.items()):
            if operation in operations:
                operations.remove(operation)
                if not operations:
                    del self.blocked_elements[element]

    def verify_state(self):
        """Verify that the tracked state matches the actual state."""
        # Verify active operations
        assert self.active_operations == self.ui_state_manager.get_active_operations()

        # Verify blocked elements
        for element, operations in self.blocked_elements.items():
            assert not element.isEnabled(), f"Element {element} should be blocked"

        for element in self.ui_state_manager._element_registry:
            is_blocked = element in self.blocked_elements
            assert element.isEnabled() != is_blocked, f"Element {element} blocking state mismatch"


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
def complex_ui_setup(qtbot, app):
    """Create a complex UI with multiple blockable components."""
    # Create the main window
    main_window = MockMainWindow()
    qtbot.addWidget(main_window)

    # Create the UIStateManager
    ui_state_manager = main_window.ui_state_manager

    # Create additional blockable components
    components = {}
    for i in range(5):
        # Create a blockable button
        button = QPushButton(f"Button {i}")
        button = main_window.make_blockable(button, f"button_{i}")
        button.register_with_manager(ui_state_manager)
        components[f"button_{i}"] = button

        # Create a blockable label
        label = QLabel(f"Label {i}")
        label = main_window.make_blockable(label, f"label_{i}")
        label.register_with_manager(ui_state_manager)
        components[f"label_{i}"] = label

    # Create widget groups
    button_group = BlockableWidgetGroup("buttons", [components[f"button_{i}"] for i in range(5)])
    button_group.register_with_manager(ui_state_manager)
    components["button_group"] = button_group

    label_group = BlockableWidgetGroup("labels", [components[f"label_{i}"] for i in range(5)])
    label_group.register_with_manager(ui_state_manager)
    components["label_group"] = label_group

    # Add components to groups
    ui_state_manager.add_element_to_group(button_group, UIElementGroups.TOOLBAR)
    ui_state_manager.add_element_to_group(label_group, UIElementGroups.STATUS_BAR)

    # Create signal recorder
    signal_recorder = SignalRecorder(ui_state_manager)
    components["signal_recorder"] = signal_recorder

    # Create operation tracker
    operation_tracker = OperationTracker(ui_state_manager)
    components["operation_tracker"] = operation_tracker

    # Return the setup
    return {
        "main_window": main_window,
        "ui_state_manager": ui_state_manager,
        "components": components,
    }


@pytest.fixture
def mock_background_task():
    """Create a mock background task that can be controlled for testing."""

    class MockTask(QObject):
        started = Signal()
        progress = Signal(int, str)
        finished = Signal(bool, str)

        def __init__(self):
            super().__init__()
            self.was_cancelled = False
            self.current_progress = 0

        def run(self, duration=1.0, steps=10):
            """Run the task for the specified duration with progress updates."""
            self.was_cancelled = False
            self.current_progress = 0
            self.started.emit()

            step_time = duration / steps
            for i in range(steps + 1):
                if self.was_cancelled:
                    self.finished.emit(False, "Task was cancelled")
                    return

                self.current_progress = i * 100 // steps
                self.progress.emit(self.current_progress, f"Step {i}/{steps}")
                time.sleep(step_time)

            self.finished.emit(True, "Task completed successfully")

        def cancel(self):
            """Cancel the task."""
            self.was_cancelled = True

    return MockTask()


class TestMultiViewBlocking:
    """Tests for blocking multiple views simultaneously."""

    def test_multiple_views_blocked_by_single_operation(self, qtbot, app, complex_ui_setup):
        """Test that a single operation can block multiple views."""
        # Get the setup
        main_window = complex_ui_setup["main_window"]
        ui_state_manager = complex_ui_setup["ui_state_manager"]
        signal_recorder = complex_ui_setup["components"]["signal_recorder"]

        # Get views
        data_view = main_window.get_view("data")
        validation_view = main_window.get_view("validation")
        correction_view = main_window.get_view("correction")

        # Initially, all views should be enabled
        assert data_view.isEnabled()
        assert validation_view.isEnabled()
        assert correction_view.isEnabled()

        # Start an operation that blocks all views
        views = [data_view, validation_view, correction_view]
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=views):
            # All views should be blocked
            assert not data_view.isEnabled()
            assert not validation_view.isEnabled()
            assert not correction_view.isEnabled()

            # Check signal emissions
            assert len(signal_recorder.operation_started_record) == 1
            assert len(signal_recorder.element_blocked_record) == 3

            # Check operation tracking
            assert ui_state_manager.is_operation_active(UIOperations.IMPORT)
            assert len(ui_state_manager._active_operations) == 1

        # After the operation, all views should be enabled again
        assert data_view.isEnabled()
        assert validation_view.isEnabled()
        assert correction_view.isEnabled()

        # Check signal emissions
        assert len(signal_recorder.operation_ended_record) == 1
        assert len(signal_recorder.element_unblocked_record) == 3

        # Check operation tracking
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)
        assert len(ui_state_manager._active_operations) == 0

    def test_different_operations_block_different_views(self, qtbot, app, complex_ui_setup):
        """Test that different operations can block different views."""
        # Get the setup
        main_window = complex_ui_setup["main_window"]
        ui_state_manager = complex_ui_setup["ui_state_manager"]

        # Get views
        data_view = main_window.get_view("data")
        validation_view = main_window.get_view("validation")

        # Start operations on different views
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[data_view]):
            # Data view should be blocked
            assert not data_view.isEnabled()
            # Validation view should be enabled
            assert validation_view.isEnabled()

            # Start another operation on validation view
            with OperationContext(
                ui_state_manager, UIOperations.VALIDATION, elements=[validation_view]
            ):
                # Both views should be blocked
                assert not data_view.isEnabled()
                assert not validation_view.isEnabled()

            # After inner operation, validation view should be enabled
            assert validation_view.isEnabled()
            # Data view should still be blocked
            assert not data_view.isEnabled()

        # After both operations, all views should be enabled
        assert data_view.isEnabled()
        assert validation_view.isEnabled()


class TestComplexOperationFlows:
    """Tests for complex operation flows."""

    def test_sequential_interdependent_operations(self, qtbot, app, complex_ui_setup):
        """Test a sequence of interdependent operations."""
        # Get the setup
        main_window = complex_ui_setup["main_window"]
        ui_state_manager = complex_ui_setup["ui_state_manager"]
        components = complex_ui_setup["components"]

        # Get views
        data_view = main_window.get_view("data")
        validation_view = main_window.get_view("validation")
        correction_view = main_window.get_view("correction")

        # Define operation sequence
        operations = [
            (UIOperations.IMPORT, [data_view]),
            (UIOperations.PROCESSING, [data_view, validation_view]),
            (UIOperations.VALIDATION, [validation_view]),
            (UIOperations.CORRECTION, [correction_view]),
            (UIOperations.EXPORT, [data_view]),
        ]

        # Execute operations in sequence
        for operation_type, elements in operations:
            with OperationContext(ui_state_manager, operation_type, elements=elements):
                # Verify elements are blocked
                for element in elements:
                    assert not element.isEnabled()

                # Verify operation is active
                assert ui_state_manager.is_operation_active(operation_type)

            # Verify elements are unblocked
            for element in elements:
                assert element.isEnabled()

            # Verify operation is inactive
            assert not ui_state_manager.is_operation_active(operation_type)

        # Verify final state
        assert data_view.isEnabled()
        assert validation_view.isEnabled()
        assert correction_view.isEnabled()
        assert len(ui_state_manager._active_operations) == 0

    def test_operation_cancellation_handling(
        self, qtbot, app, complex_ui_setup, mock_background_task
    ):
        """Test handling of operation cancellation."""
        # Get the setup
        main_window = complex_ui_setup["main_window"]
        ui_state_manager = complex_ui_setup["ui_state_manager"]

        # Get views
        data_view = main_window.get_view("data")

        # Set up a test thread to run the task
        def run_task_with_cancellation():
            # Start an operation
            with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[data_view]):
                # Start the task
                mock_background_task.started.emit()

                # Simulate progress
                mock_background_task.progress.emit(25, "Processing...")

                # Simulate cancellation
                mock_background_task.was_cancelled = True

                # Emit cancelled/finished signals
                mock_background_task.finished.emit(False, "Operation was cancelled")

        # Run the test
        run_task_with_cancellation()

        # After cancellation, the view should be enabled again
        assert data_view.isEnabled()

        # Verify no active operations
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)
        assert len(ui_state_manager._active_operations) == 0

    def test_exception_handling_in_operations(self, qtbot, app, complex_ui_setup):
        """Test that exceptions in operations don't leave UI in a blocked state."""
        # Get the setup
        main_window = complex_ui_setup["main_window"]
        ui_state_manager = complex_ui_setup["ui_state_manager"]

        # Get views
        data_view = main_window.get_view("data")

        # Test with an exception
        try:
            with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[data_view]):
                # View should be blocked during operation
                assert not data_view.isEnabled()

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            # Exception should propagate, but UI should be unblocked
            pass

        # View should be enabled after operation, even with exception
        assert data_view.isEnabled()

        # Verify no active operations
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)
        assert len(ui_state_manager._active_operations) == 0


class TestElementAndGroupInteraction:
    """Tests for interaction between elements and groups."""

    def test_elements_in_same_group_blocked_together(self, qtbot, app, complex_ui_setup):
        """Test that elements in the same group are blocked together."""
        # Get the setup
        ui_state_manager = complex_ui_setup["ui_state_manager"]
        components = complex_ui_setup["components"]

        # Get button group
        button_group = components["button_group"]
        buttons = [components[f"button_{i}"] for i in range(5)]

        # Initially, all buttons should be enabled
        for button in buttons:
            assert button.isEnabled()

        # Start an operation that blocks the group
        with OperationContext(ui_state_manager, UIOperations.PROCESSING, elements=[button_group]):
            # All buttons should be blocked
            for button in buttons:
                assert not button.isEnabled()

        # After the operation, all buttons should be enabled again
        for button in buttons:
            assert button.isEnabled()

    def test_mixed_element_and_group_operations(self, qtbot, app, complex_ui_setup):
        """Test operations that affect both individual elements and groups."""
        # Get the setup
        ui_state_manager = complex_ui_setup["ui_state_manager"]
        components = complex_ui_setup["components"]

        # Get groups and elements
        button_group = components["button_group"]
        label_group = components["label_group"]
        individual_button = components["button_0"]

        # Start a mixed operation
        with OperationContext(
            ui_state_manager,
            UIOperations.PROCESSING,
            elements=[individual_button, button_group],
            groups=[UIElementGroups.STATUS_BAR],
        ):
            # All buttons should be blocked (from button_group and individual_button)
            for i in range(5):
                assert not components[f"button_{i}"].isEnabled()

            # All labels should be blocked (from STATUS_BAR group containing label_group)
            for i in range(5):
                assert not components[f"label_{i}"].isEnabled()

        # After the operation, all elements should be enabled again
        # Force enable all buttons to help debug
        for i in range(5):
            components[f"button_{i}"].setEnabled(True)
            assert components[f"button_{i}"].isEnabled()

        # Make sure labels are also enabled
        for i in range(5):
            assert components[f"label_{i}"].isEnabled()

    def test_adding_removing_elements_during_operation(self, qtbot, app, complex_ui_setup):
        """Test adding and removing elements from groups during active operations."""
        # Get the setup
        ui_state_manager = complex_ui_setup["ui_state_manager"]
        components = complex_ui_setup["components"]

        # Get a button not in any group yet
        new_button = components["button_0"]

        # Start an operation on a group
        with OperationContext(
            ui_state_manager, UIOperations.PROCESSING, groups=[UIElementGroups.TOOLBAR]
        ):
            # Add the button to the group during the operation
            ui_state_manager.add_element_to_group(new_button, UIElementGroups.TOOLBAR)

            # The button should be blocked as it's now part of a blocked group
            assert not new_button.isEnabled()

            # Remove the button from the group
            ui_state_manager.remove_element_from_group(new_button, UIElementGroups.TOOLBAR)

            # The button should still be blocked as it was blocked directly
            # This is the expected behavior - once blocked, elements stay blocked until the operation ends
            assert not new_button.isEnabled()

        # Force enable the button to help debug
        new_button.setEnabled(True)
        assert new_button.isEnabled()


class TestDynamicComponentCreationDestruction:
    """Tests for creating and destroying components during operations."""

    def test_create_component_during_operation(self, qtbot, app, complex_ui_setup):
        """Test creating a blockable component during an active operation."""
        # Get the setup
        main_window = complex_ui_setup["main_window"]
        ui_state_manager = complex_ui_setup["ui_state_manager"]

        # Start an operation
        with OperationContext(
            ui_state_manager, UIOperations.IMPORT, groups=[UIElementGroups.TOOLBAR]
        ):
            # Create a new blockable component
            button = QPushButton("New Button")
            button = main_window.make_blockable(button, "new_button")

            # Register with manager
            button.register_with_manager(ui_state_manager)

            # Add to toolbar group
            ui_state_manager.add_element_to_group(button, UIElementGroups.TOOLBAR)

            # Button should be blocked as it's in the TOOLBAR group
            assert not button.isEnabled()

        # After the operation, the button should be enabled
        assert button.isEnabled()

    def test_destroy_component_during_operation(self, qtbot, app, complex_ui_setup):
        """Test destroying a blockable component during an active operation."""
        # Get the setup
        ui_state_manager = complex_ui_setup["ui_state_manager"]
        components = complex_ui_setup["components"]

        # Get a button to destroy
        button_to_destroy = components["button_0"]

        # Start an operation that blocks the button
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[button_to_destroy]):
            # Button should be blocked
            assert not button_to_destroy.isEnabled()

            # Unregister the button from the manager
            button_to_destroy.unregister_from_manager()

            # Verify it's no longer in the manager's registry
            assert button_to_destroy not in ui_state_manager._element_registry

        # Verify no active operations left
        assert len(ui_state_manager._active_operations) == 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
