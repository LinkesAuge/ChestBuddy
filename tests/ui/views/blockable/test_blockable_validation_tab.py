"""
test_blockable_validation_tab.py

Description: Tests for the BlockableValidationTab component integration with UI State Management
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
    mock.add_element_to_group = MagicMock()

    yield mock


@pytest.fixture
def mock_data_model():
    """Mock the ChestDataModel."""
    mock = MagicMock()
    mock.data_changed = MagicMock()
    return mock


@pytest.fixture
def mock_validation_service():
    """Mock the ValidationService."""
    mock = MagicMock()
    mock.validation_changed = MagicMock()
    return mock


class TestBlockableValidationTab:
    """Tests for the BlockableValidationTab class."""

    def test_initialization(
        self, qtbot, mock_ui_state_manager, mock_data_model, mock_validation_service
    ):
        """Test that BlockableValidationTab initializes correctly."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_validation_tab import BlockableValidationTab

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_validation_tab.UIStateManager",
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
                "chestbuddy.ui.views.blockable.blockable_validation_tab.BlockableValidationTab._register_child_widgets"
            ),
        ):
            # Create a test instance
            view = BlockableValidationTab(mock_data_model, mock_validation_service)
            qtbot.addWidget(view)

            # Check that it registered with the UI state manager
            mock_ui_state_manager.register_element.assert_called()

            # Check that it added itself to the VALIDATION group
            mock_ui_state_manager.add_element_to_group.assert_called_with(
                view, UIElementGroups.VALIDATION
            )

    def test_blocking_behavior(
        self, qtbot, mock_ui_state_manager, mock_data_model, mock_validation_service
    ):
        """Test that BlockableValidationTab applies block/unblock correctly."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_validation_tab import BlockableValidationTab

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_validation_tab.UIStateManager",
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
                "chestbuddy.ui.views.blockable.blockable_validation_tab.BlockableValidationTab._register_child_widgets"
            ),
        ):
            # Create a test instance
            view = BlockableValidationTab(mock_data_model, mock_validation_service)
            qtbot.addWidget(view)

            # Initially should be enabled
            assert view.isEnabled() == True

            # Simulate blocking
            view._apply_block(UIOperations.IMPORT)

            # Should now be disabled
            assert view.isEnabled() == False

            # Simulate unblocking
            view._apply_unblock(UIOperations.IMPORT)

            # Should be enabled again
            assert view.isEnabled() == True

    def test_validate_data_when_blocked(
        self, qtbot, mock_ui_state_manager, mock_data_model, mock_validation_service
    ):
        """Test that _validate_data does nothing when the tab is blocked."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_validation_tab import BlockableValidationTab

        # Mock the ValidationTab._validate_data method
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_validation_tab.UIStateManager",
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
                "chestbuddy.ui.views.blockable.blockable_validation_tab.BlockableValidationTab._register_child_widgets"
            ),
            patch(
                "chestbuddy.ui.validation_tab.ValidationTab._validate_data"
            ) as mock_validate_data,
        ):
            # Create a test instance
            view = BlockableValidationTab(mock_data_model, mock_validation_service)
            qtbot.addWidget(view)

            # Set is_element_blocked to return True
            mock_ui_state_manager.is_element_blocked.return_value = True

            # Call _validate_data
            view._validate_data()

            # Original _validate_data should not be called
            mock_validate_data.assert_not_called()

            # Set is_element_blocked to return False
            mock_ui_state_manager.is_element_blocked.return_value = False

            # Call _validate_data
            view._validate_data()

            # Original _validate_data should be called
            mock_validate_data.assert_called_once()

    def test_update_view_when_blocked(
        self, qtbot, mock_ui_state_manager, mock_data_model, mock_validation_service
    ):
        """Test that _update_view does nothing when the tab is blocked."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_validation_tab import BlockableValidationTab

        # First patch validation_tab._update_view to prevent it being called during init
        with patch("chestbuddy.ui.validation_tab.ValidationTab._update_view") as mock_update_view:
            # Now patch other components
            with (
                patch(
                    "chestbuddy.ui.views.blockable.blockable_validation_tab.UIStateManager",
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
                    "chestbuddy.ui.views.blockable.blockable_validation_tab.BlockableValidationTab._register_child_widgets"
                ),
            ):
                # Create a test instance
                view = BlockableValidationTab(mock_data_model, mock_validation_service)
                qtbot.addWidget(view)

                # Clear the mock to reset call count after initialization
                mock_update_view.reset_mock()

                # Need to manually set _ui_state_manager since we mocked the initialization
                view._ui_state_manager = mock_ui_state_manager

                # Set is_element_blocked to return True
                mock_ui_state_manager.is_element_blocked.return_value = True

                # Call _update_view
                view._update_view()

                # Original _update_view should not be called
                mock_update_view.assert_not_called()

                # Set is_element_blocked to return False
                mock_ui_state_manager.is_element_blocked.return_value = False

                # Call _update_view again
                view._update_view()

                # Original _update_view should be called
                mock_update_view.assert_called_once()

    def test_unregister_on_close(
        self, qtbot, mock_ui_state_manager, mock_data_model, mock_validation_service
    ):
        """Test that the tab unregisters from the UI state manager when closed."""
        # Import first so we can properly patch
        from chestbuddy.ui.views.blockable.blockable_validation_tab import BlockableValidationTab

        # Use patch to mock UIStateManager and BlockableElementMixin methods
        with (
            patch(
                "chestbuddy.ui.views.blockable.blockable_validation_tab.UIStateManager",
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
                "chestbuddy.ui.views.blockable.blockable_validation_tab.BlockableValidationTab._register_child_widgets"
            ),
            patch(
                "chestbuddy.utils.ui_state.BlockableElementMixin.unregister_from_manager"
            ) as mock_unregister,
        ):
            # Create a test instance
            view = BlockableValidationTab(mock_data_model, mock_validation_service)
            qtbot.addWidget(view)

            # Close the widget
            view.close()

            # Should unregister from the UI state manager
            mock_unregister.assert_called_once()
