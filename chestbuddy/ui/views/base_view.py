"""
base_view.py

Description: Base view class for all content views in the application.
Usage:
    Inherit from this class to create specific content views.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QSizePolicy,
)
import logging

from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.ui.resources.style import Colors

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
        button.setObjectName(f"action_button_{name}")
        button.setCursor(Qt.PointingHandCursor)

        # Apply button style based on type
        if button_type == "primary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.PRIMARY_ACTIVE};
                }}
            """)
        elif button_type == "secondary":
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.SECONDARY};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {Colors.SECONDARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {Colors.SECONDARY_ACTIVE};
                }}
            """)
        elif button_type == "success":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
        elif button_type == "danger":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
        else:  # default
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #212529;
                    border: 1px solid #d6d8db;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e2e6ea;
                }
                QPushButton:pressed {
                    background-color: #dae0e5;
                }
            """)

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

    Attributes:
        data_required (bool): Whether this view requires data to be loaded to function
    """

    # Signal to request data
    data_requested = Signal()

    def __init__(self, title, parent=None, data_required=False):
        """
        Initialize the base view.

        Args:
            title (str): The view title
            parent (QWidget, optional): The parent widget
            data_required (bool): Whether this view requires data to function
        """
        super().__init__(parent)
        logger.debug(f"[BASE_VIEW] Initializing {self.__class__.__name__}")
        self._title = title
        self._data_required = data_required
        self._setup_ui()
        self._connect_signals()
        self._add_action_buttons()
        logger.debug(f"[BASE_VIEW] {self.__class__.__name__} initialized with empty view visible")

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header
        self._header = ViewHeader(self._title)
        self._layout.addWidget(self._header)

        # Content area with stacked widget for content and empty state
        self._content_stack = QStackedWidget()
        self._layout.addWidget(self._content_stack)

        # Regular content widget
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(24, 24, 24, 24)
        self._content_stack.addWidget(self._content)

        # Empty state widget (for views that require data)
        if self._data_required:
            self._empty_state = EmptyStateWidget(
                title="No Data Available",
                message="Import data to use this view.",
                action_text="Import Data",
                icon=Icons.get_icon(Icons.IMPORT),
            )
            self._empty_state.action_clicked.connect(self._on_import_data_requested)
            self._content_stack.addWidget(self._empty_state)
        else:
            self._empty_state = None

        # Default to showing content
        self._content_stack.setCurrentWidget(self._content)

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
        return self._header.add_action_button(name, text, button_type)

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

    def set_data_available(self, data_available: bool) -> None:
        """
        Update the view based on data availability.

        Args:
            data_available (bool): Whether data is available
        """
        logger.debug(
            f"[BASE_VIEW] {self.__class__.__name__} - Setting data available: {data_available}"
        )
        if not self._data_required:
            logger.debug(
                f"[BASE_VIEW] {self.__class__.__name__} - Data not required for this view, skipping"
            )
            return

        # Log the current state
        current_widget = self._content_stack.currentWidget()
        current_widget_name = "content" if current_widget == self._content else "empty_state"
        logger.debug(
            f"[BASE_VIEW] {self.__class__.__name__} - Before change: Current widget: {current_widget_name}"
        )

        # Update visibility based on data availability
        if data_available:
            logger.debug(f"[BASE_VIEW] {self.__class__.__name__} - Switching to content widget")
            self._content_stack.setCurrentWidget(self._content)
        else:
            logger.debug(f"[BASE_VIEW] {self.__class__.__name__} - Switching to empty state widget")
            self._content_stack.setCurrentWidget(self._empty_state)

        # Log the new state
        new_widget = self._content_stack.currentWidget()
        new_widget_name = "content" if new_widget == self._content else "empty_state"
        logger.debug(
            f"[BASE_VIEW] {self.__class__.__name__} - After change: Current widget: {new_widget_name}"
        )

        # Ensure the view is properly updated
        self.update()
        logger.debug(
            f"[BASE_VIEW] {self.__class__.__name__} - View updated after data availability change"
        )

    def set_empty_state_props(self, title=None, message=None, action_text=None, icon=None):
        """
        Configure the empty state widget properties.

        Args:
            title (str, optional): Title for the empty state
            message (str, optional): Message for the empty state
            action_text (str, optional): Text for the action button
            icon (QIcon, optional): Icon to display
        """
        if not self._data_required or not self._empty_state:
            return

        if title:
            self._empty_state.set_title(title)

        if message:
            self._empty_state.set_message(message)

        if action_text:
            self._empty_state.set_action(action_text)

        if icon:
            self._empty_state.set_icon(icon)

    def is_data_required(self):
        """
        Check if this view requires data.

        Returns:
            bool: True if this view requires data, False otherwise
        """
        return self._data_required

    def _on_import_data_requested(self):
        """
        Handle when the import data button is clicked on the empty state widget.

        This method ensures a consistent approach to import requests across all views.
        It emits the appropriate signals to trigger an import action:

        1. Emits data_requested() for backward compatibility with older code
        2. Emits action_triggered("import") if the view supports it (preferred method)
        3. Falls back to action_clicked("import") for views using the older signal pattern

        This standardization ensures that all import buttons throughout the application
        trigger the same handler in MainWindow (_on_dashboard_action) with the "import"
        parameter, which calls _open_file(). This prevents code duplication and ensures
        consistent behavior.
        """
        # Emit the standard data_requested signal
        self.data_requested.emit()

        # Also emit the action_triggered signal with "import" if it exists
        # This ensures consistency with dashboard and other views
        if hasattr(self, "action_triggered") and hasattr(self.action_triggered, "emit"):
            self.action_triggered.emit("import")
        elif hasattr(self, "action_clicked") and hasattr(self.action_clicked, "emit"):
            self.action_clicked.emit("import")

    def _add_action_buttons(self):
        """Add action buttons to the header. To be implemented by subclasses."""
        pass

    def has_changed(self, force_rescan: bool = False) -> bool:
        """
        Check if the view has changed.

        Args:
            force_rescan: Whether to force a rescan

        Returns:
            True if the view has changed, False otherwise
        """
        logger.debug(
            f"[BASE_VIEW] {self.__class__.__name__} - Checking if view has changed (force_rescan: {force_rescan})"
        )
        # If force_rescan is True, always treat as changed
        if force_rescan:
            logger.debug(
                f"[BASE_VIEW] {self.__class__.__name__} - Force rescan requested, returning True"
            )
            return True

        # If parent is None, the view has not changed
        if self._parent is None:
            logger.debug(f"[BASE_VIEW] {self.__class__.__name__} - No parent, view hasn't changed")
            return False

        # Otherwise, delegate to the parent's has_changed method
        parent_changed = self._parent.has_changed(force_rescan)
        logger.debug(
            f"[BASE_VIEW] {self.__class__.__name__} - Parent has changed: {parent_changed}"
        )
        return parent_changed
