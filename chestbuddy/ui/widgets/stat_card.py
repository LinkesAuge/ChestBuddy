"""
stat_card.py

Description: A widget for displaying data metrics with visual indicators
Usage:
    stat_card = StatCard(
        title="Total Files",
        value="156",
        icon=QIcon(":/icons/file.png")
    )
    stat_card.clicked.connect(on_stat_card_clicked)
    stat_card.set_trend(StatCard.Trend.UP, "12% increase")
    stat_card.set_value_color(QColor(Colors.SUCCESS))
    layout.addWidget(stat_card)
"""

from typing import Optional, Union, Callable
from enum import Enum

from PySide6.QtCore import Qt, Signal, QSize, QRect, QRectF, QPoint
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
)

from chestbuddy.ui.resources.style import Colors


class StatCard(QWidget):
    """
    A widget for displaying a statistic with visual indicators.

    Provides a visual representation of a metric with title, value,
    trend indicators, and optional icon.

    Attributes:
        clicked (Signal): Signal emitted when the card is clicked

    Implementation Notes:
        - Supports compact and expanded modes
        - Displays trend indicators (up, down, neutral)
        - Supports custom value colors based on thresholds
        - Includes click handling for navigation
        - Can show icon for visual context
    """

    # Signal definitions
    clicked = Signal()

    # Trend enum for direction indicators
    class Trend(Enum):
        NONE = 0
        UP = 1
        DOWN = 2

    def __init__(
        self,
        title: str = "",
        value: str = "",
        subtitle: str = "",
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None,
        compact: bool = False,
    ):
        """
        Initialize a new StatCard.

        Args:
            title (str): The title/label for the statistic
            value (str): The value to display (can include units)
            subtitle (str): Additional context text to display below the value
            icon (QIcon, optional): Icon to display for visual context
            parent (QWidget, optional): Parent widget
            compact (bool): Whether to use compact mode
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._icon = icon or QIcon()
        self._compact = compact
        self._trend = self.Trend.NONE
        self._trend_text = ""
        self._value_color = QColor(Colors.TEXT_LIGHT)
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
            12, 10, 12, 10
        ) if not self._compact else main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(6) if not self._compact else main_layout.setSpacing(4)

        # Top row with title and icon
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        # Title label
        self._title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(10) if not self._compact else title_font.setPointSize(9)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        top_row.addWidget(self._title_label)

        # Spacer to push icon to the right
        top_row.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Icon (if provided)
        if not self._icon.isNull():
            self._icon_label = QLabel()
            icon_size = QSize(16, 16) if not self._compact else QSize(12, 12)
            self._icon_label.setPixmap(self._icon.pixmap(icon_size))
            top_row.addWidget(self._icon_label)
        else:
            self._icon_label = None

        main_layout.addLayout(top_row)

        # Value and trend indicators
        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(8)

        # Value label
        self._value_label = QLabel(self._value)
        value_font = QFont()
        value_font.setPointSize(18) if not self._compact else value_font.setPointSize(14)
        value_font.setBold(True)
        self._value_label.setFont(value_font)
        self._value_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")
        value_row.addWidget(self._value_label)

        # Spacer to push trend indicator to the right
        value_row.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Trend indicator (custom drawn in the paintEvent)
        self._trend_indicator = QFrame()
        self._trend_indicator.setFixedSize(QSize(24, 24) if not self._compact else QSize(18, 18))
        self._trend_indicator.setVisible(self._trend != self.Trend.NONE)
        value_row.addWidget(self._trend_indicator)

        main_layout.addLayout(value_row)

        # Subtitle/trend text (optional)
        if self._subtitle or self._trend_text:
            self._subtitle_label = QLabel(self._subtitle or self._trend_text)
            subtitle_font = QFont()
            subtitle_font.setPointSize(9) if not self._compact else subtitle_font.setPointSize(8)
            self._subtitle_label.setFont(subtitle_font)
            self._subtitle_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            main_layout.addWidget(self._subtitle_label)
        else:
            self._subtitle_label = None

        # Set minimum size
        min_width = 180 if not self._compact else 120
        min_height = 90 if not self._compact else 70
        self.setMinimumSize(min_width, min_height)

        # Set style sheet for the card
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
            StatCard:hover {{
                border: 1px solid {Colors.ACCENT};
                background-color: #1D324A;  /* Slightly lighter than PRIMARY */
            }}
        """)

    def _update_trend_indicator(self):
        """Update the trend indicator based on the current trend."""
        self._trend_indicator.setVisible(self._trend != self.Trend.NONE)
        if self._trend_indicator.isVisible():
            # Custom painting will be done in paintEvent
            self._trend_indicator.update()

        # Update subtitle if trend text exists
        if self._subtitle_label and self._trend_text:
            self._subtitle_label.setText(self._trend_text)

    def paintEvent(self, event: QPaintEvent):
        """
        Handle the paint event to draw the trend indicator.

        Args:
            event (QPaintEvent): The paint event
        """
        super().paintEvent(event)

        # Draw trend indicator if visible
        if self._trend_indicator and self._trend_indicator.isVisible():
            painter = QPainter(self._trend_indicator)
            painter.setRenderHint(QPainter.Antialiasing)

            # Calculate center of the indicator
            rect = self._trend_indicator.rect()
            center_x = rect.width() / 2
            center_y = rect.height() / 2

            # Set color based on trend
            if self._trend == self.Trend.UP:
                color = QColor(Colors.SUCCESS)
            elif self._trend == self.Trend.DOWN:
                color = QColor(Colors.ERROR)
            else:
                color = QColor(Colors.TEXT_MUTED)

            # Draw the arrow
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(QBrush(color))

            # Calculate arrow size based on compact mode
            arrow_size = 8 if not self._compact else 6

            if self._trend == self.Trend.UP:
                # Draw upward arrow
                points = [
                    QPoint(int(center_x), int(center_y - arrow_size)),
                    QPoint(int(center_x - arrow_size), int(center_y + arrow_size / 2)),
                    QPoint(int(center_x + arrow_size), int(center_y + arrow_size / 2)),
                ]
                painter.drawPolygon(points)
            elif self._trend == self.Trend.DOWN:
                # Draw downward arrow
                points = [
                    QPoint(int(center_x), int(center_y + arrow_size)),
                    QPoint(int(center_x - arrow_size), int(center_y - arrow_size / 2)),
                    QPoint(int(center_x + arrow_size), int(center_y - arrow_size / 2)),
                ]
                painter.drawPolygon(points)
            else:
                # Draw horizontal line for no trend
                painter.drawLine(
                    int(center_x - arrow_size),
                    int(center_y),
                    int(center_x + arrow_size),
                    int(center_y),
                )

            painter.end()

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

    def value(self) -> str:
        """
        Get the value text.

        Returns:
            str: The value text
        """
        return self._value

    def subtitle(self) -> str:
        """
        Get the subtitle text.

        Returns:
            str: The subtitle text
        """
        return self._subtitle

    def icon(self) -> QIcon:
        """
        Get the icon.

        Returns:
            QIcon: The icon
        """
        return self._icon

    def trend(self) -> Trend:
        """
        Get the current trend.

        Returns:
            Trend: The trend enum value
        """
        return self._trend

    def trend_text(self) -> str:
        """
        Get the trend description text.

        Returns:
            str: The trend text
        """
        return self._trend_text

    def is_compact(self) -> bool:
        """
        Check if the card is in compact mode.

        Returns:
            bool: True if compact, False otherwise
        """
        return self._compact

    def is_clickable(self) -> bool:
        """
        Check if the card is clickable.

        Returns:
            bool: True if clickable, False otherwise
        """
        return self._clickable

    def value_color(self) -> QColor:
        """
        Get the value text color.

        Returns:
            QColor: The text color
        """
        return self._value_color

    def set_title(self, title: str):
        """
        Set the title text.

        Args:
            title (str): The new title text
        """
        self._title = title
        self._title_label.setText(title)

    def set_value(self, value: str):
        """
        Set the value text.

        Args:
            value (str): The new value text
        """
        self._value = value
        self._value_label.setText(value)

    def set_subtitle(self, subtitle: str):
        """
        Set the subtitle text.

        Args:
            subtitle (str): The new subtitle text
        """
        self._subtitle = subtitle
        if self._subtitle_label:
            # Only update if not showing trend text
            if not self._trend_text:
                self._subtitle_label.setText(subtitle)
        else:
            # Create subtitle label if it doesn't exist
            self._subtitle_label = QLabel(subtitle)
            subtitle_font = QFont()
            subtitle_font.setPointSize(9) if not self._compact else subtitle_font.setPointSize(8)
            self._subtitle_label.setFont(subtitle_font)
            self._subtitle_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            self.layout().addWidget(self._subtitle_label)

    def set_icon(self, icon: QIcon):
        """
        Set the icon.

        Args:
            icon (QIcon): The new icon
        """
        self._icon = icon

        # Update icon if it exists
        if self._icon_label:
            icon_size = QSize(16, 16) if not self._compact else QSize(12, 12)
            self._icon_label.setPixmap(icon.pixmap(icon_size))
        else:
            # Create icon label if it doesn't exist and icon is valid
            if not icon.isNull():
                top_row = self.layout().itemAt(0).layout()
                self._icon_label = QLabel()
                icon_size = QSize(16, 16) if not self._compact else QSize(12, 12)
                self._icon_label.setPixmap(icon.pixmap(icon_size))
                top_row.addWidget(self._icon_label)

    def set_trend(self, trend: Trend, trend_text: str = ""):
        """
        Set the trend indicator and optional trend text.

        Args:
            trend (Trend): The trend direction (UP, DOWN, NONE)
            trend_text (str, optional): Description text for the trend
        """
        self._trend = trend
        self._trend_text = trend_text

        # Update subtitle to show trend text
        if trend_text and self._subtitle_label:
            self._subtitle_label.setText(trend_text)

        # Update trend indicator
        self._update_trend_indicator()

    def set_compact(self, compact: bool):
        """
        Set the compact mode of the card.

        Args:
            compact (bool): Whether to use compact styling
        """
        if self._compact != compact:
            self._compact = compact
            # Refresh the UI to apply compact changes
            self._refresh_ui()

    def set_clickable(self, clickable: bool):
        """
        Set whether the card is clickable.

        Args:
            clickable (bool): Whether the card should be clickable
        """
        if self._clickable != clickable:
            self._clickable = clickable

            # Update cursor
            if clickable:
                self.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

    def set_value_color(self, color: QColor):
        """
        Set the color of the value text.

        Args:
            color (QColor): The color for the value text
        """
        self._value_color = color
        self._value_label.setStyleSheet(f"color: {color.name()};")

    def _refresh_ui(self):
        """Rebuild the UI to reflect current properties."""
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

        # Restore dynamic properties
        self._value_label.setStyleSheet(f"color: {self._value_color.name()};")
        self._update_trend_indicator()
