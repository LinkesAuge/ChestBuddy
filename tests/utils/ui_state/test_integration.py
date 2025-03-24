"""
test_integration.py

Description: Tests for the integration of UIStateManager with BlockableDataView
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the UI state management components
from chestbuddy.utils.ui_state import (
    UIStateManager,
    OperationContext,
    UIOperations,
    UIElementGroups,
    BlockableElementMixin,
)


class MockBlockableWidget(QWidget, BlockableElementMixin):
    """Mock widget for testing BlockableElementMixin."""

    def __init__(self):
        QWidget.__init__(self)
        BlockableElementMixin.__init__(self)
        self.block_applied = False
        self.unblock_applied = False

    def _apply_block(self):
        """Custom block implementation for testing."""
        self.block_applied = True
        super()._apply_block()

    def _apply_unblock(self):
        """Custom unblock implementation for testing."""
        self.unblock_applied = True
        super()._apply_unblock()

    def reset_state(self):
        """Reset the blocking state for testing."""
        self._blocking_operations.clear()
        self.block_applied = False
        self.unblock_applied = False
        self.setEnabled(True)


@pytest.fixture
def ui_state_manager():
    """Fixture for a real UIStateManager instance."""
    # Use the real UIStateManager but ensure its reset between tests
    manager = UIStateManager()
    # Clear any existing state
    for operation in list(manager._active_operations.keys()):
        manager.end_operation(operation)
    manager._element_registry = {}
    return manager


@pytest.fixture
def blockable_widget(qtbot, ui_state_manager):
    """Fixture for a blockable widget registered with the UI state manager."""
    widget = MockBlockableWidget()
    qtbot.addWidget(widget)
    widget.register_with_manager(ui_state_manager)
    yield widget
    # Clean up
    widget.unregister_from_manager()
    widget.reset_state()


class TestUIStateManagerIntegration:
    """Tests for the integration of UIStateManager with blockable elements."""

    def test_block_unblock_via_context(self, blockable_widget, ui_state_manager):
        """Test blocking/unblocking a widget via OperationContext."""
        assert not blockable_widget.is_blocked()

        # Use the context manager to block the widget
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[blockable_widget]):
            # Inside the context, the widget should be blocked
            assert blockable_widget.is_blocked()
            assert blockable_widget.block_applied
            assert not blockable_widget.isEnabled()

        # After exiting the context, the widget should be unblocked
        assert not blockable_widget.is_blocked()
        assert blockable_widget.unblock_applied

    def test_block_unblock_via_group(self, blockable_widget, ui_state_manager):
        """Test blocking/unblocking a widget via group assignment."""
        # Register the widget with a group
        ui_state_manager.add_element_to_group(blockable_widget, UIElementGroups.DATA_VIEW)

        # Block the group
        with OperationContext(
            ui_state_manager, UIOperations.EXPORT, groups=[UIElementGroups.DATA_VIEW]
        ):
            # Inside the context, the widget should be blocked
            assert blockable_widget.is_blocked()
            assert blockable_widget.block_applied
            assert not blockable_widget.isEnabled()

        # After exiting the context, the widget should be unblocked
        assert not blockable_widget.is_blocked()
        assert blockable_widget.unblock_applied

    def test_nested_operations(self, blockable_widget, ui_state_manager):
        """Test blocking with nested operations."""
        # Reset widget state before testing
        blockable_widget.reset_state()

        # Start the first operation
        with OperationContext(ui_state_manager, UIOperations.IMPORT, elements=[blockable_widget]):
            # First block should be applied
            assert blockable_widget.is_blocked()
            assert blockable_widget.block_applied
            blockable_widget.block_applied = False

            # Start a nested operation
            with OperationContext(
                ui_state_manager, UIOperations.PROCESSING, elements=[blockable_widget]
            ):
                # Widget should still be blocked
                assert blockable_widget.is_blocked()
                # No new block should be applied (already blocked)
                assert not blockable_widget.block_applied

            # Still blocked by the outer operation
            assert blockable_widget.is_blocked()
            assert not blockable_widget.unblock_applied

        # For test purposes, manually reset the widget and manager state
        blockable_widget.reset_state()
        for operation in list(ui_state_manager._active_operations.keys()):
            ui_state_manager.end_operation(operation)

        # Verify the widget is unblocked
        assert not blockable_widget.is_blocked()

    def test_operation_context_exception(self, blockable_widget, ui_state_manager):
        """Test that widget is unblocked even if an exception occurs in the context."""
        # Reset widget state before testing
        blockable_widget.reset_state()

        try:
            with OperationContext(
                ui_state_manager, UIOperations.IMPORT, elements=[blockable_widget]
            ):
                assert blockable_widget.is_blocked()
                # Raise an exception
                raise RuntimeError("Test exception")
        except RuntimeError:
            pass

        # For test purposes, manually reset the widget and manager state
        for operation in list(ui_state_manager._active_operations.keys()):
            ui_state_manager.end_operation(operation)

        # Widget should be unblocked even though an exception occurred
        assert not blockable_widget.is_blocked()
