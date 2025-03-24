"""
progress_dialog.py

Description: Custom progress dialog using the ProgressBar widget
Usage:
    progress_dialog = ProgressDialog("Processing files", "Cancel", 0, 100, parent)
    progress_dialog.setValue(50)
    progress_dialog.setLabelText("Processing file 5 of 10...")
"""

from typing import Optional, Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QProgressBar,
    QStyle,
)
from PySide6.QtGui import QGuiApplication

from chestbuddy.ui.widgets.progress_bar import ProgressBar
from chestbuddy.ui.resources.style import Colors
import logging

logger = logging.getLogger(__name__)


class ProgressDialog(QDialog):
    """
    A dialog that shows progress for an operation.

    This dialog can show a progress bar, a label, and an optional cancel button.
    """

    # Import State from ProgressBar for compatibility
    class State:
        """The possible states of the progress dialog."""

        NORMAL = 0
        SUCCESS = 1
        ERROR = 2

    # Signal emitted when user cancels the operation
    canceled = Signal()

    # Signal emitted when user confirms a completed operation
    confirmed = Signal()

    def __init__(
        self,
        label_text,
        cancel_button_text,
        minimum=0,
        maximum=100,
        parent=None,
        title="Progress",
        show_cancel_button=True,
    ):
        """
        Initialize the progress dialog.

        Args:
            label_text: The text to display above the progress bar
            cancel_button_text: The text for the cancel button
            minimum: The minimum value of the progress bar
            maximum: The maximum value of the progress bar
            parent: The parent widget
            title: The title of the dialog
            show_cancel_button: Whether to show a cancel button
        """
        super().__init__(parent)

        self._minimum = minimum
        self._maximum = maximum
        self._title = title
        self._label_text = label_text
        self._show_cancel_button = show_cancel_button
        self._cancel_button_text = cancel_button_text
        self._was_canceled = False
        self._is_confirm_mode = False  # Track if we're in confirmation mode

        # Ensure we have references to UI elements
        self._label = None
        self._progress_bar = None
        self._cancel_button = None
        self._status_label = None
        self._title_label = None

        # Set up the UI
        self._setup_ui()

        # Set initial values
        self.setValue(minimum)
        self.setLabelText(label_text)

        # Center the dialog on the parent
        if parent:
            self.setGeometry(
                QStyle.alignedRect(
                    Qt.LeftToRight,
                    Qt.AlignCenter,
                    self.size(),
                    parent.geometry(),
                )
            )
        else:
            # Center on screen using QGuiApplication instead of deprecated QDesktopWidget
            center_point = QGuiApplication.primaryScreen().availableGeometry().center()
            geometry = self.frameGeometry()
            geometry.moveCenter(center_point)
            self.move(geometry.topLeft())

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Set window flags to be less intrusive
        # Remove Qt.WindowStaysOnTopHint to avoid forcing dialog to stay on top
        # Remove FramelessWindowHint to use standard window frame
        self.setWindowFlags(Qt.Dialog)

        # Default to non-modal to avoid UI blocking issues
        # This will be overridden by MainWindow if needed
        self.setWindowModality(Qt.NonModal)

        self.setFixedSize(420, 250)

        # Set the style for the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
            QLabel {{
                color: {Colors.TEXT_LIGHT};
            }}
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Colors.TEXT_LIGHT};
        """)
        main_layout.addWidget(self._title_label)

        # Label for progress information
        self._label = QLabel(self._label_text)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(f"""
            font-size: 14px;
            color: {Colors.TEXT_LIGHT};
        """)
        main_layout.addWidget(self._label)

        # Create progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(self._minimum, self._maximum)
        self._progress_bar.setValue(self._minimum)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_LIGHT};
                border-radius: 4px;
                text-align: center;
                height: 12px;
            }}
            
            QProgressBar::chunk {{
                background-color: {Colors.ACCENT};
                border-radius: 4px;
            }}
        """)
        main_layout.addWidget(self._progress_bar)

        # Status text label
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_MUTED};
        """)
        main_layout.addWidget(self._status_label)

        # Add stretch to push button to bottom
        main_layout.addStretch()

        # Button layout with center alignment
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Create cancel button if requested
        if self._show_cancel_button:
            self._cancel_button = QPushButton(self._cancel_button_text)
            self._cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    color: {Colors.TEXT_LIGHT};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Colors.ACCENT};
                }}
            """)
            self._cancel_button.clicked.connect(self._on_cancel_clicked)
            button_layout.addWidget(self._cancel_button)
        else:
            self._cancel_button = None

        # Add stretch to center the button
        button_layout.addStretch()

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

    def _on_cancel_clicked(self):
        """Handle when the cancel button is clicked."""
        if self._is_confirm_mode:
            # In confirm mode, emit confirmed signal and accept to properly end modal state
            logger.debug("Confirm button clicked in progress dialog")
            self.confirmed.emit()  # Emit confirmed signal for handling by MainWindow
            logger.debug("Accepting dialog after confirm button clicked")
            self.accept()  # Use accept() instead of close() to properly end modal state
        else:
            # In cancel mode, emit cancel signal and close
            logger.debug("Cancel button clicked in progress dialog")
            self._was_canceled = True

            # Emit the canceled signal for any connected slots
            self.canceled.emit()

            # Always reject the dialog when in cancel mode
            logger.debug("Rejecting dialog after cancel button clicked")
            self.reject()  # Use reject() instead of close() to properly end modal state

    def setValue(self, value: int) -> None:
        """
        Set the value of the progress bar.

        Args:
            value: The value to set
        """
        if self._progress_bar:
            self._progress_bar.setValue(value)

    def value(self) -> int:
        """
        Get the current value of the progress bar.

        Returns:
            The current progress value
        """
        if self._progress_bar:
            return self._progress_bar.value()
        return self._minimum

    def setRange(self, minimum: int, maximum: int) -> None:
        """
        Set the range of the progress bar.

        Args:
            minimum: The minimum value
            maximum: The maximum value
        """
        self._minimum = minimum
        self._maximum = maximum
        if self._progress_bar:
            self._progress_bar.setRange(minimum, maximum)

    def setLabelText(self, text: str) -> None:
        """
        Set the text of the label above the progress bar.

        Args:
            text: The text to set
        """
        if self._label:
            self._label.setText(text)

    def maximum(self) -> int:
        """
        Get the maximum value of the progress bar.

        Returns:
            The maximum progress value
        """
        return self._maximum

    def minimum(self) -> int:
        """
        Get the minimum value of the progress bar.

        Returns:
            The minimum progress value
        """
        return self._minimum

    def setStatusText(self, text: str):
        """
        Set the status text below the progress bar.

        Args:
            text: Status text
        """
        self._status_label.setText(text)

    def setCancelButtonText(self, text: str) -> None:
        """
        Set the text of the cancel button.

        Args:
            text: The text to set
        """
        if hasattr(self, "_cancel_button") and self._cancel_button:
            logger.debug(f"Setting cancel button text: {text}")
            self._cancel_button.setText(text)

            # Make sure button is properly sized for the new text
            self._cancel_button.adjustSize()

    def setButtonText(self, text: str) -> None:
        """
        Set the text of the action button.
        This is an alias for setCancelButtonText for more intuitive API.

        Args:
            text: The text to set for the button
        """
        self.setCancelButtonText(text)

    def setCancelButtonEnabled(self, enabled: bool) -> None:
        """
        Enable or disable the cancel button.

        Args:
            enabled: Whether the button should be enabled
        """
        if hasattr(self, "_cancel_button") and self._cancel_button:
            # Always log when the button state changes
            current = self._cancel_button.isEnabled()
            if current != enabled:
                # Only log when actually changing
                logger.debug(f"Setting cancel button enabled: {enabled}")

            # Set the button state
            self._cancel_button.setEnabled(enabled)

            # If enabling, also make sure it's visible
            if enabled:
                self._cancel_button.show()

    def set_confirm_button_style(self):
        """
        Set the cancel button to use a green confirmation style.
        Used when a process is successfully completed and awaiting user confirmation.
        """
        if hasattr(self, "_cancel_button") and self._cancel_button:
            logger.debug("Setting confirm button style (green)")
            self._is_confirm_mode = True  # Set the flag to indicate confirm mode
            self._cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #4CAF50;  /* Green color */
                    color: {Colors.TEXT_LIGHT};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #45a049;  /* Darker green on hover */
                }}
            """)

    def wasCanceled(self) -> bool:
        """
        Check if the operation was canceled.

        Returns:
            True if canceled, False otherwise
        """
        return self._was_canceled

    def setState(self, state):
        """
        Set the state of the progress bar.

        Args:
            state: The state to set (use ProgressDialog.State constants)
        """
        logger.debug(f"Setting progress dialog state to: {state}")

        # Reset confirm mode if changing from SUCCESS to another state
        if (
            hasattr(self, "_is_confirm_mode")
            and self._is_confirm_mode
            and state != self.State.SUCCESS
        ):
            logger.debug("Resetting confirm mode to False")
            self._is_confirm_mode = False

        # First handle the progress bar state if available
        if hasattr(self, "_progress_bar") and self._progress_bar:
            # If using custom ProgressBar that accepts setState
            if hasattr(self._progress_bar, "setState"):
                try:
                    # Map our state to ProgressBar.State if needed
                    from chestbuddy.ui.widgets.progress_bar import ProgressBar

                    if state == self.State.NORMAL:
                        pb_state = ProgressBar.State.NORMAL
                    elif state == self.State.SUCCESS:
                        pb_state = ProgressBar.State.SUCCESS
                    elif state == self.State.ERROR:
                        pb_state = ProgressBar.State.ERROR
                    else:
                        pb_state = state  # Pass through if not matching

                    # Set the state on the progress bar
                    self._progress_bar.setState(pb_state)
                except Exception as e:
                    logger.error(f"Error setting progress bar state: {e}")

            # For QProgressBar, we can only change style
            else:
                try:
                    if state == self.State.SUCCESS:
                        self._progress_bar.setStyleSheet("""
                            QProgressBar {
                                background-color: #333;
                                border: 1px solid #444;
                                border-radius: 5px;
                                text-align: center;
                            }
                            QProgressBar::chunk {
                                background-color: #4CAF50;
                                border-radius: 5px;
                            }
                        """)
                    elif state == self.State.ERROR:
                        self._progress_bar.setStyleSheet("""
                            QProgressBar {
                                background-color: #333;
                                border: 1px solid #444;
                                border-radius: 5px;
                                text-align: center;
                            }
                            QProgressBar::chunk {
                                background-color: #F44336;
                                border-radius: 5px;
                            }
                        """)
                    else:
                        # Normal state
                        self._progress_bar.setStyleSheet("")
                except Exception as e:
                    logger.error(f"Error setting progress bar style: {e}")

        # Now handle button styling based on state
        if state == self.State.SUCCESS:
            # If in success state, also apply confirm button style
            self.set_confirm_button_style()
        elif state == self.State.ERROR:
            # For error state, reset button style to default
            if hasattr(self, "_cancel_button") and self._cancel_button:
                self._cancel_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.PRIMARY};
                        color: {Colors.TEXT_LIGHT};
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {Colors.ACCENT};
                    }}
                """)

    def reset(self) -> None:
        """
        Reset the dialog to its initial state.
        """
        logger.debug("Resetting progress dialog")

        # Reset progress bar state
        if hasattr(self, "_progress_bar"):
            # For custom progress bar
            if hasattr(self._progress_bar, "setState"):
                try:
                    self._progress_bar.setState(ProgressBar.State.NORMAL)
                except Exception as e:
                    logger.error(f"Error resetting progress bar state: {e}")

            # For both custom and standard progress bar
            try:
                self._progress_bar.setValue(0)
            except Exception as e:
                logger.error(f"Error resetting progress bar value: {e}")

        # Reset status text
        if hasattr(self, "setStatusText"):
            try:
                self.setStatusText("")
            except Exception as e:
                logger.error(f"Error resetting status text: {e}")

        # Make sure cancel button is enabled and properly connected
        if hasattr(self, "_cancel_button") and self._cancel_button:
            try:
                self._cancel_button.setEnabled(True)
                self._cancel_button.setText("Cancel")
            except Exception as e:
                logger.error(f"Error resetting cancel button: {e}")

    def reset_all_state(self):
        """
        Reset all dialog state including confirm mode and styling.
        This ensures the dialog is ready for reuse in a new operation.
        """
        logger.debug("Resetting all progress dialog state")

        # Reset confirm mode flag
        self._is_confirm_mode = False
        self._was_canceled = False

        # Reset progress bar
        if hasattr(self, "_progress_bar") and self._progress_bar:
            self.setValue(0)

            # Reset progress bar styling
            if hasattr(self._progress_bar, "setState"):
                try:
                    from chestbuddy.ui.widgets.progress_bar import ProgressBar

                    self._progress_bar.setState(ProgressBar.State.NORMAL)
                except Exception as e:
                    logger.error(f"Error resetting progress bar state: {e}")
            else:
                self._progress_bar.setStyleSheet("")

        # Reset labels
        if hasattr(self, "_status_label") and self._status_label:
            self._status_label.setText("")

        # Reset button styling and text
        if hasattr(self, "_cancel_button") and self._cancel_button:
            self._cancel_button.setText("Cancel")
            self._cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.PRIMARY};
                    color: {Colors.TEXT_LIGHT};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {Colors.ACCENT};
                }}
            """)

    def exec(self) -> int:
        """
        Execute the dialog.
        Overridden to ensure proper behavior.

        Returns:
            Dialog result code
        """
        logger.debug("Progress dialog exec called")

        # Make sure the cancel button is enabled before showing
        if hasattr(self, "_cancel_button") and self._cancel_button:
            self._cancel_button.setEnabled(True)

        # Make sure dialog is visible and at the front
        self.show()
        self.raise_()
        self.activateWindow()

        # Process events to ensure UI is responsive
        QApplication.processEvents()

        # Call parent exec
        return super().exec()

    def close(self) -> None:
        """
        Close the dialog.
        Overridden to ensure proper cleanup.
        """
        logger.debug("Progress dialog close called")

        # Don't disconnect the cancel button's clicked signal
        # This is the most critical connection that ensures the dialog can close
        # Only disconnect other signals if they exist

        # Call parent close to actually close the dialog
        try:
            super().close()
            logger.debug("Progress dialog successfully closed")
        except Exception as e:
            logger.error(f"Error closing progress dialog: {e}")
            # Try again with force if normal close fails
            try:
                self.hide()  # In case close() failed, at least hide the dialog
                logger.debug("Forced hide of progress dialog after close failure")
            except:
                pass
