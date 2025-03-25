"""
sidebar_navigation.py

Description: Sidebar navigation widget for the application
Usage:
    sidebar = SidebarNavigation()
    sidebar.navigation_changed.connect(on_navigation_changed)
"""

import logging
from typing import Optional, Set, List

from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QSizePolicy,
    QLabel,
)
from PySide6.QtGui import QColor, QFont, QBrush

from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons

# Set up logger
logger = logging.getLogger(__name__)


class NavigationSection:
    """Constants for navigation sections."""

    DASHBOARD = "Dashboard"
    DATA = "Data"
    VALIDATION = "Validation"
    CORRECTION = "Correction"
    CHARTS = "Charts"
    REPORTS = "Reports"
    SETTINGS = "Settings"
    HELP = "Help"

    @classmethod
    def get_data_dependent_sections(cls) -> Set[str]:
        """Get sections that depend on data being loaded."""
        return {cls.VALIDATION, cls.CORRECTION, cls.CHARTS, cls.REPORTS}


class NavigationButton(QFrame):
    """A navigation button in the sidebar."""

    clicked = Signal(str)  # section name

    def __init__(self, name: str, icon_path: str, parent=None):
        """
        Initialize the navigation button.

        Args:
            name: Button name
            icon_path: Path to icon
            parent: Parent widget
        """
        super().__init__(parent)
        self._name = name
        self._icon_path = icon_path
        self._active = False
        self._enabled = True
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame properties
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setCursor(Qt.PointingHandCursor)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Create label
        self._label = QLabel(self._name)
        self._label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        icon = Icons.get_icon(self._icon_path, Colors.TEXT_LIGHT)
        self._label.setPixmap(icon.pixmap(16, 16))
        self._label.setText(f"  {self._name}")

        layout.addWidget(self._label)

        # Set initial style
        self._update_style()

    def _update_style(self):
        """Update the widget style based on state."""
        base_style = f"""
            QFrame {{
                border-radius: 4px;
                border: none;
                color: {Colors.TEXT_LIGHT};
                padding-left: 10px;
            }}
        """

        if not self._enabled:
            style = (
                base_style
                + f"""
                QFrame {{
                    background-color: transparent;
                    color: {Colors.TEXT_DISABLED};
                }}
            """
            )
            self.setCursor(Qt.ForbiddenCursor)
        elif self._active:
            style = (
                base_style
                + f"""
                QFrame {{
                    background-color: {Colors.PRIMARY_LIGHT};
                    border-left: 3px solid {Colors.ACCENT};
                }}
            """
            )
        else:
            style = (
                base_style
                + f"""
                QFrame {{
                    background-color: transparent;
                }}
                QFrame:hover {{
                    background-color: {Colors.PRIMARY};
                }}
            """
            )
            self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet(style)

        # Update font
        font = self._label.font()
        font.setItalic(not self._enabled)
        self._label.setFont(font)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if self._enabled and event.button() == Qt.LeftButton:
            self.clicked.emit(self._name)
        super().mousePressEvent(event)

    def set_active(self, active: bool):
        """
        Set whether this button is active.

        Args:
            active: Whether the button is active
        """
        if self._active != active:
            self._active = active
            self._update_style()

    def set_enabled(self, enabled: bool):
        """
        Set whether this button is enabled.

        Args:
            enabled: Whether the button is enabled
        """
        if self._enabled != enabled:
            self._enabled = enabled
            self._update_style()

            # Update text
            if not enabled:
                self._label.setText(f"  {self._name} ⊗")
            else:
                self._label.setText(f"  {self._name}")


class SidebarNavigation(QFrame):
    """
    Sidebar navigation widget for the ChestBuddy application.

    This widget provides navigation between different sections of the application.

    Signals:
        navigation_changed (str, str): Emitted when navigation changes.
            First parameter is the section, second is the optional subsection.
        data_dependent_view_clicked (str, str): Emitted when a data-dependent view is clicked
            without data loaded. First parameter is the view name, second is None.
    """

    navigation_changed = Signal(str, str)  # section, subsection
    data_dependent_view_clicked = Signal(str, str)  # section, subsection

    def __init__(self, parent=None):
        """
        Initialize the sidebar navigation.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        self._data_loaded = False
        self._active_item = ""
        self._view_availability = {}
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame properties
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"background-color: {Colors.PRIMARY_DARK};")
        self.setFixedWidth(180)

        # Create layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

        # Create logo/header
        logo_label = QLabel("ChestBuddy")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedHeight(50)
        logo_label.setStyleSheet(f"""
            background-color: {Colors.PRIMARY_DARK};
            color: {Colors.ACCENT};
            font-size: 16px;
            font-weight: bold;
            border-bottom: 1px solid {Colors.BORDER};
        """)
        self._layout.addWidget(logo_label)

        # Create navigation buttons
        self._sections = {}
        self._data_dependent_sections = NavigationSection.get_data_dependent_sections()

        # Add default sections
        self._add_section(NavigationSection.DASHBOARD, Icons.DASHBOARD)
        self._add_section(NavigationSection.DATA, Icons.DATA)
        self._add_section(NavigationSection.VALIDATION, Icons.VALIDATE)
        self._add_section(NavigationSection.CORRECTION, Icons.CORRECT)
        self._add_section(NavigationSection.CHARTS, Icons.CHART)
        self._add_section(NavigationSection.REPORTS, Icons.REPORT)
        self._add_section(NavigationSection.SETTINGS, Icons.SETTINGS)
        self._add_section(NavigationSection.HELP, Icons.HELP)

        # Add stretch to push sections to the top
        self._layout.addStretch()

    def _connect_signals(self):
        """Connect signals to slots."""
        # Connect section button signals
        for section_name, section in self._sections.items():
            section.clicked.connect(self._on_section_clicked)

    def _add_section(self, name: str, icon_path: str):
        """
        Add a navigation section.

        Args:
            name: Section name
            icon_path: Path to icon
        """
        section = NavigationButton(name, icon_path, self)
        section.clicked.connect(self._on_section_clicked)

        self._layout.addWidget(section)
        self._sections[name] = section

        # If data-dependent, initially disable
        if name in self._data_dependent_sections:
            section.set_enabled(self._data_loaded)

    def _on_section_clicked(self, section_name: str):
        """
        Handle section click event.

        Args:
            section_name: Name of the clicked section
        """
        # Check if navigation to the section is allowed
        if section_name in self._view_availability and not self._view_availability[section_name]:
            # Check if it's a data-dependent section
            if section_name in self._data_dependent_sections:
                logger.info(f"Data-dependent section {section_name} clicked, but not available")
                self.data_dependent_view_clicked.emit(section_name, None)
            return

        # Set as active and emit signal
        self.set_active_item(section_name)
        self.navigation_changed.emit(section_name, None)

    @Slot(str)
    def set_active_item(self, section_name: str):
        """
        Set the active section.

        Args:
            section_name: Name of the section to activate
        """
        if section_name not in self._sections:
            logger.warning(f"Attempted to set unknown section as active: {section_name}")
            return

        # Deactivate current active item
        if self._active_item and self._active_item in self._sections:
            self._sections[self._active_item].set_active(False)

        # Set new active item
        self._active_item = section_name
        self._sections[section_name].set_active(True)

    @Slot(bool)
    def set_data_loaded(self, has_data: bool):
        """
        Set whether data is loaded.

        Args:
            has_data (bool): Whether data is currently loaded
        """
        if self._data_loaded == has_data:
            return

        self._data_loaded = has_data

        for section_name in self._data_dependent_sections:
            section = self._sections.get(section_name)
            if section:
                section.set_enabled(has_data)

    @Slot(dict)
    def update_view_availability(self, availability: dict):
        """
        Update the availability of views.

        Args:
            availability: Dict mapping view names to availability (bool).
        """
        self._view_availability = availability

        # Update UI for each section
        for section_name, section in self._sections.items():
            if section_name in availability:
                section.set_enabled(availability[section_name])
