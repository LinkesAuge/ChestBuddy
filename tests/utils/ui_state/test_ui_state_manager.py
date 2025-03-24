"""
test_ui_state_manager.py

Description: Unit tests for the UIStateManager class
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Tuple

from PySide6.QtCore import QObject, Signal, QCoreApplication
from PySide6.QtWidgets import QWidget, QPushButton, QLabel

from chestbuddy.utils.ui_state import (
    UIStateManager,
    UIOperations,
    UIElementGroups,
    BlockableElementMixin,
)


class TestUIStateManager:
    """Test cases for the UIStateManager class."""

    @pytest.fixture
    def ui_state_manager(self) -> UIStateManager:
        """Fixture to create a UIStateManager instance."""
        # Get the singleton instance
        manager = UIStateManager()

        # Reset the manager's state for each test
        manager._element_registry.clear()
        manager._group_registry.clear()
        manager._active_operations.clear()

        return manager

    @pytest.fixture
    def mockable_widgets(self) -> Tuple[QWidget, QWidget, QWidget]:
        """Fixture to create mock widgets for testing."""
        # Create widgets
        button = QPushButton("Test Button")
        label = QLabel("Test Label")
        container = QWidget()

        return button, label, container

    def test_singleton_pattern(self):
        """Test that UIStateManager follows the singleton pattern."""
        # Get two instances
        manager1 = UIStateManager()
        manager2 = UIStateManager()

        # They should be the same instance
        assert manager1 is manager2

    def test_register_element(self, ui_state_manager, mockable_widgets):
        """Test registering elements with the manager."""
        button, label, _ = mockable_widgets

        # Register elements
        ui_state_manager.register_element(button)
        ui_state_manager.register_element(label, groups=[UIElementGroups.MAIN_WINDOW])

        # Check they're in the registry
        assert button in ui_state_manager._element_registry
        assert label in ui_state_manager._element_registry

        # Check group assignment
        assert label in ui_state_manager._group_registry.get(UIElementGroups.MAIN_WINDOW, set())

    def test_unregister_element(self, ui_state_manager, mockable_widgets):
        """Test unregistering elements from the manager."""
        button, _, _ = mockable_widgets

        # Register and then unregister
        ui_state_manager.register_element(button, groups=[UIElementGroups.TOOLBAR])
        ui_state_manager.unregister_element(button)

        # Should be removed from registry
        assert button not in ui_state_manager._element_registry

        # Should be removed from any groups
        for group_elements in ui_state_manager._group_registry.values():
            assert button not in group_elements

    def test_register_group(self, ui_state_manager, mockable_widgets):
        """Test registering a group with the manager."""
        button, label, container = mockable_widgets

        # Register a group with elements
        ui_state_manager.register_group(
            UIElementGroups.TOOLBAR, elements=[button, label, container]
        )

        # Check group exists with all elements
        group_elements = ui_state_manager._group_registry.get(UIElementGroups.TOOLBAR, set())
        assert button in group_elements
        assert label in group_elements
        assert container in group_elements

    def test_block_element(self, ui_state_manager, mockable_widgets):
        """Test blocking an element."""
        button, _, _ = mockable_widgets

        # Create a custom button with BlockableElementMixin
        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        blockable_button = BlockableButton("Blockable")
        blockable_button.register_with_manager(ui_state_manager)

        # Block the button
        ui_state_manager.block_element(blockable_button, UIOperations.IMPORT)

        # Check if it's blocked
        assert ui_state_manager.is_element_blocked(blockable_button)
        assert UIOperations.IMPORT in blockable_button.get_blocking_operations()

    def test_unblock_element(self, ui_state_manager):
        """Test unblocking an element."""

        # Create a blockable button
        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        button = BlockableButton("Blockable")
        button.register_with_manager(ui_state_manager)

        # Block and then unblock
        ui_state_manager.block_element(button, UIOperations.IMPORT)
        ui_state_manager.unblock_element(button, UIOperations.IMPORT)

        # Should no longer be blocked
        assert not ui_state_manager.is_element_blocked(button)
        assert not button.get_blocking_operations()

    def test_start_operation(self, ui_state_manager, mockable_widgets):
        """Test starting an operation."""
        button, label, container = mockable_widgets

        # Create blockable widgets
        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        class BlockableLabel(QLabel, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QLabel.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        b_button = BlockableButton("Blockable Button")
        b_label = BlockableLabel("Blockable Label")

        b_button.register_with_manager(ui_state_manager)
        b_label.register_with_manager(ui_state_manager)

        # Register a group
        ui_state_manager.register_group(UIElementGroups.MAIN_WINDOW, elements=[b_button, b_label])

        # Start an operation that blocks both elements via group
        ui_state_manager.start_operation(UIOperations.IMPORT, groups=[UIElementGroups.MAIN_WINDOW])

        # Both elements should be blocked
        assert ui_state_manager.is_element_blocked(b_button)
        assert ui_state_manager.is_element_blocked(b_label)

        # Operation should be active
        assert ui_state_manager.is_operation_active(UIOperations.IMPORT)

    def test_end_operation(self, ui_state_manager):
        """Test ending an operation."""

        # Create blockable widgets
        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        b1 = BlockableButton("Button 1")
        b2 = BlockableButton("Button 2")

        b1.register_with_manager(ui_state_manager)
        b2.register_with_manager(ui_state_manager)

        # Start operation blocking both
        ui_state_manager.start_operation(UIOperations.IMPORT, elements=[b1, b2])

        # End the operation
        ui_state_manager.end_operation(UIOperations.IMPORT)

        # Elements should be unblocked
        assert not ui_state_manager.is_element_blocked(b1)
        assert not ui_state_manager.is_element_blocked(b2)

        # Operation should no longer be active
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)

    def test_signals(self, ui_state_manager):
        """Test that signals are properly emitted."""
        # Create signal spy
        element_blocked_spy = MagicMock()
        element_unblocked_spy = MagicMock()
        operation_started_spy = MagicMock()
        operation_ended_spy = MagicMock()

        # Connect to signals
        ui_state_manager.signals.element_blocked.connect(element_blocked_spy)
        ui_state_manager.signals.element_unblocked.connect(element_unblocked_spy)
        ui_state_manager.signals.operation_started.connect(operation_started_spy)
        ui_state_manager.signals.operation_ended.connect(operation_ended_spy)

        # Create blockable widget
        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        button = BlockableButton("Test")
        button.register_with_manager(ui_state_manager)

        # Start and end an operation
        ui_state_manager.start_operation(UIOperations.IMPORT, elements=[button])
        ui_state_manager.end_operation(UIOperations.IMPORT)

        # Check signals were emitted
        assert element_blocked_spy.called
        assert element_unblocked_spy.called
        assert operation_started_spy.called
        assert operation_ended_spy.called
