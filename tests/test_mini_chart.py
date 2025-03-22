"""
Minimal test for ChartService.
"""

import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6.QtCharts import QChart

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService


@pytest.fixture
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_basic_chart_creation(qapp):
    """Test that a basic chart can be created."""
    print("Starting test_basic_chart_creation")

    # Create a data model with sample data
    data_model = ChestDataModel()
    data = pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02"],
            "Player Name": ["Player1", "Player2"],
            "Source/Location": ["Location A", "Location B"],
            "Chest Type": ["Type A", "Type B"],
            "Value": [100, 200],
            "Clan": ["Clan1", "Clan2"],
        }
    )
    data_model.update_data(data)
    print("Data model created and populated")

    # Create a chart service
    chart_service = ChartService(data_model)
    print("Chart service created")

    # Create a bar chart
    chart = chart_service.create_bar_chart(category_column="Chest Type", value_column="Value")
    print(f"Chart created: {chart is not None}")

    # Check if the chart was created
    assert chart is not None, "Chart was not created"
    assert isinstance(chart, QChart), "Created object is not a QChart"

    # Check if chart has at least one series
    assert chart.series(), "Chart has no series"
    print("Test completed successfully")
