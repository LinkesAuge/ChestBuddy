"""
icon_provider.py

Description: Provides access to application icons.
Usage:
    Import this module to access application icons.
"""

from PySide6.QtGui import QIcon, QPixmap
from chestbuddy.ui.resources.icons import Icons


class IconProvider:
    """
    Provides access to application icons.

    This class wraps the Icons class and provides additional functionality
    for icon management and retrieval.
    """

    @staticmethod
    def get_icon(name):
        """
        Get an icon by name.

        Args:
            name (str): The icon name or path

        Returns:
            QIcon: The icon
        """
        # If it's a direct path from Icons class
        if hasattr(Icons, name.upper()):
            icon_path = getattr(Icons, name.upper())
            return QIcon(icon_path)

        # If it's a custom path
        return QIcon(name)

    @staticmethod
    def get_pixmap(name):
        """
        Get a pixmap by name.

        Args:
            name (str): The icon name or path

        Returns:
            QPixmap: The pixmap
        """
        # If it's a direct path from Icons class
        if hasattr(Icons, name.upper()):
            icon_path = getattr(Icons, name.upper())
            return QPixmap(icon_path)

        # If it's a custom path
        return QPixmap(name)
