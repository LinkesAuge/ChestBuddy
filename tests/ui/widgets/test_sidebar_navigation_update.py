"""
Tests for SidebarNavigation integration with UpdateManager.
"""

import pytest
from unittest.mock import MagicMock, patch
import time

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from chestbuddy.ui.widgets.sidebar_navigation import SidebarNavigation, NavigationSection
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import ServiceLocator, get_update_manager
from chestbuddy.ui.utils.update_manager import UpdateManager


@pytest.fixture
def app(qtbot):
    """Create a QApplication for testing."""
    # qtbot will ensure QApplication exists
    return QApplication.instance()


@pytest.fixture
def update_manager():
    """Create and register an UpdateManager instance."""
    manager = UpdateManager()
    ServiceLocator.register("update_manager", manager)
    return manager


@pytest.fixture
def sidebar_navigation(app):
    """Create a SidebarNavigation instance."""
    return SidebarNavigation()


class TestSidebarNavigationUpdate:
    """Tests for SidebarNavigation integration with UpdateManager."""

    def test_implements_iupdatable(self, sidebar_navigation):
        """Test that SidebarNavigation implements the IUpdatable interface."""
        assert isinstance(sidebar_navigation, IUpdatable)

    def test_update_method(self, sidebar_navigation):
        """Test that update method properly updates the sidebar."""
        # Spy on internal methods
        sidebar_navigation._update_view_content = MagicMock()

        # Call the method
        sidebar_navigation.update()

        # Verify the update method was called
        sidebar_navigation._update_view_content.assert_called_once()

        # Verify state was updated
        assert sidebar_navigation._update_state["needs_update"] is False
        assert sidebar_navigation._update_state["update_pending"] is False
        assert sidebar_navigation._update_state["last_update_time"] > 0

    def test_refresh_method(self, sidebar_navigation):
        """Test that refresh method properly refreshes the sidebar."""
        # Spy on internal methods
        sidebar_navigation._refresh_view_content = MagicMock()

        # Call the method
        sidebar_navigation.refresh()

        # Verify the refresh method was called
        sidebar_navigation._refresh_view_content.assert_called_once()

        # Verify state was updated
        assert sidebar_navigation._update_state["last_update_time"] > 0

    def test_populate_method(self, sidebar_navigation):
        """Test that populate method properly populates the sidebar."""
        # Spy on internal methods
        sidebar_navigation._populate_view_content = MagicMock()

        # Call the method
        sidebar_navigation.populate()

        # Verify the populate method was called
        sidebar_navigation._populate_view_content.assert_called_once()

        # Verify state was updated
        assert sidebar_navigation._update_state["needs_update"] is False
        assert sidebar_navigation._update_state["update_pending"] is False
        assert sidebar_navigation._update_state["initial_population"] is True
        assert sidebar_navigation._update_state["last_update_time"] > 0

    def test_reset_method(self, sidebar_navigation):
        """Test that reset method properly resets the sidebar."""
        # Spy on internal methods
        sidebar_navigation._reset_view_content = MagicMock()

        # Call the method
        sidebar_navigation.reset()

        # Verify the reset method was called
        sidebar_navigation._reset_view_content.assert_called_once()

        # Verify state was updated
        assert sidebar_navigation._update_state["needs_update"] is False
        assert sidebar_navigation._update_state["update_pending"] is False
        assert sidebar_navigation._update_state["initial_population"] is False
        assert sidebar_navigation._update_state["last_update_time"] > 0

    def test_needs_update_method(self, sidebar_navigation):
        """Test that needs_update correctly checks update state."""
        # Initially needs update
        assert sidebar_navigation.needs_update() is True

        # After update, should not need update
        sidebar_navigation.update()
        assert sidebar_navigation.needs_update() is False

        # After setting needs_update to True, should need update
        sidebar_navigation._update_state["needs_update"] = True
        assert sidebar_navigation.needs_update() is True

    def test_schedule_update_uses_update_manager(self, sidebar_navigation, update_manager):
        """Test that schedule_update uses UpdateManager to schedule update."""
        # Spy on update_manager's schedule_update method
        update_manager.schedule_update = MagicMock()

        # Call schedule_update
        sidebar_navigation.schedule_update()

        # Verify UpdateManager's schedule_update was called
        update_manager.schedule_update.assert_called_once_with(sidebar_navigation, 50)

    def test_set_data_loaded_schedules_update(self, sidebar_navigation):
        """Test that set_data_loaded schedules an update."""
        # Spy on schedule_update
        sidebar_navigation.schedule_update = MagicMock()

        # Call set_data_loaded with new value
        sidebar_navigation.set_data_loaded(True)

        # Verify schedule_update was called
        sidebar_navigation.schedule_update.assert_called_once()

        # Verify state was updated
        assert sidebar_navigation._update_state["needs_update"] is True

    def test_update_view_availability_schedules_update(self, sidebar_navigation):
        """Test that update_view_availability schedules an update."""
        # Spy on schedule_update
        sidebar_navigation.schedule_update = MagicMock()

        # Call update_view_availability with new values
        sidebar_navigation.update_view_availability(
            {
                "Dashboard": True,
                "Data": True,
                "Validation": False,
            }
        )

        # Verify schedule_update was called
        sidebar_navigation.schedule_update.assert_called_once()

        # Verify state was updated
        assert sidebar_navigation._update_state["needs_update"] is True
