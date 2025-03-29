"""
validation_tab_view.py

Description: View for managing validation lists with import/export functionality
"""

import logging
from pathlib import Path
from typing import Optional, Dict

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
    QCheckBox,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon

from chestbuddy.ui.views.validation_list_view import ValidationListView
from chestbuddy.core.models.validation_list_model import ValidationListModel
from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.ui.utils.icon_provider import IconProvider
from chestbuddy.ui.resources.style import Colors
import pandas as pd  # Add pandas import
from chestbuddy.utils.service_locator import ServiceLocator  # Added import

logger = logging.getLogger(__name__)


class ValidationTabView(QWidget):
    """
    View for managing validation lists with import/export functionality.

    Attributes:
        validation_changed (Signal): Signal emitted when validation status changes
    """

    validation_changed = Signal(object)  # Signal emitted with validation status DataFrame

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        validation_service: Optional[ValidationService] = None,
    ) -> None:
        """
        Initialize the validation tab view.

        Args:
            parent (Optional[QWidget]): Parent widget
            validation_service (Optional[ValidationService]): Service for validation
        """
        super().__init__(parent)
        self.setObjectName("validation_tab")

        # Store validation service or get from ServiceLocator
        self._validation_service = validation_service
        if self._validation_service is None:
            try:
                self._validation_service = ServiceLocator.get("validation_service")
                logger.info("Retrieved ValidationService from ServiceLocator")
            except KeyError:
                logger.error("ValidationService not found in ServiceLocator")
                self._display_service_error()

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
        # Allow collapsing but set a minimum size
        self._splitter.setHandleWidth(8)  # Wider handle for easier grabbing
        self._splitter.setStyleSheet(f"""
            QSplitter {{
                background-color: {Colors.DARK_CONTENT_BG};
            }}
            QSplitter::handle {{
                background-color: {Colors.DARK_CONTENT_BG};
                width: 8px;
            }}
            QSplitter::handle:hover {{
                background-color: {Colors.BG_MEDIUM};
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

        # Create a widget for toolbar options section
        options_widget = QWidget()
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(10, 0, 10, 0)
        options_layout.setSpacing(20)

        # Add validation preferences checkboxes
        options_label = QLabel("Options:")
        options_label.setStyleSheet(f"color: {Colors.TEXT_LIGHT}; font-weight: bold;")

        self._case_sensitive_checkbox = QCheckBox("Case-sensitive")
        self._case_sensitive_checkbox.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")
        self._case_sensitive_checkbox.setToolTip("When enabled, validation will be case-sensitive")

        self._validate_on_import_checkbox = QCheckBox("Validate on import")
        self._validate_on_import_checkbox.setStyleSheet(f"color: {Colors.TEXT_LIGHT};")
        self._validate_on_import_checkbox.setToolTip(
            "When enabled, validation will be performed automatically when importing data"
        )

        # Load initial settings from validation service
        prefs = self._validation_service.get_validation_preferences()
        self._case_sensitive_checkbox.setChecked(prefs.get("case_sensitive", False))
        self._validate_on_import_checkbox.setChecked(prefs.get("validate_on_import", True))

        # Add widgets to options layout
        options_layout.addWidget(options_label)
        options_layout.addWidget(self._case_sensitive_checkbox)
        options_layout.addWidget(self._validate_on_import_checkbox)
        options_layout.addStretch(1)  # Add stretch to push everything to the left

        # Add validate button on the right side
        self._validate_action = QAction(
            IconProvider.get_icon("check"),
            "Validate",
            self,
        )

        # Add widgets to toolbar
        toolbar.addWidget(options_widget)
        toolbar.addSeparator()
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
            f"font-weight: bold; font-size: 16px; color: {Colors.TEXT_LIGHT}; border-bottom: 2px solid {Colors.SECONDARY}; padding-bottom: 4px; margin-bottom: 4px;"
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

        # Create and add list view with the model first (moved up)
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

        # Create buttons layout (moved below the list view)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 8, 0, 0)  # Adjusted top margin
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
        # Connect signals from validation service
        if hasattr(self._validation_service, "validation_changed"):
            # Disconnect existing connections first to prevent duplicates
            try:
                self._validation_service.validation_changed.disconnect(self._on_validation_changed)
                logger.debug("Disconnected existing validation_changed signal.")
            except (TypeError, RuntimeError):
                logger.debug("No existing validation_changed signal to disconnect.")

            # Connect the signal
            self._validation_service.validation_changed.connect(self._on_validation_changed)
            logger.debug("Connected validation_changed signal to _on_validation_changed.")
        else:
            logger.warning("ValidationService has no validation_changed signal.")

        # Connect button actions
        self._validate_action.triggered.connect(self._on_validate_clicked)

        # Connect checkbox signals
        self._case_sensitive_checkbox.stateChanged.connect(self._update_validation_preference)
        self._validate_on_import_checkbox.stateChanged.connect(self._update_validation_preference)

        # Connect signals for each list view
        for list_view in self.findChildren(ValidationListView):
            # Call model() method to get the actual model object
            model = list_view.model()
            if model and hasattr(model, "entries_changed"):
                # ValidationListModel uses a custom signal called 'entries_changed'
                # instead of standard Qt model signals
                model.entries_changed.connect(self._update_list_view_status)
                logger.debug(f"Connected entries_changed signal for {list_view.objectName()}")
            else:
                logger.warning(
                    f"ValidationListView {list_view.objectName()} has no model or missing expected signal"
                )

    def _on_validation_changed(self, status_df: pd.DataFrame) -> None:
        """
        Slot to handle validation changes.

        Args:
            status_df (pd.DataFrame): The DataFrame containing validation status.
        """
        logger.info(f"Received validation_changed signal with status shape: {status_df.shape}")
        # Potentially update UI elements based on the validation status here.
        # For now, just log the reception.
        self._set_status_message("Validation status updated.")
        # Emit our own signal if needed by parent components
        self.validation_changed.emit(status_df)

    def _update_validation_preference(self) -> None:
        """Update validation preferences in the service based on checkbox states."""
        prefs = {
            "case_sensitive": self._case_sensitive_checkbox.isChecked(),
            "validate_on_import": self._validate_on_import_checkbox.isChecked(),
        }
        self._validation_service.set_validation_preferences(prefs)
        logger.info(f"Validation preferences updated: {prefs}")
        self._set_status_message("Validation preferences updated.")

    def _update_list_view_status(self) -> None:
        """Update status based on changes in any validation list view."""
        # Check if any list has unsaved changes
        has_unsaved = any(
            lv.model.has_unsaved_changes() for lv in self.findChildren(ValidationListView)
        )
        if has_unsaved:
            self._set_status_message("Unsaved changes in validation lists.")
        else:
            self._set_status_message("Ready")

    def _on_validate_clicked(self) -> None:
        """Handle validate button click."""
        try:
            # Change status to show validation is in progress
            self._set_status_message("Validating data...")

            # Trigger validation in the validation service
            results = self._validation_service.validate_data()

            # Update status bar with validation results summary
            if results:
                total_issues = sum(len(rule_results) for rule_results in results.values())
                if total_issues > 0:
                    self._set_status_message(f"Validation complete: Found {total_issues} issues")
                else:
                    self._set_status_message("Validation complete: No issues found")
            else:
                self._set_status_message("Validation complete: No issues found")

            # Emit signal to notify about validation change
            self.validation_changed.emit(results)
            logger.info("Validation completed")

        except Exception as e:
            self._set_status_message(f"Validation error: {str(e)}")
            logger.error(f"Error during validation: {e}")

        # Update statistics after validation
        self._update_validation_stats()

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
        # Create an empty DataFrame for the signal
        empty_df = pd.DataFrame()
        self.validation_changed.emit(empty_df)
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

    def _on_case_sensitive_toggled(self, checked: bool) -> None:
        """
        Handle case sensitive checkbox toggle.

        Args:
            checked (bool): Whether the checkbox is checked
        """
        # Update validation service preferences
        prefs = self._validation_service.get_validation_preferences()
        prefs["case_sensitive"] = checked
        self._validation_service.set_validation_preferences(prefs)
        logger.info(f"Case sensitive validation set to: {checked}")

    def _on_validate_on_import_toggled(self, checked: bool) -> None:
        """
        Handle validate on import checkbox toggle.

        Args:
            checked (bool): Whether the checkbox is checked
        """
        # Update validation service preferences
        prefs = self._validation_service.get_validation_preferences()
        prefs["validate_on_import"] = checked
        self._validation_service.set_validation_preferences(prefs)
        logger.info(f"Validate on import set to: {checked}")
        # Do NOT set status message to avoid showing "Validating..." when just toggling preference

    def _display_service_error(self) -> None:
        """Display an error message when the validation service is not available."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Service Error")
        msg_box.setText("Validation service is not available.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
