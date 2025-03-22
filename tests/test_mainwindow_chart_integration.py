"""
Integration tests for MainWindow and ChartTab interaction.

This file contains tests that verify the proper integration between
MainWindow and ChartTab components, including data flow and UI interactions.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import QApplication, QTabWidget, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtCharts import QChart

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.services.csv_service import CSVService
from chestbuddy.ui.main_window import MainWindow
from chestbuddy.ui.chart_tab import ChartTab


@pytest.fixture
def app():
    """Create a QApplication instance for the tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = pd.DataFrame(
        {
            "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
            "Player Name": ["Player1", "Player2", "Player1", "Player3", "Player2"],
            "Source/Location": [
                "Location A",
                "Location B",
                "Location C",
                "Location A",
                "Location B",
            ],
            "Chest Type": ["Type A", "Type B", "Type A", "Type C", "Type B"],
            "Value": [100, 200, 150, 300, 250],
            "Clan": ["Clan1", "Clan2", "Clan1", "Clan3", "Clan2"],
        }
    )
    return data


@pytest.fixture
def data_model():
    """Create a data model for testing."""
    return ChestDataModel()


@pytest.fixture
def csv_service():
    """Create a CSV service for testing."""
    return CSVService()


@pytest.fixture
def chart_service(data_model):
    """Create a chart service for testing."""
    return ChartService(data_model)


@pytest.fixture
def main_window(app, data_model, csv_service, chart_service):
    """Create a main window for testing with all services."""
    validation_service = MagicMock()
    correction_service = MagicMock()

    window = MainWindow(
        data_model, csv_service, validation_service, correction_service, chart_service
    )

    return window


def test_chart_tab_exists_in_main_window(main_window):
    """Test that the chart tab exists in the main window."""
    # Find the tab widget
    tab_widget = None
    for child in main_window.children():
        if isinstance(child, QTabWidget):
            tab_widget = child
            break

    assert tab_widget is not None, "Tab widget not found in MainWindow"

    # Check if there's a tab labeled "Charts"
    chart_tab_index = -1
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == "Charts":
            chart_tab_index = i
            break

    assert chart_tab_index >= 0, "Chart tab not found in TabWidget"

    # Check if the tab contains a ChartTab instance
    chart_tab = tab_widget.widget(chart_tab_index)
    assert isinstance(chart_tab, ChartTab), "Chart tab is not an instance of ChartTab"


def test_data_updates_propagate_to_chart_tab(main_window, sample_data, data_model):
    """Test that data updates in the model propagate to the chart tab."""
    # First, find the chart tab
    tab_widget = None
    for child in main_window.children():
        if isinstance(child, QTabWidget):
            tab_widget = child
            break

    assert tab_widget is not None

    chart_tab_index = -1
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == "Charts":
            chart_tab_index = i
            break

    assert chart_tab_index >= 0
    chart_tab = tab_widget.widget(chart_tab_index)

    # Update the data model
    data_model.update_data(sample_data)

    # Verify column combos have been updated with data columns
    for column in ChestDataModel.EXPECTED_COLUMNS:
        assert chart_tab.x_axis_combo.findText(column) >= 0
        assert chart_tab.y_axis_combo.findText(column) >= 0
        assert chart_tab.group_by_combo.findText(column) >= 0


def test_chart_creation_from_main_window(qtbot, main_window, sample_data, data_model):
    """Test that charts can be created from the main window."""
    # Find the chart tab
    tab_widget = None
    for child in main_window.children():
        if isinstance(child, QTabWidget):
            tab_widget = child
            break

    assert tab_widget is not None

    chart_tab_index = -1
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == "Charts":
            chart_tab_index = i
            break

    assert chart_tab_index >= 0
    chart_tab = tab_widget.widget(chart_tab_index)

    # Update the data model
    data_model.update_data(sample_data)

    # Switch to the chart tab
    tab_widget.setCurrentIndex(chart_tab_index)
    qtbot.wait(100)

    # Set up chart options
    chart_tab.chart_type_combo.setCurrentText("Bar Chart")
    chart_tab.x_axis_combo.setCurrentText("Chest Type")
    chart_tab.y_axis_combo.setCurrentText("Value")

    # Create chart using the button
    qtbot.mouseClick(chart_tab.create_chart_button, Qt.LeftButton)
    qtbot.wait(100)

    # Verify a chart was created
    assert chart_tab._current_chart is not None
    assert isinstance(chart_tab._current_chart, QChart)


def test_tab_switching_preserves_chart_settings(qtbot, main_window, sample_data, data_model):
    """Test that chart settings are preserved when switching tabs."""
    # Find the tab widget
    tab_widget = None
    for child in main_window.children():
        if isinstance(child, QTabWidget):
            tab_widget = child
            break

    assert tab_widget is not None

    # Find the chart tab
    chart_tab_index = -1
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == "Charts":
            chart_tab_index = i
            break

    assert chart_tab_index >= 0
    chart_tab = tab_widget.widget(chart_tab_index)

    # Update the data model
    data_model.update_data(sample_data)

    # Switch to the chart tab
    tab_widget.setCurrentIndex(chart_tab_index)
    qtbot.wait(100)

    # Configure chart options
    chart_tab.chart_type_combo.setCurrentText("Pie Chart")
    chart_tab.x_axis_combo.setCurrentText("Player Name")
    chart_tab.y_axis_combo.setCurrentText("Value")

    # Switch to another tab and back
    tab_widget.setCurrentIndex(0)  # Switch to first tab
    qtbot.wait(100)
    tab_widget.setCurrentIndex(chart_tab_index)  # Switch back to chart tab
    qtbot.wait(100)

    # Verify settings were preserved
    assert chart_tab.chart_type_combo.currentText() == "Pie Chart"
    assert chart_tab.x_axis_combo.currentText() == "Player Name"
    assert chart_tab.y_axis_combo.currentText() == "Value"


def test_chart_export_from_main_window(qtbot, main_window, sample_data, data_model, tmpdir):
    """Test that charts can be exported from the main window."""
    # Find the chart tab
    tab_widget = None
    for child in main_window.children():
        if isinstance(child, QTabWidget):
            tab_widget = child
            break

    assert tab_widget is not None

    chart_tab_index = -1
    for i in range(tab_widget.count()):
        if tab_widget.tabText(i) == "Charts":
            chart_tab_index = i
            break

    assert chart_tab_index >= 0
    chart_tab = tab_widget.widget(chart_tab_index)

    # Update the data model
    data_model.update_data(sample_data)

    # Switch to the chart tab
    tab_widget.setCurrentIndex(chart_tab_index)
    qtbot.wait(100)

    # Set up chart options and create a chart
    chart_tab.chart_type_combo.setCurrentText("Bar Chart")
    chart_tab.x_axis_combo.setCurrentText("Chest Type")
    chart_tab.y_axis_combo.setCurrentText("Value")

    # Create chart
    qtbot.mouseClick(chart_tab.create_chart_button, Qt.LeftButton)
    qtbot.wait(100)

    # Create a temporary file path for testing
    temp_file = str(tmpdir.join("test_chart.png"))

    # Mock the file dialog to return our temp file
    with patch(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        return_value=(temp_file, "PNG Files (*.png)"),
    ):
        # Click export button
        qtbot.mouseClick(chart_tab.export_button, Qt.LeftButton)
        qtbot.wait(100)

        # Verify file exists
        assert Path(temp_file).exists()
        assert Path(temp_file).stat().st_size > 0
