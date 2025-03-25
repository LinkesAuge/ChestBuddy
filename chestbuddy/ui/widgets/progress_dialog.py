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

    # Signal emitted when user cancels the operation
    canceled = Signal()

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
        self._is_fully_initialized = False  # Track when dialog is fully shown

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
        # Set window flags to make it modal but with a frame so it can be moved
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
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
        logger.debug("Cancel button clicked in progress dialog")
        self._was_canceled = True

        # Emit the canceled signal for any connected slots
        self.canceled.emit()

        # Always close the dialog when the button is clicked
        # This ensures the button works even if signal connections are broken
        logger.debug("Directly closing dialog after cancel button clicked")
        self.close()

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
            state: The state to set
        """
        logger.debug(f"Setting progress dialog state to: {state}")

        # Check if this is a custom progress bar
        if hasattr(self, "_progress_bar"):
            # For custom progress bar with setState method
            if hasattr(self._progress_bar, "setState"):
                self._progress_bar.setState(state)

            # Also update the button style based on the state
            if hasattr(self, "_cancel_button") and self._cancel_button:
                # Ensure we're using the correct enum by importing if needed
                from chestbuddy.ui.widgets.progress_bar import ProgressBar

                if state == ProgressBar.State.SUCCESS:
                    logger.debug("Setting SUCCESS button style")
                    self._cancel_button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {Colors.SUCCESS};
                            color: {Colors.TEXT_LIGHT};
                            border: none;
                            padding: 8px 16px;
                            border-radius: 4px;
                            font-weight: bold;
                        }}
                        QPushButton:hover {{
                            background-color: {Colors.SUCCESS};
                            opacity: 0.9;
                        }}
                    """)
                elif state == ProgressBar.State.ERROR:
                    logger.debug("Setting ERROR button style")
                    self._cancel_button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {Colors.ERROR};
                            color: {Colors.TEXT_LIGHT};
                            border: none;
                            padding: 8px 16px;
                            border-radius: 4px;
                            font-weight: bold;
                        }}
                        QPushButton:hover {{
                            background-color: {Colors.ERROR};
                            opacity: 0.9;
                        }}
                    """)
                else:
                    # Reset to normal style
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

    def show(self) -> None:
        """
        Show the dialog and mark it as fully initialized.
        Overridden to prevent premature cancel signal.
        """
        result = super().show()
        # Set initialization flag after super().show() to ensure dialog is truly visible
        self._is_fully_initialized = True
        return result

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

        # Set initialization flag to ensure closeEvent will emit cancel signal if needed
        self._is_fully_initialized = True

        # Process events to ensure UI is responsive
        QApplication.processEvents()

        # Call parent exec
        return super().exec()

    def closeEvent(self, event):
        """
        Handle the close event.

        Overridden to ensure the canceled signal is emitted when the dialog is closed,
        which ensures background processes are properly cancelled.
        """
        # Only emit the signal if it hasn't been canceled already AND the dialog was properly shown
        if not self._was_canceled and self._is_fully_initialized:
            logger.debug("Dialog closed via window close button, emitting canceled signal")
            self._was_canceled = True
            self.canceled.emit()
        elif not self._is_fully_initialized:
            logger.debug("Ignoring closeEvent during initialization")

        # Call the parent class's closeEvent
        super().closeEvent(event)

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
