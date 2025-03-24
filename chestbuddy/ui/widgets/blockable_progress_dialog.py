"""
blockable_progress_dialog.py

Description: A progress dialog that integrates with the UI State Management System
"""

import logging
from typing import List, Optional, Tuple, Type, Any, Union

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QWidget

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

    def show_with_blocking(
        self,
        operation: UIOperations,
        operation_name: Optional[str] = None,
        elements: List[QWidget] = None,
        groups: List[UIElementGroups] = None,
    ) -> None:
        """
        Show the dialog and block specified UI elements or groups.

        Args:
            operation: The operation type being performed
            operation_name: Optional custom name for the operation
            elements: Specific UI elements to block
            groups: UI element groups to block
        """
        if elements is None:
            elements = []
        if groups is None:
            groups = []

        # Check if operation is already active to avoid creating duplicate contexts
        if self._ui_state_manager.is_operation_active(operation):
            logger.warning(
                f"Operation {operation} is already active, not creating duplicate context"
            )
            # Store operation for later use in _end_operation
            self._operation = operation
            # Show the dialog without creating a new blocking context
            self.show()
            return

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

        # Show the dialog
        self.show()

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
        """End the current UI blocking operation."""
        # First, check if we have an operation but no context
        if self._operation and not self._operation_context:
            logger.debug(f"No operation context for {self._operation}, checking if active directly")
            if self._ui_state_manager.is_operation_active(self._operation):
                logger.warning(
                    f"Operation {self._operation} is active without a context, ending directly"
                )
                try:
                    self._ui_state_manager.end_operation(self._operation)
                    self._operation = None
                    return
                except Exception as e:
                    logger.error(f"Error ending operation {self._operation} directly: {e}")

        # Handle normal case with operation context
        if self._operation_context and self._operation_context.is_active():
            logger.debug(f"Ending blocking operation {self._operation}")

            # Check for exceptions in the operation context
            exception_info = self._operation_context.get_exception()
            if exception_info:
                exception, traceback = exception_info
                logger.error(f"Operation {self._operation} ended with exception: {exception}")
                logger.debug(f"Traceback: {traceback}")

            # End the operation context
            try:
                self._operation_context.end()
            except Exception as e:
                logger.error(f"Error ending operation context: {e}")
                # Try direct operation end as fallback
                if self._operation and self._ui_state_manager.is_operation_active(self._operation):
                    logger.warning(
                        f"Attempting direct operation end for {self._operation} after context error"
                    )
                    try:
                        self._ui_state_manager.end_operation(self._operation)
                    except Exception as direct_e:
                        logger.error(f"Error ending operation directly: {direct_e}")

            # Clear references
            self._operation_context = None
            self._operation = None
