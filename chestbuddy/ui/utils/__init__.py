"""
UI utilities package initialization.

This package contains utility classes and functions for UI components.
"""

import logging
from PySide6.QtCore import QObject

from chestbuddy.utils.service_locator import ServiceLocator
from chestbuddy.ui.utils.icon_provider import IconProvider
from chestbuddy.ui.utils.update_manager import UpdateManager


logger = logging.getLogger(__name__)


def get_update_manager() -> UpdateManager:
    """
    Get the global UpdateManager instance from the ServiceLocator.

    Returns:
        UpdateManager: The global UpdateManager instance

    Raises:
        KeyError: If UpdateManager is not registered with ServiceLocator
    """
    try:
        return ServiceLocator.get(UpdateManager)
    except KeyError as e:
        logger.error(f"UpdateManager not found in ServiceLocator: {e}")
        raise


__all__ = ["IconProvider", "UpdateManager", "get_update_manager"]
