"""
multi_entry_dialog.py

Description: A dialog for adding multiple entries at once to validation lists
Usage:
    dialog = MultiEntryDialog(
        parent,
        title="Add Multiple Entries",
        message="Enter each entry on a new line",
        ok_text="Add",
        cancel_text="Cancel"
    )
    if dialog.exec() == QDialog.Accepted:
        entries = dialog.get_entries()
        # Process entries
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from typing import List

from chestbuddy.ui.resources.style import Colors


class MultiEntryDialog(QDialog):
    """
    A dialog for adding multiple entries at once.

    Attributes:
        _message (str): The message to display
        _ok_text (str): Text for the OK button
        _cancel_text (str): Text for the Cancel button
        _text_edit (QTextEdit): The text area for entering multiple entries
    """

    def __init__(
        self,
        parent=None,
        title="Add Multiple Entries",
        message="Enter each entry on a new line:",
        ok_text="Add",
        cancel_text="Cancel",
    ):
        """
        Initialize the multi-entry dialog.

        Args:
            parent: Parent widget
            title (str): Dialog title
            message (str): Dialog message
            ok_text (str): Text for the OK button
            cancel_text (str): Text for the Cancel button
        """
        super().__init__(parent)

        self._message = message
        self._ok_text = ok_text
        self._cancel_text = cancel_text

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Set background color
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 6px;
            }}
            QTextEdit {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {Colors.SECONDARY};
                selection-color: {Colors.TEXT_LIGHT};
                font-family: monospace;
            }}
            QPushButton {{
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton#ok_button {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.SECONDARY};
            }}
            QPushButton#ok_button:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton#cancel_button {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.TEXT_LIGHT};
                border: 1px solid {Colors.DARK_BORDER};
            }}
            QPushButton#cancel_button:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
        """)

        # Message label
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        message_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-size: 14px;")
        layout.addWidget(message_label)

        # Text edit for multiple entries
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Type or paste entries here, one per line...")
        layout.addWidget(self._text_edit)

        # Add helper text
        helper_label = QLabel("Duplicate entries and empty lines will be ignored.")
        helper_label.setWordWrap(True)
        helper_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; font-style: italic;"
        )
        layout.addWidget(helper_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        # Add spacer to push buttons to the right
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Cancel button
        cancel_button = QPushButton(self._cancel_text)
        cancel_button.setObjectName("cancel_button")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # OK button
        ok_button = QPushButton(self._ok_text)
        ok_button.setObjectName("ok_button")
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        # Add button layout to main layout
        layout.addLayout(button_layout)

    def get_entries(self) -> List[str]:
        """
        Get the list of entries from the text edit.

        Returns:
            List[str]: List of non-empty entries
        """
        text = self._text_edit.toPlainText()
        # Split by newlines and filter out empty entries
        entries = [entry.strip() for entry in text.split("\n")]
        # Return only non-empty entries
        return [entry for entry in entries if entry]
