"""
UI utilities package initialization.

This module imports and re-exports UI utility functions and classes.
"""

from chestbuddy.ui.utils.update_manager import UpdateManager
from chestbuddy.utils.service_locator import ServiceLocator


def get_update_manager() -> UpdateManager:
    """
    Get the application-wide UpdateManager instance.

    Returns:
        UpdateManager: The application's UpdateManager instance

    Raises:
        KeyError: If the UpdateManager has not been registered
    """
    return ServiceLocator.get_typed("update_manager", UpdateManager)


__all__ = ["UpdateManager", "get_update_manager"]
