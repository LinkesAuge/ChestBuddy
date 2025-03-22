"""
Tests for the ChartTab UI component.

This module contains tests for the ChartTab class, which is responsible for
displaying charts in the application.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import pytest
from PySide6.QtCore import QObject, Signal, Qt, QPoint
from PySide6.QtWidgets import QApplication, QComboBox, QPushButton, QMessageBox, QFileDialog
from PySide6.QtCharts import QChartView
from unittest import mock
from unittest.mock import MagicMock, patch, ANY
from pytestqt.qtbot import QtBot

from chestbuddy.core.models.chest_data_model import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.ui.chart_tab import ChartTab


class SignalCatcher(QObject):
    """Utility class to catch Qt signals."""

    def __init__(self):
        super().__init__()
        self.signal_received = False
        self.signal_count = 0
        self.signal_args = None

    def signal_handler(self, *args):
        """Handle signal emission."""
        self.signal_received = True
        self.signal_count += 1
        self.signal_args = args


@pytest.fixture
def app():
    """Create a QApplication instance."""
    # Check if there's already a QApplication instance
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
        "Player Name": ["Player1", "Player2", "Player3", "Player4", "Player5"],
        "Source/Location": ["Location A", "Location B", "Location A", "Location C", "Location B"],
        "Chest Type": ["Type A", "Type B", "Type A", "Type C", "Type B"],
        "Value": [100, 200, 300, 150, 250],
        "Clan": ["Clan1", "Clan2", "Clan1", "Clan3", "Clan2"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def data_model(app, sample_data):
    """Create a data model with sample data."""
    model = ChestDataModel()
    model.update_data(sample_data)
    return model


@pytest.fixture
def chart_service(data_model):
    """Create a ChartService instance."""
    return ChartService(data_model)


@pytest.fixture
def mock_chart_service():
    """Create a mocked ChartService."""
    mock_service = MagicMock(spec=ChartService)
    mock_service.create_bar_chart.return_value = MagicMock()
    mock_service.create_pie_chart.return_value = MagicMock()
    mock_service.create_line_chart.return_value = MagicMock()
    mock_service.save_chart.return_value = True
    return mock_service


class TestChartTab:
    """Tests for the ChartTab UI component."""

    def test_initialization(self, app, data_model, chart_service):
        """Test that the ChartTab initializes correctly."""
        chart_tab = ChartTab(data_model, chart_service)

        # Check that components are initialized
        assert chart_tab is not None
        assert chart_tab.chart_service == chart_service
        assert chart_tab.data_model == data_model

        # Verify UI components exist
        assert hasattr(chart_tab, "chart_type_combo")
        assert hasattr(chart_tab, "chart_view")
        assert hasattr(chart_tab, "export_button")

    def test_chart_type_selection(self, qtbot, app, data_model, mock_chart_service):
        """Test that chart type selection creates the correct chart type."""
        chart_tab = ChartTab(data_model, mock_chart_service)
        qtbot.addWidget(chart_tab)
        qtbot.wait(100)  # Wait for widget to initialize

        # Mock the _create_chart method to avoid direct chart creation
        with patch.object(chart_tab, "_create_chart"):
            # Select chart types
            if chart_tab.chart_type_combo.findText("Bar Chart") >= 0:
                chart_tab.chart_type_combo.setCurrentText("Bar Chart")
                # Manually call the handler
                chart_tab._on_chart_type_changed("Bar Chart")
                # Check that the chart type is correctly set in the UI
                assert chart_tab.chart_type_combo.currentText() == "Bar Chart"
                qtbot.wait(50)

            if chart_tab.chart_type_combo.findText("Pie Chart") >= 0:
                chart_tab.chart_type_combo.setCurrentText("Pie Chart")
                chart_tab._on_chart_type_changed("Pie Chart")
                assert chart_tab.chart_type_combo.currentText() == "Pie Chart"
                qtbot.wait(50)

            if chart_tab.chart_type_combo.findText("Line Chart") >= 0:
                chart_tab.chart_type_combo.setCurrentText("Line Chart")
                chart_tab._on_chart_type_changed("Line Chart")
                assert chart_tab.chart_type_combo.currentText() == "Line Chart"
                # For line charts, verify group_by combo is enabled
                assert chart_tab.group_by_combo.isEnabled() == True
                qtbot.wait(50)

    def test_data_update_refreshes_chart(self, qtbot, app, data_model, mock_chart_service):
        """Test that updating data refreshes the chart."""
        chart_tab = ChartTab(data_model, mock_chart_service)
        qtbot.addWidget(chart_tab)
        qtbot.wait(100)  # Wait for widget to initialize

        # Set up our mocks to avoid UI operations
        mock_create_chart = MagicMock()
        original_create_chart = chart_tab._create_chart
        chart_tab._create_chart = mock_create_chart

        try:
            # Populate initial test data to ensure combos have items
            test_data = pd.DataFrame(
                {
                    "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                    "Player Name": ["Player1", "Player2", "Player3"],
                    "Source/Location": ["Location1", "Location2", "Location3"],
                    "Chest Type": ["Type1", "Type2", "Type3"],
                    "Value": [100, 200, 300],
                    "Clan": ["Clan1", "Clan2", "Clan3"],
                }
            )
            data_model.update_data(test_data)

            # Set a chart as current to ensure it's updated
            chart_tab._current_chart = MagicMock()

            # Reset call count to start fresh
            mock_create_chart.reset_mock()

            # Update the data model with new data to trigger _on_data_changed
            new_data = pd.DataFrame(
                {
                    "Date": ["2023-01-01", "2023-01-02"],
                    "Player Name": ["Player A", "Player B"],
                    "Source/Location": ["Location A", "Location B"],
                    "Chest Type": ["Type A", "Type B"],
                    "Value": [150, 250],
                    "Clan": ["Clan A", "Clan B"],
                }
            )
            data_model.update_data(new_data)
            qtbot.wait(100)  # Wait for signals to propagate

            # Verify that _create_chart was called after the data update
            mock_create_chart.assert_called()
        finally:
            # Restore original method
            chart_tab._create_chart = original_create_chart

    def test_export_button(self, qtbot, app, data_model, mock_chart_service, tmpdir):
        """Test the export button functionality."""
        chart_tab = ChartTab(data_model, mock_chart_service)
        qtbot.addWidget(chart_tab)
        qtbot.wait(100)  # Wait for widget to initialize

        # Create a temporary file path for testing
        temp_file = str(tmpdir.join("test_chart.png"))

        # Set up a chart to export using the test-safe method
        with patch.object(chart_tab, "_update_column_combos"):  # Avoid UI updates
            # Create a mock chart
            mock_chart = MagicMock()
            chart_tab._current_chart = mock_chart

            # Mock the file dialog to return the temp file
            with patch(
                "PySide6.QtWidgets.QFileDialog.getSaveFileName",
                return_value=(temp_file, "PNG Files (*.png)"),
            ):
                # Directly call the export method
                chart_tab._export_chart()
                qtbot.wait(100)  # Wait for operation to complete

            # Check if chart service save_chart was called with the correct arguments
            mock_chart_service.save_chart.assert_called_once()

    def test_column_selection(self, qtbot, app, data_model, mock_chart_service):
        """Test that column selection controls work correctly."""
        # Create the chart tab
        chart_tab = ChartTab(data_model, mock_chart_service)
        qtbot.addWidget(chart_tab)
        qtbot.wait(100)  # Wait for widget to initialize

        # Set up the mock for _create_chart
        mock_create_chart = MagicMock()
        original_create_chart = chart_tab._create_chart
        chart_tab._create_chart = mock_create_chart

        try:
            # Set test data in the model to ensure combos have items
            test_data = pd.DataFrame(
                {
                    "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                    "Player Name": ["Player1", "Player2", "Player3"],
                    "Source/Location": ["Location1", "Location2", "Location3"],
                    "Chest Type": ["Type1", "Type2", "Type3"],
                    "Value": [100, 200, 300],
                    "Clan": ["Clan1", "Clan2", "Clan3"],
                }
            )
            data_model.update_data(test_data)

            # Update combo boxes manually
            chart_tab._update_column_combos()
            qtbot.wait(100)

            # Set values through direct property access instead of UI interaction
            if chart_tab.x_axis_combo.count() > 0:
                chart_tab.x_axis_combo.setCurrentIndex(0)

            if chart_tab.y_axis_combo.count() > 0:
                chart_tab.y_axis_combo.setCurrentIndex(0)

            # Set chart type and trigger the change handler
            chart_tab.chart_type_combo.setCurrentText("Bar Chart")
            chart_tab._on_chart_type_changed("Bar Chart")
            qtbot.wait(100)

            # Get the selected columns
            x_column = chart_tab.x_axis_combo.currentText()
            y_column = chart_tab.y_axis_combo.currentText()

            # Verify x and y columns were set
            assert x_column != ""
            assert y_column != ""

            # Verify the handler was called by checking if _create_chart was called
            mock_create_chart.assert_called_once()
        finally:
            # Restore original method
            chart_tab._create_chart = original_create_chart

    def test_ui_layout(self, app, data_model, chart_service):
        """Test that the UI layout contains the expected components."""
        chart_tab = ChartTab(data_model, chart_service)

        # Check for basic UI components
        assert any(isinstance(w, QComboBox) for w in chart_tab.findChildren(QComboBox))
        assert any(isinstance(w, QChartView) for w in chart_tab.findChildren(QChartView))
        assert any(
            isinstance(w, QPushButton) and w.text() == "Export"
            for w in chart_tab.findChildren(QPushButton)
        )
