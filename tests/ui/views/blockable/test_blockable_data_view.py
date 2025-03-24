"""
test_blockable_data_view.py

Description: Tests for the BlockableDataView component integration with UI State Management
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

# Import paths need to be added here for tests to run correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import the UI state management components
from chestbuddy.utils.ui_state import UIOperations, UIElementGroups, UIStateManager


@pytest.fixture
def mock_ui_state_manager():
    """Mock the UIStateManager to avoid singleton issues in tests."""
    with patch("chestbuddy.utils.ui_state.UIStateManager", autospec=True) as mock:
        # Configure the mock to return itself when instantiated
        instance = mock.return_value
        # Set up common methods that will be used
        instance.is_element_blocked = MagicMock(return_value=False)
        instance.register_element = MagicMock()
        instance.unregister_element = MagicMock()
        yield instance


@pytest.fixture
def mock_data_view():
    """Mock the DataView class to avoid import issues."""
    with patch("chestbuddy.ui.views.blockable.blockable_data_view.DataView") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance._update_view = MagicMock()
        yield mock


@pytest.fixture
def blockable_data_view(qtbot, mock_ui_state_manager, mock_data_view):
    """Fixture to create a BlockableDataView for testing."""
    # Patch necessary classes and imports
    with patch(
        "chestbuddy.ui.views.blockable.blockable_data_view.UIStateManager",
        return_value=mock_ui_state_manager,
    ):
        # Import here to use patched dependencies
        from chestbuddy.ui.views.blockable.blockable_data_view import BlockableDataView

        # Create the BlockableDataView
        view = BlockableDataView()
        qtbot.addWidget(view)

        # Set up the view for testing
        view.setStyleSheet = MagicMock()
        view.closeEvent = MagicMock()
        view.unregister_from_manager = MagicMock()

        yield view


class TestBlockableDataView:
    """Tests for the BlockableDataView class."""

    def test_initialization(self, blockable_data_view, mock_ui_state_manager):
        """Test that BlockableDataView initializes correctly."""
        # Check that the view was created successfully
        assert blockable_data_view is not None

        # Check that it registered with the UI state manager
        mock_ui_state_manager.register_element.assert_called()

    def test_block_unblock(self, blockable_data_view):
        """Test that BlockableDataView blocks and unblocks correctly."""
        # Store original enabled state
        original_enabled = blockable_data_view.isEnabled()

        # Trigger blocking the view
        blockable_data_view._apply_block(UIOperations.IMPORT)

        # Check that setEnabled was called with False
        blockable_data_view.setEnabled.assert_called_with(False)

        # Check that styling was applied
        blockable_data_view.setStyleSheet.assert_called()

        # Trigger unblocking the view
        blockable_data_view._apply_unblock(UIOperations.IMPORT)

        # Check that setEnabled was called with True
        blockable_data_view.setEnabled.assert_called_with(True)

        # Check that styling was removed
        blockable_data_view.setStyleSheet.assert_called_with("")

    def test_update_view_when_blocked(self, blockable_data_view, mock_ui_state_manager):
        """Test that _update_view is skipped when the view is blocked."""
        # Set up the mock to simulate the view being blocked
        mock_ui_state_manager.is_element_blocked.return_value = True

        # Create a spy for the _update_view method
        original_update_view = blockable_data_view._update_view
        blockable_data_view._update_view = MagicMock()

        # Call _update_view
        blockable_data_view._update_view()

        # Check that the UI state manager was queried
        mock_ui_state_manager.is_element_blocked.assert_called_with(blockable_data_view)

        # Reset for unblocked test
        mock_ui_state_manager.is_element_blocked.return_value = False
        blockable_data_view._update_view.reset_mock()

        # Test behavior when not blocked
        blockable_data_view._update_view()
        blockable_data_view._update_view.assert_called_once()

    def test_closeEvent(self, blockable_data_view):
        """Test that the view is unregistered when closed."""
        # Create a mock event
        mock_event = MagicMock()

        # Call closeEvent directly
        blockable_data_view.closeEvent(mock_event)

        # Check that unregister_from_manager was called
        blockable_data_view.unregister_from_manager.assert_called_once()
