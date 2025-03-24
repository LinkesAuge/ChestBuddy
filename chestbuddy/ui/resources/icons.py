"""
icons.py

Description: Defines application icons and provides convenient access to them.
Usage:
    Import this module to access application icons.
"""

from PySide6.QtCore import QDir
from PySide6.QtGui import QIcon, QPixmap


class Icons:
    """
    Collection of application icons.

    This class provides convenient access to application icons.
    """

    # Icon paths
    _ICON_PATH = ":/icons"

    # Application icons
    APP_ICON = ":/icons/app_icon.png"
    APP_LOGO = ":/icons/app_logo.png"  # Added app_logo for welcome screen

    # Action icons
    OPEN = ":/icons/open.png"
    SAVE = ":/icons/save.png"
    VALIDATE = ":/icons/validate.png"
    CORRECT = ":/icons/correct.png"
    IMPORT = ":/icons/import.png"
    EXPORT = ":/icons/export.png"
    CHECK_CIRCLE = ":/icons/check_circle.png"
    FOLDER_OPEN = ":/icons/folder_open.png"
    FILE = ":/icons/file.png"
    FILE_DOCUMENT = ":/icons/file_document.png"
    CHART_LINE = ":/icons/chart_line.png"
    CHART = ":/icons/chart.png"
    HELP_CIRCLE = ":/icons/help_circle.png"

    # Navigation icons
    DASHBOARD = ":/icons/dashboard.png"
    DATA = ":/icons/data.png"
    ANALYSIS = ":/icons/analysis.png"
    REPORTS = ":/icons/reports.png"
    SETTINGS = ":/icons/settings.png"
    HELP = ":/icons/help.png"

    # UI Control icons
    CHEVRON_UP = ":/icons/chevron_up.png"
    CHEVRON_DOWN = ":/icons/chevron_down.png"
    PLUS = ":/icons/plus.png"
    MINUS = ":/icons/minus.png"
    SEARCH = ":/icons/search.png"
    FILTER = ":/icons/filter.png"
    CLOSE = ":/icons/close.png"

    @staticmethod
    def get_icon(icon_path):
        """
        Get an icon by path.

        Args:
            icon_path (str): The icon path

        Returns:
            QIcon: The icon
        """
        return QIcon(icon_path)

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


# Import and re-export the IconProvider class
try:
    from chestbuddy.ui.resources.icon_provider import IconProvider
except ImportError:
    # Define a minimal IconProvider if the module doesn't exist
    class IconProvider:
        """Fallback IconProvider class."""

        @staticmethod
        def get_icon(name):
            """Get an icon by name."""
            if hasattr(Icons, name.upper()):
                icon_path = getattr(Icons, name.upper())
                return QIcon(icon_path)
            return QIcon(name)

        @staticmethod
        def get_pixmap(name):
            """Get a pixmap by name."""
            if hasattr(Icons, name.upper()):
                icon_path = getattr(Icons, name.upper())
                return QPixmap(icon_path)
            return QPixmap(name)


# Re-export for backward compatibility
__all__ = ["Icons", "IconProvider"]
