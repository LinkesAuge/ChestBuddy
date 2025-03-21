"""
CorrectionTab module.

This module provides the CorrectionTab class for applying corrections to data.
"""

import logging
from typing import Dict, List, Optional, Set, Any

import pandas as pd
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
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QRadioButton,
    QButtonGroup,
    QDialog,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont

from chestbuddy.core.models import ChestDataModel
from chestbuddy.core.services import CorrectionService

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionTab(QWidget):
    """
    Widget for applying corrections to data.

    The CorrectionTab provides functionality for applying various correction
    strategies to fix validation issues in the data.

    Implementation Notes:
        - Presents available correction strategies
        - Allows selection of columns and rows to correct
        - Provides parameters for correction strategies
        - Tracks correction history
    """

    def __init__(
        self,
        data_model: ChestDataModel,
        correction_service: CorrectionService,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the CorrectionTab.

        Args:
            data_model: The data model to correct.
            correction_service: The correction service to use.
            parent: The parent widget.
        """
        super().__init__(parent)

        # Initialize class variables
        self._data_model = data_model
        self._correction_service = correction_service
        self._selected_rows: List[int] = []

        # Set up UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        # Initial update
        self._update_view()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # Create splitter for correction controls and history
        splitter = QSplitter(Qt.Vertical)

        # Correction controls panel
        controls_group = QGroupBox("Correction Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Strategy selection
        strategy_form = QFormLayout()

        # Strategy combo box
        self._strategy_combo = QComboBox()
        self._strategy_combo.addItems(
            [
                "Fill Missing Values (Mean)",
                "Fill Missing Values (Median)",
                "Fill Missing Values (Mode)",
                "Fill Missing Values (Constant)",
                "Remove Duplicates",
                "Fix Outliers (Mean)",
                "Fix Outliers (Median)",
                "Fix Outliers (Winsorize)",
            ]
        )
        strategy_form.addRow("Correction Strategy:", self._strategy_combo)

        # Column selection
        self._column_combo = QComboBox()
        self._column_combo.setMinimumWidth(200)
        strategy_form.addRow("Column:", self._column_combo)

        # Rows selection
        self._rows_group = QGroupBox("Apply to Rows")
        rows_layout = QVBoxLayout(self._rows_group)

        # Radio buttons for row selection
        self._all_rows_radio = QRadioButton("All Rows")
        self._all_rows_radio.setChecked(True)
        self._validation_rows_radio = QRadioButton("Rows with Validation Issues")
        self._selected_rows_radio = QRadioButton("Selected Rows")

        # Create button group
        self._rows_button_group = QButtonGroup()
        self._rows_button_group.addButton(self._all_rows_radio, 0)
        self._rows_button_group.addButton(self._validation_rows_radio, 1)
        self._rows_button_group.addButton(self._selected_rows_radio, 2)

        rows_layout.addWidget(self._all_rows_radio)
        rows_layout.addWidget(self._validation_rows_radio)
        rows_layout.addWidget(self._selected_rows_radio)

        strategy_form.addRow("", self._rows_group)

        # Strategy parameters group
        self._params_group = QGroupBox("Strategy Parameters")
        self._params_layout = QFormLayout(self._params_group)

        # Parameter widgets
        self._constant_value = QLineEdit()
        self._constant_value.setPlaceholderText("Enter constant value...")
        self._threshold_spin = QDoubleSpinBox()
        self._threshold_spin.setRange(0.1, 10.0)
        self._threshold_spin.setValue(3.0)
        self._threshold_spin.setSingleStep(0.1)

        # Initially hide parameter widgets
        self._constant_value.hide()
        self._threshold_spin.hide()

        self._params_layout.addRow("Constant Value:", self._constant_value)
        self._params_layout.addRow("Z-score Threshold:", self._threshold_spin)

        strategy_form.addRow("", self._params_group)

        controls_layout.addLayout(strategy_form)

        # Apply button
        apply_layout = QHBoxLayout()
        self._apply_btn = QPushButton("Apply Correction")
        self._apply_btn.setMinimumWidth(150)
        apply_layout.addWidget(self._apply_btn)
        apply_layout.addStretch()

        controls_layout.addLayout(apply_layout)

        # Status label
        self._status_label = QLabel("No corrections applied")
        controls_layout.addWidget(self._status_label)

        splitter.addWidget(controls_group)

        # Correction history panel
        history_group = QGroupBox("Correction History")
        history_layout = QVBoxLayout(history_group)

        self._history_tree = QTreeWidget()
        self._history_tree.setHeaderLabels(["Timestamp", "Strategy", "Column", "Rows Affected"])
        self._history_tree.setAlternatingRowColors(True)
        self._history_tree.setColumnWidth(0, 180)
        self._history_tree.setColumnWidth(1, 150)
        self._history_tree.setColumnWidth(2, 120)

        history_layout.addWidget(self._history_tree)

        splitter.addWidget(history_group)

        # Set splitter sizes
        splitter.setSizes([300, 300])

        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect model signals
        self._data_model.data_changed.connect(self._on_data_changed)
        self._data_model.correction_applied.connect(self._on_correction_applied)

        # Connect UI signals
        self._strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)
        self._apply_btn.clicked.connect(self._apply_correction)
        self._history_tree.itemDoubleClicked.connect(self._on_history_double_clicked)

    def _update_view(self) -> None:
        """Update the view with current data and correction status."""
        # Check if data is empty
        if self._data_model.is_empty:
            self._column_combo.clear()
            self._status_label.setText("No data loaded")
            return

        # Get data from model
        data = self._data_model.data

        # Update column combo box
        current_column = self._column_combo.currentText()
        self._column_combo.clear()
        self._column_combo.addItems(self._data_model.column_names)

        # Restore selected column if it exists
        if current_column in self._data_model.column_names:
            self._column_combo.setCurrentText(current_column)

        # Update correction history
        self._update_history()

        # Update status label
        correction_status = self._data_model.get_correction_status()
        if not correction_status.empty:
            rows_affected = len(correction_status)
            self._status_label.setText(f"Corrections applied to {rows_affected} rows")
        else:
            self._status_label.setText("No corrections applied")

    def _update_history(self) -> None:
        """Update the correction history tree."""
        # Clear the history tree
        self._history_tree.clear()

        # Get correction history
        history = self._correction_service.get_correction_history()

        if not history:
            return

        # Add history items to tree
        for record in history:
            item = QTreeWidgetItem()

            # Set timestamp
            timestamp = record.get("timestamp")
            if timestamp:
                item.setText(0, timestamp.strftime("%Y-%m-%d %H:%M:%S"))

            # Set strategy
            strategy = record.get("strategy", "")
            item.setText(1, strategy)

            # Set column
            column = record.get("column", "All columns")
            item.setText(2, column or "All columns")

            # Set rows affected
            rows = record.get("rows")
            if rows:
                item.setText(3, f"{len(rows)} rows")
            else:
                item.setText(3, "All rows")

            # Store record data
            item.setData(0, Qt.UserRole, record)

            # Add to tree
            self._history_tree.addTopLevelItem(item)

        # Resize columns to contents
        for i in range(4):
            self._history_tree.resizeColumnToContents(i)

    def _on_strategy_changed(self, index: int) -> None:
        """
        Handle strategy combo box changes.

        Args:
            index: The index of the selected strategy.
        """
        # Hide all parameter widgets
        self._constant_value.hide()
        self._threshold_spin.hide()

        # Show relevant parameter widgets based on strategy
        strategy_text = self._strategy_combo.currentText()

        if "Constant" in strategy_text:
            self._constant_value.show()

        if "Outliers" in strategy_text:
            self._threshold_spin.show()

    @Slot()
    def _apply_correction(self) -> None:
        """Apply the selected correction strategy."""
        if self._data_model.is_empty:
            QMessageBox.warning(self, "Warning", "No data to correct")
            return

        # Get strategy name
        strategy_text = self._strategy_combo.currentText()
        strategy_name = self._get_strategy_name(strategy_text)

        # Get column
        column = self._column_combo.currentText()

        # Get rows to correct
        rows = self._get_rows_to_correct()

        # Get strategy-specific parameters
        params = {}

        if "constant" in strategy_name:
            params["value"] = self._constant_value.text()

        if "outliers" in strategy_name:
            params["threshold"] = self._threshold_spin.value()

        # Apply correction
        success, error = self._correction_service.apply_correction(
            strategy_name, column=column, rows=rows, **params
        )

        if not success:
            QMessageBox.critical(self, "Correction Error", f"Failed to apply correction: {error}")
            return

        # Update view
        self._update_view()

        # Show success message
        affected_rows = len(rows) if rows else len(self._data_model.data)
        QMessageBox.information(
            self,
            "Correction Applied",
            f"Correction '{strategy_text}' applied successfully to {affected_rows} rows.",
        )

    def _get_strategy_name(self, strategy_text: str) -> str:
        """
        Convert strategy display text to strategy name.

        Args:
            strategy_text: The display text of the strategy.

        Returns:
            The strategy name.
        """
        # Map display text to strategy name
        if "Fill Missing Values (Mean)" in strategy_text:
            return "fill_missing_mean"
        elif "Fill Missing Values (Median)" in strategy_text:
            return "fill_missing_median"
        elif "Fill Missing Values (Mode)" in strategy_text:
            return "fill_missing_mode"
        elif "Fill Missing Values (Constant)" in strategy_text:
            return "fill_missing_constant"
        elif "Remove Duplicates" in strategy_text:
            return "remove_duplicates"
        elif "Fix Outliers (Mean)" in strategy_text:
            return "fix_outliers_mean"
        elif "Fix Outliers (Median)" in strategy_text:
            return "fix_outliers_median"
        elif "Fix Outliers (Winsorize)" in strategy_text:
            return "fix_outliers_winsorize"
        else:
            return ""

    def _get_rows_to_correct(self) -> Optional[List[int]]:
        """
        Get the rows to apply the correction to.

        Returns:
            A list of row indices, or None for all rows.
        """
        # Get selected radio button
        button_id = self._rows_button_group.checkedId()

        if button_id == 0:
            # All rows
            return None
        elif button_id == 1:
            # Rows with validation issues
            validation_status = self._data_model.get_validation_status()
            if not validation_status.empty:
                return list(validation_status.keys())
            else:
                return None
        elif button_id == 2:
            # Selected rows
            return self._selected_rows if self._selected_rows else None
        else:
            return None

    def set_selected_rows(self, rows: List[int]) -> None:
        """
        Set the selected rows.

        Args:
            rows: The list of selected row indices.
        """
        self._selected_rows = rows

        # Update status if selected rows radio is checked
        if self._selected_rows_radio.isChecked():
            count = len(self._selected_rows)
            self._status_label.setText(f"Selected {count} rows for correction")

    @Slot(QTreeWidgetItem, int)
    def _on_history_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle double-clicking a history item.

        Args:
            item: The clicked tree widget item.
            column: The clicked column index.
        """
        # Get record data from item
        record = item.data(0, Qt.UserRole)

        if not record:
            return

        # Show record details
        self._show_record_details(record)

    def _show_record_details(self, record: Dict[str, Any]) -> None:
        """
        Show detailed information for a correction record.

        Args:
            record: The correction record to show details for.
        """
        # Format timestamp
        timestamp = record.get("timestamp")
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "Unknown"

        # Format strategy
        strategy = record.get("strategy", "Unknown")

        # Format column
        column = record.get("column", "All columns")
        column_str = column or "All columns"

        # Format rows
        rows = record.get("rows")
        if rows:
            rows_str = f"{len(rows)} rows"
            rows_detail = f"Rows: {', '.join(map(str, rows[:10]))}"
            if len(rows) > 10:
                rows_detail += f" and {len(rows) - 10} more"
        else:
            rows_str = "All rows"
            rows_detail = "All rows in the dataset"

        # Format args
        args = record.get("args", {})
        args_str = ", ".join([f"{k}={v}" for k, v in args.items()]) if args else "None"

        # Create message with record details
        message = f"<b>Correction Details:</b><br><br>"
        message += f"<b>Timestamp:</b> {timestamp_str}<br>"
        message += f"<b>Strategy:</b> {strategy}<br>"
        message += f"<b>Column:</b> {column_str}<br>"
        message += f"<b>Rows Affected:</b> {rows_str}<br>"
        message += f"<b>Parameters:</b> {args_str}<br>"
        message += f"<b>Details:</b> {rows_detail}<br>"

        # Show message box with details
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Correction Details")
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
    def _on_correction_applied(self, correction_status) -> None:
        """
        Handle correction applied signal.

        Args:
            correction_status: The correction status.
        """
        # Update view to reflect correction changes
        self._update_view()
