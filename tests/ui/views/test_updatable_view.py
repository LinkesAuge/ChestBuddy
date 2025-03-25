"""
test_updatable_view.py

Description: Tests for the UpdatableView class.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from chestbuddy.ui.views.updatable_view import UpdatableView
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import UpdateManager
from chestbuddy.utils.service_locator import ServiceLocator


class MockData:
    """Mock data class for testing."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class SimpleUpdatableView(UpdatableView):
    """Simple implementation of UpdatableView for testing."""

    def __init__(self, parent=None):
        super().__init__("Test View", parent)
        self.update_called = False
        self.refresh_called = False
        self.populate_called = False
        self.reset_called = False
        self.last_data = None

        # Add a label to the content area for testing
        self.label = QLabel("Initial content")
        self.get_content_layout().addWidget(self.label)

    def _update_view_content(self, data=None):
        """Update the view content."""
        self.update_called = True
        self.last_data = data
        if data:
            self.label.setText(f"Updated: {data}")

    def _refresh_view_content(self):
        """Refresh the view content."""
        self.refresh_called = True
        self.label.setText(f"Refreshed: {self.last_data}")

    def _populate_view_content(self, data=None):
        """Populate the view content."""
        self.populate_called = True
        self.last_data = data
        if data:
            self.label.setText(f"Populated: {data}")

    def _reset_view_content(self):
        """Reset the view content."""
        self.reset_called = True
        self.last_data = None
        self.label.setText("Initial content")


@pytest.fixture
def update_manager():
    """Fixture providing an UpdateManager instance registered with ServiceLocator."""
    # Create update manager
    manager = UpdateManager()

    # Register with ServiceLocator
    ServiceLocator.register("update_manager", manager)

    yield manager

    # Clean up
    ServiceLocator.remove("update_manager")


@pytest.fixture
def updatable_view(qtbot):
    """Fixture providing a SimpleUpdatableView instance."""
    view = SimpleUpdatableView()
    qtbot.addWidget(view)
    return view


class TestUpdatableView:
    """Tests for the UpdatableView class."""

    def test_implements_iupdatable(self, updatable_view):
        """Test that UpdatableView implements the IUpdatable interface."""
        assert isinstance(updatable_view, IUpdatable)
        assert isinstance(updatable_view, UpdatableView)

    def test_update_method(self, updatable_view):
        """Test the update method."""
        test_data = MockData("test data")
        updatable_view.update(test_data)

        assert updatable_view.update_called
        assert updatable_view.last_data == test_data
        assert updatable_view.label.text() == f"Updated: {test_data}"

    def test_refresh_method(self, updatable_view):
        """Test the refresh method."""
        # First update with data
        test_data = MockData("test data")
        updatable_view.update(test_data)

        # Then refresh
        updatable_view.refresh()

        assert updatable_view.refresh_called
        assert updatable_view.label.text() == f"Refreshed: {test_data}"

    def test_populate_method(self, updatable_view):
        """Test the populate method."""
        test_data = MockData("test data")
        updatable_view.populate(test_data)

        assert updatable_view.populate_called
        assert updatable_view.last_data == test_data
        assert updatable_view.label.text() == f"Populated: {test_data}"
        assert updatable_view.is_populated()

    def test_reset_method(self, updatable_view):
        """Test the reset method."""
        # First update with data
        test_data = MockData("test data")
        updatable_view.update(test_data)

        # Then reset
        updatable_view.reset()

        assert updatable_view.reset_called
        assert updatable_view.last_data is None
        assert updatable_view.label.text() == "Initial content"
        assert not updatable_view.is_populated()

    def test_schedule_update_with_update_manager(self, updatable_view, update_manager):
        """Test scheduling an update with UpdateManager."""
        # Set up update manager
        update_manager.schedule_update = MagicMock()

        # Call schedule_update
        updatable_view.schedule_update()

        # Verify update manager was called
        update_manager.schedule_update.assert_called_once_with(updatable_view, 50)

    @patch("chestbuddy.ui.utils.get_update_manager")
    def test_schedule_update_error_fallback(self, mock_get_update_manager, updatable_view):
        """Test fallback behavior when UpdateManager isn't available."""
        # Mock get_update_manager to raise an exception
        mock_get_update_manager.side_effect = KeyError("update_manager not registered")

        # Create spies for update method
        original_update = updatable_view.update
        updatable_view.update = MagicMock()

        try:
            # Call schedule_update
            updatable_view.schedule_update()

            # Verify direct update was called as fallback
            updatable_view.update.assert_called_once()
        finally:
            # Restore original method
            updatable_view.update = original_update

    def test_request_update(self, updatable_view, update_manager):
        """Test the request_update method."""
        # Set up update manager
        update_manager.schedule_update = MagicMock()

        # Spy on needs_update property
        updatable_view.needs_update = MagicMock(return_value=False)

        # Call request_update
        updatable_view.request_update()

        # Verify state was updated and update was scheduled
        assert updatable_view._update_state["needs_update"] is True
        update_manager.schedule_update.assert_called_once_with(updatable_view, 50)

    def test_updatable_signals(self, updatable_view, qtbot):
        """Test that updatable signals are properly connected."""
        # Set up signal spy
        update_requested_spy = qtbot.waitSignal(updatable_view.update_requested, timeout=100)
        update_completed_spy = qtbot.waitSignal(updatable_view.update_completed, timeout=100)

        # Trigger update
        updatable_view.update()

        # Verify signals were emitted
        assert update_requested_spy.signal_triggered
        assert update_completed_spy.signal_triggered

    def test_integration_with_base_view(self, updatable_view):
        """Test integration with BaseView functionality."""
        # Test title property
        assert updatable_view.get_title() == "Test View"

        # Test changing title
        updatable_view.set_title("New Title")
        assert updatable_view.get_title() == "New Title"

        # Test content layout
        assert updatable_view.get_content_layout() is not None
        assert updatable_view.label.parent() is not None
