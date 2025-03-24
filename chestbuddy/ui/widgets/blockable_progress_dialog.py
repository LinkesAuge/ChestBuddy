"""
blockable_progress_dialog.py

Description: A progress dialog that integrates with the UI State Management System
"""

import logging
from typing import List, Optional, Tuple, Type, Any, Union

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget, QApplication

from chestbuddy.ui.widgets.progress_dialog import ProgressDialog
from chestbuddy.utils.ui_state import (
    UIStateManager,
    UIElementGroups,
    UIOperations,
    ManualOperationContext,
)

logger = logging.getLogger(__name__)


class BlockableProgressDialog(ProgressDialog):
    """
    A progress dialog that integrates with the UI State Management System.

    This dialog can automatically block UI elements while it is displayed
    and unblock them when it's closed.

    Usage Example:
        ```python
        # Create a progress dialog
        dialog = BlockableProgressDialog(
            "Processing Files",
            "Cancel",
            0, 100,
            parent=self
        )

        # Show with blocking (non-modal)
        dialog.show_with_blocking(
            UIOperations.IMPORT,
            groups=[UIElementGroups.DATA_VIEW, UIElementGroups.MENU_BAR]
        )

        # Or execute with blocking (modal)
        result = dialog.exec_with_blocking(
            UIOperations.EXPORT,
            groups=[UIElementGroups.DATA_VIEW]
        )
        ```
    """

    def __init__(
        self,
        title: str,
        cancel_button_text: str,
        minimum: int,
        maximum: int,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the blockable progress dialog.

        Args:
            title: The dialog title
            cancel_button_text: Text for the cancel button
            minimum: The minimum progress value
            maximum: The maximum progress value
            parent: The parent widget
        """
        super().__init__(title, cancel_button_text, minimum, maximum, parent)

        # Get UI state manager instance
        self._ui_state_manager = UIStateManager()

        # Initialize operation context to None
        self._operation_context = None
        self._operation = None

        logger.debug(f"Created BlockableProgressDialog: {title}")

    def show_with_blocking(self, operation, blocked_groups=None) -> None:
        """
        Show the dialog and block UI elements for the given operation.

        If the operation is already active, reuse that context instead of
        creating a new one.

        Args:
            operation: The operation to start (from UIOperations enum)
            blocked_groups: List of UI element groups to block (from UIElementGroups)
        """
        if blocked_groups is None:
            blocked_groups = []

        logger.debug(f"Showing progress dialog with blocking for operation {operation}")

        # Store the operation for _end_operation to use later
        self._operation = operation

        # Check if operation is already active
        already_active = False
        try:
            already_active = self._ui_state_manager.has_active_operations(operation)
            if already_active:
                logger.warning(f"Operation {operation} already active when showing dialog")
        except Exception as e:
            logger.error(f"Error checking if operation {operation} is active: {e}")
            # If we can't check, assume it's not active for safety
            already_active = False

        if already_active:
            logger.debug(
                f"Operation {operation} already active, attempting to reuse existing context"
            )

            # Try to get active context from UIStateManager
            try:
                active_operations = self._ui_state_manager.get_active_operations()
                if operation in active_operations:
                    # Reuse the existing context
                    self._operation_context = active_operations[operation]
                    logger.debug(f"Reusing existing context for operation {operation}")

                    # Just show the dialog without creating a new blocking context
                    self.show()
                    self.raise_()
                    self.activateWindow()

                    # Log some debug info about the operation
                    logger.debug(
                        f"Active operation {operation} has {len(blocked_groups)} blocked groups"
                    )
                    return
                else:
                    logger.warning(f"Operation {operation} marked active but no context found")
                    # We need to restart the operation since something is inconsistent
            except Exception as e:
                logger.error(f"Error getting active operations: {e}")
                # Continue to start a new operation due to the error

        # At this point we need to start a new operation
        logger.debug(f"Starting new operation {operation} with blocked groups: {blocked_groups}")

        # End any existing operation with this name first
        try:
            if already_active:
                logger.warning(f"Ending existing operation {operation} before starting a new one")
                self._ui_state_manager.end_operation(operation)
        except Exception as e:
            logger.error(f"Error ending existing operation {operation}: {e}")

        # Now start a fresh operation
        try:
            # Create a new operation context - this should automatically register with the manager
            self._operation_context = self._ui_state_manager.start_operation(
                operation, groups=blocked_groups
            )

            # Show the dialog
            self.show()
            logger.debug(f"Started new operation {operation} successfully")

            # Verify the operation was started correctly
            if not self._ui_state_manager.is_operation_active(operation):
                logger.error(f"Failed to start operation {operation} - not active after starting")
        except Exception as e:
            logger.error(f"Failed to start operation {operation}: {e}")
            # Show the dialog anyway but log the error
            self.show()
            self._operation_context = None

        # Process events to ensure UI updates properly
        QApplication.processEvents()

    def exec_with_blocking(
        self,
        operation: UIOperations,
        operation_name: Optional[str] = None,
        elements: List[QWidget] = None,
        groups: List[UIElementGroups] = None,
    ) -> int:
        """
        Execute the dialog modally and block specified UI elements or groups.

        Args:
            operation: The operation type being performed
            operation_name: Optional custom name for the operation
            elements: Specific UI elements to block
            groups: UI element groups to block

        Returns:
            The dialog result code
        """
        if elements is None:
            elements = []
        if groups is None:
            groups = []

        # Create operation context
        self._operation = operation
        self._operation_context = ManualOperationContext(
            self._ui_state_manager,
            operation,
            elements=elements,
            groups=groups,
            operation_name=str(operation) if operation_name is None else operation_name,
        )

        # Start blocking operation
        logger.debug(
            f"Starting blocking operation {operation} with groups {groups} "
            f"and {len(elements)} elements"
        )
        self._operation_context.start()

        try:
            # Execute the dialog
            result = self.exec()
            return result
        finally:
            # End the operation when dialog is closed
            self._end_operation()

    def closeEvent(self, event):
        """
        Handle close events for the dialog.

        Args:
            event: The close event
        """
        # End the operation if it's active
        self._end_operation()

        # Call the parent class close event
        super().closeEvent(event)

    def _end_operation(self) -> None:
        """
        End the blocking operation if one is active.

        This method handles three cases:
        1. We have a valid operation context - end it directly
        2. We know the operation type but have no context - try to end via UIStateManager
        3. The operation has already been ended - just log and continue
        """
        if not self._operation:
            logger.debug("No operation to end")
            return

        operation_name = str(self._operation)
        logger.debug(f"Ending operation {operation_name}")

        try:
            # First check if operation is still active
            is_active = False
            try:
                is_active = self._ui_state_manager.has_active_operations(self._operation)
                if not is_active:
                    logger.debug(f"Operation {operation_name} is already inactive")
            except Exception as e:
                logger.error(f"Error checking if operation {operation_name} is active: {e}")
                # If we can't check, assume it's active for safety
                is_active = True

            # Case 1: We have a valid operation context and operation is active
            if self._operation_context and is_active:
                logger.debug(f"Ending operation {operation_name} with context")
                try:
                    self._operation_context.end()
                    logger.debug(f"Successfully ended operation {operation_name} with context")
                except Exception as e:
                    logger.error(f"Error ending operation {operation_name} with context: {e}")
                    # Fall back to ending via UIStateManager
                    try:
                        logger.warning(f"Falling back to UIStateManager to end {operation_name}")
                        self._ui_state_manager.end_operation(self._operation)
                        logger.debug(f"Successfully ended {operation_name} via direct manager call")
                    except Exception as e2:
                        logger.error(
                            f"Critical error ending {operation_name}: both methods failed: {e2}"
                        )
                        self._force_end_operation(self._operation)

            # Case 2: We know the operation type but have no context or the context failed
            elif is_active:
                logger.warning(f"Ending operation {operation_name} without context")
                try:
                    # Direct call to end the operation
                    self._ui_state_manager.end_operation(self._operation)
                    logger.debug(f"Successfully ended operation {operation_name} directly")

                    # Verify it was actually ended
                    is_still_active = self._ui_state_manager.has_active_operations(self._operation)
                    if is_still_active:
                        logger.error(
                            f"Failed to end operation {operation_name} - still active after end call"
                        )
                        self._force_end_operation(self._operation)
                except Exception as e:
                    logger.error(f"Error ending operation {operation_name} directly: {e}")
                    self._force_end_operation(self._operation)

            # Case 3: Operation is already ended
            else:
                logger.debug(f"Operation {operation_name} was already ended")
        except Exception as e:
            logger.error(f"Unexpected error in _end_operation for {operation_name}: {e}")
            # Last resort recovery attempt
            self._force_end_operation(self._operation)
        finally:
            # Clear operation references regardless of outcome
            self._operation = None
            self._operation_context = None

            # Process events to ensure UI updates properly
            try:
                QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error processing events after ending operation: {e}")

    def _force_end_operation(self, operation):
        """
        Emergency last-resort method to force an operation to end by directly
        manipulating the state manager's internal data structures.

        This should only be used when all other methods fail, as it bypasses
        the normal cleanup procedures.

        Args:
            operation: The operation to forcibly end
        """
        logger.critical(f"EMERGENCY: Force ending operation {operation}")

        try:
            # Direct access to internal state as a last resort
            if hasattr(self._ui_state_manager, "_active_operations"):
                if operation in self._ui_state_manager._active_operations:
                    active_elements = self._ui_state_manager._active_operations[operation]
                    logger.critical(
                        f"Forcibly removing operation that had {len(active_elements)} active elements"
                    )
                    del self._ui_state_manager._active_operations[operation]
                    logger.debug("Successfully forced operation end")

                    # Try to unblock elements that might be blocked
                    for element, operations in self._ui_state_manager._element_registry.items():
                        if operation in operations:
                            try:
                                operations.remove(operation)
                                if hasattr(element, "setEnabled"):
                                    element.setEnabled(True)
                            except:
                                pass  # Ignore errors in cleanup
        except Exception as e:
            logger.critical(f"Failed emergency operation end: {e}")
