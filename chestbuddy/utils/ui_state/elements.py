"""
UI State Elements.

This module defines classes for UI elements that can be blocked/unblocked
during operations, including the BlockableElementMixin.
"""

import logging
from typing import Any, Dict, Optional, Set, Callable, Union, List

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

# Set up logger
logger = logging.getLogger(__name__)


class BlockableElementMixin:
    """
    Mixin class for UI elements that can be blocked during operations.

    This mixin provides standard methods for tracking blocked state and
    implementing block/unblock behavior. Classes that use this mixin should
    also inherit from QWidget or a subclass of QWidget.

    Implementation Notes:
        - Tracks which operations are blocking this element
        - Provides hooks for custom block/unblock behavior
        - Registers with the UIStateManager
    """

    def __init__(self) -> None:
        """Initialize the mixin with empty blocking operations set."""
        # Set of operations currently blocking this element
        self._blocking_operations: Set[Any] = set()

        # Flag to track registration status
        self._is_registered = False

        # Store the original enabled state
        self._original_enabled_state = True

        # Reference to the manager (set during registration)
        self._ui_state_manager = None

    def register_with_manager(self, manager) -> None:
        """
        Register this element with the UI state manager.

        Args:
            manager: The UIStateManager instance.
        """
        if self._is_registered:
            logger.warning(f"Element {self} already registered with UI state manager")
            return

        self._ui_state_manager = manager
        self._is_registered = True
        logger.debug(f"Registered {self} with UI state manager")

    def unregister_from_manager(self) -> None:
        """Unregister this element from the UI state manager."""
        if not self._is_registered or not self._ui_state_manager:
            logger.warning(f"Element {self} not registered with any UI state manager")
            return

        self._ui_state_manager.unregister_element(self)
        self._is_registered = False
        self._ui_state_manager = None
        logger.debug(f"Unregistered {self} from UI state manager")

    def is_blocked(self) -> bool:
        """
        Check if this element is currently blocked.

        Returns:
            bool: True if blocked by any operation, False otherwise.
        """
        return len(self._blocking_operations) > 0

    def get_blocking_operations(self) -> Set[Any]:
        """
        Get the set of operations currently blocking this element.

        Returns:
            Set[Any]: Set of operations blocking this element.
        """
        return self._blocking_operations.copy()

    def block(self, operation: Any) -> None:
        """
        Block this element due to the specified operation.

        Args:
            operation: The operation blocking this element.
        """
        # Add to blocking operations
        self._blocking_operations.add(operation)

        # Only apply block if this is the first blocking operation
        if len(self._blocking_operations) == 1:
            self._apply_block()

        logger.debug(f"Element {self} blocked by operation {operation}")

    def unblock(self, operation: Any) -> None:
        """
        Unblock this element from the specified operation.

        Args:
            operation: The operation to unblock.
        """
        # Only proceed if this operation is actually blocking
        if operation not in self._blocking_operations:
            logger.warning(f"Operation {operation} not blocking element {self}")
            return

        # Remove from blocking operations
        self._blocking_operations.remove(operation)

        # Only apply unblock if no more blocking operations
        if not self._blocking_operations:
            self._apply_unblock()

        logger.debug(f"Element {self} unblocked from operation {operation}")

    def _apply_block(self) -> None:
        """
        Apply the blocking behavior to this element.

        This method can be overridden by subclasses to provide custom
        blocking behavior. The default implementation disables the widget.
        """
        if isinstance(self, QWidget):
            self._original_enabled_state = self.isEnabled()
            self.setEnabled(False)
        else:
            logger.warning(f"Element {self} is not a QWidget, cannot apply block")

    def _apply_unblock(self) -> None:
        """
        Apply the unblocking behavior to this element.

        This method can be overridden by subclasses to provide custom
        unblocking behavior. The default implementation restores the
        widget's original enabled state.
        """
        if isinstance(self, QWidget):
            self.setEnabled(self._original_enabled_state)
        else:
            logger.warning(f"Element {self} is not a QWidget, cannot apply unblock")


class BlockableWidgetGroup(QObject):
    """
    A group of blockable widgets that can be blocked/unblocked together.

    This class allows multiple widgets to be treated as a single unit
    for blocking/unblocking operations.
    """

    def __init__(self, name: str, widgets: Optional[List[QWidget]] = None) -> None:
        """
        Initialize a blockable widget group.

        Args:
            name: Name of the group for identification
            widgets: Optional list of widgets to include in the group
        """
        super().__init__()
        self.name = name
        self._widgets = widgets or []

        # Set of operations currently blocking this group
        self._blocking_operations: Set[Any] = set()

    def add_widget(self, widget: QWidget) -> None:
        """
        Add a widget to the group.

        Args:
            widget: The widget to add
        """
        if widget not in self._widgets:
            self._widgets.append(widget)

            # Apply current blocking if any
            if self._blocking_operations:
                if hasattr(widget, "block"):
                    for operation in self._blocking_operations:
                        widget.block(operation)
                else:
                    widget.setEnabled(False)

    def remove_widget(self, widget: QWidget) -> None:
        """
        Remove a widget from the group.

        Args:
            widget: The widget to remove
        """
        if widget in self._widgets:
            self._widgets.remove(widget)

            # Unblock if needed
            if self._blocking_operations:
                if hasattr(widget, "unblock"):
                    for operation in self._blocking_operations:
                        widget.unblock(operation)
                else:
                    widget.setEnabled(True)

    def block(self, operation: Any) -> None:
        """
        Block all widgets in the group.

        Args:
            operation: The operation blocking this group
        """
        self._blocking_operations.add(operation)

        for widget in self._widgets:
            if hasattr(widget, "block"):
                widget.block(operation)
            else:
                widget.setEnabled(False)

    def unblock(self, operation: Any) -> None:
        """
        Unblock all widgets in the group from the specified operation.

        Args:
            operation: The operation to unblock
        """
        if operation in self._blocking_operations:
            self._blocking_operations.remove(operation)

            # Only unblock if no more blocking operations
            if not self._blocking_operations:
                for widget in self._widgets:
                    if hasattr(widget, "unblock"):
                        widget.unblock(operation)
                    else:
                        widget.setEnabled(True)

    def is_blocked(self) -> bool:
        """
        Check if this group is currently blocked.

        Returns:
            bool: True if blocked by any operation, False otherwise
        """
        return len(self._blocking_operations) > 0

    def get_blocking_operations(self) -> Set[Any]:
        """
        Get the set of operations currently blocking this group.

        Returns:
            Set[Any]: Set of operations blocking this group
        """
        return self._blocking_operations.copy()
