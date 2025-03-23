"""
chart_card.py

Description: A card-style widget for displaying chart previews
Usage:
    card = ChartCard(
        title="Age Distribution",
        description="Distribution of patient ages",
        chart_id="age_dist",
        thumbnail=QPixmap("path/to/thumbnail.png"),
        on_click=lambda: view_chart("age_dist")
    )
    layout.addWidget(card)
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QPixmap, QEnterEvent
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)

from chestbuddy.ui.resources.style import Colors


class ChartCard(QFrame):
    """
    A card-style widget for displaying chart previews on the dashboard.

    Provides an interactive card for chart previews with title, description,
    and a thumbnail image of the chart.

    Attributes:
        clicked (Signal): Signal emitted when the card is clicked
        chart_selected (Signal[str]): Signal emitted with chart_id when the card is clicked
    """

    clicked = Signal()
    chart_selected = Signal(str)

    def __init__(
        self,
        title: str,
        description: str,
        chart_id: str,
        thumbnail: Optional[QPixmap] = None,
        on_click: Optional[Callable] = None,
        parent=None,
    ):
        """
        Initialize a new ChartCard.

        Args:
            title (str): The title of the chart
            description (str): Brief description of the chart
            chart_id (str): Unique identifier for the chart
            thumbnail (QPixmap, optional): Thumbnail preview of the chart
            on_click (Callable, optional): Callback function for when the card is clicked
            parent: Parent widget
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._description = description
        self._chart_id = chart_id
        self._thumbnail = thumbnail
        self._on_click = on_click
        self._hover = False

        # Set up the UI
        self._setup_ui()

        # Make the card clickable
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def _setup_ui(self):
        """Set up the widget's UI components."""
        # Set frame properties
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)

        # Apply card styling
        self.setStyleSheet(f"""
            ChartCard {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Thumbnail area
        if self._thumbnail:
            thumbnail_label = QLabel(self)
            thumbnail_label.setPixmap(
                self._thumbnail.scaled(300, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            thumbnail_label.setAlignment(Qt.AlignCenter)
            thumbnail_label.setMinimumHeight(180)
            thumbnail_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.PRIMARY_LIGHTER};
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    padding: 8px;
                }}
            """)
            main_layout.addWidget(thumbnail_label)
        else:
            # Placeholder for thumbnail
            placeholder = QLabel(self)
            placeholder.setMinimumHeight(180)
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setText("No Preview Available")
            placeholder.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.PRIMARY_LIGHTER};
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    color: {Colors.TEXT_MUTED};
                    font-style: italic;
                    padding: 8px;
                }}
            """)
            main_layout.addWidget(placeholder)

        # Text content container
        content_container = QFrame(self)
        content_container.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PRIMARY};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                padding: 8px;
            }}
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(4)

        # Title
        self._title_label = QLabel(self._title, content_container)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")
        content_layout.addWidget(self._title_label)

        # Description
        self._description_label = QLabel(self._description, content_container)
        description_font = QFont()
        description_font.setPointSize(9)
        self._description_label.setFont(description_font)
        self._description_label.setWordWrap(True)

        # Set description color slightly muted
        self._description_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        content_layout.addWidget(self._description_label)
        main_layout.addWidget(content_container)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        self.setMinimumHeight(250)
        self.setMaximumHeight(300)

    def enterEvent(self, event):
        """Handle mouse enter event for hover effect."""
        self._hover = True
        self.setStyleSheet(f"""
            ChartCard {{
                background-color: {Colors.PRIMARY_HOVER};
                border: 1px solid {Colors.ACCENT};
                border-radius: 8px;
            }}
        """)
        # Handle both Qt5 and Qt6 style events
        if isinstance(event, QEnterEvent):
            super().enterEvent(event)
        else:
            # For compatibility with tests
            pass

    def leaveEvent(self, event):
        """Handle mouse leave event for hover effect."""
        self._hover = False
        self.setStyleSheet(f"""
            ChartCard {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        # Pass the event to the parent class
        try:
            super().leaveEvent(event)
        except TypeError:
            # For compatibility with tests
            pass

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.setStyleSheet(f"""
                ChartCard {{
                    background-color: {Colors.PRIMARY_ACTIVE};
                    border: 1px solid {Colors.ACCENT_ACTIVE};
                    border-radius: 8px;
                }}
            """)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events to trigger the action."""
        if event.button() == Qt.LeftButton:
            # Reset style based on hover state
            if self._hover:
                self.setStyleSheet(f"""
                    ChartCard {{
                        background-color: {Colors.PRIMARY_HOVER};
                        border: 1px solid {Colors.ACCENT};
                        border-radius: 8px;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    ChartCard {{
                        background-color: {Colors.PRIMARY};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 8px;
                    }}
                """)

            # Emit our signals
            self.clicked.emit()
            self.chart_selected.emit(self._chart_id)

            # Call the callback if provided
            if self._on_click:
                self._on_click()

        super().mouseReleaseEvent(event)

    def title(self) -> str:
        """
        Get the chart title.

        Returns:
            str: The chart title
        """
        return self._title

    def description(self) -> str:
        """
        Get the chart description.

        Returns:
            str: The chart description
        """
        return self._description

    def chart_id(self) -> str:
        """
        Get the chart identifier.

        Returns:
            str: The chart identifier
        """
        return self._chart_id

    def thumbnail(self) -> Optional[QPixmap]:
        """
        Get the chart thumbnail.

        Returns:
            Optional[QPixmap]: The chart thumbnail, if any
        """
        return self._thumbnail

    def set_title(self, title: str):
        """
        Set the chart title.

        Args:
            title (str): The new chart title
        """
        self._title = title
        self._title_label.setText(title)

    def set_description(self, description: str):
        """
        Set the chart description.

        Args:
            description (str): The new chart description
        """
        self._description = description
        self._description_label.setText(description)

    def set_thumbnail(self, thumbnail: QPixmap):
        """
        Set the chart thumbnail.

        Args:
            thumbnail (QPixmap): The new chart thumbnail
        """
        self._thumbnail = thumbnail
        self._refresh_ui()

    def _refresh_ui(self):
        """Refresh the UI with current properties."""
        # This method would need to recreate the UI elements
        # For simplicity, we'll just create a new layout
        old_layout = self.layout()

        # Clear the old layout
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Remove the old layout
            self.setLayout(None)

        # Set up the UI again
        self._setup_ui()
