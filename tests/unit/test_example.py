"""
Example unit tests.

This file contains example unit tests for the ChestBuddy application.
"""

import pytest
from tests.data import TestDataFactory


class TestExample:
    """Example test class for unit tests."""

    def test_data_factory_creates_small_dataset(self):
        """Test that TestDataFactory can create a small dataset."""
        data = TestDataFactory.create_small_data()

        # Check that data has the expected columns
        for column in TestDataFactory.EXPECTED_COLUMNS:
            assert column in data.data

        # Check that data has the expected number of rows
        first_column = TestDataFactory.EXPECTED_COLUMNS[0]
        assert len(data.data[first_column]) == 10

    def test_data_factory_creates_dataset_with_errors(self):
        """Test that TestDataFactory can create a dataset with errors."""
        data = TestDataFactory.create_dataset_with_errors(size=10, error_rate=0.5)

        # Check that data has the expected columns
        for column in TestDataFactory.EXPECTED_COLUMNS:
            assert column in data.data

        # Check that data has the expected number of rows
        first_column = TestDataFactory.EXPECTED_COLUMNS[0]
        assert len(data.data[first_column]) == 10
