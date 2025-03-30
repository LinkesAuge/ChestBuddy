"""
error_handling_controller.py

Description: Controller for error handling in the ChestBuddy application
Usage:
    controller = ErrorHandlingController(signal_manager)
    controller.show_error("Error message")
    controller.handle_exception(exception, "Operation failed")
"""

import logging
import sys
import traceback
from enum import Enum, auto
from typing import Callable, Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMessageBox, QApplication

from chestbuddy.core.controllers.base_controller import BaseController

# Set up logger
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """
    Enumeration of error types for categorization.

    These categories help with appropriate error handling and presentation.
    """

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    DATA_ERROR = auto()
    VALIDATION_ERROR = auto()
    FILE_ERROR = auto()
    SYSTEM_ERROR = auto()
    UI_ERROR = auto()


class ErrorHandlingController(BaseController):
    """
    Controller for centralized error handling in ChestBuddy.

    This class provides a consistent interface for error handling,
    error display, and error logging across the application.

    Attributes:
        error_occurred (Signal): Emitted when an error occurs
        warning_occurred (Signal): Emitted when a warning occurs
        info_occurred (Signal): Emitted when an info message occurs
        exception_occurred (Signal): Emitted when an exception is handled
    """

    # Define signals
    error_occurred = Signal(str, object)  # message, error_type
    warning_occurred = Signal(str, object)  # message, error_type
    info_occurred = Signal(str, object)  # message, error_type
    exception_occurred = Signal(str, Exception, object)  # message, exception, error_type

    def __init__(self, signal_manager=None, parent=None):
        """
        Initialize the ErrorHandlingController.

        Args:
            signal_manager: Optional SignalManager instance for connection tracking
            parent: Parent object
        """
        super().__init__(signal_manager, parent)
        self._progress_controller = None
        self._last_error = None
        self._error_handlers: Dict[ErrorType, Callable] = {}

    def set_progress_controller(self, progress_controller) -> None:
        """
        Set the progress controller for integration with progress operations.

        Args:
            progress_controller: The progress controller instance
        """
        self._progress_controller = progress_controller

    def register_error_handler(self, error_type: ErrorType, handler: Callable) -> None:
        """
        Register a custom handler for a specific error type.

        Args:
            error_type: The type of error to handle
            handler: The callback function to handle the error
        """
        self._error_handlers[error_type] = handler

    def show_message(
        self,
        message: str,
        error_type: ErrorType = ErrorType.INFO,
        title: str = None,
        details: str = None,
        parent=None,
    ) -> None:
        """
        Show a message to the user with appropriate styling based on error type.

        Args:
            message: The message to display
            error_type: The type of error (determines icon and title)
            title: Optional custom title (defaults to type-based title)
            details: Optional detailed information to show in expandable area
            parent: Parent widget for the message box
        """
        # Log the message based on error type
        self._log_message(message, error_type, details)

        # Check if we have a custom handler for this error type
        if error_type in self._error_handlers:
            self._error_handlers[error_type](message, error_type, title, details)
            return

        # Update progress dialog if applicable
        self._update_progress_dialog(message, error_type)

        # Determine message box type and default title
        if title is None:
            title = self._get_default_title(error_type)

        # Show the message box
        parent = parent or QApplication.activeWindow()

        if error_type in (
            ErrorType.ERROR,
            ErrorType.DATA_ERROR,
            ErrorType.FILE_ERROR,
            ErrorType.SYSTEM_ERROR,
            ErrorType.CRITICAL,
        ):
            self._show_error_message(message, title, details, parent)
            self.error_occurred.emit(message, error_type)

        elif error_type in (ErrorType.WARNING, ErrorType.VALIDATION_ERROR):
            self._show_warning_message(message, title, details, parent)
            self.warning_occurred.emit(message, error_type)

        else:  # INFO or UI_ERROR
            self._show_info_message(message, title, details, parent)
            self.info_occurred.emit(message, error_type)

        # Store the last error
        self._last_error = {"message": message, "type": error_type, "details": details}

    def show_error(
        self, message: str, title: str = "Error", details: str = None, parent=None
    ) -> None:
        """
        Show an error message to the user.

        Args:
            message: The error message
            title: Optional title for the error dialog
            details: Optional detailed information
            parent: Parent widget for the message box
        """
        self.show_message(message, ErrorType.ERROR, title, details, parent)

    def show_warning(
        self, message: str, title: str = "Warning", details: str = None, parent=None
    ) -> None:
        """
        Show a warning message to the user.

        Args:
            message: The warning message
            title: Optional title for the warning dialog
            details: Optional detailed information
            parent: Parent widget for the message box
        """
        self.show_message(message, ErrorType.WARNING, title, details, parent)

    def show_info(
        self, message: str, title: str = "Information", details: str = None, parent=None
    ) -> None:
        """
        Show an information message to the user.

        Args:
            message: The information message
            title: Optional title for the info dialog
            details: Optional detailed information
            parent: Parent widget for the message box
        """
        self.show_message(message, ErrorType.INFO, title, details, parent)

    def handle_exception(
        self,
        exception: Exception,
        context: str = "",
        error_type: ErrorType = ErrorType.SYSTEM_ERROR,
        show_message: bool = True,
        parent=None,
    ) -> None:
        """
        Handle an exception with appropriate logging and user feedback.

        Args:
            exception: The exception that occurred
            context: Contextual information about what operation was being performed
            error_type: The type of error this exception represents
            show_message: Whether to show a message to the user
            parent: Parent widget for the message box
        """
        # Format exception details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Create message with context
        context_str = f"{context}: " if context else ""
        message = f"{context_str}{str(exception)}"

        # Log the exception
        logger.error(f"Exception: {message}\n{tb_str}")

        # Emit signal
        self.exception_occurred.emit(message, exception, error_type)

        # Show message to user if requested
        if show_message:
            self.show_message(message, error_type, details=tb_str, parent=parent)

    def log_error(
        self, message: str, error_type: ErrorType = ErrorType.ERROR, details: str = None
    ) -> None:
        """
        Log an error without displaying it to the user.

        Args:
            message: The error message
            error_type: The type of error
            details: Optional detailed information
        """
        self._log_message(message, error_type, details)

    def get_last_error(self) -> Dict[str, Any]:
        """
        Get information about the last error that occurred.

        Returns:
            Dict with 'message', 'type', and 'details' keys, or None if no error
        """
        return self._last_error

    def clear_last_error(self) -> None:
        """Clear the last error record."""
        self._last_error = None

    def _log_message(self, message: str, error_type: ErrorType, details: str = None) -> None:
        """
        Log a message with appropriate severity based on error type.

        Args:
            message: The message to log
            error_type: The type of error
            details: Optional detailed information
        """
        log_message = message
        if details:
            log_message = f"{message}\nDetails: {details}"

        if error_type in (ErrorType.CRITICAL, ErrorType.SYSTEM_ERROR):
            logger.critical(log_message)
        elif error_type in (ErrorType.ERROR, ErrorType.DATA_ERROR, ErrorType.FILE_ERROR):
            logger.error(log_message)
        elif error_type in (ErrorType.WARNING, ErrorType.VALIDATION_ERROR):
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _update_progress_dialog(self, message: str, error_type: ErrorType) -> None:
        """
        Update any active progress dialog with the error information.

        Args:
            message: The error message
            error_type: The type of error
        """
        if not self._progress_controller:
            return

        # Only update for errors, not warnings or info
        if error_type in (
            ErrorType.ERROR,
            ErrorType.DATA_ERROR,
            ErrorType.FILE_ERROR,
            ErrorType.SYSTEM_ERROR,
            ErrorType.CRITICAL,
        ):
            if self._progress_controller.is_progress_showing():
                self._progress_controller.finish_progress(f"Error: {message}", is_error=True)

    def _get_default_title(self, error_type: ErrorType) -> str:
        """
        Get a default title based on the error type.

        Args:
            error_type: The type of error

        Returns:
            str: A default title for the message box
        """
        if error_type == ErrorType.INFO:
            return "Information"
        elif error_type == ErrorType.WARNING:
            return "Warning"
        elif error_type == ErrorType.ERROR:
            return "Error"
        elif error_type == ErrorType.CRITICAL:
            return "Critical Error"
        elif error_type == ErrorType.DATA_ERROR:
            return "Data Error"
        elif error_type == ErrorType.VALIDATION_ERROR:
            return "Validation Error"
        elif error_type == ErrorType.FILE_ERROR:
            return "File Error"
        elif error_type == ErrorType.SYSTEM_ERROR:
            return "System Error"
        elif error_type == ErrorType.UI_ERROR:
            return "UI Error"
        else:
            return "Error"

    def _show_error_message(self, message: str, title: str, details: str, parent) -> None:
        """
        Show an error message box to the user.

        Args:
            message: The error message
            title: Title for the error dialog
            details: Optional detailed information
            parent: Parent widget for the message box
        """
        msg_box = QMessageBox(QMessageBox.Critical, title, message, QMessageBox.Ok, parent)

        if details:
            msg_box.setDetailedText(details)

        msg_box.exec()

    def _show_warning_message(self, message: str, title: str, details: str, parent) -> None:
        """
        Show a warning message box to the user.

        Args:
            message: The warning message
            title: Title for the warning dialog
            details: Optional detailed information
            parent: Parent widget for the message box
        """
        msg_box = QMessageBox(QMessageBox.Warning, title, message, QMessageBox.Ok, parent)

        if details:
            msg_box.setDetailedText(details)

        msg_box.exec()

    def _show_info_message(self, message: str, title: str, details: str, parent) -> None:
        """
        Show an information message box to the user.

        Args:
            message: The information message
            title: Title for the info dialog
            details: Optional detailed information
            parent: Parent widget for the message box
        """
        msg_box = QMessageBox(QMessageBox.Information, title, message, QMessageBox.Ok, parent)

        if details:
            msg_box.setDetailedText(details)

        msg_box.exec()
