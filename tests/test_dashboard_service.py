import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from PySide6.QtCore import QObject, Signal

# Import the service once it's created
# from chestbuddy.core.services.dashboard_service import DashboardService
# from chestbuddy.core.models.dataframe_store import DataFrameStore


class TestDashboardService:
    """Test suite for the DashboardService."""

    @pytest.fixture
    def mock_dataframe_store(self):
        """Fixture providing a mock DataFrameStore."""
        mock_store = MagicMock()
        # Create a sample DataFrame for testing
        mock_store.get_dataframe.return_value = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "Player Name": ["Player1", "Player2", "Player1"],
                "Chest Type": ["Gold", "Silver", "Bronze"],
                "Value": [100, 50, 25],
                "Source/Location": ["Dungeon", "Quest", "Battle"],
            }
        )
        mock_store.has_data.return_value = True
        return mock_store

    @pytest.fixture
    def mock_config_manager(self):
        """Fixture providing a mock ConfigManager."""
        mock_config = MagicMock()
        mock_config.get_value.return_value = {}
        return mock_config

    @pytest.fixture
    def mock_file_service(self):
        """Fixture providing a mock FileService."""
        mock_service = MagicMock()
        mock_service.get_recent_files.return_value = [
            {"path": "file1.csv", "date": "2023-01-01", "size": 1024, "rows": 100},
            {"path": "file2.csv", "date": "2023-01-02", "size": 2048, "rows": 200},
        ]
        return mock_service

    @pytest.fixture
    def mock_chart_service(self):
        """Fixture providing a mock ChartService."""
        mock_service = MagicMock()
        return mock_service

    @pytest.fixture
    def dashboard_service(
        self, mock_dataframe_store, mock_config_manager, mock_file_service, mock_chart_service
    ):
        """Fixture providing a DashboardService instance with mock dependencies."""
        with patch(
            "chestbuddy.core.services.dashboard_service.DataFrameStore",
            return_value=mock_dataframe_store,
        ):
            with patch(
                "chestbuddy.core.services.dashboard_service.ConfigManager",
                return_value=mock_config_manager,
            ):
                with patch(
                    "chestbuddy.core.services.dashboard_service.FileService",
                    return_value=mock_file_service,
                ):
                    with patch(
                        "chestbuddy.core.services.dashboard_service.ChartService",
                        return_value=mock_chart_service,
                    ):
                        from chestbuddy.core.services.dashboard_service import DashboardService

                        service = DashboardService()
                        return service

    def test_initialization(
        self,
        dashboard_service,
        mock_dataframe_store,
        mock_config_manager,
        mock_file_service,
        mock_chart_service,
    ):
        """Test service initialization connects to required dependencies."""
        assert dashboard_service._dataframe_store == mock_dataframe_store
        assert dashboard_service._config_manager == mock_config_manager
        assert dashboard_service._file_service == mock_file_service
        assert dashboard_service._chart_service == mock_chart_service

    def test_get_statistics(self, dashboard_service):
        """Test retrieving dashboard statistics."""
        stats = dashboard_service.get_statistics()

        # Verify expected statistics are returned
        assert isinstance(stats, dict)
        assert "total_records" in stats
        assert "total_value" in stats
        assert "unique_players" in stats
        assert "unique_chests" in stats
        assert "unique_sources" in stats

        # Verify values based on our mock data
        assert stats["total_records"] == 3
        assert stats["total_value"] == 175
        assert stats["unique_players"] == 2
        assert stats["unique_chests"] == 3
        assert stats["unique_sources"] == 3

    def test_get_recent_files(self, dashboard_service):
        """Test retrieving recent files information."""
        files = dashboard_service.get_recent_files(max_files=5)

        assert isinstance(files, list)
        assert len(files) == 2
        assert "path" in files[0]
        assert "date" in files[0]
        assert "size" in files[0]
        assert "rows" in files[0]

    def test_get_chart_preview(self, dashboard_service, mock_chart_service):
        """Test retrieving chart previews."""
        dashboard_service.get_chart_preview("chest_distribution")

        # Verify chart service was called
        mock_chart_service.create_chart.assert_called_once()
        args, kwargs = mock_chart_service.create_chart.call_args
        assert "chest_distribution" in args or kwargs.values()

    def test_get_action_cards(self, dashboard_service):
        """Test retrieving action card configurations."""
        actions = dashboard_service.get_action_cards()

        assert isinstance(actions, list)
        assert len(actions) > 0

        # Check action card structure
        for action in actions:
            assert "title" in action
            assert "description" in action
            assert "icon" in action
            assert "action" in action

    def test_statistics_update_on_data_change(self, dashboard_service, mock_dataframe_store):
        """Test that statistics update when data changes."""
        # Setup signal listener
        signal_received = False

        def on_statistics_updated():
            nonlocal signal_received
            signal_received = True

        dashboard_service.statistics_updated.connect(on_statistics_updated)

        # Trigger data change
        mock_dataframe_store.data_changed.emit()

        # Check signal was emitted
        assert signal_received

        # Verify statistics were recalculated
        dashboard_service.get_statistics.assert_called_once()

    def test_no_data_statistics(self, dashboard_service, mock_dataframe_store):
        """Test statistics when no data is available."""
        # Set the mock to indicate no data
        mock_dataframe_store.has_data.return_value = False
        mock_dataframe_store.get_dataframe.return_value = pd.DataFrame()

        stats = dashboard_service.get_statistics()

        # Verify empty/zero statistics
        assert stats["total_records"] == 0
        assert stats["total_value"] == 0
        assert stats["unique_players"] == 0
        assert stats["unique_chests"] == 0
        assert stats["unique_sources"] == 0

    def test_get_trend_data(self, dashboard_service):
        """Test retrieving trend data for stats."""
        trends = dashboard_service.get_trend_data()

        assert isinstance(trends, dict)
        # Verify trend information is provided for key metrics
        assert "total_records" in trends
        assert "total_value" in trends

        # Check trend structure
        for metric, trend in trends.items():
            assert "direction" in trend  # 'up', 'down', or 'neutral'
            assert "percentage" in trend  # percentage change
