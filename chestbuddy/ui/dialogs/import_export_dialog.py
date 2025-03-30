"""
Import/Export Dialog.

This module implements a dialog for importing and exporting correction rules.
"""

from typing import Optional, Dict, List, Any
import os
import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QMessageBox,
)


class ImportExportDialog(QDialog):
    """
    Dialog for importing and exporting correction rules.

    This dialog allows users to select a file and format for importing or exporting
    correction rules.
    """

    def __init__(self, mode: str = "import", parent=None):
        """
        Initialize the dialog.

        Args:
            mode: Dialog mode, either "import" or "export"
            parent: Parent widget
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._mode = mode.lower()

        if self._mode not in ["import", "export"]:
            raise ValueError(f"Invalid mode: {mode}. Mode must be 'import' or 'export'.")

        # Set window title based on mode
        self.setWindowTitle(
            "Import Correction Rules" if self._mode == "import" else "Export Correction Rules"
        )

        # Default file filter is CSV
        self._file_filter = "CSV Files (*.csv)"

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components for the dialog."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Form layout for input fields
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # File path with browse button
        file_layout = QHBoxLayout()
        self._file_path_edit = QLineEdit()
        self._file_path_edit.setPlaceholderText("Select a file...")
        file_layout.addWidget(self._file_path_edit)

        self._browse_button = QPushButton("Browse...")
        file_layout.addWidget(self._browse_button)

        form_layout.addRow("File:", file_layout)

        # Format selection
        self._format_combo = QComboBox()
        self._format_combo.addItem("CSV")
        self._format_combo.addItem("JSON")
        form_layout.addRow("Format:", self._format_combo)

        main_layout.addLayout(form_layout)

        # Description text based on mode
        if self._mode == "import":
            description = (
                "Select a file containing correction rules to import. "
                "The file should be in CSV or JSON format."
            )
        else:
            description = (
                "Select a destination file to export correction rules. "
                "The rules will be exported in the selected format."
            )

        description_label = QLabel(description)
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        # Spacer
        main_layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox()

        # Action button based on mode
        action_text = "Import" if self._mode == "import" else "Export"
        self._action_button = QPushButton(action_text)
        self._action_button.setDefault(True)

        self._cancel_button = QPushButton("Cancel")

        button_box.addButton(self._action_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(self._cancel_button, QDialogButtonBox.RejectRole)

        main_layout.addWidget(button_box)

        # Connect signals
        self._browse_button.clicked.connect(self._on_browse)
        self._format_combo.currentTextChanged.connect(self._on_format_changed)
        self._action_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)

        # Set minimum size for the dialog
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)

    def _on_browse(self):
        """Open a file dialog to browse for a file."""
        if self._mode == "import":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select File to Import", "", self._file_filter
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Select File to Export", "", self._file_filter
            )

        if file_path:
            self._file_path_edit.setText(file_path)

    def _on_format_changed(self, format_text):
        """Update file filter when format changes."""
        if format_text == "CSV":
            self._file_filter = "CSV Files (*.csv)"
        elif format_text == "JSON":
            self._file_filter = "JSON Files (*.json)"

    def _validate_file_path(self) -> bool:
        """
        Validate the file path.

        Returns:
            bool: True if the file path is valid, False otherwise
        """
        file_path = self._file_path_edit.text().strip()

        # Check if file path is empty
        if not file_path:
            QMessageBox.warning(self, "Validation Error", "Please select a file.")
            return False

        # Check if file extension matches selected format
        format_text = self._format_combo.currentText().lower()
        expected_ext = ".csv" if format_text == "csv" else ".json"

        if not file_path.lower().endswith(expected_ext):
            # Ask user if they want to add the extension
            result = QMessageBox.question(
                self,
                "File Extension",
                f"The file does not have a {expected_ext} extension. Would you like to add it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if result == QMessageBox.Yes:
                self._update_extension()

        return True

    def _update_extension(self):
        """Update the file extension to match the selected format."""
        file_path = self._file_path_edit.text().strip()
        format_text = self._format_combo.currentText().lower()
        expected_ext = ".csv" if format_text == "csv" else ".json"

        # Remove existing extension if present
        path = Path(file_path)
        base_name = path.stem
        directory = path.parent

        # Create new path with correct extension
        new_path = directory / f"{base_name}{expected_ext}"
        self._file_path_edit.setText(str(new_path))

    def accept(self):
        """Override accept to validate file path first."""
        if not self._validate_file_path():
            return

        # Call parent accept if validation passed
        super().accept()

    def get_file_path(self) -> str:
        """
        Get the selected file path.

        Returns:
            str: The file path
        """
        return self._file_path_edit.text().strip()

    def get_format(self) -> str:
        """
        Get the selected file format.

        Returns:
            str: The format ("CSV" or "JSON")
        """
        return self._format_combo.currentText()
