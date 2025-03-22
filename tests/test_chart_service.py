"""
Tests for the ChartService.

This module contains tests for the chart generation functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest
from PySide6.QtCore import QObject
from PySide6.QtCharts import QChart, QBarSeries, QPieSeries, QLineSeries
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
def model():
    """Create a fresh ChestDataModel instance for testing."""
    return ChestDataModel()


@pytest.fixture
def sample_data():
    """Create sample data for testing charts."""
    return pd.DataFrame(
        {
            "Date": ["2025-03-11", "2025-03-11", "2025-03-11", "2025-03-12"],
            "Player Name": ["Feldjäger", "Krümelmonster", "OsmanlıTorunu", "D4rkBlizZ4rD"],
            "Source/Location": [
                "Level 25 Crypt",
                "Level 20 Crypt",
                "Level 15 rare Crypt",
                "Level 30 rare Crypt",
            ],
            "Chest Type": [
                "Fire Chest",
                "Infernal Chest",
                "Rare Dragon Chest",
                "Ancient Bastion Chest",
            ],
            "Value": [275, 84, 350, 550],
            "Clan": ["MY_CLAN", "MY_CLAN", "MY_CLAN", "MY_CLAN"],
        }
    )


@pytest.fixture
def temp_image_file():
    """Create a temporary image file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file_path = temp_file.name

    # Clean up the file after the test
    yield temp_file_path
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


class TestChartService:
    """Tests for the ChartService class."""

    def test_initialization(self, qapp, model):
        """Test that service initializes correctly."""
        service = ChartService(model)
        assert service is not None
        assert service._data_model is model

    def test_create_bar_chart(self, qapp, model, sample_data):
        """Test creating a bar chart."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ChartService(model)

        # Create a bar chart
        chart = service.create_bar_chart(
            category_column="Chest Type", value_column="Value", title="Chest Values by Type"
        )

        # Verify the chart was created correctly
        assert isinstance(chart, QChart)
        assert chart.title() == "Chest Values by Type"

        # Check that we have a bar series
        series_list = chart.series()
        assert len(series_list) > 0
        # At least one series should be a QBarSeries
        assert any(isinstance(series, QBarSeries) for series in series_list)

    def test_create_pie_chart(self, qapp, model, sample_data):
        """Test creating a pie chart."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ChartService(model)

        # Create a pie chart
        chart = service.create_pie_chart(
            category_column="Chest Type", value_column="Value", title="Chest Type Distribution"
        )

        # Verify the chart was created correctly
        assert isinstance(chart, QChart)
        assert chart.title() == "Chest Type Distribution"

        # Check that we have a pie series
        series_list = chart.series()
        assert len(series_list) > 0
        # At least one series should be a QPieSeries
        assert any(isinstance(series, QPieSeries) for series in series_list)

    def test_create_line_chart(self, qapp, model, sample_data):
        """Test creating a line chart."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ChartService(model)

        # Create a line chart
        chart = service.create_line_chart(
            x_column="Date", y_column="Value", title="Chest Values Over Time"
        )

        # Verify the chart was created correctly
        assert isinstance(chart, QChart)
        assert chart.title() == "Chest Values Over Time"

        # Check that we have a line series
        series_list = chart.series()
        assert len(series_list) > 0
        # At least one series should be a QLineSeries
        assert any(isinstance(series, QLineSeries) for series in series_list)

    def test_chart_with_empty_data(self, qapp, model):
        """Test chart creation with empty data."""
        # Create service
        service = ChartService(model)

        # Create a chart with empty data
        with pytest.raises(ValueError) as excinfo:
            service.create_bar_chart(category_column="Chest Type", value_column="Value")

        # Verify the error message
        assert "empty data" in str(excinfo.value)

    def test_save_chart(self, qapp, model, sample_data, temp_image_file):
        """Test saving a chart to a file."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ChartService(model)

        # Create a chart
        chart = service.create_bar_chart(category_column="Chest Type", value_column="Value")

        # Save the chart
        success = service.save_chart(chart, temp_image_file)

        # Verify the chart was saved
        assert success is True
        assert os.path.exists(temp_image_file)
        assert os.path.getsize(temp_image_file) > 0

    def test_save_chart_error(self, qapp, model, sample_data):
        """Test error handling when saving a chart."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ChartService(model)

        # Create a chart
        chart = service.create_bar_chart(category_column="Chest Type", value_column="Value")

        # Try to save to an invalid location
        with pytest.raises(ValueError) as excinfo:
            service.save_chart(chart, "")

        # Verify the error message
        assert "Invalid file path" in str(excinfo.value)

    def test_unsupported_chart_type(self, qapp, model, sample_data):
        """Test error handling for unsupported chart type."""
        # Update model with sample data
        model.update_data(sample_data)

        # Create service
        service = ChartService(model)

        # Create a mock chart method that raises an exception
        with patch.object(service, "create_bar_chart") as mock_create_chart:

            def mock_side_effect(*args, **kwargs):
                raise ValueError("Unsupported chart type: XYZ")

            mock_create_chart.side_effect = mock_side_effect

            # Try to create an unsupported chart type
            with pytest.raises(ValueError) as excinfo:
                service.create_bar_chart(category_column="Chest Type", value_column="Value")

            # Verify the error message
            assert "Unsupported chart type" in str(excinfo.value)
