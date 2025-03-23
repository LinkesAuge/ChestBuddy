"""
progress_dialog.py

Description: A custom progress dialog with enhanced styling and features
Usage:
    dialog = ProgressDialog("Processing files...", "Cancel", 0, 100, parent)
    dialog.setStatusText("2 / 3 files - 14578 rows processed")
    dialog.setValue(75)
    dialog.setState(ProgressBar.State.SUCCESS)
"""

import logging
from enum import Enum
from typing import Optional, Union, Any

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QCloseEvent, QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)

from chestbuddy.ui.widgets.progress_bar import ProgressBar
from chestbuddy.ui.resources.style import Colors

logger = logging.getLogger(__name__)


class ProgressDialog(QDialog):
    """
    Custom progress dialog with enhanced styling and features.

    Signals:
        canceled (): Signal emitted when the cancel button is clicked.

    Attributes:
        minimum (int): Minimum value of the progress.
        maximum (int): Maximum value of the progress.

    Implementation Notes:
        - Uses a custom ProgressBar widget for visual feedback
        - Supports a secondary status text below the progress bar
        - Supports different states (normal, success, error)
        - Provides a cancel button for user interaction
    """

    # Signal emitted when the cancel button is clicked
    canceled = Signal()

    def __init__(
        self,
        label_text: str = "",
        cancel_button_text: str = "Cancel",
        minimum: int = 0,
        maximum: int = 100,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the progress dialog.

        Args:
            label_text: The text to display above the progress bar.
            cancel_button_text: The text to display on the cancel button.
            minimum: The minimum value of the progress.
            maximum: The maximum value of the progress.
            parent: The parent widget.
        """
        super().__init__(parent)

        # Initialize state
        self._minimum = minimum
        self._maximum = maximum
        self._cancel_button_text = cancel_button_text
        self._label_text = label_text
        self._status_text = ""

        # Set window properties
        self.setWindowTitle("Operation in Progress")
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setMinimumWidth(450)
        self.setMinimumHeight(180)
        self.setModal(True)

        # Apply shadow to make dialog pop
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
        """)

        # Set up the UI
        self._setup_ui()

        # Update the UI with initial values
        self.setLabelText(label_text)
        self.setCancelButtonText(cancel_button_text)
        self.setValue(minimum)

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Create header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Create label
        self._label = QLabel(self._label_text)
        self._label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self._label.setFont(font)
        self._label.setStyleSheet(f"color: {Colors.TEXT_DARK};")
        header_layout.addWidget(self._label)

        # Add header stretch
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Create progress bar
        self._progress_bar = ProgressBar(self)
        self._progress_bar.setMinimum(self._minimum)
        self._progress_bar.setMaximum(self._maximum)
        self._progress_bar.setValue(self._minimum)
        self._progress_bar.setMinimumHeight(24)
        layout.addWidget(self._progress_bar)

        # Create status text label
        self._status_label = QLabel(self._status_text)
        self._status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(9)
        self._status_label.setFont(font)
        self._status_label.setStyleSheet(f"color: {Colors.TEXT_DARK};")
        layout.addWidget(self._status_label)

        # Add spacer
        layout.addSpacing(16)

        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        # Add stretch to push button to the right
        button_layout.addStretch()

        # Create cancel button
        self._cancel_button = QPushButton(self._cancel_button_text)
        self._cancel_button.setMinimumWidth(100)
        self._cancel_button.setMinimumHeight(32)
        self._cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BACKGROUND_LIGHT};
                color: {Colors.TEXT_DARK};
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #EAECF0;
            }}
            QPushButton:pressed {{
                background-color: #D7DAE2;
            }}
        """)
        button_layout.addWidget(self._cancel_button)

        # Add button layout to main layout
        layout.addLayout(button_layout)

        # Connect signals
        self._cancel_button.clicked.connect(self.canceled.emit)

    def setLabelText(self, text: str) -> None:
        """
        Set the text of the label above the progress bar.

        Args:
            text: The new text.
        """
        self._label_text = text
        self._label.setText(text)

    def setStatusText(self, text: str) -> None:
        """
        Set the status text below the progress bar.

        Args:
            text: The new text.
        """
        self._status_text = text
        self._status_label.setText(text)

    def setCancelButtonText(self, text: str) -> None:
        """
        Set the text of the cancel button.

        Args:
            text: The new text.
        """
        self._cancel_button_text = text
        self._cancel_button.setText(text)

    def minimum(self) -> int:
        """
        Get the minimum value of the progress.

        Returns:
            The minimum value.
        """
        return self._minimum

    def maximum(self) -> int:
        """
        Get the maximum value of the progress.

        Returns:
            The maximum value.
        """
        return self._maximum

    def value(self) -> int:
        """
        Get the current value of the progress.

        Returns:
            The current value.
        """
        return self._progress_bar.value()

    def setMinimum(self, minimum: int) -> None:
        """
        Set the minimum value of the progress.

        Args:
            minimum: The new minimum value.
        """
        self._minimum = minimum
        self._progress_bar.setMinimum(minimum)

    def setMaximum(self, maximum: int) -> None:
        """
        Set the maximum value of the progress.

        Args:
            maximum: The new maximum value.
        """
        self._maximum = maximum
        self._progress_bar.setMaximum(maximum)

    def setValue(self, value: int) -> None:
        """
        Set the current value of the progress.

        Args:
            value: The new value.
        """
        self._progress_bar.setValue(value)

    def setState(self, state: ProgressBar.State) -> None:
        """
        Set the state of the progress bar.

        Args:
            state: The new state (NORMAL, SUCCESS, ERROR).
        """
        self._progress_bar.setState(state)

    def wasCanceled(self) -> bool:
        """
        Check if the dialog was canceled.

        Returns:
            True if the dialog was canceled, False otherwise.
        """
        return False  # This implementation doesn't track cancellation state

    def reset(self) -> None:
        """Reset the progress dialog to its initial state."""
        self.setValue(self._minimum)
        self._progress_bar.setState(ProgressBar.State.NORMAL)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle the close event.

        Args:
            event: The close event.
        """
        # Emit the canceled signal when the dialog is closed
        self.canceled.emit()
        event.accept()

    def sizeHint(self) -> QSize:
        """
        Get the recommended size for the dialog.

        Returns:
            The recommended size.
        """
        return QSize(450, 180)
