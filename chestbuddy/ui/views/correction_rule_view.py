"""
Correction Rule View.

This module implements the main UI view for managing correction rules in the ChestBuddy application.
It provides a UI for viewing, filtering, and managing correction rules.
"""

from typing import Optional, List, Dict, Any
import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QMessageBox,
    QSplitter,
    QAbstractItemView,
    QStatusBar,
)

from chestbuddy.core.controllers.correction_controller import CorrectionController
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.ui.dialogs.add_edit_rule_dialog import AddEditRuleDialog
from chestbuddy.ui.dialogs.batch_correction_dialog import BatchCorrectionDialog
from chestbuddy.ui.dialogs.import_export_dialog import ImportExportDialog
from chestbuddy.ui.models.correction_rule_table_model import CorrectionRuleTableModel


class CorrectionRuleView(QWidget):
    """
    Widget that displays and manages correction rules.

    This view provides an interface for users to view, filter, add, edit, and delete correction rules.
    It also allows users to apply corrections to data based on these rules.

    Signals:
        apply_corrections_requested (bool, bool): Signal emitted when corrections should be applied
            with parameters for recursive mode and selected only mode.
        rule_added (CorrectionRule): Signal emitted when a new rule is added.
        rule_edited (CorrectionRule): Signal emitted when a rule is edited.
        rule_deleted (int): Signal emitted when a rule is deleted, with the rule ID.
    """

    # Signals for view-controller communication
    apply_corrections_requested = Signal(bool, bool)
    rule_added = Signal(object)
    rule_edited = Signal(object)
    rule_deleted = Signal(int)

    def __init__(
        self,
        correction_controller: CorrectionController,
        parent: Optional[QWidget] = None,
        debug_mode: bool = False,
    ):
        """
        Initialize the correction rule view.

        Args:
            correction_controller: Controller for managing correction rules and applying corrections
            parent: Parent widget
            debug_mode: Whether to enable debug features
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._controller = correction_controller
        self._debug_mode = debug_mode

        # Keep track of current rule filter
        self._current_filter = {
            "category": "",
            "status": "",
            "search": "",
        }

        # Setup UI components
        self.setWindowTitle("Correction Rules")
        self._setup_ui()
        self._connect_signals()

        # Populate the view with initial data
        self._refresh_rule_table()
        self._update_categories_filter()
        self._update_status_bar()

    def _setup_ui(self):
        """Set up the UI components for the view."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main splitter for filter panel and rule table
        self._main_splitter = QSplitter(Qt.Horizontal)

        # Left panel with filters and settings
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)
        filter_layout.setContentsMargins(10, 10, 10, 10)

        # Filter controls
        self._filter_controls = QWidget()
        filter_controls_layout = QVBoxLayout(self._filter_controls)
        filter_controls_layout.setContentsMargins(0, 0, 0, 0)

        # Filter group box
        filter_group = QGroupBox("Filter Rules")
        filter_group_layout = QVBoxLayout(filter_group)

        # Category filter
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self._category_filter = QComboBox()
        self._category_filter.addItem("All Categories")
        category_layout.addWidget(self._category_filter)
        filter_group_layout.addLayout(category_layout)

        # Status filter
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItem("All")
        self._status_filter.addItem("Enabled")
        self._status_filter.addItem("Disabled")
        status_layout.addWidget(self._status_filter)
        filter_group_layout.addLayout(status_layout)

        # Search filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search rules...")
        search_layout.addWidget(self._search_edit)
        filter_group_layout.addLayout(search_layout)

        # Reset filters button
        self._reset_filters_button = QPushButton("Reset Filters")
        filter_group_layout.addWidget(self._reset_filters_button)

        filter_controls_layout.addWidget(filter_group)
        filter_layout.addWidget(self._filter_controls)

        # Settings panel
        self._settings_panel = QWidget()
        settings_layout = QVBoxLayout(self._settings_panel)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        settings_group = QGroupBox("Correction Settings")
        settings_group_layout = QVBoxLayout(settings_group)

        # Recursive option
        self._recursive_checkbox = QCheckBox("Apply corrections recursively")
        self._recursive_checkbox.setToolTip(
            "Apply corrections repeatedly until no more changes are made"
        )
        self._recursive_checkbox.setChecked(True)
        settings_group_layout.addWidget(self._recursive_checkbox)

        # Only invalid cells option
        self._correct_invalid_only_checkbox = QCheckBox("Only correct invalid cells")
        self._correct_invalid_only_checkbox.setToolTip(
            "Only apply corrections to cells marked as invalid"
        )
        self._correct_invalid_only_checkbox.setChecked(True)
        settings_group_layout.addWidget(self._correct_invalid_only_checkbox)

        # Apply corrections button
        self._apply_button = QPushButton("Apply Corrections")
        self._apply_button.setObjectName("primaryButton")
        settings_group_layout.addWidget(self._apply_button)

        settings_layout.addWidget(settings_group)
        filter_layout.addWidget(self._settings_panel)
        filter_layout.addStretch()

        # Right panel with rule table and controls
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(10, 10, 10, 10)

        # Rule table
        self._rule_table = QTableWidget()
        self._rule_table.setObjectName("ruleTable")
        self._rule_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._rule_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._rule_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rule_table.setAlternatingRowColors(True)

        # Set up columns
        self._rule_table.setColumnCount(5)
        headers = ["Order", "From", "To", "Category", "Status"]
        self._rule_table.setHorizontalHeaderLabels(headers)
        header = self._rule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Order
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status

        # Create and set model
        self._rule_table_model = CorrectionRuleTableModel(self._controller)

        table_layout.addWidget(self._rule_table)

        # Table controls
        self._rule_controls = QWidget()
        rule_controls_layout = QHBoxLayout(self._rule_controls)
        rule_controls_layout.setContentsMargins(0, 0, 0, 0)

        self._add_button = QPushButton("Add Rule")
        self._edit_button = QPushButton("Edit Rule")
        self._delete_button = QPushButton("Delete Rule")
        self._toggle_status_button = QPushButton("Toggle Status")
        self._move_up_button = QPushButton("↑")
        self._move_down_button = QPushButton("↓")
        self._move_top_button = QPushButton("Top")
        self._move_bottom_button = QPushButton("Bottom")

        rule_controls_layout.addWidget(self._add_button)
        rule_controls_layout.addWidget(self._edit_button)
        rule_controls_layout.addWidget(self._delete_button)
        rule_controls_layout.addWidget(self._toggle_status_button)
        rule_controls_layout.addStretch()
        rule_controls_layout.addWidget(self._move_top_button)
        rule_controls_layout.addWidget(self._move_up_button)
        rule_controls_layout.addWidget(self._move_down_button)
        rule_controls_layout.addWidget(self._move_bottom_button)

        table_layout.addWidget(self._rule_controls)

        # Add filter and table widgets to splitter
        self._main_splitter.addWidget(filter_widget)
        self._main_splitter.addWidget(table_widget)

        # Initial splitter proportions (1:3 ratio)
        self._main_splitter.setSizes([100, 300])

        # Add splitter to main layout
        main_layout.addWidget(self._main_splitter)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.setSizeGripEnabled(False)
        main_layout.addWidget(self._status_bar)

    def _connect_signals(self):
        """Connect signals to slots."""
        # Filter signals
        self._category_filter.currentTextChanged.connect(self._on_filter_changed)
        self._status_filter.currentTextChanged.connect(self._on_filter_changed)
        self._search_edit.textChanged.connect(self._on_filter_changed)
        self._reset_filters_button.clicked.connect(self._on_reset_filters)

        # Rule management signals
        self._add_button.clicked.connect(self._on_add_rule)
        self._edit_button.clicked.connect(self._on_edit_rule)
        self._delete_button.clicked.connect(self._on_delete_rule)
        self._toggle_status_button.clicked.connect(self._on_toggle_status)
        self._move_up_button.clicked.connect(self._on_move_rule_up)
        self._move_down_button.clicked.connect(self._on_move_rule_down)
        self._move_top_button.clicked.connect(self._on_move_rule_to_top)
        self._move_bottom_button.clicked.connect(self._on_move_rule_to_bottom)

        # Table signals
        self._rule_table.doubleClicked.connect(self._on_rule_double_clicked)

        # Apply corrections signal
        self._apply_button.clicked.connect(self._on_apply_corrections)

        # Controller signals
        self._controller.rules_changed.connect(self._on_rules_changed)
        self._controller.rule_added.connect(self._on_rule_added)
        self._controller.rule_updated.connect(self._on_rule_updated)
        self._controller.rule_deleted.connect(self._on_rule_deleted)

    def _refresh_rule_table(self):
        """Refresh the rule table with the current rules from the controller."""
        # Get filtered rules
        rules = self._controller.get_rules(
            category=self._current_filter["category"],
            status=self._current_filter["status"],
            search_term=self._current_filter["search"],
        )

        # Clear and prepare table
        self._rule_table.setRowCount(0)
        self._rule_table.setRowCount(len(rules))

        # Fill table with rule data
        for i, rule in enumerate(rules):
            # Order
            order_item = QTableWidgetItem(str(rule.order))
            order_item.setData(Qt.UserRole, i)  # Store index in user role
            self._rule_table.setItem(i, 0, order_item)

            # From
            from_item = QTableWidgetItem(rule.from_value)
            self._rule_table.setItem(i, 1, from_item)

            # To
            to_item = QTableWidgetItem(rule.to_value)
            self._rule_table.setItem(i, 2, to_item)

            # Category
            category_item = QTableWidgetItem(rule.category)
            self._rule_table.setItem(i, 3, category_item)

            # Status
            status_item = QTableWidgetItem(rule.status.capitalize())
            status_item.setForeground(Qt.green if rule.status == "enabled" else Qt.red)
            self._rule_table.setItem(i, 4, status_item)

        # Clear selection and update buttons
        self._rule_table.clearSelection()
        self._update_button_states()
        self._update_status_bar()

    def _update_categories_filter(self):
        """Update the categories filter dropdown with current categories."""
        # Remember current category
        current_category = self._category_filter.currentText()

        # Get all categories from the controller
        categories = self._controller.get_rule_categories()

        # Clear and refill the combo box
        self._category_filter.blockSignals(True)
        self._category_filter.clear()
        self._category_filter.addItem("All Categories")

        for category in sorted(categories):
            self._category_filter.addItem(category)

        # Restore selection or default to All
        if current_category and self._category_filter.findText(current_category) >= 0:
            self._category_filter.setCurrentText(current_category)
        else:
            self._category_filter.setCurrentIndex(0)  # All Categories

        self._category_filter.blockSignals(False)

    def _update_button_states(self):
        """Update the enabled state of buttons based on current selection."""
        has_selection = len(self._rule_table.selectedItems()) > 0

        # Buttons that need a selection
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._toggle_status_button.setEnabled(has_selection)
        self._move_up_button.setEnabled(has_selection)
        self._move_down_button.setEnabled(has_selection)
        self._move_top_button.setEnabled(has_selection)
        self._move_bottom_button.setEnabled(has_selection)

    def _update_status_bar(self):
        """Update the status bar with rule count information."""
        # Get rule counts
        total_rules = self._controller.get_rule_count()
        enabled_rules = self._controller.get_rule_count(status="enabled")

        # Get filtered count
        filtered_count = self._rule_table.rowCount()

        # Update status bar
        if (
            self._current_filter["category"]
            or self._current_filter["status"]
            or self._current_filter["search"]
        ):
            self._status_bar.showMessage(
                f"Showing {filtered_count} of {total_rules} rules ({enabled_rules} enabled)"
            )
        else:
            self._status_bar.showMessage(f"Total rules: {total_rules} ({enabled_rules} enabled)")

    def _get_selected_rule_id(self):
        """Get the ID of the currently selected rule."""
        selected_items = self._rule_table.selectedItems()
        if not selected_items:
            return None

        # Get the row of the first selected item
        row = selected_items[0].row()

        # Get the index stored in the first column's user role
        index_item = self._rule_table.item(row, 0)
        if index_item:
            return index_item.data(Qt.UserRole)

        return None

    def _on_filter_changed(self):
        """Handle filter changes."""
        # Update the filter criteria
        category = self._category_filter.currentText()
        if category == "All Categories":
            category = ""

        status = self._status_filter.currentText().lower()
        if status == "all":
            status = ""

        search = self._search_edit.text()

        # Store the current filter
        self._current_filter = {
            "category": category,
            "status": status,
            "search": search,
        }

        # Refresh the rule table with the new filter
        self._refresh_rule_table()

    def _on_reset_filters(self):
        """Reset all filters to default values."""
        self._category_filter.setCurrentIndex(0)  # All Categories
        self._status_filter.setCurrentIndex(0)  # All
        self._search_edit.clear()

        # Explicitly trigger filter changed to update the table
        self._on_filter_changed()

    def _on_rule_double_clicked(self, index):
        """Handle double-click on rule table item."""
        self._on_edit_rule()

    def _on_add_rule(self):
        """Add a new correction rule."""
        dialog = AddEditRuleDialog(
            validation_service=self._controller.get_validation_service(), parent=self
        )

        if dialog.exec():
            rule = dialog.get_rule()
            rule_id = self._controller.add_rule(rule)
            self.rule_added.emit(rule)
            self._logger.info(f"Added rule: {rule.from_value} -> {rule.to_value}")

    def _on_edit_rule(self):
        """Edit the selected correction rule."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        rule = self._controller.get_rule(rule_id)
        if not rule:
            QMessageBox.warning(self, "Error", "Rule not found.")
            return

        dialog = AddEditRuleDialog(
            validation_service=self._controller.get_validation_service(), parent=self, rule=rule
        )

        if dialog.exec():
            updated_rule = dialog.get_rule()
            self._controller.update_rule(rule_id, updated_rule)
            self.rule_edited.emit(updated_rule)
            self._logger.info(f"Updated rule: {updated_rule.from_value} -> {updated_rule.to_value}")

    def _on_delete_rule(self):
        """Delete the selected correction rule."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this rule?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            self._controller.delete_rule(rule_id)
            self.rule_deleted.emit(rule_id)
            self._logger.info(f"Deleted rule {rule_id}")

    def _on_toggle_status(self):
        """Toggle the status of the selected rule."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.toggle_rule_status(rule_id)
        self._logger.info(f"Toggled rule {rule_id} status")

    def _on_move_rule_up(self):
        """Move the selected rule up in the order."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.reorder_rule(rule_id, rule_id - 1)
        self._logger.info(f"Moved rule {rule_id} up")

    def _on_move_rule_down(self):
        """Move the selected rule down in the order."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.reorder_rule(rule_id, rule_id + 1)
        self._logger.info(f"Moved rule {rule_id} down")

    def _on_move_rule_to_top(self):
        """Move the selected rule to the top of its category."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.move_rule_to_top(rule_id)
        self._logger.info(f"Moved rule {rule_id} to top")

    def _on_move_rule_to_bottom(self):
        """Move the selected rule to the bottom of its category."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.move_rule_to_bottom(rule_id)
        self._logger.info(f"Moved rule {rule_id} to bottom")

    def _on_apply_corrections(self):
        """Apply corrections to the data."""
        only_invalid = self._correct_invalid_only_checkbox.isChecked()
        recursive = self._recursive_checkbox.isChecked()

        self.apply_corrections_requested.emit(recursive, only_invalid)
        self._logger.info(
            f"Apply corrections requested (recursive={recursive}, only_invalid={only_invalid})"
        )

    def _on_action_clicked(self, action_id):
        """Handle action button clicks from toolbar or menu."""
        if action_id == "apply":
            only_invalid = self._correct_invalid_only_checkbox.isChecked()
            self._controller.apply_corrections(only_invalid=only_invalid)
        elif action_id == "batch":
            self._show_batch_correction_dialog()
        elif action_id == "import":
            self._show_import_export_dialog(export_mode=False)
        elif action_id == "export":
            self._show_import_export_dialog(export_mode=True)

    def _show_batch_correction_dialog(self):
        """Show the batch correction dialog."""
        selected_cells = []  # This would come from the data view

        dialog = BatchCorrectionDialog(
            selected_cells=selected_cells,
            validation_service=self._controller.get_validation_service(),
            parent=self,
        )

        if dialog.exec():
            rules = dialog.get_rules()
            for rule in rules:
                self._controller.add_rule(rule)
            self._logger.info(f"Added {len(rules)} rules from batch correction")

    def _show_import_export_dialog(self, export_mode=False):
        """Show the import/export dialog."""
        dialog = ImportExportDialog(parent=self, export_mode=export_mode)

        if dialog.exec():
            file_path = dialog.get_file_path()
            if export_mode:
                only_enabled = dialog.get_only_enabled()
                self._controller.export_rules(file_path, only_enabled)
                self._logger.info(f"Exported rules to {file_path}")
            else:
                replace_existing = dialog.get_replace_existing()
                self._controller.import_rules(file_path, replace_existing)
                self._logger.info(f"Imported rules from {file_path}")

    @Slot(object)
    def _on_rules_changed(self):
        """Handle rules changed notification."""
        self._refresh_rule_table()
        self._update_categories_filter()

    @Slot(object)
    def _on_rule_added(self, rule):
        """Handle rule added notification."""
        self._refresh_rule_table()
        self._update_categories_filter()

    @Slot(object)
    def _on_rule_updated(self, rule):
        """Handle rule updated notification."""
        self._refresh_rule_table()

    @Slot(int)
    def _on_rule_deleted(self, rule_id):
        """Handle rule deleted notification."""
        self._refresh_rule_table()
        self._update_categories_filter()
