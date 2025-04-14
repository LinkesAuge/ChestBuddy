"""
Correction Rule View.

This module implements the main UI view for managing correction rules in the ChestBuddy application.
It provides a UI for viewing, filtering, and managing correction rules.
"""

from typing import Optional, List, Dict, Any, Tuple, Callable
import logging

from PySide6.QtCore import Qt, Signal, Slot, QPoint
from PySide6.QtGui import QAction, QIcon
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
    QApplication,
    QMenu,
    QFrame,
    QSizePolicy,
)

from chestbuddy.core.controllers import CorrectionController
from chestbuddy.core.models.correction_rule import CorrectionRule
from chestbuddy.ui.dialogs import AddEditRuleDialog
from chestbuddy.ui.dialogs.batch_correction_dialog import BatchCorrectionDialog
from chestbuddy.ui.dialogs.import_export_dialog import ImportExportDialog
from chestbuddy.ui.models.correction_rule_table_model import CorrectionRuleTableModel
from chestbuddy.ui.utils import IconProvider
from chestbuddy.utils.config import ConfigManager
from chestbuddy.ui.views.base_view import BaseView

# Set up logger
logger = logging.getLogger(__name__)


class CorrectionRuleView(BaseView):
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
        preview_rule_requested (CorrectionRule): Signal emitted when a rule is requested for preview.
    """

    # Signals for view-controller communication
    apply_corrections_requested = Signal(bool, bool)
    rule_added = Signal(object)
    rule_edited = Signal(object)
    rule_deleted = Signal(int)
    preview_rule_requested = Signal(CorrectionRule)

    def __init__(self, controller, parent=None):
        """
        Initialize the CorrectionRuleView.

        Args:
            controller: The correction controller instance
            parent: The parent widget
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._controller = controller

        # Flag to prevent multiple delete operations
        self._deletion_in_progress = False

        # Initialize attributes needed for testing
        self._import_button = None
        self._export_button = None

        # Initialize UI components
        self._rule_table = None
        self._filter_controls = None
        self._rule_controls = None
        self._settings_panel = None
        self._main_splitter = None
        self._status_bar = None

        # Filter state tracking
        self._current_filter = {
            "category": "",
            "status": "",
            "search": "",
        }

        # Set up UI
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

        # Header with title and actions
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # Title label
        title_label = QLabel("Correction Rules")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Import button
        self._import_button = QPushButton("Import Rules")
        self._import_button.clicked.connect(lambda: self._on_action_clicked("import"))
        header_layout.addWidget(self._import_button)

        # Export button
        self._export_button = QPushButton("Export Rules")
        self._export_button.clicked.connect(lambda: self._on_action_clicked("export"))
        header_layout.addWidget(self._export_button)

        main_layout.addWidget(header_widget)

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

        # Category filter - named exactly as expected by tests
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self._category_filter = QComboBox()  # Name expected by tests
        self._category_filter.addItem("All Categories")
        category_layout.addWidget(self._category_filter)
        filter_group_layout.addLayout(category_layout)

        # Status filter - named exactly as expected by tests
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()  # Name expected by tests
        self._status_filter.addItem("All")
        self._status_filter.addItem("Enabled")
        self._status_filter.addItem("Disabled")
        status_layout.addWidget(self._status_filter)
        filter_group_layout.addLayout(status_layout)

        # Search filter - named exactly as expected by tests
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()  # Name expected by tests
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

        # Set up columns - exactly match the order and names expected by tests
        self._rule_table.setColumnCount(4)
        headers = ["From", "To", "Category", "Status"]
        self._rule_table.setHorizontalHeaderLabels(headers)
        header = self._rule_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status

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

        # Ensure buttons are initially disabled as expected by tests
        self._edit_button.setEnabled(False)
        self._delete_button.setEnabled(False)
        self._toggle_status_button.setEnabled(False)
        self._move_up_button.setEnabled(False)
        self._move_down_button.setEnabled(False)
        self._move_top_button.setEnabled(False)
        self._move_bottom_button.setEnabled(False)

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
        self._rule_table.itemSelectionChanged.connect(self._update_button_states)

        # Context menu
        self._rule_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._rule_table.customContextMenuRequested.connect(self._show_context_menu)

        # Apply corrections signal
        self._apply_button.clicked.connect(self._on_apply_corrections)

    def _refresh_rule_table(self):
        """Refresh the rule table with current rules."""
        # Get filtered rules
        category = self._current_filter["category"]
        status = self._current_filter["status"]
        search = self._current_filter["search"]

        # Get the rules from the controller with filter parameters
        # We need the full unfiltered list first to get correct original indices
        all_rules = self._controller.get_rules()
        rule_to_index = {rule: idx for idx, rule in enumerate(all_rules)}

        filtered_rules = self._controller.get_rules(
            category=category, status=status, search_term=search
        )

        # Clear table but preserve headers
        self._rule_table.setRowCount(0)
        self._rule_table.setColumnCount(4)  # Ensure columns are set
        headers = ["From", "To", "Category", "Status"]
        self._rule_table.setHorizontalHeaderLabels(headers)

        # Populate table
        for i, rule in enumerate(filtered_rules):
            row = self._rule_table.rowCount()
            self._rule_table.insertRow(row)

            # Create items
            item_from = QTableWidgetItem(rule.from_value)
            item_to = QTableWidgetItem(rule.to_value)
            item_category = QTableWidgetItem(rule.category)
            item_status = QTableWidgetItem(rule.status)

            # Find the rule's original index in the full list
            # We need a reliable way to map the filtered rule back to the original list
            # Using the rule object itself as key assumes __hash__ and __eq__ are defined correctly
            original_index = rule_to_index.get(
                rule, -1
            )  # Default to -1 if not found (shouldn't happen)
            if original_index == -1:
                logger.warning(f"Could not find original index for rule: {rule}")
                # Fallback: Try matching based on content? This is less reliable.
                # For now, we'll store -1, _get_selected_rule_id should handle None return.

            # Store the original index in UserRole for *each* item in the row
            item_from.setData(Qt.UserRole, original_index)
            item_to.setData(Qt.UserRole, original_index)
            item_category.setData(Qt.UserRole, original_index)
            item_status.setData(Qt.UserRole, original_index)

            # Add items to the table
            self._rule_table.setItem(row, 0, item_from)
            self._rule_table.setItem(row, 1, item_to)
            self._rule_table.setItem(row, 2, item_category)
            self._rule_table.setItem(row, 3, item_status)

        # Restore column widths if needed (or set initially)
        header = self._rule_table.horizontalHeader()
        if not header.isSortIndicatorShown():  # Avoid resetting size if user sorted
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(
                3, QHeaderView.ResizeMode.ResizeToContents
            )  # Status column size

        # Update button states after refreshing
        self._update_button_states()

        # Update status bar with the count of *all* rules
        self._update_status_bar(all_rules)

    def _get_selected_rule_id(self) -> Optional[int]:
        """Get the ID (original index in the full list) of the selected rule."""
        current_row = self._rule_table.currentRow()  # Use currentRow for single selection
        if current_row < 0:
            # Check selectedItems as a fallback, useful if selection mode changes
            selected_items = self._rule_table.selectedItems()
            if not selected_items:
                logger.debug("_get_selected_rule_id: No selection.")
                return None
            # Use the row of the first selected item
            current_row = selected_items[0].row()
            logger.debug(f"_get_selected_rule_id: Using selectedItems[0].row() = {current_row}")
        else:
            logger.debug(f"_get_selected_rule_id: Using currentRow() = {current_row}")

        # Get the item from the *first column* of the selected row
        id_item = self._rule_table.item(current_row, 0)
        if not id_item:
            logger.warning(f"_get_selected_rule_id: No item found at row {current_row}, col 0.")
            return None

        id_data = id_item.data(Qt.UserRole)
        logger.debug(
            f"_get_selected_rule_id: Data from item({current_row}, 0) UserRole: {id_data} (Type: {type(id_data)})"
        )

        if id_data is not None and isinstance(id_data, int) and id_data >= 0:
            try:
                return int(id_data)
            except (ValueError, TypeError) as e:
                logger.error(f"Could not convert rule ID from item data: {id_data}. Error: {e}")
                return None
        logger.warning(
            f"Selected item ({current_row}, 0) does not contain valid rule ID in UserRole data. Data: {id_data}"
        )
        return None

    def _update_categories_filter(self):
        """Update the category filter with available categories."""
        # Save current selection
        current_category = self._category_filter.currentText()

        # Clear and repopulate
        self._category_filter.clear()
        self._category_filter.addItem("All Categories")

        # Get unique categories from rules
        categories = set()
        rules = self._controller.get_rules()
        for rule in rules:
            if rule.category:
                categories.add(rule.category)

        # Add sorted categories
        for category in sorted(categories):
            self._category_filter.addItem(category)

        # Restore selection if possible
        index = self._category_filter.findText(current_category)
        if index >= 0:
            self._category_filter.setCurrentIndex(index)

    def _update_status_bar(self, rules=None):
        """
        Update the status bar with rule counts.

        Args:
            rules: Optional list of rules to use. If None, fetches rules from controller.
        """
        # Get rules from controller if not provided
        if rules is None:
            rules = self._controller.get_rules()

        total_rules = len(rules)
        enabled_rules = sum(1 for rule in rules if rule.status == "enabled")
        disabled_rules = total_rules - enabled_rules

        self._status_bar.showMessage(
            f"Total rules: {total_rules} | Enabled: {enabled_rules} | Disabled: {disabled_rules}"
        )

    def _update_button_states(self):
        """Update button states based on selection."""
        has_selection = len(self._rule_table.selectedItems()) > 0

        # Update all buttons that require a selection
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._toggle_status_button.setEnabled(has_selection)
        self._move_up_button.setEnabled(has_selection)
        self._move_down_button.setEnabled(has_selection)
        self._move_top_button.setEnabled(has_selection)
        self._move_bottom_button.setEnabled(has_selection)

    def _on_filter_changed(self):
        """Handle filter changes."""
        # Update filter values
        category = self._category_filter.currentText()
        if category == "All Categories":
            category = ""

        status = self._status_filter.currentText()
        if status == "All":
            status = ""

        search = self._search_edit.text()

        # Update current filter
        self._current_filter["category"] = category
        self._current_filter["status"] = status
        self._current_filter["search"] = search

        # Refresh the table with the new filter
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
            self._refresh_rule_table()
            self._update_categories_filter()

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
            self._refresh_rule_table()
            self._update_categories_filter()

    def _on_delete_rule(self):
        """Delete the selected correction rule."""
        # Prevent multiple delete operations from a single click
        if self._deletion_in_progress:
            return

        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        rule = self._controller.get_rule(rule_id)
        if not rule:
            QMessageBox.warning(self, "Error", "Rule not found.")
            return

        # Confirm deletion
        response = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the rule: {rule.from_value} -> {rule.to_value}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if response == QMessageBox.Yes:
            try:
                # Set flag to prevent multiple deletions
                self._deletion_in_progress = True

                # Perform deletion directly on the controller
                success = self._controller.delete_rule(rule_id)
                if success:
                    self.rule_deleted.emit(rule_id)
                    self._logger.info(f"Deleted rule: {rule.from_value} -> {rule.to_value}")
                    # Refresh the table to ensure indices are updated correctly
                    self._refresh_rule_table()
                    self._update_categories_filter()
            finally:
                # Always reset the flag when done
                self._deletion_in_progress = False

    def _on_toggle_status(self):
        """Toggle the status of the selected rule."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.toggle_rule_status(rule_id)
        self._logger.info(f"Toggled status of rule {rule_id}")
        self._refresh_rule_table()

    def _on_move_rule_up(self):
        """Move the selected rule up in its category."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.reorder_rule(rule_id, -1)
        self._logger.info(f"Moved rule {rule_id} up")
        self._refresh_rule_table()

    def _on_move_rule_down(self):
        """Move the selected rule down in its category."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.reorder_rule(rule_id, 1)
        self._logger.info(f"Moved rule {rule_id} down")
        self._refresh_rule_table()

    def _on_move_rule_to_top(self):
        """Move the selected rule to the top of its category."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.move_rule_to_top(rule_id)
        self._logger.info(f"Moved rule {rule_id} to top")
        self._refresh_rule_table()

    def _on_move_rule_to_bottom(self):
        """Move the selected rule to the bottom of its category."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        self._controller.move_rule_to_bottom(rule_id)
        self._logger.info(f"Moved rule {rule_id} to bottom")
        self._refresh_rule_table()

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
        self._logger.debug(f"Action clicked: {action_id}")

        if action_id == "apply":
            only_invalid = self._correct_invalid_only_checkbox.isChecked()
            recursive = self._recursive_checkbox.isChecked()
            # Emit signal for external connections
            self.apply_corrections_requested.emit(recursive, only_invalid)
            # Also call the controller directly for test compatibility
            self._controller.apply_corrections(only_invalid=only_invalid)
        elif action_id == "batch":
            self._show_batch_correction_dialog()
        elif action_id == "import":
            self._logger.info("Import action triggered")
            self._show_import_export_dialog(export_mode=False)
        elif action_id == "export":
            self._logger.info("Export action triggered")
            self._show_import_export_dialog(export_mode=True)

    def _show_batch_correction_dialog(self):
        """Show the batch correction dialog."""
        # This would typically come from the data view
        # For now, we'll use an empty list since we're not integrating with the data view here
        selected_cells = []

        # Get the selected cells from the application's DataView
        # This is a simplified approach - the actual implementation would depend
        # on how the DataView is accessed in the application
        app = QApplication.instance()
        if hasattr(app, "get_main_window"):
            main_window = app.get_main_window()
            if main_window and hasattr(main_window, "get_active_view"):
                active_view = main_window.get_active_view()
                if active_view and hasattr(active_view, "_get_selected_cells"):
                    selected_cells = active_view._get_selected_cells()
                    self._logger.debug(f"Got {len(selected_cells)} selected cells from data view")

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
            self._refresh_rule_table()
            self._update_categories_filter()

            # Apply the rules to selected cells
            if selected_cells and hasattr(self._controller, "apply_rules_to_selection"):
                self._controller.apply_rules_to_selection(selected_cells)
                self._logger.info("Applied correction rules to selected cells")

    def _show_import_export_dialog(self, export_mode=False):
        """Show the import/export dialog."""
        dialog = ImportExportDialog(mode="export" if export_mode else "import", parent=self)

        if dialog.exec():
            if export_mode:
                file_path = dialog.get_file_path()
                file_format = dialog.get_format().lower()
                if file_path:
                    self._controller.export_rules(file_path)
                    self._logger.info(f"Rules exported successfully to {file_path}")
            else:
                file_path = dialog.get_file_path()
                file_format = dialog.get_format().lower()
                if file_path:
                    self._controller.import_rules(file_path)
                    self._logger.info(f"Rules imported successfully from {file_path}")
                    self._refresh_rule_table()
                    self._update_categories_filter()

    def _show_context_menu(self, position: QPoint, menu: Optional[QMenu] = None):
        """Show context menu for the rule table."""
        if not menu:
            menu = QMenu(self)

        # Step 1: Get the ID of the selected rule
        selected_rule_id = self._get_selected_rule_id()
        selected_rule = None

        # Step 2: If an ID was found, fetch the full rule object from the controller
        if selected_rule_id is not None:
            try:
                selected_rule = self._controller.get_rule(selected_rule_id)
                if not selected_rule:
                    logger.warning(
                        f"Controller returned None for rule ID {selected_rule_id} when building context menu."
                    )
            except Exception as e:
                logger.error(
                    f"Error calling controller.get_rule({selected_rule_id}) in _show_context_menu: {e}",
                    exc_info=True,
                )
                selected_rule = None  # Ensure rule is None if controller fails

        selected_items = self._rule_table.selectedItems()
        num_selected_rows = len(set(item.row() for item in selected_items))

        # Step 3: Build the menu based on whether a rule object was successfully fetched
        if selected_rule:
            # Actions requiring a valid rule object
            edit_action = QAction(IconProvider.get_icon("edit"), "Edit Rule", self)
            edit_action.triggered.connect(self._on_edit_rule)
            menu.addAction(edit_action)

            delete_action = QAction(IconProvider.get_icon("delete"), "Delete Rule", self)
            delete_action.triggered.connect(self._on_delete_rule)
            menu.addAction(delete_action)

            toggle_action = QAction(
                IconProvider.get_icon(
                    "toggle_on" if selected_rule.status == "disabled" else "toggle_off"
                ),
                f"Toggle Status (currently {selected_rule.status})",
                self,
            )
            toggle_action.triggered.connect(self._on_toggle_status)
            menu.addAction(toggle_action)

            menu.addSeparator()

            # Preview Action - enabled only if exactly one row is selected
            preview_action = QAction(
                IconProvider.get_icon("preview", fallback="system-search"), "Preview Rule", self
            )
            preview_action.setEnabled(num_selected_rows == 1)
            preview_action.triggered.connect(self._on_preview_rule)
            menu.addAction(preview_action)

            # Move actions - only relevant if there's more than one rule total
            if self._rule_table.rowCount() > 1:
                menu.addSeparator()
                move_top_action = QAction(
                    IconProvider.get_icon("move_top", fallback="go-top"), "Move to Top", self
                )
                move_top_action.setEnabled(selected_rule_id > 0)  # Can't move top if already at top
                move_top_action.triggered.connect(self._on_move_rule_to_top)
                menu.addAction(move_top_action)

                move_up_action = QAction(
                    IconProvider.get_icon("arrow_up", fallback="go-up"), "Move Up", self
                )
                move_up_action.setEnabled(selected_rule_id > 0)  # Can't move up if already at top
                move_up_action.triggered.connect(self._on_move_rule_up)
                menu.addAction(move_up_action)

                move_down_action = QAction(
                    IconProvider.get_icon("arrow_down", fallback="go-down"), "Move Down", self
                )
                move_down_action.setEnabled(
                    selected_rule_id < self._controller.get_rule_count() - 1
                )  # Can't move down if already at bottom
                move_down_action.triggered.connect(self._on_move_rule_down)
                menu.addAction(move_down_action)

                move_bottom_action = QAction(
                    IconProvider.get_icon("move_bottom", fallback="go-bottom"),
                    "Move to Bottom",
                    self,
                )
                move_bottom_action.setEnabled(
                    selected_rule_id < self._controller.get_rule_count() - 1
                )  # Can't move bottom if already at bottom
                move_bottom_action.triggered.connect(self._on_move_rule_to_bottom)
                menu.addAction(move_bottom_action)

        # Always show the menu if any actions were added
        if menu.actions():
            # Ensure the position is valid within the viewport
            viewport_pos = self._rule_table.viewport().mapFromGlobal(position)
            menu.exec(self._rule_table.viewport().mapToGlobal(viewport_pos))
        else:
            logger.debug("Context menu not shown because no actions were applicable.")

    @Slot()
    def _on_preview_rule(self):
        """Handle the Preview Rule action trigger."""
        logger.debug(f"_on_preview_rule called. Controller instance: {id(self._controller)}")
        # Correctly get the selected rule ID first
        selected_rule_id = self._get_selected_rule_id()
        logger.debug(f"_on_preview_rule: Got selected ID: {selected_rule_id}")
        selected_rule = None
        if selected_rule_id is not None:
            # Use the controller to get the rule object by ID
            try:
                selected_rule = self._controller.get_rule(selected_rule_id)
                logger.debug(
                    f"_on_preview_rule: Controller get_rule({selected_rule_id}) returned: {repr(selected_rule)}"
                )
            except Exception as e:
                logger.error(
                    f"Error calling controller.get_rule({selected_rule_id}): {e}", exc_info=True
                )
                selected_rule = None

        if selected_rule:
            # Log the actual rule details for clarity
            logger.info(f"Preview requested via context menu for rule: {repr(selected_rule)}")
            self.preview_rule_requested.emit(selected_rule)
        else:
            logger.warning(
                f"Preview rule action triggered but no rule selected or found (ID: {selected_rule_id})."
            )

    def _on_apply_single_rule(self):
        """Apply a single selected rule."""
        rule_id = self._get_selected_rule_id()
        if rule_id is None:
            return

        rule = self._controller.get_rule(rule_id)
        if not rule:
            QMessageBox.warning(self, "Error", "Rule not found.")
            return

        # Apply this rule only
        only_invalid = self._correct_invalid_only_checkbox.isChecked()
        success = self._controller.apply_single_rule(rule, only_invalid=only_invalid)

        if success:
            self._logger.info(f"Applied single rule: {rule.from_value} -> {rule.to_value}")
            # Refresh the view to reflect any changes
            self._refresh_rule_table()
        else:
            QMessageBox.warning(self, "Error", "Failed to apply the rule.")
