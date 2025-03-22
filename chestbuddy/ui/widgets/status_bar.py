"""
status_bar.py

Description: Custom status bar for the application.
Usage:
    Used in the MainWindow to display application status.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout

from chestbuddy.ui.resources.style import Colors


class StatusBar(QStatusBar):
    """Custom status bar for the application."""

    def __init__(self, parent=None):
        """
        Initialize the status bar.

        Args:
            parent (QWidget, optional): The parent widget
        """
        super().__init__(parent)

        # Set style
        self.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_MUTED};
                border-top: 1px solid {Colors.BORDER};
                min-height: 30px;
            }}
        """)

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize status bar components."""
        # Status message label (left)
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            padding-left: 10px;
        """)
        self.addWidget(self._status_label, 1)  # Stretch factor 1

        # Create widget for right side info
        self._info_widget = QWidget()
        self._info_layout = QHBoxLayout(self._info_widget)
        self._info_layout.setContentsMargins(0, 0, 10, 0)
        self._info_layout.setSpacing(20)

        # Record count label
        self._record_count_label = QLabel("0 records loaded")
        self._record_count_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        self._info_layout.addWidget(self._record_count_label)

        # Last modified label
        self._last_modified_label = QLabel("Last modified: Never")
        self._last_modified_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        self._info_layout.addWidget(self._last_modified_label)

        # Add info widget to right side
        self.addPermanentWidget(self._info_widget)

    def set_status(self, message):
        """
        Set the status message.

        Args:
            message (str): The status message
        """
        self._status_label.setText(message)

    def set_record_count(self, count):
        """
        Set the record count.

        Args:
            count (int): The record count
        """
        self._record_count_label.setText(f"{count:,} records loaded")

    def set_last_modified(self, date_time):
        """
        Set the last modified timestamp.

        Args:
            date_time (str): The last modified date and time
        """
        self._last_modified_label.setText(f"Last modified: {date_time}")

    def clear_all(self):
        """Clear all status information."""
        self._status_label.setText("Ready")
        self._record_count_label.setText("0 records loaded")
        self._last_modified_label.setText("Last modified: Never")
