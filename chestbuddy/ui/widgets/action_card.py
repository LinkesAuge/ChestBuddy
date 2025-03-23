"""
action_card.py

Description: A card-style widget for dashboard actions
Usage:
    card = ActionCard(
        title="Import Data",
        description="Load new data from CSV files",
        icon=QIcon(":/icons/import.svg"),
        action_callback=on_import_clicked
    )
    layout.addWidget(card)
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QEnterEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)

from chestbuddy.ui.resources.style import Colors


class ActionCard(QFrame):
    """
    A card-style widget for dashboard actions with title, description, and icon.

    Provides an interactive card that can be used as a clickable action item
    on the dashboard with visual feedback.

    Attributes:
        clicked (Signal): Signal emitted when the card is clicked
    """

    # Signal emitted when the card is clicked
    clicked = Signal()

    def __init__(
        self,
        title: str,
        description: str,
        icon: Optional[QIcon] = None,
        action_callback: Optional[Callable] = None,
        parent=None,
    ):
        """
        Initialize a new ActionCard.

        Args:
            title (str): The title text to display
            description (str): The description text to display
            icon (QIcon, optional): Icon to display on the card
            action_callback (Callable, optional): Callback function for when the card is clicked
            parent: Parent widget
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._description = description
        self._icon = icon or QIcon()
        self._action_callback = action_callback
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
            ActionCard {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Icon (if provided)
        if not self._icon.isNull():
            icon_label = QLabel(self)
            pixmap = self._icon.pixmap(QSize(48, 48))
            icon_label.setPixmap(pixmap)
            icon_label.setFixedSize(48, 48)
            main_layout.addWidget(icon_label)

        # Text content layout
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Title
        self._title_label = QLabel(self._title, self)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")
        content_layout.addWidget(self._title_label)

        # Description
        self._description_label = QLabel(self._description, self)
        description_font = QFont()
        description_font.setPointSize(10)
        self._description_label.setFont(description_font)
        self._description_label.setWordWrap(True)

        # Set description color slightly muted
        self._description_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        content_layout.addWidget(self._description_label)
        main_layout.addLayout(content_layout, 1)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(100)
        self.setMaximumHeight(120)

    def enterEvent(self, event):
        """Handle mouse enter event for hover effect."""
        self._hover = True
        self.setStyleSheet(f"""
            ActionCard {{
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
            ActionCard {{
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
                ActionCard {{
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
                    ActionCard {{
                        background-color: {Colors.PRIMARY_HOVER};
                        border: 1px solid {Colors.ACCENT};
                        border-radius: 8px;
                    }}
                """)
            else:
                self.setStyleSheet(f"""
                    ActionCard {{
                        background-color: {Colors.PRIMARY};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 8px;
                    }}
                """)

            # Emit our signal
            self.clicked.emit()

            # Call the callback if provided
            if self._action_callback:
                self._action_callback()

        super().mouseReleaseEvent(event)

    def title(self) -> str:
        """
        Get the title text.

        Returns:
            str: The title text
        """
        return self._title

    def description(self) -> str:
        """
        Get the description text.

        Returns:
            str: The description text
        """
        return self._description

    def icon(self) -> QIcon:
        """
        Get the icon.

        Returns:
            QIcon: The icon (may be null if no icon was specified)
        """
        return self._icon

    def set_title(self, title: str):
        """
        Set the title text.

        Args:
            title (str): The new title text
        """
        self._title = title
        self._title_label.setText(title)

    def set_description(self, description: str):
        """
        Set the description text.

        Args:
            description (str): The new description text
        """
        self._description = description
        self._description_label.setText(description)

    def set_icon(self, icon: QIcon):
        """
        Set the icon.

        Args:
            icon (QIcon): The new icon
        """
        self._icon = icon
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
