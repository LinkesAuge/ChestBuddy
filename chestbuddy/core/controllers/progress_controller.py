"""
progress_controller.py

Description: Controller for progress reporting in the ChestBuddy application
Usage:
    controller = ProgressController(signal_manager)
    controller.start_progress("Loading", "Loading file...")
    controller.update_progress(50, 100, "Processing...")
    controller.finish_progress("Complete")
"""

import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from chestbuddy.ui.widgets import ProgressDialog, ProgressBar
from chestbuddy.core.controllers.base_controller import BaseController

# Set up logger
logger = logging.getLogger(__name__)


class ProgressController(BaseController):
    """
    Controller for progress reporting in ChestBuddy.

    This class handles progress dialog creation, progress updates,
    and cancellation for long-running operations.

    Attributes:
        progress_canceled (Signal): Emitted when progress is canceled
        progress_completed (Signal): Emitted when progress is completed
    """

    # Define signals
    progress_canceled = Signal()
    progress_completed = Signal()

    def __init__(self, signal_manager=None, parent=None):
        """
        Initialize the ProgressController.

        Args:
            signal_manager: Optional SignalManager instance for connection tracking
            parent: Parent object
        """
        super().__init__(signal_manager)
        self._progress_dialog = None
        self._cancel_callback = None
        self._is_cancelable = False

        # File loading state tracking
        self._loading_state = self._init_loading_state()
        self._total_rows_loaded = 0
        self._last_progress_current = 0
        self._file_loading_complete = False
        self._file_sizes = {}

    def _init_loading_state(self) -> Dict:
        """
        Initialize the loading state tracking dictionary.

        Returns:
            Dict: Empty loading state dictionary
        """
        return {
            "current_file": "",
            "current_file_index": 0,
            "processed_files": [],
            "total_files": 0,
            "total_rows": 0,
        }

    def start_progress(
        self,
        title: str,
        message: str,
        cancelable: bool = True,
        cancel_callback: Optional[Callable] = None,
    ) -> bool:
        """
        Start a progress operation with a progress dialog.

        Args:
            title: Title for the progress dialog
            message: Initial message to display
            cancelable: Whether the operation can be canceled
            cancel_callback: Callback function to call when canceled

        Returns:
            bool: True if progress dialog was successfully created
        """
        try:
            # If a dialog is already showing, update it instead of creating a new one
            if self._progress_dialog:
                logger.debug(
                    f"Progress dialog already exists, updating instead of creating new one"
                )
                self._progress_dialog.setLabelText(message)

                # Update cancel button if needed
                if cancelable != self._is_cancelable:
                    self._is_cancelable = cancelable
                    self._progress_dialog.setCancelButtonText("Cancel" if cancelable else "Close")

                # Update cancel callback
                self._cancel_callback = cancel_callback

                # Make sure dialog is visible and at the front
                self._progress_dialog.show()
                self._progress_dialog.raise_()
                self._progress_dialog.activateWindow()
                QApplication.processEvents()

                return True

            # Create a new progress dialog
            self._progress_dialog = ProgressDialog(
                message,  # label_text
                "Cancel" if cancelable else "Close",  # cancel_button_text
                0,  # minimum
                100,  # maximum
                QApplication.activeWindow(),  # parent
                title,  # title
                cancelable,  # show_cancel_button
            )

            # Set cancel callback
            self._cancel_callback = cancel_callback
            self._is_cancelable = cancelable

            # Prevent dialog dismissal for important operations
            if "CSV" in title or "Loading" in title or "Export" in title:
                self._progress_dialog.set_dismissable(False)

            # Connect signals
            self._progress_dialog.canceled.connect(self._on_cancel_clicked)

            # Reset loading state tracking
            self._loading_state = self._init_loading_state()
            self._total_rows_loaded = 0
            self._last_progress_current = 0
            self._file_loading_complete = False
            self._file_sizes = {}

            # Show the dialog
            self._progress_dialog.show()
            QApplication.processEvents()

            return True
        except Exception as e:
            logger.error(f"Error creating progress dialog: {e}")
            return False

    def update_progress(
        self,
        current: int,
        total: int,
        message: str = None,
        file_info: str = None,
        status_text: str = None,
    ) -> None:
        """
        Update the progress dialog with new progress information.

        Args:
            current: Current progress value
            total: Total progress value
            message: Optional new message to display
            file_info: Optional file information to display
            status_text: Optional status text to display
        """
        if not self._progress_dialog:
            return

        try:
            # Calculate percentage
            percentage = min(100, int((current * 100 / total) if total > 0 else 0))

            # Update dialog
            self._progress_dialog.setValue(percentage)

            # Update message if provided
            if message:
                self._progress_dialog.setLabelText(message)

            # Update file info if provided
            if file_info:
                self._progress_dialog.setFileInfo(file_info)

            # Update status text if provided
            if status_text:
                self._progress_dialog.setStatusText(status_text)

            # Process events to update UI
            QApplication.processEvents()
        except Exception as e:
            logger.error(f"Error updating progress dialog: {e}")

    def update_file_progress(
        self,
        file_path: str,
        current: int,
        total: int,
    ) -> None:
        """
        Update progress for file loading operations, with enhanced tracking of multiple files.

        Args:
            file_path: Path of the file being processed (empty for overall progress)
            current: Current progress value
            total: Total progress value
        """
        try:
            # Update loading state based on signal type
            if file_path:
                # This is a file-specific progress update
                # If this is a new file, update the file index
                if file_path != self._loading_state["current_file"]:
                    # If we're moving to a new file, record the size of the completed file
                    if self._loading_state["current_file"]:
                        # Store the actual size of the completed file
                        self._file_sizes[self._loading_state["current_file"]] = self._loading_state[
                            "total_rows"
                        ]

                    # Add new file to processed files if needed
                    if file_path not in self._loading_state["processed_files"]:
                        self._loading_state["current_file_index"] += 1
                        if file_path not in self._loading_state["processed_files"]:
                            self._loading_state["processed_files"].append(file_path)
                    self._loading_state["current_file"] = file_path

                # Update total rows for this file
                self._loading_state["total_rows"] = max(total, self._loading_state["total_rows"])

                # Increment total rows loaded by the increase since last update
                # Only increment if current is greater than last value (to avoid counting backwards)
                if current > self._last_progress_current:
                    self._total_rows_loaded += current - self._last_progress_current
                self._last_progress_current = current

            # Create formatted progress messages
            message, file_info, total_progress = self._format_progress_messages(current, total)

            # Update progress dialog
            self.update_progress(
                current,
                total,
                message=message,
                file_info=file_info,
                status_text=total_progress,
            )
        except Exception as e:
            logger.error(f"Error updating file progress: {e}")

    def _format_progress_messages(self, current: int, total: int) -> tuple:
        """
        Format progress messages consistently.

        Args:
            current: Current progress value
            total: Total progress value

        Returns:
            tuple: (message, file_info, total_progress)
        """
        # Create a consistent progress message
        filename = (
            os.path.basename(self._loading_state["current_file"])
            if self._loading_state["current_file"]
            else "files"
        )

        # Default values
        message = f"Loading {filename}..."
        file_info = None
        total_progress = ""

        # Standardized progress message format: "File X of Y - Z rows processed"
        if self._loading_state["total_files"] > 0:
            # Format file information
            total_files = self._loading_state["total_files"]
            current_file_index = self._loading_state["current_file_index"]

            file_info = f"File {current_file_index} of {total_files}"

            # Add filename
            file_info += f": {filename}"

            # Format rows with commas for readability
            if total > 0:
                current_formatted = f"{current:,}"
                # Show only current rows read, not the estimated total
                row_info = f"{current_formatted} rows read"

                # Create combined message with standardized format
                message = f"{file_info} - {row_info}"

                # Add total rows information as status text
                total_progress = f"Total: {self._total_rows_loaded:,} rows"
            else:
                # If we don't have row information yet
                message = file_info
        else:
            # Fallback if we don't have file count yet
            if total > 0:
                message += f" ({current:,} rows read)"

        return message, file_info, total_progress

    def set_total_files(self, total_files: int) -> None:
        """
        Set the total number of files for progress tracking.

        Args:
            total_files: Total number of files to process
        """
        self._loading_state["total_files"] = total_files
        logger.debug(f"Set total files to {total_files}")

    def mark_file_loading_complete(self) -> None:
        """Mark file loading as complete."""
        self._file_loading_complete = True
        logger.debug("File loading marked as complete")

    def is_file_loading_complete(self) -> bool:
        """
        Check if file loading is complete.

        Returns:
            bool: True if file loading is complete
        """
        return self._file_loading_complete

    def finish_progress(self, message: str, is_error: bool = False) -> None:
        """
        Finish a progress operation.

        Args:
            message: Final message to display
            is_error: Whether an error occurred
        """
        if not self._progress_dialog:
            return

        try:
            # Set appropriate dialog state based on success/error
            if is_error:
                # Set error styling
                if hasattr(self._progress_dialog, "setState") and hasattr(ProgressBar, "State"):
                    self._progress_dialog.setState(ProgressBar.State.ERROR)
                self._progress_dialog.setLabelText("Operation failed")
            else:
                # Set success styling
                if hasattr(self._progress_dialog, "setState") and hasattr(ProgressBar, "State"):
                    self._progress_dialog.setState(ProgressBar.State.SUCCESS)
                self._progress_dialog.setLabelText("Operation complete")

            # Set status message
            self._progress_dialog.setStatusText(message)

            # Set progress to max
            self._progress_dialog.setValue(self._progress_dialog.maximum())

            # Set button text based on state
            if is_error:
                self._progress_dialog.setCancelButtonText("Close")
            else:
                self._progress_dialog.setCancelButtonText("Confirm")

            # Enable button and make dialog dismissable
            self._progress_dialog.setCancelButtonEnabled(True)
            if hasattr(self._progress_dialog, "set_dismissable"):
                self._progress_dialog.set_dismissable(True)

            # Update UI
            QApplication.processEvents()

            # Emit completed signal
            self.progress_completed.emit()
        except Exception as e:
            logger.error(f"Error finishing progress dialog: {e}")

    def close_progress(self) -> None:
        """Close the progress dialog."""
        if not self._progress_dialog:
            return

        try:
            self._progress_dialog.close()
            self._progress_dialog = None
            self._cancel_callback = None
        except Exception as e:
            logger.error(f"Error closing progress dialog: {e}")

    def is_progress_showing(self) -> bool:
        """
        Check if progress dialog is currently showing.

        Returns:
            bool: True if progress dialog is showing
        """
        return self._progress_dialog is not None

    def is_canceled(self) -> bool:
        """
        Check if the operation was canceled.

        Returns:
            bool: True if operation was canceled
        """
        return (
            self._progress_dialog is not None
            and hasattr(self._progress_dialog, "wasCanceled")
            and self._progress_dialog.wasCanceled()
        )

    def enable_cancellation(self, enable: bool = True) -> None:
        """
        Enable or disable cancellation for the current progress dialog.

        Args:
            enable: Whether to enable cancellation
        """
        if not self._progress_dialog:
            return

        try:
            self._progress_dialog.setCancelButtonEnabled(enable)
            self._is_cancelable = enable
        except Exception as e:
            logger.error(f"Error enabling/disabling cancellation: {e}")

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        logger.debug("Progress dialog cancel button clicked")

        # Call cancel callback if provided and operation is cancelable
        if self._is_cancelable and self._cancel_callback:
            try:
                self._cancel_callback()
            except Exception as e:
                logger.error(f"Error in cancel callback: {e}")

        # Emit canceled signal
        self.progress_canceled.emit()

        # Make sure to clean up the dialog reference to prevent further updates
        # This prevents further operations on a dialog that's being closed
        self._progress_dialog = None
