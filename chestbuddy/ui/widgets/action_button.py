"""
action_button.py

Description: A custom styled button for actions in ChestBuddy
Usage:
    button = ActionButton("Import", icon=QIcon(":/icons/import.svg"))
    button.clicked.connect(on_import_clicked)
"""

from typing import Optional, Callable, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtWidgets import QPushButton, QSizePolicy


class ActionButton(QPushButton):
    """
    A stylized button for actions in the ChestBuddy application.

    Provides consistent styling and behavior for action buttons
    throughout the application.

    Attributes:
        name (str): Unique identifier for the button
        _compact (bool): Whether the button is in compact mode
    """

    def __init__(
        self,
        text: str = "",
        icon: Optional[QIcon] = None,
        parent=None,
        name: str = "",
        tooltip: str = "",
        compact: bool = False,
        primary: bool = False,
    ):
        """
        Initialize a new ActionButton.

        Args:
            text (str): Text to display on the button
            icon (QIcon, optional): Icon to display on the button
            parent: Parent widget
            name (str): Identifier for the button
            tooltip (str): Tooltip text
            compact (bool): If True, minimizes padding for compact display
            primary (bool): If True, applies primary action styling
        """
        super().__init__(parent)

        # Store properties
        self._name = name
        self._compact = compact
        self._primary = primary

        # Set button properties
        if text:
            self.setText(text)
        if icon:
            self.setIcon(icon)
        if tooltip:
            self.setToolTip(tooltip)

        # Apply styling
        self._update_style()

        # Set size policy
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Set cursor
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def _update_style(self):
        """Update the button styling based on current properties."""
        # Default style
        style = """
        QPushButton {
            padding: 6px 12px;
            border: 1px solid #BBBBBB;
            border-radius: 4px;
            background-color: #F5F5F5;
            color: #333333;
        }
        QPushButton:hover {
            background-color: #E6E6E6;
            border-color: #AAAAAA;
        }
        QPushButton:pressed {
            background-color: #D6D6D6;
        }
        QPushButton:disabled {
            background-color: #F8F8F8;
            border-color: #DDDDDD;
            color: #AAAAAA;
        }
        """

        # Adjust for compact mode
        if self._compact:
            style = """
            QPushButton {
                padding: 4px 8px;
                border: 1px solid #BBBBBB;
                border-radius: 3px;
                background-color: #F5F5F5;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #E6E6E6;
                border-color: #AAAAAA;
            }
            QPushButton:pressed {
                background-color: #D6D6D6;
            }
            QPushButton:disabled {
                background-color: #F8F8F8;
                border-color: #DDDDDD;
                color: #AAAAAA;
            }
            """

        # Adjust for primary style
        if self._primary:
            style = """
            QPushButton {
                padding: %s;
                border: 1px solid #2C82C9;
                border-radius: %s;
                background-color: #3498DB;
                color: white;
            }
            QPushButton:hover {
                background-color: #2980B9;
                border-color: #2573B3;
            }
            QPushButton:pressed {
                background-color: #2471A3;
            }
            QPushButton:disabled {
                background-color: #85C1E9;
                border-color: #7FB3D5;
                color: #F8F8F8;
            }
            """ % ("4px 8px" if self._compact else "6px 12px", "3px" if self._compact else "4px")

        self.setStyleSheet(style)

    def name(self) -> str:
        """
        Get the button's identifier name.

        Returns:
            str: The button name
        """
        return self._name

    def is_compact(self) -> bool:
        """
        Check if the button is in compact mode.

        Returns:
            bool: True if compact, False otherwise
        """
        return self._compact

    def is_primary(self) -> bool:
        """
        Check if the button has primary styling.

        Returns:
            bool: True if primary, False otherwise
        """
        return self._primary

    def set_compact(self, compact: bool):
        """
        Set the compact mode of the button.

        Args:
            compact (bool): Whether to use compact styling
        """
        if self._compact != compact:
            self._compact = compact
            self._update_style()

    def set_primary(self, primary: bool):
        """
        Set the primary styling of the button.

        Args:
            primary (bool): Whether to use primary styling
        """
        if self._primary != primary:
            self._primary = primary
            self._update_style()
