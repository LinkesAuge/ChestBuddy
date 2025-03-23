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

from typing import List, Optional
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

from chestbuddy.ui.resources.style import Colors


class ActionCard(QFrame):
    """
    A card component for displaying actionable items in the dashboard.

    Attributes:
        action_clicked (Signal): Emitted when the card is clicked, with action name
        clicked (Signal): Emitted when the card is clicked (no parameters)

    Implementation Notes:
        - Card appears with shadow effect and rounded corners
        - Can be configured with title, description, icon and action
        - Provides visual feedback on hover
        - Supports custom tags for categorization
    """

    # Signals
    action_clicked = Signal(str)
    clicked = Signal()

    def __init__(
        self,
        title: str = "",
        description: str = "",
        icon_name: str = "",
        actions: list = None,
        tag: str = "",
        parent: Optional[QWidget] = None,
        # Backward compatibility parameters
        icon=None,
        action_callback=None,
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
            icon: QIcon object (backward compatibility)
            action_callback: Callback function (backward compatibility)
        """
        super().__init__(parent)

        # Store properties
        self._title = title
        self._description = description
        self._icon = icon  # Store the actual icon object

        # Handle icon_name vs icon parameter
        if icon is not None:
            self._icon_name = ""  # Use icon object instead of name
        else:
            self._icon_name = icon_name

        # Handle actions vs action_callback
        self._action_callback = action_callback
        if actions is not None:
            self._actions = actions
        elif action_callback is not None:
            # Create a default action name for the callback
            self._actions = ["default_action"]
        else:
            self._actions = []

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
        self.setStyleSheet(f"""
            #actionCard {{
                background-color: {Colors.PRIMARY};
                border-radius: 8px;
                border: 1px solid {Colors.BORDER};
            }}
            #actionCard:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                border: 1px solid {Colors.SECONDARY};
            }}
        """)

        # Apply drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Clear any existing layout
        if self.layout():
            # Remove old layout and its widgets
            old_layout = self.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        # Create layouts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Create icon and title layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Delete _icon_label attribute if it exists
        if hasattr(self, "_icon_label"):
            delattr(self, "_icon_label")

        # Icon handling - only create if we have an icon
        has_icon = (self._icon is not None and not self._icon.isNull()) or self._icon_name
        if has_icon:
            icon_label = QLabel()
            icon_label.setObjectName("actionCardIcon")

            if self._icon is not None and not self._icon.isNull():
                # Use the provided QIcon object
                icon_label.setPixmap(self._icon.pixmap(24, 24))
                header_layout.addWidget(icon_label)
            elif self._icon_name:
                # Use icon name
                icon = QIcon(f":/icons/{self._icon_name}.png")  # Adjust path as needed
                if not icon.isNull():
                    icon_label.setPixmap(icon.pixmap(24, 24))
                header_layout.addWidget(icon_label)

            # Only assign to self._icon_label if we have a valid icon
            if not (icon_label.pixmap() is None or icon_label.pixmap().isNull()):
                self._icon_label = icon_label

        # Create title label
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("actionCardTitle")
        self._title_label.setStyleSheet(f"""
            #actionCardTitle {{
                color: {Colors.TEXT_LIGHT};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        header_layout.addWidget(self._title_label, 1)
        main_layout.addLayout(header_layout)

        # Create description label if provided
        if self._description:
            self._description_label = QLabel(self._description)
            self._description_label.setObjectName("actionCardDescription")
            self._description_label.setStyleSheet(f"""
                #actionCardDescription {{
                    color: {Colors.TEXT_MUTED};
                    font-size: 13px;
                }}
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
            self._tag_label.setStyleSheet(f"""
                #actionCardTag {{
                    color: {Colors.TEXT_MUTED};
                    font-size: 11px;
                    background-color: {Colors.BG_MEDIUM};
                    border-radius: 4px;
                    padding: 2px 6px;
                }}
            """)
            tag_layout.addStretch()
            tag_layout.addWidget(self._tag_label)

            main_layout.addLayout(tag_layout)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumSize(180, 100)  # Changed to match expected values in tests
        self.setMaximumSize(300, 120)  # Changed to match expected values in tests

    def mousePressEvent(self, event):
        """
        Handle mouse press events to emit action signal.

        Args:
            event: The mouse event
        """
        if event.button() == Qt.LeftButton:
            self._use_count += 1

            # Handle action_callback if provided
            if self._action_callback is not None:
                self._action_callback()

            # Emit the primary action
            self.action_clicked.emit(self._primary_action)

            # Emit the clicked signal (no parameters)
            self.clicked.emit()

        super().mousePressEvent(event)

    # Getter/setter methods with distinct names
    def get_title(self) -> str:
        """Get the current title."""
        return self._title

    def set_title(self, title: str) -> None:
        """Set the title of the action card."""
        self._title = title
        self._title_label.setText(title)

    def get_description(self) -> str:
        """Get the current description."""
        return self._description

    def set_description(self, description: str) -> None:
        """Set the description of the action card."""
        self._description = description

        # Create or update description label
        if hasattr(self, "_description_label"):
            self._description_label.setText(description)
        else:
            # Create description label if it doesn't exist
            self._description_label = QLabel(description)
            self._description_label.setObjectName("actionCardDescription")
            self._description_label.setStyleSheet(f"""
                #actionCardDescription {{
                    color: {Colors.TEXT_MUTED};
                    font-size: 13px;
                }}
            """)
            self._description_label.setWordWrap(True)

            # Add to layout - need to rebuild layout
            self._setup_ui()

    def get_icon_name(self) -> str:
        """Get the current icon name."""
        return self._icon_name

    def set_icon_name(self, icon_name: str) -> None:
        """Set the icon name of the action card."""
        self._icon_name = icon_name
        self._icon = None  # Clear any icon object

        # Rebuild UI to update icon
        self._setup_ui()

    def get_icon(self):
        """Get the current icon."""
        if self._icon is not None:
            return self._icon
        elif self._icon_name:
            return QIcon(f":/icons/{self._icon_name}.png")
        else:
            return QIcon()  # Return a null icon

    def set_icon(self, icon) -> None:
        """Set the icon of the action card."""
        self._icon = icon
        self._icon_name = ""  # Clear icon name

        # Rebuild UI to update icon
        self._setup_ui()

    def get_actions(self) -> List[str]:
        """Get the current actions."""
        return self._actions

    def set_actions(self, actions: List[str]) -> None:
        """Set the actions associated with this card."""
        self._actions = actions
        self._primary_action = self._actions[0] if self._actions else ""

    def get_primary_action(self) -> str:
        """Get the primary action (first in the list)."""
        return self._primary_action

    def get_tag(self) -> str:
        """Get the current tag."""
        return self._tag

    def set_tag(self, tag: str) -> None:
        """Set the tag of the action card."""
        self._tag = tag

        # Rebuild UI to update tag
        self._setup_ui()

    def get_use_count(self) -> int:
        """Get the current use count."""
        return self._use_count

    def increment_use_count(self) -> None:
        """Increment the usage count of this action card."""
        self._use_count += 1

    def set_use_count(self, count: int) -> None:
        """Set the use count of the action card."""
        self._use_count = max(0, count)  # Ensure count is non-negative

    def is_compact(self) -> bool:
        """Get whether the card is in compact mode."""
        return False

    def is_clickable(self) -> bool:
        """Get whether the card is clickable."""
        return True

    # Method compatibility for tests
    def title(self) -> str:
        """Compatibility method for tests."""
        return self.get_title()

    def description(self) -> str:
        """Compatibility method for tests."""
        return self.get_description()

    def icon_name(self) -> str:
        """Compatibility method for tests."""
        return self.get_icon_name()

    def icon(self):
        """Compatibility method for tests."""
        return self.get_icon()

    def actions(self) -> List[str]:
        """Compatibility method for tests."""
        return self.get_actions()

    def primary_action(self) -> str:
        """Compatibility method for tests."""
        return self.get_primary_action()

    def tag(self) -> str:
        """Compatibility method for tests."""
        return self.get_tag()

    def use_count(self) -> int:
        """Compatibility method for tests."""
        return self.get_use_count()

    # Override QObject property methods
    def setProperty(self, name: str, value) -> bool:
        """Override setProperty for custom properties."""
        if name == "title":
            self.set_title(value)
            return True
        elif name == "description":
            self.set_description(value)
            return True
        elif name == "icon_name":
            self.set_icon_name(value)
            return True
        elif name == "tag":
            self.set_tag(value)
            return True

        # Call the parent class method for other properties
        return super().setProperty(name, value)

    def property(self, name: str):
        """Override property for custom properties."""
        if name == "title":
            return self.get_title()
        elif name == "description":
            return self.get_description()
        elif name == "icon_name":
            return self.get_icon_name()
        elif name == "tag":
            return self.get_tag()

        # Call the parent class method for other properties
        return super().property(name)

    # Define Qt properties - using different variable names to avoid conflicts
    titleProp = Property(str, get_title, set_title)
    descriptionProp = Property(str, get_description, set_description)
    icon_nameProp = Property(str, get_icon_name, set_icon_name)
    tagProp = Property(str, get_tag, set_tag)
