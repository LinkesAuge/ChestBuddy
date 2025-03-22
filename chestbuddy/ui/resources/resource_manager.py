"""
resource_manager.py

Description: Manages application resources and provides convenient access to them.
Usage:
    Import this module to initialize and access application resources.
"""

import os
import logging
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages application resources.

    This class is responsible for initializing and providing access to application resources.
    """

    # Resource paths
    _RESOURCES_DIR = Path(__file__).parent
    _ICONS_DIR = _RESOURCES_DIR / "icons"

    # Resource initialization flag
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize the resource manager."""
        if cls._initialized:
            return

        # Initialize Qt resources
        try:
            from chestbuddy.ui.resources import resources_rc

            logger.debug("Qt resources initialized")
            cls._initialized = True
        except ImportError:
            logger.warning("Failed to load Qt resources. Using file-based resources.")

            # If resources_rc is not available, we'll fall back to file-based resources
            cls._ensure_dirs_exist()

    @classmethod
    def _ensure_dirs_exist(cls):
        """Ensure resource directories exist."""
        os.makedirs(cls._ICONS_DIR, exist_ok=True)

    @classmethod
    def get_icon_path(cls, icon_name):
        """
        Get the path to an icon.

        Args:
            icon_name (str): The icon name

        Returns:
            str: The icon path
        """
        if cls._initialized:
            return f":/icons/{icon_name}"
        else:
            # Fall back to file-based resources
            return str(cls._ICONS_DIR / icon_name)

    @classmethod
    def get_pixmap(cls, icon_name):
        """
        Get a pixmap for an icon.

        Args:
            icon_name (str): The icon name

        Returns:
            QPixmap: The pixmap
        """
        icon_path = cls.get_icon_path(icon_name)

        if cls._initialized:
            return QPixmap(icon_path)
        else:
            # Load from file
            return QPixmap(str(icon_path))

    @classmethod
    def get_stylesheet(cls, name):
        """
        Get a stylesheet by name.

        Args:
            name (str): The stylesheet name

        Returns:
            str: The stylesheet content
        """
        stylesheet_path = cls._RESOURCES_DIR / "stylesheets" / f"{name}.qss"

        if stylesheet_path.exists():
            with open(stylesheet_path, "r") as f:
                return f.read()
        else:
            logger.warning(f"Stylesheet {name} not found")
            return ""
