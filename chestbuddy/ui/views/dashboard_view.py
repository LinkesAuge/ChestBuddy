"""
dashboard_view.py

Description: Dashboard view showing summary information and quick actions.
Usage:
    Used in the MainWindow as the main landing page.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QScrollArea,
    QStackedWidget,
)

from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget
from chestbuddy.ui.widgets.chart_preview import ChartPreview
from chestbuddy.ui.widgets.stat_card import StatCard


class StatsCard(QFrame):
    """A card widget displaying a statistic with title and value."""

    def __init__(self, title, value, parent=None):
        """
        Initialize the stats card.

        Args:
            title (str): The card title
            value (str): The value to display
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._title = title
        self._value = value
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            StatsCard {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        # Layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(8)

        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 14px;
        """)
        self._layout.addWidget(self._title_label)

        # Value label
        self._value_label = QLabel(self._value)
        self._value_label.setStyleSheet(f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 24px;
            font-weight: 500;
        """)
        self._layout.addWidget(self._value_label)

    def set_value(self, value):
        """
        Set the card value.

        Args:
            value (str): The new value
        """
        self._value = value
        self._value_label.setText(value)


class ChartWidget(QFrame):
    """A widget for displaying charts."""

    def __init__(self, title, parent=None):
        """
        Initialize the chart widget.

        Args:
            title (str): The chart title
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._title = title
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            ChartWidget {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        # Layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 16px;
            font-weight: 500;
            padding-bottom: 8px;
            border-bottom: 1px solid {Colors.BORDER};
        """)
        self._layout.addWidget(self._title_label)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setAlignment(Qt.AlignCenter)

        # Placeholder text
        self._placeholder = QLabel("[Chart Visualization]")
        self._placeholder.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 14px;
        """)
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._content_layout.addWidget(self._placeholder)

        self._layout.addWidget(self._content)

    def get_content_widget(self):
        """
        Get the content widget.

        Returns:
            QWidget: The content widget
        """
        return self._content

    def get_content_layout(self):
        """
        Get the content layout.

        Returns:
            QVBoxLayout: The content layout
        """
        return self._content_layout


class QuickActionsWidget(QFrame):
    """A widget for displaying quick action buttons."""

    action_triggered = Signal(str)  # action name

    def __init__(self, title, parent=None):
        """
        Initialize the quick actions widget.

        Args:
            title (str): The widget title
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._title = title
        self._setup_ui()

        # Action buttons dictionary
        self._action_buttons = {}

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QuickActionsWidget {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        # Layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(16)

        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 16px;
            font-weight: 500;
        """)
        self._layout.addWidget(self._title_label)

        # Buttons grid
        self._grid = QWidget()
        self._grid_layout = QGridLayout(self._grid)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(12)

        self._layout.addWidget(self._grid)

    def add_action(self, name, text, row, column, button_type="primary"):
        """
        Add an action button.

        Args:
            name (str): The button name (identifier)
            text (str): The button text
            row (int): The grid row
            column (int): The grid column
            button_type (str): Button type ('default', 'primary', 'secondary', 'success', 'danger')

        Returns:
            QPushButton: The created button
        """
        button = QPushButton(text)

        # Apply class based on type
        if button_type != "default":
            button.setProperty("class", button_type)

        self._grid_layout.addWidget(button, row, column)
        self._action_buttons[name] = button

        # Connect signal
        button.clicked.connect(lambda: self.action_triggered.emit(name))

        return button


class RecentFilesWidget(QFrame):
    """A widget for displaying recent files."""

    file_selected = Signal(str)  # file path

    def __init__(self, title, parent=None):
        """
        Initialize the recent files widget.

        Args:
            title (str): The widget title
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._title = title
        self._setup_ui()

        # File items
        self._file_items = []

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            RecentFilesWidget {{
                background-color: {Colors.PRIMARY};
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
            }}
            
            QPushButton {{
                text-align: left;
                background-color: transparent;
                border: none;
                padding: 4px 0px;
                color: {Colors.ACCENT};
            }}
            
            QPushButton:hover {{
                color: {Colors.SECONDARY};
                text-decoration: underline;
            }}
        """)

        # Layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 16px;
            font-weight: 500;
            padding-bottom: 8px;
            border-bottom: 1px solid {Colors.BORDER};
        """)
        self._layout.addWidget(self._title_label)

        # Files container
        self._files_container = QWidget()
        self._files_layout = QVBoxLayout(self._files_container)
        self._files_layout.setContentsMargins(0, 0, 0, 0)
        self._files_layout.setSpacing(4)

        # Placeholder text
        self._placeholder = QLabel("No recent files")
        self._placeholder.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 14px;
        """)
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._files_layout.addWidget(self._placeholder)

        self._layout.addWidget(self._files_container)

    def set_files(self, files):
        """
        Set the list of recent files.

        Args:
            files (list): List of file paths
        """
        # Clear existing items
        for button in self._file_items:
            self._files_layout.removeWidget(button)
            button.deleteLater()

        self._file_items = []

        # Show placeholder if no files
        if not files:
            self._placeholder.setVisible(True)
            return

        # Hide placeholder
        self._placeholder.setVisible(False)

        # Add file items
        for file_path in files:
            button = QPushButton(file_path)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked, path=file_path: self.file_selected.emit(path))

            self._files_layout.addWidget(button)
            self._file_items.append(button)


class DashboardView(BaseView):
    """
    Dashboard view showing summary information and quick actions.

    This is the main landing page of the application.
    """

    action_triggered = Signal(str)  # action name
    file_selected = Signal(str)  # file path
    chart_clicked = Signal(str)  # chart id

    def __init__(self, data_model=None, parent=None):
        """
        Initialize the dashboard view.

        Args:
            data_model: The data model (optional)
            parent (QWidget, optional): The parent widget
        """
        super().__init__("Dashboard", parent, data_required=False)
        self._data_model = data_model
        self._data_available = False

        # Create stacked widget for content/empty state
        self._content_stack = QStackedWidget()
        self.get_content_layout().addWidget(self._content_stack)

        # Create main content widget
        self._dash_content = QWidget()
        self._dash_layout = QVBoxLayout(self._dash_content)
        self._dash_layout.setContentsMargins(0, 0, 0, 0)
        self._dash_layout.setSpacing(20)
        self._content_stack.addWidget(self._dash_content)

        # Create empty state widget
        self._empty_state = EmptyStateWidget(
            title="No Data Available",
            message="Import data to see dashboard insights and statistics.",
            action_text="Import Data",
            icon=Icons.get_icon(Icons.IMPORT),
        )
        self._empty_state.action_clicked.connect(self._on_import_clicked)
        self._content_stack.addWidget(self._empty_state)

        # Set default view based on data availability
        self._content_stack.setCurrentWidget(self._empty_state)

        # Create dashboard widgets
        self._create_dashboard_widgets()
        self._connect_action_signals()

    def _create_dashboard_widgets(self):
        """Create the dashboard widgets."""
        content_layout = self._dash_layout

        # Stats cards grid
        self._stats_grid = QWidget()
        self._stats_layout = QGridLayout(self._stats_grid)
        self._stats_layout.setContentsMargins(0, 0, 0, 0)
        self._stats_layout.setSpacing(20)

        # Create stats cards
        self._dataset_card = StatCard("Current Dataset", "0 rows", Icons.get_icon(Icons.TABLE))
        self._validation_card = StatCard("Validation Status", "N/A", Icons.get_icon(Icons.CHECK))
        self._correction_card = StatCard(
            "Correction Status", "0 corrected", Icons.get_icon(Icons.EDIT)
        )
        self._import_card = StatCard("Last Import", "Never", Icons.get_icon(Icons.IMPORT))

        # Add to grid
        self._stats_layout.addWidget(self._dataset_card, 0, 0)
        self._stats_layout.addWidget(self._validation_card, 0, 1)
        self._stats_layout.addWidget(self._correction_card, 0, 2)
        self._stats_layout.addWidget(self._import_card, 0, 3)

        content_layout.addWidget(self._stats_grid)

        # Charts grid (two columns)
        self._charts_grid = QWidget()
        self._charts_layout = QGridLayout(self._charts_grid)
        self._charts_layout.setContentsMargins(0, 0, 0, 0)
        self._charts_layout.setSpacing(20)

        # Recent files widget
        self._recent_files = RecentFilesWidget("Recent Files")
        self._charts_layout.addWidget(self._recent_files, 0, 0)

        # Top players chart
        self._top_players_chart = ChartPreview(
            title="Top Players",
            subtitle="Most frequent players in dataset",
            icon=Icons.get_icon(Icons.USER),
        )
        self._top_players_chart.clicked.connect(lambda: self.chart_clicked.emit("top_players"))
        self._charts_layout.addWidget(self._top_players_chart, 0, 1)

        # Chest sources chart
        self._chest_sources_chart = ChartPreview(
            title="Top Chest Sources",
            subtitle="Most common chest sources",
            icon=Icons.get_icon(Icons.FOLDER),
        )
        self._chest_sources_chart.clicked.connect(lambda: self.chart_clicked.emit("chest_sources"))
        self._charts_layout.addWidget(self._chest_sources_chart, 1, 0)

        # Quick actions widget
        self._quick_actions = QuickActionsWidget("Quick Actions")
        self._quick_actions.add_action("import", "Import", 0, 0)
        self._quick_actions.add_action("validate", "Validate", 0, 1)
        self._quick_actions.add_action("analyze", "Analyze", 1, 0)
        self._quick_actions.add_action("report", "Generate Report", 1, 1)

        self._charts_layout.addWidget(self._quick_actions, 1, 1)

        content_layout.addWidget(self._charts_grid)

        # Add stretch to push everything to the top
        content_layout.addStretch()

    def _connect_action_signals(self):
        """Connect action signals."""
        # Quick actions
        self._quick_actions.action_triggered.connect(self.action_triggered)

        # Recent files
        self._recent_files.file_selected.connect(self.file_selected)

    def _on_import_clicked(self):
        """Handle import button click from empty state."""
        self.action_triggered.emit("import")

    def update_stats(
        self, dataset_rows=0, validation_status="N/A", corrections=0, last_import="Never"
    ):
        """
        Update the stats cards.

        Args:
            dataset_rows (int): Number of rows in the dataset
            validation_status (str): Validation status text
            corrections (int): Number of corrections
            last_import (str): Last import date
        """
        self._dataset_card.set_value(f"{dataset_rows:,} rows")
        self._validation_card.set_value(validation_status)
        self._correction_card.set_value(f"{corrections:,} corrected")
        self._import_card.set_value(last_import)

        # Update data availability state
        self.set_data_available(dataset_rows > 0)

    def set_recent_files(self, files):
        """
        Set the list of recent files.

        Args:
            files (list): List of file paths
        """
        self._recent_files.set_files(files)

    def set_data_available(self, available):
        """
        Set whether data is available for the dashboard.

        Args:
            available (bool): Whether data is available
        """
        self._data_available = available

        # Show appropriate view based on data availability
        if available:
            self._content_stack.setCurrentWidget(self._dash_content)
        else:
            self._content_stack.setCurrentWidget(self._empty_state)

    def set_player_chart(self, chart):
        """
        Set the top players chart.

        Args:
            chart: The chart to display
        """
        if chart:
            self._top_players_chart.set_chart(chart)
        else:
            self._top_players_chart.clear_chart()

    def set_chest_sources_chart(self, chart):
        """
        Set the chest sources chart.

        Args:
            chart: The chart to display
        """
        if chart:
            self._chest_sources_chart.set_chart(chart)
        else:
            self._chest_sources_chart.clear_chart()
