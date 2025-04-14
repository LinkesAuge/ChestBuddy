"""
correction_preview_dialog.py

Dialog to preview a proposed correction.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDialogButtonBox,
    QWidget,
)
from PySide6.QtCore import Qt


class CorrectionPreviewDialog(QDialog):
    """
    A simple dialog to show the original and corrected values before applying.
    """

    def __init__(self, original_value: str, corrected_value: str, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Correction Preview")
        self.setMinimumWidth(400)  # Set a reasonable minimum width

        self._original_value = original_value
        self._corrected_value = corrected_value

        # Layouts
        main_layout = QVBoxLayout(self)
        content_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        # Labels
        header_orig_label = QLabel("<b>Original Value:</b>")
        self.original_label = QLabel(str(self._original_value))  # Ensure string conversion
        self.original_label.setWordWrap(True)  # Allow wrapping

        header_corr_label = QLabel("<b>Suggested Correction:</b>")
        self.corrected_label = QLabel(str(self._corrected_value))  # Ensure string conversion
        self.corrected_label.setWordWrap(True)  # Allow wrapping

        # Add widgets to content layout
        content_layout.addWidget(header_orig_label)
        content_layout.addWidget(self.original_label)
        content_layout.addSpacing(10)  # Add some space
        content_layout.addWidget(header_corr_label)
        content_layout.addWidget(self.corrected_label)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Apply Correction")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        button_layout.addWidget(self.button_box)

        # Add layouts to main layout
        main_layout.addLayout(content_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
