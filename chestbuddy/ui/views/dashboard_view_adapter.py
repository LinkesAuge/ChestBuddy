"""
dashboard_view_adapter.py

Description: Adapter for the Dashboard view that connects it to the application's data model
Usage:
    Used in the MainWindow to bridge the DashboardView with application data and signals.
"""

from typing import List, Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)

from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.widgets.action_card import ActionCard
from chestbuddy.ui.widgets.chart_card import ChartCard
from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.utils.config import ConfigManager


class DashboardViewAdapter(BaseView):
    """
    Modern Dashboard implementation using card components.

    This dashboard provides a user-friendly overview of the application state
    with quick actions, recent files, and chart previews.

    Attributes:
        data_requested (Signal): Signal emitted when data import is requested
        action_triggered (Signal): Signal emitted when an action is triggered
        chart_selected (Signal): Signal emitted when a chart is selected
        file_selected (Signal): Signal emitted when a recent file is selected
    """

    # Signals
    data_requested = Signal()
    action_triggered = Signal(str)  # action name
    chart_selected = Signal(str)  # chart id
    file_selected = Signal(str)  # file path

    def __init__(self, data_model, parent=None):
        """
        Initialize the dashboard view adapter.

        Args:
            data_model: The data model to connect to
            parent (QWidget, optional): The parent widget
        """
        # Initialize parent class first
        super().__init__("Dashboard", parent, data_required=False)

        self._data_model = data_model
        self._config = ConfigManager()

        # Charts dictionary to store chart references
        self._charts = {}

        # Recent files reference
        self._recent_files = []

        # Data availability flag
        self._has_data = False

        # Initialize dashboard
        self._initialize_dashboard()

    def _setup_ui(self):
        """Set up the UI components."""
        # Call parent setup to create the base layout and content area
        super()._setup_ui()

        # Main scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Main container widget
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Section title - Actions
        actions_title = QLabel("Quick Actions")
        actions_title.setProperty("class", "section-title")
        actions_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        main_layout.addWidget(actions_title)

        # Actions grid
        self._actions_grid = QGridLayout()
        self._actions_grid.setSpacing(16)
        self._actions_grid.setContentsMargins(0, 0, 0, 0)

        # Create action cards
        self._create_action_cards()

        # Add actions grid to main layout
        actions_container = QWidget()
        actions_container.setLayout(self._actions_grid)
        main_layout.addWidget(actions_container)

        # Section divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("background-color: #E0E0E0;")
        main_layout.addWidget(divider)

        # Recent Files section
        recent_files_title = QLabel("Recent Files")
        recent_files_title.setProperty("class", "section-title")
        recent_files_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        main_layout.addWidget(recent_files_title)

        # Recent files container
        self._recent_files_layout = QVBoxLayout()
        self._recent_files_layout.setSpacing(8)
        self._recent_files_layout.setContentsMargins(0, 0, 0, 0)

        # Recent files empty state
        self._recent_files_empty = EmptyStateWidget(
            title="No Recent Files",
            message="Your recently opened files will appear here",
            icon=QIcon(Icons.FILE_DOCUMENT),
        )
        self._recent_files_layout.addWidget(self._recent_files_empty)

        # Add recent files layout to main layout
        recent_files_container = QWidget()
        recent_files_container.setLayout(self._recent_files_layout)
        main_layout.addWidget(recent_files_container)

        # Section divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setFrameShadow(QFrame.Sunken)
        divider2.setStyleSheet("background-color: #E0E0E0;")
        main_layout.addWidget(divider2)

        # Charts section
        charts_title = QLabel("Charts & Analytics")
        charts_title.setProperty("class", "section-title")
        charts_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        main_layout.addWidget(charts_title)

        # Empty state for charts
        self._charts_empty_container = QWidget()
        empty_layout = QVBoxLayout(self._charts_empty_container)
        empty_layout.setContentsMargins(0, 10, 0, 0)

        self._charts_empty = EmptyStateWidget(
            title="No Data Available",
            message="Import data to see charts and analytics",
            action_text="Import Data",
            action_callback=self._on_import_clicked,
            icon=QIcon(Icons.CHART_LINE),
        )
        empty_layout.addWidget(self._charts_empty)
        main_layout.addWidget(self._charts_empty_container)

        # Charts container
        self._charts_container = QWidget()
        self._charts_layout = QHBoxLayout(self._charts_container)
        self._charts_layout.setSpacing(16)
        self._charts_layout.setContentsMargins(0, 10, 0, 0)
        self._charts_container.setVisible(False)  # Initially hidden

        main_layout.addWidget(self._charts_container)

        # Add spacer at the bottom
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Set the container as the scroll area widget
        scroll_area.setWidget(container)

        # Add scroll area to the content layout
        self.get_content_layout().addWidget(scroll_area)

        # Create empty state view for when no data is loaded
        self._dashboard_empty_state = EmptyStateWidget(
            title="Welcome to ChestBuddy",
            message="Import data to get started with your analysis",
            action_text="Import Data",
            action_callback=self._on_import_clicked,
            icon=QIcon(Icons.FOLDER_OPEN),
        )

        # Initially hidden - will be shown when no data is available
        self._dashboard_empty_state.setVisible(False)
        self.get_content_layout().addWidget(self._dashboard_empty_state)

    def _create_action_cards(self):
        """Create the action cards for the dashboard."""
        # Import Data card
        import_card = ActionCard(
            title="Import Data",
            description="Load data from CSV files to analyze",
            icon=QIcon(Icons.IMPORT),
            action_callback=self._on_import_clicked,
        )
        self._actions_grid.addWidget(import_card, 0, 0)

        # Export Data card
        export_card = ActionCard(
            title="Export Data",
            description="Export your data in various formats",
            icon=QIcon(Icons.EXPORT),
            action_callback=lambda: self._on_action_triggered("export"),
        )
        self._actions_grid.addWidget(export_card, 0, 1)

        # Validate Data card
        validate_card = ActionCard(
            title="Validate Data",
            description="Check your data for errors and inconsistencies",
            icon=QIcon(Icons.CHECK_CIRCLE),
            action_callback=lambda: self._on_action_triggered("validate"),
        )
        self._actions_grid.addWidget(validate_card, 0, 2)

        # Generate Report card
        report_card = ActionCard(
            title="Generate Report",
            description="Create reports from your analyzed data",
            icon=QIcon(Icons.FILE_DOCUMENT),
            action_callback=lambda: self._on_action_triggered("report"),
        )
        self._actions_grid.addWidget(report_card, 1, 0)

        # Settings card
        settings_card = ActionCard(
            title="Settings",
            description="Configure application settings",
            icon=QIcon(Icons.SETTINGS),
            action_callback=lambda: self._on_action_triggered("settings"),
        )
        self._actions_grid.addWidget(settings_card, 1, 1)

        # Help card
        help_card = ActionCard(
            title="Help",
            description="Learn how to use ChestBuddy effectively",
            icon=QIcon(Icons.HELP_CIRCLE),
            action_callback=lambda: self._on_action_triggered("help"),
        )
        self._actions_grid.addWidget(help_card, 1, 2)

    def _initialize_dashboard(self):
        """Initialize the dashboard state."""
        # Set initial data availability
        has_data = (
            self._data_model is not None
            and getattr(self._data_model, "get_row_count", lambda: 0)() > 0
        )
        self.set_data_available(has_data)

        # Set recent files
        self.set_recent_files(self._config.get_recent_files() or [])

        # Update charts if data is available
        if has_data:
            self.update_charts()

    def _on_import_clicked(self):
        """Handle import button click."""
        self.data_requested.emit()

    def _on_action_triggered(self, action):
        """
        Handle action triggered from dashboard.

        Args:
            action (str): The action identifier
        """
        # Forward all actions
        self.action_triggered.emit(action)

    def _on_file_selected(self, file_path):
        """
        Handle file selection.

        Args:
            file_path (str): The selected file path
        """
        self.file_selected.emit(file_path)

    def _on_chart_clicked(self, chart_id):
        """
        Handle chart selection.

        Args:
            chart_id (str): The chart identifier
        """
        self.chart_selected.emit(chart_id)

    def update_charts(self):
        """Update the charts displayed in the dashboard."""
        # Clear existing charts
        self._clear_charts()

        # Create charts only if data is available
        if not self._data_model or getattr(self._data_model, "get_row_count", lambda: 0)() == 0:
            return

        # Create chart service
        chart_service = ChartService(self._data_model)

        # Generate chart thumbnails
        # Player distribution chart
        player_chart = chart_service.create_player_distribution_chart()
        if player_chart:
            player_pixmap = QPixmap(300, 180)
            player_pixmap.fill(Qt.white)
            # Use QPainter to render the chart to the pixmap
            painter = QPainter(player_pixmap)
            player_chart.scene().render(painter)
            painter.end()

            # Create chart card
            player_card = ChartCard(
                title="Player Distribution",
                description="Player distribution by rank and profile",
                chart_id="player_dist",
                thumbnail=player_pixmap,
                on_click=lambda: self._on_chart_clicked("player_dist"),
            )
            self._charts_layout.addWidget(player_card)
            self._charts["player_dist"] = player_card

        # Chest sources chart
        chest_chart = chart_service.create_chest_sources_chart()
        if chest_chart:
            chest_pixmap = QPixmap(300, 180)
            chest_pixmap.fill(Qt.white)
            # Use QPainter to render the chart to the pixmap
            painter = QPainter(chest_pixmap)
            chest_chart.scene().render(painter)
            painter.end()

            # Create chart card
            chest_card = ChartCard(
                title="Chest Sources",
                description="Distribution of chests by source",
                chart_id="chest_sources",
                thumbnail=chest_pixmap,
                on_click=lambda: self._on_chart_clicked("chest_sources"),
            )
            self._charts_layout.addWidget(chest_card)
            self._charts["chest_sources"] = chest_card

    def _clear_charts(self):
        """Clear all charts from the layout."""
        # Remove all chart widgets
        while self._charts_layout.count():
            item = self._charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear charts dictionary
        self._charts.clear()

    def set_recent_files(self, files: List[str]):
        """
        Set the list of recent files.

        Args:
            files (List[str]): List of file paths
        """
        # Convert file paths to strings if they're Path objects
        self._recent_files = [str(file_path) for file_path in files]
        self._update_recent_files_display()

    def _update_recent_files_display(self):
        """Update the display of recent files."""
        # Clear existing widgets
        while self._recent_files_layout.count():
            item = self._recent_files_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show empty state if no recent files
        if not self._recent_files:
            self._recent_files_empty = EmptyStateWidget(
                title="No Recent Files",
                message="Your recently opened files will appear here",
                icon=QIcon(Icons.FILE_DOCUMENT),
            )
            self._recent_files_layout.addWidget(self._recent_files_empty)
            return

        # Add file items
        for file_path in self._recent_files:
            # Create file card
            file_card = ActionCard(
                title=self._get_file_name(file_path),
                description=file_path,
                icon=QIcon(Icons.FILE),
                action_callback=lambda f=file_path: self._on_file_selected(f),
            )
            self._recent_files_layout.addWidget(file_card)

    def _get_file_name(self, file_path: str) -> str:
        """
        Get the file name from a path.

        Args:
            file_path (str): The file path

        Returns:
            str: The file name
        """
        # Extract file name from path
        import os

        return os.path.basename(file_path)

    def set_data_available(self, available: bool):
        """
        Set whether data is available.

        Args:
            available (bool): Whether data is available
        """
        self._has_data = available

        # Update UI visibility
        self._dashboard_empty_state.setVisible(not available)
        self._charts_empty_container.setVisible(available and not self._charts)
        self._charts_container.setVisible(available and bool(self._charts))

        # If data is now available, make sure to update charts
        if available and not self._charts:
            self.update_charts()

    def on_data_updated(self):
        """Handle data model update event."""
        # Update dashboard charts
        self.update_charts()
        self.set_data_available(True)

    def on_data_cleared(self):
        """Handle data model clear event."""
        # Update dashboard to show empty state
        self._clear_charts()
        self.set_data_available(False)
