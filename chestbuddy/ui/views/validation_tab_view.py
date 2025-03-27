"""
validation_tab_view.py

Description: View for managing validation lists with import/export functionality
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
    QFrame,
    QSplitter,
    QToolBar,
    QStatusBar,
    QLineEdit,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction

from chestbuddy.ui.views.validation_list_view import ValidationListView
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.ui.utils.icon_provider import IconProvider
from chestbuddy.ui.resources.style import Colors

logger = logging.getLogger(__name__)


class ValidationTabView(QWidget):
    """
    View for managing validation lists with import/export functionality.

    Attributes:
        validation_changed (Signal): Signal emitted when validation status changes
    """

    validation_changed = Signal()

    def __init__(self, validation_service: ValidationService, parent: Optional[QWidget] = None):
        """
        Initialize the validation tab view.

        Args:
            validation_service (ValidationService): Service for validation
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self._validation_service = validation_service
        self._setup_ui()
        self._connect_signals()
        logger.info("Initialized ValidationTabView")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Set background color for the main view - using Colors from style.py
        self.setStyleSheet(f"background-color: {Colors.DARK_CONTENT_BG};")
        # Ensure the widget itself has the correct background (needed for Qt styling)
        self.setAutoFillBackground(True)
        self.setProperty("lightContentView", True)  # Enable light theme styling

        # Create splitter for resizable panels
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setStyleSheet(f"""
            QSplitter {{
                background-color: {Colors.DARK_CONTENT_BG};
            }}
            QSplitter::handle {{
                background-color: {Colors.DARK_CONTENT_BG};
                width: 4px;
            }}
        """)
        # Ensure the splitter has correct background
        self._splitter.setAutoFillBackground(True)
        self._splitter.setProperty("lightContentView", True)  # Enable light theme styling

        # Create sections for players, chest types, and sources
        self._players_section = self._create_validation_list_section(
            "Players", self._validation_service.get_validation_list_path("players.txt")
        )

        self._chest_types_section = self._create_validation_list_section(
            "Chest Types", self._validation_service.get_validation_list_path("chest_types.txt")
        )

        self._sources_section = self._create_validation_list_section(
            "Sources", self._validation_service.get_validation_list_path("sources.txt")
        )

        # Add sections to splitter
        self._splitter.addWidget(self._players_section)
        self._splitter.addWidget(self._chest_types_section)
        self._splitter.addWidget(self._sources_section)

        # Set initial sizes (equal distribution)
        self._splitter.setSizes([1, 1, 1])

        # Add splitter to layout
        main_layout.addWidget(self._splitter, 1)  # 1 = stretch factor to take available space

        # Create bottom toolbar
        toolbar = QToolBar()

        # Style toolbar buttons using Colors from style.py
        toolbar_style = f"""
            QToolBar {{
                spacing: 10px;
                padding: 6px;
                background-color: {Colors.DARK_CONTENT_BG};
                border-top: 1px solid {Colors.DARK_BORDER};
                border-bottom: 1px solid {Colors.DARK_BORDER};
            }}
            QToolButton {{
                border: 1px solid {Colors.SECONDARY};
                border-radius: 4px;
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_LIGHT};
                font-weight: bold;
                font-size: 13px;
                padding: 8px 12px;
                min-width: 140px;
            }}
            QToolButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                border-color: {Colors.SECONDARY};
            }}
            QToolButton:pressed {{
                background-color: {Colors.PRIMARY_ACTIVE};
                border-color: {Colors.SECONDARY};
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            QToolButton:disabled {{
                background-color: {Colors.DISABLED};
                border-color: {Colors.DARK_BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """
        toolbar.setStyleSheet(toolbar_style)
        toolbar.setAutoFillBackground(True)  # Ensure toolbar has correct background
        toolbar.setProperty("lightContentView", True)  # Enable light theme styling

        # Add toolbar actions
        self._preferences_action = QAction(
            IconProvider.get_icon("settings"),
            "Preferences",
            self,
        )
        self._validate_action = QAction(
            IconProvider.get_icon("check"),
            "Validate",
            self,
        )

        toolbar.addAction(self._preferences_action)
        toolbar.addAction(self._validate_action)

        main_layout.addWidget(toolbar)

        # Create status bar
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Colors.PRIMARY_DARK};
                color: {Colors.TEXT_LIGHT};
                padding: 3px 6px;
            }}
        """)
        self._status_bar.setMaximumHeight(24)  # Reduce status bar height
        self._status_bar.setAutoFillBackground(True)  # Ensure status bar has correct background
        self._status_bar.setProperty("lightContentView", True)  # Enable light theme styling
        main_layout.addWidget(self._status_bar)

        # Set initial status
        self._set_status_message("Ready")

        # Ensure proper styling for all widgets
        self._ensure_widget_styling()

    def _set_status_message(self, message: str) -> None:
        """
        Set the status bar message.

        Args:
            message (str): Status message to display
        """
        self._status_bar.showMessage(message)
        logger.debug(f"Status updated: {message}")

    def _ensure_widget_styling(self):
        """
        Ensure all widgets in the hierarchy have proper background styling.
        This is crucial for Qt's styling system to render backgrounds correctly.
        """
        # For each section, ensure proper styling
        for section in [self._players_section, self._chest_types_section, self._sources_section]:
            # Set section's properties (container is already a widget)
            section.setProperty("container", True)
            section.setProperty("lightContentView", True)
            section.setAutoFillBackground(True)

            # Find all validation list views within the section
            for list_view in section.findChildren(ValidationListView):
                list_view.setProperty("lightContentView", True)
                list_view.setAutoFillBackground(True)

                # Find child widgets of the list view and set properties
                for child in list_view.findChildren(QWidget):
                    # Skip input fields which should have white background
                    if not isinstance(child, QLineEdit):
                        child.setProperty("lightContentView", True)
                        child.setAutoFillBackground(True)

    def _create_validation_list_section(self, title: str, list_path: Path) -> QWidget:
        """
        Create a validation list section with toolbar and list view.

        Args:
            title (str): Title of the section
            list_path (Path): Path to the validation list file

        Returns:
            QWidget: The created section widget
        """
        # Create container widget
        container = QWidget()
        container.setStyleSheet(f"background-color: {Colors.DARK_CONTENT_BG};")
        container.setAutoFillBackground(True)  # Ensure the container has proper background
        container.setProperty("container", True)

        # Get the appropriate model based on title
        if title.lower() == "players":
            model = self._validation_service.get_player_list_model()
        elif title.lower() == "chest types":
            model = self._validation_service.get_chest_type_list_model()
        elif title.lower() == "sources":
            model = self._validation_service.get_source_list_model()
        else:
            # Default fallback - should not happen with current design
            model = ValidationListModel(list_path)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Section header with title and count
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        header = QLabel(title)
        header.setStyleSheet(
            f"font-weight: bold; font-size: 16px; color: {Colors.TEXT_LIGHT}; background-color: {Colors.PRIMARY_DARK}; padding: 4px 8px; border-radius: 4px;"
        )
        header_layout.addWidget(header)

        # Count label will be updated later
        count_label = QLabel("(0)")
        count_label.setStyleSheet(
            f"color: {Colors.SECONDARY}; font-size: 14px; font-weight: bold; margin-left: 8px;"
        )
        header_layout.addWidget(count_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Create buttons layout (horizontal instead of grid)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 4, 0, 8)
        buttons_layout.setSpacing(6)  # Proper spacing between buttons

        # Create styled buttons with smaller size for single row
        btn_style = f"""
            QPushButton {{
                padding: 4px 8px;
                border: 1px solid {Colors.PRIMARY};
                border-radius: 4px;
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_ON_PRIMARY};
                font-weight: bold;
                font-size: 11px;
                min-width: 70px;
                margin: 1px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
                border-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_ACTIVE};
                border-color: {Colors.PRIMARY_ACTIVE};
                padding-top: 5px;
                padding-bottom: 3px;
            }}
            QPushButton:disabled {{
                background-color: {Colors.DISABLED};
                border-color: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """

        # Add button
        add_button = QPushButton(IconProvider.get_icon("plus"), "Add")
        add_button.setStyleSheet(btn_style)
        add_button.setIconSize(QSize(12, 12))

        # Remove button
        remove_button = QPushButton(IconProvider.get_icon("minus"), "Remove")
        remove_button.setStyleSheet(btn_style)
        remove_button.setIconSize(QSize(12, 12))

        # Import button
        import_button = QPushButton(IconProvider.get_icon("import"), "Import")
        import_button.setStyleSheet(btn_style)
        import_button.setIconSize(QSize(12, 12))

        # Export button
        export_button = QPushButton(IconProvider.get_icon("export"), "Export")
        export_button.setStyleSheet(btn_style)
        export_button.setIconSize(QSize(12, 12))

        # Add buttons to horizontal layout
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addWidget(import_button)
        buttons_layout.addWidget(export_button)
        buttons_layout.addStretch(1)  # Add stretch to push buttons to the left

        # Add buttons layout to main layout
        layout.addLayout(buttons_layout)

        # Create and add list view with the model
        list_view = ValidationListView(model)
        list_view.setStyleSheet(f"""
            ValidationListView {{
                background-color: {Colors.BACKGROUND_PRIMARY};
            }}
            QListView {{
                background-color: {Colors.BACKGROUND_INPUT};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 4px;
            }}
        """)
        list_view.setAutoFillBackground(True)  # Ensure list view has correct background
        layout.addWidget(list_view)

        # Update count label with actual count
        if model:
            count = len(model.entries)
            count_label.setText(f"({count})")
            # Connect model.entries_changed to update count
            model.entries_changed.connect(lambda: count_label.setText(f"({len(model.entries)})"))

        # Create normalized section name (no spaces)
        section_name = title.lower().replace(" ", "_")

        # Store references
        setattr(self, f"_{section_name}_count", count_label)
        setattr(self, f"_{section_name}_list", list_view)
        setattr(self, f"_{section_name}_add", add_button)
        setattr(self, f"_{section_name}_remove", remove_button)
        setattr(self, f"_{section_name}_import", import_button)
        setattr(self, f"_{section_name}_export", export_button)

        return container

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect toolbar actions
        self._preferences_action.triggered.connect(self._on_preferences_clicked)
        self._validate_action.triggered.connect(self._on_validate_clicked)

        # Define section names with normalized format (underscores instead of spaces)
        sections = ["players", "chest_types", "sources"]

        # Connect list actions for each section
        for section in sections:
            # Get widgets
            add_button = getattr(self, f"_{section}_add")
            remove_button = getattr(self, f"_{section}_remove")
            import_button = getattr(self, f"_{section}_import")
            export_button = getattr(self, f"_{section}_export")
            list_view = getattr(self, f"_{section}_list")

            # Connect actions
            add_button.clicked.connect(lambda checked=False, s=section: self._on_add_clicked(s))
            remove_button.clicked.connect(
                lambda checked=False, s=section: self._on_remove_clicked(s)
            )
            import_button.clicked.connect(
                lambda checked=False, s=section: self._on_list_import_clicked(s)
            )
            export_button.clicked.connect(
                lambda checked=False, s=section: self._on_list_export_clicked(s)
            )

            # Connect list view model signals
            model = list_view.model()
            if model:
                model.entries_changed.connect(self._on_entries_changed)

            # Connect status signal if available
            if hasattr(list_view, "status_changed"):
                list_view.status_changed.connect(self._on_status_changed)

    def _on_preferences_clicked(self) -> None:
        """Handle preferences button click."""
        # TODO: Show validation preferences dialog
        logger.info("Preferences clicked")

    def _on_validate_clicked(self) -> None:
        """Handle validate button click."""
        # TODO: Implement validation triggering
        self.validation_changed.emit()
        logger.info("Validate clicked")

    def _on_add_clicked(self, section: str) -> None:
        """
        Handle add button click for a section.

        Args:
            section (str): Section name (players, chest_types, sources)
        """
        list_view = getattr(self, f"_{section}_list")
        list_view.add_entry()

    def _on_remove_clicked(self, section: str) -> None:
        """
        Handle remove button click for a section.

        Args:
            section (str): Section name (players, chest_types, sources)
        """
        list_view = getattr(self, f"_{section}_list")
        list_view.remove_selected_entries()

    def _on_list_import_clicked(self, section: str) -> None:
        """
        Handle import button click for a section.

        Args:
            section (str): Section name (players, chest_types, sources)
        """
        list_view = getattr(self, f"_{section}_list")
        list_view.import_entries()

    def _on_list_export_clicked(self, section: str) -> None:
        """
        Handle export button click for a section.

        Args:
            section (str): Section name (players, chest_types, sources)
        """
        list_view = getattr(self, f"_{section}_list")
        list_view.export_entries()

    def _on_entries_changed(self) -> None:
        """Handle changes to validation list entries."""
        self.validation_changed.emit()
        self._update_validation_stats()  # Update validation statistics when entries change

    def _on_status_changed(self, message: str = "") -> None:
        """
        Handle status change.

        Args:
            message (str): Status message
        """
        if message:
            self._status_bar.showMessage(message, 3000)  # Show for 3 seconds
        else:
            self._update_validation_stats()

    def _update_validation_stats(self) -> None:
        """Update the status bar with validation statistics."""
        # Get statistics from validation service
        total_valid = 0
        total_invalid = 0
        total_missing = 0
        total_entries = 0

        # Calculate stats from all validation lists
        sections = ["players", "chest_types", "sources"]
        for section in sections:
            list_view = getattr(self, f"_{section}_list", None)
            if list_view and hasattr(list_view, "model"):
                model = list_view.model()
                if model:
                    # Get entry counts from model
                    entries = model.entries
                    total_entries += len(entries)

                    # Simple counting method - can be enhanced if model has these properties
                    valid_count = sum(
                        1
                        for entry in entries
                        if not getattr(entry, "is_invalid", False)
                        and not getattr(entry, "is_missing", False)
                    )
                    invalid_count = sum(
                        1 for entry in entries if getattr(entry, "is_invalid", False)
                    )
                    missing_count = sum(
                        1 for entry in entries if getattr(entry, "is_missing", False)
                    )

                    total_valid += valid_count
                    total_invalid += invalid_count
                    total_missing += missing_count

        # Calculate percentages
        if total_entries > 0:
            valid_pct = (total_valid / total_entries) * 100
            invalid_pct = (total_invalid / total_entries) * 100
            missing_pct = (total_missing / total_entries) * 100

            # Format status message
            status_msg = f"Validation: {valid_pct:.0f}% valid, {invalid_pct:.0f}% invalid, {missing_pct:.0f}% missing"
        else:
            status_msg = "Validation: No entries"

        # Update status bar
        self._status_bar.showMessage(status_msg)

    def refresh(self) -> None:
        """Refresh all validation lists."""
        for section in ["players", "chest_types", "sources"]:
            list_view = getattr(self, f"_{section}_list")
            list_view.refresh()

    def clear_validation(self) -> None:
        """Clear validation highlighting and status."""
        for section in ["players", "chest_types", "sources"]:
            list_view = getattr(self, f"_{section}_list")
            list_view.clear_validation()
