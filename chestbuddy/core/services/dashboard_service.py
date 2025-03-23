"""
dashboard_service.py

Description: Service for providing dashboard data and functionality
Usage:
    dashboard_service = DashboardService()
    stats = dashboard_service.get_statistics()
    charts = dashboard_service.get_chart_preview('chest_distribution')
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
from PySide6.QtCore import QObject, Signal

from chestbuddy.core.models.dataframe_store import DataFrameStore
from chestbuddy.core.services.config_manager import ConfigManager
from chestbuddy.core.services.file_service import FileService
from chestbuddy.core.services.chart_service import ChartService


class DashboardService(QObject):
    """
    Service for providing dashboard data and functionality.

    This service calculates statistics, provides chart data, tracks
    frequently used actions, and monitors data changes to update
    the dashboard.

    Signals:
        statistics_updated: Emitted when statistics are recalculated
        charts_updated: Emitted when chart data is updated
        actions_updated: Emitted when action cards are updated
    """

    # Signals
    statistics_updated = Signal()
    charts_updated = Signal()
    actions_updated = Signal()

    def __init__(self):
        """Initialize the dashboard service with required dependencies."""
        super().__init__()

        # Initialize services
        self._dataframe_store = DataFrameStore()
        self._config_manager = ConfigManager()
        self._file_service = FileService()
        self._chart_service = ChartService()

        # Initialize cache
        self._statistics_cache = {}
        self._trends_cache = {}
        self._previous_statistics = {}

        # Connect to data change signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to signals from other services."""
        if hasattr(self._dataframe_store, "data_changed"):
            self._dataframe_store.data_changed.connect(self._on_data_changed)

    def _on_data_changed(self) -> None:
        """Handle data changes by updating statistics and emitting signals."""
        # Store previous statistics for trend calculation
        self._previous_statistics = self._statistics_cache.copy()

        # Clear caches
        self._statistics_cache = {}
        self._trends_cache = {}

        # Recalculate statistics
        self.get_statistics()

        # Emit signals
        self.statistics_updated.emit()
        self.charts_updated.emit()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate and return dashboard statistics.

        Returns:
            Dict containing key statistics like total records, unique players, etc.
        """
        # Return cached statistics if available
        if self._statistics_cache:
            return self._statistics_cache

        # Initialize statistics with default values
        stats = {
            "total_records": 0,
            "total_value": 0,
            "unique_players": 0,
            "unique_chests": 0,
            "unique_sources": 0,
            "average_value": 0,
            "last_updated": None,
        }

        # Check if data is available
        if not self._dataframe_store.has_data():
            self._statistics_cache = stats
            return stats

        # Get the dataframe
        df = self._dataframe_store.get_dataframe()
        if df.empty:
            self._statistics_cache = stats
            return stats

        # Calculate statistics
        stats["total_records"] = len(df)
        stats["total_value"] = df["Value"].sum() if "Value" in df.columns else 0
        stats["unique_players"] = df["Player Name"].nunique() if "Player Name" in df.columns else 0
        stats["unique_chests"] = df["Chest Type"].nunique() if "Chest Type" in df.columns else 0
        stats["unique_sources"] = (
            df["Source/Location"].nunique() if "Source/Location" in df.columns else 0
        )

        # Calculate average value
        if stats["total_records"] > 0 and "Value" in df.columns:
            stats["average_value"] = stats["total_value"] / stats["total_records"]

        # Get last update time
        if "Date" in df.columns and not df["Date"].empty:
            stats["last_updated"] = pd.to_datetime(df["Date"]).max().strftime("%Y-%m-%d")

        # Cache the results
        self._statistics_cache = stats

        return stats

    def get_trend_data(self) -> Dict[str, Dict[str, Union[str, float]]]:
        """
        Calculate trend information for key metrics.

        Returns:
            Dict of metrics with their trend direction and percentage change.
        """
        # Return cached trends if available
        if self._trends_cache:
            return self._trends_cache

        # Get current statistics
        current_stats = self.get_statistics()

        # Initialize trends
        trends = {}

        # Check if we have previous statistics
        if not self._previous_statistics:
            # Load from configuration if available
            saved_stats = self._config_manager.get_value("previous_statistics", {})
            if saved_stats:
                self._previous_statistics = saved_stats

        # Calculate trends for key metrics
        for key in ["total_records", "total_value", "unique_players", "average_value"]:
            current = current_stats.get(key, 0)
            previous = self._previous_statistics.get(
                key, current
            )  # Default to current if no previous

            if previous == 0:
                direction = "neutral"
                percentage = 0.0
            else:
                change = current - previous
                percentage = (change / previous) * 100

                if change > 0:
                    direction = "up"
                elif change < 0:
                    direction = "down"
                else:
                    direction = "neutral"

            trends[key] = {"direction": direction, "percentage": round(percentage, 1)}

        # Cache the results
        self._trends_cache = trends

        # Save current statistics for future trend calculation
        self._config_manager.set_value("previous_statistics", current_stats)

        return trends

    def get_recent_files(self, max_files: int = 5) -> List[Dict[str, Any]]:
        """
        Get information about recently opened files.

        Args:
            max_files: Maximum number of files to return

        Returns:
            List of file information dictionaries
        """
        return self._file_service.get_recent_files(max_files)

    def get_chart_preview(self, chart_type: str) -> Any:
        """
        Get a chart preview for the dashboard.

        Args:
            chart_type: Type of chart to generate

        Returns:
            Chart object that can be displayed in the UI
        """
        return self._chart_service.create_chart(chart_type)

    def get_action_cards(self) -> List[Dict[str, Any]]:
        """
        Get action card configurations for the dashboard.

        Returns:
            List of action card configurations
        """
        # Default set of action cards
        actions = [
            {
                "title": "Import Data",
                "description": "Import chest data from CSV files",
                "icon": "import",
                "action": "import_data",
            },
            {
                "title": "Validate Data",
                "description": "Check data against validation rules",
                "icon": "validate",
                "action": "validate_data",
            },
            {
                "title": "Export Report",
                "description": "Generate a report from your data",
                "icon": "report",
                "action": "export_report",
            },
            {
                "title": "Data Analysis",
                "description": "View detailed analysis of your data",
                "icon": "analysis",
                "action": "show_analysis",
            },
        ]

        # Get user's frequently used actions from config
        frequent_actions = self._config_manager.get_value("frequent_actions", [])

        # Sort actions based on frequency (if available)
        if frequent_actions:
            # Map action names to counts
            action_counts = {
                action: frequent_actions.count(action) for action in set(frequent_actions)
            }

            # Sort actions by count (descending)
            actions.sort(key=lambda x: action_counts.get(x["action"], 0), reverse=True)

        return actions

    def track_action_used(self, action_name: str) -> None:
        """
        Track usage of an action to update frequently used actions.

        Args:
            action_name: Name of the action that was used
        """
        # Get current frequent actions
        frequent_actions = self._config_manager.get_value("frequent_actions", [])

        # Add the new action
        frequent_actions.append(action_name)

        # Keep only the last 50 actions to limit storage
        frequent_actions = frequent_actions[-50:]

        # Save back to config
        self._config_manager.set_value("frequent_actions", frequent_actions)

        # Emit signal that actions may have changed
        self.actions_updated.emit()

    def get_card_layout(self) -> Dict[str, Any]:
        """
        Get the dashboard card layout configuration.

        Returns:
            Dictionary with layout information for dashboard cards
        """
        # Get saved layout or use default
        default_layout = {
            "statistics_cards": ["total_records", "unique_players", "total_value", "average_value"],
            "chart_previews": ["chest_distribution", "value_by_source"],
            "action_cards": ["import_data", "validate_data", "export_report", "show_analysis"],
            "layout_version": 1,
        }

        return self._config_manager.get_value("dashboard_layout", default_layout)

    def save_card_layout(self, layout: Dict[str, Any]) -> None:
        """
        Save a custom dashboard card layout.

        Args:
            layout: Dictionary with layout information
        """
        self._config_manager.set_value("dashboard_layout", layout)
