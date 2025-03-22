"""
Performance tests for chart generation.

This module tests chart generation performance with datasets of various sizes.
"""

import pytest
import pandas as pd
import time
import psutil
import os
import random
from datetime import datetime, timedelta

from PySide6.QtWidgets import QApplication

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService


@pytest.fixture
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def small_dataset():
    """Create a small dataset (100 rows)."""
    return generate_dataset(100)


@pytest.fixture
def medium_dataset():
    """Create a medium dataset (1,000 rows)."""
    return generate_dataset(1000)


@pytest.fixture
def large_dataset():
    """Create a large dataset (10,000 rows)."""
    return generate_dataset(10000)


def generate_dataset(size):
    """
    Generate a test dataset of the specified size.

    Args:
        size: Number of rows to generate

    Returns:
        DataFrame with test data
    """
    # Lists of sample values for categorical columns
    player_names = ["Player" + str(i) for i in range(1, 21)]
    locations = ["Location " + chr(65 + i) for i in range(20)]
    chest_types = ["Type " + chr(65 + i) for i in range(10)]
    clans = ["Clan" + str(i) for i in range(1, 11)]

    # Generate base date and random dates around it
    base_date = datetime(2023, 1, 1)

    # Generate the data
    data = {
        "Date": [
            (base_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
            for _ in range(size)
        ],
        "Player Name": [random.choice(player_names) for _ in range(size)],
        "Source/Location": [random.choice(locations) for _ in range(size)],
        "Chest Type": [random.choice(chest_types) for _ in range(size)],
        "Value": [random.randint(50, 500) for _ in range(size)],
        "Clan": [random.choice(clans) for _ in range(size)],
    }

    return pd.DataFrame(data)


def measure_execution_time(func, *args, **kwargs):
    """
    Measure the execution time of a function.

    Args:
        func: Function to measure
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Tuple of (result, execution_time_in_ms)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()

    execution_time_ms = (end_time - start_time) * 1000
    return result, execution_time_ms


def measure_memory_usage(func, *args, **kwargs):
    """
    Measure the memory usage of a function.

    Args:
        func: Function to measure
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Tuple of (result, memory_usage_in_mb)
    """
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB

    result = func(*args, **kwargs)

    memory_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    memory_used = memory_after - memory_before

    return result, memory_used


class TestChartPerformance:
    """Tests for chart generation performance with various dataset sizes."""

    def test_bar_chart_performance_small(self, qapp, small_dataset):
        """Test bar chart generation performance with a small dataset."""
        # Setup
        model = ChestDataModel()
        model.update_data(small_dataset)
        service = ChartService(model)

        # Measure performance
        _, execution_time = measure_execution_time(
            service.create_bar_chart, category_column="Chest Type", value_column="Value"
        )

        # Assertions - threshold values can be adjusted based on actual performance
        assert execution_time < 500, f"Bar chart generation too slow: {execution_time}ms"
        print(f"Small dataset bar chart generation time: {execution_time:.2f}ms")

    def test_bar_chart_performance_medium(self, qapp, medium_dataset):
        """Test bar chart generation performance with a medium dataset."""
        # Setup
        model = ChestDataModel()
        model.update_data(medium_dataset)
        service = ChartService(model)

        # Measure performance
        _, execution_time = measure_execution_time(
            service.create_bar_chart, category_column="Chest Type", value_column="Value"
        )

        # Assertions
        assert execution_time < 1000, f"Bar chart generation too slow: {execution_time}ms"
        print(f"Medium dataset bar chart generation time: {execution_time:.2f}ms")

    def test_bar_chart_performance_large(self, qapp, large_dataset):
        """Test bar chart generation performance with a large dataset."""
        # Setup
        model = ChestDataModel()
        model.update_data(large_dataset)
        service = ChartService(model)

        # Measure performance
        _, execution_time = measure_execution_time(
            service.create_bar_chart, category_column="Chest Type", value_column="Value"
        )

        # Assertions
        assert execution_time < 2000, f"Bar chart generation too slow: {execution_time}ms"
        print(f"Large dataset bar chart generation time: {execution_time:.2f}ms")

    def test_pie_chart_performance(self, qapp, medium_dataset):
        """Test pie chart generation performance."""
        # Setup
        model = ChestDataModel()
        model.update_data(medium_dataset)
        service = ChartService(model)

        # Measure performance
        _, execution_time = measure_execution_time(
            service.create_pie_chart, category_column="Chest Type", value_column="Value"
        )

        # Assertions
        assert execution_time < 1000, f"Pie chart generation too slow: {execution_time}ms"
        print(f"Pie chart generation time: {execution_time:.2f}ms")

    def test_line_chart_performance(self, qapp, medium_dataset):
        """Test line chart generation performance."""
        # Setup
        model = ChestDataModel()
        model.update_data(medium_dataset)
        service = ChartService(model)

        # Measure performance
        _, execution_time = measure_execution_time(
            service.create_line_chart, x_column="Date", y_column="Value"
        )

        # Assertions
        assert execution_time < 1000, f"Line chart generation too slow: {execution_time}ms"
        print(f"Line chart generation time: {execution_time:.2f}ms")

    def test_memory_usage(self, qapp, large_dataset):
        """Test memory usage during chart generation with a large dataset."""
        # Setup
        model = ChestDataModel()
        model.update_data(large_dataset)
        service = ChartService(model)

        # Measure memory usage
        _, memory_used = measure_memory_usage(
            service.create_bar_chart, category_column="Chest Type", value_column="Value"
        )

        # Assertions - adjust threshold based on actual memory usage
        assert memory_used < 50, f"Chart generation uses too much memory: {memory_used:.2f}MB"
        print(f"Memory used for large dataset chart generation: {memory_used:.2f}MB")
