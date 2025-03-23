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
        # Set window flags to make it modal and frameless
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
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
            color: {Colors.TEXT_SECONDARY};
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
        self._was_canceled = True
        self.canceled.emit()

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
            text: The text to set for the cancel button
        """
        if self._cancel_button:
            self._cancel_button.setText(text)

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
            enabled: True to enable the button, False to disable it
        """
        if self._cancel_button:
            self._cancel_button.setEnabled(enabled)
            # Update styling based on enabled state
            if enabled:
                # Active button style
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
            else:
                # Disabled button style
                self._cancel_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Colors.BG_DARK};
                        color: {Colors.TEXT_DISABLED};
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
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
            state: The state to set
        """
        if hasattr(self._progress_bar, "setState"):
            self._progress_bar.setState(state)

    def reset(self):
        """Reset the progress dialog to its initial state."""
        self._was_canceled = False
        self._progress_bar.setValue(self._minimum)
        self._progress_bar.setState(ProgressBar.State.NORMAL)
        self._progress_bar.setStatus("")
