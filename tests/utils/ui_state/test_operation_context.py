"""
test_operation_context.py

Description: Unit tests for the OperationContext and ManualOperationContext classes
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QPushButton, QLabel

from chestbuddy.utils.ui_state import (
    UIStateManager,
    OperationContext,
    ManualOperationContext,
    BlockableElementMixin,
    UIOperations,
    UIElementGroups,
)


class TestOperationContext:
    """Test cases for the OperationContext class."""

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

    @pytest.fixture
    def blockable_elements(self, ui_state_manager):
        """Fixture to create blockable UI elements."""

        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        # Create buttons
        button1 = BlockableButton("Button 1")
        button2 = BlockableButton("Button 2")

        # Register with manager
        button1.register_with_manager(ui_state_manager)
        button2.register_with_manager(ui_state_manager)

        # Create a group
        ui_state_manager.register_group(UIElementGroups.TOOLBAR, elements=[button1])

        return button1, button2

    def test_context_enter_exit(self, ui_state_manager, blockable_elements):
        """Test entering and exiting the context."""
        button1, button2 = blockable_elements

        # Use as context manager
        with OperationContext(
            ui_state_manager,
            UIOperations.IMPORT,
            elements=[button2],
            groups=[UIElementGroups.TOOLBAR],
        ) as context:
            # Context should be active
            assert context._is_active

            # Elements should be blocked
            assert ui_state_manager.is_element_blocked(button1)
            assert ui_state_manager.is_element_blocked(button2)

            # Operation should be active
            assert ui_state_manager.is_operation_active(UIOperations.IMPORT)

        # After context exit
        # Elements should be unblocked
        assert not ui_state_manager.is_element_blocked(button1)
        assert not ui_state_manager.is_element_blocked(button2)

        # Operation should not be active
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)

        # Context should not be active
        assert not context._is_active

    def test_context_with_exception(self, ui_state_manager, blockable_elements):
        """Test context with an exception being raised."""
        button1, button2 = blockable_elements

        # Use as context manager with exception
        try:
            with OperationContext(
                ui_state_manager, UIOperations.IMPORT, elements=[button1, button2]
            ):
                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Elements should still be unblocked
        assert not ui_state_manager.is_element_blocked(button1)
        assert not ui_state_manager.is_element_blocked(button2)

        # Operation should not be active
        assert not ui_state_manager.is_operation_active(UIOperations.IMPORT)

    def test_context_get_exception(self, ui_state_manager):
        """Test getting the exception from the context."""
        # Create context
        context = OperationContext(ui_state_manager, UIOperations.IMPORT)

        # No exception initially
        exception, traceback = context.get_exception()
        assert exception is None
        assert traceback is None

        # Set an exception
        test_exception = ValueError("Test exception")
        context._exception = test_exception
        context._traceback = "Traceback info"

        # Should return the exception
        exception, traceback = context.get_exception()
        assert exception is test_exception
        assert traceback == "Traceback info"

    def test_context_already_active(self, ui_state_manager):
        """Test entering a context when the operation is already active."""
        # Start the operation
        ui_state_manager.start_operation(UIOperations.IMPORT)

        # Mock logger.warning
        with patch("chestbuddy.utils.ui_state.context.logger.warning") as mock_warning:
            # Use as context manager
            with OperationContext(
                ui_state_manager, UIOperations.IMPORT, check_active=True
            ) as context:
                # Context should not be active
                assert not context._is_active

            # Warning should be logged
            mock_warning.assert_called_once()
            assert "already active" in mock_warning.call_args[0][0]

        # Clean up
        ui_state_manager.end_operation(UIOperations.IMPORT)

    def test_is_active(self, ui_state_manager):
        """Test the is_active method."""
        # Create context (not entered yet)
        context = OperationContext(ui_state_manager, UIOperations.IMPORT)

        # Should not be active
        assert not context.is_active()

        # Enter context
        context.__enter__()

        # Should be active
        assert context.is_active()

        # Exit context
        context.__exit__(None, None, None)

        # Should not be active
        assert not context.is_active()


class TestManualOperationContext:
    """Test cases for the ManualOperationContext class."""

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

    @pytest.fixture
    def blockable_elements(self, ui_state_manager):
        """Fixture to create blockable UI elements."""

        class BlockableButton(QPushButton, BlockableElementMixin):
            def __init__(self, *args, **kwargs):
                QPushButton.__init__(self, *args, **kwargs)
                BlockableElementMixin.__init__(self)

        # Create buttons
        button1 = BlockableButton("Button 1")
        button2 = BlockableButton("Button 2")

        # Register with manager
        button1.register_with_manager(ui_state_manager)
        button2.register_with_manager(ui_state_manager)

        return button1, button2

    def test_manual_start_end(self, ui_state_manager, blockable_elements):
        """Test manually starting and ending an operation."""
        button1, button2 = blockable_elements

        # Create manual context
        context = ManualOperationContext(
            ui_state_manager, UIOperations.IMPORT, elements=[button1, button2]
        )

        # Should not be active
        assert not context.is_active()
        assert not ui_state_manager.is_element_blocked(button1)
        assert not ui_state_manager.is_element_blocked(button2)

        # Start the operation
        context.start()

        # Should be active
        assert context.is_active()
        assert ui_state_manager.is_element_blocked(button1)
        assert ui_state_manager.is_element_blocked(button2)

        # End the operation
        context.end()

        # Should not be active
        assert not context.is_active()
        assert not ui_state_manager.is_element_blocked(button1)
        assert not ui_state_manager.is_element_blocked(button2)

    def test_start_with_exception(self, ui_state_manager, blockable_elements):
        """Test handling exceptions during start."""
        button1, button2 = blockable_elements

        # Create manual context
        context = ManualOperationContext(
            ui_state_manager, UIOperations.IMPORT, elements=[button1, button2]
        )

        # Mock start_operation to raise exception
        with patch.object(
            ui_state_manager, "start_operation", side_effect=ValueError("Test exception")
        ):
            # Start should catch the exception
            context.start()

            # Should record the exception
            exception, _ = context.get_exception()
            assert isinstance(exception, ValueError)
            assert str(exception) == "Test exception"

        # Elements should not be blocked
        assert not ui_state_manager.is_element_blocked(button1)
        assert not ui_state_manager.is_element_blocked(button2)

    def test_end_with_exception(self, ui_state_manager, blockable_elements):
        """Test handling exceptions during end."""
        button1, button2 = blockable_elements

        # Create manual context
        context = ManualOperationContext(
            ui_state_manager, UIOperations.IMPORT, elements=[button1, button2]
        )

        # Start the operation
        context.start()

        # Mock end_operation to raise exception
        with patch.object(
            ui_state_manager, "end_operation", side_effect=ValueError("Test exception")
        ):
            # End should catch the exception
            context.end()

            # Should record the exception
            exception, _ = context.get_exception()
            assert isinstance(exception, ValueError)
            assert str(exception) == "Test exception"

        # Context should not be active
        assert not context.is_active()

    def test_use_as_context_manager(self, ui_state_manager, blockable_elements):
        """Test using ManualOperationContext as a context manager."""
        button1, button2 = blockable_elements

        # Use as context manager
        with ManualOperationContext(
            ui_state_manager, UIOperations.IMPORT, elements=[button1, button2]
        ) as context:
            # Start manually
            context.start()

            # Elements should be blocked
            assert ui_state_manager.is_element_blocked(button1)
            assert ui_state_manager.is_element_blocked(button2)

            # No need to call end(), context exit will handle it

        # Elements should be unblocked
        assert not ui_state_manager.is_element_blocked(button1)
        assert not ui_state_manager.is_element_blocked(button2)
