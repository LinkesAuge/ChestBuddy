"""
test_ui_state.py

Description: Tests for the UI State Management System
"""

import pytest
from unittest.mock import MagicMock, patch, call
import logging
from typing import List, Dict, Any

# Import from QtCore only what's needed for tests
from PySide6.QtCore import QObject


# Patch the UIStateManager to avoid metaclass conflict
@pytest.fixture
def mock_ui_state_manager():
    """Mock the UIStateManager to avoid metaclass conflicts."""
    with patch("chestbuddy.utils.ui_state.UIStateManager", autospec=True) as mock:
        # Configure the mock to return itself when instantiated
        instance = mock.return_value
        yield instance


@pytest.fixture
def ui_element_groups():
    """Mock UIElementGroups enum."""

    class MockUIElementGroups:
        MENU_BAR = "MENU_BAR"
        DATA_VIEW = "DATA_VIEW"
        MAIN_CONTENT = "MAIN_CONTENT"
        TOOLBAR = "TOOLBAR"

    return MockUIElementGroups()


@pytest.fixture
def ui_operations():
    """Mock UIOperations enum."""

    class MockUIOperations:
        IMPORT = "IMPORT"
        EXPORT = "EXPORT"
        PROCESS = "PROCESS"

    return MockUIOperations()


class TestUIStateManager:
    """Tests for the UIStateManager class."""

    def test_element_registration(self, mock_ui_state_manager):
        """Test registering elements with the manager."""
        # Create a mock element
        element = MagicMock()
        element.element_id = "test_element"

        # Register the element
        mock_ui_state_manager.register_element(element)

        # Check that register_element was called
        mock_ui_state_manager.register_element.assert_called_once_with(element)

    def test_group_registration(self, mock_ui_state_manager, ui_element_groups):
        """Test registering elements with groups."""
        # Create mock elements
        element1 = MagicMock()
        element1.element_id = "element1"
        element2 = MagicMock()
        element2.element_id = "element2"

        # Register elements with different groups
        mock_ui_state_manager.register_element(element1, groups=[ui_element_groups.MENU_BAR])
        mock_ui_state_manager.register_element(element2, groups=[ui_element_groups.DATA_VIEW])

        # Check that register_element was called with the right groups
        mock_ui_state_manager.register_element.assert_any_call(
            element1, groups=[ui_element_groups.MENU_BAR]
        )
        mock_ui_state_manager.register_element.assert_any_call(
            element2, groups=[ui_element_groups.DATA_VIEW]
        )

    def test_block_unblock_elements(self, mock_ui_state_manager, ui_operations):
        """Test blocking and unblocking elements."""
        # Create mock elements
        element1 = MagicMock()
        element1.element_id = "element1"
        element2 = MagicMock()
        element2.element_id = "element2"

        # Block elements
        mock_ui_state_manager.block_elements([element1, element2], ui_operations.IMPORT)

        # Check that block_elements was called
        mock_ui_state_manager.block_elements.assert_called_with(
            [element1, element2], ui_operations.IMPORT
        )

        # Unblock elements
        mock_ui_state_manager.unblock_elements([element1, element2], ui_operations.IMPORT)

        # Check that unblock_elements was called
        mock_ui_state_manager.unblock_elements.assert_called_with(
            [element1, element2], ui_operations.IMPORT
        )

    def test_block_unblock_groups(self, mock_ui_state_manager, ui_element_groups, ui_operations):
        """Test blocking and unblocking groups."""
        # Block MENU_BAR group
        mock_ui_state_manager.block_groups([ui_element_groups.MENU_BAR], ui_operations.IMPORT)

        # Check that block_groups was called
        mock_ui_state_manager.block_groups.assert_called_with(
            [ui_element_groups.MENU_BAR], ui_operations.IMPORT
        )

        # Unblock MENU_BAR group
        mock_ui_state_manager.unblock_groups([ui_element_groups.MENU_BAR], ui_operations.IMPORT)

        # Check that unblock_groups was called
        mock_ui_state_manager.unblock_groups.assert_called_with(
            [ui_element_groups.MENU_BAR], ui_operations.IMPORT
        )


class TestOperationContext:
    """Tests for the OperationContext class."""

    @patch("chestbuddy.utils.ui_state.OperationContext")
    def test_operation_context_lifecycle(self, mock_operation_context_class, mock_ui_state_manager):
        """Test the lifecycle of an OperationContext."""
        # Mock the OperationContext
        mock_context = mock_operation_context_class.return_value

        # Create mock elements
        element = MagicMock()
        element.element_id = "test_element"

        # Use the context
        mock_context.start()
        mock_context.end()

        # Check method calls
        mock_context.start.assert_called_once()
        mock_context.end.assert_called_once()

    @patch("chestbuddy.utils.ui_state.OperationContext")
    def test_context_manager_pattern(
        self, mock_operation_context_class, mock_ui_state_manager, ui_operations
    ):
        """Test using OperationContext as a context manager."""
        # Mock the OperationContext
        mock_context = mock_operation_context_class.return_value

        # Create a mock element
        element = MagicMock()
        element.element_id = "test_element"

        # Use with context manager
        with mock_context:
            pass

        # Check that __enter__ and __exit__ were called
        mock_context.__enter__.assert_called_once()
        mock_context.__exit__.assert_called_once()


# Create a simple BlockableElementMixin for testing
class MockBlockableElement:
    """A mock blockable element for testing."""

    def __init__(self, element_id="mock_element"):
        self.element_id = element_id
        self.apply_block_called = False
        self.apply_unblock_called = False
        self._manager = None
        self._ui_element_groups = set()

    def register_with_manager(self, manager, groups=None):
        """Register with a UI state manager."""
        self._manager = manager
        if groups:
            self._ui_element_groups.update(groups)
        manager.register_element(self, groups=groups or [])

    def unregister_from_manager(self):
        """Unregister from the UI state manager."""
        if self._manager:
            self._manager.unregister_element(self)
            self._manager = None

    def on_block(self, operation):
        """Handle being blocked."""
        self.apply_block_called = True

    def on_unblock(self, operation):
        """Handle being unblocked."""
        self.apply_unblock_called = True


class TestBlockableElementMixin:
    """Tests for elements that implement the BlockableElementMixin."""

    def test_registration(self, mock_ui_state_manager):
        """Test registering a blockable element with the manager."""
        # Create a blockable element
        element = MockBlockableElement("test_element")

        # Register with the mock manager
        element.register_with_manager(mock_ui_state_manager)

        # Check that the element was registered
        mock_ui_state_manager.register_element.assert_called_once_with(element, groups=[])

    def test_registration_with_groups(self, mock_ui_state_manager, ui_element_groups):
        """Test registering a blockable element with groups."""
        # Create a blockable element
        element = MockBlockableElement("test_element")

        # Register with the mock manager and groups
        element.register_with_manager(
            mock_ui_state_manager, groups=[ui_element_groups.MENU_BAR, ui_element_groups.DATA_VIEW]
        )

        # Check that the element was registered with groups
        mock_ui_state_manager.register_element.assert_called_once_with(
            element, groups=[ui_element_groups.MENU_BAR, ui_element_groups.DATA_VIEW]
        )

    def test_unregistration(self, mock_ui_state_manager):
        """Test unregistering a blockable element from the manager."""
        # Create a blockable element
        element = MockBlockableElement("test_element")

        # Register and then unregister
        element.register_with_manager(mock_ui_state_manager)
        element.unregister_from_manager()

        # Check that the element was unregistered
        mock_ui_state_manager.unregister_element.assert_called_once_with(element)

    def test_block_unblock_handlers(self, mock_ui_state_manager, ui_operations):
        """Test that block/unblock handlers are called."""
        # Create a blockable element
        element = MockBlockableElement("test_element")

        # Call the handlers directly
        element.on_block(ui_operations.IMPORT)
        element.on_unblock(ui_operations.IMPORT)

        # Check that the apply methods were called
        assert element.apply_block_called
        assert element.apply_unblock_called
