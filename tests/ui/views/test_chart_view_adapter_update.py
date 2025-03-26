"""
Tests for ChartViewAdapter integration with UpdateManager.
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
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import ServiceLocator, get_update_manager
from chestbuddy.ui.utils.update_manager import UpdateManager


@pytest.fixture
def app(qtbot):
    """Create a QApplication for testing."""
    # qtbot fixture will ensure QApplication exists
    return QApplication.instance()


@pytest.fixture
def data_model():
    """Create a data model with test data."""
    model = ChestDataModel()
    data = pd.DataFrame(
        {
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "PLAYER": ["Player1", "Player2", "Player3"],
            "SOURCE": ["Source1", "Source2", "Source3"],
            "CHEST": ["Gold", "Silver", "Bronze"],
            "SCORE": [100, 75, 50],
            "CLAN": ["Clan1", "Clan2", "Clan3"],
        }
    )
    model.update_data(data)
    return model


@pytest.fixture
def chart_service(data_model):
    """Create a ChartService instance."""
    return ChartService(data_model)


@pytest.fixture
def data_view_controller(data_model):
    """Create a DataViewController instance."""
    controller = DataViewController(data_model)
    return controller


@pytest.fixture
def update_manager():
    """Create and register an UpdateManager instance."""
    manager = UpdateManager()
    ServiceLocator.register("update_manager", manager)
    return manager


@pytest.fixture
def chart_view_adapter(app, data_model, chart_service, update_manager):
    """Create a ChartViewAdapter instance."""
    adapter = ChartViewAdapter(data_model, chart_service)

    # Mock chart tab's chart view to avoid QWidget issues in tests
    if hasattr(adapter._chart_tab, "chart_view") and hasattr(
        adapter._chart_tab.chart_view, "setChart"
    ):
        adapter._chart_tab.chart_view.setChart = MagicMock()

    return adapter


class TestChartViewAdapterUpdate:
    """Tests for ChartViewAdapter integration with UpdateManager."""

    def test_implements_iupdatable(self, app, chart_view_adapter):
        """Test that ChartViewAdapter implements the IUpdatable interface."""
        assert isinstance(chart_view_adapter, IUpdatable)

    def test_update_view_content_method(self, app, chart_view_adapter):
        """Test that _update_view_content method updates the view."""
        # Spy on the internal _on_create_chart method
        chart_view_adapter._on_create_chart = MagicMock()
        chart_view_adapter._chart_tab._update_column_combos = MagicMock()

        # Call the method
        chart_view_adapter._update_view_content()

        # Verify the chart tab was updated
        chart_view_adapter._chart_tab._update_column_combos.assert_called_once()

    def test_refresh_method_uses_update_manager(self, app, chart_view_adapter, update_manager):
        """Test that refresh method uses UpdateManager to schedule an update."""
        # Spy on schedule_update
        chart_view_adapter.schedule_update = MagicMock()

        # Call refresh
        chart_view_adapter.refresh()

        # Verify schedule_update was called
        chart_view_adapter.schedule_update.assert_called_once()

    def test_needs_update_method(self, app, chart_view_adapter, monkeypatch):
        """Test that needs_update correctly detects chart parameter changes."""
        # Set up a mocked _current_chart property
        monkeypatch.setattr(chart_view_adapter._chart_tab, "_current_chart", {})

        # Initialize state
        chart_view_adapter._update_chart_state()

        # Change chart parameters
        chart_view_adapter._chart_tab.chart_type_combo.setCurrentText("Pie Chart")

        # Now the view should need update
        assert chart_view_adapter.needs_update()

    def test_populate_view_content_method(self, app, chart_view_adapter):
        """Test that _populate_view_content method populates the view."""
        # Spy on the internal methods
        chart_view_adapter._chart_tab._update_column_combos = MagicMock()
        chart_view_adapter._on_create_chart = MagicMock()

        # Call the method
        chart_view_adapter._populate_view_content()

        # Verify the methods were called
        chart_view_adapter._chart_tab._update_column_combos.assert_called_once()

    def test_reset_view_content_method(self, app, chart_view_adapter, monkeypatch):
        """Test that _reset_view_content method resets the view."""
        # Mock the _clear_chart method if it exists
        if hasattr(chart_view_adapter._chart_tab, "_clear_chart"):
            chart_view_adapter._chart_tab._clear_chart = MagicMock()

            # Call the method
            chart_view_adapter._reset_view_content()

            # Verify the method was called
            chart_view_adapter._chart_tab._clear_chart.assert_called_once()
        else:
            # If _clear_chart doesn't exist, test that _current_chart is set to None
            monkeypatch.setattr(chart_view_adapter._chart_tab, "_current_chart", {})

            # Call the method
            chart_view_adapter._reset_view_content()

            # Verify _current_chart was set to None
            assert chart_view_adapter._chart_tab._current_chart is None

    def test_create_chart_updates_state(self, app, chart_view_adapter):
        """Test that creating a chart updates the chart state."""
        # Spy on the internal methods
        chart_view_adapter._update_chart_state = MagicMock()
        chart_view_adapter._chart_tab._create_chart = MagicMock()

        # Call the method
        chart_view_adapter._on_create_chart()

        # Verify state was updated
        chart_view_adapter._update_chart_state.assert_called_once()
