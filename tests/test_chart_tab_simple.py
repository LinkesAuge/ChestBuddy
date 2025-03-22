"""
Simple tests for ChartTab.
"""

import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from unittest.mock import MagicMock, patch
from pathlib import Path

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.ui.chart_tab import ChartTab


@pytest.fixture
def qapp():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        "Date": ["2023-01-01", "2023-01-02"],
        "Player Name": ["Player1", "Player2"],
        "Source/Location": ["Location A", "Location B"],
        "Chest Type": ["Type A", "Type B"],
        "Value": [100, 200],
        "Clan": ["Clan1", "Clan2"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def data_model(qapp, sample_data):
    """Create a data model with sample data."""
    model = ChestDataModel()
    model.update_data(sample_data)
    return model


@pytest.fixture
def chart_service(data_model):
    """Create a ChartService instance."""
    return ChartService(data_model)


@pytest.fixture
def mock_chart_service(data_model):
    """Create a mocked ChartService for safer testing."""
    mock = MagicMock(spec=ChartService)
    # Set up mock to return a mock chart
    mock_chart = MagicMock()
    mock.create_bar_chart.return_value = mock_chart
    mock.create_pie_chart.return_value = mock_chart
    mock.create_line_chart.return_value = mock_chart
    mock.save_chart.return_value = True
    return mock


def test_chart_tab_initialization(qapp, data_model, chart_service):
    """Test that the ChartTab can be initialized."""
    chart_tab = ChartTab(data_model, chart_service)
    assert chart_tab is not None
    assert chart_tab.chart_service == chart_service
    assert chart_tab.data_model == data_model


def test_chart_tab_ui_components(qapp, data_model, chart_service):
    """Test that the ChartTab UI components are created properly."""
    chart_tab = ChartTab(data_model, chart_service)

    # Check that essential UI components exist
    assert hasattr(chart_tab, "chart_type_combo")
    assert hasattr(chart_tab, "x_axis_combo")
    assert hasattr(chart_tab, "y_axis_combo")
    assert hasattr(chart_tab, "group_by_combo")
    assert hasattr(chart_tab, "chart_view")
    assert hasattr(chart_tab, "export_button")
    assert hasattr(chart_tab, "create_chart_button")

    # Check that the chart_type_combo has the expected options
    assert chart_tab.chart_type_combo.count() == 3
    assert chart_tab.chart_type_combo.itemText(0) == "Bar Chart"
    assert chart_tab.chart_type_combo.itemText(1) == "Pie Chart"
    assert chart_tab.chart_type_combo.itemText(2) == "Line Chart"


def test_column_combo_updates(qapp, data_model, chart_service):
    """Test that column comboboxes are updated with data model columns."""
    chart_tab = ChartTab(data_model, chart_service)

    # Verify column combos have been populated with data model columns
    columns = data_model.data.columns.tolist()

    assert chart_tab.x_axis_combo.count() == len(columns)
    assert chart_tab.y_axis_combo.count() == len(columns)

    # Group by combo should have "None" plus all columns
    assert chart_tab.group_by_combo.count() == len(columns) + 1
    assert chart_tab.group_by_combo.itemText(0) == "None"

    # Check that all columns from the data model are in the combos
    for column in columns:
        assert chart_tab.x_axis_combo.findText(column) >= 0
        assert chart_tab.y_axis_combo.findText(column) >= 0
        assert chart_tab.group_by_combo.findText(column) >= 0


def test_create_chart_for_testing(qapp, data_model, mock_chart_service):
    """Test the test-safe chart creation method."""
    chart_tab = ChartTab(data_model, mock_chart_service)

    # Set up combo selections
    chart_tab.chart_type_combo.setCurrentText("Bar Chart")
    chart_tab.x_axis_combo.setCurrentText("Chest Type")
    chart_tab.y_axis_combo.setCurrentText("Value")

    # Use the test-safe method
    chart = chart_tab.create_chart_for_testing()

    # Check that the appropriate chart creation method was called
    mock_chart_service.create_bar_chart.assert_called_once()
    # Check that the parameters passed match what we expect
    kwargs = mock_chart_service.create_bar_chart.call_args.kwargs
    assert kwargs["category_column"] == "Chest Type"
    assert kwargs["value_column"] == "Value"


def test_expected_columns(qapp):
    """Test to understand how ChestDataModel handles columns."""
    # Create a completely new data model
    model = ChestDataModel()

    # Print EXPECTED_COLUMNS
    print(f"EXPECTED_COLUMNS: {ChestDataModel.EXPECTED_COLUMNS}")

    # Create data with all expected columns plus a new one
    data = {
        "Date": ["2023-01-01"],
        "Player Name": ["Player1"],
        "Source/Location": ["Location A"],
        "Chest Type": ["Type A"],
        "Value": [100],
        "Clan": ["Clan1"],
        "Extra Column": ["Extra"],
    }
    df = pd.DataFrame(data)

    # Update the model
    model.update_data(df)

    # Check which columns remain in the model
    result_columns = model.data.columns.tolist()
    print(f"Original columns: {list(data.keys())}")
    print(f"Result columns: {result_columns}")

    # The extra column should be removed due to ChestDataModel's filtering
    assert "Extra Column" not in result_columns
    assert set(result_columns) == set(ChestDataModel.EXPECTED_COLUMNS)


def test_export_chart_for_testing(qapp, data_model, mock_chart_service):
    """Test the test-safe chart export functionality."""
    chart_tab = ChartTab(data_model, mock_chart_service)

    # Set up chart type and create a chart using the test-safe method
    chart_tab.chart_type_combo.setCurrentText("Bar Chart")
    chart_tab.x_axis_combo.setCurrentText("Chest Type")
    chart_tab.y_axis_combo.setCurrentText("Value")

    # Create a chart and store it in _current_chart (simulating what _create_chart would do)
    chart = chart_tab.create_chart_for_testing()
    chart_tab._current_chart = chart

    # Use the test-safe export method
    mock_path = str(Path.home() / "test_chart.png")
    result = chart_tab.export_chart_for_testing(mock_path)

    # Verify that save_chart was called with the correct parameters
    mock_chart_service.save_chart.assert_called()
    args = mock_chart_service.save_chart.call_args.args
    assert args[1] == mock_path
    assert result is True  # Should return True for successful export


def test_update_column_combos(qapp, data_model, chart_service):
    """Test that _update_column_combos correctly updates the combo boxes."""
    # Store original expected columns
    original_expected_columns = ChestDataModel.EXPECTED_COLUMNS.copy()

    try:
        # Add our test column to the EXPECTED_COLUMNS list
        test_column = "Test_Column"
        ChestDataModel.EXPECTED_COLUMNS = original_expected_columns + [test_column]

        # Create a chart tab with the modified data model
        chart_tab = ChartTab(data_model, chart_service)

        # Create new data that includes our test column
        new_data = data_model.data.copy()
        new_data[test_column] = "Test Value"

        # Update the data model
        data_model.update_data(new_data)

        # Verify that the column was added to the combo boxes
        assert chart_tab.x_axis_combo.findText(test_column) >= 0
        assert chart_tab.y_axis_combo.findText(test_column) >= 0
        assert chart_tab.group_by_combo.findText(test_column) >= 0

    finally:
        # Restore original expected columns
        ChestDataModel.EXPECTED_COLUMNS = original_expected_columns
