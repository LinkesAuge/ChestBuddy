"""
Dialog for adding multiple entries to a validation list.
"""

import typing
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QDialogButtonBox,
    QComboBox,
    QListWidget,
    QAbstractItemView,
)
from PySide6.QtCore import Qt

# Placeholder for ValidationListType enum if it exists
# from ...core.enums import ValidationListType


class BatchAddValidationDialog(QDialog):
    """
    A dialog to confirm adding multiple values to a specific validation list.
    """

    def __init__(self, values_to_add: typing.List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Add to Validation List")
        self.setMinimumWidth(400)

        if not values_to_add:
            raise ValueError("Cannot initialize dialog with empty values list.")

        self._values_to_add = values_to_add
        self._result: typing.Optional[typing.Dict[str, typing.Any]] = None

        # --- Widgets ---
        self.info_label = QLabel(
            f"Add the following {len(self._values_to_add)} value(s) to a validation list:"
        )

        self.value_list_widget = QListWidget()
        self.value_list_widget.addItems(self._values_to_add)
        self.value_list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.value_list_widget.setMaximumHeight(150)

        self.list_type_combo = QComboBox()
        # TODO: Populate with actual list types from an enum or service
        self.list_type_combo.addItems(["Player", "Chest Type", "Source"])  # Example types

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # --- Layout ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        layout.addWidget(self.info_label)
        layout.addWidget(self.value_list_widget)
        form_layout.addRow("Target List:", self.list_type_combo)

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def accept(self):
        """Store the result when OK is clicked."""
        self._result = {
            "values": self._values_to_add,
            "list_type": self.list_type_combo.currentText(),
        }
        super().accept()

    def get_batch_details(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """
        Execute the dialog and return the details if accepted.

        Returns:
            A dictionary with 'values' (list) and 'list_type' (str)
            if the user clicked OK, otherwise None.
        """
        if self.exec() == QDialog.Accepted:
            return self._result
        return None
