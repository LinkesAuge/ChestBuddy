"""
test_blockable_element.py

Description: Unit tests for the BlockableElementMixin class
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QPushButton, QLabel

from chestbuddy.utils.ui_state import (
    UIStateManager,
    BlockableElementMixin,
    UIOperations,
)


class TestBlockableElementMixin:
    """Test cases for the BlockableElementMixin class."""

    @pytest.fixture
    def blockable_button(self):
        """Fixture to create a button with BlockableElementMixin."""

        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        return BlockableButton("Blockable Button")

    @pytest.fixture
    def ui_state_manager(self):
        """Fixture to create a UIStateManager instance."""
        # Get the singleton instance
        manager = UIStateManager()

        # Reset the manager's state for each test
        manager._element_registry.clear()
        manager._group_registry.clear()
        manager._active_operations.clear()

        return manager

    def test_initialization(self, blockable_button):
        """Test that the mixin initializes correctly."""
        # Check initial state
        assert not blockable_button._blocking_operations
        assert not blockable_button._is_registered
        assert blockable_button._original_enabled_state
        assert blockable_button._ui_state_manager is None

    def test_register_with_manager(self, blockable_button, ui_state_manager):
        """Test registering with the UIStateManager."""
        # Register the button
        blockable_button.register_with_manager(ui_state_manager)

        # Should be registered
        assert blockable_button._is_registered
        assert blockable_button._ui_state_manager is ui_state_manager

        # Should be in the manager's registry
        assert blockable_button in ui_state_manager._element_registry

    def test_unregister_from_manager(self, blockable_button, ui_state_manager):
        """Test unregistering from the UIStateManager."""
        # Register and then unregister
        blockable_button.register_with_manager(ui_state_manager)
        blockable_button.unregister_from_manager()

        # Should be unregistered
        assert not blockable_button._is_registered
        assert blockable_button._ui_state_manager is None

        # Should not be in the manager's registry
        assert blockable_button not in ui_state_manager._element_registry

    def test_is_blocked(self, blockable_button):
        """Test checking if an element is blocked."""
        # Initially not blocked
        assert not blockable_button.is_blocked()

        # Add a blocking operation
        blockable_button._blocking_operations.add(UIOperations.IMPORT)

        # Should now be blocked
        assert blockable_button.is_blocked()

    def test_get_blocking_operations(self, blockable_button):
        """Test getting the set of blocking operations."""
        # Initially empty
        assert not blockable_button.get_blocking_operations()

        # Add blocking operations
        blockable_button._blocking_operations.add(UIOperations.IMPORT)
        blockable_button._blocking_operations.add(UIOperations.EXPORT)

        # Should contain both operations
        blocking_ops = blockable_button.get_blocking_operations()
        assert UIOperations.IMPORT in blocking_ops
        assert UIOperations.EXPORT in blocking_ops

        # Should be a copy (not the original set)
        blockable_button._blocking_operations.add(UIOperations.PROCESSING)
        assert UIOperations.PROCESSING not in blocking_ops

    def test_block(self, blockable_button):
        """Test blocking an element."""
        # Mock the _apply_block method
        blockable_button._apply_block = MagicMock()

        # Block the button
        blockable_button.block(UIOperations.IMPORT)

        # Operation should be in blocking operations
        assert UIOperations.IMPORT in blockable_button._blocking_operations

        # _apply_block should have been called
        blockable_button._apply_block.assert_called_once()

        # Block again with different operation
        blockable_button.block(UIOperations.EXPORT)

        # Both operations should now be blocking
        assert UIOperations.IMPORT in blockable_button._blocking_operations
        assert UIOperations.EXPORT in blockable_button._blocking_operations

        # _apply_block should not have been called again
        assert blockable_button._apply_block.call_count == 1

    def test_unblock(self, blockable_button):
        """Test unblocking an element."""
        # Mock the _apply_unblock method
        blockable_button._apply_unblock = MagicMock()

        # Add blocking operations
        blockable_button._blocking_operations.add(UIOperations.IMPORT)
        blockable_button._blocking_operations.add(UIOperations.EXPORT)

        # Unblock one operation
        blockable_button.unblock(UIOperations.IMPORT)

        # Operation should be removed from blocking operations
        assert UIOperations.IMPORT not in blockable_button._blocking_operations
        assert UIOperations.EXPORT in blockable_button._blocking_operations

        # _apply_unblock should not have been called yet
        blockable_button._apply_unblock.assert_not_called()

        # Unblock the other operation
        blockable_button.unblock(UIOperations.EXPORT)

        # No operations should be blocking now
        assert not blockable_button._blocking_operations

        # _apply_unblock should have been called now
        blockable_button._apply_unblock.assert_called_once()

    def test_apply_block(self, blockable_button):
        """Test the default _apply_block implementation."""
        # Button should be enabled initially
        assert blockable_button.isEnabled()

        # Block the button (calls _apply_block)
        blockable_button.block(UIOperations.IMPORT)

        # Button should be disabled
        assert not blockable_button.isEnabled()

        # Original enabled state should be preserved
        assert blockable_button._original_enabled_state

    def test_apply_unblock(self, blockable_button):
        """Test the default _apply_unblock implementation."""
        # Button should be enabled initially
        assert blockable_button.isEnabled()

        # Block and then unblock
        blockable_button.block(UIOperations.IMPORT)
        blockable_button.unblock(UIOperations.IMPORT)

        # Button should be re-enabled
        assert blockable_button.isEnabled()

    def test_custom_block_unblock_behavior(self):
        """Test implementing custom blocking behavior."""

        class CustomBlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)
                self.block_called = False
                self.unblock_called = False

            def _apply_block(self):
                self.block_called = True
                self.setText("BLOCKED")

            def _apply_unblock(self):
                self.unblock_called = True
                self.setText("UNBLOCKED")

        # Create custom button
        button = CustomBlockableButton("Test")

        # Block the button
        button.block(UIOperations.IMPORT)

        # Custom block behavior should be applied
        assert button.block_called
        assert button.text() == "BLOCKED"

        # Unblock the button
        button.unblock(UIOperations.IMPORT)

        # Custom unblock behavior should be applied
        assert button.unblock_called
        assert button.text() == "UNBLOCKED"

    def test_block_non_widget(self):
        """Test blocking an element that's not a widget."""

        class NonWidgetBlockable(QObject, BlockableElementMixin):
            def __init__(self):
                QObject.__init__(self)
                BlockableElementMixin.__init__(self)

        # Create non-widget blockable object
        obj = NonWidgetBlockable()

        # Mock the logger
        with patch("chestbuddy.utils.ui_state.elements.logger.warning") as mock_warning:
            # Block the object
            obj.block(UIOperations.IMPORT)

            # Operation should be added to blocking operations
            assert UIOperations.IMPORT in obj._blocking_operations

            # Warning should be logged
            mock_warning.assert_called_once()
            assert "not a QWidget" in mock_warning.call_args[0][0]
