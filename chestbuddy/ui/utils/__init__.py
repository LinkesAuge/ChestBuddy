"""
UI utilities package initialization.

This package contains utility classes and functions for UI components.
"""

from chestbuddy.ui.utils.icon_provider import IconProvider
from chestbuddy.ui.utils.update_manager import UpdateManager
from chestbuddy.core.service_locator import ServiceLocator


def get_update_manager() -> UpdateManager:
    """
    Get the global UpdateManager instance from the ServiceLocator.

    Returns:
        UpdateManager: The global UpdateManager instance

    Raises:
        KeyError: If UpdateManager is not registered with ServiceLocator
    """
    return ServiceLocator.get("update_manager")


__all__ = ["IconProvider", "UpdateManager", "get_update_manager"]
