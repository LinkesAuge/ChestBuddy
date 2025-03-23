"""
chart_preview.py

Description: A widget for displaying chart previews with interactive features
Usage:
    chart_preview = ChartPreview(
        title="Value Distribution",
        subtitle="Last 30 days",
        chart=chart_service.create_bar_chart("category", "value", "Distribution")
    )
    chart_preview.clicked.connect(on_chart_preview_clicked)
    layout.addWidget(chart_preview)
"""

from typing import Optional, Union

from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import (
    QIcon,
    QFont,
    QColor,
    QPainter,
    QPen,
    QBrush,
    QPaintEvent,
    QMouseEvent,
    QCursor,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QFrame,
    QStackedLayout,
)
from PySide6.QtCharts import QChartView, QChart

from chestbuddy.ui.resources.style import Colors


class ChartPreview(QWidget):
    """
    A widget for displaying interactive chart previews.

    Provides a visual container for charts with title, subtitle,
    and interactive features.

    Attributes:
        clicked (Signal): Signal emitted when the preview is clicked

    Implementation Notes:
        - Displays a QChart in a compact preview format
        - Supports clickable interaction for detailed view
        - Shows title and optional subtitle
        - Can display icon for visual context
        - Supports compact mode for space-efficient display
    """

    # Signal definitions
    clicked = Signal()

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        chart: Optional[QChart] = None,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None,
        compact: bool = False,
    ):
        """
        Initialize a new ChartPreview.

        Args:
            title (str): The title/label for the chart
            subtitle (str): Additional context text to display
            chart (QChart, optional): The chart to display
            icon (QIcon, optional): Icon to display for visual context
            parent (QWidget, optional): Parent widget
            compact (bool): Whether to use compact mode
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._subtitle = subtitle
        self._chart = chart
        self._icon = icon or QIcon()
        self._compact = compact
        self._clickable = True

        # Set up the UI
        self._setup_ui()

        # Configure widget behavior
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def _setup_ui(self):
        """Set up the widget's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            12, 12, 12, 12
        ) if not self._compact else main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8) if not self._compact else main_layout.setSpacing(6)

        # Top row with title and icon
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        # Title label
        self._title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(14) if not self._compact else title_font.setPointSize(12)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")
        top_row.addWidget(self._title_label)

        # Spacer to push icon to the right
        top_row.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Icon (if provided)
        if not self._icon.isNull():
            self._icon_label = QLabel()
            icon_size = QSize(18, 18) if not self._compact else QSize(14, 14)
            self._icon_label.setPixmap(self._icon.pixmap(icon_size))
            top_row.addWidget(self._icon_label)
        else:
            self._icon_label = None

        main_layout.addLayout(top_row)

        # Subtitle (if provided)
        if self._subtitle:
            self._subtitle_label = QLabel(self._subtitle)
            subtitle_font = QFont()
            subtitle_font.setPointSize(10) if not self._compact else subtitle_font.setPointSize(9)
            self._subtitle_label.setFont(subtitle_font)
            self._subtitle_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            main_layout.addWidget(self._subtitle_label)
        else:
            self._subtitle_label = None

        # Chart container with stacked layout for chart view and placeholder
        self._chart_container = QWidget()
        self._chart_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set minimum chart size
        min_height = 200 if not self._compact else 150
        self._chart_container.setMinimumHeight(min_height)

        self._stacked_layout = QStackedLayout(self._chart_container)
        self._stacked_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder for when no chart is available
        self._placeholder = QLabel("No chart data")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; background-color: {Colors.PRIMARY_LIGHTER};"
        )
        self._stacked_layout.addWidget(self._placeholder)

        # Add chart if available
        if self._chart:
            self._chart_view = self._create_chart_view(self._chart)
            self._stacked_layout.addWidget(self._chart_view)
            self._stacked_layout.setCurrentWidget(self._chart_view)
        else:
            self._chart_view = None
            self._stacked_layout.setCurrentWidget(self._placeholder)

        main_layout.addWidget(self._chart_container)

        # Set style sheet
        self.setStyleSheet(f"""
            ChartPreview {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
            ChartPreview:hover {{
                border: 1px solid {Colors.ACCENT};
                background-color: #1D324A;  /* Slightly lighter than PRIMARY */
            }}
        """)

    def _create_chart_view(self, chart):
        """
        Create a QChartView for the given chart.

        Args:
            chart (QChart): The chart to display

        Returns:
            QChartView: The chart view widget
        """
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setBackgroundBrush(QBrush(QColor(Colors.PRIMARY)))

        # Remove chart margins for the preview
        chart.setContentsMargins(0, 0, 0, 0)
        chart.setBackgroundVisible(False)

        # Make legend more compact
        if chart.legend():
            chart.legend().setVisible(False)

        # Remove title to avoid duplication with our widget title
        chart.setTitle("")

        return view

    def mousePressEvent(self, event: QMouseEvent):
        """
        Handle mouse press events.

        Args:
            event (QMouseEvent): The mouse event
        """
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self._clickable:
            self.clicked.emit()

    def title(self) -> str:
        """
        Get the title text.

        Returns:
            str: The title text
        """
        return self._title

    def subtitle(self) -> str:
        """
        Get the subtitle text.

        Returns:
            str: The subtitle text
        """
        return self._subtitle

    def chart(self) -> Optional[QChart]:
        """
        Get the current chart.

        Returns:
            QChart: The chart object or None
        """
        if self._chart_view:
            return self._chart_view.chart()
        return None

    def icon(self) -> QIcon:
        """
        Get the icon.

        Returns:
            QIcon: The icon
        """
        return self._icon

    def is_compact(self) -> bool:
        """
        Check if the preview is in compact mode.

        Returns:
            bool: True if compact, False otherwise
        """
        return self._compact

    def is_clickable(self) -> bool:
        """
        Check if the preview is clickable.

        Returns:
            bool: True if clickable, False otherwise
        """
        return self._clickable

    def set_title(self, title: str):
        """
        Set the title text.

        Args:
            title (str): The new title text
        """
        self._title = title
        self._title_label.setText(title)

    def set_subtitle(self, subtitle: str):
        """
        Set the subtitle text.

        Args:
            subtitle (str): The new subtitle text
        """
        self._subtitle = subtitle
        if self._subtitle_label:
            self._subtitle_label.setText(subtitle)
        else:
            # Create subtitle label if it doesn't exist
            self._subtitle_label = QLabel(subtitle)
            subtitle_font = QFont()
            subtitle_font.setPointSize(10) if not self._compact else subtitle_font.setPointSize(9)
            self._subtitle_label.setFont(subtitle_font)
            self._subtitle_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

            # Insert label after the title row but before the chart
            layout = self.layout()
            layout.insertWidget(1, self._subtitle_label)

    def set_chart(self, chart: QChart):
        """
        Set the chart to display.

        Args:
            chart (QChart): The new chart
        """
        self._chart = chart

        # Remove existing chart view if present
        if self._chart_view:
            self._stacked_layout.removeWidget(self._chart_view)
            self._chart_view.deleteLater()

        # Create new chart view
        self._chart_view = self._create_chart_view(chart)
        self._stacked_layout.addWidget(self._chart_view)
        self._stacked_layout.setCurrentWidget(self._chart_view)

    def clear_chart(self):
        """Remove the chart and show the placeholder."""
        self._chart = None

        # Remove chart view if present
        if self._chart_view:
            self._stacked_layout.removeWidget(self._chart_view)
            self._chart_view.deleteLater()
            self._chart_view = None

        # Show placeholder
        self._stacked_layout.setCurrentWidget(self._placeholder)

    def set_icon(self, icon: QIcon):
        """
        Set the icon.

        Args:
            icon (QIcon): The new icon
        """
        self._icon = icon

        # Update icon if it exists
        if self._icon_label:
            icon_size = QSize(18, 18) if not self._compact else QSize(14, 14)
            self._icon_label.setPixmap(icon.pixmap(icon_size))
        else:
            # Create icon label if it doesn't exist and icon is valid
            if not icon.isNull():
                top_row = self.layout().itemAt(0).layout()
                self._icon_label = QLabel()
                icon_size = QSize(18, 18) if not self._compact else QSize(14, 14)
                self._icon_label.setPixmap(icon.pixmap(icon_size))
                top_row.addWidget(self._icon_label)

    def set_compact(self, compact: bool):
        """
        Set the compact mode of the preview.

        Args:
            compact (bool): Whether to use compact styling
        """
        if self._compact != compact:
            self._compact = compact
            # Refresh the UI to apply compact changes
            self._refresh_ui()

    def set_clickable(self, clickable: bool):
        """
        Set whether the preview is clickable.

        Args:
            clickable (bool): Whether the preview should be clickable
        """
        if self._clickable != clickable:
            self._clickable = clickable

            # Update cursor
            if clickable:
                self.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

    def _refresh_ui(self):
        """Rebuild the UI to reflect current properties."""
        # Store the current chart
        current_chart = self.chart()

        # Clear the current layout
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear nested layouts
                while item.layout().count():
                    nested_item = item.layout().takeAt(0)
                    if nested_item.widget():
                        nested_item.widget().deleteLater()

        # Rebuild the UI
        self._setup_ui()

        # Restore the chart if one existed
        if current_chart:
            self.set_chart(current_chart)
