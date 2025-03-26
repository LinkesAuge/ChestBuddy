"""
Test suite for the DataState class.

This module provides tests to verify the functionality of the DataState class.
"""

import time
import pytest
import pandas as pd
from typing import Dict, Any

from chestbuddy.core.state.data_state import DataState


@pytest.fixture
def empty_df():
    """Fixture providing an empty DataFrame."""
    return pd.DataFrame(columns=["A", "B", "C"])


@pytest.fixture
def sample_df():
    """Fixture providing a sample DataFrame."""
    return pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"], "C": [True, False, True]})


@pytest.fixture
def numeric_df():
    """Fixture providing a DataFrame with numeric data."""
    return pd.DataFrame(
        {"A": [1, 2, 3, 4, 5], "B": [10.5, 20.5, 30.5, 40.5, 50.5], "C": [100, 200, 300, 400, 500]}
    )


@pytest.fixture
def string_df():
    """Fixture providing a DataFrame with string data."""
    return pd.DataFrame(
        {
            "A": ["apple", "banana", "cherry", "date", "elderberry"],
            "B": ["red", "yellow", "red", "brown", "purple"],
            "C": ["fruit", "fruit", "fruit", "fruit", "fruit"],
        }
    )


class TestDataState:
    """Tests for the DataState class."""

    def test_init_empty(self, empty_df):
        """Test initializing with an empty DataFrame."""
        state = DataState(empty_df)

        # Verify state properties
        assert state.row_count == 0
        assert set(state.column_names) == set(["A", "B", "C"])
        assert len(state.get_column_stats("A")) > 0  # Should have stats even for empty DataFrame

    def test_init_with_data(self, sample_df):
        """Test initializing with a populated DataFrame."""
        state = DataState(sample_df)

        # Verify state properties
        assert state.row_count == 3
        assert set(state.column_names) == set(["A", "B", "C"])

        # Verify column stats were calculated
        a_stats = state.get_column_stats("A")
        assert "min" in a_stats
        assert "max" in a_stats
        assert "mean" in a_stats

        b_stats = state.get_column_stats("B")
        assert "unique_count" in b_stats

        # Verify last_updated is recent
        assert time.time() - state.last_updated < 1.0  # Less than 1 second ago

    def test_numeric_column_stats(self, numeric_df):
        """Test statistics for numeric columns."""
        state = DataState(numeric_df)

        # Verify numeric stats for column A
        a_stats = state.get_column_stats("A")
        assert a_stats["min"] == 1.0
        assert a_stats["max"] == 5.0
        assert a_stats["mean"] == 3.0
        assert a_stats["sum"] == 15.0
        assert a_stats["null_count"] == 0

    def test_string_column_stats(self, string_df):
        """Test statistics for string columns."""
        state = DataState(string_df)

        # Verify string stats for column B
        b_stats = state.get_column_stats("B")
        assert b_stats["unique_count"] == 4  # red, yellow, brown, purple
        assert b_stats["most_common"] == "red"
        assert b_stats["most_common_count"] == 2  # red occurs twice
        assert b_stats["null_count"] == 0

        # Verify stats for column C (all values are the same)
        c_stats = state.get_column_stats("C")
        assert c_stats["unique_count"] == 1
        assert c_stats["most_common"] == "fruit"
        assert c_stats["most_common_count"] == 5

    def test_equality(self, sample_df):
        """Test equals method for comparing states."""
        # Create identical states
        state1 = DataState(sample_df)
        state2 = DataState(sample_df.copy())

        # Create a modified DataFrame
        modified_df = sample_df.copy()
        modified_df.loc[0, "A"] = 100  # Change first value
        state3 = DataState(modified_df)

        # Test equality
        assert state1.equals(state2)
        assert not state1.equals(state3)

    def test_get_changes_no_changes(self, sample_df):
        """Test get_changes method when there are no changes."""
        state1 = DataState(sample_df)
        state2 = DataState(sample_df.copy())

        changes = state1.get_changes(state2)

        # Verify no changes detected
        assert not changes["has_changes"]
        assert not changes["row_count_changed"]
        assert not changes["columns_changed"]
        assert len(changes["new_columns"]) == 0
        assert len(changes["removed_columns"]) == 0

        # Verify column changes
        for column in sample_df.columns:
            assert not changes["column_changes"][column]

    def test_get_changes_value_changes(self, sample_df):
        """Test get_changes method when values change in a column."""
        state1 = DataState(sample_df)

        # Modify column A values
        modified_df = sample_df.copy()
        modified_df.loc[0, "A"] = 100
        state2 = DataState(modified_df)

        changes = state1.get_changes(state2)

        # Verify changes detected
        assert changes["has_changes"]
        assert not changes["row_count_changed"]
        assert not changes["columns_changed"]
        assert len(changes["new_columns"]) == 0
        assert len(changes["removed_columns"]) == 0

        # Verify specific column changes
        assert changes["column_changes"]["A"]  # Column A changed
        assert not changes["column_changes"]["B"]  # Column B unchanged
        assert not changes["column_changes"]["C"]  # Column C unchanged

    def test_get_changes_row_count_changes(self, sample_df):
        """Test get_changes method when row count changes."""
        state1 = DataState(sample_df)

        # Add a row
        modified_df = sample_df.copy()
        modified_df.loc[3] = [4, "w", False]
        state2 = DataState(modified_df)

        changes = state1.get_changes(state2)

        # Verify changes detected
        assert changes["has_changes"]
        assert changes["row_count_changed"]
        assert not changes["columns_changed"]

        # All columns should show as changed due to statistical differences
        assert changes["column_changes"]["A"]
        assert changes["column_changes"]["B"]
        assert changes["column_changes"]["C"]

    def test_get_changes_column_changes(self, sample_df):
        """Test get_changes method when columns change."""
        state1 = DataState(sample_df)

        # Add a new column
        modified_df = sample_df.copy()
        modified_df["D"] = [10, 20, 30]
        state2 = DataState(modified_df)

        # The new column is in state2, so we need to call get_changes on state2 comparing with state1
        # rather than the other way around
        changes = state2.get_changes(state1)

        # Verify changes detected
        assert changes["has_changes"]
        assert not changes["row_count_changed"]
        assert changes["columns_changed"]
        assert changes["new_columns"] == ["D"]
        assert changes["removed_columns"] == []

        # Original columns should not show as changed
        assert not changes["column_changes"]["A"]
        assert not changes["column_changes"]["B"]
        assert not changes["column_changes"]["C"]

    def test_get_changes_column_removal(self, sample_df):
        """Test get_changes method when columns are removed."""
        state1 = DataState(sample_df)

        # Remove a column
        modified_df = sample_df.copy()
        modified_df = modified_df.drop(columns=["C"])
        state2 = DataState(modified_df)

        # When comparing state1 (with C) to state2 (without C), C should be in new_columns for state1
        changes = state1.get_changes(state2)

        # Verify changes detected
        assert changes["has_changes"]
        assert not changes["row_count_changed"]
        assert changes["columns_changed"]
        assert changes["new_columns"] == ["C"]  # Column C is in state1 but not in state2
        assert changes["removed_columns"] == []

        # Remaining columns should not show as changed
        assert not changes["column_changes"]["A"]
        assert not changes["column_changes"]["B"]

    def test_update_from_data(self, sample_df, numeric_df):
        """Test updating state from different DataFrames."""
        # Initialize with sample data
        state = DataState(sample_df)
        assert state.row_count == 3

        # Update with numeric data
        state.update_from_data(numeric_df)
        assert state.row_count == 5

        # Verify hash value was updated
        assert state._hash_value != ""

    def test_repr(self, sample_df):
        """Test string representation."""
        state = DataState(sample_df)
        repr_str = repr(state)

        # Verify repr contains key information
        assert "DataState" in repr_str
        assert "rows=3" in repr_str
        assert "columns=3" in repr_str
        assert "hash=" in repr_str
