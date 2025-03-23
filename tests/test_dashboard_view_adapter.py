"""
test_dashboard_view_adapter.py

Contains tests for the DashboardViewAdapter component.
"""

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtCharts import QChart

# Import the adapter we'll be creating
from chestbuddy.ui.views.dashboard_view_adapter import DashboardViewAdapter
from chestbuddy.ui.views.dashboard_view import DashboardView
from chestbuddy.ui.views.base_view import BaseView


class SignalCatcher:
    """Helper class to catch Qt signals."""

    def __init__(self):
        self.signal_received = False
        self.signal_args = None
        self.signal_count = 0

    def handler(self, *args):
        self.signal_received = True
        self.signal_args = args
        self.signal_count += 1


@pytest.fixture
def app():
    """Create a QApplication instance."""
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def mock_chart():
    """Create a mock chart for testing."""
    return QChart()


@pytest.fixture
def mock_data_model():
    """Create a mock data model."""
    model = MagicMock()
    model.get_row_count = MagicMock(return_value=1000)
    return model


class TestDashboardViewAdapter:
    def test_initialization(self, qtbot, app, mock_data_model):
        """Test the basic initialization of the dashboard view adapter."""
        # Create the adapter with a mock data model
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Verify it inherits from BaseView
        assert isinstance(adapter, BaseView)

        # Verify title and data_required property
        assert adapter.title() == "Dashboard"
        assert adapter.data_required() is False  # Dashboard should be accessible without data

        # Verify it contains a DashboardView
        assert adapter._dashboard_view is not None
        assert isinstance(adapter._dashboard_view, DashboardView)

    def test_data_requested_signal(self, qtbot, app, mock_data_model):
        """Test that data_requested signal is forwarded when empty state action is clicked."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Set up signal catcher
        signal_catcher = SignalCatcher()
        adapter.data_requested.connect(signal_catcher.handler)

        # Trigger the import action from the dashboard view
        adapter._dashboard_view.action_triggered.emit("import")

        # Verify signal was forwarded
        assert signal_catcher.signal_received

    def test_action_forwarding(self, qtbot, app, mock_data_model):
        """Test that actions from dashboard are forwarded."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Set up signal catcher for various actions
        actions_signal = SignalCatcher()
        adapter.action_triggered.connect(actions_signal.handler)

        chart_signal = SignalCatcher()
        adapter.chart_selected.connect(chart_signal.handler)

        file_signal = SignalCatcher()
        adapter.file_selected.connect(file_signal.handler)

        # Trigger different actions
        adapter._dashboard_view.action_triggered.emit("analyze")
        assert actions_signal.signal_received
        assert actions_signal.signal_args[0] == "analyze"

        adapter._dashboard_view.chart_clicked.emit("top_players")
        assert chart_signal.signal_received
        assert chart_signal.signal_args[0] == "top_players"

        adapter._dashboard_view.file_selected.emit("file1.csv")
        assert file_signal.signal_received
        assert file_signal.signal_args[0] == "file1.csv"

    def test_update_stats(self, qtbot, app, mock_data_model):
        """Test updating stats via the adapter."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Update stats through adapter
        adapter.update_stats(
            dataset_rows=1000, validation_status="Valid", corrections=50, last_import="2023-10-18"
        )

        # Verify stats were passed to view
        dashboard = adapter._dashboard_view
        assert dashboard._dataset_card.value() == "1,000 rows"
        assert dashboard._validation_card.value() == "Valid"
        assert dashboard._correction_card.value() == "50 corrected"
        assert dashboard._import_card.value() == "2023-10-18"

    def test_set_recent_files(self, qtbot, app, mock_data_model):
        """Test setting recent files via the adapter."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Set recent files
        files = ["file1.csv", "file2.csv", "file3.csv"]
        adapter.set_recent_files(files)

        # Verify files were passed to view
        dashboard = adapter._dashboard_view
        assert len(dashboard._recent_files._file_items) == 3

    def test_set_data_available(self, qtbot, app, mock_data_model):
        """Test setting data availability via the adapter."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Initially should be in empty state
        dashboard = adapter._dashboard_view
        assert dashboard._content_stack.currentWidget() == dashboard._empty_state

        # Set data available
        adapter.set_data_available(True)

        # Verify dashboard was updated
        assert dashboard._data_available is True
        assert dashboard._content_stack.currentWidget() == dashboard._dash_content

        # Set data not available
        adapter.set_data_available(False)

        # Verify dashboard was updated
        assert dashboard._data_available is False
        assert dashboard._content_stack.currentWidget() == dashboard._empty_state

    @patch("chestbuddy.ui.views.dashboard_view_adapter.ChartService")
    def test_update_charts(self, mock_chart_service, qtbot, app, mock_data_model, mock_chart):
        """Test updating charts via the adapter with chart service."""
        # Configure mock chart service
        mock_chart_service_instance = MagicMock()
        mock_chart_service_instance.create_player_distribution_chart.return_value = mock_chart
        mock_chart_service_instance.create_chest_sources_chart.return_value = mock_chart
        mock_chart_service.return_value = mock_chart_service_instance

        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Update charts
        adapter.update_charts()

        # Verify chart service was called
        mock_chart_service_instance.create_player_distribution_chart.assert_called_once()
        mock_chart_service_instance.create_chest_sources_chart.assert_called_once()

        # Verify charts were updated in the dashboard
        dashboard = adapter._dashboard_view
        assert dashboard._top_players_chart.chart() is not None
        assert dashboard._chest_sources_chart.chart() is not None

    def test_on_data_updated(self, qtbot, app, mock_data_model):
        """Test the on_data_updated method."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Mock necessary methods
        adapter.update_stats = MagicMock()
        adapter.update_charts = MagicMock()
        adapter.set_data_available = MagicMock()

        # Call on_data_updated
        adapter.on_data_updated()

        # Verify methods were called
        adapter.update_stats.assert_called_once()
        adapter.update_charts.assert_called_once()
        adapter.set_data_available.assert_called_once_with(True)

    def test_on_data_cleared(self, qtbot, app, mock_data_model):
        """Test the on_data_cleared method."""
        adapter = DashboardViewAdapter(mock_data_model)
        qtbot.addWidget(adapter)

        # Mock necessary methods
        adapter.set_data_available = MagicMock()

        # Call on_data_cleared
        adapter.on_data_cleared()

        # Verify methods were called
        adapter.set_data_available.assert_called_once_with(False)
