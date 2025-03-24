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

    Attributes:
        action_triggered (Signal): Signal emitted when an action is triggered
        file_selected (Signal): Signal emitted when a file is selected
        import_requested (Signal): Signal emitted when import is requested
    """

    action_triggered = Signal(str)  # action name
    file_selected = Signal(str)  # file path
    import_requested = Signal()  # request to import data

    def __init__(self, data_model=None, parent=None):
        """
        Initialize the dashboard view.

        Args:
            data_model: The data model (optional)
            parent (QWidget, optional): The parent widget
        """
        super().__init__("Dashboard", parent)
        self._data_model = data_model
        self._data_loaded = False

        # Create dashboard widgets
        self._setup_dashboard()
        self._connect_action_signals()

        # Set initial state
        self.set_data_loaded(False)

    def _setup_dashboard(self):
        """Set up the dashboard with content and empty state views."""
        content_layout = self.get_content_layout()

        # Create stacked widget to switch between empty state and content
        self._stacked_widget = QStackedWidget()
        content_layout.addWidget(self._stacked_widget)

        # Empty state view
        self._empty_state_widget = self._create_empty_state_widget()
        self._stacked_widget.addWidget(self._empty_state_widget)

        # Content view
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(20)
        self._create_dashboard_widgets()
        self._stacked_widget.addWidget(self._content_widget)

    def _create_empty_state_widget(self):
        """Create empty state widget for when no data is loaded."""
        empty_widget = EmptyStateWidget(
            title="No Data Loaded",
            message="Import data to see statistics and insights",
            action_text="Import Data",
            icon=Icons.get_icon(Icons.OPEN),
        )

        # Connect action button to import_requested signal
        empty_widget.action_clicked.connect(self.import_requested.emit)

        return empty_widget

    def _create_dashboard_widgets(self):
        """Create the dashboard widgets for the data-loaded state."""
        # Stats cards grid
        self._stats_grid = QWidget()
        self._stats_layout = QGridLayout(self._stats_grid)
        self._stats_layout.setContentsMargins(0, 0, 0, 0)
        self._stats_layout.setSpacing(20)

        # Create stats cards
        self._dataset_card = StatsCard("Current Dataset", "0 rows")
        self._validation_card = StatsCard("Validation Status", "N/A")
        self._correction_card = StatsCard("Correction Status", "0 corrected")
        self._import_card = StatsCard("Last Import", "Never")

        # Add to grid
        self._stats_layout.addWidget(self._dataset_card, 0, 0)
        self._stats_layout.addWidget(self._validation_card, 0, 1)
        self._stats_layout.addWidget(self._correction_card, 0, 2)
        self._stats_layout.addWidget(self._import_card, 0, 3)

        self._content_layout.addWidget(self._stats_grid)

        # Add spacing
        self._content_layout.addSpacing(20)

        # Charts grid (two columns)
        self._charts_grid = QWidget()
        self._charts_layout = QGridLayout(self._charts_grid)
        self._charts_layout.setContentsMargins(0, 0, 0, 0)
        self._charts_layout.setSpacing(20)

        # Recent files widget
        self._recent_files = RecentFilesWidget("Recent Files")
        self._charts_layout.addWidget(self._recent_files, 0, 0)

        # Top players chart
        self._top_players_chart = ChartWidget("Top Players")
        self._charts_layout.addWidget(self._top_players_chart, 0, 1)

        # Chest sources chart
        self._chest_sources_chart = ChartWidget("Top Chest Sources")
        self._charts_layout.addWidget(self._chest_sources_chart, 1, 0)

        # Quick actions widget
        self._quick_actions = QuickActionsWidget("Quick Actions")
        self._quick_actions.add_action("import", "Import", 0, 0)
        self._quick_actions.add_action("validate", "Validate", 0, 1)
        self._quick_actions.add_action("analyze", "Analyze", 1, 0)
        self._quick_actions.add_action("report", "Generate Report", 1, 1)

        self._charts_layout.addWidget(self._quick_actions, 1, 1)

        self._content_layout.addWidget(self._charts_grid)

        # Add stretch to push everything to the top
        self._content_layout.addStretch()

    def _connect_action_signals(self):
        """Connect action signals."""
        # Quick actions
        self._quick_actions.action_triggered.connect(self.action_triggered)

        # Recent files
        self._recent_files.file_selected.connect(self.file_selected)

        # Import action from empty state
        self._empty_state_widget.action_clicked.connect(
            lambda: self.action_triggered.emit("import")
        )

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

        # If we have rows, ensure we're in the data loaded state
        if dataset_rows > 0:
            self.set_data_loaded(True)

    def set_recent_files(self, files):
        """
        Set the list of recent files.

        Args:
            files (list): List of file paths
        """
        self._recent_files.set_files(files)

    def set_data_loaded(self, loaded: bool):
        """
        Set whether data is loaded and update the UI accordingly.

        Args:
            loaded (bool): Whether data is loaded
        """
        self._data_loaded = loaded

        # Switch between empty state and content views
        self._stacked_widget.setCurrentIndex(1 if loaded else 0)

    def refresh(self):
        """Refresh the dashboard view with the latest data."""
        # No need to refresh if we're not visible
        if not self.isVisible():
            return

        # Update dashboard components
        self._update_recent_file_list()
        self._update_dashboard_stats()

    def _update_recent_file_list(self):
        """Update the recent file list in the dashboard."""
        try:
            # Check if the recent files widget exists and update it
            if hasattr(self, "_recent_files") and self._recent_files is not None:
                # If we're connected to the main window, get the recent files
                parent = self.parent()
                while parent:
                    if hasattr(parent, "_recent_files"):
                        # Update with main window's recent files
                        self._recent_files.set_files(parent._recent_files)
                        break
                    parent = parent.parent()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error updating recent file list: {e}")

    def _update_dashboard_stats(self):
        """Update the dashboard statistics."""
        try:
            # Only update stats if we have the data model
            if hasattr(self, "_data_model") and self._data_model is not None:
                # Get data from the model
                has_data = not self._data_model.is_empty
                if has_data:
                    # Update dashboard stats with current data
                    row_count = (
                        len(self._data_model.data) if hasattr(self._data_model, "data") else 0
                    )
                    validation_status = (
                        "Not Validated"
                        if self._data_model.get_validation_status().empty
                        else f"{len(self._data_model.get_validation_status())} issues"
                    )
                    corrections = (
                        self._data_model.get_correction_row_count()
                        if hasattr(self._data_model, "get_correction_row_count")
                        else 0
                    )

                    from datetime import datetime

                    last_import = datetime.now().strftime("%Y-%m-%d %H:%M")

                    # Update the stats cards
                    self.update_stats(
                        dataset_rows=row_count,
                        validation_status=validation_status,
                        corrections=corrections,
                        last_import=last_import,
                    )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error updating dashboard stats: {e}")
