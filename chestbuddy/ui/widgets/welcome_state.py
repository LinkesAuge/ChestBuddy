"""
welcome_state.py

Description: A specialized widget for welcoming first-time users
Usage:
    welcome = WelcomeStateWidget()
    welcome.welcome_action_clicked.connect(self._on_welcome_action)
"""

from typing import Optional, Callable, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QFrame,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap

from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget
from chestbuddy.ui.resources.colors import Colors
from chestbuddy.ui.resources.icons import IconProvider


class WelcomeStateWidget(QWidget):
    """
    A widget for welcoming first-time users with a multi-step guide.

    This widget extends the functionality of EmptyStateWidget by adding
    a multi-step guide for new users and a checkbox to disable the welcome
    screen in future sessions.

    Attributes:
        welcome_action_clicked: Signal emitted when a welcome action is clicked
        dont_show_again_changed: Signal emitted when the "Don't show again" checkbox is toggled
    """

    # Signals
    welcome_action_clicked = Signal(str)  # Action name
    dont_show_again_changed = Signal(bool)  # Checkbox state

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the welcome state widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize state
        self._current_step = 0
        self._steps = []

        # Set up the UI
        self._setup_ui()
        self._setup_guides()
        self._setup_connections()

        # Initial update
        self._update_step()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(24, 24, 24, 24)
        self._main_layout.setSpacing(16)

        # Welcome header
        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.setSpacing(16)

        # Logo/icon
        self._logo_label = QLabel()
        pixmap = IconProvider.get_icon("app_logo").pixmap(QSize(64, 64))
        self._logo_label.setPixmap(pixmap)
        self._header_layout.addWidget(self._logo_label)

        # Title and subtitle
        self._title_layout = QVBoxLayout()
        self._title_layout.setContentsMargins(0, 0, 0, 0)
        self._title_layout.setSpacing(4)

        self._title_label = QLabel("Welcome to ChestBuddy")
        self._title_label.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {Colors.TEXT_DARK};"
        )
        self._title_layout.addWidget(self._title_label)

        self._subtitle_label = QLabel("Let's get you started with managing your chest data")
        self._subtitle_label.setStyleSheet(f"font-size: 16px; color: {Colors.TEXT_MEDIUM};")
        self._title_layout.addWidget(self._subtitle_label)

        self._header_layout.addLayout(self._title_layout)
        self._header_layout.addStretch()

        self._main_layout.addLayout(self._header_layout)

        # Separator
        self._separator = QFrame()
        self._separator.setFrameShape(QFrame.HLine)
        self._separator.setFrameShadow(QFrame.Sunken)
        self._separator.setStyleSheet(f"background-color: {Colors.BORDER};")
        self._main_layout.addWidget(self._separator)

        # Guide container
        self._guide_container = QFrame()
        self._guide_container.setObjectName("guideContainer")
        self._guide_container.setStyleSheet(f"""
            #guideContainer {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border-radius: 8px;
                border: 1px solid {Colors.BORDER};
            }}
        """)

        self._guide_layout = QVBoxLayout(self._guide_container)
        self._guide_layout.setContentsMargins(16, 16, 16, 16)
        self._guide_layout.setSpacing(16)

        # Guide content (filled dynamically)
        self._guide_title = QLabel()
        self._guide_title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {Colors.TEXT_DARK};"
        )
        self._guide_layout.addWidget(self._guide_title)

        self._guide_description = QLabel()
        self._guide_description.setWordWrap(True)
        self._guide_description.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_MEDIUM};")
        self._guide_layout.addWidget(self._guide_description)

        # Action button
        self._action_button = QPushButton()
        self._action_button.setMinimumHeight(36)
        self._action_button.setCursor(Qt.PointingHandCursor)
        self._action_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARKER};
            }}
        """)
        self._guide_layout.addWidget(self._action_button)

        # Step indicators
        self._steps_layout = QHBoxLayout()
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(8)
        self._steps_layout.setAlignment(Qt.AlignCenter)

        # Steps will be added dynamically
        self._step_indicators = []

        self._guide_layout.addLayout(self._steps_layout)
        self._main_layout.addWidget(self._guide_container)

        # Navigation buttons
        self._nav_layout = QHBoxLayout()
        self._nav_layout.setContentsMargins(0, 8, 0, 0)
        self._nav_layout.setSpacing(8)

        # Don't show again checkbox
        self._dont_show_checkbox = QCheckBox("Don't show this welcome screen again")
        self._dont_show_checkbox.setStyleSheet(f"color: {Colors.TEXT_MEDIUM};")
        self._nav_layout.addWidget(self._dont_show_checkbox)

        self._nav_layout.addStretch()

        # Previous button
        self._prev_button = QPushButton("Previous")
        self._prev_button.setMinimumHeight(36)
        self._prev_button.setCursor(Qt.PointingHandCursor)
        self._prev_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SECONDARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.SECONDARY_DARKER};
            }}
            QPushButton:disabled {{
                background-color: {Colors.DISABLED};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
        self._nav_layout.addWidget(self._prev_button)

        # Next button
        self._next_button = QPushButton("Next")
        self._next_button.setMinimumHeight(36)
        self._next_button.setCursor(Qt.PointingHandCursor)
        self._next_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARKER};
            }}
        """)
        self._nav_layout.addWidget(self._next_button)

        self._main_layout.addLayout(self._nav_layout)

    def _setup_guides(self) -> None:
        """Set up the multi-step guide content."""
        self._steps = [
            {
                "title": "Import Your Data",
                "description": "Start by importing your chest data from CSV files. "
                "You can import multiple files at once for bulk processing.",
                "action_text": "Import Data",
                "action_name": "import_data",
                "action_icon": "import",
            },
            {
                "title": "Validate Your Data",
                "description": "After importing, validate your data against known player names, "
                "chest types, and locations to ensure accuracy.",
                "action_text": "Learn About Validation",
                "action_name": "show_validation",
                "action_icon": "validate",
            },
            {
                "title": "Analyze Your Results",
                "description": "View charts and statistics to gain insights from your data. "
                "Identify trends and make better gameplay decisions.",
                "action_text": "View Analytics",
                "action_name": "show_analytics",
                "action_icon": "chart",
            },
            {
                "title": "Generate Reports",
                "description": "Create and share reports with your alliance members. "
                "Export data in various formats for further analysis.",
                "action_text": "Create Report",
                "action_name": "create_report",
                "action_icon": "report",
            },
        ]

        # Create step indicators
        for i in range(len(self._steps)):
            indicator = QFrame()
            indicator.setFixedSize(10, 10)
            indicator.setStyleSheet(f"""
                background-color: {Colors.BORDER};
                border-radius: 5px;
            """)
            self._step_indicators.append(indicator)
            self._steps_layout.addWidget(indicator)

    def _setup_connections(self) -> None:
        """Set up signal/slot connections."""
        self._prev_button.clicked.connect(self._on_prev_clicked)
        self._next_button.clicked.connect(self._on_next_clicked)
        self._action_button.clicked.connect(self._on_action_clicked)
        self._dont_show_checkbox.stateChanged.connect(self._on_dont_show_changed)

    def _update_step(self) -> None:
        """Update the UI to reflect the current step."""
        if not self._steps or self._current_step >= len(self._steps):
            return

        # Get current step data
        step = self._steps[self._current_step]

        # Update title and description
        self._guide_title.setText(step["title"])
        self._guide_description.setText(step["description"])

        # Update action button
        self._action_button.setText(step["action_text"])
        if "action_icon" in step:
            self._action_button.setIcon(IconProvider.get_icon(step["action_icon"]))

        # Update step indicators
        for i, indicator in enumerate(self._step_indicators):
            if i == self._current_step:
                indicator.setStyleSheet(f"""
                    background-color: {Colors.PRIMARY};
                    border-radius: 5px;
                """)
            else:
                indicator.setStyleSheet(f"""
                    background-color: {Colors.BORDER};
                    border-radius: 5px;
                """)

        # Update nav buttons
        self._prev_button.setEnabled(self._current_step > 0)

        if self._current_step == len(self._steps) - 1:
            self._next_button.setText("Finish")
        else:
            self._next_button.setText("Next")

    def _on_prev_clicked(self) -> None:
        """Handle previous button click."""
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step()

    def _on_next_clicked(self) -> None:
        """Handle next button click."""
        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self._update_step()
        else:
            # This is the last step, finish the welcome process
            self.welcome_action_clicked.emit("welcome_complete")

    def _on_action_clicked(self) -> None:
        """Handle action button click."""
        if self._current_step < len(self._steps):
            action_name = self._steps[self._current_step]["action_name"]
            self.welcome_action_clicked.emit(action_name)

    def _on_dont_show_changed(self, state: int) -> None:
        """
        Handle "Don't show again" checkbox state change.

        Args:
            state: Checkbox state (Qt.Checked or Qt.Unchecked)
        """
        self.dont_show_again_changed.emit(state == Qt.Checked)

    def get_dont_show_again(self) -> bool:
        """
        Get the state of the "Don't show again" checkbox.

        Returns:
            True if the checkbox is checked, False otherwise
        """
        return self._dont_show_checkbox.isChecked()

    def set_current_step(self, step: int) -> None:
        """
        Set the current step of the guide.

        Args:
            step: Step index (0-based)
        """
        if 0 <= step < len(self._steps):
            self._current_step = step
            self._update_step()
