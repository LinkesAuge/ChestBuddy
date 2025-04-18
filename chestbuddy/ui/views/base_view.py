"""
base_view.py

Description: Base view class for all content views in the application.
Usage:
    Inherit from this class to create specific content views.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
import logging

from chestbuddy.ui.resources.style import Colors
from chestbuddy.utils.signal_manager import SignalManager

# Set up logger
logger = logging.getLogger(__name__)


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
                border-bottom: 1px solid {Colors.SECONDARY};
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

    This provides common structure and functionality for all views,
    including standardized signal management.

    Signals:
        header_action_clicked (str): Emitted when a header action is clicked with the action ID
    """

    # Define signals
    header_action_clicked = Signal(str)  # Action ID

    def __init__(self, title, parent=None, debug_mode=False):
        """
        Initialize the base view.

        Args:
            title (str): The view title
            parent (QWidget, optional): The parent widget
            debug_mode (bool, optional): Enable debug mode for signal connections
        """
        super().__init__(parent)
        self._title = title
        self._debug_mode = debug_mode

        # Initialize signal manager
        self._signal_manager = SignalManager(debug_mode=debug_mode)

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
        """
        Connect signals to slots.

        This method is called during initialization. Override in derived classes
        to add specific signal connections, but always call the parent method first.
        """
        # BaseView signal connections
        pass

    def _connect_ui_signals(self):
        """
        Connect UI element signals.

        Override in derived classes to connect UI element signals to handler methods.
        """
        pass

    def _connect_controller_signals(self):
        """
        Connect controller signals.

        Override in derived classes to connect controller signals to handler methods.
        """
        pass

    def _connect_model_signals(self):
        """
        Connect data model signals.

        Override in derived classes to connect model signals to handler methods.
        """
        pass

    def _disconnect_signals(self):
        """
        Disconnect all signals connected to this view.

        Call this method before destroying the view to prevent signal-related errors.
        """
        if hasattr(self, "_signal_manager"):
            try:
                self._signal_manager.disconnect_receiver(self)
                logger.debug(f"Disconnected signals for {self.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error disconnecting signals for {self.__class__.__name__}: {e}")

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
        self._signal_manager.safe_connect(
            sender=button,
            signal_name="clicked",
            receiver=self,  # Provide self as the receiver context for the lambda
            slot_name_or_callable=lambda: self.header_action_clicked.emit(
                name
            ),  # Pass lambda as the callable slot
            safe_disconnect_first=True,  # Keep True for now
        )

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

    def closeEvent(self, event):
        """
        Handle close event by properly disconnecting signals.

        Args:
            event: The close event
        """
        self._disconnect_signals()
        super().closeEvent(event)

    def __del__(self):
        """Ensure signals are disconnected when the object is deleted."""
        try:
            self._disconnect_signals()
        except:
            # Prevent errors during deletion
            pass
