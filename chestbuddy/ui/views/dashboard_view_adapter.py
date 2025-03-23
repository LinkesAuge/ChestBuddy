"""
dashboard_view_adapter.py

Description: Adapter for the Dashboard view that connects it to the application's data model
Usage:
    Used in the MainWindow to bridge the DashboardView with application data and signals.
"""

import logging
from typing import List, Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QSize, Slot
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
    QPushButton,
)

from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.widgets.action_card import ActionCard
from chestbuddy.ui.widgets.chart_card import ChartCard
from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.ui.resources.style import Colors
from chestbuddy.core.services.chart_service import ChartService
from chestbuddy.utils.config import ConfigManager
from chestbuddy.ui.widgets.stat_card import StatCard
from chestbuddy.ui.views.dashboard_view import DashboardView
from chestbuddy.ui.resources.resource_manager import ResourceManager

# Set up logger
logger = logging.getLogger(__name__)


class WelcomePanel(QFrame):
    """
    A panel for welcoming users and showing getting started information.

    This panel provides an introduction to the application and quick links
    to get started with common tasks.
    """

    action_clicked = Signal(str)  # action name

    def __init__(self, parent=None):
        """
        Initialize the welcome panel.

        Args:
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(f"""
            WelcomePanel {{
                background-color: {Colors.PRIMARY};
                border-radius: 8px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Welcome to ChestBuddy")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Colors.TEXT_LIGHT};
        """)
        layout.addWidget(title)

        # Bullet points
        bullet_widget = QWidget()
        bullet_layout = QVBoxLayout(bullet_widget)
        bullet_layout.setContentsMargins(0, 8, 0, 8)
        bullet_layout.setSpacing(8)

        bullet_points = ["• Import and manage chest data", "• Track performance and statistics"]

        for point in bullet_points:
            bullet_label = QLabel(point)
            bullet_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            bullet_layout.addWidget(bullet_label)

        layout.addWidget(bullet_widget)

        # Import Data button (renamed from Get Started)
        import_data_btn = QPushButton("Import Data")
        import_data_btn.setCursor(Qt.PointingHandCursor)
        import_data_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.ACCENT_ACTIVE};
            }}
        """)
        import_data_btn.clicked.connect(lambda: self.action_clicked.emit("import"))

        layout.addWidget(import_data_btn)
        layout.addStretch()


class RecentFilesPanel(QFrame):
    """
    A panel for displaying recent files.

    Provides a list of recently accessed files with the ability to open them.
    """

    file_selected = Signal(str)  # file path

    def __init__(self, parent=None):
        """
        Initialize the recent files panel.

        Args:
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._file_items = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(f"""
            RecentFilesPanel {{
                background-color: {Colors.PRIMARY};
                border-radius: 8px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(8)

        # Title
        title = QLabel("Recent Files")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Colors.TEXT_LIGHT};
        """)
        self._layout.addWidget(title)

        # Files container
        self._files_container = QWidget()
        self._files_layout = QVBoxLayout(self._files_container)
        self._files_layout.setContentsMargins(0, 8, 0, 0)
        self._files_layout.setSpacing(4)

        # Placeholder text
        self._placeholder = QLabel("No recent files")
        self._placeholder.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._files_layout.addWidget(self._placeholder)

        self._layout.addWidget(self._files_container)

        # View all button
        self._view_all_btn = QPushButton("View All")
        self._view_all_btn.setCursor(Qt.PointingHandCursor)
        self._view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.ACCENT};
                border: none;
                padding: 4px 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
                text-decoration: underline;
            }}
        """)
        self._view_all_btn.setVisible(False)  # Initially hidden
        self._layout.addWidget(self._view_all_btn)

    def set_files(self, files):
        """
        Set the list of recent files.

        Args:
            files (list): List of file paths
        """
        # Clear existing items
        for widget in self._file_items:
            self._files_layout.removeWidget(widget)
            widget.deleteLater()

        self._file_items = []

        # Show placeholder if no files
        if not files:
            self._placeholder.setVisible(True)
            self._view_all_btn.setVisible(False)
            return

        # Hide placeholder
        self._placeholder.setVisible(False)

        # Add file items (max 3 for compact display)
        display_files = files[:3]
        for file_path in display_files:
            file_widget = QFrame()
            file_widget.setStyleSheet(f"""
                QFrame {{
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                }}
                QFrame:hover {{
                    background-color: {Colors.PRIMARY_HOVER};
                }}
            """)
            file_layout = QVBoxLayout(file_widget)
            file_layout.setContentsMargins(4, 4, 4, 4)
            file_layout.setSpacing(0)

            # File name
            import os

            file_name = os.path.basename(file_path)
            name_label = QLabel(file_name)
            name_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-weight: bold;")

            # File path
            path_label = QLabel(file_path)
            path_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")

            file_layout.addWidget(name_label)
            file_layout.addWidget(path_label)

            file_widget.mousePressEvent = lambda event, path=file_path: self.file_selected.emit(
                path
            )
            file_widget.setCursor(Qt.PointingHandCursor)

            self._files_layout.addWidget(file_widget)
            self._file_items.append(file_widget)

        # Show view all button if there are more files
        self._view_all_btn.setVisible(len(files) > 3)
        self._view_all_btn.clicked.connect(lambda: self.file_selected.emit("view_all_files"))


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
        dashboard_updated (Signal): Emitted when dashboard data is updated
    """

    # Signals
    data_requested = Signal()
    action_triggered = Signal(str)  # action name
    chart_selected = Signal(str)  # chart id
    file_selected = Signal(str)  # file path
    dashboard_updated = Signal()

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
        self._resource_manager = ResourceManager()

        # Charts dictionary to store chart references
        self._charts = {}

        # Recent files reference
        self._recent_files = []

        # Data availability flag
        self._has_data = False

        # Initialize dashboard
        self._initialize_dashboard()

        # Connect signals
        self._setup_connections()

    def _setup_connections(self):
        """Set up the signal connections for the dashboard view."""
        # Connect the dashboard_updated signal to update the view
        self.dashboard_updated.connect(self._update_stats)

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

        # SECTION 1: Quick Actions - Now at the top
        actions_title = QLabel("Quick Actions")
        actions_title.setProperty("class", "section-title")
        actions_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {Colors.TEXT_LIGHT};
            }}
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
        divider.setStyleSheet(f"background-color: {Colors.BORDER};")
        main_layout.addWidget(divider)

        # SECTION 2: Welcome & Recent Files - Horizontal layout
        welcome_files_layout = QHBoxLayout()
        welcome_files_layout.setSpacing(16)

        # Welcome panel on the left
        self._welcome_panel = WelcomePanel()
        self._welcome_panel.action_clicked.connect(self._handle_action)
        welcome_files_layout.addWidget(self._welcome_panel)

        # Recent files panel on the right
        self._recent_files_panel = RecentFilesPanel()
        self._recent_files_panel.file_selected.connect(self._on_file_selected)
        welcome_files_layout.addWidget(self._recent_files_panel)

        # Add welcome/files layout to main layout
        welcome_files_container = QWidget()
        welcome_files_container.setLayout(welcome_files_layout)
        main_layout.addWidget(welcome_files_container)

        # Section divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setFrameShadow(QFrame.Sunken)
        divider2.setStyleSheet(f"background-color: {Colors.BORDER};")
        main_layout.addWidget(divider2)

        # SECTION 3: Charts & Analytics
        charts_title = QLabel("Charts & Analytics")
        charts_title.setProperty("class", "section-title")
        charts_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {Colors.TEXT_LIGHT};
            }}
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

    def _create_action_cards(self):
        """Create the action cards for the dashboard."""
        # Import Data card
        import_card = ActionCard(
            title="Import Data",
            description="Import data from CSV, Excel, or other sources",
            icon_name="import",
            actions=["import_csv", "import_excel", "import_json"],
            tag="Data",
        )
        self._actions_grid.addWidget(import_card, 0, 0)

        # Analyze Data card
        analyze_card = ActionCard(
            title="Analyze Data",
            description="Run analysis on your chest data",
            icon_name="analyze",
            actions=["analyze_trend", "analyze_distribution"],
            tag="Analysis",
        )
        self._actions_grid.addWidget(analyze_card, 0, 1)

        # Export Data card
        export_card = ActionCard(
            title="Export Results",
            description="Export data to various formats",
            icon_name="export",
            actions=["export_csv", "export_pdf", "export_image"],
            tag="Data",
        )
        self._actions_grid.addWidget(export_card, 0, 2)

        # Generate Report card
        report_card = ActionCard(
            title="Generate Report",
            description="Create detailed reports from your data",
            icon_name="report",
            actions=["report_summary", "report_detailed"],
            tag="Reports",
        )
        self._actions_grid.addWidget(report_card, 1, 0)

        # Settings card
        settings_card = ActionCard(
            title="Settings",
            description="Configure application settings",
            icon_name="settings",
            actions=["open_settings"],
            tag="System",
        )
        self._actions_grid.addWidget(settings_card, 1, 1)

        # Help card
        help_card = ActionCard(
            title="Help",
            description="Get help using the application",
            icon_name="help",
            actions=["open_documentation", "contact_support"],
            tag="Support",
        )
        self._actions_grid.addWidget(help_card, 1, 2)

        # Connect action signals
        for i in range(self._actions_grid.count()):
            item = self._actions_grid.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ActionCard):
                card = item.widget()
                card.action_clicked.connect(self._handle_action)

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

    def _handle_action(self, action: str) -> None:
        """
        Handle action button click.

        Args:
            action: Action identifier
        """
        logger.debug(f"Dashboard action triggered: {action}")

        # Map action card signals to consistent action names
        # This ensures import works consistently across the application
        action_mapping = {
            "import_csv": "import",  # Map import_csv to standard import action
            "import_excel": "import",  # Map import_excel to standard import action
            "import_json": "import",  # Map import_json to standard import action
        }

        # Use mapped action if available, otherwise use original
        mapped_action = action_mapping.get(action, action)

        # Emit the action signal
        self.action_triggered.emit(mapped_action)

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

        # Update recent files panel
        self._recent_files_panel.set_files(self._recent_files)

    def set_data_available(self, available: bool):
        """
        Set whether data is available.

        Args:
            available (bool): Whether data is available
        """
        self._has_data = available

        # Update UI visibility
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

    @Slot()
    def _update_stats(self):
        """Update the statistics cards with current data."""
        # Placeholder for statistics updating
        pass

    def get_action_cards(self) -> List[ActionCard]:
        """
        Get the list of action cards.

        Returns:
            List[ActionCard]: The list of action cards
        """
        return [
            card for card in self._actions_grid.findChildren(ActionCard) if card.tag() == "Data"
        ]

    def get_stat_cards(self) -> List[StatCard]:
        """
        Get the list of stat cards.

        Returns:
            List[StatCard]: The list of stat cards
        """
        return [card for card in self._actions_grid.findChildren(StatCard)]
