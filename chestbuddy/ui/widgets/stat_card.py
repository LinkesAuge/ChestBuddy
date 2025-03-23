"""
stat_card.py

Description: Card component for displaying statistics in the dashboard
Usage:
    stat_card = StatCard("Total Records", "1,234", trend="+5%")
    stat_card.value_changed.connect(my_handler)
"""

from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)


class StatCard(QFrame):
    """
    A card component for displaying statistics with a title, value, and trend indicator.

    Attributes:
        value_changed (Signal): Emitted when the stat value changes

    Implementation Notes:
        - Card appears with shadow effect and rounded corners
        - Trend indicators show positive/negative changes with color coding
        - Supports different sizes through size_hint property
    """

    # Signal emitted when the value changes
    value_changed = Signal(str)

    def __init__(
        self,
        title: str = "",
        value: str = "0",
        subtitle: str = "",
        trend: str = "",
        icon: str = "",
        parent: QWidget = None,
    ):
        """
        Initialize the stat card with title, value, and trend.

        Args:
            title (str): The title of the stat
            value (str): The value to display
            subtitle (str): Optional subtitle or description
            trend (str): Optional trend indicator (e.g., "+5.2%")
            icon (str): Optional icon name
            parent (QWidget): Parent widget
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._trend = trend
        self._icon = icon
        self._size_hint = "medium"  # small, medium, large

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components of the stat card."""
        # Set frame styling
        self.setObjectName("statCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            #statCard {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

        # Apply drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Create layouts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Create title label
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("statCardTitle")
        self._title_label.setStyleSheet("""
            #statCardTitle {
                color: #585858;
                font-size: 14px;
                font-weight: 500;
            }
        """)

        # Create value label
        self._value_label = QLabel(self._value)
        self._value_label.setObjectName("statCardValue")
        self._value_label.setStyleSheet("""
            #statCardValue {
                color: #333333;
                font-size: 28px;
                font-weight: 600;
            }
        """)

        # Create subtitle label if provided
        self._subtitle_label = None
        if self._subtitle:
            self._subtitle_label = QLabel(self._subtitle)
            self._subtitle_label.setObjectName("statCardSubtitle")
            self._subtitle_label.setStyleSheet("""
                #statCardSubtitle {
                    color: #7c7c7c;
                    font-size: 12px;
                }
            """)

        # Create trend label if provided
        self._trend_label = None
        if self._trend:
            self._trend_label = QLabel(self._trend)
            self._trend_label.setObjectName("statCardTrend")

            # Determine trend direction and apply color
            if self._trend.startswith("+"):
                self._trend_label.setStyleSheet("""
                    #statCardTrend {
                        color: #4caf50;
                        font-size: 12px;
                        font-weight: 500;
                    }
                """)
            elif self._trend.startswith("-"):
                self._trend_label.setStyleSheet("""
                    #statCardTrend {
                        color: #f44336;
                        font-size: 12px;
                        font-weight: 500;
                    }
                """)
            else:
                self._trend_label.setStyleSheet("""
                    #statCardTrend {
                        color: #7c7c7c;
                        font-size: 12px;
                        font-weight: 500;
                    }
                """)

        # Add widgets to layout
        main_layout.addWidget(self._title_label)
        main_layout.addWidget(self._value_label)

        # Create bottom row for subtitle and trend
        if self._subtitle_label or self._trend_label:
            bottom_row = QHBoxLayout()
            bottom_row.setSpacing(8)

            if self._subtitle_label:
                bottom_row.addWidget(self._subtitle_label)

            # Add stretch if both subtitle and trend exist
            if self._subtitle_label and self._trend_label:
                bottom_row.addStretch()

            if self._trend_label:
                bottom_row.addWidget(self._trend_label, alignment=Qt.AlignRight)

            main_layout.addLayout(bottom_row)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(100)

    def set_title(self, title: str):
        """
        Set the title of the stat card.

        Args:
            title (str): The new title
        """
        self._title = title
        self._title_label.setText(title)

    def title(self) -> str:
        """
        Get the current title.

        Returns:
            str: The current title
        """
        return self._title

    def set_value(self, value: str):
        """
        Set the value of the stat card.

        Args:
            value (str): The new value
        """
        if self._value != value:
            self._value = value
            self._value_label.setText(value)
            # Emit signal
            self.value_changed.emit(value)

    def value(self) -> str:
        """
        Get the current value.

        Returns:
            str: The current value
        """
        return self._value

    def set_subtitle(self, subtitle: str):
        """
        Set the subtitle of the stat card.

        Args:
            subtitle (str): The new subtitle
        """
        self._subtitle = subtitle

        # Create subtitle label if it doesn't exist
        if not self._subtitle_label and subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("statCardSubtitle")
            self._subtitle_label.setStyleSheet("""
                #statCardSubtitle {
                    color: #7c7c7c;
                    font-size: 12px;
                }
            """)

            # Recreate layout with subtitle
            self._setup_ui()
        elif self._subtitle_label:
            self._subtitle_label.setText(subtitle)

    def subtitle(self) -> str:
        """
        Get the current subtitle.

        Returns:
            str: The current subtitle
        """
        return self._subtitle

    def set_trend(self, trend: str):
        """
        Set the trend indicator of the stat card.

        Args:
            trend (str): The new trend indicator
        """
        self._trend = trend

        # Create trend label if it doesn't exist
        if not self._trend_label and trend:
            self._trend_label = QLabel(trend)
            self._trend_label.setObjectName("statCardTrend")

            # Recreate layout with trend
            self._setup_ui()
        elif self._trend_label:
            self._trend_label.setText(trend)

            # Update styling based on trend direction
            if trend.startswith("+"):
                self._trend_label.setStyleSheet("""
                    #statCardTrend {
                        color: #4caf50;
                        font-size: 12px;
                        font-weight: 500;
                    }
                """)
            elif trend.startswith("-"):
                self._trend_label.setStyleSheet("""
                    #statCardTrend {
                        color: #f44336;
                        font-size: 12px;
                        font-weight: 500;
                    }
                """)
            else:
                self._trend_label.setStyleSheet("""
                    #statCardTrend {
                        color: #7c7c7c;
                        font-size: 12px;
                        font-weight: 500;
                    }
                """)

    def trend(self) -> str:
        """
        Get the current trend indicator.

        Returns:
            str: The current trend indicator
        """
        return self._trend

    def set_size_hint(self, size: str):
        """
        Set the size hint of the stat card.

        Args:
            size (str): Size hint ("small", "medium", or "large")
        """
        if size in ["small", "medium", "large"]:
            self._size_hint = size

            # Apply size-specific styling
            if size == "small":
                self._value_label.setStyleSheet("""
                    #statCardValue {
                        color: #333333;
                        font-size: 22px;
                        font-weight: 600;
                    }
                """)
                self.setMinimumHeight(80)
            elif size == "medium":
                self._value_label.setStyleSheet("""
                    #statCardValue {
                        color: #333333;
                        font-size: 28px;
                        font-weight: 600;
                    }
                """)
                self.setMinimumHeight(100)
            elif size == "large":
                self._value_label.setStyleSheet("""
                    #statCardValue {
                        color: #333333;
                        font-size: 36px;
                        font-weight: 600;
                    }
                """)
                self.setMinimumHeight(120)

    def size_hint(self) -> str:
        """
        Get the current size hint.

        Returns:
            str: The current size hint
        """
        return self._size_hint

    # Define Qt properties
    title = Property(str, title, set_title)
    value = Property(str, value, set_value)
    subtitle = Property(str, subtitle, set_subtitle)
    trend = Property(str, trend, set_trend)
    size_hint = Property(str, size_hint, set_size_hint)
