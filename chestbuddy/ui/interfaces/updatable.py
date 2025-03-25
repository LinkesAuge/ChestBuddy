"""
updatable.py

Description: Defines the IUpdatable protocol and UpdatableComponent base class.
Usage:
    from chestbuddy.ui.interfaces.updatable import IUpdatable, UpdatableComponent

    # Using the protocol to check type compatibility
    def update_component(component: IUpdatable) -> None:
        component.update()

    # Inheriting from the base class in custom components
    class MyComponent(UpdatableComponent):
        def _do_update(self, data: Optional[Any] = None) -> None:
            # Component-specific update logic
            pass
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from PySide6.QtCore import QObject, Qt, Signal

import logging

logger = logging.getLogger(__name__)


@runtime_checkable
class IUpdatable(Protocol):
    """
    Protocol defining the standard interface for updatable UI components.

    This protocol defines methods that all updatable UI components should implement
    to ensure consistent update patterns across the application.
    """

    def refresh(self) -> None:
        """
        Refresh the component's display with current data.

        This method should update the component's visual representation with
        the latest data, without changing the component's state.
        """
        ...

    def update(self, data: Optional[Any] = None) -> None:
        """
        Update the component with new data.

        This method should update both the component's internal state and
        visual representation with the provided data.

        Args:
            data: Optional new data to update the component with
        """
        ...

    def populate(self, data: Optional[Any] = None) -> None:
        """
        Completely populate the component with the provided data.

        This method should fully populate the component from scratch,
        replacing any existing content.

        Args:
            data: Optional data to populate the component with
        """
        ...

    def needs_update(self) -> bool:
        """
        Check if the component needs an update.

        Returns:
            bool: True if the component needs to be updated, False otherwise
        """
        ...

    def reset(self) -> None:
        """
        Reset the component to its initial state.

        This method should clear all data and return the component to its
        default state.
        """
        ...

    def last_update_time(self) -> float:
        """
        Get the timestamp of the last update.

        Returns:
            float: Timestamp of the last update (seconds since epoch)
        """
        ...


class UpdatableComponent(QObject):
    """
    Base class for updatable UI components implementing the IUpdatable interface.

    This class provides default implementations of the IUpdatable methods and
    standardized update tracking.

    Attributes:
        update_requested (Signal): Signal emitted when an update is requested
        update_completed (Signal): Signal emitted when an update is completed
        _update_state (dict): Dictionary tracking update state
    """

    update_requested = Signal()
    update_completed = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the updatable component."""
        super().__init__(parent)
        self._update_state: Dict[str, Any] = {
            "last_update_time": 0.0,
            "needs_update": True,
            "update_pending": False,
            "data_hash": None,
            "initial_population": False,
        }

    def refresh(self) -> None:
        """
        Refresh the component's display with current data.

        Default implementation marks the component as needing an update
        and emits the update_requested signal.
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

        Default implementation updates internal state and calls _do_update.

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

        Default implementation updates internal state and calls _do_populate.

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

    def _do_update(self, data: Optional[Any] = None) -> None:
        """
        Implement component-specific update logic.

        This method should be overridden by subclasses to implement
        component-specific update logic.

        Args:
            data: Optional new data to update the component with
        """
        pass

    def _do_refresh(self) -> None:
        """
        Implement component-specific refresh logic.

        This method should be overridden by subclasses to implement
        component-specific refresh logic without changing state.
        """
        # Default implementation just calls _do_update with current data
        self._do_update(None)

    def _do_populate(self, data: Optional[Any] = None) -> None:
        """
        Implement component-specific populate logic.

        This method should be overridden by subclasses to implement
        component-specific populate logic.

        Args:
            data: Optional data to populate the component with
        """
        # Default implementation just calls _do_update
        self._do_update(data)

    def _do_reset(self) -> None:
        """
        Implement component-specific reset logic.

        This method should be overridden by subclasses to implement
        component-specific reset logic.
        """
        pass

    def _update_hash(self, data: Optional[Any] = None) -> None:
        """
        Update the hash of the current data.

        This is used to detect changes in the data to avoid unnecessary updates.

        Args:
            data: Optional data to compute hash from
        """
        if data is None:
            return

        try:
            # Try to create a deterministic hash of the data
            if hasattr(data, "to_dict"):
                # For pandas DataFrame or similar
                data_str = str(data.to_dict())
            elif hasattr(data, "__dict__"):
                # For objects with __dict__
                data_str = str(data.__dict__)
            else:
                # For other types
                data_str = str(data)

            self._update_state["data_hash"] = hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(
                f"Could not compute hash for data in {self.__class__.__name__}: {str(e)}"
            )

    def _should_update(self, data: Optional[Any] = None) -> bool:
        """
        Check if the component should be updated with the given data.

        This method is used to avoid unnecessary updates when the data hasn't changed.

        Args:
            data: Optional new data to check

        Returns:
            bool: True if the component should be updated, False otherwise
        """
        # Always update if explicitly marked as needing update
        if self._update_state["needs_update"]:
            return True

        # If no previous hash or no data provided, assume update is needed
        if self._update_state["data_hash"] is None or data is None:
            return True

        # Try to create a hash of the new data to compare with current hash
        try:
            if hasattr(data, "to_dict"):
                # For pandas DataFrame or similar
                data_str = str(data.to_dict())
            elif hasattr(data, "__dict__"):
                # For objects with __dict__
                data_str = str(data.__dict__)
            else:
                # For other types
                data_str = str(data)

            new_hash = hashlib.md5(data_str.encode()).hexdigest()
            return new_hash != self._update_state["data_hash"]
        except Exception as e:
            logger.warning(
                f"Could not compute hash for comparison in {self.__class__.__name__}: {str(e)}"
            )
            return True  # Update if hash computation fails
