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

        # Store the operation for _end_operation to use later
        self._operation = operation

        # Check if operation is already active
        already_active = False
        try:
            already_active = self._ui_state_manager.is_operation_active(operation)
        except Exception as e:
            logger.error(f"Error checking if operation {operation} is active: {e}")
            # If we can't check, assume it's not active for safety
            already_active = False

        if already_active:
            logger.warning(f"Operation {operation} already active, reusing existing context")

            # Try to get active context from UIStateManager
            try:
                active_operations = self._ui_state_manager.get_active_operations()
                if operation in active_operations:
                    self._operation_context = active_operations[operation]
                    logger.debug(f"Reusing existing context for operation {operation}")
                else:
                    logger.warning(f"Operation {operation} marked active but no context found")
                    # End and restart the operation to ensure state consistency
                    try:
                        self._ui_state_manager.end_operation(operation)
                        logger.debug(f"Ended inconsistent operation {operation}")
                        already_active = False
                    except Exception as e:
                        logger.error(f"Error ending inconsistent operation {operation}: {e}")
                    self._operation_context = None
            except Exception as e:
                logger.error(f"Error getting active operations: {e}")
                self._operation_context = None
                already_active = False

            # Just show the dialog without creating a new blocking context if operation is active
            if already_active:
                self.show()
                self.raise_()
                self.activateWindow()
            return

        # If we get here, we need to start a new operation (either it wasn't active or we reset it)
        logger.debug(f"Starting new operation {operation}")
        try:
            self._operation_context = self._ui_state_manager.start_operation(
                operation, blocked_groups
            )
            # Only show the dialog if starting the operation was successful
            self.show()
            logger.debug(f"Operation {operation} started successfully")
        except Exception as e:
            logger.error(f"Failed to start operation {operation}: {e}")
            # Show the dialog anyway but log the error
            self.show()
            self._operation_context = None

        # Process events to ensure UI updates properly
        QApplication.processEvents()

        # Validate that operation started correctly
        try:
            if not self._ui_state_manager.is_operation_active(operation):
                logger.error(f"Failed to verify operation {operation} is active")
        except Exception as e:
            logger.error(f"Error validating operation {operation} state: {e}")

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

        try:
            # First check if operation is still active
            is_active = False
            try:
                is_active = self._ui_state_manager.is_operation_active(self._operation)
            except Exception as e:
                logger.error(f"Error checking if operation {self._operation} is active: {e}")
                # If we can't check, assume it's active for safety
                is_active = True

            # Case 1: We have a valid operation context
            if self._operation_context and is_active:
                logger.debug(f"Ending operation {self._operation} with context")
                try:
                    self._operation_context.end()
                    logger.debug(f"Successfully ended operation {self._operation} with context")
                except Exception as e:
                    logger.error(f"Error ending operation {self._operation} with context: {e}")
                    # Fall back to ending via UIStateManager
                    try:
                        self._ui_state_manager.end_operation(self._operation)
                        logger.debug(f"Fallback: ended operation {self._operation} via manager")
                    except Exception as e2:
                        logger.error(
                            f"Critical: failed both context and direct end for {self._operation}: {e2}"
                        )

            # Case 2: We know the operation type but have no context or context end failed
            elif is_active:
                logger.warning(f"Ending operation {self._operation} without context")
                try:
                    self._ui_state_manager.end_operation(self._operation)
                    logger.debug(f"Successfully ended operation {self._operation} via manager")
                except Exception as e:
                    logger.error(f"Error ending operation {self._operation} via manager: {e}")
                    # Try to end ALL operations as a last resort
                    try:
                        active_ops = self._ui_state_manager.get_active_operations()
                        if active_ops:
                            logger.warning(f"Attempting to end all operations: {active_ops.keys()}")
                            for op in active_ops:
                                if op != self._operation:  # Skip the one we already tried
                                    try:
                                        self._ui_state_manager.end_operation(op)
                                    except:
                                        pass  # Already logged enough errors
                    except:
                        pass  # Already in deep error handling, just continue
            # Case 3: Operation already ended
            else:
                logger.debug(f"Operation {self._operation} already ended")
        except Exception as e:
            logger.error(f"Unexpected error in _end_operation for {self._operation}: {e}")
        finally:
            # Clear operation references regardless of outcome
            self._operation = None
            self._operation_context = None

            # Process events to ensure UI updates properly
            try:
                QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error processing events after ending operation: {e}")
