"""
icons.py

Description: Defines application icons and provides convenient access to them.
Usage:
    Import this module to access application icons.
"""

from PySide6.QtCore import QDir, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor


class Icons:
    """
    Collection of application icons.

    This class provides convenient access to application icons.
    """

    # Icon paths
    _ICON_PATH = ":/icons"

    # Application icons
    APP_ICON = ":/icons/app_icon.png"

    # Action icons
    OPEN = ":/icons/open.png"
    SAVE = ":/icons/save.png"
    VALIDATE = ":/icons/validate.png"
    CORRECT = ":/icons/correct.png"

    # Navigation icons
    DASHBOARD = ":/icons/dashboard.png"
    DATA = ":/icons/data.png"
    CHART = ":/icons/analysis.png"
    REPORT = ":/icons/reports.png"
    SETTINGS = ":/icons/settings.png"
    HELP = ":/icons/help.png"

    @staticmethod
    def get_icon(icon_path, color=None):
        """
        Get an icon by path. Optionally apply a color to the icon.

        Args:
            icon_path (str): The icon path
            color (str, optional): Color to apply to the icon. Defaults to None.

        Returns:
            QIcon: The icon
        """
        if color is None:
            return QIcon(icon_path)
        else:
            # Convert icon to colored variant
            return Icons.create_colored_icon(icon_path, color)

    @staticmethod
    def get_pixmap(icon_path):
        """
        Get a pixmap by path.

        Args:
            icon_path (str): The icon path

        Returns:
            QPixmap: The pixmap
        """
        return QPixmap(icon_path)

    @staticmethod
    def create_colored_icon(icon_path, color):
        """
        Create a colored version of an icon.

        Args:
            icon_path (str): The icon path
            color (str): The color to apply (as CSS color string)

        Returns:
            QIcon: The colored icon
        """
        # Create base pixmap
        original = QPixmap(icon_path)
        if original.isNull():
            return QIcon()  # Return empty icon if original is null

        # Create transparent pixmap with the same size
        colored = QPixmap(original.size())
        colored.fill(Qt.transparent)

        # Paint the original icon with the specified color
        painter = QPainter(colored)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply color using CompositionMode_SourceIn
        if isinstance(color, str):
            painter.setBrush(QColor(color))
        else:
            painter.setBrush(color)

        painter.setPen(Qt.NoPen)
        painter.drawRect(colored.rect())

        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, original)
        painter.end()

        return QIcon(colored)
