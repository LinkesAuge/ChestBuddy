"""
Example unit test.

This is a sample unit test to demonstrate the testing structure.
"""

import pytest
from tests.data import TestDataFactory


@pytest.mark.unit
class TestExample:
    """Example test case to demonstrate testing structure."""

    def test_data_factory_creates_small_dataset(self):
        """Test that TestDataFactory can create a small dataset."""
        data = TestDataFactory.create_small_data()

        # Check that data has the expected columns
        for column in TestDataFactory.EXPECTED_COLUMNS:
            assert column in data.columns

        # Check that we have rows in the dataset
        assert len(data) > 0
        assert len(data) <= TestDataFactory.SMALL_SIZE

    def test_data_factory_creates_dataset_with_errors(self):
        """Test that TestDataFactory can create a dataset with errors."""
        data = TestDataFactory.create_dataset_with_errors(size=10, error_rate=0.5)

        # Check that data has the expected columns
        for column in TestDataFactory.EXPECTED_COLUMNS:
            assert column in data.columns

        # Check that we have rows in the dataset
        assert len(data) == 10
