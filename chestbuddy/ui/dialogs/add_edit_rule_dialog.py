"""
Add/Edit Rule Dialog.

This module implements a dialog for adding or editing correction rules.
"""

from typing import Optional, Dict, List, Any
import logging

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
    QSpinBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QMessageBox,
)

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.services.validation_service import ValidationService


class AddEditRuleDialog(QDialog):
    """
    Dialog for adding or editing a correction rule.

    This dialog allows users to create a new correction rule or edit an existing one.
    It provides fields for all rule properties and validates inputs before accepting.
    """

    def __init__(
        self,
        validation_service: ValidationService,
        parent=None,
        rule: Optional[CorrectionRule] = None,
    ):
        """
        Initialize the dialog.

        Args:
            validation_service: Service for validating values against known valid values
            parent: Parent widget
            rule: Existing rule to edit, or None to create a new rule
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._validation_service = validation_service
        self._edit_mode = rule is not None
        self._rule = rule

        # Set window title based on mode
        self.setWindowTitle("Edit Correction Rule" if self._edit_mode else "Add Correction Rule")

        # Setup UI
        self._setup_ui()

        # Populate fields if editing
        if self._edit_mode:
            self._populate_fields()

        # Update UI state based on initial values
        self._update_validation_button_state()

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

        # Original value field
        self._from_value = QLineEdit()
        self._from_value.setPlaceholderText("Value to correct")
        form_layout.addRow("Original Value:", self._from_value)

        # Corrected value field
        self._to_value = QLineEdit()
        self._to_value.setPlaceholderText("Corrected value")
        form_layout.addRow("Correct To:", self._to_value)

        # Category field with validation list options
        self._category_combo = QComboBox()
        self._category_combo.setEditable(True)
        self._category_combo.setInsertPolicy(QComboBox.InsertAlphabetically)
        self._category_combo.addItem("general")  # Default category

        # Populate categories from validation lists
        validation_lists = self._validation_service.get_validation_lists()
        for category in sorted(validation_lists.keys()):
            if category != "general":  # Skip if already added
                self._category_combo.addItem(category)

        form_layout.addRow("Category:", self._category_combo)

        # Order field
        self._order = QSpinBox()
        self._order.setMinimum(0)
        self._order.setMaximum(9999)
        self._order.setValue(0)  # Default order
        form_layout.addRow("Order:", self._order)

        # Status radio buttons
        status_group = QGroupBox("Status")
        status_layout = QHBoxLayout(status_group)

        self._status_group = QButtonGroup(self)
        self._enabled_radio = QRadioButton("Enabled")
        self._disabled_radio = QRadioButton("Disabled")

        self._status_group.addButton(self._enabled_radio, 1)
        self._status_group.addButton(self._disabled_radio, 2)

        # Connect radio buttons to ensure exclusive behavior
        self._status_group.buttonClicked.connect(self._on_status_changed)

        status_layout.addWidget(self._enabled_radio)
        status_layout.addWidget(self._disabled_radio)

        # Default to enabled
        self._enabled_radio.setChecked(True)

        form_layout.addRow("", status_group)

        main_layout.addLayout(form_layout)

        # Add to validation list button
        validation_layout = QHBoxLayout()
        validation_layout.addStretch()
        self._add_to_validation_button = QPushButton("Add to Validation List")
        self._add_to_validation_button.setEnabled(False)
        validation_layout.addWidget(self._add_to_validation_button)
        main_layout.addLayout(validation_layout)

        # Dialog buttons
        buttons_layout = QHBoxLayout()

        self._ok_button = QPushButton("OK")
        self._ok_button.setDefault(True)
        self._ok_button.clicked.connect(self.accept)

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self._ok_button)
        buttons_layout.addWidget(self._cancel_button)

        main_layout.addLayout(buttons_layout)

        # Connect signals
        self._category_combo.currentTextChanged.connect(self._update_validation_button_state)
        self._to_value.textChanged.connect(self._update_validation_button_state)
        self._add_to_validation_button.clicked.connect(self._add_to_validation_list)

        # Set minimum size for the dialog
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

    def _on_status_changed(self, button):
        """Handle status radio button changes."""
        # Ensure proper state update for test_status_radio_buttons
        if button == self._enabled_radio:
            self._enabled_radio.setChecked(True)
            self._disabled_radio.setChecked(False)
        elif button == self._disabled_radio:
            self._enabled_radio.setChecked(False)
            self._disabled_radio.setChecked(True)

    def set_status(self, status: str):
        """
        Set the status radio buttons.

        Args:
            status: The status to set ('enabled' or 'disabled')
        """
        if status == "enabled":
            self._enabled_radio.setChecked(True)
            self._disabled_radio.setChecked(False)
        else:
            self._enabled_radio.setChecked(False)
            self._disabled_radio.setChecked(True)

    def _populate_fields(self):
        """Populate the dialog fields with values from the existing rule."""
        if not self._rule:
            return

        # Fix the order of assignments to match what the test expects
        self._from_value.setText(self._rule.from_value)
        self._to_value.setText(self._rule.to_value)

        # Find category in combobox or add it
        category_index = self._category_combo.findText(self._rule.category)
        if category_index >= 0:
            self._category_combo.setCurrentIndex(category_index)
        else:
            self._category_combo.addItem(self._rule.category)
            self._category_combo.setCurrentText(self._rule.category)

        # Set order
        self._order.setValue(self._rule.order)

        # Set status
        self.set_status(self._rule.status)

    def _update_validation_button_state(self):
        """Update the state of the 'Add to Validation List' button."""
        category = self._category_combo.currentText()
        to_value = self._to_value.text()

        # Enable the button if we have a value, regardless of category
        # This matches the test expectation that general category with a to_value should enable the button
        can_add = bool(to_value)

        # Check if the value is already in the validation list
        if can_add and category in self._validation_service.get_validation_lists():
            validation_lists = self._validation_service.get_validation_lists()
            if category in validation_lists and to_value in validation_lists[category]:
                can_add = False

        self._add_to_validation_button.setEnabled(can_add)

    def _add_to_validation_list(self):
        """Add the current 'Correct To' value to the validation list for the current category."""
        category = self._category_combo.currentText()
        value = self._to_value.text()

        if not category or not value:
            return

        try:
            self._validation_service.add_validation_entry(category, value)
            QMessageBox.information(
                self,
                "Added to Validation List",
                f"Added '{value}' to the '{category}' validation list.",
            )
            self._logger.info(f"Added '{value}' to '{category}' validation list")

            # Disable the button now that the value is in the list
            self._add_to_validation_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add to validation list: {str(e)}")
            self._logger.error(f"Error adding to validation list: {str(e)}")

    def _validate_inputs(self) -> bool:
        """
        Validate the input fields.

        Returns:
            bool: True if all fields are valid, False otherwise
        """
        from_value = self._from_value.text().strip()
        to_value = self._to_value.text().strip()
        category = self._category_combo.currentText().strip()

        # Check required fields
        if not from_value or not to_value or not category:
            QMessageBox.warning(
                self, "Validation Error", "All fields are required. Please complete all fields."
            )
            return False

        # Validation passed
        return True

    def accept(self):
        """Override accept to validate inputs first."""
        if not self._validate_inputs():
            return

        # Call parent accept if validation passed
        super().accept()

    def get_rule(self) -> CorrectionRule:
        """
        Get a CorrectionRule object from the current dialog values.

        Returns:
            CorrectionRule: A new or updated correction rule
        """
        # Get values from UI
        from_value = self._from_value.text().strip()
        to_value = self._to_value.text().strip()
        category = self._category_combo.currentText().strip()
        order = self._order.value()
        status = "enabled" if self._enabled_radio.isChecked() else "disabled"

        # Create the rule object
        rule = CorrectionRule(
            to_value=to_value,
            from_value=from_value,
            category=category,
            status=status,
            order=order,
        )

        return rule
