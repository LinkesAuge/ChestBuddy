"""
confirmation_dialog.py

Description: A simple confirmation dialog with customizable buttons
Usage:
    dialog = ConfirmationDialog(
        parent,
        title="Confirm Action",
        message="Are you sure you want to proceed?",
        ok_text="Yes",
        cancel_text="No"
    )
    if dialog.exec() == QDialog.Accepted:
        # User confirmed
    else:
        # User cancelled
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from chestbuddy.ui.resources.style import Colors


class ConfirmationDialog(QDialog):
    """
    A customizable confirmation dialog.

    Attributes:
        _message (str): The message to display
        _ok_text (str): Text for the OK button
        _cancel_text (str): Text for the Cancel button
    """

    def __init__(
        self,
        parent=None,
        title="Confirm",
        message="Are you sure?",
        ok_text="OK",
        cancel_text="Cancel",
    ):
        """
        Initialize the confirmation dialog.

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
        self.setMinimumWidth(400)

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
