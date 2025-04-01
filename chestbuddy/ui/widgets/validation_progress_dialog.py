"""
validation_progress_dialog.py

Description: Progress dialog with enhanced features for validation and correction operations
Usage:
    dialog = ValidationProgressDialog("Validating data", maximum=100, parent=parent)
    dialog.add_correction_log_entry("Changed 'user1' to 'User 1'")
    dialog.set_correction_summary({"total_corrections": 10, "corrected_rows": 5})
"""

import logging
from typing import Dict, List, Any, Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTextEdit,
    QScrollArea,
    QWidget,
    QSizePolicy,
)
from PySide6.QtGui import QColor, QIcon, QFont

from chestbuddy.ui.widgets.progress_dialog import ProgressDialog
from chestbuddy.ui.resources.style import Colors

# Set up logger
logger = logging.getLogger(__name__)


class ValidationProgressDialog(ProgressDialog):
    """
    Enhanced progress dialog for validation and correction operations.

    Provides additional features like correction log, summary statistics,
    and error reporting.

    Attributes:
        correction_log_updated (Signal): Emitted when a correction log entry is added
    """

    # Signal emitted when a correction log entry is added
    correction_log_updated = Signal(str)

    def __init__(
        self,
        label_text,
        cancel_button_text="Cancel",
        minimum=0,
        maximum=100,
        parent=None,
        title="Progress",
        show_cancel_button=True,
    ):
        """
        Initialize the validation progress dialog.

        Args:
            label_text: The text to display above the progress bar
            cancel_button_text: The text for the cancel button
            minimum: The minimum value of the progress bar
            maximum: The maximum value of the progress bar
            parent: The parent widget
            title: The title of the dialog
            show_cancel_button: Whether to show a cancel button
        """
        # Initialize the base progress dialog
        super().__init__(
            label_text,
            cancel_button_text,
            minimum,
            maximum,
            parent,
            title,
            show_cancel_button,
        )

        # Set a more appropriate size for the expanded dialog
        self.setFixedSize(550, 400)

        # Add additional UI components for validation/correction feedback
        self._setup_additional_ui()

        # Initialize state variables
        self._corrections_count = 0
        self._error_count = 0
        self._log_visible = False

        logger.debug("ValidationProgressDialog initialized")

    def _setup_additional_ui(self):
        """Add additional UI components specific to validation/correction."""
        main_layout = self.layout()

        # Add a separator line after the existing progress bar
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {Colors.BORDER};")
        main_layout.addWidget(separator)

        # Summary section
        self._summary_label = QLabel("Awaiting results...")
        self._summary_label.setStyleSheet(f"""
            color: {Colors.TEXT_LIGHT};
            font-size: 13px;
            margin-top: 8px;
            margin-bottom: 8px;
        """)
        main_layout.addWidget(self._summary_label)

        # Error section (initially hidden)
        self._error_container = QWidget()
        error_layout = QVBoxLayout(self._error_container)
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.setSpacing(5)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(f"""
            color: {Colors.ERROR};
            font-weight: bold;
            font-size: 13px;
        """)
        error_layout.addWidget(self._error_label)

        self._error_details = QTextEdit()
        self._error_details.setReadOnly(True)
        self._error_details.setStyleSheet(f"""
            background-color: {Colors.BG_MEDIUM};
            color: {Colors.ERROR};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 5px;
            font-family: monospace;
            font-size: 12px;
        """)
        self._error_details.setMaximumHeight(100)
        error_layout.addWidget(self._error_details)

        main_layout.addWidget(self._error_container)
        self._error_container.hide()  # Initially hidden

        # Add show/hide log button
        log_button_layout = QHBoxLayout()
        log_button_layout.setContentsMargins(0, 5, 0, 5)

        self._show_hide_log_button = QPushButton("Show Details")
        self._show_hide_log_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_MEDIUM};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_LIGHT};
            }}
        """)
        self._show_hide_log_button.clicked.connect(self._toggle_log_visibility)
        log_button_layout.addStretch()
        log_button_layout.addWidget(self._show_hide_log_button)
        log_button_layout.addStretch()

        main_layout.addLayout(log_button_layout)

        # Log area (initially hidden)
        self._correction_log = QTextEdit()
        self._correction_log.setReadOnly(True)
        self._correction_log.setStyleSheet(f"""
            background-color: {Colors.BG_MEDIUM};
            color: {Colors.TEXT_LIGHT};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 5px;
            font-family: monospace;
            font-size: 12px;
        """)
        self._correction_log.setMinimumHeight(100)
        self._correction_log.setVisible(False)  # Initially hidden
        main_layout.addWidget(self._correction_log)

        # Adjust the main layout to give more space to the new components
        if self._cancel_button:
            main_layout.removeWidget(self._cancel_button)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(self._cancel_button)
            button_layout.addStretch()
            main_layout.addLayout(button_layout)

    def _toggle_log_visibility(self):
        """Toggle the visibility of the correction log."""
        self._log_visible = not self._log_visible
        self._correction_log.setVisible(self._log_visible)

        # Update button text
        if self._log_visible:
            self._show_hide_log_button.setText("Hide Details")
            # Resize the dialog to show the log
            self.setFixedSize(550, 500)
        else:
            self._show_hide_log_button.setText("Show Details")
            # Resize to original size
            self.setFixedSize(550, 400)

    def add_correction_log_entry(self, entry: str) -> None:
        """
        Add an entry to the correction log.

        Args:
            entry: Text entry to add to the log
        """
        if not entry:
            return

        self._corrections_count += 1

        # Add the entry to the log with a sequential number
        log_entry = f"{self._corrections_count}. {entry}"
        self._correction_log.append(log_entry)

        # Scroll to the bottom
        scrollbar = self._correction_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Emit signal
        self.correction_log_updated.emit(entry)

        # Update summary
        self._update_summary()

    def set_correction_summary(self, summary: Dict[str, Any]) -> None:
        """
        Set the correction summary information.

        Args:
            summary: Dictionary with correction statistics:
                    total_corrections: Total number of corrections applied
                    corrected_rows: Number of rows affected
                    corrected_cells: Number of cells affected
                    iterations: Number of correction iterations
        """
        if not summary:
            return

        # Extract data from summary
        total_corrections = summary.get("total_corrections", 0)
        corrected_rows = summary.get("corrected_rows", 0)
        corrected_cells = summary.get("corrected_cells", 0)
        iterations = summary.get("iterations", 1)

        # Format the summary text
        summary_text = (
            f"<b>{total_corrections}</b> corrections applied to "
            f"<b>{corrected_rows}</b> rows (<b>{corrected_cells}</b> cells) "
            f"in <b>{iterations}</b> iterations"
        )

        # Set the summary label text
        self._summary_label.setText(summary_text)

        # If we have a summary, progress is done
        self.setValue(self.maximum())

    def set_error_summary(self, errors: List[str]) -> None:
        """
        Set the error summary information.

        Args:
            errors: List of error messages
        """
        if not errors:
            return

        self._error_count = len(errors)

        # Update the error label
        self._error_label.setText(f"{self._error_count} errors occurred during processing")

        # Clear the error details
        self._error_details.clear()

        # Add each error to the details
        for i, error in enumerate(errors, 1):
            self._error_details.append(f"{i}. {error}")

        # Show the error container
        self._error_container.show()

        # Update summary
        self._update_summary()

    def _update_summary(self) -> None:
        """Update the summary label with current statistics."""
        # If we already have a custom summary, don't override it
        if "corrections applied" in self._summary_label.text():
            return

        summary_parts = []

        if self._corrections_count > 0:
            summary_parts.append(f"<b>{self._corrections_count}</b> corrections")

        if self._error_count > 0:
            summary_parts.append(f"<b>{self._error_count}</b> errors")

        if not summary_parts:
            summary_parts.append("Processing...")

        self._summary_label.setText(" | ".join(summary_parts))

    def set_error_state(self, error_message: str) -> None:
        """
        Set the dialog to an error state.

        Args:
            error_message: The error message to display
        """
        # Set label to indicate error
        self.setLabelText("Error")

        # Set the error label
        self._error_label.setText(error_message)

        # Show the error container
        self._error_container.show()

        # Set progress to complete to indicate the process is done
        self.setValue(self.maximum())

        # Change the cancel button to "Close"
        if self._cancel_button:
            self._cancel_button.setText("Close")

        logger.error(f"ValidationProgressDialog entered error state: {error_message}")

    def close(self) -> None:
        """Override close to ensure proper cleanup."""
        logger.debug("ValidationProgressDialog closing")
        super().close()
