"""
test_blockable_components.py

Description: Tests for blockable UI components that integrate with the UI State Management System
"""

import pytest
from unittest.mock import MagicMock, patch, call, PropertyMock
import logging
from typing import List, Dict, Any
import sys


# Mock constants for UI state system
class MockUIElementGroups:
    MENU_BAR = "MENU_BAR"
    DATA_VIEW = "DATA_VIEW"
    MAIN_CONTENT = "MAIN_CONTENT"
    TOOLBAR = "TOOLBAR"


class MockUIOperations:
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    PROCESS = "PROCESS"


# Create mock UIStateManager class
mock_ui_state_manager_instance = MagicMock()

# Patch modules before they're imported
sys.modules["chestbuddy.utils.ui_state"] = MagicMock()
sys.modules["chestbuddy.utils.ui_state"].UIStateManager = MagicMock(
    return_value=mock_ui_state_manager_instance
)
sys.modules["chestbuddy.utils.ui_state"].UIElementGroups = MockUIElementGroups
sys.modules["chestbuddy.utils.ui_state"].UIOperations = MockUIOperations
sys.modules["chestbuddy.utils.ui_state"].ManualOperationContext = MagicMock()

# Patch UI modules
sys.modules["chestbuddy.ui.views.blockable.blockable_base_view"] = MagicMock()
sys.modules["chestbuddy.ui.views.blockable.blockable_data_view"] = MagicMock()
sys.modules["chestbuddy.ui.widgets.blockable_progress_dialog"] = MagicMock()


# Test fixtures for mocking PySide6 components
@pytest.fixture
def mock_qevent():
    """Mock QEvent."""
    mock = MagicMock()
    type_property = PropertyMock(return_value="CloseEvent")
    type(mock).type = type_property
    return mock


@pytest.fixture
def ui_element_groups():
    """Return the mock UIElementGroups enum."""
    return MockUIElementGroups


@pytest.fixture
def ui_operations():
    """Return the mock UIOperations enum."""
    return MockUIOperations


class TestBlockableBaseView:
    """Tests for the BlockableBaseView class."""

    @patch("chestbuddy.ui.views.blockable.blockable_base_view.BlockableBaseView")
    def test_initialization(self, mock_base_view_class):
        """Test that the view is properly initialized and registered."""
        # Create a mock instance
        mock_view = mock_base_view_class.return_value

        # Get a reference to the __init__ method to verify its args
        init_method = mock_base_view_class
        init_method(parent=None)

        # Check that it was registered with the UI state manager
        assert mock_ui_state_manager_instance.register_element.called

    @patch("chestbuddy.ui.views.blockable.blockable_base_view.BlockableBaseView")
    def test_register_with_groups(self, mock_base_view_class, ui_element_groups):
        """Test registering with UI element groups."""
        # Create a mock instance
        mock_view = mock_base_view_class.return_value

        # Call the register_with_groups method
        groups = [ui_element_groups.DATA_VIEW, ui_element_groups.MAIN_CONTENT]
        mock_view.register_with_groups(groups)

        # Check that register_element_with_groups was called
        mock_ui_state_manager_instance.register_element_with_groups.assert_called_once()

    @patch("chestbuddy.ui.views.blockable.blockable_base_view.BlockableBaseView")
    def test_apply_block(self, mock_base_view_class, ui_operations):
        """Test that _apply_block properly updates the UI."""
        # Create a mock instance
        mock_view = mock_base_view_class.return_value

        # Call the _apply_block method
        mock_view._apply_block(ui_operations.IMPORT)

        # Check that setEnabled was called
        mock_view.setEnabled.assert_called_with(False)

    @patch("chestbuddy.ui.views.blockable.blockable_base_view.BlockableBaseView")
    def test_apply_unblock(self, mock_base_view_class, ui_operations):
        """Test that _apply_unblock properly updates the UI."""
        # Create a mock instance
        mock_view = mock_base_view_class.return_value

        # Call the _apply_unblock method
        mock_view._apply_unblock(ui_operations.IMPORT)

        # Check that setEnabled was called
        mock_view.setEnabled.assert_called_with(True)

    @patch("chestbuddy.ui.views.blockable.blockable_base_view.BlockableBaseView")
    def test_close_event(self, mock_base_view_class, mock_qevent):
        """Test that the view is unregistered when closed."""
        # Create a mock instance
        mock_view = mock_base_view_class.return_value

        # Call the closeEvent method
        mock_view.closeEvent(mock_qevent)

        # Check that the view was unregistered
        mock_ui_state_manager_instance.unregister_element.assert_called_once()


class TestBlockableDataView:
    """Tests for the BlockableDataView class."""

    @patch("chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView")
    def test_initialization(self, mock_data_view_class, ui_element_groups):
        """Test that the view is properly initialized and registered."""
        # Create a mock instance
        mock_view = mock_data_view_class.return_value

        # Get a reference to the __init__ method to verify its args
        init_method = mock_data_view_class
        init_method(parent=None)

        # Check that it was registered with the UI state manager
        assert mock_ui_state_manager_instance.register_element.called

    @patch("chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView")
    def test_register_child_widgets(self, mock_data_view_class):
        """Test registering child widgets."""
        # Create a mock instance with mock table_view and filter_bar
        mock_view = mock_data_view_class.return_value
        mock_view.table_view = MagicMock()
        mock_view.filter_bar = MagicMock()

        # Call _register_child_widgets
        mock_view._register_child_widgets()

        # Check that register_element was called for child widgets
        assert mock_ui_state_manager_instance.register_element.call_count >= 1

    @patch("chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView")
    def test_apply_block(self, mock_data_view_class, ui_operations):
        """Test that _apply_block properly updates the UI."""
        # Create a mock instance with mock table_view and filter_bar
        mock_view = mock_data_view_class.return_value
        mock_view.table_view = MagicMock()
        mock_view.filter_bar = MagicMock()

        # Call _apply_block
        mock_view._apply_block(ui_operations.IMPORT)

        # Check that the view and child widgets were disabled
        mock_view.setEnabled.assert_called_with(False)
        mock_view.table_view.setEnabled.assert_called_with(False)
        mock_view.filter_bar.setEnabled.assert_called_with(False)

    @patch("chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView")
    def test_update_view(self, mock_data_view_class):
        """Test that _update_view respects the blocked state."""
        # Create a mock instance
        mock_view = mock_data_view_class.return_value

        # Set up mock to return True for is_element_blocked
        mock_ui_state_manager_instance.is_element_blocked.return_value = True

        # Call _update_view
        mock_view._update_view()

        # Check that the parent's _update_view was not called
        assert not mock_data_view_class._update_view.called


class TestBlockableProgressDialog:
    """Tests for the BlockableProgressDialog class."""

    @patch("chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog")
    def test_initialization(self, mock_dialog_class):
        """Test that the dialog is properly initialized."""
        # Create a mock instance
        mock_dialog = mock_dialog_class.return_value

        # Initialize with arguments
        init_method = mock_dialog_class
        init_method("Processing", "Cancel", 0, 100, parent=None)

        # Check initialization of attributes
        assert hasattr(mock_dialog, "_ui_state_manager")
        assert hasattr(mock_dialog, "_operation_context")

    @patch("chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog")
    def test_show_with_blocking(self, mock_dialog_class, ui_operations, ui_element_groups):
        """Test that show_with_blocking properly blocks UI elements."""
        # Create a mock dialog instance
        mock_dialog = mock_dialog_class.return_value

        # Create a mock context instance
        mock_context = MagicMock()
        sys.modules["chestbuddy.utils.ui_state"].ManualOperationContext.return_value = mock_context

        # Call show_with_blocking
        groups = [ui_element_groups.DATA_VIEW]
        mock_dialog.show_with_blocking(ui_operations.IMPORT, groups=groups)

        # Check that the context was created and started
        sys.modules["chestbuddy.utils.ui_state"].ManualOperationContext.assert_called_once()
        mock_context.start.assert_called_once()

        # Check that the dialog was shown
        mock_dialog.show.assert_called_once()

    @patch("chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog")
    def test_exec_with_blocking(self, mock_dialog_class, ui_operations, ui_element_groups):
        """Test that exec_with_blocking properly blocks UI elements."""
        # Create a mock dialog instance
        mock_dialog = mock_dialog_class.return_value
        mock_dialog.exec.return_value = 1  # Return as if OK was clicked

        # Create a mock context instance
        mock_context = MagicMock()
        mock_context.is_active.return_value = True
        sys.modules["chestbuddy.utils.ui_state"].ManualOperationContext.return_value = mock_context

        # Call exec_with_blocking
        groups = [ui_element_groups.DATA_VIEW]
        result = mock_dialog.exec_with_blocking(ui_operations.IMPORT, groups=groups)

        # Check that the context was created and started
        sys.modules["chestbuddy.utils.ui_state"].ManualOperationContext.assert_called_once()
        mock_context.start.assert_called_once()

        # Check that the dialog was executed
        mock_dialog.exec.assert_called_once()

        # Check that the operation was ended after dialog execution
        mock_context.end.assert_called_once()

        # Check that the result was returned
        assert result == 1

    @patch("chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog")
    def test_close_event(self, mock_dialog_class, mock_qevent):
        """Test that the close event ends the operation."""
        # Create a mock dialog instance
        mock_dialog = mock_dialog_class.return_value

        # Create a mock operation context
        mock_context = MagicMock()
        mock_context.is_active.return_value = True
        mock_dialog._operation_context = mock_context

        # Call closeEvent
        mock_dialog.closeEvent(mock_qevent)

        # Check that the operation was ended
        mock_context.end.assert_called_once()

    @patch("chestbuddy.ui.widgets.blockable_progress_dialog.BlockableProgressDialog")
    def test_end_operation_with_exception(self, mock_dialog_class):
        """Test that _end_operation handles exceptions properly."""
        # Create a mock dialog instance
        mock_dialog = mock_dialog_class.return_value

        # Create a mock operation context with an exception
        mock_context = MagicMock()
        mock_context.is_active.return_value = True
        mock_context.get_exception.return_value = (ValueError("Test error"), "Test traceback")
        mock_dialog._operation_context = mock_context

        # Call _end_operation
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = mock_get_logger.return_value

            mock_dialog._end_operation()

            # Check that the exception was logged
            mock_logger.error.assert_called_once()
            mock_logger.debug.assert_called_once()
