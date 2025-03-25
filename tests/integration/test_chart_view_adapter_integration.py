"""
Integration tests for the ChartViewAdapter with DataViewController.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtCharts import QChart

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.views.chart_view_adapter import ChartViewAdapter


class TestChartViewAdapterIntegration:
    """Integration tests for the ChartViewAdapter with DataViewController."""

    @pytest.fixture
    def data_model(self):
        """Create a data model with test data."""
        model = ChestDataModel()
        data = pd.DataFrame(
            {
                "DATE": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "PLAYER": ["Player1", "Player2", "Player3"],
                "CHEST": ["Gold", "Silver", "Bronze"],
                "SCORE": [100, 75, 50],
                "CLAN": ["Alpha", "Beta", "Gamma"],
            }
        )
        model.set_data(data)
        return model

    @pytest.fixture
    def chart_service(self, data_model):
        """Create a ChartService instance."""
        service = ChartService(data_model)
        # Mock chart creation methods to avoid QChart initialization issues in tests
        service.create_bar_chart = MagicMock(return_value=QChart())
        service.create_pie_chart = MagicMock(return_value=QChart())
        service.create_line_chart = MagicMock(return_value=QChart())
        return service

    @pytest.fixture
    def data_view_controller(self, data_model):
        """Create a DataViewController instance."""
        controller = DataViewController(data_model)
        return controller

    @pytest.fixture
    def chart_view_adapter(self, data_model, chart_service, data_view_controller):
        """Create a ChartViewAdapter instance with controller."""
        adapter = ChartViewAdapter(data_model, chart_service)
        adapter.set_data_view_controller(data_view_controller)

        # Mock chart tab's chart view to avoid QWidget issues in tests
        adapter._chart_tab.chart_view.setChart = MagicMock()

        return adapter

    def test_end_to_end_chart_creation(
        self, chart_view_adapter, data_view_controller, chart_service, qtbot
    ):
        """Test end-to-end chart creation flow with controller."""
        # Create signal catchers
        creation_started = False
        creation_completed = False
        chart_type_result = None

        # Connect to signals
        def on_creation_started():
            nonlocal creation_started
            creation_started = True

        def on_creation_completed(chart_type):
            nonlocal creation_completed, chart_type_result
            creation_completed = True
            chart_type_result = chart_type

        chart_view_adapter.chart_creation_started.connect(on_creation_started)
        chart_view_adapter.chart_creation_completed.connect(on_creation_completed)

        # Set up chart tab UI with values
        chart_view_adapter._chart_tab.chart_type_combo.setCurrentText("Bar Chart")
        chart_view_adapter._chart_tab.x_axis_combo.setCurrentText("PLAYER")
        chart_view_adapter._chart_tab.y_axis_combo.setCurrentText("SCORE")
        chart_view_adapter._chart_tab.chart_title_input.setCurrentText("Test Chart")

        # Mock the controller's create_chart to directly call operation_completed
        def mock_create_chart(*args, **kwargs):
            # Create chart and emit completion signal
            data_view_controller.operation_completed.emit(
                "chart_creation", kwargs.get("chart_type", "Bar Chart")
            )
            return True

        data_view_controller.create_chart = MagicMock(side_effect=mock_create_chart)

        # Trigger chart creation
        with qtbot.waitSignals(
            [
                chart_view_adapter.chart_creation_started,
                chart_view_adapter.chart_creation_completed,
            ],
            timeout=1000,
        ):
            chart_view_adapter._on_create_chart()

        # Verify signals were emitted
        assert creation_started is True
        assert creation_completed is True
        assert chart_type_result == "Bar Chart"

        # Verify controller method was called with correct parameters
        data_view_controller.create_chart.assert_called_once()
        call_args = data_view_controller.create_chart.call_args[1]
        assert call_args["chart_type"] == "Bar Chart"
        assert call_args["x_column"] == "PLAYER"
        assert call_args["y_column"] == "SCORE"
        assert call_args["title"] == "Test Chart"

    def test_end_to_end_chart_export(self, chart_view_adapter, data_view_controller, qtbot):
        """Test end-to-end chart export flow with controller."""
        # Create signal catchers
        export_started = False
        export_completed = False
        export_path = None

        # Connect to signals
        def on_export_started():
            nonlocal export_started
            export_started = True

        def on_export_completed(path):
            nonlocal export_completed, export_path
            export_completed = True
            export_path = path

        chart_view_adapter.chart_export_started.connect(on_export_started)
        chart_view_adapter.chart_export_completed.connect(on_export_completed)

        # Mock the controller's export_chart to directly call operation_completed
        def mock_export_chart():
            # Emit completion signal
            data_view_controller.operation_completed.emit("chart_export", "/path/to/chart.png")
            return True

        data_view_controller.export_chart = MagicMock(side_effect=mock_export_chart)

        # Trigger chart export
        with qtbot.waitSignals(
            [chart_view_adapter.chart_export_started, chart_view_adapter.chart_export_completed],
            timeout=1000,
        ):
            chart_view_adapter._on_export_chart()

        # Verify signals were emitted
        assert export_started is True
        assert export_completed is True
        assert export_path == "/path/to/chart.png"

        # Verify controller method was called
        data_view_controller.export_chart.assert_called_once()

    def test_integration_with_error_handling(self, chart_view_adapter, data_view_controller, qtbot):
        """Test integration with error handling."""
        # Create signal catchers
        error_received = False
        error_message = None

        # Connect to signals
        def on_error(message):
            nonlocal error_received, error_message
            error_received = True
            error_message = message

        chart_view_adapter.chart_creation_error.connect(on_error)

        # Mock the controller's create_chart to directly call operation_error
        def mock_create_chart_error(*args, **kwargs):
            # Emit error signal
            data_view_controller.operation_error.emit("Error creating chart: Invalid column")
            return False

        data_view_controller.create_chart = MagicMock(side_effect=mock_create_chart_error)

        # Trigger chart creation
        with qtbot.waitSignals(
            [chart_view_adapter.chart_creation_started, chart_view_adapter.chart_creation_error],
            timeout=1000,
        ):
            chart_view_adapter._on_create_chart()

        # Verify error signal was emitted
        assert error_received is True
        assert error_message == "Error creating chart: Invalid column"

    def test_header_actions_integration(self, chart_view_adapter, data_view_controller, qtbot):
        """Test header actions integration with controller."""
        # Mock methods
        data_view_controller.create_chart = MagicMock(return_value=True)
        data_view_controller.export_chart = MagicMock(return_value=True)
        chart_view_adapter._chart_tab._update_column_combos = MagicMock()

        # Trigger header actions
        chart_view_adapter._on_header_action_clicked("create")
        chart_view_adapter._on_header_action_clicked("export")
        chart_view_adapter._on_header_action_clicked("refresh")

        # Verify methods were called
        data_view_controller.create_chart.assert_called_once()
        data_view_controller.export_chart.assert_called_once()
        chart_view_adapter._chart_tab._update_column_combos.assert_called_once()
