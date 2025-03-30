"""
Batch Correction Dialog.

This module implements a dialog for creating multiple correction rules at once
from a set of selected cells.
"""

from typing import Optional, List, Dict, Any
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QGroupBox,
    QMessageBox,
)

from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.core.services.validation_service import ValidationService


class BatchCorrectionDialog(QDialog):
    """
    Dialog for creating multiple correction rules at once.

    This dialog allows users to create multiple correction rules based on
    selected cells in a data table.
    """

    def __init__(
        self,
        selected_cells: List[Dict[str, Any]],
        validation_service: ValidationService,
        parent=None,
    ):
        """
        Initialize the dialog.

        Args:
            selected_cells: List of dictionaries containing information about selected cells
                Each dictionary should have 'row', 'col', 'value', and 'column_name' keys
            validation_service: Service for validating values against known valid values
            parent: Parent widget
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._selected_cells = selected_cells
        self._validation_service = validation_service

        # Set window title
        self.setWindowTitle("Batch Correction Rules")

        # Setup UI
        self._setup_ui()

        # Populate table with selected cells
        self._populate_table()

    def _setup_ui(self):
        """Set up the UI components for the dialog."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Table title
        title_label = QLabel("Create correction rules for selected cells:")
        title_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(title_label)

        # Corrections table
        self._corrections_table = QTableWidget()
        self._corrections_table.setAlternatingRowColors(True)
        self._corrections_table.setColumnCount(4)
        self._corrections_table.setHorizontalHeaderLabels(
            ["Original Value", "Column", "Correct To", "Category"]
        )

        # Set column stretching
        header = self._corrections_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        main_layout.addWidget(self._corrections_table)

        # Global options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # Auto-enable rules option
        self._auto_enable_checkbox = QCheckBox("Automatically enable all rules")
        self._auto_enable_checkbox.setChecked(True)
        # Connect the clicked signal to ensure it updates state correctly for tests
        self._auto_enable_checkbox.clicked.connect(self._on_auto_enable_changed)
        options_layout.addWidget(self._auto_enable_checkbox)

        # Add to validation lists option
        self._add_to_validation_checkbox = QCheckBox("Add corrections to validation lists")
        self._add_to_validation_checkbox.setChecked(True)
        # Connect the clicked signal to ensure it updates state correctly for tests
        self._add_to_validation_checkbox.clicked.connect(self._on_add_to_validation_changed)
        options_layout.addWidget(self._add_to_validation_checkbox)

        main_layout.addWidget(options_group)

        # Reset corrections button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self._reset_button = QPushButton("Reset Corrections")
        reset_layout.addWidget(self._reset_button)
        main_layout.addLayout(reset_layout)

        # Dialog buttons
        button_box = QDialogButtonBox()
        self._create_button = QPushButton("Create Rules")
        self._create_button.setDefault(True)
        self._cancel_button = QPushButton("Cancel")

        button_box.addButton(self._create_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(self._cancel_button, QDialogButtonBox.RejectRole)

        main_layout.addWidget(button_box)

        # Connect signals
        self._reset_button.clicked.connect(self._reset_corrections)
        # Use direct connect to ensure button clicks are properly processed
        self._create_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)

        # Set minimum size for the dialog
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

    def _on_auto_enable_changed(self, checked):
        """Handle auto enable checkbox state changes."""
        # Explicitly set the checked state to ensure it updates for tests
        self._auto_enable_checkbox.setChecked(checked)

    def _on_add_to_validation_changed(self, checked):
        """Handle add to validation checkbox state changes."""
        # Explicitly set the checked state to ensure it updates for tests
        self._add_to_validation_checkbox.setChecked(checked)

    def _populate_table(self):
        """Populate the corrections table with data from selected cells."""
        # Get validation lists for populating comboboxes
        validation_lists = self._validation_service.get_validation_lists()

        # Set row count based on selected cells
        self._corrections_table.setRowCount(len(self._selected_cells))

        # Fill table with cell data
        for row, cell_data in enumerate(self._selected_cells):
            # Original value (not editable)
            original_item = QTableWidgetItem(cell_data["value"])
            original_item.setFlags(original_item.flags() & ~Qt.ItemIsEditable)
            self._corrections_table.setItem(row, 0, original_item)

            # Column name (not editable)
            column_item = QTableWidgetItem(cell_data["column_name"])
            column_item.setFlags(column_item.flags() & ~Qt.ItemIsEditable)
            self._corrections_table.setItem(row, 1, column_item)

            # Correct To (combobox with suggestions)
            correction_combo = QComboBox()
            correction_combo.setEditable(True)
            correction_combo.setInsertPolicy(QComboBox.InsertAtBottom)

            # Add validation list items if available for this column/category
            if cell_data["column_name"] in validation_lists:
                for value in sorted(validation_lists[cell_data["column_name"]]):
                    correction_combo.addItem(value)

            self._corrections_table.setCellWidget(row, 2, correction_combo)

            # Category (combobox, defaulting to column name)
            category_combo = QComboBox()

            # Add all known categories
            for category in sorted(validation_lists.keys()):
                category_combo.addItem(category)

            # Set default to column name if available
            column_name = cell_data["column_name"]
            index = category_combo.findText(column_name)
            if index >= 0:
                category_combo.setCurrentIndex(index)

            self._corrections_table.setCellWidget(row, 3, category_combo)

    def _reset_corrections(self):
        """Reset all corrections to default (empty) values."""
        for row in range(self._corrections_table.rowCount()):
            # Reset the Correct To combobox
            correction_combo = self._corrections_table.cellWidget(row, 2)
            if correction_combo:
                correction_combo.setCurrentIndex(-1)
                correction_combo.setEditText("")

    def _validate_corrections(self) -> bool:
        """
        Validate that at least one correction is specified.

        Returns:
            bool: True if valid, False otherwise
        """
        # Check if at least one row has a correction specified
        for row in range(self._corrections_table.rowCount()):
            correction_combo = self._corrections_table.cellWidget(row, 2)
            if correction_combo and correction_combo.currentText().strip():
                return True

        # No corrections specified
        QMessageBox.warning(
            self, "Validation Error", "Please specify at least one correction value."
        )
        return False

    def _add_to_validation_lists(self):
        """Add all correction values to their respective validation lists."""
        if not self._add_to_validation_checkbox.isChecked():
            return

        for row in range(self._corrections_table.rowCount()):
            # Get category and correction
            category_combo = self._corrections_table.cellWidget(row, 3)
            correction_combo = self._corrections_table.cellWidget(row, 2)

            if not category_combo or not correction_combo:
                continue

            category = category_combo.currentText().strip()
            correction = correction_combo.currentText().strip()

            # Skip if category or correction is empty
            if not category or not correction:
                continue

            # Add to validation list
            try:
                self._validation_service.add_validation_entry(category, correction)
                self._logger.info(f"Added '{correction}' to '{category}' validation list")
            except Exception as e:
                self._logger.error(f"Error adding to validation list: {str(e)}")

    def accept(self):
        """Override accept to validate inputs first."""
        if not self._validate_corrections():
            return

        # Add to validation lists if requested
        self._add_to_validation_lists()

        # Call parent accept if validation passed
        super().accept()

    def get_rules(self) -> List[CorrectionRule]:
        """
        Get a list of CorrectionRule objects from the current dialog values.

        Returns:
            List[CorrectionRule]: A list of correction rules
        """
        rules = []

        for row in range(self._corrections_table.rowCount()):
            # Get values from UI
            original_item = self._corrections_table.item(row, 0)
            original_value = original_item.text() if original_item else ""

            correction_combo = self._corrections_table.cellWidget(row, 2)
            correction = correction_combo.currentText().strip() if correction_combo else ""

            category_combo = self._corrections_table.cellWidget(row, 3)
            category = category_combo.currentText() if category_combo else ""

            # Skip if no correction is specified
            if not correction:
                continue

            # Create the rule object
            rule = CorrectionRule(
                to_value=correction,
                from_value=original_value,
                category=category,
                status="enabled" if self._auto_enable_checkbox.isChecked() else "disabled",
                order=100,  # Default order
            )

            rules.append(rule)

        return rules
