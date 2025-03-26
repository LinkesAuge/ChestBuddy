"""
Test suite for the DataDependency class.

This module provides tests to verify the functionality of the DataDependency class.
"""

import pytest
from typing import Dict, Any
from unittest.mock import MagicMock

from chestbuddy.core.state.data_dependency import DataDependency


class MockUpdatable:
    """Mock class implementing the IUpdatable interface for testing."""

    def __init__(self, name="MockComponent"):
        self.name = name
        self.update_called = False

    def update(self):
        """Mock update method."""
        self.update_called = True

    def __repr__(self):
        return f"MockUpdatable({self.name})"


@pytest.fixture
def mock_component():
    """Fixture providing a mock updatable component."""
    return MockUpdatable()


@pytest.fixture
def changes_none():
    """Fixture providing a changes dictionary with no changes."""
    return {
        "has_changes": False,
        "row_count_changed": False,
        "columns_changed": False,
        "column_changes": {"A": False, "B": False, "C": False},
        "new_columns": [],
        "removed_columns": [],
    }


@pytest.fixture
def changes_row_count():
    """Fixture providing a changes dictionary with row count changes."""
    return {
        "has_changes": True,
        "row_count_changed": True,
        "columns_changed": False,
        "column_changes": {"A": True, "B": True, "C": True},
        "new_columns": [],
        "removed_columns": [],
    }


@pytest.fixture
def changes_columns():
    """Fixture providing a changes dictionary with column set changes."""
    return {
        "has_changes": True,
        "row_count_changed": False,
        "columns_changed": True,
        "column_changes": {"A": False, "B": False},
        "new_columns": ["D"],
        "removed_columns": [],
    }


@pytest.fixture
def changes_column_values():
    """Fixture providing a changes dictionary with column value changes."""
    return {
        "has_changes": True,
        "row_count_changed": False,
        "columns_changed": False,
        "column_changes": {
            "A": True,  # A changed
            "B": False,
            "C": False,
        },
        "new_columns": [],
        "removed_columns": [],
    }


class TestDataDependency:
    """Tests for the DataDependency class."""

    def test_init_default(self, mock_component):
        """Test initialization with default values."""
        dependency = DataDependency(mock_component)

        # Verify defaults
        assert dependency.component == mock_component
        assert dependency.columns == []
        assert not dependency.row_count_dependency
        assert not dependency.column_set_dependency
        assert not dependency.any_change_dependency

    def test_init_with_columns(self, mock_component):
        """Test initialization with specific columns."""
        columns = ["A", "B", "C"]
        dependency = DataDependency(mock_component, columns=columns)

        # Verify columns dependency
        assert dependency.columns == columns
        assert not dependency.row_count_dependency
        assert not dependency.column_set_dependency
        assert not dependency.any_change_dependency

    def test_init_with_row_count(self, mock_component):
        """Test initialization with row count dependency."""
        dependency = DataDependency(mock_component, row_count_dependency=True)

        # Verify row count dependency
        assert dependency.columns == []
        assert dependency.row_count_dependency
        assert not dependency.column_set_dependency
        assert not dependency.any_change_dependency

    def test_init_with_column_set(self, mock_component):
        """Test initialization with column set dependency."""
        dependency = DataDependency(mock_component, column_set_dependency=True)

        # Verify column set dependency
        assert dependency.columns == []
        assert not dependency.row_count_dependency
        assert dependency.column_set_dependency
        assert not dependency.any_change_dependency

    def test_init_with_any_change(self, mock_component):
        """Test initialization with any change dependency."""
        dependency = DataDependency(mock_component, any_change_dependency=True)

        # Verify any change dependency
        assert dependency.columns == []
        assert not dependency.row_count_dependency
        assert not dependency.column_set_dependency
        assert dependency.any_change_dependency

    def test_should_update_no_changes(self, mock_component, changes_none):
        """Test should_update with no changes."""
        # Test various dependency types
        dep_columns = DataDependency(mock_component, columns=["A", "B"])
        dep_row_count = DataDependency(mock_component, row_count_dependency=True)
        dep_column_set = DataDependency(mock_component, column_set_dependency=True)
        dep_any_change = DataDependency(mock_component, any_change_dependency=True)

        # None should update since there are no changes
        assert not dep_columns.should_update(changes_none)
        assert not dep_row_count.should_update(changes_none)
        assert not dep_column_set.should_update(changes_none)
        assert not dep_any_change.should_update(changes_none)

    def test_should_update_row_count_changes(self, mock_component, changes_row_count):
        """Test should_update with row count changes."""
        # Test various dependency types
        dep_columns = DataDependency(mock_component, columns=["A", "B"])
        dep_row_count = DataDependency(mock_component, row_count_dependency=True)
        dep_column_set = DataDependency(mock_component, column_set_dependency=True)
        dep_any_change = DataDependency(mock_component, any_change_dependency=True)

        # All should update except column_set dependency
        assert dep_columns.should_update(changes_row_count)  # A changed too
        assert dep_row_count.should_update(changes_row_count)
        assert not dep_column_set.should_update(changes_row_count)
        assert dep_any_change.should_update(changes_row_count)

    def test_should_update_column_set_changes(self, mock_component, changes_columns):
        """Test should_update with column set changes."""
        # Test various dependency types
        dep_columns = DataDependency(mock_component, columns=["A", "B"])
        dep_columns_d = DataDependency(mock_component, columns=["D"])  # New column
        dep_row_count = DataDependency(mock_component, row_count_dependency=True)
        dep_column_set = DataDependency(mock_component, column_set_dependency=True)
        dep_any_change = DataDependency(mock_component, any_change_dependency=True)

        # Column set and D dependencies should update
        assert not dep_columns.should_update(changes_columns)
        assert dep_columns_d.should_update(changes_columns)
        assert not dep_row_count.should_update(changes_columns)
        assert dep_column_set.should_update(changes_columns)
        assert dep_any_change.should_update(changes_columns)

    def test_should_update_column_values(self, mock_component, changes_column_values):
        """Test should_update with column value changes."""
        # Test various dependency types
        dep_a = DataDependency(mock_component, columns=["A"])
        dep_b = DataDependency(mock_component, columns=["B"])
        dep_row_count = DataDependency(mock_component, row_count_dependency=True)
        dep_column_set = DataDependency(mock_component, column_set_dependency=True)
        dep_any_change = DataDependency(mock_component, any_change_dependency=True)

        # Only A and any_change dependencies should update
        assert dep_a.should_update(changes_column_values)
        assert not dep_b.should_update(changes_column_values)
        assert not dep_row_count.should_update(changes_column_values)
        assert not dep_column_set.should_update(changes_column_values)
        assert dep_any_change.should_update(changes_column_values)

    def test_repr(self, mock_component):
        """Test string representation."""
        dependency = DataDependency(
            mock_component,
            columns=["A", "B"],
            row_count_dependency=True,
            column_set_dependency=False,
            any_change_dependency=True,
        )

        repr_str = repr(dependency)

        # Verify repr contains key information
        assert "DataDependency" in repr_str
        assert "MockUpdatable" in repr_str
        assert "columns=['A', 'B']" in repr_str
        assert "row_count=True" in repr_str
        assert "column_set=False" in repr_str
        assert "any_change=True" in repr_str
