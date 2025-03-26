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
    QToolBar,
    QSizePolicy,
)
from PySide6.QtGui import QIcon, QAction, QColor, QBrush

from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.ui.resources.style import Colors
from chestbuddy.ui.resources.icons import Icons

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
        self.filter_active = False

        # Set minimum width for the widget
        self.setMinimumWidth(200)

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

        # Title and count layout
        title_layout = QHBoxLayout()

        # Title label
        self.title_label = QLabel(f"{self.title}")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(self.title_label)

        # Count label
        self.count_label = QLabel(f"(0)")
        self.count_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px;")
        title_layout.addWidget(self.count_label)

        # Add stretch to push count to the right
        title_layout.addStretch(1)

        layout.addLayout(title_layout)

        # Search bar
        search_layout = QHBoxLayout()

        # Search icon - use search icon from resources if available
        search_icon_label = QLabel()
        search_icon_label.setPixmap(
            Icons.get_pixmap(Icons.DASHBOARD).scaled(
                16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        search_layout.addWidget(search_icon_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        # Clear search button
        self.clear_search_button = QPushButton("✕")
        self.clear_search_button.setFixedSize(20, 20)
        self.clear_search_button.setStyleSheet("QPushButton { border: none; }")
        self.clear_search_button.clicked.connect(self._clear_search)
        self.clear_search_button.setVisible(False)
        search_layout.addWidget(self.clear_search_button)

        layout.addLayout(search_layout)

        # List widget for entries
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

        # Set list widget styling
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: {Colors.PRIMARY};
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {Colors.BORDER_DARK};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT};
                color: {Colors.TEXT_LIGHT};
                border-left: 3px solid {Colors.SECONDARY};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {Colors.PRIMARY_LIGHT};
            }}
        """)

        layout.addWidget(self.list_widget, 1)  # Add stretch factor to expand list

        # Bottom toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))

        # Add/Remove/Filter buttons
        self.add_button = QPushButton("Add")
        self.add_button.setIcon(QIcon.fromTheme("list-add"))
        self.add_button.clicked.connect(self._on_add_clicked)
        self.toolbar.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.setIcon(QIcon.fromTheme("list-remove"))
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.remove_button.setEnabled(False)
        self.toolbar.addWidget(self.remove_button)

        self.toolbar.addSeparator()

        self.filter_button = QPushButton("Filter")
        self.filter_button.setCheckable(True)
        self.filter_button.setIcon(QIcon.fromTheme("view-filter"))
        self.filter_button.clicked.connect(self._on_filter_toggled)
        self.toolbar.addWidget(self.filter_button)

        layout.addWidget(self.toolbar)

        # Status label
        self.status_label = QLabel("0 entries")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Connect list selection to enable/disable remove button
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_entries(self) -> None:
        """Load entries from the validation model."""
        self.list_widget.clear()

        entries = self.validation_model.get_entries()
        for entry in entries:
            self._add_item_to_list(entry)

        # Update status
        self._update_status()

    def _add_item_to_list(self, entry: str) -> None:
        """
        Add an entry to the list widget with proper formatting.

        Args:
            entry (str): The entry text to add
        """
        item = QListWidgetItem(entry)

        # Set background color based on validation status (if applicable)
        # This would be extended with actual validation logic in a real implementation
        # For now, we're just demonstrating the visual appearance
        if self.title == "Players" and len(entry) < 3:
            # Example of invalid entry (too short)
            item.setBackground(QBrush(QColor("#FFCCCC")))  # Light red for invalid
            item.setToolTip("Invalid: Name too short")
        elif self.title == "Chest Types" and "?" in entry:
            # Example of missing entry (contains question mark)
            item.setBackground(QBrush(QColor("#FFFFCC")))  # Light yellow for missing
            item.setToolTip("Warning: Uncertain chest type")

        self.list_widget.addItem(item)

    def _filter_entries(self, query: str) -> None:
        """
        Filter the list entries based on search text.

        Args:
            query (str): Search query text
        """
        # Show/hide clear button based on query
        self.clear_search_button.setVisible(bool(query))

        self.list_widget.clear()

        entries = self.validation_model.find_matching_entries(query)
        for entry in entries:
            self._add_item_to_list(entry)

        # Update status to show filtered count
        filtered_text = f" (filtered from {self.validation_model.count()})" if query else ""
        self.status_label.setText(f"{len(entries)} entries{filtered_text}")

        # Update the count label
        if query:
            self.count_label.setText(f"({len(entries)}/{self.validation_model.count()})")
        else:
            self.count_label.setText(f"({self.validation_model.count()})")

    @Slot()
    def _clear_search(self) -> None:
        """Clear the search input and reset the list."""
        self.search_input.clear()
        self._filter_entries("")

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
            # Force a full reload of entries rather than filtering
            self._load_entries()
        else:
            QMessageBox.information(
                self,
                "Duplicate Entry",
                f"The entry '{text}' already exists in the {self.title} list.",
            )
            # Make sure we still show all entries
            current_query = self.search_input.text()
            if current_query:
                self._filter_entries(current_query)
            else:
                self._load_entries()

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
        # Always start with a full reload to ensure all entries are available
        current_query = self.search_input.text()

        # First reload all entries to ensure model and view are in sync
        self._load_entries()

        # Then apply any filter if search is active
        if current_query:
            self._filter_entries(current_query)

    @Slot(bool)
    def _on_filter_toggled(self, checked: bool) -> None:
        """
        Handle filter button toggle.

        Args:
            checked (bool): Whether the button is checked
        """
        self.filter_active = checked

        if checked:
            self.filter_button.setText("Filtering...")
            # In a real implementation, this would apply additional filtering logic
            # For now, just change the button text as a visual indicator
        else:
            self.filter_button.setText("Filter")
            # Remove any additional filtering beyond the search text

        # Refresh the display
        self._on_search_text_changed(self.search_input.text())

    def _update_status(self) -> None:
        """Update the status label and emit status changed signal."""
        count = self.validation_model.count()
        self.status_label.setText(f"{count} entries")
        self.count_label.setText(f"({count})")

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

        # Style the context menu
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.PRIMARY};
                border: 1px solid {Colors.BORDER};
            }}
            QMenu::item {{
                padding: 6px 20px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.ACCENT};
            }}
        """)

        add_action = QAction("Add Entry", self)
        add_action.triggered.connect(self._on_add_clicked)
        menu.addAction(add_action)

        # Only enable actions that require selection if items are selected
        if self.list_widget.selectedItems():
            remove_action = QAction("Remove Selected", self)
            remove_action.triggered.connect(self._on_remove_clicked)
            menu.addAction(remove_action)

            menu.addSeparator()

            # Add export selection action
            export_action = QAction("Export Selected", self)
            export_action.triggered.connect(self._on_export_selected)
            menu.addAction(export_action)

        menu.exec(self.list_widget.mapToGlobal(position))

    @Slot()
    def _on_export_selected(self) -> None:
        """Handle export selected action."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        from PySide6.QtWidgets import QFileDialog

        # Get file path for export
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Selected Entries", "", "Text Files (*.txt)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w") as f:
                for item in selected_items:
                    f.write(f"{item.text()}\n")

            self.status_label.setText(f"Exported {len(selected_items)} entries")
            logger.info(f"Exported {len(selected_items)} entries to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export entries: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export entries: {str(e)}")

    def refresh(self) -> None:
        """Refresh the validation list view."""
        self.validation_model.refresh()
        self._load_entries()
