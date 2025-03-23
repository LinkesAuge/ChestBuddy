"""
action_toolbar.py

Description: A toolbar for organizing action buttons in ChestBuddy
Usage:
    toolbar = ActionToolbar()
    toolbar.add_button(ActionButton("Import"))
    toolbar.add_button(ActionButton("Export"))

    # With groups
    toolbar.start_group("Data")
    toolbar.add_button(ActionButton("Import"))
    toolbar.add_button(ActionButton("Export"))
    toolbar.end_group()

    toolbar.start_group("Analysis")
    toolbar.add_button(ActionButton("Validate"))
    toolbar.add_button(ActionButton("Correct"))
    toolbar.end_group()
"""

from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QLabel,
    QSizePolicy,
    QSpacerItem,
)

from chestbuddy.ui.widgets.action_button import ActionButton


class ActionToolbar(QWidget):
    """
    A toolbar widget that organizes ActionButtons into groups.

    Provides layout management for action buttons with proper spacing,
    grouping, and alignment options.

    Attributes:
        _buttons (List[ActionButton]): List of buttons added to the toolbar
        _groups (Dict[str, List[ActionButton]]): Dictionary of button groups
        _current_group (str): Name of the current group being built
        _has_separators (List[bool]): Tracks whether separators exist after buttons
        _layout (QHBoxLayout): Main layout for the toolbar
    """

    def __init__(self, parent=None, spacing: int = 6, vertical: bool = False):
        """
        Initialize a new ActionToolbar.

        Args:
            parent: Parent widget
            spacing (int): Spacing between buttons in pixels
            vertical (bool): If True, arranges buttons vertically instead of horizontally
        """
        super().__init__(parent)

        # Initialize properties
        self._buttons: List[ActionButton] = []
        self._groups: Dict[str, List[ActionButton]] = {}
        self._current_group: Optional[str] = None
        self._has_separators: List[bool] = []
        self._vertical = vertical

        # Create layout
        if vertical:
            self._layout = QVBoxLayout(self)
        else:
            self._layout = QHBoxLayout(self)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(spacing)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def add_button(self, button: ActionButton) -> None:
        """
        Add a button to the toolbar.

        Args:
            button (ActionButton): The button to add
        """
        self._buttons.append(button)
        self._layout.addWidget(button)
        self._has_separators.append(False)

        # Add to current group if one is active
        if self._current_group:
            if self._current_group not in self._groups:
                self._groups[self._current_group] = []
            self._groups[self._current_group].append(button)

    def remove_button(self, button: ActionButton) -> bool:
        """
        Remove a button from the toolbar.

        Args:
            button (ActionButton): The button to remove

        Returns:
            bool: True if button was found and removed, False otherwise
        """
        if button in self._buttons:
            idx = self._buttons.index(button)
            self._buttons.pop(idx)
            self._has_separators.pop(idx)

            # Remove from layout
            self._layout.removeWidget(button)
            button.setParent(None)

            # Remove from any groups
            for group_name, group_buttons in self._groups.items():
                if button in group_buttons:
                    group_buttons.remove(button)

            return True
        return False

    def count(self) -> int:
        """
        Get the number of buttons in the toolbar.

        Returns:
            int: Number of buttons
        """
        return len(self._buttons)

    def group_count(self) -> int:
        """
        Get the number of button groups.

        Returns:
            int: Number of groups
        """
        return len(self._groups)

    def get_button(self, index: int) -> Optional[ActionButton]:
        """
        Get a button by its index.

        Args:
            index (int): Button index

        Returns:
            Optional[ActionButton]: The button at the specified index or None if index is out of range
        """
        if 0 <= index < len(self._buttons):
            return self._buttons[index]
        return None

    def get_button_by_name(self, name: str) -> Optional[ActionButton]:
        """
        Get a button by its name.

        Args:
            name (str): Button name

        Returns:
            Optional[ActionButton]: The button with the specified name or None if not found
        """
        for button in self._buttons:
            if button.name() == name:
                return button
        return None

    def get_buttons_in_group(self, group_name: str) -> List[ActionButton]:
        """
        Get all buttons in a specific group.

        Args:
            group_name (str): Name of the group

        Returns:
            List[ActionButton]: List of buttons in the group, or empty list if group not found
        """
        return self._groups.get(group_name, [])

    def start_group(self, group_name: str) -> None:
        """
        Start a new button group. All buttons added after this call
        until end_group() is called will be part of this group.

        Args:
            group_name (str): Name of the group
        """
        # If there's at least one button already, add a separator before starting a new group
        if self._buttons and not self._vertical:
            # Add visual separator line
            separator = QFrame(self)
            separator.setFrameShape(QFrame.VLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setFixedWidth(1)
            self._layout.addWidget(separator)

            # Mark the last button as having a separator after it
            if self._has_separators:
                self._has_separators[-1] = True

        self._current_group = group_name
        if group_name not in self._groups:
            self._groups[group_name] = []

    def end_group(self) -> None:
        """End the current button group."""
        self._current_group = None

    def has_separator_after(self, index: int) -> bool:
        """
        Check if there's a separator after the button at the specified index.

        Args:
            index (int): Button index

        Returns:
            bool: True if there's a separator after the button, False otherwise
        """
        if 0 <= index < len(self._has_separators):
            return self._has_separators[index]
        return False

    def set_spacing(self, spacing: int) -> None:
        """
        Set the spacing between buttons.

        Args:
            spacing (int): Spacing in pixels
        """
        self._layout.setSpacing(spacing)

    def add_spacer(self) -> None:
        """Add an expanding spacer to the toolbar."""
        if self._vertical:
            spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        else:
            spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._layout.addItem(spacer)

    def clear(self) -> None:
        """Remove all buttons from the toolbar."""
        for button in list(self._buttons):  # Make a copy of the list before iterating
            self.remove_button(button)

        # Clear groups
        self._groups.clear()
        self._current_group = None
        self._has_separators.clear()
