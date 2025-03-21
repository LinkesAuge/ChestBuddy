"""
ValidationTab module.

This module provides the ValidationTab class for displaying validation results.
"""

import logging
from typing import Dict, List, Optional, Set

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QHeaderView,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QSplitter,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import ValidationService

# Set up logger
logger = logging.getLogger(__name__)


class ValidationTab(QWidget):
    """
    Widget for displaying validation results.

    The ValidationTab shows validation issues in the data and allows
    for filtering and examining validation errors.

    Implementation Notes:
        - Displays validation issues in a tree view
        - Allows filtering by validation rule
        - Provides action buttons for validating data
        - Integrates with the ValidationService
    """

    def __init__(
        self,
        data_model: ChestDataModel,
        validation_service: ValidationService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the ValidationTab.

        Args:
            data_model: The data model to validate.
            validation_service: The validation service to use.
            parent: The parent widget.
        """
        super().__init__(parent)

        # Initialize class variables
        self._data_model = data_model
        self._validation_service = validation_service
        self._selected_rules: Set[str] = set()

        # Set up UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Initial update
        self._update_view()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Create splitter for validation controls and results
        splitter = QSplitter(Qt.Vertical)

        # Validation controls panel
        controls_group = QGroupBox("Validation Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Validation rules selection
        rules_layout = QHBoxLayout()

        # Label for rules
        rules_label = QLabel("Select validation rules:")
        rules_layout.addWidget(rules_label)

        # Create checkboxes for default rules
        self._missing_values_check = QCheckBox("Missing Values")
        self._missing_values_check.setChecked(True)
        self._outliers_check = QCheckBox("Outliers")
        self._outliers_check.setChecked(True)
        self._duplicates_check = QCheckBox("Duplicates")
        self._duplicates_check.setChecked(True)
        self._data_types_check = QCheckBox("Data Types")
        self._data_types_check.setChecked(True)

        rules_layout.addWidget(self._missing_values_check)
        rules_layout.addWidget(self._outliers_check)
        rules_layout.addWidget(self._duplicates_check)
        rules_layout.addWidget(self._data_types_check)

        # Add stretch to push checkboxes to the left
        rules_layout.addStretch()

        controls_layout.addLayout(rules_layout)

        # Validation buttons
        buttons_layout = QHBoxLayout()

        self._validate_btn = QPushButton("Validate Data")
        self._validate_btn.setMinimumWidth(150)

        self._clear_validation_btn = QPushButton("Clear Validation")
        self._clear_validation_btn.setMinimumWidth(150)

        buttons_layout.addWidget(self._validate_btn)
        buttons_layout.addWidget(self._clear_validation_btn)
        buttons_layout.addStretch()

        controls_layout.addLayout(buttons_layout)

        # Validation summary
        self._summary_label = QLabel("No validation performed")
        controls_layout.addWidget(self._summary_label)

        splitter.addWidget(controls_group)

        # Validation results tree
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)

        self._results_tree = QTreeWidget()
        self._results_tree.setHeaderLabels(["Row", "Column", "Rule", "Message"])
        self._results_tree.setAlternatingRowColors(True)
        self._results_tree.setColumnWidth(0, 80)
        self._results_tree.setColumnWidth(1, 150)
        self._results_tree.setColumnWidth(2, 120)
        self._results_tree.setSelectionMode(QTreeWidget.ExtendedSelection)

        results_layout.addWidget(self._results_tree)

        splitter.addWidget(results_group)

        # Set splitter sizes
        splitter.setSizes([100, 500])

        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.validation_changed.connect(self._on_validation_changed)

        # Connect UI signals
        self._validate_btn.clicked.connect(self._validate_data)
        self._clear_validation_btn.clicked.connect(self._clear_validation)
        self._results_tree.itemDoubleClicked.connect(self._on_result_double_clicked)

        # Connect checkbox signals
        self._missing_values_check.stateChanged.connect(self._update_selected_rules)
        self._outliers_check.stateChanged.connect(self._update_selected_rules)
        self._duplicates_check.stateChanged.connect(self._update_selected_rules)
        self._data_types_check.stateChanged.connect(self._update_selected_rules)

    def _update_view(self) -> None:
        """Update the view with current validation status."""
        # Clear the results tree
        self._results_tree.clear()

        # Check if data is empty
        if self._data_model.is_empty:
            self._summary_label.setText("No data loaded")
            return

        # Get validation status
        validation_status = self._data_model.get_validation_status()

        if validation_status.empty:
            self._summary_label.setText("No validation issues found")
            return

        # Add results to tree
        issue_count = 0
        rule_counts = {}

        for row_idx, rules in validation_status.items():
            for rule_name, message in rules.items():
                # Skip rules that are not selected
                if self._selected_rules and rule_name not in self._selected_rules:
                    continue

                # Increment issue count
                issue_count += 1

                # Increment rule count
                rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

                # Get row data
                row_data = self._data_model.get_row(row_idx)

                # Create tree item
                item = QTreeWidgetItem()

                # Set row index
                item.setText(0, str(row_idx))

                # Set column (if applicable to a specific column)
                if "in column" in message:
                    column = message.split("in column")[1].split(":")[0].strip()
                    item.setText(1, column)
                elif "in" in message and ":" in message:
                    column = message.split("in")[1].split(":")[0].strip()
                    item.setText(1, column)

                # Set rule name
                item.setText(2, rule_name)

                # Set message
                item.setText(3, message)

                # Set data for row index
                item.setData(0, Qt.UserRole, row_idx)

                # Add to tree
                self._results_tree.addTopLevelItem(item)

        # Update summary label
        if issue_count > 0:
            rule_summary = ", ".join([f"{rule}: {count}" for rule, count in rule_counts.items()])
            self._summary_label.setText(f"Found {issue_count} validation issues: {rule_summary}")
        else:
            self._summary_label.setText("No validation issues found")

        # Resize columns to contents
        for i in range(4):
            self._results_tree.resizeColumnToContents(i)

    def _update_selected_rules(self) -> None:
        """Update the set of selected validation rules based on checkbox states."""
        self._selected_rules = set()

        if self._missing_values_check.isChecked():
            self._selected_rules.add("missing_values")

        if self._outliers_check.isChecked():
            self._selected_rules.add("outliers")

        if self._duplicates_check.isChecked():
            self._selected_rules.add("duplicates")

        if self._data_types_check.isChecked():
            self._selected_rules.add("data_types")

        # Update view with filtered rules
        self._update_view()

    @Slot()
    def _validate_data(self) -> None:
        """Validate the data using the validation service."""
        if self._data_model.is_empty:
            QMessageBox.warning(self, "Warning", "No data to validate")
            return

        # Get selected rules
        rules_to_validate = list(self._selected_rules) if self._selected_rules else None

        # Validate data
        validation_results = self._validation_service.validate_data(rules_to_validate)

        # Update view
        self._update_view()

        # Show message if no issues found
        if not validation_results:
            QMessageBox.information(
                self, "Validation Complete", "No validation issues found with the selected rules."
            )

    @Slot()
    def _clear_validation(self) -> None:
        """Clear all validation status."""
        # Confirm clear
        if self._data_model.get_validation_status().empty:
            return

        reply = QMessageBox.question(
            self,
            "Clear Validation",
            "Are you sure you want to clear all validation results?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Clear validation status
        self._data_model.clear_validation_status()

        # Update view
        self._update_view()

    @Slot(QTreeWidgetItem, int)
    def _on_result_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle double-clicking a validation result.

        Args:
            item: The clicked tree widget item.
            column: The clicked column index.
        """
        # Get row index from item data
        row_idx = item.data(0, Qt.UserRole)

        if row_idx is None:
            return

        # Show row details
        self._show_row_details(row_idx)

    def _show_row_details(self, row_idx) -> None:
        """
        Show detailed information for a row.

        Args:
            row_idx: The index of the row to show details for.
        """
        # Get row data
        row_data = self._data_model.get_row(row_idx)

        if row_data is None:
            return

        # Create message with row details
        message = f"<b>Row {row_idx} Details:</b><br><br>"

        for col, value in row_data.items():
            message += f"<b>{col}:</b> {value}<br>"

        # Get validation status for the row
        validation_status = self._data_model.get_validation_status(row_idx)

        if validation_status:
            message += "<br><b>Validation Issues:</b><br>"
            for rule, issue in validation_status.items():
                message += f"- <span style='color:red'>{rule}:</span> {issue}<br>"

        # Show message box with details
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Row {row_idx} Details")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    @Slot(object)
    def _on_data_changed(self, data) -> None:
        """
        Handle data changed signal.

        Args:
            data: The updated data.
        """
        # Update view to reflect data changes
        self._update_view()

    @Slot(object)
    def _on_validation_changed(self, validation_status) -> None:
        """
        Handle validation changed signal.

        Args:
            validation_status: The validation status.
        """
        # Update view to reflect validation changes
        self._update_view()
