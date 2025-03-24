"""
recent_files_list.py

Description: Enhanced widget for displaying recent files with metadata and actions
Usage:
    recent_files = RecentFilesList()
    recent_files.set_files(files_data)
    recent_files.file_selected.connect(self._on_file_selected)
"""

from typing import List, Dict, Any, Optional, Callable
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QSpacerItem,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon

from chestbuddy.ui.resources.colors import Colors
from chestbuddy.ui.resources.icons import IconProvider
from chestbuddy.ui.widgets.empty_state_widget import EmptyStateWidget


class FileCard(QFrame):
    """
    A card widget for displaying file information with actions.

    This component displays file metadata (name, date, size, rows) and
    provides action buttons for common operations on the file.

    Attributes:
        file_clicked: Signal emitted when the file card is clicked
        action_clicked: Signal emitted when an action button is clicked
    """

    # Signals
    file_clicked = Signal(str)  # File path
    action_clicked = Signal(str, str)  # Action name, file path

    def __init__(self, file_data: Dict[str, Any], parent: Optional[QWidget] = None):
        """
        Initialize the file card with file data.

        Args:
            file_data: Dictionary containing file information
            parent: Parent widget
        """
        super().__init__(parent)

        # Store file data
        self._file_data = file_data
        self._file_path = file_data.get("path", "")

        # Set frame properties
        self.setObjectName("fileCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            #fileCard {{
                background-color: {Colors.BACKGROUND_LIGHT};
                border-radius: 6px;
                border: 1px solid {Colors.BORDER};
                padding: 8px;
            }}
            #fileCard:hover {{
                border: 1px solid {Colors.PRIMARY};
                background-color: {Colors.BACKGROUND_LIGHT_HOVER};
            }}
        """)

        # Set minimum height
        self.setMinimumHeight(80)

        # Set up UI
        self._setup_ui()

        # Connect internal signals
        self.mousePressEvent = self._on_mouse_press

    def _setup_ui(self) -> None:
        """Set up the card UI."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._main_layout.setSpacing(8)

        # Top row: File name and date
        self._top_layout = QHBoxLayout()
        self._top_layout.setContentsMargins(0, 0, 0, 0)
        self._top_layout.setSpacing(8)

        # File icon
        self._file_icon = QLabel()
        icon = IconProvider.get_icon("file_csv")
        pixmap = icon.pixmap(QSize(24, 24))
        self._file_icon.setPixmap(pixmap)
        self._top_layout.addWidget(self._file_icon)

        # File name
        file_name = os.path.basename(self._file_path)
        self._file_name = QLabel(file_name)
        self._file_name.setStyleSheet(f"font-weight: bold; color: {Colors.TEXT_DARK};")
        self._file_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._top_layout.addWidget(self._file_name)

        # File date
        date_str = self._file_data.get("date", "")
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_obj.strftime("%b %d, %Y")
            except ValueError:
                display_date = date_str
        else:
            display_date = "Unknown date"

        self._file_date = QLabel(display_date)
        self._file_date.setStyleSheet(f"color: {Colors.TEXT_MEDIUM}; font-size: 12px;")
        self._top_layout.addWidget(self._file_date)

        self._main_layout.addLayout(self._top_layout)

        # Middle row: File metadata
        self._meta_layout = QHBoxLayout()
        self._meta_layout.setContentsMargins(0, 0, 0, 0)
        self._meta_layout.setSpacing(16)

        # File size
        size = self._file_data.get("size", 0)
        size_str = self._format_size(size) if size else "Unknown size"
        self._size_label = QLabel(f"Size: {size_str}")
        self._size_label.setStyleSheet(f"color: {Colors.TEXT_MEDIUM}; font-size: 12px;")
        self._meta_layout.addWidget(self._size_label)

        # Row count
        rows = self._file_data.get("rows", 0)
        rows_str = f"{rows:,}" if rows else "Unknown"
        self._rows_label = QLabel(f"Rows: {rows_str}")
        self._rows_label.setStyleSheet(f"color: {Colors.TEXT_MEDIUM}; font-size: 12px;")
        self._meta_layout.addWidget(self._rows_label)

        # Add spacer to push metadata to the left
        self._meta_layout.addStretch()

        self._main_layout.addLayout(self._meta_layout)

        # Bottom row: Actions
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 4, 0, 0)
        self._actions_layout.setSpacing(8)

        # Add spacer to push buttons to the right
        self._actions_layout.addStretch()

        # Open button
        self._open_button = QPushButton("Open")
        self._open_button.setIcon(IconProvider.get_icon("open"))
        self._open_button.setCursor(Qt.PointingHandCursor)
        self._open_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SECONDARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.SECONDARY_DARKER};
            }}
        """)
        self._open_button.clicked.connect(lambda: self._on_action_clicked("open"))
        self._actions_layout.addWidget(self._open_button)

        # Validate button
        self._validate_button = QPushButton("Validate")
        self._validate_button.setIcon(IconProvider.get_icon("validate"))
        self._validate_button.setCursor(Qt.PointingHandCursor)
        self._validate_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARKER};
            }}
        """)
        self._validate_button.clicked.connect(lambda: self._on_action_clicked("validate"))
        self._actions_layout.addWidget(self._validate_button)

        # Remove button
        self._remove_button = QPushButton()
        self._remove_button.setIcon(IconProvider.get_icon("delete"))
        self._remove_button.setCursor(Qt.PointingHandCursor)
        self._remove_button.setToolTip("Remove from recent files")
        self._remove_button.setFixedSize(28, 28)
        self._remove_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: {Colors.TEXT_LIGHT};
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.DANGER_DARKER};
            }}
        """)
        self._remove_button.clicked.connect(lambda: self._on_action_clicked("remove"))
        self._actions_layout.addWidget(self._remove_button)

        self._main_layout.addLayout(self._actions_layout)

    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in a human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted size string (e.g., "2.5 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _on_mouse_press(self, event) -> None:
        """
        Handle mouse press events.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Only trigger for left button clicks
            self.file_clicked.emit(self._file_path)

    def _on_action_clicked(self, action: str) -> None:
        """
        Handle action button clicks.

        Args:
            action: Action name ('open', 'validate', or 'remove')
        """
        self.action_clicked.emit(action, self._file_path)

    def update_file_data(self, file_data: Dict[str, Any]) -> None:
        """
        Update the file card with new data.

        Args:
            file_data: Dictionary containing updated file information
        """
        self._file_data = file_data
        self._file_path = file_data.get("path", "")

        # Update UI elements
        file_name = os.path.basename(self._file_path)
        self._file_name.setText(file_name)

        date_str = self._file_data.get("date", "")
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_obj.strftime("%b %d, %Y")
            except ValueError:
                display_date = date_str
        else:
            display_date = "Unknown date"
        self._file_date.setText(display_date)

        size = self._file_data.get("size", 0)
        size_str = self._format_size(size) if size else "Unknown size"
        self._size_label.setText(f"Size: {size_str}")

        rows = self._file_data.get("rows", 0)
        rows_str = f"{rows:,}" if rows else "Unknown"
        self._rows_label.setText(f"Rows: {rows_str}")


class RecentFilesList(QWidget):
    """
    Enhanced widget for displaying recent files with metadata and actions.

    This component shows a list of recent files with detailed information
    and provides action buttons for each file.

    Attributes:
        file_selected: Signal emitted when a file is selected
        file_action: Signal emitted when a file action is clicked
    """

    # Signals
    file_selected = Signal(str)  # File path
    file_action = Signal(str, str)  # Action name, file path

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the recent files list.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize state
        self._files = []
        self._file_cards = {}

        # Set up UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Header
        self._header = QWidget()
        self._header.setMinimumHeight(40)
        self._header.setStyleSheet(f"""
            background-color: {Colors.BACKGROUND_LIGHT};
            border-bottom: 1px solid {Colors.BORDER};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        """)

        self._header_layout = QHBoxLayout(self._header)
        self._header_layout.setContentsMargins(16, 8, 16, 8)
        self._header_layout.setSpacing(8)

        self._header_icon = QLabel()
        icon = IconProvider.get_icon("history")
        pixmap = icon.pixmap(QSize(16, 16))
        self._header_icon.setPixmap(pixmap)
        self._header_layout.addWidget(self._header_icon)

        self._header_title = QLabel("Recent Files")
        self._header_title.setStyleSheet(f"font-weight: bold; color: {Colors.TEXT_DARK};")
        self._header_layout.addWidget(self._header_title)

        self._header_layout.addStretch()

        self._clear_all_button = QPushButton("Clear All")
        self._clear_all_button.setCursor(Qt.PointingHandCursor)
        self._clear_all_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.DANGER};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        self._clear_all_button.clicked.connect(self._on_clear_all)
        self._header_layout.addWidget(self._clear_all_button)

        self._main_layout.addWidget(self._header)

        # Scroll area for file cards
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Colors.BACKGROUND};
                border: 1px solid {Colors.BORDER};
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {Colors.BACKGROUND};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # Container for file cards
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(16, 16, 16, 16)
        self._container_layout.setSpacing(12)

        # Empty state
        icon = IconProvider.get_icon("history")
        self._empty_state = EmptyStateWidget(
            title="No Recent Files",
            message="Recently opened files will appear here",
            icon=icon,
            action_text="Import Files",
            action_callback=lambda: self.file_action.emit("import", ""),
        )
        self._empty_state.action_clicked.connect(lambda: self.file_action.emit("import", ""))
        self._container_layout.addWidget(self._empty_state)
        self._empty_state.setVisible(False)  # Hide initially

        self._scroll_area.setWidget(self._container)
        self._main_layout.addWidget(self._scroll_area)

    def set_files(self, files: List[Dict[str, Any]]) -> None:
        """
        Set the list of recent files to display.

        Args:
            files: List of file information dictionaries
        """
        # Save the files list
        self._files = files.copy() if files else []

        # Clear existing file cards
        self._clear_file_cards()

        # Show empty state if no files
        if not self._files:
            self._empty_state.setVisible(True)
            self._empty_state.show()
            return

        # Hide empty state
        self._empty_state.setVisible(False)
        self._empty_state.hide()

        # Create file cards for each file
        for file_data in self._files:
            self._add_file_card(file_data)

    def _add_file_card(self, file_data: Dict[str, Any]) -> None:
        """
        Add a file card to the list.

        Args:
            file_data: Dictionary containing file information
        """
        file_path = file_data.get("path", "")
        if not file_path:
            return

        # Create file card
        card = FileCard(file_data)
        card.file_clicked.connect(self._on_file_selected)
        card.action_clicked.connect(self._on_file_action)

        # Add to container
        self._container_layout.addWidget(card)

        # Store reference
        self._file_cards[file_path] = card

    def _clear_file_cards(self) -> None:
        """Remove all file cards from the container."""
        # Remove cards from layout and delete
        for path, card in self._file_cards.items():
            self._container_layout.removeWidget(card)
            card.deleteLater()

        # Clear dictionary
        self._file_cards.clear()

    def _on_file_selected(self, file_path: str) -> None:
        """
        Handle file selection.

        Args:
            file_path: Path of the selected file
        """
        self.file_selected.emit(file_path)

    def _on_file_action(self, action: str, file_path: str) -> None:
        """
        Handle file action.

        Args:
            action: Action name ('open', 'validate', or 'remove')
            file_path: Path of the file
        """
        if action == "remove":
            # Remove the file card
            if file_path in self._file_cards:
                card = self._file_cards[file_path]
                self._container_layout.removeWidget(card)
                card.deleteLater()
                del self._file_cards[file_path]

                # Remove from files list
                self._files = [f for f in self._files if f.get("path") != file_path]

                # Show empty state if no files left
                if not self._files:
                    self._empty_state.setVisible(True)

        # Emit signal
        self.file_action.emit(action, file_path)

    def _on_clear_all(self) -> None:
        """Handle clear all button click."""
        # Clear all file cards
        self._clear_file_cards()

        # Clear files list
        self._files = []

        # Show empty state
        self._empty_state.setVisible(True)
        self._empty_state.show()

        # Emit signal
        self.file_action.emit("clear_all", "")

    def update_file(self, file_path: str, file_data: Dict[str, Any]) -> None:
        """
        Update information for a specific file.

        Args:
            file_path: Path of the file to update
            file_data: Dictionary containing updated file information
        """
        if file_path in self._file_cards:
            # Update card
            self._file_cards[file_path].update_file_data(file_data)

            # Update in files list
            for i, file in enumerate(self._files):
                if file.get("path") == file_path:
                    self._files[i] = file_data
                    break
