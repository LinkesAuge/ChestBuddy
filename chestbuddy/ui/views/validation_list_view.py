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
    QDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer, QObject

from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.views.confirmation_dialog import ConfirmationDialog
from chestbuddy.ui.views.multi_entry_dialog import MultiEntryDialog

logger = logging.getLogger(__name__)


class ValidationListView(QWidget):
    """
    View for displaying and managing a single validation list.

    Attributes:
        status_changed (Signal): Signal emitted when list status changes
    """

    status_changed = Signal(str)

    def __init__(
        self, model: ValidationListModel, name: str = "", parent: Optional[QWidget] = None
    ):
        """
        Initialize the validation list view.

        Args:
            model (ValidationListModel): Model containing validation list data
            name (str, optional): Name of the validation list. If not provided, it will be extracted from file path
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self._model = model

        # Extract name from file path if not provided
        if name:
            self._name = name
        else:
            # Extract list name from file path (remove .txt and use as name)
            file_name = Path(model.file_path).stem
            self._name = file_name.replace("_", " ").title()

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)  # 300ms debounce

        # Set properties for proper styling
        self.setProperty("lightContentView", True)
        self.setProperty("container", True)

        self._setup_ui()
        self._connect_signals()
        self._populate_list()
        logger.info(
            f"Initialized ValidationListView '{self._name}' with {self._model.count()} entries"
        )

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Set background color for the entire widget
        self.setStyleSheet(f"background-color: {Colors.DARK_CONTENT_BG};")
        self.setAutoFillBackground(True)  # Ensure widget has proper background

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # List widget with improved styling for consistent colors and better item spacing
        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # Enable multiple selection using Ctrl and Shift keys
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
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

        # Search input - moved to be after the list widget
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

        # Create a copy of the entries to remove to avoid issues with items being deleted
        entries_to_remove = [item.text() for item in items]

        entry_text = "\n".join(entries_to_remove[:10])
        if len(entries_to_remove) > 10:
            entry_text += f"\n... and {len(entries_to_remove) - 10} more"

        dialog = ConfirmationDialog(
            self,
            title=f"Remove {self._name} Entries",
            message=f"Are you sure you want to remove these entries?\n\n{entry_text}",
            ok_text="Remove",
            cancel_text="Cancel",
        )

        if dialog.exec() == QDialog.Accepted:
            # Now work with the copied text entries instead of QListWidgetItems
            for entry in entries_to_remove:
                if self._model.remove_entry(entry):
                    logger.info(f"Removed entry '{entry}' from {self._name}")
                else:
                    logger.error(f"Failed to remove entry '{entry}' from {self._name}")

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

    def add_multiple_entries(self) -> None:
        """Add multiple entries to the list at once."""
        dialog = MultiEntryDialog(
            self,
            title=f"Add Multiple {self._name} Entries",
            message=f"Enter each {self._name} entry on a new line:",
            ok_text="Add Entries",
            cancel_text="Cancel",
        )

        if dialog.exec() == QDialog.Accepted:
            entries = dialog.get_entries()

            if not entries:
                QMessageBox.information(self, "No Entries", "No valid entries were provided.")
                return

            # Track statistics
            added = 0
            duplicates = 0

            # Add each entry
            for entry in entries:
                if self._model.add_entry(entry):
                    added += 1
                else:
                    duplicates += 1

            # Report results
            if added > 0:
                self.status_changed.emit(
                    f"Added {added} new entries"
                    + (f" (skipped {duplicates} duplicates)" if duplicates > 0 else "")
                )
            else:
                QMessageBox.warning(self, "Add Failed", "All entries already exist in the list.")

    def remove_selected_entries(self) -> None:
        """Remove selected entries from the list."""
        selected_items = self._list_widget.selectedItems()
        if selected_items:
            self._remove_entries(selected_items)
        else:
            QMessageBox.information(self, "Remove", "No items selected")

    def import_entries(self) -> None:
        """Import entries from a file, with options to replace or append."""
        try:
            # Start with last used directory if available
            start_dir = ""
            if hasattr(self, "_last_import_dir") and self._last_import_dir:
                start_dir = self._last_import_dir
            else:
                # Try to get from service locator
                service_locator = self.parent().findChild(QObject, "ServiceLocator")
                if service_locator:
                    config_manager = service_locator.get("config_manager")
                    if config_manager:
                        start_dir = config_manager.get("Files", "last_import_dir", "")

            # Show file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Entries", start_dir, "Text Files (*.txt)"
            )

            if not file_path:
                return

            # Remember this directory for next time
            self._last_import_dir = str(Path(file_path).parent)

            # Save to config if available
            service_locator = self.parent().findChild(QObject, "ServiceLocator")
            if service_locator:
                config_manager = service_locator.get("config_manager")
                if config_manager:
                    config_manager.set("Files", "last_import_dir", self._last_import_dir)

            # Ask if user wants to replace or append
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Import Options")
            msg_box.setText("How do you want to import entries?")
            msg_box.setIcon(QMessageBox.Question)

            replace_button = msg_box.addButton("Replace All", QMessageBox.ActionRole)
            append_button = msg_box.addButton("Append New", QMessageBox.ActionRole)
            cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

            msg_box.exec()

            chosen_button = msg_box.clickedButton()

            if chosen_button == cancel_button:
                return

            replace_mode = chosen_button == replace_button

            if replace_mode:
                # Double-check for replace mode
                confirm = QMessageBox.question(
                    self,
                    "Confirm Replace",
                    "This will replace ALL existing entries with the imported ones. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if confirm != QMessageBox.StandardButton.Yes:
                    return

                # Import with replace mode
                success, _ = self._model.import_from_file(Path(file_path))
                if success:
                    self.status_changed.emit(
                        f"Imported entries successfully, replacing all existing entries"
                    )
                else:
                    QMessageBox.critical(self, "Import Failed", "Failed to import entries")
            else:
                # Append mode - read file and add entries one by one
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        entries = [line.strip() for line in f.readlines() if line.strip()]

                    # Track statistics
                    added = 0
                    duplicates = 0

                    # Add each entry
                    for entry in entries:
                        if self._model.add_entry(entry):
                            added += 1
                        else:
                            duplicates += 1

                    # Report results
                    self.status_changed.emit(
                        f"Imported {added} new entries (skipped {duplicates} duplicates)"
                    )

                except Exception as e:
                    logger.error(f"Error appending entries from {file_path}: {e}")
                    QMessageBox.critical(self, "Import Failed", f"Error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in import_entries: {e}")
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred: {str(e)}")

    def export_entries(self) -> None:
        """Export entries to a file."""
        try:
            # Start with last used directory if available
            start_dir = ""
            if hasattr(self, "_last_export_dir") and self._last_export_dir:
                start_dir = self._last_export_dir
            else:
                # Try to get from service locator
                service_locator = self.parent().findChild(QObject, "ServiceLocator")
                if service_locator:
                    config_manager = service_locator.get("config_manager")
                    if config_manager:
                        start_dir = config_manager.get("Files", "last_export_dir", "")

            # Show file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Entries", start_dir, "Text Files (*.txt)"
            )

            if not file_path:
                return

            # Remember this directory for next time
            self._last_export_dir = str(Path(file_path).parent)

            # Save to config if available
            service_locator = self.parent().findChild(QObject, "ServiceLocator")
            if service_locator:
                config_manager = service_locator.get("config_manager")
                if config_manager:
                    config_manager.set("Files", "last_export_dir", self._last_export_dir)

            # Add .txt extension if not present
            if not file_path.lower().endswith(".txt"):
                file_path += ".txt"

            # Export entries
            success = self._model.export_to_file(Path(file_path))
            if success:
                self.status_changed.emit(f"Exported {self._model.count()} entries successfully")
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to export entries")
        except Exception as e:
            logger.error(f"Error in export_entries: {e}")
            QMessageBox.critical(self, "Export Error", f"An unexpected error occurred: {str(e)}")

    def refresh(self) -> None:
        """Refresh the list view."""
        self._model.refresh()
        self._populate_list(self._search_input.text())
