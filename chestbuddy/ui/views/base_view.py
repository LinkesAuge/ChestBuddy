"""
base_view.py

Description: Base view class for all content views in the application.
Usage:
    Inherit from this class to create specific content views.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame

from chestbuddy.ui.resources.style import Colors


class ViewHeader(QFrame):
    """Header widget for content views."""

    def __init__(self, title, parent=None):
        """
        Initialize the view header.

        Args:
            title (str): The header title
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
        self.setStyleSheet(f"""
            ViewHeader {{
                background-color: {Colors.PRIMARY};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        self.setFixedHeight(60)

        # Layout
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(24, 12, 24, 12)

        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: 500;
        """)
        self._layout.addWidget(self._title_label)

        # Spacer
        self._layout.addStretch()

        # Action buttons container
        self._action_container = QWidget()
        self._action_layout = QHBoxLayout(self._action_container)
        self._action_layout.setContentsMargins(0, 0, 0, 0)
        self._action_layout.setSpacing(10)

        self._layout.addWidget(self._action_container)

    def add_action_button(self, name, text, button_type="default"):
        """
        Add an action button to the header.

        Args:
            name (str): The button name (identifier)
            text (str): The button text
            button_type (str): Button type ('default', 'primary', 'secondary', 'success', 'danger')

        Returns:
            QPushButton: The created button
        """
        button = QPushButton(text)

        # Apply class based on type
        if button_type != "default":
            button.setProperty("class", button_type)

        self._action_layout.addWidget(button)
        self._action_buttons[name] = button

        return button

    def get_action_button(self, name):
        """
        Get an action button by name.

        Args:
            name (str): The button name

        Returns:
            QPushButton: The button, or None if not found
        """
        return self._action_buttons.get(name)

    def set_title(self, title):
        """
        Set the header title.

        Args:
            title (str): The new title
        """
        self._title = title
        self._title_label.setText(title)


class BaseView(QWidget):
    """
    Base class for all content views in the application.

    This provides common structure and functionality for all views.
    """

    # Define signals
    header_action_clicked = Signal(str)  # Action ID

    def __init__(self, title, parent=None):
        """
        Initialize the base view.

        Args:
            title (str): The view title
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._title = title
        self._setup_ui()
        self._connect_signals()
        self._add_action_buttons()

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header
        self._header = ViewHeader(self._title)
        self._layout.addWidget(self._header)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(24, 24, 24, 24)

        self._layout.addWidget(self._content)

    def _connect_signals(self):
        """Connect signals to slots."""
        pass  # To be implemented by subclasses

    def get_title(self):
        """
        Get the view title.

        Returns:
            str: The view title
        """
        return self._title

    def set_title(self, title):
        """
        Set the view title.

        Args:
            title (str): The new title
        """
        self._title = title
        self._header.set_title(title)

    def add_header_action(self, name, text, button_type="default"):
        """
        Add an action button to the header.

        Args:
            name (str): The button name (identifier)
            text (str): The button text
            button_type (str): Button type ('default', 'primary', 'secondary', 'success', 'danger')

        Returns:
            QPushButton: The created button
        """
        button = self._header.add_action_button(name, text, button_type)

        # Connect the button to emit the header_action_clicked signal with the action ID
        button.clicked.connect(lambda: self.header_action_clicked.emit(name))

        return button

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

    def _add_action_buttons(self):
        """Add action buttons to the header. To be implemented by subclasses."""
        pass
