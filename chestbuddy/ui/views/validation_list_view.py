"""
validation_list_view.py

Description: View for displaying and managing a single validation list
"""

import logging
from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer

from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.resources.style import Colors

logger = logging.getLogger(__name__)


class ValidationListView(QWidget):
    """
    View for displaying and managing a single validation list.

    Attributes:
        status_changed (Signal): Signal emitted when list status changes
    """

    status_changed = Signal(str)

    def __init__(self, model: ValidationListModel, parent: Optional[QWidget] = None):
        """
        Initialize the validation list view.

        Args:
            model (ValidationListModel): Model containing validation list data
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self._model = model
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)  # 300ms debounce

        # Set properties for proper styling
        self.setProperty("lightContentView", True)
        self.setProperty("container", True)

        self._setup_ui()
        self._connect_signals()
        self._populate_list()
        logger.info(f"Initialized ValidationListView with {self._model.count()} entries")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Set background color for the entire widget
        self.setStyleSheet(f"background-color: {Colors.DARK_CONTENT_BG};")
        self.setAutoFillBackground(True)  # Ensure widget has proper background

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search...")
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {Colors.TEXT_LIGHT};
            }}
            QLineEdit:focus {{
                border-color: {Colors.SECONDARY};
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
        """)
        self._search_input.setAutoFillBackground(True)  # Ensure search input has proper background
        layout.addWidget(self._search_input)

        # List widget with improved styling for consistent colors and better item spacing
        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px;
                color: {Colors.TEXT_LIGHT};
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {Colors.DARK_BORDER};
                margin-bottom: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                border-left: 3px solid {Colors.SECONDARY};
                color: {Colors.TEXT_LIGHT};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            QScrollBar:vertical {{
                background: {Colors.PRIMARY_DARK};
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BG_MEDIUM};
                min-height: 30px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.SECONDARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: {Colors.PRIMARY_DARK};
            }}
        """)
        self._list_widget.setAutoFillBackground(True)  # Ensure list widget has proper background

        # Ensure all QListWidgetItems will render with proper background
        self._list_widget.viewport().setAutoFillBackground(True)

        layout.addWidget(self._list_widget)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        # Model signals
        self._model.entries_changed.connect(self._on_entries_changed)

        # Search input signals
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_timer.timeout.connect(self._perform_search)

        # List widget signals
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self._list_widget.itemDoubleClicked.connect(self._edit_entry)

    def _populate_list(self, filter_text: str = "") -> None:
        """
        Populate the list widget with entries.

        Args:
            filter_text (str, optional): Text to filter entries by. Defaults to "".
        """
        self._list_widget.clear()

        # Get entries (filtered if search text is provided)
        entries = (
            self._model.find_matching_entries(filter_text)
            if filter_text
            else self._model.get_entries()
        )

        # Add entries to list widget
        for entry in entries:
            item = QListWidgetItem(entry)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self._list_widget.addItem(item)

        # Update status
        self.status_changed.emit("List populated")
        logger.debug(f"Populated list with {len(entries)} entries")

    def _on_entries_changed(self) -> None:
        """Handle changes to the model's entries."""
        self._populate_list(self._search_input.text())

    def _on_search_text_changed(self, text: str) -> None:
        """
        Handle changes to the search input text.

        Args:
            text (str): New search text
        """
        # Reset and start the timer
        self._search_timer.stop()
        self._search_timer.start()

    def _perform_search(self) -> None:
        """Perform the search operation."""
        search_text = self._search_input.text()
        self._populate_list(search_text)

    def _show_context_menu(self, position) -> None:
        """
        Show the context menu for list items.

        Args:
            position: Position where to show the menu
        """
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 8px;
                color: {Colors.TEXT_LIGHT};
            }}
            QMenu::item:selected {{
                background-color: {Colors.PRIMARY_LIGHT};
                color: {Colors.SECONDARY};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Colors.DARK_BORDER};
                margin: 4px 8px;
            }}
        """)

        # Get selected items
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return

        # Add actions
        edit_action = menu.addAction("Edit")
        menu.addSeparator()
        remove_action = menu.addAction("Remove")

        # Show menu and handle action
        action = menu.exec(self._list_widget.mapToGlobal(position))
        if action == edit_action:
            self._edit_entry(selected_items[0])
        elif action == remove_action:
            self._remove_entries(selected_items)

    def _edit_entry(self, item: QListWidgetItem) -> None:
        """
        Edit a list entry.

        Args:
            item (QListWidgetItem): Item to edit
        """
        old_text = item.text()
        new_text, ok = QInputDialog.getText(self, "Edit Entry", "Enter new value:", text=old_text)

        if ok and new_text and new_text != old_text:
            # Remove old entry
            self._model.remove_entry(old_text)

            # Try to add new entry
            if not self._model.add_entry(new_text):
                # If add fails (e.g., duplicate), restore old entry
                self._model.add_entry(old_text)
                QMessageBox.warning(
                    self, "Edit Failed", f"The entry '{new_text}' already exists in the list."
                )

    def _remove_entries(self, items: List[QListWidgetItem]) -> None:
        """
        Remove entries from the list.

        Args:
            items (List[QListWidgetItem]): Items to remove
        """
        if not items:
            return

        # Confirm deletion
        msg = "Remove selected entries?" if len(items) > 1 else "Remove selected entry?"
        if QMessageBox.question(self, "Confirm Remove", msg) == QMessageBox.StandardButton.Yes:
            for item in items:
                self._model.remove_entry(item.text())

    def model(self) -> ValidationListModel:
        """
        Get the validation list model.

        Returns:
            ValidationListModel: The model managing the validation list
        """
        return self._model

    def add_entry(self) -> None:
        """Add a new entry to the list."""
        text, ok = QInputDialog.getText(self, "Add Entry", "Enter new entry:")
        if ok and text:
            if self._model.add_entry(text):
                self.status_changed.emit("Entry added successfully")
            else:
                QMessageBox.warning(
                    self, "Add Failed", f"The entry '{text}' already exists in the list."
                )

    def remove_selected_entries(self) -> None:
        """Remove selected entries from the list."""
        selected_items = self._list_widget.selectedItems()
        if selected_items:
            self._remove_entries(selected_items)
        else:
            QMessageBox.information(self, "Remove", "No items selected")

    def import_entries(self) -> None:
        """Import entries from a file, replacing all existing entries."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Entries", "", "Text Files (*.txt)")
        if file_path:
            # Ask for confirmation since this will replace all existing entries
            result = QMessageBox.question(
                self,
                "Confirm Import",
                "This will replace ALL existing entries with the imported ones. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if result == QMessageBox.StandardButton.Yes:
                success, _ = self._model.import_from_file(Path(file_path))
                if success:
                    self.status_changed.emit(
                        f"Imported entries successfully, replacing all existing entries"
                    )
                else:
                    QMessageBox.critical(self, "Import Failed", "Failed to import entries")

    def export_entries(self) -> None:
        """Export entries to a file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Entries", "", "Text Files (*.txt)")
        if file_path:
            if self._model.export_to_file(Path(file_path)):
                self.status_changed.emit(f"Exported entries successfully")
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to export entries")

    def refresh(self) -> None:
        """Refresh the list view."""
        self._model.refresh()
        self._populate_list(self._search_input.text())
