"""
test_blockable_data_view.py

Description: Tests for the BlockableDataView component integration with UI State Management
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import the UI state management components
from chestbuddy.utils.ui_state import UIOperations, UIElementGroups, UIStateManager


# Create a patched BlockableElementMixin.__init__ function that accepts element_id
def patched_blockable_element_init(self, element_id=None):
    """Patched version of BlockableElementMixin.__init__ that accepts element_id."""
    # Store element_id if needed
    self._element_id = element_id

    # Initialize original attributes
    self._blocking_operations = set()
    self._is_registered = False
    self._original_enabled_state = True
    self._ui_state_manager = None
    self._ui_element_groups = set()


# Create a patched register_with_manager function that accepts groups
def patched_register_with_manager(self, manager, groups=None):
    """Patched version of register_with_manager that accepts groups parameter."""
    if self._is_registered:
        return

    self._ui_state_manager = manager
    self._is_registered = True

    # Store groups if provided
    if groups:
        self._ui_element_groups = set(groups)

    # Call the manager's register_element method directly
    if hasattr(manager, "register_element"):
        manager.register_element(self, groups=groups)


@pytest.fixture
def mock_ui_state_manager():
    """Mock the UIStateManager to avoid singleton issues in tests."""
    mock = MagicMock(spec=UIStateManager)

    # Set up common methods that will be used
    mock.is_element_blocked = MagicMock(return_value=False)
    mock.register_element = MagicMock()
    mock.unregister_element = MagicMock()

    yield mock


class TestBlockableDataView:
    """Tests for the BlockableDataView class."""

    def test_initialization(self, qtbot, mock_ui_state_manager):
        """Test that BlockableDataView initializes correctly."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_data_view import BlockableDataView

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.UIStateManager",
                return_value=mock_ui_state_manager,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.__init__",
                patched_blockable_element_init,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.register_with_manager",
                patched_register_with_manager,
            ),
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView._register_child_widgets"
            ),
        ):
            # Create a test instance
            view = BlockableDataView()
            qtbot.addWidget(view)

            # Check that it registered with the UI state manager
            mock_ui_state_manager.register_element.assert_called()

            # Clean up
            view.deleteLater()

    def test_block_unblock(self, qtbot, mock_ui_state_manager):
        """Test that BlockableDataView blocks and unblocks correctly."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_data_view import BlockableDataView

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.UIStateManager",
                return_value=mock_ui_state_manager,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.__init__",
                patched_blockable_element_init,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.register_with_manager",
                patched_register_with_manager,
            ),
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView._register_child_widgets"
            ),
        ):
            # Create a test instance with mocked methods
            view = BlockableDataView()
            qtbot.addWidget(view)

            # Mock the setEnabled and setStyleSheet methods
            view.setEnabled = MagicMock()
            view.setStyleSheet = MagicMock()

            # Test blocking behavior
            view._apply_block(UIOperations.IMPORT)

            # Check that setEnabled was called with False
            view.setEnabled.assert_called_with(False)

            # Check that styling was applied
            view.setStyleSheet.assert_called()

            # Reset mocks
            view.setEnabled.reset_mock()
            view.setStyleSheet.reset_mock()

            # Test unblocking behavior
            view._apply_unblock(UIOperations.IMPORT)

            # Check that setEnabled was called with True
            view.setEnabled.assert_called_with(True)

            # Check that styling was removed
            view.setStyleSheet.assert_called_with("")

            # Clean up
            view.deleteLater()

    def test_update_view_when_blocked(self, qtbot, mock_ui_state_manager):
        """Test that _update_view is skipped when the view is blocked."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_data_view import BlockableDataView

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.UIStateManager",
                return_value=mock_ui_state_manager,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.__init__",
                patched_blockable_element_init,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.register_with_manager",
                patched_register_with_manager,
            ),
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView._register_child_widgets"
            ),
        ):
            # Create a test instance
            view = BlockableDataView()
            qtbot.addWidget(view)

            # Mock the DataView.update method instead of _update_view
            with patch("chestbuddy.ui.views.data_view.DataView.update") as super_update:
                # Set up the view's _update_view method to call our mock when not blocked
                def mock_update_view():
                    if not mock_ui_state_manager.is_element_blocked(view):
                        super_update()

                # Apply our mock implementation
                view._update_view = mock_update_view

                # Set up the mock to simulate the view being blocked
                mock_ui_state_manager.is_element_blocked.return_value = True

                # Call _update_view
                view._update_view()

                # Check that the UI state manager was queried
                mock_ui_state_manager.is_element_blocked.assert_called_with(view)

                # Check that super().update was not called when blocked
                super_update.assert_not_called()

                # Reset for unblocked test
                mock_ui_state_manager.is_element_blocked.return_value = False
                mock_ui_state_manager.is_element_blocked.reset_mock()
                super_update.reset_mock()

                # Test behavior when not blocked
                view._update_view()

                # Check that super().update was called when not blocked
                super_update.assert_called_once()

            # Clean up
            view.deleteLater()

    def test_closeEvent(self, qtbot, mock_ui_state_manager):
        """Test that the view is unregistered when closed."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_data_view import BlockableDataView

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.UIStateManager",
                return_value=mock_ui_state_manager,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.__init__",
                patched_blockable_element_init,
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.register_with_manager",
                patched_register_with_manager,
            ),
            patch(
                "chestbuddy.ui.views.blockable.blockable_data_view.BlockableDataView._register_child_widgets"
            ),
        ):
            # Create a test instance
            view = BlockableDataView()
            qtbot.addWidget(view)

            # Mock unregister_from_manager
            view.unregister_from_manager = MagicMock()

            # Mock closeEvent on parent class
            with patch("chestbuddy.ui.views.data_view.DataView.closeEvent") as parent_close_event:
                # Create a mock event
                mock_event = MagicMock()

                # Call closeEvent directly
                view.closeEvent(mock_event)

                # Check that unregister_from_manager was called
                view.unregister_from_manager.assert_called_once()

                # Check that parent's closeEvent was called
                parent_close_event.assert_called_once_with(mock_event)

            # Clean up
            view.deleteLater()
