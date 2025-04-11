"""
Dialog for adding multiple correction rules from a list of 'From' values.
"""

import typing
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
    QListWidget,
    QAbstractItemView,
)
from PySide6.QtCore import Qt


class BatchAddCorrectionDialog(QDialog):
    """
    A dialog to confirm adding multiple correction rules sharing the same 'To' value.
    """

    def __init__(self, from_values: typing.List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Add Correction Rules")
        self.setMinimumWidth(450)

        if not from_values:
            raise ValueError("Cannot initialize dialog with empty from_values list.")

        self._from_values = from_values
        self._result: typing.Optional[typing.Dict[str, typing.Any]] = None

        # --- Widgets ---
        self.info_label = QLabel(
            f"Create {len(self._from_values)} correction rule(s) for the following 'From' values:"
        )

        self.from_list_widget = QListWidget()
        self.from_list_widget.addItems(self._from_values)
        # Read-only display, maybe allow selection later if needed
        self.from_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.from_list_widget.setMaximumHeight(150)  # Limit height

        self.to_value_edit = QLineEdit()
        self.category_combo = QComboBox()
        # TODO: Populate with actual categories from an enum or service
        self.category_combo.addItems(
            ["Player", "Chest Type", "Source", "General"]
        )  # Example categories

        self.enabled_checkbox = QCheckBox("Enable new rules")
        self.enabled_checkbox.setChecked(True)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # --- Layout ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        layout.addWidget(self.info_label)
        layout.addWidget(self.from_list_widget)

        form_layout.addRow("'To' Value (for all rules):", self.to_value_edit)
        form_layout.addRow("Category:", self.category_combo)
        form_layout.addRow(self.enabled_checkbox)

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.to_value_edit.textChanged.connect(self._update_ok_button_state)

        self._update_ok_button_state()  # Initial check

    def _update_ok_button_state(self):
        """Enable OK button only if 'To' value is not empty."""
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        if ok_button:
            ok_button.setEnabled(bool(self.to_value_edit.text().strip()))

    def accept(self):
        """Store the result when OK is clicked."""
        # Double check 'To' value isn't empty just in case
        to_value = self.to_value_edit.text().strip()
        if not to_value:
            # This case should ideally be prevented by the button state,
            # but add a safeguard. A QMessageBox could be shown here.
            print("Error: 'To' value cannot be empty.")
            return

        self._result = {
            "from_values": self._from_values,
            "to_value": to_value,
            "category": self.category_combo.currentText(),
            "enabled": self.enabled_checkbox.isChecked(),
        }
        super().accept()

    def get_batch_details(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Execute the dialog and return the batch details if accepted.

        Returns:
            A dictionary with 'from_values' (list), 'to_value' (str),
            'category' (str), and 'enabled' (bool) if the user clicked OK,
            otherwise None.
        """
        if self.exec() == QDialog.Accepted:
            return self._result
        return None
