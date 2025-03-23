"""
UI State Context.

This module defines context managers for UI blocking operations,
ensuring that UI elements are properly blocked and unblocked.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Set, Union, Tuple

from PySide6.QtCore import QObject

from chestbuddy.utils.ui_state.constants import UIOperations

# Set up logger
logger = logging.getLogger(__name__)


class OperationContext:
    """
    Context manager for UI blocking operations.

    This class provides a context manager that automatically blocks UI elements
    when entering the context and unblocks them when exiting, even if an
    exception occurs.

    Example:
        ```python
        # Block the main window during import
        with OperationContext(ui_state_manager, UIOperations.IMPORT, [UIElementGroups.MAIN_WINDOW]):
            # Import data, UI is blocked
            import_csv_data()
        # UI is automatically unblocked when the context exits
        ```

    Implementation Notes:
        - Handles proper cleanup even if exceptions occur
        - Works with UIStateManager to track operations
        - Can block multiple elements or groups at once
    """

    def __init__(
        self,
        ui_state_manager,
        operation: Any,
        elements: Optional[List[Any]] = None,
        groups: Optional[List[Any]] = None,
        operation_name: str = "",
        check_active: bool = True,
    ) -> None:
        """
        Initialize the operation context.

        Args:
            ui_state_manager: The UIStateManager instance.
            operation: The operation to perform (e.g., UIOperations.IMPORT).
            elements: Optional list of UI elements to block.
            groups: Optional list of element groups to block.
            operation_name: Optional name for the operation (for logging).
            check_active: Whether to check if the operation is already active.
        """
        self._ui_state_manager = ui_state_manager
        self._operation = operation
        self._elements = elements or []
        self._groups = groups or []
        self._operation_name = operation_name or str(operation)
        self._check_active = check_active
        self._is_active = False

        # For tracking errors
        self._exception = None
        self._traceback = None

    def __enter__(self) -> "OperationContext":
        """
        Enter the context, blocking UI elements.

        Returns:
            The OperationContext instance.
        """
        if self._check_active and self._ui_state_manager.is_operation_active(self._operation):
            logger.warning(f"Operation {self._operation_name} is already active")
            return self

        try:
            # Start the operation
            self._ui_state_manager.start_operation(
                self._operation, self._elements, self._groups, self._operation_name
            )
            self._is_active = True
            logger.debug(f"Started operation {self._operation_name}")
        except Exception as e:
            logger.error(f"Error starting operation {self._operation_name}: {e}")
            self._exception = e
            self._traceback = traceback.format_exc()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context, unblocking UI elements.

        Args:
            exc_type: The exception type, if an exception occurred.
            exc_val: The exception value, if an exception occurred.
            exc_tb: The exception traceback, if an exception occurred.

        Returns:
            bool: True if the exception was handled, False otherwise.
        """
        if not self._is_active:
            logger.debug(f"Operation {self._operation_name} was not active, nothing to end")
            return False

        try:
            # Record any exception that occurred
            if exc_type is not None:
                self._exception = exc_val
                self._traceback = exc_tb
                logger.error(f"Operation {self._operation_name} failed: {exc_val}")

            # End the operation
            self._ui_state_manager.end_operation(self._operation)
            logger.debug(f"Ended operation {self._operation_name}")
        except Exception as e:
            logger.error(f"Error ending operation {self._operation_name}: {e}")
            # Don't override the original exception
            if self._exception is None:
                self._exception = e
                self._traceback = traceback.format_exc()

        self._is_active = False
        return False  # Let the exception propagate

    def is_active(self) -> bool:
        """
        Check if the operation is currently active.

        Returns:
            bool: True if the operation is active, False otherwise.
        """
        return self._is_active

    def get_exception(self) -> Tuple[Optional[Exception], Optional[str]]:
        """
        Get any exception that occurred during the operation.

        Returns:
            Tuple of (exception, traceback) or (None, None) if no exception occurred.
        """
        return self._exception, self._traceback


class ManualOperationContext(OperationContext):
    """
    Context manager for manual UI blocking operations.

    This class extends OperationContext with methods to manually start and end
    the operation, instead of using the context manager protocol.

    Example:
        ```python
        # Create the context
        context = ManualOperationContext(ui_state_manager, UIOperations.IMPORT, [UIElementGroups.MAIN_WINDOW])

        # Start the operation (block UI)
        context.start()

        # Do work...

        # End the operation (unblock UI)
        context.end()
        ```

    Implementation Notes:
        - Provides more control over when blocking starts and ends
        - Useful for operations that don't fit neatly into a with block
        - Still ensures proper cleanup with try/finally
    """

    def start(self) -> "ManualOperationContext":
        """
        Manually start the operation, blocking UI elements.

        Returns:
            The ManualOperationContext instance.
        """
        return self.__enter__()

    def end(self) -> None:
        """
        Manually end the operation, unblocking UI elements.
        """
        self.__exit__(None, None, None)
