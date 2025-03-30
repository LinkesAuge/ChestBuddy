"""
icon_provider.py

Description: Provides centralized access to application icons with caching and theme support.
"""

import logging
from typing import Dict, Optional
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

logger = logging.getLogger(__name__)


class IconProvider:
    """
    Singleton class for providing application icons with caching and theme support.

    This class manages icon loading, caching, and theme-based icon selection.
    It provides a centralized way to access application icons and ensures
    consistent icon usage throughout the application.

    Attributes:
        _instance (Optional[IconProvider]): Singleton instance
        _icon_cache (Dict[str, QIcon]): Cache of loaded icons
        _icon_size (QSize): Default icon size

    Implementation Notes:
        - Uses singleton pattern for global access
        - Caches loaded icons for better performance
        - Supports both light and dark themes
        - Falls back to system icons if custom icons are not found
    """

    _instance: Optional["IconProvider"] = None
    _icon_cache: Dict[str, QIcon] = {}
    _icon_size = QSize(16, 16)

    def __new__(cls) -> "IconProvider":
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super(IconProvider, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the icon provider."""
        # Standard action icons
        self._standard_icons = {
            "plus": "list-add",
            "minus": "list-remove",
            "import": "document-import",
            "export": "document-export",
            "settings": "configure",
            "check": "dialog-ok",
            "cancel": "dialog-cancel",
            "edit": "document-edit",
            "delete": "edit-delete",
            "save": "document-save",
            "open": "document-open",
            "close": "window-close",
            "refresh": "view-refresh",
            "search": "system-search",
            "filter": "view-filter",
            "sort": "view-sort",
            "warning": "dialog-warning",
            "error": "dialog-error",
            "info": "dialog-information",
        }

    @classmethod
    def get_icon(cls, name: str, fallback: str = None) -> QIcon:
        """
        Get an icon by name.

        Args:
            name (str): Name of the icon to retrieve
            fallback (str, optional): Fallback icon name if primary icon not found

        Returns:
            QIcon: The requested icon or a fallback icon

        Note:
            If neither the requested icon nor the fallback icon is found,
            returns an empty QIcon.
        """
        instance = cls()

        # Check cache first
        if name in cls._icon_cache:
            return cls._icon_cache[name]

        # Try to get the standard icon name
        std_name = instance._standard_icons.get(name, name)

        # Try to load the icon
        icon = QIcon.fromTheme(std_name)

        # If icon not found and fallback provided, try fallback
        if icon.isNull() and fallback:
            fallback_std = instance._standard_icons.get(fallback, fallback)
            icon = QIcon.fromTheme(fallback_std)

        # Cache the icon
        cls._icon_cache[name] = icon
        return icon

    @classmethod
    def set_icon_size(cls, size: QSize) -> None:
        """
        Set the default icon size.

        Args:
            size (QSize): New default icon size
        """
        cls._icon_size = size

    @classmethod
    def get_icon_size(cls) -> QSize:
        """
        Get the current default icon size.

        Returns:
            QSize: Current default icon size
        """
        return cls._icon_size

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the icon cache."""
        cls._icon_cache.clear()
        logger.debug("Icon cache cleared")
