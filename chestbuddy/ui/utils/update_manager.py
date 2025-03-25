"""
update_manager.py

Description: Provides a utility class for managing UI component updates.
Usage:
    from chestbuddy.ui.utils import UpdateManager

    # Create an instance
    update_manager = UpdateManager()

    # Schedule updates for components
    update_manager.schedule_update(my_component)

    # Register update dependencies
    update_manager.register_dependency(parent_component, child_component)
"""

import time
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from chestbuddy.ui.interfaces import IUpdatable

import logging

logger = logging.getLogger(__name__)

# Type for updatable components
T = TypeVar("T", bound=IUpdatable)


class UpdateManager(QObject):
    """
    Utility class for managing UI component updates.

    This class provides methods for scheduling updates with debouncing,
    batching updates, and tracking update dependencies.

    Attributes:
        update_scheduled (Signal): Signal emitted when an update is scheduled
        update_completed (Signal): Signal emitted when all updates are completed
        batch_update_started (Signal): Signal emitted when a batch update starts
        batch_update_completed (Signal): Signal emitted when a batch update completes
    """

    update_scheduled = Signal(object)  # Component that needs update
    update_completed = Signal(object)  # Component that was updated
    batch_update_started = Signal()
    batch_update_completed = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the update manager."""
        super().__init__(parent)
        self._timers: Dict[IUpdatable, QTimer] = {}
        self._pending_updates: Set[IUpdatable] = set()
        self._debounce_intervals: Dict[IUpdatable, int] = {}
        self._dependencies: Dict[IUpdatable, Set[IUpdatable]] = {}
        self._update_batch_in_progress: bool = False
        self._batch_timer = QTimer(self)
        self._batch_timer.setSingleShot(True)
        self._batch_timer.timeout.connect(self._process_batch)

    def schedule_update(self, component: T, debounce_ms: int = 50) -> None:
        """
        Schedule an update for a component with debouncing.

        Args:
            component: The component to update
            debounce_ms: Debounce interval in milliseconds
        """
        if not isinstance(component, IUpdatable):
            logger.warning(f"Component {component} is not updatable")
            return

        # Store debounce interval for this component
        self._debounce_intervals[component] = debounce_ms

        # Check if there's already a timer for this component
        if component in self._timers:
            # Timer exists, restart it
            self._timers[component].stop()
            self._timers[component].start(debounce_ms)
        else:
            # Create a new timer
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._update_component(component))
            self._timers[component] = timer
            timer.start(debounce_ms)

        # Add to pending updates
        self._pending_updates.add(component)

        # Emit signal
        self.update_scheduled.emit(component)
        logger.debug(f"Update scheduled for {component.__class__.__name__}")

    def schedule_batch_update(self, components: List[T], debounce_ms: int = 50) -> None:
        """
        Schedule updates for multiple components as a batch.

        Args:
            components: List of components to update
            debounce_ms: Debounce interval in milliseconds
        """
        # Schedule updates for all components
        for component in components:
            self.schedule_update(component, debounce_ms)

        # Start batch timer
        self._batch_timer.start(debounce_ms)

    def register_dependency(self, parent: T, child: T) -> None:
        """
        Register a dependency between components.

        When the parent component is updated, the child component will be updated as well.

        Args:
            parent: The parent component
            child: The child component that depends on the parent
        """
        if not isinstance(parent, IUpdatable) or not isinstance(child, IUpdatable):
            logger.warning(f"Component {parent} or {child} is not updatable")
            return

        # Initialize dependency set if needed
        if parent not in self._dependencies:
            self._dependencies[parent] = set()

        # Add dependency
        self._dependencies[parent].add(child)
        logger.debug(
            f"Registered dependency: {child.__class__.__name__} depends on {parent.__class__.__name__}"
        )

    def unregister_dependency(self, parent: T, child: T) -> None:
        """
        Unregister a dependency between components.

        Args:
            parent: The parent component
            child: The child component
        """
        if parent in self._dependencies and child in self._dependencies[parent]:
            self._dependencies[parent].remove(child)
            logger.debug(
                f"Unregistered dependency: {child.__class__.__name__} no longer depends on {parent.__class__.__name__}"
            )

    def has_pending_updates(self) -> bool:
        """
        Check if there are any pending updates.

        Returns:
            bool: True if there are pending updates, False otherwise
        """
        return len(self._pending_updates) > 0

    def cancel_updates(self) -> None:
        """Cancel all pending updates."""
        try:
            for timer in list(self._timers.values()):
                try:
                    timer.stop()
                except RuntimeError:
                    # Timer might have already been deleted
                    pass

            self._pending_updates.clear()
            logger.debug("All updates cancelled")
        except Exception as e:
            logger.error(f"Error cancelling updates: {e}")

    def cancel_component_update(self, component: T) -> None:
        """
        Cancel pending update for a specific component.

        Args:
            component: The component to cancel updates for
        """
        if component in self._timers:
            self._timers[component].stop()
            self._pending_updates.discard(component)
            logger.debug(f"Update cancelled for {component.__class__.__name__}")

    def _update_component(self, component: IUpdatable) -> None:
        """
        Update a component and its dependencies.

        Args:
            component: The component to update
        """
        if component not in self._pending_updates:
            return

        try:
            # Remove from pending updates
            self._pending_updates.discard(component)

            # Update the component
            if hasattr(component, "update") and callable(component.update):
                component.update()
                logger.debug(f"Updated {component.__class__.__name__}")
            else:
                logger.warning(f"Component {component.__class__.__name__} has no update method")

            # Update dependencies
            self._update_dependencies(component)

            # Emit signal
            self.update_completed.emit(component)
        except Exception as e:
            logger.error(f"Error updating {component.__class__.__name__}: {str(e)}")

    def _update_dependencies(self, parent: IUpdatable) -> None:
        """
        Update all dependencies of a component.

        Args:
            parent: The parent component whose dependencies should be updated
        """
        if parent not in self._dependencies:
            return

        for child in self._dependencies[parent]:
            self.schedule_update(child)
            logger.debug(f"Scheduled update for dependent {child.__class__.__name__}")

    def _process_batch(self) -> None:
        """Process all pending updates as a batch."""
        if self._update_batch_in_progress:
            return

        self._update_batch_in_progress = True
        self.batch_update_started.emit()
        logger.debug(f"Batch update started with {len(self._pending_updates)} components")

        # Create a copy of pending updates to avoid modification during iteration
        components = list(self._pending_updates)

        try:
            # Update all components
            for component in components:
                self._update_component(component)

            logger.debug("Batch update completed successfully")
        except Exception as e:
            logger.error(f"Error during batch update: {str(e)}")
        finally:
            self._update_batch_in_progress = False
            self.batch_update_completed.emit()

    def process_pending_updates(self) -> None:
        """Process all pending updates immediately."""
        self._process_batch()

    @Slot(IUpdatable)
    def on_component_update_requested(self, component: IUpdatable) -> None:
        """
        Slot for handling update_requested signals from components.

        Args:
            component: The component requesting an update
        """
        if not isinstance(component, IUpdatable):
            return

        debounce_ms = self._debounce_intervals.get(component, 50)
        self.schedule_update(component, debounce_ms)

    def __del__(self) -> None:
        """Clean up resources on deletion."""
        try:
            # Cancel updates
            self.cancel_updates()

            # Explicitly delete all timers
            for timer in list(self._timers.values()):
                try:
                    timer.stop()
                    timer.deleteLater()
                except RuntimeError:
                    # Timer might have already been deleted
                    pass

            # Clear collections
            self._timers.clear()
            self._pending_updates.clear()
            self._dependencies.clear()
            self._debounce_intervals.clear()
        except (RuntimeError, AttributeError, TypeError):
            # Handle cases where Qt objects are already deleted or app is shutting down
            pass
