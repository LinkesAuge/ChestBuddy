"""
sidebar_navigation.py

Description: A sidebar navigation widget for the ChestBuddy application.
Usage:
    Used in the MainWindow to provide navigation functionality.
"""

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
)

from chestbuddy.ui.resources.style import Colors


class NavigationButton(QPushButton):
    """A custom button used for sidebar navigation items."""

    def __init__(self, text, icon=None, parent=None):
        """
        Initialize the navigation button.

        Args:
            text (str): The button text
            icon (QIcon, optional): The button icon
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))

        # Set style properties
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        """Update button styling based on current state."""
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 0px;
                color: {Colors.TEXT_MUTED};
                background-color: transparent;
                font-weight: normal;
            }}
            
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            
            QPushButton:checked {{
                color: {Colors.TEXT_LIGHT};
                background-color: rgba(255, 255, 255, 0.05);
                border-left: 3px solid {Colors.SECONDARY};
                font-weight: bold;
            }}
            
            QPushButton:disabled {{
                color: rgba(200, 200, 200, 0.3);
                background-color: transparent;
                border-left: none;
                font-weight: normal;
            }}
        """)

    def set_enabled(self, enabled):
        """
        Set the enabled state of the button.

        Args:
            enabled (bool): Whether the button should be enabled
        """
        self.setEnabled(enabled)
        if not enabled:
            self.setChecked(False)
        self._update_style()


class SubNavigationButton(QPushButton):
    """A custom button used for sidebar sub-navigation items."""

    def __init__(self, text, parent=None):
        """
        Initialize the sub-navigation button.

        Args:
            text (str): The button text
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self.setText(text)

        # Set style properties
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        """Update button styling based on current state."""
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 6px 15px 6px 40px;
                border: none;
                border-radius: 0px;
                color: {Colors.TEXT_MUTED};
                background-color: transparent;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            
            QPushButton:checked {{
                color: {Colors.SECONDARY};
                background-color: transparent;
                font-weight: bold;
            }}
            
            QPushButton:disabled {{
                color: rgba(200, 200, 200, 0.3);
                background-color: transparent;
                font-weight: normal;
            }}
        """)

    def set_enabled(self, enabled):
        """
        Set the enabled state of the button.

        Args:
            enabled (bool): Whether the button should be enabled
        """
        self.setEnabled(enabled)
        if not enabled:
            self.setChecked(False)
        self._update_style()


class NavigationSection(QWidget):
    """A section in the sidebar with a main button and optional sub-buttons."""

    button_clicked = Signal(str, str)  # section, button

    def __init__(self, title, icon=None, parent=None):
        """
        Initialize the navigation section.

        Args:
            title (str): The section title
            icon (QIcon, optional): The section icon
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._title = title
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Create main button
        self._main_button = NavigationButton(title, icon)
        self._layout.addWidget(self._main_button)

        # Container for sub-buttons
        self._sub_container = QWidget()
        self._sub_layout = QVBoxLayout(self._sub_container)
        self._sub_layout.setContentsMargins(0, 0, 0, 0)
        self._sub_layout.setSpacing(0)
        self._layout.addWidget(self._sub_container)

        # Connect main button
        self._main_button.clicked.connect(self._on_main_button_clicked)

        # Track sub-buttons
        self._sub_buttons = {}

    def _on_main_button_clicked(self):
        """Handle main button click."""
        if self._main_button.isEnabled():
            self.button_clicked.emit(self._title, "")

    def add_sub_button(self, text):
        """
        Add a sub-button to the section.

        Args:
            text (str): The button text

        Returns:
            SubNavigationButton: The created button
        """
        button = SubNavigationButton(text)
        self._sub_layout.addWidget(button)
        self._sub_buttons[text] = button

        # Connect button click
        button.clicked.connect(lambda: self.button_clicked.emit(self._title, text))

        return button

    def set_checked(self, is_main=True, sub_text=""):
        """
        Set the checked state of buttons in this section.

        Args:
            is_main (bool): Whether to check the main button
            sub_text (str): Text of the sub-button to check
        """
        self._main_button.setChecked(is_main)

        if sub_text:
            for text, button in self._sub_buttons.items():
                button.setChecked(button.text() == sub_text)

    def uncheck_all(self):
        """Uncheck all buttons in this section."""
        self._main_button.setChecked(False)
        for button in self._sub_buttons.values():
            button.setChecked(False)

    def set_enabled(self, enabled):
        """
        Set the enabled state for the main button and all sub-buttons.

        Args:
            enabled (bool): Whether the section should be enabled
        """
        self._main_button.set_enabled(enabled)
        for button in self._sub_buttons.values():
            button.set_enabled(enabled)

    def set_sub_button_enabled(self, text, enabled):
        """
        Set the enabled state for a specific sub-button.

        Args:
            text (str): The text of the sub-button
            enabled (bool): Whether the button should be enabled
        """
        if text in self._sub_buttons:
            self._sub_buttons[text].set_enabled(enabled)

    def is_enabled(self):
        """
        Check if the section is enabled.

        Returns:
            bool: True if the main button is enabled, False otherwise
        """
        return self._main_button.isEnabled()

    def is_sub_button_enabled(self, text):
        """
        Check if a specific sub-button is enabled.

        Args:
            text (str): The text of the sub-button

        Returns:
            bool: True if the sub-button is enabled, False otherwise
        """
        if text in self._sub_buttons:
            return self._sub_buttons[text].isEnabled()
        return False


class SidebarNavigation(QFrame):
    """
    Sidebar navigation widget for the ChestBuddy application.

    This widget provides the main navigation menu with sections and sub-items.
    """

    navigation_changed = Signal(str, str)  # section, item

    def __init__(self, parent=None):
        """
        Initialize the sidebar navigation.

        Args:
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

        # Track all sections
        self._sections = {}

        # Initialize default sections
        self._create_default_sections()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            SidebarNavigation {{
                background-color: {Colors.PRIMARY};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)

        # Fixed width
        self.setFixedWidth(220)

        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Logo area
        self._logo_container = QWidget()
        self._logo_container.setStyleSheet(f"""
            background-color: {Colors.PRIMARY};
            border-bottom: 1px solid {Colors.BORDER};
        """)
        self._logo_container.setFixedHeight(60)

        self._logo_layout = QHBoxLayout(self._logo_container)
        self._logo_layout.setContentsMargins(15, 10, 15, 10)

        self._logo_label = QLabel("ChestBuddy")
        self._logo_label.setAlignment(Qt.AlignCenter)
        self._logo_label.setStyleSheet(f"""
            color: {Colors.SECONDARY};
            font-size: 18px;
            font-weight: bold;
        """)

        self._logo_layout.addWidget(self._logo_label)
        self._layout.addWidget(self._logo_container)

        # Scroll area for navigation items
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Scroll content widget
        self._scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 10, 0, 10)
        self._scroll_layout.setSpacing(0)
        self._scroll_layout.addStretch()

        self._scroll_area.setWidget(self._scroll_content)
        self._layout.addWidget(self._scroll_area)

    def _connect_signals(self):
        """Connect signals to slots."""
        pass  # Will be connected when sections are created

    def _create_default_sections(self):
        """Create the default navigation sections."""
        # Dashboard
        self.add_section("Dashboard", None)

        # Data section with sub-items
        data_section = self.add_section("Data", None)
        data_section.add_sub_button("Validate")
        data_section.add_sub_button("Correct")

        # Analysis section with sub-items
        analysis_section = self.add_section("Analysis", None)
        analysis_section.add_sub_button("Tables")
        analysis_section.add_sub_button("Charts")

        # Reports section
        self.add_section("Reports", None)

        # Settings section with sub-items
        settings_section = self.add_section("Settings", None)
        settings_section.add_sub_button("Lists")
        settings_section.add_sub_button("Rules")
        settings_section.add_sub_button("Preferences")

        # Help section
        self.add_section("Help", None)

        # Set Dashboard as default selected
        self.set_active_item("Dashboard")

    def add_section(self, title, icon=None):
        """
        Add a new navigation section.

        Args:
            title (str): The section title
            icon (QIcon, optional): The section icon

        Returns:
            NavigationSection: The created section
        """
        section = NavigationSection(title, icon)
        # Insert before the stretch at the end
        self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, section)

        # Connect signals
        section.button_clicked.connect(self._on_button_clicked)

        # Store reference
        self._sections[title] = section

        return section

    def _on_button_clicked(self, section, item):
        """
        Handle button click events from any section.

        Args:
            section (str): The section title
            item (str): The item text (empty for main section button)
        """
        # Uncheck all other sections
        for title, section_widget in self._sections.items():
            if title != section:
                section_widget.uncheck_all()

        # Emit signal
        self.navigation_changed.emit(section, item)

    def set_active_item(self, section, item=""):
        """
        Set the active navigation item.

        Args:
            section (str): The section title
            item (str, optional): The sub-item text
        """
        # Reset all sections
        for title, section_widget in self._sections.items():
            section_widget.uncheck_all()

        # Set active section
        if section in self._sections:
            is_main = not item
            self._sections[section].set_checked(is_main, item)

    def set_section_enabled(self, section, enabled):
        """
        Set the enabled state for a section.

        Args:
            section (str): The section title
            enabled (bool): Whether the section should be enabled
        """
        if section in self._sections:
            self._sections[section].set_enabled(enabled)

    def set_item_enabled(self, section, item, enabled):
        """
        Set the enabled state for a specific item in a section.

        Args:
            section (str): The section title
            item (str): The item text (empty for main section button)
            enabled (bool): Whether the item should be enabled
        """
        if section in self._sections:
            if item:
                self._sections[section].set_sub_button_enabled(item, enabled)
            else:
                self._sections[section].set_enabled(enabled)

    def is_section_enabled(self, section):
        """
        Check if a section is enabled.

        Args:
            section (str): The section title

        Returns:
            bool: True if the section is enabled, False otherwise
        """
        if section in self._sections:
            return self._sections[section].is_enabled()
        return False

    def is_item_enabled(self, section, item):
        """
        Check if a specific item is enabled.

        Args:
            section (str): The section title
            item (str): The item text (empty for main section button)

        Returns:
            bool: True if the item is enabled, False otherwise
        """
        if section in self._sections:
            if item:
                return self._sections[section].is_sub_button_enabled(item)
            else:
                return self._sections[section].is_enabled()
        return False
