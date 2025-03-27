"""
sidebar_navigation.py

Description: Sidebar navigation widget for the application
Usage:
    sidebar = SidebarNavigation()
    sidebar.navigation_changed.connect(on_navigation_changed)
"""

import logging
import time
from typing import Optional, Set, List, Any, Dict

from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QSizePolicy,
    QLabel,
    QHBoxLayout,
)
from PySide6.QtGui import QColor, QFont, QBrush

from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons
from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.utils import get_update_manager

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
    """
    A button for the navigation sidebar.

    This button contains an icon and a text label and can be in an active,
    disabled or normal state with appropriate visual styling.
    """

    clicked = Signal()

    def __init__(
        self, text: str, icon_path: Optional[str] = None, parent: Optional[QWidget] = None
    ):
        """Initialize a new navigation button."""
        super().__init__(parent)
        self._text = text
        self._icon_path = icon_path
        self._is_active = False
        self._is_enabled = True
        self._is_hovered = False

        # Create widgets and layout
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        # Set frame properties
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setCursor(Qt.PointingHandCursor)

        # Create the main horizontal layout
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Indicator widget at left edge (vertical colored bar)
        self._indicator = QFrame(self)
        self._indicator.setFrameShape(QFrame.NoFrame)
        self._indicator.setFixedWidth(4)  # Increase indicator width for better visibility
        self._main_layout.addWidget(self._indicator)

        # Content widget containing icon and text
        self._content = QFrame(self)
        self._content.setFrameShape(QFrame.NoFrame)
        content_layout = QHBoxLayout(self._content)
        content_layout.setContentsMargins(12, 10, 12, 10)  # Increase vertical padding
        content_layout.setSpacing(10)  # Increase spacing between icon and text

        # Icon and label
        self._icon = None  # Initialize as None to check later
        if self._icon_path:
            try:
                self._icon = QLabel(self)
                self._icon.setFixedSize(22, 22)  # Slightly larger icons
                self._update_icon()
                content_layout.addWidget(self._icon)
            except Exception as e:
                # If icon loading fails, log it and continue without the icon
                logger.warning(f"Failed to load icon {self._icon_path}: {str(e)}")
                self._icon = None

        self._label = QLabel(self._text, self)
        content_layout.addWidget(self._label)
        content_layout.addStretch()

        self._main_layout.addWidget(self._content, 1)

        # Initial styling
        self._update_style()

    def _update_icon(self):
        """Update the icon based on the current state."""
        if not self._icon or not self._icon_path:
            return

        try:
            # Use appropriate color based on state
            if not self._is_enabled:
                color = Colors.TEXT_DISABLED
            elif self._is_active:
                color = Colors.SECONDARY  # Use accent gold color for active icons
            else:
                color = Colors.TEXT_LIGHT  # Use light color for better visibility

            icon = Icons.get_icon(self._icon_path, color)
            if not icon.isNull():
                self._icon.setPixmap(icon.pixmap(22, 22))  # Match the size with _setup_ui
            else:
                # Hide the icon if it couldn't be loaded
                self._icon.hide()
        except Exception as e:
            # If icon update fails, hide the icon
            logger.warning(f"Failed to update icon {self._icon_path}: {str(e)}")
            self._icon.hide()

    def _update_style(self):
        """Update the styling based on the current state."""
        # First reset all styling to avoid inheritance issues
        self.setStyleSheet("")
        self._indicator.setStyleSheet("")
        self._content.setStyleSheet("")
        self._label.setStyleSheet("")

        if self._icon:
            self._icon.setStyleSheet("")

        # Base style for all states (with explicit border clearing)
        self.setStyleSheet("""
            border: none;
            background-color: transparent;
        """)

        # Base content style with more padding to make items more distinct
        # Use padding to ensure the background extends to the full width
        content_style = f"""
            background-color: transparent;
            border: none;
            border-left: none;
            border-right: none;
            border-bottom: 1px solid {Colors.PRIMARY_LIGHT};
            padding: 6px 0px; /* Vertical padding only, let layout handle horizontal */
            margin: 0px;
        """

        # Use light text color for better visibility on dark background
        label_style = f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 15px;
            border: none;
            background-color: transparent;
        """

        # Ensure the indicator has no background initially
        indicator_style = """
            background-color: transparent;
            border: none;
        """

        # Apply specific styling based on state
        if not self._is_enabled:
            # Disabled state
            label_style = f"""
                color: {Colors.TEXT_DISABLED};
                font-size: 15px;
                border: none;
                background-color: transparent;
            """

        elif self._is_active:
            # Active state - highlighted with gold color and bolder font
            # Always use the hover background color for active items
            content_style = f"""
                background-color: {Colors.PRIMARY_HOVER};
                border: none;
                border-left: none;
                border-right: none;
                border-bottom: 1px solid {Colors.PRIMARY_LIGHT};
                padding: 6px 0px; /* Vertical padding only, let layout handle horizontal */
                margin: 0px;
            """

            indicator_style = f"""
                background-color: {Colors.SECONDARY};
                border: none;
            """

            # Make active label bold and slightly larger
            label_style = f"""
                color: {Colors.SECONDARY};
                font-size: 16px;
                font-weight: bold;
                border: none;
                background-color: transparent;
            """

        elif self._is_hovered:
            # Hover state
            content_style = f"""
                background-color: {Colors.PRIMARY_HOVER};
                border: none; 
                border-left: none;
                border-right: none;
                border-bottom: 1px solid {Colors.PRIMARY_LIGHT};
                padding: 6px 0px; /* Vertical padding only, let layout handle horizontal */
                margin: 0px;
            """

            indicator_style = f"""
                background-color: {Colors.PRIMARY_LIGHT};
                border: none;
            """

        # Apply the styles explicitly
        self._indicator.setStyleSheet(indicator_style)
        self._content.setStyleSheet(content_style)
        self._label.setStyleSheet(label_style)

        # Update icon color if needed
        self._update_icon()

    def text(self) -> str:
        """Get the button text."""
        return self._text

    def set_active(self, active: bool):
        """Set whether this button is active."""
        if self._is_active != active:
            self._is_active = active
            self._update_style()

    def is_active(self) -> bool:
        """Check if this button is active."""
        return self._is_active

    def set_enabled(self, enabled: bool):
        """Set whether this button is enabled."""
        if self._is_enabled != enabled:
            self._is_enabled = enabled
            self.setEnabled(enabled)
            self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
            self._update_style()

    def is_enabled(self) -> bool:
        """Check if this button is enabled."""
        return self._is_enabled

    # Event handling methods
    def enterEvent(self, event):
        """Handle mouse enter events."""
        if self._is_enabled:
            self._is_hovered = True
            self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton and self._is_enabled:
            self.clicked.emit()
        super().mousePressEvent(event)


class SidebarNavigation(QFrame):
    """
    Sidebar navigation widget for the ChestBuddy application.

    This widget provides navigation between different sections of the application
    and implements the IUpdatable interface for standardized updates.

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

        # Initialize update state tracking
        self._update_state = {
            "last_update_time": 0.0,
            "needs_update": True,
            "update_pending": False,
            "data_hash": None,
            "initial_population": False,
        }

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
        self._layout.setSpacing(
            0
        )  # No spacing between items - separation handled by items themselves

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
            section.clicked.connect(
                lambda checked=False, name=section_name: self._on_section_clicked(name)
            )

    def _add_section(self, name: str, icon_path: str):
        """
        Add a navigation section.

        Args:
            name: Section name
            icon_path: Path to icon
        """
        section = NavigationButton(name, icon_path, self)
        # Connection happens in _connect_signals

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

        # Mark as needing update
        self._update_state["needs_update"] = True

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

        # Request update via UpdateManager
        self._update_state["needs_update"] = True
        self.schedule_update()

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

        # Request update via UpdateManager
        self._update_state["needs_update"] = True
        self.schedule_update()

    # IUpdatable interface implementation

    def refresh(self) -> None:
        """
        Refresh the sidebar display with current data.
        """
        self._update_state["needs_update"] = True
        self._refresh_view_content()
        self._update_state["last_update_time"] = time.time()
        logger.debug(f"SidebarNavigation refreshed")

    def update(self, data: Optional[Any] = None) -> None:
        """
        Update the sidebar with new data.

        Args:
            data: Optional new data (unused in this implementation)
        """
        if not self.needs_update():
            logger.debug(f"SidebarNavigation skipping update (no change detected)")
            return

        self._update_state["needs_update"] = True
        self._update_state["update_pending"] = True

        try:
            self._update_view_content(data)
            self._update_state["needs_update"] = False
            self._update_state["update_pending"] = False
            self._update_state["last_update_time"] = time.time()
            logger.debug(f"SidebarNavigation updated")
        except Exception as e:
            self._update_state["update_pending"] = False
            logger.error(f"Error updating SidebarNavigation: {str(e)}")
            raise

    def populate(self, data: Optional[Any] = None) -> None:
        """
        Completely populate the sidebar from scratch.

        Args:
            data: Optional data to populate with (unused in this implementation)
        """
        self._update_state["needs_update"] = True
        self._update_state["update_pending"] = True

        try:
            self._populate_view_content(data)
            self._update_state["needs_update"] = False
            self._update_state["update_pending"] = False
            self._update_state["initial_population"] = True
            self._update_state["last_update_time"] = time.time()
            logger.debug(f"SidebarNavigation populated")
        except Exception as e:
            self._update_state["update_pending"] = False
            logger.error(f"Error populating SidebarNavigation: {str(e)}")
            raise

    def needs_update(self) -> bool:
        """
        Check if the sidebar needs an update.

        Returns:
            bool: True if the sidebar needs to be updated, False otherwise
        """
        return self._update_state["needs_update"]

    def reset(self) -> None:
        """
        Reset the sidebar to its initial state.
        """
        self._update_state["needs_update"] = True
        self._update_state["update_pending"] = True

        try:
            self._reset_view_content()
            self._update_state["needs_update"] = False
            self._update_state["update_pending"] = False
            self._update_state["initial_population"] = False
            self._update_state["last_update_time"] = time.time()
            logger.debug(f"SidebarNavigation reset")
        except Exception as e:
            self._update_state["update_pending"] = False
            logger.error(f"Error resetting SidebarNavigation: {str(e)}")
            raise

    def last_update_time(self) -> float:
        """
        Get the timestamp of the last update.

        Returns:
            float: Timestamp of the last update (seconds since epoch)
        """
        return self._update_state["last_update_time"]

    def schedule_update(self, debounce_ms: int = 50) -> None:
        """
        Schedule an update using the UpdateManager.

        Args:
            debounce_ms: Debounce interval in milliseconds
        """
        try:
            update_manager = get_update_manager()
            update_manager.schedule_update(self, debounce_ms)
            logger.debug(f"SidebarNavigation scheduled for update")
        except Exception as e:
            logger.error(f"Error scheduling update for SidebarNavigation: {e}")
            # Fall back to direct update if UpdateManager is not available
            self.update()

    # Internal implementation methods for IUpdatable

    def _update_view_content(self, data: Optional[Any] = None) -> None:
        """
        Update the sidebar content based on provided data.

        Args:
            data: Optional data to update with (unused in this implementation)
        """
        # In sidebar, update is primarily about reflecting availability
        if hasattr(self, "_view_availability"):
            # Apply view availability without triggering a new update
            for section_name, section in self._sections.items():
                if section_name in self._view_availability:
                    section.set_enabled(self._view_availability[section_name])

    def _refresh_view_content(self) -> None:
        """
        Refresh the sidebar content without changing underlying data.
        """
        # For sidebar, refresh just updates the current active item
        if hasattr(self, "_active_item") and self._active_item:
            # Refresh active state without triggering a new update
            for section_name, section in self._sections.items():
                section.set_active(section_name == self._active_item)

    def _populate_view_content(self, data: Optional[Any] = None) -> None:
        """
        Populate the sidebar content from scratch.

        Args:
            data: Optional data to populate with (unused in this implementation)
        """
        # For the sidebar, population happens during initialization,
        # so this is primarily about refreshing the entire state

        # Apply all current state without triggering new updates

        # Apply data loaded state
        for section_name in self._data_dependent_sections:
            section = self._sections.get(section_name)
            if section:
                section.set_enabled(self._data_loaded)

        # Apply view availability
        for section_name, section in self._sections.items():
            if section_name in self._view_availability:
                section.set_enabled(self._view_availability[section_name])

        # Apply active item
        if self._active_item:
            for section_name, section in self._sections.items():
                section.set_active(section_name == self._active_item)

    def _reset_view_content(self) -> None:
        """
        Reset the sidebar content to its initial state.
        """
        # Reset to initial state (no data, dashboard active)
        self._data_loaded = False
        self._active_item = "Dashboard"
        self._view_availability = {}

        # Update UI to reflect reset state
        for section_name in self._data_dependent_sections:
            section = self._sections.get(section_name)
            if section:
                section.set_enabled(False)

        # Set Dashboard as active
        for section_name, section in self._sections.items():
            section.set_active(section_name == "Dashboard")
