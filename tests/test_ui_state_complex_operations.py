"""
test_ui_state_complex_operations.py

Description: Tests for complex and nested operations in the UI State Management System.
This module focuses on testing reference counting, operation stacking, and complex
interactions between multiple operations and UI elements.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

# Ensure the application root is in the sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import application modules
from chestbuddy.utils.ui_state import (
    UIStateManager,
    OperationContext,
    BlockableElementMixin,
    UIOperations,
    UIElementGroups,
    BlockableWidgetGroup,
)
from chestbuddy.utils.ui_state.manager import SingletonMeta


@pytest.fixture
def app():
    """Create a QApplication instance."""
    # Check if there's already a QApplication instance
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def ui_state_manager():
    """Create a UIStateManager instance for testing."""
    # Reset the UIStateManager singleton instance
    if UIStateManager in SingletonMeta._instances:
        del SingletonMeta._instances[UIStateManager]

    # Create a new instance
    manager = UIStateManager()
    yield manager

    # Reset after test
    if UIStateManager in SingletonMeta._instances:
        del SingletonMeta._instances[UIStateManager]


class BlockableWidget(QWidget, BlockableElementMixin):
    """Test widget that implements BlockableElementMixin."""

    def __init__(self, name="unnamed", parent=None):
        QWidget.__init__(self, parent)
        BlockableElementMixin.__init__(self)
        self.name = name
        self.block_count = 0
        self.unblock_count = 0

    def _apply_block(self, operation: Any = None):
        """
        Apply the block to the widget.

        Args:
            operation: The operation causing the block
        """
        self.block_count += 1
        self.setEnabled(False)

    def _apply_unblock(self, operation: Any = None):
        """
        Apply the unblock to the widget.

        Args:
            operation: The operation unblocking the widget
        """
        self.unblock_count += 1
        self.setEnabled(True)


class TestComplexOperations:
    """Tests for complex operations in the UI State Management System."""

    def test_nested_operation_reference_counting(self, qtbot, app, ui_state_manager):
        """
        Test reference counting in nested operations.

        This test verifies that the UI State Management System correctly tracks
        reference counts for nested operations, and only unblocks UI elements
        when all operations are complete.
        """
        # Create a blockable widget
        widget = BlockableWidget()
        qtbot.addWidget(widget)
        widget.register_with_manager(ui_state_manager)

        # Verify widget is initially enabled
        assert widget.isEnabled(), "Widget should initially be enabled"

        # Nested operations with the same operation type
        with OperationContext(ui_state_manager, UIOperations.IMPORT, [widget]):
            # First level - widget is blocked
            assert not widget.isEnabled(), "Widget should be blocked at first level"
            assert widget.block_count == 1, "Block should be applied once"

            with OperationContext(ui_state_manager, UIOperations.IMPORT, [widget]):
                # Second level - widget is still blocked
                assert not widget.isEnabled(), "Widget should still be blocked at second level"
                assert widget.block_count == 1, (
                    "Block should not be applied again for same operation"
                )

                with OperationContext(ui_state_manager, UIOperations.IMPORT, [widget]):
                    # Third level - widget is still blocked
                    assert not widget.isEnabled(), "Widget should still be blocked at third level"
                    assert widget.block_count == 1, (
                        "Block should not be applied again for same operation"
                    )

                # After third level - widget is still blocked
                assert not widget.isEnabled(), "Widget should still be blocked after third level"
                assert widget.unblock_count == 0, "Unblock should not be called yet"

            # After second level - widget is still blocked
            assert not widget.isEnabled(), "Widget should still be blocked after second level"
            assert widget.unblock_count == 0, "Unblock should not be called yet"

        # After all operations - widget is unblocked
        assert widget.isEnabled(), "Widget should be unblocked after all operations"
        assert widget.unblock_count == 1, "Unblock should be called once"

        # Verify no active operations
        assert not ui_state_manager.has_active_operations(), "No operations should be active"

    def test_different_operation_types_nesting(self, qtbot, app, ui_state_manager):
        """
        Test nesting of different operation types.

        This test verifies that the UI State Management System correctly handles
        nesting of different operation types, with each operation blocking and
        unblocking independently.
        """
        # Create a blockable widget
        widget = BlockableWidget()
        qtbot.addWidget(widget)
        widget.register_with_manager(ui_state_manager)

        # Verify widget is initially enabled
        assert widget.isEnabled(), "Widget should initially be enabled"

        # Nested operations with different operation types
        with OperationContext(ui_state_manager, UIOperations.IMPORT, [widget]):
            # First level - widget is blocked
            assert not widget.isEnabled(), "Widget should be blocked at first level"
            assert widget.block_count == 1, "Block should be applied once"

            with OperationContext(ui_state_manager, UIOperations.PROCESSING, [widget]):
                # Second level - widget is still blocked
                assert not widget.isEnabled(), "Widget should still be blocked at second level"
                assert widget.block_count == 2, (
                    "Block should be applied again for different operation"
                )

                with OperationContext(ui_state_manager, UIOperations.VALIDATION, [widget]):
                    # Third level - widget is still blocked
                    assert not widget.isEnabled(), "Widget should still be blocked at third level"
                    assert widget.block_count == 3, (
                        "Block should be applied again for different operation"
                    )

                # After third level - widget is still blocked
                assert not widget.isEnabled(), "Widget should still be blocked after third level"
                assert widget.unblock_count == 1, "Unblock should be called once"

            # After second level - widget is still blocked
            assert not widget.isEnabled(), "Widget should still be blocked after second level"
            assert widget.unblock_count == 2, "Unblock should be called twice"

        # After all operations - widget is unblocked
        assert widget.isEnabled(), "Widget should be unblocked after all operations"
        assert widget.unblock_count == 3, "Unblock should be called three times"

        # Verify no active operations
        assert not ui_state_manager.has_active_operations(), "No operations should be active"

    def test_multiple_elements_in_operation(self, qtbot, app, ui_state_manager):
        """
        Test operations with multiple UI elements.

        This test verifies that the UI State Management System correctly handles
        operations that block multiple UI elements.
        """
        # Create multiple blockable widgets
        widgets = [BlockableWidget(f"widget{i}") for i in range(5)]
        for widget in widgets:
            qtbot.addWidget(widget)
            widget.register_with_manager(ui_state_manager)

        # Verify all widgets are initially enabled
        for widget in widgets:
            assert widget.isEnabled(), f"{widget.name} should initially be enabled"

        # Operation with multiple elements
        with OperationContext(ui_state_manager, UIOperations.IMPORT, widgets):
            # All widgets should be blocked
            for widget in widgets:
                assert not widget.isEnabled(), f"{widget.name} should be blocked"
                assert widget.block_count == 1, f"{widget.name} should be blocked once"

            # Nested operation with a subset of widgets
            subset = widgets[1:3]  # widgets[1] and widgets[2]
            with OperationContext(ui_state_manager, UIOperations.PROCESSING, subset):
                # Subset widgets should have additional blocks
                for i, widget in enumerate(widgets):
                    assert not widget.isEnabled(), f"{widget.name} should be blocked"
                    if i in [1, 2]:
                        assert widget.block_count == 2, f"{widget.name} should be blocked twice"
                    else:
                        assert widget.block_count == 1, f"{widget.name} should be blocked once"

            # After nested operation
            for i, widget in enumerate(widgets):
                assert not widget.isEnabled(), f"{widget.name} should still be blocked"
                if i in [1, 2]:
                    assert widget.unblock_count == 1, f"{widget.name} should be unblocked once"
                else:
                    assert widget.unblock_count == 0, f"{widget.name} should not be unblocked yet"

        # After all operations
        for widget in widgets:
            assert widget.isEnabled(), f"{widget.name} should be unblocked"
            # Each widget should be unblocked as many times as it was blocked
            assert widget.unblock_count == widget.block_count, (
                f"{widget.name} should have equal block and unblock counts"
            )

        # Verify no active operations
        assert not ui_state_manager.has_active_operations(), "No operations should be active"

    def test_element_groups_in_operations(self, qtbot, app, ui_state_manager):
        """
        Test operations with element groups.

        This test verifies that the UI State Management System correctly handles
        operations that block element groups.
        """
        # Create widgets for different groups
        menu_widgets = [BlockableWidget("menu1"), BlockableWidget("menu2")]
        data_widgets = [BlockableWidget("data1"), BlockableWidget("data2")]
        toolbar_widgets = [BlockableWidget("toolbar1"), BlockableWidget("toolbar2")]

        # Add all widgets to qtbot
        all_widgets = menu_widgets + data_widgets + toolbar_widgets
        for widget in all_widgets:
            qtbot.addWidget(widget)
            widget.register_with_manager(ui_state_manager)

        # Assign widgets to groups
        for widget in menu_widgets:
            ui_state_manager.add_element_to_group(widget, UIElementGroups.MENU_BAR)

        for widget in data_widgets:
            ui_state_manager.add_element_to_group(widget, UIElementGroups.DATA_VIEW)

        for widget in toolbar_widgets:
            ui_state_manager.add_element_to_group(widget, UIElementGroups.TOOLBAR)

        # Operation with multiple groups
        with OperationContext(
            ui_state_manager,
            UIOperations.IMPORT,
            groups=[UIElementGroups.MENU_BAR, UIElementGroups.DATA_VIEW],
        ):
            # Menu and data widgets should be blocked
            for widget in menu_widgets + data_widgets:
                assert not widget.isEnabled(), f"{widget.name} should be blocked"
                assert widget.block_count == 1, f"{widget.name} should be blocked once"

            # Toolbar widgets should not be blocked
            for widget in toolbar_widgets:
                assert widget.isEnabled(), f"{widget.name} should not be blocked"
                assert widget.block_count == 0, f"{widget.name} should not be blocked"

            # Nested operation with toolbar group
            with OperationContext(
                ui_state_manager, UIOperations.PROCESSING, groups=[UIElementGroups.TOOLBAR]
            ):
                # All widgets should now be blocked
                for widget in all_widgets:
                    assert not widget.isEnabled(), f"{widget.name} should be blocked"

                # Check block counts
                for widget in menu_widgets + data_widgets:
                    assert widget.block_count == 1, f"{widget.name} should still be blocked once"

                for widget in toolbar_widgets:
                    assert widget.block_count == 1, f"{widget.name} should be blocked once"

            # After nested operation
            for widget in menu_widgets + data_widgets:
                assert not widget.isEnabled(), f"{widget.name} should still be blocked"

            for widget in toolbar_widgets:
                assert widget.isEnabled(), f"{widget.name} should be unblocked"
                assert widget.unblock_count == 1, f"{widget.name} should be unblocked once"

        # After all operations
        for widget in all_widgets:
            assert widget.isEnabled(), f"{widget.name} should be unblocked"
            # Each widget should be unblocked as many times as it was blocked
            assert widget.unblock_count == widget.block_count, (
                f"{widget.name} should have equal block and unblock counts"
            )

        # Verify no active operations
        assert not ui_state_manager.has_active_operations(), "No operations should be active"

    def test_blockable_widget_group(self, qtbot, app, ui_state_manager):
        """
        Test BlockableWidgetGroup functionality.

        This test verifies that the BlockableWidgetGroup correctly handles
        blocking and unblocking of multiple widgets as a single unit.
        """
        # Create widgets for the group
        widgets = [BlockableWidget(f"widget{i}") for i in range(3)]
        for widget in widgets:
            qtbot.addWidget(widget)

        # Create a widget group
        widget_group = BlockableWidgetGroup(widgets)
        widget_group.register_with_manager(ui_state_manager)

        # Verify all widgets are initially enabled
        for widget in widgets:
            assert widget.isEnabled(), f"{widget.name} should initially be enabled"

        # Operation with the widget group
        with OperationContext(ui_state_manager, UIOperations.IMPORT, [widget_group]):
            # All widgets in the group should be blocked
            for widget in widgets:
                assert not widget.isEnabled(), f"{widget.name} should be blocked"
                assert widget.block_count == 1, f"{widget.name} should be blocked once"

            # Nested operation with the same group
            with OperationContext(ui_state_manager, UIOperations.IMPORT, [widget_group]):
                # All widgets should still be blocked
                for widget in widgets:
                    assert not widget.isEnabled(), f"{widget.name} should still be blocked"
                    assert widget.block_count == 1, f"{widget.name} should still be blocked once"

            # After nested operation
            for widget in widgets:
                assert not widget.isEnabled(), f"{widget.name} should still be blocked"
                assert widget.unblock_count == 0, f"{widget.name} should not be unblocked yet"

        # After all operations
        for widget in widgets:
            assert widget.isEnabled(), f"{widget.name} should be unblocked"
            assert widget.unblock_count == 1, f"{widget.name} should be unblocked once"

        # Verify no active operations
        assert not ui_state_manager.has_active_operations(), "No operations should be active"

    def test_operation_interleaving(self, qtbot, app, ui_state_manager):
        """
        Test interleaving of operations.

        This test verifies that the UI State Management System correctly handles
        interleaving of operations with different elements.
        """
        # Create multiple widgets
        widget1 = BlockableWidget("widget1")
        widget2 = BlockableWidget("widget2")

        qtbot.addWidget(widget1)
        qtbot.addWidget(widget2)

        widget1.register_with_manager(ui_state_manager)
        widget2.register_with_manager(ui_state_manager)

        # Start operation on widget1
        ctx1 = OperationContext(ui_state_manager, UIOperations.IMPORT, [widget1])
        ctx1.__enter__()

        # Widget1 should be blocked
        assert not widget1.isEnabled(), "widget1 should be blocked"
        assert widget1.block_count == 1, "widget1 should be blocked once"

        # Widget2 should not be blocked
        assert widget2.isEnabled(), "widget2 should not be blocked"
        assert widget2.block_count == 0, "widget2 should not be blocked"

        # Start operation on widget2
        ctx2 = OperationContext(ui_state_manager, UIOperations.EXPORT, [widget2])
        ctx2.__enter__()

        # Widget1 should still be blocked
        assert not widget1.isEnabled(), "widget1 should still be blocked"
        assert widget1.block_count == 1, "widget1 should still be blocked once"

        # Widget2 should now be blocked
        assert not widget2.isEnabled(), "widget2 should be blocked"
        assert widget2.block_count == 1, "widget2 should be blocked once"

        # End operation on widget1
        ctx1.__exit__(None, None, None)

        # Widget1 should be unblocked
        assert widget1.isEnabled(), "widget1 should be unblocked"
        assert widget1.unblock_count == 1, "widget1 should be unblocked once"

        # Widget2 should still be blocked
        assert not widget2.isEnabled(), "widget2 should still be blocked"
        assert widget2.unblock_count == 0, "widget2 should not be unblocked yet"

        # End operation on widget2
        ctx2.__exit__(None, None, None)

        # Widget2 should now be unblocked
        assert widget2.isEnabled(), "widget2 should be unblocked"
        assert widget2.unblock_count == 1, "widget2 should be unblocked once"

        # Verify no active operations
        assert not ui_state_manager.has_active_operations(), "No operations should be active"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
