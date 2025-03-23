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
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)

from chestbuddy.ui.widgets.progress_bar import ProgressBar
from chestbuddy.ui.resources.style import Colors


class ProgressDialog(QDialog):
    """
    Custom progress dialog using the ProgressBar widget.

    Attributes:
        canceled: Signal emitted when the user cancels the operation

    Implementation Notes:
        - Wraps the ProgressBar widget in a dialog
        - Provides a similar API to QProgressDialog
        - Includes a cancel button for operations
        - Can show detailed status information
    """

    # Signal emitted when user cancels the operation
    canceled = Signal()

    def __init__(
        self,
        label_text: str,
        cancel_button_text: str,
        minimum: int = 0,
        maximum: int = 100,
        parent: Optional[QDialog] = None,
    ):
        """
        Initialize the progress dialog.

        Args:
            label_text: Text to display above the progress bar
            cancel_button_text: Text for the cancel button
            minimum: Minimum progress value
            maximum: Maximum progress value
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize attributes
        self._cancel_button_text = cancel_button_text
        self._was_canceled = False
        self._minimum = minimum
        self._maximum = maximum

        # Configure dialog
        self.setWindowTitle("Progress")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        # Setup UI
        self._setup_ui(label_text)

    def _setup_ui(self, label_text: str):
        """
        Set up the user interface.

        Args:
            label_text: Text to display above the progress bar
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Title label
        self._label = QLabel(label_text)
        self._label.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-weight: bold;")
        self._label.setAlignment(Qt.AlignLeft)

        # Progress bar
        self._progress_bar = ProgressBar(self)
        self._progress_bar.setMaximum(self._maximum)

        # Apply additional styling to match app theme
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_DARK};
                border-radius: 4px;
                height: 12px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {Colors.ACCENT};
                border-radius: 4px;
            }}
        """)

        # Cancel/confirm button layout - centered
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Add spacers on both sides to center the button
        left_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(left_spacer)

        self._cancel_button = QPushButton(self._cancel_button_text)
        self._cancel_button.clicked.connect(self._on_cancel_clicked)

        # Apply consistent button styling
        self._cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {Colors.ACCENT};
            }}
            
            QPushButton:pressed {{
                background-color: {Colors.BG_MEDIUM};
            }}
        """)

        button_layout.addWidget(self._cancel_button)

        # Add right spacer to ensure centering
        right_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(right_spacer)

        # Add widgets to layout
        main_layout.addWidget(self._label)
        main_layout.addWidget(self._progress_bar)
        main_layout.addLayout(button_layout)

        # Set fixed size based on content
        self.adjustSize()
        self.setFixedSize(self.size())

    def _on_cancel_clicked(self):
        """Handle when the cancel button is clicked."""
        self._was_canceled = True
        self.canceled.emit()

    def setValue(self, value: int):
        """
        Set the current progress value.

        Args:
            value: Progress value
        """
        # Update progress bar
        self._progress_bar.setValue(value)

        # Process events to ensure UI updates
        self.repaint()

    def setMaximum(self, maximum: int):
        """
        Set the maximum progress value.

        Args:
            maximum: Maximum value
        """
        self._maximum = maximum
        self._progress_bar.setMaximum(maximum)

    def setLabelText(self, text: str):
        """
        Set the label text above the progress bar.

        Args:
            text: Label text
        """
        self._label.setText(text)

    def setStatusText(self, text: str):
        """
        Set the status text below the progress bar.

        Args:
            text: Status text
        """
        self._progress_bar.setStatus(text)

    def setCancelButtonText(self, text: str):
        """
        Set the cancel button text.

        Args:
            text: Button text
        """
        self._cancel_button_text = text
        self._cancel_button.setText(text)

    def wasCanceled(self) -> bool:
        """
        Check if the operation was canceled.

        Returns:
            True if canceled, False otherwise
        """
        return self._was_canceled

    def setState(self, state: ProgressBar.State):
        """
        Set the visual state of the progress bar.

        Args:
            state: The visual state (NORMAL, SUCCESS, ERROR)
        """
        self._progress_bar.setState(state)

    def reset(self):
        """Reset the progress dialog to its initial state."""
        self._was_canceled = False
        self._progress_bar.setValue(self._minimum)
        self._progress_bar.setState(ProgressBar.State.NORMAL)
        self._progress_bar.setStatus("")
