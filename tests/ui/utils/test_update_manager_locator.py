"""
Test the integration of UpdateManager with ServiceLocator.

This module tests how the UpdateManager can be accessed via the ServiceLocator,
ensuring components can get the service when needed.
"""

import pytest
from unittest.mock import MagicMock
from pytestqt.qtbot import QtBot

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.ui.utils.update_manager import UpdateManager
from chestbuddy.ui.interfaces import IUpdatable


class MockUpdatableWidget(QWidget):
    """Mock updatable widget for testing."""

    update_requested = Signal()
    update_completed = Signal()

    def __init__(self, name="mock"):
        """Initialize the mock widget."""
        super().__init__()
        self.name = name
        self.updated = False
        self.refreshed = False
        self.populated = False
        self.reset_called = False
        self._last_update_timestamp = 0.0

    def refresh(self):
        """Refresh the component."""
        self.refreshed = True

    def update(self, data=None):
        """Update the component with data."""
        self.updated = True
        self.update_data = data
        self.update_completed.emit()

    def populate(self, data=None):
        """Populate the component with data."""
        self.populated = True
        self.populate_data = data

    def needs_update(self):
        """Check if the component needs update."""
        return True

    def reset(self):
        """Reset the component."""
        self.reset_called = True

    def last_update_time(self):
        """Get the timestamp of the last update."""
        return self._last_update_timestamp


class TestUpdateManagerLocator:
    """Test the integration of UpdateManager with ServiceLocator."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Clear service locator
        ServiceLocator.clear()

    def teardown_method(self):
        """Clean up after each test."""
        ServiceLocator.clear()

    def test_register_and_access_update_manager(self, qtbot):
        """Test registering UpdateManager in ServiceLocator and accessing it."""
        # Create UpdateManager
        update_manager = UpdateManager()

        # Register in ServiceLocator
        ServiceLocator.register("update_manager", update_manager)

        # Verify it's accessible
        retrieved_manager = ServiceLocator.get("update_manager")
        assert retrieved_manager is update_manager

        # Check type-safe access
        typed_manager = ServiceLocator.get_typed("update_manager", UpdateManager)
        assert typed_manager is update_manager

    def test_component_using_service_locator(self, qtbot):
        """Test a component accessing and using UpdateManager through ServiceLocator."""
        # Create and register UpdateManager
        update_manager = UpdateManager()
        ServiceLocator.register("update_manager", update_manager)

        # Create updatable component
        component = MockUpdatableWidget("test_component")
        qtbot.add_widget(component)

        # Schedule update via service locator
        manager = ServiceLocator.get("update_manager")
        manager.schedule_update(component)

        # Process updates
        manager.process_pending_updates()

        # Verify component was updated
        assert component.updated

    def test_factory_for_update_manager(self, qtbot):
        """Test using a factory function for creating the UpdateManager."""
        # Create a factory function
        factory_called = False

        def create_update_manager():
            nonlocal factory_called
            factory_called = True
            return UpdateManager()

        # Register factory
        ServiceLocator.register_factory("update_manager", create_update_manager)

        # Verify factory wasn't called yet
        assert not factory_called

        # Get the service
        manager = ServiceLocator.get("update_manager")

        # Verify factory was called
        assert factory_called
        assert isinstance(manager, UpdateManager)

        # Use the manager
        component = MockUpdatableWidget()
        qtbot.add_widget(component)
        manager.schedule_update(component)
        manager.process_pending_updates()
        assert component.updated

    def test_multiple_components_with_same_manager(self, qtbot):
        """Test multiple components using the same UpdateManager instance from ServiceLocator."""
        # Register UpdateManager
        update_manager = UpdateManager()
        ServiceLocator.register("update_manager", update_manager)

        # Create multiple components
        components = [MockUpdatableWidget(f"component_{i}") for i in range(3)]
        for component in components:
            qtbot.add_widget(component)

        # Get manager through ServiceLocator in multiple places
        manager1 = ServiceLocator.get("update_manager")
        manager2 = ServiceLocator.get("update_manager")

        # Verify they're the same instance
        assert manager1 is manager2

        # Schedule updates from different manager instances
        manager1.schedule_update(components[0])
        manager2.schedule_update(components[1])
        manager1.schedule_update(components[2])

        # Process updates
        manager1.process_pending_updates()

        # Verify all components were updated
        for component in components:
            assert component.updated

    def test_cleanup_through_service_locator(self, qtbot):
        """Test cleaning up the UpdateManager through ServiceLocator."""
        # Register UpdateManager
        update_manager = UpdateManager()
        ServiceLocator.register("update_manager", update_manager)

        # Schedule some updates
        component = MockUpdatableWidget()
        qtbot.add_widget(component)
        update_manager.schedule_update(component)

        # Clear ServiceLocator
        ServiceLocator.clear()

        # Verify UpdateManager is no longer available
        assert not ServiceLocator.has_service("update_manager")

        # Trying to get it should raise an error
        with pytest.raises(KeyError):
            ServiceLocator.get("update_manager")
