"""
Tests for the ChartViewAdapter.
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.core.controllers.data_view_controller import DataViewController
from chestbuddy.ui.views.chart_view_adapter import ChartViewAdapter


class TestChartViewAdapter:
    """Tests for the ChartViewAdapter class."""

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
            }
        )
        model.set_data(data)
        return model

    @pytest.fixture
    def chart_service(self, data_model):
        """Create a ChartService instance."""
        return ChartService(data_model)

    @pytest.fixture
    def data_view_controller(self, data_model):
        """Create a DataViewController instance."""
        controller = DataViewController(data_model)
        return controller

    @pytest.fixture
    def chart_view_adapter(self, data_model, chart_service):
        """Create a ChartViewAdapter instance without controller."""
        return ChartViewAdapter(data_model, chart_service)

    @pytest.fixture
    def chart_view_adapter_with_controller(self, data_model, chart_service, data_view_controller):
        """Create a ChartViewAdapter instance with controller."""
        adapter = ChartViewAdapter(data_model, chart_service, data_view_controller)
        return adapter

    def test_initialization(self, chart_view_adapter):
        """Test that ChartViewAdapter initializes correctly."""
        assert chart_view_adapter._data_model is not None
        assert chart_view_adapter._chart_service is not None
        assert chart_view_adapter._data_view_controller is None
        assert chart_view_adapter._chart_tab is not None

    def test_initialization_with_controller(
        self, chart_view_adapter_with_controller, data_view_controller
    ):
        """Test that ChartViewAdapter initializes correctly with controller."""
        assert chart_view_adapter_with_controller._data_view_controller is data_view_controller

    def test_set_data_view_controller(self, chart_view_adapter, data_view_controller):
        """Test setting the data view controller after initialization."""
        # Initially the controller is not set
        assert chart_view_adapter._data_view_controller is None

        # Set the controller
        chart_view_adapter.set_data_view_controller(data_view_controller)

        # Verify the controller is set
        assert chart_view_adapter._data_view_controller is data_view_controller

    def test_chart_creation_with_controller(
        self, chart_view_adapter_with_controller, data_view_controller, qtbot
    ):
        """Test chart creation delegates to controller when available."""
        # Mock the controller's create_chart method
        data_view_controller.create_chart = MagicMock(return_value=True)

        # Create signal catchers
        chart_created = False

        # Connect to signals
        def on_chart_creation_started():
            nonlocal chart_created
            chart_created = True

        chart_view_adapter_with_controller.chart_creation_started.connect(on_chart_creation_started)

        # Trigger chart creation
        with qtbot.waitSignal(
            chart_view_adapter_with_controller.chart_creation_started, timeout=1000
        ):
            chart_view_adapter_with_controller._on_create_chart()

        # Verify the controller method was called
        data_view_controller.create_chart.assert_called_once()
        assert chart_created is True

    def test_chart_creation_without_controller(self, chart_view_adapter, qtbot):
        """Test chart creation uses direct method when controller not available."""
        # Mock the chart tab's _create_chart method
        chart_view_adapter._chart_tab._create_chart = MagicMock()

        # Create signal catchers
        chart_created = False
        chart_type = None

        # Connect to signals
        def on_chart_creation_completed(type_name):
            nonlocal chart_created, chart_type
            chart_created = True
            chart_type = type_name

        chart_view_adapter.chart_creation_completed.connect(on_chart_creation_completed)

        # Trigger chart creation
        with qtbot.waitSignal(chart_view_adapter.chart_creation_completed, timeout=1000):
            chart_view_adapter._on_create_chart()

        # Verify the chart tab method was called
        chart_view_adapter._chart_tab._create_chart.assert_called_once()
        assert chart_created is True

    def test_chart_export_with_controller(
        self, chart_view_adapter_with_controller, data_view_controller, qtbot
    ):
        """Test chart export delegates to controller when available."""
        # Mock the controller's export_chart method
        data_view_controller.export_chart = MagicMock(return_value=True)

        # Create signal catchers
        export_started = False

        # Connect to signals
        def on_export_started():
            nonlocal export_started
            export_started = True

        chart_view_adapter_with_controller.chart_export_started.connect(on_export_started)

        # Trigger export
        with qtbot.waitSignal(
            chart_view_adapter_with_controller.chart_export_started, timeout=1000
        ):
            chart_view_adapter_with_controller._on_export_chart()

        # Verify the controller method was called
        data_view_controller.export_chart.assert_called_once()
        assert export_started is True

    def test_chart_export_without_controller(self, chart_view_adapter, qtbot):
        """Test chart export uses direct method when controller not available."""
        # Mock the chart tab's _export_chart method
        chart_view_adapter._chart_tab._export_chart = MagicMock()

        # Create signal catchers
        export_started = False

        # Connect to signals
        def on_export_started():
            nonlocal export_started
            export_started = True

        chart_view_adapter.chart_export_started.connect(on_export_started)

        # Trigger export
        with qtbot.waitSignal(chart_view_adapter.chart_export_started, timeout=1000):
            chart_view_adapter._on_export_chart()

        # Verify the chart tab method was called
        chart_view_adapter._chart_tab._export_chart.assert_called_once()
        assert export_started is True

    def test_controller_signals(self, chart_view_adapter, data_view_controller, qtbot):
        """Test that the adapter handles controller signals properly."""
        # Set up the controller
        chart_view_adapter.set_data_view_controller(data_view_controller)

        # Create signal catchers
        creation_started = False
        creation_completed = False
        creation_error = False
        error_message = None

        # Connect to adapter signals
        def on_creation_started():
            nonlocal creation_started
            creation_started = True

        def on_creation_completed(chart_type):
            nonlocal creation_completed
            creation_completed = True

        def on_creation_error(message):
            nonlocal creation_error, error_message
            creation_error = True
            error_message = message

        chart_view_adapter.chart_creation_started.connect(on_creation_started)
        chart_view_adapter.chart_creation_completed.connect(on_creation_completed)
        chart_view_adapter.chart_creation_error.connect(on_creation_error)

        # Emit controller signals
        with qtbot.waitSignal(chart_view_adapter.chart_creation_started, timeout=1000):
            data_view_controller.operation_started.emit("chart_creation")

        with qtbot.waitSignal(chart_view_adapter.chart_creation_completed, timeout=1000):
            data_view_controller.operation_completed.emit("chart_creation", "Bar Chart")

        with qtbot.waitSignal(chart_view_adapter.chart_creation_error, timeout=1000):
            data_view_controller.operation_error.emit("chart_creation", "Error creating chart")

        # Verify signals were handled
        assert creation_started is True
        assert creation_completed is True
        assert creation_error is True
        assert error_message == "Error creating chart"

    def test_header_action_clicks(self, chart_view_adapter, qtbot):
        """Test that header action clicks trigger the appropriate methods."""
        # Mock the methods
        chart_view_adapter._on_create_chart = MagicMock()
        chart_view_adapter._on_export_chart = MagicMock()
        chart_view_adapter._chart_tab._update_column_combos = MagicMock()

        # Trigger header action signals
        chart_view_adapter._on_header_action_clicked("create")
        chart_view_adapter._on_header_action_clicked("export")
        chart_view_adapter._on_header_action_clicked("refresh")

        # Verify methods were called
        chart_view_adapter._on_create_chart.assert_called_once()
        chart_view_adapter._on_export_chart.assert_called_once()
        chart_view_adapter._chart_tab._update_column_combos.assert_called_once()
