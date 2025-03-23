"""
action_card.py

Description: Card component for displaying interactive action buttons in the dashboard
Usage:
    action_card = ActionCard(
        "Import Files",
        "Import CSV files with chest data",
        "import",
        ["import_csv", "import_excel"]
    )
    action_card.action_clicked.connect(handle_action)
"""

from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QPushButton,
)


class ActionCard(QFrame):
    """
    A card component for displaying actionable items in the dashboard.

    Attributes:
        action_clicked (Signal): Emitted when the card is clicked, with action name

    Implementation Notes:
        - Card appears with shadow effect and rounded corners
        - Can be configured with title, description, icon and action
        - Provides visual feedback on hover
        - Supports custom tags for categorization
    """

    # Signal emitted when the action is clicked
    action_clicked = Signal(str)

    def __init__(
        self,
        title: str = "",
        description: str = "",
        icon_name: str = "",
        actions: list = None,
        tag: str = "",
        parent: QWidget = None,
    ):
        """
        Initialize the action card with title, description, and icon.

        Args:
            title (str): The title of the action
            description (str): Short description of the action
            icon_name (str): Name of the icon to display
            actions (list): List of action names associated with this card
            tag (str): Optional tag for categorization
            parent (QWidget): Parent widget
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._description = description
        self._icon_name = icon_name
        self._actions = actions or []
        self._primary_action = self._actions[0] if self._actions else ""
        self._tag = tag
        self._use_count = 0  # Track how often this action is used

        # Setup UI
        self._setup_ui()

        # Set up interaction
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def _setup_ui(self):
        """Set up the UI components of the action card."""
        # Set frame styling
        self.setObjectName("actionCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            #actionCard {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            #actionCard:hover {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
            }
        """)

        # Apply drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Create layouts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Create icon and title layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Icon (if provided)
        if self._icon_name:
            self._icon_label = QLabel()
            self._icon_label.setObjectName("actionCardIcon")
            # Placeholder for actual icon loading
            icon = QIcon(f":/icons/{self._icon_name}.png")  # Adjust path as needed
            if not icon.isNull():
                self._icon_label.setPixmap(icon.pixmap(24, 24))
            header_layout.addWidget(self._icon_label)

        # Create title label
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("actionCardTitle")
        self._title_label.setStyleSheet("""
            #actionCardTitle {
                color: #333333;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        header_layout.addWidget(self._title_label, 1)
        main_layout.addLayout(header_layout)

        # Create description label if provided
        if self._description:
            self._description_label = QLabel(self._description)
            self._description_label.setObjectName("actionCardDescription")
            self._description_label.setStyleSheet("""
                #actionCardDescription {
                    color: #585858;
                    font-size: 13px;
                }
            """)
            self._description_label.setWordWrap(True)
            main_layout.addWidget(self._description_label)

        # Add spacer to push content to the top
        main_layout.addStretch()

        # Add tag if provided
        if self._tag:
            tag_layout = QHBoxLayout()
            tag_layout.setContentsMargins(0, 8, 0, 0)

            self._tag_label = QLabel(self._tag)
            self._tag_label.setObjectName("actionCardTag")
            self._tag_label.setStyleSheet("""
                #actionCardTag {
                    color: #757575;
                    font-size: 11px;
                    background-color: #f0f0f0;
                    border-radius: 4px;
                    padding: 2px 6px;
                }
            """)
            tag_layout.addStretch()
            tag_layout.addWidget(self._tag_label)

            main_layout.addLayout(tag_layout)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumSize(180, 120)
        self.setMaximumSize(300, 180)

    def mousePressEvent(self, event):
        """
        Handle mouse press events to emit action signal.

        Args:
            event: The mouse event
        """
        if event.button() == Qt.LeftButton:
            self._use_count += 1
            # Emit the primary action
            self.action_clicked.emit(self._primary_action)
        super().mousePressEvent(event)

    def set_title(self, title: str):
        """
        Set the title of the action card.

        Args:
            title (str): The new title
        """
        self._title = title
        self._title_label.setText(title)

    def title(self) -> str:
        """
        Get the current title.

        Returns:
            str: The current title
        """
        return self._title

    def set_description(self, description: str):
        """
        Set the description of the action card.

        Args:
            description (str): The new description
        """
        self._description = description

        # Create or update description label
        if hasattr(self, "_description_label"):
            self._description_label.setText(description)
        else:
            # Create description label if it doesn't exist
            self._description_label = QLabel(description)
            self._description_label.setObjectName("actionCardDescription")
            self._description_label.setStyleSheet("""
                #actionCardDescription {
                    color: #585858;
                    font-size: 13px;
                }
            """)
            self._description_label.setWordWrap(True)

            # Add to layout - need to rebuild layout
            self._setup_ui()

    def description(self) -> str:
        """
        Get the current description.

        Returns:
            str: The current description
        """
        return self._description

    def set_icon_name(self, icon_name: str):
        """
        Set the icon name of the action card.

        Args:
            icon_name (str): The new icon name
        """
        self._icon_name = icon_name

        # Rebuild UI to update icon
        self._setup_ui()

    def icon_name(self) -> str:
        """
        Get the current icon name.

        Returns:
            str: The current icon name
        """
        return self._icon_name

    def set_actions(self, actions: list):
        """
        Set the actions associated with this card.

        Args:
            actions (list): List of action names
        """
        self._actions = actions
        self._primary_action = self._actions[0] if self._actions else ""

    def actions(self) -> list:
        """
        Get the current actions.

        Returns:
            list: The current actions
        """
        return self._actions

    def primary_action(self) -> str:
        """
        Get the primary action (first in the list).

        Returns:
            str: The primary action
        """
        return self._primary_action

    def set_tag(self, tag: str):
        """
        Set the tag of the action card.

        Args:
            tag (str): The new tag
        """
        self._tag = tag

        # Rebuild UI to update tag
        self._setup_ui()

    def tag(self) -> str:
        """
        Get the current tag.

        Returns:
            str: The current tag
        """
        return self._tag

    def increment_use_count(self):
        """Increment the usage count of this action card."""
        self._use_count += 1

    def use_count(self) -> int:
        """
        Get the current use count.

        Returns:
            int: The current use count
        """
        return self._use_count

    def set_use_count(self, count: int):
        """
        Set the use count of the action card.

        Args:
            count (int): The new use count
        """
        self._use_count = max(0, count)  # Ensure count is non-negative

    # Define Qt properties
    title = Property(str, title, set_title)
    description = Property(str, description, set_description)
    icon_name = Property(str, icon_name, set_icon_name)
    tag = Property(str, tag, set_tag)
