"""
empty_state_widget.py

Description: Widget to display an empty state with a message and optional action.
Usage:
    widget = EmptyStateWidget(
        title="No Data",
        message="Import data to get started",
        action_text="Import",
        action_callback=on_import_clicked
    )
"""

from typing import Optional, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
)

from chestbuddy.ui.resources.style import Colors


class EmptyStateWidget(QWidget):
    """
    Widget to display an empty state with a message and optional action button.

    This widget provides a standard way to show an empty state in the application,
    with a title, message, optional icon, and an action button.

    Attributes:
        action_clicked (Signal): Signal emitted when the action button is clicked
    """

    action_clicked = Signal()

    def __init__(
        self,
        title: str = "No content",
        message: str = "There is no content to display",
        icon: Optional[QIcon] = None,
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize a new EmptyStateWidget.

        Args:
            title (str): The title text to display
            message (str): The message text to display
            icon (QIcon, optional): Icon to display above the title
            action_text (str, optional): Text for the action button
            action_callback (callable, optional): Callback function when button is clicked
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._message = message
        self._icon = icon
        self._action_text = action_text
        self._action_callback = action_callback
        self._action_button = None

        # Initialize UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(16)

        # Add some space at the top
        main_layout.addSpacing(32)

        # Icon if available
        if self._icon:
            icon_label = QLabel()
            icon_label.setPixmap(self._icon.pixmap(64, 64))
            icon_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(icon_label)
            main_layout.addSpacing(16)

        # Title
        title_label = QLabel(self._title)
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        main_layout.addWidget(title_label)

        # Message
        message_label = QLabel(self._message)
        message_font = message_label.font()
        message_font.setPointSize(12)
        message_label.setFont(message_font)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label)

        # Action button (if text provided)
        if self._action_text:
            self._action_button = QPushButton(self._action_text, self)
            self._action_button.setMinimumWidth(180)

            # Style the button
            self._action_button.setStyleSheet(f"""
                QPushButton {{
                    padding: 8px 16px;
                    background-color: {Colors.ACCENT};
                    color: {Colors.TEXT_LIGHT};
                    border-radius: 4px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {Colors.SECONDARY};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.PRIMARY_DARK};
                }}
            """)

            # Connect the button click signal
            self._action_button.clicked.connect(self._on_action_clicked)

            # Add button to layout with some spacing
            main_layout.addSpacing(8)
            main_layout.addWidget(self._action_button, 0, Qt.AlignCenter)

        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _on_action_clicked(self):
        """Handle the action button click event."""
        # Emit our signal
        self.action_clicked.emit()

        # Call the callback if provided
        if self._action_callback:
            self._action_callback()

    def title(self) -> str:
        """
        Get the title text.

        Returns:
            str: The title text
        """
        return self._title

    def message(self) -> str:
        """
        Get the message text.

        Returns:
            str: The message text
        """
        return self._message

    def action_button(self) -> Optional[QPushButton]:
        """
        Get the action button if it exists.

        Returns:
            Optional[QPushButton]: The action button, or None if no action was specified
        """
        return self._action_button

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

    def set_message(self, message: str):
        """
        Set the message text.

        Args:
            message (str): The new message text
        """
        self._message = message

    def set_action(self, action_text: str, action_callback: Optional[Callable] = None):
        """
        Set or change the action button.

        Args:
            action_text (str): Text for the action button
            action_callback (Callable, optional): Callback function for the action button
        """
        self._action_text = action_text

        if action_callback:
            self._action_callback = action_callback

        # If we already have a button, update it
        if self._action_button:
            self._action_button.setText(action_text)
        else:
            # We need to create the button
            main_layout = self.layout()

            self._action_button = QPushButton(self._action_text, self)
            self._action_button.setMinimumWidth(180)

            # Style the button
            self._action_button.setStyleSheet(f"""
                QPushButton {{
                    padding: 8px 16px;
                    background-color: {Colors.ACCENT};
                    color: {Colors.TEXT_LIGHT};
                    border-radius: 4px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {Colors.SECONDARY};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.PRIMARY_DARK};
                }}
            """)

            # Connect the button click signal
            self._action_button.clicked.connect(self._on_action_clicked)

            # Add button to layout with some spacing
            main_layout.addSpacing(8)
            main_layout.addWidget(self._action_button, 0, Qt.AlignCenter)

    def set_icon(self, icon: QIcon):
        """
        Set the icon.

        Args:
            icon (QIcon): The new icon
        """
        self._icon = icon

        # Refresh the UI to show the new icon
        # This is simplistic - in a real implementation we would just update the icon label
        # But for simplicity, we'll just rebuild the UI
        self._refresh_ui()

    def _refresh_ui(self):
        """Rebuild the UI to reflect current properties."""
        # Clear the current layout
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rebuild the UI
        self._setup_ui()
