"""
Dialog for adding a new correction rule.
"""

import typing
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QLabel,
    QDialogButtonBox,
    QComboBox,
    QCheckBox,
)
from PySide6.QtCore import Qt

# Placeholder for CorrectionCategory enum if it exists
# from ...core.enums import CorrectionCategory


class AddCorrectionRuleDialog(QDialog):
    """
    A dialog to manually add a correction rule.

    Allows specifying the 'From' value (pre-filled), 'To' value,
    and the correction category.
    """

    def __init__(self, from_value: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Correction Rule")
        self.setMinimumWidth(400)

        self._from_value = from_value
        self._result: typing.Optional[typing.Dict[str, str]] = None

        # --- Widgets ---
        self.from_label = QLabel(f"<b>From:</b> {self._from_value}")
        self.from_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("Enter the corrected value")

        self.category_combo = QComboBox()
        # TODO: Populate with actual categories from an enum or service
        # For now, use placeholder categories
        self.category_combo.addItems(["Player", "Chest Type", "Source", "General"])

        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)  # Default to enabled

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # --- Layout ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        form_layout.addRow(self.from_label)  # Span both columns
        form_layout.addRow("To:", self.to_input)
        form_layout.addRow("Category:", self.category_combo)
        form_layout.addRow("", self.enabled_checkbox)  # Checkbox below category

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.to_input.textChanged.connect(self._update_ok_button_state)

        # --- Initial State ---
        self._update_ok_button_state()  # Disable OK if 'To' is empty initially

    def _update_ok_button_state(self):
        """Enable OK button only if 'To' value is entered."""
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        if ok_button:
            ok_button.setEnabled(bool(self.to_input.text().strip()))

    def accept(self):
        """Store the result when OK is clicked."""
        if not self.to_input.text().strip():
            # Should ideally not happen due to button state, but double-check
            return

        self._result = {
            "from_value": self._from_value,
            "to_value": self.to_input.text().strip(),
            "category": self.category_combo.currentText(),
            "enabled": self.enabled_checkbox.isChecked(),
        }
        super().accept()

    def get_correction_details(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Execute the dialog and return the details if accepted.

        Returns:
            A dictionary with 'from_value', 'to_value', 'category', 'enabled'
            if the user clicked OK, otherwise None.
        """
        if self.exec() == QDialog.Accepted:
            return self._result
        return None
