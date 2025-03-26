"""
updatable_view.py

Description: Implements the UpdatableView class that combines BaseView and UpdatableComponent.
Usage:
    from chestbuddy.ui.views.updatable_view import UpdatableView

    class MyView(UpdatableView):
        def _do_update(self, data=None):
            # Custom update logic
            pass
"""

import time
import hashlib
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget

import logging

from chestbuddy.ui.interfaces import IUpdatable
from chestbuddy.ui.views.base_view import BaseView
from chestbuddy.ui.utils import get_update_manager

logger = logging.getLogger(__name__)


class UpdatableView(BaseView):
    """
    Base class for views that need standardized update functionality.

    This class combines the BaseView's UI structure with UpdatableComponent's
    update management to provide consistent update patterns for views.

    Implementation Notes:
        - Inherits from BaseView
        - Implements IUpdatable interface directly
        - Provides default implementations for update-related methods
        - Integrates with the UpdateManager for scheduling updates
    """

    # Define signals as class attributes
    update_requested = Signal()
    update_completed = Signal()

    def __init__(self, title: str, parent: Optional[QWidget] = None, debug_mode: bool = False):
        """
        Initialize the updatable view.

        Args:
            title: The view title
            parent: The parent widget
            debug_mode: Enable debug mode for signal connections
        """
        # Initialize BaseView (which inherits from QWidget)
        super().__init__(title, parent, debug_mode)

        # Initialize update state
        self._update_state = {
            "last_update_time": 0.0,
            "needs_update": True,
            "update_pending": False,
            "data_hash": None,
            "initial_population": False,
        }

    def refresh(self) -> None:
        """
        Refresh the component's display with current data.

        This method updates the component's visual representation with
        the latest data, without changing the component's state.
        """
        self._update_state["needs_update"] = True
        self.update_requested.emit()
        self._do_refresh()
        self._update_state["last_update_time"] = time.time()
        self.update_completed.emit()
        logger.debug(f"{self.__class__.__name__} refreshed")

    def update(self, data: Optional[Any] = None) -> None:
        """
        Update the component with new data.

        This method updates both the component's internal state and
        visual representation with the provided data.

        Args:
            data: Optional new data to update the component with
        """
        if not self._should_update(data):
            logger.debug(f"{self.__class__.__name__} skipping update (no change detected)")
            return

        self._update_state["needs_update"] = True
        self._update_state["update_pending"] = True
        self.update_requested.emit()

        try:
            self._do_update(data)
            self._update_hash(data)
            self._update_state["needs_update"] = False
            self._update_state["update_pending"] = False
            self._update_state["last_update_time"] = time.time()
            self.update_completed.emit()
            logger.debug(f"{self.__class__.__name__} updated")
        except Exception as e:
            self._update_state["update_pending"] = False
            logger.error(f"Error updating {self.__class__.__name__}: {str(e)}")
            raise

    def populate(self, data: Optional[Any] = None) -> None:
        """
        Completely populate the component with the provided data.

        This method should fully populate the component from scratch,
        replacing any existing content.

        Args:
            data: Optional data to populate the component with
        """
        self._update_state["needs_update"] = True
        self._update_state["update_pending"] = True
        self.update_requested.emit()

        try:
            self._do_populate(data)
            self._update_hash(data)
            self._update_state["needs_update"] = False
            self._update_state["update_pending"] = False
            self._update_state["initial_population"] = True
            self._update_state["last_update_time"] = time.time()
            self.update_completed.emit()
            logger.debug(f"{self.__class__.__name__} populated")
        except Exception as e:
            self._update_state["update_pending"] = False
            logger.error(f"Error populating {self.__class__.__name__}: {str(e)}")
            raise

    def needs_update(self) -> bool:
        """
        Check if the component needs an update.

        Returns:
            bool: True if the component needs to be updated, False otherwise
        """
        return self._update_state["needs_update"]

    def is_populated(self) -> bool:
        """
        Check if the component has been populated at least once.

        Returns:
            bool: True if the component has been populated, False otherwise
        """
        return self._update_state["initial_population"]

    def reset(self) -> None:
        """
        Reset the component to its initial state.

        Default implementation updates internal state and calls _do_reset.
        """
        self._update_state["needs_update"] = True
        self._update_state["update_pending"] = True

        try:
            self._do_reset()
            self._update_state["needs_update"] = False
            self._update_state["update_pending"] = False
            self._update_state["initial_population"] = False
            self._update_state["data_hash"] = None
            self._update_state["last_update_time"] = time.time()
            logger.debug(f"{self.__class__.__name__} reset")
        except Exception as e:
            self._update_state["update_pending"] = False
            logger.error(f"Error resetting {self.__class__.__name__}: {str(e)}")
            raise

    def last_update_time(self) -> float:
        """
        Get the timestamp of the last update.

        Returns:
            float: Timestamp of the last update (seconds since epoch)
        """
        return self._update_state["last_update_time"]

    def _should_update(self, data: Optional[Any] = None) -> bool:
        """
        Check if the component should be updated.

        Args:
            data: Optional data to check against current state

        Returns:
            bool: True if the component should be updated, False otherwise
        """
        # If no data is provided, always update
        if data is None:
            return True

        # If data hash matches current state, no need to update
        current_hash = self._compute_hash(data)
        return current_hash != self._update_state.get("data_hash")

    def _update_hash(self, data: Optional[Any] = None) -> None:
        """
        Update the data hash in the component's state.

        Args:
            data: The data to compute the hash for
        """
        if data is not None:
            self._update_state["data_hash"] = self._compute_hash(data)

    def _compute_hash(self, data: Any) -> str:
        """
        Compute a hash for the given data.

        Args:
            data: The data to compute the hash for

        Returns:
            str: Hash value as a string
        """
        try:
            # Try to use the object's own hash function if available
            if hasattr(data, "__hash__") and callable(data.__hash__):
                return str(hash(data))

            # For simple types, convert to string and hash
            return hashlib.md5(str(data).encode("utf-8")).hexdigest()
        except Exception:
            # Fallback to the object's id
            return str(id(data))

    def _do_update(self, data: Optional[Any] = None) -> None:
        """
        Implementation of the update logic for this view.

        Args:
            data: Optional data to update the view with
        """
        logger.debug(f"{self.__class__.__name__} updating with data: {type(data).__name__}")

        # Default implementation - to be overridden by subclasses
        try:
            # Subclasses should override this to implement their specific update logic
            self._update_view_content(data)
        except Exception as e:
            logger.error(f"Error in _do_update for {self.__class__.__name__}: {e}")
            raise

    def _do_refresh(self) -> None:
        """
        Implementation of the refresh logic for this view.
        """
        logger.debug(f"{self.__class__.__name__} refreshing")

        # Default implementation - to be overridden by subclasses
        try:
            # Subclasses can override this to implement specific refresh logic
            self._refresh_view_content()
        except Exception as e:
            logger.error(f"Error in _do_refresh for {self.__class__.__name__}: {e}")
            raise

    def _do_populate(self, data: Optional[Any] = None) -> None:
        """
        Implementation of the populate logic for this view.

        Args:
            data: Optional data to populate the view with
        """
        logger.debug(f"{self.__class__.__name__} populating with data: {type(data).__name__}")

        # Default implementation - to be overridden by subclasses
        try:
            # Subclasses should override this to implement their specific populate logic
            self._populate_view_content(data)
        except Exception as e:
            logger.error(f"Error in _do_populate for {self.__class__.__name__}: {e}")
            raise

    def _do_reset(self) -> None:
        """
        Implementation of the reset logic for this view.
        """
        logger.debug(f"{self.__class__.__name__} resetting")

        # Default implementation - to be overridden by subclasses
        try:
            # Subclasses should override this to implement their specific reset logic
            self._reset_view_content()
        except Exception as e:
            logger.error(f"Error in _do_reset for {self.__class__.__name__}: {e}")
            raise

    def _update_view_content(self, data: Optional[Any] = None) -> None:
        """
        Update the view content based on the provided data.

        This is a placeholder method that should be overridden by subclasses.

        Args:
            data: Optional data to update the view with
        """
        pass

    def _refresh_view_content(self) -> None:
        """
        Refresh the view content without changing the underlying data.

        This is a placeholder method that should be overridden by subclasses.
        """
        pass

    def _populate_view_content(self, data: Optional[Any] = None) -> None:
        """
        Populate the view content from scratch with the provided data.

        This is a placeholder method that should be overridden by subclasses.

        Args:
            data: Optional data to populate the view with
        """
        pass

    def _reset_view_content(self) -> None:
        """
        Reset the view content to its initial state.

        This is a placeholder method that should be overridden by subclasses.
        """
        pass

    def schedule_update(self, debounce_ms: int = 50) -> None:
        """
        Schedule an update for this view using the UpdateManager.

        Args:
            debounce_ms: Debounce interval in milliseconds
        """
        try:
            update_manager = get_update_manager()
            update_manager.schedule_update(self, debounce_ms)
            logger.debug(f"{self.__class__.__name__} scheduled for update")
        except Exception as e:
            logger.error(f"Error scheduling update for {self.__class__.__name__}: {e}")
            # Fall back to direct update if UpdateManager is not available
            self.update()

    def request_update(self, data_state=None) -> None:
        """
        Request an update for this view.

        This is a convenience method that makes the view's update state as needing
        an update and schedules it with the UpdateManager.

        Args:
            data_state: Optional DataState object from data change event
        """
        self._update_state["needs_update"] = True
        self.schedule_update()
