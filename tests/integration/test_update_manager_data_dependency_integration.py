"""
Integration tests for UpdateManager with DataDependency.

This module tests the integration between UpdateManager, DataDependency, and
IUpdatable components to ensure updates are correctly scheduled based on
specific data changes.
"""

import pytest
import pandas as pd
import time
from typing import Optional, Any
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtWidgets import QWidget

from chestbuddy.ui.utils.update_manager import UpdateManager
from chestbuddy.core.state.data_state import DataState
from chestbuddy.core.state.data_dependency import DataDependency
from chestbuddy.ui.interfaces import IUpdatable, UpdatableComponent


class MockUpdatable(UpdatableComponent):
    """Mock updatable component for testing."""

    def __init__(self, component_id=None):
        """Initialize the mock component."""
        super().__init__()
        self.component_id = component_id or "mock_component"
        self.update_count = 0
        self.last_update_timestamp = 0
        self.last_update_priority = 0

    def _do_update(self, data: Optional[Any] = None) -> None:
        """Implement component-specific update logic."""
        self.update_count += 1

    def request_update(self, timestamp=0, priority=0):
        """Handle external update requests."""
        self.update_count += 1
        self.last_update_timestamp = timestamp
        self.last_update_priority = priority
        self.update_requested.emit()


@pytest.fixture
def update_manager():
    """Create an UpdateManager instance for testing."""
    manager = UpdateManager()

    # Make sure to clean up the timer to avoid QTimer warnings
    yield manager

    if hasattr(manager, "_update_timer") and manager._update_timer is not None:
        manager._update_timer.stop()
        manager._update_timer.deleteLater()
        manager._update_timer = None


@pytest.fixture
def data_state():
    """Create a DataState instance for testing."""
    df = pd.DataFrame(
        {"column_a": [1, 2, 3], "column_b": ["a", "b", "c"], "column_c": [True, False, True]}
    )
    return DataState(df)


@pytest.fixture
def updated_data_state():
    """Create an updated DataState instance for testing."""
    df = pd.DataFrame(
        {
            "column_a": [1, 2, 3, 4],
            "column_b": ["a", "b", "c", "d"],
            "column_c": [True, False, True, False],
        }
    )
    return DataState(df)


@pytest.fixture
def column_changed_data_state():
    """Create a DataState with changed column values."""
    df = pd.DataFrame(
        {
            "column_a": [10, 20, 30],  # Changed values
            "column_b": ["a", "b", "c"],
            "column_c": [True, False, True],
        }
    )
    return DataState(df)


class TestUpdateManagerDataDependencyIntegration:
    """Test the integration between UpdateManager and DataDependency."""

    def test_register_data_dependency(self, update_manager):
        """Test registering data dependencies for components."""
        component = MockUpdatable()
        dependency = DataDependency(component, columns=["column_a"])

        update_manager.register_data_dependency(component, dependency)

        assert component in update_manager._data_dependencies
        assert update_manager._data_dependencies[component] is dependency

    def test_update_based_on_column_dependency(
        self, update_manager, data_state, column_changed_data_state
    ):
        """Test that only components with matching column dependencies get updated."""
        # Component that depends on column_a
        component_a = MockUpdatable("component_a")
        dependency_a = DataDependency(component_a, columns=["column_a"])
        update_manager.register_data_dependency(component_a, dependency_a)
        update_manager.schedule_update(component_a)

        # Component that depends on column_b
        component_b = MockUpdatable("component_b")
        dependency_b = DataDependency(component_b, columns=["column_b"])
        update_manager.register_data_dependency(component_b, dependency_b)
        update_manager.schedule_update(component_b)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Reset update counts
        component_a.update_count = 0
        component_b.update_count = 0

        # Update with column_a changed
        update_manager.update_data_state(column_changed_data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Only component_a should be updated since only column_a changed
        assert component_a.update_count == 1
        assert component_b.update_count == 0

    def test_update_based_on_row_count_dependency(
        self, update_manager, data_state, updated_data_state
    ):
        """Test that row count dependencies work correctly."""
        # Component that depends on row count
        component = MockUpdatable()
        dependency = DataDependency(component, row_count_dependency=True)
        update_manager.register_data_dependency(component, dependency)
        update_manager.schedule_update(component)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Reset update count
        component.update_count = 0

        # Update with a data state that has a different row count
        update_manager.update_data_state(updated_data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Component should be updated since row count changed
        assert component.update_count == 1

    def test_update_based_on_column_set_dependency(self, update_manager, data_state):
        """Test that column set dependencies work correctly."""
        # Component that depends on the set of columns
        component = MockUpdatable()
        dependency = DataDependency(component, column_set_dependency=True)
        update_manager.register_data_dependency(component, dependency)
        update_manager.schedule_update(component)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Reset update count
        component.update_count = 0

        # Create new data state with an additional column
        df = pd.DataFrame(
            {
                "column_a": [1, 2, 3],
                "column_b": ["a", "b", "c"],
                "column_c": [True, False, True],
                "column_d": [10, 20, 30],  # New column
            }
        )
        new_state = DataState(df)

        # Update with the new data state
        update_manager.update_data_state(new_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Component should be updated since column set changed
        assert component.update_count == 1

    def test_multiple_dependencies_with_overlap(
        self, update_manager, data_state, updated_data_state
    ):
        """Test components with multiple dependencies with overlapping data."""
        # Component with multiple dependencies
        component = MockUpdatable()

        # Register with both row count and specific column dependency
        dependency = DataDependency(component, columns=["column_a"], row_count_dependency=True)

        update_manager.register_data_dependency(component, dependency)
        update_manager.schedule_update(component)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Reset update count
        component.update_count = 0

        # Update with data state that has both more rows and changed column_a
        update_manager.update_data_state(updated_data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Component should only be updated once despite matching multiple dependencies
        assert component.update_count == 1

    def test_no_update_when_unrelated_changes(self, update_manager, data_state):
        """Test that components don't update when unrelated data changes."""
        # Component that depends on column_a
        component = MockUpdatable()
        dependency = DataDependency(component, columns=["column_a"])
        update_manager.register_data_dependency(component, dependency)
        update_manager.schedule_update(component)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Reset update count
        component.update_count = 0

        # Create new data state with change to column_b only
        df = pd.DataFrame(
            {
                "column_a": [1, 2, 3],  # Unchanged
                "column_b": ["x", "y", "z"],  # Changed
                "column_c": [True, False, True],  # Unchanged
            }
        )
        new_state = DataState(df)

        # Update with the new data state
        update_manager.update_data_state(new_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Component should not be updated since its dependency (column_a) didn't change
        assert component.update_count == 0

    def test_unregister_data_dependency(self, update_manager, data_state, updated_data_state):
        """Test unregistering data dependencies for components."""
        # Component that depends on row count
        component = MockUpdatable()
        dependency = DataDependency(component, row_count_dependency=True)
        update_manager.register_data_dependency(component, dependency)
        update_manager.schedule_update(component)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Unregister data dependency
        update_manager.unregister_data_dependency(component)

        # Reset update count
        component.update_count = 0

        # Update with a data state that has a different row count
        update_manager.update_data_state(updated_data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Component should not be updated since its dependency was unregistered
        assert component.update_count == 0
        assert component not in update_manager._data_dependencies

    def test_data_dependency_priority(self, update_manager, data_state, updated_data_state):
        """Test that both components with row count dependencies get updated."""
        # Components with different names
        component_a = MockUpdatable("component_a")
        component_b = MockUpdatable("component_b")

        # Register both with row count dependency
        dep_a = DataDependency(component_a, row_count_dependency=True)
        dep_b = DataDependency(component_b, row_count_dependency=True)

        update_manager.register_data_dependency(component_a, dep_a)
        update_manager.register_data_dependency(component_b, dep_b)

        # Register components
        update_manager.schedule_update(component_a)
        update_manager.schedule_update(component_b)

        # Initial update with original data state
        update_manager.update_data_state(data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Reset update counts
        component_a.update_count = 0
        component_b.update_count = 0

        # Update with a data state that has a different row count
        update_manager.update_data_state(updated_data_state)

        # Process immediate updates
        update_manager.process_pending_updates()

        # Both components should be updated since row count changed
        assert component_a.update_count == 1
        assert component_b.update_count == 1
