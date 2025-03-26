"""
validation_list_view.py

Description: View for displaying and editing validation lists
"""

import logging
from typing import Optional, List, Callable

from PySide6.QtCore import Qt, Slot, Signal, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QMenu,
    QMessageBox,
)
from PySide6.QtGui import QIcon, QAction

from chestbuddy.core.models.validation_list_model import ValidationListModel

logger = logging.getLogger(__name__)


class ValidationListView(QWidget):
    """
    View for displaying and editing validation lists.

    This widget allows viewing, searching, and modifying validation lists
    for players, chest types, and sources.

    Attributes:
        status_changed (Signal): Signal emitted when the validation list status changes
    """

    status_changed = Signal(str, int)  # category, count

    def __init__(
        self, title: str, validation_model: ValidationListModel, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the ValidationListView.

        Args:
            title (str): Title for the validation list
            validation_model (ValidationListModel): Model containing validation entries
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.title = title
        self.validation_model = validation_model

        # Connect to model signals
        self.validation_model.entries_changed.connect(self._on_entries_changed)

        # Setup UI
        self._setup_ui()

        # Load initial data
        self._load_entries()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title label
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self._on_search_text_changed)

        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # List widget for entries
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

        # Add/Remove buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.remove_button.setEnabled(False)
        button_layout.addWidget(self.remove_button)

        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("0 entries")
        layout.addWidget(self.status_label)

        # Connect list selection to enable/disable remove button
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_entries(self) -> None:
        """Load entries from the validation model."""
        self.list_widget.clear()

        entries = self.validation_model.get_entries()
        for entry in entries:
            item = QListWidgetItem(entry)
            self.list_widget.addItem(item)

        # Update status
        self._update_status()

    def _filter_entries(self, query: str) -> None:
        """
        Filter the list entries based on search text.

        Args:
            query (str): Search query text
        """
        self.list_widget.clear()

        entries = self.validation_model.find_matching_entries(query)
        for entry in entries:
            item = QListWidgetItem(entry)
            self.list_widget.addItem(item)

        # Update status to show filtered count
        filtered_text = f" (filtered from {self.validation_model.count()})" if query else ""
        self.status_label.setText(f"{len(entries)} entries{filtered_text}")

    @Slot()
    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        # Use the search text as the new entry if it's not empty
        text = self.search_input.text().strip()

        if not text:
            # If search is empty, show input dialog
            from PySide6.QtWidgets import QInputDialog

            text, ok = QInputDialog.getText(
                self, f"Add {self.title} Entry", f"Enter a new {self.title.lower()} entry:"
            )

            if not ok or not text.strip():
                return

        # Add the entry
        success = self.validation_model.add_entry(text)

        if success:
            # Clear search to show updated list
            self.search_input.clear()
            logger.info(f"Added entry '{text}' to {self.title}")
        else:
            QMessageBox.information(
                self,
                "Duplicate Entry",
                f"The entry '{text}' already exists in the {self.title} list.",
            )

    @Slot()
    def _on_remove_clicked(self) -> None:
        """Handle remove button click."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        # Confirm deletion
        if len(selected_items) == 1:
            message = f"Are you sure you want to remove '{selected_items[0].text()}'?"
        else:
            message = f"Are you sure you want to remove {len(selected_items)} entries?"

        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                self.validation_model.remove_entry(item.text())

            # Clear selection
            self.list_widget.clearSelection()

            # Update the filter if search is active
            if self.search_input.text():
                self._on_search_text_changed(self.search_input.text())

    @Slot(str)
    def _on_search_text_changed(self, text: str) -> None:
        """
        Handle search text changes.

        Args:
            text (str): Current search text
        """
        self._filter_entries(text)

    @Slot()
    def _on_selection_changed(self) -> None:
        """Handle list selection changes."""
        self.remove_button.setEnabled(len(self.list_widget.selectedItems()) > 0)

    @Slot()
    def _on_entries_changed(self) -> None:
        """Handle changes in the validation model."""
        # Reload the entries
        current_query = self.search_input.text()
        if current_query:
            self._filter_entries(current_query)
        else:
            self._load_entries()

    def _update_status(self) -> None:
        """Update the status label and emit status changed signal."""
        count = self.validation_model.count()
        self.status_label.setText(f"{count} entries")

        # Emit signal with category and count
        self.status_changed.emit(self.title, count)

    @Slot(object)
    def _show_context_menu(self, position) -> None:
        """
        Show context menu for list items.

        Args:
            position: Position where to show the menu
        """
        menu = QMenu()

        add_action = QAction("Add Entry", self)
        add_action.triggered.connect(self._on_add_clicked)
        menu.addAction(add_action)

        # Only enable actions that require selection if items are selected
        if self.list_widget.selectedItems():
            remove_action = QAction("Remove Selected", self)
            remove_action.triggered.connect(self._on_remove_clicked)
            menu.addAction(remove_action)

        menu.exec(self.list_widget.mapToGlobal(position))

    def refresh(self) -> None:
        """Refresh the validation list view."""
        self.validation_model.refresh()
        self._load_entries()
