"""
validation_preferences_view.py

Description: View for configuring validation preferences
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Callable

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QGroupBox,
    QFrame,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
)

from chestbuddy.core.services.validation_service import ValidationService
from chestbuddy.utils.config import ConfigManager

logger = logging.getLogger(__name__)


class ValidationPreferencesView(QDialog):
    """
    Dialog for configuring validation preferences.

    This dialog allows users to configure validation settings such as
    case sensitivity, validation on import, file paths, and auto-save preferences.

    Attributes:
        preferences_changed (Signal): Signal emitted when preferences are changed
    """

    preferences_changed = Signal(dict)  # Dict of preferences

    def __init__(
        self,
        validation_service: ValidationService,
        config_manager: ConfigManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the ValidationPreferencesView.

        Args:
            validation_service (ValidationService): Service for validation
            config_manager (ConfigManager): Application configuration manager
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.validation_service = validation_service
        self._config_manager = config_manager

        # Set window properties
        self.setWindowTitle("Validation Preferences")
        self.setModal(True)
        self.resize(500, 400)

        # Setup UI
        self._setup_ui()

        # Load initial settings
        self._load_preferences()

    def _setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        title_label = QLabel("Validation Settings")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        general_layout.setSpacing(8)

        # Case sensitivity checkbox
        self.case_sensitive_checkbox = QCheckBox("Case-sensitive validation")
        self.case_sensitive_checkbox.setToolTip(
            "When enabled, validation will be case-sensitive (e.g., 'Player' and 'player' are different)"
        )
        general_layout.addWidget(self.case_sensitive_checkbox)

        # Validate on import checkbox
        self.validate_on_import_checkbox = QCheckBox("Validate on import")
        self.validate_on_import_checkbox.setToolTip(
            "When enabled, validation will be performed automatically when importing data"
        )
        general_layout.addWidget(self.validate_on_import_checkbox)

        # Auto-save checkbox
        self.auto_save_checkbox = QCheckBox("Auto-save validation lists")
        self.auto_save_checkbox.setToolTip(
            "When enabled, validation lists will be saved automatically when modified"
        )
        general_layout.addWidget(self.auto_save_checkbox)

        layout.addWidget(general_group)

        # File paths group
        paths_group = QGroupBox("Validation List Paths")
        paths_layout = QVBoxLayout(paths_group)
        paths_layout.setSpacing(8)

        # Players path
        players_layout = QHBoxLayout()
        players_label = QLabel("Players:")
        self.players_path = QLineEdit()
        self.players_path.setReadOnly(True)
        players_browse = QPushButton("Browse...")
        players_browse.clicked.connect(lambda: self._browse_path("players"))
        players_layout.addWidget(players_label)
        players_layout.addWidget(self.players_path)
        players_layout.addWidget(players_browse)
        paths_layout.addLayout(players_layout)

        # Chest types path
        chest_types_layout = QHBoxLayout()
        chest_types_label = QLabel("Chest Types:")
        self.chest_types_path = QLineEdit()
        self.chest_types_path.setReadOnly(True)
        chest_types_browse = QPushButton("Browse...")
        chest_types_browse.clicked.connect(lambda: self._browse_path("chest_types"))
        chest_types_layout.addWidget(chest_types_label)
        chest_types_layout.addWidget(self.chest_types_path)
        chest_types_layout.addWidget(chest_types_browse)
        paths_layout.addLayout(chest_types_layout)

        # Sources path
        sources_layout = QHBoxLayout()
        sources_label = QLabel("Sources:")
        self.sources_path = QLineEdit()
        self.sources_path.setReadOnly(True)
        sources_browse = QPushButton("Browse...")
        sources_browse.clicked.connect(lambda: self._browse_path("sources"))
        sources_layout.addWidget(sources_label)
        sources_layout.addWidget(self.sources_path)
        sources_layout.addWidget(sources_browse)
        paths_layout.addLayout(sources_layout)

        layout.addWidget(paths_group)

        # Add spacer
        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Orientation.Horizontal, self
        )
        button_box.accepted.connect(self._save_preferences)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_preferences(self) -> None:
        """Load preferences from the validation service and config manager."""
        # Load validation preferences
        prefs = self.validation_service.get_validation_preferences()

        # Update checkboxes without triggering signals
        self.case_sensitive_checkbox.blockSignals(True)
        self.validate_on_import_checkbox.blockSignals(True)
        self.auto_save_checkbox.blockSignals(True)

        self.case_sensitive_checkbox.setChecked(prefs.get("case_sensitive", False))
        self.validate_on_import_checkbox.setChecked(prefs.get("validate_on_import", True))
        self.auto_save_checkbox.setChecked(
            self._config_manager.get_bool("Validation", "auto_save", True)
        )

        self.case_sensitive_checkbox.blockSignals(False)
        self.validate_on_import_checkbox.blockSignals(False)
        self.auto_save_checkbox.blockSignals(False)

        # Load file paths
        self.players_path.setText(str(self._config_manager.get_validation_list_path("players.txt")))
        self.chest_types_path.setText(
            str(self._config_manager.get_validation_list_path("chest_types.txt"))
        )
        self.sources_path.setText(str(self._config_manager.get_validation_list_path("sources.txt")))

        logger.debug(f"Loaded validation preferences: {prefs}")

    def _browse_path(self, list_type: str) -> None:
        """
        Show file dialog to browse for a validation list path.

        Args:
            list_type (str): Type of validation list ('players', 'chest_types', 'sources')
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {list_type.replace('_', ' ').title()} List File",
            str(Path.home()),
            "Text Files (*.txt)",
        )

        if not file_path:
            return

        if list_type == "players":
            self.players_path.setText(file_path)
        elif list_type == "chest_types":
            self.chest_types_path.setText(file_path)
        elif list_type == "sources":
            self.sources_path.setText(file_path)

    def _save_preferences(self) -> None:
        """Save preferences and close dialog."""
        # Update validation preferences
        preferences = {
            "case_sensitive": self.case_sensitive_checkbox.isChecked(),
            "validate_on_import": self.validate_on_import_checkbox.isChecked(),
        }
        self.validation_service.set_validation_preferences(preferences)

        # Update auto-save preference
        self._config_manager.set(
            "Validation", "auto_save", str(self.auto_save_checkbox.isChecked())
        )

        # Update file paths
        self._config_manager.set("Validation", "players_list", self.players_path.text())
        self._config_manager.set("Validation", "chest_types_list", self.chest_types_path.text())
        self._config_manager.set("Validation", "sources_list", self.sources_path.text())

        # Save config
        self._config_manager.save()

        # Emit signal
        self.preferences_changed.emit(preferences)

        # Close dialog
        self.accept()

    def refresh(self) -> None:
        """Refresh the preferences view."""
        self._load_preferences()
