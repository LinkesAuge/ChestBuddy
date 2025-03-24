"""
UI State Manager.

This module defines the UIStateManager, which is the central singleton class
for the UI state management system. It tracks UI state, manages operations,
and coordinates between UI elements.
"""

import logging
import traceback
import time
from typing import Any, Dict, List, Optional, Set, Union, Tuple, Callable, ContextManager
from weakref import WeakSet, WeakKeyDictionary, WeakValueDictionary
from contextlib import contextmanager

from PySide6.QtCore import QMutex, QObject, Qt, QThread

from chestbuddy.utils.ui_state.signals import UIStateSignals
from chestbuddy.utils.ui_state.constants import UIElementGroups, UIOperations

# Set up logger
logger = logging.getLogger(__name__)


@contextmanager
def mutex_lock(mutex: QMutex = None) -> None:
    """
    Context manager for safely locking and unlocking a QMutex.

    If no mutex is provided, a new one will be created.

    Args:
        mutex: Optional QMutex instance to lock. If None, a new QMutex is created.

    Yields:
        None
    """
    if mutex is None:
        mutex = QMutex()

    mutex.lock()
    try:
        yield
    finally:
        mutex.unlock()


class SingletonMeta(type):
    """Metaclass for implementing the Singleton pattern."""

    _instances = {}
    _mutex = QMutex()

    def __call__(cls, *args, **kwargs):
        mutex = QMutex()
        mutex.lock()
        try:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]
        finally:
            mutex.unlock()


# Get the metaclass of QObject
QObjectMetaClass = type(QObject)


class QObjectSingletonMeta(QObjectMetaClass, SingletonMeta):
    """
    Metaclass that combines QObject's metaclass with SingletonMeta.

    This resolves the metaclass conflict when a class inherits from both
    QObject and uses SingletonMeta as its metaclass.
    """

    pass


class UIStateManager(QObject, metaclass=QObjectSingletonMeta):
    """
    Central manager for UI state in the application.

    This singleton class manages the blocking and unblocking of UI elements
    during operations, tracking which operations are blocking which elements
    and ensuring proper reference counting.

    Implementation Notes:
        - Singleton pattern ensures only one instance exists
        - Thread-safe implementation using QMutex
        - Uses weak references to avoid memory leaks
        - Emits signals when UI state changes
    """

    def __init__(self) -> None:
        """Initialize the UI state manager."""
        super().__init__()

        # Create signals instance
        self.signals = UIStateSignals()

        # Mutex for thread safety
        self._mutex = QMutex()

        # Registry of UI elements
        # {element: set(operations_blocking_it)}
        self._element_registry = WeakKeyDictionary()

        # Registry of element groups
        # {group_id: set(elements_in_group)}
        self._group_registry = {}

        # Custom handlers for elements
        # {element: (block_func, unblock_func)}
        self._element_handlers = WeakKeyDictionary()

        # Active operations
        # {operation: set(elements_blocked_by_operation)}
        self._active_operations = {}

        # Custom group handlers
        # {group_id: (block_func, unblock_func)}
        self._group_handlers = {}

        # Debug info
        self._debug_info = {
            "element_registry_size": 0,
            "active_operations_count": 0,
            "last_operation_time": 0,
        }

        logger.debug("UIStateManager initialized")

    def register_element(
        self,
        element: Any,
        groups: Optional[List[Any]] = None,
        block_handler: Optional[callable] = None,
        unblock_handler: Optional[callable] = None,
    ) -> None:
        """
        Register a UI element with the manager.

        Args:
            element: The UI element to register.
            groups: Optional list of groups to add the element to.
            block_handler: Optional custom function to call when blocking.
            unblock_handler: Optional custom function to call when unblocking.
        """
        with mutex_lock():
            # Initialize element in registry if not present
            if element not in self._element_registry:
                self._element_registry[element] = set()

                logger.debug(f"Registered element {element}")

            # Set custom handlers if provided
            if block_handler or unblock_handler:
                self._element_handlers[element] = (block_handler, unblock_handler)
                logger.debug(f"Set custom handlers for element {element}")

            # Add to groups if specified
            if groups:
                for group in groups:
                    self.add_element_to_group(element, group)

            # Update debug info
            self._update_debug_info()

    def unregister_element(self, element: Any) -> None:
        """
        Unregister a UI element from the manager.

        Args:
            element: The UI element to unregister.
        """
        with mutex_lock():
            # Remove from registry
            if element in self._element_registry:
                del self._element_registry[element]
                logger.debug(f"Unregistered element {element}")

            # Remove custom handlers
            if element in self._element_handlers:
                del self._element_handlers[element]

            # Remove from groups
            for group_id, elements in self._group_registry.items():
                if element in elements:
                    elements.remove(element)

            # Update debug info
            self._update_debug_info()

    def register_group(
        self,
        group_id: Any,
        elements: Optional[List[Any]] = None,
        block_handler: Optional[callable] = None,
        unblock_handler: Optional[callable] = None,
    ) -> None:
        """
        Register a group of UI elements.

        Args:
            group_id: The identifier for the group.
            elements: Optional list of elements to add to the group.
            block_handler: Optional custom function to call when blocking the group.
            unblock_handler: Optional custom function to call when unblocking the group.
        """
        with mutex_lock():
            # Initialize group in registry if not present
            if group_id not in self._group_registry:
                self._group_registry[group_id] = set()
                logger.debug(f"Registered group {group_id}")

            # Set custom handlers if provided
            if block_handler or unblock_handler:
                self._group_handlers[group_id] = (block_handler, unblock_handler)
                logger.debug(f"Set custom handlers for group {group_id}")

            # Add elements if specified
            if elements:
                for element in elements:
                    self.add_element_to_group(element, group_id)

    def unregister_group(self, group_id: Any) -> None:
        """
        Unregister a group of UI elements.

        Args:
            group_id: The identifier for the group.
        """
        with mutex_lock():
            # Remove from registry
            if group_id in self._group_registry:
                del self._group_registry[group_id]
                logger.debug(f"Unregistered group {group_id}")

            # Remove custom handlers
            if group_id in self._group_handlers:
                del self._group_handlers[group_id]

    def add_element_to_group(self, element: Any, group_id: Any) -> None:
        """
        Add an element to a group.

        Args:
            element: The UI element to add.
            group_id: The identifier for the group.
        """
        with mutex_lock():
            # Register the group if not present
            if group_id not in self._group_registry:
                self._group_registry[group_id] = set()
                logger.debug(f"Created group {group_id}")

            # Add element to group
            self._group_registry[group_id].add(element)
            logger.debug(f"Added element {element} to group {group_id}")

            # If the group is blocked by any operations, block the element too
            for operation, blocked_elements in self._active_operations.items():
                if group_id in blocked_elements:
                    self._block_element(element, operation)

    def remove_element_from_group(self, element: Any, group_id: Any) -> None:
        """
        Remove an element from a group.

        Args:
            element: The UI element to remove.
            group_id: The identifier for the group.
        """
        with mutex_lock():
            # Remove element from group
            if group_id in self._group_registry and element in self._group_registry[group_id]:
                self._group_registry[group_id].remove(element)
                logger.debug(f"Removed element {element} from group {group_id}")

    def block_element(self, element: Any, operation: Any) -> None:
        """
        Block a UI element due to an operation.

        Args:
            element: The UI element to block.
            operation: The operation blocking the element.
        """
        with mutex_lock():
            self._block_element(element, operation)

    def unblock_element(self, element: Any, operation: Any) -> None:
        """
        Unblock a UI element from an operation.

        Args:
            element: The UI element to unblock.
            operation: The operation to unblock.
        """
        with mutex_lock():
            self._unblock_element(element, operation)

    def block_group(self, group_id: Any, operation: Any) -> None:
        """
        Block a group of UI elements.

        Args:
            group_id: The identifier for the group.
            operation: The operation blocking the group.
        """
        with mutex_lock():
            if group_id not in self._group_registry:
                logger.warning(f"Group {group_id} not found")
                return

            # Add group to active operations
            if operation not in self._active_operations:
                self._active_operations[operation] = set()
            self._active_operations[operation].add(group_id)

            # Call group block handler if available
            if group_id in self._group_handlers and self._group_handlers[group_id][0]:
                try:
                    self._group_handlers[group_id][0](group_id, operation)
                except Exception as e:
                    logger.error(f"Error in group block handler for {group_id}: {e}")

            # Block all elements in the group
            for element in self._group_registry[group_id]:
                self._block_element(element, operation)

            logger.debug(f"Blocked group {group_id} for operation {operation}")

            # Emit signal
            self.signals.element_blocked.emit(group_id, operation)

    def unblock_group(self, group_id: Any, operation: Any) -> None:
        """
        Unblock a group of UI elements.

        Args:
            group_id: The identifier for the group.
            operation: The operation to unblock.
        """
        with mutex_lock():
            if group_id not in self._group_registry:
                logger.warning(f"Group {group_id} not found")
                return

            # Remove group from active operations
            if (
                operation in self._active_operations
                and group_id in self._active_operations[operation]
            ):
                self._active_operations[operation].remove(group_id)
                if not self._active_operations[operation]:
                    del self._active_operations[operation]

            # Call group unblock handler if available
            if group_id in self._group_handlers and self._group_handlers[group_id][1]:
                try:
                    self._group_handlers[group_id][1](group_id, operation)
                except Exception as e:
                    logger.error(f"Error in group unblock handler for {group_id}: {e}")

            # Unblock all elements in the group
            for element in self._group_registry[group_id]:
                self._unblock_element(element, operation)

            logger.debug(f"Unblocked group {group_id} for operation {operation}")

            # Emit signal
            self.signals.element_unblocked.emit(group_id, operation)

    def start_operation(
        self,
        operation: Any,
        elements: Optional[List[Any]] = None,
        groups: Optional[List[Any]] = None,
        operation_name: str = "",
    ) -> None:
        """
        Start a blocking operation.

        Args:
            operation: The operation to start.
            elements: Optional list of elements to block.
            groups: Optional list of groups to block.
            operation_name: Optional name for the operation (for logging).
        """
        with mutex_lock():
            if operation not in self._active_operations:
                self._active_operations[operation] = set()

            # Block elements
            if elements:
                for element in elements:
                    self.block_element(element, operation)

            # Block groups
            if groups:
                for group in groups:
                    self.block_group(group, operation)

            # Update debug info
            self._debug_info["last_operation_time"] = time.time()
            self._update_debug_info()

            # Calculate affected elements for signal
            affected_elements = set()
            if elements:
                affected_elements.update(elements)
            if groups:
                for group in groups:
                    if group in self._group_registry:
                        affected_elements.update(self._group_registry[group])

            logger.debug(f"Started operation {operation_name or operation}")

            # Emit signal
            self.signals.operation_started.emit(operation, affected_elements)

    def end_operation(self, operation: Any) -> None:
        """
        End a blocking operation.

        Args:
            operation: The operation to end.
        """
        with mutex_lock():
            if operation not in self._active_operations:
                logger.warning(f"Operation {operation} not active")
                return

            # Get a copy of the affected elements/groups
            affected_elements = set()
            elements_to_unblock = set()

            # Collect elements blocked by this operation
            for element, operations in self._element_registry.items():
                if operation in operations:
                    affected_elements.add(element)
                    elements_to_unblock.add(element)

            # Collect groups blocked by this operation
            groups_to_unblock = set()
            for group_id in self._group_registry:
                if (
                    operation in self._active_operations
                    and group_id in self._active_operations[operation]
                ):
                    groups_to_unblock.add(group_id)
                    if group_id in self._group_registry:
                        affected_elements.update(self._group_registry[group_id])

            # Unblock groups first (to handle custom group handlers)
            for group_id in groups_to_unblock:
                self.unblock_group(group_id, operation)

            # Unblock individual elements
            for element in elements_to_unblock:
                self.unblock_element(element, operation)

            # Remove operation from active operations
            if operation in self._active_operations:
                del self._active_operations[operation]

            # Update debug info
            self._debug_info["last_operation_time"] = time.time()
            self._update_debug_info()

            logger.debug(f"Ended operation {operation}")

            # Emit signal
            self.signals.operation_ended.emit(operation, affected_elements)

    def is_element_blocked(self, element: Any) -> bool:
        """
        Check if an element is currently blocked.

        Args:
            element: The UI element to check.

        Returns:
            bool: True if the element is blocked, False otherwise.
        """
        with mutex_lock():
            if element not in self._element_registry:
                return False

            return bool(self._element_registry[element])

    def get_element_blocking_operations(self, element: Any) -> Set[Any]:
        """
        Get the operations currently blocking an element.

        Args:
            element: The UI element to check.

        Returns:
            Set[Any]: Set of operations blocking the element.
        """
        with mutex_lock():
            if element not in self._element_registry:
                return set()

            return set(self._element_registry[element])

    def is_group_blocked(self, group_id: Any) -> bool:
        """
        Check if a group is currently blocked.

        Args:
            group_id: The group identifier to check.

        Returns:
            bool: True if the group is blocked, False otherwise.
        """
        with mutex_lock():
            if group_id not in self._group_registry:
                return False

            # Check if group is directly blocked by any operation
            for operation, blocked_elements in self._active_operations.items():
                if group_id in blocked_elements:
                    return True

            # Check if all elements in the group are blocked
            if not self._group_registry[group_id]:
                return False

            return all(
                self.is_element_blocked(element) for element in self._group_registry[group_id]
            )

    def is_operation_active(self, operation: Any) -> bool:
        """
        Check if an operation is active.

        Args:
            operation: The operation to check.

        Returns:
            bool: True if the operation is active, False otherwise.
        """
        with mutex_lock():
            return operation in self._active_operations

    def is_element_in_group(self, element: Any, group_id: Any) -> bool:
        """
        Check if an element is in a specific group.

        Args:
            element: The UI element to check.
            group_id: The identifier for the group.

        Returns:
            bool: True if the element is in the group, False otherwise.
        """
        with mutex_lock():
            return group_id in self._group_registry and element in self._group_registry[group_id]

    def get_active_operations(self) -> Set[Any]:
        """
        Get the set of active operations.

        Returns:
            Set[Any]: Set of active operations.
        """
        with mutex_lock():
            return set(self._active_operations.keys())

    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about the manager state.

        Returns:
            Dict[str, Any]: Dictionary of debug information.
        """
        with mutex_lock():
            # Update debug info before returning
            self._update_debug_info()
            return self._debug_info.copy()

    def _block_element(self, element: Any, operation: Any) -> None:
        """
        Internal method to block an element.

        Args:
            element: The UI element to block.
            operation: The operation blocking the element.
        """
        # Register element if not already registered
        if element not in self._element_registry:
            self._element_registry[element] = set()

        # Check if already blocked by this operation
        if operation in self._element_registry[element]:
            return

        # Add to blocking operations
        self._element_registry[element].add(operation)

        # Use custom handler if available
        if element in self._element_handlers and self._element_handlers[element][0]:
            try:
                self._element_handlers[element][0](element, operation)
            except Exception as e:
                logger.error(f"Error in element block handler for {element}: {e}")
        # Use BlockableElementMixin if available
        elif hasattr(element, "block"):
            try:
                element.block(operation)
            except Exception as e:
                logger.error(f"Error in element.block() for {element}: {e}")
        # Default: disable QWidget
        elif hasattr(element, "setEnabled"):
            try:
                element.setEnabled(False)
            except Exception as e:
                logger.error(f"Error in element.setEnabled(False) for {element}: {e}")
        else:
            logger.warning(f"No blocking mechanism available for element {element}")

        # Emit signal
        self.signals.element_blocked.emit(element, operation)
        self.signals.blocking_state_changed.emit(element, True, self._element_registry[element])

    def _unblock_element(self, element: Any, operation: Any) -> None:
        """
        Internal method to unblock an element.

        Args:
            element: The UI element to unblock.
            operation: The operation to unblock.
        """
        # Check if element is registered
        if element not in self._element_registry:
            return

        # Check if blocked by this operation
        if operation not in self._element_registry[element]:
            return

        # Remove from blocking operations
        self._element_registry[element].remove(operation)

        # Only unblock if no more operations are blocking
        if not self._element_registry[element]:
            # Use custom handler if available
            if element in self._element_handlers and self._element_handlers[element][1]:
                try:
                    self._element_handlers[element][1](element, operation)
                except Exception as e:
                    logger.error(f"Error in element unblock handler for {element}: {e}")
            # Use BlockableElementMixin if available
            elif hasattr(element, "unblock"):
                try:
                    element.unblock(operation)
                except Exception as e:
                    logger.error(f"Error in element.unblock() for {element}: {e}")
            # Default: enable QWidget
            elif hasattr(element, "setEnabled"):
                try:
                    element.setEnabled(True)
                except Exception as e:
                    logger.error(f"Error in element.setEnabled(True) for {element}: {e}")
            else:
                logger.warning(f"No unblocking mechanism available for element {element}")

        # Emit signal
        self.signals.element_unblocked.emit(element, operation)
        self.signals.blocking_state_changed.emit(
            element, bool(self._element_registry[element]), self._element_registry[element]
        )

    def _update_debug_info(self) -> None:
        """Update the debug information dictionary."""
        self._debug_info["element_registry_size"] = len(self._element_registry)
        self._debug_info["active_operations_count"] = len(self._active_operations)
        self._debug_info["groups_count"] = len(self._group_registry)

        # Count blocked elements
        blocked_elements = 0
        for element, operations in self._element_registry.items():
            if operations:
                blocked_elements += 1
        self._debug_info["blocked_elements_count"] = blocked_elements

        # Get active operations details
        active_operations_details = {}
        for operation, blocked_elements in self._active_operations.items():
            active_operations_details[str(operation)] = len(blocked_elements)
        self._debug_info["active_operations_details"] = active_operations_details
